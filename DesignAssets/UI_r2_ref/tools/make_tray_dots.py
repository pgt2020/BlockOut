# -*- coding: utf-8 -*-
"""生成棋盘托盘的点阵底（可平铺 32x32，点距 16px）。

为什么要单独出一张：托盘内芯是纯色九宫格，放大到 342x430 后完全是空白色块；
参考图里那层极淡的点阵是「不是空白」的关键细节。Unity 侧用 Image.Type.Tiled 平铺，
因此 .meta 必须写 spriteMeshType: 0（Full Rect），Tight 网格会让 Tiled 退化。
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'Assets/BlockOut/Resources/ArtOutPresentation/Sprites/tray_dots.png'
SIZE, PITCH, DOT_R, COLOR = 32, 16, 1.0, (216, 196, 166, 90)

im = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
for cy in range(PITCH // 2, SIZE, PITCH):
    for cx in range(PITCH // 2, SIZE, PITCH):
        d.ellipse((cx - DOT_R, cy - DOT_R, cx + DOT_R, cy + DOT_R), fill=COLOR)
im.save(OUT)

meta = OUT.with_suffix('.png.meta')
if not meta.exists():
    meta.write_text(f'''fileFormatVersion: 2
guid: 7c1f4a2d9b6e4c8fa13d5b0e2c7f4a91
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
    x: 0
    y: 0
    z: 0
    w: 0
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 1
    mipBias: 0
    wrapU: 0
    wrapV: 0
    wrapW: 0
  maxTextureSize: 2048
  nPOTScale: 0
  textureCompression: 1
  compressionQuality: 50
  spriteSheet:
    serializedVersion: 2
    sprites: []
    outline: []
    physicsShape: []
    bones: []
    spriteID: 5e97eb03825dee720800000000000000
    internalID: 0
    vertices: []
    indices:
    edges: []
    weights: []
    secondaryTextures: []
    nameFileIdTable: {{}}
  platformSettings:
  - serializedVersion: 3
    buildTarget: DefaultTexturePlatform
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 1
    compressionQuality: 50
  userData:
  assetBundleName:
  assetBundleVariant:
''', encoding='utf-8')
print('wrote', OUT, im.size)
