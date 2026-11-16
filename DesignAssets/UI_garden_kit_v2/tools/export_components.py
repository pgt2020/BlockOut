# -*- coding: utf-8 -*-
"""Export the component set at 2x (2160-wide design space) with nine-slice metadata."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import components as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'components')
os.makedirs(OUT, exist_ok=True)

K = 2  # 2x of the 1080x1920 design space

records = []


def save(img, name, note, border=None, state=None):
    img.save(os.path.join(OUT, name + '.png'), optimize=True)
    rec = {'file': 'components/%s.png' % name, 'size': list(img.size), 'note': note}
    if border:
        rec['nine_slice'] = border
    if state:
        rec['state'] = state
    records.append(rec)


for st, note in [('locked', '未解锁关卡'), ('completed', '已通关关卡'), ('current', '当前关卡'),
                 ('star', '星级/里程碑关卡'), ('fail', '失败关卡'), ('challenge', '挑战关卡')]:
    key = 'done' if st == 'completed' else st
    im = C.node(key, 256 * K)
    b = int(14 * K)
    save(im, 'node_' + st, note + '（无数字，可叠任意文案）', [b, b, b, b], st)

save(C.node_pointer(64 * K), 'node_pointer', '当前关卡下方指向箭')

cta = C.pill(615 * K, 257 * K, int(104 * K), (122, 226, 152), (44, 164, 86),
             rim_w=int(12 * K), gloss=0.6)
save(cta, 'btn_primary', '主按钮（无文字），左右九宫格拉伸', [int(110 * K), int(60 * K), int(110 * K), int(60 * K)])
save(C.pill(283 * K, 94 * K, int(44 * K), (255, 250, 238), (250, 238, 212), rim_w=6 * K),
     'capsule', '货币胶囊底（票券/数字/加号另叠）', [int(44 * K), int(20 * K), int(44 * K), int(20 * K)])
save(C.pill(943 * K, 248 * K, int(56 * K), (255, 247, 226), (246, 226, 190), rim_w=3 * K, gloss=0.35),
     'nav_bar', '底部导航条底（tab 另叠）', [int(56 * K), int(30 * K), int(56 * K), int(30 * K)])
save(C.tab_card(225 * K, 240 * K, True), 'tab_active', '选中态 tab 卡片')
save(C.plate(300 * K, 92 * K, int(30 * K)), 'plate_label', '小标签底板（任务/成就等）',
     [int(30 * K), int(30 * K), int(30 * K), int(30 * K)])
save(C.circle_btn(120 * K), 'circle_button', '圆形按钮底（齿轮/关闭等）')
save(C.bubble(300 * K, 150 * K), 'bubble', '气泡“当前关卡”底')
for nm, fn in [('badge_lock', C.badge_lock), ('badge_star', C.badge_star),
               ('badge_skull', C.badge_skull), ('badge_plus', C.badge_plus),
               ('badge_alert', C.badge_alert)]:
    save(fn(64 * K), nm, '独立徽章')

with open(os.path.join(OUT, 'components.json'), 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)
print('exported', len(records))
