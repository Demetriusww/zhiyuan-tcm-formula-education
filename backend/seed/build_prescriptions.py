# -*- coding: utf-8 -*-
"""生成最终种子数据: prescriptions_all.json
合并原有35方 + 新增83方;将 herbs 字符串解析为 herb_names(规范名,关联药材库)
"""
import re, json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prescriptions_extra_a import PRESCRIPTIONS_EXTRA_A
from prescriptions_extra_b import PRESCRIPTIONS_EXTRA_B
from prescriptions_extra_c import PRESCRIPTIONS_EXTRA_C

base = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extracted_frontend_data.json'), encoding='utf-8'))
herbs_all = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'herbs_all.json'), encoding='utf-8'))
std_names = set(herbs_all['herbs'].keys())

ALIAS = {  # 同药异名 → 标准名
    '生地黄': '地黄', '干地黄': '地黄', '生地': '地黄', '鲜生地': '地黄',
    '炙甘草': '甘草', '生甘草': '甘草', '粉甘草': '甘草', '甘草梢': '甘草',
    '胆南星': '天南星', '制南星': '天南星',
    '瓜蒌仁': '瓜蒌', '全瓜蒌': '瓜蒌', '瓜蒌皮': '瓜蒌', '栝楼': '瓜蒌',
    '苦杏仁': '苦杏仁', '光杏仁': '苦杏仁', '杏仁': '苦杏仁', '炒杏仁': '苦杏仁',
    '炮姜': '干姜', '黑姜': '干姜',
    '酸枣仁': '酸枣仁', '炒枣仁': '酸枣仁',
    '当归身': '当归', '当归尾': '当归', '全当归': '当归', '当归头': '当归',
    '熟地': '熟地黄', '大熟地': '熟地黄',
    '杭白芍': '白芍', '生白芍': '白芍', '大白芍': '白芍', '炒白芍': '白芍',
    '生黄芪': '黄芪', '炙黄芪': '黄芪', '绵黄芪': '黄芪', '北芪': '黄芪',
    '人参须': '人参', '白参': '人参', '生晒参': '人参',
    '茯苓块': '茯苓', '白茯苓': '茯苓', '云茯苓': '茯苓', '茯神': '茯苓',
    '土炒白术': '白术', '焦白术': '白术', '生白术': '白术',
    '川贝': '川贝母', '浙贝': '浙贝母',
    '大麦冬': '麦冬', '寸冬': '麦冬', '麦门冬': '麦冬',
    '天门冬': '天冬',
    '淮山药': '山药', '怀山药': '山药', '薯蓣': '山药',
    '山萸肉': '山茱萸', '枣皮': '山茱萸',
    '枸杞': '枸杞子', '甘杞子': '枸杞子',
    '元参': '玄参',
    '粉丹皮': '牡丹皮', '丹皮': '牡丹皮',
    '川牛膝': '牛膝', '怀牛膝': '牛膝',
    '制附子': '附子', '熟附子': '附子', '黑顺片': '附子', '炮附子': '附子',
    '桂枝尖': '桂枝', '嫩桂枝': '桂枝',
    '肉桂心': '肉桂', '官桂': '肉桂', '油肉桂': '肉桂',
    '炒枳壳': '枳壳', '江枳壳': '枳壳',
    '广陈皮': '陈皮', '橘皮': '陈皮', '新会皮': '陈皮',
    '广木香': '木香', '云木香': '木香', '煨木香': '木香',
    '制香附': '香附', '醋香附': '香附',
    '广郁金': '郁金', '川郁金': '郁金',
    '紫丹参': '丹参', '炒丹参': '丹参',
    '生牡蛎': '牡蛎', '煅牡蛎': '牡蛎',
    '生龙骨': '龙骨', '煅龙骨': '龙骨',
    '忍冬花': '金银花', '双花': '金银花',
    '连翘壳': '连翘', '青连翘': '连翘',
    '麻黄绒': '麻黄', '净麻黄': '麻黄',
    '北细辛': '细辛',
    '生姜': '生姜', '煨生姜': '生姜', '鲜生姜': '生姜',
    '红枣': '大枣', '黑枣': '大枣',
    '法半夏': '半夏', '姜半夏': '半夏', '清半夏': '半夏', '制半夏': '半夏',
    '北防风': '防风',
    '荆芥穗': '荆芥', '荆芥炭': '荆芥',
    '苦桔梗': '桔梗',
    '枯黄芩': '黄芩', '条芩': '黄芩',
    '川连': '黄连', '雅连': '黄连',
    '川黄柏': '黄柏',
    '山栀': '栀子', '炒栀子': '栀子',
    '肥知母': '知母',
    '生石膏': '石膏', '煅石膏': '石膏',
    '淡竹叶': '竹叶',
    '淡竹茹': '竹茹', '姜竹茹': '竹茹',
    '大米': '粳米',
    '生大黄': '大黄', '酒大黄': '大黄', '熟大黄': '大黄', '制大黄': '大黄',
    '玄明粉': '芒硝', '朴硝': '芒硝',
    '炒枳实': '枳实', '江枳实': '枳实',
    '川朴': '厚朴', '制厚朴': '厚朴', '姜厚朴': '厚朴',
    '粉猪苓': '猪苓',
    '建泽泻': '泽泻',
    '飞滑石': '滑石', '六一散': '滑石',
    '车前仁': '车前子', '炒车前子': '车前子',
    '关木通': '木通', '川木通': '木通',
    '绵茵陈': '茵陈', '茵陈蒿': '茵陈',
    '苡仁': '薏苡仁', '生薏仁': '薏苡仁', '炒薏仁': '薏苡仁', '薏米': '薏苡仁',
    '过路黄': '金钱草',
    '茅苍术': '苍术', '炒苍术': '苍术',
    '香白芷': '白芷', '杭白芷': '白芷',
    '土藿香': '广藿香',
    '槟榔皮': '大腹皮',
    '化橘红': '橘红',
    '苏薄荷': '薄荷',
    '大力子': '牛蒡子', '炒牛蒡子': '牛蒡子',
    '冬桑叶': '桑叶', '霜桑叶': '桑叶',
    '杭菊花': '菊花', '白菊花': '菊花', '甘菊花': '菊花',
    '粉葛根': '葛根', '煨葛根': '葛根',
    '绿升麻': '升麻',
    '北柴胡': '柴胡', '醋柴胡': '柴胡',
    '川羌活': '羌活',
    '大川芎': '川芎',
    '淡吴萸': '吴茱萸', '吴萸': '吴茱萸',
    '北五味': '五味子',
    '桂圆肉': '龙眼肉',
    '炙远志': '远志',
    '光桃仁': '桃仁', '炒桃仁': '桃仁',
    '藏红花': '红花',
    '鲜石斛': '石斛', '霍山石斛': '石斛', '金石斛': '石斛',
    '沙参': '北沙参', '南沙参': '北沙参',
    '驴皮胶': '阿胶',
    '鹿胶': '鹿角胶',
    '龟板胶': '龟甲胶',
    '川杜仲': '杜仲', '炒杜仲': '杜仲',
    '盐菟丝子': '菟丝子',
    '广地龙': '地龙', '蚯蚓': '地龙',
    '明天麻': '天麻',
    '牛角': '水牛角',
    '六神曲': '神曲', '焦神曲': '神曲',
    '焦山楂': '山楂', '炒山楂': '山楂', '生山楂': '山楂', '南山楂': '山楂',
    '萝卜子': '莱菔子', '炒莱菔子': '莱菔子',
    '内金': '鸡内金',
    '花粉': '天花粉', '瓜蒌根': '天花粉',
    '菖蒲': '石菖蒲',
    '缩砂仁': '砂仁', '春砂仁': '砂仁', '砂米': '砂仁',
    '辰砂': '朱砂', '飞朱砂': '朱砂',
    '苏叶': '紫苏', '紫苏叶': '紫苏',
    '桂枝': '桂枝', '白芍': '白芍', '当归': '当归', '人参': '人参',
    '白术': '白术', '茯苓': '茯苓', '甘草': '甘草', '朱砂': '朱砂',
    '麻黄': '麻黄', '紫苏': '紫苏', '荆芥': '荆芥', '防风': '防风',
    '金银花': '金银花', '连翘': '连翘', '板蓝根': '板蓝根', '石膏': '石膏',
    '栀子': '栀子', '半夏': '半夏', '附子': '附子', '干姜': '干姜',
    '肉桂': '肉桂', '熟地黄': '熟地黄', '饴糖': '饴糖', '大枣': '大枣',
    '生姜': '生姜', '肉豆蔻': '肉豆蔻', '补骨脂': '补骨脂', '麻黄根': '麻黄根',
    '石菖蒲': '石菖蒲', '砂仁': '砂仁', '天花粉': '天花粉', '鸡内金': '鸡内金',
    '乌梅': '乌梅', '龙齿': '龙骨', '远志': '远志', '木香': '木香',
    # 古籍/原方剂名称中的别名补全
    '苇根': '芦根', '犀角': '水牛角', '竹叶心': '竹叶', '龙胆草': '龙胆',
    '生甘草梢': '甘草', '甘草梢': '甘草', '苦杏仁': '苦杏仁',
    '麻仁': '火麻仁', '火麻仁': '火麻仁', '藿香': '广藿香', '广藿香': '广藿香',
}

def parse_herbs(hstr):
    """解析 '人参9g、白术9g' → 药材规范名列表"""
    names = []
    for part in re.split(r'[、，,;；]', hstr):
        part = part.strip()
        if not part:
            continue
        m = re.match(r'^(.+?)([\d.]+(?:～|~|－|-)?[\d.]*)?(?:g|克|枚|片|钱|两|个|升|分|粒|条|块|匙)$', part)
        name = m.group(1).strip() if m else part
        std = ALIAS.get(name, name)
        names.append(std)
    return names

def check(herb_names):
    bad = [n for n in herb_names if n not in std_names]
    return bad

# 组装所有方剂
from prescription_categories import CATEGORY as RX_CATEGORY
result = []
sid = 1
dup_names = set()
for p in base['prescriptions']:
    herb_names = [ALIAS.get(n, n) for n in p['herb_names']]
    result.append({'id': sid, 'name': p['name'], 'source': p['source'],
                   'functions': p['functions'], 'indications': p['indications'],
                   'category': RX_CATEGORY.get(p['name']),
                   'herbs_raw': p.get('herbs_raw', ''), 'herb_names': herb_names})
    dup_names.add(p['name'])
    sid += 1

for p in PRESCRIPTIONS_EXTRA_A + PRESCRIPTIONS_EXTRA_B + PRESCRIPTIONS_EXTRA_C:
    if p['name'] in dup_names:
        continue  # 去重
    dup_names.add(p['name'])
    herb_names = parse_herbs(p['herbs'])
    bad = check(herb_names)
    if bad:
        print(f"!! {p['name']} 缺药材: {bad}")
    result.append({'id': sid, 'name': p['name'], 'source': p['source'],
                   'functions': p['functions'], 'indications': p['indications'],
                   'category': RX_CATEGORY.get(p['name']),
                   'herbs_raw': p['herbs'], 'herb_names': herb_names})
    sid += 1

print(f"最终方剂数: {len(result)}")
# 统计关联完整性
total_links = sum(len(p['herb_names']) for p in result)
uniq_herbs_used = set()
for p in result:
    uniq_herbs_used.update(p['herb_names'])
print(f"方剂-药材关联总数: {total_links}")
print(f"方剂实际用到的药材种数: {len(uniq_herbs_used)} / {len(std_names)}")

json.dump({'prescriptions': result, 'herbs': herbs_all['herbs']},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prescriptions_all.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print("已生成 backend/seed/prescriptions_all.json")
