"""渲染 generate_beads_prefabs.py 生成的设计态预览图。

直接复用生成脚本的内存节点树，不解析 prefab YAML；BoardDemoArt 这类默认禁用的
「设计态演示层」也会画出来，方便把预制与画布设计稿逐屏对比。
运行：python3 Tools/UIAuthoring/render_beads_preview.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import generate_beads_prefabs as G

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'UI原型' / 'beads_v2'
FONT_PATH = ROOT / 'Assets/Resources/Fonts/SourceHanSansCN-Regular.otf'
W, H = 390, 844

IMGS = {}
BORDERS = {}
_ws = G._write_sprite


def _capture(name, im, border=0):
    IMGS[name] = im.copy()
    BORDERS[name] = border
    return _ws(name, im, border)


G._write_sprite = _capture

PAGES = []
_save = G.Page.save


def _keep(self):
    PAGES.append(self)
    return _save(self)


G.Page.save = _keep

G.build_sprites()
for maker in (G.make_home, G.make_board, G.make_settlement):
    maker()


def col(c, default=(255, 255, 255, 255)):
    if not isinstance(c, dict):
        return default
    return tuple(int(round(float(c.get(k, 1)) * 255)) for k in ('r', 'g', 'b', 'a'))


def sprite_of(ref):
    if not isinstance(ref, dict) or not ref.get('guid'):
        return None, None
    for name, r in G.SPR.items():
        if isinstance(r, dict) and r.get('guid') == ref['guid']:
            return IMGS.get(name), name
    return None, None


def border_of(name):
    b = BORDERS.get(name, 0)
    if isinstance(b, (tuple, list)):
        return int(b[0]), int(b[1]), int(b[2]), int(b[3])
    return (int(b),) * 4


def fit(im, w, h, typ=0, preserve=False, name=None):
    w, h = max(1, int(w)), max(1, int(h))
    if typ == 2:  # Tiled
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        for y in range(0, h, im.height):
            for x in range(0, w, im.width):
                out.alpha_composite(im, (x, y))
        return out
    if typ == 1 and name:  # Sliced
        bx, by, bz, bw = border_of(name)
        if bx + bz < im.width and by + bw < im.height and max(bx, by, bz, bw) > 0:
            l, t, r, b = bx, by, bz, bw
            parts = [im.crop((0, 0, l, t)), im.crop((l, 0, im.width - r, t)),
                     im.crop((im.width - r, 0, im.width, t)),
                     im.crop((0, t, l, im.height - b)),
                     im.crop((l, t, im.width - r, im.height - b)),
                     im.crop((im.width - r, t, im.width, im.height - b)),
                     im.crop((0, im.height - b, l, im.height)),
                     im.crop((l, im.height - b, im.width - r, im.height)),
                     im.crop((im.width - r, im.height - b, im.width, im.height))]
            cw, ch = max(1, w - l - r), max(1, h - t - b)
            parts[1] = parts[1].resize((cw, t), Image.LANCZOS)
            parts[3] = parts[3].resize((l, ch), Image.LANCZOS)
            parts[4] = parts[4].resize((cw, ch), Image.LANCZOS)
            parts[5] = parts[5].resize((r, ch), Image.LANCZOS)
            parts[7] = parts[7].resize((cw, b), Image.LANCZOS)
            out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            for part, pos in zip(parts, [(0, 0), (l, 0), (w - r, 0),
                                         (0, t), (l, t), (w - r, t),
                                         (0, h - b), (l, h - b), (w - r, h - b)]):
                out.alpha_composite(part, pos)
            return out
    if preserve and im.width and im.height:
        s = min(w / im.width, h / im.height)
        nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
        r = im.resize((nw, nh), Image.LANCZOS)
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        out.alpha_composite(r, ((w - nw) // 2, (h - nh) // 2))
        return out
    return im.resize((w, h), Image.LANCZOS)


def tint(im, c):
    if c == (255, 255, 255, 255):
        return im
    from PIL import ImageChops
    rgb = ImageChops.multiply(im.convert('RGB'), Image.new('RGB', im.size, c[:3]))
    a = im.getchannel('A').point(lambda v: v * c[3] // 255)
    rgb.putalpha(a)
    return rgb


def render(page):
    canvas = Image.new('RGBA', (W, H), (255, 255, 255, 255))
    docs = {cid: data for _, cid, _, data in page.docs}

    def draw(node, ox, oy):
        if not node.active and node.name != 'BoardDemoArt':
            return
        x = ox + node.position['x']
        y = oy - node.position['y']
        w, h = node.size['x'], node.size['y']
        for cid in node.components:
            d = docs.get(cid)
            if not isinstance(d, dict) or not d.get('m_Enabled', 1):
                continue
            if 'm_Sprite' in d:
                im, name = sprite_of(d['m_Sprite'])
                if im is None:
                    continue
                c = col(d.get('m_Color'))
                if c[3] == 0:
                    continue
                piece = fit(im, w, h, int(d.get('m_Type', 0)),
                            bool(d.get('m_PreserveAspect')), name)
                piece = tint(piece, c)
                canvas.alpha_composite(piece, (int(x), int(y)))
            elif 'm_Text' in d:
                txt = str(d.get('m_Text', ''))
                if not txt:
                    continue
                fd = d.get('m_FontData', {})
                size = int(fd.get('m_FontSize', 14))
                c = col(d.get('m_Color'))
                try:
                    font = ImageFont.truetype(str(FONT_PATH), size)
                except OSError:
                    font = ImageFont.load_default()
                dd = ImageDraw.Draw(canvas)
                tw = dd.textlength(txt, font=font)
                align = int(fd.get('m_Alignment', 4))
                tx = x + (w - tw) / 2 if align == 4 else (x + w - tw if align == 5 else x + 4)
                ty = y + max(0, (h - size * 1.25) / 2)
                dd.text((tx, ty), txt, font=font, fill=c)
        for child in node.children:
            draw(child, x, y)

    draw(page.surface, 0, 0)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (page.name + '.png')
    canvas.convert('RGB').save(path)
    return path


if __name__ == '__main__':
    for p in PAGES:
        print('预览:', render(p))
