"""Patch the delivered prefabs in place; preserve GUIDs and existing art/layout.
Run after authoring. Never imports Unity or modifies player saves.
"""
from pathlib import Path
import re
import copy
import yaml

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI'

class Dumper(yaml.SafeDumper):
    def ignore_aliases(self, data): return True

class Prefab:
    def __init__(self, name):
        self.path = UI / (name + '.prefab')
        self.docs = []
        for part in re.split(r'^--- !u!', self.path.read_text(encoding='utf-8-sig'), flags=re.M)[1:]:
            head, body = part.split('\n', 1)
            doc = yaml.safe_load(body); kind = next(iter(doc))
            self.docs.append((int(head.split(' &')[0]), int(head.split('&')[1]), kind, doc[kind]))
        self.ids = {i: d for c, i, k, d in self.docs}
        self.gos = {i: d for c, i, k, d in self.docs if k == 'GameObject'}
    def go(self, name): return next(d for d in self.gos.values() if d['m_Name'] == name)
    def components(self, go): return [(x['component']['fileID'], self.ids[x['component']['fileID']]) for x in go['m_Component']]
    def field(self, key): return next(d for c,i,k,d in self.docs if key in d)
    def rect(self, go): return next(d for i,d in self.components(go) if 'm_AnchoredPosition' in d)
    def text(self, go): return next(d for i,d in self.components(go) if 'm_Text' in d)
    def place(self, name, x, y, w, h):
        d=self.rect(self.go(name)); d.update(m_AnchorMin={'x':0,'y':1},m_AnchorMax={'x':0,'y':1},m_Pivot={'x':0,'y':1},m_AnchoredPosition={'x':x,'y':-y},m_SizeDelta={'x':w,'y':h})
    def save(self):
        self.path.write_text('%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'+''.join(f'--- !u!{c} &{i}\n'+yaml.dump({k:d},Dumper=Dumper,sort_keys=False,allow_unicode=True) for c,i,k,d in self.docs),encoding='utf-8')

def main():
    p=Prefab('BlockOutHomePage'); v=p.field('HomeCtaButton')
    v['HomeLevelTitle']={'fileID':next(i for i,d in p.components(p.go('TitleText')) if 'm_Text' in d)}
    v['HomeCoinsButton']={'fileID':next(i for i,d in p.components(p.go('PlusBtn')) if 'm_Interactable' in d)}
    for name in ('HomeDailyBtn','HomeAchievementBtn'): p.go(name)['m_IsActive']=0
    # Balanced two useful secondary entrances; keep the existing illustrated play identity.
    for name,label,x in [('HomeGalleryBtn','关卡',22),('HomeSkinBtn','道具',300)]:
        p.place(name,x,490,68,68)
        rt=p.rect(p.go(name))
        child=next(p.gos[p.ids[r['fileID']]['m_GameObject']['fileID']] for r in rt['m_Children'] if p.gos[p.ids[r['fileID']]['m_GameObject']['fileID']]['m_Name']=='Label')
        p.text(child)['m_Text']=label
    p.go('Sub')['m_IsActive']=1
    p.place('Sub',-20,94,320,24)
    p.text(p.go('Sub'))['m_Color']={'r':.43,'g':.33,'b':.29,'a':1}
    p.text(p.go('Sub'))['m_FontData']['m_FontSize']=14
    p.save()

    p=Prefab('BlockOutSettlementPage')
    for name in ('SettlePieceText','SettleNoteText'): p.go(name)['m_IsActive']=1
    # Place text in screen coordinates beside the real completion image.
    surface=next(i for i,d in p.ids.items() if 'm_Children' in d and d.get('m_GameObject',{}).get('fileID')==next(i for i,g in p.gos.items() if g['m_Name']=='DesignSurface'))
    for name,box in [('SettlePieceText',(35,172,320,28)),('SettleNoteText',(35,592,320,40))]:
        go=p.go(name); rt=p.rect(go); rid=next(i for i,d in p.components(go) if d is rt)
        old=p.ids[rt['m_Father']['fileID']]; old['m_Children']=[r for r in old['m_Children'] if r['fileID']!=rid]
        rt['m_Father']={'fileID':surface}; p.ids[surface]['m_Children'].append({'fileID':rid})
        p.place(name,*box); p.text(go)['m_FontData']['m_FontSize']=14
    p.save()

    p=Prefab('BlockOutCollectionPage'); v=p.field('CollectionContent')
    content=p.ids[v['CollectionContent']['fileID']]
    repeat=v['CollectionRepeatGrid']; chapters=v['CollectionChapterList']
    content['m_Children']=[r for r in content['m_Children'] if r not in (repeat,chapters)]+[repeat,chapters]
    for i,d in p.components(p.go('SummaryCard')):
        if 'm_MinHeight' in d:d['m_MinHeight']=120
    p.text(p.go('RepeatLabel'))['m_Text']='选择关卡'
    p.save()

    for path in UI.glob('*.prefab'):
        p=Prefab(path.stem)
        original_sizes={i:dict(d['m_SizeDelta']) for i,d in p.ids.items() if 'm_SizeDelta' in d}
        for i,d in p.ids.items():
            if 'm_AnchorMin' not in d:continue
            parent=original_sizes.get(d['m_Father']['fileID'])
            if not parent:continue
            a,b=d['m_AnchorMin'],d['m_AnchorMax']
            # Legacy offline authoring wrote final dimensions as stretch deltas.
            # Positive small deltas (intentional shadows/outset) are left intact.
            if not any(b[k]>a[k] and d['m_SizeDelta'][k]>30 for k in ('x','y')):continue
            for k in ('x','y'):
                if b[k]>a[k] and parent[k]>0:d['m_SizeDelta'][k]-=parent[k]*(b[k]-a[k])
        for gid,go in list(p.gos.items()):
            comps=p.components(go)
            if sum('m_RaycastTarget' in d for i,d in comps)<2:continue
            tid,td=next((i,d) for i,d in comps if 'm_Text' in d)
            renderers=[(i,d) for i,d in comps if 'm_CullTransparentMesh' in d]
            cid,cd=renderers[-1]
            newgo=max(p.ids)+1; newrt=newgo+1
            ng=copy.deepcopy(go); ng['m_Name']='CountText';ng['m_Component']=[{'component':{'fileID':newrt}},{'component':{'fileID':cid}},{'component':{'fileID':tid}}]
            if 'm_GameObject' in ng:ng['m_GameObject']={'fileID':newgo}
            rt=copy.deepcopy(p.rect(go)); parentid=next(i for i,d in comps if 'm_AnchoredPosition' in d)
            rt.update(m_GameObject={'fileID':newgo},m_Father={'fileID':parentid},m_Children=[],m_AnchorMin={'x':0,'y':0},m_AnchorMax={'x':1,'y':1},m_Pivot={'x':.5,'y':.5},m_AnchoredPosition={'x':0,'y':0},m_SizeDelta={'x':0,'y':0})
            go['m_Component']=[r for r in go['m_Component'] if r['component']['fileID'] not in (cid,tid)]
            p.rect(go)['m_Children'].append({'fileID':newrt})
            td['m_GameObject']=cd['m_GameObject']={'fileID':newgo}
            p.docs.extend([(1,newgo,'GameObject',ng),(224,newrt,'RectTransform',rt)])
            p.ids.update({newgo:ng,newrt:rt});p.gos[newgo]=ng
        for c,i,k,d in p.docs:
            if 'm_Text' not in d: continue
            t=d['m_Text']
            d['m_Text']=t.replace('图库','关卡').replace('图鉴','关卡').replace('炸弹','魔法').replace('还没有拼片，去完成关卡吧','完成第一关后，在这里重温挑战').replace('解锁新拼片','本章通关进度').replace('作品已收集','进度已保存').replace('已通关关卡可重复挑战','点选当前关卡，或重温已完成关卡')
            if 'm_FontData' in d and d['m_FontData']['m_FontSize']<12:
                d['m_FontData']['m_FontSize']=12
                rt=p.rect(p.gos[d['m_GameObject']['fileID']])
                if rt['m_SizeDelta']['y']>0:rt['m_SizeDelta']['y']=max(18,rt['m_SizeDelta']['y'])
        # Layout edits must resize the real button label along with its hit target.
        for go in p.gos.values():
            if not any('m_Interactable' in d for i,d in p.components(go)):continue
            rt=p.rect(go); w,h=rt['m_SizeDelta']['x'],rt['m_SizeDelta']['y']
            for ref in rt.get('m_Children',[]):
                child=p.ids[ref['fileID']]; cg=p.gos[child['m_GameObject']['fileID']]
                if cg['m_Name']!='Text':continue
                if w<=0 or h<=0:continue
                child.update(m_AnchorMin={'x':.5,'y':.5},m_AnchorMax={'x':.5,'y':.5},m_Pivot={'x':.5,'y':.5},m_AnchoredPosition={'x':0,'y':0},m_SizeDelta={'x':max(1,w-12),'y':max(1,h-6)})
                if path.stem=='BlockOutSettlementPage' and go['m_Name']=='SettleHomeBtn':
                    p.text(cg)['m_Text']='首页';p.text(cg)['m_FontData']['m_FontSize']=14
        p.save()

    p=Prefab('BlockOutHomePage')
    p.place('CoinText',40,0,48,40);p.place('PlusBtn',88,5,30,30)
    for name in ('CTA','SettingsBtn','HomeGalleryBtn','HomeSkinBtn','PlusBtn'):
        for i,d in p.components(p.go(name)):
            if 'm_Sprite' in d:d['m_Type']=0;d['m_PreserveAspect']=1
    p.save()
    p=Prefab('BlockOutSettlementPage');p.place('SettlePieceText',35,150,320,28)
    p.place('SettleNextBtn',65,645,260,64)
    round_guid=re.search(r'guid: (\w+)',(ROOT/'Assets/BlockOut/Resources/ArtOutPresentation/Sprites/round.png.meta').read_text())[1]
    for i,d in p.components(p.go('SettleNextBtn')):
        if 'm_Sprite' in d:d['m_Sprite']={'fileID':21300000,'guid':round_guid,'type':3};d['m_Type']=1;d['m_Color']={'r':.16,'g':.40,'b':.31,'a':1}
    # Native separate frame: never a baked screenshot of a completed level.
    if not any(g['m_Name']=='CompletionFrame' for g in p.gos.values()):
        source=p.go('SettleLevelImage');newgo=max(p.ids)+1;nextid=newgo+1;ng=copy.deepcopy(source);ng['m_Name']='CompletionFrame';ng['m_Component']=[]
        if 'm_GameObject' in ng:ng['m_GameObject']={'fileID':newgo}
        parent=p.rect(source)['m_Father']['fileID'];newrt=nextid
        for cid,original in p.components(source):
            c,_,kind,_=next(row for row in p.docs if row[1]==cid);d=copy.deepcopy(original);d['m_GameObject']={'fileID':newgo}
            if kind=='RectTransform':
                d.update(m_Children=[],m_AnchorMin={'x':0,'y':1},m_AnchorMax={'x':0,'y':1},m_Pivot={'x':0,'y':1},m_AnchoredPosition={'x':25,'y':-177},m_SizeDelta={'x':340,'y':350})
            if 'm_Sprite' in d:
                d['m_Sprite']={'fileID':21300000,'guid':round_guid,'type':3};d['m_Type']=1;d['m_Color']={'r':1,'g':.99,'b':.97,'a':1};d['m_PreserveAspect']=0
            ng['m_Component'].append({'component':{'fileID':nextid}});p.docs.append((c,nextid,kind,d));nextid+=1
        p.docs.append((1,newgo,'GameObject',ng));p.ids[parent]['m_Children'].insert(0,{'fileID':newrt})
    p.save()
    # A wand silhouette communicates targeted magic; a bomb promises a different tool.
    old=re.search(r'guid: (\w+)',(ROOT/'Assets/BlockOut/Resources/ArtOutPresentation/Sprites/wand.png.meta').read_text())[1]
    new=re.search(r'guid: (\w+)',(UI/'AuthoredSprites/wand.png.meta').read_text())[1]
    for path in list(UI.glob('*.prefab'))+list((UI/'Items').glob('*.prefab')):
        p=Prefab(str(path.relative_to(UI).with_suffix('')));changed=False
        for c,i,k,d in p.docs:
            if d.get('m_Sprite',{}).get('guid')==old:
                d['m_Sprite']['guid']=new;d['m_Color']={'r':.72,'g':.47,'b':.12,'a':1};changed=True
        if changed:p.save()
    print('Player experience prefab polish applied.')

if __name__ == '__main__': main()
