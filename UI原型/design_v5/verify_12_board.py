# -*- coding: utf-8 -*-
"""12_screen_adapt_360 棋盘结构校验：验证缩放后棋盘与 04 定稿一致。
注意：04 数据表用 (col, y)，y=5 在顶部；本脚本 row=0 为顶部，转换 row_idx = 5 - y。
棋盘框 SVG (438,202) 324x324，格 54；采样格心偏移 (+20,+20) 避开居中箭头。"""
from PIL import Image

PNG = "12_screen_adapt_360.png"
S = 2
OX, OY, CELL = 438.0, 202.0, 54.0

# (col, y) -> (col, row_idx)
def T(cells):
    return [(c, 5 - y) for c, y in cells]

EXPECT = {
    "A": (T([(1, 4), (1, 3), (2, 3)]), "orange"),
    "B": (T([(4, 4), (4, 3)]), "mint"),
    "C": (T([(0, 1), (1, 1), (2, 1)]), "purple"),
    "D": (T([(3, 2), (5, 2), (3, 1), (4, 1), (5, 1)]), "pink"),
    "E": (T([(0, 4)]), "yellow"),
    "F": (T([(2, 5), (2, 4)]), "blue"),
}
ARROWS = {"A": (2, 3), "B": (4, 4), "C": (1, 1), "D": (4, 1), "E": (0, 4), "F": (2, 5)}

def fam(p):
    r, g, b = p
    if r > 232 and 168 < g < 218 and 95 < b < 175: return "orange"
    if g > 195 and 115 < r < 195 and 140 < b < 225 and g > r and g > b: return "mint"
    if b > 200 and r > 150 and g > 125 and b - r > 30 and b - g > 45: return "purple"
    if r > 228 and 135 < g < 215 and 160 < b < 230 and r > g: return "pink"
    if r > 230 and g > 195 and b < 155: return "yellow"
    if r > 130 and g > 165 and b > 220 and b > g > r: return "blue"
    if r > 238 and g > 232 and b > 218: return "."
    if 225 < r < 245 and 195 < g < 220 and 180 < b < 210: return "."  # 格线/晕染
    return f"?{p}"

im = Image.open(PNG).convert("RGB")

def sample(col, row):
    cx = OX + col * CELL + CELL / 2 + 20
    cy = OY + row * CELL + CELL / 2 + 20
    return im.getpixel((int(cx * S), int(cy * S)))

occ = {}
for row in range(6):
    line = ""
    for col in range(6):
        f = fam(sample(col, row))
        occ[(col, row)] = f
        line += (f if f != "." else ".") + " "
    print("  " + line)

fails = []
for name, (cells, want) in EXPECT.items():
    for c in cells:
        got = occ.get(c, "?")
        if got != want:
            fails.append(f"{name} 格{c} 期望 {want} 实得 {got}")

for name, (col, y) in ARROWS.items():
    row = 5 - y
    cx = int((OX + col * CELL + CELL / 2) * S)
    cy = int((OY + row * CELL + CELL / 2) * S)
    white = cocoa = 0
    for dy in range(-13, 14, 2):
        for dx in range(-13, 14, 2):
            p = im.getpixel((cx + dx, cy + dy))
            if p[0] > 243 and p[1] > 238 and p[2] > 228: white += 1
            if p[0] < 130 and p[1] < 115 and p[2] < 105: cocoa += 1
    ok = white >= 8 and cocoa >= 3
    print(f"  箭头 {name} @(col{col},row{row}) 白 {white} 可可描边 {cocoa} -> {'OK' if ok else 'FAIL'}")
    if not ok:
        fails.append(f"箭头 {name} 检测失败")

total = sum(len(c) for c, _ in EXPECT.values())
print(f"\n独立块 6 · 总占格 {total} · 箭头 6")
print("结论:", "PASS - 12 棋盘与 04 定稿结构一致（六块占格/箭头/相对位置相同）" if not fails else "FAIL: " + "; ".join(fails))
