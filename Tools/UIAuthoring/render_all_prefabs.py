"""从 prefab YAML 直接渲染预览图（不启动 Unity）。

两种模式：
  默认（真实态）：严格按 m_IsActive 渲染，默认禁用的设计演示层不出现，
                 与 Play Mode 的 UI 框架一致（运行时棋子由代码生成，静态图不显示）。
  --design     ：额外画出 BoardDemoArt 设计态演示层，供与画布稿比对。

运行：python3 Tools/UIAuthoring/render_all_prefabs.py [--design]
输出：UI原型/beads_final/*.png（真实态）/ UI原型/beads_design/*.png（设计态）
"""
from pathlib import Path
import re, yaml, math
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI'
import sys
OUT = ROOT / 'UI原型' / 'beads_final'
DESIGN_VIEW = '--design' in sys.argv
if DESIGN_VIEW:
    OUT = ROOT / 'UI原型' / 'beads_design'
FONT_PATH = ROOT / 'Assets/Resources/Fonts/SourceHanSansCN-Regular.otf'
W, H = 390, 844

# guid -> 贴图路径 / 贴图 meta 的 spriteBorder
GUID2FILE = {}
BORDER = {}
for m in (ROOT / 'Assets').rglob('*.meta'):
    g = re.search(r'^guid: (\w+)', m.read_text(encoding='utf-8-sig', errors='ignore'), re.M)
    if not g:
        continue
    f = m.with_suffix('')
    if f.suffix.lower() in ('.png', '.jpg', '.jpeg'):
        GUID2FILE[g.group(1)] = f
    try:
        d = yaml.safe_load(m.read_text(encoding='utf-8-sig', errors='ignore'))
        b = (d or {}).get('TextureImporter', {}).get('spriteBorder')
        if isinstance(b, dict):
            BORDER[g.group(1)] = (int(b.get('x', 0)), int(b.get('y', 0)),
                                  int(b.get('z', 0)), int(b.get('w', 0)))
    except yaml.YAMLError:
        pass

_CACHE = {}


def parse(path):
    s = path.read_text(encoding='utf-8-sig')
    heads = list(re.finditer(r'^--- !u!(\d+) &(-?\d+).*\n', s, re.M))
    docs = []
    for i, h in enumerate(heads):
        chunk = s[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(s)]
        d = yaml.safe_load(chunk)
        key = next(iter(d))
        docs.append([int(h.group(1)), int(h.group(2)), key, d[key]])
    return docs


def col(c, default=(255, 255, 255, 255)):
    if not isinstance(c, dict):
        return default
    return tuple(max(0, min(255, int(round(float(c.get(k, 1)) * 255))))
                 for k in ('r', 'g', 'b', 'a'))


def load(guid):
    if guid not in GUID2FILE:
        return None
    p = GUID2FILE[guid]
    if p not in _CACHE:
        try:
            _CACHE[p] = Image.open(p).convert('RGBA')
        except OSError:
            return None
    return _CACHE[p]


def sliced(im, w, h, b):
    l, t, r, bo = b
    if l + r >= im.width or t + bo >= im.height or max(b) <= 0:
        return im.resize((max(1, w), max(1, h)), Image.LANCZOS)
    parts = [im.crop((0, 0, l, t)), im.crop((l, 0, im.width - r, t)),
             im.crop((im.width - r, 0, im.width, t)),
             im.crop((0, t, l, im.height - bo)),
             im.crop((l, t, im.width - r, im.height - bo)),
             im.crop((im.width - r, t, im.width, im.height - bo)),
             im.crop((0, im.height - bo, l, im.height)),
             im.crop((l, im.height - bo, im.width - r, im.height)),
             im.crop((im.width - r, im.height - bo, im.width, im.height))]
    cw, ch = max(1, w - l - r), max(1, h - t - bo)
    parts[1] = parts[1].resize((cw, t), Image.LANCZOS)
    parts[3] = parts[3].resize((l, ch), Image.LANCZOS)
    parts[4] = parts[4].resize((cw, ch), Image.LANCZOS)
    parts[5] = parts[5].resize((r, ch), Image.LANCZOS)
    parts[7] = parts[7].resize((cw, bo), Image.LANCZOS)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    for part, pos in zip(parts, [(0, 0), (l, 0), (w - r, 0), (0, t), (l, t),
                                 (w - r, t), (0, h - bo), (l, h - bo), (w - r, h - bo)]):
        out.alpha_composite(part, pos)
    return out


def fit(im, w, h, typ, preserve, fill, border):
    w, h = max(1, int(w)), max(1, int(h))
    if typ == 2:  # Tiled
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        for y in range(0, h, max(1, im.height)):
            for x in range(0, w, max(1, im.width)):
                out.alpha_composite(im, (x, y))
        return out
    if typ == 1 and border:
        return sliced(im, w, h, border)
    if typ == 3 and fill < .999:  # Filled（水平）
        out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        piece = im.resize((w, h), Image.LANCZOS).crop((0, 0, max(1, int(w * fill)), h))
        out.alpha_composite(piece, (0, 0))
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
    rgb = ImageChops.multiply(im.convert('RGB'), Image.new('RGB', im.size, c[:3]))
    a = im.getchannel('A').point(lambda v: v * c[3] // 255)
    rgb.putalpha(a)
    return rgb


def composite(canvas, piece, x, y):
    """安全叠加：自动裁剪超出画布的部分。"""
    x, y = int(round(x)), int(round(y))
    cw, ch = canvas.size
    sx, sy = max(0, -x), max(0, -y)
    dx, dy = max(0, x), max(0, y)
    w, h = min(piece.width - sx, cw - dx), min(piece.height - sy, ch - dy)
    if w <= 0 or h <= 0:
        return
    canvas.alpha_composite(piece.crop((sx, sy, sx + w, sy + h)), (dx, dy))


def rect_of(rt, parent):
    px, py, pw, ph = parent
    a0, a1 = rt['m_AnchorMin'], rt['m_AnchorMax']
    pivot, pos, sd = rt['m_Pivot'], rt['m_AnchoredPosition'], rt['m_SizeDelta']
    stretch_x = abs(float(a1['x']) - float(a0['x'])) > 1e-4
    stretch_y = abs(float(a1['y']) - float(a0['y'])) > 1e-4
    if stretch_x or stretch_y:
        w = pw + float(sd['x']) if stretch_x else float(sd['x'])
        h = ph + float(sd['y']) if stretch_y else float(sd['y'])
        cx = px + pw / 2 + float(pos['x'])
        cy = py + ph / 2 - float(pos['y'])
        return (cx - w / 2, cy - h / 2, w, h)
    ax = px + float(a0['x']) * pw
    ay = py + (1 - float(a0['y'])) * ph
    w, h = float(sd['x']), float(sd['y'])
    return (ax + float(pos['x']) - float(pivot['x']) * w,
            ay - float(pos['y']) - (1 - float(pivot['y'])) * h, w, h)


def draw_text(canvas, d, rect):
    txt = str(d.get('m_Text', ''))
    if not txt:
        return
    fd = d.get('m_FontData', {}) or {}
    size = int(fd.get('m_FontSize', 16))
    c = col(d.get('m_Color'))
    x, y, w, h = rect
    align = int(fd.get('m_Alignment', 4))
    lines = txt.split('\n')

    def font(sz):
        try:
            return ImageFont.truetype(str(FONT_PATH), max(8, int(sz)))
        except OSError:
            return ImageFont.load_default()

    f = font(size)
    bold = bool(int(fd.get('m_FontStyle', 0)) & 1)
    probe = ImageDraw.Draw(canvas)
    longest = max((probe.textlength(t, font=f) for t in lines), default=0)
    if longest > w and w > 0:
        size = max(int(fd.get('m_MinSize', 9)), int(size * w / longest))
        f = font(size)
        longest = max((probe.textlength(t, font=f) for t in lines), default=0)
    lh = size * 1.32
    total = lh * len(lines)
    if align <= 2:
        ty = y + 2
    elif align >= 6:
        ty = y + h - total - 2
    else:
        ty = y + (h - total) / 2
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for line in lines:
        tw = ld.textlength(line, font=f)
        if align in (1, 4, 7):
            tx = x + (w - tw) / 2
        elif align in (2, 5, 8):
            tx = x + w - tw - 2
        else:
            tx = x + 2
        ld.text((tx, ty), line, font=f, fill=c,
                 stroke_width=1 if bold else 0, stroke_fill=c)
        ty += lh
    canvas.alpha_composite(layer)


def render(path):
    docs = parse(path)
    byid = {fid: (cls, name, data) for cls, fid, name, data in docs}
    go_by_rt = {fid: d['m_GameObject']['fileID'] for cls, fid, _, d in docs if cls == 224}
    rt_of_go = {d['m_GameObject']['fileID']: fid for cls, fid, _, d in docs if cls == 224}
    roots = [fid for cls, fid, _, d in docs
             if cls == 224 and d.get('m_Father', ref_zero())['fileID'] == 0]
    if not roots:
        return None
    root_rt = roots[0]
    root_go = go_by_rt[root_rt]
    stem = byid[root_go][2]['m_Name']
    is_item = stem in ('ChapterItem', 'RepeatItem', 'StoreHint', 'StoreHammer', 'StoreMagic')

    base = (0, 0, W, H)
    if is_item:
        # 列表项根节点被布局脚本改成 stretch anchor，但 sizeDelta 仍是绝对卡片尺寸；
        # 预览按固定尺寸卡片还原（不改 prefab，运行时由 LayoutGroup 控制）。
        rt = byid[root_rt][2]
        rt['m_AnchorMin'] = {'x': 0, 'y': 1}
        rt['m_AnchorMax'] = {'x': 0, 'y': 1}
        rt['m_Pivot'] = {'x': 0, 'y': 1}
        rt['m_AnchoredPosition'] = {'x': 0, 'y': 0}
    root_rect = rect_of(byid[root_rt][2], base)
    if is_item:
        # 列表项单独预览也铺同一张夜空底，避免浅青底与整套深蓝紫体系割裂
        sky_path = next((p for p in GUID2FILE.values() if p.name == 'sky.png'), None)
        sky = Image.open(sky_path).convert('RGBA') if sky_path else None
        canvas = Image.new('RGBA', (W, int(root_rect[3]) + 48), (59, 50, 131, 255))
        if sky:
            canvas.alpha_composite(sky.crop((0, 0, W, min(sky.height, canvas.height))))
        offset = (24, 24)
    else:
        canvas = Image.new('RGBA', (W, H), (255, 255, 255, 255))
        offset = (0, 0)

    def components(go_fid):
        g = byid.get(go_fid)
        if not g:
            return []
        return [byid[c['component']['fileID']][2]
                for c in g[2].get('m_Component', [])
                if c['component']['fileID'] in byid]

    def draw(rt_fid, parent, shift=(0, 0), surf=None, origin=(0, 0)):
        surf = canvas if surf is None else surf
        rt = byid.get(rt_fid)
        if not rt:
            return
        go_fid = go_by_rt.get(rt_fid)
        go = byid.get(go_fid)
        # 三屏的 BoardDemoArt 是默认禁用的「设计态演示层」，预览时照样画出来，
        # 只有 --design 模式才画默认禁用的演示层；真实态严格按 m_IsActive。
        show = DESIGN_VIEW and go[2]['m_Name'] == 'BoardDemoArt'
        if not go or (not go[2].get('m_IsActive', 1) and not show):
            return
        r = rect_of(rt[2], parent)
        x, y, w, h = (r[0] + shift[0], r[1] + shift[1], r[2], r[3])
        if w < 1 or h < 1:
            if go[2]['m_Name'] == 'Content':
                # ScrollRect 的 Content 在静态 YAML 里高度为 0，运行时由
                # VerticalLayoutGroup + ContentSizeFitter 撑开，且锚点贴父容器顶部。
                # 之前按父高的一半居中，会把整块内容推到屏幕中间，造成上半屏空白。
                x, y, w, h = parent[0], parent[1], parent[2], parent[3]
            else:
                return
        sx, sy = x - origin[0], y - origin[1]
        comps = components(go_fid)
        for comp in comps:
            # 组件级禁用（如结算页默认关闭、运行时才启用的 SettleLevelImage）
            if not comp.get('m_Enabled', 1):
                continue
            if 'm_Sprite' in comp:
                sp = comp.get('m_Sprite') or {}
                im = load(sp.get('guid', ''))
                if im is None:
                    continue
                c = col(comp.get('m_Color'))
                if c[3] == 0:
                    continue
                border = BORDER.get(sp.get('guid', ''), (0, 0, 0, 0))
                piece = fit(im, w, h, int(comp.get('m_Type', 0)),
                            bool(comp.get('m_PreserveAspect')),
                            float(comp.get('m_FillAmount', 1)), border)
                composite(surf, tint(piece, c), sx, sy)
            elif 'm_Text' in comp:
                draw_text(surf, comp, (sx, sy, w, h))
        children = [ch['fileID'] for ch in rt[2].get('m_Children', [])]
        # RectMask2D 的滚动视口：子节点画到临时层再裁到视口矩形内
        is_viewport = any('m_Softness' in c and 'm_Padding' in c for c in comps)
        if is_viewport:
            sub = Image.new('RGBA', (max(1, int(w)), max(1, int(h))), (0, 0, 0, 0))
            for ch in children:
                draw(ch, (x, y, w, h), surf=sub, origin=(x, y))
            composite(surf, sub, sx, sy)
            return
        # VerticalLayoutGroup：静态 YAML 里子项 anchoredPosition 全为 0，按序累加
        has_vlg = any('m_Spacing' in c and 'm_ChildAlignment' in c for c in comps)
        running = 0
        for ch in children:
            crt = byid.get(ch)
            if not crt:
                continue
            ch_go = go_by_rt.get(ch)
            if ch_go and not byid[ch_go][2].get('m_IsActive', 1):
                continue          # Unity LayoutGroup 不计入未激活子节点
            if has_vlg:
                cr = rect_of(crt[2], (x, y, w, h))
                ch_h = max(cr[3], 24)
                draw(ch, (x, y, w, h), (0, running - (cr[1] - y)),
                     surf=surf, origin=origin)
                running += ch_h + 12
            else:
                draw(ch, (x, y, w, h), surf=surf, origin=origin)

    draw(root_rt, base, offset)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / (path.stem + '.png')
    canvas.convert('RGB').save(out)
    return out


def ref_zero():
    return {'fileID': 0}


CN = {
    'BlockOutHomePage': '01_首页', 'BlockOutGameHud': '02_游戏页',
    'BlockOutSettlementPage': '03_结算页', 'BlockOutCollectionPage': '04_图鉴',
    'BlockOutStorePage': '05_商店', 'BlockOutSettingsPage': '06_设置',
    'BlockOutPausePopup': '07_暂停', 'BlockOutFailPopup': '08_失败',
    'BlockOutConfirmPopup': '09_确认', 'BlockOutGuidePopup': '10_玩法说明',
    'BlockOutAboutPopup': '11_关于', 'BlockOutLoadingPage': '12_加载页',
    'ChapterItem': '13_章节条目', 'RepeatItem': '14_重复挑战格',
    'StoreHint': '15_商店商品项', 'StoreHammer': '16_商店·锤子',
    'StoreMagic': '17_商店·魔法棒',
}


def contact_sheet(paths):
    """把全部单屏拼成一张带中文标题的全览，供每轮人工验收。"""
    scale = .5
    cw, ch = int(W * scale), int(H * scale)
    pad, title_h, cols = 12, 26, 5
    rows = math.ceil(len(paths) / cols)
    sheet = Image.new('RGB', (cols * (cw + pad) + pad,
                              rows * (ch + title_h + pad) + pad), (238, 241, 250))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(FONT_PATH), 16)
    head = ImageFont.truetype(str(FONT_PATH), 20)
    d.text((pad + 4, 2), 'BlockOut · 商业化 UI 逐轮验收', fill=(30, 40, 72), font=head)
    for i, p in enumerate(paths):
        x = pad + (i % cols) * (cw + pad)
        y = pad + title_h + (i // cols) * (ch + title_h + pad)
        im = Image.open(p).convert('RGB')
        s = min(cw / im.width, ch / im.height)
        nw, nh = max(1, int(im.width * s)), max(1, int(im.height * s))
        thumb = im.resize((nw, nh), Image.LANCZOS)
        sheet.paste(thumb, (x + (cw - nw) // 2, y + (ch - nh) // 2))
        d.text((x + 4, y + ch + 4), CN.get(p.stem, p.stem),
               fill=(40, 52, 88), font=font)
    sheet.save(OUT / '00_全览.png')
    return OUT / '00_全览.png'


if __name__ == '__main__':
    outs = []
    prefabs = [p for p in UI.rglob('*.prefab')
            if p.stem != 'BlockOutPopupLayer']
    prefabs.sort(key=lambda p: CN.get(p.stem, 'zz' + p.stem))
    for p in prefabs:
        out = render(p)
        outs.append(out)
        if p.stem in CN:
            Image.open(out).convert('RGB').save(OUT / (CN[p.stem] + '.png'))
        print('预览:', out)
    print('全览:', contact_sheet(outs))
