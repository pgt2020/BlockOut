# -*- coding: utf-8 -*-
"""本轮（第十一轮）修复的像素级验证（不凭"脚本执行成功"下结论）：

A. 适配图 = 真实设备高度（沿用上轮断言）
B. 等比显示（无拉伸）（沿用上轮断言）
C. 17_chapter_end_clean：三态均为程序结算层真实布局——
   contain 信笺边在位 / 主按钮三态颜色（A 珊瑚 / B 禁用灰 / C 珊瑚）/
   收藏+重玩左右并排（一行两枚）/ 页外图注在位 / 无安全区虚线
D. 首页 12/12 两态（沿用上轮断言）
H. clean_settlement 家族 = LayoutFullPages 真实全页布局：
   H1 卡铺满安全区（上下安全区带仍是 Dim 下的游戏页，非卡白底）
   H2 标题/拼片/注记/金币行文字均已渲染
   H3 作品区渲染 ≈ PIL center-cover 期望（无拉伸）；章末 = contain 1:1 且信笺边 #FFF7EF
   H4 下一关珊瑚（可点）/ 禁用灰（章末·未发布）
   H5 查看收藏/重玩本关**同一行两枚**（不是三枚纵排）；返回首页通栏一枚
   H6 短屏（360×640）真实排版：卡 312×600、作品区 280×270、内容不越卡底
   H7 SVG 字符串断言：三态文案逐条对应 HandleLevelWon；无旧 300×500 弹窗几何；无查看大图
I. 纯界面无开发说明 / 奖励文案准确：
   I1 clean_settings 无「二级页面：不显示底部导航；返回上一层」（PNG 对应带无墨痕）
   I2 clean_collection 无「道具」承诺，改为「重玩已通关关卡可获得金币，拼片不会重复解锁」
   I3 全套 clean_*.svg 渲染文本扫描：无开发说明类词汇（道具/刷金币/入口见/未实现/TODO…）
J. PNG 尺寸与画布一致
"""
import os
import re
import sys
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(BASE, "assets")

fails = []


def check(name, cond, detail=""):
    print("  %-58s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        fails.append(name)


def px(im, x, y):
    return im.getpixel((x, y))


def close(c, ref, tol=14):
    return all(abs(a - b) <= tol for a, b in zip(c[:3], ref))


def is_dash_red(c):
    """#F45F70 安全区虚线专色（容差收紧，避开珊瑚 CTA #FF6B5C 与渐变）。"""
    return abs(c[0] - 244) <= 8 and abs(c[1] - 95) <= 12 and abs(c[2] - 112) <= 14


def band_red(im, y0, y1):
    n = 0
    for y in range(y0, y1):
        for x in range(0, im.size[0], 2):
            if is_dash_red(px(im, x, y)):
                n += 1
    return n


def cover_crop(master, w, h):
    s = max(w / master.size[0], h / master.size[1])
    sw, sh = round(master.size[0] * s), round(master.size[1] * s)
    r = master.resize((sw, sh), Image.LANCZOS)
    x, y = (sw - w) // 2, (sh - h) // 2
    return r.crop((x, y, x + w, y + h))


def mean_abs(im1, im2):
    d1, d2 = list(im1.getdata()), list(im2.getdata())
    assert len(d1) == len(d2)
    tot = 0
    for p, q in zip(d1, d2):
        tot += abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2])
    return tot / (len(d1) * 3)


def upscale(im, f=2):
    return im.resize((im.size[0] * f, im.size[1] * f), Image.LANCZOS)


def ink(im, x0, y0, x1, y1, thr=430):
    """区域内深色像素数（文字墨痕）。坐标为**逻辑坐标**，内部按 2x 换算。"""
    return sum(1 for y in range(y0 * 2, y1 * 2)
               for x in range(x0 * 2, x1 * 2) if sum(px(im, x, y)) < thr)


def stroke_runs(im, y_logical, x0, x1, ref=(232, 205, 187), tol=22):
    """某逻辑行上 ≈ 描边色 的连续段（按钮圆角矩形顶/底边）。"""
    hits = []
    for x in range(x0, x1):
        hits.append(close(px(im, x * 2, y_logical * 2), ref, tol)
                    or close(px(im, x * 2, y_logical * 2 + 1), ref, tol))
    runs, start = [], None
    for i, h in enumerate(hits):
        if h and start is None:
            start = i
        elif not h and start is not None:
            if i - start >= 20:
                runs.append((x0 + start, x0 + i))
            start = None
    if start is not None and len(hits) - start >= 20:
        runs.append((x0 + start, x0 + len(hits)))
    return runs


def read(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as f:
        return f.read()


def texts_of(svg):
    """仅取渲染的 <text> 内容（不含 aria-label / 注释 / 批注）。"""
    body = re.sub(r"<!--.*?-->", "", svg, flags=re.S)
    return " ".join(re.findall(r"<text[^>]*>(.*?)</text>", body, re.S))


# ================================================================ A 适配图
print("== A · 适配图真实设备高度 ==")
ADAPT = [
    ("adapt_360x640.png", 360, 640, 20, 20, 56, 556, 338, 84, 204, 90),
    ("adapt_390x844.png", 390, 844, 24, 34, 64, 738, 504, 98, 288, 90),
    ("adapt_390x932.png", 390, 932, 44, 34, 64, 826, 592, 118, 288, 90),
]
STRIP_BG = (247, 242, 235)

for fn, W, H, st, sb, nav_h, nav_y, cta_y, card_top, art_h, strip_h in ADAPT:
    im = Image.open(os.path.join(BASE, fn)).convert("RGB")
    tag = "%dx%d" % (W, H)
    check("%s 画布 = 页面+H+说明区" % tag,
          im.size == (W * 2, (H + strip_h) * 2), "got %s" % (im.size,))

    col = W * 2 // 2
    first_strip = None
    for y in range(H * 2 - 6, (H + 40) * 2):
        if close(px(im, col, y), STRIP_BG, 8):
            first_strip = y
            break
    check("%s 页面边界恰在 y=%d（页面严格 0..H）" % (tag, H * 2),
          first_strip is not None and abs(first_strip - H * 2) <= 2,
          "first strip bg y=%s" % first_strip)
    check("%s H-3 处仍是页面底色（未被加长）" % tag,
          not close(px(im, col, H * 2 - 3), STRIP_BG, 8))

    c = px(im, col, (nav_y + nav_h // 2) * 2)
    check("%s 导航白色且在页面内" % tag, min(c) > 240, "px=%s" % (c,))
    check("%s 导航底 %d 止于安全区上方 (<= %d)" % (tag, nav_y + nav_h, H - sb),
          nav_y + nav_h <= H - sb)
    below = px(im, col, (nav_y + nav_h + 3) * 2)
    check("%s 导航下方 3px 非导航白" % tag, not (min(below) > 245))

    cta_c = px(im, col, (cta_y + 44) * 2)
    check("%s CTA 珊瑚色（高 88 不压缩）" % tag,
          cta_c[0] > 220 and cta_c[0] - cta_c[2] > 50, "px=%s" % (cta_c,))
    gap = px(im, col, (card_top + art_h + 36 + 7) * 2)
    check("%s 预览卡与 CTA 间隙为背景（无重叠）" % tag, not (min(gap) > 245), "px=%s" % (gap,))

    n_top = band_red(im, st * 2 - 6, st * 2 + 6)
    n_bot = band_red(im, (H - sb) * 2 - 6, (H - sb) * 2 + 6)
    check("%s 安全区虚线在 st=%d / H-sb=%d 行（检测器正向对照）" % (tag, st, sb),
          n_top > 0 and n_bot > 0, "top=%d bottom=%d" % (n_top, n_bot))

# ================================================================ B 等比显示
print("== B · 预览容器等比显示（无拉伸） ==")
m3 = Image.open(os.path.join(A, "reveal_03.png")).convert("RGB")
old_none_asset = Image.open(os.path.join(A, "r03_330x288.png")).convert("RGB")
HIST = {"adapt_360x640.png": (300, 210), "adapt_390x844.png": (330, 300), "adapt_390x932.png": (330, 300)}
for fn, W, H, st, sb, nav_h, nav_y, cta_y, card_top, art_h, strip_h in ADAPT:
    im = Image.open(os.path.join(BASE, fn)).convert("RGB")
    tag = "%dx%d" % (W, H)
    cw = 300 if W == 360 else 330
    box = (60, (card_top + 6) * 2, 60 + cw * 2, (card_top + 6 + art_h) * 2)
    rendered = im.crop(box)
    expect = upscale(cover_crop(m3, cw, art_h))
    d_cover = mean_abs(rendered, expect)
    hw, hh = HIST[fn]
    ref_none = upscale(old_none_asset.resize((hw, hh), Image.BILINEAR))
    ref_none = ref_none.crop((0, 0, cw * 2, art_h * 2))
    d_none = mean_abs(rendered, ref_none)
    ref_squash = upscale(m3.resize((cw, art_h), Image.BILINEAR))
    d_squash = mean_abs(rendered, ref_squash)
    check("%s 渲染 ≈ center-cover 期望 (meanabsdiff=%.2f)" % (tag, d_cover), d_cover < 12)
    check("%s 远离 none 拉伸参照 %dx%d (%.1f vs %.1f)" % (tag, hw, hh, d_none, d_cover),
          d_none > d_cover * 1.15)
    check("%s 远离母版压扁参照 (%.1f vs %.1f)" % (tag, d_squash, d_cover),
          d_squash > d_cover * 1.25)

# ================================================================ 结算页几何断言（H）
print("== H · clean_settlement 家族 = LayoutFullPages 真实全页布局 ==")
# 390×844 / st=24 / sb=34：卡 24..366 × 24..810；y=84+revealH=444
SET390 = dict(W=390, st=24, L=24, cw=342, card=(24, 24, 366, 810),
             reveal=(40, 108, 350, 468), note=(478, 496), coin=(502, 526),
             nxt=(540, 588), sub=(600, 644), home=(656, 700))
SET360 = dict(W=360, st=24, L=24, cw=312, card=(24, 24, 336, 624),
             reveal=(40, 108, 320, 378), note=(388, 406), coin=(412, 436),
             nxt=(450, 498), sub=(510, 554), home=(566, 610))

m4 = Image.open(os.path.join(A, "reveal_04.png")).convert("RGB")
m12 = Image.open(os.path.join(A, "reveal_12.png")).convert("RGB")
CARD_WHITE = (255, 253, 248)

for fn, g in (("clean_settlement.png", SET390),
              ("clean_settlement_repeat.png", SET390),
              ("clean_settlement_chapter.png", SET390),
              ("clean_settlement_short.png", SET360)):
    im = Image.open(os.path.join(BASE, fn)).convert("RGB")
    x0, y0, x1, y1 = g["card"]
    # H1 卡铺满安全区：卡内为卡白底；顶部/底部安全区带仍是 Dim 下游戏页（非卡白底）
    check("%s 卡内为 #FFFDF8（卡存在）" % fn,
          close(px(im, (x0 + 40) * 2, (y0 + 40) * 2), CARD_WHITE, 6))
    top_strip = px(im, g["W"] * 2 // 2, (y0 - 8) * 2)
    bot_strip = px(im, g["W"] * 2 // 2, (g["card"][3] + 8) * 2)
    check("%s 顶部安全区带非卡白底（Dim 下游戏页）" % fn,
          not close(top_strip, CARD_WHITE, 6), "px=%s" % (top_strip,))
    check("%s 底部安全区带非卡白底" % fn,
          not close(bot_strip, CARD_WHITE, 6), "px=%s" % (bot_strip,))
    # H2 文字渲染
    check("%s 标题文字已渲染" % fn, ink(im, x0 + 60, y0 + 14, x1 - 60, y0 + 46) > 80,
          "ink=%d" % ink(im, x0 + 60, y0 + 14, x1 - 60, y0 + 46))
    check("%s 拼片进度文字已渲染" % fn, ink(im, x0 + 60, y0 + 50, x1 - 60, y0 + 74) > 15)
    check("%s 注记文字已渲染" % fn,
          ink(im, x0 + 30, g["note"][0], x1 - 30, g["note"][1]) > 10)
    ccx, ccy = g["W"] // 2 - 120 + 23, g["coin"][0] + 12
    check("%s 金币图标已渲染" % fn,
          any(close(px(im, ccx * 2, (ccy + dy) * 2), ref, 34)
              for dy in (-7, -4, 0, 4, 7) for ref in ((255, 197, 61), (227, 162, 46))),
          "px=%s" % (px(im, ccx * 2, ccy * 2),))
    check("%s 奖励文字已渲染" % fn,
          ink(im, x0 + 90, g["coin"][0], x1 - 40, g["coin"][1]) > 25)
    # H3 作品区
    rx0, ry0, rx1, ry1 = g["reveal"]
    rendered_art = im.crop((rx0 * 2, ry0 * 2, rx1 * 2, ry1 * 2))
    if fn == "clean_settlement_chapter.png":
        expect_art = upscale(Image.open(os.path.join(A, "r12_310x360_contain.png")).convert("RGB"))
        d = mean_abs(rendered_art, expect_art)
        check("%s 章末 contain 1:1（meanabsdiff=%.2f）" % (fn, d), d < 2, "d=%.2f" % d)
        # contain 信笺边（MistWarm #FFF7EF）：作品区上下各 25px
        for yy in (ry0 + 4, ry0 + 20, ry1 - 20, ry1 - 4):
            c = px(im, (rx0 + rx1) // 2 * 2, yy * 2)
            check("%s contain 信笺边 y=%d" % (fn, yy), close(c, (255, 247, 239), 6), "px=%s" % (c,))
    else:
        expect_art = upscale(cover_crop(m4, rx1 - rx0, ry1 - ry0))
        d = mean_abs(rendered_art, expect_art)
        check("%s 作品区 ≈ center-cover 期望（无拉伸，meanabsdiff=%.2f）" % (fn, d), d < 12)
        nonbg = sum(1 for p in rendered_art.getdata() if not close(p, (255, 247, 239), 6))
        check("%s 作品区已绘制 4/12 插画" % fn, nonbg > 1000, "nonbg=%d" % nonbg)
    # H4 下一关按钮
    ny0, ny1 = g["nxt"]
    if fn == "clean_settlement_chapter.png":
        gc = px(im, 300 * 2, (ny0 + 24) * 2)
        check("%s 「新章节准备中」主按钮禁用灰" % fn,
              not (gc[0] > 220 and gc[0] - gc[2] > 50) and 190 <= gc[0] <= 240,
              "px=%s" % (gc,))
    else:
        nc = px(im, 300 * 2, (ny0 + 24) * 2)
        check("%s 「下一关」珊瑚主按钮（48 高不压缩）" % fn,
              nc[0] > 220 and nc[0] - nc[2] > 50, "px=%s" % (nc,))
        check("%s 主按钮文字已渲染" % fn,
              ink(im, x0 + 90, ny0 + 8, x1 - 90, ny1 - 8, thr=700) > 25)
    # H5 次级行：同一行两枚（查看收藏 / 重玩本关），返回首页通栏一枚
    sy = g["sub"][0]
    runs = stroke_runs(im, sy, x0 + 10, x1 - 10)
    check("%s 次级行 = 同一行两枚按钮（非纵排）" % fn, len(runs) == 2,
          "runs=%s" % (runs,))
    if len(runs) == 2:
        w1, w2 = runs[0][1] - runs[0][0], runs[1][1] - runs[1][0]
        check("%s 两枚等宽（左右对称）" % fn, abs(w1 - w2) <= 4 and w1 >= 100,
              "w1=%d w2=%d" % (w1, w2))
        check("%s 两枚之间为卡底间隙（真实 12，扫描行含圆角内缩）" % fn,
              10 <= runs[1][0] - runs[0][1] <= 50, "gap=%d" % (runs[1][0] - runs[0][1]))
    check("%s 次级行按钮文字已渲染" % fn,
          ink(im, x0 + 20, sy + 10, x1 - 20, g["sub"][1] - 6) > 20)
    hy = g["home"][0]
    hruns = stroke_runs(im, hy, x0 + 10, x1 - 10)
    check("%s 返回首页 = 通栏一枚（≈卡宽−32）" % fn,
          len(hruns) == 1 and hruns[0][1] - hruns[0][0] >= (g["cw"] - 32) - 30,
          "runs=%s" % (hruns,))
    # H6 内容不越卡底
    check("%s 内容底 %.0f <= 卡底 %d" % (fn, g["home"][1], y1), g["home"][1] <= y1)

# H7 SVG 字符串断言（文案 ↔ HandleLevelWon；几何 ↔ LayoutFullPages）
print("== H7 · 结算 SVG 文案/几何断言 ==")
SETTLE_TEXT = {
    "clean_settlement.svg": ["新拼片解锁", "拼片 4/12", "本次新揭晓 1 片拼片",
                             "首次通关 · 获得 40 金币", "下一关", "查看收藏", "重玩本关", "返回首页"],
    "clean_settlement_repeat.svg": ["关卡完成", "拼片 4/12", "重复通关 · 拼片不重复解锁",
                                    "重复通关 · 获得 40 金币", "下一关", "查看收藏", "重玩本关"],
    "clean_settlement_chapter.svg": ["本章通关", "拼片 12/12 · 本章作品已集齐",
                                     "本章 12 片拼片全部揭晓 · 完整作品已解锁",
                                     "首次通关 · 获得 80 金币", "新章节准备中"],
    "clean_settlement_short.svg": ["新拼片解锁", "首次通关 · 获得 40 金币", "下一关"],
}
for fn, needles in SETTLE_TEXT.items():
    svg = read(fn)
    txt = texts_of(svg)
    missing = [n for n in needles if n not in txt]
    check("%s 文案齐备（对应 HandleLevelWon）" % fn, not missing, "missing=%s" % missing)
    check("%s 无旧 300×500 居中弹窗几何" % fn,
          'width="300" height="500"' not in svg and "300×500" not in svg)
    check("%s 无查看大图入口（程序结算层没有）" % fn, "查看大图" not in txt)
    check("%s 无水平堆叠容器（封面预览卡规则不适用结算）" % fn, 'width="330" height="288"' not in svg)

# 次级按钮精确几何（程序 SetTopLeft：CollectionBtn x=16 / ReplayBtn x=width/2+6，各 (w-44)/2×44）
GEOM = {
    "clean_settlement.svg": ('x="40" y="600" width="149" height="44"',
                             'x="201" y="600" width="149" height="44"'),
    "clean_settlement_repeat.svg": ('x="40" y="600" width="149" height="44"',
                                    'x="201" y="600" width="149" height="44"'),
    "clean_settlement_chapter.svg": ('x="40" y="600" width="149" height="44"',
                                     'x="201" y="600" width="149" height="44"'),
    "clean_settlement_short.svg": ('x="40" y="510" width="134" height="44"',
                                   'x="186" y="510" width="134" height="44"'),
}
for fn, (left, right) in GEOM.items():
    svg = read(fn)
    check("%s 查看收藏按钮几何 = L+16" % fn, left in svg)
    check("%s 重玩本关按钮几何 = L+卡宽/2+6" % fn, right in svg)

# ================================================================ C 17_chapter_end_clean
print("== C · 17_chapter_end_clean 三态 = 程序结算层布局 ==")
im = Image.open(os.path.join(BASE, "17_chapter_end_clean.png")).convert("RGB")
check("size 780x5348", im.size == (780, 5348), "got %s" % (im.size,))
for name, y0, nxt_color in (("A", 40, "coral"), ("B", 920, "gray"), ("C", 1800, "coral")):
    # contain 信笺边（页面内 reveal 区 y0+108..y0+468，作品 y0+133..y0+443）
    for yy in (y0 + 112, y0 + 128, y0 + 452, y0 + 464):
        c = px(im, 195 * 2, yy * 2)
        check("页 %s contain 信笺边 y=%d" % (name, yy), close(c, (255, 247, 239), 6), "px=%s" % (c,))
    # 主按钮（页面内 next_y = 540）
    nc = px(im, 300 * 2, (y0 + 564) * 2)
    if nxt_color == "coral":
        check("页 %s 主按钮珊瑚（进入下一章）" % name, nc[0] > 220 and nc[0] - nc[2] > 50, "px=%s" % (nc,))
    else:
        check("页 %s 主按钮禁用灰（新章节准备中）" % name,
              not (nc[0] > 220 and nc[0] - nc[2] > 50) and 190 <= nc[0] <= 240, "px=%s" % (nc,))
    # 次级行：一行两枚
    runs = stroke_runs(im, y0 + 600, 34, 356)
    check("页 %s 收藏/重玩同一行两枚" % name, len(runs) == 2, "runs=%s" % (runs,))
    # 标题墨痕
    check("页 %s 标题已渲染" % name, ink(im, 100, y0 + 30, 290, y0 + 50) > 60)
# 页外图注（各页面间隙，位于页面边距之外：页面起点 40/920/1800 上方 14px）
for name, y in (("A", 26), ("B", 906), ("C", 1786)):
    t = ink(im, 60, y - 12, 330, y + 10)
    check("页 %s 页外图注在位（状态名不进页面）" % name, t > 25, "ink=%d" % t)
svg17 = read("17_chapter_end_clean.svg")
check("17 clean 无安全区虚线", 'stroke-dasharray="4 3"' not in svg17)
check("17 clean 无查看大图入口", "查看大图" not in texts_of(svg17))
check("17 clean 无旧自绘奖励卡/264 作品盒", "查看大图" not in svg17 and "264" not in svg17)
check("17 clean 无 +N", "+N" not in texts_of(svg17))
check("17 spec 版保留了说明注记（规格版与纯界面版分清）",
      "· 重复通关奖励相同" in read("17_chapter_end.svg"))

# ================================================================ D 首页两态
print("== D · 首页 12/12 两态 ==")
prep = Image.open(os.path.join(BASE, "clean_home_12_preparing.png")).convert("RGB")
c = px(prep, 200, 1000)
check("preparing 主 CTA 为禁用灰 (px=%s)" % (c,),
      195 <= c[0] <= 245 and c[0] - c[2] <= 34 and c[1] >= 150)
pub = Image.open(os.path.join(BASE, "clean_home_12.png")).convert("RGB")
c2 = px(pub, 200, 1000)
check("已发布示例主 CTA 为珊瑚红", c2[0] > 220 and c2[0] - c2[2] > 50, "px=%s" % (c2,))

# ================================================================ I 纯界面说明/文案
print("== I · 纯界面无开发说明 / 奖励文案准确 ==")
svg_set = read("clean_settings.svg")
check("clean_settings 无「二级页面：不显示底部导航」说明", "二级页面" not in svg_set)
check("规格版 16 仍保留该说明（两版分清）", "二级页面" in read("16_settings_page.svg"))
ims = Image.open(os.path.join(BASE, "clean_settings.png")).convert("RGB")
# 旧说明所在带（规格版组内 y=712 + translate 60 → 绝对 772）：应无墨痕
n = ink(ims, 40, 766, 350, 780)
check("clean_settings.png 底部无说明墨痕", n == 0, "ink=%d" % n)

svg_col = read("clean_collection.svg")
col_txt = texts_of(svg_col)
check("clean_collection 无「道具」奖励承诺", "道具" not in col_txt)
check("clean_collection 无「刷金币」表述", "刷金币" not in col_txt)
check("clean_collection 奖励文案准确",
      "重玩已通关关卡可获得金币，拼片不会重复解锁" in col_txt)
check("规格版 14 同步修正（两版一致）",
      "重玩已通关关卡可获得金币，拼片不会重复解锁" in texts_of(read("14_collection_page.svg")))
imc = Image.open(os.path.join(BASE, "clean_collection.png")).convert("RGB")
# 新文案在规格稿组内 y=632 + translate(0,60) → 绝对 y≈692
n = ink(imc, 40, 684, 350, 700)
check("clean_collection.png 新文案已渲染", n > 10, "ink=%d" % n)

# I3 全套 clean 渲染文本扫描：开发说明类词汇零容忍
print("== I3 · 全套 clean 开发说明扫描 ==")
FORBIDDEN = ["二级页面", "不显示", "入口见", "刷金币", "道具", "+N", "TODO", "未实现",
             "待定", "示意", "规格", "标注", "开发", "设计说明"]
for f in sorted(x for x in os.listdir(BASE) if x.startswith("clean_") and x.endswith(".svg")):
    txt = texts_of(read(f))
    hit = [w for w in FORBIDDEN if w in txt]
    check("%s 无开发说明词汇" % f, not hit, "hit=%s" % hit)

# ================================================================ F clean 全套
print("== F · clean 全套安全区行带无红线 ==")
BANDS = [("clean_game.png", 770), ("clean_collection.png", 770), ("clean_store.png", 770),
         ("clean_settings.png", 770), ("clean_home.png", 770), ("clean_home_00.png", 770),
         ("clean_home_11.png", 770), ("clean_home_12.png", 770),
         ("clean_home_12_preparing.png", 770), ("clean_settlement.png", 770),
         ("clean_settlement_repeat.png", 770), ("clean_settlement_chapter.png", 770),
         ("clean_settlement_short.png", 620)]
for f, by in BANDS:
    im2 = Image.open(os.path.join(BASE, f)).convert("RGB")
    n = band_red(im2, by * 2, (by + 20) * 2)
    check("%s 安全区行带(y=%d)无红线" % (f, by), n == 0, "red px=%d" % n)

# ================================================================ J 尺寸
print("== J · PNG 尺寸与画布一致 ==")
for f, size in (("adapt_360x640.png", (720, 1460)), ("adapt_390x844.png", (780, 1868)),
                ("adapt_390x932.png", (780, 2044)), ("17_chapter_end.png", (780, 5670)),
                ("17_chapter_end_clean.png", (780, 5348)),
                ("clean_game.png", (780, 1688)), ("clean_collection.png", (780, 1688)),
                ("clean_store.png", (780, 1688)), ("clean_settings.png", (780, 1688)),
                ("clean_settlement.png", (780, 1688)),
                ("clean_settlement_repeat.png", (780, 1688)),
                ("clean_settlement_chapter.png", (780, 1688)),
                ("clean_settlement_short.png", (720, 1280)),
                ("clean_home_12_preparing.png", (780, 1688))):
    check("%s = %s" % (f, size), Image.open(os.path.join(BASE, f)).size == size)

print("\n%s" % ("ALL PASS" if not fails else "FAILED: %s" % fails))
sys.exit(1 if fails else 0)
