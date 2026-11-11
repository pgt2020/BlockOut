# -*- coding: utf-8 -*-
"""把用户参考图 9 屏按 bbox 1:1 还原成 Unity Prefab（editor-independent / 幂等）。

真源 : Assets/BlockOut/Resources/UI/Reference/reference_layout.json  —— 每屏 size / bg / 元件 bbox
       Tools/UIAuthoring/reference_bind.json                        —— 动态字段 / 热区 / 挖空
资源 : Reference/sprites|bg|tiles/*.png（元件级 RGBA，straight alpha）
输出 : Assets/BlockOut/Resources/Prefabs/UI/Reference/ReferenceS*.prefab

与 v6/v7 的根本区别：本脚本不做配色、形状、字号、留白的任何设计判断，
只把原图元件按 manifest bbox 摆成独立 UGUI Image 节点；背景插画单独一层。

运行时接线（BlockOutReferenceSkin）：
  · 视觉层置顶、所有元件 raycastTarget=0 → 业务 View / Controller 一行不改；
  · Hotspot_<bind> 透明热区按原图按钮 bbox 摆放，点击转发到业务 Button；
  · Dyn_<key> Text 节点镜像业务真实数值（切图里的静态数字已由 prepare 擦除）；
  · s4 棋盘区挖空，运行时真棋盘透出；
  · Letterbox 纯色衬底铺满全屏，解决原图 325:478 与手机 390:844 的比例差。

用法：python Tools/UIAuthoring/prepare_reference_skin.py
      python Tools/UIAuthoring/apply_reference_skin.py
"""
from pathlib import Path
import json
import math
import re
import uuid

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "Assets/BlockOut/Resources/UI/Reference"
OUT = ROOT / "Assets/BlockOut/Resources/Prefabs/UI/Reference"
LAYOUT = REF / "reference_layout.json"
BIND = Path(__file__).parent / "reference_bind.json"

# 现有工程里实测的 UGUI / 工程脚本 GUID
GUID_IMAGE = "fe87c0e1cc204ed48ad3b37840f39efc"       # UnityEngine.UI.Image
GUID_TEXT = "5f7201a12d95ffc409449d95f23cf332"         # UnityEngine.UI.Text
GUID_BUTTON = "4e29b1a8efbd4b44bb3f3716e73f07ff"       # UnityEngine.UI.Button
GUID_FONT = "fd593325a489afb46b970fe4942877e4"          # 工程内置中文字体
GUID_PAGE_LAYOUT = "f0ec713160a541789aa18448ee150c92"   # BlockOutPageLayout
GUID_SKIN = "00bb8f5a829a544ebe120a6999397f83"          # BlockOutReferenceSkin

PREFAB_META = """fileFormatVersion: 2
guid: {guid}
PrefabImporter:
  externalObjects: {{}}
  userData: ''
  assetBundleName: ''
  assetBundleVariant: ''
"""

HEADER = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
"""

SCREEN_NAMES = {
    "s1": "Loading", "s2": "Level", "s3": "Gallery", "s4": "Game",
    "s5": "Complete", "s6": "Fail", "s7": "Skin", "s8": "Daily", "s9": "Map",
}

CLASS_NAME = {"1": "GameObject", "224": "RectTransform",
              "222": "CanvasRenderer", "114": "MonoBehaviour"}


def locate_sprite(fname):
    for sub in ("sprites", "bg", "tiles"):
        if (REF / sub / fname).is_file():
            return sub + "/" + fname
    raise FileNotFoundError("原图资源缺失: " + fname)


def sprite_guid(rel):
    p = REF / rel
    if not p.is_file():
        raise FileNotFoundError("缺少还原资源: " + rel)
    m = re.search(r"guid: (\w+)", Path(str(p) + ".meta").read_text(encoding="utf-8-sig"))
    if not m:
        raise ValueError("资源缺 .meta / guid: " + rel)
    return m.group(1)


def unity_rgba(hex_color, alpha=1.0):
    h = hex_color.lstrip("#")
    return tuple(round(int(h[i:i + 2], 16) / 255.0, 4) for i in (0, 2, 4)) + (alpha,)


def letterbox_color(bg_file):
    """取背景图上下边缘的中位色作为留白衬底，保证与插画衔接不断层。"""
    a = np.asarray(Image.open(REF / "bg" / bg_file).convert("RGB"))
    band = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3)], axis=0)
    return tuple(int(v) for v in np.median(band, axis=0))


class Builder:
    """拼 Unity YAML 多文档；预分配 fileID，保证父子引用与重跑结果稳定。"""

    def __init__(self):
        self.docs = []
        self.next = 100000

    def alloc(self):
        self.next += 1
        return self.next

    def add(self, cls, fid, body):
        self.docs.append("--- !u!%s &%d\n%s:\n%s" % (cls, fid, CLASS_NAME[cls], body))

    @staticmethod
    def common(go):
        return ("  m_ObjectHideFlags: 0\n"
                "  m_CorrespondingSourceObject:\n    fileID: 0\n"
                "  m_PrefabInstance:\n    fileID: 0\n"
                "  m_PrefabAsset:\n    fileID: 0\n"
                "  m_GameObject:\n    fileID: %d\n" % go)

    def gameobject(self, name, comps, fid=None, active=1):
        go = fid if fid is not None else self.alloc()
        body = self.common(go) + "  serializedVersion: 6\n  m_Component:\n"
        for c in comps:
            body += "  - component:\n      fileID: %d\n" % c
        body += ("  m_Layer: 5\n  m_Name: %s\n  m_TagString: Untagged\n"
                 "  m_IsActive: %d\n" % (name, active))
        self.add("1", go, body)
        return go

    def rect(self, go, children, father, anchor_min=(0, 1), anchor_max=(0, 1),
             pivot=(0, 1), pos=(0, 0), size=(0, 0), fid=None, angle=0):
        rt = fid if fid is not None else self.alloc()
        z = math.sin(math.radians(-angle) / 2.0)
        w = math.cos(math.radians(-angle) / 2.0)
        body = self.common(go)
        body += ("  m_LocalRotation:\n    x: 0\n    y: 0\n    z: %.6f\n    w: %.6f\n"
                 "  m_LocalPosition:\n    x: 0\n    y: 0\n    z: 0\n"
                 "  m_LocalScale:\n    x: 1\n    y: 1\n    z: 1\n" % (z, w))
        if children:
            body += "  m_Children:\n"
            for c in children:
                body += "  - fileID: %d\n" % c
        else:
            body += "  m_Children: []\n"
        body += ("  m_Father:\n    fileID: %d\n"
                 "  m_LocalEulerAnglesHint:\n    x: 0\n    y: 0\n    z: 0\n"
                 "  m_AnchorMin:\n    x: %s\n    y: %s\n"
                 "  m_AnchorMax:\n    x: %s\n    y: %s\n"
                 "  m_AnchoredPosition:\n    x: %s\n    y: %s\n"
                 "  m_SizeDelta:\n    x: %s\n    y: %s\n"
                 "  m_Pivot:\n    x: %s\n    y: %s\n" % (
                     father, anchor_min[0], anchor_min[1], anchor_max[0], anchor_max[1],
                     pos[0], pos[1], size[0], size[1], pivot[0], pivot[1]))
        self.add("224", rt, body)
        return rt

    def renderer(self, go, fid=None):
        cr = fid if fid is not None else self.alloc()
        self.add("222", cr, self.common(go) + "  m_CullTransparentMesh: 1\n")
        return cr

    def image(self, go, sprite_rel=None, color=(1, 1, 1, 1), raycast=0, fid=None):
        cid = fid if fid is not None else self.alloc()
        sp = ("  m_Sprite:\n    fileID: 21300000\n    guid: %s\n    type: 3\n"
              % sprite_guid(sprite_rel)) if sprite_rel else "  m_Sprite:\n    fileID: 0\n"
        body = self.common(go)
        body += ("  m_Enabled: 1\n  m_EditorHideFlags: 0\n"
                 "  m_Script:\n    fileID: 11500000\n    guid: %s\n    type: 3\n"
                 "  m_Name: ''\n  m_EditorClassIdentifier: ''\n"
                 "  m_Material:\n    fileID: 0\n"
                 "  m_Color:\n    r: %.4f\n    g: %.4f\n    b: %.4f\n    a: %.4f\n"
                 "  m_RaycastTarget: %d\n  m_Maskable: 1\n"
                 "  m_OnCullStateChanged:\n    m_PersistentCalls:\n      m_Calls: []\n"
                 "%s"
                 "  m_Type: 0\n  m_PreserveAspect: 0\n  m_FillCenter: 1\n"
                 "  m_FillMethod: 0\n  m_FillAmount: 1\n  m_FillClockwise: 1\n"
                 "  m_FillOrigin: 0\n  m_UseSpriteMesh: 0\n  m_PixelsPerUnitMultiplier: 1\n" % (
                     GUID_IMAGE, color[0], color[1], color[2], color[3], raycast, sp))
        self.add("114", cid, body)
        return cid

    def text(self, go, content, size, rgba, fid=None):
        cid = fid if fid is not None else self.alloc()
        body = self.common(go)
        body += ("  m_Enabled: 1\n  m_EditorHideFlags: 0\n"
                 "  m_Script:\n    fileID: 11500000\n    guid: %s\n    type: 3\n"
                 "  m_Name: ''\n  m_EditorClassIdentifier: ''\n"
                 "  m_Material:\n    fileID: 0\n"
                 "  m_Color:\n    r: %.4f\n    g: %.4f\n    b: %.4f\n    a: %.4f\n"
                 "  m_RaycastTarget: 0\n  m_Maskable: 1\n"
                 "  m_FontData:\n    m_Font:\n      fileID: 12800000\n      guid: %s\n      type: 3\n"
                 "    m_FontSize: %d\n    m_FontStyle: 1\n    m_BestFit: 0\n"
                 "    m_MinSize: 8\n    m_MaxSize: %d\n    m_Alignment: 4\n"
                 "    m_AlignByGeometry: 0\n    m_RichText: 1\n"
                 "    m_HorizontalOverflow: 1\n    m_VerticalOverflow: 1\n    m_LineSpacing: 1\n"
                 "  m_Text: \"%s\"\n" % (
                     GUID_TEXT, rgba[0], rgba[1], rgba[2], rgba[3],
                     GUID_FONT, size, size, content.replace("\\", "\\\\").replace('"', '\\"')))
        self.add("114", cid, body)
        return cid

    def button(self, go, target_img, fid=None):
        cid = fid if fid is not None else self.alloc()
        body = self.common(go)
        body += ("  m_Enabled: 1\n  m_EditorHideFlags: 0\n"
                 "  m_Script:\n    fileID: 11500000\n    guid: %s\n    type: 3\n"
                 "  m_Name: ''\n  m_EditorClassIdentifier: ''\n"
                 "  m_Navigation:\n    m_Mode: 0\n    m_WrapAround: 0\n"
                 "    m_SelectOnUp:\n      fileID: 0\n    m_SelectOnDown:\n      fileID: 0\n"
                 "    m_SelectOnLeft:\n      fileID: 0\n    m_SelectOnRight:\n      fileID: 0\n"
                 "  m_Transition: 0\n  m_Colors:\n"
                 "    m_NormalColor:\n      r: 1\n      g: 1\n      b: 1\n      a: 1\n"
                 "    m_HighlightedColor:\n      r: 1\n      g: 1\n      b: 1\n      a: 1\n"
                 "    m_PressedColor:\n      r: 1\n      g: 1\n      b: 1\n      a: 1\n"
                 "    m_SelectedColor:\n      r: 1\n      g: 1\n      b: 1\n      a: 1\n"
                 "    m_DisabledColor:\n      r: 1\n      g: 1\n      b: 1\n      a: 1\n"
                 "    m_ColorMultiplier: 1\n    m_FadeDuration: 0.1\n"
                 "  m_Interactable: 1\n  m_TargetGraphic:\n    fileID: %d\n"
                 "  m_OnClick:\n    m_PersistentCalls:\n      m_Calls: []\n" % (GUID_BUTTON, target_img))
        self.add("114", cid, body)
        return cid

    def page_layout(self, go, surface_rt, w, h, fid=None):
        cid = fid if fid is not None else self.alloc()
        body = self.common(go)
        body += ("  m_Enabled: 1\n  m_EditorHideFlags: 0\n"
                 "  m_Script:\n    fileID: 11500000\n    guid: %s\n    type: 3\n"
                 "  m_Name: ''\n  m_EditorClassIdentifier: ''\n"
                 "  Surface:\n    fileID: %d\n  DesignSize:\n    x: %d\n    y: %d\n"
                 "  RespectSafeArea: 1\n" % (GUID_PAGE_LAYOUT, surface_rt, w, h))
        self.add("114", cid, body)
        return cid

    def skin(self, go, sid, passthrough, fid=None):
        cid = fid if fid is not None else self.alloc()
        body = self.common(go)
        body += ("  m_Enabled: 1\n  m_EditorHideFlags: 0\n"
                 "  m_Script:\n    fileID: 11500000\n    guid: %s\n    type: 3\n"
                 "  m_Name: ''\n  m_EditorClassIdentifier: ''\n"
                 "  ScreenId: %s\n  PassthroughBoard: %d\n" % (
                     GUID_SKIN, sid, 1 if passthrough else 0))
        self.add("114", cid, body)
        return cid

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(HEADER + "\n".join(self.docs), encoding="utf-8")
        mp = Path(str(path) + ".meta")
        if not mp.is_file() or not re.search(r"guid:", mp.read_text(encoding="utf-8-sig", errors="ignore")):
            g = uuid.uuid5(uuid.NAMESPACE_URL, "blockout-ref-prefab:" + path.name).hex
            mp.write_text(PREFAB_META.format(guid=g), encoding="utf-8")


def build_screen(sid, spec, cfg, data):
    W, H = spec["size"]
    b = Builder()
    passthrough = bool(cfg.get("passthrough"))
    texts = cfg.get("texts", [])
    hotspots = cfg.get("hotspots", [])
    hearts = cfg.get("hearts")
    items = {it["name"]: it for it in spec["items"]}

    # 动态字段对应的元件图改用擦过数字的变体
    dyn_file = {}
    for f in texts:
        fn = items[f["item"]]["file"]
        stem = Path(fn).stem + "_dyn" + Path(fn).suffix
        dyn_file[f["item"]] = "sprites/" + stem

    # s4 挖空背景
    bg_rel = "bg/" + (cfg["passthrough"]["bg_out"] if passthrough else spec["bg"])
    lb = letterbox_color(spec["bg"])

    # ---- 预分配所有 fileID ----
    root_go, root_rt, layout_cid, skin_cid = b.alloc(), b.alloc(), b.alloc(), b.alloc()
    lb_go, lb_rt, lb_cr, lb_img = b.alloc(), b.alloc(), b.alloc(), b.alloc()
    surf_go, surf_rt, surf_cr, surf_img = b.alloc(), b.alloc(), b.alloc(), b.alloc()
    skin_go, skin_rt = b.alloc(), b.alloc()
    bg_go, bg_rt, bg_cr, bg_img = b.alloc(), b.alloc(), b.alloc(), b.alloc()

    nodes = []
    for it in spec["items"]:
        if hearts and it["name"] == hearts["item"]:
            continue
        nodes.append({"it": it, "go": b.alloc(), "rt": b.alloc(),
                      "cr": b.alloc(), "img": b.alloc()})

    heart_nodes = []
    if hearts:
        src = items[hearts["item"]]
        step = src["w"] / hearts["count"]
        for i in range(hearts["count"]):
            heart_nodes.append({"x": src["x"] + i * step, "y": src["y"],
                                "w": step, "h": src["h"],
                                "go": b.alloc(), "rt": b.alloc(),
                                "cr": b.alloc(), "img": b.alloc()})

    # 非 passthrough 屏才生成组件化棋盘格（s4 挖空后由运行时真棋盘接管）
    board_cells = []
    tiles = data["tilekit"]
    if sid == "s4" and not passthrough:
        grid, pal = tiles["grid"], tiles["palette"]
        for row in tiles["board"]:
            for cell in row:
                if cell["color"] is None and cell["dir"] == "none":
                    continue
                board_cells.append({
                    "x": grid["x"] + cell["c"] * grid["size"],
                    "y": grid["y"] + cell["r"] * grid["size"],
                    "s": grid["size"], "r": cell["r"], "c": cell["c"],
                    "angle": tiles["rotation"].get(cell["dir"], 0), "dir": cell["dir"],
                    "go": b.alloc(), "rt": b.alloc(), "cr": b.alloc(), "img": b.alloc(),
                    "arrow_go": b.alloc(), "arrow_rt": b.alloc(),
                    "arrow_cr": b.alloc(), "arrow_img": b.alloc(),
                })

    hot_nodes = []
    for hp in hotspots:
        it = items.get(hp["item"])
        if not it:
            continue
        hot_nodes.append({"bind": hp["bind"], "it": it, "go": b.alloc(), "rt": b.alloc(),
                          "cr": b.alloc(), "img": b.alloc(), "btn": b.alloc()})

    dyn_nodes = []
    for f in texts:
        it = items[f["item"]]
        x0, y0, bw, bh = f["box"]
        dyn_nodes.append({"f": f, "x": it["x"] + x0, "y": it["y"] + y0,
                          "w": bw, "h": bh,
                          "go": b.alloc(), "rt": b.alloc(), "cr": b.alloc(), "txt": b.alloc()})

    skin_children = ([bg_rt]
                     + [h["rt"] for h in heart_nodes]
                     + [c["rt"] for c in board_cells]
                     + [n["rt"] for n in nodes]
                     + [h["rt"] for h in hot_nodes]
                     + [d["rt"] for d in dyn_nodes])

    # ---- 文档 ----
    name = "ReferenceS%s_%s" % (sid[1:], SCREEN_NAMES[sid])
    b.gameobject(name, [root_rt, layout_cid, skin_cid], fid=root_go)
    b.rect(root_go, [lb_rt, surf_rt], 0, anchor_min=(0, 0), anchor_max=(1, 1),
           pivot=(0.5, 0.5), size=(0, 0), fid=root_rt)
    b.page_layout(root_go, surf_rt, W, H, fid=layout_cid)
    b.skin(root_go, sid, passthrough, fid=skin_cid)

    # 纯色衬底：铺满全屏，解决原图与手机比例差带来的上下留白
    b.gameobject("Letterbox", [lb_rt, lb_cr, lb_img], fid=lb_go)
    b.rect(lb_go, [], root_rt, anchor_min=(0, 0), anchor_max=(1, 1),
           pivot=(0.5, 0.5), size=(0, 0), fid=lb_rt)
    b.renderer(lb_go, fid=lb_cr)
    b.image(lb_go, None, color=unity_rgba("#%02X%02X%02X" % lb), fid=lb_img)

    b.gameobject("DesignSurface", [surf_rt, surf_cr, surf_img], fid=surf_go)
    b.rect(surf_go, [skin_rt], root_rt, anchor_min=(0.5, 0.5), anchor_max=(0.5, 0.5),
           pivot=(0.5, 0.5), size=(W, H), fid=surf_rt)
    b.renderer(surf_go, fid=surf_cr)
    b.image(surf_go, None, color=(1, 1, 1, 0), fid=surf_img)

    b.gameobject("ReferenceSkin", [skin_rt], fid=skin_go)
    b.rect(skin_go, skin_children, surf_rt, anchor_min=(0, 0), anchor_max=(1, 1),
           pivot=(0.5, 0.5), size=(0, 0), fid=skin_rt)

    b.gameobject("Background", [bg_rt, bg_cr, bg_img], fid=bg_go)
    b.rect(bg_go, [], skin_rt, pos=(0, 0), size=(W, H), fid=bg_rt)
    b.renderer(bg_go, fid=bg_cr)
    b.image(bg_go, bg_rel, fid=bg_img)

    # 元件层：bbox 原样搬，x/y/w/h 不做任何微调
    for n in nodes:
        it = n["it"]
        b.gameobject(it["name"], [n["rt"], n["cr"], n["img"]], fid=n["go"])
        b.rect(n["go"], [], skin_rt, pos=(it["x"], -it["y"]),
               size=(it["w"], it["h"]), fid=n["rt"])
        b.renderer(n["go"], fid=n["cr"])
        rel = dyn_file.get(it["name"]) or locate_sprite(it["file"])
        b.image(n["go"], rel, fid=n["img"])

    # 心形组件：4 颗独立 Image，运行时按生命数切 on/off
    for i, h in enumerate(heart_nodes):
        b.gameobject("Heart_%d" % i, [h["rt"], h["cr"], h["img"]], fid=h["go"])
        b.rect(h["go"], [], skin_rt, pos=(h["x"], -h["y"]),
               size=(h["w"], h["h"]), fid=h["rt"])
        b.renderer(h["go"], fid=h["cr"])
        rel = "tiles/" + (hearts["on"] if i < 3 else hearts["off"])
        b.image(h["go"], rel, fid=h["img"])

    # 组件化棋盘格（仅未挖空的屏）
    for c in board_cells:
        b.gameobject("tile_r%dc%d" % (c["r"], c["c"]),
                     [c["rt"], c["cr"], c["img"]], fid=c["go"])
        b.rect(c["go"], [c["arrow_rt"]] if c["dir"] != "none" else [], skin_rt,
               pos=(c["x"], -c["y"]), size=(c["s"], c["s"]), fid=c["rt"])
        b.renderer(c["go"], fid=c["cr"])
        b.image(c["go"], "tiles/tile_base.png", fid=c["img"])
        if c["dir"] != "none":
            arrow = "tiles/arrow_cross.png" if c["dir"] == "cross" else "tiles/arrow_up.png"
            b.gameobject("arrow", [c["arrow_rt"], c["arrow_cr"], c["arrow_img"]], fid=c["arrow_go"])
            aw = int(round(c["s"] * 0.66))
            b.rect(c["arrow_go"], [], c["rt"], anchor_min=(0.5, 0.5), anchor_max=(0.5, 0.5),
                   pivot=(0.5, 0.5), pos=(0, 0), size=(aw, aw), fid=c["arrow_rt"],
                   angle=c["angle"])
            b.renderer(c["arrow_go"], fid=c["arrow_cr"])
            b.image(c["arrow_go"], arrow, fid=c["arrow_img"])

    # 透明热区：唯一 raycastTarget=1 的节点，点击转发到业务 Button
    for h in hot_nodes:
        it = h["it"]
        b.gameobject("Hotspot_" + h["bind"], [h["rt"], h["cr"], h["img"], h["btn"]], fid=h["go"])
        b.rect(h["go"], [], skin_rt, pos=(it["x"], -it["y"]),
               size=(it["w"], it["h"]), fid=h["rt"])
        b.renderer(h["go"], fid=h["cr"])
        b.image(h["go"], None, color=(1, 1, 1, 0), raycast=1, fid=h["img"])
        b.button(h["go"], h["img"], fid=h["btn"])

    # 动态文字层：最顶，镜像业务真实数值
    for d in dyn_nodes:
        f = d["f"]
        b.gameobject("Dyn_" + f["key"], [d["rt"], d["cr"], d["txt"]], fid=d["go"])
        b.rect(d["go"], [], skin_rt, pos=(d["x"], -d["y"]),
               size=(d["w"], d["h"]), fid=d["rt"])
        b.renderer(d["go"], fid=d["cr"])
        b.text(d["go"], f["text"], f["size"], unity_rgba(f["color"]), fid=d["txt"])

    return b, len(nodes), len(board_cells), len(hot_nodes), len(dyn_nodes)


def main():
    data = json.loads(LAYOUT.read_text(encoding="utf-8"))
    bind = json.loads(BIND.read_text(encoding="utf-8"))
    tot = [0, 0, 0, 0]
    for sid, spec in data["screens"].items():
        cfg = bind["screens"].get(sid, {"hotspots": [], "texts": []})
        b, ni, nc, nh, nd = build_screen(sid, spec, cfg, data)
        path = OUT / ("ReferenceS%s_%s.prefab" % (sid[1:], SCREEN_NAMES[sid]))
        b.save(path)
        tot[0] += ni; tot[1] += nc; tot[2] += nh; tot[3] += nd
        print("%s -> %-26s %dx%d | 元件 %2d 格 %2d 热区 %d 动态 %d | 文档 %d" % (
            sid, path.name, spec["size"][0], spec["size"][1], ni, nc, nh, nd, len(b.docs)))
    print("合计 9 屏 | 元件 %d 棋盘格 %d 热区 %d 动态文字 %d" % tuple(tot))


if __name__ == "__main__":
    main()
