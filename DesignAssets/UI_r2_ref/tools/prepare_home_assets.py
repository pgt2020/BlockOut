"""首页 R2 还原：从已生成背景与既有 3D 图标包制作 Unity 可直接用的 sprite。

输入：
  DesignAssets/UI_r2_ref/assets/A_clean_full_screen_background_*.png  (AI 生成，已去水印)
  Assets/BlockOut/Resources/UI/Reference/fullscreen/s2.png             (仅取像素猫画作)
  DesignAssets/UI_garden_kit_v2/ui/*.png                               (既有 3D 图标)
输出：
  Assets/BlockOut/Resources/ArtOutPresentation/Sprites/home_*.png + .meta
不启动 Unity，不触发导表/编译。
"""
from pathlib import Path
import math
import re
import uuid

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
BG_SRC = ROOT / 'DesignAssets/UI_r2_ref/assets/A_clean_full_screen_background_2026-11-17T06-17-04.png'
ERASED = ROOT / 'DesignAssets/UI_r2_ref/assets/home_bg_no_watermark.png'
S2 = ROOT / 'Assets/BlockOut/Resources/UI/Reference/fullscreen/s2.png'
KIT = ROOT / 'DesignAssets/UI_garden_kit_v2'
DEST = ROOT / 'Assets/BlockOut/Resources/ArtOutPresentation/Sprites'
OUT = ROOT / 'DesignAssets/UI_r2_ref/out'

META_TEMPLATE = '''fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
  externalObjects: {{}}
  serializedVersion: 12
  mipmaps:
    enableMipMap: 0
  isReadable: 0
  textureType: 8
  textureShape: 1
  sRGBTexture: 1
  alphaIsTransparency: 1
  spriteMode: 1
  spritePixelsToUnits: 100
  spriteMeshType: 0
  spriteAlignment: 0
  spritePivot:
    x: 0.5
    y: 0.5
  spriteBorder:
    x: {b0}
    y: {b1}
    z: {b2}
    w: {b3}
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 1
    mipBias: 0
    wrapU: 1
    wrapV: 1
    wrapW: 1
  maxTextureSize: 2048
  nPOTScale: 0
  spriteSheet:
    serializedVersion: 2
    sprites: []
    outline: []
    physicsShape: []
    bones: []
    spriteID: {sid}
    internalID: 0
    vertices: []
    indices: ''
'''


def save(im, name, border=(0, 0, 0, 0)):
    path = DEST / f'{name}.png'
    im.save(path)
    # GUID 必须稳定，否则重跑脚本会让 prefab 的精灵引用全部失效。
    meta_path = DEST / f'{name}.png.meta'
    old = meta_path.read_text(encoding='utf-8') if meta_path.exists() else ''
    m = re.search(r'^guid: (\w+)', old, re.M)
    sid_m = re.search(r'spriteID: (\w+)', old)
    meta = META_TEMPLATE.format(
        guid=m.group(1) if m else uuid.uuid4().hex,
        sid=sid_m.group(1) if sid_m else uuid.uuid4().hex,
        b0=border[0], b1=border[1], b2=border[2], b3=border[3],
    )
    meta_path.write_text(meta, encoding='utf-8')
    print(f'{name:22s} {im.size} border={border}')


def make_background():
    bg = Image.open(ERASED if ERASED.exists() else BG_SRC).convert('RGB')
    # 参考 s2 里像素猫画板：只取画作本身，画框/画架留在 AI 背景里
    cat = Image.open(S2).convert('RGB').crop((92, 126, 246, 306))
    cat = cat.resize((396, 460), Image.LANCZOS)
    # 极轻的暗角让画作贴进空白画布，而不是像贴纸浮在上面
    shade = Image.new('L', cat.size, 0)
    sd = ImageDraw.Draw(shade)
    sd.rounded_rectangle((0, 0, cat.width - 1, cat.height - 1), radius=4, outline=26, width=3)
    cat = Image.composite(Image.blend(cat, Image.new('RGB', cat.size, (60, 45, 32)), 0.12), cat, shade)
    bg.paste(cat, (314, 618))
    bg.save(OUT / 'home_bg_clean.png')
    save(bg, 'home_bg')


def circular_icon(name, src, box, outname, target=190):
    im = Image.open(src).convert('RGBA').crop(box)
    scale = target / max(im.size)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    canvas = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    canvas.alpha_composite(im, ((256 - im.width) // 2, (256 - im.height) // 2))
    # 柔边圆遮罩：保留奶油底与图标自身高光，不把软阴影削掉
    yy, xx = np.mgrid[0:256, 0:256]
    d = np.sqrt((xx - 127.5) ** 2 + (yy - 127.5) ** 2)
    a = np.clip((122.0 - d) / 8.0 + 0.5, 0, 1) * 255
    rgba = np.array(canvas)
    rgba[..., 3] = (rgba[..., 3] * a / 255).astype(np.uint8)
    out = Image.fromarray(rgba, 'RGBA')
    save(out, outname)


def make_circle_and_settings():
    circle = Image.open(KIT / 'components/circle_button.png').convert('RGBA')
    save(circle, 'home_circle', border=(96, 96, 96, 96))
    gear = Image.open(KIT / 'ui/btn_settings.png').convert('RGBA')
    save(gear, 'home_settings', border=(48, 48, 48, 48))
    plate = Image.open(KIT / 'components/plate_label.png').convert('RGBA')
    save(plate, 'home_title_plate', border=(180, 60, 180, 60))


def make_start_button():
    w, h, r = 572, 180, 82
    pad = 16
    canvas = Image.new('RGBA', (w, h + pad), (0, 0, 0, 0))
    # 柔投影
    sh = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle((8, 8 + pad, w - 10, h - 8 + pad), radius=r, fill=(92, 66, 28, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    canvas.alpha_composite(sh)
    # 奶油外描边
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((4, 2, w - 5, h - 6 + pad), radius=r, fill=(255, 250, 234, 255))
    # 绿色渐变主体（逐行画）
    mask = Image.new('L', canvas.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((12, 10, w - 13, h - 14 + pad), radius=r - 8, fill=255)
    grad = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    gp = grad.load()
    for y in range(canvas.height):
        t = max(0.0, min(1.0, (y - 10) / (h + pad - 24)))
        col = (int(154 - 42 * t), int(202 - 44 * t), int(72 - 22 * t), 255)
        for x in range(canvas.width):
            gp[x, y] = col
    canvas.paste(grad, (0, 0), mask)
    # 顶部高光
    hl = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle((28, 20, w - 29, 58 + pad), radius=30, fill=(255, 255, 255, 52))
    hl = hl.filter(ImageFilter.GaussianBlur(8))
    canvas = Image.alpha_composite(canvas, hl)
    save(canvas, 'home_btn_start', border=(150, 70, 150, 70))


def make_plus():
    s = 96
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4, 4, s - 5, s - 5), fill=(72, 168, 92, 255), outline=(255, 252, 236, 255), width=4)
    d.rounded_rectangle((s // 2 - 5, 25, s // 2 + 5, s - 25), radius=4, fill=(255, 255, 255, 255))
    d.rounded_rectangle((25, s // 2 - 5, s - 25, s // 2 + 5), radius=4, fill=(255, 255, 255, 255))
    save(im, 'home_plus', border=(36, 36, 36, 36))


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    make_background()
    make_circle_and_settings()
    circular_icon('gallery', KIT / 'ui/tab_gallery.png', (30, 18, 162, 130), 'home_icon_gallery')
    circular_icon('skin', KIT / 'ui/tab_skin.png', (30, 18, 162, 130), 'home_icon_skin')
    circular_icon('daily', KIT / 'ui/tab_daily.png', (24, 14, 152, 126), 'home_icon_daily')
    circular_icon('achievement', KIT / 'ui/btn_achievement.png', (21, 8, 176, 126), 'home_icon_achievement')
    make_start_button()
    make_plus()
    print('done')
