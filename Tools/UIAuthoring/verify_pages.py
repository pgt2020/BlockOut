"""全部 UI prefab 的静态契约校验（不开 Unity）。

覆盖：
1. 每个 MonoBehaviour 里指向本 prefab 的 fileID 都能解析（无悬空引用）
2. RectTransform 无负尺寸（拉伸锚点换算错误的标志）
3. 每个 Image 的 sprite guid 都能解析到工程内的 .meta（贴图没丢）
4. 关键页面（加载/图库/商店/失败/结算/暂停/确认）的 View 字段都绑定了正确组件类型
"""
import re
import sys
import glob
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI'

# 字段 → 期望组件类型（None = GameObject 引用）
EXPECT = {
    'BlockOutLoadingPage': {},
    'BlockOutCollectionPage': {
        'CollectionBackBtn': 'Button', 'CollectionCoinText': 'Text',
        'CollectionChapterText': 'Text', 'CollectionPieceText': 'Text',
        'CollectionEmptyText': 'Text', 'CollectionProgressFill': 'Image',
        'CollectionChapterList': 'RectTransform', 'CollectionContent': 'RectTransform',
        'CollectionRepeatGrid': 'RectTransform', 'RepeatListRoot': 'RectTransform',
        'ChapterItemPrefab': 'prefab', 'RepeatItemPrefab': 'prefab',
        'CollectionNavHomeBtn': 'Button', 'CollectionNavCollectionBtn': 'Button',
        'CollectionNavStoreBtn': 'Button',
    },
    'BlockOutStorePage': {
        'StoreBackBtn': 'Button', 'StoreCoinText': 'Text', 'StoreListRoot': 'RectTransform',
        'StoreEmptyText': 'Text', 'StoreNavHomeBtn': 'Button',
        'StoreNavCollectionBtn': 'Button', 'StoreNavStoreBtn': 'Button',
    },
    'BlockOutFailPopup': {
        'FailReasonText': 'Text', 'FailReviveLabel': 'Text', 'FailReviveNote': 'Text',
        'FailExhaustedNote': 'Text', 'FailReviveBtn': 'Button', 'FailRestartBtn': 'Button',
        'FailQuitBtn': 'Button', 'FailFreeBadge': 'GameObject',
    },
    'BlockOutSettlementPage': {
        'SettleTitleText': 'Text', 'SettlePieceText': 'Text', 'SettleRewardText': 'Text',
        'SettleNoteText': 'Text', 'SettleNextBtn': 'Button', 'SettleReplayBtn': 'Button',
        'SettleCollectionBtn': 'Button', 'SettleHomeBtn': 'Button', 'SettleLevelImage': 'Image',
    },
    'BlockOutPausePopup': {
        'PauseResumeBtn': 'Button', 'PauseRestartBtn': 'Button',
        'PauseSettingsBtn': 'Button', 'PauseQuitBtn': 'Button',
    },
    'BlockOutConfirmPopup': {'ConfirmTitle': 'Text', 'ConfirmBody': 'Text',
                             'ConfirmCancelBtn': 'Button', 'ConfirmOkBtn': 'Button'},
}

COMP_KIND = {'Button': 'Button', 'Text': 'Text', 'Image': 'Image', 'RectTransform': 'RectTransform'}


def load(path):
    s = path.read_text(encoding='utf-8')
    heads = list(re.finditer(r'^--- !u!(\d+) &(-?\d+).*\n', s, re.M))
    docs = []
    for i, h in enumerate(heads):
        body = s[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(s)]
        d = yaml.safe_load(body)
        k = next(iter(d))
        docs.append((int(h.group(1)), int(h.group(2)), k, d[k]))
    return docs


def main():
    guid_map = {}
    for m in glob.glob(str(ROOT / 'Assets/**/*.meta'), recursive=True):
        t = open(m, encoding='utf-8-sig', errors='ignore').read()
        mm = re.search(r'^guid: (\w+)', t, re.M)
        if mm:
            guid_map[mm.group(1)] = m

    errors = []
    for name, expect in EXPECT.items():
        path = UI / f'{name}.prefab'
        docs = load(path)
        byid = {i: (c, k, d) for c, i, k, d in docs}
        gos = {i: d for c, i, k, d in docs if k == 'GameObject'}
        name_of = {i: d['m_Name'] for i, d in gos.items()}

        def go_of(cid):
            c, k, d = byid[cid]
            if k == 'GameObject':
                return cid
            return d.get('m_GameObject', {}).get('fileID', 0)

        # 1 悬空引用
        def walk(v):
            if isinstance(v, dict):
                if 'fileID' in v and v['fileID'] != 0 and 'guid' not in v and v['fileID'] not in byid:
                    errors.append(f'{name}: 悬空 fileID {v["fileID"]}')
                for x in v.values():
                    walk(x)
            elif isinstance(v, list):
                for x in v:
                    walk(x)
        for c, i, k, d in docs:
            walk(d)

        # 2 负尺寸
        for c, i, k, d in docs:
            if k == 'RectTransform':
                sz = d['m_SizeDelta']
                # Stretch sizeDelta is an inset, not the resulting rectangle size.
                if any(sz[axis] < 0 and d['m_AnchorMin'][axis] == d['m_AnchorMax'][axis] for axis in ('x','y')):
                    errors.append(f'{name}/{name_of[d["m_GameObject"]["fileID"]]}: 负尺寸 {sz}')

        # 3 sprite 解析
        for c, i, k, d in docs:
            if k == 'MonoBehaviour' and 'm_Sprite' in d:
                g = d['m_Sprite'].get('guid')
                if g and g not in guid_map:
                    errors.append(f'{name}/{name_of[go_of(i)]}: sprite guid 未解析 {g}')

        # 4 字段绑定
        views = [d for c, i, k, d in docs if k == 'MonoBehaviour' and 'm_Script' in d
                 and not str(d['m_Script'].get('guid', '')).startswith('0')]
        views = [d for d in views if any(f in d for f in expect)]
        if not views and expect:
            errors.append(f'{name}: 找不到 View 组件')
            continue
        for d in views:
            for key, kind in expect.items():
                v = d.get(key)
                if v is None:
                    errors.append(f'{name}: 字段 {key} 未绑定')
                    continue
                fid = v['fileID']
                c, k, dd = byid.get(fid, (None, None, None))
                if kind == 'GameObject':
                    if k != 'GameObject':
                        errors.append(f'{name}.{key}: 应为 GameObject，实为 {k}')
                elif kind == 'prefab':
                    if 'guid' not in v:
                        errors.append(f'{name}.{key}: 应为 prefab 引用')
                elif kind == 'RectTransform':
                    if k != 'RectTransform':
                        errors.append(f'{name}.{key}: 应为 RectTransform，实为 {k}')
                else:
                    if k != 'MonoBehaviour':
                        errors.append(f'{name}.{key}: 应为 {kind} 组件，实为 {k}')
                    else:
                        has = kind == 'Button' and 'm_OnClick' in dd or \
                              kind == 'Text' and 'm_FontData' in dd or \
                              kind == 'Image' and 'm_Sprite' in dd
                        if not has:
                            errors.append(f'{name}.{key}: 组件类型不像 {kind}')

    if errors:
        print(f'✗ {len(errors)} 处问题:')
        for e in errors:
            print(' -', e)
        sys.exit(1)
    print('✓ 全部 UI prefab 静态校验通过（引用完整 / 无负尺寸 / 贴图可解析 / 字段绑定正确）')


if __name__ == '__main__':
    main()
