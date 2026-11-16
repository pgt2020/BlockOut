# -*- coding: utf-8 -*-
"""Clay-style component generator (nodes, buttons, bars, badges) for the garden UI kit.

Everything is drawn at 4x and downsampled, so the assets are clean at 2x usage.
Shapes follow the reference: cream rim, vertical colour gradient, top gloss,
inner bottom shade, soft drop shadow.
"""
import os
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter

SS = 4


def _rr_mask(size, box, radius):
    m = Image.new('L', size, 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=radius, fill=255)
    return m


def _gradient(size, box, top, bottom):
    g = Image.new('RGBA', size, (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    y1, y2 = box[1], box[3]
    for y in range(y1, y2 + 1):
        t = (y - y1) / max(1, y2 - y1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (size[0], y)], fill=c + (255,))
    return g


def clay(w, h, radius, top, bottom, rim=(255, 253, 245), rim_w=9,
         gloss=0.55, shadow=90, glow=None, inner_line=True, ground=0):
    """One clay element: rounded rect with rim, gradient fill and soft lights."""
    W, H = w * SS, h * SS
    rim_w *= SS
    radius *= SS
    pad = 14 * SS
    box = [pad, pad, W - pad, H - pad]
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    if glow:
        gl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(gl).rounded_rectangle(box, radius=radius, fill=glow)
        im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(16 * SS)))

    if shadow:
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle(
            [box[0] + 3 * SS, box[1] + 11 * SS, box[2] + 3 * SS, box[3] + 11 * SS],
            radius=radius, fill=(34, 48, 26, shadow))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9 * SS)))

    # cream rim
    ImageDraw.Draw(im).rounded_rectangle(box, radius=radius, fill=rim)
    inner = [box[0] + rim_w, box[1] + rim_w, box[2] - rim_w, box[3] - rim_w]
    ir = max(4, radius - rim_w)
    grad = _gradient((W, H), inner, top, bottom)
    im.paste(grad, (0, 0), _rr_mask((W, H), inner, ir))

    fill_mask = _rr_mask((W, H), inner, ir)

    # gloss band across the upper third
    if gloss:
        band_h = int((inner[3] - inner[1]) * 0.34)
        gl = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(gl).rounded_rectangle(
            [inner[0] + 3 * SS, inner[1] + 2 * SS, inner[2] - 3 * SS, inner[1] + band_h],
            radius=ir, fill=(255, 255, 255, int(255 * gloss * 0.42)))
        gl = gl.filter(ImageFilter.GaussianBlur(9 * SS))
        im.alpha_composite(Image.composite(gl, Image.new('RGBA', (W, H), (0, 0, 0, 0)), fill_mask))

    # inner bottom shade
    dk = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(dk).rounded_rectangle(
        [inner[0] + 2 * SS, inner[3] - 22 * SS, inner[2] - 2 * SS, inner[3] + 6 * SS],
        radius=ir, fill=(0, 0, 0, 46))
    dk = dk.filter(ImageFilter.GaussianBlur(7 * SS))
    im.alpha_composite(Image.composite(dk, Image.new('RGBA', (W, H), (0, 0, 0, 0)), fill_mask))

    # light inner bevel line
    if inner_line:
        ln = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ln).rounded_rectangle(
            [inner[0] + 2 * SS, inner[1] + 2 * SS, inner[2] - 2 * SS, inner[3] - 2 * SS],
            radius=ir, outline=(255, 255, 255, 78), width=max(1, SS))
        ln = ln.filter(ImageFilter.GaussianBlur(1.4 * SS))
        im.alpha_composite(Image.composite(ln, Image.new('RGBA', (W, H), (0, 0, 0, 0)), fill_mask))

    # rim shading so the cream ring reads as a raised border
    rm = _rr_mask((W, H), box, radius)
    ring = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.rounded_rectangle(box, radius=radius, outline=(198, 172, 130, 120), width=2 * SS)
    rd.rounded_rectangle([inner[0] - 2 * SS, inner[1] - 2 * SS, inner[2] + 2 * SS, inner[3] + 2 * SS],
                         radius=ir + 2 * SS, outline=(255, 255, 255, 130), width=SS)
    ring = ring.filter(ImageFilter.GaussianBlur(0.8 * SS))
    im.alpha_composite(Image.composite(ring, Image.new('RGBA', (W, H), (0, 0, 0, 0)), rm))

    return im.resize((w, h), Image.LANCZOS)


def pill(w, h, radius, top, bottom, rim=(255, 253, 245), rim_w=7, gloss=0.5, shadow=80):
    return clay(w, h, radius, top, bottom, rim=rim, rim_w=rim_w, gloss=gloss,
                shadow=shadow, inner_line=False)


NODE_COLORS = {
    'locked':    ((206, 204, 202), (156, 154, 152), (255, 253, 245), None),
    'current':   ((126, 226, 190), (58, 178, 138), (255, 253, 240), (255, 236, 150, 120)),
    'star':      ((202, 160, 244), (148, 100, 206), (255, 253, 245), None),
    'fail':      ((250, 148, 132), (214, 84, 72), (255, 253, 245), None),
    'challenge': ((250, 148, 132), (214, 84, 72), (255, 253, 245), None),
    'done':      ((150, 232, 186), (74, 186, 126), (255, 253, 245), None),
    'completed': ((150, 232, 186), (74, 186, 126), (255, 253, 245), None),
}


def node(state, size=256):
    top, bottom, rim, glow = NODE_COLORS[state]
    return clay(size, size, int(size * 0.26), top, bottom, rim=rim, rim_w=14,
                gloss=0.62, shadow=105, glow=glow)


def badge_star(size=128):
    W = size * SS
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    pad = 6 * SS
    sh = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([pad, pad + 4 * SS, W - pad, W - pad + 4 * SS], fill=(40, 50, 30, 80))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(2.5 * SS)))
    ImageDraw.Draw(im).ellipse([pad, pad, W - pad, W - pad], fill=(255, 250, 238))
    ImageDraw.Draw(im).ellipse([pad + 5 * SS, pad + 5 * SS, W - pad - 5 * SS, W - pad - 5 * SS],
                               fill=(156, 106, 214))
    pts = []
    cx = cy = W / 2
    R, r = W * 0.30, W * 0.135
    for i in range(10):
        ang = -np.pi / 2 + i * np.pi / 5
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * np.cos(ang), cy + rad * np.sin(ang)))
    ImageDraw.Draw(im).polygon(pts, fill=(255, 253, 246))
    return im.resize((size, size), Image.LANCZOS)


def badge_plus(size=128):
    W = size * SS
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    pad = 6 * SS
    sh = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([pad, pad + 4 * SS, W - pad, W - pad + 4 * SS], fill=(40, 60, 30, 85))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(2.5 * SS)))
    ImageDraw.Draw(im).ellipse([pad, pad, W - pad, W - pad], fill=(255, 251, 240))
    ImageDraw.Draw(im).ellipse([pad + 5 * SS, pad + 5 * SS, W - pad - 5 * SS, W - pad - 5 * SS],
                               fill=(64, 190, 112))
    bar_w = int(W * 0.13)
    bar_l = int(W * 0.30)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([bar_l, W / 2 - bar_w / 2, W - bar_l, W / 2 + bar_w / 2],
                        radius=bar_w / 2, fill=(255, 255, 255))
    d.rounded_rectangle([W / 2 - bar_w / 2, bar_l, W / 2 + bar_w / 2, W - bar_l],
                        radius=bar_w / 2, fill=(255, 255, 255))
    return im.resize((size, size), Image.LANCZOS)


def badge_lock(size=128):
    W = size * SS
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    pad = 8 * SS
    d = ImageDraw.Draw(im)
    # shackle
    sw = int(W * 0.10)
    d.arc([W * 0.31 - sw, W * 0.20, W * 0.69 + sw, W * 0.62],
          start=180, end=360, fill=(255, 250, 238), width=sw + 2 * SS)
    d.arc([W * 0.34, W * 0.24, W * 0.66, W * 0.60],
          start=180, end=360, fill=(176, 172, 168), width=sw)
    body = [pad, W * 0.42, W - pad, W - pad]
    d.rounded_rectangle(body, radius=int(W * 0.12), fill=(255, 250, 238))
    d.rounded_rectangle([body[0] + 4 * SS, body[1] + 4 * SS, body[2] - 4 * SS, body[3] - 4 * SS],
                        radius=int(W * 0.10), fill=(186, 182, 178))
    # keyhole
    cx, cy = W / 2, W * 0.62
    d.ellipse([cx - W * 0.06, cy - W * 0.06, cx + W * 0.06, cy + W * 0.06], fill=(255, 252, 245))
    d.rounded_rectangle([cx - W * 0.025, cy, cx + W * 0.025, cy + W * 0.12],
                        radius=W * 0.02, fill=(255, 252, 245))
    return im.resize((size, size), Image.LANCZOS)


def badge_skull(size=128):
    W = size * SS
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([W * 0.10, W * 0.10, W * 0.90, W * 0.86], fill=(255, 250, 240))
    d.ellipse([W * 0.20, W * 0.18, W * 0.80, W * 0.76], fill=(246, 240, 228))
    d.ellipse([W * 0.28, W * 0.36, W * 0.44, W * 0.55], fill=(120, 104, 92))
    d.ellipse([W * 0.56, W * 0.36, W * 0.72, W * 0.55], fill=(120, 104, 92))
    d.polygon([(W * 0.50, W * 0.58), (W * 0.44, W * 0.68), (W * 0.56, W * 0.68)], fill=(120, 104, 92))
    d.rounded_rectangle([W * 0.32, W * 0.72, W * 0.68, W * 0.88], radius=W * 0.05, fill=(246, 240, 228))
    for i in range(3):
        x = W * (0.36 + i * 0.12)
        d.line([(x, W * 0.74), (x, W * 0.86)], fill=(150, 132, 118), width=max(1, int(W * 0.02)))
    return im.resize((size, size), Image.LANCZOS)


def badge_alert(size=96):
    W = size * SS
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([W * 0.06, W * 0.06, W * 0.94, W * 0.94], fill=(255, 250, 240))
    d.ellipse([W * 0.16, W * 0.16, W * 0.84, W * 0.84], fill=(240, 92, 80))
    return im.resize((size, size), Image.LANCZOS)


def tab_card(w=196, h=210, active=True):
    W, H = w * SS, h * SS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if active:
        pad = 4 * SS
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([pad, pad + 5 * SS, W - pad, H - pad + 5 * SS],
                                             radius=26 * SS, fill=(60, 70, 40, 55))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5 * SS)))
        ImageDraw.Draw(im).rounded_rectangle([pad, pad, W - pad, H - pad], radius=26 * SS,
                                             fill=(255, 253, 245))
        g = _gradient((W, H), [pad + 6 * SS, pad + 6 * SS, W - pad - 6 * SS, H - pad - 6 * SS],
                      (255, 255, 252), (252, 245, 226))
        im.paste(g, (0, 0), _rr_mask((W, H), [pad + 6 * SS, pad + 6 * SS, W - pad - 6 * SS, H - pad - 6 * SS], 25 * SS))
        # active underline
        ImageDraw.Draw(im).rounded_rectangle(
            [W * 0.28, H - 22 * SS, W * 0.72, H - 12 * SS], radius=5 * SS, fill=(86, 196, 120))
    return im.resize((w, h), Image.LANCZOS)


def plate(w=280, h=88, radius=26):
    return clay(w, h, radius, (255, 250, 236), (248, 233, 203),
                rim=(255, 252, 242), rim_w=4, gloss=0.25, shadow=55, inner_line=False)


def circle_btn(size=120):
    return clay(size, size, size // 2, (255, 253, 246), (247, 233, 205),
                rim=(255, 252, 242), rim_w=6, gloss=0.3, shadow=70)


def checkered_preview(img, bg=(240, 238, 230)):
    w, h = img.size
    out = Image.new('RGB', (w, h), bg)
    out.paste(img, (0, 0), img)
    return out


def bubble(w=300, h=140, radius=34, tail=True):
    """Cream speech bubble with a small tail, used for the 当前关卡 callout."""
    W, H = w * SS, h * SS
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    pad = 8 * SS
    box = [pad, pad, W - pad, H - pad - (26 * SS if tail else 0)]
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([box[0] + 2 * SS, box[1] + 8 * SS, box[2] + 2 * SS, box[3] + 8 * SS],
                                         radius=radius, fill=(40, 56, 30, 80))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6 * SS)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, radius=radius, fill=(255, 252, 242))
    inner = [box[0] + 4 * SS, box[1] + 4 * SS, box[2] - 4 * SS, box[3] - 4 * SS]
    g = _gradient((W, H), inner, (255, 253, 246), (252, 240, 216))
    im.paste(g, (0, 0), _rr_mask((W, H), inner, radius - 4 * SS))
    if tail:
        tip = [(W * 0.18, box[3] - 4 * SS), (W * 0.34, box[3] - 4 * SS), (W * 0.16, H - pad)]
        d.polygon([(tip[0][0], tip[0][1] - 2 * SS), (tip[1][0], tip[1][1] - 2 * SS), tip[2]],
                  fill=(255, 252, 242))
    return im.resize((w, h), Image.LANCZOS)


def node_pointer(size=64):
    """Downward pointer under the current-level node."""
    W = size * SS
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(W * 0.24, W * 0.02), (W * 0.76, W * 0.02), (W * 0.5, W * 0.72)], fill=(255, 252, 242))
    d.polygon([(W * 0.32, W * 0.06), (W * 0.68, W * 0.06), (W * 0.5, W * 0.60)], fill=(96, 214, 170))
    return im.resize((size, size), Image.LANCZOS)
