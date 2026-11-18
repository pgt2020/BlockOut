"""
v02 修订处理：frame-art_v02 / pill-cream_v02 / icon-lock_v02 / mascot_v02
严格按《全套素材审查与最后修订.md》执行：
  frame  -> 严格正视对称方框，外框 24..744，内孔 96..672 全透明，单条细金线
  pill   -> 512x160，主体 12..500 x 10..142，上下各留透明安全边，平坦暖白中心
  lock   -> 256x256，主体最长边 ~205，透明边距 >=20，清残渣/杂点，不伤轮廓
  mascot -> 可选，512x640 正面视角，眼嘴不透明
"""
import cv2, numpy as np, shutil, os

M = r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media'
BASE = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output'
REVIEW = BASE + r'\review'
SRC = {
    'frame':  M + r'\miora_text_to_image-1794910185454-0-1262bf84196a.png',
    'pill':   M + r'\miora_text_to_image-1794910409239-0-702abad431c3.png',
    'lock':   M + r'\miora_text_to_image-1794910218679-0-92923ee47720.png',
    'mascot': M + r'\miora_text_to_image-1794910238801-0-71d5802db411.png',
}


# ---------------------------------------------------------------- 基础工具
def chroma_key(im):
    """自适应色键 -> (rgb去底, alpha)"""
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


def gold_mask(rgb):
    b, g, r = rgb[:, :, 0].astype(int), rgb[:, :, 1].astype(int), rgb[:, :, 2].astype(int)
    return (r > 150) & (r - b > 45) & (g > 95) & (g < r * 0.98)


def fill_nearest(rgb, mask, exclude=None):
    """把 mask 区域用最近的非 mask 像素颜色填充（等距最近邻）"""
    h, w = mask.shape
    valid = (~mask).astype(np.uint8)
    if exclude is not None:
        valid[exclude] = 0
    if valid.sum() == 0:
        return rgb
    dist, labels = cv2.distanceTransformWithLabels(1 - valid, cv2.DIST_L2, 5,
                                                    labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(valid)
    coord = np.stack([xs, ys], 1)
    idx = labels - 1
    safe = np.clip(idx, 0, len(coord) - 1)
    ok = (idx >= 0) & (idx < len(coord))
    gy, gx = np.mgrid[0:h, 0:w]
    nx = np.where(ok, coord[safe, 0], gx)
    ny = np.where(ok, coord[safe, 1], gy)
    out = rgb.copy()
    out[mask] = rgb[ny[mask], nx[mask]]
    return out


def despeckle(rgb, alpha, min_area=40):
    """移除孤立小碎块；填充主体内的小空洞"""
    solid = (alpha > 40).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(solid, 8)
    if n > 1:
        biggest = 1 + int(np.argmax(stats[1:, 4]))
        small = [i for i in range(1, n) if stats[i, 4] < min_area]
        if small:
            kill = np.isin(lab, small)
            alpha = alpha.copy()
            alpha[kill] = 0
    return rgb, alpha


def despill_edge(rgb, alpha):
    """半透明边缘颜色替换为最近实心主体色（清除洋红/灰毛边）"""
    solid = (alpha >= 250).astype(np.uint8)
    if solid.sum() == 0:
        return rgb
    dist, labels = cv2.distanceTransformWithLabels(1 - solid, cv2.DIST_L2, 5,
                                                    labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(solid)
    coord = np.stack([xs, ys], 1)
    idx = labels - 1
    safe = np.clip(idx, 0, len(coord) - 1)
    ok = (idx >= 0) & (idx < len(coord))
    h, w = alpha.shape
    gy, gx = np.mgrid[0:h, 0:w]
    nx = np.where(ok, coord[safe, 0], gx)
    ny = np.where(ok, coord[safe, 1], gy)
    band = (alpha > 0) & (alpha < 250)
    out = rgb.copy()
    out[band] = rgb[ny[band], nx[band]]
    return out


def nearest_solid_color(rgb, alpha):
    solid = (alpha >= 250).astype(np.uint8)
    ys, xs = np.nonzero(solid)
    return np.median(rgb[solid.astype(bool)], axis=0)


def previews(rgba, name, size):
    a = rgba[:, :, 3].astype(np.float32) / 255
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    chk = (((xx // 24 + yy // 24) % 2) * 28 + 120).astype(np.uint8)
    bgs = {
        'checker': np.dstack([chk] * 3).astype(np.float32),
        'white': np.full((h, w, 3), 255, np.float32),
        'darkgray': np.full((h, w, 3), 55, np.float32),
        'lightblue': np.dstack([np.full((h, w), 205, np.float32),
                                np.full((h, w), 228, np.float32),
                                np.full((h, w), 245, np.float32)]),
    }
    for bn, bg in bgs.items():
        comp = (rgba[:, :, :3].astype(np.float32) * a[..., None] + bg * (1 - a[..., None])).astype(np.uint8)
        cv2.imwrite(os.path.join(REVIEW, f'{name}_{bn}.png'), comp)


def save(rgba, path, name):
    cv2.imwrite(path, rgba)
    previews(rgba, name, None)
    a = rgba[:, :, 3]
    ys, xs = np.nonzero(a > 40)
    print(f'  -> {os.path.basename(path)}  {rgba.shape[1]}x{rgba.shape[0]}  '
          f'bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) '
          f'body={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}')
    return rgba


def piece_map(dst_lo, dst_mid1, dst_mid2, dst_hi, src_lo, src_m1, src_m2, src_hi, n):
    """构造 dst->src 分段线性映射"""
    m = np.zeros(n, np.float32)
    def seg(d0, d1, s0, s1):
        d = np.arange(d0, d1)
        m[d] = s0 + (d - d0) * (s1 - s0) / (d1 - d0)
    seg(0, dst_lo, 0, src_lo)
    seg(dst_lo, dst_mid1, src_lo, src_m1)
    seg(dst_mid1, dst_mid2, src_m1, src_m2)
    seg(dst_mid2, dst_hi, src_m2, src_hi)
    seg(dst_hi, n, src_hi, n)
    return m


# ================================================================ A11 画框
def build_frame():
    print('=== A11 frame-art_v02 ===')
    im = cv2.imread(SRC['frame'])
    rgb, alpha = chroma_key(im)
    rgb, alpha = despeckle(rgb, alpha, 60)

    # 1) 去掉 AI 生成的多余金线，换成后面统一绘制的单条细金线
    gm = gold_mask(rgb) & (alpha > 30)
    rgb = fill_nearest(rgb, gm)
    print(f'  源金线像素={int(gm.sum())} -> 已移除，待统一重绘')

    # 2) 分段线性 warp：源外框 94..673 / 孔 169..598,169..596 -> 目标外框 24..744 / 孔 96..672
    mx = piece_map(24, 96, 672, 744, 94, 169, 598, 673, 768)
    my = piece_map(24, 96, 672, 744, 93, 169, 596, 673, 768)
    MX, MY = np.meshgrid(mx, my)
    w_rgb = cv2.remap(rgb, MX, MY, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    w_a = cv2.remap(alpha, MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # 3) 强制内孔 = 正方形 96..672 全透明（含四角），外框保留源圆角
    out = np.zeros((768, 768, 4), np.uint8)
    xs = np.arange(768)
    hole_mask = ((xs[None, :] >= 96) & (xs[None, :] <= 672)).astype(np.uint8) * \
                ((xs[:, None] >= 96) & (xs[:, None] <= 672)).astype(np.uint8)
    a = w_a.copy()
    a[hole_mask > 0] = 0

    # 4) 内缘柔和阴影（孔外 0..4px）
    #    注意：distanceTransform 以 0 像素为"背景"，故用 1-hole_mask 才能量出
    #    框体像素到孔边缘的距离（用 hole_mask 时框体侧恒为 0）
    dist_out = cv2.distanceTransform((1 - hole_mask).astype(np.uint8), cv2.DIST_L2, 5)
    shadow = (dist_out > 0) & (dist_out <= 4) & (a > 0)
    out_rgb = w_rgb.astype(np.float32)
    out_rgb[shadow] *= 0.90

    # 5) 单条细金线（距孔边缘 16..22px 的等距环）
    gold_band = (dist_out >= 16) & (dist_out <= 22) & (a > 0)
    gcol = np.array([96, 205, 244], np.float32)   # BGR，暖金
    # 顶边稍亮、底边稍暗，模拟左上光
    yy = np.arange(768, dtype=np.float32)
    shade = 1.06 - 0.16 * (yy / 768.0)
    gold_rgb = gcol[None, :] * shade[:, None]          # (768,3)
    gold3 = np.repeat(gold_rgb[:, None, :], 768, axis=1)   # (768,768,3)
    out_rgb[gold_band] = gold3[gold_band]
    print(f'  金线像素={int(gold_band.sum())}')

    out[:, :, :3] = np.clip(out_rgb, 0, 255).astype(np.uint8)
    out[:, :, 3] = a
    save(out, BASE + r'\components\frame-art_v02.png', 'frame-art_v02')
    shutil.copy(SRC['frame'], BASE + r'\source\frame-art_v02-source.png')

    # 报告
    ys, xs2 = np.nonzero(out[:, :, 3] > 40)
    print(f'  外框 bbox=({xs2.min()},{ys.min()})-({xs2.max()},{ys.max()})')
    print(f'  内孔 96..672 全透明? {int((out[96:673,96:673,3] > 0).sum())} 个非透明像素（应为0）')


# ================================================================ A13 胶囊
def build_pill():
    print('=== A13 pill-cream_v02 ===')
    im = cv2.imread(SRC['pill'])
    rgb, alpha = chroma_key(im)
    rgb, alpha = despeckle(rgb, alpha, 60)
    gm = gold_mask(rgb) & (alpha > 30)
    rgb = fill_nearest(rgb, gm)
    print(f'  源金线像素={int(gm.sum())} -> 已移除，待统一重绘')

    # 源胶囊: x176..592, y53..201, 中心 y127, r74.5, 直段 250.5..517.5
    # 目标胶囊: x12..500, y10..142, 中心 y76, r66, 直段 78..434
    sc = 74.5 / 66.0
    mid_scale = (517.5 - 250.5) / (434.0 - 78.0)
    X, Y = np.meshgrid(np.arange(512, dtype=np.float32), np.arange(160, dtype=np.float32))
    sx = np.empty_like(X); sy = np.empty_like(Y)
    a_t, b_t, c_t = 78.0, 434.0, 76.0
    a_s, b_s, c_s = 250.5, 517.5, 127.0
    left = X < a_t
    right = X > b_t
    mid = ~(left | right)
    sx[mid] = a_s + (X[mid] - a_t) * mid_scale
    sy[mid] = c_s + (Y[mid] - c_t) * sc
    sx[left] = a_s + (X[left] - a_t) * sc
    sy[left] = c_s + (Y[left] - c_t) * sc
    sx[right] = b_s + (X[right] - b_t) * sc
    sy[right] = c_s + (Y[right] - c_t) * sc
    w_rgb = cv2.remap(rgb, sx, sy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    w_a = cv2.remap(alpha, sx, sy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # 目标胶囊 alpha（真圆端，主体 x12..500 / y10..142）
    mask = np.zeros((160, 512), np.uint8)
    cv2.rectangle(mask, (int(a_t), int(c_t - 66)), (int(b_t), int(c_t + 66)), 255, -1)
    cv2.ellipse(mask, (int(a_t), int(c_t)), (66, 66), 0, 90, 270, 255, -1)
    cv2.ellipse(mask, (int(b_t), int(c_t)), (66, 66), 0, -90, 90, 255, -1)
    alpha = cv2.GaussianBlur(mask, (3, 3), 0.4)

    out_rgb = w_rgb.astype(np.float32)
    # 内缘柔和阴影
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    inner = (dist > 0) & (dist <= 3) & (alpha > 0)
    out_rgb[inner] *= 0.92
    # 单条细金线：距胶囊边缘 19..25px
    gold_band = (dist >= 19) & (dist <= 25) & (alpha > 0)
    gcol = np.array([96, 205, 244], np.float32)
    yy = np.arange(160, dtype=np.float32)
    shade = 1.06 - 0.16 * (yy / 160.0)
    gold_rgb = gcol[None, :] * shade[:, None]          # (160,3)
    gold3 = np.repeat(gold_rgb[:, None, :], 512, axis=1)   # (160,512,3)
    out_rgb[gold_band] = gold3[gold_band]

    out = np.dstack([np.clip(out_rgb, 0, 255).astype(np.uint8), alpha])
    save(out, BASE + r'\components\pill-cream_v02.png', 'pill-cream_v02')
    shutil.copy(SRC['pill'], BASE + r'\source\pill-cream_v02-source.png')
    print(f'  上下透明安全边: 上={int((alpha[:10] > 10).sum())} 下={int((alpha[150:] > 10).sum())} (应全0)')


# ================================================================ A24 锁
def build_lock():
    print('=== A24 icon-lock_v02 ===')
    im = cv2.imread(SRC['lock'])
    rgb, alpha = chroma_key(im)
    rgb, alpha = despeckle(rgb, alpha, 40)
    print(f'  去碎块后连通域面积: {int((alpha>40).sum())}')

    # 清除与主体相连的半透明灰/洋红毛边：收紧 alpha 阈值 + 边缘色换成实心色
    band = (alpha > 0) & (alpha < 250)
    alpha = np.where(band, np.where(alpha > 120, 255, 0), alpha).astype(np.uint8)
    rgb = despill_edge(rgb, alpha)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.4)

    # 锁梁开口内部保持透明：清掉孔内任何不透明杂点
    solid = alpha > 60
    free = (~solid).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(free, 4)
    h, w = solid.shape
    border = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    holes = [i for i in range(1, n) if i not in border and stats[i, 4] > 30]
    for i in holes:
        comp = (lab == i)
        alpha[comp] = 0
        ys, xs = np.nonzero(comp)
        print(f'  锁梁开口透明化: bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) area={stats[i,4]}')

    # 归一：主体最长边 ~205，居中，四周透明边距 >=20
    ys, xs = np.nonzero(alpha > 60)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    scale = 205.0 / max(bw, bh)
    nw, nh = max(1, round(bw * scale)), max(1, round(bh * scale))
    body = alpha[y0:y1 + 1, x0:x1 + 1]
    body_rgb = rgb[y0:y1 + 1, x0:x1 + 1]
    res_a = cv2.resize(body, (nw, nh), interpolation=cv2.INTER_AREA)
    res_rgb = cv2.resize(body_rgb, (nw, nh), interpolation=cv2.INTER_CUBIC)
    canvas = np.zeros((256, 256, 4), np.uint8)
    cx, cy = 128, 128
    ox, oy = cx - nw // 2, cy - nh // 2
    canvas[oy:oy + nh, ox:ox + nw, :3] = res_rgb
    canvas[oy:oy + nh, ox:ox + nw, 3] = res_a
    save(canvas, BASE + r'\icons\icon-lock_v02.png', 'icon-lock_v02')
    shutil.copy(SRC['lock'], BASE + r'\source\icon-lock_v02-source.png')
    ys2, xs2 = np.nonzero(canvas[:, :, 3] > 60)
    print(f'  透明边距: 左={xs2.min()} 右={255-xs2.max()} 上={ys2.min()} 下={255-ys2.max()} (需>=20)')


# ================================================================ A26 角色
def build_mascot():
    print('=== A26 mascot_v02 (可选) ===')
    im = cv2.imread(SRC['mascot'])
    rgb, alpha = chroma_key(im)
    rgb, alpha = despeckle(rgb, alpha, 60)
    alpha = np.where((alpha > 0) & (alpha < 250), np.where(alpha > 120, 255, 0), alpha).astype(np.uint8)
    rgb = despill_edge(rgb, alpha)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.4)
    ys, xs = np.nonzero(alpha > 60)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    # 目标：留白 >=36px
    margin = 36
    scale = min((512 - 2 * margin) / bw, (640 - 2 * margin) / bh)
    nw, nh = max(1, round(bw * scale)), max(1, round(bh * scale))
    res_a = cv2.resize(alpha[y0:y1 + 1, x0:x1 + 1], (nw, nh), interpolation=cv2.INTER_AREA)
    res_rgb = cv2.resize(rgb[y0:y1 + 1, x0:x1 + 1], (nw, nh), interpolation=cv2.INTER_CUBIC)
    canvas = np.zeros((640, 512, 4), np.uint8)
    ox, oy = 256 - nw // 2, 320 - nh // 2
    canvas[oy:oy + nh, ox:ox + nw, :3] = res_rgb
    canvas[oy:oy + nh, ox:ox + nw, 3] = res_a
    save(canvas, BASE + r'\optional\mascot_v02.png', 'mascot_v02')
    shutil.copy(SRC['mascot'], BASE + r'\source\mascot_v02-source.png')


if __name__ == '__main__':
    build_frame()
    build_pill()
    build_lock()
    build_mascot()
    print('done')
