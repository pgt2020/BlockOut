# -*- coding: utf-8 -*-
"""统一后处理：1) 用最近实心主体色替换半透明洋红残边(保alpha抗锯齿)；2) 图标尺寸归一化到最长边≈205居中。"""
import cv2, numpy as np, os
BASE = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output'
REVIEW = BASE + r'\review'

def despill_by_nearest_solid(rgba, replace_thresh=250):
    """半透明带(0<alpha<replace_thresh)颜色替换为最近实心像素色，alpha不变。"""
    b,g,r,a = cv2.split(rgba)
    solid = (a >= replace_thresh).astype(np.uint8)
    # 最近实心点标签
    dist, labels = cv2.distanceTransformWithLabels(
        (1-solid).astype(np.uint8), cv2.DIST_L2, 5,
        labelType=cv2.DIST_LABEL_PIXEL)
    # 实心像素坐标列表（label 从1开始指向第label个实心点）
    ys, xs = np.nonzero(solid)
    coord = np.stack([xs, ys], axis=1)  # [x,y]
    # labels 映射到实心点索引：label 1..N 对应 coord[label-1]
    idx = labels - 1
    valid = (idx >= 0) & (idx < len(coord))
    safe = np.clip(idx, 0, len(coord)-1)
    H,W = a.shape
    gx, gy = np.meshgrid(np.arange(W), np.arange(H))  # 逐像素自身坐标(兜底)
    nx = np.where(valid, coord[safe,0], gx)
    ny = np.where(valid, coord[safe,1], gy)
    nb = b[ny,nx]; ng = g[ny,nx]; nr = r[ny,nx]
    band = (a > 0) & (a < replace_thresh)
    out = rgba.copy()
    out[:,:,0] = np.where(band, nb, b)
    out[:,:,1] = np.where(band, ng, g)
    out[:,:,2] = np.where(band, nr, r)
    return out

def normalize_icon(rgba, target=205, canvas=256):
    a = rgba[:,:,3]; ys,xs = np.nonzero(a>40)
    if not len(xs): return rgba
    body = rgba[ys.min():ys.max()+1, xs.min():xs.max()+1]
    bh,bw = body.shape[:2]; longest=max(bh,bw)
    scale = target/longest
    nw,nh = round(bw*scale), round(bh*scale)
    res = cv2.resize(body,(nw,nh),interpolation=cv2.INTER_LANCZOS4)
    out = np.zeros((canvas,canvas,4),np.uint8)
    x0,y0=(canvas-nw)//2,(canvas-nh)//2
    out[y0:y0+nh,x0:x0+nw]=res
    return out

def preview(rgba,name):
    b,g,r,a=cv2.split(rgba); al=a.astype(np.float32)/255; h,w=a.shape
    yy,xx=np.mgrid[0:h,0:w]; chk=(((xx//24+yy//24)%2)*28+120).astype(np.uint8)
    bgs={'checker':np.dstack([chk]*3).astype(np.float32),'white':np.full((h,w,3),255,np.float32),
         'darkgray':np.full((h,w,3),55,np.float32),'lightblue':np.dstack([np.full((h,w),205,np.float32),np.full((h,w),228,np.float32),np.full((h,w),245,np.float32)])}
    for bn,bg in bgs.items():
        comp=(rgba[:,:,:3].astype(np.float32)*al[...,None]+bg*(1-al[...,None])).astype(np.uint8)
        cv2.imwrite(os.path.join(REVIEW,f'{name}_{bn}.png'),comp)

# 图标清单（256系列）
icons=['icon-hammer','icon-magic','icon-settings','icon-home','icon-levels','icon-store',
       'icon-coin','icon-heart','icon-heart-broken','icon-lock','icon-trophy']
for nm in icons:
    p=BASE+r'\icons\\'+nm+'.png'
    im=cv2.imread(p,cv2.IMREAD_UNCHANGED)
    clean=despill_by_nearest_solid(im)
    norm=normalize_icon(clean,205,256)
    cv2.imwrite(p,norm)
    preview(norm,nm)
    a=norm[:,:,3]; ys,xs=np.nonzero(a>40)
    print(f'{nm}: body {xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}')

# 画框：只despill，不改尺寸（它是组件，768）
p=BASE+r'\components\frame-art.png'
im=cv2.imread(p,cv2.IMREAD_UNCHANGED)
frame=despill_by_nearest_solid(im)
cv2.imwrite(p,frame); preview(frame,'frame-art')
print('frame-art despilled')
print('DONE')
