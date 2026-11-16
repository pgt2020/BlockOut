# -*- coding: utf-8 -*-
"""Matte extraction helpers for slicing UI elements out of a rendered screenshot.

Pipeline per element:
  1. a hand-fitted soft silhouette (rounded rect / circle / polygon)
  2. a soft colour trim, so background pixels that fall inside the rough
     silhouette (sky showing in a corner, grass behind a corner radius) drop out
  3. edge colour decontamination against an inpainted interior, which kills the
     blue/cream fringe without the noise that full un-premultiply produces
"""
import numpy as np
import cv2
from PIL import Image, ImageDraw


def _ss_mask(w, h, shapes, scale=4):
    m = Image.new('L', (w * scale, h * scale), 0)
    d = ImageDraw.Draw(m)
    for s in shapes:
        t = s[0]
        if t == 'rr':
            _, x1, y1, x2, y2, r = s
            d.rounded_rectangle([x1 * scale, y1 * scale, x2 * scale, y2 * scale],
                                radius=max(0, r) * scale, fill=255)
        elif t == 'circle':
            _, cx, cy, r = s
            d.ellipse([(cx - r) * scale, (cy - r) * scale, (cx + r) * scale, (cy + r) * scale], fill=255)
        elif t == 'ellipse':
            _, cx, cy, rx, ry = s
            d.ellipse([(cx - rx) * scale, (cy - ry) * scale, (cx + rx) * scale, (cy + ry) * scale], fill=255)
        elif t == 'poly':
            _, pts = s
            d.polygon([(x * scale, y * scale) for x, y in pts], fill=255)
    return np.array(m.resize((w, h), Image.LANCZOS), dtype=np.float32) / 255.0


def local_shapes(shapes, x1, y1):
    out = []
    for s in shapes:
        t = s[0]
        if t == 'rr':
            _, a, b, c, d_, r = s
            out.append(('rr', a - x1, b - y1, c - x1, d_ - y1, r))
        elif t == 'circle':
            _, cx, cy, r = s
            out.append(('circle', cx - x1, cy - y1, r))
        elif t == 'ellipse':
            _, cx, cy, rx, ry = s
            out.append(('ellipse', cx - x1, cy - y1, rx, ry))
        elif t == 'poly':
            _, pts = s
            out.append(('poly', [(a - x1, b - y1) for a, b in pts]))
    return out


def matte(src, box, shapes, feather=1.0, trim=0.20, trim_floor=0.05, glow=0, desky=False,
          hard=True, degrass=0):
    """Return an RGBA crop of the element described by `shapes`."""
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    crop = np.array(src.convert('RGB').crop(box), dtype=np.float32)
    sil = _ss_mask(w, h, local_shapes(shapes, x1, y1))
    sil = cv2.GaussianBlur(sil, (0, 0), feather)

    inner = (sil > 0.5).astype(np.uint8)
    grown = cv2.dilate(cv2.dilate(inner, np.ones((5, 5), np.uint8)),
                       cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
    plate = cv2.inpaint(crop.astype(np.uint8), grown, 7, cv2.INPAINT_TELEA).astype(np.float32)

    dist = np.linalg.norm(crop - plate, axis=2) / 255.0
    # soft "is this pixel part of the element" test; shadows count as element
    col = np.clip((dist - trim_floor) / max(trim, 1e-3), 0.0, 1.0)
    col = cv2.GaussianBlur(col, (0, 0), 1.0)
    if glow:
        col = np.clip(col * (1 + glow), 0, 1)

    alpha = sil.astype(np.float32) if hard else sil * np.maximum(col, 0.0)
    # keep the solid core fully opaque even where colour is flat
    core = cv2.erode(inner, np.ones((5, 5), np.uint8))
    alpha = np.where(core > 0, np.maximum(alpha, 0.97), alpha)

    if degrass:
        # the bar/button rim picks up a tint of the grass shadow behind it; drop that band
        hsv = cv2.cvtColor(crop.astype(np.uint8), cv2.COLOR_RGB2HSV)
        grass = (hsv[:, :, 0] >= 33) & (hsv[:, :, 0] <= 82) & (hsv[:, :, 1] > 50) & (hsv[:, :, 2] > 40)
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (degrass * 2 + 1,) * 2)
        eroded = cv2.erode((sil > 0.5).astype(np.uint8), k)
        alpha = np.where(grass & (eroded == 0), 0.0, alpha)

    if desky:
        # drop sky (and the bluish shadow it casts) that crept inside the silhouette
        hsv = cv2.cvtColor(crop.astype(np.uint8), cv2.COLOR_RGB2HSV)
        sky = (hsv[:, :, 0] >= 92) & (hsv[:, :, 0] <= 132) & (hsv[:, :, 1] > 22) & (hsv[:, :, 2] > 80)
        alpha = np.where(sky, 0.0, alpha)
    alpha = np.clip(alpha, 0, 1)

    # decontaminate edges: pull border colour toward the inpainted interior
    edge_unknown = (alpha < 0.92).astype(np.uint8)
    interior = cv2.inpaint(crop.astype(np.uint8), edge_unknown, 8, cv2.INPAINT_TELEA).astype(np.float32)
    t = np.clip((alpha - 0.10) / 0.82, 0.0, 1.0)[:, :, None]
    fg = interior * (1 - t) + crop * t

    out = np.dstack([np.clip(fg, 0, 255), alpha * 255.0]).astype(np.uint8)
    return Image.fromarray(out, 'RGBA')


def inpaint_text(rgba, mask_fn, radius=6, feather=1.4, grow=3):
    """Erase baked glyphs from an RGBA sprite and rebuild the fill underneath."""
    arr = np.array(rgba.convert('RGBA'), dtype=np.uint8)
    rgb = arr[:, :, :3].astype(np.float32)
    a = arr[:, :, 3]
    m = mask_fn(rgb, a).astype(np.uint8) * 255
    if grow:
        m = cv2.dilate(m, cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (grow * 2 + 1, grow * 2 + 1)))
    patched = cv2.inpaint(cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR), m, radius, cv2.INPAINT_TELEA)
    patched = cv2.cvtColor(patched, cv2.COLOR_BGR2RGBA).astype(np.float32)
    mm = (m.astype(np.float32) / 255.0)[:, :, None]
    mm = cv2.GaussianBlur(mm, (0, 0), feather)
    out = arr.astype(np.float32) * (1 - mm) + patched * mm
    out[:, :, 3] = a
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')
