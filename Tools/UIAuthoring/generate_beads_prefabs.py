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

# ---- 设计 token（取自画布「珠子」方向，均为项目内可复用的 UI 控件色） ----
SKY = [(0.0, (126, 216, 240)), (0.36, (168, 232, 242)),
       (0.68, (216, 245, 228)), (1.0, (255, 243, 214))]
INK = (0.106, 0.294, 0.420, 1)        # #1B4B6B
INK_SOFT = (0.42, 0.59, 0.67, 1)
WHITE = (1, 1, 1, 1)
GREEN = (0.35, 0.78, 0.38, 1)
GREEN_DARK = (0.16, 0.55, 0.28, 1)
PINK = (0.96, 0.34, 0.55, 1)
GOLD = (1.0, 0.76, 0.24, 1)
BEAD_COLORS = [
    (1.0, 0.55, 0.30, 1), (1.0, 0.76, 0.24, 1), (0.98, 0.42, 0.62, 1),
    (0.42, 0.80, 0.40, 1), (0.26, 0.80, 0.86, 1), (0.38, 0.55, 0.95, 1),
    (0.68, 0.48, 0.88, 1), (0.30, 0.68, 0.85, 1), (0.96, 0.68, 0.30, 1),
    (0.55, 0.85, 0.55, 1), (0.45, 0.72, 0.98, 1), (0.98, 0.52, 0.45, 1),
]
BEAD_OFF = (0.83, 0.89, 0.91, 1)
# 白色图标贴图落在白色圆底上必须染色才可见；金币本身是彩色，保持原色
ICON_TINT = {'gear': INK_SOFT, 'pause': INK_SOFT, 'close': INK_SOFT,
             'lock': INK_SOFT, 'heart': PINK, 'coin': WHITE,
             'bulb': (1.0, 0.64, 0.22, 1), 'hammer': (0.36, 0.58, 0.90, 1),
             'wand': (0.68, 0.48, 0.88, 1)}


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
    im = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / max(1, h - 1)
        for i in range(len(SKY) - 1):
            if SKY[i][0] <= t <= SKY[i + 1][0]:
                k = (t - SKY[i][0]) / (SKY[i + 1][0] - SKY[i][0])
                d.line([(0, y), (w, y)], fill=_lerp(SKY[i][1], SKY[i + 1][1], k))
                break
    return im.convert('RGBA')


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


def _holes(d, box, step=26, color=(196, 222, 233, 150)):
    x0, y0, x1, y1 = box
    x, y = x0 + step, y0 + step
    while x < x1 - 6:
        while y < y1 - 6:
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=color)
            y += step
        x += step
        y = y0 + step


def _grid_board(size=336, cols=6, rows=6):
    """6×6 浅蓝格线 + 每格淡珠孔：运行时真实棋子的底纹。"""
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    step = size / cols
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=28,
                        fill=(232, 246, 250, 255))
    for i in range(1, cols):
        x = i * step
        d.line([(x, 8), (x, size - 8)], fill=(203, 230, 240, 110), width=2)
    for j in range(1, rows):
        y = j * step
        d.line([(8, y), (size - 8, y)], fill=(203, 230, 240, 110), width=2)
    for i in range(cols):
        for j in range(rows):
            cx, cy = (i + .5) * step, (j + .5) * step
            d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=(196, 224, 235, 190))
    return im


def _rounded_panel(size, radius, tint=(255, 255, 255, 238), holes=True, tilt=0):
    """半透明白色拼豆板：圆角 + 孔点网格 + 柔和投影；tilt 为倾斜角度。"""
    w, h = size
    canvas = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    pad = int(min(w, h) * .07)
    base = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(base)
    rect = (pad, pad, w - pad, h - pad)
    shadow = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((rect[0] + 5, rect[1] + 10, rect[2] + 5, rect[3] + 10),
                         radius=radius, fill=(60, 110, 135, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    canvas.alpha_composite(shadow)
    bd.rounded_rectangle(rect, radius=radius, fill=tint,
                         outline=(255, 255, 255, 255), width=3)
    if holes:
        _holes(bd, (rect[0] + 8, rect[1] + 8, rect[2] - 8, rect[3] - 8))
    if tilt:
        base = base.rotate(tilt, resample=Image.BICUBIC, expand=False)
        canvas.alpha_composite(base)
    else:
        canvas.alpha_composite(base)
    return canvas


def _button(w, h, top, bottom, edge, radius=26):
    """立体圆角按钮，9-slice 用；上亮下暗 + 底部厚边 + 顶部高光。"""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 5, w - 4, h - 3), radius=radius, fill=edge)
    body = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    for y in range(2, h - 7):
        t = y / max(1, h - 9)
        bd.line([(3, y), (w - 4, y)], fill=_lerp(top, bottom, t) + (255,))
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((3, 2, w - 4, h - 8), radius=radius, fill=255)
    im.paste(body, (0, 0), mask)
    d.rounded_rectangle((3, 2, w - 4, h - 8), radius=radius, outline=(255, 255, 255, 70), width=2)
    # 顶部只留一条薄高光；太厚会在 9-slice 拉伸后压住按钮文字
    d.rounded_rectangle((18, 5, w - 18, int(h * .16)), radius=int(radius * .35),
                        fill=(255, 255, 255, 48))
    return im


def _pill(w, h, fill=(255, 255, 255, 246), edge=(214, 232, 238, 255)):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = h // 2
    d.rounded_rectangle((2, 5, w - 3, h - 2), radius=r, fill=(80, 130, 150, 55))
    d.rounded_rectangle((2, 2, w - 3, h - 6), radius=r, fill=fill, outline=edge, width=2)
    d.rounded_rectangle((14, 6, w - 14, int(h * .34)), radius=r // 3, fill=(255, 255, 255, 120))
    return im


def _slice_panel(size=160, radius=28):
    """专为九宫格准备的纯白圆角面板：圆角区正好落在 border(30) 内，拉伸不会切角。"""
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, size - 3, size - 3), radius=radius,
                        fill=(255, 255, 255, 244), outline=(222, 238, 244, 255), width=2)
    return im


def _circle_button(size=128):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((6, 12, size - 6, size - 2), fill=(70, 120, 150, 60))
    d.ellipse((6, 5, size - 6, size - 11), fill=(255, 255, 255, 250),
              outline=(226, 240, 244, 255), width=3)
    d.ellipse((24, 16, size - 24, int(size * .44)), fill=(255, 255, 255, 170))
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
    """全屏散落珠子装饰，确定性排布。"""
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    pts = [(32, 210, 11), (372, 232, 9), (22, 396, 8), (366, 420, 12),
           (10, 530, 8), (352, 548, 8), (18, 658, 7), (374, 676, 9),
           (60, 118, 6), (330, 132, 7), (28, 762, 8), (362, 764, 7),
           (110, 46, 6), (286, 62, 6), (16, 300, 6), (378, 316, 6)]
    rgb = [(255, 138, 74), (255, 196, 61), (250, 110, 158), (108, 204, 102),
           (66, 204, 219), (97, 140, 242), (174, 122, 224)]
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for i, (x, y, r) in enumerate(pts):
        bead = Image.new('RGBA', (r * 2 + 8, r * 2 + 8), (0, 0, 0, 0))
        _draw_bead(ImageDraw.Draw(bead), r + 4, r + 4, r)
        tint = Image.new('RGBA', bead.size, rgb[i % len(rgb)] + (255,))
        bead = ImageChopsMultiply(bead, tint)
        layer.alpha_composite(bead, (int(x - r - 4), int(y - r - 4)))
    # 淡孔点
    d = ImageDraw.Draw(layer)
    for x in range(14, w, 42):
        for y in range(24, h, 42):
            d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(255, 255, 255, 70))
    return layer


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
    SR('plate_tilt', _rounded_panel((512, 512), 62, tilt=-8))
    SR('plate', _rounded_panel((512, 512), 54, holes=True))
    SR('plate_soft', _rounded_panel((256, 256), 36, tint=(246, 253, 255, 232), holes=False), 36)
    SR('btn_green', _button(160, 84, (139, 232, 107), (72, 184, 74), (32, 118, 54)), 26)
    SR('btn_pink', _button(160, 84, (255, 150, 183), (244, 86, 138), (196, 56, 106)), 26)
    SR('btn_white', _button(160, 84, (255, 255, 255), (238, 248, 250), (198, 222, 230)), 26)
    SR('pill', _pill(160, 64), 32)
    SR('panel', _slice_panel(), 30)
    SR('circle', _circle_button(128))
    holes = Image.new('RGBA', (28, 28), (0, 0, 0, 0))
    ImageDraw.Draw(holes).ellipse((12, 12, 16, 16), fill=(196, 222, 233, 165))
    SR('holes', holes)
    for n in ['gear', 'pause', 'close', 'heart', 'coin', 'bulb', 'hammer', 'wand', 'lock']:
        SR('icon_' + n, _icon(n))
    # 画布设计稿的主体珠阵图：首页糖果树 / 游戏页六组异形珠块 / 结算页完整作品。
    # 第二版直接用原图，不再用灰色占位珠重画，保证预制与画布稿一致。
    for key, src in [('art_home', 'beads_home_plate.png'),
                     ('art_board', 'beads_board.png'),
                     ('art_settle', 'beads_settle_plate.png')]:
        f = ROOT / 'generated-images' / src
        if not f.exists():
            raise FileNotFoundError('缺少设计稿珠阵原图: ' + str(f))
        SR(key, Image.open(f).convert('RGBA'))
    SR('grid', _grid_board())
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

    # 顶栏：设置 / 标题 / 金币
    setn, _, _ = p.btn('HomeSettingsBtn', '设置', (24, 28, 52, 52), p.surface,
                       SPR['circle'], txt=INK, size=10,
                       text_box=(6, 30, 40, 18))
    icon(p, 'gear', (14, 6, 24, 24), setn)
    p.label('Logo', 'BlockOut', (24, 92, 342, 46), size=34, color=INK)
    p.node('LogoSub', (24, 138, 342, 24)).text('箭头方块消除', 13, INK_SOFT, 4)

    coin = p.node('CoinPill', (270, 28, 96, 44), p.surface)
    coin.img(WHITE, SPR['pill'], sliced=True)
    icon(p, 'coin', (8, 8, 28, 28), coin)
    p.label('HomeCoinText', '300', (38, 6, 52, 32), coin, size=15, color=INK, align=3)

    # 倾斜拼豆板 + 画布稿的彩色糖果树珠阵（不再用灰色占位珠重画）
    card = p.node('PreviewCard', (24, 174, 342, 318))
    card.img(WHITE, SPR['plate_tilt'])
    p.fields['HomePreviewCard'] = ref(card.rt)
    dec = p.node('HomeArtDecor', (16, 18, 310, 268), card)
    dec.img(WHITE, SPR['art_home'])
    vp, art = p.art('HomeArtViewport', 'HomeRegionArts', (26, 24, 290, 250), card,
                    flat=True)
    locks = []
    for i in range(12):
        lk = Node(p, 'Lock_' + str(i), art,
                  (i % 4 * 290 / 4 + 28, i // 4 * 250 / 3 + 28, 22, 22))
        lk.img(INK_SOFT, SPR['icon_lock'], preserve=True)
        lk.active = False          # 首页展示已收集作品，静态不显示锁
        locks.append(ref(lk.go))
    p.fields['HomeRegionLocks'] = locks
    fail = p.node('FailBox', (26, 24, 290, 250), card, active=False)
    fail.img((1, 1, 1, .82), SPR['plate_soft'])
    p.fields['HomeFailBox'] = ref(fail.go)
    p.btn('HomeRetryBtn', '重试', (85, 96, 120, 44), fail, SPR['btn_white'],
          txt=INK, size=15)
    p.label('HomeRetryExhausted', '稍后再试', (65, 150, 160, 24), fail, 12, INK_SOFT)
    tag, _ = p.label('HomePlaceholderTag', '作品预览', (110, 278, 122, 24), card, 12, INK_SOFT)
    p.fields['HomePlaceholderTag'] = ref(tag.go)
    badge = p.node('PieceBadgePill', (246, 4, 84, 28), card)
    badge.img(WHITE, SPR['pill'], sliced=True)
    p.label('HomePieceBadge', '6/12', (4, 2, 76, 24), badge, 12, INK, 4)

    # 章节 / 进度 / 拼片：演示态数值沿用画布稿，运行时由 Controller 覆盖
    p.label('HomeChapterTitle', '第一章', (24, 502, 220, 26), size=17, color=INK, align=3)
    p.btn('HomeCollectionLink', '查看图鉴', (272, 500, 94, 34), p.surface,
          SPR['pill'], txt=INK, size=12, text_box=(4, 2, 86, 30))
    p.label('HomePieceText', '拼片 6/12', (24, 532, 342, 24), size=12, color=INK_SOFT, align=3)
    p.image('HomeProgressFill', (24, 562, 171, 12), p.surface,
            GREEN, SPR['pill'], filled=True)
    nodes = []
    for i in range(12):
        n, cid = p.image('Node_' + str(i), (24 + i * 29, 582, 20, 20), p.surface,
                         BEAD_COLORS[i % 12] if i < 6 else BEAD_OFF, SPR['bead'])
        nodes.append(ref(cid))
    p.fields['HomeNodes'] = nodes

    # 三个圆形快捷入口：视觉沿用设计稿，文案只用项目已有功能名
    for i, (title, tint) in enumerate([('图鉴', BEAD_COLORS[0]),
                                       ('商店', BEAD_COLORS[3]),
                                       ('设置', BEAD_COLORS[5])]):
        cx = 42 + i * 116
        ring = p.node('HomeQuick_' + str(i), (cx, 606, 62, 56))
        ring.img(WHITE, SPR['circle'])
        b = p.node('QuickBead', (13, 4, 36, 36), ring)
        b.img(tint, SPR['bead'], preserve=True)
        p.node('QuickLabel', (cx - 8, 664, 78, 20)).text(title, 11, INK_SOFT, 4)

    cta, _, tid = p.btn('HomeCtaButton', '开始游戏', (24, 686, 342, 62), p.surface,
                        SPR['btn_green'], color=WHITE, txt=WHITE, size=23,
                        text_box=(20, 4, 302, 36))
    p.fields['HomeCtaTitle'] = ref(tid)
    p.label('HomeCtaSub', '第 07 关', (20, 40, 302, 18), cta, 12, WHITE)
    p.btn('HomeCtaSecondary', '玩法说明', (79, 752, 232, 22), p.surface,
          SPR['btn_white'], color=(1, 1, 1, 0), txt=INK_SOFT, size=11,
          text_box=(0, 0, 232, 22))

    # 底部导航
    nav = p.node('BottomNav', (24, 780, 342, 56))
    nav.img(WHITE, SPR['pill'], sliced=True)
    for i, (key, title) in enumerate([('NavHomeBtn', '首页'),
                                      ('NavCollectionBtn', '图鉴'),
                                      ('NavStoreBtn', '商店')]):
        sp = SPR['btn_green'] if i == 0 else SPR['btn_white']
        p.btn(key, title, (6 + i * 110, 3, 104, 48), nav, sp,
              txt=WHITE if i == 0 else INK, size=14,
              text_box=(2, 2, 100, 44))
    return p.save()


def make_board():
    p = Page('BlockOutGameHud', 'BlockOutBoardPageView')

    # 顶栏
    pause, _, _ = p.btn('BoardPauseBtn', '暂停', (24, 26, 48, 48), p.surface,
                        SPR['circle'], txt=INK, size=9,
                        text_box=(4, 30, 40, 16))
    icon(p, 'pause', (14, 7, 20, 22), pause)
    p.label('BoardLevelTitle', '第 1 章 · 第 07 关', (82, 24, 220, 30), size=20, color=INK)
    p.label('BoardLevelSub', '沿箭头方向移除方块', (82, 54, 220, 20), size=11, color=INK_SOFT)

    hearts = []
    hr = p.node('Hearts', (312, 34, 72, 26))
    for i in range(3):
        n, cid = p.image('Heart' + str(i), (i * 25, 0, 23, 23), hr,
                         PINK, SPR['icon_heart'])
        hearts.append(ref(cid))
    p.fields['BoardHearts'] = hearts

    timer = p.node('Timer', (262, 62, 104, 28))
    timer.img(WHITE, SPR['pill'], sliced=True)
    p.fields['BoardTimerPill'] = ref(timer.rt)
    p.label('BoardTimerText', '02:00', (6, 0, 92, 28), timer, 13, INK)

    # 剩余块数胶囊
    pill = p.node('RemainingPill', (24, 90, 342, 44))
    pill.img(WHITE, SPR['pill'], sliced=True)
    icon(p, 'coin', (12, 9, 26, 26), pill)
    p.label('BoardRemainingText', '剩余 06 块', (46, 6, 200, 32), pill,
            size=16, color=INK, align=3)
    combo = p.node('ComboTag', (242, 8, 92, 28), pill)
    combo.img(GOLD, SPR['pill'], sliced=True)
    p.label('ComboText', '连击 ×3', (2, 2, 88, 24), combo, 11, WHITE, 4)

    # 常驻拼装条（视觉版，12 颗珠子）
    p.node('AssemblyLabel', (24, 142, 200, 20)).text('拼片 6/12', 11, INK_SOFT, 3)
    bead_row(p, 'AssemblyBar', (24, 164, 342, 20), p.surface, active=6, size=20)

    # 棋盘：BoardArea 自己带 6×6 珠格底板；运行时 boardGo 挂在它下面，
    # SetAsFirstSibling 后棋子才不会被白色面板盖住（上一版层级是反的）。
    panel = p.node('BoardPanel', (18, 200, 354, 28))
    p.node('BoardPanelTitle', (30, 204, 180, 20)).text('对局棋盘', 11, INK_SOFT, 3)
    p.node('BoardPanelSub', (196, 204, 162, 20)).text('第 1 章 · 第 07 关', 11, INK_SOFT, 5)
    area = p.node('BoardArea', (18, 232, 354, 354))
    area.img(WHITE, SPR['grid'])
    p.fields['BoardArea'] = ref(area.rt)
    demo = p.node('BoardDemoArt', (30, 244, 330, 330), p.surface, active=False)
    demo.img(WHITE, SPR['art_board'])

    hint = p.node('HintPill', (24, 598, 342, 34))
    hint.img((1, 1, 1, .62), SPR['pill'], sliced=True)
    p.label('BoardHintPill', '轻点整块方块，沿箭头方向飞出', (8, 2, 326, 30), hint,
            size=12, color=INK, align=4)

    # 三个工具槽：首个高亮可用，后两个灰态锁定（对齐画布稿）
    tools = [('HintSlot', '提示', 'bulb', '×3 可用'),
             ('HammerSlot', '锤子', 'hammer', '第 11 关'),
             ('MagicSlot', '魔法棒', 'wand', '第 16 关')]
    for i, (key, title, ic, cond) in enumerate(tools):
        root = p.node(key, (24 + i * 116, 642, 110, 106))
        root.img((0.92, 1, 0.93, 1) if i == 0 else (0.90, 0.94, 0.96, 1),
                 SPR['plate_soft'])
        slot = {'Rect': ref(root.rt), 'Button': ref(root.button())}
        _, cid = p.image('Icon', (37, 10, 36, 36), root,
                         ICON_TINT[ic] if i == 0 else (0.62, 0.70, 0.76, 1),
                         SPR['icon_' + ic])
        slot['Icon'] = ref(cid)
        badge = p.node('CountBadge', (78, 6, 26, 22), root, active=(i == 0))
        badge.img(GOLD, SPR['pill'], sliced=True)
        slot['CountBadge'] = ref(badge.go)
        _, cid = p.label('Count', '×3' if i == 0 else '0', (0, 0, 26, 22), badge,
                         10, WHITE)
        slot['CountText'] = ref(cid)
        lock, _ = p.image('LockBadge', (78, 6, 26, 22), root, INK_SOFT, SPR['icon_lock'])
        lock.active = (i > 0)   # 与 CountBadge 互斥，运行时由 RefreshToolSlot 切换
        slot['LockBadge'] = ref(lock.go)
        _, cid = p.label('NameText', title, (4, 50, 102, 24), root, 13,
                         INK if i == 0 else INK_SOFT)
        slot['NameText'] = ref(cid)
        _, cid = p.label('CondText', cond, (4, 76, 102, 22), root, 10, INK_SOFT)
        slot['CondText'] = ref(cid)
        p.fields[key] = slot

    p.node('Footer', (24, 768, 342, 20)).text('第一章 · 生命模式', 10, INK_SOFT, 4)
    return p.save()


def make_settlement():
    p = Page('BlockOutSettlementPage', 'BlockOutSettlementView')
    p.node('ChapterTag', (24, 34, 220, 22)).text('第 07 关 · 已通关', 12, INK, 3)
    close = p.node('SettleCloseDecor', (314, 28, 52, 52))
    close.img(WHITE, SPR['circle'])
    icon(p, 'close', (14, 14, 24, 24), close)
    p.label('SettleTitleText', '关卡完成', (24, 70, 342, 48), size=30, color=INK, align=4)
    p.node('SettleSub', (24, 120, 342, 22)).text('清空全部方块 · 新作品已解锁', 12, INK_SOFT, 4)

    # 白卡：中央直接铺画布设计稿的完整彩色珠阵作品
    card = p.node('Card', (20, 150, 350, 360))
    card.img(WHITE, SPR['panel'], sliced=True)
    holes = p.node('HolesLayer', (10, 10, 330, 340), card)
    set_type(p, holes.img(WHITE, SPR['holes']), 2)

    tag = p.node('NewUnlockTag', (12, 12, 76, 28), card)
    tag.img((0.96, 0.35, 0.45, 1), SPR['pill'], sliced=True)
    Node(p, 'Text', tag, (0, 0, 76, 28)).text('新解锁', 12, WHITE, 4)

    dec = p.node('SettleArtDecor', (12, 46, 326, 224), card)
    dec.img(WHITE, SPR['art_settle'])
    p.art('SettleRevealRoot', 'SettleRevealRegions', (12, 46, 326, 224), card,
          flat=True)
    _, cid = p.image('SettleLevelImage', (12, 46, 326, 224), card,
                     WHITE, SPR['plate_soft'])
    disable(p, cid)

    p.label('SettleNoteText', '作品已收藏', (12, 276, 200, 24), card, 13, INK, 3)
    got = p.node('InCollectionTag', (238, 274, 96, 30), card)
    got.img(GREEN, SPR['pill'], sliced=True)
    Node(p, 'Text', got, (0, 0, 96, 30)).text('已入图鉴', 11, WHITE, 4)
    p.label('SettlePieceText', '获得新拼片', (12, 312, 200, 22), card, 12, INK_SOFT, 3)

    p.node('AssemblyLabel', (24, 524, 200, 20)).text('本章拼片 07/12', 11, INK_SOFT, 3)
    p.node('AssemblyRemain', (214, 524, 152, 20)).text('还差 5 片完成本章', 10, INK_SOFT, 5)
    bead_row(p, 'AssemblyBar', (24, 548, 342, 22), p.surface, active=7, size=22)

    # 奖励胶囊：+30 / 通关奖励 / 翻倍
    reward = p.node('RewardPill', (20, 584, 350, 62))
    reward.img(WHITE, SPR['pill'], sliced=True)
    icon(p, 'coin', (12, 16, 30, 30), reward)
    p.node('RewardAmount', (48, 8, 70, 44), reward).text('+30', 24, (0.95, 0.62, 0.14, 1), 3)
    p.label('SettleRewardText', '通关奖励 · 难度 2 · 可翻倍', (118, 12, 146, 38), reward,
            11, INK, 3)
    dbl = p.node('SettleDoubleDecor', (266, 13, 92, 36), reward)
    dbl.img(WHITE, SPR['btn_pink'])
    Node(p, 'Text', dbl, (0, 0, 92, 36)).text('翻倍 +30', 12, WHITE, 4)

    p.node('SettleStats', (24, 656, 342, 20)).text('用时 01:42 · 最高连击 ×3 · 错误 0 次',
                                                   10, INK_SOFT, 4)
    p.btn('SettleNextBtn', '下一关 · 第 08 关', (20, 686, 350, 64), p.surface,
          SPR['btn_green'], txt=WHITE, size=20)
    for i, (key, title) in enumerate([('SettleReplayBtn', '重玩'),
                                      ('SettleHomeBtn', '返回首页'),
                                      ('SettleCollectionBtn', '查看收藏')]):
        p.btn(key, title, (20 + i * 117, 762, 110, 28), p.surface,
              SPR['btn_white'], color=(1, 1, 1, 0), txt=INK_SOFT, size=12,
              text_box=(0, 0, 110, 28))
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
