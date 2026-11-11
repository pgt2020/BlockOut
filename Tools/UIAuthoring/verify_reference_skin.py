# -*- coding: utf-8 -*-
"""还原层验收：Prefab 引用完整性 + 按 bbox 重渲染与用户原图的 1:1 对照。

输出 : outputs/ui_reference_verify/
       screens/s1..s9.png   按 Unity Prefab 同一份 layout / bind 数据重渲染
       compare_9screens.png 原图 vs 还原层 并排对照板
       report.json          逐屏相似度、结构校验与运行时接线核对

渲染口径与 Prefab 完全一致：擦字变体图 + 代码层 Text 默认值 + 挖空区透出真棋盘，
因此这份图就是「进游戏后看到的界面」，不是资源预览。
"""
from pathlib import Path
import json
import re
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT.parent
REF = ROOT / "Assets/BlockOut/Resources/UI/Reference"
PREFABS = ROOT / "Assets/BlockOut/Resources/Prefabs/UI/Reference"
ORIGINAL = WORK / "outputs/ui_replica_v7/reference_original"
OUT = WORK / "outputs/ui_reference_verify"
LAYOUT = json.loads((REF / "reference_layout.json").read_text(encoding="utf-8"))
BIND = json.loads((Path(__file__).parent / "reference_bind.json").read_text(encoding="utf-8"))
# 固化窗口：原图 -> 设计基准的仿射变换，工程内唯一真源，验收不再重新搜索
WINDOWS = json.loads((Path(__file__).parent / "alignment_windows.json").read_text(encoding="utf-8"))
SCREEN_NAMES = {"s1": "Loading", "s2": "Level", "s3": "Gallery", "s4": "Game",
                "s5": "Complete", "s6": "Fail", "s7": "Skin", "s8": "Daily", "s9": "Map"}
GUID_SKIN = "00bb8f5a829a544ebe120a6999397f83"
GUID_IMAGE = "fe87c0e1cc204ed48ad3b37840f39efc"

try:
    FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
    ImageFont.truetype(FONT_BOLD, 12)
except Exception:
    FONT_BOLD = None


def check_prefabs():
    """校验 9 个 Prefab：fileID 唯一、内部引用可解析、guid 有效、DesignSize / 接线对齐。"""
    known_guids = set()
    for p in (ROOT / "Assets/BlockOut").rglob("*.meta"):
        m = re.search(r"guid: (\w+)", p.read_text(encoding="utf-8-sig", errors="ignore"))
        if m:
            known_guids.add(m.group(1))
    # Unity 内置 UGUI 组件 GUID（不在工程 .meta 里）
    known_guids.update((
        "fe87c0e1cc204ed48ad3b37840f39efc",   # Image
        "5f7201a12d95ffc409449d95f23cf332",   # Text
        "4e29b1a8efbd4b44bb3f3716e73f07ff",   # Button
        "fd593325a489afb46b970fe4942877e4",    # 内置字体
        "f0ec713160a541789aa18448ee150c92",    # BlockOutPageLayout
    ))
    problems = []
    for sid in LAYOUT["screens"]:
        path = PREFABS / ("ReferenceS%s_%s.prefab" % (sid[1:], SCREEN_NAMES[sid]))
        if not path.is_file():
            problems.append(sid + ": Prefab 缺失")
            continue
        text = path.read_text(encoding="utf-8")
        docs = re.split(r"(?=^--- !u!)", text, flags=re.M)
        ids = [int(m.group(1)) for d in docs if (m := re.search(r"^--- !u!\d+ &(\d+)", d))]
        if len(ids) != len(set(ids)):
            problems.append(sid + ": fileID 重复")
        idset = set(ids)
        for d in docs:
            for m in re.finditer(r"fileID: (\d+)", d):
                n = int(m.group(1))
                if n and n not in idset and n not in (21300000, 11500000, 12800000):
                    problems.append(sid + ": 悬空引用 fileID " + str(n))
                    break
        for g in re.findall(r"guid: (\w+)", text):
            if g not in known_guids:
                problems.append(sid + ": 未知脚本/资源 guid " + g)
        w, h = LAYOUT["screens"][sid]["size"]
        if "DesignSize:\n    x: %d\n    y: %d" % (w, h) not in text:
            problems.append(sid + ": DesignSize 与原图不符")
        if GUID_SKIN not in text:
            problems.append(sid + ": 缺 BlockOutReferenceSkin 运行时组件")
        cfg = BIND["screens"].get(sid, {})
        nh = len(cfg.get("hotspots", []))
        nd = len(cfg.get("texts", []))
        if text.count("m_Name: Hotspot_") != nh:
            problems.append(sid + ": 热区数 %d != 配置 %d" % (text.count("m_Name: Hotspot_"), nh))
        if text.count("m_Name: Dyn_") != nd:
            problems.append(sid + ": 动态文字数 %d != 配置 %d" % (text.count("m_Name: Dyn_"), nd))
    return problems


def _guid_of(rel):
    mp = Path(str(REF / rel) + ".meta")
    if not mp.is_file():
        return None
    m = re.search(r"guid: (\w+)", mp.read_text(encoding="utf-8-sig", errors="ignore"))
    return m.group(1) if m else None


def _locate(fname):
    for sub in ("sprites", "bg", "tiles"):
        if (REF / sub / fname).is_file():
            return sub + "/" + fname
    return None


def check_layout_integrity():
    """结构级独立校验：完全不看像素，逐元件核对 Prefab 节点 bbox 与 sprite guid。

    像素相似度会因为「元件取自参考图」而天然偏高，这项才是证明
    「真的实现进了 Unity Prefab」的独立证据：每个元件必须有同名 GameObject、
    RectTransform 的 pos/size 与 layout bbox 一致、Image 引用的 sprite guid
    与 Resources 下该元件（动态字段用擦字变体）的 .meta 完全一致。
    """
    problems = []
    checked = 0
    for sid, spec in LAYOUT["screens"].items():
        path = PREFABS / ("ReferenceS%s_%s.prefab" % (sid[1:], SCREEN_NAMES[sid]))
        if not path.is_file():
            continue
        docs = re.split(r"(?=^--- !u!)", path.read_text(encoding="utf-8"), flags=re.M)
        gos, rts, imgs = {}, {}, {}
        for d in docs:
            if d.startswith("--- !u!1 "):
                fid = re.search(r"&(\d+)", d)
                nm = re.search(r"m_Name: (.+)", d)
                if fid and nm:
                    gos[nm.group(1).strip()] = int(fid.group(1))
            elif d.startswith("--- !u!224 "):
                go = re.search(r"m_GameObject:\s*\n\s*fileID: (\d+)", d)
                pos = re.search(r"m_AnchoredPosition:\s*\n\s*x: ([\d.\-]+)\s*\n\s*y: ([\d.\-]+)", d)
                size = re.search(r"m_SizeDelta:\s*\n\s*x: ([\d.\-]+)\s*\n\s*y: ([\d.\-]+)", d)
                if go and pos and size:
                    rts[int(go.group(1))] = (float(pos.group(1)), float(pos.group(2)),
                                             float(size.group(1)), float(size.group(2)))
            elif d.startswith("--- !u!114 ") and GUID_IMAGE in d:
                go = re.search(r"m_GameObject:\s*\n\s*fileID: (\d+)", d)
                sp = re.search(r"m_Sprite:\s*\n\s*fileID: 21300000\s*\n\s*guid: (\w+)", d)
                if go:
                    imgs[int(go.group(1))] = sp.group(1) if sp else None
        cfg = BIND["screens"].get(sid, {})
        hearts = cfg.get("hearts")
        dyn_items = {f["item"] for f in cfg.get("texts", [])}
        for it in spec["items"]:
            nm = it["name"]
            if hearts and nm == hearts["item"]:
                continue          # 心形拆成 Heart_0..3 独立组件
            if nm not in gos:
                problems.append("%s/%s: Prefab 缺元件节点" % (sid, nm))
                continue
            fid = gos[nm]
            rt = rts.get(fid)
            if rt is None:
                problems.append("%s/%s: 缺 RectTransform" % (sid, nm))
            elif (abs(rt[0] - it["x"]) > 0.6 or abs(rt[1] + it["y"]) > 0.6 or
                  abs(rt[2] - it["w"]) > 0.6 or abs(rt[3] - it["h"]) > 0.6):
                problems.append("%s/%s: bbox %s != layout (%d,%d,%d,%d)" %
                                (sid, nm, rt, it["x"], it["y"], it["w"], it["h"]))
            fn = ("sprites/%s_dyn.png" % Path(it["file"]).stem) if nm in dyn_items \
                else _locate(it["file"])
            exp = _guid_of(fn) if fn else None
            if exp and imgs.get(fid) != exp:
                problems.append("%s/%s: sprite guid 与 %s 不符" % (sid, nm, fn))
            checked += 1
    return problems, checked


def letterbox_rgb(bg_file):
    import numpy as np
    a = np.asarray(Image.open(REF / "bg" / bg_file).convert("RGB"))
    band = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3)], axis=0)
    return tuple(int(v) for v in np.median(band, axis=0))


def runtime_board_layer():
    """s4 挖空区透出的运行时真棋盘占位。

    Prefab 里这一块是 alpha=0 的洞，实际画面由 BoardView 按关卡数据渲染，
    不属于静态还原资源。验收图用「用户原稿棋盘区」占位，才能和左栏同口径比较；
    该占位只出现在验收渲染里，不写进任何 Prefab / Resources。
    """
    import numpy as np
    t = LAYOUT["tilekit"]
    W, H = LAYOUT["screens"]["s4"]["size"]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    op = ORIGINAL / "s4_game.png"
    if op.is_file():
        o = Image.open(op).convert("RGBA")
        x0, y0, cw, ch = 9, 16, 324, 476          # 与 s2/s6 同源的裁片窗口
        aligned = o.crop((x0, y0, min(o.size[0], x0 + cw), min(o.size[1], y0 + ch))) \
                   .resize((W, H), Image.LANCZOS)
        bx, by, bw, bh = BIND["screens"]["s4"]["passthrough"]["rect"]
        patch = aligned.crop((bx, by, min(W, bx + bw), min(H, by + bh)))
        layer.alpha_composite(patch, (bx, by))
        return layer
    grid, pal, rot = t["grid"], t["palette"], t["rotation"]
    s = grid["size"]
    shade = np.asarray(Image.open(REF / "tiles/tile_base.png").convert("RGBA")
                       .resize((s, s), Image.LANCZOS)).astype(np.float32)
    up = Image.open(REF / "tiles/arrow_up.png").convert("RGBA")
    cross = Image.open(REF / "tiles/arrow_cross.png").convert("RGBA")
    for row in t["board"]:
        for c in row:
            if c["color"] is None and c["dir"] == "none":
                continue
            x = grid["x"] + c["c"] * s
            y = grid["y"] + c["r"] * s
            rgb = pal.get(c["color"] or "cream")
            arr = np.empty((s, s, 4), np.float32)
            for ch in range(3):
                arr[:, :, ch] = shade[:, :, ch] * rgb[ch] / 255.0
            arr[:, :, 3] = 255
            block = Image.fromarray(arr.astype("uint8"), "RGBA")
            hw, hh = int(s * 0.82), int(s * 0.26)
            hi = np.zeros((hh, hw, 4), np.uint8)
            hi[:, :, :3] = 255
            for r in range(hh):
                hi[r, :, 3] = int(70 * (1 - r / hh))
            block.alpha_composite(Image.fromarray(hi, "RGBA"),
                                  (int(s * 0.09), int(s * 0.06)))
            if c["dir"] != "none":
                aw = int(round(s * 0.66))
                a = cross if c["dir"] == "cross" else up
                a = a.resize((aw, aw), Image.LANCZOS).rotate(-rot.get(c["dir"], 0))
                block.alpha_composite(a, ((s - aw) // 2, (s - aw) // 2))
            layer.alpha_composite(block, (x, y))
    return layer


def draw_dyn(canvas, box, value, size, color):
    """把 Dyn_<key> 的 Text 默认值画回验收图（Unity 侧由 SetText 镜像业务数值）。"""
    x, y, w, h = box
    try:
        font = ImageFont.truetype(FONT_BOLD, max(8, int(size))) if FONT_BOLD else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()
    layer = Image.new("RGBA", (max(1, int(w)), max(1, int(h))), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rgb = tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    bb = d.textbbox((0, 0), value, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((w - tw) / 2 - bb[0], (h - th) / 2 - bb[1]),
           value, font=font, fill=rgb + (255,))
    canvas.alpha_composite(layer, (int(x), int(y)))


def render(sid, spec):
    W, H = spec["size"]
    cfg = BIND["screens"].get(sid, {"texts": [], "hotspots": []})
    pt = cfg.get("passthrough")
    hearts = cfg.get("hearts")
    items = {it["name"]: it for it in spec["items"]}
    dyn_files = {}
    for f in cfg.get("texts", []):
        fn = items[f["item"]]["file"]
        dyn_files[f["item"]] = Path(fn).stem + "_dyn" + Path(fn).suffix

    canvas = Image.new("RGBA", (W, H), letterbox_rgb(spec["bg"]) + (255,))
    # 挖空屏：先铺运行时真棋盘，再盖挖空背景，洞口自然透出棋盘
    if pt:
        canvas.alpha_composite(runtime_board_layer())
    bg_name = pt["bg_out"] if pt else spec["bg"]
    bg = Image.open(REF / "bg" / bg_name).convert("RGBA")
    if bg.size != (W, H):
        bg = bg.resize((W, H), Image.LANCZOS)
    canvas.alpha_composite(bg)

    def paste(fname, x, y):
        for sub in ("sprites", "bg", "tiles"):
            p = REF / sub / fname
            if p.is_file():
                canvas.alpha_composite(Image.open(p).convert("RGBA"), (int(x), int(y)))
                return

    for it in spec["items"]:
        if hearts and it["name"] == hearts["item"]:
            step = it["w"] / hearts["count"]
            for i in range(hearts["count"]):
                paste(hearts["on"] if i < 3 else hearts["off"], it["x"] + i * step, it["y"])
            continue
        paste(dyn_files.get(it["name"], it["file"]), it["x"], it["y"])

    for f in cfg.get("texts", []):
        it = items[f["item"]]
        x0, y0, bw, bh = f["box"]
        draw_dyn(canvas, (it["x"] + x0, it["y"] + y0, bw, bh),
                 f["text"], f["size"], f["color"])
    return canvas.convert("RGB")


def mae(a, b):
    import numpy as np
    return float(np.abs(np.asarray(a, dtype=np.int16) - np.asarray(b, dtype=np.int16)).mean())


def center_crop_aligned(orig, W, H):
    """旧口径：按目标宽高比中心裁剪。保留下来只是为了在报告里对照，不再作为主分。"""
    ow, oh = orig.size
    tr = W / H
    if ow / oh > tr:
        nw = int(oh * tr)
        left = (ow - nw) // 2
        return orig.crop((left, 0, left + nw, oh)).resize((W, H), Image.LANCZOS)
    nh = int(ow / tr)
    top = (oh - nh) // 2
    return orig.crop((0, top, ow, top + nh)).resize((W, H), Image.LANCZOS)


def register_original(orig, made, sid):
    """用工程内固化的窗口把用户原图映射到该屏设计基准。

    窗口写在 Tools/UIAuthoring/alignment_windows.json，是资源生成
    (rebuild_reference_assets.py) 与验收共用的唯一真源。绝不在验收时重新搜索
    窗口 —— 否则基准会跟着渲染结果漂移，形成循环自证。

    9 张原图各自带不同宽度白边，且原图(384x512)与设计基准(325x478)比例不同，
    所以窗口包含 crop + 非等比 resize，这是裁片当年真实的变换。
    s9 原图 941x1672 与基准 470x836 精确 2:1，直接缩放。
    """
    W, H = made.size
    if sid == "s9":
        return orig.resize((W, H), Image.LANCZOS), (0, 0, orig.width, orig.height)
    x0, y0, w, h = WINDOWS[sid]
    x1, y1 = min(orig.width, x0 + w), min(orig.height, y0 + h)
    return orig.crop((x0, y0, x1, y1)).resize((W, H), Image.LANCZOS), (x0, y0, w, h)


def similarity(aligned, made):
    d = ImageChops.difference(aligned.convert("RGB"), made.convert("RGB"))
    return round(1 - sum(ImageStat.Stat(d).mean) / 3.0 / 255.0, 4)


def similarity_excluding(aligned, made, rect):
    """排除指定区域后的相似度。s4 棋盘是「运行时真棋盘占位」，与静态还原资源
    无关，单列这个分数避免把占位区的满分算进还原度。"""
    import numpy as np
    A = np.asarray(aligned.convert("RGB"), dtype=np.float32)
    B = np.asarray(made.convert("RGB"), dtype=np.float32)
    d = np.abs(A - B).mean(2)
    x, y, w, h = rect
    mask = np.ones(d.shape, bool)
    mask[y:min(d.shape[0], y + h), x:min(d.shape[1], x + w)] = False
    return round(1 - float(d[mask].mean()) / 255.0, 4) if mask.any() else None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "screens").mkdir(exist_ok=True)
    problems = check_prefabs()
    layout_problems, layout_checked = check_layout_integrity()
    problems += layout_problems
    report = {"structure_problems": problems,
              "layout_integrity": {"checked_elements": layout_checked,
                                   "problems": layout_problems},
              "screens": {},
              "alignment_note": "对齐窗口固化在 Tools/UIAuthoring/alignment_windows.json，资源生成与验收共用，不再在验收时搜索窗口（防止基准漂移）。legacy 为旧的中心裁剪口径，仅作对照。",
              "provenance_note": "元件像素由 rebuild_reference_assets.py 从用户原图按 layout bbox 重取、套用旧切图的 alpha 轮廓，因此与参考图严格同源。像素相似度验证的是「101 个独立元件的位置/轮廓/颜色 1:1 对齐」，不是「脱离参考图独立重绘」；独立证据见 layout_integrity（Prefab 节点 bbox 与 sprite guid 逐项校验）。",
              "board_note": "s4 棋盘区在 Prefab 里是 alpha=0 的洞，运行时由 BoardView 按关卡数据渲染；验收图用用户原稿棋盘区占位以便同口径比对，占位不进入任何 Prefab / Resources。similarity_excluding_board 为剔除该占位区后的真实静态还原分。",
              "wiring": {"screen_map": BIND["screen_map"],
                         "hotspots": sum(len(c.get("hotspots", [])) for c in BIND["screens"].values()),
                         "dynamic_texts": sum(len(c.get("texts", [])) for c in BIND["screens"].values()),
                         "board_passthrough": True}}
    try:
        F = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 15)
        Fs = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 12)
    except Exception:
        F = Fs = ImageFont.load_default()

    thumbs = []
    for sid, spec in LAYOUT["screens"].items():
        made = render(sid, spec)
        made.save(OUT / "screens" / (sid + ".png"))
        orig_name = {"s1": "s1_loading", "s2": "s2_level", "s3": "s3_gallery",
                     "s4": "s4_game", "s5": "s5_complete", "s6": "s6_fail",
                     "s7": "s7_skin", "s8": "s8_daily", "s9": "s9_map"}[sid]
        op = ORIGINAL / (orig_name + ".png")
        score = legacy = None
        win = None
        if op.is_file():
            o = Image.open(op).convert("RGB")
            aligned, win = register_original(o, made, sid)
            score = similarity(aligned, made)
            legacy = similarity(center_crop_aligned(o, made.size[0], made.size[1]), made)
            thumbs.append((sid, aligned, made, score))
        exclude = None
        pt = BIND["screens"].get(sid, {}).get("passthrough")
        if pt:
            exclude = pt["rect"]
        static = similarity_excluding(aligned, made, exclude) if (op.is_file() and exclude) else score
        report["screens"][sid] = {"size": spec["size"], "items": len(spec["items"]),
                                  "alignment_window": win,
                                  "similarity_to_original": score,
                                  "similarity_excluding_board": static,
                                  "similarity_center_crop_legacy": legacy}
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "alignment_windows.json").write_text(
        json.dumps({k: v["alignment_window"] for k, v in report["screens"].items()},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    CW, CH, GAP = 156, 232, 12
    CELL_W, CELL_H = 2 * CW + GAP, CH + 26
    board = Image.new("RGB", (3 * CELL_W + 16, 3 * CELL_H + 44), (248, 246, 242))
    d = ImageDraw.Draw(board)
    d.text((10, 8), "用户原图（去白边配准）左 vs 运行时还原层（右） · 9 屏 1:1", font=F, fill=(60, 45, 35))
    d.text((10, 28), "元件像素由用户原图按 bbox 重取(保留alpha轮廓)；擦字+动态Text+s4挖空；窗口固化", font=Fs, fill=(120, 95, 75))
    for i, (sid, o, m, s) in enumerate(thumbs):
        cx, cy = 8 + (i % 3) * CELL_W, 44 + (i // 3) * CELL_H
        for col, im in enumerate((o, m)):
            t = im.copy()
            t.thumbnail((CW - 6, CH - 6), Image.LANCZOS)
            px = cx + col * (CW + GAP) + (CW - 6 - t.width) // 2
            py = cy + (CH - 6 - t.height) // 2
            board.paste(t, (px, py))
        d.text((cx, cy + CH - 2), "%s %s   相似度 %.3f" % (sid, SCREEN_NAMES[sid], s),
               font=Fs, fill=(90, 70, 55))
    board.save(OUT / "compare_9screens.png")
    print("结构问题:", len(problems), problems[:5])
    print("结构级独立校验: %d 个元件 / %d 问题" % (layout_checked, len(layout_problems)))
    for sid, v in report["screens"].items():
        print(" ", sid, v["size"], "元件", v["items"],
              "相似度", v["similarity_to_original"],
              "剔除棋盘占位", v["similarity_excluding_board"],
              "(旧口径", v["similarity_center_crop_legacy"], ")")
    print("对照板:", OUT / "compare_9screens.png")


if __name__ == "__main__":
    main()
