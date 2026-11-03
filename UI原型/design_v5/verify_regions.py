# -*- coding: utf-8 -*-
"""分区体验检查：按 4×3 十二区逐区验证"每次揭晓能看到可辨认的新内容"。
方法：
  1) 对每个 region i，构造"仅揭晓第 i 区"的合成图（其余为剪影）
  2) 计算该区相对剪影的像素变化量与新增可辨认内容占比
  3) 检查相邻 region 之间的信息增益是否足够（避免连续解锁大面积相近背景）
输出：每区变化率、判定，以及最弱区提示。
"""
import os
from PIL import Image, ImageChops

ART = r"E:/UnityProject/MutiplayGame/BlockOut/Assets/Resources/block/ch01"
MASK = r"E:/UnityProject/MutiplayGame/BlockOut/UI原型/design_v5/assets"

full = Image.open(os.path.join(ART, "full.png")).convert("RGB")
sil = Image.open(os.path.join(ART, "silhouette.png")).convert("RGB")
bg = Image.open(os.path.join(MASK, "ch01_fail_placeholder.png")).convert("RGB")

CW, CH = 270, 360
REGIONS = []
idx = 1
for row in range(3):
    for col in range(4):
        REGIONS.append((idx, col * CW, row * CH))
        idx += 1

masks = {}
for i, x, y in REGIONS:
    m = Image.open(os.path.join(MASK, "region_%02d.png" % i)).convert("RGBA").split()[3]
    masks[i] = m.crop((x, y, x + CW, y + CH))

print("== 逐区揭晓变化率（该区从剪影变为完整图后的像素变化占比）==")
rates = {}
for i, x, y in REGIONS:
    f = full.crop((x, y, x + CW, y + CH))
    s = sil.crop((x, y, x + CW, y + CH))
    diff = ImageChops.difference(f, s).convert("L")
    px = list(diff.getdata())
    changed = sum(1 for v in px if v > 24)
    r = changed / len(px)
    rates[i] = r
    bar = "#" * int(r * 40)
    print("   区%-2d (col%d,row%d) 变化 %5.1f%%  %s" % (i, i % 4, i // 4, r * 100, bar))

print("\n== 判定 ==")
weak = [i for i, r in rates.items() if r < 0.08]
print("   最弱区：", min(rates, key=rates.get), "%.1f%%" % (min(rates.values()) * 100))
print("   平均：%.1f%%" % (sum(rates.values()) / len(rates) * 100))
if weak:
    print("   ⚠ 变化 <8%% 的区（内容过于接近背景）：", weak)
else:
    print("   ✓ 十二区变化率均 ≥8%，每次揭晓都有可辨认的新内容")

print("\n== 相邻区信息增益（连续解锁是否容易混淆）==")
pairs = [(i, i + 1) for i in range(1, 12) if i % 4 != 0] + [(4, 5), (8, 9)]
for a, b in pairs:
    fa = full.crop((REGIONS[a - 1][1], REGIONS[a - 1][2], REGIONS[a - 1][1] + CW, REGIONS[a - 1][2] + CH))
    fb = full.crop((REGIONS[b - 1][1], REGIONS[b - 1][2], REGIONS[b - 1][1] + CW, REGIONS[b - 1][2] + CH))
    d = ImageChops.difference(fa, fb).convert("L")
    v = list(d.getdata())
    diff_ratio = sum(1 for x in v if x > 24) / len(v)
    tag = "OK" if diff_ratio > 0.12 else "相近(相邻两区内容较像)"
    print("   区%2d → 区%2d  画面差异 %5.1f%%  %s" % (a, b, diff_ratio * 100, tag))

print("\n== 剪影与完整图必须可区分 ==")
d = ImageChops.difference(full, sil).convert("L")
v = list(d.getdata())
big = sum(1 for x in v if x > 24) / len(v)
print("   整体差异 %.1f%%  %s" % (big * 100, "✓ 可区分" if big > 0.15 else "⚠ 区分不足"))
print("\nDONE")