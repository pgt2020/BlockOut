# -*- coding: utf-8 -*-
"""母版 v02 处理：统一色键判据抠透明 + 严格去色边 + 报告真实包围盒 + 三底预览。"""
import cv2, numpy as np, os, shutil
from PIL import Image

BASE = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output'
M = r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media'
REVIEW = BASE + r'\review'
os.makedirs(REVIEW, exist_ok=True)

# 生成稿 -> (透明成品, 带底原图, 期望尺寸)
JOBS = [
    ('miora_text_to_image-1794907129021-0-293ea87477da.png',
     BASE + r'\components\panel-cream_v02.png', 'panel-cream_v02', (768,1024)),
    ('miora_text_to_image-1794907203095-0-4e96e2fb6de6.png',
     BASE + r'\components\button-green_v02.png', 'button-green_v02', (768,256)),
    ('miora_text_to_image-1794907213420-0-39206d34da84.png',
     BASE + r'\icons\icon-hint_v02.png', 'icon-hint_v02', (256,256)),
]

def chroma_key(src, expect):
    im = cv2.imread(src).astype(np.float32)  # BGR
    b, g, r = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    # 主体判据：max(G/R, G/B)。背景洋红最高约 0.54，主体金色最低约 0.9
    subj = np.maximum(g/(r+1.0), g/(b+1.0))
    alpha = np.clip((subj - 0.62) / 0.20, 0, 1)
    alpha = (alpha*255).astype(np.uint8)
    # 低 alpha 直接归零，杜绝残点/毛刺（审查重点）
    alpha[alpha < 18] = 0
    alpha = cv2.GaussianBlur(alpha, (3,3), 0.5)
    # 连通域只留最大主体，清掉水印文字等误判块
    n, labels, stats, _ = cv2.connectedComponentsWithStats((alpha>40).astype(np.uint8), 8)
    if n > 1:
        keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        alpha[labels != keep] = 0
    # despill：用实测洋红(均值)中和半透明边缘残色；下限 0.5，防止放大噪点产生粉橙边
    bg_est = np.median(im[alpha < 10].reshape(-1,3), axis=0)  # BGR 实测底色
    a = alpha[..., None].astype(np.float32)/255.0
    denom = np.maximum(a, 0.5)
    out = np.clip((im - (1-a)*bg_est)/denom, 0, 255)
    # 极低 alpha 区域直接沿用底色，避免脏边
    out = np.where((alpha[..., None] < 25), im, out)
    rgba = np.dstack([out.astype(np.uint8), alpha])
    return rgba, bg_est

def bbox(alpha, thr=40):
    ys, xs = np.nonzero(alpha > thr)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))

def make_preview(rgba, name):
    b,g,r,a = cv2.split(rgba)
    al = a.astype(np.float32)/255
    h,w = a.shape
    yy,xx = np.mgrid[0:h,0:w]
    chk = (((xx//24+yy//24)%2)*28+120).astype(np.uint8)
    checker = np.dstack([chk]*3).astype(np.float32)
    bgs = {
        'white': np.full((h,w,3), 255, np.float32),
        'darkgray': np.full((h,w,3), 55, np.float32),
        'lightblue': np.zeros((h,w,3), np.float32),
    }
    bgs['lightblue'][:,:,0] = 205; bgs['lightblue'][:,:,1]=228; bgs['lightblue'][:,:,2]=245
    for bn, bg in bgs.items():
        comp = (rgba[:,:,:3].astype(np.float32)*al[...,None] + bg*(1-al[...,None])).astype(np.uint8)
        cv2.imwrite(os.path.join(REVIEW, f'{name}_{bn}.png'), comp)
    # 棋盘透明预览
    comp = (rgba[:,:,:3].astype(np.float32)*al[...,None] + checker*(1-al[...,None])).astype(np.uint8)
    cv2.imwrite(os.path.join(REVIEW, f'{name}_checker.png'), comp)

for fn, dst, name, expect in JOBS:
    rgba, bg_est = chroma_key(M + '\\' + fn, expect)
    cv2.imwrite(dst, rgba)
    shutil.copy(M + '\\' + fn, BASE + r'\source' + f'\\{name}-source.png')
    x1,y1,x2,y2 = bbox(rgba[:,:,3])
    bw,bh = x2-x1+1, y2-y1+1
    print(f'{name}: canvas {expect[0]}x{expect[1]}  bbox=({x1},{y1})-({x2},{y2})  body={bw}x{bh}  ratio={bw/bh:.2f}  fill={bw*bh/(expect[0]*expect[1])*100:.0f}%  bg_est(BGR)={bg_est.round().astype(int).tolist()}')
    make_preview(rgba, name)
print('DONE -> review', REVIEW)
