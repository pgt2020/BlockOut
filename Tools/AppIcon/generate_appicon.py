# -*- coding: utf-8 -*-
"""
BlockOut · App 上线图标生成器（v2 · 与游戏本体视觉对齐）

设计对齐依据（来自 DesignAssets/UI_v7/tile_kit.py 的真源）：
- 背景：奶油米底 BG=[247,232,208]，同游戏棋盘底。
- 方块：中性灰度光照模板 L（顶亮 + 内高光 + 底暗 + 同色描边）× tint 色
        = 软胶立体方块（顶高光、底阴影、圆角），与游戏内方块同一套渲染。
- 箭头：近白色 [236,234,226] + 柔光晕，白色嵌在方块中央。
- 品牌六色（用户首版设计 + 游戏 UI 强调色）：绿/橙/黄/粉/蓝/红。
- 排版：棕圆体字（Baloo2）作 BLOCKOUT 字标（仅横幅/商店图用）。

输出：master 1024（不透明+RGBA）、iOS AppIcon.appiconset、Android legacy+adaptive
      mipmap 五密度、Play Store 512 + feature graphic 1024x500、manifest.json。
straight-alpha 铁律：透明区 RGB 严格清零。
"""
import os, json, random, string
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "outputs", "appicon_launch"))
os.makedirs(ROOT, exist_ok=True)

# ---------------- design tokens ----------------
CREAM = np.array([247.0, 232.0, 208.0])          # 游戏底
CREAM_TOP = np.array([252.0, 240.0, 222.0])      # 轻微提亮
SHADOW = np.array([150.0, 128.0, 100.0])         # 软投影
BROWN = (92, 58, 22)
BROWN_SUB = (122, 86, 40)
ARROW_RGB = np.array([236.0, 234.0, 226.0])

# 品牌六色（与首版设计 + 游戏强调色一致）
TILE_COLORS = [
    (139, 193, 91),   # green
    (255, 159, 64),   # orange
    (246, 186, 74),   # yellow
    (247, 143, 147),  # pink
    (97, 161, 220),   # blue
    (240, 85, 107),   # red
]
TILE_ARROWS = ['up', 'up', 'right', 'left', 'right', 'down']


# ---------------- 软胶方块（与游戏 tile_kit 同语言） ----------------
def block_lightmap(S):
    """生成 S×S 中性灰度光照模板 L（顶亮/内高光/底暗/同色描边），范围 ~0.55..1.30。"""
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    ny, nx = yy / (S - 1), xx / (S - 1)
    grad = 1.08 - 0.30 * ny ** 1.6                       # 顶亮底暗
    hl = 0.18 * np.exp(-((ny - 0.16) / 0.14) ** 2) * np.exp(-((nx - 0.5) / 0.44) ** 2)
    shade = 0.07 * np.exp(-((ny - 0.92) / 0.07) ** 2)
    L = grad + hl - shade
    rad = max(2, int(round(S * 0.18)))
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, S - 1, S - 1), radius=rad, fill=255)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(max(1.0, S * 0.02)))).astype(float) / 255.0
    INNER = m > 0.5
    er = INNER.copy()
    for _ in range(2):
        e = er.copy()
        e[1:, :] &= er[:-1, :]; e[:-1, :] &= er[1:, :]
        e[:, 1:] &= er[:, :-1]; e[:, :-1] &= er[:, 1:]
        er = e
    L[INNER & ~er] *= 0.68                                # 圆角内芯同色描边（暗）
    L[~INNER] = 0.72                                      # 四角 = 同色深色外框
    L = np.clip(L, 0.55, 1.30)
    L = np.asarray(Image.fromarray((L * 255 / 1.30).clip(0, 255).astype(np.uint8))
                   .filter(ImageFilter.GaussianBlur(max(0.5, S * 0.004)))).astype(float) / 255.0 * 1.30
    cm = L[S // 4:S // 4 + 5, S // 4:S // 4 + 5].mean()
    L = np.clip(L / cm, 0.55, 1.30)
    return L, (m > 0.5).astype(np.float32)


def _draw_arrow_rgba(S, direction):
    """近白箭头 + 柔光晕，居中，按方向旋转。返回 RGBA。"""
    big = S * 4
    m = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(m)
    u = big / 24.0
    poly = [(12 * u, 2.5 * u), (20.5 * u, 11 * u), (15.5 * u, 11 * u),
            (15.5 * u, 21 * u), (8.5 * u, 21 * u), (8.5 * u, 11 * u), (3.5 * u, 11 * u)]
    d.polygon(poly, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(big * 0.006))
    core = (np.asarray(m).astype(float) / 255.0 > 0.5).astype(float)
    core = np.asarray(Image.fromarray((core * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(big * 0.004))).astype(float) / 255.0
    halo = np.asarray(Image.fromarray((core * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(big * 0.012))).astype(float) / 255.0
    rgba = np.zeros((big, big, 4), np.uint8)
    rgba[:, :, :3] = ARROW_RGB.astype(np.uint8)
    rgba[:, :, 3] = (halo * 150).clip(0, 255).astype(np.uint8)
    w = (core * 255).clip(0, 255).astype(np.uint8)
    for ch in range(3):
        rgba[:, :, ch] = np.maximum(rgba[:, :, ch], w)
    rgba[:, :, 3] = np.maximum(rgba[:, :, 3], w)
    img = Image.fromarray(rgba, "RGBA")
    deg = {'up': 0, 'right': 90, 'down': 180, 'left': 270}[direction]
    if deg:
        img = img.rotate(-deg, resample=Image.BICUBIC, expand=False)
    return img.resize((S, S), Image.LANCZOS)


def draw_tile(S, color, direction):
    """单个软胶立体方块（RGBA，透明圆角外 RGB 清零）。"""
    L, mask = block_lightmap(S)
    rgb = np.clip(np.array(color, float)[None, None, :] * L[:, :, None], 0, 255)
    alpha = (mask * 255).astype(np.uint8)
    out = np.dstack([rgb, alpha]).astype(np.uint8)
    arrow = np.asarray(_draw_arrow_rgba(S, direction)).astype(np.float32)
    am = arrow[:, :, 3:4] / 255.0
    for ch in range(3):
        out[:, :, ch] = (out[:, :, ch].astype(np.float32) * (1 - am[:, :, 0])
                         + ARROW_RGB[ch] * am[:, :, 0]).astype(np.uint8)
    out[:, :, 3] = np.maximum(out[:, :, 3], arrow[:, :, 3])
    out[:, :, :3][out[:, :, 3] == 0] = 0
    return Image.fromarray(out, "RGBA")


# ---------------- 奶油背景（近平底，贴近游戏纯奶油底） ----------------
def draw_background(S):
    cw = S * 3
    yy, xx = np.mgrid[0:cw, 0:cw].astype(float)
    ny, nx = yy / (cw - 1), xx / (cw - 1)
    glow = np.exp(-((nx - 0.42) ** 2 + (ny - 0.38) ** 2) / (2 * 0.6 ** 2))
    base = CREAM[None, None, :] + (CREAM_TOP - CREAM)[None, None, :] * glow[:, :, None] * 0.35
    vig = 1 - 0.04 * ((nx - 0.5) ** 2 + (ny - 0.5) ** 2) / 0.5
    base = np.clip(base * vig[:, :, None], 0, 255)
    return Image.fromarray(base.astype(np.uint8), "RGB").resize((S, S), Image.LANCZOS)


# ---------------- 6 块拼板（奶油底上软胶方块簇） ----------------
def draw_cluster(S, ss=3, transparent=False):
    """奶油底 + 2×3 软胶方块簇（整簇一个柔和落地投影），返回 RGBA。
    transparent=True 时背景透明（仅方块+柔影），用于 Android 自适应前景层。"""
    cw = S * ss
    cell = int(cw * 0.78 / 3)
    gap = max(2, int(cell * 0.06))
    ts = cell - gap
    total_w = 3 * cell - gap
    total_h = 2 * cell - gap
    ox = int((cw - total_w) / 2)
    oy = int((cw - total_h) / 2)
    # 先在一张透明层上渲染所有方块，得到方块 RGBA 与并集 alpha
    layer = np.zeros((cw, cw, 4), np.float32)
    for i in range(6):
        r, c = divmod(i, 3)
        bx = ox + c * cell
        by = oy + r * cell
        tt = np.asarray(draw_tile(ts, TILE_COLORS[i], TILE_ARROWS[i])).astype(np.float32)
        sub = layer[by:by + ts, bx:bx + ts]
        ta = tt[:, :, 3:4] / 255.0
        sub[:, :, :3] = sub[:, :, :3] * (1 - ta) + tt[:, :, :3] * ta
        sub[:, :, 3] = np.maximum(sub[:, :, 3], tt[:, :, 3])
    union = layer[:, :, 3:4] / 255.0
    # 整簇柔和落地投影：小幅模糊 + 微量下移，棕影
    sh = np.asarray(Image.fromarray((union[:, :, 0] * 255).astype(np.uint8))
                    .filter(ImageFilter.GaussianBlur(max(2.0, cw * 0.006)))).astype(np.float32) / 255.0
    oy_sh = int(cw * 0.012)
    sh = np.roll(sh, oy_sh, axis=0)
    sh[:oy_sh, :] = 0
    # 合成
    canvas = np.zeros((cw, cw, 4), np.float32)
    if not transparent:
        bg = draw_background(cw)
        canvas[:, :, :3] = np.asarray(bg).astype(np.float32)
        canvas[:, :, 3] = 255
    sa = sh[:, :, None]
    canvas[:, :, :3] = canvas[:, :, :3] * (1 - sa) + SHADOW[None, None, :] * sa
    canvas[:, :, :3] = canvas[:, :, :3] * (1 - union) + layer[:, :, :3] * union
    canvas[:, :, 3] = np.maximum(canvas[:, :, 3], layer[:, :, 3])
    out = np.clip(canvas, 0, 255).astype(np.uint8)
    out[:, :, :3][out[:, :, 3] == 0] = 0
    return Image.fromarray(out, "RGBA").resize((S, S), Image.LANCZOS)


def render_master(S=1024, ss=3):
    img = draw_cluster(S, ss)
    img.save(os.path.join(ROOT, "master_1024_opaque.png"))
    img.convert("RGBA").save(os.path.join(ROOT, "master_1024_rgba.png"))
    return img


# ---------------- Play Store 横幅 ----------------
def render_feature(size=(1024, 500), ss=3):
    W, H = size
    cw, ch = int(W * ss), int(H * ss)
    canvas = np.zeros((ch, cw, 4), np.float32)
    bg = draw_background(max(cw, ch))
    canvas[:, :, :3] = np.asarray(bg.resize((cw, ch))).astype(np.float32)[:, :, :3]
    canvas[:, :, 3] = 255
    panel_size = int(ch * 0.82)
    panel = draw_cluster(panel_size, transparent=True)
    px = int(cw * 0.05)
    py = int((ch - panel_size) / 2)
    pp = np.asarray(panel).astype(np.float32)
    sub = canvas[py:py + panel_size, px:px + panel_size]
    pa = pp[:, :, 3:4] / 255.0
    sub[:, :, :3] = sub[:, :, :3] * (1 - pa) + pp[:, :, :3] * pa
    sub[:, :, 3] = np.maximum(sub[:, :, 3], pp[:, :, 3])
    img = Image.fromarray(canvas.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    try:
        fp = os.path.join(HERE, "Baloo2.ttf")
        fnt_big = ImageFont.truetype(fp, int(ch * 0.30))
        fnt_sub = ImageFont.truetype(fp, int(ch * 0.082))
        try:
            fnt_big.set_variation_by_axes([800])
            fnt_sub.set_variation_by_axes([600])
        except Exception:
            pass
    except Exception:
        fnt_big = ImageFont.load_default()
        fnt_sub = ImageFont.load_default()
    wm = "BLOCKOUT"
    bb = d.textbbox((0, 0), wm, font=fnt_big)
    w_w = bb[2] - bb[0]
    avail = int(cw * 0.50)
    scale = min(1.0, (avail * 0.95) / w_w) if w_w else 1.0
    if scale < 1.0:
        fnt_big = ImageFont.truetype(fp, int(ch * 0.30 * scale))
        try:
            fnt_big.set_variation_by_axes([800])
        except Exception:
            pass
        bb = d.textbbox((0, 0), wm, font=fnt_big)
        w_w = bb[2] - bb[0]
    tx0, tx1 = int(cw * 0.40), int(cw * 0.95)
    cx = int((tx0 + tx1) / 2) - w_w // 2
    w_h = bb[3] - bb[1]
    cy = int(ch * 0.40) - w_h // 2
    d.text((cx - bb[0], cy - bb[1]), wm, font=fnt_big, fill=BROWN)
    sub_txt = "ARROW MATCHING PUZZLE"
    sb = d.textbbox((0, 0), sub_txt, font=fnt_sub)
    s_w = sb[2] - sb[0]
    scx = int((tx0 + tx1) / 2) - s_w // 2
    scy = cy + w_h + int(ch * 0.04) - sb[1]
    d.text((scx, scy), sub_txt, font=fnt_sub, fill=BROWN_SUB)
    canvas = np.asarray(img, np.float32)
    out = np.clip(canvas, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA").resize((W, H), Image.LANCZOS)


# ---------------- 输出全套 ----------------
IOS_FILES = [
    (20, 2, "iphone-notification@2x"), (20, 3, "iphone-notification@3x"),
    (29, 2, "iphone-settings@2x"), (29, 3, "iphone-settings@3x"),
    (40, 2, "iphone-spotlight@2x"), (40, 3, "iphone-spotlight@3x"),
    (60, 2, "iphone-app@2x"), (60, 3, "iphone-app@3x"),
    (76, 1, "ipad-app"), (76, 2, "ipad-app@2x"),
    (83.5, 2, "ipad-pro-app@2x"), (1024, 1, "ios-marketing"),
]
ANDROID_DENSITIES = [("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)]


def gen_set():
    manifest = {"generated": True, "platforms": {}}
    master = render_master(1024, 3)
    ios_dir = os.path.join(ROOT, "ios", "AppIcon.appiconset")
    os.makedirs(ios_dir, exist_ok=True)
    ios_manifest = {"images": [], "info": {"version": 1, "author": "xcode"}}
    for (pts, scale, name) in IOS_FILES:
        px = int(round(pts * scale))
        im = master.resize((px, px), Image.LANCZOS)
        fn = "%s-%dx%d.png" % (name, px, px)
        im.save(os.path.join(ios_dir, fn))
        idiom = "ipad" if pts in (76, 83.5) else "iphone"
        ios_manifest["images"].append({
            "size": "%gx%g" % (pts, pts), "idiom": idiom,
            "filename": fn, "scale": "%dx" % scale})
    with open(os.path.join(ios_dir, "Contents.json"), "w", encoding="utf-8") as f:
        json.dump(ios_manifest, f, indent=2)
    manifest["platforms"]["ios"] = len(ios_manifest["images"])
    for (dens, px) in ANDROID_DENSITIES:
        d = os.path.join(ROOT, "android", "mipmap-" + dens)
        os.makedirs(d, exist_ok=True)
        leg = master.resize((px, px), Image.LANCZOS)
        leg.save(os.path.join(d, "ic_launcher.png"))
        rnd = Image.new("RGBA", (px, px), (0, 0, 0, 0))
        rmask = Image.new("L", (px, px), 0)
        ImageDraw.Draw(rmask).ellipse((0, 0, px - 1, px - 1), fill=255)
        rmask = rmask.filter(ImageFilter.GaussianBlur(1))
        rnd.paste(draw_background(px), (0, 0), rmask)
        clu = draw_cluster(px)
        clu_s = clu.resize((int(px * 0.88), int(px * 0.88)), Image.LANCZOS)
        off = (px - clu_s.size[0]) // 2
        rnd.paste(clu_s, (off, off), clu_s)
        rnd.save(os.path.join(d, "ic_launcher_round.png"))
        fg = Image.new("RGBA", (px, px), (0, 0, 0, 0))
        fg_s = draw_cluster(int(px * 0.92), transparent=True)
        fg_off = (px - fg_s.size[0]) // 2
        fg.paste(fg_s, (fg_off, fg_off), fg_s)
        fg.save(os.path.join(d, "ic_launcher_foreground.png"))
        draw_background(px).save(os.path.join(d, "ic_launcher_background.png"))
    anydpi = os.path.join(ROOT, "android", "mipmap-anydpi-v26")
    os.makedirs(anydpi, exist_ok=True)
    for nm in ("ic_launcher", "ic_launcher_round"):
        with open(os.path.join(anydpi, nm + ".xml"), "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="utf-8"?>\n'
                '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                '    <background android:drawable="@mipmap/ic_launcher_background"/>\n'
                '    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>\n'
                '</adaptive-icon>\n')
    manifest["platforms"]["android"] = {"densities": len(ANDROID_DENSITIES)}
    master.resize((512, 512), Image.LANCZOS).save(os.path.join(ROOT, "play_store_512.png"))
    render_feature((1024, 500), 3).save(os.path.join(ROOT, "feature_graphic_1024x500.png"))
    manifest["platforms"]["play_store"] = ["play_store_512.png", "feature_graphic_1024x500.png"]
    with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print("done. files under", ROOT)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    gen_set()
