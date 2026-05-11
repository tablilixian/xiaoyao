#!/usr/bin/env python3
import json, re, os
from collections import defaultdict

FOOTPRINT_FILE = os.path.join(os.path.dirname(__file__), '..', 'novel_data', 'footprint_v2.json')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'novel_data', 'footprint_v2_verification.json')
READER_INDEX = os.path.join(os.path.dirname(__file__), '..', 'novel_reader', 'index.json')
READER_CHAPTERS = os.path.join(os.path.dirname(__file__), '..', 'novel_reader', 'chapters')

CN_NUM = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
          '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18,'十九':19,'二十':20,
          '二十一':21,'二十二':22,'二十三':23,'二十四':24,'二十五':25,'二十六':26,'二十七':27,'二十八':28}

def extract_chapter_number(ch_str):
    s = str(ch_str).strip()
    if '楔子' in s: return 0
    m = re.search(r'第(\d+)回', s)
    if m: return int(m.group(1))
    m = re.search(r'第([一二三四五六七八九十]+)回', s)
    if m and m.group(1) in CN_NUM: return CN_NUM[m.group(1)]
    return None

def build_reader_index():
    idx_by_vol_title = defaultdict(list)
    vols = os.listdir(READER_CHAPTERS)
    for vol_dir in sorted(vols):
        vol_path = os.path.join(READER_CHAPTERS, vol_dir)
        if not os.path.isdir(vol_path): continue
        vol_num = int(vol_dir.split('_')[1])
        for fname in sorted(os.listdir(vol_path)):
            if not fname.endswith('.json'): continue
            fpath = os.path.join(vol_path, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    ch = json.load(f)
                title = ch.get('title', '')
                content = ch.get('content', '')
                chapter_num = ch.get('chapter', 0)
                info = {'title': title, 'content': content,
                        'reader_volume': vol_num, 'reader_chapter': chapter_num, 'file': fname}
                idx_by_vol_title[vol_num].append(info)
            except: pass
    for vol in idx_by_vol_title:
        idx_by_vol_title[vol].sort(key=lambda x: x['reader_chapter'])
    return idx_by_vol_title

def find_reader_chapter(vol, chapter_str, reader_by_vol):
    if vol not in reader_by_vol: return None
    ch_num = extract_chapter_number(chapter_str)
    if ch_num is None: return None
    if vol == 1:
        target = ch_num + 1
    else:
        target = ch_num
    for info in reader_by_vol[vol]:
        if info['reader_chapter'] == target:
            return info
    return None

def verify_chapters(fp_chapters, reader_by_vol):
    results = []
    stats = {'verified': 0, 'partial': 0, 'unverified': 0, 'not_found': 0}
    for ch in fp_chapters:
        vol = ch.get('volume', 0)
        chapter_str = ch.get('chapter', '')
        location_name = ch.get('location_name', '')
        characters = ch.get('characters', [])
        reader_info = find_reader_chapter(vol, chapter_str, reader_by_vol)
        if not reader_info:
            results.append({
                'volume': vol, 'chapter': chapter_str,
                'location': location_name, 'verification': 'not_found',
                'score': 0, 'details': 'No matching reader chapter found'
            })
            stats['not_found'] += 1
            continue

        content = reader_info['content']
        reader_title = reader_info['title']
        matches = 0
        checks = []

        loc_in_text = location_name in content
        if loc_in_text:
            matches += 1
            checks.append(f"location '{location_name}' ✓")
        else:
            loc_alt = location_name.replace('（', '(').replace('）', ')')
            loc_in_text_alt = loc_alt in content
            if loc_in_text_alt:
                matches += 1
                checks.append(f"location '{loc_alt}' ✓ (alt)")
            else:
                checks.append(f"location '{location_name}' ✗")

        char_matches = 0
        for char in characters[:8]:
            if char in content:
                char_matches += 1
        if characters:
            ratio = char_matches / len(characters)
            matches += ratio
            checks.append(f"characters {char_matches}/{len(characters)} ✓")

        n_events = len(ch.get('events', []))
        score = min(100, int((matches / max(1, 1 + len(checks) * 0.3)) * 100))
        if loc_in_text and char_matches >= len(characters) * 0.5:
            level = 'verified'
            stats['verified'] += 1
        elif loc_in_text:
            level = 'partial'
            stats['partial'] += 1
        else:
            level = 'unverified'
            stats['unverified'] += 1

        results.append({
            'volume': vol,
            'chapter': chapter_str,
            'full_name': ch.get('full_name', ''),
            'location': location_name,
            'verification': level,
            'score': score,
            'reader_volume': reader_info['reader_volume'],
            'reader_chapter': reader_info['reader_chapter'],
            'reader_title': reader_title,
            'details': '; '.join(checks)
        })
    return results, stats

def main():
    print("=" * 60)
    print("Footprint Data Verification")
    print("=" * 60)
    with open(FOOTPRINT_FILE, 'r', encoding='utf-8') as f:
        fp_data = json.load(f)
    chapters = fp_data['chapters']
    print(f"Loading reader chapters...")
    reader_by_vol = build_reader_index()
    total_reader = sum(len(v) for v in reader_by_vol.values())
    print(f"  Reader chapters loaded: {total_reader} across {len(reader_by_vol)} volumes")

    print(f"Verifying {len(chapters)} footprint chapters...")
    results, stats = verify_chapters(chapters, reader_by_vol)

    output = {
        'meta': {
            'novel': '逍遥小散仙',
            'total_footprint_chapters': len(chapters),
            'verified': stats['verified'],
            'partial': stats['partial'],
            'unverified': stats['unverified'],
            'not_found': stats['not_found'],
            'accuracy_pct': round(stats['verified'] / max(1, len(chapters)) * 100, 1),
        },
        'results': results
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    size = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"Written: {OUTPUT_FILE} ({size:.0f} KB)")
    print(f"\nResults:")
    print(f"  Verified:   {stats['verified']}")
    print(f"  Partial:    {stats['partial']}")
    print(f"  Unverified: {stats['unverified']}")
    print(f"  Not found:  {stats['not_found']}")
    print(f"  Accuracy:   {output['meta']['accuracy_pct']}%")

    print(f"\nSample verified:")
    for r in results[:5]:
        print(f"  [{r['verification']}] Vol{r['volume']} {r['chapter']} -> {r['location']} (score: {r['score']})")

if __name__ == "__main__":
    main()
