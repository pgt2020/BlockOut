# -*- coding: utf-8 -*-
"""从项目真实关卡 JSON 提取棋盘几何，输出给渲染器使用。

数据源：Assets/Resources/ArtOut/Levels/*.json
形状表：Runtime/Core/Rules/BlockOutShapeLibrary.cs（已逐条抄录，注释见下）
"""
import json, os, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJ = os.path.abspath(os.path.join(ROOT, '..', '..'))
OUT = os.path.join(ROOT, 'data')
os.makedirs(OUT, exist_ok=True)

# shapeId -> [(row, col), ...]，与 BlockOutShapeLibrary.ShapeIdToCoords 1..30 一致
SHAPES = {
    1:  [(0,0)],
    2:  [(0,0),(0,1)],
    3:  [(0,0),(1,0)],
    4:  [(0,0),(1,0),(1,1)],
    5:  [(0,0),(0,1),(1,0)],
    6:  [(0,0),(0,1),(0,2)],
    7:  [(0,0),(1,0),(2,0)],
    8:  [(0,0),(0,1),(0,2),(0,3)],
    9:  [(0,0),(1,0),(2,0),(3,0)],
    10: [(0,0),(0,1),(1,0),(1,1)],
    11: [(0,1),(1,0),(1,1),(1,2)],
    12: [(0,1),(1,0),(1,1),(2,1)],
    13: [(0,0),(0,1),(0,2),(1,1)],
    14: [(0,1),(0,2),(1,0),(1,1)],
    15: [(0,1),(1,0),(1,1),(2,0)],
    16: [(0,1),(1,1),(2,0),(2,1)],
    17: [(0,0),(0,1),(1,1),(2,1)],
    18: [(0,2),(1,0),(1,1),(1,2)],
    19: [(0,0),(0,1),(0,2),(1,2)],
    20: [(0,1),(1,0),(1,1),(1,2),(2,1)],
    21: [(0,1),(0,2),(1,0),(1,1),(1,2)],
    22: [(0,1),(1,0),(1,1),(2,0),(2,1)],
    23: [(0,0),(0,1),(1,0),(1,1),(2,0)],
    24: [(0,0),(0,1),(1,1),(2,1)],
    25: [(0,0),(0,1),(0,2),(1,1),(1,2)],
    26: [(0,0),(0,2),(1,0),(1,1),(1,2)],
    27: [(0,0),(0,1),(1,1),(2,0),(2,1)],
    28: [(0,0),(0,1),(0,2),(1,0),(1,2)],
    29: [(0,2),(1,0),(1,1),(1,2),(2,0)],
    30: [(0,1),(0,2),(1,1),(2,0),(2,1)],
}

# DesignSystem.md §1.4 的 6 组方块色（顶/底），按其语义顺序把关卡里的色相映射过去
PALETTE = {
    'orange': ('#F6B36A', '#E08A3C'),
    'mint':   ('#67C9A2', '#2E9E75'),
    'violet': ('#A992E0', '#7C63C4'),
    'pink':   ('#F39BB4', '#DC6A8C'),
    'yellow': ('#F2CE63', '#D9A622'),
    'blue':   ('#8FB8EE', '#4A82CF'),
    'stone':  ('#6B5A4E', '#453931'),
}


def hue_family(hexcolor):
    h = hexcolor.lstrip('#')
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 0.10:
        return 'stone'
    if mx == r:
        d = (g - b) / (mx - mn)
        deg = (60 * d) % 360
    elif mx == g:
        deg = 60 * ((b - r) / (mx - mn) + 2)
    else:
        deg = 60 * ((r - g) / (mx - mn) + 4)
    if deg < 20 or deg >= 340: return 'pink'
    if deg < 45: return 'orange'
    if deg < 70: return 'yellow'
    if deg < 170: return 'mint'
    if deg < 260: return 'blue'
    return 'violet'


DIRV = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}


def can_exit(block, occ, cols, rows):
    """按真实规则判断：沿箭头方向的完整通路上没有其他存活块。"""
    dc, dr = DIRV[block['dir']]
    for c, r in block['cells']:
        cc, rr = c + dc, r + dr
        while 0 <= cc < cols and 0 <= rr < rows:
            o = occ.get((cc, rr))
            if o is not None and o != block['id']:
                return False
            cc += dc
            rr += dr
    return True


def simulate(blocks, cols, rows, take):
    """贪心模拟前 take 步：每步移除一个可飞出的块，得到可信的残局。"""
    occ = {}
    for b in blocks:
        for c, r in b['cells']:
            occ[(c, r)] = b['id']
    cleared = []
    for _ in range(take):
        cands = [b for b in blocks if b['id'] not in cleared and can_exit(b, occ, cols, rows)]
        if not cands:
            break
        # 优先取更靠外（通路更短）的块，读起来更像人在玩
        def openness(b):
            dc, dr = DIRV[b['dir']]
            d = 99
            for c, r in b['cells']:
                cc, rr, k = c, r, 0
                while 0 <= cc < cols and 0 <= rr < rows:
                    cc += dc; rr += dr; k += 1
                d = min(d, k)
            return d
        cands.sort(key=openness)
        pick = cands[0]
        cleared.append(pick['id'])
        for c, r in pick['cells']:
            occ.pop((c, r), None)
    for b in blocks:
        b['skip'] = b['id'] in cleared
    print('模拟已飞出', len(cleared), '块 -> 剩余', len(blocks) - len(cleared))
    return len(cleared)


def main(level_file):
    path = os.path.join(PROJ, 'Assets', 'Resources', 'ArtOut', 'Levels', level_file)
    d = json.load(open(path, encoding='utf-8'))
    cols, rows = d['width'], d['height']
    occ = {}
    blocks = []
    for i, p in enumerate(d['pieces']):
        cells = [(p['column'] + c, p['row'] + r) for (r, c) in SHAPES[int(p['shapeId'])]]
        for c, r in cells:
            if (c, r) in occ:
                print('!! 重叠 cell', (c, r), 'block', i, '与', occ[(c, r)])
            occ[(c, r)] = i
        ac = p.get('arrowCell') or {'x': 0, 'y': 0}
        arrow = (p['column'] + ac['x'], p['row'] + ac['y'])
        fam = hue_family(p['color'])
        blocks.append({
            'id': i,
            'cells': [[c, r] for c, r in sorted(cells)],
            'arrow': list(arrow),
            'dir': p['direction'].lower(),
            'family': fam,
            'hex': p['color'],
        })

    used = sorted({b['family'] for b in blocks})
    print('关卡', level_file, '格', cols, 'x', rows, '块', len(blocks), '占格', len(occ), '/', cols * rows)
    print('色系分布', Counter(b['family'] for b in blocks))
    print('用到色系', used)
    print('方向分布', Counter(b['dir'] for b in blocks))
    cleared = simulate(blocks, cols, rows, int(os.environ.get('TAKE', '8')))
    out = {
        'level': level_file,
        'displayName': d.get('displayName'),
        'levelInChapter': d.get('levelInChapter'),
        'chapter': d.get('chapter'),
        'cols': cols, 'rows': rows,
        'total': len(blocks),
        'cleared': cleared,
        'palette': {k: {'top': v[0], 'bottom': v[1]} for k, v in PALETTE.items()},
        'blocks': blocks,
    }
    with open(os.path.join(OUT, 'board.json'), 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print('->', os.path.join(OUT, 'board.json'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '20260805_v1_Level3_easy.json')
