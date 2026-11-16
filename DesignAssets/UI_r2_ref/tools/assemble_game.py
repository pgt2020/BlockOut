# -*- coding: utf-8 -*-
"""用真实方块素材 + 真实关卡数据重组对局页（保留多格连体块、一块一箭头的真实规则）。"""
import os, json, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 941, 1672
FB='C:/Windows/Fonts/msyhbd.ttc'
def font(sz): return ImageFont.truetype(FB, sz)

FAM2TILE = {
    'orange':'tile_orange', 'mint':'tile_green', 'violet':'tile_blue',
    'pink':'tile_coral', 'yellow':'tile_yellow', 'blue':'tile_blue',
    'stone':'tile_grey',
}
DIRV = {
    'up':    (0,-1,-math.pi/2),
    'right': (1,0,0),
    'down':  (0,1,math.pi/2),
    'left':  (-1,0,math.pi),
}

def trim(im):
    bb = im.getchannel('A').getbbox()
    return im.crop(bb) if bb else im

def tile_img(fam):
    return trim(Image.open(os.path.join(ROOT,'assets','tiles',FAM2TILE.get(fam,'tile_grey')+'.png')).convert('RGBA'))

def arrow_layer(size, direction):
    """白色箭头（原生矢量，方向精确）"""
    lay = Image.new('RGBA',(size,size),(0,0,0,0)); d=ImageDraw.Draw(lay)
    cx=cy=size/2; L=size*0.32; w=size*0.13
    # 画一个朝上的箭头，再按方向旋转
    pts=[(cx,cy-L),(cx+w,cy-L*0.25),(cx+w*0.42,cy-L*0.25),
         (cx+w*0.42,cy+L*0.75),(cx-w*0.42,cy+L*0.75),(cx-w*0.42,cy-L*0.25),
         (cx-w,cy-L*0.25)]
    d.polygon(pts, fill=(255,255,255,250))
    d.line(pts+[pts[0]], fill=(255,255,255,255), width=max(2,int(size*0.03)), joint='curve')
    # 轻微阴影描边
    deg = {'up':0,'right':90,'down':180,'left':270}[direction]
    return lay.rotate(-deg, resample=Image.BICUBIC, center=(cx,cy))

def main():
    d0 = json.load(open(os.path.join(ROOT,'data','board.json'),encoding='utf-8'))
    Wd,Hd = d0['cols'], d0['rows']
    # 棋盘区域
    BX,BY,BS = 70, 265, 800
    Hd = d0['rows']
    cell = min(BS/Wd, BS/Hd)
    gw,gh = int(cell*Wd), int(cell*Hd)
    BX = int((W-gw)/2); BY = int(265 + (BS-gh)/2)
    canvas = Image.new('RGBA',(W,H),(0,0,0,0))
    d = ImageDraw.Draw(canvas)

    # 背景：浅奶油点阵（参考第4屏）
    for y in range(H):
        pass
    bg = Image.new('RGBA',(W,H),(255,253,247,255)); bd=ImageDraw.Draw(bg)
    # 渐变底
    for y in range(0,H,4):
        t=y/H; c=(int(255-6*t),int(253-10*t),int(247-18*t),255)
        bd.rectangle((0,y,W,y+4),fill=c)
    # 点阵
    for yy in range(20,H,26):
        for xx in range(20,W,26):
            bd.ellipse((xx,yy,xx+2,yy+2),fill=(214,193,163,90))
    canvas=bg

    # 顶部 HUD
    d=ImageDraw.Draw(canvas)
    d.ellipse((30,30,98,98),fill=(255,252,242,255),outline=(255,255,255,255),width=3)
    d.polygon([(58,64),(80,44),(80,56),(64,64),(80,72),(80,84)],fill=(155,130,88,255))
    d.text((W//2,64),'第 1 关',font=font(34),fill=(122,96,56),anchor='mm')
    d.rounded_rectangle((843,30,911,98),radius=20,fill=(255,252,242,255),outline=(255,255,255,255),width=3)
    d.rounded_rectangle((866,52,875,80),radius=3,fill=(169,138,92,255))
    d.rounded_rectangle((881,52,890,80),radius=3,fill=(169,138,92,255))

    # 心 x4 (3满1空)
    def heart(draw,cx,cy,s,fill):
        pts=[]
        for a in [i*2*math.pi/60 for i in range(60)]:
            x=16*math.sin(a)**3; y=13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a)
            pts.append((cx+x*s/32, cy-y*s/32))
        draw.polygon(pts,fill=fill,outline=(255,255,255,255))
    for i in range(4):
        heart(d,68+i*46,136,34,(242,96,92,255) if i<3 else (228,217,198,255))
    # 进度条
    d.rounded_rectangle((270,124,806,150),radius=13,fill=(234,220,196,255),outline=(255,255,255,255),width=2)
    d.rounded_rectangle((272,126,272+int(532*0.65),148),radius=11,fill=(95,194,58,255))
    d.text((868,137),'65%',font=font(24),fill=(169,138,92),anchor='mm')

    # 棋盘托盘
    d.rounded_rectangle((BX-14,BY-14,BX+gw+14,BY+gh+14),radius=30,
                        fill=(255,252,244,255),outline=(255,255,255,255),width=4)
    # 点阵底
    pbd=ImageDraw.Draw(canvas)
    for yy in range(BY+10,BY+gh-10,20):
        for xx in range(BX+10,BX+gw-10,20):
            pbd.ellipse((xx,yy,xx+2,yy+2),fill=(214,193,163,80))

    # 方块：按真实 blocks，块内每格贴同源方块素材，箭头只在 arrow 格（真实规则）
    tile_cache={}
    for b in d0['blocks']:
        fam=b['family']; tile=tile_img(fam)
        for (c,r) in b['cells']:
            x=BX+c*cell; y=BY+r*cell
            t=tile.resize((int(cell*0.99),int(cell*0.99)),Image.LANCZOS)
            canvas.alpha_composite(t,(int(x+cell*0.005),int(y+cell*0.005)))
        # 箭头放该块 arrow 格
        ac,ar=b['arrow']
        ax=BX+ac*cell; ay=BY+ar*cell
        al=arrow_layer(int(cell),b['dir'])
        canvas.alpha_composite(al,(int(ax),int(ay)))

    # 底部三道具卡（用真实抠图图标 + 矢量奶油耗材）
    d=ImageDraw.Draw(canvas)
    d.rounded_rectangle((30,1060,912,1270),radius=32,fill=(255,251,240,255),outline=(255,255,255,255),width=4)
    tools=[('提示','assets/icons/bulb.png','3',(238,88,70,255)),
           ('锤子','assets/icons/hammer.png','2',(150,190,70,255)),
           ('炸弹','assets/icons/bomb.png','1',(238,88,70,255))]
    for i,(name,src,cnt,badge_col) in enumerate(tools):
        cx=30+(i+0.5)*(882/3)
        d.rounded_rectangle((cx-130,1078,cx+130,1258),radius=24,fill=(255,253,246,255),outline=(240,226,204,255),width=2)
        icon=trim(Image.open(os.path.join(ROOT,src)).convert('RGBA'))
        icon=icon.resize((88,88),Image.LANCZOS)
        canvas.alpha_composite(icon,(int(cx-44),int(1086)))
        d=ImageDraw.Draw(canvas)
        d.text((cx,1240),name,font=font(26),fill=(138,106,56),anchor='mm')
        d.ellipse((cx+66,1072,cx+108,1114),fill=badge_col,outline=(255,255,255,255),width=3)
        d.text((cx+87,1093),cnt,font=font(24),fill=(255,255,255),anchor='mm')

    out=os.path.join(ROOT,'samples','game_full_reassembled.png')
    canvas.convert('RGB').save(out)

    # 与参考第4屏并排
    ref=Image.open(os.path.join(ROOT,'ref','02_game_crop.png')).convert('RGB')
    hh=900; rr=ref.resize((int(ref.width*hh/ref.height),hh),Image.LANCZOS)
    bb=canvas.convert('RGB').resize((int(W*hh/H),hh),Image.LANCZOS)
    pad,top=20,50
    cv=Image.new('RGB',(rr.width+bb.width+pad*3,hh+top+pad),(28,26,24));dd=ImageDraw.Draw(cv)
    cv.paste(rr,(pad,top));cv.paste(bb,(pad*2+rr.width,top))
    dd.text((pad+4,14),'用户参考：对局页',font=font(24),fill=(235,228,214))
    dd.text((pad*2+rr.width+4,14),'真实素材+真实关卡重组',font=font(24),fill=(235,228,214))
    cv.save(os.path.join(ROOT,'samples','game_full_compare.png'))
    print('saved',out)

if __name__=='__main__': main()
