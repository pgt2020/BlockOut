# -*- coding: utf-8 -*-
"""按进度合成章节揭晓结果图（0/12、3/12、11/12、12/12）。
规则：
  · 已揭晓区域 = full.png 的对应源区域；未揭晓区域 = silhouette.png 的对应源区域
  · region 固定 1080×1080 源画布 4×3（每区 270×360），不随容器重划分
  · 未揭晓区域**绝不出现 full 的像素**（不泄露原图）——逐像素断言校验
输出：UI原型/design_v5/assets/reveal_00.png / reveal_03.png / reveal_11.png / reveal_12.png
这些图供各页面 SVG 直接 <image> 引用，保证同一进度跨页面揭晓结果一致。
"""
import os
from PIL import Image

ART = r"E:/UnityProject/MutiplayGame/BlockOut/Assets/Resources/block/ch01"
MASK = r"E:/UnityProject/MutiplayGame/BlockOut/UI原型/design_v5/assets"
OUT = MASK

full = Image.open(os.path.join(ART, "full.png")).convert("RGB")
sil = Image.open(os.path.join(ART, "silhouette.png")).convert("RGB")

CW, CH = 270, 360
# region i -> (col,row)；region_01 在左上，行优先
def region_xy(i):
    return (i - 1) % 4 * CW, (i - 1) // 4 * CH

masks = {}
for i in range(1, 13):
    x, y = region_xy(i)
    masks[i] = Image.open(os.path.join(MASK, "region_%02d.png" % i)).convert("RGBA") \
                  .split()[3].crop((x, y, x + CW, y + CH))

STATES = [(0, "00"), (3, "03"), (11, "11"), (12, "12")]

for n, tag in STATES:
    out = sil.copy()                      # 底 = 剪影
    revealed = set(range(1, n + 1))
    for i in range(1, 13):
        if i not in revealed:
            continue
        x, y = region_xy(i)
        f = full.crop((x, y, x + CW, y + CH))
        # 用 mask 做 alpha 混合，保证边缘不出血
        f.putalpha(masks[i])
        out.paste(f, (x, y), f)
    path = os.path.join(OUT, "reveal_%s.png" % tag)
    out.save(path)
    print("wrote %s  (已揭晓 %d/12)" % (path, n))

# ---- 不泄露校验：未揭晓区域必须与 silhouette 逐像素一致 ----
print("\n== 未解锁区域不得泄露原图（逐像素断言）==")
ok_all = True
for n, tag in STATES:
    out = Image.open(os.path.join(OUT, "reveal_%s.png" % tag)).convert("RGB")
    leaks = 0
    for i in range(1, 13):
        if i <= n:
            continue
        x, y = region_xy(i)
        a = out.crop((x, y, x + CW, y + CH))
        b = sil.crop((x, y, x + CW, y + CH))
        if list(a.getdata()) != list(b.getdata()):
            leaks += 1
    print("   reveal_%s：未揭晓 %2d 区，泄露 %d 区  %s"
          % (tag, 12 - n, leaks, "PASS" if leaks == 0 else "FAIL"))
    ok_all = ok_all and leaks == 0

# ---- 已揭晓区域必须与 full 一致 ----
print("\n== 已揭晓区域必须与完整图一致 ==")
for n, tag in STATES:
    out = Image.open(os.path.join(OUT, "reveal_%s.png" % tag)).convert("RGB")
    bad = 0
    for i in range(1, n + 1):
        x, y = region_xy(i)
        a = out.crop((x, y, x + CW, y + CH))
        b = full.crop((x, y, x + CW, y + CH))
        if list(a.getdata()) != list(b.getdata()):
            bad += 1
    print("   reveal_%s：已揭晓 %2d 区，不一致 %d 区  %s"
          % (tag, n, bad, "PASS" if bad == 0 else "FAIL"))
    ok_all = ok_all and bad == 0

print("\n== 四档尺寸 ==")
for n, tag in STATES:
    print("   reveal_%s %s" % (tag, Image.open(os.path.join(OUT, "reveal_%s.png" % tag)).size))
print("\n%s" % ("ALL PASS" if ok_all else "HAS FAIL"))
print("DONE")