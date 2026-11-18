import cv2, numpy as np
B = r'E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output'

# 1) 锁：清掉 alpha<22 的极淡灰雾，再轻微柔化，保留轮廓
p = B + r'\icons\icon-lock_v02.png'
im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
a = im[:, :, 3].copy()
before = int(((a > 0) & (a < 22)).sum())
a[a < 22] = 0
a = cv2.GaussianBlur(a, (3, 3), 0.35)
im[:, :, 3] = a
cv2.imwrite(p, im)
print(f'锁: 清除极淡灰雾 {before} px -> 剩余半透明(0<a<40)={int(((a>0)&(a<40)).sum())}')

# 2) 真实金线位置（r-b>60 才算金）
for name, path, row, xr in [('frame', B + r'\components\frame-art_v02.png', 384, range(26, 96)),
                            ('pill',  B + r'\components\pill-cream_v02.png', 76,  range(12, 60))]:
    im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    px = im[row, :, :3].astype(int)
    xs = [x for x in xr if px[x][2] - px[x][0] > 60 and im[row, x, 3] > 200]
    if xs:
        print(f'{name} 金线 x={min(xs)}..{max(xs)} 宽={max(xs)-min(xs)+1}px 色BGR={tuple(px[(min(xs)+max(xs))//2])}')
    else:
        print(f'{name} 未检出金线')

# 3) 锁梁开口内部
im = cv2.imread(B + r'\icons\icon-lock_v02.png', cv2.IMREAD_UNCHANGED)
a = im[:, :, 3]
print('锁梁开口(112..148,58..88) alpha>40 =', int((a[58:89, 112:149] > 40).sum()))
ys, xs = np.nonzero(a > 40)
print(f'锁 bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) 边距 左{xs.min()} 右{255-xs.max()} 上{ys.min()} 下{255-ys.max()}')
