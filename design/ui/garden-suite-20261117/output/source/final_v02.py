"""
v02 终稿：统一程序化引擎重建 frame-art_v02 / pill-cream_v02，锁做 rim despill
配色全部取自已通过的 panel-cream_v02（BGR）
"""
import cv2, numpy as np, os

BASE = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output'
REVIEW = BASE + r'\review'
LOCK_SRC = r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media\miora_text_to_image-1794910218679-0-92923ee47720.png'

CREAM = np.array([216, 233, 249], np.float32)   # 奶油边  (RGB 249,233,216)
GOLD  = np.array([112, 180, 224], np.float32)   # 淡金细线 (RGB 224,180,112)
FACE  = np.array([238, 244, 251], np.float32)   # 暖白面  (RGB 251,244,238)

LX, LY = -0.62, -0.78                            # 左上方光源


# ------------------------------------------------------------------ 通用
def shade_field(mask, bevel=14.0, ao=26.0, k_bevel=0.13, k_ao=0.10, grad=0.024):
    """基于距离场的软倒角 + 环境遮蔽 + 垂直渐变"""
    d = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    gx = cv2.Sobel(d, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(d, cv2.CV_32F, 0, 1, ksize=3)
    nrm = np.sqrt(gx * gx + gy * gy) + 1e-6
    nx, ny = gx / nrm, gy / nrm
    lam = -(nx * LX + ny * LY)                   # 朝光为正
    h, w = mask.shape
    yy = np.arange(h, dtype=np.float32)[:, None]
    g = grad - 2 * grad * (yy / max(1, h - 1))
    b = np.clip(1.0 - d / bevel, 0, 1)
    a = np.clip(1.0 - d / ao, 0, 1)
    return np.clip(1.0 + k_bevel * b * lam - k_ao * a + g, 0.78, 1.16), d_out_only(mask)


def d_out_only(mask):
    """到 mask 外边界的距离（只测外侧，孔/内面不算）"""
    solid = (mask > 0).astype(np.uint8)
    free = (1 - solid).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(free, 4)
    h, w = mask.shape
    border = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    holes = [i for i in range(1, n) if i not in border]
    outside = np.isin(lab, list(border)) & (free > 0)
    m = outside.astype(np.uint8)
    return cv2.distanceTransform(1 - m, cv2.DIST_L2, 5)


def gold_overlay(rgb, dist, lo, hi, feather=1.6, strength=1.0):
    """在 dist∈[lo,hi] 处叠一条柔边金线"""
    mid = (lo + hi) / 2.0
    half = (hi - lo) / 2.0
    t = np.clip(1.0 - (np.abs(dist - mid) - (half - feather)) / feather, 0, 1)
    t = np.clip(t, 0, 1) ** 0.75 * strength
    return rgb * (1 - t[:, :, None]) + GOLD[None, None, :] * t[:, :, None]


def grain(rgb, amp=1.2, seed=3):
    rng = np.random.default_rng(seed)
    return rgb + rng.normal(0, amp, rgb.shape[:2])[:, :, None]


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


def rrect(size, l, t, r_, b, rad):
    m = np.zeros((size, size), np.uint8)
    cv2.rectangle(m, (l + rad, t), (r_ - rad, b), 255, -1)
    cv2.rectangle(m, (l, t + rad), (r_, b - rad), 255, -1)
    for cx, cy in [(l + rad, t + rad), (r_ - rad, t + rad),
                   (l + rad, b - rad), (r_ - rad, b - rad)]:
        cv2.circle(m, (cx, cy), rad, 255, -1)
    return m


# ============================================================ A11 画框
def build_frame():
    print('=== A11 frame-art_v02 ===')
    S = 768
    outer = rrect(S, 24, 24, 744, 744, 46)
    hole = np.zeros((S, S), np.uint8)
    cv2.rectangle(hole, (96, 96), (672, 672), 255, -1)
    ring = ((outer > 0) & (hole == 0)).astype(np.uint8)

    sh, d_out = shade_field(ring, bevel=16.0, ao=30.0, k_bevel=0.14, k_ao=0.13)
    rgb = CREAM[None, None, :] * sh[:, :, None]

    # 单条金线：距外轮廓 45..51px（孔边留 21px 奶油内唇，金线不进透明区）
    rgb = gold_overlay(rgb, d_out, 44, 51, feather=2.0, strength=0.92)

    # 内唇微压暗，读作画框内侧凹槽
    lip = ((d_out > 53) & (ring > 0)).astype(np.float32)
    lip = cv2.GaussianBlur(lip, (5, 5), 1.4)[:, :, None]
    rgb = rgb * (1 - 0.10 * lip)
    # 最外缘 2px 柔光高光，避免硬边
    riml = np.clip(1 - d_out / 2.5, 0, 1)[:, :, None] * 0.05
    rgb = rgb + 255 * riml * (ring > 0)[:, :, None]

    rgb = grain(rgb, 1.2)
    alpha = cv2.GaussianBlur((ring * 255).astype(np.uint8), (3, 3), 0.6)
    alpha[96:673, 96:673] = 0
    out = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), alpha])
    save(out, BASE + r'\components\frame-art_v02.png', 'frame-art_v02')
    print(f'  内孔 96..672 非透明像素={int((out[96:673,96:673,3]>0).sum())} (须0)')
    print(f'  金线@x=72 均值={float(rgb[384,72].mean()):.0f}  奶油@x=40 均值={float(rgb[384,40].mean()):.0f}')


# ============================================================ A13 胶囊
def build_pill():
    print('=== A13 pill-cream_v02 ===')
    W, H = 512, 160
    a_t, b_t, c_t, r = 78, 434, 76, 66
    outer = np.zeros((H, W), np.uint8)
    cv2.rectangle(outer, (a_t, c_t - r), (b_t, c_t + r), 255, -1)
    cv2.ellipse(outer, (a_t, c_t), (r, r), 0, 90, 270, 255, -1)
    cv2.ellipse(outer, (b_t, c_t), (r, r), 0, -90, 90, 255, -1)

    # 内面（暖白平板）：内缩 30px 的胶囊
    inset = 30
    face = np.zeros((H, W), np.uint8)
    cv2.rectangle(face, (a_t, c_t - (r - inset)), (b_t, c_t + (r - inset)), 255, -1)
    cv2.ellipse(face, (a_t, c_t), (r - inset, r - inset), 0, 90, 270, 255, -1)
    cv2.ellipse(face, (b_t, c_t), (r - inset, r - inset), 0, -90, 90, 255, -1)

    ringm = ((outer > 0) & (face == 0)).astype(np.uint8)
    sh, d_out = shade_field(ringm, bevel=10.0, ao=14.0, k_bevel=0.12, k_ao=0.11, grad=0.020)
    rgb = CREAM[None, None, :] * sh[:, :, None]
    rgb = gold_overlay(rgb, d_out, 17, 21.5, feather=1.6, strength=0.92)

    # 暖白面：平整，只在贴边 3px 处轻微内阴影
    dface = cv2.distanceTransform(face, cv2.DIST_L2, 5)
    fsh = 1.0 + 0.018 - 0.028 * (np.arange(H, dtype=np.float32)[:, None] / H)
    face_rgb = FACE[None, None, :] * fsh[:, :, None]
    edge_sh = np.clip(1.0 - dface / 3.0, 0, 1)[:, :, None] * 0.06
    face_rgb = face_rgb * (1 - edge_sh)
    fm = (face > 0)[:, :, None]
    rgb = np.where(fm, face_rgb, rgb)

    rgb = grain(rgb, 1.0, seed=11)
    alpha = cv2.GaussianBlur(outer.copy(), (3, 3), 0.5)
    out = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), alpha])
    save(out, BASE + r'\components\pill-cream_v02.png', 'pill-cream_v02')
    print(f'  上安全边(0..9)非透明={int((alpha[:10]>0).sum())} 下(143..159)={int((alpha[143:]>0).sum())} (须0)')


# ============================================================ A24 锁
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


def despill_rim(rgb, alpha, rim=6):
    solid = (alpha > 0).astype(np.uint8)
    dist_in = cv2.distanceTransform(solid, cv2.DIST_L2, 5)
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
    rm = (alpha > 0) & (~core.astype(bool))
    out = rgb.copy()
    out[rm] = rgb[ny[rm], nx[rm]]
    return out


def build_lock():
    print('=== A24 icon-lock_v02 ===')
    im = cv2.imread(LOCK_SRC)
    rgb, alpha = chroma_key(im)
    n, lab, stats, _ = cv2.connectedComponentsWithStats((alpha > 40).astype(np.uint8), 8)
    if n > 1:
        small = [i for i in range(1, n) if stats[i, 4] < 40]
        if small:
            alpha[np.isin(lab, small)] = 0

    band = (alpha > 0) & (alpha < 250)
    alpha = np.where(band, np.where(alpha > 128, 255, 0), alpha).astype(np.uint8)
    rgb = despill_rim(rgb, alpha, rim=6)

    sm = cv2.bilateralFilter(rgb, 9, 42, 9)
    sm = cv2.bilateralFilter(sm, 9, 42, 9)
    rgb = cv2.addWeighted(rgb, 0.15, sm, 0.85, 0)
    gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
    rgb = cv2.addWeighted(rgb, 0.78, cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), 0.22, 0)
    rgb = despill_rim(rgb, alpha, rim=4)

    solid = (alpha > 60).astype(np.uint8)
    free = (1 - solid).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(free, 4)
    border = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    for i in [i for i in range(1, n) if i not in border and stats[i, 4] > 30]:
        alpha[lab == i] = 0
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.4)

    ys, xs = np.nonzero(alpha > 60)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    s = 205.0 / max(bw, bh)
    nw, nh = max(1, round(bw * s)), max(1, round(bh * s))
    ra = cv2.resize(alpha[y0:y1 + 1, x0:x1 + 1], (nw, nh), interpolation=cv2.INTER_AREA)
    rc = cv2.resize(rgb[y0:y1 + 1, x0:x1 + 1], (nw, nh), interpolation=cv2.INTER_CUBIC)
    canvas = np.zeros((256, 256, 4), np.uint8)
    ox, oy = 128 - nw // 2, 128 - nh // 2
    canvas[oy:oy + nh, ox:ox + nw, :3] = rc
    canvas[oy:oy + nh, ox:ox + nw, 3] = ra
    save(canvas, BASE + r'\icons\icon-lock_v02.png', 'icon-lock_v02')

    ys2, xs2 = np.nonzero(canvas[:, :, 3] > 60)
    b, g, r = [canvas[:, :, i].astype(int) for i in range(3)]
    mag = int(((r - g > 40) & (b - g > 20) & (canvas[:, :, 3] > 60)).sum())
    print(f'  边距 左={xs2.min()} 右={255-xs2.max()} 上={ys2.min()} 下={255-ys2.max()} (>=20)')
    print(f'  洋红像素={mag}')


if __name__ == '__main__':
    build_frame()
    build_pill()
    build_lock()
    print('done')
