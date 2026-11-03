# -*- coding: utf-8 -*-
"""生成 BlockOut 第一章章节图集素材（1080×1080 同画布、同构图）。
输出（BlockOut/Assets/Resources/block/ch01/）：
  full.png / preview.png / silhouette.png
可编辑源：同目录 .source/ch01_full.svg、ch01_preview.svg、ch01_silhouette.svg
规则（11 §1.1 / §1.2）：
  · 同一 1080×1080 坐标系，4 列×3 行 region 固定，不随容器重划分
  · 主体居中偏上 → contain 时四周主体完整；关键主体落在中央带 → cover 裁上下不丢主体
  · 正式图不含编号 / 虚线 / 关号 / 开发标注
  · silhouette 为同构图单色剪影（#EBD9C6），不是纯色方块、不用 full 替代
色彩全部取自 09 §1 Token。
"""
import os, math

OUT = r"E:/UnityProject/MutiplayGame/BlockOut/Assets/Resources/block/ch01"
SRC = os.path.join(OUT, ".source")
os.makedirs(SRC, exist_ok=True)

CREAM_TOP, CREAM_DEEP = "#FFFAF4", "#FFF1E3"
COCOA_60 = "#8A6E62"
CORAL, CORAL_DEEP = "#FF7568", "#FF6B5C"
MINT, MINT_DEEP, MINT_BG, MINT_TEXT = "#62CFA7", "#3BB98E", "#DFF6EC", "#2E7C5B"
BERRY, GOLD, GOLD_RIM, GOLD_LIGHT = "#F45F70", "#FFC53D", "#E3A22E", "#FFE9B0"
SIL = "#EBD9C6"

BLOCKS = {
    "A": ("#F8CCA0", "#F0AC6E"),
    "B": ("#A9E8CF", "#79D2B2"),
    "C": ("#CFC2F2", "#AC95E2"),
    "D": ("#FABCD0", "#F193AF"),
    "E": ("#FAE49B", "#F2C957"),
    "F": ("#B9D2F7", "#84B4EB"),
}


def head():
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080" width="1080" height="1080">',
        '  <defs>',
        '    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>' % (CREAM_TOP, CREAM_DEEP),
        '    <radialGradient id="glow" cx="0.5" cy="0.42" r="0.60">'
        '<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.95"/>'
        '<stop offset="0.60" stop-color="#FFFFFF" stop-opacity="0.32"/>'
        '<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient>',
        '    <linearGradient id="cream" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#FFF6E8"/><stop offset="1" stop-color="#F7E2C6"/></linearGradient>',
        '    <linearGradient id="creamLt" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#FFFBF3"/><stop offset="1" stop-color="#FBEBD5"/></linearGradient>',
        '    <linearGradient id="coralG" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>' % (CORAL, CORAL_DEEP),
        '  </defs>',
        '  <rect x="0" y="0" width="1080" height="1080" fill="url(#bg)"/>',
    ]


def star(cx, cy, r, fill=GOLD, stroke=GOLD_RIM):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.44
        a = -math.pi / 2 + i * math.pi / 5
        pts.append("%.1f,%.1f" % (cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return ['    <polygon points="%s" fill="%s" stroke="%s" stroke-width="2.5" stroke-linejoin="round"/>'
            % (" ".join(pts), fill, stroke)]


def candy(cx, cy, r, key, ring=True):
    c1, c2 = BLOCKS[key]
    s = []
    if ring:
        s.append('    <circle cx="%g" cy="%g" r="%g" fill="%s" stroke="#FFFFFF" stroke-width="4"/>' % (cx, cy, r, c2))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="url(#creamLt)" stroke="#FFFFFF" stroke-width="3"/>' % (cx, cy, r * 0.8))
    s.append('    <path d="M%g %g a%g %g 0 0 1 %g 0 z" fill="%s"/>'
             % (cx - r * 0.8, cy - r * 0.12, r * 0.8, r * 0.8, r * 1.6, c1))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="#FFFFFF" opacity="0.66"/>' % (cx - r * 0.3, cy - r * 0.44, r * 0.16))
    return s


def full_scene():
    s = head()
    s.append('  <circle cx="540" cy="452" r="336" fill="url(#glow)"/>')

    # 远景糖果（散布于 4×3 各区域）
    for cx, cy, r, k in [(150, 176, 42, "C"), (930, 168, 36, "F"), (300, 132, 24, "B"),
                         (786, 142, 26, "D"), (96, 646, 32, "D"), (986, 660, 30, "B"),
                         (126, 906, 36, "E"), (954, 916, 38, "A")]:
        s += candy(cx, cy, r, k)

    # 星星
    for cx, cy, r in [(250, 214, 46), (830, 196, 38), (906, 300, 27), (150, 380, 23), (944, 424, 21)]:
        s += star(cx, cy, r)

    # 云底座
    for cx, cy, rx in [(330, 806, 64), (540, 838, 76), (750, 806, 64)]:
        s.append('    <ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#FFFFFF" opacity="0.74"/>'
                 % (cx, cy, rx, rx * 0.64))

    # 蛋糕
    s.append('    <rect x="392" y="576" width="296" height="152" rx="18" fill="url(#cream)" stroke="#E8CDBB" stroke-width="3"/>')
    s.append('    <rect x="392" y="576" width="296" height="34" rx="16" fill="#FFF6EA"/>')
    s.append('    <rect x="392" y="664" width="296" height="18" fill="%s" opacity="0.5"/>' % BERRY)
    for i in range(9):
        s.append('    <circle cx="%g" cy="614" r="15" fill="#FFFFFF" stroke="#F0DCCB" stroke-width="2"/>' % (410 + i * 32))
    s.append('    <path d="M366 728h348l-18 30q-6 10-20 10H404q-14 0-20-10z" fill="%s" stroke="%s" stroke-width="3"/>'
             % (COCOA_60, COCOA_60))

    # 冰淇淋
    s.append('    <circle cx="540" cy="500" r="134" fill="url(#cream)" stroke="#FFFFFF" stroke-width="5"/>')
    s.append('    <circle cx="472" cy="468" r="88" fill="url(#creamLt)" stroke="#FFFFFF" stroke-width="5"/>')
    s.append('    <circle cx="614" cy="486" r="80" fill="url(#creamLt)" stroke="#FFFFFF" stroke-width="5"/>')
    s.append('    <path d="M406 512c24-32 48-20 68 2s46 32 68 4 48-26 68-2" fill="none" stroke="url(#coralG)" '
             'stroke-width="15" stroke-linecap="round"/>')

    # 樱桃 + 薄荷叶
    s.append('    <circle cx="540" cy="356" r="38" fill="%s" stroke="#FFFFFF" stroke-width="5"/>' % BERRY)
    s.append('    <circle cx="526" cy="342" r="13" fill="#FFFFFF" opacity="0.72"/>')
    s.append('    <path d="M540 318c8-24 28-32 46-28" fill="none" stroke="%s" stroke-width="7" stroke-linecap="round"/>' % MINT_DEEP)
    s.append('    <ellipse cx="598" cy="288" rx="28" ry="14" fill="%s" stroke="%s" stroke-width="2.5"/>' % (MINT, MINT_DEEP))

    # 前景糖果
    for cx, cy, r, k in [(268, 792, 46, "A"), (816, 788, 44, "C"), (372, 878, 36, "D"),
                         (712, 872, 38, "F"), (548, 906, 32, "E")]:
        s += candy(cx, cy, r, k)

    # 薄荷小旗
    s.append('    <rect x="700" y="392" width="8" height="98" rx="4" fill="%s"/>' % COCOA_60)
    s.append('    <path d="M708 396l74 23-74 23z" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>' % (MINT, MINT_DEEP))

    # 极淡内框：仅压暗四边，保证 contain 观感与安全边距（无任何文字/编号）
    s.append('  <rect x="6" y="6" width="1068" height="1068" rx="42" fill="none" stroke="%s" stroke-width="18" opacity="0.28"/>' % CREAM_DEEP)
    return s


def sil_scene():
    """同构图单色剪影：#EBD9C6 基底 + 层次用透明度区分，不用纯色方块替代。"""
    s = head()
    s.append('  <rect x="0" y="0" width="1080" height="1080" fill="%s"/>' % SIL)
    s.append('  <circle cx="540" cy="452" r="330" fill="#FFFFFF" opacity="0.30"/>')

    for cx, cy, r in [(150, 176, 42), (930, 168, 36), (300, 132, 24), (786, 142, 26),
                      (96, 646, 32), (986, 660, 30), (126, 906, 36), (954, 916, 38),
                      (268, 792, 46), (816, 788, 44), (372, 878, 36), (712, 872, 38), (548, 906, 32)]:
        s.append('    <circle cx="%g" cy="%g" r="%g" fill="#FFFFFF" opacity="0.20"/>' % (cx, cy, r))

    for cx, cy, r in [(250, 214, 46), (830, 196, 38), (906, 300, 27), (150, 380, 23), (944, 424, 21)]:
        s += star(cx, cy, r, "#FFFFFF", "#FFFFFF")

    for cx, cy, rx in [(330, 806, 64), (540, 838, 76), (750, 806, 64)]:
        s.append('    <ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#FFFFFF" opacity="0.24"/>' % (cx, cy, rx, rx * 0.64))

    s.append('    <rect x="392" y="576" width="296" height="152" rx="18" fill="#FFFFFF" opacity="0.42"/>')
    s.append('    <rect x="392" y="576" width="296" height="34" rx="16" fill="#FFFFFF" opacity="0.30"/>')
    for i in range(9):
        s.append('    <circle cx="%g" cy="614" r="15" fill="#FFFFFF" opacity="0.24"/>' % (410 + i * 32))
    s.append('    <path d="M366 728h348l-18 30q-6 10-20 10H404q-14 0-20-10z" fill="#FFFFFF" opacity="0.34"/>')

    s.append('    <circle cx="540" cy="500" r="134" fill="#FFFFFF" opacity="0.46"/>')
    s.append('    <circle cx="472" cy="468" r="88" fill="#FFFFFF" opacity="0.38"/>')
    s.append('    <circle cx="614" cy="486" r="80" fill="#FFFFFF" opacity="0.38"/>')
    s.append('    <path d="M406 512c24-32 48-20 68 2s46 32 68 4 48-26 68-2" fill="none" stroke="#FFFFFF" '
             'stroke-width="15" stroke-linecap="round" opacity="0.34"/>')
    s.append('    <circle cx="540" cy="356" r="38" fill="#FFFFFF" opacity="0.40"/>')
    s.append('    <ellipse cx="598" cy="288" rx="28" ry="14" fill="#FFFFFF" opacity="0.36"/>')

    s.append('    <rect x="700" y="392" width="8" height="98" rx="4" fill="#FFFFFF" opacity="0.36"/>')
    s.append('    <path d="M708 396l74 23-74 23z" fill="#FFFFFF" opacity="0.36"/>')

    s.append('  <rect x="6" y="6" width="1068" height="1068" rx="42" fill="none" stroke="#FFFFFF" stroke-width="18" opacity="0.14"/>')
    return s


def write(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines + ["</svg>"]))
    print("wrote", path)


write(os.path.join(SRC, "ch01_full.svg"), full_scene())
write(os.path.join(SRC, "ch01_preview.svg"), full_scene())
write(os.path.join(SRC, "ch01_silhouette.svg"), sil_scene())
print("OK")