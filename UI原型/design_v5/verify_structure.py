# -*- coding: utf-8 -*-
"""BlockOut design_v5 结构校验：采样 6x6 棋盘 36 格心 + 6 箭头位，与规范数据表比对。
用法: python verify_structure.py [png路径]   （默认校验 01_structure_proof.png）"""
import sys
from PIL import Image

PNG = sys.argv[1] if len(sys.argv) > 1 else r"E:\UnityProject\MutiplayGame\BlockOut\UI原型\design_v5\01_structure_proof.png"
S = 2  # 780/390 缩放
OX, OY, CELL = 9, 140, 62

# 规范数据表：块 -> (占格, [平涂色, 渐变顶, 渐变底])（02/04 高保真用渐变体色，01 校对图用平涂）
EXPECT = {
    "A": ([(1, 4), (1, 3), (2, 3)], [(0xF5, 0xBD, 0x84), (0xF8, 0xCC, 0xA0), (0xF0, 0xAC, 0x6E)]),
    "B": ([(4, 4), (4, 3)], [(0x8A, 0xDB, 0xC0), (0xA9, 0xE8, 0xCF), (0x79, 0xD2, 0xB2)]),
    "C": ([(0, 1), (1, 1), (2, 1)], [(0xB9, 0xA4, 0xE8), (0xCF, 0xC2, 0xF2), (0xAC, 0x95, 0xE2)]),
    "D": ([(3, 2), (5, 2), (3, 1), (4, 1), (5, 1)], [(0xF6, 0xA4, 0xBA), (0xFA, 0xBC, 0xD0), (0xF1, 0x93, 0xAF)]),
    "E": ([(0, 4)], [(0xF7, 0xD3, 0x6C), (0xFA, 0xE4, 0x9B), (0xF2, 0xC9, 0x57)]),
    "F": ([(2, 5), (2, 4)], [(0x92, 0xBB, 0xEF), (0xB9, 0xD2, 0xF7), (0x84, 0xB4, 0xEB)]),
}
EMPTY = (0xFF, 0xFD, 0xF8)
ARROW_CENTERS = {"A": (2, 3), "B": (4, 4), "C": (1, 1), "D": (4, 1), "E": (0, 4), "F": (2, 5)}
ARROW_DIR = {"A": "→", "B": "↑", "C": "←", "D": "↓", "E": "↑", "F": "→"}

img = Image.open(PNG).convert("RGB")


def cell_px(cx, cy, dx=18, dy=18):
    """格内采样点（避开箭头/徽标），返回 PNG 像素坐标"""
    x = OX + CELL * cx + CELL // 2 + dx
    y = OY + CELL * (5 - cy) + CELL // 2 + dy
    return x * S, y * S


def close(a, b, tol=14):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def classify(px):
    for name, (_, colors) in EXPECT.items():
        for color in colors:  # 渐变稿：任一端点命中即算该块
            if close(px, color, tol=22):
                return name
    if close(px, EMPTY, tol=24):  # B 的薄荷发光会轻微染到相邻空格（样板同款滤镜）
        return "."
    return f"?{px}"


# 1) 逐格比对
errors, grid = [], {}
for cy in range(5, -1, -1):
    row = ""
    for cx in range(6):
        px = img.getpixel(cell_px(cx, cy))
        c = classify(px)
        grid[(cx, cy)] = c
        row += f"{c:>2}"
        if c.startswith("?"):
            errors.append(f"格({cx},{cy}) 颜色异常: {px}")
    print(f"y{cy}: {row}")

# 期望占据表
occupied = {}
for name, (cells, _) in EXPECT.items():
    for c in cells:
        occupied[c] = name
mismatch = [(c, occupied.get(c, "."), grid[c]) for c in grid if occupied.get(c, ".") != grid[c]]
print("\n占据格比对:", "全部一致 ✓" if not mismatch else f"不一致 {mismatch}")

# 2) 箭头位采样（中心应为白色箭头 #FFFEFA 或深色描边 #5A4038）
print("\n箭头位检查（6 枚）:")
arrow_ok = 0
for name, (cx, cy) in ARROW_CENTERS.items():
    x = OX + CELL * cx + CELL // 2
    y = OY + CELL * (5 - cy) + CELL // 2
    hit = []
    for ddx in range(-8, 9, 4):
        for ddy in range(-8, 9, 4):
            hit.append(img.getpixel(((x + ddx) * S, (y + ddy) * S)))
    white = sum(1 for p in hit if p[0] > 235 and p[1] > 225 and p[2] > 210)
    dark = sum(1 for p in hit if p[0] < 130 and p[1] < 110 and p[2] < 105)
    ok = white >= 3 or dark >= 3
    arrow_ok += ok
    print(f"  {name} {ARROW_DIR[name]} @({cx},{cy}): 白:{white} 描边:{dark} -> {'✓' if ok else '✗ 未检出箭头'}")
print(f"箭头总数: {arrow_ok}/6")

# 3) 独立块数与总占格数
total_cells = sum(len(c) for c, _ in EXPECT.values())
print(f"\n独立块数: {len(EXPECT)}（规范要求 6）  总占格: {total_cells}（3+2+3+5+1+2=16）")

print("\n结论:", "PASS - 结构与规范完全一致" if not errors and not mismatch and arrow_ok == 6 else "FAIL - 需修图")
