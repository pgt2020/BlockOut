import cv2, numpy as np
p = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output\components\panel-cream_v02.png'
im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
print('shape', im.shape)
a = im[:, :, 3]
ys, xs = np.nonzero(a > 40)
print('alpha bbox', xs.min(), ys.min(), xs.max(), ys.max())
# 每行 alpha 边界，看轮廓形状
for y in [0, 5, 20, 40, 80, 120, 384, 650, 700, 740, 760, 767]:
    row = np.nonzero(a[y] > 40)[0]
    print('row', y, 'x', row.min() if len(row) else None, row.max() if len(row) else None, 'n', len(row))
for x in [0, 5, 20, 40, 80, 120, 384, 650, 700, 740, 760, 767]:
    col = np.nonzero(a[:, x] > 40)[0]
    print('col', x, 'y', col.min() if len(col) else None, col.max() if len(col) else None, 'n', len(col))
# 采样颜色
def px(x, y): return im[y, x][:3].tolist()
print('外边条色 (x=30,y=384):', px(30, 384))
print('外边条色 (x=384,y=30):', px(384, 30))
print('内面色 (x=384,y=384):', px(384, 384))
print('内面边 (x=110,y=384):', px(110, 384))
print('外缘 (x=12,y=384):', px(12, 384))
print('金线扫描 row384:')
prev = None
for x in range(60, 140):
    c = px(x, 384)
    tag = ''
    if c[2] > 150 and c[2] - c[0] > 40: tag = 'GOLD'
    if tag: print('  x=', x, c, tag)
