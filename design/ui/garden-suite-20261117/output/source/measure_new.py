"""测量新生成素材的 alpha 几何：外框 bbox / 内孔 bbox / 胶囊主体 / 锁主体"""
import cv2, numpy as np

M = r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media'
SRC = {
    'frame':  M + r'\miora_text_to_image-1794910185454-0-1262bf84196a.png',
    'pill':   M + r'\miora_text_to_image-1794910409239-0-702abad431c3.png',
    'lock':   M + r'\miora_text_to_image-1794910218679-0-92923ee47720.png',
    'mascot': M + r'\miora_text_to_image-1794910238801-0-71d5802db411.png',
}


def chroma_alpha(im, k=10):
    """自适应色键：四角背景中值 -> 主体分数"""
    b, g, r = im[:, :, 0].astype(np.float32), im[:, :, 1].astype(np.float32), im[:, :, 2].astype(np.float32)
    subj = np.maximum(g / (r + 1), g / (b + 1))
    corners = np.concatenate([
        subj[:k, :k].ravel(), subj[:k, -k:].ravel(),
        subj[-k:, :k].ravel(), subj[-k:, -k:].ravel()])
    lo = float(np.median(corners)) + 0.10
    hi = lo + 0.18
    alpha = np.clip((subj - lo) / (hi - lo), 0, 1)
    return (alpha * 255).astype(np.uint8), lo, hi


def largest_component(alpha, thr=40):
    n, lab, stats, _ = cv2.connectedComponentsWithStats((alpha > thr).astype(np.uint8), 8)
    if n <= 1:
        return alpha
    keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    out = alpha.copy()
    out[lab != keep] = 0
    return out


def inner_holes(alpha, thr=40):
    """返回被主体包围的透明区域（内孔）列表"""
    free = (alpha <= thr).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(free, 4)
    h, w = alpha.shape
    border_labels = set(np.unique(np.concatenate([
        lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    holes = []
    for i in range(1, n):
        if i in border_labels:
            continue
        ys, xs = np.nonzero(lab == i)
        holes.append((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()), int(len(xs))))
    return holes


for key, path in SRC.items():
    im = cv2.imread(path).astype(np.float32)
    h, w = im.shape[:2]
    alpha, lo, hi = chroma_alpha(im)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0.5)
    alpha = largest_component(alpha)
    ys, xs = np.nonzero(alpha > 40)
    ox0, oy0, ox1, oy1 = xs.min(), ys.min(), xs.max(), ys.max()
    print(f'=== {key} canvas {w}x{h}  key lo={lo:.2f} hi={hi:.2f}')
    print(f'    outer bbox=({ox0},{oy0})-({ox1},{oy1})  size={ox1-ox0+1}x{oy1-oy0+1}')
    for hx0, hy0, hx1, hy1, area in sorted(inner_holes(alpha), key=lambda t: -t[4])[:4]:
        print(f'    hole bbox=({hx0},{hy0})-({hx1},{hy1}) size={hx1-hx0+1}x{hy1-hy0+1} area={area}'
              f'  outer-margin L={hx0-ox0} R={ox1-hx1} T={hy0-oy0} B={oy1-hy1}')

    # 孔边直线性：沿中线扫描 alpha 边界
    cy = (oy0 + oy1) // 2
    row = alpha[cy] > 40
    edges = np.diff(row.astype(np.int8))
    starts = np.nonzero(edges == 1)[0] + 1
    ends = np.nonzero(edges == -1)[0]
    if len(starts):
        print(f'    row y={cy} opaque runs start={starts.tolist()} end={ends.tolist()}')
    cx = (ox0 + ox1) // 2
    col = alpha[:, cx] > 40
    edges = np.diff(col.astype(np.int8))
    starts = np.nonzero(edges == 1)[0] + 1
    ends = np.nonzero(edges == -1)[0]
    if len(starts):
        print(f'    col x={cx} opaque runs start={starts.tolist()} end={ends.tolist()}')

    # 锁/图标：金色像素（用于判断金线层数）
    b, g, r = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    gold = (alpha > 200) & (r > 170) & (b < 170) & (g < r * 0.95)
    if gold.sum() > 50:
        ys2, xs2 = np.nonzero(gold)
        print(f'    gold px={int(gold.sum())} bbox=({xs2.min()},{ys2.min()})-({xs2.max()},{ys2.max()})')
