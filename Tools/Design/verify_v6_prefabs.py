# -*- coding: utf-8 -*-
"""
v6 Prefab 色彩落地静态核查（只读，可重复执行）。

用途：
  1. 校验 13 个 UI Prefab 的 m_Color 是否全部落在 v6 调色板内；
  2. 按组件类型（Image / Text / Button）分别统计颜色；
  3. 找出「浅色文字」，并沿 RectTransform 父链找最近的 Image 底色，
     计算 WCAG 对比度，标出真正不可读的组合；
  4. 统计 Text 的 m_FontSize / m_BestFit 下限。

注意：Unity Prefab YAML 的 m_Script / m_GameObject 是多行格式：
    m_Script:
      fileID: 11500000
      guid: 5f7201a12d95ffc409449d95f23cf332
      type: 3
所以不能用单行正则抓 guid，必须按 YAML 文档块逐块解析，
且 m_Script 下同时存在 fileID 与 guid，必须精确取 guid 那一行。

不依赖 Unity，不修改任何文件。运行：
    python -X utf8 Tools/Design/verify_v6_prefabs.py
"""
import glob
import io
import os
import re
import collections

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
PREFAB_DIR = os.path.normpath(
    os.path.join(ROOT, "Assets", "BlockOut", "Resources", "Prefabs", "UI")
)

# v6 唯一允许的 m_Color 值（Docs/DesignSystem.md §2）
PALETTE = {
    "#FFFFFF",  # 白：文字 / 图标遮罩
    "#000000",  # 黑：Dim 遮罩
    "#FFF8F0",  # surface.page
    "#E7D2BE",  # surface.line / 分割线 / 未选中
    "#3B2A24",  # text.cocoa
    "#4A2F26",  # action.primary
    "#1E8F68",  # state.go
    "#DFF6EC",  # state.go 浅底
}

# Unity 内置 UGUI 组件脚本 GUID
UGUI = {
    "fe87c0e1cc204ed48ad3b37840f39efc": "Image",
    "5f7201a12d95ffc409449d95f23cf332": "Text",
    "4e29b1a8efbd4b44bb3f3716e73f07ff": "Button",
}

DOC_RE = re.compile(r"^--- !u!([0-9]+) &([0-9]+)")
FILEID_RE = re.compile(r"^[ ]+fileID:[ ]*([0-9]+)")
GUID_RE = re.compile(r"^[ ]+guid:[ ]*([0-9a-f]+)")


def hx(r, g, b):
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def lum(rgb):
    def ch(v):
        v = float(v)
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(rgb[0]) + 0.7152 * ch(rgb[1]) + 0.0722 * ch(rgb[2])


def contrast(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def parse_blocks(lines):
    blocks, cur = [], None
    for line in lines:
        m = DOC_RE.match(line)
        if m:
            if cur:
                blocks.append(cur)
            cur = {"class": int(m.group(1)), "id": m.group(2), "lines": []}
        if cur:
            cur["lines"].append(line)
    if cur:
        blocks.append(cur)
    return blocks


def scalar(block, key, cast=str):
    for line in block["lines"]:
        s = line.strip()
        if s.startswith(key + ":"):
            try:
                return cast(s.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def child_ref(block, key, want="fileID"):
    """多行字段（m_Script / m_GameObject / m_Father）里的 fileID 或 guid。"""
    rx = GUID_RE if want == "guid" else FILEID_RE
    for i, line in enumerate(block["lines"][:30]):
        if line.strip() == key + ":":
            for k in range(i + 1, min(i + 5, len(block["lines"]))):
                m = rx.match(block["lines"][k])
                if m:
                    return m.group(1)
    return None


def color_of(block):
    for i, line in enumerate(block["lines"]):
        if line.strip() != "m_Color:":
            continue
        try:
            return (tuple(float(block["lines"][i + 1 + k].split(":")[1]) for k in range(3)),
                    hx(*[float(block["lines"][i + 1 + k].split(":")[1]) for k in range(3)]))
        except (IndexError, ValueError):
            return None
    return None


def main():
    by_type = collections.Counter()
    all_colors = collections.Counter()
    stray, bad_contrast, sizes, bestfit_off = [], [], [], []
    files = sorted(glob.glob(os.path.join(PREFAB_DIR, "*.prefab")))
    print("prefab count: %d" % len(files))

    for path in files:
        base = os.path.basename(path)
        lines = io.open(path, encoding="utf-8").read().splitlines()
        blocks = parse_blocks(lines)

        # GameObject 名字
        names = {b["id"]: scalar(b, "m_Name")
                 for b in blocks if b["class"] == 1}

        # 组件类型 / 颜色 / 归属 GameObject
        info = {}
        for b in blocks:
            guid = child_ref(b, "m_Script", want="guid")
            typ = UGUI.get(guid) if guid else None
            go = child_ref(b, "m_GameObject")
            col = color_of(b)
            info[b["id"]] = {"type": typ, "go": go, "color": col,
                             "block": b, "name": names.get(go, "?")}

        # RectTransform 父链：transform_id -> (go, father_transform_id)
        xf = {}
        go_to_xf = {}
        for b in blocks:
            if b["class"] in (4, 224):
                go = child_ref(b, "m_GameObject")
                father = child_ref(b, "m_Father")
                xf[b["id"]] = (go, father)
                if go:
                    go_to_xf[go] = b["id"]

        # 每个 GameObject 上挂的 Image 颜色
        images_by_go = collections.defaultdict(list)
        for cid, d in info.items():
            if d["type"] == "Image" and d["color"] and d["go"]:
                images_by_go[d["go"]].append(d["color"][0])

        for cid, d in info.items():
            if not d["color"]:
                continue
            rgb, color = d["color"]
            typ = d["type"] or "?"
            by_type[(typ, color)] += 1
            all_colors[color] += 1
            if color not in PALETTE:
                stray.append((base, typ, d["name"], color))

            if typ != "Text":
                continue
            fsz = scalar(d["block"], "m_FontSize", int)
            if fsz is not None:
                sizes.append(fsz)
            bf = scalar(d["block"], "m_BestFit", int)
            if bf == 0:
                bestfit_off.append((base, d["name"], fsz))

            # 浅色文字：沿父链找最近的非透明 Image 底色，算对比度
            if lum(rgb) <= 0.35:
                continue
            bg, bg_where = None, None
            sid = go_to_xf.get(d["go"])
            for _ in range(6):
                if not sid or sid not in xf:
                    break
                go, father = xf[sid]
                cands = images_by_go.get(go, [])
                if cands:
                    bg, bg_where = cands[0], names.get(go, "?")
                    break
                sid = father
            if bg is None:
                bad_contrast.append((base, d["name"], fsz, "NO-BG-FOUND", 0.0))
                continue
            ratio = contrast(rgb, bg)
            if ratio < 4.5:
                bad_contrast.append((base, d["name"], fsz,
                                     hx(*bg) + " @" + bg_where, round(ratio, 2)))

    print("\n=== color x component type ===")
    for (typ, color), n in by_type.most_common():
        print("  %-7s %-9s %3d" % (typ, color, n))

    print("\n=== all colors ===")
    for color, n in all_colors.most_common():
        print("  %-9s %3d" % (color, n))

    print("\n=== stray colors (not in v6 palette): %d ===" % len(stray))
    for s in stray[:40]:
        print("  ", s)

    print("\n=== light Text with contrast < 4.5 (real readability risk): %d ===" %
          len(bad_contrast))
    for s in bad_contrast[:40]:
        print("  ", s)

    if sizes:
        print("\n=== Text m_FontSize min/max: %d / %d (count %d) ===" %
              (min(sizes), max(sizes), len(sizes)))
    print("=== Text with m_BestFit disabled: %d ===" % len(bestfit_off))
    for s in bestfit_off[:20]:
        print("  ", s)


if __name__ == "__main__":
    main()
