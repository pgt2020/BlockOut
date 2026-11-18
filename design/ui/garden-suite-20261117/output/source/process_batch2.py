# -*- coding: utf-8 -*-
"""第二批5张：A02对局背景(去水印补边)、A05/A06按钮换色、A07圆底座/A08绿节点(自适应色键抠图)。"""
import cv2, numpy as np, os, shutil
BASE = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output'
M = r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media'
REVIEW = BASE + r'\review'
os.makedirs(REVIEW, exist_ok=True)

def adaptive_chroma(src, dst, name):
    """自适应色键：从四角估背景色，阈值随背景偏色自动调整。"""
    im = cv2.imread(src).astype(np.float32)
    h, w = im.shape[:2]
    b, g, r = im[:,:,0], im[:,:,1], im[:,:,2]
    subj = np.maximum(g/(r+1.0), g/(b+1.0))
    # 四角背景采样
    k = 12
    corners = np.concatenate([
        subj[:k,:k].ravel(), subj[:k,-k:].ravel(), subj[-k:,:k].ravel(), subj[-k:,-k:].ravel()
    ])
    bg_level = float(np.median(corners))
    lo = bg_level + 0.10
    hi = lo + 0.18
    alpha = np.clip((subj - lo)/(hi-lo), 0, 1)
    alpha = (alpha*255).astype(np.uint8)
    alpha[alpha < 18] = 0
    alpha = cv2.GaussianBlur(alpha, (3,3), 0.5)
    # 连通域只留最大主体（清水印）
    n, labels, stats, _ = cv2.connectedComponentsWithStats((alpha>40).astype(np.uint8), 8)
    if n > 1:
        keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        alpha[labels != keep] = 0
    # despill 用实测底色中值
    bg_est = np.median(im[alpha < 10].reshape(-1,3), axis=0)
    a = alpha[...,None].astype(np.float32)/255.0
    out = np.clip((im - (1-a)*bg_est)/np.maximum(a, 0.5), 0, 255)
    out = np.where((alpha[...,None] < 25), im, out)
    rgba = np.dstack([out.astype(np.uint8), alpha])
    cv2.imwrite(dst, rgba)
    ys, xs = np.nonzero(alpha > 40)
    print(f'{name}: bg_level={bg_level:.2f} lo={lo:.2f} hi={hi:.2f} canvas={w}x{h} bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) body={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}')
    return rgba

def recolor_button(src, dst, name, top_bgr, bottom_bgr):
    """以绿按钮v02为底，只换面层颜色，几何/alpha完全不动。"""
    im = cv2.imread(src, cv2.IMREAD_UNCHANGED)  # BGRA
    b, g, r, alpha = cv2.split(im.astype(np.float32))
    # 绿色面层 mask（含软边）：G 明显高于 R 和 B
    gs = np.clip((g.astype(np.float32) - np.maximum(r,b) - 5.0)/25.0, 0, 1)
    gs[alpha < 128] = 0
    # 原面层的亮度层次（低频保留立体光影）
    gface = g.copy()
    gface[gs <= 0] = np.nan
    with np.errstate(all='ignore'):
        vlow = cv2.GaussianBlur(np.nan_to_num(gface, nan=200.0), (0,0), 12)
        vref = np.nanmean(gface)
    mod = np.clip(vlow/(vref+1e-6), 0.78, 1.18)
    # 沿Y方向的顶→底渐变
    ys, xs = np.nonzero(gs > 0.3)
    y1, y2 = ys.min(), ys.max()
    t = np.clip((np.arange(im.shape[0])[:,None] - y1)/max(y2-y1,1), 0, 1)
    top = np.array(top_bgr, np.float32); bot = np.array(bottom_bgr, np.float32)
    grad = top[None,None,:]*(1-t[...,None]) + bot[None,None,:]*t[...,None]
    grad = np.broadcast_to(grad, (im.shape[0], im.shape[1], 3)).copy()
    modulated = np.clip(grad*mod[...,None], 0, 255)
    out = im[:,:,:3]*(1-gs[...,None]) + modulated*gs[...,None]
    res = np.dstack([np.clip(out,0,255).astype(np.uint8), alpha.astype(np.uint8)])
    cv2.imwrite(dst, res)
    print(f'{name}: recolored face pixels={int((gs>0.5).sum())} y-range={y1}..{y2}')

def remove_wm_resize(src, dst, target=(1080,1920)):
    im = cv2.imread(src); h, w = im.shape[:2]
    crop = im[int(h*0.86):, int(w*0.70):]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = ((hsv[:,:,1] < 70) & (hsv[:,:,2] > 170)).astype(np.uint8)*255
    mask = cv2.dilate(mask, np.ones((5,5),np.uint8), 1)
    full = np.zeros((h,w), np.uint8); full[int(h*0.86):, int(w*0.70):] = mask
    cleaned = cv2.inpaint(im, full, 5, cv2.INPAINT_TELEA)
    scale = min(target[0]/w, target[1]/h); nw,nh = round(w*scale), round(h*scale)
    rz = cv2.resize(cleaned,(nw,nh),interpolation=cv2.INTER_LANCZOS4)
    canvas = np.zeros((target[1],target[0],3),np.uint8)
    x0,y0=(target[0]-nw)//2,(target[1]-nh)//2
    canvas[y0:y0+nh,x0:x0+nw]=rz
    cv2.imwrite(dst,canvas)
    print(f'A02 garden-play: {canvas.shape[1]}x{canvas.shape[0]} pad=({x0},{y0})')

def center_circle(src, dst, name, target_cy=120, want_d=208):
    """圆底座：检测主体，等比缩到目标直径，圆心移到(128,120)。"""
    im = cv2.imread(src, cv2.IMREAD_UNCHANGED)
    a = im[:,:,3]; ys,xs=np.nonzero(a>40)
    x1,x2,y1,y2=xs.min(),xs.max(),ys.min(),ys.max()
    body=im[y1:y2+1,x1:x2+1]
    ch,cw=body.shape[:2]
    scale=want_d/max(ch,cw)
    nw,nh=round(cw*scale),round(ch*scale)
    res=cv2.resize(body,(nw,nh),interpolation=cv2.INTER_LANCZOS4)
    canvas=np.zeros((256,256,4),np.uint8)
    x0=128-nw//2; y0=target_cy-nh//2
    x0=max(0,min(256-nw,x0)); y0=max(0,min(256-nh,y0))
    canvas[y0:y0+nh,x0:x0+nw]=res
    cv2.imwrite(dst,canvas)
    ys2,xs2=np.nonzero(canvas[:,:,3]>40)
    print(f'{name}: before {cw}x{ch} -> {nw}x{nh}, final bbox=({xs2.min()},{ys2.min()})-({xs2.max()},{ys2.max()})')
    return canvas

def preview(rgba, name):
    b,g,r,a=cv2.split(rgba); al=a.astype(np.float32)/255; h,w=a.shape
    yy,xx=np.mgrid[0:h,0:w]; chk=(((xx//24+yy//24)%2)*28+120).astype(np.uint8)
    bgs={'white':np.full((h,w,3),255,np.float32),'darkgray':np.full((h,w,3),55,np.float32),
         'lightblue':np.zeros((h,w,3),np.float32),'checker':np.dstack([chk]*3).astype(np.float32)}
    bgs['lightblue'][:,:,0]=205; bgs['lightblue'][:,:,1]=228; bgs['lightblue'][:,:,2]=245
    for bn,bg in bgs.items():
        comp=(rgba[:,:,:3].astype(np.float32)*al[...,None]+bg*(1-al[...,None])).astype(np.uint8)
        cv2.imwrite(os.path.join(REVIEW,f'{name}_{bn}.png'),comp)

# A02 对局背景
remove_wm_resize(M+r'\miora_text_to_image-1794907701661-0-dc8f70987002.png', BASE+r'\backgrounds\garden-play.png')
shutil.copy(M+r'\miora_text_to_image-1794907701661-0-dc8f70987002.png', BASE+r'\source\garden-play-source.png')

# A05 奶油按钮 top暖白 bottom浅蜂蜜(BGR)
recolor_button(BASE+r'\components\button-green_v02.png', BASE+r'\components\button-cream.png',
               'A05 button-cream', (232,246,252), (150,192,224))
# 带底原图：用绿按钮source不合适，另存成品的带底近似（在洋红底上合成）
# 审查要求保留带底原图，这里记录生成时的绿按钮source作为几何来源
shutil.copy(BASE+r'\source\button-green_v02-source.png', BASE+r'\source\button-cream-derived-from.png')

# A06 珊瑚按钮 top珊瑚 bottom深珊瑚(BGR)
recolor_button(BASE+r'\components\button-green_v02.png', BASE+r'\components\button-coral.png',
               'A06 button-coral', (110,135,250), (78,92,222))
shutil.copy(BASE+r'\source\button-green_v02-source.png', BASE+r'\source\button-coral-derived-from.png')

# A07 圆底座：先抠图再居中定尺寸
r7=adaptive_chroma(M+r'\miora_text_to_image-1794907713732-0-5cdb8f06c1ba.png',
                   BASE+r'\source\_round_raw.png','A07 raw')
shutil.copy(M+r'\miora_text_to_image-1794907713732-0-5cdb8f06c1ba.png', BASE+r'\source\round-base-source.png')
c7=center_circle(BASE+r'\source\_round_raw.png', BASE+r'\components\round-base.png','A07 round-base')
preview(c7,'round-base')

# A08 绿节点
r8=adaptive_chroma(M+r'\miora_text_to_image-1794907721800-0-780e4d5c3792.png',
                   BASE+r'\components\tile-green.png','A08 tile-green')
shutil.copy(M+r'\miora_text_to_image-1794907721800-0-780e4d5c3792.png', BASE+r'\source\tile-green-source.png')
preview(r8,'tile-green')

# A05/A06 预览
for nm in ['button-cream','button-coral']:
    preview(cv2.imread(BASE+f'\\components\\{nm}.png',cv2.IMREAD_UNCHANGED), nm)
print('DONE')
