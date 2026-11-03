# -*- coding: utf-8 -*-
"""生成 BlockOut 第一章可交付几何素材（design_v5/assets/）。
- 12 张独立 region 遮罩 PNG（1080x1080，固定源坐标，无虚线/编号）
- 共用 fail 占位 PNG
- 干净母版 SVG（供美术切分 full/preview/silhouette 对齐用，无标注）
- region <-> 关卡对应表 CSV
几何严格遵循 ch01_region_mask.svg：4 列 x 3 行，每区 270x360，行优先编号。
"""
import csv, os, json
from pathlib import Path
from PIL import Image, ImageDraw

CANVAS = 1080
CELL_W, CELL_H = 270, 360
OUT = os.path.dirname(os.path.abspath(__file__)) + "/assets"
os.makedirs(OUT, exist_ok=True)

# region_01 起点 (0,0)，行优先：col 0..3, row 0..2
RECTS = {}
idx = 1
for row in range(3):
    for col in range(4):
        x = col * CELL_W
        y = row * CELL_H
        RECTS["region_%02d" % idx] = (x, y, CELL_W, CELL_H)
        idx += 1

# 1) 12 张独立 region 遮罩：该区域填白（alpha），其余透明。
#    约定：white=该 level 的揭晓区域；程序用其 alpha 决定"该区域是否已解锁显示完整图"。
for name, (x, y, w, h) in RECTS.items():
    im = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=(255, 255, 255, 255))
    im.save(OUT + "/" + name + ".png")
print("region masks:", len(RECTS))

# 2) 共用 fail 占位：暖色底 + 居中圆角破损图标（无文字，中性，可 contain 任意容器）
ph = Image.new("RGBA", (CANVAS, CANVAS), (255, 247, 239, 255))  # #FFF7EF
d = ImageDraw.Draw(ph)
# 居中圆角矩形外框
m = 340
d.rounded_rectangle([m, m, CANVAS - m, CANVAS - m], radius=48,
                    outline=(233, 207, 192, 255), width=10)  # #E9CFC0
# 简易"破损图"图标：山形 + 斜杠
cx0, cy0, cx1, cy1 = 420, 470, 660, 610
d.line([(cx0, cy1), (520, 540), (580, 590), (640, 520), (cx1, cy1)],
       fill=(185, 167, 155, 255), width=10, joint="curve")
d.ellipse([470, 430, 520, 480], outline=(185, 167, 155, 255), width=10)
d.line([(400, 400), (CANVAS - 400, CANVAS - 400)], fill=(244, 95, 112, 200), width=12)
ph.save(OUT + "/ch01_fail_placeholder.png")
print("fail placeholder: ok")

# 3) 干净母版 SVG（无虚线/编号/关号），供美术对齐切分
svg = ['<?xml version="1.0" encoding="UTF-8"?>']
svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="第一章章节图集干净几何母版（无标注，供美术切分 full/preview/silhouette 对齐）">'
           % (CANVAS, CANVAS, CANVAS, CANVAS))
svg.append('  <rect x="1" y="1" width="%d" height="%d" fill="none" stroke="#E8CDBB" stroke-width="3"/>' % (CANVAS - 2, CANVAS - 2))
gfill = ["#FFF7EF", "#FFF1E3"]
fi = 0
for name, (x, y, w, h) in RECTS.items():
    svg.append('  <rect x="%d" y="%d" width="%d" height="%d" fill="%s" opacity=".0"/>' % (x, y, w, h, gfill[fi % 2]))
    fi += 1
# 仅用极淡描边标出 12 区边界（无编号/关号），便于美术分层
svg.append('  <g fill="none" stroke="#E8CDBB" stroke-width="1.5">')
for name, (x, y, w, h) in RECTS.items():
    svg.append('    <rect x="%d" y="%d" width="%d" height="%d"/>' % (x, y, w, h))
svg.append('  </g>')
svg.append('</svg>')
with open(OUT + "/ch01_mask_master_clean.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print("clean master svg: ok")

# 4) 读取当前包内真实目录；补齐关ID与 BlockOutCatalog 一致，保持现有存档兼容。
manifest_path = Path(__file__).resolve().parents[2] / "Assets/Resources/ArtOut/GameAssets.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
level_ids = [item["id"] for item in manifest["levels"]]

# 4) region <-> 关卡对应表 CSV
with open(OUT + "/region_level_map.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["region_id", "global_level", "chapter", "level_in_chapter",
                "grid_col", "grid_row", "pixel_x", "pixel_y", "pixel_w", "pixel_h",
                "source_canvas", "level_id", "content_status"])
    idx = 1
    for row in range(3):
        for col in range(4):
            x, y, cw, ch = RECTS["region_%02d" % idx]
            w.writerow(["region_%02d" % idx, idx, 1, idx,
                        col, row, x, y, cw, ch, "1080x1080",
                        level_ids[idx - 1] if idx <= len(level_ids) else "gen_placeholder_%03d" % idx,
                        "bundled" if idx <= len(level_ids) else "generated_placeholder"])
            idx += 1
print("csv: ok")
print("ALL DONE ->", OUT)
