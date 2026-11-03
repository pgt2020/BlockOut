# -*- coding: utf-8 -*-
"""生成 17_chapter_end：三个状态统一为程序结算层（SettlementLayer）的**真实完整页面**结构。

本轮修正（P2 结算结构一致性）：旧稿 17 虽是"完整页"，但内部结构
（264×264 作品盒 + 奖励卡 + 88 高主 CTA + 查看大图入口）是自绘结构，
与程序 LayoutFullPages 重排后的真实结算页不符。现三态统一改为与
clean_settlement 系列**同源同几何**（直接复用 gen_clean_pages.settle_geom /
settlement_page，杜绝两份脚本各自漂移）：

  · Card 挂 SafeRoot 下**铺满安全区**（LayoutFullPages，BlockOutUIManager.cs:1673-1732）
  · revealH = clamp(安全区高−330, 120, 360) = 360；作品区 310×360 **contain** 完整显示
    （章末 SetSettlementArtworkMode(true)，MistWarm #FFF7EF 信笺边）
  · 查看收藏 / 重玩本关 **左右并排**（各 149×44），返回首页通栏
  · 文案逐条对应 HandleLevelWon（BlockOutUIController.cs:670-733）：
      A 已发布 → 「本章通关」+ 进入下一章（可点）
      B 未发布 → 「本章通关」+ 新章节准备中（禁用；当前 PublishedChapters=1）
      C 重复通关 → 「本章已完成」+ 重复通关文案 + 进入下一章
    按钮标签统一用程序标签（"重玩本关"，不用"重玩第 12 关"）。
  · 奖励 = 25 + levelInChapter×5（0-based），第 12 关 index 11 → 80 金币；
    重复通关奖励相同（SettleWin 不区分首通）；页面不显示 "+N"。
  · 禁用态：程序 Button transition=None 不会自动变灰，按设计规范灰底 + 禁止图标。
  · 页内无状态徽章 / 安全区标注；A/B/C 名称只出现在**页外图注**。
  · 换算结论为设计稿对照程序源码；Unity 内实际运行效果仍未验证（18 号文档四档口径）。

输出两份：
  17_chapter_end.svg/.png        规格标注版（页间图注 + 底部设计注释）
  17_chapter_end_clean.svg/.png 纯界面效果图（页面无任何标注，状态名仅在页外）
"""
import os

from gen_clean_pages import settle_geom, settlement_page, SETTLE_DEFS

BASE = os.path.dirname(os.path.abspath(__file__))

# 390×844 基准：卡 342×786 铺满安全区（st=24 / sb=34），与 clean_settlement 完全一致
W, H, ST, SB = 390, 844, 24, 34

# 三态（字段含义同 HandleLevelWon：title/piece/note/reward/next/next_on）
STATES = [
    dict(cid="A", y0=40,
         title="本章通关", piece="拼片 12/12 · 本章作品已集齐",
         note="本章 12 片拼片全部揭晓 · 完整作品已解锁",
         reward="首次通关 · 获得 80 金币", next_label="进入下一章", next_on=True,
         cap="图 A · 下一章已发布（主按钮进入下一章）"),
    dict(cid="B", y0=920,
         title="本章通关", piece="拼片 12/12 · 本章作品已集齐",
         note="本章 12 片拼片全部揭晓 · 完整作品已解锁",
         reward="首次通关 · 获得 80 金币", next_label="新章节准备中", next_on=False,
         cap="图 B · 下一章未发布（主按钮禁用 · 当前程序 PublishedChapters=1）"),
    dict(cid="C", y0=1800,
         title="本章已完成", piece="拼片 12/12 · 本章作品已集齐",
         note="重复通关 · 拼片不重复解锁，可继续刷金币",
         reward="重复通关 · 获得 80 金币", next_label="进入下一章", next_on=True,
         cap="图 C · 重复通关（拼片不重复解锁 + 金币照常）"),
]

PAGES_END = 2644          # 1800 + 844

NOTES = [
    "三态统一为程序结算层真实布局：卡铺满安全区、收藏/重玩并排、作品区随余高伸缩",
    "（与 clean_settlement 系列同源同几何：gen_clean_pages.settle_geom / settlement_page）",
    "章末作品 contain 完整显示（MistWarm #FFF7EF 信笺边），不裁作品边缘",
    "奖励取项目现有配置 25+levelInChapter×5（0-based）：第 12 关 = 80 金币",
    "重复通关奖励相同（SettleWin 不区分首通）；页面不显示 +N 占位",
    "禁用态：程序 Button transition=None 不会自动变灰，按设计规范灰底 + 禁止图标",
    "未发布态主按钮禁用，但不隐藏收藏 / 重玩 / 返回首页入口",
    "本轮删除旧版自绘元素（264×264 作品盒 / 奖励卡 / 查看大图入口）：程序结算层没有这些",
    "三档交付：布局已定稿 / 资源已交付 / 程序待验收（18 号文档）",
]


def state(s):
    """把 17 的三态定义转换成 settlement_page 需要的 state 字段。"""
    d = dict(s)
    d.update(art="assets/r12_310x360_contain.png", mode="contain", level=12)
    return d


def page(y0, cid, s):
    """一个 390×844 完整结算页（程序 SettlementLayer 布局），放在 y0。"""
    g = settle_geom(W, H, ST, SB)
    inner = settlement_page(g, state(s), cid)
    return (["  <g transform=\"translate(0,%d)\">" % y0]
            + ["  " + ln for ln in inner]
            + ["  </g>"])


def gap_caption(y, text, spec):
    """页外图注：放在页面间隙（任何 390×844 页面边界之外）。"""
    if spec:
        return ('  <text x="195" y="%d" text-anchor="middle" font-size="11" font-weight="900" '
                'fill="#FF7568">%s</text>' % (y, text))
    return ('  <text x="195" y="%d" text-anchor="middle" font-size="9" font-weight="800" '
            'fill="#8A7568">%s</text>' % (y, text))


def build(with_notes):
    parts = []
    strip_note_h = 40 + len(NOTES) * 15 + 16
    total_h = PAGES_END + (strip_note_h if with_notes else 30)
    aria = "章末结算三态完整页面：下一章已发布进入下一章、未发布新章节准备中禁用、重复通关"
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                 'viewBox="0 0 390 %d" width="780" height="%d" role="img" aria-label="%s">'
                 % (total_h, total_h * 2, aria))
    parts.append('''  <!-- ============================================================
         BlockOut · 章末结算（第 12 关通关）  v5 定稿
         三态统一为**程序结算层真实布局**（SettlementLayer / LayoutFullPages）：
           A 已发布   → 「本章通关」+ 进入下一章（可点）
           B 未发布   → 「本章通关」+ 新章节准备中（禁用，PublishedChapters=1）
           C 重复通关 → 「本章已完成」+ 重复通关文案 + 进入下一章
         卡铺满安全区；作品区 310×360 contain 完整显示（章末 contain 模式）；
         查看收藏/重玩本关左右并排；奖励 80 金币（25+11×5，0-based）；
         页面不显示 "+N"；禁用态按设计规范灰底+禁止图标。
         页内无状态徽章 / 安全区标注；A/B/C 名称只出现在页外图注区。
         ============================================================ -->''')
    # 结算页所需的渐变/symbol/字体样式（与 clean_settlement 家族共用，防止两端漂移）
    parts.append(SETTLE_DEFS)
    for p in STATES:
        parts.append(gap_caption(p["y0"] - 14, p["cap"], with_notes))
        parts += page(p["y0"], p["cid"], p)
    if with_notes:
        y = PAGES_END + 40
        for n in NOTES:
            parts.append('  <text x="24" y="%d" font-size="8" fill="#8A6E62">· %s</text>' % (y, n))
            y += 15
    parts.append('</svg>')
    return "\n".join(parts)


if __name__ == "__main__":
    with open(os.path.join(BASE, "17_chapter_end.svg"), "w", encoding="utf-8") as f:
        f.write(build(True))
    print("wrote 17_chapter_end.svg (spec, notes outside pages)")
    with open(os.path.join(BASE, "17_chapter_end_clean.svg"), "w", encoding="utf-8") as f:
        f.write(build(False))
    print("wrote 17_chapter_end_clean.svg (pure UI, no annotations)")
    print("pages at 40/920/1800 · spec total =", PAGES_END + 40 + len(NOTES) * 15 + 16,
          "· clean total =", PAGES_END + 30)
