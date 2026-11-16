# -*- coding: utf-8 -*-
"""用真实抠图素材全量重组关卡地图页（941x1672 设计尺寸），并与用户参考并排。"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 941, 1672
FB = 'C:/Windows/Fonts/msyhbd.ttc'
FR = 'C:/Windows/Fonts/msyh.ttc'
def font(sz, bold=True):
    return ImageFont.truetype(FB if bold else FR, sz)

def trim_a(im):
    """按 alpha 裁到主体外接框，返回 (裁图, 原图内偏移)"""
    a = im.getchannel('A')
    bb = a.getbbox()
    if not bb:
        return im, (0, 0, im.width, im.height)
    return im.crop(bb), bb

def put(canvas, src, box, fit='contain'):
    """把透明素材按主体外接框缩放后放进 box（box 是设计坐标）"""
    im = Image.open(os.path.join(ROOT, 'assets', src)).convert('RGBA')
    im, bb = trim_a(im)
    bw, bh = box[2] - box[0], box[3] - box[1]
    s = min(bw / im.width, bh / im.height) if fit == 'contain' else max(bw / im.width, bh / im.height)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    canvas.alpha_composite(im, (box[0] + (bw - im.width) // 2, box[1] + (bh - im.height) // 2))

def number(d, cx, cy, text, size, color=(255,255,255), stroke=(70,60,50), sw=4):
    f = font(size)
    d.text((cx, cy + 3), text, font=f, fill=(0,0,0,90), anchor='mm')  # 轻微投影
    d.text((cx, cy), text, font=f, fill=color, stroke_width=sw, stroke_fill=stroke, anchor='mm')

def round_card(d, box, r, fill, shadow=True, outline=(255,255,255,255)):
    if shadow:
        tmp = Image.new('RGBA', (W, H), (0,0,0,0))
        td = ImageDraw.Draw(tmp)
        td.rounded_rectangle((box[0],box[1]+7,box[2],box[3]+7), radius=r, fill=(90,65,35,75))
        tmp = tmp.filter(ImageFilter.GaussianBlur(9))
        d._image.alpha_composite(tmp)
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=3)

def main():
    bg = Image.open(os.path.join(ROOT,'assets','bg_garden_r2.png')).convert('RGBA').resize((W,H))
    d = ImageDraw.Draw(bg)

    # 中央浅色通道（半透明，压掉过重石板纹理，给节点让路）
    road = Image.new('RGBA',(W,H),(0,0,0,0)); rd=ImageDraw.Draw(road)
    rd.rounded_rectangle((430,0,512,1230), radius=36, fill=(255,252,238,95))
    road = road.filter(ImageFilter.GaussianBlur(12))
    bg.alpha_composite(road)
    d = ImageDraw.Draw(bg)

    # 关卡节点：灰锁40/39, 紫38, 绿37当前, 红36+挑战
    node_box = lambda cy, s, cx=470: (cx - s//2, cy - s//2, cx + s//2, cy + s//2)
    put(bg, 'parts/07_node_lock.png', node_box(102, 118))
    number(d, 470, 102, '40', 56)
    put(bg, 'parts/07_node_lock.png', node_box(224, 118))
    number(d, 470, 224, '39', 56)
    put(bg, 'parts/08_node_violet.png', node_box(346, 118))
    number(d, 470, 346, '38', 56)
    put(bg, 'parts/09_node_current.png', node_box(472, 132))
    number(d, 470, 472, '37', 62)
    # 当前关卡气泡
    d.rounded_rectangle((556,448,662,492), radius=14, fill=(255,253,247,255), outline=(240,228,208,255), width=2)
    d.polygon([(556,464),(544,470),(556,476)], fill=(255,253,247,255))
    d.text((609,470),'当前关卡',font=font(19),fill=(130,105,68),anchor='mm')

    put(bg, 'parts/10_node_red.png', node_box(610, 116, 300))
    number(d, 300, 610, '36', 54)
    # 挑战节点 = 红节点 + 文字
    put(bg, 'parts/10_node_red.png', node_box(610, 116, 640))
    d.text((640,610),'挑战',font=font(34),fill=(255,255,255),stroke_width=4,stroke_fill=(150,60,45),anchor='mm')

    # 吉祥物
    put(bg, 'parts/00_mascot.png', (415,548,525,670))

    # 右上票券：底胶囊 + 票 + 加号（用真实素材）+ 数字3
    put(bg, 'parts/06_ticket.png', (690,48,930,140))
    d.text((845,94),'3',font=font(34),fill=(120,92,45),anchor='mm')

    # 右侧任务圆钮（剪贴板素材 + 矢量圆底 + 标签）
    task = Image.open(os.path.join(ROOT,'samples','fix_icon_task.png')).convert('RGBA')
    put(bg, 'fix_icon_task.png', (752,232,936,430))
    d.rounded_rectangle((778,404,912,444),radius=18,fill=(255,252,242,255),outline=(255,255,255,255),width=3)
    d.text((845,424),'任务',font=font(22),fill=(138,106,56),anchor='mm')

    # 成就奖杯：矢量圆底 + 真实奖杯
    ax,ay,ar = 844,392,62
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(sh)
    sd.ellipse((ax-ar,ay-ar+6,ax+ar,ay+ar+6),fill=(70,50,25,70)); sh=sh.filter(ImageFilter.GaussianBlur(8)); bg.alpha_composite(sh)
    d=ImageDraw.Draw(bg)
    d.ellipse((ax-ar,ay-ar,ax+ar,ay+ar),fill=(255,251,240,255),outline=(255,255,255,255),width=3)
    d.ellipse((ax-ar+6,ay-ar+6,ax+ar-6,ay+ar-6),outline=(235,218,188,190),width=2)
    put(bg,'parts/05_trophy.png',(ax-46,ay-46,ax+46,ay+46))
    d.rounded_rectangle((ax-46,ay+48,ax+46,ay+84),radius=16,fill=(255,252,242,255),outline=(255,255,255,255),width=3)
    d.text((ax,ay+66),'成就',font=font(21),fill=(138,106,56),anchor='mm')

    # 左上设置齿轮（矢量，几何简单）
    gx,gy=68,72
    d.ellipse((gx-30,gy-30,gx+30,gy+30),fill=(255,252,242,255),outline=(255,255,255,255),width=3)
    import math
    pts=[]
    for i in range(16):
        a=i*math.pi/8; r=24 if i%2==0 else 18
        pts.append((gx+math.cos(a)*r, gy+math.sin(a)*r))
    d.polygon(pts, fill=(158,132,88,255))
    d.ellipse((gx-9,gy-9,gx+9,gy+9), fill=(246,232,206,255))

    # 绿色主按钮（真实抠图素材 mat_btn_cta）
    put(bg,'mat_btn_cta.png',(150,1200,792,1408))

    # 点击提示
    d.text((470,1452),'点击开始游戏',font=font(21),fill=(255,250,232,255),stroke_width=3,stroke_fill=(110,85,50,255),anchor='mm')

    # 底部导航：一整块奶油底板 + 4个真实图标 + 文字
    d.rounded_rectangle((30,1478,912,1656),radius=34,fill=(255,251,240,255),outline=(255,255,255,255),width=4)
    tabs=[('首页','parts/01_tab_home.png',True),('图库','parts/02_tab_gallery.png',False),
          ('皮肤','parts/03_tab_skin.png',False),('每日','parts/04_tab_daily.png',False)]
    for i,(name,src,active) in enumerate(tabs):
        cx=30+(i+0.5)*(882/4)
        put(bg,src,(int(cx-48),1494,int(cx+48),1582))
        d.text((cx,1614),name,font=font(25),fill=(138,106,56),anchor='mm')
        if active:
            d.rounded_rectangle((cx-26,1638,cx+26,1644),radius=3,fill=(90,190,58,255))

    bg.convert('RGB').save(os.path.join(ROOT,'samples','map_full_reassembled.png'))

    # 并排对比
    ref=Image.open(os.path.join(ROOT,'ref','01_user_map.jpg')).convert('RGB')
    hh=900; rr=ref.resize((int(ref.width*hh/ref.height),hh),Image.LANCZOS)
    bb=bg.convert('RGB').resize((int(W*hh/H),hh),Image.LANCZOS)
    pad,top=20,50
    cv=Image.new('RGB',(rr.width+bb.width+pad*3,hh+top+pad),(28,26,24));dd=ImageDraw.Draw(cv)
    cv.paste(rr,(pad,top));cv.paste(bb,(pad*2+rr.width,top))
    dd.text((pad+4,14),'用户参考',font=font(24),fill=(235,228,214))
    dd.text((pad*2+rr.width+4,14),'全量真实素材重组',font=font(24),fill=(235,228,214))
    cv.save(os.path.join(ROOT,'samples','map_full_compare.png'))
    print('saved map_full_reassembled.png / map_full_compare.png')

if __name__=='__main__':
    main()
