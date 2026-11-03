# -*- coding: utf-8 -*-
"""按容器精确比例，从统一 1080×1080 源画布导出等比 cover 裁切图。

背景（本轮 P1/P2 修复）：
  · 适配图把同一张 r03_330x288.png 塞进 300×204 / 330×300 等不同比例容器，
     previously 用 preserveAspectRatio="none" 直接拉伸 → 圆形糖果/主体轮廓变形。
  · 规则：**每张展示图都从统一源画布按目标容器比例重新裁切导出**，容器与素材
    比例严格一致；SVG 里再配 preserveAspectRatio="xMidYMid slice" 双保险。
    作品与 12 揭晓区域的相对几何关系 = 源画布几何，不随容器重划分。

本脚本产出：
  · reveal_04.png（4/12 揭晓态母版，供普通结算页使用；逐像素断言不泄露）
  · r03_300x204.png（360×640 适配图预览卡 300×204）
  · r04_310x360.png（390×844 结算揭晓区 310×360 = 卡宽342−32 × clamp(786−330,120,360)）
  · r04_280x270.png（360×640 短屏结算揭晓区 280×270 = 卡宽312−32 × clamp(600−330,120,360)）
  · r12_310x360_contain.png（章末 contain 预渲染：310×310 作品居中于 310×360 视区，
    上下 25px 信笺边 = 程序 MistWarm #FFF7EF；与 LayoutArtwork(contain=true) 一致）
  · 复验全部既有裁切图与其母版一致（center-cover，逐像素必须完全一致）
"""
import os
from PIL import Image

ART = r"E:/UnityProject/MutiplayGame/BlockOut/Assets/Resources/block/ch01"
OUT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(OUT, "assets")

CW, CH = 270, 360  # region 固定源画布 4×3，每区 270×360
MIST_WARM = (255, 247, 239)   # BlockOutDesignTokens.MistWarm（章末 contain 信笺边）


def region_xy(i):
    return (i - 1) % 4 * CW, (i - 1) // 4 * CH


def compose(n):
    """合成 n/12 揭晓态：已揭晓 = full 对应源区，未揭晓 = silhouette 对应源区。"""
    full = Image.open(os.path.join(ART, "full.png")).convert("RGB")
    sil = Image.open(os.path.join(ART, "silhouette.png")).convert("RGB")
    out = sil.copy()
    for i in range(1, n + 1):
        x, y = region_xy(i)
        f = full.crop((x, y, x + CW, y + CH))
        mask = Image.open(os.path.join(ASSETS, "region_%02d.png" % i)).convert("RGBA") \
            .split()[3].crop((x, y, x + CW, y + CH))
        f.putalpha(mask)
        out.paste(f, (x, y), f)
    return out, sil


def cover_crop(master, w, h):
    """中心 cover 裁切：等比放大到覆盖 (w,h)，居中裁到目标尺寸。
    源画布 → 容器只做等比缩放 + 裁切，不做任何非等比拉伸。"""
    s = max(w / master.size[0], h / master.size[1])
    sw, sh = round(master.size[0] * s), round(master.size[1] * s)
    r = master.resize((sw, sh), Image.LANCZOS)
    x, y = (sw - w) // 2, (sh - h) // 2
    assert x >= 0 and y >= 0, "cover scale must fully cover the container"
    return r.crop((x, y, x + w, y + h))


def contain_fit(master, vw, vh, bar=MIST_WARM):
    """contain 预渲染：作品等比缩至 min(vw,vh) 正方形，居中，其余为信笺边。
    与程序 LayoutArtwork(contain=true)（side = min(viewport.w, viewport.h)）一致。"""
    side = min(vw, vh)
    art = master.resize((side, side), Image.LANCZOS)
    out = Image.new("RGB", (vw, vh), bar)
    out.paste(art, ((vw - side) // 2, (vh - side) // 2))
    return out


def main():
    # ---- 1. 4/12 揭晓态母版（首次通关第 4 关后的收藏/结算展示态）----
    out, sil = compose(4)
    path = os.path.join(ASSETS, "reveal_04.png")
    out.save(path)
    print("wrote %s  (已揭晓 4/12)" % path)

    # 不泄露断言：未揭晓 8 区与 silhouette 逐像素一致
    leaks = 0
    px_out, px_sil = out.load(), sil.load()
    for i in range(5, 13):
        x0, y0 = region_xy(i)
        for yy in range(y0, y0 + CH):
            for xx in range(x0, x0 + CW):
                if px_out[xx, yy] != px_sil[xx, yy]:
                    leaks += 1
    assert leaks == 0, "reveal_04 leaks %d px of unrevealed art" % leaks
    print("  unrevealed-region leak check: PASS (0 px)")

    # ---- 2. 新容器裁切（几何来自程序 LayoutFullPages / LayoutArtwork）----
    jobs = [
        ("reveal_04.png", "r04_310x360.png", 310, 360),   # 390×844 结算揭晓区（cover）
        ("reveal_04.png", "r04_280x270.png", 280, 270),   # 360×640 短屏结算揭晓区（cover）
        ("reveal_03.png", "r03_300x204.png", 300, 204),   # 360×640 首页预览卡
    ]
    for src, dst, w, h in jobs:
        m = Image.open(os.path.join(ASSETS, src)).convert("RGB")
        c = cover_crop(m, w, h)
        assert c.size == (w, h)
        c.save(os.path.join(ASSETS, dst))
        print("wrote assets/%s  %dx%d (center-cover from %s)" % (dst, w, h, src))

    # 章末 contain 预渲染（12/12 完整作品，章末结算 SetSettlementArtworkMode(true)）
    m12 = Image.open(os.path.join(ASSETS, "reveal_12.png")).convert("RGB")
    ct = contain_fit(m12, 310, 360)
    assert ct.size == (310, 360)
    # 信笺边断言：上下各 25px 必须是 MistWarm，中部 310×310 非纯色
    for y in (2, 12, 23, 336, 348, 357):
        assert ct.getpixel((5, y)) == MIST_WARM, "contain bar broken at y=%d" % y
    assert ct.getpixel((155, 180)) != MIST_WARM, "contain artwork missing"
    ct.save(os.path.join(ASSETS, "r12_310x360_contain.png"))
    print("wrote assets/r12_310x360_contain.png  310x360 (contain, bars 25px MistWarm)")

    # ---- 3. 复验既有裁切图 = center-cover（meanabsdiff 必须为 0）----
    print("\n== 既有裁切图与母版一致性复验 ==")
    ok = True
    checks = []
    for tag in ("00", "03", "11", "12"):
        for size in ("330x288", "120x124", "117", "64x64", "260x216", "264x264"):
            checks.append(("r%s_%s.png" % (tag, size), "reveal_%s.png" % tag))
    checks.append(("r12_117x100.png", None))       # contain 预渲染（带信笺边），单独说明
    checks.append(("r04_260x216.png", None))       # 旧居中弹窗结算盒（260×216），已被 310×360 取代
    for name, master_name in checks:
        p = os.path.join(ASSETS, name)
        if name == "r04_260x216.png":
            print("   %-18s deprecated（旧弹窗结算盒裁切，现用 r04_310x360）%s"
                  % (name, "存在" if os.path.exists(p) else "已不存在"))
            continue
        if not os.path.exists(p):
            print("   %-18s MISSING" % name)
            ok = False
            continue
        if master_name is None:
            im = Image.open(p)
            left = [im.getpixel((x, im.size[1] // 2)) for x in (0, 1, 2)]
            contained = all(px == (255, 253, 248) for px in left)
            print("   %-18s %s contain 预渲染（信笺边 %s）→ SVG 须按 1:1 放置，禁 slice"
                  % (name, im.size, "PASS" if contained else "FAIL"))
            ok = ok and contained
            continue
        m = Image.open(os.path.join(ASSETS, master_name)).convert("RGB")
        ex = Image.open(p).convert("RGB")
        cc = cover_crop(m, *ex.size)
        diff = list(ex.getdata()) != list(cc.getdata())
        if diff:
            ok = False
        print("   %-18s %s vs %s  %s" % (name, ex.size, master_name,
                                           "PASS" if not diff else "FAIL"))
    assert ok, "existing crops inconsistent with center-cover rule"
    print("\nALL PASS")


if __name__ == "__main__":
    main()
