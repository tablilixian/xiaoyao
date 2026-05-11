#!/usr/bin/env python3
import json, re, math, os
from collections import defaultdict, OrderedDict

INPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'novel_data', 'footprint_map.json')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'novel_data', 'footprint_v2.json')
MAP_WIDTH, MAP_HEIGHT = 1200, 800

REGION_CENTERS = OrderedDict([
    ("千翠山",       (180, 180, "#5a9a8f")),
    ("大泽平原",     (450, 330, "#d4a574")),
    ("巨竹谷",       (700, 280, "#6b8cae")),
    ("七绝界",       (850, 150, "#c75b5b")),
    ("葫芦镇",       (550, 200, "#9a6ad4")),
    ("迷林",         (580, 210, "#7cb87c")),
    ("快活岛/妖界", (350, 480, "#d4878a")),
    ("玉京/迷楼",   (600, 100, "#d4b87c")),
    ("虚照境",       (700, 440, "#8eb5d0")),
    ("辟邪宫",       (820, 380, "#b8a3d4")),
    ("常羊山秘境",  (280, 520, "#6a9a8a")),
    ("南海/海外",    (650, 500, "#a87a6a")),
    ("天庭/天界",    (450, 60,  "#7a6a9a")),
    ("灵山/西天",    (300, 60,  "#9a7a6a")),
    ("冥界/黑焰岛", (500, 580, "#8a6a7a")),
])

CN_NUM = {'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
    '十一':11,'十二':12,'十三':13,'十四':14,'十五':15,'十六':16,'十七':17,'十八':18,'十九':19,'二十':20,
    '二十一':21,'二十二':22,'二十三':23,'二十四':24,'二十五':25,'二十六':26,'二十七':27,'二十八':28}

def extract_volume_number(vol_str):
    s = str(vol_str)
    m = re.search(r'\b(\d+)\b', s)
    if m: return int(m.group(1))
    m = re.search(r'[第卷]?\s*([一二三四五六七八九十]+)\s*[卷]?', s)
    if m and m.group(1) in CN_NUM: return CN_NUM[m.group(1)]
    m = re.search(r'(\d+)', s)
    if m: return int(m.group(1))
    return 0

def extract_chapter_number(ch_str):
    s = str(ch_str).strip()
    if '楔子' in s: return 0
    m = re.search(r'第(\d+)回', s)
    if m: return int(m.group(1))
    m = re.search(r'第([一二三四五六七八九十]+)回', s)
    if m and m.group(1) in CN_NUM: return CN_NUM[m.group(1)]
    return 999

def is_chapter_fragment(ch_str):
    s = str(ch_str).strip()
    if s in ('楔子',): return False
    if re.match(r'^(第[一二三四五六七八九十\d]+回)', s): return False
    if len(s) > 2: return False
    if s in ('第','卷','回'): return True
    if re.match(r'^[一二三四五六七八九十]$', s): return True
    return False

def clean_chapters(chapters):
    fragments_by_loc = []
    current_group = []
    prev_loc = None
    for ch in chapters:
        chap_str = str(ch.get('chapter', ''))
        loc = ch.get('location_name', '')
        if is_chapter_fragment(chap_str):
            if loc != prev_loc and current_group:
                fragments_by_loc.append((prev_loc, list(current_group)))
                current_group = []
            current_group.append(ch)
            prev_loc = loc
        else:
            if current_group:
                fragments_by_loc.append((prev_loc, list(current_group)))
                current_group = []
            prev_loc = None
    if current_group:
        fragments_by_loc.append((prev_loc, list(current_group)))

    result = []
    for ch in chapters:
        ch_str = str(ch.get('chapter', ''))
        if not is_chapter_fragment(ch_str) and ch_str.strip() not in ('', '-'):
            result.append(dict(ch))

    for loc, frags in fragments_by_loc:
        raw = ''.join(str(f.get('chapter', '')) for f in frags)
        pattern = re.findall(r'(第[一二三四五六七八九十\d]+卷第[一二三四五六七八九十\d]+回)', raw)
        if not pattern:
            vol_m = re.search(r'第([一二三四五六七八九十\d]+)卷', raw)
            chap_m = re.search(r'第([一二三四五六七八九十\d]+)回', raw)
            if vol_m and chap_m:
                full = f"第{vol_m.group(1)}卷第{chap_m.group(1)}回"
                pattern = [full]
        if not pattern:
            continue
        for i, full_chapter in enumerate(pattern):
            base = dict(frags[0])
            base['chapter'] = full_chapter
            vol_m = re.search(r'第([一二三四五六七八九十\d]+)卷', full_chapter)
            if vol_m:
                vn = CN_NUM.get(vol_m.group(1), vol_m.group(1))
                base['volume'] = int(vn) if str(vn).isdigit() else 0
            base['full_name'] = full_chapter
            base['_fragment_merged'] = True
            result.append(base)

    def sort_key(ch):
        v = ch.get('volume', 0) if isinstance(ch.get('volume', 0), (int, float)) else extract_volume_number(str(ch.get('volume', '')))
        cn = ch.get('chapter', '')
        if '楔子' in cn: c = 0
        else:
            m = re.search(r'第(\d+)回', cn)
            c = int(m.group(1)) if m else 999
        return (v, c)

    result.sort(key=sort_key)
    return result

def find_region(name, parent_name, loc_type, all_locations, depth=0):
    if depth > 10: return None
    s = str(name)
    p = str(parent_name) if parent_name else None
    for rk in REGION_CENTERS:
        if rk == s or (p and rk == p): return rk
        if '/' in rk:
            for alias in rk.split('/'):
                if s == alias or (p and p == alias): return rk
    if p and p in all_locations:
        pl = all_locations[p]
        return find_region(p, pl.get('parent'), pl.get('type'), all_locations, depth + 1)
    type_map = {'天界':'天庭/天界','天庭':'天庭/天界','佛门':'灵山/西天','佛教':'灵山/西天',
                '仙境':'天庭/天界','妖界':'快活岛/妖界','魔域':'七绝界','冥界':'冥界/黑焰岛'}
    for t, r in type_map.items():
        if loc_type and t in str(loc_type): return r
    return None

def assign_coordinates(locations):
    children_of = defaultdict(list)
    for name, loc in locations.items():
        parent = loc.get('parent')
        if parent:
            children_of[parent].append(name)
        else:
            children_of[None].append(name)
    coords = {}
    location_region = {}
    region_used = defaultdict(int)
    for name, loc in locations.items():
        region = find_region(name, loc.get('parent'), loc.get('type'), locations)
        if region:
            location_region[name] = region

    def get_region_center(name):
        region = location_region.get(name)
        if region and region in REGION_CENTERS:
            return REGION_CENTERS[region][:2]
        return (MAP_WIDTH - 100, MAP_HEIGHT - 100)

    roots_candidates = []
    for name in locations:
        parent = locations[name].get('parent')
        if not parent or parent not in locations:
            roots_candidates.append(name)
    for i, name in enumerate(sorted(roots_candidates)):
        cx, cy = get_region_center(name)
        region = location_region.get(name)
        count = region_used[region] if region else 0
        ox = (count % 4 - 1.5) * 35
        oy = (count // 4) * 35
        if region:
            region_used[region] += 1
        coords[name] = (cx + ox, cy + oy)

    for level in range(5):
        for name, loc in locations.items():
            if name in coords: continue
            parent = loc.get('parent')
            if parent and parent in coords:
                px, py = coords[parent]
                siblings = [n for n in children_of.get(parent, []) if n not in coords]
                all_siblings = children_of.get(parent, [])
                idx = all_siblings.index(name) if name in all_siblings else 0
                total = max(len(all_siblings), 1)
                radius = max(35, 70 - level * 12)
                angle = (2 * math.pi * idx / total) - math.pi / 2
                x = max(25, min(MAP_WIDTH - 25, px + radius * math.cos(angle)))
                y = max(25, min(MAP_HEIGHT - 25, py + radius * math.sin(angle)))
                coords[name] = (round(x, 1), round(y, 1))

    if len(coords) < len(locations):
        for name in locations:
            if name not in coords:
                cx, cy = get_region_center(name)
                coords[name] = (cx + random_offset(name), cy + random_offset(name))
    return coords

def random_offset(name):
    h = hash(name) % 200 - 100
    return h * 1.0

def main():
    print("=" * 60)
    print("Footprint V2 Data Preparation")
    print("=" * 60)
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        raw = json.load(f)
    print(f"Loaded: {raw['meta']['total_locations']} locations, {len(raw['chapters'])} chapters")

    print("\n[1/3] Cleaning chapters...")
    fixed = clean_chapters(raw['chapters'])
    for ch in fixed:
        v = ch.get('volume')
        if not isinstance(v, int):
            ch['volume'] = extract_volume_number(str(v))
        vn = ch.get('volume', 0)
        ct = ch.get('chapter', '')
        if vn and ct:
            if ct.startswith(f'第{vn}卷'):
                ch['full_name'] = ct
            else:
                ch['full_name'] = f"第{vn}卷 {ct}"
    print(f"  {len(raw['chapters'])} -> {len(fixed)} chapters")

    print("\n[2/3] Assigning coordinates...")
    locations = raw['locations']
    coords = assign_coordinates(locations)
    assigned = len(coords)
    unassigned = [n for n in locations if n not in coords]
    print(f"  {assigned}/{len(locations)} locations assigned")
    if unassigned:
        print(f"  Unassigned: {len(unassigned)}")

    region_map = defaultdict(list)
    for name in locations:
        r = find_region(name, locations[name].get('parent'), locations[name].get('type'), locations)
        if r: region_map[r].append(name)

    print("\n[3/3] Writing output...")
    location_coords = {}
    for name in locations:
        if name in coords:
            location_coords[name] = {"x": coords[name][0], "y": coords[name][1]}
        else:
            location_coords[name] = {"x": MAP_WIDTH - 50, "y": MAP_HEIGHT - 50}

    regions = []
    for rn in REGION_CENTERS:
        cx, cy, color = REGION_CENTERS[rn]
        locs = region_map.get(rn, [])
        regions.append({"id": rn, "name": rn, "x": cx, "y": cy, "color": color,
                        "locations": locs, "location_count": len(locs)})

    chapter_lookup = {}
    for idx, ch in enumerate(fixed):
        key = f"{ch.get('volume',0)}_{ch.get('chapter','')}"
        chapter_lookup[key] = {
            "index": idx,
            "reader_volume": ch.get('volume', 0),
            "reader_chapter": extract_chapter_number(ch.get('chapter', '')),
        }

    output = {
        "meta": {
            "novel": raw['meta'].get('novel', ''),
            "total_volumes": raw['meta'].get('total_volumes', 0),
            "total_chapters": len(fixed),
            "total_locations": len(locations),
            "total_routes": len(raw['routes']),
            "total_regions": len(regions),
            "generated_at": "2025-05-11",
            "map_width": MAP_WIDTH,
            "map_height": MAP_HEIGHT
        },
        "regions": regions,
        "locations": {},
        "location_coords": location_coords,
        "chapters": fixed,
        "routes": raw['routes'],
        "chapter_lookup": chapter_lookup
    }
    for name, loc in locations.items():
        entry = dict(loc)
        if name in coords:
            entry['x'] = coords[name][0]
            entry['y'] = coords[name][1]
        entry['region'] = find_region(name, loc.get('parent'), loc.get('type'), locations)
        output['locations'][name] = entry

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    size = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"  Written: {OUTPUT_FILE} ({size:.0f} KB)")
    print(f"\nStats:")
    print(f"  Chapters: {output['meta']['total_chapters']}")
    print(f"  Locations: {output['meta']['total_locations']}")
    print(f"  Regions: {output['meta']['total_regions']}")
    print(f"  Routes: {output['meta']['total_routes']}")
    for r in regions:
        if r['location_count'] > 0:
            print(f"    {r['name']}: {r['location_count']} locs ({r['x']},{r['y']})")

if __name__ == "__main__":
    main()
