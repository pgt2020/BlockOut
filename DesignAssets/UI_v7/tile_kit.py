# -*- coding: utf-8 -*-
"""
BlockOut v7 · 方块组件化资源（干净版）
原则：只出 1 张中性方块底 + 1 张箭头；颜色靠 tint，方向靠旋转。
方块底由参数化生成（圆角 / 顶部高光 / 底部暗边 / 同色描边），
不再从参考图逐像素统计——那样会把箭头残影和噪点烘进资源里。
关卡语义（哪格什么色、什么方向）来自人工读参考图，运行时由代码数据提供。
"""
import os, io, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = r"E:\UnityProject\MutiplayGame\outputs\ui_replica_v7"
OUT = os.path.join(ROOT, "tilekit")
os.makedirs(OUT, exist_ok=True)

# 零截图依赖：底色来自 design token，不再从参考裁片里取中位色
H, W = 478, 325
BG = np.array([247.0, 232.0, 208.0])
DOT = [237, 220, 200]
DOT_STEP = 14

# 代码侧渲染网格：整数、紧贴、gap=0
TX, TY, TS, COLS, ROWS = 28, 128, 32, 10, 8
LSCALE = 1.30
RAD = 3

# 从参考图读取的关卡语义（演示数据）。颜色 G/Y/B/P/C/W，方向 U/D/L/R/X，-- 空格
CMAP = {"G": "green", "Y": "yellow", "B": "blue", "P": "pink", "C": "charcoal", "W": "cream"}
DMAP = {"U": "up", "D": "down", "L": "left", "R": "right", "X": "cross"}
SRC = [
    "-- -- GU -- -- -- GU YR -- --",
    "-- GU YX GU -- GU YR YR GU --",
    "BD YX YR YU GU PL YR YR BD --",
    "PL YR YU CU WU WU CU YU YR YR",
    "PL YU CU WU WU WU WU CU YR YR",
    "BD YU WD WU WU WU WU WX YU YR",
    "-- BD BD BD WU WU GU PL PL --",
    "-- -- -- BD WU GU BD -- -- --",
]
grid = []
for r, line in enumerate(SRC):
    row = []
    for c, tok in enumerate(line.split()):
        row.append(dict(r=r, c=c, color=None, dir="none") if tok == "--" else
                   dict(r=r, c=c, color=CMAP[tok[0]], dir=DMAP[tok[1]]))
    grid.append(row)
assert len(grid) == ROWS and all(len(x) == COLS for x in grid)

# ---------- 1. 中性方块底：参数化生成，绝对干净 ----------
yy, xx = np.mgrid[0:TS, 0:TS].astype(float)
grad = 1.08 - 0.30 * (yy / (TS - 1)) ** 1.6                    # 顶亮底暗
hl = 0.18 * np.exp(-((yy - 5.0) / 4.6) ** 2) * np.exp(-((xx - TS / 2) / (TS * 0.44)) ** 2)
shade = 0.07 * np.exp(-((yy - (TS - 2.5)) / 2.3) ** 2)
L = grad + hl - shade

def rounded_alpha(size, rad, feather=0.8):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size - 1, size - 1), radius=rad, fill=255)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(feather))).astype(float) / 255.0

# 参考图方块是「方形同色深外框 + 圆角亮芯」：四角不透明，紧贴时才不会漏出菱形底色
INNER = rounded_alpha(TS, RAD) > 0.5
er = INNER.copy()
for _ in range(2):
    e = er.copy()
    e[1:, :] &= er[:-1, :]; e[:-1, :] &= er[1:, :]
    e[:, 1:] &= er[:, :-1]; e[:, :-1] &= er[:, 1:]
    er = e
L[INNER & ~er] *= 0.68                                        # 圆角内芯的深色描边
L[~INNER] = 0.72                                              # 四角 = 同色深色外框
L = np.clip(L, 0.55, 1.30)
L = np.asarray(Image.fromarray((L * 255 / LSCALE).clip(0, 255).astype(np.uint8)).filter(
    ImageFilter.GaussianBlur(0.4))).astype(float) / 255.0 * LSCALE
L = np.clip(L / float(L[14:19, 8:24].mean()), 0.55, 1.30)    # 中间调归一，着色不偏暗
print("光照模板 顶 %.2f / 中 %.2f / 底 %.2f / 边 %.2f" % (
    L[3:8, 10:22].mean(), L[14:19, 10:22].mean(), L[26:30, 10:22].mean(),
    L[8:24, 0:2].mean()))

def save_base(size, fn):
    alpha = np.ones((size, size), float)                      # 方形不透明，紧贴无缝
    light = np.asarray(Image.fromarray((L * 255 / LSCALE).clip(0, 255).astype(np.uint8)).resize(
        (size, size), Image.LANCZOS)).astype(float) / 255.0 * LSCALE
    rgb = np.clip(light * 255 / LSCALE, 0, 255).astype(np.uint8)
    rgba = np.dstack([rgb, rgb, rgb, (alpha * 255).astype(np.uint8)])
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, fn))

save_base(32, "tile_base.png")
save_base(128, "tile_base@4x.png")

# ---------- 2. 箭头：1 张向上（旋转出 4 向）+ 1 张十字语义变体 ----------
def draw_arrow(size, kind="up"):
    S = size * 4
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    u = S / 24.0
    if kind == "up":
        poly = [(12*u, 2.5*u), (20.5*u, 11*u), (15.5*u, 11*u),
                (15.5*u, 21*u), (8.5*u, 21*u), (8.5*u, 11*u), (3.5*u, 11*u)]
    else:
        poly = [(10*u,1.5*u),(14*u,1.5*u),(14*u,9*u),(22.5*u,9*u),(22.5*u,13*u),
                (14*u,13*u),(14*u,22.5*u),(10*u,22.5*u),(10*u,13*u),(1.5*u,13*u),
                (1.5*u,9*u),(10*u,9*u)]
    d.polygon(poly, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(S * 0.006))
    core = (np.asarray(m).astype(float) / 255.0 > 0.5).astype(float)
    core = np.asarray(Image.fromarray((core * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(S * 0.004))).astype(float) / 255.0
    halo = np.asarray(Image.fromarray((core * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(S * 0.012))).astype(float) / 255.0
    rgba = np.zeros((S, S, 4), np.uint8)
    rgba[:, :, 0] = 236; rgba[:, :, 1] = 234; rgba[:, :, 2] = 226
    rgba[:, :, 3] = (halo * 145).clip(0, 255).astype(np.uint8)
    w = (core * 255).clip(0, 255).astype(np.uint8)
    for ch in range(3): rgba[:, :, ch] = np.maximum(rgba[:, :, ch], w)
    rgba[:, :, 3] = np.maximum(rgba[:, :, 3], w)
    return Image.fromarray(rgba, "RGBA").resize((size, size), Image.LANCZOS)

for kind in ("up", "cross"):
    draw_arrow(24, kind).save(os.path.join(OUT, "arrow_%s.png" % kind))
    draw_arrow(96, kind).save(os.path.join(OUT, "arrow_%s@4x.png" % kind))

# ---------- 3. 色板 ----------
PALETTE = {
    "green":    [139, 193, 91],
    "yellow":   [246, 186, 74],
    "blue":     [97, 161, 220],
    "pink":     [247, 143, 147],
    "charcoal": [104, 92, 76],
    "cream":    [233, 217, 198],
}
ROT = {"up": 0, "right": 90, "down": 180, "left": 270, "cross": 0, "none": 0}

# ---------- 4. 点阵底板 ----------
def dot_bg(w, h):
    out = Image.new("RGB", (w, h), tuple(int(x) for x in BG))
    d = ImageDraw.Draw(out)
    rad = 2.2
    for y in range(0, h + DOT_STEP, DOT_STEP):
        for x in range(0, w + DOT_STEP, DOT_STEP):
            d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=tuple(DOT))
    return out.filter(ImageFilter.GaussianBlur(0.45))

# ---------- 5. 装配：底 × tint + 箭头，整数网格 gap=0 ----------
base = np.asarray(Image.open(os.path.join(OUT, "tile_base.png")).convert("RGBA")).astype(float)
LM = np.clip(base[:, :, 0] / 255.0 * LSCALE, 0, 1.35)
LA = base[:, :, 3] / 255.0
AR = {k: np.asarray(Image.open(os.path.join(OUT, "arrow_%s.png" % k)).convert("RGBA")).astype(float)
      for k in ("up", "cross")}

def render_board(scale=1):
    S = TS * scale
    out = np.asarray(dot_bg(COLS * S, ROWS * S)).astype(float).copy()
    lm = np.asarray(Image.fromarray((LM / LSCALE * 255).clip(0, 255).astype(np.uint8)).resize(
        (S, S), Image.LANCZOS)).astype(float) / 255.0 * LSCALE
    la = np.asarray(Image.fromarray((LA * 255).astype(np.uint8)).resize(
        (S, S), Image.LANCZOS)).astype(float) / 255.0
    for r in range(ROWS):
        for c in range(COLS):
            v = grid[r][c]
            if not v["color"]: continue
            tint = np.array(PALETTE[v["color"]], float)
            y0, x0 = r * S, c * S
            dst = out[y0:y0 + S, x0:x0 + S]
            colored = np.clip(tint[None, None, :] * lm[:, :, None], 0, 255)
            dst[:] = dst * (1 - la[:, :, None]) + colored * la[:, :, None]
            if v["dir"] == "none": continue
            ai = Image.fromarray(AR["cross" if v["dir"] == "cross" else "up"].astype(np.uint8), "RGBA")
            deg = ROT[v["dir"]]
            if deg: ai = ai.rotate(-deg, resample=Image.BICUBIC)
            aw = int(S * 0.66); off = (S - aw) // 2
            ai = ai.resize((aw, aw), Image.LANCZOS)
            am = np.asarray(ai).astype(float)
            sub = out[y0 + off:y0 + off + aw, x0 + off:x0 + off + aw]
            aa = am[:, :, 3:4] / 255.0
            sub[:] = sub * (1 - aa) + am[:, :, :3] * aa
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

board_img = render_board(1)
board3 = render_board(3)
# 预览图是自检产物，不写进 tilekit/ 资源目录
board_img.save(os.path.join(ROOT, "_preview_board_component.png"))
board3.save(os.path.join(ROOT, "_preview_board_component@3x.png"))

# 整屏演示：程序化点阵背景 + 组件棋盘，完全不读参考图
demo = Image.new("RGB", (W, H), tuple(int(v) for v in BG))
dd = ImageDraw.Draw(demo)
for yy in range(0, H + DOT_STEP, DOT_STEP):
    for xx in range(0, W + DOT_STEP, DOT_STEP):
        dd.ellipse((xx - 2.2, yy - 2.2, xx + 2.2, yy + 2.2), fill=tuple(DOT))
b = np.asarray(board_img).astype(np.uint8)
demo.paste(Image.fromarray(b), (TX, TY))
demo.save(os.path.join(ROOT, "_preview_s4_component.png"))

# ---------- 6. 自检板 ----------
try:
    F = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 16)
    Fs = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 11)
except Exception:
    F = Fs = ImageFont.load_default()
CW, GAP, PAD = 300, 16, 18
rep = Image.new("RGB", (PAD * 2 + 3 * CW + 2 * GAP, 860), (248, 246, 242))
d = ImageDraw.Draw(rep)
d.text((PAD, 10), "方块组件自检 · 1 张方块底 + 1 张箭头 + 6 色 tint + 4 向旋转", font=F, fill=(60, 45, 35))
d.text((PAD, 34), "资源 6 张（含 @4x）；组件参数化生成，无箭头残影 / 无逐格切图 / 无累积错位", font=Fs, fill=(120, 95, 75))

def tinted(color, size=112):
    t = np.asarray(Image.open(os.path.join(OUT, "tile_base.png")).convert("RGBA")).astype(float)
    rgb = np.clip(np.array(color, float)[None, None, :] * (t[:, :, 0:1] / 255.0 * LSCALE), 0, 255)
    al = t[:, :, 3:4]
    rgba = Image.fromarray(np.dstack([rgb, al]).astype(np.uint8), "RGBA").resize(
        (size, size), Image.LANCZOS)
    card = Image.new("RGB", (size, size), tuple(int(x) for x in BG))
    card.paste(rgba, (0, 0), rgba)
    return card

x1 = PAD
d.text((x1, 62), "① 中性资源（白/灰度，可着色）", font=Fs, fill=(70, 55, 45))
rep.paste(tinted([255, 255, 255], 112), (x1, 84))
ar = Image.open(os.path.join(OUT, "arrow_up@4x.png")).convert("RGBA").resize((84, 84), Image.LANCZOS)
card = Image.new("RGB", (84, 84), tuple(PALETTE["green"])); card.paste(ar, (0, 0), ar)
rep.paste(card, (x1 + 128, 98))
d.text((x1, 200), "tile_base.png 32×32 / @4x 128×128", font=Fs, fill=(90, 75, 60))
d.text((x1, 216), "RGBA：RGB=灰度光照，A=圆角轮廓", font=Fs, fill=(90, 75, 60))
d.text((x1, 236), "arrow_up.png 白箭头，90/180/270 旋转出 4 向", font=Fs, fill=(90, 75, 60))
d.text((x1, 252), "arrow_cross.png 十字语义变体（参考图有）", font=Fs, fill=(90, 75, 60))

x2 = x1 + CW + GAP
d.text((x2, 62), "② 同一张底 × tint = 6 种方块", font=Fs, fill=(70, 55, 45))
for i, (k, v) in enumerate(PALETTE.items()):
    cx = x2 + (i % 3) * 96; cy = 84 + (i // 3) * 96
    rep.paste(tinted(v, 72), (cx, cy))
    d.text((cx, cy + 74), "%s #%02X%02X%02X" % (k, *v), font=Fs, fill=(90, 75, 60))
d.text((x2, 280), "③ 同一支箭头 × 旋转 = 4 个方向", font=Fs, fill=(70, 55, 45))
for i, (name, deg) in enumerate([("up", 0), ("right", 90), ("down", 180), ("left", 270)]):
    cx = x2 + i * 72
    ai = Image.open(os.path.join(OUT, "arrow_up.png")).convert("RGBA")
    if deg: ai = ai.rotate(-deg, resample=Image.BICUBIC)
    ai = ai.resize((56, 56), Image.LANCZOS)
    card = Image.new("RGB", (56, 56), tuple(PALETTE["green"])); card.paste(ai, (0, 0), ai)
    rep.paste(card, (cx, 302))
    d.text((cx, 360), name, font=Fs, fill=(90, 75, 60))

x3 = x2 + CW + GAP
d.text((x3, 62), "④ 单格装配 = 底板 + tint/光照 + 箭头", font=Fs, fill=(70, 55, 45))
s0 = dot_bg(64, 64).resize((64, 64), Image.LANCZOS)
s1 = tinted(PALETTE["green"], 64)
ai = Image.open(os.path.join(OUT, "arrow_up.png")).convert("RGBA").resize((48, 48), Image.LANCZOS)
s2 = s1.copy(); s2.paste(ai, (8, 8), ai)
for i, (lab, s_) in enumerate([("底板点阵", s0), ("+ 着色", s1), ("+ 箭头", s2)]):
    cx = x3 + i * 90
    rep.paste(s_, (cx, 84)); d.text((cx, 150), lab, font=Fs, fill=(90, 75, 60))
d.text((x3, 190), "⑤ 代码按 10×8 整数网格紧贴铺（gap=0）", font=Fs, fill=(70, 55, 45))
rep.paste(board3.resize((228, 182), Image.LANCZOS), (x3, 212))
d.text((x3, 398), "整屏棋盘 320×256，起点(28,128)，步长32", font=Fs, fill=(90, 75, 60))

y = 440
d.text((PAD, y), "⑥ 组件棋盘（统一整数网格，零累积错位、零残影、零截图依赖）", font=Fs, fill=(70, 55, 45))
mc = board3.resize((430, 350), Image.LANCZOS)
rep.paste(mc, (PAD, y + 22))
d.text((PAD, y + 378), "10×8 · 起点(28,128) · 步长32 · gap=0 · 颜色由 tint、方向由旋转", font=Fs, fill=(120, 95, 75))
rep.save(os.path.join(ROOT, "tilekit_report.png"))

# ---------- 6.9 资源归一：RGBA straight alpha，透明区 RGB 严格清零 ----------
for fn in sorted(f for f in os.listdir(OUT) if f.endswith(".png")):
    p = os.path.join(OUT, fn)
    arr = np.asarray(Image.open(p).convert("RGBA")).copy()
    al = arr[:, :, 3]
    al[al < 6] = 0
    arr[:, :, :3][al == 0] = 0
    Image.fromarray(arr, "RGBA").save(p)

# ---------- 7. 数据 ----------
kit = dict(
    grid=dict(x=TX, y=TY, size=TS, cols=COLS, rows=ROWS, gap=0),
    assets=dict(base="tilekit/tile_base.png", base_hd="tilekit/tile_base@4x.png",
                arrow="tilekit/arrow_up.png", arrow_hd="tilekit/arrow_up@4x.png",
                cross="tilekit/arrow_cross.png", cross_hd="tilekit/arrow_cross@4x.png"),
    palette=PALETTE, rotation=ROT, board=grid,
    note="颜色由 Image.color / CSS tint 乘中性灰度底实现；方向由旋转实现；禁止逐格切实例图。",
    reference_grid_note="参考图实测 X步长≈32.3 / Y步长≈30.4（非等比缩放），只用于读语义，不用于切图或渲染。")
for p in (ROOT, OUT):
    io.open(os.path.join(p, "tilekit.json"), "w", encoding="utf-8").write(
        json.dumps(kit, ensure_ascii=False, indent=1))
print("产出", sorted(f for f in os.listdir(OUT) if f.endswith(".png")))
print("自检板", rep.size)
