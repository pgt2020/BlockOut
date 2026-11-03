from pathlib import Path
import re,yaml,shutil,uuid
R=Path('E:/UnityProject/MutiplayGame/BlockOut');REF=Path('E:/UnityProject/ArrowOutBlockGallery/ArtOutBlockGallery/Assets');D=R/'Assets/BlockOut/Resources/ArtOutPresentation/Reference'
class Dumper(yaml.SafeDumper):
 def ignore_aliases(self,data):return True
def load(p):
 s=p.read_text(encoding='utf-8-sig');hs=list(re.finditer(r'^--- !u!(\d+) &(-?\d+).*\n',s,re.M));out=[]
 for i,h in enumerate(hs):
  doc=yaml.safe_load(s[h.end():hs[i+1].start() if i+1<len(hs) else len(s)]);k=next(iter(doc));out.append([int(h[1]),int(h[2]),k,doc[k]])
 return out
def save(p,docs):
 p.write_text('%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'+''.join('--- !u!%s &%s\n'%(c,i)+yaml.dump({k:d},Dumper=Dumper,sort_keys=False) for c,i,k,d in docs),encoding='utf-8')
def named(docs):
 byid={i:(c,d) for c,i,k,d in docs};out={}
 for c,i,k,d in docs:
  if c==1:
   out.setdefault(d['m_Name'],[]).append((d,[(x['component']['fileID'],*byid[x['component']['fileID']]) for x in d['m_Component']]))
 return out
refs=load(REF/'Bundles/Main/Prefabs/UI/View/ArtOutGameHudView.prefab');rn=named(refs)
index={}
for p in REF.rglob('*.meta'):
 m=re.search(r'^guid: (\w+)',p.read_text(encoding='utf-8-sig',errors='ignore'),re.M)
 if m:index[m[1]]=Path(str(p)[:-5])
local={}
for p in (R/'Assets').rglob('*.meta'):
 m=re.search(r'^guid: (\w+)',p.read_text(encoding='utf-8-sig',errors='ignore'),re.M)
 if m:local[m[1]]=p
copied=[]
def copy(g):
 if g in local or g.startswith('0000000000000000'):return
 p=index[g];dst=D/p.relative_to(REF);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);shutil.copy2(str(p)+'.meta',str(dst)+'.meta');local[g]=dst;copied.append(str(dst.relative_to(R)))
 if p.suffix in ['.mat','.asset']:
  for dep in re.findall(r'guid: ([a-f0-9]{32})',p.read_text(encoding='utf-8-sig')):copy(dep)
def sourceImage(name):
 for _,parts in rn[name]:
  for fid,c,d in parts:
   if c==114 and 'm_Sprite' in d:return d
p=R/'Assets/BlockOut/Resources/Prefabs/UI/BlockOutGameHud.prefab';docs=load(p);names=named(docs)
def rect(name):return next(d for fid,c,d in names[name][0][1] if c==224)
def image(name):return next((d for fid,c,d in names[name][0][1] if c==114 and 'm_Sprite' in d),None)
def box(name,x,y,w,h):
 d=rect(name);d['m_AnchorMin']=d['m_AnchorMax']={'x':0,'y':1};d['m_Pivot']={'x':0,'y':1};d['m_AnchoredPosition']={'x':x,'y':-y};d['m_SizeDelta']={'x':w,'y':h}
def art(name,source):
 d=image(name);src=sourceImage(source)
 if d is None or src is None:return
 for k in ['m_Sprite','m_Type','m_PreserveAspect']:d[k]=src.get(k,0)
 d['m_Color']={'r':1,'g':1,'b':1,'a':1}
 g=d['m_Sprite'].get('guid')
 if g:copy(g)
# Reference design 1125 x 2436 scaled onto existing 390 x 844 surface.
f=390/1125
box('BoardPauseBtn',36*f,158*f,110*f,110*f);art('BoardPauseBtn','SettingsButton')
box('BoardLevelTitle',65,145*f,260,76*f)
box('Hearts',141,205*f,108,31)
for i in range(3):box('Heart'+str(i),i*36,0,90*f,90*f)
box('BoardArea',0,115,390,470)
box('BoardHintPill',46,716,298,24)
for i,name in enumerate(['HintSlot','HammerSlot','MagicSlot']):
 box(name,[37,150,263][i],844-498*f-38,90,77);art(name,'ButtonBg')
 # Scope inner nodes by parent component IDs to avoid changing another slot.
 root=names[name][0][0];rootid=next(i for c,i,k,d in docs if c==1 and d is root)
 rootrt=next(fid for fid,c,d in names[name][0][1] if c==224)
 for c,fid,k,d in docs:
  if c==224 and d.get('m_Father',{}).get('fileID')==rootrt:
   go=next(v for cl,ii,kk,v in docs if cl==1 and ii==d['m_GameObject']['fileID']);n=go['m_Name']
   if n=='Icon':d['m_AnchoredPosition']={'x':20,'y':-5};d['m_SizeDelta']={'x':50,'y':50}
   if n in ['NameText','CondText']:go['m_IsActive']=0
for n in ['BoardLevelSub','BoardRemainingText']:names[n][0][0]['m_IsActive']=0
pauseRect=next(fid for fid,c,d in names['BoardPauseBtn'][0][1] if c==224)
for c,fid,k,d in docs:
 if c==224 and d.get('m_Father',{}).get('fileID')==pauseRect:
  go=next(v for cl,ii,kk,v in docs if cl==1 and ii==d['m_GameObject']['fileID']);go['m_IsActive']=0
save(p,docs)
# Reuse actual reference panel backgrounds on matching local screens; retain business bindings.
for localname,refname in [('BlockOutHomePage','ArtOutHomeView'),('BlockOutPausePopup','ArtOutSettingsPopup'),('BlockOutFailPopup','ArtOutFailPopup'),('BlockOutConfirmPopup','ArtOutToolConfirmPopup')]:
 target=R/'Assets/BlockOut/Resources/Prefabs/UI'/(localname+'.prefab');source=REF/'Bundles/Main/Prefabs/UI/View'/(refname+'.prefab')
 if not target.exists() or not source.exists():continue
 src=named(load(source));ld=load(target);ln=named(ld)
 for lnkey,snkey in [('Card','ContentCard'),('Card','ToolPurchaseContentCard'),('HomeCtaButton','StartButton'),('HomeSettingsBtn','SettingsButton'),('HomeCollectionLink','CollectionButton'),('PreviewCard','PictureFrame')]:
  if lnkey not in ln or snkey not in src:continue
  a=next((d for _,c,d in ln[lnkey][0][1] if c==114 and 'm_Sprite' in d),None);b=next((d for _,c,d in src[snkey][0][1] if c==114 and 'm_Sprite' in d),None)
  if a and b:
   a['m_Sprite']=b['m_Sprite'];a['m_Color']={'r':1,'g':1,'b':1,'a':1};a['m_Type']=b.get('m_Type',0)
   if b['m_Sprite'].get('guid'):copy(b['m_Sprite']['guid'])
 if localname=='BlockOutHomePage':
  def homebox(name,x,y,w,h):
   if name not in ln:return
   r=next(d for _,c,d in ln[name][0][1] if c==224);r['m_AnchorMin']=r['m_AnchorMax']={'x':0,'y':1};r['m_Pivot']={'x':0,'y':1};r['m_AnchoredPosition']={'x':x,'y':-y};r['m_SizeDelta']={'x':w,'y':h}
  homebox('HomeSettingsBtn',12.48,54.77,38.13,38.13);homebox('HomeCoinText',294,54.77,70,34)
  homebox('PreviewCard',64.65,262.3,261.39,261.39);homebox('HomeArtViewport',12,12,237.39,237.39)
  homebox('HomeCtaButton',87.53,595.2,215.63,81.12);homebox('HomeCollectionLink',314,601.7,66.56,70.03)
  homebox('HomeCtaSub',8,43,200,24);homebox('HomeCtaSecondary',79,710,232,40)
  for name in ['BottomNav','Logo','HomePieceBadge','HomeChapterTitle','HomePieceText','HomeProgressFill','NavHomeBtn','NavCollectionBtn','NavStoreBtn']+['Node_'+str(i) for i in range(12)]:
   if name in ln:ln[name][0][0]['m_IsActive']=0
  ctaRect=next(fid for fid,c,d in ln['HomeCtaButton'][0][1] if c==224)
  for c,fid,k,d in ld:
   if c==224 and d.get('m_Father',{}).get('fileID')==ctaRect:
    go=next(v for cl,ii,kk,v in ld if cl==1 and ii==d['m_GameObject']['fileID'])
    if go['m_Name']=='Text':d['m_SizeDelta']={'x':200,'y':32};d['m_AnchoredPosition']={'x':8,'y':-8}
  # Reuse the actual static source logo hierarchy; business fields stay on local views.
  srcdocs=load(source);sourceById={i:(c,k,d) for c,i,k,d in srcdocs};srcnames=named(srcdocs)
  surface=next((fid for fid,c,d in ln['Surface'][0][1] if c==224),None) if 'Surface' in ln else None
  if surface is None:surface=next(d['m_Father']['fileID'] for _,c,d in ln['PreviewCard'][0][1] if c==224)
  if 'ReferenceLogo' not in ln and 'Logo' in srcnames:
   import copy as cp
   go,parts=srcnames['Logo'][0];goid=next(i for c,i,k,d in srcdocs if c==1 and d is go);ids=[goid]+[i for i,c,d in parts];start=max(i for c,i,k,d in ld)+1;remap={old:start+j for j,old in enumerate(ids)}
   for old in ids:
    c,k,d=sourceById[old];d=cp.deepcopy(d)
    def remaprefs(v):
     if isinstance(v,dict):
      if 'fileID' in v and 'guid' not in v and v['fileID'] in remap:v['fileID']=remap[v['fileID']]
      for child in v.values():remaprefs(child)
     elif isinstance(v,list):
      for child in v:remaprefs(child)
    remaprefs(d)
    if c==1:d['m_Name']='ReferenceLogo'
    if c==224:
     d['m_Father']={'fileID':surface};d['m_AnchoredPosition']={axis:value*f for axis,value in d['m_AnchoredPosition'].items()};d['m_LocalScale']={'x':f,'y':f,'z':1};d['m_Children']=[]
     next(v for cl,ii,kk,v in ld if ii==surface)['m_Children'].append({'fileID':remap[old]})
    if c==114 and d.get('m_Sprite',{}).get('guid'):copy(d['m_Sprite']['guid']);d['m_RaycastTarget']=0
    ld.append([c,remap[old],k,d])
 save(target,ld)
# Full-screen win layout: same image anchor as the board completion presentation.
p=R/'Assets/BlockOut/Resources/Prefabs/UI/BlockOutSettlementPage.prefab';docs=load(p);names=named(docs)
card=rect('Card');card['m_AnchorMin']={'x':0,'y':0};card['m_AnchorMax']={'x':1,'y':1};card['m_Pivot']={'x':.5,'y':.5};card['m_AnchoredPosition']={'x':0,'y':0};card['m_SizeDelta']={'x':0,'y':0}
img=image('Card')
if img:img['m_Color']={'r':.847,'g':.925,'b':1,'a':1};img['m_Sprite']={'fileID':0}
for _,c,d in names['Card'][0][1]:
 if c==114 and 'Popup' in d:d['Popup']=0
for n in ['Heading','SettlePieceText','SettleNoteText']:names[n][0][0]['m_IsActive']=0
box('SettleTitleText',41,100,308,70)
box('SettleLevelImage',34,185,322,322)
r=rect('SettleLevelImage');r['m_AnchorMin']=r['m_AnchorMax']=r['m_Pivot']={'x':.5,'y':.5};r['m_AnchoredPosition']={'x':2*844/2436,'y':220*844/2436};r['m_SizeDelta']={'x':930*844/2436,'y':930*844/2436}
box('SettleRewardText',45,548,300,42)
box('SettleNextBtn',105,635,180,74);box('SettleReplayBtn',35,740,145,42);box('SettleCollectionBtn',210,740,145,42);box('SettleHomeBtn',12,55,50,38)
src=named(load(REF/'Bundles/Main/Prefabs/UI/View/ArtOutWinPopup.prefab'))
for localname,sourceName in [('SettleNextBtn','NextButton')]:
 target=image(localname);source=next((d for _,c,d in src[sourceName][0][1] if c==114 and 'm_Sprite' in d),None)
 if target is not None and source is not None:
  target['m_Sprite']=source['m_Sprite'];target['m_Color']={'r':1,'g':1,'b':1,'a':1}
  if source['m_Sprite'].get('guid'):copy(source['m_Sprite']['guid'])
save(p,docs)

for p in D.rglob('*'):
 if p.is_dir() and not Path(str(p)+'.meta').exists():Path(str(p)+'.meta').write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n',encoding='utf-8')
print('Adapted HUD layout and reference UI sprites; imported',len(copied),'assets')
