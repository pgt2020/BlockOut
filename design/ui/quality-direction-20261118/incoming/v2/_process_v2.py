# -*- coding: utf-8 -*-
"""v2 返工处理：native 原样留存；final 主体真透明但保留工具来源标识(右下角水印区)；
另出紧凑边距接入副本。严格不擦除/不裁掉水印，不放大不拉伸。"""
import os, json, shutil
import numpy as np
from PIL import Image, ImageDraw

BASE = r'E:/UnityProject/MutiplayGame/BlockOut/design/ui/quality-direction-20261118/incoming/v2'
MEDIA = r'C:/Users/admin/.workbuddy/plugins/data/mcp-miora/miora-media'
SRC = {
    'garden-play-hd':  MEDIA + '/miora_edit_image-1795000835754-0-d499acef8afd.png',  # 1152x2496, 目标精确0.8倍
    'garden-play-alt': MEDIA + '/miora_edit_image-1795000819890-0-bb3406a00f3a.png',  # 1280x2560 备选
    'icon-hint-hd':    MEDIA + '/miora_edit_image-1795000762322-0-b8e0c05a99af.png',
    'icon-hammer-hd':  MEDIA + '/miora_edit_image-1795000776198-0-53c18a9c49eb.png',
    'icon-magic-hd':   MEDIA + '/miora_edit_image-1795000788304-0-e3f9610b6e64.png',
}
STATS = {}
os.makedirs(BASE + '/native', exist_ok=True)
os.makedirs(BASE + '/final', exist_ok=True)

for name, p in SRC.items():
    shutil.copy2(p, BASE + '/native/%s.png' % name)
    im = Image.open(p)
    STATS[name] = {'native_size': list(im.size), 'native_mode': im.mode,
                   'native_file': 'native/%s.png' % name}

# ---------- 图标：主体真透明 + 右下角水印区保留 ----------
def subject_alpha(a):
    """色度判据：中性灰棋盘格->透明，暖色主体保留。"""
    chroma = a.max(2) - a.min(2)
    bright = a.mean(2)
    alpha_c = np.clip((chroma - 10.0) / 12.0, 0, 1)
    alpha_d = np.clip((150.0 - bright) / 25.0, 0, 1)   # 深色阴影保护
    return np.maximum(alpha_c, alpha_d)

def build_icon(path, ratio, keep_watermark=True):
    im = Image.open(path).convert('RGB')
    a = np.array(im).astype(np.int16)
    h, w, _ = a.shape
    alpha = subject_alpha(a)
    # 右下角水印区：原生像素原样保留(不抠不改)，确保工具来源标识完整可见。
    # 工具无透明/无水印导出能力，按返工单第3条不得擦除标识，故该小区块保留原生棋盘格底。
    wm_box = (int(w*0.80), int(h*0.905), w, h)
    rgba = Image.fromarray(np.dstack([a.astype(np.uint8), (alpha*255).astype(np.uint8)]), 'RGBA')
    # 主体重排布（水印在背景区，不随主体缩放）
    mask = rgba.getchannel('A').point(lambda v: 255 if v > 40 else 0)
    # 只取中央主体 bbox：排除右下角水印区
    arr = np.array(mask)
    arr[wm_box[1]:, wm_box[0]:] = 0
    mask = Image.fromarray(arr)
    bbox = mask.getbbox()
    sub = rgba.crop(bbox)
    target = 768 * ratio
    s = target / max(sub.size)
    new = (max(1, round(sub.width*s)), max(1, round(sub.height*s)))
    sub = sub.resize(new, Image.LANCZOS)
    canvas = Image.new('RGBA', (768,768), (0,0,0,0))
    canvas.paste(sub, ((768-new[0])//2, (768-new[1])//2), sub)
    if keep_watermark:
        # 原样贴回含水印的原生像素块(alpha=255)，标识与棋盘格底一并保留，不擦不裁
        wm_native = im.crop(wm_box).convert('RGBA')
        canvas.alpha_composite(wm_native, (wm_box[0], wm_box[1]))
    return canvas, list(bbox), round(s,4), new

ICONS = {'icon-hint-hd': 0.78, 'icon-hammer-hd': 0.80, 'icon-magic-hd': 0.80}
TIGHT  = {'icon-hint-hd': 0.92, 'icon-hammer-hd': 0.92, 'icon-magic-hd': 0.92}
finals, tight = {}, {}
for name, ratio in ICONS.items():
    out, bbox, scale, new = build_icon(SRC[name], ratio, True)
    dst = BASE + '/final/%s.png' % name
    out.save(dst)
    finals[name] = out
    t_out, tb, ts, tn = build_icon(SRC[name], TIGHT[name], True)
    t_dst = BASE + '/final/%s-tight.png' % name
    t_out.save(t_dst)
    tight[name] = t_out
    ar = np.array(out.getchannel('A'))
    STATS[name].update({
        'final_size': list(out.size), 'final_mode': 'RGBA',
        'process': '主体色度抠图->真透明；右下角水印区用颜色距离判据保留工具标识(候选图)',
        'native_subject_bbox': bbox, 'subject_scale': scale, 'subject_final_px': new,
        'subject_long_side_ratio': round(max(new)/768,4),
        'tight_subject_ratio': round(max(tn)/768,4),
        'tight_subject_px': list(tn),
        'transparent_pct': round(float((ar==0).mean()*100),1),
        'watermark_retained': True,
        'final_file': 'final/%s.png' % name,
        'tight_file': 'final/%s-tight.png' % name,
    })

# 背景：原样，不放大/拉伸/裁切
shutil.copy2(SRC['garden-play-hd'], BASE + '/final/garden-play-hd.png')
shutil.copy2(SRC['garden-play-alt'], BASE + '/final/garden-play-alt-1280x2560.png')
for n, f in [('garden-play-hd','final/garden-play-hd.png'),
             ('garden-play-alt','final/garden-play-alt-1280x2560.png')]:
    STATS[n].update({'final_size': STATS[n]['native_size'], 'final_mode':'RGB',
                     'process':'原生原样复制，未放大/拉伸/裁切', 'final_file': f})

# ---------- 检查总览：48 / 28 标准+紧凑，浅底合成 ----------
cell, pad = 118, 14
W = pad*2 + 3*cell
H = 30 + 48 + 16 + 28 + pad
board = Image.new('RGB', (W,H), (255,255,255))
d = ImageDraw.Draw(board)
for i,n in enumerate(ICONS):
    x = pad + i*cell
    d.text((x+18,4), n.replace('icon-','').replace('-hd',''), fill=(60,52,43))
    for y0,sz,obj,lab in ((30,48,finals[n],'48'),(30+48+16,28,tight[n],'28紧')):
        th = obj.resize((sz,sz), Image.LANCZOS)
        bg = Image.new('RGBA',(sz,sz),(255,255,255,255)); bg.alpha_composite(th)
        board.paste(bg.convert('RGB'),(x+(cell-sz)//2,y0))
        d.text((x+(cell-24)//2, y0+sz+1), lab, fill=(120,110,100))
board.save(BASE + '/icon-size-check.png')

for name in SRC:
    for sub,f in [('native',name+'.png'),('final', STATS[name].get('final_file','final/'+name+'.png').split('/')[-1])]:
        p = BASE+'/'+sub+'/'+f
        im=Image.open(p); im.load()
print(json.dumps(STATS, ensure_ascii=False, indent=2))
