"""v02 素材分析：frame 孔边直线性、lock 噪点/杂点/饱和度、pill 层次与端部"""
import cv2, numpy as np

M = r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media'
frame = cv2.imread(M + r'\miora_text_to_image-1794910185454-0-1262bf84196a.png')
pill = cv2.imread(M + r'\miora_text_to_image-1794910409239-0-702abad431c3.png')
lock = cv2.imread(M + r'\miora_text_to_image-1794910218679-0-92923ee47720.png')
mascot = cv2.imread(M + r'\miora_text_to_image-1794910238801-0-71d5802db411.png')


def chroma_alpha(im):
    b, g, r = im[:, :, 0].astype(np.float32), im[:, :, 1].astype(np.float32), im[:, :, 2].astype(np.float32)
    subj = np.maximum(g / (r + 1), g / (b + 1))
    k = 10
    corners = np.concatenate([subj[:k, :k].ravel(), subj[:k, -k:].ravel(),
                              subj[-k:, :k].ravel(), subj[-k:, -k:].ravel()])
    lo = float(np.median(corners)) + 0.10
    hi = lo + 0.18
    a = np.clip((subj - lo) / (hi - lo), 0, 1) * 255
    a = cv2.GaussianBlur(a, (3, 3), 0.5)
    n, lab, stats, _ = cv2.connectedComponentsWithStats((a > 40).astype(np.uint8), 8)
    if n > 1:
        keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        a[lab != keep] = 0
    return a


def hole_of(alpha):
    free = (alpha <= 40).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(free, 4)
    h, w = alpha.shape
    border = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
    best = None
    for i in range(1, n):
        if i in border:
            continue
        if best is None or stats[i, 4] > stats[best, 4]:
            best = i
    ys, xs = np.nonzero(lab == best)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


print('===== FRAME 直线性 =====')
fa = chroma_alpha(frame)
hx0, hy0, hx1, hy1 = hole_of(fa)
print(f'  hole=({hx0},{hy0})-({hx1},{hy1})  outer-ish')
for y in [180, 220, 280, 340, 383, 430, 490, 550, 585]:
    idx = np.nonzero(fa[y] > 40)[0]
    if len(idx) == 0:
        continue
    brk = np.nonzero(np.diff(idx) > 1)[0]
    st = np.concatenate([[idx[0]], idx[brk + 1]]).tolist()
    en = np.concatenate([idx[brk], [idx[-1]]]).tolist()
    print(f'  y={y}: runs={list(zip(st, en))}')
for x in [180, 220, 280, 340, 384, 430, 490, 550, 585]:
    idx = np.nonzero(fa[:, x] > 40)[0]
    if len(idx) == 0:
        continue
    brk = np.nonzero(np.diff(idx) > 1)[0]
    st = np.concatenate([[idx[0]], idx[brk + 1]]).tolist()
    en = np.concatenate([idx[brk], [idx[-1]]]).tolist()
    print(f'  x={x}: runs={list(zip(st, en))}')

print()
print('===== LOCK 质量 =====')
la = chroma_alpha(lock)
lb, lg, lr = lock[:, :, 0].astype(int), lock[:, :, 1].astype(int), lock[:, :, 2].astype(int)
mag = (lr > 140) & (lb > 140) & (lg < 120)
solid = la > 40
print(f'  品红像素={int(mag.sum())} 其中被判为主体(毛边)={int((mag & solid).sum())}')
gray = cv2.cvtColor(lock, cv2.COLOR_BGR2GRAY).astype(np.float32)
noise = np.abs(gray - cv2.blur(gray, (5, 5)))
sat = np.maximum(lr, lb) - np.minimum(lr, lb)
body = solid & (lr > 130) & (lb > 90)
print(f'  锁身像素={int(body.sum())} 噪声 mean={noise[body].mean():.2f} p95={np.percentile(noise[body],95):.1f}')
print(f'  锁身饱和度 mean={sat[body].mean():.1f} p90={np.percentile(sat[body],90):.0f}')
free = (~solid).astype(np.uint8)
n, lab, stats, _ = cv2.connectedComponentsWithStats(free, 4)
h, w = free.shape
border = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
for i in range(1, n):
    if i in border or stats[i, 4] < 30:
        continue
    ys, xs = np.nonzero(lab == i)
    print(f'  内孔: bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) area={stats[i,4]} '
          f'孔内不透明杂点={int(solid[ys, xs].sum())}')
# 孤立的非主体小块（水印残留）
n2, lab2, st2, _ = cv2.connectedComponentsWithStats(solid.astype(np.uint8), 8)
print(f'  主体连通域数={n2-1}  最大={st2[1:,4].max() if n2>1 else 0}  其他域面积={sorted(st2[1:,4].tolist())[::-1][1:4]}')

print()
print('===== PILL 层次（x=384 垂直剖面）=====')
pa = chroma_alpha(pill)
for y in range(50, 210, 3):
    b, g, r = pill[y, 384]
    tag = ''
    if r > 165 and b < 165 and 90 < g < r * 0.96:
        tag = 'GOLD'
    print(f'  y={y:3d} BGR=({b:5.1f},{g:5.1f},{r:5.1f}) a={pa[y,384]:3.0f} {tag}')
print('  端部轮廓（逐行左右边界）:')
for y in range(53, 202, 4):
    idx = np.nonzero(pa[y] > 40)[0]
    if len(idx):
        print(f'   y={y:3d} left={idx.min():3d} right={idx.max():3d} w={idx.max()-idx.min()+1:3d}')

print()
print('===== MASCOT 眼睛/嘴不透明度 =====')
ma = chroma_alpha(mascot)
mb, mg, mr = mascot[:, :, 0].astype(int), mascot[:, :, 1].astype(int), mascot[:, :, 2].astype(int)
eye = (mr < 120) & (mb < 100) & (mg < 90) & (ma > 200)
ys, xs = np.nonzero(eye)
print(f'  深咖眼像素={int(eye.sum())} bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()})')
# 眼白高光
hi_ = (mr > 200) & (mg > 200) & (mb > 200) & (ma > 200)
print(f'  高光像素={int(hi_.sum())}')
green = (mg > 110) & (mr < 140) & (mb < 120) & (ma > 200)
ys3, xs3 = np.nonzero(green)
if len(ys3):
    print(f'  绿色箭头像素={int(green.sum())} bbox=({xs3.min()},{ys3.min()})-({xs3.max()},{ys3.max()})')
ys2, xs2 = np.nonzero(ma > 40)
print(f'  主体 bbox=({xs2.min()},{ys2.min()})-({xs2.max()},{ys2.max()})')
