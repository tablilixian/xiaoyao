import json
import random
import math

with open('novel_data/footprint_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

regions = data['regions']
locations = data['locations']
location_coords = data['location_coords']

# 为每个区域内的位置生成围绕区域中心的坐标
for region in regions:
    center_x = region['x']
    center_y = region['y']
    region_locations = region['locations']
    count = len(region_locations)
    
    print(f"处理区域: {region['name']}, 位置数: {count}")
    
    # 根据区域大小确定分布半径
    base_radius = 50 + count * 8
    if count > 30:
        base_radius = 120 + count * 5
    
    # 生成围绕中心的坐标
    for i, loc_name in enumerate(region_locations):
        # 使用极坐标分布
        angle = (i / count) * 2 * math.pi + random.uniform(-0.3, 0.3)
        radius = base_radius * (0.4 + random.random() * 0.6)
        
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # 更新位置坐标
        if loc_name in location_coords:
            location_coords[loc_name]['x'] = int(x)
            location_coords[loc_name]['y'] = int(y)
            print(f"  {loc_name}: ({int(x)}, {int(y)})")
        elif loc_name in locations:
            # 如果坐标不存在，创建新的
            location_coords[loc_name] = {'x': int(x), 'y': int(y)}

# 保存更新后的文件
with open('novel_data/footprint_v2.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n位置布局完成！")
