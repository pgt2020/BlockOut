"""BlockOut 珠子风格 UI 预制生成器（第一版）。

与 generate_prefabs.py 同一套路：纯 Python + PyYAML + Pillow 直接写 uGUI prefab YAML，
不启动 Unity、不刷新 AssetDatabase。保留现有 prefab 的 .meta GUID、View 字段名、
GameObject 命名和项目原有中文文案；只替换视觉资源、配色与布局。

生成目标：
  Assets/BlockOut/Resources/Prefabs/UI/BlockOutHomePage.prefab        (BlockOutHomeView)
  Assets/BlockOut/Resources/Prefabs/UI/BlockOutGameHud.prefab         (BlockOutBoardPageView)
  Assets/BlockOut/Resources/Prefabs/UI/BlockOutSettlementPage.prefab  (BlockOutSettlementView)
  Assets/BlockOut/Resources/Prefabs/UI/BeadsSprites/*.png             (UI 控件贴图)

运行前自动把三个原 prefab 备份到 Tools/UIAuthoring/backup/<时间戳>/。
"""
from pathlib import Path
import re, uuid, yaml, shutil, datetime, math
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI'
SPRITE_DIR = DEST / 'BeadsSprites'
RUNTIME = ROOT / 'Assets/BlockOut/Runtime/UI'
PACKAGE = next((ROOT / 'Library/PackageCache').glob('com.unity.ugui@*'))
FONT = None
SPR = {}

# ---- 商业化色板 v2：深蓝紫夜空 + 奶油白卡 + 高饱和糖果控件 ----
# SKY 为 PIL 用的 0~255 色标；其余为 Unity m_Color 用的 0~1 线性值。
# apply_beads_to_all.py 直接 import 本模块的颜色常量，保证 17 屏同源。
SKY = [(0.0, (24, 34, 92)), (0.30, (42, 44, 118)),
       (0.62, (72, 56, 148)), (0.86, (104, 68, 162)), (1.0, (128, 84, 168))]
INK = (0.086, 0.137, 0.259, 1)        # #16233F 卡片内主文字
INK_SOFT = (0.34, 0.39, 0.53, 1)     # 卡片内次要文字（R8 提高对比度）
ON_BG = (0.965, 0.980, 1.0, 1)       # 深背景上的主文字
ON_BG_SOFT = (0.73, 0.77, 0.93, 1)   # 深背景上的次要文字
CREAM = (1.0, 0.988, 0.960, 1)       # 奶油白卡片
WHITE = (1, 1, 1, 1)
GREEN = (0.29, 0.79, 0.36, 1)
GREEN_DARK = (0.09, 0.42, 0.23, 1)
PINK = (0.98, 0.35, 0.52, 1)
GOLD = (1.0, 0.79, 0.24, 1)
BEAD_COLORS = [
    (1.0, 0.44, 0.28, 1), (1.0, 0.76, 0.20, 1), (0.98, 0.32, 0.58, 1),
    (0.32, 0.82, 0.38, 1), (0.16, 0.78, 0.86, 1), (0.34, 0.52, 0.98, 1),
    (0.70, 0.44, 0.94, 1), (0.24, 0.64, 0.94, 1), (1.0, 0.60, 0.24, 1),
    (0.52, 0.87, 0.50, 1), (0.42, 0.70, 1.0, 1), (0.98, 0.46, 0.40, 1),
]
BEAD_OFF = (0.58, 0.63, 0.80, 1)
# 深色图标贴图落在白色圆底上必须染色才可见；金币本身是彩色，保持原色
ICON_TINT = {'gear': INK, 'pause': INK, 'close': INK_SOFT, 'lock': INK_SOFT,
             'heart': PINK, 'coin': WHITE,
             'bulb': (1.0, 0.58, 0.12, 1), 'hammer': (0.28, 0.50, 0.90, 1),
             'wand': (0.66, 0.42, 0.92, 1)}
# 卡片与描边的 PIL 色（R1 起统一，后续轮次只在此处调）
CARD_FILL = (255, 253, 246, 252)
CARD_EDGE = (188, 198, 230, 255)
CARD_SHADOW = (88, 98, 150, 70)
GRID_FILL = (246, 250, 255, 255)
GRID_EDGE = (176, 192, 232, 255)
GRID_LINE = (206, 220, 246, 160)


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def guid(path):
    meta = Path(str(path) + '.meta')
    if not meta.exists():
        meta.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir() or not path.suffix:
            meta.write_text('fileFormatVersion: 2\nguid: ' + uuid.uuid4().hex +
                            '\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n', encoding='utf-8')
        else:
            meta.write_text('fileFormatVersion: 2\nguid: ' + uuid.uuid4().hex + '\n', encoding='utf-8')
    return re.search(r'guid: (\w+)', meta.read_text(encoding='utf-8-sig'))[1]


def script(name):
    paths = list(RUNTIME.rglob(name + '.cs')) or list(PACKAGE.rglob(name + '.cs'))
    if not paths:
        raise ValueError('script not found: ' + name)
    return {'fileID': 11500000, 'guid': guid(paths[0]), 'type': 3}


def ref(n=0):
    return {'fileID': n}


def vec(x=0, y=0):
    return {'x': x, 'y': y}


def rgba(c):
    return dict(zip(('r', 'g', 'b', 'a'), c))


def ext(path, file_id):
    return {'fileID': file_id, 'guid': guid(path), 'type': 3}


# ---------------------------------------------------------------- sprites
def _lerp(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def _sky_gradient(w, h):
    """深蓝紫夜空：纵向渐变 + 三团柔光晕，给白卡和糖果色控件一个足够暗的舞台。"""
    im = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(SKY) - 1):
            if SKY[i][0] <= t <= SKY[i + 1][0]:
                k = (t - SKY[i][0]) / (SKY[i + 1][0] - SKY[i][0])
                d.line([(0, y), (w, y)], fill=_lerp(SKY[i][1], SKY[i + 1][1], k))
                break
    im = im.convert('RGBA')
    glow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse((-w * .42, -h * .20, w * .72, h * .32), fill=(58, 148, 224, 105))
    g.ellipse((w * .48, h * .04, w * 1.52, h * .56), fill=(186, 92, 210, 78))
    g.ellipse((-w * .28, h * .70, w * 1.05, h * 1.24), fill=(255, 126, 164, 62))
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(w * .16)))
    return im


def _draw_bead(d, cx, cy, r):
    """逐颗珠子：球面渐变 + 左上高光 + 底部暗边 + 中孔。灰度绘制，交给 Image.m_Color 染色。"""
    box = (cx - r, cy - r, cx + r, cy + r)
    d.ellipse((cx - r + 1, cy - r + r * .13, cx + r + 1, cy + r + r * .13),
              fill=(70, 95, 115, 55))
    steps = max(8, int(r / 2))
    for i in range(steps):
        t = i / steps
        inset = r * t * .92
        v = int(198 + 57 * t)
        d.ellipse((cx - r + inset, cy - r + inset, cx + r - inset, cy + r - inset),
                  fill=(v, v, v, 255))
    d.ellipse(box, outline=(178, 195, 208, 255), width=max(1, int(r * .07)))
    d.ellipse((cx - r * .62, cy - r * .70, cx - r * .02, cy - r * .28),
              fill=(255, 255, 255, 185))
    d.ellipse((cx - r * .70, cy - r * .58, cx - r * .48, cy - r * .40),
              fill=(255, 255, 255, 225))
    hr = r * .24
    d.ellipse((cx - hr - 2, cy - hr - 2, cx + hr + 2, cy + hr + 2), fill=(150, 170, 188, 170))
    d.ellipse((cx - hr, cy - hr, cx + hr, cy + hr), fill=(92, 118, 140, 190))
    d.ellipse((cx - hr * .55, cy - hr * .55, cx + hr * .55, cy + hr * .55),
              fill=(62, 88, 110, 150))
    d.arc((cx - r * .82, cy - r * .78, cx + r * .82, cy + r * .90),
          25, 155, fill=(80, 105, 130, 80), width=max(1, int(r * .10)))


def _holes(d, box, step=30, color=(196, 212, 240, 80)):
    x0, y0, x1, y1 = box
    x, y = x0 + step, y0 + step
    while x < x1 - 6:
        while y < y1 - 6:
            d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=color)
            y += step
        x += step
        y = y0 + step


def _brand_art(w=390, h=260):
    """加载页品牌层：金环作品徽章 + 12 颗拼片进度珠。
    中间留透明带，不会遮住原有的中文标题与「加载中」。"""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = w // 2
    d.ellipse((cx - 52, 2, cx + 52, 106), fill=(255, 214, 110, 255),
              outline=(186, 130, 40, 255), width=3)
    d.ellipse((cx - 44, 10, cx + 44, 98), fill=(44, 40, 96, 255))
    art = Image.open(ROOT / 'generated-images' / 'beads_home_plate.png').convert('RGBA')
    art = art.crop((38, 12, 310, 284)).resize((76, 76), Image.LANCZOS)
    im.alpha_composite(art, (cx - 38, 16))
    for i in range(12):
        c = BEAD_COLORS[i] if i < 6 else BEAD_OFF
        rgb = tuple(int(v * 255) for v in c[:3])
        x = 63 + i * 22
        d.ellipse((x, 226, x + 18, 244), fill=rgb + (255,),
                  outline=(255, 255, 255, 190), width=2)
    return im


def _slots_grid(w=318, h=96, cols=6, rows=2):
    """重复挑战格的静态槽位：运行时格子由代码实例化，这层是常驻底衬，
    让未加载时也不出现一整块空白米卡，且与运行时绿色关卡珠不冲突。"""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pad = 6
    cw = (w - pad * (cols + 1)) / cols
    ch = (h - pad * (rows + 1)) / rows
    for r in range(rows):
        for c in range(cols):
            x, y = pad + c * (cw + pad), pad + r * (ch + pad)
            d.rounded_rectangle((x, y, x + cw, y + ch), radius=10,
                                fill=(228, 231, 247, 255),
                                outline=(186, 196, 228, 255), width=2)
            d.ellipse((x + cw / 2 - 3, y + ch / 2 - 3,
                       x + cw / 2 + 3, y + ch / 2 + 3),
                      fill=(176, 188, 220, 190))
    return im


def _grid_board(size=336, cols=6, rows=6):
    """亮色棋盘底板：深底上形成唯一的高亮焦点，格线克制、交点用珠孔点。」"""
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    step = size / cols
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=22,
                        fill=GRID_FILL, outline=GRID_EDGE, width=3)
    for i in range(1, cols):
        x = i * step
        d.line([(x, 12), (x, size - 12)], fill=GRID_LINE, width=2)
    for j in range(1, rows):
        y = j * step
        d.line([(12, y), (size - 12, y)], fill=GRID_LINE, width=2)
    for i in range(cols):
        for j in range(rows):
            cx, cy = (i + .5) * step, (j + .5) * step
            d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=(186, 204, 240, 190))
    return im


def _rounded_panel(size, radius, tint=CARD_FILL, holes=True, tilt=0):
    """奶油白卡：柔和底部压边 + 细冷灰描边 + 顶部一道内高光。"""
    w, h = size
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 4, w - 1, h - 1), radius=radius, fill=CARD_SHADOW)
    d.rounded_rectangle((0, 0, w - 1, h - 4), radius=radius, fill=tint,
                        outline=CARD_EDGE, width=2)
    d.line([(radius + 4, 3), (w - radius - 4, 3)], fill=(255, 255, 255, 210), width=2)
    if holes:
        _holes(d, (8, 8, w - 8, h - 12))
    return im


def _button(w, h, top, bottom, edge, radius=8):
    """糖果立体按钮：一体成型的厚底 + 上下渐变 + 柔和高光 + 亮描边。
    厚底与主体共用同一个圆角轮廓（不做错位叠层），九宫格拉伸后任意高度都规整。"""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 1) 深色厚底：比主体下移 6px，形成可按的「厚度」
    d.rounded_rectangle((0, 6, w - 1, h - 1), radius=radius,
                        fill=_lerp(edge, (0, 0, 0), .12) + (255,))
    # 2) 主体：纵向渐变
    body = Image.new('RGBA', (w, h - 6), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    for y in range(h - 6):
        t = y / max(1, h - 7)
        bd.line([(0, y), (w, y)], fill=_lerp(top, bottom, t) + (255,))
    # 3) 上半部柔和高光：白色由 32% 平滑衰减到 0，不做硬边高光条
    gloss = Image.new('RGBA', (w, h - 6), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gloss)
    for y in range(int((h - 6) * .52)):
        a = int(78 * (1 - y / max(1, (h - 6) * .52)))
        gd.line([(0, y), (w, y)], fill=(255, 255, 255, a))
    body = Image.alpha_composite(body, gloss)
    mask = Image.new('L', (w, h - 6), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 7), radius=radius, fill=255)
    im.paste(body, (0, 0), mask)
    d = ImageDraw.Draw(im)
    # 4) 亮描边 + 顶部一道细亮线，强化立体边缘
    d.rounded_rectangle((1, 1, w - 2, h - 8), radius=radius,
                        outline=_lerp(top, (255, 255, 255), .48) + (235,), width=2)
    d.line([(radius + 3, 2), (w - radius - 3, 2)],
           fill=(255, 255, 255, 150), width=2)
    return im


def _pill(w, h, fill=CARD_FILL, edge=CARD_EDGE):
    """奶油白胶囊：细描边 + 底部一道压边，先统一底色，立体化留到 R2。"""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 3, w - 1, h - 1), radius=8, fill=CARD_SHADOW)
    d.rounded_rectangle((0, 0, w - 1, h - 3), radius=8, fill=fill,
                        outline=edge, width=2)
    return im


def _slice_panel(size=160, radius=8):
    """九宫格白卡：顶部 8px 品牌色带（金→绿），圆角与 border 一致，拉伸不变形。"""
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 4, size - 1, size - 1), radius=radius, fill=CARD_SHADOW)
    d.rounded_rectangle((0, 0, size - 1, size - 4), radius=radius,
                        fill=CARD_FILL, outline=CARD_EDGE, width=2)
    band = Image.new('RGBA', (size, 8), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for x in range(size):
        bd.line([(x, 0), (x, 7)],
                fill=_lerp((255, 201, 74), (76, 206, 120), x / (size - 1)) + (255,))
    corner = Image.new('L', (size, size), 0)
    ImageDraw.Draw(corner).rounded_rectangle((0, 0, size - 1, size - 4),
                                             radius=radius, fill=255)
    im.paste(band, (0, 0), corner.crop((0, 0, size, 8)))
    d.line([(radius + 4, 10), (size - radius - 4, 10)],
           fill=(255, 255, 255, 190), width=1)
    return im


def _circle_button(size=128):
    """圆形按钮：奶油白底 + 冷灰描边 + 底部一圈压边。"""
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((2, 5, size - 3, size - 2), fill=CARD_SHADOW)
    d.ellipse((2, 2, size - 3, size - 6), fill=CARD_FILL,
              outline=CARD_EDGE, width=3)
    return im


def _icon(name, size=96):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2
    ink = (255, 255, 255, 255)
    if name == 'gear':
        d.ellipse((c - 10, c - 10, c + 10, c + 10), fill=ink)
        for a in range(0, 360, 45):
            x, y = c + math.cos(math.radians(a)) * 24, c + math.sin(math.radians(a)) * 24
            d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=ink)
        d.ellipse((c - 9, c - 9, c + 9, c + 9), fill=(110, 170, 195, 255))
    elif name == 'pause':
        d.rounded_rectangle((c - 15, c - 22, c - 5, c + 22), radius=4, fill=ink)
        d.rounded_rectangle((c + 5, c - 22, c + 15, c + 22), radius=4, fill=ink)
    elif name == 'close':
        d.line([(c - 18, c - 18), (c + 18, c + 18)], fill=ink, width=9)
        d.line([(c + 18, c - 18), (c - 18, c + 18)], fill=ink, width=9)
    elif name == 'heart':
        d.ellipse((size * .18, size * .20, size * .55, size * .62), fill=ink)
        d.ellipse((size * .45, size * .20, size * .82, size * .62), fill=ink)
        d.polygon([(size * .21, size * .50), (size * .79, size * .50), (c, size * .82)], fill=ink)
    elif name == 'coin':
        d.ellipse((size * .16, size * .16, size * .84, size * .84), fill=(255, 199, 64, 255))
        d.ellipse((size * .24, size * .22, size * .70, size * .56), fill=(255, 236, 160, 190))
        d.ellipse((c - 8, c - 8, c + 8, c + 8), fill=(214, 148, 30, 210))
    elif name == 'bulb':
        d.ellipse((size * .28, size * .14, size * .72, size * .62), fill=ink)
        d.rounded_rectangle((size * .38, size * .58, size * .62, size * .80), radius=5, fill=ink)
        d.line([(size * .40, size * .86), (size * .60, size * .86)], fill=ink, width=7)
    elif name == 'hammer':
        d.line([(size * .30, size * .82), (size * .64, size * .34)], fill=ink, width=12)
        d.polygon([(size * .48, size * .18), (size * .62, size * .08),
                   (size * .86, size * .30), (size * .74, size * .42)], fill=ink)
    elif name == 'wand':
        d.line([(size * .24, size * .82), (size * .66, size * .36)], fill=ink, width=10)
        star = []
        for i in range(10):
            a = math.radians(-90 + i * 36)
            r = 20 if i % 2 == 0 else 9
            star.append((size * .72 + math.cos(a) * r, size * .26 + math.sin(a) * r))
        d.polygon(star, fill=ink)
    elif name == 'lock':
        d.arc((size * .32, size * .14, size * .68, size * .56), 180, 360, fill=ink, width=9)
        d.rounded_rectangle((size * .24, size * .44, size * .76, size * .82), radius=9, fill=ink)
        d.ellipse((c - 5, size * .56, c + 5, size * .66), fill=(110, 170, 195, 255))
    else:
        d.ellipse((size * .2, size * .2, size * .8, size * .8), fill=ink)
    return im


def _decor(w=390, h=844):
    """夜空星点 + 边缘极淡彩珠光斑。装饰层在所有内容之下，不抢可读性。"""
    import random
    rnd = random.Random(42)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _ in range(110):
        x, y = rnd.randrange(8, w - 8), rnd.randrange(8, h - 8)
        r = rnd.choice((1, 1, 1, 2, 2, 3))
        a = rnd.choice((26, 38, 52, 70))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))
    for x, y, r, c in [(-14, 118, 52, (86, 170, 240)), (374, 246, 42, (206, 108, 226)),
                       (36, 690, 46, (255, 156, 120)), (352, 742, 58, (108, 220, 190))]:
        d.ellipse((x - r, y - r, x + r, y + r), fill=c + (34,))
    return im


def ImageChopsMultiply(a, b):
    from PIL import ImageChops
    return ImageChops.multiply(a, b)


def _write_sprite(name, im, border=0):
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)
    path = SPRITE_DIR / (name + '.png')
    im.save(path)
    g = guid(path)
    if isinstance(border, (tuple, list)):
        x, y, z, w = border
    else:
        x = y = z = w = border
    bd = {'x': x, 'y': y, 'z': z, 'w': w}
    meta = {'fileFormatVersion': 2, 'guid': g, 'TextureImporter': {
        'internalIDToNameTable': [], 'externalObjects': {}, 'serializedVersion': 12,
        'mipmaps': {'enableMipMap': 0}, 'isReadable': 0, 'textureType': 8,
        'textureShape': 1, 'sRGBTexture': 1, 'alphaIsTransparency': 1, 'spriteMode': 1,
        'spritePixelsToUnits': 100, 'spriteMeshType': 1, 'spriteAlignment': 0,
        'spritePivot': vec(.5, .5), 'spriteBorder': bd,
        'textureSettings': {'serializedVersion': 2, 'filterMode': 1, 'aniso': 1,
                            'mipBias': 0, 'wrapU': 1, 'wrapV': 1, 'wrapW': 1},
        'maxTextureSize': 2048, 'nPOTScale': 0,
        'spriteSheet': {'serializedVersion': 2, 'sprites': [], 'outline': [], 'physicsShape': [],
                        'bones': [], 'spriteID': uuid.uuid5(uuid.NAMESPACE_URL, 'blockout:beads:' + name).hex,
                        'internalID': 0, 'vertices': [], 'indices': '', 'edges': [], 'weights': [],
                        'secondaryTextures': [], 'nameFileIdTable': {}},
        'platformSettings': [], 'userData': '', 'assetBundleName': '', 'assetBundleVariant': ''}}
    Path(str(path) + '.meta').write_text(yaml.safe_dump(meta, sort_keys=False), encoding='utf-8')
    return ext(path, 21300000)


def build_sprites():
    global FONT
    FONT = ext(ROOT / 'Assets/Resources/Fonts/SourceHanSansCN-Regular.otf', 12800000)
    SPRITE_DIR.mkdir(parents=True, exist_ok=True)
    guid(SPRITE_DIR)
    SR = lambda n, im, b=0: SPR.__setitem__(n, _write_sprite(n, im, b))

    bead = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    _draw_bead(ImageDraw.Draw(bead), 64, 62, 56)
    SR('bead', bead)

    SR('sky', _sky_gradient(390, 844))
    # 圆角半径必须 <= 九宫格 border，否则切片会把角拉成斜角（上一版工具卡的菱形即由此而来）
    SR('plate_tilt', _rounded_panel((512, 512), 24))
    SR('plate', _rounded_panel((512, 512), 24))
    SR('plate_soft', _rounded_panel((256, 256), 8, tint=CARD_FILL, holes=False), 8)
    SR('btn_green', _button(160, 80, (146, 244, 132), (52, 190, 92), (20, 116, 60)), 8)
    SR('btn_pink', _button(160, 80, (255, 160, 190), (242, 82, 136), (158, 38, 90)), 8)
    SR('btn_white', _button(160, 80, (255, 255, 255), (236, 238, 230), (170, 182, 214)), 8)
    SR('pill', _pill(160, 64), 8)
    SR('panel', _slice_panel(), 8)
    SR('circle', _circle_button(128))
    holes = Image.new('RGBA', (28, 28), (0, 0, 0, 0))
    ImageDraw.Draw(holes).ellipse((13, 13, 16, 16), fill=(196, 212, 240, 80))
    SR('holes', holes)
    for n in ['gear', 'pause', 'close', 'heart', 'coin', 'bulb', 'hammer', 'wand', 'lock']:
        SR('icon_' + n, _icon(n))
    # 画布设计稿的主体珠阵图：首页糖果树 / 游戏页六组异形珠块 / 结算页完整作品。
    # 第二版直接用原图，不再用灰色占位珠重画，保证预制与画布稿一致。
    crops = {'art_home': (38, 12, 310, 284), 'art_settle': (12, 8, 344, 232)}
    for key, src in [('art_home', 'beads_home_plate.png'),
                     ('art_board', 'beads_board.png'),
                     ('art_settle', 'beads_settle_plate.png')]:
        f = ROOT / 'generated-images' / src
        if not f.exists():
            raise FileNotFoundError('缺少设计稿珠阵原图: ' + str(f))
        im = Image.open(f).convert('RGBA')
        if key in crops:
            im = im.crop(crops[key]).resize((350, 300 if key == 'art_home' else 240),
                                            Image.LANCZOS)
        SR(key, im)
    SR('grid', _grid_board())
    SR('slots', _slots_grid())
    SR('brand', _brand_art())
    SR('decor', _decor())


# ---------------------------------------------------------------- uGUI 节点
class Node:
    def __init__(self, page, name, parent=None, box=(0, 0, 390, 844), active=True):
        self.p = page
        self.go = page.alloc()
        self.rt = page.alloc()
        self.children = []
        self.components = [self.rt]
        self.name = name
        self.parent = parent
        self.active = active
        if parent:
            parent.children.append(self)
        self.anchor_min = vec(0, 1)
        self.anchor_max = vec(0, 1)
        self.pivot = vec(0, 1)
        self.position = vec(box[0], -box[1])
        self.size = vec(box[2], box[3])
        self.scale = {'x': 1, 'y': 1, 'z': 1}
        page.nodes.append(self)
        self.image = None

    def component(self, name, fields):
        cid = self.p.alloc()
        self.components.append(cid)
        data = {'m_ObjectHideFlags': 0, 'm_CorrespondingSourceObject': ref(),
                'm_PrefabInstance': ref(), 'm_PrefabAsset': ref(),
                'm_GameObject': ref(self.go), 'm_Enabled': 1, 'm_EditorHideFlags': 0,
                'm_Script': script(name), 'm_Name': '', 'm_EditorClassIdentifier': ''}
        data.update(fields)
        self.p.docs.append((114, cid, 'MonoBehaviour', data))
        return cid

    def renderer(self):
        cid = self.p.alloc()
        self.components.append(cid)
        self.p.docs.append((222, cid, 'CanvasRenderer', {
            'm_ObjectHideFlags': 0, 'm_CorrespondingSourceObject': ref(),
            'm_PrefabInstance': ref(), 'm_PrefabAsset': ref(),
            'm_GameObject': ref(self.go), 'm_CullTransparentMesh': 1}))

    def img(self, color=WHITE, sp=None, hit=False, sliced=False, filled=False, preserve=False):
        self.renderer()
        cid = self.component('Image', {
            'm_Material': ref(), 'm_Color': rgba(color), 'm_RaycastTarget': int(hit),
            'm_Maskable': 1, 'm_OnCullStateChanged': {'m_PersistentCalls': {'m_Calls': []}},
            'm_Sprite': sp or ref(), 'm_Type': 3 if filled else (1 if sliced else 0),
            'm_PreserveAspect': int(preserve), 'm_FillCenter': 1, 'm_FillMethod': 0,
            'm_FillAmount': 1, 'm_FillClockwise': 1, 'm_FillOrigin': 0,
            'm_UseSpriteMesh': 0, 'm_PixelsPerUnitMultiplier': 1})
        self.image = cid
        return cid

    def text(self, value, size=16, color=INK, align=4):
        self.renderer()
        return self.component('Text', {
            'm_Material': ref(), 'm_Color': rgba(color), 'm_RaycastTarget': 0,
            'm_Maskable': 1, 'm_FontData': {
                'm_Font': FONT, 'm_FontSize': size, 'm_FontStyle': 0, 'm_BestFit': 1,
                'm_MinSize': max(8, size - 4), 'm_MaxSize': size, 'm_Alignment': align,
                'm_AlignByGeometry': 0, 'm_RichText': 1, 'm_HorizontalOverflow': 0,
                'm_VerticalOverflow': 0, 'm_LineSpacing': 1}, 'm_Text': value})

    def button(self):
        if self.image is None:
            self.img(WHITE, hit=True)
        else:
            for doc in self.p.docs:
                if doc[1] == self.image:
                    doc[3]['m_RaycastTarget'] = 1
        return self.component('Button', {
            'm_Navigation': {'m_Mode': 0, 'm_WrapAround': 0, 'm_SelectOnUp': ref(),
                             'm_SelectOnDown': ref(), 'm_SelectOnLeft': ref(),
                             'm_SelectOnRight': ref()},
            'm_Transition': 1, 'm_Colors': {
                'm_NormalColor': rgba(WHITE), 'm_HighlightedColor': rgba(WHITE),
                'm_PressedColor': rgba((.86, .86, .86, 1)), 'm_SelectedColor': rgba(WHITE),
                'm_DisabledColor': rgba((.65, .65, .65, .5)), 'm_ColorMultiplier': 1,
                'm_FadeDuration': .1},
            'm_Interactable': 1, 'm_TargetGraphic': ref(self.image),
            'm_OnClick': {'m_PersistentCalls': {'m_Calls': []}}})

    def mask(self):
        return self.component('RectMask2D', {
            'm_Padding': {'x': 0, 'y': 0, 'z': 0, 'w': 0}, 'm_Softness': vec()})


class Page:
    def __init__(self, name, view):
        self.name = name
        self.view = view
        self.next = 100000
        self.nodes = []
        self.docs = []
        self.fields = {}
        self.root = Node(self, name)
        self.root.anchor_min = vec()
        self.root.anchor_max = vec(1, 1)
        self.root.pivot = vec(.5, .5)
        self.root.position = vec()
        self.root.size = vec()
        self.surface = Node(self, 'DesignSurface', self.root)
        self.surface.anchor_min = self.surface.anchor_max = vec(.5, .5)
        self.surface.pivot = vec(.5, .5)
        self.surface.position = vec()
        self.surface.img(WHITE, SPR['sky'])
        self._decor()
        self.root.component('BlockOutPageLayout', {
            'Surface': ref(self.surface.rt), 'DesignSize': vec(390, 844), 'RespectSafeArea': 1})

    def _decor(self):
        n = Node(self, 'BeadsDecor', self.surface, (0, 0, 390, 844))
        n.img(WHITE, SPR['decor'])
        return n

    def alloc(self):
        self.next += 1
        return self.next

    def node(self, name, box, parent=None, active=True):
        return Node(self, name, parent or self.surface, box, active)

    def label(self, key, text, box, parent=None, size=16, color=INK, align=4):
        n = self.node(key, box, parent)
        cid = n.text(text, size, color, align)
        self.fields[key] = ref(cid)
        return n, cid

    def btn(self, key, text, box, parent, sp, color=WHITE, txt=INK, size=17,
            text_box=None, sliced=True):
        n = self.node(key, box, parent)
        # 圆形按钮不应做九宫格拉伸，否则圆角会被拉成方角
        if sp == SPR['circle'] or sp == SPR['plate'] or sp == SPR['plate_tilt']:
            sliced = False
        n.img(color, sp, sliced=sliced)
        cid = n.button()
        self.fields[key] = ref(cid)
        tb = text_box or (10, 4, box[2] - 20, box[3] - 10)
        t = Node(self, 'Text', n, tb)
        tid = t.text(text, size, txt, 4)
        return n, cid, tid

    def image(self, key, box, parent, color=WHITE, sp=None, sliced=False, filled=False):
        n = self.node(key, box, parent)
        cid = n.img(color, sp, sliced=sliced, filled=filled)
        self.fields[key] = ref(cid)
        return n, cid

    def art(self, rootkey, arraykey, box, parent, active=0, flat=False):
        """flat=True：12 个揭晓格静态透明，让位给设计稿的彩色珠阵作品贴图层。
        运行时由 Controller 重新赋 sprite / color，透明静态值不影响功能。"""
        vp = self.node(rootkey, box, parent)
        vp.img((0, 0, 0, 0))
        vp.mask()
        self.fields[rootkey] = ref(vp.rt)
        art = Node(self, 'Artwork', vp, (0, 0, box[2], box[3]))
        imgs = []
        for i in range(12):
            r = Node(self, 'Region_' + str(i), art,
                     (i % 4 * box[2] / 4, i // 4 * box[3] / 3,
                      box[2] / 4 - 4, box[3] / 3 - 4))
            color = ((0, 0, 0, 0) if flat else
                     (BEAD_COLORS[i % 12] if i < active else BEAD_OFF))
            imgs.append(ref(r.img(color, SPR['bead'])))
        self.fields[arraykey] = imgs
        return vp, art

    def save(self):
        source = next(RUNTIME.rglob(self.view + '.cs')).read_text(encoding='utf-8-sig')
        required = []
        for decl in re.findall(r'public\s+[\w.\[\]]+\s+([^;{}]+);', source):
            required.extend(part.split('=')[0].strip() for part in decl.split(','))
        missing = set(required) - set(self.fields)
        if missing:
            raise ValueError(self.name + ': 缺少 View 字段绑定 ' + str(missing))
        self.root.component(self.view, {k: self.fields[k] for k in required})
        docs = []
        for n in self.nodes:
            docs.append((1, n.go, 'GameObject', {
                'm_ObjectHideFlags': 0, 'm_CorrespondingSourceObject': ref(),
                'm_PrefabInstance': ref(), 'm_PrefabAsset': ref(), 'serializedVersion': 6,
                'm_Component': [{'component': ref(c)} for c in n.components],
                'm_Layer': 5, 'm_Name': n.name, 'm_TagString': 'Untagged',
                'm_IsActive': int(n.active)}))
            docs.append((224, n.rt, 'RectTransform', {
                'm_ObjectHideFlags': 0, 'm_CorrespondingSourceObject': ref(),
                'm_PrefabInstance': ref(), 'm_PrefabAsset': ref(),
                'm_GameObject': ref(n.go),
                'm_LocalRotation': {'x': 0, 'y': 0, 'z': 0, 'w': 1},
                'm_LocalPosition': {'x': 0, 'y': 0, 'z': 0}, 'm_LocalScale': n.scale,
                'm_Children': [ref(c.rt) for c in n.children],
                'm_Father': ref(n.parent.rt if n.parent else 0),
                'm_LocalEulerAnglesHint': {'x': 0, 'y': 0, 'z': 0},
                'm_AnchorMin': n.anchor_min, 'm_AnchorMax': n.anchor_max,
                'm_AnchoredPosition': n.position, 'm_SizeDelta': n.size,
                'm_Pivot': n.pivot}))
        path = DEST / (self.name + '.prefab')
        text = '%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'
        for kind, cid, label, data in docs + self.docs:
            text += '--- !u!' + str(kind) + ' &' + str(cid) + '\n' + \
                    yaml.dump({label: data}, Dumper=NoAliasDumper,
                              allow_unicode=True, sort_keys=False, width=120)
        path.write_text(text, encoding='utf-8')
        guid(path)
        return path


def icon(page, name, box, parent, color=None, hit=False):
    n = page.node('Icon_' + name, box, parent)
    n.img(color or ICON_TINT.get(name, INK_SOFT), SPR['icon_' + name], hit=hit, preserve=True)
    return n


def disable(page, cid):
    """静态隐藏某个 Image（运行时由控制器自行 enabled=true）。"""
    for doc in page.docs:
        if doc[1] == cid:
            doc[3]['m_Enabled'] = 0
            return


def set_type(page, cid, image_type):
    """0=Simple 1=Sliced 2=Tiled 3=Filled"""
    for doc in page.docs:
        if doc[1] == cid:
            doc[3]['m_Type'] = image_type
            return


def bead_row(page, name, box, parent, active=6, size=20):
    """12 颗进度珠：前 active 颗彩色，其余灰珠。纯视觉装饰，不占 View 字段。"""
    row = page.node(name, box, parent)
    gap = (box[2] - 12 * size) / 11
    for i in range(12):
        b = Node(page, 'Bead_' + str(i), row, (i * (size + gap), 0, size, size))
        b.img(BEAD_COLORS[i % 12] if i < active else BEAD_OFF, SPR['bead'])
    return row


# ---------------------------------------------------------------- 三屏
def make_home():
    p = Page('BlockOutHomePage', 'BlockOutHomeView')

    # 顶栏：设置 / 金币；主标题全中文，不再用英文描述
    setn, _, _ = p.btn('HomeSettingsBtn', '', (20, 24, 48, 48), p.surface,
                       SPR['circle'], txt=INK, size=10,
                       text_box=(0, 0, 48, 48))
    icon(p, 'gear', (12, 12, 24, 24), setn)
    coin = p.node('CoinPill', (266, 26, 100, 44), p.surface)
    coin.img(WHITE, SPR['pill'], sliced=True)
    icon(p, 'coin', (9, 9, 27, 27), coin)
    p.label('HomeCoinText', '300', (40, 6, 54, 32), coin, size=17, color=INK, align=3)

    p.label('Logo', '箭头方块消除', (20, 88, 350, 44), size=27, color=ON_BG, align=4)
    p.node('LogoSub', (20, 132, 350, 22)).text('第 07 关 · 生命模式', 13, ON_BG_SOFT, 4)

    # 主视觉卡：作品珠阵放大到接近满卡
    card = p.node('PreviewCard', (20, 166, 350, 322))
    card.img(WHITE, SPR['plate_tilt'])
    p.fields['HomePreviewCard'] = ref(card.rt)
    dec = p.node('HomeArtDecor', (10, 12, 330, 282), card)
    dec.img(WHITE, SPR['art_home'])
    vp, art = p.art('HomeArtViewport', 'HomeRegionArts', (16, 16, 318, 272), card,
                    flat=True)
    locks = []
    for i in range(12):
        lk = Node(p, 'Lock_' + str(i), art,
                  (i % 4 * 318 / 4 + 26, i // 4 * 272 / 3 + 26, 22, 22))
        lk.img(INK_SOFT, SPR['icon_lock'], preserve=True)
        lk.active = False
        locks.append(ref(lk.go))
    p.fields['HomeRegionLocks'] = locks
    fail = p.node('FailBox', (16, 16, 318, 272), card, active=False)
    fail.img((1, 1, 1, .86), SPR['plate_soft'])
    p.fields['HomeFailBox'] = ref(fail.go)
    p.btn('HomeRetryBtn', '重试', (99, 112, 120, 44), fail, SPR['btn_white'],
          txt=INK, size=15)
    p.label('HomeRetryExhausted', '稍后再试', (79, 168, 160, 24), fail, 12, INK_SOFT)
    tag, _ = p.label('HomePlaceholderTag', '已收集作品', (16, 292, 130, 20), card,
                     11, INK_SOFT)
    p.fields['HomePlaceholderTag'] = ref(tag.go)
    badge = p.node('PieceBadgePill', (252, 8, 86, 30), card)
    badge.img(WHITE, SPR['pill'], sliced=True)
    p.label('HomePieceBadge', '6/12', (4, 2, 78, 26), badge, 13, INK, 4)

    # 章节进度整合进一张白卡，信息不再散落在背景上
    chapter = p.node('ChapterCard', (20, 502, 350, 138))
    chapter.img(WHITE, SPR['plate_soft'], sliced=True)
    p.label('HomeChapterTitle', '第一章 · 拼图进度', (16, 10, 220, 28), chapter,
            size=17, color=INK, align=3)
    p.btn('HomeCollectionLink', '查看图鉴', (246, 10, 92, 30), chapter,
          SPR['pill'], txt=INK, size=12, text_box=(2, 2, 88, 26))
    p.label('HomePieceText', '拼片 6/12', (16, 42, 220, 22), chapter,
            size=12, color=INK_SOFT, align=3)
    track = p.node('ProgressTrack', (16, 66, 318, 18), chapter)
    track.img((.86, .88, .94, 1), SPR['pill'], sliced=True)
    p.image('HomeProgressFill', (16, 66, 159, 18), chapter,
            GREEN, SPR['pill'], filled=True)
    nodes = []
    for i in range(12):
        n, cid = p.image('Node_' + str(i), (16 + i * 26.5, 90, 20, 20), chapter,
                         BEAD_COLORS[i % 12] if i < 6 else BEAD_OFF, SPR['bead'])
        nodes.append(ref(cid))
    p.fields['HomeNodes'] = nodes

    # 唯一的主行动按钮；玩法说明降级为次要文字入口
    cta, _, tid = p.btn('HomeCtaButton', '开始游戏', (20, 656, 350, 66), p.surface,
                        SPR['btn_green'], color=WHITE, txt=WHITE, size=24,
                        text_box=(20, 8, 310, 30))
    p.fields['HomeCtaTitle'] = ref(tid)
    p.label('HomeCtaSub', '第 07 关 · 继续挑战', (20, 40, 310, 18), cta, 12, WHITE)
    p.btn('HomeCtaSecondary', '玩法说明', (115, 730, 160, 28), p.surface,
          SPR['pill'], color=(1, 1, 1, .001), txt=ON_BG_SOFT, size=13,
          text_box=(0, 0, 160, 28))

    # 底部导航：深色磨砂底 + 绿色选中态，去掉重复的三个圆形入口
    nav = p.node('BottomNav', (20, 772, 350, 56))
    nav.img((.18, .16, .34, .82), SPR['pill'], sliced=True)
    for i, (key, title) in enumerate([('NavHomeBtn', '首页'),
                                      ('NavCollectionBtn', '图鉴'),
                                      ('NavStoreBtn', '商店')]):
        box = (6 + i * 113, 4, 106, 48)
        if i == 0:
            p.btn(key, title, box, nav, SPR['btn_green'], txt=WHITE, size=15,
                  text_box=(2, 2, 102, 44))
        else:
            p.btn(key, title, box, nav, SPR['pill'], color=(1, 1, 1, .001),
                  txt=ON_BG_SOFT, size=15, text_box=(2, 2, 102, 44))
    return p.save()

def make_board():
    p = Page('BlockOutGameHud', 'BlockOutBoardPageView')

    # 顶栏：暂停 / 关卡胶囊 / 三心 / 计时，一条水平信息带
    pause, _, _ = p.btn('BoardPauseBtn', '', (20, 20, 44, 44), p.surface,
                        SPR['circle'], txt=INK, size=9,
                        text_box=(0, 0, 44, 44))
    icon(p, 'pause', (12, 10, 20, 24), pause)
    level = p.node('LevelPill', (72, 20, 150, 44), p.surface)
    level.img(WHITE, SPR['pill'], sliced=True)
    p.label('BoardLevelTitle', '第 07 关', (10, 3, 130, 24), level,
            size=17, color=INK, align=3)
    p.label('BoardLevelSub', '第一章 · 生命模式', (10, 26, 130, 16), level,
            size=10, color=INK_SOFT, align=3)

    hearts = []
    hr = p.node('Hearts', (228, 24, 66, 24))
    for i in range(3):
        n, cid = p.image('Heart' + str(i), (i * 22, 0, 22, 22), hr,
                         PINK, SPR['icon_heart'])
        hearts.append(ref(cid))
    p.fields['BoardHearts'] = hearts

    timer = p.node('Timer', (300, 20, 70, 44))
    timer.img(WHITE, SPR['pill'], sliced=True)
    p.fields['BoardTimerPill'] = ref(timer.rt)
    p.label('BoardTimerText', '02:00', (4, 4, 62, 36), timer, 14, INK)

    # 第二带：剩余块数 + 连击，唯一一处行动目标
    pill = p.node('RemainingPill', (20, 76, 350, 44))
    pill.img(WHITE, SPR['pill'], sliced=True)
    dot = p.node('RemainingDot', (12, 12, 20, 20), pill)
    dot.img(GREEN, SPR['bead'], preserve=True)
    p.label('BoardRemainingText', '剩余 06 块', (42, 6, 170, 32), pill,
            size=17, color=INK, align=3)
    combo = p.node('ComboTag', (248, 8, 90, 28), pill)
    combo.img(GOLD, SPR['pill'], sliced=True)
    p.label('ComboText', '连击 ×3', (2, 2, 86, 24), combo, 12, INK, 4)

    # 第三带：常驻拼装进度，收进一张胶囊，不再散落四行小字
    assembly = p.node('AssemblyCard', (20, 128, 350, 44), p.surface)
    assembly.img((1, 1, 1, .92), SPR['pill'], sliced=True)
    p.node('AssemblyLabel', (14, 3, 160, 16), assembly).text('本章拼片 6/12',
                                                             10, INK_SOFT, 3)
    bead_row(p, 'AssemblyBar', (14, 20, 322, 18), assembly, active=6, size=18)

    # 棋盘：深底上唯一的高亮区域，占据视觉中心
    area = p.node('BoardArea', (16, 180, 358, 358))
    area.img(WHITE, SPR['grid'])
    p.fields['BoardArea'] = ref(area.rt)
    demo = p.node('BoardDemoArt', (28, 192, 334, 334), p.surface, active=False)
    demo.img(WHITE, SPR['art_board'])

    hint = p.node('HintPill', (20, 548, 350, 34))
    hint.img((1, 1, 1, .88), SPR['pill'], sliced=True)
    p.label('BoardHintPill', '轻点整块方块，沿箭头方向飞出', (8, 2, 334, 30), hint,
            size=13, color=INK, align=4)

    # 工具槽：更大的图标、更清楚的名称与解锁条件
    tools = [('HintSlot', '提示', 'bulb', '×3 可用'),
             ('HammerSlot', '锤子', 'hammer', '第 11 关解锁'),
             ('MagicSlot', '魔法棒', 'wand', '第 16 关解锁')]
    for i, (key, title, ic, cond) in enumerate(tools):
        root = p.node(key, (20 + i * 117, 610, 110, 112))
        root.img((.95, 1, .96, 1) if i == 0 else (.96, .97, 1, 1),
                 SPR['plate_soft'], sliced=True)
        slot = {'Rect': ref(root.rt), 'Button': ref(root.button())}
        _, cid = p.image('Icon', (35, 10, 40, 40), root,
                         ICON_TINT[ic] if i == 0 else (.46, .54, .66, 1),
                         SPR['icon_' + ic])
        slot['Icon'] = ref(cid)
        badge = p.node('CountBadge', (72, 10, 30, 22), root, active=(i == 0))
        badge.img(GOLD, SPR['pill'], sliced=True)
        slot['CountBadge'] = ref(badge.go)
        _, cid = p.label('Count', '×3' if i == 0 else '0', (0, 0, 30, 22), badge,
                         11, INK)
        slot['CountText'] = ref(cid)
        lock, _ = p.image('LockBadge', (78, 12, 26, 22), root, INK_SOFT,
                          SPR['icon_lock'])
        lock.active = (i > 0)
        slot['LockBadge'] = ref(lock.go)
        _, cid = p.label('NameText', title, (4, 54, 102, 26), root, 14,
                         INK if i == 0 else INK_SOFT)
        slot['NameText'] = ref(cid)
        _, cid = p.label('CondText', cond, (4, 82, 102, 20), root, 11, INK_SOFT)
        slot['CondText'] = ref(cid)
        p.fields[key] = slot

    p.node('Footer', (20, 738, 350, 22)).text('第一章 · 生命模式', 11, ON_BG_SOFT, 4)
    return p.save()

def make_settlement():
    p = Page('BlockOutSettlementPage', 'BlockOutSettlementView')
    p.node('ChapterTag', (20, 22, 220, 22)).text('第 07 关 · 已通关', 12, ON_BG_SOFT, 3)
    close = p.node('SettleCloseDecor', (318, 20, 52, 52))
    close.img(WHITE, SPR['circle'])
    icon(p, 'close', (14, 14, 24, 24), close)

    # 庆祝焦点：金色奖章 + 大标题，先给情绪再给信息
    medal = p.node('WinMedal', (151, 48, 88, 88))
    medal.img(GOLD, SPR['circle'])
    inner = p.node('MedalInner', (6, 6, 76, 76), medal)
    inner.img((.20, .17, .40, 1), SPR['circle'])
    icon(p, 'coin', (14, 14, 48, 48), inner)
    p.label('SettleTitleText', '关卡完成', (20, 138, 350, 46),
            size=32, color=ON_BG, align=4)
    p.node('SettleSub', (20, 184, 350, 22)).text('清空全部方块 · 新作品已解锁',
                                                 12, ON_BG_SOFT, 4)

    # 作品卡：揭晓的完整珠阵占满主视觉
    card = p.node('Card', (20, 214, 350, 320))
    card.img(WHITE, SPR['panel'], sliced=True)
    holes = p.node('HolesLayer', (10, 10, 330, 300), card)
    set_type(p, holes.img(WHITE, SPR['holes']), 2)

    tag = p.node('NewUnlockTag', (14, 12, 82, 30), card)
    tag.img((.96, .30, .44, 1), SPR['pill'], sliced=True)
    Node(p, 'Text', tag, (0, 0, 82, 30)).text('新解锁', 13, WHITE, 4)

    dec = p.node('SettleArtDecor', (12, 48, 326, 198), card)
    dec.img(WHITE, SPR['art_settle'], preserve=True)
    p.art('SettleRevealRoot', 'SettleRevealRegions', (12, 48, 326, 198), card,
          flat=True)
    _, cid = p.image('SettleLevelImage', (12, 48, 326, 198), card,
                     WHITE, SPR['plate_soft'])
    disable(p, cid)

    p.label('SettleNoteText', '作品已收藏', (14, 256, 180, 26), card, 14, INK, 3)
    got = p.node('InCollectionTag', (238, 254, 96, 30), card)
    got.img(GREEN, SPR['pill'], sliced=True)
    Node(p, 'Text', got, (0, 0, 96, 30)).text('已入图鉴', 12, INK, 4)
    p.label('SettlePieceText', '获得新拼片', (14, 288, 220, 22), card,
            12, INK_SOFT, 3)

    # 拼装进度：与游戏页同一套胶囊语言
    assembly = p.node('AssemblyCard', (20, 544, 350, 44), p.surface)
    assembly.img((1, 1, 1, .92), SPR['pill'], sliced=True)
    p.node('AssemblyLabel', (14, 3, 170, 16), assembly).text('本章拼片 07/12',
                                                             10, INK_SOFT, 3)
    p.node('AssemblyRemain', (210, 3, 126, 16), assembly).text('还差 5 片',
                                                                10, INK_SOFT, 5)
    bead_row(p, 'AssemblyBar', (14, 20, 322, 18), assembly, active=7, size=18)

    # 奖励卡：金币数字放大，翻倍作为次级强调
    reward = p.node('RewardPill', (20, 598, 350, 72))
    reward.img((1, .97, .88, 1), SPR['plate_soft'], sliced=True)
    icon(p, 'coin', (14, 20, 34, 34), reward)
    p.node('RewardAmount', (54, 10, 96, 50), reward).text('+30', 30,
                                                          (.90, .55, .08, 1), 3)
    p.label('SettleRewardText', '通关奖励 · 可翻倍', (152, 12, 118, 30), reward,
            12, INK, 3)
    dbl = p.node('SettleDoubleDecor', (268, 16, 70, 40), reward)
    dbl.img(WHITE, SPR['btn_pink'], sliced=True)
    Node(p, 'Text', dbl, (0, 0, 70, 40)).text('翻倍', 14, WHITE, 4)

    p.node('SettleStats', (20, 678, 350, 20)).text('用时 01:42 · 最高连击 ×3 · 错误 0 次',
                                                   11, ON_BG_SOFT, 4)
    p.btn('SettleNextBtn', '下一关 · 第 08 关', (20, 706, 350, 64), p.surface,
          SPR['btn_green'], txt=WHITE, size=21)
    for i, (key, title) in enumerate([('SettleReplayBtn', '重玩'),
                                      ('SettleHomeBtn', '返回首页'),
                                      ('SettleCollectionBtn', '查看收藏')]):
        p.btn(key, title, (20 + i * 117, 780, 110, 32), p.surface,
              SPR['pill'], color=(1, 1, 1, .001), txt=ON_BG_SOFT, size=12,
              text_box=(0, 0, 110, 32))
    return p.save()

# ---------------------------------------------------------------- 入口
def backup():
    """只保留一份原始 prefab 备份；重复执行不会覆盖它。"""
    out = Path(__file__).parent / 'backup' / 'original'
    if (out / 'BlockOutHomePage.prefab').exists():
        return out
    out.mkdir(parents=True, exist_ok=True)
    for name in ['BlockOutHomePage', 'BlockOutGameHud', 'BlockOutSettlementPage']:
        for suffix in ['.prefab', '.prefab.meta']:
            src = DEST / (name + suffix)
            if src.exists():
                shutil.copy2(src, out / (name + suffix))
    return out


if __name__ == '__main__':
    saved = backup()
    build_sprites()
    made = [make_home(), make_board(), make_settlement()]
    print('备份目录:', saved)
    print('UI 贴图:', len(SPR), '张 ->', SPRITE_DIR)
    for p in made:
        print('生成预制:', p)
