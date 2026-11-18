"""精细几何/质量分析：frame 孔边直线性、lock 残留品红/噪点、pill 层次结构"""
import cv2, numpy as np

M = r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media'
frame = cv2.imread(M + r'\miora_text_to_image-1794910185454-0-1262bf84196a.png')
pill = cv2.imread(M + r'\miora_text_to_image-1794910409239-0-702abad431c3.png')
lock = cv2.imread(M + r'\miora_text_to_image-1794910218679-0-92923ee47720.png')
mascot = cv2.imread(M + r'\miora_text_to_image-1794910238801-0-71d5802db411.png')


def is_bg(pix):
    b, g, r = [int(v) for v in pix]
    return r > 140 and b > 140 and g < 120


def subject_mask(im):
    b, g, r = im[:, :, 0].astype(np.float32), im[:, :, 1].astype(np.float32), im[:, :, 2].astype(np.float32)
    return ~((r > 140) & (b > 140) & (g < 130))


print('===== FRAME 孔边直线性（逐行测左右边界、逐列测上下边界）=====')
m = subject_mask(frame)
for y in [200, 250, 300, 350, 383, 420, 470, 520, 560]:
    idx = np.nonzero(m[y])[0]
    runs = []
    if len(idx):
        brk = np.nonzero(np.diff(idx) > 1)[0]
        starts = np.concatenate([[idx[0]], idx[brk + 1]])
        ends = np.concatenate([idx[brk], [idx[-1]]])
        runs = list(zip(starts.tolist(), ends.tolist()))
    print(f'  y={y}: runs={runs}')
for x in [200, 250, 300, 350, 384, 420, 470, 520, 560]:
    idx = np.nonzero(m[:, x])[0]
    runs = []
    if len(idx):
        brk = np.nonzero(np.diff(idx) > 1)[0]
        starts = np.concatenate([[idx[0]], idx[brk + 1]])
        ends = np.concatenate([idx[brk], [idx[-1]]])
        runs = list(zip(starts.tolist(), ends.tolist()))
    print(f'  x={x}: runs={runs}')

print()
print('===== LOCK 质量 =====')
lb, lg, lr = lock[:, :, 0].astype(int), lock[:, :, 1].astype(int), lock[:, :, 2].astype(int)
mag = (lr > 140) & (lb > 140) & (lg < 120)
# 主体内的品红像素（毛边）
m2 = subject_mask(lock)
print(f'  品红像素总数={int(mag.sum())}  其中位于主体包围盒内(毛边)={int((mag & m2).sum())}')
# 噪点：主体内颜色方差高的像素
gray = cv2.cvtColor(lock, cv2.COLOR_BGR2GRAY).astype(np.float32)
local = cv2.blur(gray, (5, 5))
noise = np.abs(gray - local)
body = m2 & (lr > 140)  # 浅色锁身
print(f'  锁身区域像素={int(body.sum())}  局部噪声均值={noise[body].mean():.2f} p95={np.percentile(noise[body],95):.1f} max={noise[body].max():.0f}')
# 金属感：饱和度高且亮
sat = lr.max() - lr.min()
print(f'  锁身饱和度 mean={sat[body].mean():.1f} p90={np.percentile(sat[body],90):.0f} (金属通常>40)')
# 锁梁内部杂点：找锁梁内透明区内的非透明像素
mask255 = (~m2).astype(np.uint8)
n, lab, stats, cent = cv2.connectedComponentsWithStats(mask255, 4)
h, w = mask255.shape
border = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]])))
holes = [(i, stats[i]) for i in range(1, n) if i not in border and stats[i, 4] > 40]
for i, st in holes:
    comp = (lab == i)
    ys, xs = np.nonzero(comp)
    # 孔内是否有非透明杂点
    solid = m2[ys, xs]
    print(f'  内孔 #{i}: bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()}) area={st[4]} 孔内不透明像素={int(solid.sum())}')

print()
print('===== PILL 垂直剖面 x=384 =====')
for y in range(48, 100):
    b, g, r = pill[y, 384]
    gold = 'GOLD' if (r > 165 and b < 165 and 90 < g < r * 0.96) else ''
    print(f'  y={y:3d} BGR=({b:5.1f},{g:5.1f},{r:5.1f}) {gold}')
print('===== PILL 端部形状（逐行左右边界）=====')
pm = subject_mask(pill)
for y in range(50, 205, 5):
    idx = np.nonzero(pm[y])[0]
    if len(idx):
        print(f'  y={y:3d} left={idx.min():3d} right={idx.max():3d} width={idx.max()-idx.min()+1:3d}')

print()
print('===== MASCOT 眼/嘴不透明检查 =====')
mm = subject_mask(mascot)
ys, xs = np.nonzero(mm)
print(f'  主体 bbox=({xs.min()},{ys.min()})-({xs.max()},{ys.max()})')
# 眼睛区域（上部）：找深棕像素
mb, mg, mr = mascot[:, :, 0].astype(int), mascot[:, :, 1].astype(int), mascot[:, :, 2].astype(int)
eye = (mr < 110) & (mb < 90) & (mg < 80)
print(f'  深咖(眼)像素={int(eye.sum())}')
ys2, xs2 = np.nonzero(eye)
if len(ys2):
    print(f'  眼 bbox=({xs2.min()},{ys2.min()})-({xs2.max()},{ys2.max()})')
    # 眼睛内部是否有透明/背景像素
    print(f'  眼区域内非主体像素={int((~mm[ys2,xs2]).sum())}')
green = (mg > 110) & (mr < 130) & (mb < 110)
ys3, xs3 = np.nonzero(green)
if len(ys3):
    print(f'  绿(箭头)像素={int(green.sum())} bbox=({xs3.min()},{ys3.min()})-({xs3.max()},{ys3.max()})')
