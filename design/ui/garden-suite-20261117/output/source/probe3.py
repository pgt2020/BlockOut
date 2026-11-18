import cv2, numpy as np

# ---------- panel-cream_v02 结构 ----------
p = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output\components\panel-cream_v02.png'
im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
h, w = im.shape[:2]
a = im[:, :, 3]
print('panel shape', im.shape)
ys, xs = np.nonzero(a > 40)
print('panel alpha bbox x', xs.min(), xs.max(), 'y', ys.min(), ys.max())

def bgr(x, y):
    return tuple(int(v) for v in im[y, x][:3])

# 沿 row=middle 扫描左右两侧
my = (ys.min() + ys.max()) // 2
print('--- row', my, 'scan x 40..130 ---')
for x in range(40, 131, 4):
    print('  x=%3d' % x, bgr(x, my), 'a=%d' % a[my, x])
print('--- col 384 scan y 40..130 ---')
for y in range(40, 131, 6):
    print('  y=%3d' % y, bgr(384, y), 'a=%d' % a[384, y])
print('panel center', bgr(w // 2, h // 2))

# ---------- pill 边缘洋红检测 ----------
p2 = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output\components\pill-cream_v02.png'
im2 = cv2.imread(p2, cv2.IMREAD_UNCHANGED)
a2 = im2[:, :, 3]
solid = (a2 > 250).astype(np.uint8)
band = ((a2 > 0) & (a2 < 250)).astype(np.uint8)
b, g, r = [im2[:, :, i].astype(int) for i in range(3)]
mag = (r - g > 45) & (b - g > 25) & (a2 > 10)
print('pill band px', int(band.sum()), 'magenta-ish px', int(mag.sum()))
ys2, xs2 = np.nonzero(mag)
if len(ys2):
    print('  magenta bbox', xs2.min(), ys2.min(), xs2.max(), ys2.max())
    print('  sample', [tuple(int(v) for v in im2[ys2[i], xs2[i]][:3]) for i in range(0, len(ys2), max(1, len(ys2)//6))])

# ---------- lock 采样 ----------
p3 = r'E:\UnityProject\MutiplayGame\BlockOut\design\ui\garden-suite-20261117\output\icons\icon-lock_v02.png'
im3 = cv2.imread(p3, cv2.IMREAD_UNCHANGED)
a3 = im3[:, :, 3]
ys3, xs3 = np.nonzero(a3 > 60)
print('lock bbox', xs3.min(), ys3.min(), xs3.max(), ys3.max())
print('lock shackle top (128,35)', tuple(int(v) for v in im3[35, 128][:3]))
print('lock shackle left (70,70)', tuple(int(v) for v in im3[70, 70][:3]))
print('lock body (128,160)', tuple(int(v) for v in im3[160, 128][:3]))
print('lock body (90,200)', tuple(int(v) for v in im3[200, 90][:3]))
print('lock keyhole (120,195)', tuple(int(v) for v in im3[195, 120][:3]))
# 噪点强度
body = im3[130:220, 70:190]
m = (a3[130:220, 70:190] > 250)
vals = body[:, :, 1][m]
print('lock body G std', round(float(vals.std()), 2), 'mean', round(float(vals.mean()), 1))
