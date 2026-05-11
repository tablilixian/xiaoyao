#!/usr/bin/env python3
"""
足迹地图数据预处理脚本
功能：分析所有 volume_*.json，生成按章节组织的地图路线数据
"""

import json
import os
from pathlib import Path
from collections import OrderedDict

# 配置路径
VOLUMES_DIR = Path("/Users/lilixian/jobs/AI/temp/xiaoyao_project/novel_data/volumes")
OUTPUT_FILE = Path("/Users/lilixian/jobs/AI/temp/xiaoyao_project/novel_data/footprint_map.json")

# 章节顺序映射
CHAPTER_ORDER = {
    "楔子": 0,
    "第一回": 1, "第二回": 2, "第三回": 3, "第四回": 4, "第五回": 5,
    "第六回": 6, "第七回": 7, "第八回": 8, "第九回": 9, "第十回": 10,
    "第十一回": 11, "第十二回": 12
}

def parse_chapter_name(chapter_str):
    """解析章节名称，返回 (卷号, 章节序号, 完整名称)"""
    if "楔子" in chapter_str:
        return (0, 0, chapter_str)
    
    # 匹配 "第X回" 格式
    import re
    match = re.search(r'第(\d+)回', chapter_str)
    if match:
        num = int(match.group(1))
        return (0, num, chapter_str)
    return (0, 999, chapter_str)

def load_all_volumes():
    """加载所有卷的数据"""
    volumes = []
    for i in range(1, 29):  # 28卷
        filename = f"volume_{i}.json"
        filepath = VOLUMES_DIR / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                volumes.append(data)
                print(f"✓ 加载 {filename}: {data.get('meta', {}).get('volume', 'N/A')}")
        else:
            print(f"✗ 缺少 {filename}")
    return volumes

def extract_chapter_data(volumes):
    """按章节顺序提取所有数据"""
    all_chapters = []
    all_locations = {}
    all_events = {}
    
    for volume_data in volumes:
        meta = volume_data.get('meta', {})
        volume_num = meta.get('volume', 0)
        
        # 获取 scenes 和 events
        scenes = volume_data.get('scenes', [])
        events = volume_data.get('events', [])
        locations = volume_data.get('locations', [])
        
        # 收集地点信息
        for loc in locations:
            loc_name = loc.get('name')
            if loc_name and loc_name not in all_locations:
                all_locations[loc_name] = {
                    "name": loc_name,
                    "type": loc.get('type'),
                    "parent": loc.get('parent'),
                    "importance": loc.get('importance', 0),
                    "description": loc.get('description', ''),
                    "appearances": []
                }
        
        # 收集事件信息
        for evt in events:
            evt_id = evt.get('id')
            if evt_id:
                all_events[evt_id] = evt
        
        # 按 scenes 展开章节
        for scene in scenes:
            chapters = scene.get('chapters', [])
            for chapter_name in chapters:
                # 构建章节数据 - 处理 volume_num 可能是字符串或数字
                vol_display = volume_num if isinstance(volume_num, int) else str(volume_num)
                if "卷" not in str(volume_num):
                    vol_display = f"第{vol_display}卷"
                else:
                    vol_display = str(volume_num)
                    
                chapter_entry = {
                    "volume": volume_num,
                    "chapter": chapter_name,
                    "full_name": f"{vol_display} {chapter_name}",
                    "scene_id": scene.get('id'),
                    "location_id": scene.get('location_id'),
                    "location_name": scene.get('location_name'),
                    "characters": scene.get('characters', []),
                    "event_ids": scene.get('events', [])
                }
                all_chapters.append(chapter_entry)
                
                # 更新地点出现记录
                loc_name = scene.get('location_name')
                if loc_name in all_locations:
                    all_locations[loc_name]["appearances"].append({
                        "volume": volume_num,
                        "chapter": chapter_name,
                        "scene_id": scene.get('id')
                    })
    
    # 按卷号和章节顺序排序
    def sort_key(ch):
        vol = ch['volume']
        # 确保 volume 是数字
        if isinstance(vol, str):
            import re
            match = re.search(r'(\d+)', vol)
            vol = int(match.group(1)) if match else 0
        ch_name = ch['chapter']
        # 提取章节数字
        if '楔子' in str(ch_name):
            order = 0
        else:
            import re
            match = re.search(r'第(\d+)回', str(ch_name))
            order = int(match.group(1)) if match else 999
        return (vol, order)
    
    all_chapters.sort(key=sort_key)
    
    return all_chapters, all_locations, all_events

def build_routes(all_chapters):
    """根据章节顺序构建地点间的路线"""
    routes = []
    prev_location = None
    
    for chapter in all_chapters:
        curr_location = chapter.get('location_name')
        if curr_location and prev_location and curr_location != prev_location:
            # 添加路线（去重）
            route_entry = {
                "from": prev_location,
                "to": curr_location,
                "volume": chapter['volume'],
                "chapter": chapter['chapter']
            }
            # 避免重复添加相同路线
            if not any(r['from'] == prev_location and r['to'] == curr_location for r in routes):
                routes.append(route_entry)
        prev_location = curr_location
    
    return routes

def build_chapter_detail(all_chapters, all_events):
    """构建每个章节的详细信息"""
    chapter_details = []
    
    for ch in all_chapters:
        events = []
        for evt_id in ch.get('event_ids', []):
            if evt_id in all_events:
                evt = all_events[evt_id]
                events.append({
                    "id": evt.get('id'),
                    "type": evt.get('type'),
                    "summary": evt.get('summary', ''),
                    "outcome": evt.get('outcome', ''),
                    "participants": evt.get('participants', [])
                })
        
        detail = {
            "volume": ch['volume'],
            "chapter": ch['chapter'],
            "full_name": ch['full_name'],
            "location_name": ch.get('location_name', ''),
            "location_id": ch.get('location_id', ''),
            "characters": ch.get('characters', []),
            "events": events
        }
        chapter_details.append(detail)
    
    return chapter_details

def main():
    print("=" * 50)
    print("足迹地图数据预处理")
    print("=" * 50)
    
    # 1. 加载所有卷
    print("\n[1/4] 加载所有卷数据...")
    volumes = load_all_volumes()
    print(f"\n共加载 {len(volumes)} 卷")
    
    # 2. 提取章节数据
    print("\n[2/4] 按章节提取数据...")
    all_chapters, all_locations, all_events = extract_chapter_data(volumes)
    print(f"  - 章节数: {len(all_chapters)}")
    print(f"  - 地点数: {len(all_locations)}")
    print(f"  - 事件数: {len(all_events)}")
    
    # 3. 构建路线
    print("\n[3/4] 构建地点路线...")
    routes = build_routes(all_chapters)
    print(f"  - 路线数: {len(routes)}")
    
    # 4. 构建章节详情
    print("\n[4/4] 构建章节详情...")
    chapter_details = build_chapter_detail(all_chapters, all_events)
    
    # 5. 组装最终数据
    result = {
        "meta": {
            "novel": "逍遥小散仙",
            "total_volumes": 28,
            "total_chapters": len(all_chapters),
            "total_locations": len(all_locations),
            "total_events": len(all_events),
            "total_routes": len(routes),
            "generated_at": "2025-01-01"
        },
        "locations": all_locations,
        "routes": routes,
        "chapters": chapter_details
    }
    
    # 6. 保存
    print(f"\n[保存] 输出到: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print("✓ 预处理完成!")
    print("=" * 50)
    
    # 输出统计
    print(f"\n📊 数据统计:")
    print(f"   总卷数: {result['meta']['total_volumes']}")
    print(f"   总章节: {result['meta']['total_chapters']}")
    print(f"   总地点: {result['meta']['total_locations']}")
    print(f"   总事件: {result['meta']['total_events']}")
    print(f"   总路线: {result['meta']['total_routes']}")

if __name__ == "__main__":
    main()
