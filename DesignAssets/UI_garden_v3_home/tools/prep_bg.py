# -*- coding: utf-8 -*-
"""Prepare a generated background: locate/remove the AI watermark and save bg_source.png."""
import os, sys
import numpy as np
import cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, 'art')


def find_watermark(img):
    """The generator stamps a rounded light box in the bottom area - find its bright bbox."""
    a = np.array(img.convert('RGB'))
    h, w = a.shape[:2]
    band = a[int(h * 0.80):, :, :]
    gray = cv2.cvtColor(band, cv2.COLOR_RGB2GRAY)
    # the badge is a flat, near-white rounded box on a colourful scene
    m = (gray > 205).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    best, area = None, 0
    for i in range(1, n):
        x, y, bw, bh, ar = st[i]
        if ar > 2000 and bw > 60 and bh > 30 and bw / max(1, bh) > 1.6:
            if ar > area:
                best, area = (x, y + int(h * 0.80), bw, bh), ar
    return best


def remove_watermark(img, box=None):
    """Patch the stamped badge out by cloning the scene from straight above it."""
    arr = np.array(img.convert('RGB'), dtype=np.float32)
    h, w = arr.shape[:2]
    if box is None:
        # fixed position of the generator stamp: bottom-right, above the nav area
        bw_, bh_ = int(img.width * 0.36), int(img.height * 0.075)
        box = (img.width - bw_ - 4, img.height - bh_ - 6, bw_, bh_)
    if box is None:
        return img, None
    x, y, bw, bh = box
    pad = 12
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(w, x + bw + pad), min(h, y + bh + pad)
    bh_, bw_ = y1 - y0, x1 - x0
    sy = y0 - bh_ - 18
    if sy >= 0:
        src = arr[sy:sy + bh_, x0:x1, :]
    else:
        src = np.repeat(arr[y0:y0 + 1, x0:x1, :], bh_, axis=0)
    m = np.ones((bh_, bw_), np.float32)
    m[:4, :] = 0; m[-4:, :] = 0; m[:, :4] = 0; m[:, -4:] = 0
    m = cv2.GaussianBlur(m, (0, 0), 5)[:, :, None]
    out = arr.copy()
    out[y0:y1, x0:x1, :] = arr[y0:y1, x0:x1, :] * (1 - m) + src * m
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)), (x0, y0, x1, y1)


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'gen', 'bg_v1.png')
    im = Image.open(src)
    out, box = remove_watermark(im)
    print('watermark box:', box)
    out.save(os.path.join(ART, 'bg_source.png'))
    print('saved art/bg_source.png', out.size)
