# -*- coding: utf-8 -*-
"""按 shapeId 生成软胶方块贴图（灰阶白模，供 Custom_PerfectTint 染色）。

为什么是灰阶：项目 shader 是 `texColor.rgb * tint.rgb`，彩色贴图乘色会脏。
明暗信息（体积感/描边/格线）全部烘进 RGB，色相由关卡 block.Color 提供。

每格 240px：与 BlockOutBoardView 的 `sizeDelta = sprite.rect.width * (cellSize/240f)` 对齐，
贴图宽度 = cols*240 → 方块正好铺满 cols 个格子。
"""
import os, sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'UI_r1_board', 'tools'))
from extract_level import SHAPES  # noqa: E402

CELL = 240
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'block_sprites')
os.makedirs(OUT, exist_ok=True)


def make(shape_id, cells):
    rows = max(r for r, c in cells) + 1
    cols = max(c for r, c in cells) + 1
    W, H = cols * CELL, rows * CELL
    P = 64  # 画布外扩：PIL 高斯模糊在图像边界按钳制处理，不留边则边缘不会衰减（圆角失效）

    # ---- 1) 并集掩码（画在带 padding 的画布上） ----
    m = Image.new('L', (W + 2 * P, H + 2 * P), 0)
    d = ImageDraw.Draw(m)
    for (r, c) in cells:
        d.rectangle((P + c * CELL, P + r * CELL,
                     P + (c + 1) * CELL - 1, P + (r + 1) * CELL - 1), fill=255)

    # ---- 2) 高斯模糊 + 阈值 = 圆角外轮廓（同时向内收形成块间缝隙） ----
    blurred = m.filter(ImageFilter.GaussianBlur(27)).crop((P, P, P + W, P + H))
    a = np.array(blurred, np.float32) / 255.0
    T = 0.600
    alpha = np.clip((a - T) / 0.040 + 0.5, 0.0, 1.0)
    solid = alpha > 0.5

    # ---- 3) 体积：每格独立的顶亮→底暗渐变 ----
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rgb = np.full((H, W), 0.865, np.float32)
    for (r, c) in cells:
        y0, y1, x0, x1 = r * CELL, (r + 1) * CELL, c * CELL, (c + 1) * CELL
        ly = (yy[y0:y1, x0:x1] - y0) / CELL
        # 每格只做轻微起伏：幅度一大，多格块会出现一条条重复暗带，像断层
        grad = np.interp(ly, [0.0, 0.5, 1.0], [0.040, 0.0, -0.040])
        rgb[y0:y1, x0:x1] += grad
        # 左右侧轻微压暗，暗示每格的厚度
        lx = np.abs((xx[y0:y1, x0:x1] - x0) / CELL - 0.5) * 2.0
        rgb[y0:y1, x0:x1] -= np.clip((lx - 0.80) / 0.20, 0, 1) * 0.035

    # 整块统一的受光：顶部亮面 → 底部侧面折线（厚度只出现在块的上下沿，不在每格）
    gy = yy / H
    rgb += np.interp(gy, [0.0, 0.05, 0.18, 0.82, 0.885, 1.0],
                          [0.075, 0.045, 0.0, 0.0, -0.150, -0.185])

    # ---- 4) 格线：仅画块内部相邻格的接缝（块外轮廓由 alpha 决定，不画） ----
    seam = np.zeros((H, W), np.float32)
    cellset = set(cells)
    for (r, c) in cells:
        if (r + 1, c) in cellset:            # 水平接缝
            y = (r + 1) * CELL
            seam[max(0, y - 4):y + 4, c * CELL + 6:(c + 1) * CELL - 6] = 1.0
        if (r, c + 1) in cellset:            # 垂直接缝
            x = (c + 1) * CELL
            seam[r * CELL + 6:(r + 1) * CELL - 6, max(0, x - 4):x + 4] = 1.0
    seam = np.array(Image.fromarray((seam * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255.0
    rgb -= seam * 0.090 * solid

    # ---- 5) 外描边：alpha 边缘环提亮，模拟浅奶油描边（染色后为亮色版本） ----
    ai = Image.fromarray((alpha * 255).astype(np.uint8))
    inner = np.array(ai.filter(ImageFilter.MinFilter(13)), np.float32) / 255.0
    rim = np.clip(alpha - inner, 0.0, 1.0)
    rim = np.array(Image.fromarray((rim * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6)), np.float32) / 255.0
    rgb += rim * 0.14

    rgb = np.clip(rgb, 0.0, 1.0)
    buf = np.empty((H, W, 4), np.uint8)
    g = (rgb * 255.0).astype(np.uint8)          # 灰阶明暗：RGB 三通道同值，色相由 tint 给
    buf[..., 0] = g
    buf[..., 1] = g
    buf[..., 2] = g
    buf[..., 3] = (np.clip(alpha, 0.0, 1.0) * 255.0).astype(np.uint8)
    return Image.frombytes('RGBA', (W, H), buf.tobytes())


def main():
    ids = sorted(SHAPES.keys())
    for sid in ids:
        cells = SHAPES[sid]
        img = make(sid, cells)
        img.save(os.path.join(OUT, '%d.png' % sid))
    print('generated', len(ids), 'sprites ->', OUT)
    print('sizes', [(sid, make(sid, SHAPES[sid]).size) for sid in (1, 10, 20, 29, 30)])


if __name__ == '__main__':
    main()
