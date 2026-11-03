# -*- coding: utf-8 -*-
"""生成三档适配图（规格标注版，含安全区示意线）：
  360×640（小屏 / 短屏分支）
  390×844（基准）
  390×932（长屏）+ **不对称安全区示例**（顶部 44 / 底部 34）

本轮修复（P1）：
  · adapt() 布局使用**真实设备高度**（640 / 844 / 932）。底部导航、CTA、进度卡
    按真实剩余高度自下向上排布；预览卡按 min(cap, 余高) 压缩。
  · 说明区（图题 + 注记）**单独追加在页面之外**：页面底边界之外另起一版，
    不同底色 + 边界线，不参与导航 / 安全区 / 组件布局的任何计算。
  · 画布总高 = 页面高 H + 说明区高；页面区域严格 = 0..H，可逐像素验证。
  · 绝不允许把页面加长来消除重叠——生成时对每档做布局断言。

本轮修复（P2）：
  · 作品图按容器精确比例从统一源画布重新裁切导出（见 gen_cover_crops.py），
    SVG 内 preserveAspectRatio="xMidYMid slice" 双保险；不做任何非等比拉伸。
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FONT = "font-family:'Source Han Sans CN','Noto Sans SC','Microsoft YaHei','PingFang SC',sans-serif"

DEFS = '''  <defs>
    <linearGradient id="bg" x2="0" y2="1"><stop stop-color="#FFFAF4"/><stop offset="1" stop-color="#FFF1E3"/></linearGradient>
    <linearGradient id="cta" x2="0" y2="1"><stop stop-color="#FF8B7E"/><stop offset="1" stop-color="#FF6B5C"/></linearGradient>
    <style>text{%s}</style>
  </defs>
''' % FONT


def adapt(W, H, safe_top, safe_bottom, art, art_w, art_h_used, geom):
    """按**真实设备高度 H** 生成一屏首页。geom 由 build() 预算并回填：
       top_bar_y/h, card_top, card_bottom, cta_y, prog_y, nav_y, art_h
    规则来自 09 §6：首页边距 24；CTA 高 88 不压缩；底部导航 56(360)/64(390)；
    组件一律位于安全区内，底部组件止于安全区上方；预览卡 min(cap, 余高)。
    """
    is360 = (W <= 360)
    m = 24
    card_w = W - m * 2
    cta_h = 88
    y = geom["top_bar_y"]

    o = []
    # 页面背景（严格 0..H）
    o.append('  <rect x="0" y="0" width="%d" height="%d" fill="url(#bg)"/>' % (W, H))
    # 安全区示意（仅规格版有；clean 版无）
    o.append('  <rect x="0" y="0" width="%d" height="%d" fill="#FF7568" opacity=".07"/>' % (W, safe_top))
    o.append('  <rect x="0" y="%d" width="%d" height="%d" fill="#FF7568" opacity=".07"/>' % (H - safe_bottom, W, safe_bottom))
    o.append('  <path d="M0 %dH%d" stroke="#F45F70" stroke-width="1" stroke-dasharray="4 3"/>' % (safe_top, W))
    o.append('  <path d="M0 %dH%d" stroke="#F45F70" stroke-width="1" stroke-dasharray="4 3"/>' % (H - safe_bottom, W))
    o.append('  <text x="%d" y="%d" text-anchor="middle" font-size="7" fill="#C7432F">顶部安全区 %d</text>'
             % (W // 2, safe_top - 4 if safe_top > 12 else 9, safe_top))
    o.append('  <text x="%d" y="%d" text-anchor="middle" font-size="7" fill="#C7432F">底部安全区 %d</text>'
             % (W // 2, H - safe_bottom + 11, safe_bottom))

    # 顶栏
    bar_h = geom["bar_h"]
    o.append('  <rect x="%d" y="%d" width="%d" height="%d" rx="12" fill="#62CFA7"/>' % (m, y, 40 if is360 else 44, bar_h))
    cx = m + (20 if is360 else 22)
    cy = y + (20 if is360 else 22)
    o.append('  <path d="M%g %gl11 7-11 7z" fill="#FFFFFF"/>' % (cx - 5, cy - 7))
    o.append('  <text x="%d" y="%g" font-size="%g" font-weight="900" fill="#553B36">BlockOut</text>'
             % (m + (52 if is360 else 60), y + (22 if is360 else 26), 15 if is360 else 17))
    o.append('  <text x="%d" y="%g" font-size="8.5" fill="#8A6E62">箭头方块消除</text>' % (m + (52 if is360 else 60), y + (36 if is360 else 42)))
    coin_r = 14 if is360 else 16
    o.append('  <circle cx="%g" cy="%g" r="%g" fill="#FFFFFF" stroke="#F0DCCB" stroke-width="1.5"/>'
             % (W - m - 18, y + coin_r, coin_r))
    o.append('  <circle cx="%g" cy="%g" r="%g" fill="#FFC53D" stroke="#E3A22E" stroke-width="1.8"/>'
             % (W - m - 18, y + coin_r, coin_r * 0.62))

    # 预览卡（真实资源；素材按容器比例裁切导出，slice 仅作双保险）
    y = geom["card_top"]
    o.append('  <rect x="%d" y="%d" width="%d" height="%d" rx="20" fill="#FFFDF8" stroke="#F0DCCB" stroke-width="2"/>'
             % (m, y, card_w, art_h_used + 36))
    inner_w, inner_h = card_w - 12, art_h_used
    o.append('  <clipPath id="cpA%d"><rect x="%d" y="%d" width="%d" height="%d" rx="16"/></clipPath>'
             % (W, m + 6, y + 6, inner_w, inner_h))
    o.append('  <image x="%d" y="%d" width="%d" height="%d" preserveAspectRatio="xMidYMid slice" '
             'xlink:href="assets/%s" clip-path="url(#cpA%d)"/>'
             % (m + 6, y + 6, inner_w, inner_h, art, W))
    o.append('  <rect x="%d" y="%d" width="%d" height="%d" rx="16" fill="#FFF7EF" opacity=".22"/>'
             % (m + 6, y + 6, inner_w, inner_h))
    o.append('  <rect x="%d" y="%d" width="72" height="22" rx="11" fill="#FFFDF8" stroke="#FF7568" stroke-width="1.2"/>'
             % (W - m - 78, y + 12))
    o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="8.5" font-weight="900" fill="#FF6B5C">拼片 3/12</text>'
             % (W - m - 42, y + 27))

    # CTA（高 88 不压缩）
    y = geom["cta_y"]
    o.append('  <rect x="%d" y="%d" width="%d" height="%d" rx="22" fill="url(#cta)"/>' % (m, y, card_w, cta_h))
    o.append('  <rect x="%d" y="%d" width="40" height="40" rx="12" fill="#FFFFFF" opacity=".95"/>' % (m + 20, y + 24))
    o.append('  <path d="M%g %gl13 7-13 7z" fill="#FF6B5C"/>' % (m + 33, y + 37))
    o.append('  <text x="%d" y="%g" font-size="%g" font-weight="900" fill="#FFFFFF">继续第 4 关</text>'
             % (m + 74, y + 42, 15 if is360 else 16.5))
    o.append('  <text x="%d" y="%g" font-size="8.5" fill="#FFFFFF" opacity=".93">第一章 · 甜点星球 · 已通关 3 关</text>'
             % (m + 74, y + 62))

    # 进度卡
    y = geom["prog_y"]
    prog_h = geom["prog_h"]
    o.append('  <rect x="%d" y="%d" width="%d" height="%d" rx="20" fill="#FFFDF8" stroke="#F0DCCB" stroke-width="2"/>'
             % (m, y, card_w, prog_h))
    o.append('  <text x="%d" y="%g" font-size="%g" font-weight="900" fill="#553B36">第一章 · 甜点星球</text>'
             % (m + 18, y + 26, 11 if is360 else 12))
    o.append('  <rect x="%d" y="%g" width="%d" height="9" rx="4.5" fill="#F5E6D8"/>' % (m + 18, y + 38, card_w - 36))
    o.append('  <rect x="%d" y="%g" width="%g" height="9" rx="4.5" fill="#FF7568"/>' % (m + 18, y + 38, (card_w - 36) * 0.25))
    for i in range(12):
        nx = m + 18 + (card_w - 36) / 24 + i * (card_w - 36) / 12
        if i < 3:
            o.append('  <circle cx="%g" cy="%g" r="7" fill="#DFF6EC" stroke="#62CFA7" stroke-width="1.4"/>' % (nx, y + 68))
            o.append('  <path d="M%g %gL%g %gL%g %g" fill="none" stroke="#2E7C5B" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>'
                     % (nx - 3, y + 68, nx - 0.6, y + 70.4, nx + 3.2, y + 65.4))
        else:
            o.append('  <circle cx="%g" cy="%g" r="7" fill="none" stroke="#E0CDBC" stroke-width="1.6"/>' % (nx, y + 68))
    o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="8.5" fill="#8A6E62">拼片 3/12 · 还差 9 片解锁完整作品</text>'
             % (W // 2, y + prog_h - 12))

    # 底部导航（吸底，止于安全区上方）
    y = geom["nav_y"]
    nav_h = geom["nav_h"]
    o.append('  <rect x="%d" y="%d" width="%d" height="%d" rx="20" fill="#FFFFFF" stroke="#F0DCCB" stroke-width="2"/>'
             % (m, y, card_w, nav_h))
    for idx, (name, col) in enumerate((("首页", "#FF6B5C"), ("图鉴", "#8A7568"), ("商店", "#8A7568"))):
        ix = m + card_w / 6 + idx * card_w / 3
        if name == "首页":
            o.append('  <path d="M%g %gl9-8 9 8v10h-6v-6h-6v6h-6z" fill="%s"/>' % (ix - 9, y + (18 if is360 else 20), col))
        elif name == "图鉴":
            o.append('  <rect x="%g" y="%g" width="13" height="17" rx="2" fill="none" stroke="%s" stroke-width="1.9"/>'
                     % (ix - 6.5, y + (16 if is360 else 18), col))
        else:
            o.append('  <path d="M%g %gh18l-2 14h-14z" fill="none" stroke="%s" stroke-width="1.9"/>'
                     % (ix - 9, y + (20 if is360 else 22), col))
        o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="8.5" font-weight="800" fill="%s">%s</text>'
                 % (ix, y + nav_h - 8, col, name))

    # 设备屏幕边界（发丝线，标示页面到此为止；下方为说明区）
    o.append('  <rect x="0.5" y="0.5" width="%g" height="%g" fill="none" stroke="#C9B8AC" stroke-width="1"/>'
             % (W - 1, H - 1))
    return o


def note_strip(W, H, label, note_lines):
    """页外说明区：从 y=H 开始，独立底色 + 边界线。
    只放图题与注记，绝不参与页面布局 / 导航 / 安全区计算。"""
    strip_h = 52 + (len(note_lines) - 1) * 12 + 14
    o = ['  <rect x="0" y="%d" width="%d" height="%d" fill="#F7F2EB"/>' % (H, W, strip_h)]
    o.append('  <path d="M0 %dH%d" stroke="#E0D2C4" stroke-width="1"/>' % (H, W))
    o.append('  <text x="12" y="%d" font-size="8" font-weight="800" fill="#8A7568">'
             '▲ 页面边界 %d×%d · 以上为设备屏幕；以下为图注说明区（不参与页面布局）</text>'
             % (H + 16, W, H))
    o.append('  <text x="12" y="%d" font-size="10.5" font-weight="900" fill="#FF7568">%s</text>'
             % (H + 34, label))
    for i, n in enumerate(note_lines):
        o.append('  <text x="12" y="%g" font-size="7.5" fill="#8A6E62">· %s</text>' % (H + 52 + i * 12, n))
    return o, strip_h


# 布局预算：自下向上固定链（CTA 88 / 进度卡 / 导航），预览卡吸收剩余高度
def plan(W, H, safe_top, safe_bottom):
    is360 = (W <= 360)
    bar_h = 40 if is360 else 44
    nav_h = 56 if is360 else 64
    prog_h = 104 if is360 else 120
    cta_h = 88
    top_gap = 10 if is360 else 16

    top_bar_y = safe_top + top_gap
    card_top = top_bar_y + bar_h + 14
    nav_y = H - safe_bottom - nav_h - 8
    prog_y = nav_y - 12 - prog_h
    cta_y = prog_y - 14 - cta_h
    card_bottom = cta_y - 14
    avail = card_bottom - card_top - 36          # 预览卡作品区可用高度
    cap = 210 if is360 else 288                  # 288 = 与 06 首页预览卡一致
    art_h = max(0, min(cap, avail))

    # ---- 布局断言：真实高度下无重叠、不越安全区、不出现负高度 ----
    assert art_h >= 0, "preview art height negative at %dx%d" % (W, H)
    assert card_top >= top_bar_y + bar_h, "top bar overlaps preview card"
    assert card_top + art_h + 36 <= card_bottom + 0.001, "preview card overlaps CTA"
    assert cta_y + cta_h <= prog_y, "CTA overlaps progress card"
    assert prog_y + prog_h <= nav_y, "progress card overlaps nav"
    assert nav_y + nav_h <= H - safe_bottom + 0.001, "nav crosses bottom safe area"
    assert top_bar_y >= safe_top, "top bar crosses top safe area"
    return dict(top_bar_y=top_bar_y, bar_h=bar_h, card_top=card_top, card_bottom=card_bottom,
                cta_y=cta_y, prog_y=prog_y, nav_y=nav_y, nav_h=nav_h, prog_h=prog_h, art_h=art_h)


SPECS = [
    dict(W=360, H=640, st=20, sb=20, art="r03_300x204.png",
         label="360×640 · 小屏（页面高 = 真实 640）",
         notes=["底部导航 56 吸底、止于底部安全区上方；CTA 312×88 高不压缩",
                "预览卡作品区按真实剩余高度压缩：300×204（min(210, 余高 204)）",
                "等比裁切导出自统一源画布；棋盘 324 = 屏宽−36；安全区 20/20 为示例值"]),
    dict(W=390, H=844, st=24, sb=34, art="r03_330x288.png",
         label="390×844 · 基准（页面高 = 真实 844）",
         notes=["底部导航 64 吸底、止于安全区 34 上方；CTA 342×88 高不压缩",
                "预览卡作品区 330×288（与 06 首页一致，等比裁切非拉伸）",
                "中部留白由弹性间隙吸收，不通过加长页面消除；棋盘 354 = 屏宽−36"]),
    dict(W=390, H=932, st=44, sb=34, art="r03_330x288.png",
         label="390×932 · 长屏 + 不对称安全区（页面高 = 真实 932）",
         notes=["**不对称安全区示例**：顶部 44 / 底部 34，验证组件不依赖上下对称",
                "顶栏起点 = 44+16；导航止于 34 之上；CTA/导航吸底",
                "预览卡 330×288；长屏中部留白增大，组件高度一律不压缩"]),
]


def build(spec):
    geom = plan(spec["W"], spec["H"], spec["st"], spec["sb"])
    body = adapt(spec["W"], spec["H"], spec["st"], spec["sb"], spec["art"],
                 spec["W"] - 48 - 12, geom["art_h"], geom)
    strip, strip_h = note_strip(spec["W"], spec["H"], spec["label"], spec["notes"])
    total_h = spec["H"] + strip_h
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s 适配图（页面 %d 高 + 页外说明区 %d）">\n%s\n%s\n%s\n</svg>\n'
            % (spec["W"], total_h, spec["W"] * 2, total_h * 2, spec["label"],
               spec["H"], strip_h, DEFS, "\n".join(body), "\n".join(strip)))


if __name__ == "__main__":
    names = []
    for s in SPECS:
        g = plan(s["W"], s["H"], s["st"], s["sb"])
        print("%dx%d: art=%.0f  card %.0f..%.0f  cta %.0f..%.0f  prog %.0f..%.0f  nav %.0f..%.0f  (page H=%d, safe %d/%d)"
              % (s["W"], s["H"], g["art_h"], g["card_top"], g["card_top"] + g["art_h"] + 36,
                 g["cta_y"], g["cta_y"] + 88, g["prog_y"], g["prog_y"] + g["prog_h"],
                 g["nav_y"], g["nav_y"] + g["nav_h"], s["H"], s["st"], s["sb"]))
        tag = "%dx%d" % (s["W"], s["H"])
        fn = "adapt_%s.svg" % tag
        with open(os.path.join(BASE, fn), "w", encoding="utf-8") as f:
            f.write(build(s))
        names.append((fn, tag))
        print("wrote", fn)
    print("adapt set:", names)
