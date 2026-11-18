"""
v02 最终修订：画框程序化重建（对齐 panel-cream_v02 配色）、胶囊/锁 rim despill
输出：components/frame-art_v02.png  components/pill-cream_v02.png  icons/icon-lock_v02.png
"""
import cv2, numpy as np, os, shutil

BASE = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output'
REVIEW = BASE + r'\review'
SRC = {
    'pill':   r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media\miora_text_to_image-1794910409239-0-702abad431c3.png',
    'lock':   r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media\miora_text_to_image-1794910218679-0-92923ee47720.png',
}
# 取自 panel-cream_v02 实测（BGR）
CREAM = np.array([218, 234, 249], np.float32)   # 奶油主色
GOLD  = np.array([127, 196, 235], np.float32)   # 淡金辅线


# ------------------------------------------------------------------ 工具
def chroma_key(im):
    f = im.astype(np.float32)
    b, g, r = f[:, :, 0], f[:, :, 1], f[:, :, 2]
    subj = np.maximum(g / (r + 1), g / (b + 1))
    k = 10
    corners = np.concatenate([subj[:k, :k].ravel(), subj[:k, -k:].ravel(),
                              subj[-k:, :k].ravel(), subj[-k:, -k:].ravel()])
    lo = float(np.median(corners)) + 0.10
    hi = lo + 0.18
    a = (np.clip((subj - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
    a = cv2.GaussianBlur(a, (3, 3), 0.5)
    n, lab, stats, _ = cv2.connectedComponentsWithStats((a > 40).astype(np.uint8), 8)
    if n > 1:
        keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        a[lab != keep] = 0
    bg = np.median(im[a < 10].reshape(-1, 3), axis=0)
    al = a[..., None].astype(np.float32) / 255
    rgb = np.clip((f - (1 - al) * bg) / np.maximum(al, 0.5), 0, 255)
    rgb = np.where(a[..., None] < 25, im, rgb)
    return rgb.astype(np.uint8), a


def despeckle(rgb, alpha, min_area=40):
    solid = (alpha > 40).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(solid, 8)
    if n > 1:
        small = [i for i in range(1, n) if stats[i, 4] < min_area]
        if small:
            alpha = alpha.copy()
            alpha[np.isin(lab, small)] = 0
    return rgb, alpha


def despill_rim(rgb, alpha, rim=4):
    """把 alpha 边缘 rim 像素内的颜色替换为内侧实心色，清除洋红残留。
       注意：不止处理半透明像素，而是处理任何距透明区 <= rim 的像素。"""
    solid = (alpha > 0).astype(np.uint8)
    dist_in = cv2.distanceTransform(solid, cv2.DIST_L2, 5)   # 到透明边的距离
    core = (dist_in > rim + 1.5).astype(np.uint8)
    if core.sum() < 30:
        return rgb
    d2, labels = cv2.distanceTransformWithLabels(1 - core, cv2.DIST_L2, 5,
                                                 labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(core)
    coord = np.stack([xs, ys], 1)
    idx = labels - 1
    ok = (idx >= 0) & (idx < len(coord))
    safe = np.clip(idx, 0, len(coord) - 1)
    h, w = alpha.shape
    gy, gx = np.mgrid[0:h, 0:w]
    nx = np.where(ok, coord[safe, 0], gx)
    ny = np.where(ok, coord[safe, 1], gy)
    rim_mask = (alpha > 0) & (~core.astype(bool))
    out = rgb.copy()
    out[rim_mask] = rgb[ny[rim_mask], nx[rim_mask]]
    return out


def previews(rgba, name):
    a = rgba[:, :, 3].astype(np.float32) / 255
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    chk = (((xx // 24 + yy // 24) % 2) * 28 + 120).astype(np.uint8)
    bgs = {
        'checker': np.dstack([chk] * 3).astype(np.float32),
        'white': np.full((h, w, 3), 255, np.float32),
        'darkgray': np.full((h, w, 3), 55, np.float32),
        'lightblue': np.dstack([np.full((h, w), 245, np.float32),
                                np.full((h, w), 228, np.float32),
                                np.full((h, w), 205, np.float32)]),
    }
    for bn, bg in bgs.items():
        comp = (rgba[:, :, :3].astype(np.float32) * a[..., None] + bg * (1 - a[..., None])).astype(np.uint8)
        cv2.imwrite(os.path.join(REVIEW, f'{name}_{bn}.png'), comp)


def save(rgba, path, name):
    cv2.imwrite(path, rgba)
    previews(rgba, name)
    a = rgba[:, :, 3]
    ys, xs = np.nonzero(a > 40)
    print(f'  -> {os.path.basename(path)}  {rgba.shape[1]}x{rgba.shape[0]}  '
          f'bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) '
          f'body={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}')


def rounded_rect(size, l, t, r_, b, rad):
    m = np.zeros((size, size), np.uint8)
    cv2.rectangle(m, (l + rad, t), (r_ - rad, b), 255, -1)
    cv2.rectangle(m, (l, t + rad), (r_, b - rad), 255, -1)
    for cx, cy in [(l + rad, t + rad), (r_ - rad, t + rad),
                   (l + rad, b - rad), (r_ - rad, b - rad)]:
        cv2.circle(m, (cx, cy), rad, 255, -1)
    return m


# ============================================================ A11 画框
def build_frame():
    print('=== A11 frame-art_v02 (程序化重建) ===')
    S = 768
    outer = rounded_rect(S, 24, 24, 744, 744, 46)
    hole = np.zeros((S, S), np.uint8)
    cv2.rectangle(hole, (96, 96), (672, 672), 255, -1)
    mask = ((outer > 0) & (hole == 0)).astype(np.uint8)

    # 距离场：到任一边缘（含孔边缘）
    d = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    gx = cv2.Sobel(d, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(d, cv2.CV_32F, 0, 1, ksize=3)
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-6
    nx, ny = gx / nrm, gy / nrm
    lam = -(nx * -0.68 + ny * -0.68)              # 光来自左上

    bevel = np.clip(1.0 - d / 14.0, 0, 1)          # 边缘 14px 内做倒角
    ao = np.clip(1.0 - d / 26.0, 0, 1)             # 内缘环境遮蔽
    yy = np.arange(S, dtype=np.float32)[:, None]
    grad = (0.022 - 0.045 * (yy / S))              # 上亮下暗
    shade = 1.0 + 0.115 * bevel * lam - 0.075 * ao + grad
    shade = np.clip(shade, 0.80, 1.14)

    rgb = CREAM[None, None, :] * shade[:, :, None]

    # 单条金色细线：距外轮廓 46..54px（孔边留 18px 奶油内唇）
    d_out = cv2.distanceTransform((1 - outer).astype(np.uint8), cv2.DIST_L2, 5)
    d_out[outer == 0] = 0
    glow = np.clip(1.0 - np.abs(d_out - 50.0) / 5.0, 0, 1) ** 0.8   # 0..1 柔边
    gold_layer = GOLD[None, None, :] * (1.0 + 0.10 * lam)[:, :, None]
    gk = (glow * (mask > 0))[:, :, None]
    rgb = rgb * (1 - gk) + gold_layer * gk

    # 内唇（金线到孔之间）压暗，读作凹进去的内圈
    lip = ((d_out > 54) & (mask > 0)).astype(np.float32)
    lip = cv2.GaussianBlur(lip, (5, 5), 1.2)[:, :, None]
    rgb = rgb * (1 - 0.10 * lip)

    # 极轻颗粒，避免渐变色带
    rng = np.random.default_rng(7)
    rgb = rgb + rng.normal(0, 1.3, rgb.shape[:2])[:, :, None]

    alpha = cv2.GaussianBlur((mask * 255).astype(np.uint8), (3, 3), 0.6)
    alpha[96:673, 96:673] = 0                       # 保证要求区域全透明

    out = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), alpha])
    save(out, BASE + r'\components\frame-art_v02.png', 'frame-art_v02')
    print(f'  内孔 96..672 非透明像素={int((out[96:673,96:673,3]>0).sum())} (须0)')
    print(f'  金线亮度差: {float(rgb[384,72].mean()):.0f} vs 奶油 {float(rgb[384,40].mean()):.0f}')


# ============================================================ A13 胶囊
def build_pill():
    print('=== A13 pill-cream_v02 ===')
    im = cv2.imread(SRC['pill'])
    rgb, alpha = chroma_key(im)
    rgb, alpha = despeckle(rgb, alpha, 60)

    # 源胶囊 x176..592 y53..201 -> 目标 x12..500 y10..142
    sc = 74.5 / 66.0
    mid_scale = (517.5 - 250.5) / (434.0 - 78.0)
    X, Y = np.meshgrid(np.arange(512, dtype=np.float32), np.arange(160, dtype=np.float32))
    sx = np.empty_like(X); sy = np.empty_like(Y)
    a_t, b_t, c_t = 78.0, 434.0, 76.0
    a_s, b_s, c_s = 250.5, 517.5, 127.0
    left = X < a_t; right = X > b_t; mid = ~(left | right)
    sx[mid] = a_s + (X[mid] - a_t) * mid_scale
    sx[left] = a_s + (X[left] - a_t) * sc
    sx[right] = b_s + (X[right] - b_t) * sc
    sy[mid] = c_s + (Y[mid] - c_t) * sc
    sy[left] = c_s + (Y[left] - c_t) * sc
    sy[right] = c_s + (Y[right] - c_t) * sc
    w_rgb = cv2.remap(rgb, sx, sy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    mask = np.zeros((160, 512), np.uint8)
    cv2.rectangle(mask, (int(a_t), int(c_t - 66)), (int(b_t), int(c_t + 66)), 255, -1)
    cv2.ellipse(mask, (int(a_t), int(c_t)), (66, 66), 0, 90, 270, 255, -1)
    cv2.ellipse(mask, (int(b_t), int(c_t)), (66, 66), 0, -90, 90, 255, -1)

    # 关键：remap 在边缘采到了源图的洋红晕 -> 用 rim despill 换成内侧实心色
    w_rgb = despill_rim(w_rgb, mask, rim=5)
    alpha = cv2.GaussianBlur(mask, (3, 3), 0.4)

    out_rgb = w_rgb.astype(np.float32)
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    inner = (dist > 0) & (dist <= 3)
    out_rgb[inner] *= 0.93
    # 单条淡金细线：距胶囊边缘 20..24px
    band = (dist >= 20) & (dist <= 24)
    yy = np.arange(160, dtype=np.float32)
    shade = 1.05 - 0.14 * (yy / 160.0)
    g3 = np.repeat((GOLD[None, :] * shade[:, None])[:, None, :], 512, axis=1)
    out_rgb[band] = g3[band]

    out = np.dstack([np.clip(out_rgb, 0, 255).astype(np.uint8), alpha])
    save(out, BASE + r'\components\pill-cream_v02.png', 'pill-cream_v02')

    b, g, r = [out[:, :, i].astype(int) for i in range(3)]
    mag = int(((r - g > 45) & (b - g > 25) & (out[:, :, 3] > 10)).sum())
    print(f'  洋红残留像素={mag} (之前2016)  上安全边={int((alpha[:10]>10).sum())} 下={int((alpha[150:]>10).sum())}')


# ============================================================ A24 锁
def build_lock():
    print('=== A24 icon-lock_v02 ===')
    im = cv2.imread(SRC['lock'])
    rgb, alpha = chroma_key(im)
    rgb, alpha = despeckle(rgb, alpha, 40)

    # 清灰/洋红毛边
    band = (alpha > 0) & (alpha < 250)
    alpha = np.where(band, np.where(alpha > 128, 255, 0), alpha).astype(np.uint8)
    rgb = despill_rim(rgb, alpha, rim=4)

    # 降噪 + 弱化金属颗粒（审查：锁身噪点偏粗糙金属）
    sm = cv2.bilateralFilter(rgb, 9, 42, 9)
    sm = cv2.bilateralFilter(sm, 9, 42, 9)
    rgb = cv2.addWeighted(rgb, 0.15, sm, 0.85, 0)
    # 略降饱和，往奶油暖灰靠
    gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    rgb = cv2.addWeighted(rgb, 0.78, cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), 0.22, 0)
    rgb = despill_rim(rgb, alpha, rim=3)

    # 锁梁开口内清成透明
    solid = (alpha > 60).astype(np.uint8)
    free = (1 - solid).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(free, 4)
    border = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    holes = [i for i in range(1, n) if i not in border and stats[i, 4] > 30]
    for i in holes:
        comp = (lab == i)
        alpha[comp] = 0
        ys, xs = np.nonzero(comp)
        print(f'  开口透明化 bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) area={stats[i,4]}')
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.4)

    # 归一：最长边 205，居中
    ys, xs = np.nonzero(alpha > 60)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    scale = 205.0 / max(bw, bh)
    nw, nh = max(1, round(bw * scale)), max(1, round(bh * scale))
    res_a = cv2.resize(alpha[y0:y1 + 1, x0:x1 + 1], (nw, nh), interpolation=cv2.INTER_AREA)
    res_rgb = cv2.resize(rgb[y0:y1 + 1, x0:x1 + 1], (nw, nh), interpolation=cv2.INTER_CUBIC)
    canvas = np.zeros((256, 256, 4), np.uint8)
    ox, oy = 128 - nw // 2, 128 - nh // 2
    canvas[oy:oy + nh, ox:ox + nw, :3] = res_rgb
    canvas[oy:oy + nh, ox:ox + nw, 3] = res_a
    save(canvas, BASE + r'\icons\icon-lock_v02.png', 'icon-lock_v02')

    ys2, xs2 = np.nonzero(canvas[:, :, 3] > 60)
    b, g, r = [canvas[:, :, i].astype(int) for i in range(3)]
    mag = int(((r - g > 45) & (b - g > 25) & (canvas[:, :, 3] > 60)).sum())
    print(f'  边距 左={xs2.min()} 右={255-xs2.max()} 上={ys2.min()} 下={255-ys2.max()} (>=20)')
    print(f'  洋红像素={mag}  锁身噪点std={float(canvas[oy:oy+nh, ox:ox+nw, 1][res_a>250].std()):.1f}')


if __name__ == '__main__':
    build_frame()
    build_pill()
    build_lock()
    print('done')
