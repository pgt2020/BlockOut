# -*- coding: utf-8 -*-
"""
BlockOut TapAway · 5 屏软胶风格还原稿 (v9)
按实机 1125x2436 布局，复用 UI_v7 软胶组件 + tile_kit 方块光照，风格与第一版设计统一。
支持 --round N 输出到 qa/roundN/，用于逐轮截图自检收敛。
不接入 Unity、不编译、不运行。
"""
import os, sys, io, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

V7 = r"E:\UnityProject\MutiplayGame\BlockOut\DesignAssets\UI_v7"
sys.path.insert(0, V7)
import gen_ui as G

HERE = os.path.dirname(os.path.abspath(__file__))
SCREENS = os.path.join(HERE, "screens")

# ---------- 画布（跟实机一致） ----------
CW, CH = 1125, 2436
FB = r"C:\Windows\Fonts\msyhbd.ttc"
FR = r"C:\Windows\Fonts\msyh.ttc"

def font(sz, bold=True):
    try:
        return ImageFont.truetype(FB if bold else FR, max(8, int(sz)))
    except Exception:
        return ImageFont.load_default()

def text(d, xy, s, size, fill, stroke=None, sw=2, bold=True, anchor="la", sh=False):
    f = font(size, bold)
    kw = dict(font=f, fill=fill, anchor=anchor)
    if stroke:
        kw.update(stroke_width=sw, stroke_fill=stroke)
    if sh:
        d.text((xy[0] + 2, xy[1] + 4), s, font=f, fill=(92, 58, 36, 120), anchor=anchor)
    d.text(xy, s, **kw)

def text_auto(d, box, s, size, fill, **kw):
    """在给定宽度内自适应缩字号，防裁切。box=(x,y,w,h) 左上基准。"""
    x, y, w, h = box
    fsz = size
    while fsz > 12:
        f = font(fsz, kw.get("bold", True))
        bb = d.textbbox((0, 0), s, font=f)
        if bb[2] - bb[0] <= w:
            break
        fsz -= 2
    text(d, (x, y), s, fsz, fill, anchor="la", **kw)

# ---------- 通用绘制 ----------
def cream_bg(top=(255, 247, 229), bot=(244, 219, 182), dots=True):
    a = np.zeros((CH, CW, 4), np.uint8)
    t = np.linspace(0, 1, CH)[:, None, None]
    col = np.array(top, float)[None, None, :] * (1 - t) + np.array(bot, float)[None, None, :] * t
    a[:, :, :3] = np.repeat(np.clip(col, 0, 255), CW, axis=1).astype(np.uint8)
    a[:, :, 3] = 255
    if dots:
        yy, xx = np.mgrid[0:CH, 0:CW]
        dm = ((xx % 32 == 6) & (yy % 32 == 6))
        a[:, :, :3][dm] = (a[:, :, :3][dm].astype(float) * .92 +
                           np.array([240, 216, 184]) * .08).astype(np.uint8)
    return Image.fromarray(a, "RGBA")

def dim(canvas, alpha=140):
    ov = Image.new("RGBA", (CW, CH), (58, 40, 28, alpha))
    canvas.alpha_composite(ov)

def comp(canvas, img, xy):
    canvas.alpha_composite(img, (int(xy[0]), int(xy[1])))

def rr(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)

# ---------- 软胶方块棋盘（复用 tile_kit 光照模板） ----------
PAL = {
    "green": (139, 193, 91), "yellow": (246, 186, 74), "blue": (97, 161, 220),
    "pink": (247, 143, 147), "charcoal": (104, 92, 76), "cream": (233, 217, 198),
}
CMAP = {"G": "green", "Y": "yellow", "B": "blue", "P": "pink", "C": "charcoal", "W": "cream"}
DMAP = {"U": "up", "D": "down", "L": "left", "R": "right", "X": "cross"}
SRC = [
    "-- -- GU -- -- -- GU YR -- --",
    "-- GU YX GU -- GU YR YR GU --",
    "BD YX YR YU GU PL YR YR BD --",
    "PL YR YU CU WU WU CU YU YR YR",
    "PL YU CU WU WU WU WU CU YR YR",
    "BD YU WD WU WU WU WU WX YU YR",
    "-- BD BD BD WU WU GU PL PL --",
    "-- -- -- BD WU GU BD -- -- --",
]
ROT = {"up": 0, "right": 90, "down": 180, "left": 270, "cross": 0}

def _light_template(S):
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    grad = 1.08 - 0.30 * (yy / (S - 1)) ** 1.6
    hl = 0.18 * np.exp(-((yy - S * 5 / 32) / (S * 4.6 / 32)) ** 2) * np.exp(-((xx - S / 2) / (S * .44)) ** 2)
    sh = 0.07 * np.exp(-((yy - (S - S * 2.5 / 32)) / (S * 2.3 / 32)) ** 2)
    L = grad + hl - sh
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, S - 1, S - 1), radius=max(2, int(S * .10)), fill=255)
    inner = np.asarray(m.filter(ImageFilter.GaussianBlur(S * .025))).astype(float) / 255 > .5
    er = inner.copy()
    for _ in range(max(1, int(S / 16))):
        e = er.copy()
        e[1:, :] &= er[:-1, :]; e[:-1, :] &= er[1:, :]
        e[:, 1:] &= er[:, :-1]; e[:, :-1] &= er[:, 1:]
        er = e
    L[inner & ~er] *= .70
    L[~inner] = .74
    return np.clip(L, .55, 1.22), inner

def _arrow_img(size, kind="up"):
    S = size * 4
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    u = S / 24.0
    if kind == "up":
        poly = [(12*u, 2.5*u), (20.5*u, 11*u), (15.5*u, 11*u),
                (15.5*u, 21*u), (8.5*u, 21*u), (8.5*u, 11*u), (3.5*u, 11*u)]
    else:
        poly = [(10*u,1.5*u),(14*u,1.5*u),(14*u,9*u),(22.5*u,9*u),(22.5*u,13*u),
                (14*u,13*u),(14*u,22.5*u),(10*u,22.5*u),(10*u,13*u),(1.5*u,13*u),(1.5*u,9*u),(10*u,9*u)]
    d.polygon(poly, fill=255)
    core = (np.asarray(m).astype(float) / 255 > .5).astype(np.uint8) * 255
    return Image.fromarray(core, "L").resize((size, size), Image.LANCZOS)

def soft_tile(size, color, direction):
    S = size
    L, inner = _light_template(S)
    tint = np.array(color, float)
    rgb = np.clip(tint[None, None, :] * L[:, :, None], 0, 255).astype(np.uint8)
    al = np.where(inner, 255, 255).astype(np.uint8)  # 方形不透明，紧贴无缝
    im = Image.fromarray(np.dstack([rgb, al]), "RGBA")
    if direction != "none":
        ai = _arrow_img(int(size * .60), "cross" if direction == "cross" else "up")
        deg = ROT[direction]
        if deg:
            ai = ai.rotate(-deg, resample=Image.BICUBIC)
        off = (size - ai.width) // 2
        wh = np.asarray(ai).astype(float) / 255
        ar = np.zeros((size, size, 4), np.uint8)
        ar[off:off+ai.height, off:off+ai.width, :3] = (245, 241, 230)
        ar[off:off+ai.height, off:off+ai.width, 3] = (wh * 235).astype(np.uint8)
        im.alpha_composite(Image.fromarray(ar, "RGBA"))
    return im

def board_img(cell, cols=10, rows=8):
    W, H = cols * cell, rows * cell
    out = Image.new("RGBA", (W, H), (250, 237, 216, 255))
    d = ImageDraw.Draw(out)
    step = max(18, cell // 4)
    for y in range(0, H + step, step):
        for x in range(0, W + step, step):
            d.ellipse((x-2, y-2, x+2, y+2), fill=(238, 219, 193, 255))
    for r in range(rows):
        for c in range(cols):
            parts = SRC[r].split() if r < len(SRC) else []
            tok = parts[c] if c < len(parts) else "--"
            if tok == "--":
                continue
            color = PAL[CMAP[tok[0]]]
            direction = DMAP[tok[1]]
            im = soft_tile(cell - 2, color, direction)
            out.alpha_composite(im, (c * cell + 1, r * cell + 1))
    return out

# ---------- 组件（复用 gen_ui 绘制原语，修复大尺寸下的字号/图标问题） ----------
def make_button(w, h, label, variant="green"):
    """自绘按钮：字号随高度动态，无 gen_ui 的 27px 硬上限。"""
    r = min(h * .42, h / 2 - 2)
    c = G.newc(w, h)
    G.paste(c, G.shadow_layer(w, h, r, "round", dy=3.5, blur=3.5, alpha=.28))
    if variant == "green":
        top, bot, line, txt = G.T["green_light"], G.T["green"], G.T["green_line"], G.T["white"]
    elif variant == "gold":
        top, bot, line, txt = G.lighten(G.T["gold"], .30), G.T["gold"], G.T["gold_line"], G.T["cocoa"]
    else:
        top, bot, line, txt = G.T["cream_light"], G.T["cream_deep"], G.T["brown_line"], G.T["cocoa"]
    G.paste(c, G.grad_layer(w, h, r, top, bot, "round", ow=2.6, line=line))
    hl = G.newc(w, h)
    ImageDraw.Draw(hl).rounded_rectangle((int(7*G.S), int(5*G.S), int((w-7)*G.S), int(h*.38*G.S)),
                                          radius=int(h*.18*G.S), fill=(255,255,255,60))
    c.alpha_composite(hl)
    G.centered_text(c, w, h, label, h * .40, txt,
                    stroke=G.darken(line, .7) if variant=="green" else None,
                    sw=.05, shadow=(variant == "green"))
    return G.finish(c, w, h)

def make_icon_btn(sz, kind, variant="cream"):
    """自绘圆按钮，pause 等用矢量图标，不再回退成文字。"""
    c = G.newc(sz, sz)
    G.paste(c, G.shadow_layer(sz, sz, sz/2, "circle", dy=2.6, blur=2.6, alpha=.26))
    top, bot, line = G.T["cream_light"], G.T["cream_deep"], G.T["brown_line"]
    G.paste(c, G.grad_layer(sz, sz, sz/2, top, bot, "circle", ow=2.2, line=line))
    d = ImageDraw.Draw(c)
    cx = cy = sz * G.S / 2
    if kind == "pause":
        bar_w, bar_h, gap = sz*.13*G.S, sz*.42*G.S, sz*.13*G.S
        col = G.T["brown_line"] + (255,)
        d.rounded_rectangle((cx-gap/2-bar_w, cy-bar_h/2, cx-gap/2, cy+bar_h/2), radius=bar_w*.4, fill=col)
        d.rounded_rectangle((cx+gap/2, cy-bar_h/2, cx+gap/2+bar_w, cy+bar_h/2), radius=bar_w*.4, fill=col)
    else:
        G.draw_icon(c, sz, sz, kind, scale=.50, color=G.T["cocoa"])
    return G.finish(c, sz, sz)

def make_panel(w, h, kind="panel"):
    return G.panel(w, h, kind)

def make_progress(w, h, ratio):
    r = h / 2.0
    c = G.newc(w, h)
    G.paste(c, G.grad_layer(w, h, r, (226,206,176),(206,180,146), "round", ow=1.6, line=G.T["brown_line"], highlight=False))
    fw = max(h, w * ratio)
    G.paste(c, G.grad_layer(fw, h-6, (h-6)/2, G.T["green_light"], G.T["green"], "round", ow=1.2, line=G.T["green_line"]), (3,3))
    return G.finish(c, w, h)

# =========================================================
# 屏 1：游戏主界面（关键：棋盘必须填满软胶方块）
# =========================================================
def screen_game():
    c = cream_bg()
    d = ImageDraw.Draw(c)
    # 顶部标题（单一木牌，无双层）
    make_panel_t = make_panel(280, 118, "wood")
    comp(c, make_panel_t, (36, 122))
    text(d, (176, 181), "第 4 关", 66, (255, 246, 224, 255), stroke=(126, 76, 36, 255), sw=2, bold=True, anchor="mm")
    comp(c, make_icon_btn(112, "pause"), (968, 124))
    # 红心
    hb = G.hud_pill(360, 96, "hearts", "")
    hb = hb.resize((420, 112), Image.LANCZOS)
    comp(c, hb, ((CW - 420) // 2, 268))
    # 进度条 + 65%
    pb = make_progress(880, 58, .65)
    comp(c, pb, (60, 418))
    text(d, (1035, 447), "65%", 46, (92, 58, 36, 255), bold=True, anchor="lm")
    # 棋盘面板（点阵底 + 软胶方块）
    board_panel = make_panel(1053, 1450, "dots")
    comp(c, board_panel, (36, 528))
    bimg = board_img(102, 10, 8)  # 1020x816
    comp(c, bimg, ((CW - 1020) // 2, 640))
    # 底部道具栏
    bar = make_panel(1053, 300, "panel")
    comp(c, bar, (36, 2020))
    props = [("bulb", "8"), ("hammer", "2"), ("bomb", "1"), ("grid", "3")]
    pxs = [78, 332, 586, 840]
    for (ic, num), px in zip(props, pxs):
        cd = G.newc(220, 220)
        G.paste(cd, G.shadow_layer(220, 220, 34, "round", dy=3, blur=3, alpha=.26))
        G.paste(cd, G.grad_layer(220, 220, 34, G.T["cream_light"], G.T["cream_deep"], "round", ow=2.4, line=G.T["brown_line"]))
        G.draw_icon(cd, 220, 220, ic, .46, G.T["cocoa"])
        ic_img = G.finish(cd, 220, 220).resize((228, 228), Image.LANCZOS)
        comp(c, ic_img, (px, 2054))
        # 角标
        badge = G.circle_button(66, 66, number=num, variant="red" if num in ("1", "3") else "gold")
        comp(c, badge.resize((72, 72), Image.LANCZOS), (px + 170, 2048))
        text(d, (px + 114, 2312), {"bulb":"提示","hammer":"锤子","bomb":"炸弹","grid":"重排"}[ic], 34,
             (120, 84, 56, 255), bold=True, anchor="mm")
    return c

# =========================================================
# 屏 2：加载页（去掉写实照片，改程序化软胶画廊）
# =========================================================
def screen_loading():
    c = cream_bg((255, 244, 218), (238, 205, 160))
    d = ImageDraw.Draw(c)
    # 顶部画架软胶框
    panel = make_panel(940, 1180, "wood")
    comp(c, panel, (92, 300))
    # 内画布
    inner = make_panel(820, 1040, "dots")
    comp(c, inner, (152, 370))
    # 四色箭头 logo（2x2 软胶方块）
    cols = [PAL["green"], PAL["yellow"], PAL["blue"], PAL["pink"]]
    dirs = ["up", "right", "left", "down"]
    bx, by, bs, gap = 400, 600, 160, 18
    for i in range(4):
        t = soft_tile(bs, cols[i], dirs[i])
        comp(c, t, (bx + (i % 2) * (bs + gap), by + (i // 2) * (bs + gap)))
    # 艺术字
    text(d, (CW//2, 1080), "点击画廊", 118, (255, 248, 226, 255),
         stroke=(120, 72, 40, 255), sw=10, bold=True, anchor="mm", sh=True)
    text(d, (CW//2, 1190), "正在准备画作…", 52, (150, 104, 70, 255), bold=True, anchor="mm")
    # 进度：木框底部条 + 百分比置于条上方白底处
    pb = make_progress(720, 54, .60)
    comp(c, pb, ((CW - 720)//2, 1380))
    text(d, (CW//2, 1332), "60%", 46, (120, 84, 56, 255), bold=True, anchor="mm")
    return c

# =========================================================
# 屏 3：章节菜单（首页）
# =========================================================
def screen_menu():
    c = cream_bg((255, 247, 228), (242, 216, 178))
    d = ImageDraw.Draw(c)
    # 顶部头像 + 金币
    av = G.circle_button(120, 120, icon="palette", variant="gold")
    comp(c, av.resize((128, 128), Image.LANCZOS), (60, 110))
    coin = G.hud_pill(260, 92, "coin", "30")
    comp(c, coin.resize((280, 100), Image.LANCZOS), (CW - 340, 118))
    # 艺术字 logo（彩色方块字）
    text(d, (CW//2, 360), "PUZZLE", 72, (247, 143, 147, 255), stroke=(120, 72, 40, 255), sw=6, bold=True, anchor="mm")
    text(d, (CW//2, 470), "BLOCKOUT", 116, (255, 201, 60, 255), stroke=(120, 72, 40, 255), sw=9, bold=True, anchor="mm", sh=True)
    text(d, (CW//2, 566), "Tap Away", 66, (97, 161, 220, 255), stroke=(255, 248, 226, 255), sw=5, bold=True, anchor="mm")
    # 章节标题
    text(d, (CW//2, 760), "第 1 章 · 像素画廊", 60, (92, 58, 36, 255), bold=True, anchor="mm")
    # 关卡进度点（3 亮 9 灰）
    dots_n, done = 12, 3
    dx0, dy, ds, dg = 250, 850, 44, 22
    for i in range(dots_n):
        x = dx0 + i * (ds + dg)
        col = PAL["green"] if i < done else (226, 214, 196, 255)
        d.ellipse((x, dy, x+ds, dy+ds), fill=col, outline=(150, 110, 70, 255), width=3)
    text(d, (CW//2, 960), "通关 3/12 · 还需 9 关完成本章", 44, (120, 84, 56, 255), bold=True, anchor="mm")
    # 主按钮
    btn = make_button(820, 168, "继续第 4 关", "green")
    comp(c, btn, ((CW-820)//2, 1060))
    text(d, (CW//2, 1280), "第 1 章 · 像素画廊 · 已通关 3 关", 36, (140, 104, 74, 255), anchor="mm")
    # 次按钮
    btn2 = make_button(340, 120, "图鉴", "gold")
    comp(c, btn2, ((CW-340)//2, 1350))
    # 底部 tab
    tabbar = make_panel(1053, 190, "panel")
    comp(c, tabbar, (36, 2180))
    for i, lab in enumerate(["首页", "图鉴", "商店"]):
        col = PAL["green"] if i == 0 else (150, 110, 70, 255)
        text(d, (235 + i * 330, 2276), lab, 52, col, bold=True, anchor="mm")
    return c

# =========================================================
# 屏 4：确认弹窗
# =========================================================
def screen_confirm():
    c = screen_game()
    dim(c, 150)
    d = ImageDraw.Draw(c)
    pw, ph = 880, 760
    px, py = (CW - pw)//2, 830
    panel = make_panel(pw, ph, "panel")
    comp(c, panel, (px, py))
    text(d, (CW//2, py + 130), "请确认", 72, (92, 58, 36, 255), bold=True, anchor="mm")
    text(d, (CW//2, py + 230), "补充提示", 58, (120, 84, 56, 255), bold=True, anchor="mm")
    text(d, (CW//2, py + 360), "300 金币购买 2 个，", 48, (110, 78, 54, 255), anchor="mm")
    text(d, (CW//2, py + 430), "购买后使用一次。", 48, (110, 78, 54, 255), anchor="mm")
    b1 = make_button(330, 130, "取消", "cream")
    b2 = make_button(330, 130, "确认", "green")
    comp(c, b1, (px + 70, py + 570))
    comp(c, b2, (px + pw - 400, py + 570))
    return c

# =========================================================
# 屏 5：暂停弹窗
# =========================================================
def screen_pause():
    c = screen_game()
    dim(c, 150)
    d = ImageDraw.Draw(c)
    pw, ph = 880, 1120
    px, py = (CW - pw)//2, 660
    panel = make_panel(pw, ph, "panel")
    comp(c, panel, (px, py))
    text(d, (CW//2, py + 130), "暂停", 76, (92, 58, 36, 255), bold=True, anchor="mm")
    labels = ["继续游戏", "重开本关", "设置", "返回首页"]
    variants = ["green", "cream", "cream", "cream"]
    for i, (lab, var) in enumerate(zip(labels, variants)):
        btn = make_button(720, 140, lab, var)
        comp(c, btn, ((CW - 720)//2, py + 230 + i * 190))
    return c

SCREENS_FN = [
    ("01_game", screen_game),
    ("02_loading", screen_loading),
    ("03_menu", screen_menu),
    ("04_confirm", screen_confirm),
    ("05_pause", screen_pause),
]

def contact(save_dir):
    thumbs = []
    tw, th = 360, 780
    for name, _ in SCREENS_FN:
        im = Image.open(os.path.join(save_dir, name + ".png")).convert("RGB")
        im.thumbnail((tw, th), Image.LANCZOS)
        thumbs.append((name, im))
    sheet = Image.new("RGB", (tw * len(thumbs) + 40 * (len(thumbs)+1), th + 100), (248, 246, 242))
    sd = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(thumbs):
        x = 40 + i * (tw + 40)
        sheet.paste(im, (x, 70))
        sd.text((x, 28), name, fill=(70, 50, 35), font=font(30, True))
    sheet.save(os.path.join(save_dir, "contact_sheet.png"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=str, default="")
    args = ap.parse_args()
    save_dir = os.path.join(HERE, "qa", "round" + args.round) if args.round else SCREENS
    os.makedirs(save_dir, exist_ok=True)
    for name, fn in SCREENS_FN:
        im = fn()
        im.convert("RGB").save(os.path.join(save_dir, name + ".png"))
        print("生成", name, im.size, "->", save_dir)
    contact(save_dir)
    print("拼图", os.path.join(save_dir, "contact_sheet.png"))

if __name__ == "__main__":
    main()
