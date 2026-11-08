"""UI 预制硬性布局自检（只读，不启动 Unity）。

逐屏把 RectTransform 还原成设计画布的绝对坐标，检查：
  1. 文字框互相重叠（Play Mode 里糊成一团的主要来源）
  2. 元素溢出设计画布（列表项按自身根节点尺寸单独定基准）
  3. 中文按字号估算放不下、会被 uGUI 折行的框 / 字号过小
  4. 九宫格边界大于目标高度，切片会把圆角挤成尖角
  5. 装饰性全屏 Image 仍开着 raycastTarget（会吃掉点击）
  6. 按钮没有任何可见文字（纯图标按钮需在白名单里）

与渲染器一致地模拟 VerticalLayoutGroup 的纵向累加，避免把静态
anchoredPosition=0 的滚动内容误判成重叠。

运行：python3 Tools/UIAuthoring/check_layout.py
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import render_all_prefabs as R

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI'
W, H = 390, 844

ITEMS = {'ChapterItem', 'RepeatItem', 'StoreHint', 'StoreHammer', 'StoreMagic'}
ICON_ONLY_BUTTONS = {'BoardPauseBtn', 'HomeSettingsBtn', 'SettleCloseDecor'}
# 这些全屏 Image 必须保留 raycast：弹窗根节点挡下层穿透、滚动视口要接拖拽、
# 大图预览遮罩要接点击关闭。它们是父节点，不会挡住自己的子按钮。
RAYCAST_OK = {'ContentViewport', 'StoreViewport', 'CollectionBigLayer',
              'CollectionBigRoot', 'BlockOutAboutPopup', 'BlockOutConfirmPopup',
              'BlockOutFailPopup', 'BlockOutGuidePopup', 'BlockOutPausePopup',
              'BlockOutSettingsPage'}


def collect(path):
    docs = R.parse(path)
    byid = {f: (c, n, d) for c, f, n, d in docs}
    go_by_rt = {f: d['m_GameObject']['fileID'] for c, f, n, d in docs if c == 224}
    root_rt = next(f for c, f, n, d in docs
                   if c == 224 and d['m_Father']['fileID'] == 0)

    is_item = path.stem in ITEMS
    if is_item:
        rd = byid[root_rt][2]
        cw, ch = float(rd['m_SizeDelta']['x']), float(rd['m_SizeDelta']['y'])
        cw, ch = (cw if cw > 1 else 342), (ch if ch > 1 else 112)
    else:
        cw, ch = W, H
    base = (0, 0, cw, ch)

    def walk(rt_fid, parent, trail, parent_active, is_root=False, shift_y=0.0):
        entry = byid.get(rt_fid)
        if not entry:
            return []
        rt = entry[2]
        r = (0, 0, cw, ch) if is_root else R.rect_of(rt, parent)
        x, y, w, h = r
        y += shift_y
        r = (x, y, w, h)
        go = byid.get(go_by_rt.get(rt_fid))
        if not go:
            return []
        gd = go[2]
        name = gd['m_Name']
        comps = [byid[q['component']['fileID']][2] for q in gd['m_Component']
                 if q['component']['fileID'] in byid]
        active = parent_active and int(gd.get('m_IsActive', 1))
        texts = [c for c in comps if 'm_Text' in c and str(c.get('m_Text', '')).strip()]
        imgs = [c for c in comps if 'm_Sprite' in c]
        is_btn = any('m_TargetGraphic' in c for c in comps)
        rows = [{
            'name': name, 'path': '/'.join(trail + [name]), 'rect': r,
            'active': active, 'texts': texts, 'imgs': imgs, 'btn': is_btn,
            # ScrollRect 的 Content 会滚动，静态 YAML 的 anchoredPosition 全为 0，
            # 精确还原需要运行时布局组件；其子树的越界/重叠不做硬性判定。
            'scroll': '/Content/' in '/'.join(trail + [name]),
        }]
        has_vlg = any('m_Spacing' in c and 'm_ChildAlignment' in c for c in comps)
        running = 0.0
        for child in rt.get('m_Children', []):
            if has_vlg:
                crt = byid.get(child['fileID'])
                if crt:
                    cr = R.rect_of(crt[2], r)
                    h_child = max(cr[3], 24)
                    rows += walk(child['fileID'], r, trail + [name], active,
                                 shift_y=running - (cr[1] - y))
                    running += h_child + 12
            else:
                rows += walk(child['fileID'], r, trail + [name], active)
        return rows

    return walk(root_rt, base, [], 1, is_root=True), (cw, ch)


def overlap(a, b):
    x = max(0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    y = max(0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    smaller = min(a[2] * a[3], b[2] * b[3]) or 1
    return x * y / smaller


def check(path):
    rows, (cw, ch) = collect(path)
    viewports = [r['rect'] for r in rows
                 if r['name'] in ('ContentViewport', 'StoreViewport')]
    for r in rows:
        if r['scroll'] and viewports:
            # 滚动内容被 RectMask2D 裁在视口内；静态推算到视口外的部分不会出现
            x, y, w, h = r['rect']
            r['clipped'] = not any(
                min(x + w, v[0] + v[2]) > max(x, v[0]) and
                min(y + h, v[1] + v[3]) > max(y, v[1]) for v in viewports)
        else:
            r['clipped'] = False
    rows = [r for r in rows if r['active']]
    problems = []
    text_rows = [r for r in rows if r['texts'] and not r['clipped']]

    for i, a in enumerate(text_rows):
        for b in text_rows[i + 1:]:
            if a['scroll'] and b['scroll']:
                continue
            if a['path'].startswith(b['path'] + '/') or b['path'].startswith(a['path'] + '/'):
                continue
            ratio = overlap(a['rect'], b['rect'])
            if ratio > .15:
                problems.append(f"文字重叠 {a['name']} × {b['name']} ({ratio:.0%})")

    for r in rows:
        x, y, w, h = r['rect']
        if (not r['scroll'] and w > 1 and h > 1
                and (x < -2 or y < -2 or x + w > cw + 2 or y + h > ch + 2)):
            if r['name'] not in ('DesignSurface', 'BeadsDecor', 'BeadsHoles'):
                problems.append(f"越界 {r['name']} ({x:.0f},{y:.0f},{w:.0f}×{h:.0f}) / 画布{cw:.0f}×{ch:.0f}")

        for t in r['texts']:
            txt = str(t.get('m_Text', '')).strip()
            size = int((t.get('m_FontData') or {}).get('m_FontSize', 14))
            cjk = sum(1 for c in txt if '\u4e00' <= c <= '\u9fff')
            need = cjk * size + (len(txt) - cjk) * size * .55
            if need > w * 1.35 and '\n' not in txt:
                problems.append(f"文字过窄 {r['name']} 「{txt[:12]}」 需≈{need:.0f}px 框宽{w:.0f}px")
            if size < 10:
                problems.append(f"字号过小 {r['name']} 「{txt[:10]}」 {size}px")

        for im in r['imgs']:
            if int(im.get('m_Type', 0)) != 1:
                continue
            sp = im.get('m_Sprite') or {}
            b = R.BORDER.get(sp.get('guid', ''), (0, 0, 0, 0))
            if (b[1] + b[3]) >= h * .9 and h > 0:
                problems.append(f"九宫格挤角 {r['name']} 高{h:.0f} 边界{b[1]}+{b[3]}")

        if not r['btn'] and r['name'] not in RAYCAST_OK and w * h > cw * ch * .5:
            if any(int(im.get('m_RaycastTarget', 1)) == 1 for im in r['imgs']):
                problems.append(f"全屏装饰 Image 拦截点击 {r['name']}")

        if r['btn'] and not r['texts'] and r['name'] not in ICON_ONLY_BUTTONS:
            if not any(q['path'].startswith(r['path'] + '/') and q['texts'] for q in rows):
                problems.append(f"按钮无可见文字 {r['name']}")

    return rows, problems


if __name__ == '__main__':
    total = 0
    for p in sorted(UI.rglob('*.prefab')):
        if p.stem == 'BlockOutPopupLayer':
            continue
        rows, probs = check(p)
        total += len(probs)
        print(f"{'OK ' if not probs else str(len(probs)) + ' ':3s}{p.stem:32s} 节点{len(rows):3d}")
        for q in probs:
            print('    -', q)
    print(f'\n合计问题: {total}')
