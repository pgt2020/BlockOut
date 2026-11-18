import cv2, numpy as np, os
B = r'E:/UnityProject/MutiplayGame/BlockOut/design/ui/garden-suite-20261117/output'
R = B + r'\review'
p = B + r'\optional\mascot_v02.png'
im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
rgb = im[:, :, :3].astype(np.uint8); a = im[:, :, 3]

def despill_rim(rgb, alpha, rim=6):
    solid = (alpha > 0).astype(np.uint8)
    d = cv2.distanceTransform(solid, cv2.DIST_L2, 5)
    core = (d > rim + 1.5).astype(np.uint8)
    d2, labels = cv2.distanceTransformWithLabels(1 - core, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.nonzero(core); coord = np.stack([xs, ys], 1)
    idx = labels - 1; ok = (idx >= 0) & (idx < len(coord)); safe = np.clip(idx, 0, len(coord)-1)
    h, w = alpha.shape; gy, gx = np.mgrid[0:h, 0:w]
    nx = np.where(ok, coord[safe,0], gx); ny = np.where(ok, coord[safe,1], gy)
    m = (alpha > 0) & (~core.astype(bool)); out = rgb.copy()
    out[m] = rgb[ny[m], nx[m]]; return out

b0, g0, r0 = [rgb[:,:,i].astype(int) for i in range(3)]
mag0 = int(((r0-g0>50) & (b0-g0>30) & (a>0)).sum())
rgb = despill_rim(rgb, a, rim=7)
b, g, r = [rgb[:,:,i].astype(int) for i in range(3)]
mag1 = int(((r-g>50) & (b-g>30) & (a>0)).sum())
im[:, :, :3] = rgb
cv2.imwrite(p, im)
print(f'mascot 洋红像素 {mag0} -> {mag1}')

def previews(rgba, name):
    al = rgba[:, :, 3].astype(np.float32)/255; h, w = al.shape
    yy, xx = np.mgrid[0:h, 0:w]; chk = (((xx//24 + yy//24) % 2)*28+120).astype(np.uint8)
    for bn, bg in {'white': np.full((h,w,3),255,np.float32),
                   'darkgray': np.full((h,w,3),55,np.float32),
                   'lightblue': np.dstack([np.full((h,w),245,np.float32),np.full((h,w),228,np.float32),np.full((h,w),205,np.float32)]),
                   'checker': np.dstack([chk]*3).astype(np.float32)}.items():
        cv2.imwrite(os.path.join(R, f'{name}_{bn}.png'),
                    (rgba[:,:,:3].astype(np.float32)*al[...,None]+bg*(1-al[...,None])).astype(np.uint8))
previews(im, 'mascot_v02')
print('ok')
