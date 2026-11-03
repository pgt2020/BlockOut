# -*- coding: utf-8 -*-
"""第一章章节插画 v3（精修·立体感与构图秩序）。
在 v2 基础上解决三个残留问题：
  1. 主体仍偏平 → 强化明暗（暗部用暖褐而非灰）、加高光、描边加粗、投影更实
  2. 外围糖果散乱 → 改为**中下缘花环式聚集**（底部两簇 + 左右各一簇），上部留白，
     形成"中心主体 + 底部花环 + 上方星光"的三段式秩序
  3. 盘子发灰 → 改暖陶色 #D9A05B，与奶油主体同色系
同时保证：画布 1080×1080 不变、region 坐标不变、主体包围盒基本不变，
4×3 十二区每区仍有可辨认内容（避免连续大面积纯背景）。
"""
import os, math

OUT = r"E:/UnityProject/MutiplayGame/BlockOut/Assets/Resources/block/ch01"
SRC = os.path.join(OUT, ".source")

BG_TOP, BG_BOT = "#DFF1EA", "#C4E4D9"
COCOA, COCOA_60 = "#553B36", "#8A6E62"
CORAL, CORAL_DEEP = "#FF7568", "#FF6B5C"
MINT, MINT_DEEP = "#62CFA7", "#3BB98E"
BERRY, GOLD, GOLD_RIM = "#F45F70", "#FFC53D", "#E3A22E"
SIL = "#EBD9C6"

BLOCKS = {
    "A": ("#F8CCA0", "#F0AC6E"),
    "B": ("#A9E8CF", "#79D2B2"),
    "C": ("#CFC2F2", "#AC95E2"),
    "D": ("#FABCD0", "#F193AF"),
    "E": ("#FAE49B", "#F2C957"),
    "F": ("#B9D2F7", "#84B4EB"),
}
# 暗部色（暖褐，用于立体暗面）
SHADE = "#E0BC8C"
DEEP = "#C99A66"


def head():
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080" width="1080" height="1080">',
        '  <defs>',
        '    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>' % (BG_TOP, BG_BOT),
        '    <radialGradient id="vig" cx="0.5" cy="0.44" r="0.74">'
        '<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.60"/>'
        '<stop offset="0.58" stop-color="#FFFFFF" stop-opacity="0.12"/>'
        '<stop offset="1" stop-color="#4E9B84" stop-opacity="0.42"/></radialGradient>',
        '    <linearGradient id="cream" x1="0.22" y1="0" x2="0.78" y2="1">'
        '<stop offset="0" stop-color="#FFFCF3"/><stop offset="0.45" stop-color="#FDEFCF"/>'
        '<stop offset="1" stop-color="%s"/></linearGradient>' % SHADE,
        '    <linearGradient id="creamLt" x1="0.18" y1="0" x2="0.82" y2="1">'
        '<stop offset="0" stop-color="#FFFEF9"/><stop offset="0.5" stop-color="#FFF6E2"/>'
        '<stop offset="1" stop-color="%s"/></linearGradient>' % DEEP,
        '    <linearGradient id="coralG" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#FF8B7E"/><stop offset="1" stop-color="%s"/></linearGradient>' % CORAL_DEEP,
        '    <linearGradient id="plateG" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#E8B571"/><stop offset="1" stop-color="#C98A45"/></linearGradient>',
        '    <radialGradient id="sh" cx="0.5" cy="0.5" r="0.5">'
        '<stop offset="0" stop-color="#3F7A66" stop-opacity="0.40"/>'
        '<stop offset="0.62" stop-color="#3F7A66" stop-opacity="0.18"/>'
        '<stop offset="1" stop-color="#3F7A66" stop-opacity="0"/></radialGradient>',
        '    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">'
        '<stop offset="0" stop-color="#FFF8E2" stop-opacity="0.92"/>'
        '<stop offset="1" stop-color="#FFF8E2" stop-opacity="0"/></radialGradient>',
        '  </defs>',
        '  <rect x="0" y="0" width="1080" height="1080" fill="url(#bg)"/>',
        '  <circle cx="540" cy="470" r="400" fill="url(#glow)"/>',
    ]


def star(cx, cy, r, fill=GOLD, stroke=GOLD_RIM):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.44
        a = -math.pi / 2 + i * math.pi / 5
        pts.append("%.1f,%.1f" % (cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return ['    <polygon points="%s" fill="%s" stroke="%s" stroke-width="3.5" stroke-linejoin="round"/>'
            % (" ".join(pts), fill, stroke)]


def candy(cx, cy, r, key, shadow=True):
    """糖果球：实投影 + 深色外环 + 渐变体 + 高光。"""
    c1, c2 = BLOCKS[key]
    s = []
    if shadow:
        s.append('    <ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#3F7A66" opacity="0.26"/>'
                 % (cx + 5, cy + r * 0.92, r * 0.92, r * 0.26))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="%s" stroke="%s" stroke-width="5"/>' % (cx, cy, r, c2, COCOA))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="url(#creamLt)"/>' % (cx, cy, r * 0.76))
    s.append('    <path d="M%g %g a%g %g 0 0 1 %g 0 z" fill="%s"/>'
             % (cx - r * 0.76, cy - r * 0.08, r * 0.76, r * 0.76, r * 1.52, c1))
    s.append('    <ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#FFFFFF" opacity="0.88"/>'
             % (cx - r * 0.3, cy - r * 0.42, r * 0.2, r * 0.13))
    return s


def lollipop(cx, cy, r, key):
    c1, c2 = BLOCKS[key]
    s = ['    <ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#3F7A66" opacity="0.24"/>'
         % (cx + 4, cy + r * 2.1, r * 0.5, r * 0.18)]
    s.append('    <rect x="%g" y="%g" width="11" height="%g" rx="5.5" fill="#FFFDF6" stroke="%s" stroke-width="3.5"/>'
             % (cx - 5.5, cy + r * 0.72, r * 1.5, COCOA))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="%s" stroke="%s" stroke-width="5"/>' % (cx, cy, r, c2, COCOA))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" stroke-width="8"/>' % (cx, cy, r * 0.6, c1))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" stroke-width="5"/>' % (cx, cy, r * 0.28, c2))
    s.append('    <ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#FFFFFF" opacity="0.72"/>'
             % (cx - r * 0.34, cy - r * 0.42, r * 0.16, r * 0.11))
    return s


def full_scene():
    s = head()

    # ================= 上方星光带（区1–区4 上部） =================
    s += lollipop(104, 158, 48, "C")      # 区1
    s += star(226, 92, 32)                 # 区1
    s += candy(268, 320, 26, "B")          # 区1/区2 交界
    # 区2 (270-540, 0-360)：补强（原变化率偏低）
    s += candy(346, 128, 32, "D")
    s += star(452, 216, 28)
    s += candy(310, 268, 26, "F")
    # 区3 (540-810, 0-360)
    s += star(614, 96, 26)
    s += star(706, 118, 40)
    s += candy(752, 288, 26, "F")
    s += candy(608, 300, 24, "E")
    # 区4 (810-1080, 0-360)：补强（原变化率偏低）
    s += candy(910, 156, 40, "F")
    s += star(982, 96, 26)
    s += candy(1000, 300, 24, "E")
    s += star(866, 246, 28)
    s += candy(944, 330, 24, "C")

    # ================= 中段左右（区5 / 区8）——分区检查显示这两区偏空，加密内容 =================
    # 区5 (0-270, 360-720)：三颗糖 + 两颗星，满铺
    s += candy(88, 430, 40, "A")
    s += candy(196, 508, 34, "F")
    s += candy(74, 592, 32, "E")
    s += candy(178, 664, 30, "B")
    s += star(140, 372, 26)
    s += star(226, 578, 24)
    # 区8 (810-1080, 360-720)：同样满铺
    s += candy(986, 432, 38, "E")
    s += candy(880, 512, 34, "D")
    s += candy(1006, 596, 32, "C")
    s += candy(892, 668, 30, "A")
    s += star(940, 374, 26)
    s += star(866, 580, 24)

    # ================= 底部花环（区9–区12，成簇，左右下三簇 + 中下两簇，避免堆叠） =================
    # 左簇（区9）
    s += lollipop(106, 800, 44, "B")
    s += candy(222, 928, 32, "D")
    # 中左簇（区10）
    s += candy(342, 856, 38, "C")
    s += star(452, 946, 26)
    # 中右簇（区11）
    s += candy(742, 862, 34, "F")
    s += candy(640, 950, 28, "E")
    # 右簇（区12）
    s += candy(900, 862, 36, "A")
    s += star(1004, 948, 28)

    # ================= 云底座 =================
    s.append('    <ellipse cx="540" cy="816" rx="336" ry="54" fill="url(#sh)"/>')
    for cx, cy, rx in [(308, 790, 76), (540, 820, 88), (772, 790, 76)]:
        s.append('    <ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#FFFDF8" stroke="#A8CFC1" stroke-width="3.5"/>'
                 % (cx, cy, rx, rx * 0.6))

    # ================= 主体投影 =================
    s.append('    <ellipse cx="578" cy="788" rx="236" ry="42" fill="url(#sh)"/>')

    # ================= 蛋糕 =================
    s.append('    <rect x="384" y="570" width="312" height="162" rx="22" fill="url(#cream)" stroke="%s" stroke-width="6"/>' % COCOA)
    s.append('    <rect x="384" y="570" width="312" height="38" rx="18" fill="#FFFDF4" stroke="%s" stroke-width="4.5"/>' % COCOA)
    s.append('    <rect x="384" y="662" width="312" height="22" fill="%s"/>' % BERRY)
    s.append('    <rect x="384" y="662" width="312" height="22" fill="%s" opacity="0.35"/>' % COCOA)
    for i in range(9):
        s.append('    <circle cx="%g" cy="616" r="17" fill="#FFFEF8" stroke="%s" stroke-width="3.5"/>'
                 % (404 + i * 33, COCOA_60))
    # 盘子（暖陶色）
    s.append('    <path d="M354 732h372l-22 34q-8 12-24 12H400q-16 0-24-12z" fill="url(#plateG)" stroke="%s" stroke-width="6"/>' % COCOA)

    # ================= 冰淇淋 =================
    s.append('    <circle cx="540" cy="502" r="158" fill="#FFE9B8" opacity="0.55"/>')     # 外发光（暖调，与主体同色系）
    s.append('    <circle cx="540" cy="500" r="136" fill="url(#cream)" stroke="%s" stroke-width="8"/>' % COCOA)
    s.append('    <circle cx="468" cy="464" r="90" fill="url(#creamLt)" stroke="%s" stroke-width="7"/>' % COCOA)
    s.append('    <circle cx="618" cy="482" r="82" fill="url(#creamLt)" stroke="%s" stroke-width="7"/>' % COCOA)
    # 暗面（右下弧形，加明暗层次）
    s.append('    <path d="M604 396a136 136 0 0 1 0 208z" fill="%s" opacity="0.30"/>' % DEEP)
    s.append('    <path d="M534 384a90 90 0 0 1 0 160z" fill="%s" opacity="0.24"/>' % DEEP)
    s.append('    <path d="M660 434a82 82 0 0 1 0 96z" fill="%s" opacity="0.26"/>' % DEEP)
    # 高光
    s.append('    <ellipse cx="488" cy="416" rx="44" ry="28" fill="#FFFFFF" opacity="0.6" transform="rotate(-22 488 416)"/>')
    # 淋酱
    s.append('    <path d="M400 512c26-36 52-22 72 2s50 36 72 4 52-29 72-2" fill="none" stroke="url(#coralG)" '
             'stroke-width="18" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append('    <path d="M400 512c26-36 52-22 72 2s50 36 72 4 52-29 72-2" fill="none" stroke="%s" '
             'stroke-width="3" stroke-linecap="round" opacity="0.4"/>' % COCOA)
    # 樱桃
    s.append('    <circle cx="540" cy="350" r="44" fill="%s" stroke="%s" stroke-width="6"/>' % (BERRY, COCOA))
    s.append('    <path d="M540 356a44 44 0 0 0 40 26z" fill="%s" opacity="0.4"/>' % COCOA)
    s.append('    <ellipse cx="520" cy="332" rx="15" ry="11" fill="#FFFFFF" opacity="0.85" transform="rotate(-25 520 332)"/>')
    s.append('    <path d="M540 306c10-28 32-37 52-32" fill="none" stroke="%s" stroke-width="9" stroke-linecap="round"/>' % MINT_DEEP)
    s.append('    <ellipse cx="606" cy="272" rx="33" ry="17" fill="%s" stroke="%s" stroke-width="4"/>' % (MINT, MINT_DEEP))

    # ================= 薄荷小旗 =================
    s.append('    <rect x="716" y="386" width="10" height="112" rx="5" fill="%s" stroke="%s" stroke-width="4"/>' % (COCOA_60, COCOA))
    s.append('    <path d="M726 390l84 27-84 27z" fill="%s" stroke="%s" stroke-width="4.5" stroke-linejoin="round"/>' % (MINT, COCOA))

    # ================= 前景糖果（左右各一，贴底座两侧压层次，中间留空给盘子） =================
    for cx, cy, r, k in [(214, 764, 48, "A"), (866, 760, 46, "C")]:
        s += candy(cx, cy, r, k)

    s.append('  <rect x="0" y="0" width="1080" height="1080" fill="url(#vig)"/>')
    s.append('  <rect x="6" y="6" width="1068" height="1068" rx="42" fill="none" stroke="%s" stroke-width="20" opacity="0.24"/>' % BG_BOT)
    return s


def sil_scene():
    """同构图剪影：#EBD9C6 基底 + 去饱和暖灰层次。
    不用纯色方块、不用 full 替代。
    与 full 保持明显可区分：剪影整体降饱和 + 压暗，揭晓瞬间色彩与明度同时跃升。"""
    s = head()
    s.append('  <rect x="0" y="0" width="1080" height="1080" fill="%s"/>' % SIL)
    BGEL = [(104, 158, 48), (268, 320, 26), (346, 128, 32), (310, 268, 26),
            (452, 216, 28), (752, 288, 26), (608, 300, 24), (910, 156, 40),
            (1000, 300, 24), (866, 246, 28), (944, 330, 24),
            (88, 430, 40), (196, 508, 34), (74, 592, 32), (178, 664, 30),
            (986, 432, 38), (880, 512, 34), (1006, 596, 32), (892, 668, 30),
            (222, 928, 32), (342, 856, 38), (742, 862, 34), (640, 950, 28),
            (900, 862, 36), (214, 764, 48), (866, 760, 46)]
    for cx, cy, r in BGEL:
        s.append('    <circle cx="%g" cy="%g" r="%g" fill="#C9B49B" opacity="0.55"/>' % (cx, cy, r))
    STEL = [(226, 92, 32), (452, 216, 28), (614, 96, 26), (706, 118, 40),
            (982, 96, 26), (866, 246, 28), (140, 372, 26), (226, 578, 24),
            (940, 374, 26), (866, 580, 24), (452, 946, 26), (1004, 948, 28)]
    for cx, cy, r in STEL:
        s += star(cx, cy, r, "#D8C4AC", "#C9B49B")
    for cx, cy, r in [(106, 800, 44), (104, 158, 48)]:
        s.append('    <rect x="%g" y="%g" width="11" height="%g" rx="5.5" fill="#C9B49B" opacity="0.55"/>'
                 % (cx - 5.5, cy + r * 0.72, r * 1.5))
    s.append('    <ellipse cx="540" cy="816" rx="336" ry="54" fill="#C9B49B" opacity="0.34"/>')
    for cx, cy, rx in [(308, 790, 76), (540, 820, 88), (772, 790, 76)]:
        s.append('    <ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#BFA894" opacity="0.55"/>' % (cx, cy, rx, rx * 0.6))
    s.append('    <rect x="384" y="570" width="312" height="162" rx="22" fill="#F3E6D2" opacity="0.80"/>')
    s.append('    <rect x="384" y="570" width="312" height="38" rx="18" fill="#FFF8EC" opacity="0.62"/>')
    for i in range(9):
        s.append('    <circle cx="%g" cy="616" r="17" fill="#FFF8EC" opacity="0.55"/>' % (404 + i * 33))
    s.append('    <path d="M354 732h372l-22 34q-8 12-24 12H400q-16 0-24-12z" fill="#D8C0A2" opacity="0.72"/>')
    s.append('    <circle cx="540" cy="500" r="136" fill="#F7ECDA" opacity="0.85"/>')
    s.append('    <circle cx="468" cy="464" r="90" fill="#FFFBF2" opacity="0.66"/>')
    s.append('    <circle cx="618" cy="482" r="82" fill="#FFFBF2" opacity="0.66"/>')
    s.append('    <path d="M400 512c26-36 52-22 72 2s50 36 72 4 52-29 72-2" fill="none" stroke="#D9AFA6" '
             'stroke-width="18" stroke-linecap="round" opacity="0.55"/>')
    s.append('    <circle cx="540" cy="350" r="44" fill="#E8B0AE" opacity="0.68"/>')
    s.append('    <ellipse cx="606" cy="272" rx="33" ry="17" fill="#AFC8BC" opacity="0.62"/>')
    s.append('    <rect x="716" y="386" width="10" height="112" rx="5" fill="#C9B49B" opacity="0.66"/>')
    s.append('    <path d="M726 390l84 27-84 27z" fill="#AFC8BC" opacity="0.66"/>')
    s.append('  <rect x="0" y="0" width="1080" height="1080" fill="url(#vig)" opacity="0.62"/>')
    s.append('  <rect x="6" y="6" width="1068" height="1068" rx="42" fill="none" stroke="#C4AE96" stroke-width="20" opacity="0.4"/>')
    return s


def write(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines + ["</svg>"]))
    print("wrote", path)


if __name__ == "__main__":
    write(os.path.join(SRC, "ch01_full.svg"), full_scene())
    write(os.path.join(SRC, "ch01_preview.svg"), full_scene())
    write(os.path.join(SRC, "ch01_silhouette.svg"), sil_scene())
    print("OK v3")
