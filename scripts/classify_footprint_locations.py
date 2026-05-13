#!/usr/bin/env python3
"""
足迹数据精标脚本 v3
基于原文逐章分析，用规则引擎区分"实景"vs"提及"地点
不依赖大模型，纯规则+交叉验证

策略:
  1. 扫描原文找出所有已知地点的出现
  2. 通过上下文关键词判断是"实景"(角色在此活动)还是"提及"(口头提到)
  3. 对 footprint_v2 中每条章节-地点映射，判断其分类
  4. 如果精确地点名未出现在原文中，尝试通过 parent、events 等渠道佐证
"""

import json
import re
import os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS_DIR = os.path.join(BASE_DIR, 'novel_reader', 'chapters')
VOLUMES_DIR = os.path.join(BASE_DIR, 'novel_data', 'volumes')
FPV2_PATH = os.path.join(BASE_DIR, 'novel_data', 'footprint_v2.json')
OUTPUT_PATH = os.path.join(BASE_DIR, 'novel_data', 'footprint_v3.json')

CN_NUM_MAP = {
    '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
    '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
    '二十一': 21, '二十二': 22, '二十三': 23, '二十四': 24, '二十五': 25,
    '二十六': 26, '二十七': 27, '二十八': 28,
}


# ========== 工具函数 ==========

def extract_chapter_num(ch_str):
    s = str(ch_str).strip()
    if '楔子' in s:
        return 0
    m = re.search(r'第(\d+)回', s)
    if m:
        return int(m.group(1))
    m = re.search(r'第([一二三四五六七八九十]+)回', s)
    if m and m.group(1) in CN_NUM_MAP:
        return CN_NUM_MAP[m.group(1)]
    return None


def get_reader_key(vol, ch_name):
    """将 footprint 的章节名转为 reader 文件中的 key {(vol, reader_ch_num)}"""
    ch_num = extract_chapter_num(ch_name)
    if vol == 1:
        if ch_num is not None:
            return (vol, ch_num + 1)
        elif '楔子' in str(ch_name):
            return (vol, 1)
        return (vol, 1)
    else:
        if ch_num is not None:
            return (vol, ch_num)
        return (vol, 1)


def find_quote_boundaries(text):
    """找出文本中所有引号对的位置"""
    boundaries = []
    for pair in [('\u201c', '\u201d'), ('\u2018', '\u2019'), ('"', '"'), ("'", "'")]:
        open_q, close_q = pair
        i = 0
        while i < len(text):
            if text[i] == open_q:
                j = text.find(close_q, i + 1)
                if j != -1:
                    boundaries.append((i, j))
                    i = j + 1
                    continue
            i += 1
    boundaries.sort()
    return boundaries


def is_in_any_quote(pos, boundaries):
    for start, end in boundaries:
        if start <= pos <= end:
            return True
    return False


# ========== 加载数据 ==========

def load_all_chapter_texts():
    """加载所有章节原文，返回 {(vol_num, reader_chapter_num): text}"""
    texts = {}
    for vol_dir in sorted(os.listdir(CHAPTERS_DIR)):
        vol_path = os.path.join(CHAPTERS_DIR, vol_dir)
        if not os.path.isdir(vol_path):
            continue
        vol_num = int(vol_dir.split('_')[1])
        for fname in sorted(os.listdir(vol_path)):
            if not fname.endswith('.json'):
                continue
            fpath = os.path.join(vol_path, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    ch = json.load(f)
                texts[(vol_num, ch['chapter'])] = ch['content']
            except Exception as e:
                print(f'  ⚠ 加载失败 {fpath}: {e}')
    return texts


def load_all_volume_events():
    """加载所有 volume_*.json 的 events"""
    events_by = defaultdict(list)
    for i in range(1, 29):
        fpath = os.path.join(VOLUMES_DIR, f'volume_{i}.json')
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for evt in data.get('events', []):
                ch_name = evt.get('chapter', '')
                events_by[(i, ch_name)].append(evt)
        except Exception:
            pass
    return dict(events_by)


# ========== 核心匹配与分类 ==========

# 实景动词（出现在地点名之前 → 角色亲身到达）
DIRECT_PRE = [
    '飞抵', '飞到', '飞向', '飞临', '飞至', '飞降',
    '御剑落下', '御剑降在', '御剑落在',
    '落在', '落于', '降在', '降于', '降落在',
    '来到', '进入', '走進', '踏进', '踏进',
    '奔向', '赶往', '赶到', '到达', '抵达',
    '回到', '返回', '退回',
    '进了', '进了', '走出', '走出',
    '驻扎在', '停在', '站在', '坐在', '躺在', '蹲在',
    '潜入', '冲入', '落入', '躲进',
    '出现于', '出现在', '现身于',
]

# 提及触发词
MENTION_PRE = [
    '听说', '据说', '据闻', '传言', '听人说', '有人说',
    '听说过', '提到过', '提及', '听闻',
    '要不要去', '想去', '打算去', '准备去',
    '传说', '知道', '不知', '可知道', '可知',
]


def match_location_in_text(text, loc_name, all_loc_names, locations_data, vol_events=None, vol=None, ch_name=None):
    """
    在原文中匹配地点名，返回 (positions, match_strategy)
    使用多种策略:
      1. 精确匹配 loc_name  → 'exact'
      2. parent 匹配        → 'parent'
      3. 后缀剥离匹配基名    → 'suffix'
      4. 括号前主名匹配      → 'paren'
      5. events 别名匹配     → 'events'
    """
    result = []

    # Strategy 1: 精确匹配
    for m in re.finditer(re.escape(loc_name), text):
        result.append(m.start())

    if result:
        return result, 'exact'

    # Strategy 2: parent 匹配
    loc_info = locations_data.get(loc_name, {})
    parent = loc_info.get('parent', '')
    if parent and parent in all_loc_names:
        for m in re.finditer(re.escape(parent), text):
            result.append(m.start())
        if result:
            return result, 'parent'

    # Strategy 3: 去掉常见的层级后缀
    BASE_SUFFIXES = [
        '后山脚', '小玄房中', '小玄房', '房中',
        '郊外酒肆', '平原丛林', '岛高台', '营外土坡',
        '上空战场', '所在山洞', '所在洞厅', '所在位置',
        '（魅影制造工棚）', '（树洞）', '（外围竹林）', '（大堂）', '（拱桥）', '（竹林高地）',
        '（白眉翁居所外战场）', '（飞萝离去之路）', '（返回太碧途中）', '（追怪鸟途中）',
        '（武翩跹入侵）', '（天庭/妖界/西方三方对峙处外围）',
    ]
    for suffix in BASE_SUFFIXES:
        if loc_name.endswith(suffix):
            base = loc_name[:-len(suffix)]
            if base and base in all_loc_names:
                for m in re.finditer(re.escape(base), text):
                    result.append(m.start())
                if result:
                    return result, 'suffix'

    # Strategy 4: 对含括号的，匹配括号前的主名
    paren_idx = loc_name.find('（')
    if paren_idx != -1:
        main_part = loc_name[:paren_idx]
        if main_part in all_loc_names:
            for m in re.finditer(re.escape(main_part), text):
                result.append(m.start())
            if result:
                return result, 'paren'

    # Strategy 5: 利用 events 数据的 location 别名
    if vol_events and vol and ch_name:
        def get_evts(v, cn):
            lst = []
            if (v, cn) in vol_events:
                lst.extend(vol_events[(v, cn)])
            vp = f'第{v}卷'
            pf = f'{vp}{cn}' if cn else ''
            if pf and (v, pf) in vol_events:
                lst.extend(vol_events[(v, pf)])
            st = re.sub(r'^第\d+卷', '', cn).strip() if cn else ''
            if st != cn and st and (v, st) in vol_events:
                lst.extend(vol_events[(v, st)])
            return lst

        evts = get_evts(vol, ch_name)
        for evt in evts:
            evt_loc = evt.get('location', '')
            if evt_loc and evt_loc != loc_name:
                if evt_loc in text:
                    for m in re.finditer(re.escape(evt_loc), text):
                        result.append(m.start())
                    if result:
                        return result, 'events'

    return result, None


def analyze_location_in_text(text, loc_name, all_loc_names, locations_data, quote_bounds, vol_events=None, vol=None, ch_name=None):
    """
    在原文中分析该地点的所有出现，返回分类结果
    """
    positions, match_strat = match_location_in_text(text, loc_name, all_loc_names, locations_data, vol_events, vol, ch_name)
    if not positions:
        # 尝试只匹配地名中的核心词（最后一个策略）
        for m in re.finditer(re.escape(loc_name), text):
            positions.append(m.start())
        if not positions:
            return None

    direct_count = 0
    mention_count = 0
    in_quote_count = 0
    total = len(positions)
    evidence = []

    # 后缀匹配或 events 别名匹配时，置信度提升
    is_indirect_match = match_strat in ('suffix', 'parent', 'events')

    for pos in positions:
        # 对于间接匹配，扩宽上下文窗口
        context_radius = 60 if is_indirect_match else 40
        before_raw = text[max(0, pos - context_radius):pos]
        after_raw = text[pos + len(loc_name) if not is_indirect_match else pos:min(len(text), pos + context_radius)]
        before = before_raw.strip()
        after = after_raw.strip()

        in_quote = is_in_any_quote(pos, quote_bounds)

        if in_quote:
            in_quote_count += 1
            is_dialogue = bool(re.search(r'[的道说问答喊叫喝]', before[-15:]))
            if is_dialogue:
                if is_indirect_match:
                    direct_count += 1
                    if len(evidence) < 2:
                        evidence.append({'type': 'direct', 'note': 'indirect_match_in_quote', 'context': before + f"『{loc_name}』" + after})
                else:
                    mention_count += 1
                    if len(evidence) < 2:
                        evidence.append({'type': 'mentioned', 'in_quote': True, 'context': before + f"『{loc_name}』" + after})
                continue
            else:
                direct_count += 1
                if len(evidence) < 2:
                    evidence.append({'type': 'direct', 'in_quote': False, 'context': before + f"『{loc_name}』" + after})
                continue

        is_direct = False
        for pat in DIRECT_PRE:
            if pat in before:
                is_direct = True
                break

        if not is_direct and '在' in before:
            is_direct = True

        if not is_direct and len(before) <= 3 and (after.endswith('。') or after.endswith('，') or after == ''):
            is_direct = True

        is_mention = False
        if not is_direct:
            for pat in MENTION_PRE:
                if pat in before:
                    is_mention = True
                    break

        if is_direct:
            direct_count += 1
        elif is_mention:
            mention_count += 1
        else:
            direct_count += 1

        if len(evidence) < 2:
            cls_type = 'direct' if is_direct else ('mentioned' if is_mention else 'uncertain')
            evidence.append({'type': cls_type, 'in_quote': in_quote, 'context': before + f"『{loc_name}』" + after})

    return {
        'total': total,
        'direct': direct_count,
        'mentioned': mention_count,
        'in_quote': in_quote_count,
        'evidence': evidence,
    }


def classify_from_analysis(analysis, orig_loc, vol, ch_name, vol_events, events_fallback):
    """
    综合单章分析结果确定分类

    策略:
    - 如果分析显示有 direct 出现 → 实景
    - 如果只有 mention → 提及
    - 如果原文找不到 → 看 events 交叉
    - 如果 events 也找不到 → inferred
    """
    event_ref = {'total_events': 0, 'matched': 0, 'consistency': 0}

    # 尝试多种 key 格式查找 events
    def get_events(v, cn):
        candidates = []
        # 直接匹配
        if (v, cn) in vol_events:
            candidates.extend(vol_events[(v, cn)])
        # 加卷前缀：如 vol=4, cn="第八回" → "第四卷第八回"
        vol_prefix = f'第{v}卷'
        prefixed = f'{vol_prefix}{cn}' if cn else ''
        if prefixed and (v, prefixed) in vol_events:
            candidates.extend(vol_events[(v, prefixed)])
        # 去掉卷前缀：如 cn="第四卷第八回" → "第八回"
        stripped = re.sub(r'^第\d+卷', '', cn).strip() if cn else ''
        if stripped != cn and stripped and (v, stripped) in vol_events:
            candidates.extend(vol_events[(v, stripped)])
        return candidates

    evts = get_events(vol, ch_name)
    matched_events = 0
    for evt in evts:
        evt_loc = evt.get('location', '')
        if orig_loc in evt_loc or evt_loc in orig_loc:
            matched_events += 1
    event_ref = {
        'total_events': len(evts),
        'matched': matched_events,
        'consistency': round(matched_events / max(len(evts), 1), 2),
    }

    if analysis is None:
        if matched_events >= 1:
            return {
                'type': 'direct',
                'confidence': 'medium',
                'confidence_score': 0.55 + matched_events * 0.05,
                'note': f'原文未找到精确地点名，但有 {matched_events}/{len(evts)} 个 events 佐证',
                'event_cross_ref': event_ref,
            }
        return {
            'type': 'inferred',
            'confidence': 'low',
            'confidence_score': 0.2,
            'note': '原文中未找到该地点名，events 也缺乏直接证据',
            'event_cross_ref': event_ref,
        }

    direct_ratio = analysis['direct'] / max(analysis['total'], 1)
    mention_ratio = analysis['mentioned'] / max(analysis['total'], 1)

    if direct_ratio >= 0.4:
        if event_ref['consistency'] >= 0.4:
            return {
                'type': 'direct',
                'confidence': 'high',
                'confidence_score': round(0.85 + direct_ratio * 0.15, 2),
                'evidence': analysis['evidence'],
                'event_cross_ref': event_ref,
            }
        else:
            return {
                'type': 'direct',
                'confidence': 'medium',
                'confidence_score': round(0.6 + direct_ratio * 0.2, 2),
                'evidence': analysis['evidence'],
                'event_cross_ref': event_ref,
            }
    elif mention_ratio >= 0.6:
        return {
            'type': 'mentioned',
            'confidence': 'high',
            'confidence_score': round(0.7 + mention_ratio * 0.2, 2),
            'evidence': analysis['evidence'],
            'event_cross_ref': event_ref,
        }
    else:
        return {
            'type': 'uncertain',
            'confidence': 'low',
            'confidence_score': round(0.2 + direct_ratio * 0.4, 2),
            'evidence': analysis['evidence'],
            'event_cross_ref': event_ref,
        }


def find_other_location_mentions(text, all_loc_names, locations_data, exclude_names, max_show=8, vol_events=None, vol=None, ch_name=None):
    """找出本章中出现过的其他地点名"""
    quote_bounds = find_quote_boundaries(text)
    result = []

    for name in all_loc_names:
        if name in exclude_names:
            continue
        analysis = analyze_location_in_text(
            text, name, all_loc_names, locations_data, quote_bounds,
            vol_events, vol, ch_name
        )
        if analysis and analysis['total'] > 0:
            result.append({
                'name': name,
                'occurrences': analysis['total'],
                'direct': analysis['direct'],
                'mentioned': analysis['mentioned'],
                'direct_pct': round(analysis['direct'] / max(analysis['total'], 1), 2),
            })

    result.sort(key=lambda x: x['occurrences'], reverse=True)
    return result[:max_show]


def main():
    print('=' * 55)
    print('  足迹数据精标 v3')
    print('  基于原文规则的实景/提及分类')
    print('=' * 55)

    print('\n[1/5] 加载数据...')
    with open(FPV2_PATH, 'r', encoding='utf-8') as f:
        fpv2 = json.load(f)

    chapter_texts = load_all_chapter_texts()
    vol_events = load_all_volume_events()
    all_loc_names = sorted(fpv2['locations'].keys(), key=len, reverse=True)
    locations_data = fpv2['locations']

    # 额外收集 chapters 中用到但 locations 中缺失的地点
    chapters_only_locs = set()
    for ch in fpv2['chapters']:
        loc = ch['location_name']
        if loc not in locations_data:
            chapters_only_locs.add(loc)
    if chapters_only_locs:
        print(f'  ⚠ chapters 中有 {len(chapters_only_locs)} 个地点不在 locations 中:')
        for loc in sorted(chapters_only_locs):
            print(f'    - {loc}')

    print(f'  原文: {len(chapter_texts)} 章节')
    print(f'  Volume events: {sum(len(v) for v in vol_events.values())} 条')
    print(f'  地点: {len(all_loc_names)} 个 (+{len(chapters_only_locs)} chapters-only)')
    print(f'  Footprint章节: {len(fpv2["chapters"])} 条')

    # 全量地点名（含 chapters_only）
    full_loc_names = list(chapters_only_locs) + all_loc_names
    full_loc_names.sort(key=len, reverse=True)

    print('\n[2/5] 逐章分析...')
    total = len(fpv2['chapters'])
    type_counts = defaultdict(int)
    results = []
    prev_location = None
    prev_type = None

    for idx, ch_entry in enumerate(fpv2['chapters']):
        vol = ch_entry['volume']
        ch_name = ch_entry['chapter']
        full_name = ch_entry['full_name']
        orig_loc = ch_entry['location_name']

        reader_key = get_reader_key(vol, ch_name)
        text = chapter_texts.get(reader_key, '')
        if not text and vol == 1:
            text = chapter_texts.get((1, 1), '')

        if not text:
            results.append({
                'volume': vol, 'chapter': ch_name, 'full_name': full_name,
                'original_location': orig_loc,
                'classification': {
                    'type': 'skipped', 'confidence': 'low', 'confidence_score': 0,
                    'note': f'原文未找到 reader_key={reader_key}',
                    'event_cross_ref': {'total_events': 0, 'matched': 0, 'consistency': 0},
                },
            })
            type_counts['skipped'] += 1
            continue

        quote_bounds = find_quote_boundaries(text)

        # 分析原始地点
        orig_analysis = analyze_location_in_text(
            text, orig_loc, full_loc_names, locations_data, quote_bounds,
            vol_events, vol, ch_name
        )

        # events 是否有同名的事件地点可以佐证
        def get_evts(v, cn):
            lst = []
            if (v, cn) in vol_events:
                lst.extend(vol_events[(v, cn)])
            vp = f'第{v}卷'
            pf = f'{vp}{cn}' if cn else ''
            if pf and (v, pf) in vol_events:
                lst.extend(vol_events[(v, pf)])
            st = re.sub(r'^第\d+卷', '', cn).strip() if cn else ''
            if st != cn and st and (v, st) in vol_events:
                lst.extend(vol_events[(v, st)])
            return lst

        evts = get_evts(vol, ch_name)
        events_support_orig = any(
            orig_loc in e.get('location', '') or e.get('location', '') in orig_loc
            for e in evts
        )

        cls = classify_from_analysis(
            orig_analysis, orig_loc, vol, ch_name, vol_events, events_support_orig
        )

        # 场景连续性修正：同类地点在不同章节连续出现且后一章未明确换场景 → 保持实景
        if cls['type'] == 'mentioned' and orig_loc == prev_location and prev_type == 'direct':
            cls = {
                'type': 'direct',
                'confidence': 'medium',
                'confidence_score': 0.6,
                'note': '场景连续性：前一章在此地且本章未明确换场景',
                'evidence': cls.get('evidence', []),
                'event_cross_ref': cls.get('event_cross_ref', {'total_events': 0, 'matched': 0, 'consistency': 0}),
            }

        type_counts[cls['type']] += 1

        prev_location = orig_loc
        prev_type = cls['type']

        # 找出其他地点
        other = find_other_location_mentions(
            text, full_loc_names, locations_data,
            exclude_names={orig_loc}, max_show=8,
            vol_events=vol_events, vol=vol, ch_name=ch_name,
        )

        results.append({
            'volume': vol,
            'chapter': ch_name,
            'full_name': full_name,
            'original_location': orig_loc,
            'classification': cls,
            'other_locations': other,
        })

        if (idx + 1) % 20 == 0:
            print(f'  已分析 {idx + 1}/{total}...')

    print('\n[3/5] 构建地点统计摘要...')
    loc_summary = {}
    loc_info_template = {name: {'direct_in': [], 'mentioned_in': [], 'inferred_in': [], 'total_direct': 0, 'total_mentioned': 0, 'total_inferred': 0} for name in locations_data}

    for r in results:
        loc = r['original_location']
        if loc not in loc_info_template:
            loc_info_template[loc] = {'direct_in': [], 'mentioned_in': [], 'inferred_in': [], 'total_direct': 0, 'total_mentioned': 0, 'total_inferred': 0}
        t = r['classification']['type']
        if t == 'direct':
            loc_info_template[loc]['direct_in'].append(r['full_name'])
            loc_info_template[loc]['total_direct'] += 1
        elif t == 'mentioned':
            loc_info_template[loc]['mentioned_in'].append(r['full_name'])
            loc_info_template[loc]['total_mentioned'] += 1
        else:
            loc_info_template[loc]['inferred_in'].append(r['full_name'])
            loc_info_template[loc]['total_inferred'] += 1

    loc_summary = loc_info_template

    print('\n[4/5] 组装输出...')
    output = {
        'meta': {
            'novel': '逍遥小散仙',
            'description': '足迹精标数据 v3 — 基于原文规则分类实景/提及',
            'generated_at': '2025-05-12',
            'method': '规则引擎：上下文关键词匹配 + parent/events 交叉验证',
            'data_source': 'novel_reader/chapters/* 原文 + novel_data/footprint_v2.json',
        },
        'summary': {
            'total': len(results),
            'direct': type_counts.get('direct', 0),
            'mentioned': type_counts.get('mentioned', 0),
            'inferred': type_counts.get('inferred', 0),
            'uncertain': type_counts.get('uncertain', 0),
            'skipped': type_counts.get('skipped', 0),
            'direct_pct': round(type_counts.get('direct', 0) / max(len(results), 1) * 100, 1),
            'mentioned_pct': round(type_counts.get('mentioned', 0) / max(len(results), 1) * 100, 1),
        },
        'chapters': results,
        'location_summary': loc_summary,
    }

    print(f'\n[5/5] 保存到 {OUTPUT_PATH}...')
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print('\n' + '=' * 55)
    print('  分类结果摘要')
    print('=' * 55)
    print(f'  总分析条目: {output["summary"]["total"]}')
    print(f'  ✅ 实景:     {output["summary"]["direct"]} ({output["summary"]["direct_pct"]}%)')
    print(f'  💬 提及:     {output["summary"]["mentioned"]} ({output["summary"]["mentioned_pct"]}%)')
    print(f'  🤔 推理:     {output["summary"]["inferred"]}')
    print(f'  ❓ 不确定:   {output["summary"]["uncertain"]}')
    print(f'  ⏭ 跳过:     {output["summary"]["skipped"]}')
    print(f'\n  输出: {OUTPUT_PATH}')
    print('=' * 55)

    print('\n  实景样例:')
    n = 0
    for r in results:
        if r['classification']['type'] == 'direct' and n < 5:
            print(f'    ✅ {r["full_name"]:25s} → {r["original_location"]:15s} '
                  f'({r["classification"]["confidence_score"]})')
            n += 1

    print('\n  提及需关注:')
    n = 0
    for r in results:
        if r['classification']['type'] == 'mentioned' and n < 8:
            print(f'    💬 {r["full_name"]:25s} → {r["original_location"]:15s} '
                  f'({r["classification"]["confidence_score"]})')
            n += 1

    print('\n  推理(无原文匹配):')
    n = 0
    for r in results:
        if r['classification']['type'] == 'inferred' and n < 5:
            others = [o['name'] for o in r.get('other_locations', [])[:3]]
            print(f'    🤔 {r["full_name"]:25s} → {r["original_location"]:15s} '
                  f'| 文中出现: {others}')
            n += 1

    return output


if __name__ == '__main__':
    main()
