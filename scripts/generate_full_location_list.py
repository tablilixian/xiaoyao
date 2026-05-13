#!/usr/bin/env python3
"""
完整剧情地点清单生成脚本
遍历所有 282 章原文 + 28 卷 events 数据，生成逐章剧情地点清单
"""

import json
import re
import os
from collections import defaultdict, Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, 'novel_reader', 'index.json')
CHAPTERS_DIR = os.path.join(BASE_DIR, 'novel_reader', 'chapters')
VOLUMES_DIR = os.path.join(BASE_DIR, 'novel_data', 'volumes')
FPV2_PATH = os.path.join(BASE_DIR, 'novel_data', 'footprint_v2.json')
FPV3_PATH = os.path.join(BASE_DIR, 'novel_data', 'footprint_v3.json')
OUTPUT_PATH = os.path.join(BASE_DIR, 'novel_data', 'full_location_list.md')

CN_NUM_MAP = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15,
    '十六': 16, '十七': 17, '十八': 18, '十九': 19, '二十': 20,
    '二十一': 21, '二十二': 22, '二十三': 23, '二十四': 24, '二十五': 25,
    '二十六': 26, '二十七': 27, '二十八': 28,
}


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


def get_events_for_chapter(vol, ch_num, vol_events, cumulative_offset=0):
    """获取某卷某章节的所有事件
    支持所有已知的命名模式。
    cumulative_offset: 累计章节偏移（vol>=10 时用于匹配阿拉伯数字编号）
    """

    CN_SHORT = ['零','一','二','三','四','五','六','七','八','九','十']
    CN = ['零','一','二','三','四','五','六','七','八','九','十',
          '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十']

    candidates = set()

    if vol == 1:
        if ch_num == 1:
            candidates.add('楔子')
            candidates.add('0')
        else:
            cn_idx = ch_num - 1
            if cn_idx < len(CN):
                candidates.add(f'第{CN[cn_idx]}回')
            candidates.add(f'第{cn_idx}回')
    elif vol == 2 or vol == 3:
        # "第二卷第一回", "第三卷第一回"
        if vol < len(CN_SHORT) and ch_num < len(CN):
            candidates.add(f'第{CN_SHORT[vol]}卷第{CN[ch_num]}回')
        # "第六卷第一回" (作为vol 6的备用)
        if vol <= 6 and ch_num < len(CN):
            candidates.add(f'第{CN_SHORT[vol]}卷第{CN[ch_num]}回')
    elif vol == 6:
        # volume 6 特殊: 使用"第六卷第一回"格式
        if ch_num < len(CN):
            candidates.add(f'第{CN_SHORT[vol]}卷第{CN[ch_num]}回')
            candidates.add(f'第{CN[ch_num]}回')
    elif 4 <= vol <= 9:
        if ch_num < len(CN):
            candidates.add(f'第{CN[ch_num]}回')
        candidates.add(f'第{ch_num}回')
        # 部分卷(6)用卷前缀
        if vol < len(CN_SHORT) and ch_num < len(CN):
            candidates.add(f'第{CN_SHORT[vol]}卷第{CN[ch_num]}回')
    else:
        # vol >= 10: 阿拉伯数字 "第91回" 或纯数字 91
        cum = cumulative_offset + ch_num
        candidates.add(f'第{cum}回')
        candidates.add(str(cum))
        candidates.add(f'第{ch_num}回')
        candidates.add(str(ch_num))

    result = []
    for c in candidates:
        result.extend(vol_events.get((vol, c), []))

    # 尝试所有可能的跨章节和近似匹配
    all_keys = list(vol_events.keys())
    for key, evts in vol_events.items():
        if key[0] != vol:
            continue
        key_str = str(key[1])
        for c in candidates:
            # 精确匹配
            if c == key_str:
                for e in evts:
                    result.append(e)
            # 跨章节: "第一回/第二回" 或 "第1-2回"
            elif '/' in key_str and c in key_str:
                for e in evts:
                    result.append(e)
            elif '-' in key_str and c in key_str:
                for e in evts:
                    result.append(e)

    # 去重
    seen = set()
    unique = []
    for e in result:
        eid = e.get('id', '')
        if eid not in seen:
            seen.add(eid)
            unique.append(e)
    return unique


def get_chapter_title_display(vol, ch_num, reader_chapters):
    """获取章节的展示名"""
    for v in reader_chapters:
        if v['volume'] == vol:
            for c in v['chapters']:
                if c['chapter'] == ch_num:
                    return c['title']
    return f'第{ch_num}回'


def is_intro_or_volume_page(ch):
    """判断是否是 intro 或 volume_page 类型"""
    return ch.get('type') in ('intro', 'volume_page')


def main():
    print('=' * 55)
    print('  完整剧情地点清单生成')
    print('=' * 55)

    # 1. 加载数据
    print('\n[1/4] 加载数据...')
    with open(INDEX_PATH, 'r', encoding='utf-8') as f:
        index = json.load(f)

    # 加载所有 volume events
    vol_events = defaultdict(list)
    for i in range(1, 29):
        fpath = os.path.join(VOLUMES_DIR, f'volume_{i}.json')
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for evt in data.get('events', []):
                ch_name = evt.get('chapter', '')
                vol_events[(i, ch_name)].append(evt)

    # 加载 footprint_v2 (作为参考)
    fp2_data = {}
    if os.path.exists(FPV2_PATH):
        with open(FPV2_PATH) as f:
            fp2 = json.load(f)
        for ch in fp2['chapters']:
            key = (ch['volume'], ch['chapter'])
            if key not in fp2_data:
                fp2_data[key] = []
            fp2_data[key].append(ch['location_name'])

    # 加载 footprint_v3 (已分类)
    fp3_data = {}
    if os.path.exists(FPV3_PATH):
        with open(FPV3_PATH) as f:
            fp3 = json.load(f)
        for r in fp3['chapters']:
            key = (r['volume'], r['chapter'])
            if key not in fp3_data:
                fp3_data[key] = []
            fp3_data[key].append(r)

    print(f'  总章节: {index["total_chapters"]}')
    print(f'  Volumes events: {sum(len(v) for v in vol_events.values())} 条')
    print(f'  footprint_v2: {len(fp2_data)} 个章节key')
    print(f'  footprint_v3: {len(fp3_data)} 个章节key')

    # 预计算每卷起始累计值（用于 vol>=10 的阿拉伯数字编号映射）
    vol_cumulative_start = {}
    cum = 0
    for v_info in index['volumes']:
        v = v_info['volume']
        vol_cumulative_start[v] = cum
        cum += sum(1 for ch in v_info['chapters'] if not is_intro_or_volume_page(ch))

    # 2. 遍历所有章节
    print('\n[2/4] 遍历章节确定地点...')
    all_entries = []
    prev_location = None
    skipped = 0

    for vol_info in index['volumes']:
        vol = vol_info['volume']
        for ch in vol_info['chapters']:
            if is_intro_or_volume_page(ch):
                skipped += 1
                continue

            ch_num = ch['chapter']
            ch_title = ch['title']
            ch_file = ch['file']

            # 构建 events 中的章节显示名
            if vol == 1:
                if ch_num == 1:
                    evt_ch_name = '楔子'
                else:
                    CN = ['零','一','二','三','四','五','六','七','八','九','十']
                    cn_idx = ch_num - 1
                    evt_ch_name = f'第{CN[cn_idx]}回' if cn_idx < len(CN) else f'第{ch_num - 1}回'
            elif 2 <= vol <= 3:
                CN = ['零','一','二','三','四','五','六','七','八','九','十']
                cv = CN[vol] if vol < len(CN) else str(vol)
                cc = CN[ch_num] if ch_num < len(CN) else str(ch_num)
                evt_ch_name = f'第{cv}卷第{cc}回'
            elif 4 <= vol <= 9:
                CN = ['零','一','二','三','四','五','六','七','八','九','十',
                      '十一','十二','十三','十四','十五','十六','十七','十八','十九','二十']
                cc = CN[ch_num] if ch_num < len(CN) else str(ch_num)
                evt_ch_name = f'第{cc}回'
            else:
                evt_ch_name = f'第{ch_num}回'

            # 获取 events
            cum_offset = vol_cumulative_start.get(vol, 0)
            evts = get_events_for_chapter(vol, ch_num, vol_events, cum_offset)

            # 提取 events 中的 locations
            evt_locations = [e.get('location', '') for e in evts]
            evt_location_counts = Counter(evt_locations)

            # 主要地点 = events 中最常出现的 location
            primary_location = ''
            if evt_location_counts:
                primary_location = evt_location_counts.most_common(1)[0][0]

            # 所有不同地点
            all_locations_this_ch = list(dict.fromkeys(evt_locations))

            # 检查 footprint_v2/v3 数据
            # fp2/fp3 使用 reader chapter name 作为 key
            fp2_locs = fp2_data.get((vol, evt_ch_name), [])
            fp3_entries = fp3_data.get((vol, evt_ch_name), [])
            # 也尝试用卷前缀
            if not fp2_locs and vol > 1:
                alt_key = f'第{evt_ch_name}' if not evt_ch_name.startswith('第') else evt_ch_name
                fp2_locs = fp2_data.get((vol, '第' + str(vol) + '卷' + evt_ch_name), [])
                fp3_entries = fp3_data.get((vol, '第' + str(vol) + '卷' + evt_ch_name), [])

            fp3_type = None
            fp3_score = None
            if fp3_entries:
                cls_types = [e['classification']['type'] for e in fp3_entries]
                scores = [e['classification']['confidence_score'] for e in fp3_entries]
                fp3_type = cls_types[0] if cls_types else None
                fp3_score = scores[0] if scores else None

            entry = {
                'vol': vol,
                'ch_num': ch_num,
                'ch_title': ch_title,
                'evt_ch_name': evt_ch_name,
                'primary_location': primary_location,
                'all_locations': all_locations_this_ch,
                'events_count': len(evts),
                'fp2_locs': fp2_locs,
                'fp3_type': fp3_type,
                'location_source': 'events',
            }

            # 如果没有 events 但有 footprint 数据
            if not primary_location and fp2_locs:
                # 取 fp2 的第一个地点
                candidate = fp2_locs[0]
                # 如果有 fp3 且是 direct, 使用它
                if fp3_entries:
                    for e in fp3_entries:
                        if e['classification']['type'] == 'direct':
                            candidate = e['original_location']
                            break
                primary_location = candidate
                entry['location_source'] = 'footprint_v2'

            # 如果还是没有地点，尝试从 prev 延续
            if not primary_location and prev_location:
                primary_location = f'（承接）{prev_location}'
                entry['location_source'] = 'continuity'

            if primary_location:
                entry['primary_location'] = primary_location

            all_entries.append(entry)
            if primary_location:
                prev_location = primary_location

    print(f'  有效章节: {len(all_entries)}, intro/卷页跳过: {skipped}')

    # 3. 统计
    print('\n[3/4] 统计...')
    by_source = Counter(e['location_source'] for e in all_entries)

    # 4. 生成 MD
    print('\n[4/4] 生成 Markdown...')
    lines = []

    lines.append('# 逍遥小散仙 · 完整剧情地点清单')
    lines.append('')
    lines.append(f'> 基于 28 卷 events 数据 + novel_reader 282 章原文索引')
    lines.append(f'> 共 {len(all_entries)} 个故事章节 | events 确定: {by_source.get("events",0)} | footprint 补充: {by_source.get("footprint_v2",0)} | 延续推断: {by_source.get("continuity",0)}')
    lines.append('')

    lines.append('## 总览')
    lines.append('')
    lines.append(f'| 数据来源 | 章节数 |')
    lines.append(f'|----------|--------|')
    for src, cnt in sorted(by_source.items()):
        lines.append(f'| {src:12s} | {cnt} |')
    lines.append('')
    lines.append('---')
    lines.append('')

    # 计算每卷的累计偏移
    vol_chapter_counts = {}
    for v_info in index['volumes']:
        v = v_info['volume']
        count = sum(1 for ch in v_info['chapters'] if not is_intro_or_volume_page(ch))
        vol_chapter_counts[v] = count

    current_vol = 0
    in_vol_table = False

    for entry in all_entries:
        vol = entry['vol']
        ch_num = entry['ch_num']
        ch_title = entry['ch_title']
        loc = entry.get('primary_location', '—')
        evt_ch_name = entry['evt_ch_name']
        evt_count = entry['events_count']
        all_locs = entry['all_locations']
        fp2_locs = entry['fp2_locs']
        fp3_type = entry.get('fp3_type')
        loc_source = entry['location_source']

        if vol != current_vol:
            if in_vol_table:
                lines.append('')
                lines.append('---')
                lines.append('')
            current_vol = vol
            in_vol_table = True

            vol_title = f'第{vol}卷'

            # Find volume intro if exists
            vol_intro = ''
            for v in index['volumes']:
                if v['volume'] == vol:
                    intro_data = v.get('intro', {})
                    if intro_data and intro_data.get('content'):
                        vol_intro = intro_data['content'].replace('\n', ' ')[:60]
                    break

            lines.append(f'## {vol_title}')
            if vol_intro:
                lines.append(f'')
                lines.append(f'> {vol_intro}...')
                lines.append('')
            lines.append(f'| # | 章节 | 标题 | 剧情地点 | events | 验证 |')
            lines.append(f'|---|------|------|----------|--------|------|')

        # Build location string
        loc_display = loc if loc else '—'

        # Verification badge
        badge = ''
        if fp3_type == 'direct':
            badge = '✅'
        elif fp3_type == 'mentioned':
            badge = '💬'
        elif fp3_type == 'inferred':
            badge = '🤔'
        elif loc_source == 'events':
            badge = '✓' if evt_count > 0 else '?'

        location_note = ''
        if fp2_locs and loc not in fp2_locs:
            location_note = f' (V2: {fp2_locs[0]})'

        lines.append(f'| {ch_num:2d} | {evt_ch_name:12s} | {ch_title:20s} | {loc_display:30s} | {evt_count:2d}条 | {badge:4s} |')

    lines.append('')
    lines.append('---')
    lines.append('')
    lines.append('## 说明')
    lines.append('')
    lines.append('- **剧情地点**: 来自 volume_*.json 的 events 数据，取本章出现次数最多的地点')
    lines.append('  - events = 该章有具体事件标注的地点，可靠性最高')
    lines.append('  - footprint_v2 = 原始 scenes 数据展开，部分章节补充')
    lines.append('  - continuity = 无 events 数据和 footprint 数据时，沿用前一章地点')
    lines.append('- **验证列**: 标记含义')
    lines.append('  - ✅ = V3 确认为实景')
    lines.append('  - 💬 = V3 标注为提及（仅对话中出现）')
    lines.append('  - 🤔 = V3 推理（原文无精确匹配）')
    lines.append('  - ✓ = 有 events 数据但 V3 未覆盖')
    lines.append('  - ? = 无 events、无 V3 覆盖')
    lines.append('')

    md_content = '\n'.join(lines)

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f'\n✅ 已生成: {OUTPUT_PATH}')
    print(f'   共 {len(all_entries)} 个故事章节')
    print(f'   events 确定: {by_source.get("events", 0)}')
    print(f'   footprint 补充: {by_source.get("footprint_v2", 0)}')
    print(f'   延续推断: {by_source.get("continuity", 0)}')


if __name__ == '__main__':
    main()
