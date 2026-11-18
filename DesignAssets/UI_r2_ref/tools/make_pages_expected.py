"""按 prefab 实际设计盒坐标，用真实素材合成 5 页预期图（2×，非运行截图）。

页面：加载 / 图库 / 商店 / 失败弹窗 / 结算弹窗
坐标来源：Tools/UIAuthoring/generate_prefabs.py 中的设计盒数值（390×844）。
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'Assets/BlockOut/Resources/ArtOutPresentation/Sprites'
FONT_PATH = ROOT / 'Assets/Resources/Fonts/SourceHanSansCN-Regular.otf'
OUT = ROOT / 'DesignAssets/UI_r2_ref/samples'
S = 2
W, H = 390 * S, 844 * S

CREAM = (255, 246, 236, 255)
RAISED = (255, 253, 248, 255)
DEEP = (252, 235, 216, 255)
STROKE = (231, 210, 190, 255)
COCOA = (59, 42, 36, 255)
COCOA60 = (110, 84, 73, 255)
DISABLED = (138, 117, 104, 255)
GREEN = (30, 143, 104, 255)
GOLD = (107, 71, 0, 255)
CORAL = (247, 110, 94, 255)


def sc(v):
    return int(round(v * S))


def f(size):
    return ImageFont.truetype(str(FONT_PATH), sc(size))


def sprite(name):
    return Image.open(ART / f'{name}.png').convert('RGBA')


SP_ROUND = sprite('round')
SP_CIRCLE = sprite('circle')
SP_SHADOW = sprite('card_soft_shadow')
SP_COIN = sprite('coin')
SP_LOGO = sprite('loading_logo')
SP_HEART = sprite('icon_heart_broken')
SP_BUNT_L = sprite('deco_bunting_l')
SP_BUNT_R = sprite('deco_bunting_r')
SP_ICON = {n: sprite(n) for n in ('bulb', 'hammer', 'wand', 'heart', 'lock', 'pause')}


def shadow_card(d, box, fill, radius=22, stroke=STROKE, sw=2, pad=7):
    l, t, r, b = [sc(v) for v in box]
    img = d._image
    if pad:
        sh = SP_SHADOW.resize((r - l + 2 * sc(pad), b - t + 2 * sc(pad)))
        tint = Image.new('RGBA', sh.size, (102, 69, 33, 87))
        img.paste(tint, (l - sc(pad), t - sc(pad) + sc(2)), sh.split()[3])
    rr = SP_ROUND.resize((r - l, b - t))
    img.paste(stroke, (l, t), rr.split()[3])
    inner = SP_ROUND.resize((r - l - 2 * sc(sw), b - t - 2 * sc(sw)))
    img.paste(fill, (l + sc(sw), t + sc(sw)), inner.split()[3])


def soft_button(d, box, text, fill=GREEN, tcolor=(255, 255, 255, 255), size=16):
    shadow_card(d, box, fill, radius=16, stroke=(255, 255, 255, 255), sw=2, pad=5)
    l, t, r, b = box
    d.text((sc((l + r) / 2), sc((t + b) / 2)), text, font=f(size), fill=tcolor, anchor='mm')


def icon(d, name, box):
    im = SP_ICON[name]
    l, t, r, b = [sc(v) for v in box]
    w, h = r - l, b - t
    k = min(w / im.width, h / im.height)
    im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))))
    d._image.alpha_composite(im, (l + (w - im.width) // 2, t + (h - im.height) // 2))


def coin_icon(d, box):
    l, t, r, b = [sc(v) for v in box]
    im = SP_COIN.resize((r - l, b - t))
    d._image.alpha_composite(im, (l, t))


def make_page():
    img = Image.new('RGBA', (W, H), CREAM)
    d = ImageDraw.Draw(img)
    d._image = img
    return d


def header(d, title, active):
    d.ellipse([sc(22), sc(26), sc(62), sc(66)], fill=(255, 255, 255, 255))
    d.line([sc(34), sc(46), sc(50), sc(34)], fill=COCOA, width=sc(2.6))
    d.line([sc(34), sc(46), sc(50), sc(58)], fill=COCOA, width=sc(2.6))
    shadow_card(d, (250, 26, 368, 66), RAISED, radius=14, sw=1.5, pad=4)
    coin_icon(d, (260, 33, 286, 59))
    d.text((sc(294), sc(46)), '0', font=f(18), fill=GOLD, anchor='lm')
    d.text((sc(195), sc(47)), title, font=f(20), fill=COCOA, anchor='mm')


def nav(d, active):
    shadow_card(d, (24, 756, 366, 820), RAISED, radius=18, sw=2, pad=6)
    for i, (t, key) in enumerate([('首页', 'Home'), ('图鉴', 'Collection'), ('商店', 'Store')]):
        x0 = 36 + i * 110
        on = key == active
        soft_button(d, (x0, 764, x0 + 98, 812), t,
                    fill=GREEN if on else RAISED,
                    tcolor=(255, 255, 255, 255) if on else COCOA, size=14)


def regions(d, box, art_index):
    """12 格拼片占位：浅底 + 一两块已点亮（示意），正式运行时由真实 artwork 驱动。"""
    l, t, r, b = [sc(v) for v in box]
    cw, ch = (r - l) / 4, (b - t) / 3
    for i in range(12):
        x, y = l + (i % 4) * cw, t + (i // 4) * ch
        d.rounded_rectangle([x + sc(1), y + sc(1), x + cw - sc(1), y + ch - sc(1)],
                            radius=sc(4), fill=(240, 228, 210, 255))
    for i in range(art_index):
        x, y = l + (i % 4) * cw, t + (i // 4) * ch
        d.rounded_rectangle([x + sc(2), y + sc(2), x + cw - sc(2), y + ch - sc(2)],
                            radius=sc(4), fill=GREEN)


# ============ 1) 加载页 ============
d = make_page()
bg = sprite('loading_bg').resize((W, H))
d._image.alpha_composite(bg)
logo = SP_LOGO
logo = logo.resize((sc(150), sc(146)))
d._image.alpha_composite(logo, (sc(120), sc(236)))
d.text((sc(195), sc(447)), '点击画廊', font=f(32), fill=CORAL, anchor='mm')
d.text((sc(195), sc(490)), '正在准备画作…', font=f(14), fill=COCOA, anchor='mm')
shadow_card(d, (85, 688, 305, 702), DEEP, radius=7, sw=0, pad=0)
d.rounded_rectangle([sc(88), sc(691), sc(88) + int(sc(214) * .6), sc(699)], radius=sc(4), fill=GREEN)
d._image.convert('RGB').resize((W, H), Image.LANCZOS).save(OUT / 'loading_expected.png')

# ============ 2) 图库页 ============
d = make_page()
header(d, '图库', 'Collection')
shadow_card(d, (24, 86, 366, 276), RAISED, radius=22, sw=2, pad=6)
shadow_card(d, (38, 100, 158, 262), (240, 228, 210, 255), radius=14, sw=1, pad=0)
regions(d, (42, 104, 154, 258), 5)
d.text((sc(195), sc(122)), '第一章', font=f(16), fill=COCOA, anchor='lm')
d.text((sc(195), sc(154)), '拼片 5/12', font=f(12), fill=COCOA60, anchor='lm')
shadow_card(d, (174, 190, 352, 206), DEEP, radius=6, sw=0, pad=0)
d.rounded_rectangle([sc(177), sc(193), sc(177) + int(sc(175) * .42), sc(203)], radius=sc(4), fill=GREEN)
soft_button(d, (174, 226, 352, 266), '查看大图', fill=DEEP, tcolor=COCOA, size=14)
for row in range(2):
    y0 = 288 + row * 88
    shadow_card(d, (24, y0, 366, y0 + 76), RAISED, radius=18, sw=2, pad=5)
    d.rounded_rectangle([sc(38), sc(y0 + 10), sc(94), sc(y0 + 66)], radius=sc(10), fill=(240, 228, 210, 255))
    d.text((sc(110), sc(y0 + 26)), '第 %d 关' % (row + 1), font=f(16), fill=COCOA, anchor='lm')
    d.text((sc(110), sc(y0 + 52)), '章节进度', font=f(12), fill=DISABLED, anchor='lm')
shadow_card(d, (24, 464, 366, 636), RAISED, radius=20, sw=2, pad=5)
d.text((sc(38), sc(486)), '重复挑战', font=f(15), fill=COCOA, anchor='lm')
for i in range(6):
    x0 = 38 + i * 52
    d.ellipse([sc(x0), sc(508), sc(x0 + 44), sc(552)], fill=GREEN if i < 3 else (240, 228, 210, 255))
    d.text((sc(x0 + 22), sc(530)), str(i + 1), font=f(14),
           fill=(255, 255, 255, 255) if i < 3 else DISABLED, anchor='mm')
d.text((sc(38), sc(608)), '已通关关卡可重复挑战', font=f(11), fill=DISABLED, anchor='lm')
nav(d, 'Collection')
d._image.convert('RGB').resize((W, H), Image.LANCZOS).save(OUT / 'collection_expected.png')

# ============ 3) 商店页 ============
d = make_page()
header(d, '皮肤', 'Store')
tools = [('bulb', '提示', '高亮可飞出的方块', '300'), ('hammer', '锤子', '消除任意在场方块', '500'),
         ('wand', '炸弹', '自动消除一组方块', '800')]
for i, (ic, name, desc, price) in enumerate(tools):
    y0 = 86 + i * 124
    shadow_card(d, (24, y0, 366, y0 + 112), RAISED, radius=20, sw=2, pad=6)
    shadow_card(d, (38, y0 + 20, 110, y0 + 92), DEEP, radius=14, sw=1, pad=0)
    icon(d, ic, (48, y0 + 30, 100, y0 + 82))
    d.text((sc(124), sc(y0 + 28)), name, font=f(16), fill=COCOA, anchor='lm')
    d.text((sc(124), sc(y0 + 54)), desc, font=f(11), fill=DISABLED, anchor='lm')
    coin_icon(d, (126, y0 + 84, 144, y0 + 102))
    d.text((sc(152), sc(y0 + 94)), price + ' 金币', font=f(13), fill=GOLD, anchor='lm')
    soft_button(d, (276, y0 + 34, 352, y0 + 78), '购买', size=15)
nav(d, 'Store')
d._image.convert('RGB').resize((W, H), Image.LANCZOS).save(OUT / 'store_expected.png')

# ============ 4) 失败弹窗 ============
d = make_page()
d.rectangle([0, 0, W, H], fill=(43, 30, 24, 150))
d._image.alpha_composite(Image.new('RGBA', (W, H), (43, 30, 24, 105)))
shadow_card(d, (35, 212, 355, 632), RAISED, radius=26, sw=3, pad=8)
d.text((sc(195), sc(255)), '生命用完了', font=f(24), fill=COCOA, anchor='mm')
hb = SP_HEART.resize((sc(100), int(sc(100) * SP_HEART.height / SP_HEART.width)))
d._image.alpha_composite(hb, (sc(145), sc(282)))
d.text((sc(195), sc(372)), '再试一次，一次就能成功哦！', font=f(13), fill=DISABLED, anchor='mm')
soft_button(d, (65, 396, 325, 450), '看广告复活', size=18)
shadow_card(d, (251, 388, 311, 412), (232, 162, 12, 255), radius=12, sw=0, pad=0)
d.text((sc(281), sc(400)), '免费', font=f(12), fill=GOLD, anchor='mm')
d.text((sc(195), sc(468)), '恢复后继续当前关卡', font=f(11), fill=DISABLED, anchor='mm')
soft_button(d, (65, 494, 325, 542), '重新开始', fill=DEEP, tcolor=COCOA, size=16)
soft_button(d, (65, 556, 325, 596), '回首页', fill=RAISED, tcolor=DISABLED, size=14)
d._image.convert('RGB').resize((W, H), Image.LANCZOS).save(OUT / 'fail_expected.png')

# ============ 5) 结算弹窗 ============
d = make_page()
d.rectangle([0, 0, W, H], fill=(43, 30, 24, 150))
d._image.alpha_composite(Image.new('RGBA', (W, H), (43, 30, 24, 105)))
shadow_card(d, (30, 100, 360, 744), RAISED, radius=26, sw=3, pad=8)
bl = SP_BUNT_L.resize((sc(74), sc(58)))
br = SP_BUNT_R.resize((sc(74), sc(58)))
d._image.alpha_composite(bl, (sc(42), sc(108)))
d._image.alpha_composite(br, (sc(274), sc(108)))
d.text((sc(195), sc(141)), '完成', font=f(28), fill=COCOA, anchor='mm')
shadow_card(d, (45, 184, 345, 488), (255, 255, 255, 255), radius=18, sw=2, pad=5)
regions(d, (54, 193, 336, 479), 5)
coin_icon(d, (133, 505, 161, 533))
d.text((sc(184), sc(519)), '+60', font=f(20), fill=GOLD, anchor='lm')
d.text((sc(195), sc(551)), '获得新拼片', font=f(13), fill=COCOA, anchor='mm')
d.text((sc(195), sc(578)), '作品已收入图库', font=f(11), fill=DISABLED, anchor='mm')
soft_button(d, (65, 602, 325, 656), '下一关', size=19)
for i, t in enumerate(['重玩', '收藏', '首页']):
    x0 = 45 + i * 102
    soft_button(d, (x0, 672, x0 + 96, 720), t, fill=DEEP, tcolor=COCOA, size=14)
d._image.convert('RGB').resize((W, H), Image.LANCZOS).save(OUT / 'settlement_expected.png')

print('5 张预期图已输出')
