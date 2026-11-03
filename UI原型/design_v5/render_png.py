import os
import sys
import subprocess
import urllib.parse

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = os.path.dirname(os.path.abspath(__file__))

# (svg 文件名, 输出 png 名, 窗口宽高)
JOBS = [
    ("01_structure_proof.svg", "01_structure_proof.png", 780, 2240),
    ("02_game_hifi.svg", "02_game_hifi.png", 780, 1688),
    ("03_home_hifi.svg", "03_home_hifi.png", 780, 1688),
    ("04_game_default.svg", "04_game_default.png", 780, 1688),
    ("05_game_states.svg", "05_game_states.png", 780, 4300),
    ("06_home_default.svg", "06_home_default.png", 780, 1688),
    ("07_home_states.svg", "07_home_states.png", 780, 2660),
    ("08_page_flow.svg", "08_page_flow.png", 780, 1580),
    ("12_screen_adapt_360.svg", "12_screen_adapt_360.png", 1560, 1800),
    ("13_expansion_pages.svg", "13_expansion_pages.png", 780, 4820),
    ("14_collection_page.svg", "14_collection_page.png", 780, 3184),
    ("15_shop_page.svg", "15_shop_page.png", 780, 3104),
    ("16_settings_page.svg", "16_settings_page.png", 780, 2480),
    ("17_chapter_end.svg", "17_chapter_end.png", 780, 5670),
    ("17_chapter_end_clean.svg", "17_chapter_end_clean.png", 780, 5348),
    ("clean_home.svg", "clean_home.png", 780, 1688),
    ("clean_home_00.svg", "clean_home_00.png", 780, 1688),
    ("clean_home_11.svg", "clean_home_11.png", 780, 1688),
    ("clean_home_12.svg", "clean_home_12.png", 780, 1688),
    ("clean_home_12_preparing.svg", "clean_home_12_preparing.png", 780, 1688),
    ("clean_game.svg", "clean_game.png", 780, 1688),
    ("clean_collection.svg", "clean_collection.png", 780, 1688),
    ("clean_store.svg", "clean_store.png", 780, 1688),
    ("clean_settings.svg", "clean_settings.png", 780, 1688),
    ("clean_settlement.svg", "clean_settlement.png", 780, 1688),
    ("clean_settlement_repeat.svg", "clean_settlement_repeat.png", 780, 1688),
    ("clean_settlement_chapter.svg", "clean_settlement_chapter.png", 780, 1688),
    ("clean_settlement_short.svg", "clean_settlement_short.png", 720, 1280),
    ("adapt_360x640.svg", "adapt_360x640.png", 720, 1460),
    ("adapt_390x844.svg", "adapt_390x844.png", 780, 1868),
    ("adapt_390x932.svg", "adapt_390x932.png", 780, 2044),


    ("ch01_region_mask.svg", "ch01_region_mask.png", 1100, 1100),
]

selected = set(sys.argv[1:])
for svg_name, png_name, w, h in JOBS:
    if selected and svg_name not in selected:
        continue
    src = os.path.join(BASE, svg_name)
    out = os.path.join(BASE, png_name)
    url = "file:///" + urllib.parse.quote(os.path.abspath(src).replace("\\", "/"), safe="/:")
    cmd = [
        CHROME,
        "--headless",
        "--disable-gpu",
        # 允许 SVG 通过 file:// 引用同目录/相对路径的 PNG（页面稿引用真实美术资源）
        "--allow-file-access-from-files",
        f"--screenshot={out}",
        f"--window-size={w},{h}",
        url,
    ]
    print(f"Rendering {png_name} ({w}x{h}) ...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
    ok = r.returncode == 0 and os.path.exists(out)
    print(f"  -> {'OK ' + str(os.path.getsize(out)) + ' bytes' if ok else 'FAILED'}")
    if not ok:
        print("  stdout:", r.stdout[:500])
        print("  stderr:", r.stderr[:500])

print("Done.")
