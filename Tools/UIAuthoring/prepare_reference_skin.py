# -*- coding: utf-8 -*-
"""还原层资源预处理：擦掉烧死在切图里的动态数字、拆分心形组件、s4 棋盘挖空。

真源 : reference_layout.json（bbox） + reference_bind.json（字段/热区/挖空）
输入 : Resources/UI/Reference/sprites|bg|tiles 下从旧包导入的元件级 RGBA 切图
输出 : 同目录下的 *_dyn.png / heart_on|off.png / s4_hud.png，并为新资源补 .meta

不覆盖任何原始切图 —— 用户原图资产保持只读，重跑幂等。
"""
from pathlib import Path
import json
import re
import uuid

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "Assets/BlockOut/Resources/UI/Reference"
LAYOUT = json.loads((REF / "reference_layout.json").read_text(encoding="utf-8"))
BIND = json.loads((Path(__file__).parent / "reference_bind.json").read_text(encoding="utf-8"))

META = """fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
  externalObjects: {{}}
  serializedVersion: 12
  mipmaps:
    enableMipMap: 0
  isReadable: 0
  textureType: 8
  textureShape: 1
  sRGBTexture: 1
  alphaIsTransparency: 1
  spriteMode: 1
  spritePixelsToUnits: 100
  spriteMeshType: 1
  spriteAlignment: 0
  spritePivot:
    x: 0.5
    y: 0.5
  spriteBorder:
    x: 0
    y: 0
    z: 0
    w: 0
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 1
    mipBias: 0
    wrapU: 1
    wrapV: 1
    wrapW: 1
  maxTextureSize: 2048
  nPOTScale: 0
  spriteSheet:
    serializedVersion: 2
    sprites: []
    outline: []
    physicsShape: []
    bones: []
    spriteID: {sid}
    internalID: 0
    vertices: []
    indices: ''
    edges: []
    weights: []
    secondaryTextures: []
    nameFileIdTable: {{}}
  platformSettings: []
  userData: ''
  assetBundleName: ''
  assetBundleVariant: ''
"""


def ensure_meta(path):
    mp = Path(str(path) + ".meta")
    if mp.is_file() and re.search(r"guid:\s*\w+", mp.read_text(encoding="utf-8-sig", errors="ignore")):
        return
    key = path.relative_to(REF).as_posix()
    g = uuid.uuid5(uuid.NAMESPACE_URL, "blockout-ref:" + key).hex
    sid = uuid.uuid5(uuid.NAMESPACE_URL, "blockout-ref-sprite:" + g).hex
    mp.write_text(META.format(guid=g, sid=sid), encoding="utf-8")


def find(fname):
    for sub in ("sprites", "bg", "tiles"):
        p = REF / sub / fname
        if p.is_file():
            return p
    raise FileNotFoundError(fname)


def erase_ink(im, box, ink_hex):
    """只擦文字笔画，不擦底板。

    早期版本对整块 box 做左右插值，遇到「数字画在绿色圆形按钮中央」这类结构
    会把整块底色抹成边缘色（s9 第 37 关的绿圆被抹白）。这里改为：
      ① 按字段的 Text 颜色（ink）在 box 内找文字像素；
      ② 3×3 膨胀两次，连带吃掉描边与抗锯齿软边；
      ③ 逐行用同一行的非文字像素做线性插值回填，保留底板渐变。
    """
    a = np.asarray(im.convert("RGBA")).copy()
    H, W = a.shape[:2]
    x0, y0, bw, bh = box
    x1, y1 = min(W, x0 + bw), min(H, y0 + bh)
    x0, y0 = max(0, x0), max(0, y0)
    if x1 <= x0 or y1 <= y0:
        return im
    h = ink_hex.lstrip("#")
    ink = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)
    reg = a[y0:y1, x0:x1]
    rgb = reg[:, :, :3].astype(float)
    dist = np.sqrt(((rgb - ink[None, None, :]) ** 2).sum(2))
    m = dist < 78
    for _ in range(2):
        p = np.pad(m, 1, mode="edge")
        m = (p[:-2, :-2] | p[:-2, 1:-1] | p[:-2, 2:] |
             p[1:-1, :-2] | p[1:-1, 1:-1] | p[1:-1, 2:] |
             p[2:, :-2] | p[2:, 1:-1] | p[2:, 2:])
    for yy in range(y1 - y0):
        row = reg[yy]
        good = ~m[yy]
        bad = np.where(m[yy])[0]
        if good.sum() < 2 or len(bad) == 0:
            continue
        idx = np.where(good)[0]
        for ch in range(3):
            row[bad, ch] = np.interp(bad, idx, row[idx, ch].astype(float)).astype(np.uint8)
    a[:, :, :3][a[:, :, 3] == 0] = 0
    return Image.fromarray(a, "RGBA")


def dyn_name(fname):
    p = Path(fname)
    return p.stem + "_dyn" + p.suffix


def prepare_dynamic():
    """为每个动态字段生成一张擦过数字的变体图，不改原图。"""
    made = {}
    for sid, cfg in BIND["screens"].items():
        items = {it["name"]: it for it in LAYOUT["screens"][sid]["items"]}
        groups = {}
        for f in cfg.get("texts", []):
            groups.setdefault(f["item"], []).append(f)
        for item_name, fields in groups.items():
            it = items[item_name]
            dst = REF / "sprites" / dyn_name(it["file"])
            # 每次都从原始切图起算：多字段可累积，重跑幂等
            im = Image.open(find(it["file"])).convert("RGBA")
            for f in fields:
                im = erase_ink(im, f["box"], f["color"])
            im.save(dst)
            ensure_meta(dst)
            made[(sid, item_name)] = dst.name
    return made


def prepare_hearts():
    sid, cfg = "s4", BIND["screens"]["s4"]
    hc = cfg["hearts"]
    it = next(i for i in LAYOUT["screens"][sid]["items"] if i["name"] == hc["item"])
    src = find(it["file"])
    im = Image.open(src).convert("RGBA")
    W, H = im.size
    step = W / hc["count"]
    on = im.crop((0, 0, int(round(step)), H))
    off = im.crop((int(round(step * (hc["count"] - 1))), 0, W, H))
    for img, name in ((on, hc["on"]), (off, hc["off"])):
        p = REF / "tiles" / name
        img.save(p)
        ensure_meta(p)
    return hc


def prepare_passthrough():
    """s4：把棋盘区域从背景里挖成透明，运行时真棋盘才能透出来。"""
    sid, cfg = "s4", BIND["screens"]["s4"]
    pt = cfg["passthrough"]
    spec = LAYOUT["screens"][sid]
    src = find(spec["bg"])
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).copy()
    x, y, w, h = pt["rect"]
    H, W = a.shape[:2]
    x1, y1 = min(W, x + w), min(H, y + h)
    # 中心全挖空、四边 3px 羽化，避免锯齿轮廓。
    # 注意方向：早期版本写成 alpha *= (1 - keep) 正好反了，把中心留成不透明，
    # 结果整张背景盖住真棋盘 —— 这是 s4 验收图棋盘空白的根因。
    fh, fw = y1 - y, x1 - x
    cut = np.ones((fh, fw), dtype=float)
    feather = 3
    for k in range(feather):
        v = (k + 1) / (feather + 1)
        cut[k, :] = np.minimum(cut[k, :], v)
        cut[-(k + 1), :] = np.minimum(cut[-(k + 1), :], v)
        cut[:, k] = np.minimum(cut[:, k], v)
        cut[:, -(k + 1)] = np.minimum(cut[:, -(k + 1)], v)
    alpha = a[:, :, 3].astype(float)
    alpha[y:y1, x:x1] *= (1 - cut)
    a[:, :, 3] = alpha.astype(np.uint8)
    a[:, :, :3][a[:, :, 3] == 0] = 0
    out = REF / "bg" / pt["bg_out"]
    Image.fromarray(a, "RGBA").save(out)
    ensure_meta(out)
    return out


def normalize_all():
    """straight alpha 铁律：alpha=0 的像素 RGB 必须清零，否则 JPEG 预览 /
    Unity 纹理压缩 / 双线性采样都会渗出米色底板。旧包导入的 102 张切图
    透明区残留了近白底色（RGB 均值 ~200），这里统一归一，重跑幂等。
    """
    fixed = edge_white = 0
    for p in sorted(REF.rglob("*.png")):
        a = np.asarray(Image.open(p).convert("RGBA")).copy()
        al = a[:, :, 3]
        dirty = (al == 0) & (a[:, :, :3].max(2) > 0)
        if dirty.any():
            fixed += 1
        al[al < 6] = 0
        a[:, :, 3] = al
        # 半透明抗锯齿边若被白底污染，用同行最近的不透明前景色回填。
        # 注意：sprites/ 与 bg/ 下的元件已由 rebuild_reference_assets.py 从
        # 用户原图重取 RGB，其半透明边本就是「前景+背景」的正确混合色，
        # 再回填反而会把软边改成硬色、破坏 1:1。这里只修旧的组件化方块资源。
        edge = (al > 0) & (al < 250)
        legacy_tile = p.parent.name == "tiles" and not p.name.startswith("heart_")
        if legacy_tile and edge.any() and a[:, :, :3][edge].mean() > 218:
            solid = (al >= 250)
            for y in range(a.shape[0]):
                idx = np.where(solid[y])[0]
                bad = np.where(edge[y])[0]
                if len(idx) == 0 or len(bad) == 0:
                    continue
                for ch in range(3):
                    a[y, bad, ch] = np.interp(bad, idx, a[y, idx, ch].astype(float)).astype(np.uint8)
            edge_white += 1
        a[:, :, :3][al == 0] = 0
        Image.fromarray(a, "RGBA").save(p)
    return fixed, edge_white


def main():
    dyn = prepare_dynamic()
    hc = prepare_hearts()
    out = prepare_passthrough()
    fixed, edge_white = normalize_all()
    print("动态字段擦除变体: %d 张" % len(dyn))
    for (sid, item), fn in dyn.items():
        print("  %s / %s -> %s" % (sid, item, fn))
    print("心形组件: %s, %s (%d 颗)" % (hc["on"], hc["off"], hc["count"]))
    print("s4 挖空背景: bg/%s" % out.name)
    print("straight-alpha 归一: 修 %d 张透明区残留 / %d 张抗锯齿白边" % (fixed, edge_white))


if __name__ == "__main__":
    main()
