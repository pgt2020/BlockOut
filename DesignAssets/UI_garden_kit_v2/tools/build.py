# -*- coding: utf-8 -*-
"""Build the garden-home UI kit (v2) from the reference screenshot.

Outputs
  ui/          baked elements as they appear in the reference (RGBA)
  ui_empty/    same elements with baked level numbers / labels removed
  preview/     rebuilt 1080x1920 screen using the empty assets + live text
  manifest.json, README.md
"""
import os, sys, json, shutil
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matte import matte, _ss_mask, local_shapes
import kit_defs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = Image.open(os.path.join(ROOT, '..', 'UI_garden_kit', 'source', 'reference.jpg')).convert('RGB')
UI = os.path.join(ROOT, 'ui')
PRE = os.path.join(ROOT, 'preview')
BG = os.path.join(ROOT, 'background')
for d in (UI, PRE, BG):
    os.makedirs(d, exist_ok=True)

FONT_CJK = 'C:/Windows/Fonts/msyhbd.ttc'
manifest = []


def save(img, rel, box, note, extra=None):
    p = os.path.join(ROOT, rel)
    img.save(p, optimize=True)
    rec = {'file': rel.replace('\\', '/'),
           'size': list(img.size),
           'source_box': list(box),
           'note': note}
    if extra:
        rec.update(extra)
    manifest.append(rec)
    return p


def fill_box(rgba, box, axis='h', feather=2.0):
    """Erase the glyphs inside `box` and rebuild the fill from the element's own pixels.

    Samples only pixels that are opaque (alpha > .95) and outside the box, so a glyph
    box that reaches the rim can never pull sky/grass into the fill.
    """
    arr = np.array(rgba.convert('RGBA'), dtype=np.float32)
    h, w = arr.shape[:2]
    x1, y1, x2, y2 = box
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    a = arr[:, :, 3]
    filled = arr.copy()

    def med(px):
        return np.median(px, axis=0) if len(px) else None

    if axis == 'h':
        for y in range(y1, y2):
            row_opaque = a[y] > 235
            left = np.where(row_opaque[:x1])[0]
            right = np.where(row_opaque[x2:])[0] + x2
            c0 = med(arr[y, left[-14:], :3]) if len(left) else None
            c1 = med(arr[y, right[:14], :3]) if len(right) else None
            if c0 is None and c1 is None:
                continue
            c0 = c1 if c0 is None else c0
            c1 = c0 if c1 is None else c1
            n = x2 - x1
            t = (np.arange(n, dtype=np.float32) / max(1, n - 1))[:, None]
            filled[y, x1:x2, :3] = c0 * (1 - t) + c1 * t
        filled[y1:y2, x1:x2, :3] = cv2.blur(filled[y1:y2, x1:x2, :3], (9, 1))
    else:
        for x in range(x1, x2):
            col_opaque = a[:, x] > 235
            top = np.where(col_opaque[:y1])[0]
            bot = np.where(col_opaque[y2:])[0] + y2
            c0 = med(arr[top[-14:], x, :3]) if len(top) else None
            c1 = med(arr[bot[:14], x, :3]) if len(bot) else None
            if c0 is None and c1 is None:
                continue
            c0 = c1 if c0 is None else c0
            c1 = c0 if c1 is None else c1
            n = y2 - y1
            t = (np.arange(n, dtype=np.float32) / max(1, n - 1))[:, None]
            filled[y1:y2, x, :3] = c0 * (1 - t) + c1 * t
        filled[y1:y2, x1:x2, :3] = cv2.blur(filled[y1:y2, x1:x2, :3], (1, 9))

    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rectangle([x1, y1, x2 - 1, y2 - 1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(feather))
    m = (np.array(mask, dtype=np.float32) / 255.0)[:, :, None]
    out = arr * (1 - m) + filled * m
    out[:, :, 3] = arr[:, :, 3]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')


def save_pair(img, name, box, note):
    save(img, os.path.join('ui', name + '.png'), box, note)


# ---------------------------------------------------------------- baked slices
baked = {}
for name, box, shapes, opt in kit_defs.ELEMENTS:
    im = matte(SRC, box, shapes, feather=opt.get('feather', 1.15),
               desky=opt.get('desky', False), degrass=opt.get('degrass', 0))
    if name == 'nav_bar':
        a = im.getchannel('A').point(lambda v: 0 if v < 150 else v)
        im.putalpha(a)
    baked[name] = im
    save_pair(im, name, box, '参考图原样切出（含烘焙文字）')

# NOTE: 去文字出无字底座已放弃（见 README），动态件走 components/

# tabs / nav are kept as baked slices for now (they carry the cream card artwork)
for name, box, r in kit_defs.TABS:
    im = SRC.crop(box).convert('RGBA')
    w, h = im.size
    m = Image.new('L', (w * 4, h * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 4 - 1, h * 4 - 1], radius=r * 4, fill=255)
    m = m.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.7))
    im.putalpha(m)
    save(im, os.path.join('ui', name + '.png'), box, '导航卡片（含图标与文字）')

# NOTE: 程序化组件统一由 tools/export_components.py 输出到 components/（2x + 九宫格）。
# 这里只保留切图与拼图，不再重复生成栅格组件。

# ------------------------------------------------------------------ background
bg_src = os.path.join(ROOT, '..', 'UI_garden_kit', 'background', 'bg_garden_1080x1920.png')
if os.path.exists(bg_src):
    shutil.copy2(bg_src, os.path.join(BG, 'bg_garden_1080x1920.png'))

# 拼图（1080x1920 还原图）已移到 tools/build_preview.py：
#   它用 components/ 的动态件 + ui/ 的静态件组合，文案可换。

with open(os.path.join(ROOT, 'manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print('built', len(manifest), 'records')
