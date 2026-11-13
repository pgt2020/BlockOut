from pathlib import Path
import re,yaml
R=Path(__file__).resolve().parents[2]
class Dumper(yaml.SafeDumper):
 def ignore_aliases(self,data):return True
def prefab(name,remove,boxes):
 p=R/'Assets/BlockOut/Resources/Prefabs/UI'/ (name+'.prefab'); s=p.read_text(encoding='utf-8'); docs=[]
 for part in re.split(r'^--- !u!',s,flags=re.M)[1:]:
  h,b=part.split('\n',1); d=yaml.safe_load(b); k=next(iter(d)); docs.append([int(h.split(' &')[0]),int(h.split('&')[1]),k,d[k]])
 gos={i:d for c,i,k,d in docs if c==1}; transforms={i:d for c,i,k,d in docs if c==224}
 removed={i for i,d in transforms.items() if gos[d['m_GameObject']['fileID']]['m_Name'] in remove}
 while True:
  new={i for i,d in transforms.items() if d.get('m_Father',{}).get('fileID') in removed}; before=len(removed); removed|=new
  if len(removed)==before:break
 gonego={transforms[i]['m_GameObject']['fileID'] for i in removed}
 gone={i for c,i,k,d in docs if i in gonego or d.get('m_GameObject',{}).get('fileID') in gonego}
 fields=set()
 for c,i,k,d in docs:
  if c==114 and any(key.startswith(('HomeCta','CollectionBack','SettleNext')) for key in d):
   for key,v in list(d.items()):
    if not key.startswith('m_') and ((isinstance(v,dict) and v.get('fileID') in gone) or (isinstance(v,list) and any(isinstance(x,dict) and x.get('fileID') in gone for x in v))):fields.add(key);del d[key]
 for c,i,k,d in docs:
  if i in gone:continue
  if c==1 and d.get('m_Name') in boxes: d['m_IsActive']=1
  if c==1 and name=='BlockOutHomePage' and d.get('m_Name') in ['BottomNav','NavHomeBtn','NavCollectionBtn','NavStoreBtn']: d['m_IsActive']=1
  if c==224:
   d['m_Children']=[x for x in d.get('m_Children',[]) if x['fileID'] not in gone]
   n=gos[d['m_GameObject']['fileID']]['m_Name']
   if n in boxes:
    x,y,w,h=boxes[n];d['m_AnchoredPosition']={'x':x,'y':-y};d['m_SizeDelta']={'x':w,'y':h}
  if c==114 and 'm_Text' in d:
   t=d['m_Text'];d['m_Text']=t.replace('收藏','关卡').replace('查看作品','查看关卡').replace('还没有拼片，去完成第一章的关卡解锁作品吧','完成关卡后，可以在这里重复挑战').replace('收集拼片','挑战关卡').replace('逐步解锁章节作品','逐步完成更多关卡')
  if c==114 and d.get('m_PreferredHeight')==190 and name=='BlockOutCollectionPage':d['m_PreferredHeight']=120
 p.write_text('%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'+''.join('--- !u!%s &%s\n'%(c,i)+yaml.dump({k:d},Dumper=Dumper,sort_keys=False,allow_unicode=True) for c,i,k,d in docs if i not in gone),encoding='utf-8')
 return fields
hf=prefab('BlockOutHomePage',{'PreviewCard'}, {'HomeChapterTitle':(24,310,342,32),'HomeProgressFill':(24,365,342,10),'HomePieceText':(24,430,342,30),'HomeCtaButton':(65,510,260,81),'HomeCollectionLink':(145,610,100,50),'HomeCtaSecondary':(79,675,232,40), **{'Node_'+str(i):(24+i*28,390,18,18) for i in range(12)}})
cf=prefab('BlockOutCollectionPage',{'CollectionThumbRoot','CollectionViewBigBtn','CollectionBigLayer','RetryBar'}, {'SummaryCard':(0,0,342,120),'CollectionChapterText':(16,14,310,32),'CollectionPieceText':(16,52,310,30),'CollectionProgressFill':(16,94,310,10)})

sf=prefab('BlockOutSettlementPage', {'SettleRevealRoot'}, {})
