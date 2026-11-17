# -*- coding: utf-8 -*-
import re, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

herb_file = 'frontend/src/pages/HerbKnowledge.tsx'
rx_file = 'frontend/src/pages/PrescriptionDatabase.tsx'

src = open(herb_file, encoding='utf-8').read()

# 1) 分类树叶节点 { id:'mahuang', name:'麻黄', ... }
leaf_re = re.compile(r"\{\s*id:\s*'([a-z0-9]+)'\s*,\s*name:\s*'([^']+)'\s*,\s*pinyin:\s*'([^']*)'\s*,\s*description:\s*'([^']*)'\s*\}", re.S)
leaves = leaf_re.findall(src)
name2key = {n: k for k, n, p, d in leaves}

# 2) herbDetails 中文名作 key
details_block = src[src.index('const herbDetails'):src.index('const HerbKnowledge')]
det_re = re.compile(r"'([^']{2,10})':\s*\{([\s\S]*?)\n\s*\},?", re.S)
detail_names = {}
for k, body in det_re.findall(details_block):
    if k in ('Record', 'string', 'any'):
        continue
    fields = dict(re.findall(r"(name|pinyin|latin|property|meridian|functions|indications|dosage|precautions|modernResearch|description|flavor):\s*'([^']*)'", body))
    if fields:
        detail_names[k] = fields

# 3) 方剂
rx_src = open(rx_file, encoding='utf-8').read()
rx_re = re.compile(r"\{\s*id:\s*(\d+)\s*,\s*name:\s*'([^']+)'\s*,\s*pinyin:\s*'([^']*)'\s*,\s*type:\s*'([^']*)'\s*,\s*source:\s*'([^']*)'\s*,\s*functions:\s*'([^']*)'\s*,\s*indications:\s*'([^']*)'\s*,\s*herbs:\s*'([^']*)'\s*,\s*createTime:\s*'([^']*)'\s*\}", re.S)
rx = rx_re.findall(rx_src)

print("【分类树叶】", len(leaves), "棵,药材名去重:", len(set(n for _, n, _, _ in leaves)))
print("【herbDetails】", len(detail_names), "条")
comp = sum(1 for f in detail_names.values() if f.get('property') and f.get('meridian') and f.get('functions') and f.get('indications'))
print("  核心四字段齐全:", comp)
print("  字段分布:", {k: sum(1 for f in detail_names.values() if k in f) for k in ['property', 'meridian', 'functions', 'indications', 'dosage', 'precautions', 'modernResearch', 'description']})
print("  详情是否都命中树叶:", sum(1 for n in detail_names if n in name2key), "/", len(detail_names))

# 别名归一化映射
ALIAS = {
    '生甘草': '甘草', '炙甘草': '甘草', '生地黄': '地黄', '干地黄': '地黄',
    '苦桔梗': '桔梗', '半夏曲': '半夏', '白茯苓': '茯苓', '茯神': '茯苓',
    '山萸肉': '山茱萸', '淮山药': '山药', '怀山药': '山药', '枸杞': '枸杞子',
    '元参': '玄参', '黑玄参': '玄参', '杭芍': '白芍', '大白芍': '白芍',
    '潞党参': '党参', '台党参': '党参', '绵黄芪': '黄芪', '北芪': '黄芪',
    '桂心': '桂枝', '官桂': '肉桂', '大芸': '肉苁蓉', '寸冬': '麦冬',
    '天冬': '麦冬', '大麦冬': '麦冬', '明党参': '党参', '云苓': '茯苓',
    '浙贝': '浙贝母', '川贝': '川贝母', '大腹绒': '大腹皮', '甘草梢': '甘草',
}

def parse_herbs(hstr):
    names = []
    for p in re.split(r'[、，,;；]', hstr):
        p = p.strip()
        if not p:
            continue
        m = re.match(r'^(.+?)(?:[\d]+|半|两)?(?:g|克|枚|片|钱|个|升|分)$', p)
        names.append(m.group(1) if m else p)
    return names

missing = {}
rx_herb_names = {}
for rid, name, py, typ, src_, func, ind, herbs, ct in rx:
    for n in parse_herbs(herbs):
        canon = ALIAS.get(n, n)
        rx_herb_names.setdefault(rid, set())
        rx_herb_names[rid].add(canon)
        if canon not in name2key:
            missing.setdefault(canon, 0)
            missing[canon] += 1

print("\n【方剂】", len(rx), "条")
allnames = set()
for s in rx_herb_names.values():
    allnames |= s
print("方剂涉及药材名(归一化后)去重:", len(allnames))
print("可匹配到药材库:", len(allnames & set(name2key)), "| 缺失:", len(allnames - set(name2key)))
print("\n缺失药材 Top30:")
for k, v in sorted(missing.items(), key=lambda x: -x[1])[:30]:
    print(f"   {k} x{v}")

print("\n=== 方剂-药材关联抽样 ===")
for rid, name in [(1, '四君子汤'), (6, '桂枝汤'), (16, '大承气汤')]:
    print(f" {name}: {sorted(rx_herb_names[str(rid)])}")

out = {
    'name2key': name2key,
    'herbs': detail_names,
    'prescriptions': [{'id': int(a), 'name': b, 'source': e, 'functions': f,
                        'indications': g, 'herb_names': sorted(rx_herb_names.get(a, [])),
                        'herbs_raw': h} for a, b, c, d, e, f, g, h, i in rx],
    'missing_herbs': dict(sorted(missing.items(), key=lambda x: -x[1])),
}
open('_data_analysis.json', 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
print("\n已存 _data_analysis.json")
