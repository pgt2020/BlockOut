from pathlib import Path
import re,uuid,yaml,zlib
R=Path(__file__).resolve().parents[2]; D=R/'Assets/BlockOut/Resources/ArtOutPresentation/Animations';D.mkdir(parents=True,exist_ok=True)
def guid(p):
 m=Path(str(p)+'.meta')
 if not m.exists():m.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n',encoding='utf-8')
 return re.search(r'guid: (\w+)',m.read_text(encoding='utf-8-sig'))[1]
def ref(n=0):return {'fileID':n}
def ext(p,n):return {'fileID':n,'guid':guid(p),'type':2 if p.suffix in ['.anim','.controller'] else 3}
def common():return {'m_ObjectHideFlags':0,'m_CorrespondingSourceObject':ref(),'m_PrefabInstance':ref(),'m_PrefabAsset':ref()}
class Dumper(yaml.SafeDumper):
 def ignore_aliases(self,data):return True
def save(p,docs):
 s='%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'
 for cls,fid,name,data in docs:s+=f'--- !u!{cls} &{fid}\n'+yaml.dump({name:data},Dumper=Dumper,sort_keys=False)
 p.write_text(s,encoding='utf-8');guid(p)
script=ext(R/'Assets/BlockOut/Runtime/Gameplay/Presentation/BlockOutAnimationPlayer.cs',11500000)
curves={
 'GuideTap':(1.1,{'VisualScale':[(0,1),(.3,1),(.48,.9),(.7,1),(1.1,1)]}),
 'Entrance':(1,{'MotionBlend':[(0,0),(.25,.578125),(.5,.875),(.75,.984375),(1,1)]}),
 'HudIntro':(.9,{'HudAlpha':[(0,0),(.46,1),(.9,1)],'ToolAlpha':[(0,0),(.28,0),(.64,1),(.9,1)]}),
 'CompletePulse':(.5,{'VisualScale':[(0,1),(.25,1.2),(.5,1)]}),
 'HudOutro':(.5,{'HudAlpha':[(0,1),(.5,0)],'ToolAlpha':[(0,1),(.5,0)]}),
 'ButtonTween':(.3,{'MotionBlend':[(0,0),(.3,1)]}),
 'Hint':(.4,{'HintBlend':[(0,0),(.2,1),(.4,0)]}),
 'MagicHit':(.24,{'VisualScale':[(0,1),(.12,1.15),(.24,1)]}),
 'WrongFlash':(.24,{'ArrowAlpha':[(0,1),(.03999,1),(.04,0),(.07999,0),(.08,1),(.11999,1),(.12,0),(.15999,0),(.16,1),(.19999,1),(.20,0),(.23999,0),(.24,1)]}),
 'PopupOpen':(.2,{'VisualScale':[(0,0),(.2,1)]}),
 'PopupClose':(.16,{'VisualScale':[(0,1),(.16,.88)]}),
 'ButtonPress':(.12,{'VisualScale':[(0,1),(.05,.94),(.12,1)]}),
 'ToolLocked':(.24,{'VisualScale':[(0,1),(.06,.93),(.12,1.04),(.18,.97),(.24,1)]}),
 'Launch':(.09,{'VisualScale':[(0,1),(.045,.94),(.09,1)]})}
clips={}
for name,(duration,values) in curves.items():
 for field,default in [('HintBlend',0),('ArrowAlpha',1),('VisualScale',1),('MotionBlend',1),('HudAlpha',1),('ToolAlpha',1)]:values.setdefault(field,[(0,default),(duration,default)])
 floats=[];bindings=[]
 for field,keys in values.items():
  curve={'serializedVersion':2,'m_Curve':[{'serializedVersion':3,'time':t,'value':v,'inSlope':(5 if name=='PopupOpen' and field=='VisualScale' else (3*(1-t)**2 if name=='Entrance' and field=='MotionBlend' else 0)),'outSlope':(5 if name=='PopupOpen' and field=='VisualScale' else (3*(1-t)**2 if name=='Entrance' and field=='MotionBlend' else (3/.46 if name=='HudIntro' and field=='HudAlpha' and t==0 else (3/.36 if name=='HudIntro' and field=='ToolAlpha' and t==.28 else 0)))),'tangentMode':0,'weightedMode':0,'inWeight':0,'outWeight':0} for t,v in keys],'m_PreInfinity':2,'m_PostInfinity':2,'m_RotationOrder':4}
  if name in ['Hint','MagicHit']:
   for i,key in enumerate(curve['m_Curve']):
    if i>0:key['inSlope']=(keys[i][1]-keys[i-1][1])/(keys[i][0]-keys[i-1][0])
    if i+1<len(keys):key['outSlope']=(keys[i+1][1]-keys[i][1])/(keys[i+1][0]-keys[i][0])
  if name=='CompletePulse' and field=='VisualScale':
   curve['m_Curve'][0]['outSlope']=1.6;curve['m_Curve'][1]['outSlope']=-1.6
  if name=='ButtonTween' and field=='MotionBlend':curve['m_Curve'][0]['outSlope']=2/.3
  floats.append({'curve':curve,'attribute':field,'path':'','classID':114,'script':script,'flags':0})
  bindings.append({'serializedVersion':2,'path':0,'attribute':zlib.crc32(field.encode()),'script':script,'typeID':114,'customType':0,'isPPtrCurve':0,'isIntCurve':0,'isSerializeReferenceCurve':0})
 data=common();data.update({'m_Name':name,'serializedVersion':7,'m_Legacy':0,'m_Compressed':0,'m_UseHighQualityCurve':1,'m_RotationCurves':[],'m_CompressedRotationCurves':[],'m_EulerCurves':[],'m_PositionCurves':[],'m_ScaleCurves':[],'m_FloatCurves':floats,'m_PPtrCurves':[],'m_SampleRate':60,'m_WrapMode':0,'m_Bounds':{'m_Center':dict(x=0,y=0,z=0),'m_Extent':dict(x=0,y=0,z=0)},'m_ClipBindingConstant':{'genericBindings':bindings,'pptrCurveMapping':[]},'m_AnimationClipSettings':{'serializedVersion':2,'m_AdditiveReferencePoseClip':ref(),'m_AdditiveReferencePoseTime':0,'m_StartTime':0,'m_StopTime':duration,'m_OrientationOffsetY':0,'m_Level':0,'m_CycleOffset':0,'m_HasAdditiveReferencePose':0,'m_LoopTime':0,'m_LoopBlend':0,'m_LoopBlendOrientation':0,'m_LoopBlendPositionY':0,'m_LoopBlendPositionXZ':0,'m_KeepOriginalOrientation':0,'m_KeepOriginalPositionY':1,'m_KeepOriginalPositionXZ':0,'m_HeightFromFeet':0,'m_Mirror':0},'m_EditorCurves':floats,'m_EulerEditorCurves':[],'m_HasGenericRootTransform':0,'m_HasMotionFloatCurves':0,'m_Events':[]})
 p=D/(name+'.anim');save(p,[(74,7400000,'AnimationClip',data)]);clips[name]=p
states=[];docs=[]
for i,(name,p) in enumerate(clips.items()):
 fid=1102000+i;states.append({'serializedVersion':1,'m_State':ref(fid),'m_Position':dict(x=250+i*40,y=50+i*60,z=0)})
 data=common();data.update({'serializedVersion':6,'m_Name':name,'m_Speed':1,'m_CycleOffset':0,'m_Transitions':[],'m_StateMachineBehaviours':[],'m_Position':dict(x=50,y=50,z=0),'m_IKOnFeet':0,'m_WriteDefaultValues':0,'m_Mirror':0,'m_SpeedParameterActive':0,'m_MirrorParameterActive':0,'m_CycleOffsetParameterActive':0,'m_TimeParameterActive':0,'m_Motion':ext(p,7400000),'m_Tag':'','m_SpeedParameter':'','m_MirrorParameter':'','m_CycleOffsetParameter':'','m_TimeParameter':''});docs.append((1102,fid,'AnimatorState',data))
sm=common();sm.update({'serializedVersion':6,'m_Name':'Base Layer','m_ChildStates':states,'m_ChildStateMachines':[],'m_AnyStateTransitions':[],'m_EntryTransitions':[],'m_StateMachineTransitions':{},'m_StateMachineBehaviours':[],'m_AnyStatePosition':dict(x=50,y=20,z=0),'m_EntryPosition':dict(x=50,y=120,z=0),'m_ExitPosition':dict(x=800,y=120,z=0),'m_ParentStateMachinePosition':dict(x=800,y=20,z=0),'m_DefaultState':ref(1102000)});docs.append((1107,1107000,'AnimatorStateMachine',sm))
c=common();c.update({'m_Name':'Feedback','serializedVersion':5,'m_AnimatorParameters':[],'m_AnimatorLayers':[{'serializedVersion':5,'m_Name':'Base Layer','m_StateMachine':ref(1107000),'m_Mask':ref(),'m_Motions':[],'m_Behaviours':[],'m_BlendingMode':0,'m_SyncedLayerIndex':-1,'m_DefaultWeight':1,'m_IKPass':0,'m_SyncedLayerAffectsTiming':0,'m_Controller':ref(9100000)}]});docs.append((91,9100000,'AnimatorController',c));save(D/'Feedback.controller',docs);guid(D)
print('Created',len(clips),'clips and Feedback.controller')
