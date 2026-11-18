"""Static aspect-ratio/safe-area/page coverage audit. No Unity execution."""
import json,re
from pathlib import Path
import yaml
from polish_player_experience import Prefab,ROOT,UI
from integrate_garden_ui import ART,comp,children

def main():
    errors=[];pages=[];graphics=0
    sprites={}
    for meta in ART.glob('*.png.meta'):
        doc=yaml.safe_load(meta.read_text());sprites[doc['guid']]=(meta.stem,doc['TextureImporter'])
    registry=(ROOT/'Assets/BlockOut/Runtime/UI/Navigation/BlockOutUIPrefabRegistry.cs').read_text(encoding='utf-8')
    required=sorted(set(re.findall(r'return PrefabRoot \+ "([^"]+)"',registry)))
    for name in required:
        p=Prefab(name);layout=p.field('DesignSize')
        if not layout.get('RespectSafeArea'):errors.append(name+': safe area disabled')
        if layout['DesignSize']!={'x':390,'y':844}:errors.append(name+': unexpected design size')
        surface=p.ids[layout['Surface']['fileID']];g=p.gos[surface['m_GameObject']['fileID']]
        def walk(go,box,flow=False):
            if not go.get('m_IsActive',1):return
            rt=p.rect(go);px,py,pw,ph=box;a=rt['m_AnchorMin'];b=rt['m_AnchorMax'];v=rt['m_Pivot'];pos=rt['m_AnchoredPosition'];s=rt['m_SizeDelta']
            w=pw*(b['x']-a['x'])+s['x'];h=ph*(b['y']-a['y'])+s['y']
            x=px+pw*a['x']+pos['x']-v['x']*s['x'];y=py+ph*(1-a['y'])-pos['y']-(1-v['y'])*h-v['y']*ph*(b['y']-a['y'])
            flow=flow or comp(p,go,'m_ChildForceExpandHeight') is not None or go['m_Name'] in ('Content','Cells')
            if not flow and (comp(p,go,'m_Text') or comp(p,go,'m_Interactable')):
                if x < -1 or y < -1 or x+w>391 or y+h>845:errors.append(name+': out-of-design '+go['m_Name'])
            for ch in children(p,go):walk(ch,(x,y,w,h),flow)
        for ch in children(p,g):walk(ch,(0,0,390,844))
        pages.append(name)
    for file in list(UI.glob('*.prefab'))+list((UI/'Items').glob('*.prefab')):
        p=Prefab(str(file.relative_to(UI).with_suffix('')))
        for go in p.gos.values():
            im=comp(p,go,'m_Sprite')
            if not im or im.get('m_Sprite',{}).get('guid') not in sprites:continue
            graphics+=1;asset,importer=sprites[im['m_Sprite']['guid']]
            if im.get('m_Type')==0 and not im.get('m_PreserveAspect'):errors.append(file.stem+': unsliced stretch '+go['m_Name'])
            if im.get('m_Type')==1:
                if not asset.startswith(('panel-','button-','pill-','frame-')):errors.append(file.stem+': sliced illustration '+go['m_Name'])
                if not any(importer['spriteBorder'].values()):errors.append(asset+': missing borders')
    scenarios=[]
    for w,h,top,bottom in [(360,640,0,0),(390,844,0,0),(390,844,47,34),(390,932,47,34),(768,1024,24,20)]:
        scale=min(w/390,(h-top-bottom)/844)
        rect=[(w-390*scale)/2,top+(h-top-bottom-844*scale)/2,390*scale,844*scale]
        scenarios.append(dict(viewport=[w,h],safe_insets_top_bottom=[top,bottom],scale=round(scale,4),content_rect=[round(v,2) for v in rect],nominal_16px_text=round(16*scale,2)))
    report=dict(registered_pages=pages,garden_graphics=graphics,scenarios=scenarios,errors=errors,
        limits=['Static geometry only; scrolling content and dynamic text require runtime inspection.','Uniform fit preserves ratio but reduces touch targets/text on short screens.','Landscape is not part of this portrait UI acceptance.'],runtime='not-run')
    dest=ROOT/'design/ui/garden-suite-20261117/adaptation-audit.json';dest.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
