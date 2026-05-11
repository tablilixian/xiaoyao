#!/usr/bin/env python3
"""构建角色数据库"""

import json
import re
from collections import defaultdict

# 读取知识库数据
with open('../novel_data/knowledge/knowledge_full.json', 'r', encoding='utf-8') as f:
    knowledge = json.load(f)

# 读取角色索引
with open('../novel_data/index/characters.json', 'r', encoding='utf-8') as f:
    core_chars = json.load(f)

with open('../novel_data/index/characters_minor.json', 'r', encoding='utf-8') as f:
    minor_chars = json.load(f)

# 构建角色数据库
characters_db = {}

# 处理核心角色
for name, data in core_chars.items():
    characters_db[name] = {
        'name': name,
        'type': 'core',
        'gender': data.get('gender', '未知'),
        'appearances': data.get('volumes', []),
        'aliases': data.get('aliases', []),
        'faction': data.get('faction', ''),
        'description': '',
        'personality': '',
        'appearance': '',
        'image': None,
        'relationships': []
    }

# 处理次要角色
for name, data in minor_chars.items():
    if name not in characters_db:
        characters_db[name] = {
            'name': name,
            'type': 'minor',
            'gender': data.get('gender', '未知'),
            'appearances': data.get('volumes', []),
            'aliases': data.get('aliases', []),
            'faction': data.get('faction', ''),
            'description': '',
            'personality': '',
            'appearance': '',
            'image': None,
            'relationships': []
        }

# 从关系数据中提取更多信息
for rel in knowledge.get('relationships', []):
    source = rel.get('source', '')
    target = rel.get('target', '')
    rel_type = rel.get('type', '')
    desc = rel.get('description', '')
    
    for name in [source, target]:
        if name in characters_db:
            characters_db[name]['relationships'].append({
                'with': target if name == source else source,
                'type': rel_type,
                'description': desc
            })

# 角色-图片映射（根据用户提供的准确信息）
# character_001 ~ character_012 是角色插图
character_image_map = {
    # 主角 - 暂无图像，但有4个物品是他的 back 1 2 6 8
    '崔小玄': None,
    
    # 角色插图映射
    '程水若': 'images/character_001-1.jpg',   # 三师姐
    '飞萝': 'images/character_002.jpg',        # 三十三师叔
    '崔采婷': 'images/character_003.jpg',      # 师父
    '婀妍': 'images/character_004.jpg',        # 妖界少谷主
    '夏小婉': 'images/character_005.jpg',      # 四师姐
    '李梦棠': 'images/character_006.jpg',      # 二师姐
    '夭夭': 'images/character_007.jpg',        # 
    '五姐姐': 'images/character_008.jpg',      # 蝎子精
    '紫儿': 'images/character_009.jpg',        # 蝴蝶精（与碧儿共用）
    '碧儿': 'images/character_009.jpg',        # 蝴蝶精（与紫儿共用）
    '武翩跹': 'images/character_010.jpg',      # 天妃娘娘
    '程雪若': 'images/character_011.jpg',      # 
    '皇后': 'images/character_012.jpg',        # 
    
    # 其他可能有插图的角色（待确认）
    '雪涵': 'images/character_013.jpg',        # 大师姐（推测）
}

# 关系类型中文映射
RELATION_TYPE_CN = {
    'ally': '盟友',
    'ambiguous': '暧昧',
    'crush': '暗恋',
    'descendant': '后裔',
    'employer': '雇佣',
    'enemy': '敌人',
    'ex_lover': '前任恋人',
    'friend': '朋友',
    'guardian': '守护者',
    'junior': '晚辈',
    'kinship': '亲属',
    'lover': '恋人',
    'manipulator': '操纵者',
    'master': '师父',
    'nemesis': '宿敌',
    'parent': '父母',
    'protector': '保护者',
    'rival': '对手',
    'savior': '恩人',
    'senior': '前辈',
    'sibling': '兄弟姐妹',
    'spouse': '配偶',
    'subordinate': '下属',
    'superior': '上级',
    'sworn': '结拜',
    'child': '子女',
    'disciple': '徒弟',
    'creditor': '恩人',
}

# 将关系类型翻译为中文
for name, char in characters_db.items():
    for rel in char.get('relationships', []):
        rel['type_cn'] = RELATION_TYPE_CN.get(rel['type'], rel['type'])

# 为有图片的角色设置头像
for name, img_path in character_image_map.items():
    if name in characters_db:
        characters_db[name]['image'] = img_path

# 手动添加一些第一卷重要角色的详细信息
character_details = {
    '崔小玄': {
        'description': '本书主角，玄教如意仙娘崔采婷的末徒儿，质属火。醉心于异宝新术的发明创造，性格活泼跳脱，经常惹出各种麻烦。',
        'personality': '活泼跳脱、好奇心强、发明创造狂、有点好色但心地善良',
        'appearance': '少年模样，穿着无袖紧身衫，臂上绕着数圈醒目的乌赤细链',
    },
    '程水若': {
        'description': '崔采婷门下三弟子，家世非凡，乃当今皇朝奉天侯程兆琦之女。体质属水，悟性最好，学东西最快。',
        'personality': '性情毛躁、有点小脾气、但心地善良、容易被哄',
        'appearance': '身着绿衫、娇俏秀丽，生着一双水灵灵的大眼睛',
    },
    '夏小婉': {
        'description': '崔采婷门下四弟子，属性为土，最是踏实勤奋，根骨亦佳，十分痴迷召唤术。',
        'personality': '踏实勤奋、性格温和、痴迷召唤术',
        'appearance': '瓜子脸上生着一双水灵灵的大眼睛，模样十分甜美',
    },
    '雪涵': {
        'description': '崔采婷门下大弟子，质合五行之金，入门最早，根基最好，真气最强、武技最高。已出山，侍于天道阁刑飞麾下。',
        'personality': '沉稳大气、威仪隐蕴、实力强大',
        'appearance': '年正双十，长挑身材，削肩瘦腰，模样有点弱不禁风，但眉目之间却似隐蕴威仪',
    },
    '李梦棠': {
        'description': '崔采婷门下二弟子，木行属性极佳，灵力最强，对各种治疗术颇有心得，喜欢读书阅典，有过目不忘的本领。',
        'personality': '温柔体贴、博学多才、过目不忘',
        'appearance': '腮凝新桃，肤腻鹅脂，一头过腰及股的如瀑长发，宛若天女仙妃',
    },
    '崔采婷': {
        'description': '玄教如意仙娘，崔小玄的师父。一首白发，容端颜丽。',
        'personality': '端庄威严、对徒弟要求严格',
        'appearance': '一首白发，容端颜丽',
    },
    '黎山老母': {
        'description': '玄教长辈，崔采婷的师姐。',
        'personality': '慈祥温和、见多识广',
        'appearance': '慈祥老者形象',
    },
    '飞萝': {
        'description': '玄教三十三师叔，大名鼎鼎的御甲师和机关师。',
        'personality': '神秘莫测、机关术高超',
        'appearance': '美丽神秘的女子',
    },
    '程兆琦': {
        'description': '当今皇朝奉天侯，程水若的父亲。',
        'personality': '位高权重',
        'appearance': '侯爷形象',
    }
}

# 合并详细信息
for name, details in character_details.items():
    if name in characters_db:
        characters_db[name].update(details)

# 保存角色数据库
with open('characters_db.json', 'w', encoding='utf-8') as f:
    json.dump(characters_db, f, ensure_ascii=False, indent=2)

print(f"角色数据库构建完成！")
print(f"共 {len(characters_db)} 个角色")
print(f"核心角色: {sum(1 for c in characters_db.values() if c['type'] == 'core')} 个")
print(f"次要角色: {sum(1 for c in characters_db.values() if c['type'] == 'minor')} 个")

# 显示前10个角色
print("\n前10个角色:")
for i, (name, data) in enumerate(list(characters_db.items())[:10]):
    print(f"  {i+1}. {name} ({data['type']}) - {len(data.get('relationships', []))} 个关系")
