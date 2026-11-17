# -*- coding: utf-8 -*-
"""合并药材: 现有52味(前端抽取) + 补充48味 → 完整药材库 herbs_all.json
注: 前端抽取的 herbDetails 用中文名作 key,结构一致,直接合并。
"""
import json, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from herbs_extra_a import HERBS_EXTRA_A
from herbs_extra_b import HERBS_EXTRA_B
from herbs_extra_c import HERBS_EXTRA_C
from herbs_extra_d import HERBS_EXTRA_D

base = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extracted_frontend_data.json'), encoding='utf-8'))
herbs = dict(base['herbs'])

extra = {}
extra.update(HERBS_EXTRA_A)
extra.update(HERBS_EXTRA_B)
extra.update(HERBS_EXTRA_C)
extra.update(HERBS_EXTRA_D)
print("补充药材数:", len(extra))

# 命名对齐: 缺失清单名 -> 标准名(标准名在 extra 或 base 中)
RENAME = {
    '杏仁': '苦杏仁',      # 经典方中用杏仁,标准药材名苦杏仁
    '麻仁': '火麻仁',
    '藿香': '广藿香',
    '地黄': '地黄',        # 生地黄/干地黄 归一化为地黄(标准药材名)
}
# 补充条目内 name 字段同步修正
for alias, std in RENAME.items():
    if alias in extra and std not in extra:
        extra[std] = extra.pop(alias)
for k, v in extra.items():
    v['name'] = k

before = len(herbs)
herbs.update(extra)
print(f"药材库: {before} -> {len(herbs)} 味")

# 缺失自检
missing_meta = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'missing_herbs.json'), encoding='utf-8'))
missing_names = set(missing_meta['missing'])
still_missing = [n for n in missing_names if n not in herbs and RENAME.get(n, n) not in herbs]
print("缺失清单仍未被覆盖:", still_missing if still_missing else "无 ✓ 全部覆盖")

out = {'herbs': herbs}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'herbs_all.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print("已生成 backend/seed/herbs_all.json")
