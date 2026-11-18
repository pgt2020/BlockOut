# -*- coding: utf-8 -*-
"""第三批：返工背景/圆底座 + 剩余16张必做 + A26角色。
全部用自适应色键抠图；换色件保持母版alpha几何一致；碎心基于爱心加透明裂缝。"""
import cv2, numpy as np, os, shutil
BASE = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output'
M = r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media'
REVIEW = BASE + r'\review'
os.makedirs(REVIEW, exist_ok=True)

def adaptive_chroma(src, dst, name, save_src=True):
    """自适应色键：从四角估背景偏色，阈值自动调整；连通域只留最大主体清水印；实测底色despill。"""
    im = cv2.imread(src).astype(np.float32)
    h, w = im.shape[:2]
    b, g, r = im[:,:,0], im[:,:,1], im[:,:,2]
    subj = np.maximum(g/(r+1.0), g/(b+1.0))
    k = 12
    corners = np.concatenate([subj[:k,:k].ravel(), subj[:k,-k:].ravel(),
                              subj[-k:,:k].ravel(), subj[-k:,-k:].ravel()])
    bg_level = float(np.median(corners))
    lo = bg_level + 0.10
    hi = lo + 0.18
    alpha = np.clip((subj-lo)/(hi-lo), 0, 1)
    alpha = (alpha*255).astype(np.uint8)
    alpha[alpha < 18] = 0
    alpha = cv2.GaussianBlur(alpha, (3,3), 0.5)
    n, labels, stats, _ = cv2.connectedComponentsWithStats((alpha>40).astype(np.uint8), 8)
    if n > 1:
        keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        alpha[labels != keep] = 0
    bg_est = np.median(im[alpha < 10].reshape(-1,3), axis=0)
    a = alpha[...,None].astype(np.float32)/255.0
    out = np.clip((im-(1-a)*bg_est)/np.maximum(a,0.5), 0, 255)
    out = np.where((alpha[...,None] < 25), im, out)
    rgba = np.dstack([out.astype(np.uint8), alpha])
    cv2.imwrite(dst, rgba)
    if save_src:
        shutil.copy(src, BASE + r'\source\\' + os.path.basename(dst).replace('.png','-source.png'))
    ys, xs = np.nonzero(alpha > 40)
    if len(xs):
        print(f'{name}: bg={bg_level:.2f} bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) body={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1} canvas={w}x{h}')
    else:
        print(f'{name}: WARNING empty alpha!')
    return rgba

def preview(rgba, name):
    b,g,r,a=cv2.split(rgba); al=a.astype(np.float32)/255; h,w=a.shape
    yy,xx=np.mgrid[0:h,0:w]; chk=(((xx//24+yy//24)%2)*28+120).astype(np.uint8)
    bgs={'white':np.full((h,w,3),255,np.float32),'darkgray':np.full((h,w,3),55,np.float32),
         'lightblue':np.zeros((h,w,3),np.float32),'checker':np.dstack([chk]*3).astype(np.float32)}
    bgs['lightblue'][:,:,0]=205; bgs['lightblue'][:,:,1]=228; bgs['lightblue'][:,:,2]=245
    for bn,bg in bgs.items():
        comp=(rgba[:,:,:3].astype(np.float32)*al[...,None]+bg*(1-al[...,None])).astype(np.uint8)
        cv2.imwrite(os.path.join(REVIEW,f'{name}_{bn}.png'),comp)

def remove_wm_resize(src, dst, target=(1080,1920)):
    im=cv2.imread(src); h,w=im.shape[:2]
    crop=im[int(h*0.86):, int(w*0.70):]
    hsv=cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask=((hsv[:,:,1]<70)&(hsv[:,:,2]>170)).astype(np.uint8)*255
    mask=cv2.dilate(mask, np.ones((5,5),np.uint8),1)
    full=np.zeros((h,w),np.uint8); full[int(h*0.86):,int(w*0.70):]=mask
    cleaned=cv2.inpaint(im, full, 5, cv2.INPAINT_TELEA)
    scale=min(target[0]/w, target[1]/h); nw,nh=round(w*scale),round(h*scale)
    rz=cv2.resize(cleaned,(nw,nh),interpolation=cv2.INTER_LANCZOS4)
    canvas=np.zeros((target[1],target[0],3),np.uint8)
    x0,y0=(target[0]-nw)//2,(target[1]-nh)//2
    canvas[y0:y0+nh,x0:x0+nw]=rz
    cv2.imwrite(dst,canvas)
    print(f'garden-play_v02: {canvas.shape[1]}x{canvas.shape[0]} pad=({x0},{y0})')

def recolor_face(src, dst, name, top_bgr, bottom_bgr):
    """以绿节点为底，只换绿色面层颜色，alpha/几何完全不动。"""
    im=cv2.imread(src, cv2.IMREAD_UNCHANGED)
    b,g,r,alpha=cv2.split(im.astype(np.float32))
    gs=np.clip((g-np.maximum(r,b)-5.0)/25.0,0,1)
    gs[alpha<128]=0
    gface=g.copy(); gface[gs<=0]=np.nan
    with np.errstate(all='ignore'):
        vlow=cv2.GaussianBlur(np.nan_to_num(gface,nan=150.0),(0,0),9)
        vref=np.nanmean(gface)
    mod=np.clip(vlow/(vref+1e-6),0.80,1.18)
    ys,xs=np.nonzero(gs>0.3); y1,y2=ys.min(),ys.max()
    t=np.clip((np.arange(im.shape[0])[:,None]-y1)/max(y2-y1,1),0,1)
    top=np.array(top_bgr,np.float32); bot=np.array(bottom_bgr,np.float32)
    grad=top[None,None,:]*(1-t[...,None])+bot[None,None,:]*t[...,None]
    grad=np.broadcast_to(grad,(im.shape[0],im.shape[1],3)).copy()
    modulated=np.clip(grad*mod[...,None],0,255)
    out=im[:,:,:3]*(1-gs[...,None])+modulated*gs[...,None]
    res=np.dstack([np.clip(out,0,255).astype(np.uint8),alpha.astype(np.uint8)])
    cv2.imwrite(dst,res)
    print(f'{name}: recolored face px={int((gs>0.5).sum())}')
    return res

def fix_round_base(src, dst, name):
    """圆底座局部修色：粉紫环带→奶油金；高饱和橙金细线降饱和；几何/alpha完全不动。"""
    im=cv2.imread(src,cv2.IMREAD_UNCHANGED).astype(np.float32)
    b,g,r,a=cv2.split(im); h,w=a.shape[:2]; yy,xx=np.mgrid[0:h,0:w]
    d=np.sqrt((xx-128)**2+(yy-120)**2)
    ring=(d>76)&(d<108)&(a>60)
    pink=(r>g+16)&(b>g+6)&ring
    target=np.array([176,212,234],np.float32)  # 目标奶油金 BGR
    lum_full=0.114*b+0.587*g+0.299*r
    tlum=float(0.114*target[0]+0.587*target[1]+0.299*target[2])
    B2,G2,R2=b.copy(),g.copy(),r.copy()
    ratio=np.clip(lum_full[pink]/(tlum+1e-6),0.72,1.12)
    for i,ch in enumerate([B2,G2,R2]):
        ch[pink]=np.clip(target[i]*ratio,0,255)
    sat=np.maximum.reduce([b,g,r])-np.minimum.reduce([b,g,r])
    goldline=(sat>52)&(~pink)&ring
    for i,ch in enumerate([B2,G2,R2]):
        ch[goldline]=ch[goldline]*0.68+target[i]*0.32
    out=np.dstack([B2,G2,R2,a])
    cv2.imwrite(dst,np.clip(out,0,255).astype(np.uint8))
    print(f'{name}: pink fixed={int(pink.sum())} goldline softened={int(goldline.sum())}')
    return np.clip(out,0,255).astype(np.uint8)

def make_broken_heart(src_rgba, dst, name):
    """基于完整爱心加一条中央窄锯齿裂缝(alpha=0)，几何其余不动。"""
    im=src_rgba.copy()
    h,w=im.shape[:2]; a=im[:,:,3]
    ys,xs=np.nonzero(a>60); x1,x2,y1,y2=xs.min(),xs.max(),ys.min(),ys.max()
    cy=(y1+y2)//2; cx=(x1+x2)//2
    # 锯齿裂缝：从顶部偏左到底部偏右，之字形
    pts=[]
    yy0,yy1=int(y1+h*0.12),int(y2-h*0.10)
    nseg=9
    for i in range(nseg+1):
        yy=int(yy0+(yy1-yy0)*i/nseg)
        zig = cx + (-1)**i * int(w*0.035)
        pts.append([zig,yy])
    pts=np.array(pts,np.int32)
    crack=np.zeros((h,w),np.uint8)
    cv2.polylines(crack,[pts],False,255,3,cv2.LINE_AA)
    # 只在爱心内部开缝
    crack[(a<80)]=0
    im[:,:,3][crack>0]=0
    cv2.imwrite(dst,im)
    print(f'{name}: crack pixels={int((crack>0).sum())}')

def resize_pill(rgba, dst, name, target=(512,160)):
    """等比缩放+透明补边到目标画布，不拉伸。"""
    a=rgba[:,:,3]; ys,xs=np.nonzero(a>40)
    body=rgba[ys.min():ys.max()+1, xs.min():xs.max()+1]
    bh,bw=body.shape[:2]
    scale=min(target[0]/bw, target[1]/bh)
    nw,nh=round(bw*scale),round(bh*scale)
    res=cv2.resize(body,(nw,nh),interpolation=cv2.INTER_LANCZOS4)
    canvas=np.zeros((target[1],target[0],4),np.uint8)
    x0,y0=(target[0]-nw)//2,(target[1]-nh)//2
    canvas[y0:y0+nh,x0:x0+nw]=res
    cv2.imwrite(dst,canvas)
    print(f'{name}: body {bw}x{bh} -> {nw}x{nh} pad=({x0},{y0}) canvas={target}')
    return canvas

print('=== 返工背景 ===')
remove_wm_resize(M+r'\miora_text_to_image-1794909146071-0-9ad9ecdf0004.png', BASE+r'\backgrounds\garden-play_v02.png')
shutil.copy(M+r'\miora_text_to_image-1794909146071-0-9ad9ecdf0004.png', BASE+r'\source\garden-play_v02-source.png')

print('=== 返工圆底座(局部修色) ===')
r=fix_round_base(BASE+r'\components\round-base.png', BASE+r'\components\round-base_v02.png','round-base_v02')
preview(r,'round-base_v02')

print('=== A09/A10 节点换色 ===')
r9=recolor_face(BASE+r'\components\tile-green.png', BASE+r'\components\tile-grey.png','A09 tile-grey',
                (168,170,178),(120,124,134))   # 暖灰 BGR
r10=recolor_face(BASE+r'\components\tile-green.png', BASE+r'\components\tile-purple.png','A10 tile-purple',
                 (198,150,224),(150,104,182))  # 柔和紫 BGR
preview(r9,'tile-grey'); preview(r10,'tile-purple')

print('=== A11画框 / A12横幅 / A13胶囊 ===')
r11=adaptive_chroma(M+r'\miora_text_to_image-1794908839366-0-4ee29a3367c7.png', BASE+r'\components\frame-art.png','A11 frame-art')
preview(r11,'frame-art')
r12=adaptive_chroma(M+r'\miora_text_to_image-1794908856024-0-c68842dfc9e8.png', BASE+r'\components\ribbon-coral.png','A12 ribbon-coral')
preview(r12,'ribbon-coral')
pill_raw=adaptive_chroma(M+r'\miora_text_to_image-1794908877825-0-f9efc43807c2.png', BASE+r'\source\_pill_raw.png','A13 pill raw')
r13=resize_pill(pill_raw, BASE+r'\components\pill-cream.png','A13 pill-cream')
preview(r13,'pill-cream')

print('=== 图标 A15-A22, A24-A25 ===')
icons={
 'A15 hammer':'miora_text_to_image-1794908927625-0-b792d904cc94.png',
 'A16 magic':'miora_text_to_image-1794908944709-0-b480e7b4453f.png',
 'A17 settings':'miora_text_to_image-1794908958532-0-76628d71fd5c.png',
 'A18 home':'miora_text_to_image-1794908976319-0-33d959e999d2.png',
 'A19 levels':'miora_text_to_image-1794908991294-0-9e39ec456bee.png',
 'A20 store':'miora_text_to_image-1794909006437-0-4f1d4d8b7875.png',
 'A21 coin':'miora_text_to_image-1794909022017-0-c002b4f056b9.png',
 'A22 heart':'miora_text_to_image-1794909040181-0-40abf0818eb1.png',
 'A24 lock':'miora_text_to_image-1794909057498-0-51c0a4fa55df.png',
 'A25 trophy':'miora_text_to_image-1794909075326-0-e48307dec642.png',
}
name2file={'hammer':'icon-hammer','magic':'icon-magic','settings':'icon-settings','home':'icon-home',
 'levels':'icon-levels','store':'icon-store','coin':'icon-coin','heart':'icon-heart','lock':'icon-lock','trophy':'icon-trophy'}
heart_rgba=None
for key,fn in icons.items():
    tag,short=key.split(' ')
    dst=BASE+r'\icons\\'+name2file[short]+'.png'
    rr=adaptive_chroma(M+'\\'+fn, dst, key)
    preview(rr,name2file[short])
    if short=='heart': heart_rgba=rr

print('=== A23 碎心(基于爱心) ===')
make_broken_heart(heart_rgba, BASE+r'\icons\icon-heart-broken.png','A23 heart-broken')
preview(cv2.imread(BASE+r'\icons\icon-heart-broken.png',cv2.IMREAD_UNCHANGED),'icon-heart-broken')

print('=== A26 角色 ===')
r26=adaptive_chroma(M+r'\miora_text_to_image-1794909090047-0-2f7e5b94f184.png', BASE+r'\optional\mascot.png','A26 mascot')
preview(r26,'mascot')
print('DONE')
