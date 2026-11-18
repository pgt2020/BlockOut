# -*- coding: utf-8 -*-
"""对局页 prefab 的静态契约校验（不启动 Unity、不编译、不读 Console）。

校验的是「运行时能不能真的用起来」，不是好不好看：
  1. BlockOutBoardPageView 的每个序列化字段都已绑定，且绑到正确类型的组件上
  2. Relayout 按名字重排的节点全部存在（名字 = 节点名，不是字段名）
  3. 托盘是 BoardArea 的后代 —— 否则 BlockOutAppBuilder 的 SetAsFirstSibling 会让托盘盖住方块
  4. 一个 GameObject 上没有两个 Image（Image.color 会互相打架，且点击热区错乱）
  5. BoardArea 轴心 0.5/0.5（BoardView 以节点中心铺格）
  6. 关键矩形等于 390×844 基线数值（prefab 与 BuildBoardScreen/Relayout 同一套坐标）
  7. 所有 fileID 引用都能解析到本文档内对象

用法：python Tools/UIAuthoring/verify_board_page.py
"""
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PREFAB = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI/BlockOutGameHud.prefab'

# 字段 → (期望组件标签, 允许的多个候选)
FIELD_TYPES = {
    'BoardArea': 'RectTransform', 'BoardPauseBtn': 'Button', 'BoardLevelTitle': 'Text',
    'BoardLevelSub': 'Text', 'BoardTimerPill': 'RectTransform', 'BoardTimerText': 'Text',
    'BoardRemainingText': 'Text', 'BoardHintPill': 'Text', 'BoardProgressFill': 'Image',
    'BoardProgressText': 'Text', 'BoardTray': 'RectTransform',
}
ARRAY_FIELDS = {'BoardHearts': 3}
TOOL_SLOTS = ['HintSlot', 'HammerSlot', 'MagicSlot']
SLOT_FIELDS = {'Button': 'Button', 'Icon': 'Image', 'CountText': 'Text', 'NameText': 'Text',
               'CondText': 'Text', 'Rect': 'RectTransform', 'CountBadge': 'GameObject',
               'LockBadge': 'GameObject'}

# Relayout 里的 (父节点, 节点名)。页面节点都在 DesignSurface 之下（BlockOutPageLayout 把它
# 固定成 390×844 设计盒再整体缩放），所以屏级节点的父是 DesignSurface 而不是屏根节点。
NAMED_NODES = [
    ('TopHUD', 'LevelTitle'), ('TopHUD', 'LevelSub'), ('TopHUD', 'PauseBtn'),
    ('TopHUD', 'LivesRow'), ('TopHUD', 'TimerPill'), ('TopHUD', 'ProgressBar'),
    ('TopHUD', 'ProgressText'), ('DesignSurface', 'BoardArea'),
    ('DesignSurface', 'RemainingText'), ('DesignSurface', 'HintPill'),
    ('DesignSurface', 'BottomToolbar'),
]

# 节点名 → (锚点min, 锚点max, 位置, 尺寸)；与 BuildBoardScreen / generate_prefabs 同值
EXPECTED_RECTS = {
    'BoardArea': ((.5, .5), (.5, .5), (0, 73), (318, 404)),
    'LevelTitle': ((.5, 1), (.5, 1), (0, -46), (240, 26)),
    'LevelSub': ((.5, 1), (.5, 1), (0, -72), (240, 14)),
    'PauseBtn': ((1, 1), (1, 1), (-24, -46), (40, 40)),
    'LivesRow': ((0, 1), (0, 1), (24, -88), (56, 16)),
    'TimerPill': ((0, 1), (0, 1), (24, -85), (64, 22)),
    'ProgressBar': ((.5, 1), (.5, 1), (0, -88), (196, 13)),
    'ProgressText': ((0, 1), (0, 1), (318, -87), (44, 15)),
    # Garden tray: below the playable area, so the counter cannot cover bottom-row blocks.
    'RemainingText': ((0, 1), (0, 1), (202, -574), (140, 18)),
    'HintPill': ((.5, 1), (.5, 1), (0, -642), (288, 28)),
    'BottomToolbar': ((.5, 0), (.5, 0), (0, 12), (319, 84)),
}


def load_docs(path):
    text = path.read_text(encoding='utf-8')
    heads = list(re.finditer(r'^--- !u!(\d+) &(-?\d+).*\n', text, re.M))
    docs = []
    for i, h in enumerate(heads):
        body = text[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        data = yaml.safe_load(body)
        key = next(iter(data))
        docs.append((int(h[1]), int(h[2]), key, data[key]))
    return docs


def main():
    docs = load_docs(PREFAB)
    byid = {i: (c, k, d) for c, i, k, d in docs}
    errors = []

    # 7. 引用完整性
    def walk_refs(v):
        if isinstance(v, dict):
            if 'fileID' in v and v['fileID'] != 0 and 'guid' not in v:
                if v['fileID'] not in byid:
                    errors.append('悬空引用 fileID=%s' % v['fileID'])
            for x in v.values():
                walk_refs(x)
        elif isinstance(v, list):
            for x in v:
                walk_refs(x)
    walk_refs([d for _, _, _, d in docs])

    gos = {i: d for c, i, k, d in docs if k == 'GameObject'}
    rts = {i: d for c, i, k, d in docs if k == 'RectTransform'}
    go_name = {i: d['m_Name'] for i, d in gos.items()}
    rt_of_go, go_of_rt = {}, {}
    for gi, d in gos.items():
        for comp in d['m_Component']:
            c, k, cd = byid[comp['component']['fileID']]
            if k == 'RectTransform':
                rt_of_go[gi] = cd
                go_of_rt[comp['component']['fileID']] = gi
    parent_go = {gi: go_of_rt.get(rt['m_Father']['fileID']) for gi, rt in rt_of_go.items()}

    def comp_types(gi):
        out = []
        for comp in gos[gi]['m_Component']:
            c, k, cd = byid[comp['component']['fileID']]
            if k == 'MonoBehaviour':
                out.append((comp['component']['fileID'], cd))
            else:
                out.append((comp['component']['fileID'], None, k))
        return out

    def types_of(gi):
        names = []
        for item in comp_types(gi):
            if len(item) == 3:
                names.append(item[2])
            else:
                cd = item[1]
                names.append('Image' if 'm_Sprite' in cd else
                             'Text' if 'm_FontData' in cd else
                             'Button' if 'm_OnClick' in cd else
                             'Custom')
        return names

    # 4. 每个 GameObject 只能有一个 Image
    for gi, name in go_name.items():
        n = types_of(gi).count('Image')
        if n > 1:
            errors.append('%s 上有 %d 个 Image' % (name, n))

    # 1. View 字段绑定
    view = next(((i, d) for c, i, k, d in docs if k == 'MonoBehaviour' and 'BoardArea' in d), None)
    if view is None:
        print('找不到 BlockOutBoardPageView（含 BoardArea 的 MonoBehaviour）')
        return 1
    _, vd = view
    for field, want in FIELD_TYPES.items():
        ref = vd.get(field)
        if not isinstance(ref, dict) or ref.get('fileID', 0) == 0:
            errors.append('%s 未绑定' % field)
            continue
        c, k, cd = byid[ref['fileID']]
        got = {'RectTransform': 'RectTransform', 'Animator': 'Animator'}.get(k) or \
              ('Image' if 'm_Sprite' in cd else 'Text' if 'm_FontData' in cd else
               'Button' if 'm_OnClick' in cd else 'Custom')
        if got != want:
            errors.append('%s 绑到了 %s（期望 %s）' % (field, got, want))
    for field, n in ARRAY_FIELDS.items():
        arr = vd.get(field)
        if not isinstance(arr, list) or len(arr) != n:
            errors.append('%s 数量=%s（期望 %d）' % (field, len(arr) if isinstance(arr, list) else arr, n))
        else:
            for ref in arr:
                c, k, cd = byid[ref['fileID']]
                if 'm_Sprite' not in cd:
                    errors.append('%s 中含非 Image 元素' % field)
    for slot in TOOL_SLOTS:
        d = vd.get(slot)
        if not isinstance(d, dict):
            errors.append('%s 未绑定' % slot)
            continue
        for key, want in SLOT_FIELDS.items():
            ref = d.get(key)
            if not isinstance(ref, dict) or ref.get('fileID', 0) == 0:
                errors.append('%s.%s 未绑定' % (slot, key))
                continue
            c, k, cd = byid[ref['fileID']]
            got = 'GameObject' if k == 'GameObject' else 'RectTransform' if k == 'RectTransform' else \
                  ('Image' if 'm_Sprite' in cd else 'Text' if 'm_FontData' in cd else
                   'Button' if 'm_OnClick' in cd else 'Custom')
            if got != want:
                errors.append('%s.%s 绑到了 %s（期望 %s）' % (slot, key, got, want))

    # 2. Relayout 依赖的节点名（父 → 子）
    for parent, child in NAMED_NODES:
        hit = [gi for gi, n in go_name.items()
               if n == child and go_name.get(parent_go.get(gi)) == parent]
        if not hit:
            errors.append('缺少节点 %s/%s' % (parent, child))

    # 3. 托盘必须是 BoardArea 的后代
    tray = [gi for gi, n in go_name.items() if n == 'BoardTray']
    area = [gi for gi, n in go_name.items() if n == 'BoardArea']
    if not tray or not area:
        errors.append('缺少 BoardTray 或 BoardArea')
    else:
        cur, chain = tray[0], []
        while cur is not None:
            cur = parent_go.get(cur)
            chain.append(go_name.get(cur))
            if cur is None:
                break
        if 'BoardArea' not in chain:
            errors.append('BoardTray 不是 BoardArea 的后代（会被 SetAsFirstSibling 顶到方块之上）')

    # 5. BoardArea 轴心
    if area:
        rt = rt_of_go[area[0]]
        if (rt['m_Pivot']['x'], rt['m_Pivot']['y']) != (0.5, 0.5):
            errors.append('BoardArea 轴心必须是 0.5/0.5，实际 %s' % rt['m_Pivot'])

    # 6. 关键矩形
    for name, (amin, amax, pos, size) in EXPECTED_RECTS.items():
        hit = [gi for gi, n in go_name.items() if n == name]
        if not hit:
            errors.append('缺少节点 %s' % name)
            continue
        rt = rt_of_go[hit[0]]
        got = ((rt['m_AnchorMin']['x'], rt['m_AnchorMin']['y']),
               (rt['m_AnchorMax']['x'], rt['m_AnchorMax']['y']),
               (rt['m_AnchoredPosition']['x'], rt['m_AnchoredPosition']['y']),
               (rt['m_SizeDelta']['x'], rt['m_SizeDelta']['y']))
        for label, a, b in zip(('锚点min', '锚点max', '位置', '尺寸'), got, (amin, amax, pos, size)):
            if abs(a[0] - b[0]) > 0.51 or abs(a[1] - b[1]) > 0.51:
                errors.append('%s 的%s 为 %s，基线应为 %s' % (name, label, a, b))

    print('文档 %d 个，GameObject %d 个' % (len(docs), len(gos)))
    if errors:
        print('校验失败 %d 项：' % len(errors))
        for e in errors:
            print('  - ' + e)
        return 1
    print('通过：字段绑定 / 节点名 / 托盘层级 / 单 Image / 轴心 / 基线矩形 / 引用完整性')
    return 0


if __name__ == '__main__':
    sys.exit(main())
