# -*- coding: utf-8 -*-
import re, json, io, sys
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

d = json.load(open('backend/seed/extracted_frontend_data.json', encoding='utf-8'))
herbs = set(d['herbs'].keys())          # 现有药材名(key 即中文名)
print("现有药材:", len(herbs))

# 别名归一化(含炮制前缀处理)
PREFIX = ['炙', '制', '生', '炒', '煅', '醋', '酒', '盐', '蜜', '姜', '焦', '麸', '水', '鲜', '干']
ALIAS = {
    # 炮制前缀别名
    '生甘草': '甘草', '炙甘草': '甘草', '粉甘草': '甘草', '甘草梢': '甘草',
    '生地黄': '地黄', '干地黄': '地黄', '生地': '地黄', '熟地': '熟地黄',
    '苦桔梗': '桔梗', '半夏曲': '半夏', '白茯苓': '茯苓', '茯神': '茯苓', '云苓': '茯苓',
    '山萸肉': '山茱萸', '淮山药': '山药', '怀山药': '山药', '枸杞': '枸杞子',
    '元参': '玄参', '杭芍': '白芍', '大白芍': '白芍', '潞党参': '党参', '台党参': '党参',
    '绵黄芪': '黄芪', '北芪': '黄芪', '桂心': '桂枝', '官桂': '肉桂', '紫油桂': '肉桂',
    '寸冬': '麦冬', '大麦冬': '麦冬', '麦门冬': '麦冬', '天门冬': '天冬',
    '浙贝': '浙贝母', '川贝': '川贝母', '大芸': '肉苁蓉',
    '胆南星': '天南星', '制南星': '天南星', '生姜汁': '生姜', '鲜姜': '生姜',
    '炮姜': '干姜', '黑姜': '干姜', '淡竹叶': '竹叶', '鲜竹叶': '竹叶', '竹叶心': '竹叶',
    '大腹绒': '大腹皮', '明天麻': '天麻', '绵茵陈': '茵陈', '广藿香': '藿香',
    '土白术': '白术', '於术': '白术', '酸枣仁': '酸枣仁', '炒枣仁': '酸枣仁',
    '当归尾': '当归', '当归身': '当归', '全当归': '当归', '川牛膝': '牛膝', '怀牛膝': '牛膝',
    '荆芥穗': '荆芥', '龙胆草': '龙胆', '龟板胶': '龟甲胶', '苇根': '芦根', '鲜芦根': '芦根',
    '犀角': '水牛角', '橘皮': '陈皮', '广陈皮': '陈皮', '净麻黄': '麻黄', '西羌活': '羌活',
    '软防风': '防风', '江枳壳': '枳壳', '炒枳壳': '枳壳', '川杜仲': '杜仲', '绵杜仲': '杜仲',
}

def norm(name):
    if name in ALIAS:
        return ALIAS[name]
    for p in PREFIX:
        if name.startswith(p) and len(name) > len(p) + 1:
            base = name[len(p):]
            if base in ALIAS:
                return ALIAS[base]
            return base
    return name

# 统计所有方剂出现药材(归一化后)
cnt = Counter()
for p in d['prescriptions']:
    for n in p['herb_names']:
        cnt[norm(n)] += 1

all_used = set(cnt)
missing = sorted([(n, c) for n, c in cnt.items() if n not in herbs], key=lambda x: -x[1])
print("方剂涉及药材(归一化)总数:", len(all_used))
print("缺失药材数:", len(missing))
print("\n=== 缺失药材按频次排序 ===")
for n, c in missing:
    print(f"{n}: {c}")

# 输出缺失清单 JSON
json.dump({'missing': [n for n, c in missing], 'count': dict(cnt)},
          open('backend/seed/missing_herbs.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print("\n缺失清单已存 backend/seed/missing_herbs.json")
