# -*- coding: utf-8 -*-
"""
BlockOut TapAway 设计稿 v10 —— 严格对齐第一版原图风格
核心修正：真实3D场景背景 + 厚软胶UI浮层（高光/暗边/同色描边/柔投影）
不是 v9 那种程序化点阵底 + 扁平卡片。
9屏对应第一版拼图：加载/主页/图库/游戏/结算/失败/皮肤/每日/地图关卡
输出 UI_v10/screens/，不接入 Unity、未编译未运行。
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
BGDIR = os.path.join(HERE, "bg")
OUT = os.path.join(HERE, "screens")
os.makedirs(OUT, exist_ok=True)

W, H = 720, 1560
FB = r"C:\Windows\Fonts\msyhbd.ttc"
FR = r"C:\Windows\Fonts\msyh.ttc"

def font(sz, bold=True):
    try: return ImageFont.truetype(FB if bold else FR, max(8, int(sz)))
    except Exception: return ImageFont.load_default()

def text(d, xy, s, sz, fill, stroke=None, sw=2, bold=True, anchor="mm", sh=False):
    f = font(sz, bold); kw = dict(font=f, fill=fill, anchor=anchor)
    if stroke: kw.update(stroke_width=sw, stroke_fill=stroke)
    if sh: d.text((xy[0]+2, xy[1]+3), s, font=f, fill=(120,80,40,110), anchor=anchor)
    d.text(xy, s, **kw)

def load_bg(name):
    """裁掉右下角AI生成水印区（底部约6%），再铺满。"""
    p = os.path.join(BGDIR, name)
    im = Image.open(p).convert("RGBA")
    w, h = im.size
    im = im.crop((0, 0, w, int(h * 0.94)))
    return im.resize((W, H), Image.LANCZOS)

GARDEN = None
GALLERY = None
def init_bg():
    global GARDEN, GALLERY
    GARDEN = load_bg("Vertical_mobile_game_backgroun_2026-11-16T07-30-06.png")
    GALLERY = load_bg("Vertical_mobile_game_loading_s_2026-11-16T07-30-35.png")

def icon_heart(d, cx, cy, sz, col, stroke=None):
    """参数方程画饱满爱心。"""
    import math
    pts=[]
    for a in np.linspace(0, 2*math.pi, 90):
        x=16*math.sin(a)**3
        y=13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a)
        pts.append((cx+x/16*sz*.42, cy-y/16*sz*.42))
    d.polygon(pts,fill=col+(255,))
    if stroke:
        d.line(pts+[pts[0]],fill=stroke+(255,),width=3,joint="curve")

def icon_lock(d,cx,cy,sz,col=(110,110,110)):
    d.arc((cx-sz*.22,cy-sz*.30,cx+sz*.22,cy+sz*.06),180,360,fill=col+(255,),width=max(2,int(sz*.10)))
    d.rounded_rectangle((cx-sz*.28,cy-sz*.04,cx+sz*.28,cy+sz*.32),radius=sz*.08,fill=col+(255,))

def icon_star(d,cx,cy,sz,col):
    import math
    pts=[]
    for i in range(10):
        a=-math.pi/2+i*math.pi/5; r=sz*.5 if i%2==0 else sz*.22
        pts.append((cx+math.cos(a)*r,cy+math.sin(a)*r))
    d.polygon(pts,fill=col+(255,),outline=shade(col,.6)+(255,))

def icon_gear(d,cx,cy,sz,col):
    import math
    pts=[]
    for i in range(16):
        a=i*math.pi/8; r=sz*.5 if i%2==0 else sz*.38
        pts.append((cx+math.cos(a)*r,cy+math.sin(a)*r))
    d.polygon(pts,fill=col+(255,))
    d.ellipse((cx-sz*.18,cy-sz*.18,cx+sz*.18,cy+sz*.18),fill=(255,246,224,255))

def icon_grid(d,cx,cy,sz,col):
    for r in range(2):
        for c in range(2):
            x=cx-sz*.4+c*sz*.42; y=cy-sz*.4+r*sz*.42
            d.rounded_rectangle((x,y,x+sz*.34,y+sz*.34),radius=sz*.06,fill=col+(255,))

def icon_ticket(d,cx,cy,sz,col):
    d.rounded_rectangle((cx-sz*.5,cy-sz*.28,cx+sz*.5,cy+sz*.28),radius=sz*.1,fill=col+(255,))
    d.line((cx+sz*.2,cy-sz*.28,cx+sz*.2,cy+sz*.28),fill=(255,246,224,255),width=3)

def icon_home(d,cx,cy,sz,col):
    d.polygon([(cx,cy-sz*.45),(cx-sz*.5,cy),(cx+sz*.5,cy)],fill=col+(255,))
    d.rectangle((cx-sz*.34,cy,cx+sz*.34,cy+sz*.45),fill=col+(255,))
    d.rectangle((cx-sz*.10,cy+sz*.18,cx+sz*.10,cy+sz*.45),fill=(255,246,224,255))

def icon_palette(d,cx,cy,sz,col):
    d.ellipse((cx-sz*.48,cy-sz*.40,cx+sz*.42,cy+sz*.42),fill=col+(255,))
    for a,cc in [((-.2,-.1),(240,130,130)),((.2,-.05),(120,180,110)),((0,.2),(110,150,210))]:
        d.ellipse((cx+a[0]*sz-6,cy+a[1]*sz-6,cx+a[0]*sz+6,cy+a[1]*sz+6),fill=cc+(255,))

def icon_calendar(d,cx,cy,sz,col):
    d.rounded_rectangle((cx-sz*.42,cy-sz*.34,cx+sz*.42,cy+sz*.42),radius=sz*.08,fill=col+(255,))
    d.line((cx-sz*.42,cy-sz*.10,cx+sz*.42,cy-sz*.10),fill=(255,246,224,255),width=3)
    icon_star(d,cx,cy+sz*.16,sz*.4,(245,195,75))

def shade(c, f): return tuple(max(0, min(255, int(v * f))) for v in c)
def light(c, f): return tuple(max(0, min(255, int(v + (255-v)*f))) for v in c)

# ---------- 厚软胶圆角块（第一版质感核心） ----------
def clay_block(w, h, color, r=None, label=None, label_sz=None, label_col=(255,255,255),
               badge=None, outline=True, shadow=True, hi=True):
    """厚软胶：外描边 + 顶高光带 + 底部暗边 + 柔投影 + 可选数字/角标。"""
    r = r or min(w, h) * .24
    S = 3
    c = Image.new("RGBA", (w*S, h*S), (0,0,0,0))
    d = ImageDraw.Draw(c)
    if shadow:
        pad = 10*S
        sh = Image.new("RGBA", (w*S+2*pad, h*S+2*pad), (0,0,0,0))
        sd = ImageDraw.Draw(sh)
        sd.rounded_rectangle((pad, pad+4*S, pad+w*S-1, pad+h*S-1+4*S), radius=r*S, fill=(70,45,28,95))
        sh = sh.filter(ImageFilter.GaussianBlur(5*S))
        c.alpha_composite(sh, (-pad, -pad))
    d = ImageDraw.Draw(c)
    ol = shade(color, .62) if outline else color
    d.rounded_rectangle((0, 0, w*S-1, h*S-1), radius=r*S, fill=ol+(255,))
    # 主体渐变（顶亮底暗）
    for yy in range(int(h*S*0.10), int(h*S*0.92)):
        t = (yy - h*S*0.10) / (h*S*0.82)
        col = tuple(int(light(color,.18)[i]*(1-t) + shade(color,.92)[i]*t) for i in range(3))
        inset = int(r*S*.28)
        d.line((inset, yy, w*S-inset, yy), fill=col+(255,))
    # 顶部椭圆高光
    if hi:
        d.rounded_rectangle((w*S*.10, h*S*.07, w*S*.90, h*S*.26), radius=r*S*.5, fill=(255,255,255,70))
    # 底部内侧暗边
    d.arc((w*S*.04, h*S*.66, w*S*.96, h*S*1.02), 15, 165, fill=shade(color,.68)+(140,), width=max(1,int(3*S)))
    if label is not None:
        text(d, (w*S/2, h*S/2), str(label), (label_sz or h*.42)*S, label_col+(255,),
             stroke=shade(label_col,.55)+(255,) if label_col!=(255,255,255) else shade(color,.5)+(255,),
             sw=2*S, bold=True, sh=True)
    out = c.resize((w, h), Image.LANCZOS)
    if badge:
        bx, by, bs = int(w*.80), int(h*.66), int(min(w,h)*.34)
        bb = clay_block(bs, bs, badge[0], r=bs*.34, label=badge[1], label_sz=bs*.5)
        out.alpha_composite(bb, (bx, by))
    return out

def soft_tile(size, color, direction):
    """棋盘软胶方块（复用tile_kit光照，带箭头）。"""
    S = size
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    grad = 1.08 - .28*(yy/(S-1))**1.5
    hl = .16*np.exp(-((yy-S*.16)/(S*.15))**2)*np.exp(-((xx-S/2)/(S*.44))**2)
    L = np.clip(grad+hl-.05*np.exp(-((yy-(S-S*.09))/(S*.09))**2), .62, 1.2)
    m = Image.new("L",(S,S),0)
    ImageDraw.Draw(m).rounded_rectangle((0,0,S-1,S-1), radius=int(S*.16), fill=255)
    inner = np.asarray(m.filter(ImageFilter.GaussianBlur(S*.02))).astype(float)/255>.5
    er = inner.copy()
    for _ in range(max(1,int(S/12))):
        e=er.copy(); e[1:,:]&=er[:-1,:]; e[:-1,:]&=er[1:,:]; e[:,1:]&=er[:,:-1]; e[:,:-1]&=er[:,1:]; er=e
    L[inner & ~er] *= .74
    rgb = np.clip(np.array(color,float)[None,None,:]*L[:,:,None],0,255).astype(np.uint8)
    im = Image.fromarray(np.dstack([rgb, np.where(inner,255,255).astype(np.uint8)]),"RGBA")
    if direction!="none":
        rot={"U":0,"R":90,"D":180,"L":270,"X":0}
        am=Image.new("L",(S,S),0); ad=ImageDraw.Draw(am); u=S/24
        if direction=="X":
            poly=[(10*u,2*u),(14*u,2*u),(14*u,10*u),(22*u,10*u),(22*u,14*u),(14*u,14*u),(14*u,22*u),(10*u,22*u),(10*u,14*u),(2*u,14*u),(2*u,10*u),(10*u,10*u)]
        else:
            poly=[(12*u,3*u),(20*u,11*u),(15.5*u,11*u),(15.5*u,20*u),(8.5*u,20*u),(8.5*u,11*u),(4*u,11*u)]
        ad.polygon(poly,fill=255)
        if rot[direction]: am=am.rotate(-rot[direction],resample=Image.BICUBIC)
        aa=np.asarray(am).astype(float)/255
        ar=np.zeros((S,S,4),np.uint8); ar[:,:,:3]=(248,244,232); ar[:,:,3]=(aa*225).astype(np.uint8)
        im.alpha_composite(Image.fromarray(ar,"RGBA"))
    return im

PAL={"G":(139,193,91),"Y":(246,186,74),"B":(97,161,220),"P":(247,143,147),"C":(104,92,76),"W":(233,217,198),"O":(240,150,80)}
# 第一版游戏页的异形棋盘（1=有块）
BOARD=[
 "..GGGGG..",
 ".GGGGGGG.",
 "GGGGGGGGG",
 "GGGGGGGGG",
 ".GGGGGGG.",
 "..GGGGG..",
]
BOARD_DIRS=[["U","R","L","D","U","R","L","U","R"] for _ in range(6)]
BOARD_COLS=["G","Y","B","P","G","O","B","Y","P"]

def board_area(cell=54):
    rows=len(BOARD); cols=len(BOARD[0])
    bw,bh=cols*cell,rows*cell
    im=Image.new("RGBA",(bw,bh),(0,0,0,0))
    d=ImageDraw.Draw(im)
    for r in range(rows):
        for c in range(cols):
            if BOARD[r][c]==".": continue
            col=PAL[BOARD_COLS[(r*3+c)%len(BOARD_COLS)]]
            dr=BOARD_DIRS[r][c]
            t=soft_tile(cell-2,col,dr)
            im.alpha_composite(t,(c*cell+1,r*cell+1))
    return im

def mascot(sz=150):
    """黄色方块吉祥物：眼睛/腮红/嘴/手脚/绿箭头。"""
    c=Image.new("RGBA",(sz*2,sz*2),(0,0,0,0)); d=ImageDraw.Draw(c)
    x0,y0=sz*.45,sz*.35; b=sz*1.1
    # 手
    d.rounded_rectangle((x0-sz*.20,y0+b*.42,x0,y0+b*.62),radius=sz*.06,fill=(235,190,60,255),outline=(180,135,30,255),width=3)
    d.rounded_rectangle((x0+b,y0+b*.42,x0+b+sz*.20,y0+b*.62),radius=sz*.06,fill=(235,190,60,255),outline=(180,135,30,255),width=3)
    # 脚
    d.rounded_rectangle((x0+b*.20,y0+b*.96,x0+b*.42,y0+b*1.10),radius=sz*.06,fill=(210,160,45,255))
    d.rounded_rectangle((x0+b*.58,y0+b*.96,x0+b*.80,y0+b*1.10),radius=sz*.06,fill=(210,160,45,255))
    # 身体（黄软胶）
    d.rounded_rectangle((x0,y0,x0+b,y0+b),radius=sz*.18,fill=(140,100,30,255))
    d.rounded_rectangle((x0+4,y0+2,x0+b-4,y0+b-6),radius=sz*.16,fill=(250,205,70,255))
    d.rounded_rectangle((x0+b*.12,y0+b*.06,x0+b*.88,y0+b*.26),radius=sz*.10,fill=(255,228,120,160))
    # 眼睛
    for ex in (x0+b*.30,x0+b*.66):
        d.ellipse((ex-sz*.055,y0+b*.34-sz*.055,ex+sz*.055,y0+b*.34+sz*.055),fill=(60,40,25,255))
        d.ellipse((ex-sz*.018,y0+b*.34-sz*.03,ex+sz*.01,y0+b*.34),fill=(255,255,255,255))
    # 腮红
    d.ellipse((x0+b*.12,y0+b*.46,x0+b*.24,y0+b*.54),fill=(245,150,150,180))
    d.ellipse((x0+b*.76,y0+b*.46,x0+b*.88,y0+b*.54),fill=(245,150,150,180))
    # 嘴
    d.arc((x0+b*.40,y0+b*.42,x0+b*.60,y0+b*.60),10,170,fill=(120,70,35,255),width=4)
    # 绿箭头
    ax,ay=x0+b*.30,y0+b*.58; u=sz*.09
    d.polygon([(ax,y0+b*.62),(ax+u*5,y0+b*.62),(ax+u*5,y0+b*.54),(ax+u*8,y0+b*.70),(ax+u*5,y0+b*.86),(ax+u*5,y0+b*.78),(ax,y0+b*.78)],fill=(90,180,80,255),outline=(50,130,50,255))
    return c.resize((sz,sz),Image.LANCZOS)

def float_btn(sz, kind, label, badge=None):
    """悬浮圆钮：奶油圆底 + 图标 + 下方标签胶囊。"""
    c=Image.new("RGBA",(sz,int(sz*1.32)),(0,0,0,0)); d=ImageDraw.Draw(c)
    # 投影
    sh=Image.new("RGBA",c.size,(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.ellipse((6,12,sz-6,sz+6),fill=(70,45,28,90)); sh=sh.filter(ImageFilter.GaussianBlur(6))
    c.alpha_composite(sh)
    d=ImageDraw.Draw(c)
    d.ellipse((2,2,sz-2,sz-2),fill=(168,120,72,255))
    d.ellipse((5,5,sz-5,sz-5),fill=(255,246,224,255))
    d.ellipse((sz*.12,sz*.10,sz*.88,sz*.52),fill=(255,255,255,110))
    ic={"task":("T",(90,170,120)),"ach":("S",(235,175,60)),"gallery":("G",(120,150,190)),"skin":("S",(210,130,180)),"daily":("D",(230,160,70))}
    sym,col=ic.get(kind,("★",(120,150,190)))
    text(d,(sz/2,sz*.48),sym,int(sz*.42),col+(255,),bold=True)
    if badge:
        d.ellipse((sz*.72,sz*.06,sz*.94,sz*.28),fill=(235,80,95,255))
        text(d,(sz*.83,sz*.17),badge,int(sz*.17),(255,255,255,255),bold=True)
    # 标签胶囊
    d.rounded_rectangle((sz*.04,sz*.86,sz*.96,sz*1.26),radius=sz*.18,fill=(168,120,72,255))
    d.rounded_rectangle((sz*.07,sz*.89,sz*.93,sz*1.22),radius=sz*.15,fill=(255,244,222,255))
    text(d,(sz/2,sz*1.055),label,int(sz*.24),(120,80,50,255),bold=True)
    return c

def nav_bar(labels=("首页","图库","皮肤","每日"),active=0):
    n=len(labels); gap=12; bw=(W-40-gap*(n+1))/n; bh=150
    c=Image.new("RGBA",(W,bh+30),(0,0,0,0))
    for i,lab in enumerate(labels):
        x=20+gap+i*(bw+gap)
        on=(i==active)
        base=(168,120,72,255) if on else (210,180,140,200)
        face=(255,246,224,255) if on else (248,235,212,235)
        d=ImageDraw.Draw(c)
        d.rounded_rectangle((x,bh*.08,x+bw,bh*.86),radius=26,fill=base)
        d.rounded_rectangle((x+3,bh*.08+3,x+bw-3,bh*.86-3),radius=23,fill=face)
        if on:
            d.rounded_rectangle((x+bw*.25,bh*.84,x+bw*.75,bh*.88),radius=3,fill=(90,170,80,255))
        iccol=(90,170,110) if on else (170,130,90); icx=x+bw/2; icy=bh*.38; icsz=bh*.34
        if lab=="首页": icon_home(d,icx,icy,icsz,iccol)
        elif lab=="图库": icon_grid(d,icx,icy,icsz,iccol)
        elif lab=="皮肤": icon_palette(d,icx,icy,icsz,iccol)
        elif lab=="每日": icon_calendar(d,icx,icy,icsz,iccol)
        else: icon_star(d,icx,icy,icsz,iccol)
        text(d,(x+bw/2,bh*.68),lab,int(bh*.20),(120,80,50,255),bold=True)
    return c

def cream_dot_bg():
    im=Image.new("RGBA",(W,H),(255,247,230,255)); d=ImageDraw.Draw(im)
    for y in range(0,H,26):
        for x in range(0,W,26):
            d.ellipse((x-1,y-1,x+1,y+1),fill=(238,220,195,255))
    return im

# ================= 屏1：地图关卡页（第一版图1） =================
def screen_map():
    c=GARDEN.copy(); d=ImageDraw.Draw(c)
    # 左上设置
    d.ellipse((34,34,124,124),fill=(168,120,72,255)); d.ellipse((40,40,118,118),fill=(255,246,224,255))
    icon_gear(d,79,79,58,(130,95,60))
    # 右上票券
    d.rounded_rectangle((W-250,36,W-34,110),radius=30,fill=(168,120,72,255))
    d.rounded_rectangle((W-247,39,W-37,107),radius=27,fill=(255,246,224,255))
    icon_ticket(d,W-215,73,44,(245,195,75)); text(d,(W-160,73),"3",32,(120,80,50,255),bold=True,anchor="lm")
    d.ellipse((W-96,40,W-30,106),fill=(120,190,90,255)); text(d,(W-63,73),"+",40,(255,255,255,255),bold=True)
    # 中央竖向浅色通道
    d.rounded_rectangle((W*.40,0,W*.60,H*.72),radius=20,fill=(230,245,215,70))
    # 关卡节点
    def node(cy,sz,col,label,badge=None,bubble=None):
        nx=W/2-sz/2
        b=clay_block(sz,sz,col,r=sz*.24,label=label,label_sz=sz*.5,badge=badge)
        c.alpha_composite(b,(int(nx),int(cy)))
        if bubble:
            bx=W/2+sz*.42; by=cy+sz*.10
            d.rounded_rectangle((bx,by,bx+150,by+56),radius=22,fill=(255,255,255,235),outline=(200,170,130,255),width=2)
            text(d,(bx+75,by+28),"当前关卡",24,(130,90,60,255),bold=True)
            d.polygon([(bx+20,by+54),(bx+44,by+54),(bx+24,by+76)],fill=(255,255,255,235))
    node(40,118,(190,190,190),"40",badge=((150,150,150),"L"))
    node(222,118,(190,190,190),"39",badge=((150,150,150),"L"))
    node(404,118,(165,120,215),"38",badge=((120,90,180),"S"))
    node(586,150,(90,185,110),"37",bubble=True)
    # 吉祥物
    mas=mascot(160); c.alpha_composite(mas,(int(W/2-80),748))
    # 左右红节点
    lb=clay_block(130,130,(235,110,110),r=34,label="36",label_sz=58,badge=((200,80,90),"!"))
    c.alpha_composite(lb,(64,790))
    rb=clay_block(130,130,(235,110,110),r=34,label="挑战",label_sz=38,badge=((200,80,90),"!"))
    c.alpha_composite(rb,(W-194,790))
    # 悬浮任务/成就
    c.alpha_composite(float_btn(120,"task","任务",badge="1"),(W-190,300))
    c.alpha_composite(float_btn(120,"ach","成就"),(W-190,520))
    # 主CTA
    cta=clay_block(W-96,170,(90,185,95),r=70,label="第 37 关  ›",label_sz=64,shadow=True)
    c.alpha_composite(cta,(48,1030))
    text(d,(W/2,1228),"点击开始游戏",26,(255,250,235,255),stroke=(140,100,60,255),sw=2,bold=True)
    # 底部导航
    c.alpha_composite(nav_bar(),(0,H-190))
    return c

# ================= 屏2：加载页（第一版图2左上） =================
def screen_loading():
    c=GALLERY.copy(); d=ImageDraw.Draw(c)
    # 柔化压暗背景，突出logo
    ov=Image.new("RGBA",(W,H),(60,40,25,55)); c.alpha_composite(ov)
    # 四色箭头logo（2x2软胶）
    cols=[(110,190,110),(245,195,75),(95,160,215),(240,140,150)]
    dirs=["U","R","L","D"]
    bs=76; gap=10; ox=W/2-bs-gap/2; oy=360
    for i in range(4):
        t=soft_tile(bs,cols[i],dirs[i])
        c.alpha_composite(t,(int(ox+(i%2)*(bs+gap)),int(oy+(i//2)*(bs+gap))))
    text(d,(W/2,620),"点击画廊",88,(255,248,228,255),stroke=(120,72,40,255),sw=10,bold=True,sh=True)
    text(d,(W/2,710),"正在准备画作…",34,(255,245,225,235),bold=True)
    # 进度条
    bw=440; bx=W/2-bw/2; by=1120
    d.rounded_rectangle((bx-4,by-4,bx+bw+4,by+34),radius=18,fill=(168,120,72,255))
    d.rounded_rectangle((bx,by,bx+bw,by+30),radius=15,fill=(240,225,200,255))
    d.rounded_rectangle((bx,by,bx+int(bw*.60),by+30),radius=15,fill=(110,200,110,255))
    text(d,(W/2,1190),"60%",30,(255,248,230,255),bold=True)
    return c

# ================= 屏3：主页画架（第一版图2右上1） =================
def screen_home():
    c=GALLERY.copy(); d=ImageDraw.Draw(c)
    # 顶部标题牌
    d.rounded_rectangle((W/2-130,34,W/2+130,96),radius=28,fill=(168,120,72,255))
    d.rounded_rectangle((W/2-126,38,W/2+126,92),radius=25,fill=(255,246,224,255))
    text(d,(W/2,65),"第 1 关",40,(120,80,50,255),bold=True)
    # 金币 + 设置
    d.ellipse((30,34,100,104),fill=(245,195,70,255)); text(d,(65,69),"◉",34,(255,255,255,255),bold=True)
    text(d,(120,69),"1280",32,(255,248,230,255),stroke=(120,80,50,255),sw=2,bold=True)
    d.ellipse((W-104,34,W-34,104),fill=(168,120,72,255)); icon_gear(d,W-69,69,50,(255,246,224))
    # 悬浮按钮
    c.alpha_composite(float_btn(104,"gallery","图库"),(30,300))
    c.alpha_composite(float_btn(104,"skin","皮肤"),(30,500))
    c.alpha_composite(float_btn(104,"daily","每日"),(W-134,300))
    c.alpha_composite(float_btn(104,"ach","成就"),(W-134,500))
    # 中央画架 + 像素画
    px,py,pw,ph=W/2-190,300,380,540
    d.rounded_rectangle((px-14,py-14,px+pw+14,py+ph+14),radius=18,fill=(150,105,60,255))
    d.rounded_rectangle((px,py,px+pw,py+ph),radius=10,fill=(255,250,235,255))
    # 像素图案（小猫）
    cs=32; gx=px+30; gy=py+40
    pat=["0011111100","0122222210","01232232210","0122222210","0123443210","0114444110","0014444100","0011111100"]
    pcol={"0":(250,246,232,255),"1":(90,80,70,255),"2":(245,180,70,255),"3":(60,50,45,255),"4":(255,225,190,255)}
    for r,row in enumerate(pat):
        for cc,ch in enumerate(row):
            if ch=="0" and (r+cc)%2==0: col=(235,225,205,255)
            else: col=pcol.get(ch,(240,230,210,255))
            d.rectangle((gx+cc*cs,gy+r*cs,gx+cc*cs+cs-1,gy+r*cs+cs-1),fill=col)
    # 开始按钮
    cta=clay_block(W-140,150,(95,185,100),r=64,label="开始",label_sz=62)
    c.alpha_composite(cta,(70,1000))
    return c

# ================= 屏4：游戏主界面（第一版图2右上4） =================
def screen_game():
    c=cream_dot_bg(); d=ImageDraw.Draw(c)
    # 顶部关卡牌 + 暂停
    d.rounded_rectangle((W/2-120,26,W/2+120,84),radius=28,fill=(168,120,72,255))
    d.rounded_rectangle((W/2-116,30,W/2+116,80),radius=25,fill=(255,246,224,255))
    text(d,(W/2,55),"第 1 关",36,(120,80,50,255),bold=True)
    # 3心
    for i in range(3):
        hx=W/2-84+i*84
        icon_heart(d,hx,112,52,(235,90,110),(175,50,70))
    # 进度条 65%
    bx,by,bw=40,166,W-80
    d.rounded_rectangle((bx,by,bx+bw,by+26),radius=13,fill=(232,214,188,255))
    d.rounded_rectangle((bx,by,bx+int(bw*.65),by+26),radius=13,fill=(110,200,110,255))
    text(d,(W-70,by+13),"65%",30,(120,80,50,255),bold=True,anchor="lm")
    # 棋盘
    b=board_area(cell=54)
    c.alpha_composite(b,(int(W/2-b.width/2),300))
    # 道具栏
    pys=1290
    props=[("提示","3",(245,195,75)),("锤子","2",(180,140,100)),("炸弹","1",(90,90,95))]
    for i,(nm,num,col) in enumerate(props):
        px=60+i*((W-120)//3)
        blk=clay_block(120,120,(255,246,224),r=30,label=None,shadow=True)
        c.alpha_composite(blk,(px,pys))
        text(d,(px+60,pys+52),{"提示":"?","锤子":"T","炸弹":"O"}[nm],56,(120,80,50,255),bold=True)
        text(d,(px+60,pys+95),nm,26,(120,80,50,255),bold=True)
        d.ellipse((px+84,pys-8,px+128,pys+36),fill=(235,90,110,255))
        text(d,(px+106,pys+14),num,26,(255,255,255,255),bold=True)
    return c

# ================= 屏5：图库（第一版图2左上3） =================
def screen_gallery():
    c=cream_dot_bg(); d=ImageDraw.Draw(c)
    text(d,(W/2,70),"图 库",52,(120,80,50,255),bold=True)
    thumbs=[(245,170,70),(110,160,215),(240,150,120),(150,190,110),(200,180,160),(120,190,180)]
    for i in range(6):
        r,cc=divmod(i,3); px=40+cc*((W-80)//3); py=140+r*330
        blk=clay_block((W-100)//3,280,(255,248,232),r=26,shadow=True)
        c.alpha_composite(blk,(px,py))
        bx=px+24; by=py+24; bs=(W-100)//3-48
        # 像素缩略
        for rr in range(6):
            for ccc in range(6):
                col=thumbs[i] if (rr+ccc+i)%3 else light(thumbs[i],.3)
                d.rectangle((bx+ccc*bs/6,by+rr*bs/6,bx+(ccc+1)*bs/6-1,by+(rr+1)*bs/6-1),fill=col+(255,))
        text(d,(px+(W-100)//6,py+bs+50),str(i+1)+(" ✓" if i<2 else ""),26,(120,80,50,255),bold=True)
    c.alpha_composite(nav_bar(("首页","图库","皮肤","每日"),1),(0,H-190))
    return c

# ================= 屏6：结算（第一版图2左下1） =================
def screen_win():
    c=cream_dot_bg(); d=ImageDraw.Draw(c)
    # 彩旗
    for i in range(9):
        x=i*W/9; col=[(240,120,110),(245,195,75),(120,190,110),(110,160,215),(240,150,180)][i%5]
        d.polygon([(x,20),(x+W/12,20),(x+W/24,80)],fill=col+(255,))
    # 完成横幅
    bn=clay_block(340,110,(235,100,95),r=30,label="完 成",label_sz=58,label_col=(255,250,235))
    c.alpha_composite(bn,(int(W/2-170),80))
    # 画作
    blk=clay_block(400,520,(255,248,232),r=24,shadow=True); c.alpha_composite(blk,(int(W/2-200),230))
    for r in range(8):
        for cc in range(8):
            col=(245,180,70) if (r+cc)%3 else (90,80,70)
            d.rectangle((W/2-160+cc*40,270+r*40,W/2-160+cc*40+39,270+r*40+39),fill=col+(255,))
    text(d,(W/2,790),"+60",52,(230,170,50,255),bold=True)
    # 按钮
    c.alpha_composite(clay_block(W-140,130,(95,185,100),r=56,label="下一关",label_sz=52),(40,1000))
    c.alpha_composite(clay_block(W-140,130,(255,246,224),r=56,label="首页",label_sz=48,label_col=(120,80,50),hi=False),(40,1160))
    return c

# ================= 屏7：失败弹窗（第一版图2左下2） =================
def screen_fail():
    c=screen_game()
    ov=Image.new("RGBA",(W,H),(40,30,25,150)); c.alpha_composite(ov)
    # 弹窗
    pw,ph=520,740; px,py=(W-pw)//2,380
    blk=clay_block(pw,ph,(255,246,228),r=44,shadow=True); c.alpha_composite(blk,(px,py))
    d=ImageDraw.Draw(c)
    text(d,(W/2,py+110),"生命用完了",54,(120,70,55,255),bold=True)
    icon_heart(d,W/2,py+220,150,(235,90,110),(175,50,70))
    text(d,(W/2,py+330),"再试一次就能成功哦！",30,(130,90,65,255),bold=True)
    c.alpha_composite(clay_block(pw-80,110,(95,185,100),r=46,label="看广告复活",label_sz=44),(px+40,py+400))
    c.alpha_composite(clay_block(pw-80,100,(255,246,224),r=42,label="重新开始",label_sz=42),(px+40,py+540))
    return c

# ================= 屏8：皮肤（第一版图2右下2） =================
def screen_skin():
    c=cream_dot_bg(); d=ImageDraw.Draw(c)
    text(d,(W/2,64),"皮 肤",50,(120,80,50,255),bold=True)
    d.rounded_rectangle((60,110,W/2-6,168),radius=24,fill=(95,185,100,255)); text(d,(W/4,139),"方块皮肤",30,(255,255,255,255),bold=True)
    text(d,(W*3/4,139),"拖尾效果",30,(140,100,70,255),bold=True)
    cols=[(110,190,110),(160,210,130),(240,150,170),(245,195,75),(110,160,215),(150,120,200),(90,90,95),(230,140,90)]
    for i in range(8):
        r,cc=divmod(i,4); px=36+cc*((W-72)//4); py=200+r*300
        blk=clay_block((W-90)//4,250,(255,248,232),r=24,shadow=True); c.alpha_composite(blk,(px,py))
        t=soft_tile(96,cols[i],"U"); c.alpha_composite(t,(px+((W-90)//4-96)//2,py+30))
        text(d,(px+(W-90)//8,py+180),"免费" if i<4 else "800",26,(120,80,50,255),bold=True)
    return c

# ================= 屏9：每日成就（第一版图2右下1） =================
def screen_daily():
    c=cream_dot_bg(); d=ImageDraw.Draw(c)
    d.rounded_rectangle((W/2-160,30,W/2-6,88),radius=24,fill=(95,185,100,255)); text(d,(W/4,59),"每日",32,(255,255,255,255),bold=True)
    text(d,(W*3/4,59),"成就",32,(140,100,70,255),bold=True)
    text(d,(W/2,140),"每日挑战",42,(120,80,50,255),bold=True)
    # 签到7格
    for i in range(7):
        px=30+i*((W-60)//7)
        col=(245,195,75) if i<4 else (230,220,205)
        d.rounded_rectangle((px,190,px+(W-80)//7-6,270),radius=16,fill=col+(255,),outline=(170,130,85,255),width=2)
        text(d,(px+((W-80)//7-6)/2,230),"✓" if i<4 else str(i+1),30,(120,80,50,255),bold=True)
    # 成就列表
    ach=[("初出茅庐","完成第 1 关",6,10),("集邮册","收集 10 幅画",12,20),("一桶金","累计 1000 金币",9,15)]
    for i,(nm,desc,p,total) in enumerate(ach):
        py=340+i*260
        blk=clay_block(W-60,220,(255,248,232),r=26,shadow=True); c.alpha_composite(blk,(30,py))
        text(d,(110,py+60),nm,34,(120,80,50,255),bold=True,anchor="lm")
        text(d,(110,py+105),desc+"  "+str(p)+"/"+str(total),24,(150,110,80,255),anchor="lm")
        bx,bw=110,W-160
        d.rounded_rectangle((bx,py+140,bx+bw,py+168),radius=14,fill=(232,214,188,255))
        d.rounded_rectangle((bx,py+140,bx+int(bw*p/total),py+168),radius=14,fill=(245,195,75,255))
    return c

SCREENS=[
    ("01_map",screen_map),("02_loading",screen_loading),("03_home",screen_home),
    ("04_game",screen_game),("05_gallery",screen_gallery),("06_win",screen_win),
    ("07_fail",screen_fail),("08_skin",screen_skin),("09_daily",screen_daily),
]

def contact():
    th_w,th_h=300,650
    sheet=Image.new("RGB",(th_w*3+40*4,th_h*3+70*4+40),(248,246,242)); sd=ImageDraw.Draw(sheet)
    for i,(nm,fn) in enumerate(SCREENS):
        im=Image.open(os.path.join(OUT,nm+".png")).convert("RGB"); im.thumbnail((th_w,th_h),Image.LANCZOS)
        r,cc=divmod(i,3); x=40+cc*(th_w+40); y=70+r*(th_h+70)
        sheet.paste(im,(x,y)); sd.text((x,y-26),nm,fill=(70,50,35),font=font(28,True))
    sheet.save(os.path.join(OUT,"contact_sheet.png"))

def main():
    init_bg()
    for nm,fn in SCREENS:
        im=fn(); im.convert("RGB").save(os.path.join(OUT,nm+".png")); print("生成",nm,im.size)
    contact(); print("拼图完成",os.path.join(OUT,"contact_sheet.png"))

if __name__=="__main__":
    main()
