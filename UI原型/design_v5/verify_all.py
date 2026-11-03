# -*- coding: utf-8 -*-
"""design_v5 校验②：高保真游戏页（渐变果冻块按色相分类 + 无 A-F 徽标 + HUD/轨迹）
   + 首页（3/12 进度条、12 圆点、3 片揭晓、设置入口、导航图标）。"""
from PIL import Image

BASE = r"E:\UnityProject\MutiplayGame\BlockOut\UI原型\design_v5"
S = 2
OX, OY, CELL = 9, 140, 62

EXPECT = {
    "A": ([(1, 4), (1, 3), (2, 3)], "orange"),
    "B": ([(4, 4), (4, 3)], "mint"),
    "C": ([(0, 1), (1, 1), (2, 1)], "purple"),
    "D": ([(3, 2), (5, 2), (3, 1), (4, 1), (5, 1)], "pink"),
    "E": ([(0, 4)], "yellow"),
    "F": ([(2, 5), (2, 4)], "blue"),
}
ARROW_CENTERS = {"A": (2, 3), "B": (4, 4), "C": (1, 1), "D": (4, 1), "E": (0, 4), "F": (2, 5)}


def hue_family(p):
    r, g, b = p
    if r > 225 and 130 < g < 215 and 80 < b < 175 and r > g > b:
        return "orange"      # A #F8CCA0→#F0AC6E
    if g > 185 and g > b > r and b > 140:
        return "mint"        # B #A9E8CF→#79D2B2
    if b > 205 and b > r > g:
        return "purple"      # C #CFC2F2→#AC95E2
    if r > 225 and 140 < g < 215 and 165 < b < 225 and b > g:
        return "pink"        # D #FABCD0→#F193AF
    if r > 225 and g > 185 and b < 185 and r >= g > b:
        return "yellow"      # E #FAE49B→#F2C957
    if b > 210 and b > g > r:
        return "blue"        # F #B9D2F7→#84B4EB
    return f"?{p}"


# ============ 1. 高保真游戏页 ============
img = Image.open(BASE + r"\02_game_hifi.png").convert("RGB")
print("=== 02_game_hifi：棋盘占据（色相分类） ===")
errors = []
for cy in range(5, -1, -1):
    row = ""
    for cx in range(6):
        # E 为黄色渐变，采上半部避开与橙色重叠的渐变底部；B 上方空格容忍发光晕染
        dx, dy = (18, -14) if (cx, cy) == (0, 4) else (18, 18)
        x = (OX + CELL * cx + CELL // 2 + dx) * S
        y = (OY + CELL * (5 - cy) + CELL // 2 + dy) * S
        fam = hue_family(img.getpixel((x, y)))
        row += f"{fam:>7}"
        want = next((n for n, (cells, f) in EXPECT.items() if (cx, cy) in cells), None)
        if want and fam != EXPECT[want][1]:
            errors.append(f"格({cx},{cy}) 期望 {EXPECT[want][1]} 实得 {fam}")
        if not want and not (fam.startswith("?") or fam == "mint"):
            errors.append(f"空格({cx},{cy}) 被占据: {fam}")
    print(f"y{cy}: {row}")
print("占据比对:", "全部一致 ✓" if not errors else errors)

print("\n=== 箭头位（6 枚） ===")
n = 0
for name, (cx, cy) in ARROW_CENTERS.items():
    x = OX + CELL * cx + CELL // 2
    y = OY + CELL * (5 - cy) + CELL // 2
    if name == "B":
        y -= 7  # B 抬起 7px
    hits = [img.getpixel(((x + dx) * S, (y + dy) * S)) for dx in range(-8, 9, 4) for dy in range(-8, 9, 4)]
    white = sum(1 for p in hits if p[0] > 235 and p[1] > 225 and p[2] > 210)
    n += white >= 3
    print(f"  {name}: 白色箭头像素 {white}/25 {'✓' if white >= 3 else '✗'}")
print(f"箭头总数: {n}/6")

print("\n=== A-F 徽标必须已移除（原徽标位不应为白色圆） ===")
badge_spots = {"A": (86, 218), "B": (272, 308), "C": (27, 404), "D": (210, 404), "E": (24, 212), "F": (148, 218)}
bad = []
for name, (bx, by) in badge_spots.items():
    p = img.getpixel((bx * S, by * S))
    is_white = p[0] > 240 and p[1] > 235 and p[2] > 225
    if is_white:
        bad.append(f"{name}@{bx},{by} 仍为白色徽标")
    print(f"  {name} 徽标位采样 {p} -> {'✗ 仍有徽标' if is_white else '✓ 已移除'}")
print("徽标移除:", "全部通过 ✓" if not bad else bad)

print("\n=== B 飞出轨迹（棋板上沿虚线 + 箭头） ===")
traj = [img.getpixel((288 * S, y * S)) for y in range(150, 192, 6)]
mint = sum(1 for p in traj if p[1] > 150 and p[1] > p[0] and p[2] > 120)
print(f"  轨迹采样 {len(traj)} 点，薄荷色命中 {mint} -> {'✓' if mint >= 4 else '✗'}")
lifted = img.getpixel(((288 + 18) * S, (233 - 7 + 18) * S))
print(f"  B 抬起后格心色相: {hue_family(lifted)}")

# ============ 2. 首页 ============
h = Image.open(BASE + r"\03_home_hifi.png").convert("RGB")
print("\n=== 03_home_hifi：章节进度 3/12 ===")
bar_y = (634 + 6) * S
fill_px = h.getpixel((int((44 + 37) * S), bar_y))     # 进度条 25% 处
track_px = h.getpixel((int((44 + 200) * S), bar_y))   # 进度条 66% 处
print(f"  进度条 25% 处 {fill_px} -> {'珊瑚✓' if fill_px[0] > 230 and fill_px[1] < 160 else '✗'}")
print(f"  进度条 66% 处 {track_px} -> {'轨道✓' if 235 < track_px[0] < 252 and 220 < track_px[1] < 240 else '✗'}")

dots = [52 + 26 * i for i in range(12)]
filled = sum(1 for dx in dots if (lambda p: p[0] > 230 and p[1] < 160)(h.getpixel((dx * S, 662 * S))))
print(f"  12 圆点中珊瑚色(已收集): {filled} -> {'✓ 3/12' if filled == 3 else '✗'}")

print("\n=== 章节作品卡：3 片已揭晓 ===")
p1 = h.getpixel((195 * S, 238 * S))   # 顶部奶油（薄荷）
p1b = h.getpixel((195 * S, 212 * S))  # 樱桃（草莓红）
p2 = h.getpixel((160 * S, 300 * S))   # 左侧奶油（珊瑚）
p3 = h.getpixel((195 * S, 390 * S))   # 杯身下部（黄）
gray = h.getpixel((230 * S, 300 * S)) # 右侧奶油（灰=未揭晓）
checks = [
    ("顶部奶油 薄荷", p1, lambda p: p[1] > 180 and p[0] < 160),
    ("樱桃 草莓红", p1b, lambda p: p[0] > 220 and p[1] < 110),
    ("左侧奶油 珊瑚", p2, lambda p: p[0] > 230 and 100 < p[1] < 160),
    ("杯身下部 黄", p3, lambda p: p[0] > 220 and p[1] > 180 and p[2] < 130),
    ("右侧奶油 灰(未揭晓)", gray, lambda p: 225 < p[0] < 245 and 215 < p[1] < 232 and 205 < p[2] < 225),
]
for label, p, ok in checks:
    print(f"  {label}: {p} -> {'✓' if ok(p) else '✗'}")

print("\n=== 设置入口 / 导航 ===")
gear_ring = h.getpixel((46 * S, 27 * S))  # 按钮上沿（避开图标）
print(f"  左上设置按钮 {gear_ring} -> {'✓ 白色圆按钮' if gear_ring[0] > 235 else '✗'}")
for label, x, y, want in [("首页(激活)", 97, 764, "coral"), ("图鉴", 195, 764, "gray"), ("商店", 293, 771, "gray")]:
    p = h.getpixel((x * S, y * S))
    fam = "coral" if (p[0] > 220 and p[1] < 150) else ("gray" if 150 < p[0] < 210 else f"?{p}")
    print(f"  导航「{label}」({x},{y}) {p} -> {'✓' if fam == want else '✗'}")

# ============ 3. 04_game_default 最终版 ============
g4 = Image.open(BASE + r"\04_game_default.png").convert("RGB")
print("\n=== 04_game_default：棋盘全中性（默认无红描边/无抬起/无发光） ===")
err4 = []
for cy in range(5, -1, -1):
    row = ""
    for cx in range(6):
        dx, dy = (18, -14) if (cx, cy) == (0, 4) else (18, 18)
        x = (OX + CELL * cx + CELL // 2 + dx) * S
        y = (OY + CELL * (5 - cy) + CELL // 2 + dy) * S
        fam = hue_family(g4.getpixel((x, y)))
        row += f"{fam:>7}"
        want = next((n for n, (cells, f) in EXPECT.items() if (cx, cy) in cells), None)
        if want and fam != EXPECT[want][1]:
            err4.append(f"格({cx},{cy}) 期望 {EXPECT[want][1]} 实得 {fam}")
        if not want and not (fam.startswith("?") or fam == "mint"):
            err4.append(f"空格({cx},{cy}) 被占据: {fam}")
    print(f"y{cy}: {row}")
print("占据比对:", "全部一致 ✓" if not err4 else err4)

print("\n=== 04：默认态 A/F 无红色描边（块边缘应为体色/白描边） ===")
for name, (ex, ey) in [("A 块边缘", (100, 202)), ("F 块边缘", (164, 140))]:
    p = g4.getpixel((ex * S, ey * S))
    is_red = p[0] > 200 and p[1] < 120 and p[2] < 130
    print(f"  {name} {p} -> {'✗ 有红描边' if is_red else '✓ 无红色'}")

print("\n=== 04：HUD 三心 + 暂停按钮 + 剩余 6 块 ===")
hearts = [g4.getpixel((int(cx * S), int(41 * S))) for cx in (318, 338, 358)]
heart_ok = all(p[0] > 200 and p[1] < 130 for p in hearts)
print(f"  三心采样 {hearts} -> {'✓ 3 颗红心' if heart_ok else '✗'}")
pause_btn = g4.getpixel((46 * S, 26 * S))
print(f"  暂停按钮上沿 {pause_btn} -> {'✓ 白色圆钮' if pause_btn[0] > 235 else '✗'}")
remain = g4.getpixel((int(262 * S), int(87 * S)))
print(f"  剩余块 pill 区 {remain} -> {'✓ 薄荷底' if remain[1] > 220 else '✗'}")

print("\n=== 04：三工具（提示/锤子/魔法棒）第 4 关均未解锁 → 锁徽章 #8A6E62 ===")
for label, bx in [("提示", 117), ("锤子", 215), ("魔法棒", 313)]:
    p = g4.getpixel(((bx - 8) * S, 662 * S))  # 徽章左缘（圆心是白色锁形）
    is_brown = 110 < p[0] < 165 and 85 < p[1] < 135 and 70 < p[2] < 125
    print(f"  {label} 锁徽章 {p} -> {'✓ 可可锁标' if is_brown else '✗'}")

# ============ 4. 06_home_default 最终版 ============
h6 = Image.open(BASE + r"\06_home_default.png").convert("RGB")
print("\n=== 06_home_default：拼片进度 3/12 ===")
bar_y6 = (624 + 5) * S
fill6 = h6.getpixel((int((42 + 38) * S), bar_y6))
track6 = h6.getpixel((int((42 + 200) * S), bar_y6))
print(f"  进度条 3/12 处 {fill6} -> {'珊瑚✓' if fill6[0] > 230 and fill6[1] < 160 else '✗'}")
print(f"  进度条 66% 处 {track6} -> {'轨道✓' if 235 < track6[0] < 252 and 220 < track6[1] < 240 else '✗'}")
nodes = [48 + 26.8 * i for i in range(12)]
filled6 = sum(1 for nx in nodes if (lambda p: p[0] > 230 and p[1] < 160)(h6.getpixel((int(nx * S), 651 * S))))
print(f"  12 节点中珊瑚色: {filled6} -> {'✓ 3/12' if filled6 == 3 else '✗'}")

print("\n=== 06：金币统一图标（左上区域为金色硬币，非星星） ===")
coin = h6.getpixel((int(236 * S), int(60 * S)))  # 币环（中心为星形压印）
coin_ok = coin[0] > 240 and 170 < coin[1] < 220 and coin[2] < 130
print(f"  金币环 {coin} -> {'✓ 金色硬币' if coin_ok else '✗'}")

print("\n=== 06：遮罩预览卡 3 片揭晓 + 2 个剪影 + 前景玩具块 ===")
checks6 = [
    ("P1 薄荷球(揭晓)", (195, 234), lambda p: p[1] > 180 and p[0] < 190),
    ("樱桃(揭晓·薄雾混合)", (195, 207), lambda p: p[0] > 220 and p[1] < 170),
    ("P2 左勺珊瑚(揭晓)", (160, 296), lambda p: p[0] > 230 and 100 < p[1] < 160),
    ("P3 杯身黄(揭晓·薄雾混合)", (195, 380), lambda p: p[0] > 220 and p[1] > 180 and p[2] < 175),
    ("P4 右勺剪影(薄雾混合)", (230, 296), lambda p: p[0] > 238 and p[1] > 225 and p[2] > 210 and p[0] - p[2] < 20),
    ("P5 杯身上部剪影", (195, 332), lambda p: 225 < p[0] < 245 and 210 < p[1] < 232 and 195 < p[2] < 222),
    ("玩具块A 橙(0,0格)", (271, 347), lambda p: 230 < p[0] < 255 and 150 < p[1] < 215 and 90 < p[2] < 175),
    ("玩具块A 橙(1,1格)", (300, 371), lambda p: 230 < p[0] < 255 and 140 < p[1] < 200 and 80 < p[2] < 160),
    ("玩具块B 薄荷", (129, 348), lambda p: p[1] > 190 and 120 < p[0] < 190),
    ("CTA 珊瑚", (195, 512), lambda p: p[0] > 240 and p[1] < 160),
]
for label, (px6, py6), ok in checks6:
    p = h6.getpixel((px6 * S, py6 * S))
    print(f"  {label}: {p} -> {'✓' if ok(p) else '✗'}")

print("\n=== 06：底部三导航 ===")
for label, x, y, want in [("首页(激活)", 84, 750, "coral"), ("图鉴", 190, 754, "gray"), ("商店", 306, 750, "gray")]:
    p = h6.getpixel((x * S, y * S))
    fam = "coral" if (p[0] > 220 and p[1] < 150) else ("gray" if 150 < p[0] < 210 else f"?{p}")
    print(f"  「{label}」({x},{y}) {p} -> {'✓' if fam == want else '✗'}")
