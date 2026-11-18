# -*- coding: utf-8 -*-
"""按 BlockOutHomePage.prefab 的实际 rect，用交付素材合成首页预期效果图（非运行截图）。"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, '..', '..', 'Assets/BlockOut/Resources/ArtOutPresentation/Sprites')
FB = 'C:/Windows/Fonts/msyhbd.ttc'
S = 2
W, H = 390 * S, 844 * S


def f(sz):
    return ImageFont.truetype(FB, int(sz * S))


def sc(v):
    return int(round(v * S))


def sprite(name):
    return Image.open(os.path.join(ART, name + '.png')).convert('RGBA')


def at(im, box):
    x, y, w, h = box
    im2 = im.resize((sc(w), sc(h)), Image.LANCZOS)
    canvas.alpha_composite(im2, (sc(x), sc(y)))


canvas = Image.new('RGBA', (W, H), (255, 255, 255, 255))
at(sprite('home_bg'), (0, 0, 390, 844))
d = ImageDraw.Draw(canvas)

# 金币胶囊 22,26 118x40
d.rounded_rectangle((sc(22), sc(26), sc(140), sc(66)), radius=sc(20), fill=(255, 253, 248, 255),
                    outline=(231, 210, 190, 255), width=sc(2))
at(sprite('coin'), (32, 33, 26, 26))
d.text((sc(65), sc(46)), '1280', font=f(18), fill=(184, 124, 5, 255), anchor='lm')
at(sprite('home_plus'), (105, 31, 30, 30))

# 设置 22 距右 / y26 40x40
at(sprite('home_settings'), (328, 26, 40, 40))

# 标题牌 150x46 @ y150
at(sprite('home_title_plate'), (120, 150, 150, 46))
d.text((sc(195), sc(174)), '第 1 关', font=f(22), fill=(59, 42, 36, 255), anchor='mm')

# 四个入口
tools = [('gallery', '图库', 22, 366, 'tl'), ('skin', '皮肤', 22, 474, 'tl'),
         ('daily', '每日', 22, 366, 'tr'), ('achievement', '成就', 22, 474, 'tr')]
for key, label, x, y, side in tools:
    left = x if side == 'tl' else 390 - x - 68
    at(sprite('home_circle'), (left, y, 68, 68))
    at(sprite('home_icon_' + key), (left + 11, y + 11, 46, 46))
    cx, cy = sc(left + 34), sc(y + 79)
    for dx, dy in ((1, -1), (-1, -1), (1, 1), (-1, 1)):
        d.text((cx + dx, cy + dy), label, font=f(14), fill=(255, 255, 255, 255), anchor='mm')
    d.text((cx, cy), label, font=f(14), fill=(59, 42, 36, 255), anchor='mm')

# 绿色 CTA 280x86 @ y690
at(sprite('home_btn_start'), (55, 690, 280, 86))
d.text((sc(195), sc(733)), '开始', font=f(34), fill=(255, 255, 255, 255), anchor='mm')

out = canvas.convert('RGB')
out.resize((390 * 2, 844 * 2), Image.LANCZOS).save(os.path.join(ROOT, 'samples', 'home_expected.png'))
print('saved home_expected.png', out.size)
