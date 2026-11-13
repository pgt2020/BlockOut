# -*- coding: utf-8 -*-
import os, json, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
import cv2, numpy as np

SRC = 'DesignAssets/UI_garden_kit/source/reference.jpg'
OUT = 'DesignAssets/UI_garden_kit'
UI = os.path.join(OUT, 'ui')
GEN = os.path.join(OUT, 'generated')
ICON = os.path.join(OUT, 'icons')
PRE = os.path.join(OUT, 'preview')
for d in (UI, GEN, ICON, PRE):
    os.makedirs(d, exist_ok=True)

src = Image.open(SRC).convert('RGBA')
SS = 4
manifest = []

def rrect_mask(w, h, shapes, feather=0.9):
    m = Image.new('L', (w * SS, h * SS), 0)
    d = ImageDraw.Draw(m)
    for s in shapes:
        t = s[0]
        if t == 'rr':
            _, x1, y1, x2, y2, r = s
            d.rounded_rectangle([x1 * SS, y1 * SS, x2 * SS, y2 * SS], radius=r * SS, fill=255)
        elif t == 'circle':
            _, cx, cy, r = s
            d.ellipse([(cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS], fill=255)
        elif t == 'poly':
            _, pts = s
            d.polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    m = m.resize((w, h), Image.LANCZOS)
    if feather:
        m = m.filter(ImageFilter.GaussianBlur(feather))
    return m

def cut(name, box, shapes, feather=0.9, folder=UI, note='', skyclean=True):
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    local = []
    for s in shapes:
        t = s[0]
        if t == 'rr':
            _, a, b, c, d_, r = s
            local.append(('rr', a - x1, b - y1, c - x1, d_ - y1, r))
        elif t == 'circle':
            _, cx, cy, r = s
            local.append(('circle', cx - x1, cy - y1, r))
        elif t == 'poly':
            _, pts = s
            local.append(('poly', [(a - x1, b - y1) for a, b in pts]))
    m = rrect_mask(w, h, local, feather)
    im = src.crop(box).convert('RGBA')
    im.putalpha(m)
    if skyclean:
        arr = np.array(im)
        hsv = cv2.cvtColor(arr[:, :, :3], cv2.COLOR_RGB2HSV)
        sky = (hsv[:, :, 0] >= 90) & (hsv[:, :, 0] <= 125) & (hsv[:, :, 1] > 70) & (hsv[:, :, 2] > 95)
        arr[:, :, 3][sky] = 0
        im = Image.fromarray(arr)
    path = os.path.join(folder, name + '.png')
    im.save(path, optimize=True)
    manifest.append({'file': os.path.relpath(path, OUT).replace('\\', '/'), 'type': 'sliced', 'size': [w, h], 'source_box': list(box), 'note': note})

# ---------------- sliced UI ----------------
cut('btn_settings', (50, 48, 158, 156), [('circle', 104, 102, 49)], 1.0, note='圆形奶油底 + 齿轮')
cut('pill_currency', (662, 58, 916, 150), [('rr', 672, 68, 906, 140, 36)], 1.0, note='票券 + 数量 + 加号，复合胶囊')
cut('btn_task', (735, 240, 910, 440), [('circle', 820, 320, 74), ('rr', 755, 375, 895, 428, 20)], 1.0, note='任务按钮：圆盘 + 标签')
cut('btn_achievement', (735, 483, 910, 685), [('circle', 820, 563, 74), ('rr', 755, 620, 895, 673, 20)], 1.0, note='成就按钮：圆盘 + 标签')
cut('node_locked_40', (395, 45, 565, 220), [('rr', 404, 56, 556, 190, 32), ('circle', 520, 163, 28)], 1.0, note='灰锁节点（数字烘焙）')
cut('node_locked_39', (395, 265, 565, 425), [('rr', 404, 273, 556, 396, 32), ('circle', 520, 382, 28)], 1.0, note='灰锁节点（数字烘焙）')
cut('node_star_38', (394, 504, 570, 682), [('rr', 402, 512, 539, 668, 32), ('circle', 521, 632, 27)], 1.0, note='紫星节点（数字烘焙）')
cut('node_current_37', (360, 732, 570, 958), [('rr', 376, 744, 556, 916, 48), ('poly', [(450, 900), (490, 900), (470, 940)])], 3.0, note='当前关卡绿节点 + 下指箭头')
cut('node_fail_36', (193, 968, 350, 1125), [('rr', 205, 977, 341, 1083, 32), ('circle', 272, 1088, 28)], 1.0, note='失败红节点 + 骷髅')
cut('node_challenge', (588, 968, 755, 1125), [('rr', 600, 977, 744, 1083, 32), ('circle', 672, 1088, 28)], 1.0, note='挑战红节点 + 骷髅')
cut('bubble_current', (553, 692, 700, 785), [('rr', 563, 703, 685, 758, 24), ('poly', [(570, 748), (596, 756), (578, 777)])], 1.0, note='“当前关卡”气泡')
cut('mascot_arrow', (378, 944, 530, 1080), [
    ('rr', 413, 948, 502, 1072, 12),
    ('rr', 398, 950, 416, 978, 3), ('rr', 388, 990, 410, 1016, 3),
    ('rr', 383, 1024, 401, 1046, 3), ('rr', 398, 1050, 416, 1076, 3),
    ('rr', 500, 958, 518, 980, 3), ('rr', 500, 988, 518, 1014, 3),
    ('rr', 500, 1022, 522, 1046, 3), ('rr', 500, 1048, 516, 1072, 3)
], 1.0, note='黄色方块角色 + 绿箭头，按轮廓遮罩')


cut('btn_primary', (198, 1156, 744, 1372), [('rr', 208, 1166, 734, 1362, 72)], 1.2, note='主按钮完整版（文字烘焙）')

# nav bar
cut('nav_bar', (48, 1438, 892, 1672), [('rr', 58, 1448, 882, 1662, 54)], 1.2, note='底部导航整条')
# tabs: opaque crops on the bar (baked cream)
for name, box in [
    ('tab_home', (80, 1480, 264, 1650)),
    ('tab_gallery', (288, 1480, 472, 1650)),
    ('tab_skin', (496, 1480, 680, 1650)),
    ('tab_daily', (704, 1480, 888, 1650)),
]:
    im = src.crop(box).convert('RGBA')
    w, h = im.size
    r = 50 if name == 'tab_daily' else 30
    m = Image.new('L', (w * 4, h * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 4 - 1, h * 4 - 1], radius=r * 4, fill=255)
    m = m.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
    im.putalpha(m)
    p = os.path.join(UI, name + '.png')
    im.save(p, optimize=True)
    manifest.append({'file': os.path.relpath(p, OUT).replace('\\', '/'), 'type': 'sliced-opaque', 'size': [box[2]-box[0], box[3]-box[1]], 'source_box': list(box), 'note': '带导航奶油底，需与 nav_bar 同位置使用'})

# ---------------- generated node bases ----------------
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def node_base(name, top, bottom, glow=None, border='#FFFDF6', size=256):
    S = 1024
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = 70
    box = [pad, pad - 10, S - pad, S - pad - 10]
    # shadow
    sh = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([box[0] + 14, box[1] + 26, box[2] + 14, box[3] + 26], radius=170, fill=(30, 40, 20, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(26))
    im.alpha_composite(sh)
    if glow:
        g = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(g).rounded_rectangle([box[0] - 18, box[1] - 18, box[2] + 18, box[3] + 18], radius=190, fill=glow)
        g = g.filter(ImageFilter.GaussianBlur(26))
        im.alpha_composite(g)
    # outer cream border
    d.rounded_rectangle(box, radius=170, fill=border)
    inner = [box[0] + 16, box[1] + 14, box[2] - 16, box[3] - 12]
    # body gradient
    grad = Image.new('RGBA', (inner[2] - inner[0], inner[3] - inner[1]))
    gd = ImageDraw.Draw(grad)
    for y in range(grad.height):
        t = y / max(1, grad.height - 1)
        c = lerp(top, bottom, t)
        gd.line([(0, y), (grad.width, y)], fill=c)
    mask = Image.new('L', grad.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, grad.width - 1, grad.height - 1], radius=150, fill=255)
    im.paste(grad, (inner[0], inner[1]), mask)
    # bevel + clipped inner light
    d.rounded_rectangle(inner, radius=150, outline=(255, 255, 255, 110), width=5)
    overlay = Image.new('RGBA', grad.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle([14, 8, grad.width - 14, 54], radius=24, fill=(255, 255, 255, 95))
    od.ellipse([-50, -80, grad.width + 50, 120], fill=(255, 255, 255, 70))
    od.rounded_rectangle([0, grad.height - 92, grad.width, grad.height], radius=90, fill=(0, 0, 0, 32))
    overlay = overlay.filter(ImageFilter.GaussianBlur(12))
    overlay.putalpha(ImageChops.multiply(overlay.getchannel('A'), mask))
    im.alpha_composite(overlay, dest=(inner[0], inner[1]))
    im = im.resize((size, size), Image.LANCZOS)
    im.save(os.path.join(GEN, name + '.png'), optimize=True)
    manifest.append({'file': 'generated/' + name + '.png', 'type': 'generated', 'size': [size, size], 'note': '无文字节点底座，可叠加关卡数字'})

node_base('node_base_locked', (214, 214, 222), (150, 150, 160))
node_base('node_base_current', (126, 226, 170), (56, 176, 110), glow=(255, 232, 120, 130))
node_base('node_base_star', (196, 156, 238), (128, 86, 190))
node_base('node_base_fail', (255, 138, 120), (218, 72, 62))
node_base('node_base_challenge', (255, 148, 126), (224, 78, 66))

# ---------------- generated primary button ----------------
def primary_button():
    W, H = 1024, 400
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([48, 52, W - 48, H - 20], radius=160, fill=(30, 50, 20, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    im.alpha_composite(sh)
    d.rounded_rectangle([36, 28, W - 36, H - 64], radius=164, fill=(247, 234, 202, 255), outline=(214, 185, 130, 255), width=6)
    d.rounded_rectangle([52, 40, W - 52, H - 76], radius=150, fill=(255, 250, 230, 255))
    # green body
    inner = [64, 52, W - 64, H - 88]
    grad = Image.new('RGBA', (inner[2] - inner[0], inner[3] - inner[1]))
    gd = ImageDraw.Draw(grad)
    for y in range(grad.height):
        t = y / max(1, grad.height - 1)
        c = lerp((112, 218, 136), (42, 158, 82), t)
        gd.line([(0, y), (grad.width, y)], fill=c)
    mask = Image.new('L', grad.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, grad.width - 1, grad.height - 1], radius=140, fill=255)
    im.paste(grad, (inner[0], inner[1]), mask)
    d.rounded_rectangle(inner, radius=140, outline=(34, 130, 66, 120), width=5)
    d.arc([inner[0] + 30, inner[1] + 12, inner[2] - 30, inner[1] + 110], 190, 350, fill=(255, 255, 255, 120), width=10)
    gl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([inner[0] + 30, inner[1] + 10, inner[2] - 30, inner[1] + 120], fill=(255, 255, 255, 85))
    gl = gl.filter(ImageFilter.GaussianBlur(14))
    im.alpha_composite(gl)
    im = im.resize((512, 200), Image.LANCZOS)
    im.save(os.path.join(GEN, 'btn_primary_empty.png'), optimize=True)
    manifest.append({'file': 'generated/btn_primary_empty.png', 'type': 'generated', 'size': [512, 200], 'note': '无文字主按钮，文字/图标另叠'})
primary_button()

def nav_empty():
    W, H = 900, 250
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([36, 40, W - 30, H - 14], radius=70, fill=(30, 50, 20, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    im.alpha_composite(sh)
    d.rounded_rectangle([26, 22, W - 26, H - 40], radius=68, fill=(247, 234, 202, 255), outline=(213, 184, 128, 255), width=5)
    d.rounded_rectangle([36, 32, W - 36, H - 50], radius=60, fill=(255, 251, 238, 255))
    gl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(gl).ellipse([60, 38, W - 60, 120], fill=(255, 255, 255, 120))
    gl = gl.filter(ImageFilter.GaussianBlur(12))
    im.alpha_composite(gl)
    im.resize((450, 125), Image.LANCZOS).save(os.path.join(GEN, 'nav_bar_empty.png'), optimize=True)
    manifest.append({'file': 'generated/nav_bar_empty.png', 'type': 'generated', 'size': [450, 125], 'note': '空导航条，tab 另叠'})
nav_empty()

def bubble_empty():
    W, H = 220, 140
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([30, 24, 200, 110], radius=26, fill=(40, 50, 30, 60))
    sh = sh.filter(ImageFilter.GaussianBlur(8))
    im.alpha_composite(sh)
    d.rounded_rectangle([24, 18, 196, 102], radius=26, fill=(255, 249, 236), outline=(232, 220, 198), width=3)
    d.polygon([(58, 96), (92, 104), (66, 126)], fill=(255, 249, 236), outline=(232, 220, 198))
    d.rounded_rectangle([34, 26, 186, 50], radius=12, fill=(255, 255, 255, 120))
    im.resize((220, 140), Image.LANCZOS).save(os.path.join(GEN, 'bubble_current_empty.png'), optimize=True)
    manifest.append({'file': 'generated/bubble_current_empty.png', 'type': 'generated', 'size': [220, 140], 'note': '空气泡，文字另叠'})
bubble_empty()

# ---------------- generated badges ----------------
def badge(name, kind):
    S = 256
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sh = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([34, 44, 226, 236], fill=(30, 40, 20, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    im.alpha_composite(sh)
    if kind == 'lock':
        d.rounded_rectangle([34, 34, 222, 222], radius=52, fill=(232, 232, 236), outline=(255, 255, 255), width=12)
        d.rounded_rectangle([42, 42, 214, 214], radius=46, fill=(176, 176, 184), outline=(120, 120, 128), width=3)
        d.arc([88, 78, 168, 158], 180, 360, fill=(255, 255, 255), width=16)
        d.rounded_rectangle([76, 116, 180, 196], radius=18, fill=(252, 250, 244), outline=(140, 140, 148), width=4)
        d.ellipse([118, 138, 138, 158], fill=(120, 120, 128))
        d.rounded_rectangle([124, 150, 132, 174], radius=4, fill=(120, 120, 128))
    elif kind == 'star':
        d.ellipse([28, 28, 228, 228], fill=(255, 255, 255))
        d.ellipse([36, 36, 220, 220], fill=(178, 132, 232))
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = 66 if i % 2 == 0 else 28
            pts.append((128 + rad * math.cos(ang), 128 + rad * math.sin(ang)))
        d.polygon(pts, fill=(255, 255, 255))
    else:
        d.ellipse([28, 28, 228, 228], fill=(255, 253, 245), outline=(226, 214, 190), width=6)
        d.ellipse([78, 62, 178, 166], fill=(255, 255, 255), outline=(60, 54, 48), width=6)
        d.rounded_rectangle([92, 136, 164, 192], radius=24, fill=(255, 255, 255), outline=(60, 54, 48), width=6)
        d.ellipse([100, 102, 124, 128], fill=(60, 54, 48))
        d.ellipse([132, 102, 156, 128], fill=(60, 54, 48))
        d.polygon([(123, 126), (133, 126), (128, 140)], fill=(60, 54, 48))
        for x in (108, 122, 136, 150):
            d.line([(x, 162), (x, 184)], fill=(60, 54, 48), width=4)
        d.ellipse([96, 74, 116, 90], fill=(255, 255, 255))
    im = im.resize((128, 128), Image.LANCZOS)
    im.save(os.path.join(GEN, 'badge_' + name + '.png'), optimize=True)
    manifest.append({'file': 'generated/badge_' + name + '.png', 'type': 'generated', 'size': [128, 128], 'note': '独立徽章'})
badge('lock', 'lock')
badge('star', 'star')
badge('skull', 'skull')

# alert + plus
def simple_round(name, fill, glyph):
    S = 256
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([20, 20, 236, 236], fill=(255, 255, 255))
    d.ellipse([28, 28, 228, 228], fill=fill)
    if glyph == 'plus':
        d.rounded_rectangle([92, 116, 164, 140], radius=12, fill=(255, 255, 255))
        d.rounded_rectangle([116, 92, 140, 164], radius=12, fill=(255, 255, 255))
    else:
        d.ellipse([86, 86, 170, 170], fill=fill)
    im = im.resize((128, 128), Image.LANCZOS)
    im.save(os.path.join(GEN, name + '.png'), optimize=True)
    manifest.append({'file': 'generated/' + name + '.png', 'type': 'generated', 'size': [128, 128], 'note': '简单徽章'})
simple_round('badge_plus', (78, 190, 110), 'plus')
simple_round('badge_alert', (234, 64, 52), 'dot')

# ---------------- generated path strips ----------------
def path_strip(name, w, h, horizontal=False):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    edge = (162, 198, 130); mid = (214, 235, 186); light = (238, 249, 222)
    if horizontal:
        for y in range(h):
            t = abs(y - h / 2) / (h / 2)
            c = tuple(int(light[i] * (1 - t ** 1.5) + edge[i] * (t ** 1.5)) for i in range(3))
            d.line([(0, y), (w, y)], fill=c + (235,))
        mask = Image.new('L', (w * 4, h * 4), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w * 4 - 1, h * 4 - 1], radius=h * 2, fill=255)
        mask = mask.resize((w, h), Image.LANCZOS)
        im.putalpha(mask)
        d.rounded_rectangle([14, h // 2 - 4, w - 14, h // 2 + 4], radius=4, fill=(255, 255, 255, 55))
    else:
        for x in range(w):
            t = abs(x - w / 2) / (w / 2)
            c = tuple(int(light[i] * (1 - t ** 1.6) + edge[i] * (t ** 1.6)) for i in range(3))
            d.line([(x, 0), (x, h)], fill=c + (235,))
        d.rectangle([w // 2 - 10, 0, w // 2 + 10, h], fill=(255, 255, 255, 38))
        d.rectangle([0, 0, 1, h], fill=(142, 178, 112, 70))
        d.rectangle([w - 2, 0, w - 1, h], fill=(142, 178, 112, 70))
    im.save(os.path.join(GEN, name + '.png'), optimize=True)
    manifest.append({'file': 'generated/' + name + '.png', 'type': 'generated', 'size': [w, h], 'note': '可纵向/横向平铺的路径条'})
path_strip('path_vertical', 96, 640, False)
path_strip('path_horizontal', 320, 56, True)

bgs = [
    {'file': 'background/bg_garden_1080x1920.png', 'type': 'generated-background', 'size': [1080, 1920], 'note': '生成的花园画廊底图（无 UI）'},
    {'file': 'background/bg_garden_2160x3840.png', 'type': 'generated-background', 'size': [2160, 3840], 'note': '2x 渲染'},
    {'file': 'background/bg_garden_941x1672.png', 'type': 'generated-background', 'size': [941, 1672], 'note': '与参考图同尺寸'},
]
json.dump(bgs + manifest, open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('assets:', len(manifest))
