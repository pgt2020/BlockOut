# -*- coding: utf-8 -*-
"""BlockOut UI Design System v6 · Prefab 色彩烘焙脚本（幂等）。

唯一真源: BlockOut/Docs/DesignSystem.md §1
作用: 把 Resources/Prefabs/UI/*.prefab 的 m_Color 从 v5 烘焙值刷新为 v6 值。
      仅改 m_Color 的 r/g/b，保留 a、保留白色/黑色/透明占位色、不改任何结构与 GUID。

注意: 运行时棋盘/方块不在这些 Prefab 内（见 DesignSystem.md §1.4 运行时色链路），
      对局方块色的表现层重映射需在 Unity 侧接线，本脚本不覆盖。

用法 (在 BlockOut/ 目录):
    python Tools/Design/apply_v6_to_prefabs.py
可重复执行；已刷新过的色块不会被二次改写。
"""
import io
import os
import sys

PREFAB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Assets", "BlockOut", "Resources", "Prefabs", "UI",
)

# 烘焙后的实际色值 -> v6 目标色值（RGB 0-1 浮点由 8bit 反算，保留 3 位小数）
IMAGE_MAP = {
    "#FFFFFF": "#FFFFFF",   # 白：卡片/图标块，保留
    "#000000": "#000000",   # 黑：透明命中区/占位，保留
    "#52382E": "#3B2A24",   # text.cocoa
    "#FFF6EC": "#FFF8F0",   # bg.cream
    "#E0D9CC": "#E7D2BE",   # stroke.warm / 浅暖底
    "#F76E5E": "#4A2F26",   # 珊瑚 CTA -> action.primary
    "#A8DBC2": "#1E8F68",   # 薄荷块 -> state.go
    "#D8ECFF": "#DFF6EC",   # 浅蓝点缀 -> state.goBg
}
# Text 组件上的同色值：必须保证在浅底上可读，用语义文字色而非实底色
TEXT_MAP = dict(IMAGE_MAP)
TEXT_MAP.update({
    "#A8DBC2": "#14664A",   # state.goText
    "#D8ECFF": "#14664A",
    "#E0D9CC": "#6E5449",   # text.secondary（浅色文字不会被当描边）
    "#52382E": "#3B2A24",
})

UGUI_IMAGE_GUID = "fe87c0e1cc204ed48ad3b37840f39efc"
UGUI_TEXT_GUID = "5f7201a12d95ffc409449d95f23cf332"


def nearest_hex(r, g, b):
    """把浮点 RGB 归到最近的已知烘焙色（容差 2/255），未命中返回 None。"""
    rgb = tuple(round(float(x) * 255) for x in (r, g, b))
    key = "#%02X%02X%02X" % rgb
    if key in IMAGE_MAP:
        return key
    for k in IMAGE_MAP:
        kr = tuple(int(k[i:i + 2], 16) for i in (1, 3, 5))
        if all(abs(a - bb) <= 2 for a, bb in zip(rgb, kr)):
            return k
    return None


def component_kind(lines, idx):
    """向上找最近的组件块，按 m_Script guid 判断是 Image 还是 Text。"""
    for j in range(idx - 1, max(-1, idx - 40), -1):
        if lines[j].startswith("--- !u!"):
            chunk = "\n".join(lines[j:idx])
            if UGUI_TEXT_GUID in chunk:
                return "text"
            if UGUI_IMAGE_GUID in chunk:
                return "image"
            return "other"
    return "other"


def process(path):
    with io.open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    lines = text.splitlines(True)
    out = list(lines)
    changed = 0
    skipped = 0
    for i, line in enumerate(lines):
        if line.strip() != "m_Color:" or i + 4 >= len(lines):
            continue
        try:
            r = float(lines[i + 1].split(":")[1].strip())
            g = float(lines[i + 2].split(":")[1].strip())
            b = float(lines[i + 3].split(":")[1].strip())
        except (ValueError, IndexError):
            skipped += 1
            continue
        src = nearest_hex(r, g, b)
        if src is None:
            skipped += 1
            continue
        table = TEXT_MAP if component_kind(lines, i) == "text" else IMAGE_MAP
        dst = table.get(src, src)
        if dst == src:
            continue
        dr = int(dst[1:3], 16) / 255.0
        dg = int(dst[3:5], 16) / 255.0
        db = int(dst[5:7], 16) / 255.0
        # 保留原 a 行与缩进/行尾风格
        for k, val in enumerate((dr, dg, db)):
            raw = lines[i + 1 + k]
            prefix = raw[:raw.index(":") + 1]
            eol = "\r\n" if raw.endswith("\r\n") else "\n"
            out[i + 1 + k] = "%s %.3f%s" % (prefix, round(val, 3), eol)
        changed += 1
    if changed:
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write("".join(out))
    return changed, skipped


def main():
    if not os.path.isdir(PREFAB_DIR):
        print("PREFAB_DIR not found:", PREFAB_DIR)
        return 1
    files = sorted(f for f in os.listdir(PREFAB_DIR) if f.endswith(".prefab"))
    total = 0
    for name in files:
        c, sk = process(os.path.join(PREFAB_DIR, name))
        total += c
        print("%-38s changed %4d  unchanged/other %4d" % (name, c, sk))
    print("TOTAL color blocks rewritten:", total, "in", len(files), "prefabs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
