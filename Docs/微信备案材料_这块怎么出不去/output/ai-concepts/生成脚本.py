# -*- coding: utf-8 -*-
"""
《这块怎么出不去》六张界面效果图 —— 程序化合成
方法：使用项目原始美术素材 + 真实中文字体(思源黑体)合成，非运行截图。
输出：1170x2532 PNG，标 "AI生成 · 界面效果示意"。
01 与 06 共用同一棋盘绘制函数，保证逐块一致。
"""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = 3
W, H = 390*S, 844*S          # 1170 x 2532

GARDEN = "E:/UnityProject/MutiplayGame/BlockOut/Assets/BlockOut/Resources/UI/Garden"
FONT   = "C:/Windows/Fonts/NotoSansSC-VF.ttf"
OUT    = "E:/UnityProject/MutiplayGame/BlockOut/Docs/微信备案材料_这块怎么出不去/output/ai-concepts"
os.makedirs(OUT, exist_ok=True)

# ---------- palette ----------
BROWN   = (91, 70, 50, 255)
BROWN2  = (120, 96, 72, 255)
GOLD    = (217, 185, 120, 255)
CREAM_T = (253, 244, 232, 255)
CREAM_B = (246, 230, 211, 255)
GREEN_T = (126, 199, 92, 255)
GREEN_B = (76, 158, 48, 255)
GREEN_LINE=(54, 118, 34, 255)
WHITE   = (255, 255, 255, 255)
SHADOW  = (92, 66, 40, 46)
CORAL   = (240, 121, 106, 255)
MINT    = (127, 203, 160, 255)
SKY     = (120, 190, 232, 255)
YELLOW  = (243, 205, 105, 255)
LAVENDER= (192, 169, 224, 255)
PEACH   = (244, 176, 140, 255)
HILITE  = (255, 211, 78, 255)
GREYBLK = (154, 158, 150, 255)

BLOCK_COLORS = [[CORAL, MINT], [SKY, YELLOW], [LAVENDER, PEACH], [MINT, SKY]]

# ---------- font ----------
def font(px, weight=400):
    f = ImageFont.truetype(FONT, px*S)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f

F_TITLE = font(20, 800)
F_H1    = font(17, 700)
F_H2    = font(15, 700)
F_BODY  = font(12, 400)
F_SMALL = font(10, 400)
F_TINY  = font(8, 400)
F_NUM   = font(15, 800)
F_NUM2  = font(12, 700)

# ---------- asset helpers ----------
def load(name):
    return Image.open(os.path.join(GARDEN, name)).convert("RGBA")

def cover_bg(name):
    im = Image.open(os.path.join(GARDEN, name)).convert("RGBA")
    sw, sh = im.size
    scale = max(W/sw, H/sh)
    nw, nh = int(sw*scale)+1, int(sh*scale)+1
    im = im.resize((nw, nh), Image.LANCZOS)
    left = (nw-W)//2; top = (nh-H)//2
    return im.crop((left, top, left+W, top+H))

def paste_asset(base, asset, x, y, w=None, h=None):
    a = asset
    if w is not None or h is not None:
        if w is None: w = int(a.width*h/a.height)
        if h is None: h = int(a.height*w/a.width)
        a = a.resize((int(w*S), int(h*S)), Image.LANCZOS)
    base.paste(a, (int(x*S), int(y*S)), a)

def vgrad_round(w, h, radius, ctop, cbot, outline=None, ow=1.5):
    Wp, Hp = int(w*S), int(h*S)
    grad = Image.new("RGB", (Wp, Hp))
    gd = ImageDraw.Draw(grad)
    for y in range(Hp):
        t = y/max(1, Hp-1)
        c = tuple(int(ctop[i]+(cbot[i]-ctop[i])*t) for i in range(3))
        gd.line((0, y, Wp, y), fill=c)
    mask = Image.new("L", (Wp, Hp), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,Wp-1,Hp-1), radius=int(radius*S), fill=255)
    out = Image.new("RGBA", (Wp, Hp), (0,0,0,0))
    out.paste(grad, (0,0), mask)
    d = ImageDraw.Draw(out)
    if outline:
        d.rounded_rectangle((int(ow*S),int(ow*S),Wp-1-int(ow*S),Hp-1-int(ow*S)),
                            radius=int(radius*S), outline=outline, width=int(ow*S))
    return out

def panel(base, x, y, w, h, radius=16, shadow=True):
    if shadow:
        sh = vgrad_round(w, h, radius, (90,66,40,255),(90,66,40,255))
        m = sh.getchannel("A")
        blur = Image.new("L", sh.size, 0)
        blur.paste(m, (0,int(4*S)))
        blur = blur.filter(ImageFilter.GaussianBlur(5*S))
        shad = Image.new("RGBA", sh.size, SHADOW)
        shad.putalpha(blur.point(lambda v:int(v*0.5)))
        base.alpha_composite(shad, (int(x*S), int(y*S)))
    p = vgrad_round(w, h, radius, CREAM_T, CREAM_B, GOLD, 1.5)
    base.alpha_composite(p, (int(x*S), int(y*S)))

def button(base, x, y, w, h, text, tcol=WHITE, green=True, fnt=None):
    p = vgrad_round(w, h, h/2, GREEN_T if green else CREAM_T,
                    GREEN_B if green else CREAM_B,
                    GREEN_LINE if green else GOLD, 2)
    base.alpha_composite(p, (int(x*S), int(y*S)))
    d = ImageDraw.Draw(base)
    ctext(d, x+w/2, y+h/2, text, fnt or F_H2,
          tcol if green else BROWN)

def ctext(d, cx, cy, text, f, fill, anchor="mm"):
    d.text((int(cx*S), int(cy*S)), text, font=f, fill=fill, anchor=anchor)

def ltext(d, x, y, text, f, fill):
    d.text((int(x*S), int(y*S)), text, font=f, fill=fill, anchor="lm")

def watermark(base):
    d = ImageDraw.Draw(base)
    txt = "AI生成 · 界面效果示意"
    f = F_TINY
    bb = d.textbbox((0,0), txt, font=f)
    tw = bb[2]-bb[0]
    d.rounded_rectangle((int(8*S), int(832*S), int((22+tw/S)*S), int(842*S)),
                        radius=int(4*S), fill=(255,255,255,190))
    d.text((int(12*S), int(837*S)), txt, font=f, fill=(120,96,72,255), anchor="lm")

def base_screen(bg="garden-home.png"):
    im = cover_bg(bg).convert("RGBA")
    return im

# ---------- shared widgets ----------
def topbar_store_levels(base, title, coins="600", selected="关卡"):
    d = ImageDraw.Draw(base)
    panel(base, 14, 14, 362, 40, radius=14)
    # back pill
    back = vgrad_round(46, 26, 11, CREAM_T, CREAM_B, GOLD, 1.5)
    base.alpha_composite(back, (int(22*S), int(21*S)))
    ctext(d, 45, 34, "返回", F_SMALL, BROWN)
    ctext(d, 195, 34, title, F_H1, BROWN)
    paste_asset(base, load("icon-coin.png"), 294, 22, 18, 18)
    ctext(d, 344, 34, coins, F_H2, BROWN, anchor="rm")

def bottom_nav(base, selected):
    d = ImageDraw.Draw(base)
    panel(base, 18, 788, 354, 44, radius=18)
    items = [("首页","icon-home.png",72), ("关卡","icon-levels.png",195), ("道具","icon-store.png",318)]
    for label, ic, cx in items:
        on = (label==selected)
        if on:
            hi = vgrad_round(96, 34, 14, (232,244,214,255),(206,230,180,255), GREEN_LINE, 1.5)
            base.alpha_composite(hi, (int((cx-48)*S), int(792*S)))
        paste_asset(base, load(ic), cx-9, 792, 18, 18)
        ctext(d, cx, 821, label, F_SMALL, BROWN if on else BROWN2)

def progress_bar(base, x, y, w, h, frac, bgc=(210,200,184,255)):
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((int(x*S),int(y*S),int((x+w)*S),int((y+h)*S)), radius=int(h/2*S), fill=bgc)
    if frac>0:
        d.rounded_rectangle((int(x*S),int(y*S),int((x+w*frac)*S),int((y+h)*S)), radius=int(h/2*S), fill=GREEN_B)
    d.rounded_rectangle((int(x*S),int(y*S),int((x+w)*S),int((y+h)*S)), radius=int(h/2*S), outline=GOLD, width=int(1*S))

# =====================================================================
# 01 / 06  board (shared, pixel-identical)
# =====================================================================
def draw_block(base, bx, by, bw, bh, color, arrow, highlight=False):
    d = ImageDraw.Draw(base)
    # contact shadow (drawn first, under the block)
    d.rounded_rectangle((int((bx+1.5)*S), int((by+3)*S), int((bx+bw+1.5)*S), int((by+bh+3)*S)),
                        radius=int(12*S), fill=(90,66,40,40))
    # body gradient composited immediately so the arrow can be drawn on top
    g = vgrad_round(bw, bh, 12,
                    tuple(min(255,c+22) for c in color[:3])+(255,),
                    tuple(max(0,c-16) for c in color[:3])+(255,),
                    tuple(max(0,c-40) for c in color[:3])+(120,), 1)
    base.alpha_composite(g, (int(bx*S), int(by*S)))
    d = ImageDraw.Draw(base)
    # arrow
    cx = bx + bw/2; cy = by + bh/2
    L = 30; head = 12; t = 4
    ac = (255,255,255,235)
    if arrow == "left":
        x1, x2 = cx+L/2, cx-L/2+head
        d.line((int(x1*S),int(cy*S),int(x2*S),int(cy*S)), fill=ac, width=int(t*S))
        d.polygon([(int((cx-L/2)*S),int(cy*S)),
                   (int((cx-L/2+head)*S),int((cy-head*0.8)*S)),
                   (int((cx-L/2+head)*S),int((cy+head*0.8)*S))], fill=ac)
    else:
        x1, x2 = cx-L/2, cx+L/2-head
        d.line((int(x1*S),int(cy*S),int(x2*S),int(cy*S)), fill=ac, width=int(t*S))
        d.polygon([(int((cx+L/2)*S),int(cy*S)),
                   (int((cx+L/2-head)*S),int((cy-head*0.8)*S)),
                   (int((cx+L/2-head)*S),int((cy+head*0.8)*S))], fill=ac)
    if highlight:
        d.rounded_rectangle((int((bx-2)*S),int((by-2)*S),int((bx+bw+2)*S),int((by+bh+2)*S)),
                            radius=int(14*S), outline=HILITE, width=int(3.5*S))

def draw_hud(base, hint_stock=2, tip="轻点方块，沿箭头方向移出", highlight=False):
    global IMG_HOLDER
    IMG_HOLDER = []
    d = ImageDraw.Draw(base)
    # top card
    panel(base, 18, 20, 354, 82, radius=16)
    ctext(d, 195, 42, "第5关", F_H1, BROWN)
    ctext(d, 195, 62, "生命模式", F_BODY, BROWN2)
    for i in range(3):
        paste_asset(base, load("icon-heart.png"), 32+i*18, 78, 15, 15)
    progress_bar(base, 92, 82, 230, 8, 0.0)
    # pause
    pause = vgrad_round(26, 26, 9, CREAM_T, CREAM_B, GOLD, 1.5)
    base.alpha_composite(pause, (int(337*S), int(30*S)))
    d = ImageDraw.Draw(base)
    d.rounded_rectangle((int(345*S),int(36*S),int(348*S),int(50*S)), fill=BROWN)
    d.rounded_rectangle((int(352*S),int(36*S),int(355*S),int(50*S)), fill=BROWN)

    # board panel
    panel(base, 20, 112, 350, 442, radius=20)
    bx0, by0, bw, bh = 34, 128, 322, 410
    gap = 9
    block_w = (bw-gap)/2
    block_h = (bh-gap*3)/4
    for r in range(4):
        for c in range(2):
            bxx = bx0 + c*(block_w+gap)
            byy = by0 + r*(block_h+gap)
            draw_block(base, bxx, byy, block_w, block_h, BLOCK_COLORS[r][c],
                       "left" if c==0 else "right",
                       highlight=(highlight and r==0 and c==0))
    d = ImageDraw.Draw(base)
    ctext(d, 336, 572, "剩余8块", F_BODY, BROWN2, anchor="rm")

    # tip pill
    panel(base, 44, 590, 302, 30, radius=14)
    d = ImageDraw.Draw(base)
    paste_asset(base, load("icon-hint.png"), 56, 594, 11, 20)
    ltext(d, 74, 605, tip, F_SMALL, BROWN)

    # bottom items
    items = [("提示","icon-hint.png",hint_stock), ("锤子","icon-hammer.png",2), ("魔法","icon-magic.png",2)]
    for i,(label,ic,cnt) in enumerate(items):
        x = 26 + i*114
        panel(base, x, 738, 106, 62, radius=14)
        paste_asset(base, load(ic), x+16, 746, 20, 26)
        ctext(d, x+63, 752, str(cnt), F_NUM2, CORAL, anchor="lm")
        ctext(d, x+63, 768, label, F_H2, BROWN, anchor="lm")
        sub = {"提示":"高亮可飞块","锤子":"消除一块","魔法":"飞走多块"}[label]
        ctext(d, x+53, 788, sub, F_TINY, BROWN2)
    watermark(base)

# =====================================================================
# 02 settlement
# =====================================================================
def screen02():
    im = base_screen()
    d = ImageDraw.Draw(im)
    back = vgrad_round(60, 26, 11, CREAM_T, CREAM_B, GOLD, 1.5)
    im.alpha_composite(back, (int(18*S), int(18*S)))
    ctext(d, 48, 31, "首页", F_SMALL, BROWN)
    # ribbon
    paste_asset(im, load("ribbon-coral.png"), 100, 56, 190, 50)
    ctext(d, 195, 82, "关卡完成", F_H1, WHITE)
    ctext(d, 195, 112, "画作已揭晓", F_BODY, BROWN)
    # frame + pixel flower
    paste_asset(im, load("frame-art.png"), 78, 140, 234, 234)
    draw_pixel_flower(im, 100, 162, 190, 190)
    # reward
    paste_asset(im, load("icon-coin.png"), 150, 402, 22, 22)
    ltext(d, 178, 413, "通关奖励", F_BODY, BROWN)
    ctext(d, 195, 442, "进度已保存", F_SMALL, BROWN2)
    # buttons
    button(im, 60, 468, 270, 44, "下一关", fnt=F_H1)
    button(im, 60, 522, 130, 40, "重玩", green=False, fnt=F_H2)
    button(im, 200, 522, 130, 40, "查看关卡", green=False, fnt=F_H2)
    watermark(im)
    return im

def draw_pixel_flower(im, x, y, w, h):
    d = ImageDraw.Draw(im)
    d.rectangle((int(x*S),int(y*S),int((x+w)*S),int((y+h)*S)), fill=(252,244,231,255))
    n = 19
    cw = w/n; ch = h/n
    def cell(cx, cy, col):
        d.rectangle((int((x+cx*cw)*S), int((y+cy*ch)*S),
                     int((x+(cx+1)*cw)*S), int((y+(cy+1)*ch)*S)), fill=col)
    pink=(242,138,158,255); pink2=(248,175,190,255)
    yellow=(247,206,86,255); green=(126,178,96,255); green2=(154,196,112,255)
    # stem
    for r in range(9,17): cell(9,r,green)
    # leaves
    for c in range(5,9): cell(c,12,green2)
    for c in range(10,14): cell(c,14,green2)
    # flower petals 5x5 centered ~ (9,7)
    for (cx,cy) in [(9,4),(9,5),(7,6),(8,6),(10,6),(11,6),(7,7),(8,7),(10,7),(11,7),(9,8),(8,9),(9,9),(10,9)]:
        cell(cx,cy,pink)
    for (cx,cy) in [(8,5),(10,5),(9,6),(9,7)]:
        cell(cx,cy,pink2)
    for (cx,cy) in [(9,6),(9,7),(8,7),(10,7)]:
        cell(cx,cy,yellow)

# =====================================================================
# 03 home
# =====================================================================
def screen03():
    im = base_screen()
    d = ImageDraw.Draw(im)
    paste_asset(im, load("icon-settings.png"), 18, 18, 30, 30)
    # coin bar
    panel(im, 262, 16, 110, 32, radius=14)
    paste_asset(im, load("icon-coin.png"), 270, 21, 18, 18)
    ctext(d, 350, 32, "600", F_H2, BROWN, anchor="rm")
    # title in sky
    d.text((int(195*S), int(96*S)), "这块怎么出不去", font=F_TITLE, fill=BROWN,
           anchor="mm", stroke_width=int(2*S), stroke_fill=(255,250,240,255))
    # path nodes bottom->top 1..5
    node_xy = {1:(92,588),2:(168,470),3:(196,352),4:(212,234),5:(226,148)}
    # connecting light path
    pts=[node_xy[i] for i in range(1,6)]
    for i in range(len(pts)-1):
        d.line((int(pts[i][0]*S),int(pts[i][1]*S),int(pts[i+1][0]*S),int(pts[i+1][1]*S)),
               fill=(255,255,255,150), width=int(6*S))
    for n,(cx,cy) in node_xy.items():
        if n==5:
            g = vgrad_round(56,56,14,GREEN_T,GREEN_B,GREEN_LINE,2)
        else:
            g = vgrad_round(50,50,12,(150,150,146,255),(108,110,104,255),(92,94,88,255),2)
        im.alpha_composite(g,(int((cx-28)*S),int((cy-28)*S)))
        ctext(ImageDraw.Draw(im),cx,cy,str(n),F_NUM,WHITE if n==5 else (245,240,232,255))
        # no locks on 1-4 (completed)
    paste_asset(im, load("mascot.png"), 232, 470, 78, 80)
    ctext(d, 268, 452, "当前关卡", F_SMALL, BROWN)
    # main button
    button(im, 60, 660, 270, 50, "继续第5关", fnt=F_H1)
    bottom_nav(im, "首页")
    watermark(im)
    return im

# =====================================================================
# 04 level select
# =====================================================================
def screen04():
    im = base_screen()
    d = ImageDraw.Draw(im)
    topbar_store_levels(im, "关卡", "600", "关卡")
    # summary card
    panel(im, 30, 66, 330, 92, radius=16)
    ctext(d, 195, 88, "第一章", F_H2, BROWN)
    ctext(d, 195, 112, "通关4/12", F_BODY, BROWN2)
    progress_bar(im, 60, 136, 270, 9, 4/12)
    # selection panel
    panel(im, 24, 172, 342, 196, radius=18)
    ctext(d, 195, 194, "选择关卡", F_H2, BROWN)
    gx0, gy0 = 46, 214
    cw, ch, gap = 46, 44, 8
    for idx in range(12):
        r, c = divmod(idx,6)
        x = gx0 + c*(cw+gap); y = gy0 + r*(ch+gap)
        n = idx+1
        if n<=4:
            g = vgrad_round(cw,ch,10,GREEN_T,GREEN_B,GREEN_LINE,1.5)
            im.alpha_composite(g,(int(x*S),int(y*S)))
            dd=ImageDraw.Draw(im)
            ctext(dd,x+cw/2,y+ch/2,str(n),F_NUM2,WHITE)
            # check mark
            dd.ellipse((int((x+cw-13)*S),int((y+2)*S),int((x+cw-2)*S),int((y+13)*S)),fill=(255,255,255,230))
            dd.line((int((x+cw-11)*S),int((y+7)*S),int((x+cw-8)*S),int((y+10)*S),int((x+cw-4)*S),int((y+4)*S)),
                    fill=GREEN_LINE,width=int(1.6*S))
        elif n==5:
            g = vgrad_round(cw,ch,10,GREEN_T,GREEN_B,(255,236,120,255),3)
            im.alpha_composite(g,(int(x*S),int(y*S)))
            ctext(ImageDraw.Draw(im),x+cw/2,y+ch/2,str(n),F_NUM2,WHITE)
        else:
            g = vgrad_round(cw,ch,10,(176,180,172,255),(140,145,138,255),(120,124,118,255),1.5)
            im.alpha_composite(g,(int(x*S),int(y*S)))
            dd=ImageDraw.Draw(im)
            paste_asset(im, load("icon-lock.png"), x+cw/2-8, y+ch/2-11, 16, 22)
    ctext(d, 195, 354, "点击当前关卡，或重温已完成关卡", F_TINY, BROWN2)
    # chapter cards
    chapters=[("第一章","4/12"),("第二章","待解锁"),("第三章","待解锁")]
    for i,(nm,st) in enumerate(chapters):
        y=380+i*50
        panel(im, 24, y, 342, 42, radius=14)
        paste_asset(im, load("tile-green.png"), 30, y+3, 36, 36)
        ctext(d, 210, y+14, nm, F_H2, BROWN)
        ctext(d, 210, y+31, "章节 · "+st, F_TINY, BROWN2)
    bottom_nav(im, "关卡")
    watermark(im)
    return im

# =====================================================================
# 05 store
# =====================================================================
def screen05():
    im = base_screen()
    d = ImageDraw.Draw(im)
    topbar_store_levels(im, "道具", "600", "道具")
    cards=[
        ("icon-hint.png","提示","高亮可移出的方块"),
        ("icon-hammer.png","锤子","选择并移除一个方块"),
        ("icon-magic.png","魔法","自动移除最多3个方块"),
    ]
    for i,(ic,name,desc) in enumerate(cards):
        y=68+i*168
        panel(im, 20, y, 350, 152, radius=18)
        paste_asset(im, load(ic), 38, y+24, 46, 54)
        ctext(d, 195, y+34, name, F_H1, BROWN)
        ctext(d, 195, y+62, desc, F_BODY, BROWN2)
        ctext(d, 300, y+62, "×2", F_H2, CORAL)
        paste_asset(im, load("icon-coin.png"), 44, y+104, 18, 18)
        ltext(d, 68, y+113, "300 金币", F_BODY, BROWN)
        button(im, 246, y+100, 96, 34, "购买", fnt=F_H2)
    bottom_nav(im, "道具")
    watermark(im)
    return im

# =====================================================================
# run
# =====================================================================
def save(im, name):
    im.convert("RGB").save(os.path.join(OUT, name), "PNG")
    print("saved", name, im.size)

def main():
    # 01
    im = base_screen("garden-play.png")
    draw_hud(im, hint_stock=2, tip="轻点方块，沿箭头方向移出", highlight=False)
    save(im, "01_方块闯关_进行中_效果图.png")

    save(screen02(), "02_方块闯关_通关结算_效果图.png")
    save(screen03(), "03_关卡进度_首页_效果图.png")
    save(screen04(), "04_关卡进度_关卡选择_效果图.png")
    save(screen05(), "05_道具辅助_道具商店_效果图.png")

    # 06 from same board function
    im = base_screen("garden-play.png")
    draw_hud(im, hint_stock=1, tip="试试这块，它可以向左移出", highlight=True)
    save(im, "06_道具辅助_局内提示_效果图.png")

if __name__ == "__main__":
    main()
