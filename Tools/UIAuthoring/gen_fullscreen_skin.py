# -*- coding: utf-8 -*-
"""整屏贴图还原（用户选 1 方案）：原图整张铺满，透明热区管点击。

与 apply_reference_skin.py 的根本区别：
  · 不再把原图切成几十个元件 → 不切、不擦字、不挖空、不动态镜像；
  · ReferenceSkin 下只有 1 个 FullImage(整张原图) + N 个透明 Hotspot；
  · 因此像素级 = 原图本身，细节 100% 等于第一版设计。

真源 : DesignAssets/UI_v7/reference_original/s1..s9（用户第一版原图）
热区 : reference_bind.json 的 hotspots + reference_layout.json 的 bbox
输出 : Resources/Prefabs/UI/Reference/ReferenceS*.prefab（固定加载路径，覆盖前先备份）

用法：python Tools/UIAuthoring/gen_fullscreen_skin.py
"""
from pathlib import Path
import sys
import uuid

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import apply_reference_skin as A  # 复用 Builder / 常量 / GUID

ROOT = A.ROOT
REF = A.REF
ORIG = ROOT / "DesignAssets" / "UI_v7" / "reference_original"
FULL = REF / "fullscreen"
OUT = A.OUT

ORIG_FILES = {
    "s1": "s1_loading.png", "s2": "s2_level.png", "s3": "s3_gallery.png",
    "s4": "s4_game.png", "s5": "s5_complete.png", "s6": "s6_fail.png",
    "s7": "s7_skin.png", "s8": "s8_daily.png", "s9": "s9_map.png",
}

META_TPL = """fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
  externalObjects: {{}}
  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 0
    sRGBTexture: 1
    linearTexture: 0
    fadeOut: 0
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  bumpmap:
    convertToNormalMap: 0
  isReadable: 0
  streamingMipmaps: 0
  streamingMipmapsPriority: 0
  vTOnly: 0
  grayScaleToAlpha: 0
  generateCubemap: 6
  cubemapConvolution: 0
  seamlessCubemap: 0
  textureFormat: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 1
    mipBias: 0
    wrapU: 1
    wrapV: 1
    wrapW: 0
  nPOTScale: 0
  lightmap: 0
  compressionQuality: 50
  spriteMode: 1
  spriteExtrude: 1
  spriteMeshType: 1
  alignment: 0
  spritePivot: {{x: 0.5, y: 0.5}}
  spritePixelsToUnits: 100
  alphaUsage: 1
  alphaIsTransparency: 1
  spriteTessellationDetail: -1
  textureType: 8
  textureShape: 1
  spriteSheet:
    serializedVersion: 2
    sprites: []
  platformSettings: []
"""


def ensure_sprite_meta(path):
    mp = Path(str(path) + ".meta")
    if mp.is_file() and "guid:" in mp.read_text(encoding="utf-8-sig", errors="ignore"):
        return mp.read_text(encoding="utf-8-sig").strip()
    g = uuid.uuid5(uuid.NAMESPACE_URL, "blockout-fullscreen:" + path.name).hex
    txt = META_TPL.format(guid=g)
    mp.write_text(txt, encoding="utf-8")
    return txt


def prepare_images():
    """把第一版原图原样复制到 Resources/fullscreen/ 并生成 sprite meta。零处理。"""
    FULL.mkdir(parents=True, exist_ok=True)
    sizes = {}
    for sid, fn in ORIG_FILES.items():
        src = ORIG / fn
        if not src.is_file():
            raise FileNotFoundError("第一版原图缺失: " + str(src))
        dst = FULL / (sid + ".png")
        # 直接复制字节，不做任何缩放/重采样/擦字
        dst.write_bytes(src.read_bytes())
        ensure_sprite_meta(dst)
        im = Image.open(dst)
        sizes[sid] = im.size
        print("prepare", sid, fn, "->", sid + ".png", im.size)
    return sizes


def letterbox_color(path):
    a = np.asarray(Image.open(path).convert("RGB"))
    band = np.concatenate([a[:8].reshape(-1, 3), a[-8:].reshape(-1, 3)], axis=0)
    return tuple(int(v) for v in np.median(band, axis=0))


# 目标画布比例 = 实机 1125x2436 ≈ 0.462；用 390x844 逻辑坐标，整图 stretch 铺满全屏。
FILL_W, FILL_H = 390, 844


def build_screen(sid, layout, bind, sizes):
    spec = layout["screens"][sid]
    cfg = bind["screens"][sid]
    ow, oh = sizes[sid]
    dw, dh = spec["size"]                     # 设计坐标 325x478 / 470x836
    items = {it["name"]: it for it in spec["items"]}
    lb = letterbox_color(FULL / (sid + ".png"))

    b = A.Builder()
    root_go, root_rt, layout_cid, skin_cid = b.alloc(), b.alloc(), b.alloc(), b.alloc()
    lb_go, lb_rt, lb_cr, lb_img = b.alloc(), b.alloc(), b.alloc(), b.alloc()
    surf_go, surf_rt, surf_cr, surf_img = b.alloc(), b.alloc(), b.alloc(), b.alloc()
    skin_go, skin_rt = b.alloc(), b.alloc()
    img_go, img_rt, img_cr, img_img = b.alloc(), b.alloc(), b.alloc(), b.alloc()

    # 透明热区：设计坐标(dw×dh) bbox 按比例映射到铺满画布(FILL_W×FILL_H)
    fx, fy = FILL_W / dw, FILL_H / dh
    hot_nodes = []
    for hp in cfg.get("hotspots", []):
        it = items.get(hp["item"])
        if not it:
            continue
        hx, hy = it["x"] * fx, it["y"] * fy
        hw, hh = it["w"] * fx, it["h"] * fy
        hot_nodes.append({"bind": hp["bind"], "x": hx, "y": hy, "w": hw, "h": hh,
                          "go": b.alloc(), "rt": b.alloc(), "cr": b.alloc(),
                          "img": b.alloc(), "btn": b.alloc()})

    skin_children = [img_rt] + [n["rt"] for n in hot_nodes]

    name = "ReferenceS%s_%s" % (sid[1:], A.SCREEN_NAMES[sid])

    # Root：挂 PageLayout + ReferenceSkin，铺满父容器
    b.gameobject(name, [root_rt, layout_cid, skin_cid], fid=root_go)
    b.rect(root_go, [lb_rt, surf_rt], 0, anchor_min=(0, 0), anchor_max=(1, 1),
           pivot=(0.5, 0.5), size=(0, 0), fid=root_rt)
    b.page_layout(root_go, surf_rt, FILL_W, FILL_H, fid=layout_cid)
    b.skin(root_go, sid, False, fid=skin_cid)   # 不做 passthrough：整图自带棋盘

    # Letterbox：原图上下边缘中位色，铺满全屏，填充比例差留白
    b.gameobject("Letterbox", [lb_rt, lb_cr, lb_img], fid=lb_go)
    b.rect(lb_go, [], root_rt, anchor_min=(0, 0), anchor_max=(1, 1),
           pivot=(0.5, 0.5), size=(0, 0), fid=lb_rt)
    b.renderer(lb_go, fid=lb_cr)
    b.image(lb_go, None, color=A.unity_rgba("#%02X%02X%02X" % lb), fid=lb_img)

    # DesignSurface：铺满画布(390x844)，PageLayout 按安全区等比缩放，无上下大留白
    b.gameobject("DesignSurface", [surf_rt, surf_cr, surf_img], fid=surf_go)
    b.rect(surf_go, [skin_rt], root_rt, anchor_min=(0.5, 0.5), anchor_max=(0.5, 0.5),
           pivot=(0.5, 0.5), size=(FILL_W, FILL_H), fid=surf_rt)
    b.renderer(surf_go, fid=surf_cr)
    b.image(surf_go, None, color=(1, 1, 1, 0), fid=surf_img)

    # ReferenceSkin 容器：铺满 DesignSurface
    b.gameobject("ReferenceSkin", [skin_rt], fid=skin_go)
    b.rect(skin_go, skin_children, surf_rt, anchor_min=(0, 0), anchor_max=(1, 1),
           pivot=(0.5, 0.5), size=(0, 0), fid=skin_rt)

    # FullImage：整张原图 stretch 铺满画布，零切片、零留白；raycast 关闭不吞点击
    b.gameobject("FullImage", [img_rt, img_cr, img_img], fid=img_go)
    b.rect(img_go, [], skin_rt, anchor_min=(0, 0), anchor_max=(1, 1),
           pivot=(0.5, 0.5), pos=(0, 0), size=(0, 0), fid=img_rt)
    b.renderer(img_go, fid=img_cr)
    b.image(img_go, "fullscreen/" + sid + ".png", fid=img_img)

    # 透明热区：透明 Image(raycast=1) + Button，叠在原按钮位置
    for n in hot_nodes:
        b.gameobject("Hotspot_" + n["bind"],
                     [n["rt"], n["cr"], n["img"], n["btn"]], fid=n["go"])
        b.rect(n["go"], [], skin_rt, pos=(n["x"], -n["y"]),
               size=(n["w"], n["h"]), fid=n["rt"])
        b.renderer(n["go"], fid=n["cr"])
        b.image(n["go"], None, color=(1, 1, 1, 0.01), raycast=1, fid=n["img"])
        b.button(n["go"], n["img"], fid=n["btn"])

    b.save(OUT / (name + ".prefab"))
    print("build", sid, name, "fullsize", (ow, oh), "hotspots", len(hot_nodes))


def main():
    layout = A.json.loads((A.LAYOUT).read_text(encoding="utf-8-sig"))
    bind = A.json.loads((A.BIND).read_text(encoding="utf-8-sig"))
    sizes = prepare_images()
    for sid in ORIG_FILES:
        build_screen(sid, layout, bind, sizes)
    print("DONE: 9 fullscreen prefabs ->", OUT)


if __name__ == "__main__":
    main()
