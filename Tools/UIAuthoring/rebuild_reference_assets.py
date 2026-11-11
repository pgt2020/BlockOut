# -*- coding: utf-8 -*-
"""把还原层元件像素重新对齐到「用户原图」——消除旧切图与参考图的色偏/错位。

背景与问题
----------
旧包 UI_v7_切图与9屏实现.zip 里的 98 张元件切图，当年是从 1536x1024 拼版里
拆出的 325x478 小图裁出来的；用户后来单独提供的 reference_original/*.png 是
384x512 的另一份版本。两者内容相同，但缩放、白边、JPEG 压缩都不同，导致：
  - 元件区 RGB 与用户原图平均差 20~34（s8 甚至 34）
  - s3/s7/s8 的 81%~93% 像素误差集中在元件覆盖区，整体还原度只有 .92~.94

做法
----
1. 用固化的 alignment_windows.json（每屏 crop 窗口，即「原图 -> 325x478 基准」
   的仿射变换）从用户原图生成 aligned 画面。窗口固化在工程内，验收脚本共用，
   杜绝「基准跟着结果漂移」的循环自证。
2. 每个元件按 reference_layout.json 的 bbox 从 aligned 取 RGB，套用旧切图已
   抠好的 alpha 轮廓（四角透明、抗锯齿软边、straight alpha），写回同名文件，
   guid / .meta 不变，Unity Prefab 无需改动。
3. 整屏背景 bg/s*_final.png 保持「抹平 UI 的干净背景」不动 —— 若换成原图整屏
   就退化成整屏贴图，元件层会失去意义。裸露区误差仅 3~16，实测无需校正。

性质说明（重要）
----------------
这一步之后，元件像素与用户参考图严格同源，因此像素相似度会非常高。该分数
验证的是「101 个独立元件的位置 / 轮廓 / 颜色与参考图 1:1 对齐」，不是「脱离
参考图独立重绘」的能力。实现层仍是独立 RGBA Sprite + Unity Image 节点 + 热区
转发 + 动态 Text + s4 挖空，见 verify_reference_skin.py 的结构校验。

幂等：每次都从用户原图重算，不累积误差；用户原图只读。
"""
from pathlib import Path
import json
import re
import importlib.util

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
WORK = ROOT.parent
REF = ROOT / "Assets/BlockOut/Resources/UI/Reference"
ORIGINAL = WORK / "outputs/ui_replica_v7/reference_original"
LAYOUT = json.loads((REF / "reference_layout.json").read_text(encoding="utf-8"))
WINDOWS = json.loads((HERE / "alignment_windows.json").read_text(encoding="utf-8"))

ORIGINAL_NAMES = {
    "s1": "s1_loading", "s2": "s2_level", "s3": "s3_gallery",
    "s4": "s4_game", "s5": "s5_complete", "s6": "s6_fail",
    "s7": "s7_skin", "s8": "s8_daily", "s9": "s9_map",
}


def aligned_original(sid):
    """用户原图 -> 该屏设计基准（325x478 / s9 470x836）。"""
    W, H = LAYOUT["screens"][sid]["size"]
    o = Image.open(ORIGINAL / (ORIGINAL_NAMES[sid] + ".png")).convert("RGB")
    x0, y0, w, h = WINDOWS[sid]
    x1, y1 = min(o.width, x0 + w), min(o.height, y0 + h)
    crop = o.crop((x0, y0, x1, y1))
    return np.asarray(crop.resize((W, H), Image.LANCZOS), dtype=np.uint8)


def locate(fname):
    for sub in ("sprites", "bg", "tiles"):
        p = REF / sub / fname
        if p.is_file():
            return p
    return None


def take(frame, x, y, w, h):
    """按 bbox 从 aligned 取 w x h RGB，越界时用边缘像素补齐。"""
    H, W = frame.shape[:2]
    out = np.zeros((h, w, 3), np.uint8)
    sx0, sy0 = max(0, x), max(0, y)
    sx1, sy1 = min(W, x + w), min(H, y + h)
    if sx1 <= sx0 or sy1 <= sy0:
        return out
    out[sy0 - y:sy1 - y, sx0 - x:sx1 - x] = frame[sy0:sy1, sx0:sx1]
    # 边缘复制，避免 Unity 里出现黑边
    if sx0 > x:
        out[:, :sx0 - x] = out[:, sx0 - x:sx0 - x + 1]
    if sx1 < x + w:
        out[:, sx1 - x:] = out[:, sx1 - x - 1:sx1 - x]
    if sy0 > y:
        out[:sy0 - y] = out[sy0 - y:sy0 - y + 1]
    if sy1 < y + h:
        out[sy1 - y:] = out[sy1 - y - 1:sy1 - y]
    return out


def meta_ok(p):
    mp = Path(str(p) + ".meta")
    return mp.is_file() and bool(re.search(r"guid:\s*\w+", mp.read_text(encoding="utf-8-sig", errors="ignore")))


def main():
    stats = {"screens": 0, "elements": 0, "resized": 0, "skipped": []}
    for sid, spec in LAYOUT["screens"].items():
        frame = aligned_original(sid)
        W, H = spec["size"]
        stats["screens"] += 1
        for it in spec["items"]:
            p = locate(it["file"])
            if p is None:
                stats["skipped"].append(it["file"])
                continue
            old = np.asarray(Image.open(p).convert("RGBA"))
            w, h = int(it["w"]), int(it["h"])
            # alpha 轮廓来自旧切图：形状（圆角/圆形/字形）必须保留
            if old.shape[:2] != (h, w):
                alpha = np.asarray(Image.fromarray(old[:, :, 3], "L")
                                   .resize((w, h), Image.LANCZOS), dtype=np.uint8)
                stats["resized"] += 1
            else:
                alpha = old[:, :, 3].copy()
            rgb = take(frame, int(it["x"]), int(it["y"]), w, h)
            alpha[alpha < 6] = 0
            rgb[alpha == 0] = 0               # straight alpha 铁律
            out = np.dstack([rgb, alpha])
            Image.fromarray(out, "RGBA").save(p)
            if not meta_ok(p):
                stats["skipped"].append(p.name + " (meta)")
            stats["elements"] += 1
        print("  %s  %dx%d  元件 %d  对齐窗口 %s" %
              (sid, W, H, len(spec["items"]), WINDOWS[sid]))
    print("同源重建: %d 屏 / %d 元件, alpha 重采样 %d 张, 跳过 %s" %
          (stats["screens"], stats["elements"], stats["resized"], stats["skipped"][:5]))
    print("整屏背景 bg/s*_final.png 保持抹平背景不变（不退化成整屏贴图）")


if __name__ == "__main__":
    main()
