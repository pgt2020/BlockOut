# -*- coding: utf-8 -*-
"""母版处理：A01 去水印+resize；A03/A04/A14 洋红底色度键抠透明。"""
import cv2, numpy as np
from PIL import Image

BASE = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output'
SRC = BASE + r'\source'
M = r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media'

def remove_watermark_a01(src, dst, target=(1080, 1920)):
    im = cv2.imread(src)
    h, w = im.shape[:2]
    # 水印位于右下角，检测高亮低饱和的白色文字像素
    crop = im[int(h*0.86):, int(w*0.70):]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    H, S, V = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
    mask = ((S < 70) & (V > 170)).astype(np.uint8) * 255
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)
    full = np.zeros((h, w), np.uint8)
    full[int(h*0.86):, int(w*0.70):] = mask
    cleaned = cv2.inpaint(im, full, 5, cv2.INPAINT_TELEA)
    # resize 保持比例后居中补到目标尺寸（不拉伸）
    ch, cw = cleaned.shape[:2]
    scale = min(target[0]/cw, target[1]/ch)
    nw, nh = round(cw*scale), round(ch*scale)
    resized = cv2.resize(cleaned, (nw, nh), interpolation=cv2.INTER_LANCZOS4)
    canvas = np.zeros((target[1], target[0], 3), np.uint8)
    x0, y0 = (target[0]-nw)//2, (target[1]-nh)//2
    canvas[y0:y0+nh, x0:x0+nw] = resized
    cv2.imwrite(dst, canvas)
    print('A01 ->', dst, canvas.shape, 'pad', (x0, y0))

def chroma_key(src, dst, desc):
    im = cv2.imread(src).astype(np.float32)  # BGR
    b, g, r = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    gr = g/(r+1.0); gb = g/(b+1.0)
    # 主体判据：奶油/绿/金 —— G/R 或 G/B 明显偏高
    subj = np.maximum(gr, gb)
    # alpha：0=背景, 255=主体；渐变羽化带
    alpha = np.clip((subj-0.30)/0.16, 0, 1)
    # 高亮奶油/白中心即便 G/R 高也应实心；绿色主体实心底
    alpha = (alpha*255).astype(np.uint8)
    # 轻微羽化平滑边缘
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.6)
    # 连通域过滤：只保留主体（最大连通块），清除远处误判的水印文字小块
    n, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 40).astype(np.uint8), 8)
    if n > 1:
        areas = stats[1:, cv2.CC_STAT_AREA]
        keep = 1 + int(np.argmax(areas))
        alpha[labels != keep] = 0
    # despill：去掉半透明边缘残留的品红，用邻近主体色中和
    out = im
    mag = np.array([185, 30, 215], np.float32)  # BGR 品红近似
    a = alpha[..., None].astype(np.float32)/255.0
    out = np.clip((out - (1-a)*mag)/np.maximum(a, 0.15), 0, 255)
    rgba = np.dstack([out.astype(np.uint8), alpha])
    cv2.imwrite(dst, rgba)
    # 统计
    vis = int((alpha > 8).sum()); tot = alpha.size
    print(f'{desc} -> {dst}  alpha>8: {vis*100/tot:.1f}%  fully-opaque: {int((alpha>250).sum())*100/tot:.1f}%')

# A01 去水印 + 尺寸
remove_watermark_a01(
    M + r'\miora_text_to_image-1794906093113-0-17c60135cb33.png',
    BASE + r'\backgrounds\garden-home.png')

# 带底原图另存（正式素材不混带底图）
import shutil
pairs = [
    ('miora_text_to_image-1794906327443-0-ef432032dba0.png', 'panel-cream', 'A03面板'),
    ('miora_text_to_image-1794906341958-0-5cd9f23bad75.png', 'button-green', 'A04绿按钮'),
    ('miora_text_to_image-1794906359164-0-b972d05323d9.png', 'icon-hint', 'A14灯泡'),
]
for fn, name, desc in pairs:
    shutil.copy(M + '\\' + fn, SRC + f'\\{name}-source.png')

chroma_key(M + r'\miora_text_to_image-1794906327443-0-ef432032dba0.png', BASE + r'\components\panel-cream.png', 'A03面板')
chroma_key(M + r'\miora_text_to_image-1794906341958-0-5cd9f23bad75.png', BASE + r'\components\button-green.png', 'A04绿按钮')
chroma_key(M + r'\miora_text_to_image-1794906359164-0-b972d05323d9.png', BASE + r'\icons\icon-hint.png', 'A14灯泡')
print('DONE')
