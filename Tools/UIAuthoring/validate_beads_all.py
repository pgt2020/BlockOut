"""珠子风格全量换肤后的完整性校验（只读，不启动 Unity）。

检查项：
  1. 18 个 UI prefab 的 .meta GUID 与换肤前一致
  2. 每个 View 的 public 字段全部绑定、所有 fileID 引用指向存在的文档
  3. 节点名只增不减，新增仅限 BeadsDecor / BeadsHoles
  4. 脚本 GUID 集合只允许新增 uGUI Image
  5. 所有 sprite 引用能解析到本地贴图
  6. 界面文案无英文（BlockOut 产品名除外）
  7. 按钮反馈组件数量
运行：python3 Tools/UIAuthoring/validate_beads_all.py
"""
from pathlib import Path
import re, yaml, collections

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI'
VIEWS = ROOT / 'Assets/BlockOut/Runtime/UI/Views'
BACKUP_MAIN = Path(__file__).parent / 'backup' / 'original'
BACKUP_REST = Path(__file__).parent / 'backup' / 'original_rest'
MAIN_THREE = {'BlockOutHomePage', 'BlockOutGameHud', 'BlockOutSettlementPage'}
NEW_NODES = {'BeadsDecor', 'BeadsHoles'}
# 主屏由 generate_beads_prefabs.py 全量重生成，节点增删属预期，只校验绑定与引用
SKIP_NAME_DIFF = MAIN_THREE


def parse(p):
    s = p.read_text(encoding='utf-8-sig')
    heads = list(re.finditer(r'^--- !u!(\d+) &(-?\d+).*\n', s, re.M))
    out = []
    for i, h in enumerate(heads):
        d = yaml.safe_load(s[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(s)])
        key = next(iter(d))
        out.append([int(h.group(1)), int(h.group(2)), key, d[key]])
    return out


def mguid(p):
    m = Path(str(p) + '.meta')
    if not m.exists():
        return None
    g = re.search(r'^guid: (\w+)', m.read_text(encoding='utf-8-sig'), re.M)
    return g.group(1) if g else None


# 资源 guid -> 是否存在
ASSET_GUIDS = set()
for m in (ROOT / 'Assets').rglob('*.meta'):
    g = re.search(r'^guid: (\w+)', m.read_text(encoding='utf-8-sig', errors='ignore'), re.M)
    if g:
        ASSET_GUIDS.add(g.group(1))
PKG_GUIDS = set()
for m in (ROOT / 'Library/PackageCache').rglob('*.meta'):
    g = re.search(r'^guid: (\w+)', m.read_text(encoding='utf-8-sig', errors='ignore'), re.M)
    if g:
        PKG_GUIDS.add(g.group(1))

# View 类的 public 字段
VIEW_FIELDS = {}
for f in VIEWS.glob('BlockOut*View.cs'):
    s = f.read_text(encoding='utf-8-sig')
    fields = []
    for decl in re.findall(r'public\s+[\w.\[\]<>]+\s+([^;{}]+);', s):
        fields += [p.split('=')[0].strip() for p in decl.split(',')]
    VIEW_FIELDS[mguid(f)] = [x for x in fields if x]
VIEW_BY_FILE = {mguid(f): f.stem for f in VIEWS.glob('BlockOut*View.cs')}
FEEDBACK = mguid(ROOT / 'Assets/BlockOut/Runtime/UI/Components/BlockOutUIFeedback.cs')
IMAGE_GUID = None
for m in (ROOT / 'Library/PackageCache').rglob('Image.cs.meta'):
    IMAGE_GUID = mguid(m.with_suffix(''))
    break


def all_refs(obj):
    """递归收集 {'fileID': n}（n != 0，且没有 guid 的外部引用）。"""
    if isinstance(obj, dict):
        if 'fileID' in obj and 'guid' not in obj:
            n = obj['fileID']
            if isinstance(n, int) and n != 0:
                yield n
        for v in obj.values():
            yield from all_refs(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from all_refs(v)


problems = []
summary = []
for p in sorted(UI.rglob('*.prefab')):
    stem = p.stem
    docs = parse(p)
    byid = {fid: (cls, name, d) for cls, fid, name, d in docs}
    names = collections.Counter(d['m_Name'] for c, f, n, d in docs if c == 1)
    scripts = {d.get('m_Script', {}).get('guid') for c, f, n, d in docs
               if c == 114 and isinstance(d, dict) and isinstance(d.get('m_Script'), dict)}
    scripts.discard(None)
    feedback = sum(1 for c, f, n, d in docs
                   if c == 114 and d.get('m_Script', {}).get('guid') == FEEDBACK)
    texts = [str(d['m_Text']) for c, f, n, d in docs
             if c == 114 and 'm_Text' in d and str(d['m_Text']).strip()]

    # 1. .meta GUID 不变
    src = (BACKUP_MAIN if stem in ('BlockOutHomePage', 'BlockOutGameHud',
                                  'BlockOutSettlementPage') else BACKUP_REST)
    rel = p.relative_to(UI)
    old = src / rel
    if old.exists() and mguid(p) != mguid(old):
        problems.append(f'{stem}: prefab .meta GUID 变化')

    # 2. 节点名 / 脚本 GUID 对比原始（主屏为全量重生成，跳过节点名对比）
    if old.exists():
        od = parse(old)
        on = set(d['m_Name'] for c, f, n, d in od if c == 1)
        os = {d.get('m_Script', {}).get('guid') for c, f, n, d in od
              if c == 114 and isinstance(d.get('m_Script'), dict)}
        os.discard(None)
        if stem not in SKIP_NAME_DIFF:
            lost = on - set(names)
            gain = set(names) - on
            if lost:
                problems.append(f'{stem}: 节点丢失 {sorted(lost)}')
            if gain - NEW_NODES:
                problems.append(f'{stem}: 意外新增节点 {sorted(gain - NEW_NODES)}')
        extra_scripts = scripts - os
        if extra_scripts - {IMAGE_GUID}:
            problems.append(f'{stem}: 脚本引用变化 {sorted(extra_scripts - {IMAGE_GUID})}')

    # 3. 内部引用完整性
    missing = sorted({r for c, f, n, d in docs for r in all_refs(d) if r not in byid})
    if missing:
        problems.append(f'{stem}: 悬空 fileID {missing[:6]}（共 {len(missing)}）')

    # 4. View 字段绑定
    view = None
    for c, f, n, d in docs:
        g = d.get('m_Script', {}).get('guid') if c == 114 else None
        if g in VIEW_FIELDS and (view is None or len(d) > len(view[1])):
            view = (g, d)
    bound = 0
    if view:
        g, d = view
        required = VIEW_FIELDS[g]
        absent = [k for k in required if k not in d]
        if absent:
            problems.append(f'{stem}: {VIEW_BY_FILE[g]} 未绑定字段 {absent}')
        bound = len(required) - len(absent)
        for k in required:
            if k in d:
                bad = [r for r in all_refs(d[k]) if r not in byid]
                if bad:
                    problems.append(f'{stem}: 字段 {k} 指向不存在的文档 {bad[:3]}')
    else:
        if stem != 'BlockOutPopupLayer':
            problems.append(f'{stem}: 未找到 View 组件')

    # 5. sprite 引用可解析
    for c, f, n, d in docs:
        if c != 114 or 'm_Sprite' not in d:
            continue
        g = (d.get('m_Sprite') or {}).get('guid')
        if g and g not in ASSET_GUIDS and g not in PKG_GUIDS:
            problems.append(f'{stem}: 未解析 sprite guid {g}')

    # 6. 英文文案（产品名 BlockOut 与数字/符号允许）
    for t in texts:
        words = [w for w in re.findall(r'[A-Za-z]{2,}', t) if w != 'BlockOut']
        if words:
            problems.append(f'{stem}: 英文文案 {words} -> {t[:30]}')

    summary.append((stem, len(docs), len(names), bound, feedback, len(texts)))

print('=== 全量 UI 预制校验 ===')
print(f'{"预制":34s} {"文档":>5s} {"节点":>5s} {"View字段":>8s} {"反馈":>5s} {"文案":>5s}')
for stem, nd, nn, bound, fb, nt in summary:
    print(f'{stem:34s} {nd:5d} {nn:5d} {bound:8d} {fb:5d} {nt:5d}')
print(f'\n预制总数 {len(summary)} | 节点合计 {sum(x[2] for x in summary)} '
      f'| 字段绑定合计 {sum(x[3] for x in summary)} | 反馈组件合计 {sum(x[4] for x in summary)}')
if problems:
    print(f'\n发现 {len(problems)} 个问题：')
    for x in problems:
        print('  -', x)
    raise SystemExit(1)
print('\n全部通过：GUID / 节点名 / 脚本引用 / 字段绑定 / 贴图 / 文案均无异常。')
