from pathlib import Path
import re,yaml,uuid
R=Path(__file__).resolve().parents[2];UI=R/'Assets/BlockOut/Resources/Prefabs/UI';A=R/'Assets/BlockOut/Resources/ArtOutPresentation'
class Dumper(yaml.SafeDumper):
 def ignore_aliases(self,data):return True
def guid(p):return re.search(r'^guid: (\w+)',Path(str(p)+'.meta').read_text(encoding='utf-8-sig'),re.M)[1]
def ext(p,n):return {'fileID':n,'guid':guid(p),'type':2 if p.suffix=='.controller' else 3}
def ref(n=0):return {'fileID':n}
def common():return {'m_ObjectHideFlags':0,'m_CorrespondingSourceObject':ref(),'m_PrefabInstance':ref(),'m_PrefabAsset':ref()}
pkg=next((R/'Library/PackageCache').glob('com.unity.ugui@*'));button=guid(next(pkg.rglob('Button.cs')));image=guid(next(pkg.rglob('Image.cs')))
feedback=ext(R/'Assets/BlockOut/Runtime/UI/Components/BlockOutUIFeedback.cs',11500000);player=ext(R/'Assets/BlockOut/Runtime/Gameplay/Presentation/BlockOutAnimationPlayer.cs',11500000);controller=ext(A/'Animations/Feedback.controller',9100000)
iconmap={guid(UI/'AuthoredSprites'/(old+'.png')):ext(A/'Sprites'/(new+'.png'),21300000) for old,new in [('bulb','bulb'),('hammer','hammer'),('wand','wand'),('lock','lock'),('heart','heart')]}
changed=0
for p in UI.rglob('*.prefab'):
 s=p.read_text(encoding='utf-8-sig');heads=list(re.finditer(r'^--- !u!(\d+) &(-?\d+).*\n',s,re.M));docs=[]
 for i,h in enumerate(heads):
  data=yaml.safe_load(s[h.end():heads[i+1].start() if i+1<len(heads) else len(s)]);name=next(iter(data));docs.append([int(h[1]),int(h[2]),name,data[name]])
 byid={i:(c,n,d) for c,i,n,d in docs};new=[];nextid=max(abs(i) for _,i,_,_ in docs)+1
 popup=('Popup' in p.stem and p.stem!='BlockOutPopupLayer') or p.stem in ['BlockOutSettingsPage','BlockOutSettlementPage']
 for cls,fid,name,data in docs:
  if cls==114 and data.get('m_Script',{}).get('guid')==image:
   sprite=data.get('m_Sprite',{}).get('guid')
   if sprite in iconmap:data['m_Sprite']=iconmap[sprite];data['m_Color']=dict(r=1,g=1,b=1,a=1);data['m_PreserveAspect']=1
  if cls!=1:continue
  comps=[byid[x['component']['fileID']][2] for x in data['m_Component']]
  isButton=any(c.get('m_Script',{}).get('guid')==button for c in comps)
  isPopup=popup and data['m_Name']=='Card'
  if not isButton and not isPopup:continue
  if any(c.get('m_Script',{}).get('guid')==feedback['guid'] for c in comps):continue
  for script,fields in [(feedback,{'Popup':1 if isPopup else 0}),(player,{'HintBlend':0,'ArrowAlpha':1,'VisualScale':1})]:
   nextid+=1;c=common();c.update({'m_GameObject':ref(fid),'m_Enabled':1,'m_EditorHideFlags':0,'m_Script':script,'m_Name':'','m_EditorClassIdentifier':''});c.update(fields);new.append([114,nextid,'MonoBehaviour',c]);data['m_Component'].append({'component':ref(nextid)})
  nextid+=1;c=common();c.update({'serializedVersion':7,'m_GameObject':ref(fid),'m_Enabled':0,'m_Avatar':ref(),'m_Controller':controller,'m_CullingMode':0,'m_UpdateMode':0,'m_ApplyRootMotion':0,'m_LinearVelocityBlending':0,'m_StabilizeFeet':0,'m_AnimatePhysics':0,'m_WarningMessage':'','m_HasTransformHierarchy':1,'m_AllowConstantClipSamplingOptimization':1,'m_KeepAnimatorStateOnDisable':0,'m_WriteDefaultValuesOnDisable':0});new.append([95,nextid,'Animator',c]);data['m_Component'].append({'component':ref(nextid)})
 if new:
  out='%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'
  for c,fid,n,d in docs+new:out+=f'--- !u!{c} &{fid}\n'+yaml.dump({n:d},Dumper=Dumper,sort_keys=False)
  p.write_text(out,encoding='utf-8');changed+=1
print('Updated prefabs:',changed)
