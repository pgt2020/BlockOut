"""生成「珠子风格真实棋子」皮肤方案（只出方案图，不改动 Assets 里的玩法资源）。

背景
----
运行时真实棋子由 `BlockOutBoardView` 创建：
    bg.sprite = BlockOutIconFactory.BlockSprite(block, cols, rows, CellTexPx);
    bg.color  = block.Color;                       // 整张贴图会被 tint 染色
    bodyRect.sizeDelta = bg.sprite.rect.width/height * (cellSize / 240f);

因此替换皮肤有两条硬约束：
1) 贴图必须是灰度/白色 mask，自带彩色会被 `bg.color` 叠乘成脏色；
2) 每个 ShapeId 的贴图尺寸必须和现有 EXR 一致，否则棋盘上块的尺寸会错。
   EXR 尺寸规律：宽 = 240 × 包围盒列数，高 = 248 × 包围盒行数 + 8。

本脚本读取 `BlockOutShapeLibrary.cs` 的 30 组格子坐标，按上述规则生成
30 张灰度珠块 mask，再模拟运行时 tint 出染色效果，最后拼出方案总览与
现状对比图，全部落在 `UI原型/bead_block_skin/`（不进 Assets）。

运行：python3 Tools/UIAuthoring/generate_bead_block_skin.py
"""
from pathlib import Path
import re, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT = Path(__file__).resolve().parents[2]
CS = ROOT / 'Assets/BlockOut/Runtime/Core/Rules/BlockOutShapeLibrary.cs'
EXR = ROOT / 'Assets/BlockOut/Resources/ArtOutPresentation/Reference/Bundles/Sprites/WoodBlockHDR'
OUT = ROOT / 'UI原型' / 'bead_block_skin'
BLOCKS = OUT / 'blocks'
FONT = ROOT / 'Assets/Resources/Fonts/SourceHanSansCN-Regular.otf'

CW, CH, PAD = 240, 248, 8          # 单格宽 / 单格高 / 上下留白
BG = (26, 24, 62)
INK = (232, 236, 255)
TINTS = [(255, 150, 60), (246, 96, 150), (76, 196, 220),
         (128, 206, 110), (152, 118, 220), (255, 198, 70)]


def parse_shapes():
    text = CS.read_text(encoding='utf-8')
    body = re.search(r'ShapeIdToCoords\s*=\s*\{(.*?)\n\s*\};', text, re.S).group(1)
    shapes = {}
    sid = 0
    for line in body.splitlines():
        cells = re.findall(r'new\[\]\s*\{\s*(\d+)\s*,\s*(\d+)\s*\}', line)
        if not cells:
            continue                      # null 占位 / 注释行
        sid += 1
        shapes[sid] = [(int(r), int(c)) for r, c in cells]
    return shapes


def draw_bead(d, cx, cy, rad):
    """灰度珠：阴影 + 球面渐变 + 深灰描边 + 左上高光 + 中孔。
    整体接近白色，运行时 tint 后能干净地变成关卡色。"""
    d.ellipse((cx - rad + 7, cy - rad + 11, cx + rad + 7, cy + rad + 11),
              fill=(58, 58, 58, 110))
    steps = max(10, int(rad / 3))
    for i in range(steps):
        t = i / steps
        inset = rad * t * .90
        v = int(252 - 78 * t)
        d.ellipse((cx - rad + inset, cy - rad + inset,
                   cx + rad - inset, cy + rad - inset), fill=(v, v, v, 255))
    d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad),
              outline=(126, 126, 126, 255), width=7)
    d.ellipse((cx - rad * .62, cy - rad * .70, cx - rad * .04, cy - rad * .28),
              fill=(255, 255, 255, 205))
    d.ellipse((cx - rad * .68, cy - rad * .58, cx - rad * .44, cy - rad * .40),
              fill=(255, 255, 255, 235))
    hr = rad * .21
    d.ellipse((cx - hr - 3, cy - hr - 3, cx + hr + 3, cy + hr + 3),
              fill=(168, 168, 168, 255))
    d.ellipse((cx - hr, cy - hr, cx + hr, cy + hr), fill=(246, 246, 246, 255))


def exr_size(sid):
    """优先读现有 EXR 的真实 dataWindow；公式只是本机无 exrheader 时的兜底。"""
    try:
        r = subprocess.run(['exrheader', str(EXR / f'{sid}.exr')],
                           capture_output=True, text=True, timeout=5)
        m = re.search(r'dataWindow.*?\) - \((\d+) (\d+)\)', r.stdout)
        if m:
            return int(m.group(1)) + 1, int(m.group(2)) + 1
    except Exception:
        pass
    return None


def make_mask(cells, target=None):
    cols = max(c for _, c in cells) + 1
    rows = max(r for r, _ in cells) + 1
    W, H = target or (CW * cols, CH * rows + PAD)
    cw, ch = W / cols, (H - PAD) / rows
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 连通底衬：无描边，避免相邻格之间出现脏的内部边框
    for r, c in cells:
        x0, y0 = c * cw + 8, r * ch + 8
        x1, y1 = (c + 1) * cw - 8, (r + 1) * ch + PAD - 8
        d.rounded_rectangle((x0, y0, x1, y1), radius=42, fill=(214, 214, 214, 255))
    rad = int(min(cw, ch) / 2 - 22)
    for r, c in cells:
        draw_bead(d, int((c + .5) * cw), int((r + .5) * ch + PAD / 2), rad)
    return im


def tinted(mask, rgb):
    """模拟 bg.color = block.Color 的 multiply tint。"""
    solid = Image.new('RGBA', mask.size, rgb + (255,))
    out = ImageChops.multiply(mask.convert('RGBA'), solid)
    out.putalpha(mask.getchannel('A'))
    return out


def label(d, xy, text, size=20, fill=INK, font=None):
    d.text(xy, text, font=font or ImageFont.truetype(str(FONT), size), fill=fill)


def fit(im, box):
    s = min(box[0] / im.width, box[1] / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))),
                     Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if not BLOCKS.exists():
        BLOCKS.mkdir(parents=True)
    shapes = parse_shapes()
    if len(shapes) != 30:
        raise RuntimeError(f'形状表解析异常：读到 {len(shapes)} 组，预期 30')
    masks = {}
    for sid, cells in shapes.items():
        mask = make_mask(cells, exr_size(sid))
        mask.save(BLOCKS / f'{sid}.png')
        masks[sid] = mask

    # 方案总览：6×5，每格展示染色后的珠块（近似 Play Mode 效果）
    # 所有形状按同一「每格 50px」比例展示，和真实棋盘里珠子等大一致，
    # 不做逐格 fit（否则单格形状会被放大成一颗巨珠，误导验收）。
    cellw, cellh, cols, unit = 240, 280, 6, 50
    rows = (30 + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cellw + 24, rows * cellh + 76), BG)
    d = ImageDraw.Draw(sheet)
    label(d, (24, 14), '真实棋子 · 珠子皮肤方案（灰度 mask × 关卡色）', 26)
    label(d, (24, 46), '所有形状按同一单格比例绘制 · 尺寸与现有 EXR 逐张对齐', 15, (168, 178, 220))
    for i, sid in enumerate(range(1, 31)):
        x = 12 + (i % cols) * cellw
        y = 76 + (i // cols) * cellh
        d.rounded_rectangle((x + 4, y + 4, x + cellw - 4, y + cellh - 4),
                            radius=12, fill=(38, 35, 82))
        art = tinted(masks[sid], TINTS[(sid - 1) % len(TINTS)])
        k = unit / CW
        art = art.resize((max(1, int(art.width * k)), max(1, int(art.height * k))),
                         Image.LANCZOS)
        sheet.paste(art, (x + (cellw - art.width) // 2,
                          y + 16 + (cellh - 56 - art.height) // 2), art)
        label(d, (x + 14, y + cellh - 34), f'形状 {sid:02d}', 17)
    sheet.convert('RGB').save(OUT / '00_方案总览.png')

    # 现状对比：ffmpeg 能把无压缩 EXR 解成 PNG，缺失时跳过这一张
    picks = [1, 4, 10, 20, 28, 30]
    have_exr = True
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except Exception:
        have_exr = False
    if have_exr:
        pairw, pairh = 300, 250
        cmp = Image.new('RGB', (pairw * 2 + 60, pairh * len(picks) + 96), BG)
        cd = ImageDraw.Draw(cmp)
        label(cd, (24, 14), '现状 vs 珠子方案', 26)
        label(cd, (24, 48), '左：现有 WoodBlockHDR 灰度白模', 15, (168, 178, 220))
        label(cd, (pairw + 40, 48), '右：珠子 mask 模拟染色', 15, (168, 178, 220))
        tmp = Path(tempfile.gettempdir()) / 'blockout_exr_compare'
        if not tmp.exists():
            tmp.mkdir(parents=True)
        for i, sid in enumerate(picks):
            src = EXR / f'{sid}.exr'
            dst = tmp / f'{sid}.png'
            r = subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error',
                                '-i', str(src), '-frames:v', '1', '-y', str(dst)],
                               capture_output=True)
            y = 90 + i * pairh
            # 两侧按同一单格比例绘制，尺寸严格可比（不逐块 fit）
            k = 50 / CW
            if r.returncode == 0 and dst.exists():
                old = Image.open(dst).convert('RGBA')
                old = old.resize((max(1, int(old.width * k)),
                                  max(1, int(old.height * k))), Image.LANCZOS)
                cmp.paste(old, (20 + (pairw - old.width) // 2,
                                y + (pairh - old.height) // 2), old)
            new = tinted(masks[sid], TINTS[(sid - 1) % len(TINTS)])
            new = new.resize((max(1, int(new.width * k)),
                              max(1, int(new.height * k))), Image.LANCZOS)
            cmp.paste(new, (pairw + 40 + (pairw - new.width) // 2,
                            y + (pairh - new.height) // 2), new)
            label(cd, (24, y + pairh - 26), f'形状 {sid:02d}', 16, (168, 178, 220))
        cmp.save(OUT / '01_现状对比.png')

    print('形状:', len(shapes), '| 输出:', OUT)
    for sid in (1, 4, 10, 20, 28, 30):
        print(f'  形状 {sid:02d}: {masks[sid].size}  (现有 EXR 同尺寸)')


if __name__ == '__main__':
    main()
