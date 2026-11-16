# -*- coding: utf-8 -*-
"""Compose the v3 home screen: 3D-rendered components + sliced static bits + live text."""
import os, sys, json, glob
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'art')
OUT = os.path.join(ROOT, 'components')
PRE = os.path.join(ROOT, 'preview')
REF = os.path.join(ROOT, '..', 'UI_garden_kit', 'ui')
os.makedirs(OUT, exist_ok=True)
os.makedirs(PRE, exist_ok=True)

W, H = 1080, 1920
S = W / 941.0
FONT_CN = 'C:/Windows/Fonts/msyhbd.ttc'
FONT_NUM = 'C:/Windows/Fonts/msyhbd.ttc'


def trim(img, thr=0):
    a = np.array(img)[:, :, 3]
    ys, xs = np.where(a > thr)
    return img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def body_box(img, thr=200):
    a = np.array(img)[:, :, 3]
    ys, xs = np.where(a > thr)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def place_body(canvas, sprite, target_box, opaque=200, shadow=True):
    """Scale so the opaque body lands exactly on target_box (source coords)."""
    sprite = trim(sprite, 0)
    bx1, by1, bx2, by2 = body_box(sprite, opaque)
    body_w, body_h = bx2 - bx1, by2 - by1
    tx1, ty1, tx2, ty2 = [v * S for v in target_box]
    k = min((tx2 - tx1) / body_w, (ty2 - ty1) / body_h)
    new_w, new_h = int(sprite.width * k), int(sprite.height * k)
    sp = sprite.resize((new_w, new_h), Image.LANCZOS)
    x = int(tx1 - bx1 * k)
    y = int(ty1 - by1 * k)
    if shadow:
        sh = Image.new('RGBA', sp.size, (0, 0, 0, 0))
        a = sp.getchannel('A')
        sh.putalpha(a.point(lambda v: int(v * 0.22)))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        canvas.alpha_composite(sh, (x + int(4 * S), y + int(7 * S)))
    canvas.alpha_composite(sp, (x, y))


def txt(canvas, cx, cy, s, size, fill=(255, 255, 255, 255), shadow=(20, 56, 44, 175),
        dy=4, font=None, blur=None):
    f = ImageFont.truetype(font or FONT_CN, size)
    if shadow:
        pad = size
        layer = Image.new('RGBA', (int(size * len(s) * 1.7) + pad * 2, size * 2 + pad), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((layer.width / 2, layer.height / 2), s, font=f, fill=shadow, anchor='mm')
        layer = layer.filter(ImageFilter.GaussianBlur(blur or max(1.0, size / 30)))
        canvas.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2 + dy)))
    ImageDraw.Draw(canvas).text((cx, cy), s, font=f, fill=fill, anchor='mm')


# ---------------------------------------------------------------- background
def cover_resize(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((max(1, int(im.width * s + 0.5)), max(1, int(im.height * s + 0.5))), Image.LANCZOS)
    x = (im.width - w) // 2
    y = (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def grade_bg(img, strong):
    a = np.array(img.convert('RGB'), dtype=np.float32) / 255.0
    h, w = a.shape[:2]
    lum = a.max(axis=2)
    bright = np.clip(lum - 0.80, 0, 1)[..., None] * a
    bloom = cv2.GaussianBlur(bright, (0, 0), 20)
    a = np.clip(a + bloom * (0.45 if strong else 0.22), 0, 1)
    a[..., 0] = np.clip(a[..., 0] * 1.03, 0, 1)
    a[..., 2] = np.clip(a[..., 2] * 0.97, 0, 1)
    if strong:
        a = np.clip((a - 0.5) * 1.06 + 0.5 + 0.010, 0, 1)
        blur = cv2.GaussianBlur(a, (0, 0), 3.0)
        yy = np.linspace(0, 1, h)[:, None, None]
        m = np.clip((0.46 - yy) / 0.34, 0, 1) ** 1.5
        a = a * (1 - m) + blur * m
    Y, X = np.mgrid[0:h, 0:w]
    r = np.sqrt(((X - w / 2) / (w / 2)) ** 2 + ((Y - h / 2) / (h / 2)) ** 2)
    v = np.clip(1.05 - 0.12 * np.clip(r - 0.6, 0, None) / 0.6, 0, 1)[..., None]
    a = a * v
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).convert('RGBA')


BG_CANDIDATES = ['bg_source.png', 'bg_source.jpg', 'bg_source.jpeg', 'bg_garden.png']
bg_path, bg_name = None, None
for name in BG_CANDIDATES:
    cand = os.path.join(ART, name)
    if os.path.exists(cand):
        bg_path, bg_name = cand, name
        break
if bg_path is None:
    raise SystemExit('no background found in art/')
external = bg_name.startswith('bg_source')
bg_src = cover_resize(Image.open(bg_path).convert('RGB'), W, H)
# mild unsharp so the upscaled art does not read as soft
bg_src = bg_src.filter(ImageFilter.UnsharpMask(radius=2.0, percent=68, threshold=2))
bg = grade_bg(bg_src, strong=not external)
print('background:', bg_name, '(external, light grade)' if external else '(render, full grade)')
screen = bg.copy()

# ---------------------------------------------------------------- nodes
NODES = [
    ('node_locked',    '8',    (408, 60, 553, 196),  ('lock', 'br')),
    ('node_locked',    '7',    (408, 272, 551, 408), ('lock', 'br')),
    ('node_star',      '6',    (397, 508, 544, 642), ('star', 'br')),
    ('node_current',   '5',    (379, 737, 555, 921), None),
    ('node_fail',      '4',    (207, 999, 338, 1086), ('skull', 'b')),
    ('node_challenge', '挑战', (599, 1001, 729, 1086), ('skull', 'b')),
]
BADGES = {k: Image.open(os.path.join(ART, 'badge_%s.png' % k)).convert('RGBA')
          for k in ('lock', 'star', 'skull')}

for name, digit, box, badge in NODES:
    if name == 'node_current':
        gw = int((box[2] - box[0]) * S * 2.1)
        gh = int((box[3] - box[1]) * S * 2.1)
        glow = Image.new('RGBA', (gw, gh), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([0, 0, gw, gh], fill=(255, 226, 140, 92))
        glow = glow.filter(ImageFilter.GaussianBlur(int(gw * 0.16)))
        screen.alpha_composite(glow, (int((box[0] + box[2]) / 2 * S - gw / 2),
                                      int((box[1] + box[3]) / 2 * S - gh / 2)))
    spr = Image.open(os.path.join(ART, name + '.png')).convert('RGBA')
    place_body(screen, spr, box)
    cx = (box[0] + box[2]) / 2 * S
    cy = (box[1] + box[3]) / 2 * S
    size = int((box[2] - box[0]) * S * (0.70 if digit != '挑战' else 0.33))
    txt(screen, cx, cy, digit, size, shadow=(16, 52, 38, 235), dy=max(2, size // 18),
        font=FONT_NUM if digit != '挑战' else FONT_CN)
    if badge:
        kind, pos = badge
        b = trim(BADGES[kind], 0)
        bw = int((box[2] - box[0]) * S * 0.34)
        b = b.resize((bw, int(b.height * bw / b.width)), Image.LANCZOS)
        if pos == 'br':
            screen.alpha_composite(b, (int(box[2] * S - b.width * 0.62), int(box[3] * S - b.height * 0.72)))
        else:
            screen.alpha_composite(b, (int(cx - b.width / 2), int(box[3] * S - b.height * 0.34)))

# ---------------------------------------------------------------- callout bubble
bub = trim(Image.open(os.path.join(ART, 'bubble.png')).convert('RGBA'), 0)
bw = int(138 * S)
bub = bub.resize((bw, int(bub.height * bw / bub.width)), Image.LANCZOS)
screen.alpha_composite(bub, (int(556 * S), int(692 * S)))
txt(screen, 626 * S, 726 * S, '当前关卡', int(25 * S), fill=(116, 84, 52, 255), shadow=None)

# ---------------------------------------------------------------- mascot (sliced)
mascot = Image.open(os.path.join(REF, 'mascot_arrow.png')).convert('RGBA')
mascot = mascot.resize((int(mascot.width * S), int(mascot.height * S)), Image.LANCZOS)
screen.alpha_composite(mascot, (int(378 * S), int(944 * S)))

# ---------------------------------------------------------------- static slices
for name, (x, y) in [('btn_settings', (40, 38)), ('pill_currency', (650, 48)),
                     ('btn_task', (726, 228)), ('btn_achievement', (726, 473))]:
    im = Image.open(os.path.join(REF, name + '.png')).convert('RGBA')
    im = im.resize((int(im.width * S), int(im.height * S)), Image.LANCZOS)
    screen.alpha_composite(im, (int(x * S), int(y * S)))

# ---------------------------------------------------------------- CTA
place_body(screen, Image.open(os.path.join(ART, 'btn_primary.png')).convert('RGBA'),
           (204, 1162, 728, 1372))
txt(screen, 468 * S, 1267 * S, '第 5 关', int(76 * S), shadow=(14, 60, 36, 200), dy=int(5 * S))
ImageDraw.Draw(screen).text((634 * S, 1266 * S), '›',
                            font=ImageFont.truetype(FONT_CN, int(76 * S)),
                            fill=(226, 255, 234, 235), anchor='mm')
txt(screen, 470 * S, 1406 * S, '点击开始游戏', int(26 * S), fill=(255, 255, 255, 255),
    shadow=(24, 42, 20, 215), dy=2, blur=1.1)

# ---------------------------------------------------------------- nav (sliced)
nav = Image.open(os.path.join(REF, 'nav_bar.png')).convert('RGBA')
nav = nav.resize((int(nav.width * S), int(nav.height * S)), Image.LANCZOS)
screen.alpha_composite(nav, (int(38 * S), int(1430 * S)))

# ---------------------------------------------------------------- output
screen.convert('RGB').save(os.path.join(PRE, 'rebuilt_home_1080x1920.png'), optimize=True)

ref = Image.open(os.path.join(ROOT, '..', 'UI_garden_kit', 'source', 'reference.jpg')).convert('RGB')
h = 1100
ref_s = ref.resize((int(ref.width * h / ref.height), h), Image.LANCZOS)
out_s = screen.convert('RGB').resize((int(W * h / H), h), Image.LANCZOS)
cmp = Image.new('RGB', (ref_s.width + out_s.width + 30, h + 40), (250, 250, 246))
cmp.paste(ref_s, (10, 30)); cmp.paste(out_s, (ref_s.width + 20, 30))
d = ImageDraw.Draw(cmp)
F = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 18)
d.text((10, 6), 'REFERENCE', font=F, fill=(40, 40, 40))
d.text((ref_s.width + 20, 6), 'V3 3D REBUILD', font=F, fill=(40, 40, 40))
cmp.save(os.path.join(PRE, 'reference_vs_rebuilt.png'))

# ---------------------------------------------------------------- component export
recs = []
for p in sorted(glob.glob(os.path.join(ART, '*.png'))):
    name = os.path.splitext(os.path.basename(p))[0]
    if name.startswith('bg_'):
        continue
    im = trim(Image.open(p).convert('RGBA'), 0)
    im.save(os.path.join(OUT, name + '.png'), optimize=True)
    rec = {'file': 'components/%s.png' % name, 'size': list(im.size)}
    if name in ('btn_primary', 'capsule', 'nav_bar', 'plate_label'):
        r = int(min(im.size) * 0.34)
        rec['nine_slice'] = [r, r, r, r]
    recs.append(rec)
json.dump(recs, open(os.path.join(OUT, 'components.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print('composed; %d components exported' % len(recs))
