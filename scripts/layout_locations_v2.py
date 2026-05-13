import json
import math
import random

with open('novel_data/footprint_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

regions = data['regions']
locations = data['locations']
location_coords = data['location_coords']

# 力导向布局算法，避免位置重叠
def force_directed_layout(center_x, center_y, positions, iterations=100):
    """
    使用力导向算法优化位置分布
    positions: [(name, importance), ...]
    """
    n = len(positions)
    if n == 0:
        return {}
    
    # 初始化位置 - 圆形分布
    coords = {}
    base_radius = 80 + n * 12
    if n > 30:
        base_radius = 150 + n * 8
    
    for i, (name, importance) in enumerate(positions):
        angle = (i / n) * 2 * math.pi + random.uniform(-0.2, 0.2)
        # 重要度高的位置放在外围，便于显示标签
        radius_factor = 0.5 + (importance / 10) * 0.5
        radius = base_radius * radius_factor * (0.7 + random.random() * 0.3)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        coords[name] = {'x': x, 'y': y, 'vx': 0, 'vy': 0, 'importance': importance}
    
    # 力导向迭代
    for _ in range(iterations):
        # 计算斥力（节点间相互排斥）
        for name1 in coords:
            for name2 in coords:
                if name1 >= name2:
                    continue
                
                n1 = coords[name1]
                n2 = coords[name2]
                dx = n1['x'] - n2['x']
                dy = n1['y'] - n2['y']
                dist = math.sqrt(dx * dx + dy * dy)
                
                # 最小距离根据重要度调整
                min_dist = 60 + (n1['importance'] + n2['importance']) * 3
                
                if dist < min_dist and dist > 0.1:
                    # 斥力
                    force = (min_dist - dist) / dist * 2
                    fx = dx / dist * force
                    fy = dy / dist * force
                    
                    n1['vx'] += fx
                    n1['vy'] += fy
                    n2['vx'] -= fx
                    n2['vy'] -= fy
        
        # 计算引力（向中心吸引）
        for name in coords:
            n = coords[name]
            dx = center_x - n['x']
            dy = center_y - n['y']
            dist = math.sqrt(dx * dx + dy * dy)
            
            # 引力系数
            k = 0.05
            n['vx'] += dx * k
            n['vy'] += dy * k
        
        # 更新位置
        for name in coords:
            n = coords[name]
            # 阻尼
            n['vx'] *= 0.8
            n['vy'] *= 0.8
            
            n['x'] += n['vx']
            n['y'] += n['vy']
            
            # 限制在区域内
            max_radius = base_radius * 1.5
            dx = n['x'] - center_x
            dy = n['y'] - center_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > max_radius:
                n['x'] = center_x + dx / dist * max_radius
                n['y'] = center_y + dy / dist * max_radius
    
    return {name: {'x': int(coords[name]['x']), 'y': int(coords[name]['y'])} 
            for name in coords}

# 为每个区域布局位置
for region in regions:
    center_x = region['x']
    center_y = region['y']
    region_locations = region['locations']
    
    print(f"处理区域: {region['name']}, 位置数: {len(region_locations)}")
    
    # 收集位置信息
    positions = []
    for loc_name in region_locations:
        loc_data = locations.get(loc_name, {})
        importance = loc_data.get('importance', 1)
        positions.append((loc_name, importance))
    
    # 使用力导向算法布局
    new_coords = force_directed_layout(center_x, center_y, positions)
    
    # 更新坐标
    for name, coord in new_coords.items():
        if name in location_coords:
            location_coords[name]['x'] = coord['x']
            location_coords[name]['y'] = coord['y']
        else:
            location_coords[name] = coord

# 保存更新后的文件
with open('novel_data/footprint_v2.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n位置布局优化完成！使用力导向算法避免重叠")
