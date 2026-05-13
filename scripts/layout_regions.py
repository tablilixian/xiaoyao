import json
import math

with open('novel_data/footprint_v2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

regions = data['regions']

# 仙侠风配色方案
xianxia_colors = {
    'primary': ['#5a9a8f', '#6b8cae', '#d4a574', '#9a6ad4', '#c75b5b'],
    'secondary': ['#7cb87c', '#8eb5d0', '#b8a3d4', '#a87a6a', '#7a6a9a'],
    'accent': ['#d4878a', '#5a9a8f', '#6b8cae', '#d4b87c', '#8a6a7a']
}

# 根据大小分级
large_regions = [r for r in regions if r['location_count'] >= 30]
medium_regions = [r for r in regions if 5 <= r['location_count'] < 30]
small_regions = [r for r in regions if r['location_count'] < 5]

print(f"大区域: {len(large_regions)} | 中等区域: {len(medium_regions)} | 小区域: {len(small_regions)}")

# 地图尺寸 - 扩大以便更好地分布
map_width = 2000
map_height = 1400
center_x = map_width // 2
center_y = map_height // 2

# 大区域布局 - 放在中心区域，呈菱形分布
large_positions = [
    (center_x, center_y - 150),      # 上方
    (center_x - 200, center_y + 100), # 左下方
    (center_x + 200, center_y + 100), # 右下方
    (center_x - 150, center_y - 50)   # 左上方
]

for i, region in enumerate(large_regions):
    if i < len(large_positions):
        region['x'] = large_positions[i][0]
        region['y'] = large_positions[i][1]
    region['color'] = xianxia_colors['primary'][i % len(xianxia_colors['primary'])]
    print(f"大区域 {region['name']}: ({region['x']}, {region['y']})")

# 中等区域布局 - 放在次中心区域
medium_positions = [
    (center_x - 400, center_y - 200),  # 左上
    (center_x + 400, center_y - 200),  # 右上
    (center_x - 350, center_y + 250),  # 左下
    (center_x + 350, center_y + 250),  # 右下
    (center_x, center_y + 350),        # 正下方
    (center_x - 500, center_y + 100)   # 左中
]

for i, region in enumerate(medium_regions):
    if i < len(medium_positions):
        region['x'] = medium_positions[i][0]
        region['y'] = medium_positions[i][1]
    region['color'] = xianxia_colors['secondary'][i % len(xianxia_colors['secondary'])]
    print(f"中等区域 {region['name']}: ({region['x']}, {region['y']})")

# 小区域布局 - 放在边缘
edge_positions = [
    (center_x + 600, center_y - 100),  # 右中
    (center_x - 600, center_y - 100),  # 左中
    (center_x + 550, center_y + 200),  # 右下偏中
    (center_x - 550, center_y + 200),  # 左下偏中
    (center_x + 450, center_y - 350),  # 右上
    (center_x - 450, center_y - 350),  # 左上
    (center_x + 650, center_y + 400),  # 最右下
    (center_x - 650, center_y + 400)   # 最左下
]

for i, region in enumerate(small_regions):
    if i < len(edge_positions):
        region['x'] = edge_positions[i][0]
        region['y'] = edge_positions[i][1]
    region['color'] = xianxia_colors['accent'][i % len(xianxia_colors['accent'])]
    print(f"小区域 {region['name']}: ({region['x']}, {region['y']})")

# 更新地图尺寸
data['meta']['map_width'] = map_width
data['meta']['map_height'] = map_height

# 保存更新后的文件
with open('novel_data/footprint_v2.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n布局完成！地图尺寸: {} x {}".format(map_width, map_height))
