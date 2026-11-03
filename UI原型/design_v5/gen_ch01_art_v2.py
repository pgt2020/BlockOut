# -*- coding: utf-8 -*-
"""第一章章节插画 v2（视觉精修）。
相对 v1 的改动（任务二要求）：
  1. 背景改为**冷调薄荷奶油**并加径向压暗，主体（蛋糕/冰淇淋）改为**暖奶油高光 + 可可描边**，
     主体与背景的明度差从 ~8% 提到 ~25%，轮廓用 6px 可可色 + 外发光，不再糊在一起。
  2. 主体加投影（dy=10 blur 近似：多层低透明偏移椭圆），前后景分明。
  3. **按 4×3 十二区逐区布置内容**：每区至少一个可辨认元素（糖果/星/棒棒糖/云/cherry），
     避免出现连续大面积纯背景；连续解锁时每次都有新东西出现。
  4. 保持 1080×1080 画布与 region 坐标不变（每区 270×360），不移动主体位置。
色彩仍取自 09 §1 Token。
"""
import os, math

OUT = r"E:/UnityProject/MutiplayGame/BlockOut/Assets/Resources/block/ch01"
SRC = os.path.join(OUT, ".source")
os.makedirs(SRC, exist_ok=True)

CREAM_TOP, CREAM_DEEP = "#FFFAF4", "#FFF1E3"
BG_TOP, BG_BOT = "#EAF7F1", "#D8EFE6"      # 冷调薄荷奶油背景（拉开与暖主体对比）
COCOA, COCOA_60 = "#553B36", "#8A6E62"
CORAL, CORAL_DEEP = "#FF7568", "#FF6B5C"
MINT, MINT_DEEP, MINT_BG, MINT_TEXT = "#62CFA7", "#3BB98E", "#DFF6EC", "#2E7C5B"
BERRY, GOLD, GOLD_RIM, GOLD_LIGHT = "#F45F70", "#FFC53D", "#E3A22E", "#FFE9B0"
SIL, LOCK = "#EBD9C6", "#8A6E62"

BLOCKS = {
    "A": ("#F8CCA0", "#F0AC6E"),
    "B": ("#A9E8CF", "#79D2B2"),
    "C": ("#CFC2F2", "#AC95E2"),
    "D": ("#FABCD0", "#F193AF"),
    "E": ("#FAE49B", "#F2C957"),
    "F": ("#B9D2F7", "#84B4EB"),
}
# 区域网格：4 列 × 3 行，每区 270×360
CW, CH = 270, 360
# 主体包围盒（保持与 v1 一致，region 坐标不变）
SUBJECT = (366, 280, 782, 768)


def head():
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 1080" width="1080" height="1080">',
        '  <defs>',
        '    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>' % (BG_TOP, BG_BOT),
        '    <radialGradient id="vig" cx="0.5" cy="0.46" r="0.72">'
        '<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.55"/>'
        '<stop offset="0.62" stop-color="#FFFFFF" stop-opacity="0.10"/>'
        '<stop offset="1" stop-color="#7FB8A4" stop-opacity="0.30"/></radialGradient>',
        # 主体奶油：暖白高光 → 奶黄暗部，与冷背景形成明确明度/色温差
        '    <linearGradient id="cream" x1="0.25" y1="0" x2="0.7" y2="1">'
        '<stop offset="0" stop-color="#FFFBF0"/><stop offset="0.5" stop-color="#FDEBC8"/>'
        '<stop offset="1" stop-color="#F0D3A2"/></linearGradient>',
        '    <linearGradient id="creamLt" x1="0.2" y1="0" x2="0.8" y2="1">'
        '<stop offset="0" stop-color="#FFFDF6"/><stop offset="0.55" stop-color="#FFF4DC"/>'
        '<stop offset="1" stop-color="#F6DDB2"/></linearGradient>',
        '    <linearGradient id="coralG" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>' % (CORAL, CORAL_DEEP),
        # 投影：多层递减透明椭圆模拟柔和阴影
        '    <radialGradient id="sh" cx="0.5" cy="0.5" r="0.5">'
        '<stop offset="0" stop-color="#5A7F72" stop-opacity="0.34"/>'
        '<stop offset="0.6" stop-color="#5A7F72" stop-opacity="0.16"/>'
        '<stop offset="1" stop-color="#5A7F72" stop-opacity="0"/></radialGradient>',
        '    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">'
        '<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.85"/>'
        '<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient>',
        '  </defs>',
        '  <rect x="0" y="0" width="1080" height="1080" fill="url(#bg)"/>',
        '  <circle cx="540" cy="500" r="430" fill="url(#glow)"/>',
    ]


def star(cx, cy, r, fill=GOLD, stroke=GOLD_RIM):
    pts = []
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.44
        a = -math.pi / 2 + i * math.pi / 5
        pts.append("%.1f,%.1f" % (cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return ['    <polygon points="%s" fill="%s" stroke="%s" stroke-width="3" stroke-linejoin="round"/>'
            % (" ".join(pts), fill, stroke)]


def candy(cx, cy, r, key):
    """糖果球：外环深色 + 内体渐变 + 白高光。"""
    c1, c2 = BLOCKS[key]
    s = ['    <circle cx="%g" cy="%g" r="%g" fill="%s" stroke="%s" stroke-width="4"/>'
         % (cx + 4, cy + 8, r, "#5A7F72", "none")]          # 落影
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="%s" stroke="%s" stroke-width="4.5"/>' % (cx, cy, r, c2, COCOA))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="url(#creamLt)"/>' % (cx, cy, r * 0.78))
    s.append('    <path d="M%g %g a%g %g 0 0 1 %g 0 z" fill="%s"/>'
             % (cx - r * 0.78, cy - r * 0.1, r * 0.78, r * 0.78, r * 1.56, c1))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="#FFFFFF" opacity="0.85"/>'
             % (cx - r * 0.32, cy - r * 0.42, r * 0.18))
    return s


def lollipop(cx, cy, r, key):
    """棒棒糖：环 + 旋涡 + 柄。"""
    c1, c2 = BLOCKS[key]
    s = ['    <rect x="%g" y="%g" width="10" height="%g" rx="5" fill="%s" stroke="%s" stroke-width="3"/>'
         % (cx - 5, cy + r * 0.7, r * 1.5, "#FFFDF8", COCOA)]
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="%s" stroke="%s" stroke-width="4.5"/>' % (cx, cy, r, c2, COCOA))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" stroke-width="7"/>' % (cx, cy, r * 0.62, c1))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="none" stroke="%s" stroke-width="5"/>' % (cx, cy, r * 0.3, c2))
    s.append('    <circle cx="%g" cy="%g" r="%g" fill="#FFFFFF" opacity="0.7"/>' % (cx - r * 0.36, cy - r * 0.4, r * 0.14))
    return s


def full_scene():
    s = head()

    # ================= 按 4×3 十二区逐区布置内容 =================
    # 区1 (0-270, 0-360)：棒棒糖紫 + 星 + 小糖果
    s += lollipop(96, 150, 46, "C")
    s += star(214, 96, 34)
    s += candy(228, 268, 28, "B")
    # 区2 (270-540, 0-360)：星 + 小旗杆顶 + 薄荷叶
    s += star(392, 120, 30, "#FFC53D", GOLD_RIM)
    s += candy(462, 286, 30, "D")
    # 区3 (540-810, 0-360)：大星 + 糖果
    s += star(700, 130, 42)
    s += candy(742, 292, 26, "F")
    # 区4 (810-1080, 0-360)：糖果蓝 + 棒棒糖粉 + 星
    s += candy(898, 152, 38, "F")
    s += lollipop(1006, 268, 34, "D")
    s += star(964, 92, 26)

    # 区5 (0-270, 360-720)：糖果橙 + 星 + 小糖果（左侧留白给主体）
    s += candy(120, 452, 34, "A")
    s += star(206, 566, 28)
    s += candy(86, 654, 26, "E")
    # 区6 (270-540, 360-720)：主体左半（蛋糕+冰淇淋左球）
    # 区7 (540-810, 360-720)：主体右半（冰淇淋右球 + 旗）
    # 区8 (810-1080, 360-720)：糖果黄 + 星
    s += candy(952, 470, 32, "E")
    s += star(898, 596, 30)
    s += candy(1004, 676, 24, "B")

    # 区9 (0-270, 720-1080)：棒棒糖薄荷 + 糖果粉
    s += lollipop(112, 812, 42, "B")
    s += candy(212, 946, 30, "D")
    # 区10 (270-540, 720-1080)：糖果紫 + 星（前景）
    s += candy(360, 872, 38, "C")
    s += star(468, 962, 28)
    # 区11 (540-810, 720-1080)：糖果黄 + 糖果蓝（前景）
    s += candy(620, 886, 34, "E")
    s += candy(742, 972, 28, "F")
    # 区12 (810-1080, 720-1080)：糖果橙 + 星
    s += candy(892, 878, 36, "A")
    s += star(1000, 962, 30)

    # ================= 云底座（增强前后景） =================
    s.append('    <ellipse cx="540" cy="812" rx="330" ry="52" fill="url(#sh)"/>')
    for cx, cy, rx in [(312, 792, 74), (540, 820, 86), (768, 792, 74)]:
        s.append('    <ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#FFFFFF" stroke="%s" stroke-width="3"/>'
                 % (cx, cy, rx, rx * 0.62, "#B9D9CC"))

    # ================= 主体投影 =================
    s.append('    <ellipse cx="574" cy="782" rx="230" ry="40" fill="url(#sh)"/>')

    # ================= 蛋糕 =================
    s.append('    <rect x="386" y="572" width="308" height="158" rx="20" fill="url(#cream)" stroke="%s" stroke-width="5"/>' % COCOA)
    s.append('    <rect x="386" y="572" width="308" height="36" rx="17" fill="#FFFBF0" stroke="%s" stroke-width="4"/>' % COCOA)
    s.append('    <rect x="386" y="662" width="308" height="20" fill="%s" opacity="0.85"/>' % BERRY)
    for i in range(9):
        s.append('    <circle cx="%g" cy="616" r="16" fill="#FFFDF6" stroke="%s" stroke-width="3"/>'
                 % (406 + i * 33, COCOA_60))
    # 盘子
    s.append('    <path d="M358 730h364l-20 32q-7 11-22 11H400q-15 0-22-11z" fill="%s" stroke="%s" stroke-width="5"/>'
             % (COCOA_60, COCOA))

    # ================= 冰淇淋（暖奶油 + 可可描边 + 外发光） =================
    s.append('    <circle cx="540" cy="504" r="152" fill="#FFF6DF" opacity="0.55"/>')   # 外发光
    s.append('    <circle cx="540" cy="500" r="134" fill="url(#cream)" stroke="%s" stroke-width="6"/>' % COCOA)
    s.append('    <circle cx="470" cy="466" r="88" fill="url(#creamLt)" stroke="%s" stroke-width="5"/>' % COCOA)
    s.append('    <circle cx="616" cy="484" r="80" fill="url(#creamLt)" stroke="%s" stroke-width="5"/>' % COCOA)
    # 淋酱
    s.append('    <path d="M404 514c25-34 50-21 70 2s48 34 70 4 50-27 70-2" fill="none" stroke="url(#coralG)" '
             'stroke-width="17" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append('    <path d="M404 514c25-34 50-21 70 2s48 34 70 4 50-27 70-2" fill="none" stroke="%s" '
             'stroke-width="2.5" stroke-linecap="round" opacity="0.35"/>' % COCOA)
    # 樱桃
    s.append('    <circle cx="540" cy="352" r="42" fill="%s" stroke="%s" stroke-width="5"/>' % (BERRY, COCOA))
    s.append('    <circle cx="524" cy="336" r="14" fill="#FFFFFF" opacity="0.8"/>')
    s.append('    <path d="M540 310c9-26 30-35 50-30" fill="none" stroke="%s" stroke-width="8" stroke-linecap="round"/>' % MINT_DEEP)
    s.append('    <ellipse cx="602" cy="278" rx="31" ry="16" fill="%s" stroke="%s" stroke-width="3"/>' % (MINT, MINT_DEEP))

    # ================= 薄荷小旗（右侧，平衡构图） =================
    s.append('    <rect x="712" y="392" width="9" height="104" rx="4.5" fill="%s" stroke="%s" stroke-width="3"/>' % (COCOA_60, COCOA))
    s.append('    <path d="M721 396l80 25-80 25z" fill="%s" stroke="%s" stroke-width="4" stroke-linejoin="round"/>' % (MINT, COCOA))

    # ================= 前景糖果（压底座前，加层次） =================
    for cx, cy, r, k in [(252, 782, 48, "A"), (830, 778, 46, "C"),
                         (356, 884, 36, "D"), (726, 878, 38, "F"), (546, 902, 32, "E")]:
        s += candy(cx, cy, r, k)

    # ================= 暗角（收拢视线） =================
    s.append('  <rect x="0" y="0" width="1080" height="1080" fill="url(#vig)"/>')
    # 极淡内框：压暗四边保证 contain 观感（无文字/编号）
    s.append('  <rect x="6" y="6" width="1068" height="1068" rx="42" fill="none" stroke="%s" stroke-width="20" opacity="0.26"/>' % BG_BOT)
    return s


def sil_scene():
    """同构图剪影：#EBD9C6 基底 + 层次用透明度与描边区分，保留可辨认轮廓。
    不用纯色方块、不用 full 替代。"""
    s = head()
    s.append('  <rect x="0" y="0" width="1080" height="1080" fill="%s"/>' % SIL)

    # 背景区元素（浅）
    for cx, cy, r in [(96, 150, 46), (228, 268, 28), (462, 286, 30), (742, 292, 26),
                      (898, 152, 38), (1006, 268, 34), (120, 452, 34), (86, 654, 26),
                      (952, 470, 32), (1004, 676, 24), (112, 812, 42), (212, 946, 30),
                      (360, 872, 38), (620, 886, 34), (742, 972, 28), (892, 878, 36)]:
        s.append('    <circle cx="%g" cy="%g" r="%g" fill="#FFFFFF" opacity="0.30"/>' % (cx, cy, r))
    for cx, cy, r in [(214, 96, 34), (392, 120, 30), (700, 130, 42), (964, 92, 26),
                      (206, 566, 28), (898, 596, 30), (468, 962, 28), (1000, 962, 30)]:
        s += star(cx, cy, r, "#FFFFFF", "#FFFFFF")

    # 云底座
    s.append('    <ellipse cx="540" cy="812" rx="330" ry="52" fill="#FFFFFF" opacity="0.18"/>')
    for cx, cy, rx in [(312, 792, 74), (540, 820, 86), (768, 792, 74)]:
        s.append('    <ellipse cx="%g" cy="%g" rx="%g" ry="%g" fill="#FFFFFF" opacity="0.34"/>' % (cx, cy, rx, rx * 0.62))

    # 主体（中深）
    s.append('    <rect x="386" y="572" width="308" height="158" rx="20" fill="#FFFFFF" opacity="0.46"/>')
    s.append('    <rect x="386" y="572" width="308" height="36" rx="17" fill="#FFFFFF" opacity="0.30"/>')
    for i in range(9):
        s.append('    <circle cx="%g" cy="616" r="16" fill="#FFFFFF" opacity="0.26"/>' % (406 + i * 33))
    s.append('    <path d="M358 730h364l-20 32q-7 11-22 11H400q-15 0-22-11z" fill="#FFFFFF" opacity="0.38"/>')
    s.append('    <circle cx="540" cy="500" r="134" fill="#FFFFFF" opacity="0.50"/>')
    s.append('    <circle cx="470" cy="466" r="88" fill="#FFFFFF" opacity="0.40"/>')
    s.append('    <circle cx="616" cy="484" r="80" fill="#FFFFFF" opacity="0.40"/>')
    s.append('    <path d="M404 514c25-34 50-21 70 2s48 34 70 4 50-27 70-2" fill="none" stroke="#FFFFFF" '
             'stroke-width="17" stroke-linecap="round" opacity="0.38"/>')
    s.append('    <circle cx="540" cy="352" r="42" fill="#FFFFFF" opacity="0.44"/>')
    s.append('    <ellipse cx="602" cy="278" rx="31" ry="16" fill="#FFFFFF" opacity="0.38"/>')
    s.append('    <rect x="712" y="392" width="9" height="104" rx="4.5" fill="#FFFFFF" opacity="0.40"/>')
    s.append('    <path d="M721 396l80 25-80 25z" fill="#FFFFFF" opacity="0.40"/>')

    # 前景（深）
    for cx, cy, r in [(252, 782, 48), (830, 778, 46), (356, 884, 36), (726, 878, 38), (546, 902, 32)]:
        s.append('    <circle cx="%g" cy="%g" r="%g" fill="#FFFFFF" opacity="0.28"/>' % (cx, cy, r))

    s.append('  <rect x="0" y="0" width="1080" height="1080" fill="url(#vig)" opacity="0.5"/>')
    s.append('  <rect x="6" y="6" width="1068" height="1068" rx="42" fill="none" stroke="#FFFFFF" stroke-width="20" opacity="0.16"/>')
    return s


def write(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines + ["</svg>"]))
    print("wrote", path)


if __name__ == "__main__":
    write(os.path.join(SRC, "ch01_full.svg"), full_scene())
    write(os.path.join(SRC, "ch01_preview.svg"), full_scene())
    write(os.path.join(SRC, "ch01_silhouette.svg"), sil_scene())
    print("OK — 画布 1080×1080，region 坐标未变，主体包围盒", SUBJECT)
