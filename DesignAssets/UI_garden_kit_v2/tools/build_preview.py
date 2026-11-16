# -*- coding: utf-8 -*-
"""Compose the 1080x1920 home-screen preview from procedural components + slices."""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import components as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, '..', 'UI_garden_kit')
UI = os.path.join(ROOT, 'ui')
PRE = os.path.join(ROOT, 'preview')
os.makedirs(PRE, exist_ok=True)

W, H = 1080, 1920
S = W / 941.0
FONT = 'C:/Windows/Fonts/msyhbd.ttc'
FONT_NUM = 'C:/Windows/Fonts/ariblk.ttf'

screen = Image.open(os.path.join(ROOT, 'background', 'bg_garden_1080x1920.png')).convert('RGBA')
screen = screen.resize((W, H), Image.LANCZOS)
d = ImageDraw.Draw(screen)


def paste(img, cx=None, cy=None, x=None, y=None):
    if x is None:
        x = int(cx - img.width / 2)
    if y is None:
        y = int(cy - img.height / 2)
    screen.alpha_composite(img, (int(x), int(y)))


def txt(cx, cy, s, size, fill=(255, 255, 255, 255), shadow=(24, 64, 44, 165), dy=4, blur=None,
        font=None):
    f = ImageFont.truetype(font or FONT, size)
    if shadow:
        pad = size
        layer = Image.new('RGBA', (int(size * len(s) * 1.6) + pad * 2, size * 2 + pad), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((layer.width / 2, layer.height / 2), s, font=f,
                                   fill=shadow, anchor='mm')
        layer = layer.filter(ImageFilter.GaussianBlur(blur or max(1.5, size / 16)))
        paste(layer, cx=cx, cy=cy + dy)
    d.text((cx, cy), s, font=f, fill=fill, anchor='mm')


# ---- path strip behind the nodes
path = Image.open(os.path.join(REF, 'generated', 'path_vertical.png')).convert('RGBA')
pw = int(path.width * S * 0.60)
path = path.resize((pw, H), Image.LANCZOS)
path.putalpha(path.getchannel('A').point(lambda v: int(v * 0.85)))
screen.alpha_composite(path, (int(W * 0.5 - pw / 2), 0))

# ---- node layout (source coordinates from the reference)
NODES = [
    dict(asset='locked',    digit='8',    x1=408, y1=60,  x2=549, y2=184, badge=('lock', 'br')),
    dict(asset='locked',    digit='7',    x1=408, y1=273, x2=549, y2=393, badge=('lock', 'br')),
    dict(asset='star',      digit='6',    x1=406, y1=512, x2=541, y2=667, badge=('star', 'br')),
    dict(asset='current',   digit='5',    x1=381, y1=720, x2=551, y2=911, badge=None),
    dict(asset='fail',      digit='4',    x1=212, y1=978, x2=334, y2=1080, badge=('skull', 'b')),
    dict(asset='challenge', digit='挑战', x1=608, y1=978, x2=738, y2=1080, badge=('skull', 'b')),
]
BADGES = {
    'lock': C.badge_lock(224),
    'star': C.badge_star(224),
    'skull': C.badge_skull(224),
}
POINTER = C.node_pointer(200)
node_cache = {}
for n in NODES:
    bw = (n['x2'] - n['x1']) * S
    bh = (n['y2'] - n['y1']) * S
    body_frac = 228 / 256.0
    sprite = node_cache.setdefault(n['asset'], C.node(n['asset'], 256))
    spr = sprite.resize((int(bw / body_frac), int(bh / body_frac)), Image.LANCZOS)
    cx = (n['x1'] + n['x2']) / 2 * S
    cy = (n['y1'] + n['y2']) / 2 * S
    paste(spr, cx=cx, cy=cy)

    if n['asset'] == 'current':
        pt = POINTER.resize((int(bw * 0.34), int(bw * 0.34)), Image.LANCZOS)
        paste(pt, cx=cx, cy=n['y2'] * S + pt.height * 0.22)

    size = int(min(bw, bh) * (0.62 if n['digit'] != '挑战' else 0.36))
    txt(cx, cy, n['digit'], size, shadow=(16, 54, 40, 190), dy=max(2, size // 14),
        font=FONT_NUM if n['digit'] != '挑战' else FONT)

    if n['badge']:
        kind, pos = n['badge']
        b = BADGES[kind].resize((int(52 * S), int(52 * S)), Image.LANCZOS)
        if pos == 'br':
            paste(b, cx=n['x2'] * S - b.width * 0.22, cy=n['y2'] * S - b.height * 0.20)
        else:
            paste(b, cx=cx, cy=n['y2'] * S + b.height * 0.10)

# ---- current-node callout bubble
bub = C.bubble(300, 150, 34, tail=True).resize((int(138 * S), int(69 * S)), Image.LANCZOS)
paste(bub, x=558 * S, y=696 * S)
txt(628 * S, 724 * S, '当前关卡', int(25 * S), fill=(116, 84, 52, 255), shadow=None)

# ---- mascot (sliced from the reference, alpha cleaned in v1)
mascot = Image.open(os.path.join(REF, 'ui', 'mascot_arrow.png')).convert('RGBA')
mascot = mascot.resize((int(mascot.width * S), int(mascot.height * S)), Image.LANCZOS)
paste(mascot, x=378 * S, y=944 * S)

# ---- top bar slices (static, kept exactly as drawn in the reference)
for name, (x, y) in [('btn_settings', (40, 38)), ('pill_currency', (650, 48)),
                     ('btn_task', (726, 228)), ('btn_achievement', (726, 473))]:
    im = Image.open(os.path.join(UI, name + '.png')).convert('RGBA')
    im = im.resize((int(im.width * S), int(im.height * S)), Image.LANCZOS)
    paste(im, x=x * S, y=y * S)

# ---- CTA
cta = C.pill(int(536 * S), int(224 * S), int(104 * S), (122, 226, 152), (44, 164, 86),
             rim_w=max(6, int(12 * S)), gloss=0.6)
ring = Image.new('RGBA', cta.size, (0, 0, 0, 0))
_r = int(104 * S) - int(12 * S)
ImageDraw.Draw(ring).rounded_rectangle(
    [int(12 * S) + 2, int(12 * S) + 2, cta.width - int(12 * S) - 2, cta.height - int(12 * S) - 2],
    radius=_r, outline=(232, 214, 158, 210), width=max(2, int(3 * S)))
cta.alpha_composite(ring.filter(ImageFilter.GaussianBlur(0.6)))
paste(cta, x=202 * S, y=1152 * S)
txt(470 * S, 1268 * S, '第 5 关', int(76 * S), shadow=(16, 66, 40, 170), dy=int(6 * S))
fs = int(76 * S)
d.text((636 * S, 1266 * S), '›', font=ImageFont.truetype(FONT, fs), fill=(226, 255, 234, 235), anchor='mm')

txt(470 * S, 1406 * S, '点击开始游戏', int(25 * S), fill=(255, 255, 255, 250),
    shadow=(30, 58, 28, 130), dy=2, blur=1.5)

# ---- bottom navigation (sliced, baked tabs)
nav = Image.open(os.path.join(UI, 'nav_bar.png')).convert('RGBA')
nav = nav.resize((int(nav.width * S), int(nav.height * S)), Image.LANCZOS)
paste(nav, x=38 * S, y=1430 * S)

screen.convert('RGB').save(os.path.join(PRE, 'rebuilt_home_1080x1920.png'), optimize=True)
print('preview written')
