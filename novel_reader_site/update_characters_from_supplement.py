#!/usr/bin/env python3
"""
根据补充资料更新角色数据库
"""

import json
import re

# 读取现有角色数据库
with open('characters_db.json', 'r', encoding='utf-8') as f:
    characters_db = json.load(f)

# 从补充资料中提取的角色详细信息
supplement_data = {
    # 玄教
    '无上圣母': {
        'faction': '玄教',
        'description': '玄教教祖。玄教有两大玄功，一为镇元子的袖里乾坤，一为重元子的如意乾坤，据传皆是无上圣母悟混沌而创。',
        'personality': '神秘莫测',
        'appearance': '未知'
    },
    '重元子': {
        'faction': '玄教',
        'description': '玄教教主。地仙之祖之一。绝顶的双修大家。修为已臻大罗之界。创立玄教。',
        'personality': '威严深沉',
        'appearance': '仙风道骨',
        'cultivation': '功法：如意乾坤',
        'items': '法宝：阴阳鼎'
    },
    '镇元子': {
        'faction': '玄教',
        'description': '重元子大师兄。地仙之祖之一。',
        'cultivation': '功法：袖里乾坤'
    },
    '黎山老母': {
        'faction': '玄教',
        'description': '玄教第三代弟子排行第三。修为已达太乙境界。',
        'cultivation': '经咒：太衡明净经',
        'mount': '坐骑：青鸾'
    },
    '武翩跹': {
        'faction': '玄教/迷渊宫',
        'description': '玄教第三代弟子排行第七。号三绝，原于玄教中武技第一，阵法第一，机关术第一。刑天与黄姖之女。已臻太乙之境。',
        'personality': '绝世强者、深不可测',
        'appearance': '风华绝代',
        'cultivation': '功法：北溟玄数第七境守虚，诛天诀',
        'items': '兵器：聚宝剑；法宝：落宝金钱，过天虹，冰火炼狱，大荒，夜酣香',
        'formation': '阵法：先天无极阵',
        'mount': '坐骑：云水宝车（猼訑）'
    },
    '崔采婷': {
        'faction': '玄教',
        'description': '玄教第三代弟子排行第九。号如意仙娘、白首娘娘。修为已达飞仙境界。小玄之师，执掌先天太幻图镇守梦巢。',
        'personality': '端庄威严、对徒弟要求严格',
        'appearance': '一首白发，容端颜丽',
        'cultivation': '武技：如意五行诸技；法术：如意五行诸法，御剑飞行术，如意五行三大绝顶法诀（五元归宗）',
        'items': '兵器：入梦；法宝：先天太幻图'
    },
    '飞萝': {
        'faction': '玄教',
        'description': '玄教第三代弟子排行第三十三。玄教教主的关门弟子，修为已达飞仙境界，号魅仙。天赋异禀，最擅御甲术及机关术，