"""Static integration contracts only; does not compile or execute Unity."""
from pathlib import Path
import re,json
from PIL import Image
from fontTools.ttLib import TTFont
from polish_player_experience import Prefab,ROOT,UI
from integrate_garden_ui import comp,guid,ART,FONT,parent

def main():
    errors=[];pages=0;texts=0
    assets={}
    for m in (ROOT/'Assets').rglob('*.meta'):
        match=re.search(r'guid: (\w+)',m.read_text(encoding='utf-8-sig',errors='ignore'))
        if match:assets[match[1]]=Path(str(m)[:-5])
    cmap=TTFont(str(FONT)).getBestCmap()
    for file in list(UI.glob('*.prefab'))+list((UI/'Items').glob('*.prefab')):
        p=Prefab(str(file.relative_to(UI).with_suffix('')));pages+=1
        for g in p.gos.values():
            if sum('m_RaycastTarget' in d for _,d in p.components(g))>1:errors.append(file.name+': duplicate graphic '+g['m_Name'])
            text=comp(p,g,'m_Text')
            if text:
                texts+=1
                if text['m_FontData']['m_Font'].get('guid')==guid(FONT):
                    missing={c for c in text['m_Text'] if not c.isspace() and ord(c) not in cmap}
                    if missing:errors.append(file.name+': font missing '+''.join(missing))
        if file.stem=='BlockOutHomePage':
            path=p.field('Nodes')
            for key in ('Nodes','Numbers','Locks'):
                if len(path[key])!=5 or any(r['fileID'] not in p.ids for r in path[key]):errors.append('Invalid garden path '+key)
            if p.go('HomeDailyBtn')['m_IsActive'] or p.go('HomeAchievementBtn')['m_IsActive']:errors.append('Unimplemented home entry visible')
        for _,_,_,d in p.docs:
            if 'm_Sprite' in d and d['m_Sprite'].get('guid'):
                if d['m_Sprite']['guid'] not in assets:errors.append(file.name+': missing sprite GUID')
    for png in ART.glob('*.png'):
        im=Image.open(png)
        if not png.name.startswith('garden-') and im.getextrema()[3][0]!=0:errors.append('Missing transparency '+png.name)
    # This is evidence for serialization/resource integrity, not runtime behavior.
    report=dict(prefabs=pages,text_nodes=texts,garden_sprites=len(list(ART.glob('*.png'))),errors=errors,runtime_checks='not-run-user-owned')
    (ROOT/'design/ui/garden-suite-20261117/integration-static-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
