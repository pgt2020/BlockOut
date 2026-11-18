"""弹层与加载页素材：从参考截图裁出无文字的装饰元素。

- loading_bg：拱廊画廊干净背景（复用 R2 背景，按 390:844 裁切）
- loading_logo：s1 中央圆角 logo 卡（圆角羽化）
- icon_heart_broken：s6 碎心（边界泛洪去平底色，保留心内高光）
- deco_bunting_l / deco_bunting_r：s5 顶部三角彩旗（左右镜像一对）

save() 复用已有 .meta 的 guid，重跑不会让 prefab 引用失效。
"""
from pathlib import Path
from collections import deque
import re
import uuid

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
ART = ROOT / 'Assets/BlockOut/Resources/ArtOutPresentation/Sprites'
REF = ROOT / 'Assets/BlockOut/Resources/UI/Reference/fullscreen'
R2 = ROOT / 'DesignAssets/UI_r2_ref/assets'

META_TEMPLATE = '''fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
  externalObjects: {{}}
  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 0
    sRGBTexture: 1
    linearTexture: 0
    fadeOut: 1
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  bumpmap:
    convertToNormalMap: 0
    externalNormalMap: 0
    heightScale: 0.25
    normalMapFilter: 0
    flipGreenChannel: 0
  isReadable: 0
  streamingMipmaps: 0
  streamingMipmapsPriority: 0
  vTOnly: 0
  ignoreMipmapLimits: 0
  grayScaleToAlpha: 0
  generateCubemap: 6
  cubemapConvolution: 0
  seamlessCubemap: 0
  textureFormat: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 1
    mipBias: 0
    wrapU: 1
    wrapV: 1
    wrapW: 1
  nPOTScale: 0
  lightmap: 0
  compressionQuality: 50
  spriteMode: 1
  spriteExtrude: 1
  spriteMeshType: 0
  alignment: 0
  spritePivot: {{x: 0.5, y: 0.5}}
  spritePixelsToUnits: 100
  spriteBorder: {{x: {bx}, y: {by}, z: {bz}, w: {bw}}}
  spriteGenerateFallbackPhysicsShape: 1
  alphaUsage: 1
  alphaIsTransparency: 1
  spriteTilingProperty:
    border: {{x: 0, y: 0, z: 0, w: 0}}
    pivot: {{x: 0, y: 0, w: 0, h: 0}}
    oldBorder: {{x: 0, y: 0, z: 0, w: 0}}
  spriteOutline: []
  physicsShape: []
  bones: []
  spriteID: {sid}
  internalID: 0
  vertices: []
  indices: 
  edges: []
  weights: []
  secondaryTextures: []
  nameMap: []
  freeAlphas: []
  textureType: 8
  textureShape: 1
  singleChannelComponent: 0
  flipbookRows: 1
  flipbookColumns: 1
  maxTextureSizeSet: 0
  compressionQualitySet: 0
  textureFormatSet: 0
  ignorePngGamma: 0
  applyGammaDecoding: 0
  swizzle: 50462976
  cookieLightType: 0
platformSettings:
  - serializedVersion: 3
    buildTarget: DefaultTexturePlatform
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 1
    compressionQuality: 50
    crunchedCompression: 0
    allowsAlphaSplitting: 0
    overridden: 0
    ignorePlatformSupport: 0
    androidETC2FallbackOverride: 0
    forceMaximumCompressionQuality_BC6H_BC7: 0
  - serializedVersion: 3
    buildTarget: Standalone
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 1
    compressionQuality: 50
    crunchedCompression: 0
    allowsAlphaSplitting: 0
    overridden: 0
    ignorePlatformSupport: 0
    androidETC2FallbackOverride: 0
    forceMaximumCompressionQuality_BC6H_BC7: 0
  - serializedVersion: 3
    buildTarget: Android
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 1
    compressionQuality: 50
    crunchedCompression: 0
    allowsAlphaSplitting: 0
    overridden: 0
    ignorePlatformSupport: 0
    androidETC2FallbackOverride: 0
    forceMaximumCompressionQuality_BC6H_BC7: 0
spriteSheet:
  serializedVersion: 2
  sprites: []
  outline: []
  physicsShape: []
  bones: []
  spriteID: 
  internalID: 0
  vertices: []
  indices: 
  edges: []
  weights: []
  secondaryTextures: []
  nameMap: []
  freeAlphas: []
spritePackingTag: 
pSDRemapChart: 
textureImporterSettings:
  alphaIsTransparency: 1
'''


def save(im, name, border=(0, 0, 0, 0)):
    path = ART / f'{name}.png'
    im.save(path)
    # GUID 必须稳定，否则重跑脚本会让 prefab 的精灵引用全部失效。
    meta_path = ART / f'{name}.png.meta'
    old = meta_path.read_text(encoding='utf-8') if meta_path.exists() else ''
    m = re.search(r'^guid: (\w+)', old, re.M)
    sid_m = re.search(r'spriteID: (\w+)', old)
    meta = META_TEMPLATE.format(
        guid=m.group(1) if m else uuid.uuid4().hex,
        sid=sid_m.group(1) if sid_m else uuid.uuid4().hex,
        bx=border[0], by=border[1], bz=border[2], bw=border[3])
    meta_path.write_text(meta, encoding='utf-8')
    print('saved', name, im.size)


def rounded_alpha(im, radius):
    """圆角羽化：参考截图裁片自带底色，四角用圆角 mask 融掉。"""
    im = im.convert('RGBA')
    mask = Image.new('L', im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=radius, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    im.putalpha(mask)
    return im


def cut_background(im, tol=30):
    """边界泛洪去平底色：只从边缘的近似底色像素开始扩散，内部高光不受影响。"""
    im = im.convert('RGBA')
    px = im.load()
    w, h = im.size
    border = [px[x, 0][:3] for x in range(w)] + [px[x, h - 1][:3] for x in range(w)] + \
             [px[0, y][:3] for y in range(h)] + [px[w - 1, y][:3] for y in range(h)]
    bg = tuple(sum(c[i] for c in border) // len(border) for i in range(3))

    def is_bg(p):
        return abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) <= tol * 3

    alpha = Image.new('L', im.size, 255)
    a = alpha.load()
    seen = [[False] * w for _ in range(h)]
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= w or y >= h or seen[y][x]:
            continue
        seen[y][x] = True
        if not is_bg(px[x, y]):
            continue
        a[x, y] = 0
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.8))
    im.putalpha(alpha)
    bbox = alpha.getbbox()
    return im.crop(bbox) if bbox else im


# ---- 加载页背景：复用拱廊画廊干净背景，按 390:844 比例居中裁切 ----
bg = Image.open(R2 / 'bg_gallery_clean.png').convert('RGB')
tw, th = 780, 1688                     # 390x844 的 2 倍
ratio = tw / th
sw, sh = bg.size
cw = int(sh * ratio)
left = (sw - cw) // 2
bg = bg.crop((left, 0, left + cw, sh)).resize((tw, th), Image.LANCZOS)
save(bg.convert('RGB'), 'loading_bg')

# ---- 加载页 logo 卡：s1 中央圆角卡 ----
s1 = Image.open(REF / 's1.png').convert('RGB')
logo = s1.crop((120, 114, 262, 252))
save(rounded_alpha(logo, 26), 'loading_logo')

# ---- 碎心：s6，边界泛洪去奶油底 ----
s6 = Image.open(REF / 's6.png').convert('RGB')
heart = s6.crop((110, 138, 240, 224))
save(cut_background(heart), 'icon_heart_broken')

# ---- 彩旗：s5 顶部左右角（不含"完成"绶带文字）----
s5 = Image.open(REF / 's5.png').convert('RGB')
bunt = s5.crop((28, 44, 102, 100))
left_deco = cut_background(bunt)
save(left_deco, 'deco_bunting_l')
save(left_deco.transpose(Image.FLIP_LEFT_RIGHT), 'deco_bunting_r')

print('done')
