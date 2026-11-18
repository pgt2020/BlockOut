"""Read-only checks using the shipped C# shape table, not an old generator table.
Verify every published level's geometry, arrows, no-tool solvability and sprite masks.
"""
from pathlib import Path
import json
import re
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]

def main():
    source=(ROOT/'Assets/BlockOut/Runtime/Core/Rules/BlockOutShapeLibrary.cs').read_text(encoding='utf-8-sig')
    table=source.split('private static readonly int[][][] ShapeIdToCoords =')[1].split('};')[0]
    shapes={i:{(int(x),int(y)) for y,x in re.findall(r'new\[\] \{ (\d+), (\d+) \}',line)}
            for i,line in enumerate([l for l in table.splitlines() if 'new[]' in l],1)}
    failures=[]
    sprites=ROOT/'Assets/BlockOut/Resources/ArtOutPresentation/Reference/Bundles/Sprites/BlockSoft'
    for i,cells in shapes.items():
        im=Image.open(sprites/(str(i)+'.png')).convert('RGBA');w,h=im.size
        cols=max(x for x,y in cells)+1;rows=max(y for x,y in cells)+1
        mask={(x,y) for y in range(rows) for x in range(cols)
              if im.getpixel((int((x+.5)*w/cols),int((rows-y-.5)*h/rows)))[3]>128}
        if mask!=cells:failures.append({'sprite':i,'error':'visible mask differs from gameplay cells'})
    root=ROOT/'Assets/Resources/ArtOut';manifest=json.loads((root/'GameAssets.json').read_text(encoding='utf-8'))
    blocks=0
    for entry in manifest['levels']:
        lv=json.loads((root/'Levels'/(entry['id']+'.json')).read_text(encoding='utf-8'))
        pieces=lv['pieces'];cells=[{(p['column']+x,p['row']+y) for x,y in shapes[p['shapeId']]} for p in pieces]
        occ={};errors=[];w=lv['width'];h=lv['height'];blocks+=len(pieces)
        for i,cs in enumerate(cells):
            for x,y in cs:
                if not(0<=x<w and 0<=y<h):errors.append('bounds')
                if (x,y) in occ:errors.append('overlap')
                occ[x,y]=i
            arrow=pieces[i].get('arrowCell')
            if arrow and (arrow['x'],arrow['y']) not in shapes[pieces[i]['shapeId']]:errors.append('arrow outside block')
        deps=[]
        for i,cs in enumerate(cells):
            dx,dy={'Right':(1,0),'Left':(-1,0),'Up':(0,1),'Down':(0,-1)}[pieces[i]['direction']];d=set()
            for x,y in cs:
                x+=dx;y+=dy
                while 0<=x<w and 0<=y<h:
                    j=occ.get((x,y))
                    if j is not None and j!=i:d.add(j)
                    x+=dx;y+=dy
            deps.append(d)
        active=set(range(len(pieces)))
        while active:
            free={i for i in active if not(deps[i]&active)}
            if not free:errors.append('unsolvable');break
            active-=free
        if errors:failures.append({'level':entry['id'],'errors':sorted(set(errors))})
    result={'levels':len(manifest['levels']),'blocks':blocks,'shapes':len(shapes),'failures':failures}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if failures else 0

if __name__=='__main__':raise SystemExit(main())
