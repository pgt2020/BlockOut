# -*- coding: utf-8 -*-
"""Build the review sheets: asset contact sheet, node-state matrix, reference vs rebuilt."""
import os, glob
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, 'preview')
REF = os.path.join(ROOT, '..', 'UI_garden_kit')
FONT = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 17)
FONT_CJK = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22)

BG = (244, 246, 241)


def label(d, xy, text, fill=(38, 52, 44)):
    d.text(xy, text, font=FONT, fill=fill)


def sheet(groups, out, cols=4, cell=210, title_size=26):
    pad = 16
    rows = sum((len(v) + cols - 1) // cols for _, v in groups) + len(groups)
    W = pad + cols * (cell + pad)
    H = pad + rows * (cell + 34 + pad)
    canvas = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(canvas)
    y = pad
    for gname, items in groups:
        d.rectangle([0, y + 6, W, y + 44], fill=(26, 44, 36))
        d.text((pad, y + 14), gname, font=FONT_CJK, fill=(255, 255, 255))
        y += 56
        for i, (name, img) in enumerate(items):
            c, r = i % cols, i // cols
            x = pad + c * (cell + pad)
            ey = y + r * (cell + 34 + pad)
            d.rectangle([x, ey, x + cell, ey + cell], fill=(255, 255, 252),
                        outline=(214, 218, 208))
            im = img.copy()
            if im.width > cell - 16 or im.height > cell - 16:
                k = min((cell - 16) / im.width, (cell - 16) / im.height)
                im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
            canvas.paste(im, (x + (cell - im.width) // 2, ey + (cell - im.height) // 2), im)
            label(d, (x + 4, ey + cell + 6), name)
        y += ((len(items) + cols - 1) // cols) * (cell + 34 + pad)
    canvas.save(out)


slices = []
for p in sorted(glob.glob(os.path.join(ROOT, 'ui', '*.png'))):
    slices.append((os.path.splitext(os.path.basename(p))[0], Image.open(p).convert('RGBA')))
comps = []
for p in sorted(glob.glob(os.path.join(ROOT, 'components', '*.png'))):
    comps.append((os.path.splitext(os.path.basename(p))[0], Image.open(p).convert('RGBA')))

sheet([('A · SLICED FROM REFERENCE — static parts, 1x, text baked in', slices),
       ('B · COMPONENTS — 2x, any text, nine-slice ready', comps)],
      os.path.join(PRE, 'contact_sheet.png'), cols=4, cell=220)

# node state matrix
state_row = [('locked', '8', '未解锁'), ('completed', '7', '已通关'), ('star', '6', '星级'),
             ('current', '5', '当前'), ('fail', '4', '失败'), ('challenge', '挑战', '挑战')]
cw, ch = 240, 300
motor = Image.new('RGB', (cw * len(state_row), ch), (236, 243, 248))
d = ImageDraw.Draw(motor)
for i, (st, num, cap) in enumerate(state_row):
    im = Image.open(os.path.join(ROOT, 'components', 'node_%s.png' % st)).convert('RGBA')
    im = im.resize((200, 200), Image.LANCZOS)
    motor.paste(im, (i * cw + 20, 30), im)
    f = ImageFont.truetype('C:/Windows/Fonts/ariblk.ttf' if len(num) < 3 else 'C:/Windows/Fonts/msyhbd.ttc', 80 if len(num) < 3 else 52)
    d.text((i * cw + cw // 2, 132), num, font=f, fill=(255, 255, 255), anchor='mm')
    d.text((i * cw + cw // 2, 258), cap, font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 20),
           fill=(50, 70, 60), anchor='mm')
motor.save(os.path.join(PRE, 'node_states.png'))

# reference vs rebuilt
ref = Image.open(os.path.join(REF, 'source', 'reference.jpg')).convert('RGB')
reb = Image.open(os.path.join(PRE, 'rebuilt_home_1080x1920.png')).convert('RGB')
h = 1100
ref = ref.resize((int(ref.width * h / ref.height), h), Image.LANCZOS)
reb = reb.resize((int(reb.width * h / reb.height), h), Image.LANCZOS)
cmp = Image.new('RGB', (ref.width + reb.width + 30, h + 40), (250, 250, 246))
cmp.paste(ref, (10, 30))
cmp.paste(reb, (ref.width + 20, 30))
dd = ImageDraw.Draw(cmp)
dd.text((10, 6), 'REFERENCE', font=FONT, fill=(40, 40, 40))
dd.text((ref.width + 20, 6), 'REBUILT 1080x1920', font=FONT, fill=(40, 40, 40))
cmp.save(os.path.join(PRE, 'reference_vs_rebuilt.png'))
print('sheets done')
