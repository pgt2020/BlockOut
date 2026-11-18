import cv2, numpy as np

B = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output'
def load(p): return cv2.imread(p, cv2.IMREAD_UNCHANGED)

print('===== A11 frame-art_v02.png =====')
im = load(B + r'\components\frame-art_v02.png')
a = im[:, :, 3]; h, w = a.shape
ys, xs = np.nonzero(a > 40)
print(f'画布 {w}x{h}  alpha bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) 主体={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}')
print(f'内孔96..672 非透明像素={int((a[96:673,96:673]>0).sum())}')
print(f'内孔96..672 alpha>40 像素={int((a[96:673,96:673]>40).sum())}')
# 对称性：左右/上下边厚度
print(f'左边厚(384行)={int(np.nonzero(a[384,:384]>40)[0].max())-23+1}  右边厚={745-int(np.nonzero(a[384,384:]>40)[0].min())-384+1}')
print(f'上边厚(384列)={int(np.nonzero(a[:384,384]>40)[0].max())-23+1}')
# 金线位置
row = im[384, :, :3].astype(int)
best = None
for x in range(30, 96):
    b_, g_, r_ = row[x]
    if r_ - b_ > 30:
        best = x if best is None else best
print(f'金线起始x={best} (距外缘 {best-24}px)' if best else '金线未检出')
# 内孔边缘是否水平/垂直
top = [np.nonzero(a[:, x] > 40)[0][0] for x in range(150, 620, 60)]
print('外轮廓上沿 y（150..620）:', top)
print()

print('===== A13 pill-cream_v02.png =====')
im = load(B + r'\components\pill-cream_v02.png')
a = im[:, :, 3]; h, w = a.shape
ys, xs = np.nonzero(a > 40)
print(f'画布 {w}x{h}  alpha bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) 主体={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}')
for n in range(0, 12):
    if (a[n] > 0).sum() == 0: continue
    print(f'  顶部第 {n} 行非透明像素={int((a[n]>0).sum())} → 完全透明边仅 {n}px'); break
for n in range(0, 20):
    if (a[h-1-n] > 0).sum() == 0: continue
    print(f'  底部最后 {n} 行完全透明 → {n}px'); break
c = im[60:92, 150:360, :3].astype(float)
print(f'中心平整度: 亮度std={c.mean(axis=2).std():.2f} 均值={c.mean():.1f}（<3 视为平整）')
print(f'端头圆度: 左端最外侧x={xs.min()} 该列y范围={np.nonzero(a[:, xs.min()+2]>40)[0].min()}..{np.nonzero(a[:, xs.min()+2]>40)[0].max()}')
print()

print('===== A24 icon-lock_v02.png =====')
im = load(B + r'\icons\icon-lock_v02.png')
a = im[:, :, 3]; h, w = a.shape
ys, xs = np.nonzero(a > 40)
print(f'画布 {w}x{h}  alpha bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) 主体={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}')
print(f'透明边距: 左={xs.min()} 右={w-1-xs.max()} 上={ys.min()} 下={h-1-ys.max()}')
inner = a[60:90, 110:150]
print(f'锁梁开口内(110..150,60..90) alpha>40 像素={int((inner>40).sum())}')
print(f'主体内半透明像素(0<a<40)={int(((a>0)&(a<40)).sum())}')
print()

print('===== A26 mascot_v02.png（可选）=====')
import os
p = B + r'\optional\mascot_v02.png'
if os.path.exists(p):
    im = load(p); a = im[:, :, 3]; h, w = a.shape
    ys, xs = np.nonzero(a > 40)
    print(f'画布 {w}x{h}  alpha bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) 主体={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}')
    dk = ((im[:, :, 2] < 110) & (a > 200)).sum()
    print(f'深咖不透明像素={int(dk)}')
