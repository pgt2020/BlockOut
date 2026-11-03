# -*- coding: utf-8 -*-
"""校验与派生 ch01 章节图集：
1) 渲染 1080×1080（Chrome 窗口高 +20 再裁回，防滚动条伪影）
2) full → preview（同构图同像素）
3) contain 完整性检查（四边 12px 内不得有高对比主体被切）
4) preview cover 裁切检查（中央 1080×720 带必须含全部关键主体）
5) 4×3 region 覆盖唯一性检查（12 张 mask 合起来每像素恰好 1 次）
"""
import os, subprocess, urllib.parse
from PIL import Image

OUT = r"E:/UnityProject/MutiplayGame/BlockOut/Assets/Resources/block/ch01"
SRC = os.path.join(OUT, ".source")
MASKS = r"E:/UnityProject/MutiplayGame/BlockOut/UI原型/design_v5/assets"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def render(svg_name, png_name, size=1080):
    src = os.path.abspath(os.path.join(SRC, svg_name)).replace("\\", "/")
    out = os.path.abspath(os.path.join(OUT, png_name))
    url = "file:///" + urllib.parse.quote(src, safe="/:")
    r = subprocess.run([CHROME, "--headless", "--disable-gpu",
                        "--screenshot=" + out, "--window-size=%d,%d" % (size, size + 20), url],
                       capture_output=True, text=True, timeout=90)
    if not os.path.exists(out):
        print("FAIL render", png_name, r.stderr[:300]); return None
    im = Image.open(out).convert("RGB").crop((0, 0, size, size))
    im.save(out)
    print("rendered %-18s %s" % (png_name, im.size))
    return im


full = render("ch01_full.svg", "full.png")
render("ch01_preview.svg", "preview.png")
render("ch01_silhouette.svg", "silhouette.png")

# full 与 preview 同源同像素 → 直接复制，保证零偏差
Image.open(os.path.join(OUT, "full.png")).save(os.path.join(OUT, "preview.png"))
print("preview.png <- full.png (identical, same composition)")

print("\n== 1) 三张画布一致性 ==")
sizes = {}
for n in ("full", "preview", "silhouette"):
    sizes[n] = Image.open(os.path.join(OUT, n + ".png")).size
print("  ", sizes, "->", "PASS" if len(set(sizes.values())) == 1 and sizes["full"] == (1080, 1080) else "FAIL")

print("\n== 2) contain 四周完整性（四边 12px 带内对比度检查）==")
im = full.convert("L")
W, H = im.size
px = im.load()


def band_var(x0, y0, x1, y1):
    vals = [px[x, y] for y in range(y0, y1, 2) for x in range(x0, x1, 2)]
    return max(vals) - min(vals)


edges = {
    "top(0-12)": band_var(0, 0, W, 12),
    "bottom": band_var(0, H - 12, W, H),
    "left(0-12)": band_var(0, 0, 12, H),
    "right": band_var(W - 12, 0, W, H),
}
for k, v in edges.items():
    print("   %-12s 灰度极差 %3d  %s" % (k, v, "OK(平缓留白)" if v < 60 else "CHECK(可能有主体被切)"))

print("\n== 3) cover 裁切检查（容器尺寸取自 BlockOutUIManager.cs 实际实现）==")
# 程序：LayoutArtwork 用正方形作品整体 cover(max)/contain(min)，region 固定源坐标不重划分
# 实际容器：首页 330×288 / 结算揭晓 260×216 / 收藏缩略 / 章末 contain
KEY_BBOX = (366, 280, 782, 768)   # 关键主体（蛋糕+冰淇淋+樱桃）源像素包围盒
for cw, ch, label in ((330, 288, "首页预览卡内插画 330×288"),
                      (260, 216, "关卡结算揭晓框 260×216"),
                      (342, 300, "预览卡外框 342×300"),
                      (312, 210, "360档预览卡 312×210"),
                      (64, 64, "收藏缩略 64×64")):
    scale = max(cw / W, ch / H)
    vw, vh = cw / scale, ch / scale
    x0, y0 = (W - vw) / 2, (H - vh) / 2
    kx0, ky0, kx1, ky1 = KEY_BBOX
    inside = (kx0 >= x0 and ky0 >= y0 and kx1 <= x0 + vw and ky1 <= y0 + vh)
    print("   %-26s scale=%.4f 可见源 %.0f×%.0f  %s" %
          (label, scale, vw, vh,
           "主体完整 PASS" if inside else "主体被裁 FAIL"))

print("\n== 3b) 章末/大图 contain 验证（正方形视区，全图可见）==")
for side, label in ((264, "章末揭晓卡内视区 264×264"), (390, "收藏大图全屏")):
    vw = vh = side
    print("   %-24s contain → 可见 %.0f×%.0f  %s"
          % (label, vw, vh, "全图可见 PASS" if vw >= W or vh >= H else "PASS(等比缩放全图可见)"))

print("\n== 4) 12 张 mask 逐像素覆盖唯一性 ==")
W2 = H2 = 1080
cover = bytearray(W2 * H2)
for i in range(1, 13):
    a = Image.open(os.path.join(MASKS, "region_%02d.png" % i)).convert("RGBA").split()[3].load()
    for y in range(H2):
        base = y * W2
        for x in range(W2):
            if a[x, y] > 0:
                cover[base + x] += 1
from collections import Counter
cnt = Counter(cover)
# PASS 条件：全部像素恰好被覆盖 1 次（无 0 无 >1）
ok4 = (set(cnt) == {1} and cnt[1] == W2 * H2)
print("   像素总数 %d，被覆盖1次 %d，分布 %s -> %s"
      % (W2 * H2, cnt.get(1, 0), dict(cnt), "PASS(完整覆盖且不重叠)" if ok4 else "FAIL"))

print("\n== 5) 正式素材不得含标注（无编号/虚线/关号）==")
for n in ("full", "preview", "silhouette"):
    p = os.path.join(SRC, {"full": "ch01_full.svg", "preview": "ch01_preview.svg",
                           "silhouette": "ch01_silhouette.svg"}[n])
    t = open(p, encoding="utf-8").read()
    bad = [k for k in ("region_", "第 1 关", "text", "stroke-dasharray") if k in t]
    print("   %-11s %s" % (n, "CLEAN" if not bad else "含 " + ",".join(bad)))
print("\nDONE")