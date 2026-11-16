# -*- coding: utf-8 -*-
"""按新的 390x844 对局页布局，用真实素材合成「预期效果图」（不是运行截图）。

坐标与 BlockOutUIManager.Authoring.BuildBoardScreen / Relayout 一一对应：
  托盘 24..366 x 120..550 / BoardArea 318x402 居中于托盘 / 提示 288x28 y=564
  道具容器 319x78 距底 20 / 三卡 94x66 中心距 106.3
"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FB = 'C:/Windows/Fonts/msyhbd.ttc'
S = 3  # 超采样
W, H = 390 * S, 844 * S


def f(sz):
    return ImageFont.truetype(FB, int(sz * S))


def sc(v):
    return int(round(v * S))


# ---- 素材 ----
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import make_block_sprites as MBS

_SPR = {}


def block_sprite(cells_cr):
    """board.json 的 cells 是 [c, r]；生成器按 (r, c) 建模，这里转置后按形状缓存。"""
    rc = [(r, c) for (c, r) in cells_cr]
    minr = min(r for r, c in rc)
    minc = min(c for r, c in rc)
    rc = [(r - minr, c - minc) for r, c in rc]      # board.json 是全局坐标，生成器要局部形状
    key = frozenset(rc)
    if key not in _SPR:
        _SPR[key] = MBS.make(0, rc)
    return _SPR[key]


def icon(name):
    p = os.path.join(ROOT, 'assets/icons', name + '.png')
    a = np.array(Image.open(p).convert('RGBA').getchannel('A'))
    ys, xs = np.where(a > 8)
    im = Image.open(p).convert('RGBA').crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    return im


BOARD = json.load(open(os.path.join(ROOT, 'data', 'board.json'), encoding='utf-8'))
PALETTE = BOARD['palette']

canvas = Image.new('RGBA', (W, H), (255, 253, 247, 255))
d = ImageDraw.Draw(canvas)


def soft_card(box, fill, stroke=(255, 255, 255, 255), sw=3, radius=26, shadow=(0.40, 0.27, 0.13, 0.30), pad=9):
    x1, y1, x2, y2 = [sc(v) for v in box]
    # 阴影
    sh = Image.new('RGBA', (int(x2 - x1 + 2 * sc(pad)) + 8, int(y2 - y1 + 2 * sc(pad)) + 8), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle((sc(pad), sc(pad) + sc(2), sc(pad) + (x2 - x1), sc(pad) + (y2 - y1) + sc(2)),
                         radius=sc(radius), fill=(int(255 * shadow[0]), int(255 * shadow[1]), int(255 * shadow[2]), int(255 * shadow[3])))
    sh = sh.filter(ImageFilter.GaussianBlur(sc(7)))
    canvas.alpha_composite(sh, (int(x1 - sc(pad)), int(y1 - sc(pad) - sc(2))))
    # 描边 + 填充
    d.rounded_rectangle((x1, y1, x2, y2), radius=sc(radius), fill=stroke)
    d.rounded_rectangle((x1 + sc(sw), y1 + sc(sw), x2 - sc(sw), y2 - sc(sw)), radius=sc(radius - sw * 0.6), fill=fill)


# ================= 托盘 =================
soft_card((24, 134, 366, 564), (255, 253, 248, 255), radius=30, sw=3, pad=10)
# 点阵底
for yy in range(134 + 14, 564 - 10, 16):
    for xx in range(24 + 14, 366 - 10, 16):
        d.ellipse((sc(xx), sc(yy), sc(xx + 1.6), sc(yy + 1.6)), fill=(216, 196, 166, 90))

# ================= 棋盘 =================
AREA = (36, 147, 354, 551)   # BoardArea 318x404 @ center 349
aw, ah = AREA[2] - AREA[0], AREA[3] - AREA[1]
cols, rows = BOARD['cols'], BOARD['rows']
cell = min(aw * 0.9 / max(9.5, cols), ah / (rows * 248 / 240))
gw, gh = cell * cols, cell * rows * 248 / 240
bx = AREA[0] + (aw - gw) / 2
by = AREA[1] + (ah - gh) / 2

tint_cache = {}


def tinted(fam, key):
    if key in tint_cache:
        return tint_cache[key]
    p = PALETTE[fam]
    top = np.array([int(p['top'][i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    bot = np.array([int(p['bottom'][i:i + 2], 16) for i in (1, 3, 5)], np.float32)
    c = (top + bot) * 0.5 / 255.0
    tint_cache[key] = c
    return c


DIRS = {'up': 0, 'right': 90, 'down': 180, 'left': 270}


def arrow_layer(px, direction):
    a = Image.new('RGBA', (px, px), (0, 0, 0, 0))
    ad = ImageDraw.Draw(a)
    c = px / 2
    L = px * 0.20
    w = px * 0.115
    pts = [(c, c - L), (c + w, c), (c + w * 0.34, c), (c + w * 0.34, c + L * 0.92),
           (c - w * 0.34, c + L * 0.92), (c - w * 0.34, c), (c - w, c)]
    ad.polygon(pts, fill=(255, 255, 255, 250))
    ad.line(pts + [pts[0]], fill=(255, 255, 255, 255), width=max(2, int(px * 0.028)), joint='curve')
    if direction != 'up':
        a = a.rotate(-DIRS[direction], resample=Image.BICUBIC)
    return a


for b in BOARD['blocks']:
    if b.get('skip'):
        continue
    tile = block_sprite(b['cells'])
    tint = tinted(b['family'], b['family'])
    arr = np.array(tile).astype(np.float32)
    for ch in range(3):
        arr[..., ch] *= tint[ch]
    body = Image.fromarray(arr.astype(np.uint8), 'RGBA')

    # 白描边底：外扩
    rim_pad = int(cell * 0.09 * S)
    tw = int(tile.width / 240 * cell * S)
    th = int(tile.height / 240 * cell * S)
    white = body.resize((tw + 2 * rim_pad, th + 2 * rim_pad), Image.LANCZOS)
    wl = Image.new('RGBA', white.size, (255, 253, 248, 255))
    wl.putalpha(white.getchannel('A'))
    body2 = body.resize((tw, th), Image.LANCZOS)

    x0 = sc(bx + min(c for c, r in b['cells']) * cell)
    y0 = sc(by + min(r for c, r in b['cells']) * cell)
    grp = Image.new('RGBA', white.size, (0, 0, 0, 0))
    grp.alpha_composite(wl)
    grp.alpha_composite(body2, (rim_pad, rim_pad))
    canvas.alpha_composite(grp, (int(x0 - rim_pad), int(y0 - rim_pad)))

# 箭头
for b in BOARD['blocks']:
    if b.get('skip'):
        continue
    ac, ar = b['arrow']
    px = int(cell * 0.58 * S)
    al = arrow_layer(px, b['dir'])
    cx = sc(bx + (ac + 0.5) * cell) - px // 2
    cy = sc(by + (ar + 0.5) * cell) - px // 2
    canvas.alpha_composite(al, (int(cx), int(cy)))

# ================= HUD（数值 = prefab 实际 rect，逐项对齐） =================
# 标题：TopCenter (0,46) 240x26 → 中心 (195,59)；副标题 (0,72) h14 → 中心 79
d.text((sc(195), sc(59)), '第 %d 关' % BOARD.get('levelInChapter', 16),
       font=f(20), fill=(59, 42, 36, 255), anchor='mm')
d.text((sc(195), sc(79)), '甜点星球', font=f(12), fill=(110, 84, 73, 255), anchor='mm')

# 暂停：TopRight (-24,-46) 40x40 → 326..366 / 46..86，白圆 + 咖色双竖条图标
d.ellipse((sc(326), sc(46), sc(366), sc(86)), fill=(255, 255, 255, 255))
d.rounded_rectangle((sc(341.4), sc(57), sc(345.0), sc(75)), radius=sc(1.6), fill=(59, 42, 36, 255))
d.rounded_rectangle((sc(347.0), sc(57), sc(350.6), sc(75)), radius=sc(1.6), fill=(59, 42, 36, 255))

# 心：TopLeft (24,88) 16x16，步距 18
def heart(dr, cx, cy, s, fill):
    pts = []
    for i in range(60):
        t = i * 2 * math.pi / 60
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((sc(cx + x * s / 32), sc(cy - y * s / 32)))
    dr.polygon(pts, fill=fill)

for i in range(3):
    heart(d, 32 + i * 18, 96, 17, (235, 62, 61, 255))

# 推进条：TopCenter (0,88) 196x13 → 97..293；Bar 内缩 3；Gloss 内缩 (4, ~6)
d.rounded_rectangle((sc(97), sc(88), sc(293), sc(101)), radius=sc(6.5), fill=(252, 235, 216, 255))
d.rounded_rectangle((sc(100), sc(91), sc(100 + 190 * 0.30), sc(98)), radius=sc(3.5), fill=(30, 143, 104, 255))
d.rounded_rectangle((sc(101), sc(92.5), sc(101 + 186 * 0.28), sc(95.5)), radius=sc(1.5), fill=(255, 255, 255, 70))
d.text((sc(318), sc(94.5)), '32%', font=f(12), fill=(110, 84, 73, 255), anchor='lm')

# 剩余：TopRight (-42,546) 140x16，右对齐 → 右缘 348
d.text((sc(348), sc(554)), '剩余 %d 块' % len([x for x in BOARD['blocks'] if not x.get('skip')]), font=f(13),
       fill=(138, 117, 104, 255), anchor='rm')

# 提示 pill：TopCenter (0,578) 288x28 → 51..339；灯泡 18x18 @ (63,583)；文字左缘 87
soft_card((51, 642, 339, 670), (255, 255, 255, 255), radius=14, sw=1.5, pad=5)
bulb = icon('bulb').resize((int(18 * S), int(18 * S)), Image.LANCZOS)
canvas.alpha_composite(bulb, (sc(63), sc(647)))
d.text((sc(87), sc(656)), '轻点整块方块，沿箭头方向飞出', font=f(12), fill=(59, 42, 36, 255), anchor='lm')

# ================= 道具（BottomToolbar 35.5..354.5 / 754..832；三卡 94x66，中心距 106.3） =================
soft_card((35.5, 748, 354.5, 832), (252, 235, 216, 255), radius=26, sw=3, pad=8)
tools = [('bulb', '提示', '3', '轮换高亮可飞块'),
         ('hammer', '锤子', '2', '消除任意在场块'),
         ('bomb', '炸弹', '1', '飞走最多 3 块')]
for i, (src, name, cnt, cond) in enumerate(tools):
    left = 35.5 + 6.2 + i * 106.3
    soft_card((left, 754, left + 94, 826), (255, 253, 248, 255), radius=22, sw=2, pad=5)
    ic = icon(src)
    ic.thumbnail((int(32 * S), int(32 * S)), Image.LANCZOS)
    canvas.alpha_composite(ic, (int(sc(left + 31)), int(sc(762))))
    d.text((sc(left + 47), sc(803)), name, font=f(12), fill=(59, 42, 36, 255), anchor='mm')
    d.text((sc(left + 47), sc(816)), cond, font=f(10), fill=(138, 117, 104, 255), anchor='mm')
    # 数量徽标：BerryRed #C62F45，18x18 @ 卡内 (70,5)
    d.ellipse((sc(left + 70), sc(759), sc(left + 88), sc(777)), fill=(198, 47, 69, 255))
    d.text((sc(left + 79), sc(768)), cnt, font=f(10), fill=(255, 255, 255, 255), anchor='mm')

out = canvas.convert('RGB')
out.resize((390 * 2, 844 * 2), Image.LANCZOS).save(os.path.join(ROOT, 'samples', 'board_expected.png'))
print('saved', out.size)
