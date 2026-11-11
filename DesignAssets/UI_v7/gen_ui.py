# -*- coding: utf-8 -*-
"""
UI_v7 元件库 · 按需求参数化生成（零截图依赖）

与旧方案的根本区别：
  旧：从 ref/*_ref.png 裁一块 -> 想办法把背景标成透明（永远是「截图 + alpha 补丁」）
  新：从空白 RGBA 画布起稿，按 design token 绘制每个控件
      -> 轮廓外天然 alpha=0，透明区 RGB=0，同系列共享同一束光与同一套描边

输出保持 manifest.json 的文件名 / bbox 不变，因此 ui_final.html 无需改动即可重拼 9 屏。
"""
import os, io, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(ROOT, "assets")
BG = os.path.join(ROOT, "bg")
os.makedirs(ASSETS, exist_ok=True)
os.makedirs(BG, exist_ok=True)

S = 4  # 超采样倍数，保证降采样后边缘抗锯齿

# ============================ Design Tokens ============================
T = {
    "cream":        (255, 246, 226),
    "cream_light":  (255, 252, 240),
    "cream_deep":   (240, 214, 174),
    "cocoa":        (92, 58, 36),
    "cocoa_soft":   (139, 90, 43),
    "brown_line":   (168, 116, 68),
    "wood":         (183, 126, 66),
    "wood_dark":    (126, 76, 36),
    "green":        (139, 197, 63),
    "green_light":  (186, 226, 122),
    "green_deep":   (79, 140, 40),
    "green_line":   (58, 104, 30),
    "gold":         (255, 201, 60),
    "gold_deep":    (211, 138, 11),
    "gold_line":    (160, 96, 6),
    "red":          (240, 82, 107),
    "red_deep":     (194, 46, 72),
    "red_line":     (146, 30, 54),
    "blue":         (92, 184, 232),
    "pink":         (245, 143, 184),
    "purple":       (168, 126, 222),
    "orange":       (247, 148, 78),
    "gray":         (142, 138, 134),
    "white":        (255, 255, 255),
    "shadow":       (74, 47, 30),
}
SKIN = ["green", "gold", "blue", "pink", "purple", "orange"]

def rgb(k):
    return T[k]

def mix(a, b, t):
    return tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3))

def darken(c, f):
    return tuple(max(0, int(v * f)) for v in c)

def lighten(c, f):
    return tuple(min(255, int(v + (255 - v) * f)) for v in c)

FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_R = r"C:\Windows\Fonts\msyh.ttc"

def font(sz, bold=True):
    try:
        return ImageFont.truetype(FONT_B if bold else FONT_R, max(6, int(sz * S)))
    except Exception:
        return ImageFont.load_default()

# ============================ 绘制原语 ============================
def newc(w, h):
    return Image.new("RGBA", (max(1, int(w * S)), max(1, int(h * S))), (0, 0, 0, 0))

def finish(c, w, h):
    im = c.resize((int(w), int(h)), Image.LANCZOS)
    a = np.asarray(im).copy()
    al = a[:, :, 3]
    al[al < 6] = 0
    # 只清 LANCZOS 在角点混出的 1~3px 残余；数值过大会把圆角硬切成直角台阶
    q = max(2, min(4, int(min(w, h) * 0.02)))
    al[:q, :q] = 0; al[:q, -q:] = 0; al[-q:, :q] = 0; al[-q:, -q:] = 0
    a[:, :, :3][al == 0] = 0                 # 铁律：透明区 RGB 必须清零
    return Image.fromarray(a, "RGBA")

def _sd_round(W, H, R):
    yy, xx = np.mgrid[0:H, 0:W]
    qx = np.abs(xx - (W - 1) / 2.0) - (W / 2.0 - R)
    qy = np.abs(yy - (H - 1) / 2.0) - (H / 2.0 - R)
    sd = (np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) +
          np.minimum(np.maximum(qx, qy), 0) - R)
    return np.clip(0.5 - sd, 0, 1)

def _sd_circle(W, H):
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = (W - 1) / 2.0, (H - 1) / 2.0
    d = np.sqrt(((xx - cx) / (W / 2.0)) ** 2 + ((yy - cy) / (H / 2.0)) ** 2)
    return np.clip((1.0 - d) * min(W, H) * 0.5, 0, 1)

def grad_layer(w, h, r, top, bottom, shape="round", ow=0, line=None,
               highlight=True, inset=0):
    """垂直渐变 + 统一左上高光 + 底部暗边的实心形状，返回 RGBA 层。"""
    W, H = int(w * S), int(h * S)
    R = max(2, int(r * S))
    sd = _sd_round(W, H, R) if shape == "round" else _sd_circle(W, H)
    m = np.clip(sd, 0, 1).astype(float)

    t = np.linspace(0, 1, H)[:, None, None]
    col = np.array(top, float)[None, None, :] * (1 - t) + np.array(bottom, float)[None, None, :] * t
    col = np.repeat(col, W, axis=1)
    # 顶部柔光带（统一光源：左上）
    if highlight:
        hy = np.clip(1.0 - np.linspace(0, 1, H)[:, None] * 3.2, 0, 1)
        hx = np.clip(1.0 - np.linspace(0, 1, W)[None, :] * 1.5, 0, 1)
        glow = (hy * hx)[:, :, None] * 0.30
        col = col * (1 - glow) + 255.0 * glow
    # 底部同色暗边
    by = np.clip((np.linspace(0, 1, H)[:, None] - 0.72) * 3.4, 0, 1)
    col = col * (1 - by[:, :, None] * 0.16)

    a = m.copy()
    if line:
        ow2 = max(1, int(ow * S))
        inner = _sd_round(W - 2 * ow2, H - 2 * ow2, max(2, R - ow2)) if shape == "round" \
                else _sd_circle(W - 2 * ow2, H - 2 * ow2)
        im = np.zeros((H, W), float)
        im[ow2:H - ow2, ow2:W - ow2] = np.clip(inner, 0, 1)
        ring = np.clip(m - im, 0, 1)
        lc = np.array(line, float)[None, None, :]
        col = col * (1 - ring[:, :, None]) + lc * ring[:, :, None]
    arr = np.dstack([np.clip(col, 0, 255), a * 255]).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")

def shadow_layer(w, h, r, shape="round", dy=3.0, blur=3.2, alpha=0.30, grow=0):
    W, H = int(w * S), int(h * S)
    R = max(2, int((r + grow) * S))
    pad = int(blur * S * 2 + abs(dy) * S + 4)
    CW, CH = W + 2 * pad, H + 2 * pad
    sd = _sd_round(CW, CH, R + pad * 0) if False else None
    m = Image.new("L", (CW, CH), 0)
    d = ImageDraw.Draw(m)
    off = int(dy * S)
    if shape == "round":
        d.rounded_rectangle((pad, pad + off, pad + W - 1, pad + H - 1 + off),
                            radius=R, fill=255)
    else:
        d.ellipse((pad, pad + off, pad + W - 1, pad + H - 1 + off), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur * S))
    a = np.asarray(m).astype(float) / 255.0 * alpha
    c = np.array(T["shadow"], float)[None, None, :]
    col = np.repeat(np.repeat(c, CH, axis=0), CW, axis=1)
    arr = np.dstack([np.clip(col, 0, 255).astype(np.uint8), (a * 255).astype(np.uint8)])
    im = Image.fromarray(arr, "RGBA")
    # 裁回主画布坐标系（右下投影会略微溢出，允许保留在画布内）
    return im.crop((pad, pad, pad + W, pad + H))

def paste(base, layer, box=(0, 0)):
    base.alpha_composite(layer, (int(box[0] * S), int(box[1] * S)))

def outline_ring(base, w, h, r, color, ow=2, shape="round"):
    W, H = int(w * S), int(h * S)
    c = newc(w, h)
    d = ImageDraw.Draw(c)
    o = max(1, int(ow * S))
    if shape == "round":
        d.rounded_rectangle((0, 0, W - 1, H - 1), radius=max(2, int(r * S)),
                            outline=color + (255,), width=o)
    else:
        d.ellipse((0, 0, W - 1, H - 1), outline=color + (255,), width=o)
    base.alpha_composite(c)

def centered_text(base, w, h, text, size, color, stroke=None, sw=0.06,
                  dy=0, bold=True, shadow=False):
    if not text:
        return
    c = newc(w, h)
    d = ImageDraw.Draw(c)
    f = font(size, bold)
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    # 自适应缩字号：长文案不允许溢出画布被裁掉
    if tw > w * S * 0.90 and tw > 0:
        f = font(max(6, size * w * S * 0.90 / tw), bold)
        bb = d.textbbox((0, 0), text, font=f)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (w * S - tw) / 2 - bb[0]
    y = (h * S - th) / 2 - bb[1] + dy * S
    if shadow:
        d.text((x + 0.6 * S, y + 1.6 * S), text, font=f, fill=darken(color, 0.55) + (170,),
               stroke_width=max(1, int(sw * size * S)),
               stroke_fill=darken(color, 0.55) + (170,))
    kw = dict(font=f, fill=color + (255,))
    if stroke:
        kw["stroke_width"] = max(1, int(sw * size * S))
        kw["stroke_fill"] = stroke + (255,)
    d.text((x, y), text, **kw)
    base.alpha_composite(c)

# ============================ 矢量图标库 ============================
def icon_arrow_left(d, cx, cy, s, col):
    p = [(cx + s * .30, cy - s * .55), (cx - s * .30, cy),
         (cx + s * .30, cy + s * .55), (cx + s * .10, cy + s * .55),
         (cx - s * .48, cy), (cx + s * .10, cy - s * .55)]
    d.polygon(p, fill=col)

def icon_gear(d, cx, cy, s, col):
    r0, r1 = s * .46, s * .62
    pts = []
    for i in range(8):
        a0 = i * math.pi / 4
        for rr, aa in [(r0, a0 - .20), (r1, a0 - .13), (r1, a0 + .13), (r0, a0 + .20)]:
            pts.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa)))
    d.polygon(pts, fill=col)
    d.ellipse((cx - s * .20, cy - s * .20, cx + s * .20, cy + s * .20),
              fill=(0, 0, 0, 0))

def icon_close(d, cx, cy, s, col):
    w = max(2, int(s * .15))
    d.line((cx - s * .32, cy - s * .32, cx + s * .32, cy + s * .32), fill=col, width=w)
    d.line((cx + s * .32, cy - s * .32, cx - s * .32, cy + s * .32), fill=col, width=w)

def icon_pause(d, cx, cy, s, col):
    w = max(2, int(s * .20))
    d.rounded_rectangle((cx - s * .34, cy - s * .38, cx - s * .10, cy + s * .38),
                        radius=w / 2, fill=col)
    d.rounded_rectangle((cx + s * .10, cy - s * .38, cx + s * .34, cy + s * .38),
                        radius=w / 2, fill=col)

def icon_heart(d, cx, cy, s, col, broken=False):
    pts = []
    for i in range(40):
        t = i / 39.0 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s / 34.0, cy + y * s / 34.0))
    d.polygon(pts, fill=col)
    if broken:
        d.line((cx + s * .02, cy - s * .52, cx - s * .10, cy - s * .10,
                cx + s * .12, cy + s * .06, cx - s * .04, cy + s * .50),
               fill=(255, 255, 255, 230), width=max(2, int(s * .10)))

def icon_coin(d, cx, cy, s, col, line):
    d.ellipse((cx - s * .46, cy - s * .46, cx + s * .46, cy + s * .46),
              fill=col, outline=line, width=max(1, int(s * .09)))
    d.ellipse((cx - s * .30, cy - s * .30, cx + s * .30, cy + s * .30),
              outline=lighten(col, .35), width=max(1, int(s * .06)))

def icon_star(d, cx, cy, s, col):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        r = s * (.52 if i % 2 == 0 else .23)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=col)

def icon_lock(d, cx, cy, s, col):
    d.rounded_rectangle((cx - s * .34, cy - s * .04, cx + s * .34, cy + s * .44),
                        radius=s * .10, fill=col)
    d.arc((cx - s * .24, cy - s * .44, cx + s * .24, cy + s * .10),
          180, 360, fill=col, width=max(2, int(s * .11)))

def icon_bulb(d, cx, cy, s, col):
    d.ellipse((cx - s * .32, cy - s * .48, cx + s * .32, cy + s * .16), fill=col)
    d.rounded_rectangle((cx - s * .16, cy + s * .10, cx + s * .16, cy + s * .38),
                        radius=s * .06, fill=col)
    d.line((cx - s * .14, cy + s * .46, cx + s * .14, cy + s * .46),
           fill=col, width=max(2, int(s * .08)))

def icon_hammer(d, cx, cy, s, col):
    d.rounded_rectangle((cx - s * .34, cy - s * .40, cx + s * .18, cy - s * .14),
                        radius=s * .06, fill=col)
    d.rounded_rectangle((cx - s * .04, cy - s * .34, cx + s * .10, cy + s * .44),
                        radius=s * .05, fill=col)

def icon_bomb(d, cx, cy, s, col):
    d.ellipse((cx - s * .38, cy - s * .22, cx + s * .30, cy + s * .46), fill=col)
    d.line((cx + s * .16, cy - s * .26, cx + s * .34, cy - s * .48),
           fill=T["cocoa"], width=max(2, int(s * .09)))

def icon_grid(d, cx, cy, s, col):
    for i in range(2):
        for j in range(2):
            x, y = cx - s * .30 + i * s * .34, cy - s * .30 + j * s * .34
            d.rounded_rectangle((x, y, x + s * .28, y + s * .28), radius=s * .06, fill=col)

def icon_palette(d, cx, cy, s, col):
    d.ellipse((cx - s * .42, cy - s * .42, cx + s * .42, cy + s * .42), fill=col)
    for a, cc in [(-.9, T["red"]), (.2, T["gold"]), (1.4, T["blue"]), (2.6, T["green"])]:
        d.ellipse((cx + s * .24 * math.cos(a) - s * .09,
                   cy + s * .24 * math.sin(a) - s * .09,
                   cx + s * .24 * math.cos(a) + s * .09,
                   cy + s * .24 * math.sin(a) + s * .09), fill=cc)

def icon_gift(d, cx, cy, s, col):
    d.rounded_rectangle((cx - s * .40, cy - s * .14, cx + s * .40, cy + s * .42),
                        radius=s * .06, fill=col)
    d.rounded_rectangle((cx - s * .44, cy - s * .30, cx + s * .44, cy - s * .06),
                        radius=s * .05, fill=lighten(col, .18))
    d.rounded_rectangle((cx - s * .07, cy - s * .30, cx + s * .07, cy + s * .42),
                        radius=s * .02, fill=T["white"])

def icon_flag(d, cx, cy, s, col):
    d.line((cx - s * .30, cy - s * .46, cx - s * .30, cy + s * .46),
           fill=T["cocoa"], width=max(2, int(s * .09)))
    d.polygon([(cx - s * .28, cy - s * .44), (cx + s * .42, cy - s * .30),
               (cx - s * .28, cy - s * .06)], fill=col)

def icon_home(d, cx, cy, s, col):
    d.polygon([(cx, cy - s * .46), (cx - s * .44, cy - s * .04),
               (cx + s * .44, cy - s * .04)], fill=col)
    d.rectangle((cx - s * .32, cy - s * .04, cx + s * .32, cy + s * .42), fill=col)

def icon_trophy(d, cx, cy, s, col):
    d.polygon([(cx - s * .30, cy - s * .40), (cx + s * .30, cy - s * .40),
               (cx + s * .22, cy + s * .10), (cx - s * .22, cy + s * .10)], fill=col)
    d.rectangle((cx - s * .07, cy + s * .08, cx + s * .07, cy + s * .34), fill=col)
    d.rounded_rectangle((cx - s * .22, cy + s * .32, cx + s * .22, cy + s * .44),
                        radius=s * .04, fill=col)

ICON = {
    "back": icon_arrow_left, "settings": icon_gear, "close": icon_close,
    "pause": icon_pause, "heart": icon_heart, "coin": icon_coin,
    "star": icon_star, "lock": icon_lock, "bulb": icon_bulb,
    "hammer": icon_hammer, "bomb": icon_bomb, "grid": icon_grid,
    "palette": icon_palette, "gift": icon_gift, "flag": icon_flag,
    "home": icon_home, "trophy": icon_trophy,
}

def draw_icon(base, w, h, kind, scale=0.52, color=None, broken=False, cx=None, cy=None):
    c = newc(w, h)
    d = ImageDraw.Draw(c)
    s = min(w, h) * S * scale
    X = (w * S / 2 if cx is None else cx * S)
    Y = (h * S / 2 if cy is None else cy * S)
    col = (color or T["cocoa"]) + (255,)
    fn = ICON.get(kind)
    if fn:
        if kind == "heart" and broken:
            fn(d, X, Y, s, col, broken=True)
        elif kind == "coin":
            fn(d, X, Y, s, col, T["gold_line"])
        else:
            fn(d, X, Y, s, col)
    base.alpha_composite(c)

# ============================ 元件工厂 ============================
def circle_button(w, h, icon=None, number=None, variant="cream", state="normal"):
    r = min(w, h) / 2.0
    c = newc(w, h)
    paste(c, shadow_layer(w, h, r, "circle", dy=2.6, blur=2.6, alpha=.26))
    if variant == "green":
        top, bot, line = T["green_light"], T["green"], T["green_line"]
    elif variant == "gold":
        top, bot, line = lighten(T["gold"], .28), T["gold"], T["gold_line"]
    elif variant == "locked":
        top, bot, line = (214, 208, 198), (186, 178, 166), (132, 124, 114)
    else:
        top, bot, line = T["cream_light"], T["cream_deep"], T["brown_line"]
    paste(c, grad_layer(w, h, r, top, bot, "circle", ow=2.2, line=line))
    # 内圈高光
    inn = newc(w, h)
    d = ImageDraw.Draw(inn)
    m = int(4.5 * S)
    d.ellipse((m, m, w * S - m, h * S - m), outline=lighten(top, .5) + (110,),
              width=max(1, int(1.3 * S)))
    c.alpha_composite(inn)
    if number is not None:
        centered_text(c, w, h, str(number), min(w, h) * .46, T["cocoa"],
                      stroke=T["white"], sw=.07, shadow=True)
    elif icon:
        draw_icon(c, w, h, icon, scale=.50,
                  color=T["white"] if variant == "green" else T["cocoa"])
    return finish(c, w, h)

def pill_button(w, h, label, variant="green", icon=None):
    r = min(h * .48, h / 2 - 1)
    c = newc(w, h)
    paste(c, shadow_layer(w, h, r, "round", dy=3.0, blur=3.0, alpha=.28))
    if variant == "green":
        top, bot, line, txt = T["green_light"], T["green"], T["green_line"], T["white"]
    elif variant == "gold":
        top, bot, line, txt = lighten(T["gold"], .30), T["gold"], T["gold_line"], T["cocoa"]
    else:
        top, bot, line, txt = T["cream_light"], T["cream_deep"], T["brown_line"], T["cocoa"]
    paste(c, grad_layer(w, h, r, top, bot, "round", ow=2.4, line=line))
    # 顶部高光条
    hl = newc(w, h)
    d = ImageDraw.Draw(hl)
    d.rounded_rectangle((int(6 * S), int(4 * S), int((w - 6) * S), int(h * .36 * S)),
                        radius=int(h * .16 * S), fill=(255, 255, 255, 62))
    c.alpha_composite(hl)
    if icon:
        draw_icon(c, w, h, icon, scale=.42, color=txt, cx=w * .14)
        tmp = newc(w, h)
        centered_text(tmp, w * .84, h, label, min(h * .46, 25), txt,
                      stroke=darken(line, .7) if variant == "green" else None,
                      sw=.055, shadow=(variant != "cream"))
        c.alpha_composite(tmp, (int(w * .12 * S), 0))
    else:
        centered_text(c, w, h, label, min(h * .46, 27), txt,
                      stroke=darken(line, .7) if variant == "green" else None,
                      sw=.055, shadow=(variant != "cream"))
    return finish(c, w, h)

def card(w, h, kind="gallery", idx=0, locked=False, fill=None):
    r = min(w, h) * .16
    c = newc(w, h)
    paste(c, shadow_layer(w, h, r, "round", dy=2.2, blur=2.2, alpha=.22))
    top, bot, line = T["cream_light"], mix(T["cream"], T["cream_deep"], .35), T["brown_line"]
    paste(c, grad_layer(w, h, r, top, bot, "round", ow=1.8, line=line))
    # 内容区（缩略图 / 方块皮肤 / 签到格）
    pad = min(w, h) * .13
    iw, ih = w - 2 * pad, h - 2 * pad
    ir = min(iw, ih) * .14
    inner = grad_layer(iw, ih, ir,
                       mix(T["cream"], (255, 255, 255), .4), T["cream_deep"],
                       "round", ow=1.2, line=mix(T["brown_line"], T["cream"], .25))
    paste(c, inner, (pad, pad))
    if kind == "skin":
        col = T[SKIN[idx % len(SKIN)]]
        draw_icon(c, w, h, "grid", scale=.56, color=col)
    elif kind == "sign":
        draw_icon(c, w, h, "gift" if idx == 6 else "star", scale=.42,
                  color=T["gold"] if idx >= 3 else T["gray"], cy=h * .38)
        centered_text(c, w, h, str(idx + 1), 10, T["cocoa_soft"],
                      dy=h * .26, bold=True)
    elif kind == "ach":
        draw_icon(c, w, h, "trophy", scale=.34, color=T["gold"], cx=w * .10)
        bar = grad_layer(w * .34, h * .16, h * .08, T["green_light"], T["green"],
                         "round", ow=1.0, line=T["green_line"], highlight=False)
        paste(c, bar, (w * .50, h * .54))
    else:
        if locked:
            draw_icon(c, w, h, "lock", scale=.40, color=T["gray"])
        else:
            col = T[SKIN[idx % len(SKIN)]]
            dd = ImageDraw.Draw(c)
            rr = min(w, h) * .20
            cx, cy = w * S / 2, h * S / 2
            dd.rounded_rectangle((cx - rr * S, cy - rr * S, cx + rr * S, cy + rr * S),
                                 radius=rr * S * .3, fill=col + (255,))
    return finish(c, w, h)

def progress(w, h, ratio=.60):
    r = h / 2.0
    c = newc(w, h)
    paste(c, grad_layer(w, h, r, (226, 206, 176), (206, 180, 146), "round",
                        ow=1.6, line=T["brown_line"], highlight=False))
    fw = max(h, w * ratio)
    paste(c, grad_layer(fw, h - 5, (h - 5) / 2.0, T["green_light"], T["green"],
                        "round", ow=1.2, line=T["green_line"]), (2.5, 2.5))
    return finish(c, w, h)

def hud_pill(w, h, kind="coin", label="1,250"):
    r = h / 2.0
    c = newc(w, h)
    paste(c, shadow_layer(w, h, r, "round", dy=1.8, blur=1.8, alpha=.20))
    paste(c, grad_layer(w, h, r, T["cream_light"], T["cream_deep"], "round",
                        ow=1.6, line=T["brown_line"]))
    if kind == "hearts":
        for i in range(3):
            draw_icon(c, w, h, "heart", scale=.62, color=T["red"],
                      cx=w * (.22 + i * .28))
    elif kind == "ticket":
        draw_icon(c, w, h, "star", scale=.52, color=T["gold"], cx=w * .22)
        centered_text(c, w, h, label, min(h * .40, 20), T["cocoa"], dy=h * .02)
    else:
        draw_icon(c, w, h, "coin", scale=.62, color=T["gold"], cx=w * .19)
        centered_text(c, w, h, label, min(h * .40, 19), T["cocoa"], dy=h * .02)
    return finish(c, w, h)

def panel_canvas(w, h, kind="panel"):
    r = min(w, h) * .15
    c = newc(w, h)
    paste(c, shadow_layer(w, h, r, "round", dy=3.2, blur=3.4, alpha=.26))
    if kind == "wood":
        top, bot, line = lighten(T["wood"], .22), T["wood"], T["wood_dark"]
    elif kind == "dots":
        top, bot, line = T["cream_light"], T["cream"], T["brown_line"]
    else:
        top, bot, line = T["cream_light"], T["cream_deep"], T["brown_line"]
    paste(c, grad_layer(w, h, r, top, bot, "round", ow=2.2, line=line))
    return c

def panel(w, h, kind="panel"):
    return finish(panel_canvas(w, h, kind), w, h)


def art_panel(w, h, kind):
    """内容容器：木框/画架里必须有程序化画作，不能留实心块或空白。"""
    c = panel_canvas(w, h, "wood" if kind == "frame" else "dots")
    pad = min(w, h) * .11
    iw, ih = w - 2 * pad, h - 2 * pad
    inner = grad_layer(iw, ih, min(iw, ih) * .06, T["cream_light"],
                       mix(T["cream"], T["cream_deep"], .45), "round",
                       ow=1.2, line=T["brown_line"], highlight=False)
    paste(c, inner, (pad, pad))
    d = ImageDraw.Draw(c)
    x0, y0, x1, y1 = pad * S, pad * S, (w - pad) * S, (h - pad) * S
    iw_s, ih_s = x1 - x0, y1 - y0
    if kind == "board":
        # 4x4 彩色拼块预览（对应玩法的方块阵列）
        n = 4
        g = min(iw_s, ih_s) * .70 / n
        ox = x0 + (iw_s - g * n) / 2
        oy = y0 + (ih_s - g * n) / 2
        cols = [T["green"], T["gold"], T["blue"], T["pink"], T["purple"], T["orange"]]
        for r in range(n):
            for cc in range(n):
                col = cols[(r * 3 + cc * 2) % len(cols)]
                bx, by = ox + cc * g, oy + r * g
                d.rounded_rectangle((bx + g * .06, by + g * .06,
                                     bx + g * .94, by + g * .94),
                                    radius=g * .20, fill=col + (255,),
                                    outline=darken(col, .68) + (255,),
                                    width=max(1, int(g * .05)))
    else:
        # 揭晓画作：暖色天空 + 太阳 + 起伏山丘 + 小草
        sky = np.linspace(0, 1, max(2, int(ih_s)))[:, None, None]
        col = (np.array((255, 226, 170), float)[None, None, :] * (1 - sky) +
               np.array((250, 196, 158), float)[None, None, :] * sky)
        art = Image.new("RGBA", (int(iw_s), int(ih_s)), (0, 0, 0, 0))
        ar = np.dstack([np.repeat(np.clip(col, 0, 255), int(iw_s), axis=1),
                        np.full((int(ih_s), int(iw_s)), 255)]).astype(np.uint8)
        art = Image.fromarray(ar, "RGBA")
        ad = ImageDraw.Draw(art)
        aw, ah = art.size
        ad.ellipse((aw * .68, ah * .10, aw * .88, ah * .30), fill=T["gold"] + (255,))
        ad.polygon([(0, ah * .72), (aw * .32, ah * .42), (aw * .62, ah * .72),
                    (aw * .82, ah * .52), (aw, ah * .70), (aw, ah), (0, ah)],
                   fill=T["green_deep"] + (255,))
        ad.polygon([(0, ah * .84), (aw * .40, ah * .60), (aw * .76, ah * .86),
                    (aw, ah * .74), (aw, ah), (0, ah)], fill=T["green"] + (255,))
        for i in range(7):
            gx = aw * (.08 + i * .135)
            ad.line((gx, ah * .93, gx + aw * .012, ah * .84),
                    fill=T["green_line"] + (255,), width=max(1, int(aw * .008)))
        art = art.resize((int(iw_s), int(ih_s)), Image.LANCZOS)
        # 内圆角遮罩
        mm = Image.new("L", art.size, 0)
        ImageDraw.Draw(mm).rounded_rectangle((0, 0, art.width - 1, art.height - 1),
                                             radius=int(min(iw_s, ih_s) * .06), fill=255)
        art.putalpha(ImageChops.multiply(art.getchannel("A"), mm))
        c.alpha_composite(art, (int(x0), int(y0)))
    return finish(c, w, h)

def tabs(w, h, labels=("每日", "成就"), active=0):
    c = newc(w, h)
    r = h * .42
    paste(c, grad_layer(w, h, r, (232, 212, 182), (214, 190, 156), "round",
                        ow=1.4, line=T["brown_line"], highlight=False))
    bw = (w - 4 * (len(labels) + 1)) / len(labels)
    for i, t in enumerate(labels):
        x = 4 + i * (bw + 4)
        if i == active:
            paste(c, grad_layer(bw, h - 6, r * .85, T["green_light"], T["green"],
                                "round", ow=1.2, line=T["green_line"]), (x, 3))
        tmp = newc(bw, h)
        centered_text(tmp, bw, h, t, min(h * .38, 15),
                      T["white"] if i == active else T["cocoa_soft"],
                      dy=0, bold=True)
        c.alpha_composite(tmp, (int(x * S), 0))
    return finish(c, w, h)

def bunting(w, h):
    c = newc(w, h)
    d = ImageDraw.Draw(c)
    d.line((0, 6 * S, w * S, 10 * S), fill=T["wood_dark"] + (255,), width=max(2, int(2 * S)))
    cols = [T["red"], T["gold"], T["green"], T["blue"], T["pink"], T["cream_deep"]]
    n = 11
    for i in range(n):
        x = (i + .5) * w / n
        col = cols[i % len(cols)]
        hh = h * (.52 if i % 2 else .66)
        d.polygon([((x - w / n * .42) * S, 8 * S),
                   ((x + w / n * .42) * S, 8 * S),
                   (x * S, hh * S)], fill=col + (255,))
        d.line(((x - w / n * .42) * S, 8 * S, x * S, hh * S),
               fill=darken(col, .72) + (255,), width=max(1, int(1 * S)))
    return finish(c, w, h)

def banner(w, h, label="完成！"):
    c = newc(w, h)
    r = min(w, h) * .22
    paste(c, shadow_layer(w, h, r, "round", dy=2.8, blur=2.8, alpha=.28))
    paste(c, grad_layer(w, h, r, lighten(T["red"], .30), T["red"], "round",
                        ow=2.4, line=T["red_line"]))
    centered_text(c, w, h, label, min(h * .48, 34), T["white"],
                  stroke=T["red_line"], sw=.07, shadow=True)
    for sx in (w * .10, w * .90):
        draw_icon(c, w, h, "star", scale=.34, color=T["gold"], cx=sx, cy=h * .26)
    return finish(c, w, h)

def artword(w, h, text, size=None, color=None, stroke=None):
    c = newc(w, h)
    centered_text(c, w, h, text, size or min(h * .74, 42), color or T["white"],
                  stroke=stroke or T["cocoa"], sw=.085, shadow=True)
    return finish(c, w, h)

def plain_text(w, h, text, size=None, color=None):
    c = newc(w, h)
    centered_text(c, w, h, text, size or min(h * .62, 19), color or T["cocoa"],
                  stroke=None, sw=0, shadow=False, bold=True)
    return finish(c, w, h)

def logo(w, h):
    c = newc(w, h)
    d = ImageDraw.Draw(c)
    # 画架 + 画布（矢量，暖奶油木框 + 果冻色块）
    d.rounded_rectangle((w * .18 * S, h * .14 * S, w * .82 * S, h * .80 * S),
                        radius=int(12 * S), fill=T["cream_light"] + (255,),
                        outline=T["wood_dark"] + (255,), width=max(2, int(4 * S)))
    cols = [T["green"], T["gold"], T["blue"], T["pink"]]
    for i in range(4):
        x = w * (.24 + (i % 2) * .28)
        y = h * (.22 + (i // 2) * .28)
        d.rounded_rectangle((x * S, y * S, (x + w * .24) * S, (y + h * .24) * S),
                            radius=int(5 * S), fill=cols[i] + (255,))
    d.line((w * .30 * S, h * .82 * S, w * .16 * S, h * .98 * S),
           fill=T["wood"] + (255,), width=max(2, int(5 * S)))
    d.line((w * .70 * S, h * .82 * S, w * .84 * S, h * .98 * S),
           fill=T["wood"] + (255,), width=max(2, int(5 * S)))
    return finish(c, w, h)

def bubble(w, h, text="当前关卡"):
    return pill_button(w, h, text, variant="cream")

# ============================ 名称 -> 元件映射 ============================
TEXT = {
    "s1_title_art": ("点击画廊", None), "s1_subtitle": ("正在准备画作···", None),
    "s2_level_plate": ("第 37 关", None), "s2_btn_start": ("开始游戏", None),
    "s3_title": ("图库", None), "s4_title": ("第 37 关", None),
    "s5_banner_complete": ("完成！", None), "s5_btn_next": ("下一关", None),
    "s5_btn_home": ("首页", None), "s6_btn_revive": ("看广告复活", None),
    "s6_btn_restart": ("重新开始", None), "s6_btn_home": ("回首页", None),
    "s7_title": ("皮肤", None), "s7_more_label": ("更多皮肤", None),
    "s8_daily_title": ("每日挑战", None), "s8_daily_hint": ("连续签到 3 天，明日可得宝箱", None),
    "s8_ach_title": ("成就", None), "s9_start_hint": ("点击开始游戏", None),
    "s9_btn_level": ("第 37 关", None), "s9_bubble": ("当前关卡", None),
}

def numbered(name):
    for p in ("card_", "skin_", "sign_", "ach_", "node_"):
        if name.startswith(p):
            tail = name[len(p):]
            if tail.isdigit():
                return int(tail)
    return 0

def make(rec, screen):
    nm, cat, w, h = rec["name"], rec.get("cat", ""), rec["w"], rec["h"]
    key = screen + "_" + nm
    idx = numbered(nm)

    if nm == "logo":                 return logo(w, h)
    if nm == "title_art":            return artword(w, h, "点击画廊", 36)
    if nm == "bunting":              return bunting(w, h)
    if nm == "banner_complete":      return banner(w, h, "完成！")
    if nm == "heart_broken":
        c = newc(w, h); draw_icon(c, w, h, "heart", .82, T["red"], broken=True)
        return finish(c, w, h)
    if nm == "hero":
        c = newc(w, h)
        paste(c, shadow_layer(w, h, w / 2, "circle", dy=2, blur=2, alpha=.22))
        paste(c, grad_layer(w, h, w / 2, T["gold"], T["gold_deep"], "circle",
                            ow=2, line=T["gold_line"]))
        draw_icon(c, w, h, "star", .52, T["white"])
        return finish(c, w, h)
    if nm == "progress":             return progress(w, h, .60 if screen == "s1" else .54)
    if nm in ("coin_bar", "coin_reward", "ticket_bar", "hearts"):
        k = "hearts" if nm == "hearts" else ("ticket" if nm == "ticket_bar" else "coin")
        lab = "+60" if nm == "coin_reward" else ("× 3" if k == "ticket" else "1,250")
        return hud_pill(w, h, k, lab)
    if nm in ("level_plate", "bubble"):
        base = panel_canvas(w, h, "wood" if nm == "level_plate" else "panel")
        centered_text(base, w, h, TEXT.get(key, ("", None))[0], min(h * .44, 21),
                      T["white"] if nm == "level_plate" else T["cocoa"],
                      stroke=T["wood_dark"] if nm == "level_plate" else None,
                      sw=.06, shadow=(nm == "level_plate"))
        return finish(base, w, h)
    if nm == "tab_bar":
        return tabs(w, h, ("方块皮肤", "拖尾效果") if screen == "s7" else ("每日", "成就"), 0)
    if nm in ("board", "frame_art"):
        return art_panel(w, h, "frame" if nm == "frame_art" else "board")
    if nm in ("task_panel", "bottom_bar"):
        return panel(w, h)
    if cat == "node":
        num = {"node_40": 40, "node_39": 39, "node_38": 38, "node_37": 37,
               "node_36": 36}.get(nm)
        if nm == "node_challenge":
            c = circle_button(w, h, "flag", variant="gold")
        else:
            c = circle_button(w, h, number=num, variant="gold" if num == 37 else "cream")
        return c
    if nm.startswith("entry_"):
        ic = {"entry_gallery": "grid", "entry_skin": "palette",
              "entry_daily": "gift", "entry_achieve": "trophy"}[nm]
        return circle_button(w, h, ic)
    if nm.startswith("prop_"):
        ic = {"prop_hint": "bulb", "prop_hammer": "hammer", "prop_bomb": "bomb"}[nm]
        c = newc(w, h)
        paste(c, shadow_layer(w, h, min(w, h) * .16, "round", dy=2.2, blur=2.2, alpha=.24))
        paste(c, grad_layer(w, h, min(w, h) * .16, T["cream_light"], T["cream_deep"],
                            "round", ow=1.8, line=T["brown_line"]))
        draw_icon(c, w, h, ic, .48, T["cocoa"])
        return finish(c, w, h)
    if nm.startswith(("card_", "skin_", "sign_", "ach_")) and nm[-1].isdigit():
        kind = ("gallery" if nm.startswith("card_") else
                "skin" if nm.startswith("skin_") else
                "sign" if nm.startswith("sign_") else "ach")
        return card(w, h, kind, idx, locked=(kind == "gallery" and idx >= 6))
    if nm in ("back", "settings", "close", "pause"):
        ic = {"back": "back", "settings": "settings", "close": "close", "pause": "pause"}[nm]
        return circle_button(w, h, ic)
    if nm.startswith("nav_"):
        try:
            ni = int(nm.rsplit("_", 1)[1]) - 1
        except ValueError:
            ni = 0
        ic = ["home", "grid", "trophy", "settings"][min(3, max(0, ni))]
        return circle_button(w, h, ic, variant="cream")
    if nm in ("btn_task", "btn_achieve"):
        return circle_button(w, h, "gift" if nm == "btn_task" else "trophy", variant="green")
    if cat == "button" or nm.startswith("btn_"):
        txt = TEXT.get(key, ("", None))[0] or nm.replace("btn_", "")
        var = "green" if nm in ("btn_start", "btn_next", "btn_revive", "btn_level") else "cream"
        return pill_button(w, h, txt, var)
    if cat in ("text", "artword"):
        txt = TEXT.get(key, (nm, None))[0]
        if cat == "artword":
            return artword(w, h, txt, min(h * .8, 34), T["cocoa"], T["cream_light"])
        return plain_text(w, h, txt, min(h * .62, 20))
    return panel(w, h)

# ============================ 背景（程序化，非截图） ============================
def make_bg(screen, W, H):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a = np.zeros((H, W, 4), float)
    if screen == "s6":
        top, bot = (74, 56, 44), (48, 36, 30)
    elif screen == "s9":
        top, bot = (255, 240, 208), (238, 214, 176)
    else:
        top, bot = (255, 247, 229), (246, 224, 190)
    t = np.linspace(0, 1, H)[:, None, None]
    col = np.array(top, float)[None, None, :] * (1 - t) + np.array(bot, float)[None, None, :] * t
    a[:, :, :3] = np.repeat(col, W, axis=1)
    a[:, :, 3] = 255
    # 点阵纹理（统一 14px 网格）
    if screen not in ("s6",):
        yy, xx = np.mgrid[0:H, 0:W]
        dot = ((xx % 14 == 3) & (yy % 14 == 3)).astype(float)
        a[:, :, :3] = a[:, :, :3] * (1 - dot[:, :, None] * .10) + \
                      np.array([255, 246, 220], float)[None, None, :] * dot[:, :, None] * .10
    if screen == "s9":
        # 关卡路径：一条柔和虚线曲线
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        d = ImageDraw.Draw(im)
        pts = [(235, 60), (235, 175), (235, 285), (235, 415), (135, 520), (335, 520)]
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]; x1, y1 = pts[i + 1]
            steps = int(math.hypot(x1 - x0, y1 - y0) / 9)
            for s in range(steps):
                if s % 2 == 0:
                    u = s / max(1, steps)
                    x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
                    d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(205, 168, 118, 150))
        return im.convert("RGB")
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").convert("RGB")

def make_plate(name, w, h):
    if name == "dialog":
        c = newc(w, h)
        r = min(w, h) * .09
        paste(c, shadow_layer(w, h, r, "round", dy=4, blur=5, alpha=.32))
        paste(c, grad_layer(w, h, r, T["cream_light"], T["cream_deep"], "round",
                            ow=2.6, line=T["brown_line"]))
        return finish(c, w, h)
    if name == "daily_panel":
        return panel(w, h)
    return panel(w, h, "wood")

# ============================ 主流程 ============================
def main():
    M = json.loads(io.open(os.path.join(ROOT, "manifest.json"), encoding="utf-8").read())
    stats = {}
    for screen, blk in M.items():
        W, H = blk["size"]
        # 背景：完全程序化
        make_bg(screen, W, H).save(os.path.join(BG, screen + "_final.png"))
        stats[screen] = []
        for rec in blk["items"]:
            if rec.get("layer") == "bg":
                im = make_plate(rec["name"], rec["w"], rec["h"])
                im.save(os.path.join(BG, rec["file"]))
                continue
            im = make(rec, screen)
            im.save(os.path.join(ASSETS, rec["file"]))
            arr = np.asarray(im)
            al = arr[:, :, 3]
            zr = arr[:, :, :3][al == 0]
            stats[screen].append(dict(
                name=rec["name"], file=rec["file"], size=list(im.size),
                transparent=round(float((al == 0).mean()), 3),
                opaque=round(float((al == 255).mean()), 3),
                fog=round(float(((al > 0) & (al < 200)).mean()), 3),
                corners=[int(al[0, 0]), int(al[0, -1]), int(al[-1, 0]), int(al[-1, -1])],
                zero_rgb_max=int(zr.max()) if len(zr) else 0,
                cat=rec.get("cat"), cls=shape_class(rec)))
        print("%s 生成 %d 个元件" % (screen, len(stats[screen])))
    # s4 点阵底（棋盘区专用，程序化）
    from PIL import ImageDraw as _ID
    dotw, doth = 297, 256
    dots = Image.new("RGB", (dotw, doth), (247, 232, 208))
    dd = _ID.Draw(dots)
    for y in range(0, doth + 14, 14):
        for x in range(0, dotw + 14, 14):
            dd.ellipse((x - 2.2, y - 2.2, x + 2.2, y + 2.2), fill=(237, 220, 200))
    dots.save(os.path.join(BG, "s4_dots.png"))

    io.open(os.path.join(ROOT, "alpha_stats.json"), "w", encoding="utf-8").write(
        json.dumps(stats, ensure_ascii=False, indent=1))
    build_html(M)
    board(stats)
    tot = sum(len(v) for v in stats.values())
    hard = [(n, it["name"], it["corners"], it["transparent"], it["zero_rgb_max"])
            for n in stats for it in stats[n]
            if any(v > 40 for v in it["corners"]) or it["zero_rgb_max"] > 0]
    print("\n元件库生成完成 %d 张 | 硬性不合规 %d 张" % (tot, len(hard)))
    for x in hard[:20]:
        print("  BAD", x)


def shape_class(rec):
    """实心几何件 / 文字笔划件 / 图标散件，判据必须分开。"""
    cat, nm = rec.get("cat", ""), rec["name"]
    if cat in ("text", "artword", "decor"):
        return "text"
    if cat == "hud" or nm in ("logo", "heart_broken", "hero"):
        return "icon"
    if nm.startswith(("sign_", "ach_")):
        return "card"
    return "solid"


def is_bad(it):
    if any(v > 40 for v in it["corners"]):
        return True
    if it["zero_rgb_max"] > 0:
        return True
    cls = it.get("cls", "solid")
    if cls == "text" and it["transparent"] < 0.10:
        return True                       # 美术字却几乎全不透明 = 文字块
    if cls == "solid" and it["transparent"] <= 0:
        return True                       # 完全没有任何透明像素 = 截图
    if cls == "icon" and it["transparent"] < 0.02:
        # 紧凑条状 HUD（coin_bar / hearts）本身就几乎填满包围盒，
        # 透明占比 3~4% 属正常；只要四角 alpha=0 且 straight alpha 干净即合格。
        # 0.05 是给「有明显镂空的散件图标」定的，套到条状件会误判。
        return True
    return False


def build_html(M):
    """从 manifest + tilekit.json 生成 9 屏可运行 UI；资源全部指向本次生成的元件。"""
    KIT = json.loads(io.open(os.path.join(ROOT, "tilekit.json"), encoding="utf-8").read())
    KG = KIT["grid"]
    TX0, TY0, TS = KG["x"], KG["y"], KG["size"]
    BOARD, PALT, ROT = KIT["board"], KIT["palette"], KIT["rotation"]
    html = ["""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>点击画廊 · v7 参数化生成 UI（9 屏）</title><style>
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#fff;overflow:hidden}
.screen{position:absolute;left:0;top:0;width:325px;height:478px;overflow:hidden;display:none;background:#f9eed9}
.screen.map{width:470px;height:836px}
.screen.on{display:block}
.bg{position:absolute;left:0;top:0;display:block}
.ui{position:absolute;display:block;cursor:pointer;transition:transform .09s ease,filter .09s ease}
.ui:active{transform:scale(.965);filter:brightness(.94)}
.ui[data-cat=panel],.ui[data-cat=decor],.ui[data-cat=artword]{cursor:default}
.ui[data-cat=panel]:active,.ui[data-cat=decor]:active,.ui[data-cat=artword]:active{transform:none;filter:none}
.tile{position:absolute;width:32px;height:32px;cursor:pointer;filter:brightness(1.10)}
.tile:active{transform:scale(.965)}
.tile .tc{position:absolute;inset:0}
.tile .tl{position:absolute;inset:0;width:100%;height:100%;mix-blend-mode:multiply}
.tile .ta{position:absolute;left:17%;top:17%;width:66%;height:66%;transform-origin:50% 50%;pointer-events:none}
.ui.sel{outline:2px solid rgba(230,80,60,.8);outline-offset:-2px}
#hint{position:fixed;left:8px;bottom:6px;font:12px/1.4 "Microsoft YaHei",sans-serif;color:#7a6048;
 background:rgba(255,248,232,.9);padding:4px 8px;border-radius:6px;display:none}
</style></head><body>"""]
    for n in M:
        html.append('<div class="%s" id="%s"><img class="bg" src="bg/%s_final.png">' %
                    ("screen map" if n == "s9" else "screen", n, n))
        for r in M[n]["items"]:
            sub = "bg" if r.get("layer") == "bg" else "assets"
            html.append('<img class="%s" data-cat="%s" data-name="%s" src="%s/%s" '
                        'style="left:%dpx;top:%dpx;width:%dpx;height:%dpx" alt="%s">' %
                        ("bg" if sub == "bg" else "ui", r["cat"], r["name"], sub, r["file"],
                         r["x"], r["y"], r["w"], r["h"], r["name"]))
        if n == "s4":
            html.append('<img class="bg" src="bg/s4_dots.png" style="left:%dpx;top:%dpx">' % (TX0, TY0))
            for row in BOARD:
                for v in row:
                    if not v["color"]:
                        continue
                    css = "#%02X%02X%02X" % tuple(PALT[v["color"]])
                    ar = "arrow_cross.png" if v["dir"] == "cross" else "arrow_up.png"
                    html.append('<div class="ui tile" data-cat="tile" data-name="tile_r%dc%d_%s_%s" '
                                'style="left:%dpx;top:%dpx">' % (v["r"], v["c"], v["color"], v["dir"],
                                                                TX0 + v["c"] * TS, TY0 + v["r"] * TS))
                    html.append('<div class="tc" style="background:%s"></div>' % css)
                    html.append('<img class="tl" src="tilekit/tile_base.png">')
                    if v["dir"] != "none":
                        html.append('<img class="ta" src="tilekit/%s" style="transform:rotate(%ddeg)">' %
                                    (ar, ROT[v["dir"]]))
                    html.append('</div>')
        html.append('</div>')
    html.append("""<div id="hint"></div><script>
function show(){
  var id=(location.hash||'#s1').slice(1);
  document.querySelectorAll('.screen').forEach(function(s){s.classList.remove('on')});
  var el=document.getElementById(id); if(el) el.classList.add('on');
  var h=document.getElementById('hint');
  h.style.display = location.search.indexOf('audit=1')>=0 ? 'block':'none';
  h.textContent = id+' · 控件 '+el.querySelectorAll('.ui').length+' 个 · 点击控件可查看名称';
}
document.addEventListener('click',function(e){
  var t=e.target.closest('.ui'); if(!t) return;
  document.querySelectorAll('.ui.sel').forEach(function(x){x.classList.remove('sel')});
  if(location.search.indexOf('audit=1')>=0){t.classList.add('sel');
    document.getElementById('hint').textContent=t.dataset.name+' · '+t.dataset.cat;}
});
window.addEventListener('hashchange',show); show();
</script></body></html>""")
    io.open(os.path.join(ROOT, "ui_final.html"), "w", encoding="utf-8").write("\n".join(html))
    print("ui_final.html 已按参数化元件重建")


def board(stats):
    try:
        F = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 16)
        Fs = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 10)
    except Exception:
        F = Fs = ImageFont.load_default()
    CW, CH, COLS, LBL, ROWH = 78, 94, 16, 92, 118
    W, H = LBL + COLS * CW + 16, 64 + 9 * ROWH + 20
    b = Image.new("RGB", (W, H), (248, 246, 242))
    d = ImageDraw.Draw(b)
    d.text((12, 8), "UI_v7 参数化生成元件自检 · 棋盘格=透明 · RGBA · 透明区 RGB=0", font=F, fill=(60, 45, 35))
    d.text((12, 34), "按类型判据：几何件查四角、文字件查透明占比；红框=不合规。", font=Fs, fill=(120, 95, 75))

    def checker(w, h, s=8):
        o = Image.new("RGB", (w, h), (236, 236, 236))
        dd = ImageDraw.Draw(o)
        for yy in range(0, h, s):
            for xx in range(0, w, s):
                if (xx // s + yy // s) % 2:
                    dd.rectangle((xx, yy, xx + s - 1, yy + s - 1), fill=(255, 255, 255))
        return o

    for ri, n in enumerate(stats):
        y = 64 + ri * ROWH
        d.rectangle((0, y, W, y + ROWH - 1), fill=(243, 240, 234) if ri % 2 == 0 else (248, 246, 242))
        d.text((10, y + 36), "%s  %d张" % (n, len(stats[n])), font=F, fill=(90, 60, 40))
        for ci, it in enumerate(stats[n][:COLS]):
            x = LBL + ci * CW
            im = Image.open(os.path.join(ASSETS, it["file"])).convert("RGBA")
            im.thumbnail((CW - 10, 62), Image.LANCZOS)
            bg = checker(CW - 8, 62)
            bg.paste(im, ((CW - 8 - im.width) // 2, (62 - im.height) // 2), im)
            b.paste(bg, (x + 4, y + 4))
            bad = is_bad(it)
            d.rectangle((x + 4, y + 4, x + 4 + CW - 8, y + 66),
                        outline=(220, 60, 60) if bad else (215, 205, 190), width=1)
            d.text((x + 2, y + 68), it["name"][:11], font=Fs, fill=(200, 50, 50) if bad else (70, 55, 45))
            d.text((x + 2, y + 80), "T%.2f R%d" % (it["transparent"], it["zero_rgb_max"]),
                   font=Fs, fill=(130, 115, 100))
    b.save(os.path.join(ROOT, "alpha_report.png"))

    # 深灰底预览：验货视角，有底板残留立刻显形
    names = ["s4_back", "s2_settings", "s3_back", "s6_close", "s9_node_40",
             "s3_card_01", "s9_btn_level", "s1_progress", "s8_ach_1", "s4_prop_hint"]
    CW2 = 220
    b2 = Image.new("RGB", (5 * CW2, 2 * 250), (248, 246, 242))
    d2 = ImageDraw.Draw(b2)
    d2.text((12, 8), "深灰底验货视角 · 轮廓外应只见深灰，绝无米色/褐色方块", font=F, fill=(60, 45, 35))
    for i, nm in enumerate(names):
        p = os.path.join(ASSETS, nm + ".png")
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA")
        k = min(160 / im.width, 160 / im.height)
        big = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
        bg = Image.new("RGB", (CW2 - 12, 196), (64, 64, 68))
        bg.paste(big, ((CW2 - 12 - big.width) // 2, (196 - big.height) // 2), big)
        x, y = (i % 5) * CW2 + 6, 34 + (i // 5) * 250
        b2.paste(bg, (x, y))
        d2.text((x, y + 200), nm, font=Fs, fill=(70, 55, 45))
    b2.save(os.path.join(ROOT, "alpha_dark_preview.png"))

if __name__ == "__main__":
    main()
