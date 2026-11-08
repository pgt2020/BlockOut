"""BlockOut 珠子风格「全量」换肤：把剩余 15 个 UI 预制统一到三屏的视觉语言。

与 generate_beads_prefabs.py 的关系：
  - 三个主屏（HomePage / GameHud / SettlementPage）由 generate_beads_prefabs.py 全量生成，本脚本不碰。
  - 其余页面、弹窗、列表项由 generate_prefabs.py 生成，本脚本在原 prefab 上做「原地换肤」：
    只改 Image.m_Sprite / m_Color / m_Type 与 Text.m_Color，并新增纯视觉装饰节点
    (BeadsDecor / BeadsHoles)。不改任何 GameObject 名、fileID、MonoBehaviour 字段、
    脚本 GUID、.meta GUID、布局 RectTransform 数值，因此运行时绑定与业务逻辑完全不变。

可重复执行：首次运行把原始 prefab 备份到 backup/original_rest/，之后每次运行都先从备份
恢复再换肤，不会叠加装饰节点。不启动 Unity、不刷新 AssetDatabase。

运行顺序：
  python3 Tools/UIAuthoring/apply_beads_to_all.py
  python3 Tools/UIAuthoring/bind_authored_feedback.py
  python3 Tools/UIAuthoring/render_all_prefabs.py
"""
from pathlib import Path
import re, shutil, yaml
from PIL import Image  # 仅用于确认贴图存在，不生成图片

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI'
SPRITES = DEST / 'BeadsSprites'
BACKUP = Path(__file__).parent / 'backup' / 'original_rest'
RUNTIME = ROOT / 'Assets/BlockOut/Runtime/UI'
PACKAGE = next((ROOT / 'Library/PackageCache').glob('com.unity.ugui@*'))

# 三屏由 generate_beads_prefabs.py 生成，跳过；PopupLayer 是纯层容器，无可视元素，跳过。
SKIP = {'BlockOutHomePage', 'BlockOutGameHud', 'BlockOutSettlementPage', 'BlockOutPopupLayer'}
ITEMS = {'ChapterItem', 'RepeatItem', 'StoreHint', 'StoreHammer', 'StoreMagic'}

# 运行时由 Controller 按状态 SetActive 的互斥节点，静态默认态不该同时显示。
# 依据：BlockOutDialogsController(81/120)、BlockOutCollectionController(102)、
#       BlockOutStoreController(47)、BlockOutUIManager.Authoring(404/411/942)。
DEFAULT_INACTIVE = {
    'BlockOutFailPopup': {'FailExhaustedNote', 'FreeBadge'},
    'RepeatItem': {'Mark', 'Locked'},
    'StoreHint': {'LockBadge'},
    'StoreHammer': {'LockBadge'},
    'StoreMagic': {'LockBadge'},
}
# 确认弹窗离线生成版把固定标题与动态标题都写成「请确认」，静态重复。
# 改成项目烘焙版已有的文案（BlockOutUIManager.Authoring.cs:425），运行时仍会被覆盖。
STATIC_TEXT_FIX = {
    'BlockOutConfirmPopup': {'ConfirmTitle': '重开本关？'},
    'BlockOutAboutPopup': {'Description': '箭头方块消除\n拼图闯关 · 收集作品'},
    'BlockOutLoadingPage': {'Title': '箭头方块消除'},
}
# 列表项文案靠左，与左侧图标对齐。
LEFT_ALIGN = {'NameText', 'DescText', 'CoinText', 'Title', 'Subtitle'}

# 色板单点维护：直接复用三屏生成器的常量，避免 17 屏出现两套颜色。
import generate_beads_prefabs as THEME
WHITE = THEME.WHITE
INK = THEME.INK
INK_SOFT = THEME.INK_SOFT
ON_BG = THEME.ON_BG
ON_BG_SOFT = THEME.ON_BG_SOFT
CREAM = THEME.CREAM
GREEN = THEME.GREEN
PINK = THEME.PINK
GOLD = THEME.GOLD
BEAD_OFF = THEME.BEAD_OFF
OLD_INK = (.32, .22, .18, 1)
OLD_CORAL = (.97, .43, .37, 1)
OLD_MINT = (.66, .86, .76, 1)
OLD_MUTED = (.88, .85, .80, 1)
OLD_CREAM = (1, .963, .925, 1)

ICON_TINT = THEME.ICON_TINT
ICON_NAMES = set(ICON_TINT) | {'gear', 'pause', 'close', 'coin'}
# 深底上的文字与白卡里的文字必须用两套对比色：沿父链找最近的浅色容器。
LIGHT_HINT = ('Card', 'Panel', 'Bar', 'Nav', 'Viewport', 'Switch', 'Pill',
              'Track', 'Item', 'Slot', 'Retry', 'Tag', 'Badge')
# 弹窗卡片顶部的悬浮徽章，填补大留白并给出视觉锚点
BADGE_ICON = {
    'BlockOutPausePopup': ('icon_pause', INK),
    'BlockOutFailPopup': ('icon_heart', PINK),
    'BlockOutConfirmPopup': ('icon_gear', INK),
    'BlockOutGuidePopup': ('icon_bulb', (1, .58, .12, 1)),
    'BlockOutAboutPopup': ('icon_coin', WHITE),
}
# 列表页静态态改造：金币胶囊、规整空态卡、格子孔板。
# 装饰全部挂在原本就由 Controller 控制显隐的 GO 上（StoreEmptyText /
# CollectionEmptyText），运行时 SetActive 会连同装饰一起切换，
# 不会和运行时实例化出来的商品项 / 章节条目叠在一起。
LIST_FIX = {
    ('BlockOutCollectionPage', 'CollectionCoinText'): dict(
        rect=(262, 26, 104, 40), bg=('pill', WHITE, 1),
        icon=('icon_coin', WHITE, (10, 7, 26, 26)),
        text_color=INK, size=17, align=5),
    ('BlockOutStorePage', 'StoreCoinText'): dict(
        rect=(262, 26, 104, 40), bg=('pill', WHITE, 1),
        icon=('icon_coin', WHITE, (10, 7, 26, 26)),
        text_color=INK, size=17, align=5),
    ('BlockOutCollectionPage', 'CollectionEmptyText'): dict(
        rect=(0, 0, 342, 56), bg=('pill', WHITE, 1),
        icon=('icon_lock', INK_SOFT, (14, 12, 32, 32)),
        text='还没有拼片\n完成关卡即可解锁完整作品',
        text_color=INK, size=13, align=4),
    ('BlockOutStorePage', 'StoreEmptyText'): dict(
        rect=(24, 240, 342, 200), bg=('panel', CREAM, 1),
        icon=('icon_bulb', (1, .58, .12, 1), (131, 8, 64, 64)),
        text='道具商店准备中\n完成关卡即可解锁道具礼包',
        text_color=INK, size=16, align=4),
    ('BlockOutCollectionPage', 'Cells'): dict(
        bg=('slots', WHITE, 0)),
    # 章节条目：金色珠子改成作品缩略封面，锁图标用深墨蓝重新染色
    ('ChapterItem', 'Thumbnail'): dict(image=('art_home', WHITE, 0, 1)),
    ('ChapterItem', 'LockIcon'): dict(image=('icon_lock', INK, 0, 1)),
}

BUTTON_GUID = re.search(r'^guid: (\w+)', next(PACKAGE.rglob('Button.cs.meta')).read_text(
    encoding='utf-8-sig'), re.M).group(1)
IMAGE_GUID = re.search(r'^guid: (\w+)', next(PACKAGE.rglob('Image.cs.meta')).read_text(
    encoding='utf-8-sig'), re.M).group(1)


class Dumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def ref(n=0):
    return {'fileID': n}


def vec(x=0, y=0):
    return {'x': x, 'y': y}


def rgba(c):
    return dict(zip(('r', 'g', 'b', 'a'), c))


def meta_guid(path):
    return re.search(r'^guid: (\w+)', Path(str(path) + '.meta').read_text(
        encoding='utf-8-sig'), re.M).group(1)


def sprite(name):
    f = SPRITES / (name + '.png')
    if not f.exists():
        raise FileNotFoundError('缺少珠子风格贴图: ' + str(f))
    return {'fileID': 21300000, 'guid': meta_guid(f), 'type': 3}


SPR = {n: sprite(n) for n in [
    'sky', 'decor', 'holes', 'panel', 'plate', 'plate_soft', 'pill', 'circle',
    'bead', 'btn_green', 'btn_pink', 'btn_white', 'art_home', 'art_board',
    'art_settle', 'grid', 'slots', 'brand'] + ['icon_' + n for n in sorted(ICON_NAMES)]}

# 旧贴图 guid -> 名字，用于识别图标
GUID2SPRITE = {}
for m in (ROOT / 'Assets').rglob('*.meta'):
    try:
        g = re.search(r'^guid: (\w+)', m.read_text(encoding='utf-8-sig', errors='ignore'), re.M)
    except OSError:
        continue
    if g:
        GUID2SPRITE[g.group(1)] = m.with_suffix('').stem


def parse(path):
    s = path.read_text(encoding='utf-8-sig')
    heads = list(re.finditer(r'^--- !u!(\d+) &(-?\d+).*\n', s, re.M))
    docs = []
    for i, h in enumerate(heads):
        chunk = s[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(s)]
        d = yaml.safe_load(chunk)
        key = next(iter(d))
        docs.append([int(h.group(1)), int(h.group(2)), key, d[key]])
    return docs


def dump(docs, path):
    out = '%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'
    for cls, fid, name, data in docs:
        out += f'--- !u!{cls} &{fid}\n' + yaml.dump(
            {name: data}, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=140)
    path.write_text(out, encoding='utf-8')


def near(a, b, eps=.06):
    return all(abs(x - y) < eps for x, y in zip(a[:3], b[:3]))


def colour(d):
    c = d.get('m_Color', {})
    return (float(c.get('r', 1)), float(c.get('g', 1)),
            float(c.get('b', 1)), float(c.get('a', 1)))


def is_popup(stem):
    return ('Popup' in stem and stem != 'BlockOutPopupLayer') or stem == 'BlockOutSettingsPage'


def button_kind(name, c, stem):
    """返回 (sprite_name, 文字色)。颜色为主，名字为辅。"""
    if name == 'FailReviveBtn':
        return 'btn_pink', WHITE
    if name in ('ConfirmCancelBtn', 'AboutCloseBtn', 'SettingsCloseBtn',
                'CollectionBigCloseBtn', 'FailQuitBtn', 'SettingsAboutBtn') or \
            name.endswith('BackBtn') or name.endswith('QuitBtn'):
        return 'btn_white', INK
    if name.startswith('Settings') and name.endswith('Switch'):
        return 'btn_white', INK
    if name.startswith(('Nav', 'CollectionNav', 'StoreNav', 'HomeNav')):
        return ('btn_green', WHITE) if near(c, OLD_MINT) else ('btn_white', INK)
    if near(c, WHITE) and not any(k in name for k in
                                  ('Resume', 'Revive', 'Ok', 'Buy', 'Dismiss', 'Retry',
                                   'ViewBig', 'Restart', 'Next', 'Start')):
        return 'btn_white', INK
    return 'btn_green', WHITE


def classify(name, stem, c, is_btn, spr_file, typ, is_root):
    """返回 dict：sp / color / type / preserve / holes / keep。None 表示保持原样。"""
    if name == 'DesignSurface':
        # 弹窗保留一点通透感，页面用不透明天空渐变
        return {'sp': 'sky', 'color': WHITE if not is_popup(stem) else (1, 1, 1, .93),
                'type': 0, 'preserve': 0}
    if spr_file is None and c[3] < .6 and c[0] < .15:
        return None                                   # 遮罩 / 透明容器，保持
    if is_root and stem in ITEMS:
        # 列表项根节点是「一张卡」，即使挂了 Button 也不能套按钮贴图。
        # ChapterItem 是 342×72 的横条，同样用九宫格白卡，圆角不随宽度拉伸变形。
        if stem == 'ChapterItem':
            return {'sp': 'pill', 'color': WHITE, 'type': 1, 'preserve': 0,
                    'holes': True}
        return {'sp': 'plate_soft', 'color': WHITE, 'type': 1,
                'preserve': 0, 'holes': True}
    if name in ('BeadsDecor', 'BeadsHoles', 'HolesLayer'):
        return None
    if name.startswith('Region_'):
        return {'sp': 'bead', 'color': BEAD_OFF, 'type': 0, 'preserve': 1}
    if name in ('CollectionBigLayer',):
        return None                                   # 大图预览黑色遮罩
    if name in ('ContentViewport', 'StoreViewport', 'HomeArtViewport',
                'SettleRevealRoot', 'CollectionThumbRoot', 'CollectionBigRoot'):
        if spr_file is None:
            return None
        return {'sp': 'plate', 'color': WHITE, 'type': 0, 'preserve': 0}
    if 'ProgressFill' in name:
        return {'sp': 'pill', 'color': GREEN, 'type': 3, 'preserve': 0}
    if name == 'BottomNav':
        return {'sp': 'pill', 'color': WHITE, 'type': 1, 'preserve': 0}
    if name in ('Card', 'SummaryCard', 'RepeatCard', 'RetryBar'):
        if stem == 'BlockOutSettingsPage' and name == 'Card':
            # 设置页原来是整屏米白大卡，改成深色磨砂玻璃，与夜空底统一
            return {'sp': 'plate_soft', 'color': (.16, .15, .34, .92),
                    'type': 1, 'preserve': 0, 'holes': True}
        return {'sp': 'panel', 'color': CREAM, 'type': 1,
                'preserve': 0, 'holes': True}
    if is_btn:
        sp, _ = button_kind(name, c, stem)
        return {'sp': sp, 'color': WHITE, 'type': 1, 'preserve': 0}
    if name == 'Track':
        return {'sp': 'pill', 'color': GREEN, 'type': 1, 'preserve': 0}
    if name == 'Knob':
        return {'sp': 'circle', 'color': WHITE, 'type': 0, 'preserve': 1}
    if name in ('Thumbnail', 'Background', 'Mark', 'FreeBadge'):
        col = (GOLD if name in ('Thumbnail', 'Mark', 'FreeBadge')
               else GREEN if name in ('Background',) else BEAD_OFF)
        return {'sp': 'bead' if name != 'FreeBadge' else 'pill',
                'color': col, 'type': 0, 'preserve': 1}
    if name == 'LockIcon' or name == 'LockBadge' or spr_file == 'lock':
        return {'sp': 'icon_lock', 'color': INK_SOFT, 'type': 0, 'preserve': 1}
    if spr_file in ICON_TINT:
        return {'sp': 'icon_' + spr_file, 'color': ICON_TINT[spr_file],
                'type': 0, 'preserve': 1}
    if spr_file == 'check':
        return {'sp': 'bead', 'color': GREEN, 'type': 0, 'preserve': 1}
    if is_root and stem in ITEMS:
        return {'sp': 'plate_soft', 'color': WHITE, 'type': 1, 'preserve': 0, 'holes': True}
    if spr_file in ('round', 'content_card') or typ == 1:
        return {'sp': 'plate_soft', 'color': WHITE, 'type': 1, 'preserve': 0}
    return None


def text_colour(c, button_text=None, on_dark=False):
    """深底用近白文字，白卡里用深墨蓝；按钮文字由 button_kind 决定，优先级最高。"""
    if button_text is not None:
        return button_text
    if on_dark:
        return ON_BG_SOFT if near(c, OLD_MUTED, .08) else ON_BG
    if near(c, WHITE, .05):
        return INK
    if near(c, OLD_MUTED, .08):
        return INK_SOFT
    return INK


def new_image_component(go_fid, cr_fid, im_fid, sp_name, color, typ=0):
    """给一个原本没有 Image 的 GameObject 补背景图（不改变任何已有组件与字段）。"""
    common = {'m_ObjectHideFlags': 0, 'm_CorrespondingSourceObject': ref(),
              'm_PrefabInstance': ref(), 'm_PrefabAsset': ref()}
    cr = dict(common, m_GameObject=ref(go_fid), m_CullTransparentMesh=1)
    im = dict(common, m_GameObject=ref(go_fid), m_Enabled=1, m_EditorHideFlags=0,
              m_Script={'fileID': 11500000, 'guid': IMAGE_GUID, 'type': 3},
              m_Name='', m_EditorClassIdentifier='', m_Material=ref(),
              m_Color=rgba(color), m_RaycastTarget=0, m_Maskable=1,
              m_OnCullStateChanged={'m_PersistentCalls': {'m_Calls': []}},
              m_Sprite=SPR[sp_name], m_Type=typ, m_PreserveAspect=0, m_FillCenter=1,
              m_FillMethod=0, m_FillAmount=1, m_FillClockwise=1, m_FillOrigin=0,
              m_UseSpriteMesh=0, m_PixelsPerUnitMultiplier=1)
    return [(222, cr_fid, 'CanvasRenderer', cr), (114, im_fid, 'MonoBehaviour', im)]


def new_decor_node(go_fid, rt_fid, cr_fid, im_fid, name, sp, color,
                   typ, parent_rt, stretch=True, box=(0, 0, 390, 844),
                   pos=(0, 0)):
    """构造一个纯装饰 Image 节点（4 个文档），不参与任何 View 字段绑定。"""
    common = {'m_ObjectHideFlags': 0, 'm_CorrespondingSourceObject': ref(),
              'm_PrefabInstance': ref(), 'm_PrefabAsset': ref()}
    go = dict(common, serializedVersion=6,
              m_Component=[{'component': ref(x)} for x in (rt_fid, cr_fid, im_fid)],
              m_Layer=5, m_Name=name, m_TagString='Untagged', m_IsActive=1)
    rt = dict(common, m_GameObject=ref(go_fid),
              m_LocalRotation={'x': 0, 'y': 0, 'z': 0, 'w': 1},
              m_LocalPosition={'x': 0, 'y': 0, 'z': 0},
              m_LocalScale={'x': 1, 'y': 1, 'z': 1}, m_Children=[],
              m_Father=ref(parent_rt), m_LocalEulerAnglesHint={'x': 0, 'y': 0, 'z': 0},
              m_AnchorMin=vec(0, 0) if stretch else vec(0, 1),
              m_AnchorMax=vec(1, 1) if stretch else vec(0, 1),
              m_AnchoredPosition=vec() if stretch else vec(pos[0], -pos[1]),
              m_SizeDelta=vec(0, 0) if stretch else vec(box[2], box[3]),
              m_Pivot=vec(.5, .5) if stretch else vec(0, 1))
    cr = dict(common, m_GameObject=ref(go_fid), m_CullTransparentMesh=1)
    im = dict(common, m_GameObject=ref(go_fid), m_Enabled=1, m_EditorHideFlags=0,
              m_Script={'fileID': 11500000, 'guid': IMAGE_GUID, 'type': 3},
              m_Name='', m_EditorClassIdentifier='', m_Material=ref(),
              m_Color=rgba(color), m_RaycastTarget=0, m_Maskable=1,
              m_OnCullStateChanged={'m_PersistentCalls': {'m_Calls': []}},
              m_Sprite=SPR[sp], m_Type=typ, m_PreserveAspect=0, m_FillCenter=1,
              m_FillMethod=0, m_FillAmount=1, m_FillClockwise=1, m_FillOrigin=0,
              m_UseSpriteMesh=0, m_PixelsPerUnitMultiplier=1)
    return [(1, go_fid, 'GameObject', go), (224, rt_fid, 'RectTransform', rt),
            (222, cr_fid, 'CanvasRenderer', cr), (114, im_fid, 'MonoBehaviour', im)]


def reskin(path, stem):
    docs = parse(path)
    byid = {fid: (cls, name, data) for cls, fid, name, data in docs}
    go_by_rt = {}
    rt_by_go = {}
    parent_rt = {}
    for cls, fid, _, d in docs:
        if cls == 224:
            go_by_rt[fid] = d['m_GameObject']['fileID']
            rt_by_go[d['m_GameObject']['fileID']] = fid
            for ch in d.get('m_Children', []):
                parent_rt[ch['fileID']] = fid

    def components(go_fid):
        g = byid.get(go_fid)
        if not g:
            return []
        return [byid[c['component']['fileID']][2] for c in g[2].get('m_Component', [])
                if c['component']['fileID'] in byid]

    def on_dark_background(go_fid):
        """沿父链向上找浅色容器；一路到 DesignSurface 都没有 → 文字落在深蓝紫背景上。"""
        if stem in ITEMS:
            return False
        rt = rt_by_go.get(go_fid)
        seen = set()
        for _ in range(12):
            if not rt or rt in seen:
                break
            seen.add(rt)
            g = go_by_rt.get(rt)
            if g is None:
                break
            name = byid[g][2].get('m_Name', '')
            if stem == 'BlockOutSettingsPage' and name == 'Card':
                return True          # 深色磨砂卡，按深底处理
            if any(k in name for k in LIGHT_HINT) or name.endswith(('Btn', 'Button')):
                return False
            if name == 'DesignSurface':
                return True
            rt = parent_rt.get(rt)
        return True

    # 按钮文字色：先算出每个按钮 GO 应使用的文字色，供子节点 Text 使用
    btn_text = {}
    for cls, fid, _, d in docs:
        if cls != 1:
            continue
        comps = components(fid)
        if not any('m_TargetGraphic' in c for c in comps):
            continue
        img = next((c for c in comps if 'm_Sprite' in c), None)
        if img is None:
            continue
        _, tcol = button_kind(d['m_Name'], colour(img), stem)
        rt = rt_by_go.get(fid)
        for ch in byid[rt][2].get('m_Children', []) if rt in byid else []:
            child_go = go_by_rt.get(ch['fileID'])
            if child_go:
                btn_text[child_go] = tcol

    added = []
    extra = []
    next_id = max(abs(fid) for _, fid, _, _ in docs) + 1
    stats = {'images': 0, 'texts': 0, 'holes': 0, 'decor': 0}

    for cls, fid, _, d in docs:
        if cls != 1:
            continue
        name = d['m_Name']
        comps = components(fid)
        imgs = [c for c in comps if 'm_Sprite' in c]
        texts = [c for c in comps if 'm_Text' in c]
        if name in DEFAULT_INACTIVE.get(stem, set()):
            d['m_IsActive'] = 0
        is_btn = any('m_TargetGraphic' in c for c in comps)
        rt = rt_by_go.get(fid)
        is_root = rt is not None and byid[rt][2].get('m_Father', ref())['fileID'] == 0
        h = float(byid[rt][2].get('m_SizeDelta', {}).get('y', 0)) if rt in byid else 0

        for im in imgs:
            old = im.get('m_Sprite', {}) or {}
            old_guid = old.get('guid', '')
            spr_file = GUID2SPRITE.get(old_guid) if old_guid else None
            c = colour(im)
            rule = classify(name, stem, c, is_btn, spr_file,
                            int(im.get('m_Type', 0)), is_root)
            if rule is None:
                continue
            # 新控件贴图圆角半径与九宫格边界都是 8px，任意高度切片都规整，
            # 不再需要「矮按钮改 Simple 拉伸」的兜底。
            im['m_Sprite'] = SPR[rule['sp']]
            im['m_Color'] = rgba(rule['color'])
            im['m_Type'] = rule['type']
            im['m_PreserveAspect'] = int(rule.get('preserve', 0))
            im['m_FillCenter'] = 1
            im['m_RaycastTarget'] = 1 if (is_btn or im.get('m_RaycastTarget')) else 0
            stats['images'] += 1

            if rule.get('holes') and rt is not None:
                ids = [next_id + i for i in range(4)]
                next_id += 4
                extra += new_decor_node(*ids, 'BeadsHoles', 'holes', (1, 1, 1, .55),
                                        2, rt)
                byid[rt][2].setdefault('m_Children', []).insert(0, ref(ids[1]))
                stats['holes'] += 1
                added.append(rt)

        for t in texts:
            t['m_Color'] = rgba(text_colour(colour(t), btn_text.get(fid),
                                            on_dark_background(fid)))
            if name in STATIC_TEXT_FIX.get(stem, {}):
                t['m_Text'] = STATIC_TEXT_FIX[stem][name]
            if stem in ITEMS and name in LEFT_ALIGN:
                t.setdefault('m_FontData', {})['m_Alignment'] = 3
            stats['texts'] += 1

    # ---- 列表页静态态商业化：金币胶囊 / 规整空态卡 / 格子孔板 ----
    def add_bg_image(go_fid, sp, color, typ):
        nonlocal next_id
        cr_id, im_id = next_id, next_id + 1
        next_id += 2
        extra.extend(new_image_component(go_fid, cr_id, im_id, sp, color, typ))
        comps = byid[go_fid][2].setdefault('m_Component', [])
        # 背景必须排在 Text 之前，Unity 与预览器都按组件顺序绘制
        comps[1:1] = [{'component': ref(cr_id)}, {'component': ref(im_id)}]
        stats['images'] += 1

    def add_child_image(go_fid, name, sp, color, x, y, w, h):
        nonlocal next_id
        ids = [next_id + k for k in range(4)]
        next_id += 4
        prt = rt_by_go[go_fid]
        extra.extend(new_decor_node(*ids, name, sp, color, 0, prt,
                                    stretch=False, box=(0, 0, w, h), pos=(x, y)))
        byid[prt][2].setdefault('m_Children', []).append(ref(ids[1]))
        stats['decor'] += 1

    for cls, fid, _, d in docs:
        if cls != 1:
            continue
        rule = LIST_FIX.get((stem, d['m_Name']))
        if not rule:
            continue
        rt = rt_by_go.get(fid)
        if 'rect' in rule:
            x, y, w, h = rule['rect']
            byid[rt][2]['m_AnchoredPosition'] = {'x': x, 'y': -y}
            byid[rt][2]['m_SizeDelta'] = {'x': w, 'y': h}
        if 'image' in rule:
            sp, c, typ, preserve = rule['image']
            for im in [c for c in components(fid) if 'm_Sprite' in c]:
                im['m_Sprite'] = SPR[sp]
                im['m_Color'] = rgba(c)
                im['m_Type'] = typ
                im['m_PreserveAspect'] = preserve
        if 'bg' in rule:
            sp, c, typ = rule['bg']
            add_bg_image(fid, sp, c, typ)
        if 'icon' in rule:
            sp, c, (x, y, w, h) = rule['icon']
            add_child_image(fid, 'BeadsListIcon', sp, c, x, y, w, h)
        for t in [c for c in components(fid) if 'm_Text' in c]:
            if 'text' in rule:
                t['m_Text'] = rule['text']
            t['m_Color'] = rgba(rule.get('text_color', INK))
            fd = t.setdefault('m_FontData', {})
            fd['m_FontSize'] = rule.get('size', 16)
            fd['m_Alignment'] = rule.get('align', 4)

    # 每个页面在 DesignSurface 下加一层散珠装饰，放到子节点最前面（最底层）
    surface_rt = None
    surface_go = None
    for cls, fid, _, d in docs:
        if cls == 1 and d['m_Name'] == 'DesignSurface':
            surface_rt = rt_by_go.get(fid)
            surface_go = fid
            break
    if surface_rt is not None:
        # 弹窗的 DesignSurface 原本没有 Image（只靠根节点半透明遮罩），
        # 这里补一层半透明天空渐变，保持与三屏同色系。
        if not any('m_Sprite' in c for c in components(surface_go)):
            cr_id, im_id = next_id, next_id + 1
            next_id += 2
            extra += new_image_component(surface_go, cr_id, im_id, 'sky',
                                         (1, 1, 1, .72), 0)
            comps = byid[surface_go][2].setdefault('m_Component', [])
            comps[1:1] = [{'component': ref(cr_id)}, {'component': ref(im_id)}]
            stats['images'] += 1
        ids = [next_id + i for i in range(4)]
        next_id += 4
        decor_col = (1, 1, 1, .6) if is_popup(stem) else WHITE
        extra += new_decor_node(*ids, 'BeadsDecor', 'decor', decor_col, 0, surface_rt)
        byid[surface_rt][2].setdefault('m_Children', []).insert(0, ref(ids[1]))
        stats['decor'] += 1

    # 弹窗悬浮徽章：挂在卡片下、顶部露出 36px，纯装饰不参与字段绑定
    if stem in BADGE_ICON and surface_rt is not None:
        card_rt = None
        for cls, fid, _, d in docs:
            if cls == 1 and d['m_Name'] == 'Card':
                card_rt = rt_by_go.get(fid)
                break
        if card_rt is not None:
            cw = float(byid[card_rt][2].get('m_SizeDelta', {}).get('x', 340)) or 340
            bi = [next_id + k for k in range(4)]
            next_id += 4
            extra += new_decor_node(*bi, 'BeadsBadge', 'circle', GOLD, 0,
                                    card_rt, stretch=False, box=(0, 0, 80, 80),
                                    pos=(cw / 2 - 40, -56))
            ic, col = BADGE_ICON[stem]
            ii = [next_id + k for k in range(4)]
            next_id += 4
            extra += new_decor_node(*ii, 'BeadsBadgeIcon', ic, col, 0,
                                    bi[1], stretch=False, box=(0, 0, 48, 48),
                                    pos=(16, 16))
            for doc in extra:
                if doc[0] == 224 and doc[1] == bi[1]:
                    doc[3].setdefault('m_Children', []).append(ref(ii[1]))
            byid[card_rt][2].setdefault('m_Children', []).append(ref(bi[1]))
            stats['decor'] += 1

    # 加载页品牌层：金环作品徽章 + 12 颗拼片珠，中间透明带避开标题
    if stem == 'BlockOutLoadingPage' and surface_rt is not None:
        ids = [next_id + k for k in range(4)]
        next_id += 4
        extra.extend(new_decor_node(*ids, 'BeadsBrand', 'brand', WHITE, 0,
                                    surface_rt, stretch=False,
                                    box=(0, 0, 390, 260), pos=(0, 200)))
        ch = byid[surface_rt][2].setdefault('m_Children', [])
        ch.insert(1, ref(ids[1]))
        stats['decor'] += 1

    # 图鉴 / 商店的 BottomNav 在原始生成顺序里排在滚动内容之前，内容会盖住导航。
    # 只调整同层 children 顺序（无代码按索引取子节点），把导航放到内容之后、
    # 大图预览层之前。
    if surface_rt is not None and stem in ('BlockOutCollectionPage', 'BlockOutStorePage'):
        ch = byid[surface_rt][2].get('m_Children', [])

        def child_name(r):
            g = go_by_rt.get(r['fileID'])
            return byid[g][2]['m_Name'] if g in byid else ''

        nav = next((r for r in ch if child_name(r) == 'BottomNav'), None)
        if nav is not None:
            ch.remove(nav)
            big = next((i for i, r in enumerate(ch) if 'BigLayer' in child_name(r)), None)
            ch.insert(big if big is not None else len(ch), nav)

    dump(docs + extra, path)
    return stats


# 字体层级：项目只有一份 Regular 中文字体，不做 faux bold。
# R8 曾用 m_FontStyle=1 给标题/按钮加粗，但伪粗体在 12~16px 中文上会糊成墨块，
# 已回退；层级改由字号（<12px 统一抬到 12px）与 INK_SOFT 对比度建立。
def polish_typography():
    changed = 0
    for path in sorted(DEST.rglob('*.prefab')):
        docs = parse(path)
        dirty = False
        for cls, fid, _, d in docs:
            if cls != 114 or 'm_Text' not in d:
                continue
            fd = d.setdefault('m_FontData', {})
            if int(fd.get('m_FontSize', 16)) < 12:
                fd['m_FontSize'] = 12
                fd['m_MinSize'] = 12
                fd['m_MaxSize'] = max(12, int(fd.get('m_MaxSize', 12)))
                changed += 1
                dirty = True
            if int(fd.get('m_FontStyle', 0)) != 0:
                fd['m_FontStyle'] = 0
                dirty = True
        if dirty:
            dump(docs, path)
    return changed


def backup_all():
    BACKUP.mkdir(parents=True, exist_ok=True)
    files = []
    for p in sorted(DEST.rglob('*.prefab')):
        if p.stem in SKIP:
            continue
        files.append(p)
    if not (BACKUP / 'BlockOutPausePopup.prefab').exists():
        for p in files:
            rel = p.relative_to(DEST)
            dst = BACKUP / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            for suffix in ('', '.meta'):
                src = Path(str(p) + suffix)
                if src.exists():
                    shutil.copy2(src, Path(str(dst) + suffix))
        print('原始预制已备份:', BACKUP)
    # 幂等：每次都从备份恢复，避免重复叠加装饰节点
    for p in files:
        rel = p.relative_to(DEST)
        src = BACKUP / rel
        if src.exists():
            shutil.copy2(src, p)
            m = Path(str(src) + '.meta')
            if m.exists():
                shutil.copy2(m, Path(str(p) + '.meta'))
    return files


if __name__ == '__main__':
    files = backup_all()
    total = {'images': 0, 'texts': 0, 'holes': 0, 'decor': 0}
    for p in files:
        st = reskin(p, p.stem)
        for k in total:
            total[k] += st[k]
        print(f'  换肤 {p.stem:32s} Image {st["images"]:3d} / Text {st["texts"]:3d} '
              f'/ 孔板 {st["holes"]} / 散珠 {st["decor"]}')
    print('合计:', total, '| 覆盖', len(files), '个预制')
    print('字号规范: 抬升', polish_typography(), '处小于 12px 的文字（不使用伪粗体）')
