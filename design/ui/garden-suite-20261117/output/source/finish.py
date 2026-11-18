import cv2, numpy as np, os
B = r'E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output'
R = B + r'\review'

def previews(rgba, name):
    a = rgba[:, :, 3].astype(np.float32) / 255
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    chk = (((xx // 24 + yy // 24) % 2) * 28 + 120).astype(np.uint8)
    for bn, bg in {
        'checker': np.dstack([chk]*3).astype(np.float32),
        'white': np.full((h, w, 3), 255, np.float32),
        'darkgray': np.full((h, w, 3), 55, np.float32),
        'lightblue': np.dstack([np.full((h,w),245,np.float32), np.full((h,w),228,np.float32), np.full((h,w),205,np.float32)]),
    }.items():
        comp = (rgba[:, :, :3].astype(np.float32)*a[...,None] + bg*(1-a[...,None])).astype(np.uint8)
        cv2.imwrite(os.path.join(R, f'{name}_{bn}.png'), comp)

p = B + r'\icons\icon-lock_v02.png'
im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
a = im[:, :, 3].copy()
a[a < 12] = 0
im[:, :, 3] = a
cv2.imwrite(p, im)

# 检查边缘半透明像素的颜色是否干净（不应是灰/洋红）
b, g, r = [im[:, :, i].astype(int) for i in range(3)]
band = (a > 0) & (a < 200)
n = int(band.sum())
print(f'锁 边缘半透明像素={n}  平均BGR=({b[band].mean():.0f},{g[band].mean():.0f},{r[band].mean():.0f})')
mag = int(((r-g > 40) & (b-g > 20) & band).sum())
gray = int((band & (np.abs(r-b) < 12) & (r < 180)).sum())
print(f'  洋红偏色={mag}  偏灰={gray} (应为个位数)')
previews(im, 'icon-lock_v02')
ys, xs = np.nonzero(a > 40)
print(f'  最终 bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) 主体={xs.max()-xs.min()+1}x{ys.max()-ys.min()+1}')

# 三张一起再刷一次预览，确保与磁盘一致
for name, path in [('frame-art_v02', B + r'\components\frame-art_v02.png'),
                   ('pill-cream_v02', B + r'\components\pill-cream_v02.png')]:
    previews(cv2.imread(path, cv2.IMREAD_UNCHANGED), name)
print('previews refreshed')
