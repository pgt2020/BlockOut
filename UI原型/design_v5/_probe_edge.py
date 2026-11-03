# -*- coding: utf-8 -*-
"""边缘裁切探针：扫描 PNG 四边 6px，报告深色像素（疑似文字/内容被裁切）。"""
from PIL import Image
import glob, os

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = ["05_game_states.png", "07_home_states.png", "08_page_flow.png",
         "12_screen_adapt_360.png", "13_expansion_pages.png", "14_collection_page.png",
         "15_shop_page.png", "16_settings_page.png", "17_chapter_end.png"]

for name in FILES:
    im = Image.open(os.path.join(BASE, name)).convert("RGB")
    W, H = im.size
    hits = []
    for y in range(0, 6):
        for x in range(0, W, 3):
            if sum(im.getpixel((x, y))) < 380: hits.append(("top", x, y))
    for y in range(H - 6, H):
        for x in range(0, W, 3):
            if sum(im.getpixel((x, y))) < 380: hits.append(("bottom", x, y))
    for x in range(0, 6):
        for y in range(0, H, 3):
            if sum(im.getpixel((x, y))) < 380: hits.append(("left", x, y))
    for x in range(W - 6, W):
        for y in range(0, H, 3):
            if sum(im.getpixel((x, y))) < 380: hits.append(("right", x, y))
    print(f"{name}: {W}x{H} -> {'CLEAN' if not hits else str(len(hits)) + ' hits ' + str(hits[:4])}")
