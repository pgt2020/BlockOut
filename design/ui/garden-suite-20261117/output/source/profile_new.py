"""分析新 frame / pill 的横截面结构：金线层数、边框层序、孔角圆角"""
import cv2, numpy as np

M = r'C:\Users\admin\.workbuddy\plugins\data\mcp-miora\miora-media'
frame = cv2.imread(M + r'\miora_text_to_image-1794910185454-0-1262bf84196a.png').astype(np.float32)
pill = cv2.imread(M + r'\miora_text_to_image-1794910409239-0-702abad431c3.png').astype(np.float32)

print('===== FRAME 水平中线 y=383, x=88..180 =====')
for x in range(88, 180, 2):
    b, g, r = frame[383, x]
    gold = 'GOLD' if (r > 165 and b < 165 and g < r * 0.96) else ''
    print(f'  x={x:3d} BGR=({b:5.1f},{g:5.1f},{r:5.1f}) {gold}')

print('===== FRAME 孔左上角 alpha 边界 =====')
# 找孔轮廓：x=160..210 逐行第一列透明
for y in range(160, 200):
    row = frame[y, :, 0]
    # magenta test
    r_, g_, b_ = frame[y, 200]
    print(f'  y={y:3d} BGR@x=200=({b_:.0f},{g_:.0f},{r_:.0f})')

print('===== FRAME 顶部中线 x=384, y=88..180 =====')
for y in range(88, 180, 2):
    b, g, r = frame[y, 384]
    gold = 'GOLD' if (r > 165 and b < 165 and g < r * 0.96) else ''
    print(f'  y={y:3d} BGR=({b:5.1f},{g:5.1f},{r:5.1f}) {gold}')

print('===== PILL 垂直中线 x=384, y=48..108 =====')
for y in range(48, 108):
    b, g, r = pill[y, 384]
    gold = 'GOLD' if (r > 165 and b < 165 and g < r * 0.96) else ''
    print(f'  y={y:3d} BGR=({b:5.1f},{g:5.1f},{r:5.1f}) {gold}')

print('===== PILL 端部形状：左端各行最左非洋红像素 =====')
for y in range(53, 202, 6):
    row = pill[y]
    sub = row[:, :]
    # magenta-ish?
    r_, g_, b_ = sub[:, 0], sub[:, 1], sub[:, 2]
    notbg = ~((r_ > 150) & (b_ > 150) & (g_ < 130))
    idx = np.nonzero(notbg)[0]
    print(f'  y={y:3d} left={idx.min() if len(idx) else -1} right={idx.max() if len(idx) else -1}')
