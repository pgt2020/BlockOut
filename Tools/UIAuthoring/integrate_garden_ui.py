"""Apply reviewed garden assets to real UGUI prefabs. Never invokes Unity.
Preserves existing serialized view references, GUIDs and gameplay bindings.
"""
from pathlib import Path
import copy, json, re, uuid, shutil
from PIL import Image
import yaml
from polish_player_experience import Prefab, ROOT, UI

PACK = ROOT/'design/ui/garden-suite-20261117'
ART = ROOT/'Assets/BlockOut/Resources/UI/Garden'
FONT = ROOT/'Assets/Resources/Fonts/ZCOOLKuaiLe-Regular.ttf'
WHITE = dict(r=1,g=1,b=1,a=1)
INK = dict(r=.30,g=.20,b=.13,a=1)
IMAGE = 'fe87c0e1cc204ed48ad3b37840f39efc'
TEXT = '5f7201a12d95ffc409449d95f23cf332'
BUTTON = '4e29b1a8efbd4b44bb3f3716e73f07ff'

def guid(path):
    meta=Path(str(path)+'.meta')
    if not meta.exists():
        meta.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid5(uuid.NAMESPACE_URL,'blockout-garden:'+path.relative_to(ROOT).as_posix()).hex+'\n',encoding='utf-8')
    return re.search(r'guid: (\w+)',meta.read_text(encoding='utf-8-sig'))[1]

def import_assets():
    ART.mkdir(parents=True,exist_ok=True)
    template=yaml.safe_load((ROOT/'Assets/BlockOut/Resources/UI/Reference/sprites/s2_settings.png.meta').read_text())
    result={}
    for entry in json.loads((PACK/'selected-asset-manifest.json').read_text(encoding='utf-8'))['assets']:
        src=PACK/entry['file'];name=re.sub('_v02$','',src.stem);dst=ART/(name+'.png')
        im=Image.open(src).convert('RGBA')
        if entry['alpha']=='transparent':
            im=im.crop(im.getbbox())
            # Normalize transparent padding before assigning nine-slice borders.
            pad=4; canvas=Image.new('RGBA',(im.width+pad*2,im.height+pad*2));canvas.paste(im,(pad,pad));im=canvas
        im.save(dst)
        m=copy.deepcopy(template);m['guid']=guid(dst);t=m['TextureImporter']
        border=(0,0,0,0)
        if name=='panel-cream':border=(80,80,80,80)
        elif name.startswith('button-'):border=(100,50,100,50)
        elif name=='pill-cream':border=(72,32,72,32)
        elif name=='frame-art':border=(77,77,77,77)
        t.update(spriteBorder=dict(zip(('x','y','z','w'),border)),spritePixelsToUnits=100,spriteMeshType=1,maxTextureSize=2048,nPOTScale=0,alphaIsTransparency=1)
        t['mipmaps']['enableMipMap']=0
        t['textureSettings'].update(filterMode=1,wrapU=1,wrapV=1)
        t['spriteSheet']['spriteID']=uuid.uuid5(uuid.NAMESPACE_URL,'garden:'+name).hex
        Path(str(dst)+'.meta').write_text(yaml.safe_dump(m,sort_keys=False),encoding='utf-8')
        result[name]={'fileID':21300000,'guid':m['guid'],'type':3}
    guid(ART);guid(FONT);guid(FONT.with_name('ZCOOLKuaiLe-OFL.txt'))
    fm=yaml.safe_load((ROOT/'Assets/Resources/Fonts/SourceHanSansCN-Regular.otf.meta').read_text())
    fm['guid']=guid(FONT);fm['TrueTypeFontImporter']['fontNames']=['ZCOOL KuaiLe']
    fm['TrueTypeFontImporter']['fallbackFontReferences']=[{'fileID':12800000,'guid':guid(ROOT/'Assets/Resources/Fonts/SourceHanSansCN-Regular.otf'),'type':3}]
    Path(str(FONT)+'.meta').write_text(yaml.safe_dump(fm,sort_keys=False),encoding='utf-8')
    return result

def comp(p,g,key):return next((d for _,d in p.components(g) if key in d),None)
def children(p,g):return [p.gos[p.ids[r['fileID']]['m_GameObject']['fileID']] for r in p.rect(g)['m_Children']]
def rid(p,g):return next(i for i,d in p.components(g) if 'm_AnchoredPosition' in d)
def parent(p,g):return p.gos.get(p.ids.get(p.rect(g)['m_Father']['fileID'],{}).get('m_GameObject',{}).get('fileID'))
def image(p,g,name,sliced=False):
    d=comp(p,g,'m_Sprite')
    if d is None:return
    d.update(m_Sprite=SPR[name],m_Color=dict(WHITE),m_Type=1 if sliced else 0,m_PreserveAspect=0 if sliced else 1,m_PixelsPerUnitMultiplier=3 if sliced else 1)
def place(p,g,x,y,w,h):
    p.rect(g).update(m_AnchorMin={'x':0,'y':1},m_AnchorMax={'x':0,'y':1},m_Pivot={'x':0,'y':1},m_AnchoredPosition={'x':x,'y':-y},m_SizeDelta={'x':w,'y':h})
def stretch(p,g):
    p.rect(g).update(m_AnchorMin={'x':0,'y':0},m_AnchorMax={'x':1,'y':1},m_Pivot={'x':.5,'y':.5},m_AnchoredPosition={'x':0,'y':0},m_SizeDelta={'x':0,'y':0})

def add_component(p,g,fields,script=None,cls=114,kind='MonoBehaviour'):
    i=max(p.ids)+1
    gid=next(i for i,d in p.gos.items() if d is g)
    d=dict(m_ObjectHideFlags=0,m_CorrespondingSourceObject={'fileID':0},m_PrefabInstance={'fileID':0},m_PrefabAsset={'fileID':0},m_GameObject={'fileID':gid})
    if script:d.update(m_Enabled=1,m_EditorHideFlags=0,m_Script={'fileID':11500000,'guid':script,'type':3},m_Name='',m_EditorClassIdentifier='')
    d.update(fields);p.docs.append((cls,i,kind,d));p.ids[i]=d;g['m_Component'].append({'component':{'fileID':i}})
    return i

def node(p,name,par,box,sprite=None,text=None,size=18):
    # No subtree cloning: one graphic and one renderer per node.
    existing=next((g for g in p.gos.values() if g['m_Name']==name and parent(p,g) is par),None)
    if existing:return existing
    gid=max(p.ids)+1;rtid=gid+1
    g=dict(m_ObjectHideFlags=0,m_CorrespondingSourceObject={'fileID':0},m_PrefabInstance={'fileID':0},m_PrefabAsset={'fileID':0},serializedVersion=6,m_Component=[{'component':{'fileID':rtid}}],m_Layer=5,m_Name=name,m_TagString='Untagged',m_Icon={'fileID':0},m_NavMeshLayer=0,m_StaticEditorFlags=0,m_IsActive=1)
    rt=copy.deepcopy(p.rect(par));rt.update(m_GameObject={'fileID':gid},m_Children=[],m_Father={'fileID':rid(p,par)},m_LocalScale={'x':1,'y':1,'z':1})
    p.docs.extend([(1,gid,'GameObject',g),(224,rtid,'RectTransform',rt)]);p.ids.update({gid:g,rtid:rt});p.gos[gid]=g
    p.rect(par)['m_Children'].append({'fileID':rtid});place(p,g,*box)
    add_component(p,g,{'m_CullTransparentMesh':1},cls=222,kind='CanvasRenderer')
    common=dict(m_Material={'fileID':0},m_Color=dict(WHITE),m_RaycastTarget=0,m_RaycastPadding={'x':0,'y':0,'z':0,'w':0},m_Maskable=1,m_OnCullStateChanged={'m_PersistentCalls':{'m_Calls':[]}})
    if text is not None:
        common.update(m_Text=text,m_FontData=dict(m_Font={'fileID':12800000,'guid':guid(FONT),'type':3},m_FontSize=size,m_FontStyle=0,m_BestFit=1,m_MinSize=max(12,size-5),m_MaxSize=size,m_Alignment=4,m_AlignByGeometry=0,m_RichText=0,m_HorizontalOverflow=0,m_VerticalOverflow=0,m_LineSpacing=1))
        add_component(p,g,common,TEXT)
    else:
        common.update(m_Sprite=SPR[sprite] if sprite else {'fileID':0},m_Type=0,m_PreserveAspect=1,m_FillCenter=1,m_FillMethod=4,m_FillAmount=1,m_FillClockwise=1,m_FillOrigin=0,m_UseSpriteMesh=0,m_PixelsPerUnitMultiplier=1)
        add_component(p,g,common,IMAGE)
    return g

def button(p,g):
    im=comp(p,g,'m_Sprite');im['m_RaycastTarget']=1
    target=next(i for i,d in p.components(g) if d is im)
    return add_component(p,g,dict(m_Navigation={'m_Mode':0,'m_WrapAround':0,'m_SelectOnUp':{'fileID':0},'m_SelectOnDown':{'fileID':0},'m_SelectOnLeft':{'fileID':0},'m_SelectOnRight':{'fileID':0}},m_Transition=1,m_Colors={'m_NormalColor':WHITE,'m_HighlightedColor':WHITE,'m_PressedColor':dict(r=.85,g=.88,b=.83,a=1),'m_SelectedColor':WHITE,'m_DisabledColor':dict(r=.75,g=.75,b=.75,a=1),'m_ColorMultiplier':1,'m_FadeDuration':.08},m_Interactable=1,m_TargetGraphic={'fileID':target},m_OnClick={'m_PersistentCalls':{'m_Calls':[]}}),BUTTON)

def background(p,name):
    root=next(g for g in p.gos.values() if p.rect(g)['m_Father']['fileID']==0)
    g=node(p,'GardenBackdrop',root,(0,0,390,844),name);stretch(p,g)
    # Envelope parent covers letterboxing while the safe-area design surface stays unchanged.
    fitter=next(ROOT.glob('Library/PackageCache/com.unity.ugui@*/Runtime/UGUI/UI/Core/Layout/AspectRatioFitter.cs'))
    if comp(p,g,'m_AspectMode') is None:add_component(p,g,dict(m_AspectMode=4,m_AspectRatio=1080/1920),guid(fitter))
    ch=p.rect(root)['m_Children'];ref={'fileID':rid(p,g)};ch.remove(ref);ch.insert(0,ref)

def apply(p):
    names={g['m_Name']:g for g in p.gos.values()};surface=names.get('DesignSurface')
    page=p.path.stem
    fullscreen=page in ('BlockOutHomePage','BlockOutLoadingPage','BlockOutGameHud','BlockOutStorePage','BlockOutCollectionPage','BlockOutSettlementPage')
    if fullscreen:
        background(p,'garden-play' if page=='BlockOutGameHud' else 'garden-home')
        if surface and comp(p,surface,'m_Sprite'):comp(p,surface,'m_Sprite')['m_Color']['a']=0
        for name in ('HomeBackground','LoadingBackground'):
            if name in names:names[name]['m_IsActive']=0
    iconmap={'bulb':'icon-hint','hammer':'icon-hammer','wand':'icon-magic','coin':'icon-coin','heart':'icon-heart','lock':'icon-lock','icon_heart_broken':'icon-heart-broken','home_settings':'icon-settings','home_gallery':'icon-levels','home_skin':'icon-store'}
    old={}
    for path in (ROOT/'Assets/BlockOut/Resources/ArtOutPresentation/Sprites').glob('*.png'):
        if path.stem in iconmap:old[guid(path)]=iconmap[path.stem]
    old[guid(UI/'AuthoredSprites/wand.png')]='icon-magic'
    primary={'CTA','SettleNextBtn','PauseResumeBtn','ConfirmOkBtn','FailReviveBtn','GuideDismissBtn','SettingsCloseBtn','AboutCloseBtn','BuyBtn'}
    for g in list(p.gos.values()):
        name=g['m_Name'];par=parent(p,g);pn=par['m_Name'] if par else '';im=comp(p,g,'m_Sprite');bt=comp(p,g,'m_Interactable');tx=comp(p,g,'m_Text')
        if im and im.get('m_Sprite',{}).get('guid') in old:image(p,g,old[im['m_Sprite']['guid']])
        if im:
            if name in ('Card','SummaryCard','RepeatCard','BottomNav') or page.startswith('Store') and par is None or page=='ChapterItem' and par is None:image(p,g,'panel-cream',True)
            if name in ('CoinPill','HintPill','TimerPill'):image(p,g,'pill-cream',True)
            if name in ('Stroke','Fill') and pn in ('BoardTray','BottomToolbar','HintSlot','HammerSlot','MagicSlot'):
                if name=='Stroke':image(p,g,'panel-cream',True)
                else:g['m_IsActive']=0
            if name=='Dots':g['m_IsActive']=0
            if name in ('Lock','Locked','LockIcon','LockBadge') and (name!='LockBadge' or 'Store' in page):image(p,g,'icon-lock')
            if name.startswith('Heart_'):image(p,g,'icon-heart')
            if name=='Background' and page=='RepeatItem':image(p,g,'tile-green')
            if name=='CompletionFrame':image(p,g,'frame-art')
            if name=='CollectionProgressFill':im['m_Color']=dict(r=.22,g=.67,b=.37,a=1)
            if name=='Thumbnail' and page=='ChapterItem':image(p,g,'icon-levels')
        if bt and im:
            if name.startswith('GardenLevel'):image(p,g,'tile-green' if name=='GardenLevel1' else 'tile-grey')
            elif name in primary:image(p,g,'button-green',True)
            elif name in ('FailRestartBtn','PauseRestartBtn'):image(p,g,'button-coral',True)
            elif name in ('PauseBtn','SettingsBtn','HomeGalleryBtn','HomeSkinBtn'):image(p,g,'round-base')
            elif name in ('HintSlot','HammerSlot','MagicSlot'):pass
            elif name.endswith('Switch'):image(p,g,'panel-cream',True)
            else:image(p,g,'button-cream',True)
            bt['m_Transition']=1
            bt['m_Colors'].update(m_NormalColor=WHITE,m_HighlightedColor=WHITE,m_SelectedColor=WHITE,m_PressedColor=dict(r=.84,g=.87,b=.82,a=1),m_DisabledColor=dict(r=.72,g=.72,b=.72,a=.85),m_FadeDuration=.08)
        if tx:
            if tx['m_Text']=='商店':tx['m_Text']='道具'
            title=name in ('Heading','Title','TitleText','SettleTitleText','PageTitle','LevelTitle','NameText','Number','Label') or (par and comp(p,par,'m_Interactable') is not None)
            if title:tx['m_FontData'].update(m_Font={'fileID':12800000,'guid':guid(FONT),'type':3},m_FontStyle=0)
            if par and comp(p,par,'m_Interactable') is not None:
                tx['m_Color']=dict(WHITE if pn in primary or pn in ('FailRestartBtn','PauseRestartBtn') or pn.startswith('GardenLevel') else INK)
                if name=='Text' and 'Nav' not in pn:
                    tx['m_FontData'].update(m_FontSize=17,m_MaxSize=17,m_MinSize=13)
            elif title:tx['m_Color']=dict(INK)
    if page=='BlockOutGameHud':
        plate=node(p,'GardenHudPlate',surface,(16,28,358,88),'panel-cream');image(p,plate,'panel-cream',True)
        refs=p.rect(surface)['m_Children'];r={'fileID':rid(p,plate)};refs.remove(r);refs.insert(1,r)
        image(p,names['HintPill'],'pill-cream',True)
        for child in children(p,names['PauseBtn']):
            if child['m_Name']=='Icon':place(p,child,12,12,16,16)
        # Keep text outside BoardArea (ends at y=551), clear of playable cells.
        place(p,names['RemainingText'],202,574,140,18)
    if page=='BlockOutHomePage':home(p,surface,names)
    if page in ('BlockOutStorePage','BlockOutCollectionPage'):
        header=node(p,'GardenHeader',surface,(12,16,366,64),'panel-cream');image(p,header,'panel-cream',True)
        refs=p.rect(surface)['m_Children'];r={'fileID':rid(p,header)};refs.remove(r);refs.insert(0,r)
        for g in list(p.gos.values()):
            if 'Nav' in g['m_Name'] and comp(p,g,'m_Interactable'):
                suffix='home' if 'Home' in g['m_Name'] else 'levels' if 'Collection' in g['m_Name'] else 'store'
                node(p,'GardenNavIcon',g,(38,3,30,30),'icon-'+suffix)
                for child in children(p,g):
                    if comp(p,child,'m_Text'):place(p,child,4,34,98,19)
    if page=='BlockOutLoadingPage':image(p,names['Logo'],'mascot')
    if page=='BlockOutFailPopup':
        heart=node(p,'GardenBrokenHeart',surface,(153,112,84,84),'icon-heart-broken');place(p,heart,153,112,84,84)
        # Migrate the earlier in-card draft without leaving a duplicate over the reason.
        for g in list(p.gos.values()):
            if g['m_Name']=='GardenBrokenHeart' and parent(p,g) is not surface:g['m_IsActive']=0
        comp(p,names['FailExhaustedNote'],'m_Text')['m_FontData'].update(m_FontSize=13,m_MaxSize=13)
    if page=='BlockOutGuidePopup':
        # Keep the rule text unobstructed; mascot occupies the space above the card.
        mascot=node(p,'GardenGuideMascot',surface,(151,108,88,88),'mascot');place(p,mascot,151,108,88,88)
    if page=='BlockOutConfirmPopup':
        # The dedicated ConfirmTitle already carries the live title.
        if 'Heading' in names:names['Heading']['m_IsActive']=0
    if page=='RepeatItem':
        place(p,names['Background'],0,0,44,44)
        if 'Number' in names:comp(p,names['Number'],'m_Text')['m_Color']=WHITE
    if page in ('StoreHint','StoreHammer','StoreMagic'):
        root=next(g for g in p.gos.values() if p.rect(g)['m_Father']['fileID']==0)
        p.rect(root)['m_SizeDelta']['y']=136
        layout=comp(p,root,'m_PreferredHeight')
        if layout:layout.update(m_PreferredHeight=136,m_MinHeight=136)
        image(p,root,'panel-cream',True)
        place(p,names['Icon'],18,29,54,54)
        place(p,names['NameText'],84,16,226,26)
        place(p,names['DescText'],84,45,232,37)
        place(p,names['CoinText'],84,96,148,24)
        place(p,names['BuyBtn'],238,87,88,40)
        for child in children(p,names['BuyBtn']):
            if comp(p,child,'m_Text'):place(p,child,5,3,78,34)
    if page=='BlockOutSettlementPage':
        comp(p,names['Card'],'m_Sprite')['m_Color']['a']=0
        names['Heading']['m_IsActive']=0
        banner=node(p,'GardenWinRibbon',names['Card'],(45,85,300,83),'ribbon-coral')
        refs=p.rect(names['Card'])['m_Children'];ref={'fileID':rid(p,banner)};refs.remove(ref);refs.insert(0,ref)
        place(p,names['SettleTitleText'],65,100,260,45);comp(p,names['SettleTitleText'],'m_Text')['m_Color']=WHITE
        place(p,names['CompletionFrame'],35,194,320,320)
        place(p,names['SettleLevelImage'],68,227,254,254)
        # Frame is behind the contained real image; its opening remains clear.
        node(p,'GardenRewardCoin',names['Card'],(55,548,30,30),'icon-coin')
        place(p,names['SettleRewardText'],88,540,265,45)
        image(p,names['SettleHomeBtn'],'button-cream',True)
    p.save()

def home(p,s,n):
    place(p,n['SettingsBtn'],20,25,48,48);node(p,'GardenGear',n['SettingsBtn'],(11,11,26,26),'icon-settings')
    place(p,n['CoinPill'],232,28,140,42);place(p,n['CoinText'],38,0,67,42);place(p,n['PlusBtn'],106,6,30,30)
    place(p,n['CoinIcon'],8,8,26,26)
    plus=node(p,'GardenPlus',n['PlusBtn'],(0,0,30,30),text='+',size=24);comp(p,plus,'m_Text')['m_Color']=INK
    n['TitlePlate']['m_IsActive']=0
    path=node(p,'GardenPathRail',s,(188,120,14,475),'pill-cream');image(p,path,'pill-cream',True)
    refs=p.rect(s)['m_Children'];rr={'fileID':rid(p,path)};refs.remove(rr);refs.insert(0,rr)
    buttons=[];numbers=[];locks=[]
    for i,box in enumerate([(68,560,70,74),(141,435,108,114),(154,324,82,86),(157,216,76,80),(161,116,68,72)]):
        g=node(p,'GardenLevel'+str(i),s,box,'tile-green' if i==1 else 'tile-grey')
        b=comp(p,g,'m_Interactable');bid=button(p,g) if b is None else next(j for j,d in p.components(g) if d is b)
        num=node(p,'GardenNumber',g,(4,8,box[2]-8,box[3]-16),text=str(i+1),size=42 if i==1 else 28)
        lock=node(p,'GardenLock',g,(box[2]-22,box[3]-26,24,24),'icon-lock');lock['m_IsActive']=0 if i<=1 else 1
        buttons.append({'fileID':bid});numbers.append({'fileID':next(j for j,d in p.components(num) if 'm_Text' in d)});locks.append({'fileID':next(j for j,d in p.components(lock) if 'm_Sprite' in d)})
    node(p,'GardenMascot',s,(219,551,88,90),'mascot')
    bubble=node(p,'GardenCurrentBadge',s,(252,451,114,36),'pill-cream');image(p,bubble,'pill-cream',True)
    text=node(p,'GardenCurrentLabel',bubble,(7,4,100,27),text='当前关卡',size=16);comp(p,text,'m_Text')['m_Color']=INK
    place(p,n['CTA'],45,648,300,82);place(p,n['Title'],8,14,284,50);place(p,n['Sub'],-15,84,330,24)
    nav=node(p,'GardenHomeNav',s,(22,759,346,69),'panel-cream');image(p,nav,'panel-cream',True)
    refs=p.rect(s)['m_Children'];rr={'fileID':rid(p,nav)};refs.remove(rr);refs.insert(0,rr)
    for name,x,icon in [('HomeGalleryBtn',159,'icon-levels'),('HomeSkinBtn',280,'icon-store')]:
        place(p,n[name],x,762,52,52)
        for child in children(p,n[name]):
            if child['m_Name']=='Icon':image(p,child,icon);place(p,child,8,0,36,36)
            elif comp(p,child,'m_Text'):place(p,child,-3,37,58,21)
    node(p,'GardenHomeIcon',s,(55,765,36,36),'icon-home')
    tx=node(p,'GardenHomeLabel',s,(43,799,60,22),text='首页',size=16);comp(p,tx,'m_Text')['m_Color']=INK
    selected=node(p,'GardenHomeSelected',s,(50,822,46,3));comp(p,selected,'m_Sprite')['m_Color']=dict(r=.22,g=.66,b=.35,a=1)
    script=ROOT/'Assets/BlockOut/Runtime/UI/Components/BlockOutGardenHomePath.cs'
    root=next(g for g in p.gos.values() if p.rect(g)['m_Father']['fileID']==0)
    data=dict(Nodes=buttons,Numbers=numbers,Locks=locks,Available=SPR['tile-green'],Completed=SPR['tile-purple'],Locked=SPR['tile-grey'])
    existing=comp(p,root,'Nodes')
    if existing:existing.update(data)
    else:add_component(p,root,data,guid(script))

if __name__=='__main__':
    SPR=import_assets()
    for file in list(UI.glob('*.prefab'))+list((UI/'Items').glob('*.prefab')):
        apply(Prefab(str(file.relative_to(UI).with_suffix(''))))
    from refine_garden_ui import refine
    refine()
    print('Garden assets and all delivered prefabs integrated; Unity not invoked.')
