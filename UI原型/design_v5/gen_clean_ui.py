# -*- coding: utf-8 -*-
"""生成纯界面效果图（clean）：
纯界面效果图：不含任何图注、设计注释、安全区示意线、标注文字；
              仅保留玩家实际看到的界面元素（含真实美术资源）。

本轮修订：
  · 所有作品图 preserveAspectRatio="xMidYMid slice"；素材按容器精确比例从统一
    源画布裁切导出（gen_cover_crops.py），容器与素材比例一致，双保险防拉伸。
  · 首页 12/12 拆两态（P2 发布状态一致）：
      home_12           下一章已发布（示例，PublishedChapters>=2 时）
      home_12_preparing 下一章未发布（当前程序 PublishedChapters=1 的真实状态）：
                        主 CTA 禁用「新章节准备中」，不给可进入第 13 关的有效按钮
  · 12/12 进度文案改「完整作品已解锁」，不再出现"还差 0 片"。
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))
FONT = "font-family:'Source Han Sans CN','Noto Sans SC','Microsoft YaHei','PingFang SC',sans-serif"

DEFS = '''  <defs>
    <linearGradient id="bg" x2="0" y2="1"><stop stop-color="#FFFAF4"/><stop offset="1" stop-color="#FFF1E3"/></linearGradient>
    <linearGradient id="cta" x2="0" y2="1"><stop stop-color="#FF8B7E"/><stop offset="1" stop-color="#FF6B5C"/></linearGradient>
    <linearGradient id="dis" x2="0" y2="1"><stop stop-color="#E9DED3"/><stop offset="1" stop-color="#D4C5B6"/></linearGradient>
    <style>text{%s}</style>
  </defs>
''' % FONT


def coin(cx, cy, r=15):
    return ('    <circle cx="%g" cy="%g" r="%g" fill="#FFC53D" stroke="#E3A22E" stroke-width="2"/>\n'
            '    <circle cx="%g" cy="%g" r="%g" fill="none" stroke="#FFE9B0" stroke-width="2.5"/>'
            % (cx, cy, r, cx, cy, r * 0.6))


def check(cx, cy, r=13, fill="#DFF6EC", stroke="#62CFA7", tick="#2E7C5B"):
    """薄荷圆底 + 可可勾（路径用绝对坐标，避免相对指令书写错误）。"""
    return ('    <circle cx="%g" cy="%g" r="%g" fill="%s" stroke="%s" stroke-width="1.5"/>\n'
            '    <path d="M%g %gL%g %gL%g %g" fill="none" stroke="%s" stroke-width="2.2" '
            'stroke-linecap="round" stroke-linejoin="round"/>'
            % (cx, cy, r, fill, stroke,
               cx - r * 0.42, cy, cx - r * 0.08, cy + r * 0.34, cx + r * 0.45, cy - r * 0.36, tick))


def lock(cx, cy, s=1.0):
    return ('    <rect x="%g" y="%g" width="%g" height="%g" rx="2" fill="#B9A79B"/>\n'
            '    <path d="M%g %gv-3a%g %g 0 0 1 %g 0v3" fill="none" stroke="#B9A79B" stroke-width="2"/>'
            % (cx - 5 * s, cy - 1 * s, 10 * s, 8 * s,
               cx - 3.5 * s, cy - 1 * s, 3.5 * s, 3.5 * s, 7 * s))


# ============ 首页（390×844） ============
def home(art, progress_n, cta_text, cta_sub, cta_disabled=False):
    o = []
    o.append('  <rect x="0" y="0" width="390" height="844" fill="url(#bg)"/>')
    # 顶栏
    o.append('    <rect x="24" y="40" width="44" height="44" rx="14" fill="#62CFA7"/>')
    o.append('    <path d="M46 54l12 8-12 8z" fill="#FFFFFF"/>')
    o.append('    <text x="80" y="60" font-size="17" font-weight="900" fill="#553B36">BlockOut</text>')
    o.append('    <text x="80" y="76" font-size="9" fill="#8A6E62">箭头方块消除</text>')
    o.append('    <rect x="252" y="44" width="90" height="32" rx="16" fill="#FFFFFF" stroke="#F0DCCB" stroke-width="1.5"/>')
    o.append(coin(272, 60, 11))
    o.append('    <text x="292" y="65" font-size="12.5" font-weight="900" fill="#553B36">300</text>')
    o.append('    <circle cx="366" cy="60" r="16" fill="#FFFFFF" stroke="#F0DCCB" stroke-width="1.5"/>')
    import math
    teeth = []
    for i in range(8):
        a0 = i * math.pi / 4
        for rr, aa in ((9.5, a0 - 0.16), (9.5, a0 + 0.16)):
            teeth.append("%.1f,%.1f" % (366 + rr * math.cos(aa), 60 + rr * math.sin(aa)))
        for rr, aa in ((6.6, a0 + math.pi / 4 - 0.20), (6.6, a0 + math.pi / 4 + 0.20)):
            teeth.append("%.1f,%.1f" % (366 + rr * math.cos(aa), 60 + rr * math.sin(aa)))
    o.append('    <polygon points="%s" fill="#553B36"/>' % " ".join(teeth))
    o.append('    <circle cx="366" cy="60" r="3" fill="#FFFFFF"/>')
    # 预览卡（真实资源；素材与容器同比例裁切导出 + slice 双保险）
    o.append('    <rect x="24" y="104" width="342" height="336" rx="24" fill="#FFFDF8" stroke="#F0DCCB" stroke-width="2"/>')
    o.append('    <clipPath id="cpHome"><rect x="30" y="110" width="330" height="288" rx="18"/></clipPath>')
    o.append('    <image x="30" y="110" width="330" height="288" preserveAspectRatio="xMidYMid slice" '
             'xlink:href="assets/%s" clip-path="url(#cpHome)"/>' % art)
    o.append('    <rect x="30" y="110" width="330" height="288" rx="18" fill="#FFF7EF" opacity=".22"/>')
    o.append('    <text x="46" y="132" font-size="9" font-weight="700" fill="#8A6E62">第一章 · 作品预览</text>')
    o.append('    <rect x="272" y="118" width="76" height="24" rx="12" fill="#FFFDF8" stroke="#FF7568" stroke-width="1.2"/>')
    o.append('    <text x="310" y="134" text-anchor="middle" font-size="9" font-weight="900" fill="#FF6B5C">拼片 %d/12</text>' % progress_n)
    # CTA
    if cta_disabled:
        o.append('    <rect x="24" y="456" width="342" height="88" rx="24" fill="url(#dis)"/>')
        o.append('    <rect x="46" y="478" width="44" height="44" rx="14" fill="#FFFFFF" opacity=".72"/>')
        o.append('    <path d="M62 492v16M54 500h16" stroke="#A2938A" stroke-width="3.2" stroke-linecap="round"/>')
        o.append('    <text x="104" y="500" font-size="16.5" font-weight="900" fill="#857A72">%s</text>' % cta_text)
        o.append('    <text x="104" y="522" font-size="9" fill="#9A8F87">%s</text>' % cta_sub)
    else:
        o.append('    <rect x="24" y="456" width="342" height="88" rx="24" fill="url(#cta)"/>')
        o.append('    <rect x="46" y="478" width="44" height="44" rx="14" fill="#FFFFFF" opacity=".95"/>')
        o.append('    <path d="M62 492l15 8-15 8z" fill="#FF6B5C"/>')
        o.append('    <text x="104" y="500" font-size="16.5" font-weight="900" fill="#FFFFFF">%s</text>' % cta_text)
        o.append('    <text x="104" y="522" font-size="9" fill="#FFFFFF" opacity=".93">%s</text>' % cta_sub)
    # 进度卡
    o.append('    <rect x="24" y="560" width="342" height="120" rx="24" fill="#FFFDF8" stroke="#F0DCCB" stroke-width="2"/>')
    o.append('    <text x="42" y="588" font-size="12" font-weight="900" fill="#553B36">第一章 · 甜点星球</text>')
    o.append('    <text x="348" y="588" text-anchor="end" font-size="10" font-weight="800" fill="#FF6B5C">查看收藏 ›</text>')
    o.append('    <rect x="42" y="600" width="306" height="10" rx="5" fill="#F5E6D8"/>')
    o.append('    <rect x="42" y="600" width="%g" height="10" rx="5" fill="#FF7568"/>' % (306 * progress_n / 12))
    for i in range(12):
        cx = 42 + 306 / 24 + i * (306 - 306 / 12) / 11
        if i < progress_n:
            o.append(check(cx, 632, 8))
        else:
            o.append('    <circle cx="%g" cy="632" r="8" fill="none" stroke="#E0CDBC" stroke-width="1.8"/>' % cx)
    if progress_n >= 12:
        o.append('    <text x="195" y="666" text-anchor="middle" font-size="9" fill="#8A6E62">拼片 12/12 · 完整作品已解锁，可前往收藏查看</text>')
    else:
        o.append('    <text x="195" y="666" text-anchor="middle" font-size="9" fill="#8A6E62">拼片 %d/12 · 还差 %d 片解锁完整作品</text>'
                 % (progress_n, 12 - progress_n))
    # 底部导航
    o.append('    <rect x="24" y="696" width="342" height="64" rx="22" fill="#FFFFFF" stroke="#F0DCCB" stroke-width="2"/>')
    o.append('    <path d="M85 726l10-9 10 9v11h-7v-7h-6v7h-7z" fill="#FF6B5C"/>')
    o.append('    <text x="95" y="750" text-anchor="middle" font-size="9" font-weight="800" fill="#FF6B5C">首页</text>')
    o.append('    <rect x="188" y="717" width="14" height="18" rx="2" fill="none" stroke="#8A7568" stroke-width="2"/>')
    o.append('    <path d="M193 726h4" stroke="#8A7568" stroke-width="2"/>')
    o.append('    <text x="205" y="750" text-anchor="middle" font-size="9" font-weight="800" fill="#8A7568">图鉴</text>')
    o.append('    <path d="M298 722h20l-2 16h-16z" fill="none" stroke="#8A7568" stroke-width="2"/>')
    o.append('    <path d="M303 722v-3a5 5 0 0 1 10 0v3" fill="none" stroke="#8A7568" stroke-width="2"/>')
    o.append('    <text x="315" y="750" text-anchor="middle" font-size="9" font-weight="800" fill="#8A7568">商店</text>')
    return o


PAGES = [
    ("home", home("r03_330x288.png", 3, "继续第 4 关", "第一章 · 甜点星球 · 已通关 3 关"),
     "首页 · 3/12 部分揭晓"),
    ("home_00", home("r00_330x288.png", 0, "开始第 1 关", "第一章 · 甜点星球 · 尚未解锁"),
     "首页 · 0/12 全部剪影"),
    ("home_11", home("r11_330x288.png", 11, "继续第 12 关", "第一章 · 甜点星球 · 已通关 11 关"),
     "首页 · 11/12 接近完成"),
    # 12/12 两态：下一章已发布（示例）/ 下一章未发布（当前程序状态 PublishedChapters=1）
    ("home_12", home("r12_330x288.png", 12, "进入下一章 · 第 13 关", "第一章已完成 · 第二章已发布"),
     "首页 · 12/12 · 下一章已发布（示例）"),
    ("home_12_preparing", home("r12_330x288.png", 12, "新章节准备中", "暂不可进入 · 可查看收藏或返回", cta_disabled=True),
     "首页 · 12/12 · 下一章未发布（当前程序状态，主按钮禁用）"),
]


def wrap(body, h=844, aria=""):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'viewBox="0 0 390 %d" width="780" height="%d" role="img" aria-label="%s">\n%s\n%s\n</svg>\n'
            % (h, h * 2, aria, DEFS, "\n".join(body)))


if __name__ == "__main__":
    for name, body, aria in PAGES:
        p = os.path.join(BASE, "clean_%s.svg" % name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(wrap(body, aria=aria))
        print("wrote clean_%s.svg" % name)
    print("pure UI clean set done")
