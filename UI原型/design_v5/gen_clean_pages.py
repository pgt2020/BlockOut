# -*- coding: utf-8 -*-
"""导出剩余页面的**纯界面效果图**（clean）：游戏页 / 收藏 / 商店 / 设置 / 普通结算。

来源与规则：
  · clean_game / clean_collection / clean_store / clean_settings
    从对应规格标注稿（04 / 14 / 15 / 16）提取**页面主体**，剔除所有标注：
    安全区虚线+示意带+说明文字、手势指示条、滚动区示意、热区虚线框、
    页外图注与设计注释、XML 注释。规格标注版保留不动，两版分清。
    玩家不可见的开发说明（如设置页"二级页面：不显示底部导航"）一律剔除，
    只留在规格标注版；收藏页奖励文案与程序实际发放项一致（只有金币）。
  · clean_settlement / _repeat / _chapter / _short：普通关卡结算纯界面，
    按程序**运行时布局**重绘（上一版画的是构建时的 300×500 居中弹窗，
    三个次级按钮纵向排列，与 LayoutFullPages 重排后的真实结构不符）：
      - 布局：BlockOutUIManager.LayoutFullPages（BlockOutUIManager.cs:1673-1732）
        SettlementLayer 的 Card 挂 SafeRoot 下**铺满安全区**；
        revealH = clamp(安全区高−330, 120, 360)；
        查看收藏/重玩本关**左右并排**（各 (卡宽−44)/2 × 44）；
        作品区随余高伸缩；章末切 contain（LayoutArtwork，MistWarm 信笺边）。
      - 文案：BlockOutUIController.HandleLevelWon（BlockOutUIController.cs:670-733）
      - 奖励：BlockOutLevelParser.cs:67 / BlockOutCatalog.cs:277
        rewardCoins>0 ? rewardCoins : 25 + levelInChapter×5（0-based）
        第 4 关 index3 → 40 金币；第 12 关 index11 → 80 金币；
        重复通关奖励相同（SettleWin 不区分首通，只按关卡发奖）。
      - 短屏（360×640）：st=24/sb=16（程序夹取下限），卡 312×600，
        revealH = clamp(600−330,120,360) = 270，布局仍成立。
    注意：程序 Button transition=None，禁用态不会自动变灰；禁用外观按设计规范
    绘制（灰底 + 禁止图标，与 17 B 页 / 首页 preparing 一致）。
    以上结论为**设计稿对照程序源码**；Unity 内实际运行效果仍未验证（18 号文档四档口径）。
  · 作品图一律 1:1 放置或 xMidYMid slice；素材与容器同比例，无拉伸。
"""
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- 提取工具

def read(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as f:
        return f.read()


def extract_defs(src):
    m = re.search(r"  <defs>.*?</defs>", src, re.S)
    assert m, "defs block not found"
    return m.group(0)


def extract_group(src, marker):
    """提取两个空格缩进的 <g transform=...> 页面组（14/15/16 的主页面）。"""
    i = src.index(marker)
    j = src.index("\n  </g>", i) + len("\n  </g>")
    return src[i:j]


def strip_annotations(lines, rules):
    """按规则剔除标注行；每条规则返回剔除行数并断言命中。
    支持**多行注释**（<!-- 开头的行到含 --> 的行为止整段剔除）——
    旧版只删单行注释，14 号稿的两行缩略图注释会残留 "-->" 触发断言失败，
    导致上一轮 clean_collection 实际未重新生成（本轮修正）。"""
    kept, dropped = [], 0
    skip_next = 0
    in_comment = False
    for ln in lines:
        if skip_next > 0:
            skip_next -= 1
            dropped += 1
            continue
        if in_comment:                      # 多行注释体内
            dropped += 1
            if "-->" in ln:
                in_comment = False
            continue
        if ln.strip().startswith("<!--"):   # 注释起始行（单行或多行首行）
            dropped += 1
            if "-->" not in ln:
                in_comment = True
            continue
        if any(r(ln) for r in rules):
            # 热区虚线组：<g ...> 后跟一行 rect 再 </g>
            if ln.rstrip().endswith('opacity=".6">'):
                skip_next = 2
            dropped += 1
            continue
        kept.append(ln)
    return kept, dropped


SAFE_AREA_RULES = [
    lambda ln: "底部安全区" in ln,                                  # 安全区说明文字
    lambda ln: 'fill="#674138" opacity=".07"' in ln,               # 安全区示意带
    lambda ln: 'stroke-dasharray="4 3"' in ln and 'stroke="#F45F70"' in ln,  # 安全区虚线
    lambda ln: 'fill="#553B36" opacity=".2"' in ln,                # 手势指示条
    lambda ln: ln.strip().startswith("<!--") and ln.rstrip().endswith("-->"),  # 单行注释
]

COLLECTION_EXTRA_RULES = SAFE_AREA_RULES + [
    lambda ln: 'stroke="#62CFA7" stroke-width="1.5" stroke-dasharray="6 5"' in ln,  # 滚动区示意框
    lambda ln: 'fill="#62CFA7" opacity=".38"' in ln,               # 滚动条示意
    lambda ln: 'fill="#3BB98E"' in ln,                             # 绿色开发注记
    lambda ln: 'stroke-dasharray="3 3" opacity=".6"' in ln,        # 导航热区虚线组（含后续 2 行）
]

# 纯界面专属：剔除给开发看的说明文字（保留在规格标注版 16）
SETTINGS_EXTRA_RULES = SAFE_AREA_RULES + [
    lambda ln: "二级页面" in ln,                                   # 「二级页面：不显示底部导航；返回上一层」
]


def build_clean(src_name, marker, rules, expect_drop, out_name, aria):
    src = read(src_name)
    if marker:
        body = extract_group(src, marker)
    else:
        body = src[src.index("</defs>") + len("</defs>"):src.rindex("</svg>")]
    kept, dropped = strip_annotations(body.split("\n"), rules)
    assert dropped >= expect_drop, "%s: dropped %d < expected %d" % (out_name, dropped, expect_drop)
    # 不得残留多行注释残尸
    assert not any("-->" in ln for ln in kept), "%s: dangling comment" % out_name
    svg = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           'viewBox="0 0 390 844" width="780" height="1688" role="img" aria-label="%s">\n%s\n%s\n</svg>\n'
           % (aria, extract_defs(src), "\n".join(kept).strip("\n")))
    with open(os.path.join(BASE, out_name), "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote %s  (dropped %d annotation lines)" % (out_name, dropped))
    return svg


# ---------------------------------------------------------------- 普通结算页（安全区完整布局）
# 几何来源：程序 BlockOutUIManager.LayoutFullPages（.cs:1673-1732，Relayout 时的**运行时**布局）：
#   Card 挂 SafeRoot 下铺满安全区（anchorMin/Max=0/1，零内缩），之后：
#     revealH = clamp(height-330, 120, 360)        height = H - SafeTop - SafeBottom
#     Title/PieceText:  TopCenter y=16/52（w-32）
#     RevealRoot/Frame: TopLeft  x=16, y=84, w-32 × revealH
#     NoteText:  y+10 ；CoinRow: y+34（240×24）；NextBtn: y+72（w-32×48）
#     CollectionBtn/ReplayBtn: y+132，各 (w-44)/2×44，**左右并排**（x=16 / x=w/2+6）
#     HomeBtn:    y+188（w-32×44）                其中 y = 84 + revealH
# 文案来源：BlockOutUIController.HandleLevelWon（.cs:670-733）
# 奖励来源：BlockOutLevelParser.cs:67 / BlockOutCatalog.cs:277 → 25 + levelInChapter×5（0-based）
SETTLE_DEFS = '''  <defs>
    <linearGradient id="stbg" x2="0" y2="1"><stop stop-color="#FFFAF4"/><stop offset="1" stop-color="#FFF1E3"/></linearGradient>
    <linearGradient id="gcta" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#FF8B7E"/><stop offset="1" stop-color="#FF6B5C"/></linearGradient>
    <linearGradient id="gdis" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#E9DED3"/><stop offset="1" stop-color="#D4C5B6"/></linearGradient>
    <radialGradient id="bm"><stop stop-color="#62CFA7" stop-opacity=".16"/><stop offset="1" stop-color="#62CFA7" stop-opacity="0"/></radialGradient>
    <radialGradient id="bc"><stop stop-color="#FF7568" stop-opacity=".12"/><stop offset="1" stop-color="#FF7568" stop-opacity="0"/></radialGradient>
    <symbol id="coinS" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#FFC53D" stroke="#E3A22E" stroke-width="1.4"/>
      <circle cx="12" cy="12" r="6.5" fill="none" stroke="#FFE9B0" stroke-width="1.4"/>
      <path d="M12 7l1.6 3.4 3.4 1.6-3.4 1.6L12 17l-1.6-3.4L7 12l3.4-1.6z" fill="#E3A22E"/>
    </symbol>
    <style>
      text{font-family:'Source Han Sans CN','Noto Sans SC','Microsoft YaHei','PingFang SC',sans-serif}
      .grid{fill:none;stroke:#E9CFC0;stroke-width:1.5;stroke-dasharray="4 8"}
    </style>
  </defs>'''


def settle_geom(W, H, st, sb, L=24, R=24):
    """按 LayoutFullPages 计算结算页几何（设计坐标）。"""
    w = W - L - R
    h = H - st - sb
    reveal_h = max(120, min(360, h - 330))          # clamp(height-330, 120, 360)
    y = 84 + reveal_h
    g = dict(W=W, H=H, st=st, sb=sb, L=L, R=R, w=w, h=h,
             reveal_h=reveal_h, reveal_x=L + 16, reveal_y=st + 84, reveal_w=w - 32,
             note_y=st + y + 10, coin_y=st + y + 34, next_y=st + y + 72,
             sub_y=st + y + 132, home_y=st + y + 188,
             sub_w=(w - 44) / 2.0, card_bottom=st + h, content_bottom=st + y + 232)
    # 布局断言（等价于程序运行约束：内容不得超出 Card，作品区在夹取范围内）
    assert 120 <= g["reveal_h"] <= 360, "revealH out of clamp range"
    assert g["content_bottom"] <= g["card_bottom"] + 0.01, \
        "settlement content overflows card: %.0f > %.0f" % (g["content_bottom"], g["card_bottom"])
    assert g["next_y"] + 48 <= g["sub_y"], "next button overlaps secondary row"
    assert g["sub_y"] + 44 <= g["home_y"], "secondary row overlaps home button"
    return g


def dim_backdrop(W, H, st, sb, L, cw, level=4):
    """Dim 下的游戏页（04 结构；程序棋盘 = min(W−36, 可用高)，工具条 cw×104 吸底）。
    结算卡铺满安全区后该背景仅安全区边缘可见。"""
    o = []
    o.append('  <rect width="%d" height="%d" fill="url(#stbg)"/>' % (W, H))
    o.append('  <circle cx="%g" cy="130" r="150" fill="url(#bm)"/>' % (W * 0.14))
    o.append('  <circle cx="%g" cy="420" r="165" fill="url(#bc)"/>' % (W * 0.88))
    o.append('  <circle cx="%g" cy="%g" r="150" fill="url(#bm)"/>' % (W * 0.18, H - 84))
    o.append('  <circle cx="%g" cy="%g" r="22" fill="#FFFFFF"/>' % (L + 22, st + 22))
    o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="18" font-weight="700" '
             'fill="#553B36">第一章 · 第 %d 关</text>' % (W / 2, st + 27, level))
    for i in range(3):
        o.append('  <circle cx="%g" cy="%g" r="9" fill="#F45F70"/>' % (W - 74 + i * 22, st + 22))
    # 棋盘（程序 BoardSideByWidth = W−36；可用高度内继续收缩）
    board_top = st + 116
    board_bottom_limit = H - sb - 104 - 12 - 26 - 12
    side = max(120, min(W - 36, board_bottom_limit - board_top))
    cy = (board_top + board_bottom_limit) / 2.0
    bx, by = (W - side) / 2.0, cy - side / 2.0
    o.append('  <rect x="%g" y="%g" width="%g" height="%g" rx="22" fill="#FFFDF8" '
             'stroke="#E8CDBB" stroke-width="3"/>' % (bx, by, side, side))
    for i in range(1, 6):
        o.append('  <path class="grid" d="M%g %gV%gM%g %gH%g"/>'
                 % (bx + side * i / 6.0, by, by + side, bx, by + side * i / 6.0, bx + side))
    # 工具条（程序：cw×104 固定高，止于底部安全区上方；槽位中心 = L+26+(cw−52)(2i+1)/6）
    ty = H - sb - 104
    o.append('  <rect x="%d" y="%g" width="%d" height="104" rx="26" fill="#FFFDF8" '
             'stroke="#F0DCCB" stroke-width="2"/>' % (L, ty, cw))
    for i, (nm, sub) in enumerate((("提示", "第 7 关解锁"), ("锤子", "第 11 关解锁"),
                                    ("魔法棒", "第 16 关解锁"))):
        cx = L + 26 + (cw - 52) * (2 * i + 1) / 6.0
        o.append('  <circle cx="%g" cy="%g" r="30" fill="#FFFFFF"/>' % (cx, ty + 46))
        o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="10.5" fill="#553B36">%s</text>'
                 % (cx, ty + 85, nm))
        o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="9" fill="#8A6E62">%s</text>'
                 % (cx, ty + 98, sub))
    return o


def settlement_page(g, s, cid):
    """一个安全区完整结算页。s 含 title/piece/note/reward/next_label/next_on/art/mode/level。"""
    W, H, st, L, cw = g["W"], g["H"], g["st"], g["L"], g["w"]
    cx = W / 2.0
    rx, ry, rw, rh = g["reveal_x"], g["reveal_y"], g["reveal_w"], g["reveal_h"]
    o = []
    o += dim_backdrop(W, H, st, g["sb"], L, cw, s.get("level", 4))
    # Dim 层（程序 BlockOutWidgets.Dim：MaskWarm 30%）
    o.append('  <rect x="0" y="0" width="%d" height="%d" fill="#674138" opacity=".3"/>' % (W, H))
    # Card：SafeRoot 下铺满安全区（LayoutFullPages：anchorMin/Max = 0/1，零内缩，圆角 24）
    o.append('  <rect x="%d" y="%d" width="%d" height="%d" rx="24" fill="#FFFDF8" '
             'stroke="#F0DCCB" stroke-width="2"/>' % (L, st, cw, g["h"]))
    # 标题 22/900（SettleTitleText.fontSize = 22，TopCenter y=16）
    o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="22" font-weight="900" '
             'fill="#553B36">%s</text>' % (cx, st + 38, s["title"]))
    # 拼片进度 11/800 薄荷（SettlePieceText，TopCenter y=52）
    o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="11" font-weight="800" '
             'fill="#2E7C5B">%s</text>' % (cx, st + 66, s["piece"]))
    # 揭晓区：RevealRoot 背景 MistWarm #FFF7EF + RectMask2D 硬裁切；
    # RevealFrame 在程序中为透明 Panel（Color.clear），不绘制边框（与程序一致）。
    o.append('  <rect x="%g" y="%g" width="%g" height="%g" fill="#FFF7EF"/>' % (rx, ry, rw, rh))
    o.append('  <clipPath id="cp%s"><rect x="%g" y="%g" width="%g" height="%g"/></clipPath>'
             % (cid, rx, ry, rw, rh))
    if s["mode"] == "contain":
        # 章末：contain 预渲染成图（310×310 作品 + 信笺边），与容器同尺寸 1:1 放置
        o.append('  <image x="%g" y="%g" width="%g" height="%g" preserveAspectRatio="none" '
                 'xlink:href="%s" clip-path="url(#cp%s)"/>' % (rx, ry, rw, rh, s["art"], cid))
    else:
        # 首通/重复：素材与容器同比例（cover 裁切导出），slice 双保险
        o.append('  <image x="%g" y="%g" width="%g" height="%g" preserveAspectRatio="xMidYMid slice" '
                 'xlink:href="%s" clip-path="url(#cp%s)"/>' % (rx, ry, rw, rh, s["art"], cid))
    # 注记 9/400（SettleNoteText）
    o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="9" fill="#8A6E62">%s</text>'
             % (cx, g["note_y"] + 12, s["note"]))
    # 金币行 240×24（CoinRow：CoinIcon 22×22 @ x+12；RewardText 11/900 @ x+44）
    row_x = cx - 120
    o.append('  <use href="#coinS" x="%g" y="%g" width="22" height="22"/>' % (row_x + 12, g["coin_y"] + 1))
    o.append('  <text x="%g" y="%g" font-size="11" font-weight="900" fill="#553B36">%s</text>'
             % (row_x + 44, g["coin_y"] + 17, s["reward"]))
    # 下一关（NextBtn，w-32×48；CoralButton 圆角 24）
    if s["next_on"]:
        o.append('  <rect x="%g" y="%g" width="%g" height="48" rx="24" fill="url(#gcta)"/>'
                 % (rx, g["next_y"], rw))
        o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="13" font-weight="900" '
                 'fill="#FFFFFF">%s</text>' % (cx, g["next_y"] + 31, s["next_label"]))
    else:
        # 禁用态：程序 Button transition=None 不会自动变灰，按设计规范绘灰底 + 禁止图标
        o.append('  <rect x="%g" y="%g" width="%g" height="48" rx="24" fill="url(#gdis)"/>'
                 % (rx, g["next_y"], rw))
        o.append('  <rect x="%g" y="%g" width="26" height="26" rx="9" fill="#FFFFFF" opacity=".72"/>'
                 % (rx + 16, g["next_y"] + 11))
        o.append('  <path d="M%g %gv12M%g %gh12" stroke="#A2938A" stroke-width="2.6" '
                 'stroke-linecap="round"/>' % (rx + 29, g["next_y"] + 18, rx + 23, g["next_y"] + 24))
        o.append('  <text x="%g" y="%g" font-size="13" font-weight="900" fill="#857A72">%s</text>'
                 % (rx + 54, g["next_y"] + 30, s["next_label"]))
    # 查看收藏 / 重玩本关：左右并排（程序：x=16 / x=width/2+6，各 (w-44)/2×44，
    # SecondaryButton 白底 + StrokeBoard 1.5；左右内边距均为 16，间隙 12）
    sw = g["sub_w"]
    for i, t in enumerate(("查看收藏", "重玩本关")):
        sx = rx if i == 0 else L + cw / 2.0 + 6
        o.append('  <rect x="%g" y="%g" width="%g" height="44" rx="19" fill="#FFFFFF" '
                 'stroke="#E8CDBB" stroke-width="1.5"/>' % (sx, g["sub_y"], sw))
        o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="11" font-weight="800" '
                 'fill="#553B36">%s</text>' % (sx + sw / 2.0, g["sub_y"] + 28, t))
    # 返回首页（HomeBtn，w-32×44）
    o.append('  <rect x="%g" y="%g" width="%g" height="44" rx="19" fill="#FFFFFF" '
             'stroke="#E8CDBB" stroke-width="1.5"/>' % (rx, g["home_y"], rw))
    o.append('  <text x="%g" y="%g" text-anchor="middle" font-size="11" font-weight="800" '
             'fill="#553B36">返回首页</text>' % (cx, g["home_y"] + 28))
    return o


# 四态：首通 / 重复通关 / 章末首通（下一章未发布）+ 短屏首通
# 文案逐条对应 HandleLevelWon：
#   isChapterEnd ? (firstClear?"本章通关":"本章已完成") : (firstClear?"新拼片解锁":"关卡完成")
#   chapterComplete ? "拼片 12/12 · 本章作品已集齐" : "拼片 4/12"
#   NextBtn：hasNext ? (章末?"进入下一章":"下一关") : "新章节准备中"（禁用）
SETTLE_STATES = [
    dict(fn="clean_settlement", W=390, H=844, st=24, sb=34, level=4,
         title="新拼片解锁", piece="拼片 4/12", note="本次新揭晓 1 片拼片",
         reward="首次通关 · 获得 40 金币", next_label="下一关", next_on=True,
         art="assets/r04_310x360.png", mode="cover",
         aria="普通关卡结算纯界面（安全区完整页）：首次通关第4关，新拼片解锁，拼片4/12，获得40金币，下一关；查看收藏与重玩本关左右并排"),
    dict(fn="clean_settlement_repeat", W=390, H=844, st=24, sb=34, level=4,
         title="关卡完成", piece="拼片 4/12", note="重复通关 · 拼片不重复解锁",
         reward="重复通关 · 获得 40 金币", next_label="下一关", next_on=True,
         art="assets/r04_310x360.png", mode="cover",
         aria="普通关卡结算纯界面（重复通关第4关）：关卡完成，拼片4/12不重复解锁，获得40金币"),
    dict(fn="clean_settlement_chapter", W=390, H=844, st=24, sb=34, level=12,
         title="本章通关", piece="拼片 12/12 · 本章作品已集齐",
         note="本章 12 片拼片全部揭晓 · 完整作品已解锁",
         reward="首次通关 · 获得 80 金币", next_label="新章节准备中", next_on=False,
         art="assets/r12_310x360_contain.png", mode="contain",
         aria="章末结算纯界面（安全区完整页）：本章通关，拼片12/12已集齐，完整作品contain完整显示，获得80金币；下一章未发布（PublishedChapters=1）主按钮禁用"),
    dict(fn="clean_settlement_short", W=360, H=640, st=24, sb=16, level=4,
         title="新拼片解锁", piece="拼片 4/12", note="本次新揭晓 1 片拼片",
         reward="首次通关 · 获得 40 金币", next_label="下一关", next_on=True,
         art="assets/r04_280x270.png", mode="cover",
         aria="普通关卡结算纯界面（360×640短屏真实排版）：卡312×600铺满安全区，作品区280×270按余高压缩，查看收藏与重玩本关左右并排"),
]


def build_settlements():
    for s in SETTLE_STATES:
        g = settle_geom(s["W"], s["H"], s["st"], s["sb"])
        body = settlement_page(g, s, s["fn"].replace("clean_settlement", "S"))
        svg = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
               'viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-label="%s">\n'
               '%s\n%s\n</svg>\n'
               % (s["W"], s["H"], s["W"] * 2, s["H"] * 2, s["aria"],
                  SETTLE_DEFS, "\n".join(body)))
        with open(os.path.join(BASE, s["fn"] + ".svg"), "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote %s.svg  %dx%d 卡%.0fx%.0f 揭晓区%.0fx%.0f 内容底%.0f<=卡底%.0f"
              % (s["fn"], s["W"], s["H"], g["w"], g["h"], g["reveal_w"], g["reveal_h"],
                 g["content_bottom"], g["card_bottom"]))


if __name__ == "__main__":
    build_clean("04_game_default.svg", None, SAFE_AREA_RULES, 2,
                "clean_game.svg", "游戏页纯界面：6×6 棋盘六块中性方块，HUD 与三道具锁定态")
    build_clean("14_collection_page.svg", '  <g transform="translate(0,60)">', COLLECTION_EXTRA_RULES, 10,
                "clean_collection.svg", "收藏页纯界面：章节摘要、章节列表、重复挑战关卡网格、底部导航")
    build_clean("15_shop_page.svg", '  <g transform="translate(0,60)">', SAFE_AREA_RULES, 4,
                "clean_store.svg", "商店纯界面：三商品、可买与禁买态、金币获取说明、底部导航")
    build_clean("16_settings_page.svg", '  <g transform="translate(0,60)">', SETTINGS_EXTRA_RULES, 5,
                "clean_settings.svg", "设置纯界面：音乐音效震动开关与关于，无底部导航")
    build_settlements()
    print("clean extra pages done")
