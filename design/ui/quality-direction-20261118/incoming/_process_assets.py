# -*- coding: utf-8 -*-
"""按任务书处理第一批 4 张生成素材：native 原样留存，final 做棋盘格->真透明抠图与主体重排布。
v2：用色度(chroma)判据分离中性灰棋盘格与暖色主体，清除棋盘格残留线与右下角水印。
"""
import os, json, shutil
import numpy as np
from PIL import Image, ImageDraw

BASE = r'E:/UnityProject/MutiplayGame/BlockOut/design/ui/quality-direction-20261118/incoming'
MEDIA = r'C:/Users/admin/.workbuddy/plugins/data/mcp-miora/miora-media'
SRC = {
    'garden-play-hd': MEDIA + '/miora_edit_image-1794999721413-0-94f51ed94f2d.png',
    'icon-hint-hd':   MEDIA + '/miora_edit_image-1794999685918-0-d4003f1cdee6.png',
    'icon-hammer-hd': MEDIA + '/miora_edit_image-1794999761006-0-1200a73d4522.png',
    'icon-magic-hd':  MEDIA + '/miora_edit_image-1794999774910-0-18f6548d0b6d.png',
}
STATS = {}

os.makedirs(BASE + '/native', exist_ok=True)
os.makedirs(BASE + '/final', exist_ok=True)

for name, p in SRC.items():
    dst = BASE + '/native/%s.png' % name
    shutil.copy2(p, dst)
    im = Image.open(p)
    STATS[name] = {'native_size': list(im.size), 'native_mode': im.mode}

def keyout(path):
    im = Image.open(path).convert('RGB')
    a = np.array(im).astype(np.int16)
    mx = a.max(2); mn = a.min(2)
    chroma = mx - mn                      # 中性灰=0；暖色物体高
    bright = a.mean(2)
    # 中性灰棋盘格与水印：色度≈0 -> 透明；暖色主体色度>22 -> 不透明
    alpha_c = np.clip((chroma - 10.0) / 12.0, 0, 1)
    # 保护深色阴影（低亮度即便中性也保留），本批物体均暖色，此项几乎不触发
    alpha_d = np.clip((150.0 - bright) / 25.0, 0, 1)
    alpha = np.maximum(alpha_c, alpha_d) * 255
    rgba = np.dstack([a.astype(np.uint8), alpha.astype(np.uint8)])
    return Image.fromarray(rgba, 'RGBA'), round(float((alpha == 0).mean() * 100), 1)

def recompose(im, ratio):
    mask = im.getchannel('A').point(lambda v: 255 if v > 40 else 0)
    bbox = mask.getbbox()
    sub = im.crop(bbox)
    target = 768 * ratio
    s = target / max(sub.size)
    new = (max(1, round(sub.width * s)), max(1, round(sub.height * s)))
    sub = sub.resize(new, Image.LANCZOS)
    canvas = Image.new('RGBA', (768, 768), (0, 0, 0, 0))
    canvas.paste(sub, ((768 - new[0]) // 2, (768 - new[1]) // 2), sub)
    return canvas, list(bbox), round(s, 4), new

ICONS = {'icon-hint-hd': 0.78, 'icon-hammer-hd': 0.80, 'icon-magic-hd': 0.80}
finals = {}
for name, ratio in ICONS.items():
    rgba, native_transparent_pct = keyout(SRC[name])
    out, bbox, scale, newsize = recompose(rgba, ratio)
    dst = BASE + '/final/%s.png' % name
    out.save(dst)
    ar = np.array(out.getchannel('A'))
    STATS[name].update({
        'final_size': list(out.size), 'final_mode': out.mode,
        'method': '色度判据抠图(中性灰棋盘格/水印->透明, 暖色主体保留)',
        'native_transparent_pct': native_transparent_pct,
        'native_subject_bbox': bbox, 'subject_scale': scale,
        'subject_final_px': newsize,
        'subject_long_side_ratio': round(max(newsize) / 768, 4),
        'transparent_pct': round(float((ar == 0).mean() * 100), 1),
        'final_saved': os.path.exists(dst),
    })
    finals[name] = out
    keyout(BASE + '/native/%s.png' % name)
    # 保存中间抠图供核对
    rgba2, _ = keyout(SRC[name])
    rgba2.save(BASE + '/native/%s.keyed-preview.png' % name)

shutil.copy2(SRC['garden-play-hd'], BASE + '/final/garden-play-hd.png')
STATS['garden-play-hd'].update({
    'final_size': STATS['garden-play-hd']['native_size'],
    'final_mode': 'RGB', 'process': '原样复制，未放大/未拉伸（工具不支持1440x3120）',
    'final_saved': os.path.exists(BASE + '/final/garden-play-hd.png'),
})

cell, pad, label = 130, 16, 26
W = pad + 3 * cell + pad
H = label + 48 + 18 + 96 + pad + label
board = Image.new('RGB', (W, H), (255, 255, 255))
d = ImageDraw.Draw(board)
names = ['icon-hint-hd', 'icon-hammer-hd', 'icon-magic-hd']
for i, n in enumerate(names):
    x = pad + i * cell
    d.text((x + 30, 6), n.replace('-hd', ''), fill=(60, 52, 43))
    for y0, sz in ((label, 48), (label + 48 + 18, 96)):
        thumb = finals[n].resize((sz, sz), Image.LANCZOS)
        bg = Image.new('RGBA', (sz, sz), (255, 255, 255, 255))
        bg.alpha_composite(thumb)
        board.paste(bg.convert('RGB'), (x + (cell - sz) // 2, y0))
    d.text((x + 40, label + 48 + 2), '48', fill=(120, 110, 100))
    d.text((x + 30, label + 48 + 18 + 96 + 2), '96', fill=(120, 110, 100))
board.save(BASE + '/icon-size-check.png')

for name in SRC:
    for sub in ('native', 'final'):
        p = BASE + '/%s/%s.png' % (sub, name)
        im = Image.open(p); im.load()
print(json.dumps(STATS, ensure_ascii=False, indent=2))
