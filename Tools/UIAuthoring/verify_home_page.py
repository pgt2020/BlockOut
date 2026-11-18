"""首页 R2 还原的静态契约校验。只解析 prefab / C# 源码，不启动 Unity。

检查：View 字段绑定与组件类型、Relayout 节点名、负尺寸、整屏图不接点击、
四个入口结构（含文字描边）、CTA 真 Button、ScreenSkinMap 不再覆盖 Home/Board。
"""
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
PREFAB = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI/BlockOutHomePage.prefab'
VIEW = ROOT / 'Assets/BlockOut/Runtime/UI/Views/BlockOutHomeView.cs'
AUTHORING = ROOT / 'Assets/BlockOut/Runtime/UI/Views/BlockOutUIManager.Authoring.cs'
MANAGER = ROOT / 'Assets/BlockOut/Runtime/UI/Views/BlockOutUIManager.cs'
PKG = next((ROOT / 'Library/PackageCache').glob('com.unity.ugui@*'))

errors = []


def fail(msg):
    errors.append(msg)


def script_guid(name):
    for p in (PKG / 'Runtime/UGUI').rglob(name + '.cs'):
        meta = Path(str(p) + '.meta')
        if meta.exists():
            m = re.search(r'^guid: (\w+)', meta.read_text(encoding='utf-8-sig'), re.M)
            if m:
                return m.group(1)
    return None


GUID_CLASS = {script_guid(n): n for n in ('Button', 'Text', 'Image', 'Outline') if script_guid(n)}

text = PREFAB.read_text(encoding='utf-8')
heads = list(re.finditer(r'^--- !u!(\d+) &(-?\d+).*\n', text, re.M))
docs = []
for i, h in enumerate(heads):
    d = yaml.safe_load(text[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)])
    k = next(iter(d))
    docs.append((int(h[1]), int(h[2]), k, d[k]))
byid = {i: (c, k, d) for c, i, k, d in docs}
gos = {i: d for c, i, k, d in docs if k == 'GameObject'}
name_of = {i: d['m_Name'] for i, d in gos.items()}
by_name = {n: i for i, n in name_of.items()}
rt_of, comp_of, rt_to_go = {}, {}, {}
for go_id, go in gos.items():
    comps = []
    for x in go['m_Component']:
        cid = x['component']['fileID']
        c, k, d = byid[cid]
        comps.append((cid, k, d))
        if k == 'RectTransform':
            rt_of[go_id] = d
            rt_to_go[cid] = go_id
    comp_of[go_id] = comps


def component_kind(fid):
    if fid == 0 or fid not in byid:
        return '<null>'
    k, d = byid[fid][1:]
    if k == 'GameObject':
        return 'GameObject'
    if k == 'MonoBehaviour':
        return GUID_CLASS.get(d.get('m_Script', {}).get('guid'), 'MonoBehaviour')
    return k


def owner(fid):
    if fid == 0 or fid not in byid:
        return '<null>'
    k, d = byid[fid][1:]
    if k == 'GameObject':
        return d['m_Name']
    return name_of.get(d.get('m_GameObject', {}).get('fileID', 0), '?')


view = next((d for c, i, k, d in docs if k == 'MonoBehaviour' and 'HomeCtaButton' in d), None)
if view is None:
    fail('找不到 BlockOutHomeView 组件')
    sys.exit(1)

# 1. View 字段全部绑定且类型正确
src = VIEW.read_text(encoding='utf-8-sig')
required = [x.strip() for x in re.findall(r'public\s+[\w.\[\]]+\s+([^;{}]+);', src) for x in x.split(',')]
expect = {
    'HomeCtaButton': 'Button', 'HomeCtaTitle': 'Text', 'HomeCtaSub': 'Text',
    'HomeCoinText': 'Text', 'HomeSettingsBtn': 'Button', 'HomeGalleryBtn': 'Button',
    'HomeLevelTitle': 'Text', 'HomeCoinsButton': 'Button',
    'HomeSkinBtn': 'Button', 'HomeDailyBtn': 'Button', 'HomeAchievementBtn': 'Button',
}
for key in required:
    if key not in view or view[key].get('fileID', 0) == 0:
        fail(f'字段未绑定: {key}')
    elif key in expect:
        got = component_kind(view[key]['fileID'])
        if got != expect[key]:
            fail(f'{key} 指向 {owner(view[key]["fileID"])}/{got}，应为 {expect[key]}')

# 2. Relayout 中 Home 段引用的节点名（字段名 → prefab 节点名）
a = AUTHORING.read_text(encoding='utf-8-sig')
seg = a[a.index('// ---- Home（R2'):a.index('// ---- Board（R2')]
rename = {'GalleryBtn': 'HomeGalleryBtn', 'SkinBtn': 'HomeSkinBtn',
          'DailyBtn': 'HomeDailyBtn', 'AchievementBtn': 'HomeAchievementBtn'}
for name in re.findall(r'SetTop(?:Left|Right|Center)\(surface, "([^"]+)"', seg):
    if rename.get(name, name) not in by_name:
        fail(f'Relayout 引用的节点不存在: {name}')

# 3. 负尺寸
for go_id, rt in rt_of.items():
    s = rt['m_SizeDelta']
    if any(s[k]<0 and rt['m_AnchorMin'][k]==rt['m_AnchorMax'][k] for k in ('x','y')):
        fail(f'负尺寸节点: {name_of[go_id]} {s}')

# 4. 整屏背景不接点击且拉伸
bg_id = by_name.get('HomeBackground')
if bg_id is None:
    fail('缺少 HomeBackground')
else:
    bg = rt_of[bg_id]
    if bg['m_AnchorMin'] != {'x': 0, 'y': 0} or bg['m_AnchorMax'] != {'x': 1, 'y': 1}:
        fail('HomeBackground 未拉伸铺满')
    for _, k, d in comp_of[bg_id]:
        if k == 'MonoBehaviour' and 'm_RaycastTarget' in d and d['m_RaycastTarget']:
            fail('HomeBackground 仍在接收点击')

# 5. 四个入口：Button/Image/Icon/Label/Outline
for key in ('HomeGalleryBtn', 'HomeSkinBtn', 'HomeDailyBtn', 'HomeAchievementBtn'):
    go_id = by_name[owner(view[key]['fileID'])]
    kinds = [component_kind(x['component']['fileID']) for x in gos[go_id]['m_Component']]
    if not {'Button', 'Image'} <= set(kinds):
        fail(f'{key} 缺少真 Button/Image')
    child_ids = [rt_to_go[x['fileID']] for x in rt_of[go_id]['m_Children']]
    children = {name_of[i] for i in child_ids}
    if not {'Icon', 'Label'} <= children:
        fail(f'{key} 缺少 Icon/Label: {children}')
    label_id = next((i for i in child_ids if name_of[i] == 'Label'), None)
    if label_id is None:
        fail(f'{key} 找不到 Label 节点')
    else:
        kinds = [component_kind(x['component']['fileID']) for x in gos[label_id]['m_Component']]
        if 'Outline' not in kinds:
            fail(f'{key} 文字缺少白色描边 Outline')

# 6. 参考皮肤不再覆盖 Home / Board
m = MANAGER.read_text(encoding='utf-8-sig')
skin_seg = m[m.index('ScreenSkinMap ='):m.index('LayerSkinMap =')]
for screen in ('Home', 'Board'):
    if re.search(r'BlockOutScreenId\.' + screen + r'\s*,\s*"s\d"', skin_seg):
        fail(f'{screen} 仍被全屏参考图覆盖')

if errors:
    for e in errors:
        print('FAIL', e)
    sys.exit(1)
print('通过：View 字段 / 组件类型 / 节点名 / 尺寸 / 背景层 / 四入口 / 描边 / 皮肤映射')
