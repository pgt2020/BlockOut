"""Recording-driven geometry/import fixes. Offline only; never invokes Unity."""
from pathlib import Path
import json, re
import yaml
from PIL import Image
from polish_player_experience import Prefab, ROOT, UI

ART = ROOT/'Assets/BlockOut/Resources/UI/Garden'

def component(p, g, key):
    return next((d for _, d in p.components(g) if key in d), None)

def place(p, g, x, y, w, h):
    p.rect(g).update(m_AnchorMin={'x':0,'y':1}, m_AnchorMax={'x':0,'y':1},
        m_Pivot={'x':0,'y':1}, m_AnchoredPosition={'x':x,'y':-y}, m_SizeDelta={'x':w,'y':h})

def center_pivot(p, g):
    r=p.rect(g); old=r['m_Pivot']; size=dimensions(p,g)
    r['m_AnchoredPosition']['x']+=(.5-old['x'])*size[0]
    r['m_AnchoredPosition']['y']+=(.5-old['y'])*size[1]
    r['m_Pivot']={'x':.5,'y':.5}

def dimensions(p,g):
    r=p.rect(g); parent=p.ids.get(r['m_Father']['fileID'])
    pw,ph=dimensions(p,p.gos[parent['m_GameObject']['fileID']]) if parent else (390,844)
    a,b=r['m_AnchorMin'],r['m_AnchorMax'];s=r['m_SizeDelta']
    return (s['x']+pw*(b['x']-a['x']),s['y']+ph*(b['y']-a['y']))

def refine():
    sprites={}
    for asset in ART.glob('*.png'):
        path=Path(str(asset)+'.meta');m=yaml.safe_load(path.read_text(encoding='utf-8'));t=m['TextureImporter']
        w,h=Image.open(asset).size
        # Preserve the complete rounded ends. Old cuts crossed the end-cap curves.
        if asset.stem.startswith('button-') or asset.stem=='pill-cream':
            side=min(w//2-1,round(h*.55));vertical=(h-2)//2
            t['spriteBorder']=dict(x=side,y=vertical,z=side,w=vertical)
        t.update(textureCompression=0,crunchedCompression=0,compressionQuality=100,
                 maxTextureSize=4096,nPOTScale=0)
        t['mipmaps']['enableMipMap']=0
        t['platformSettings']=[dict(serializedVersion=3,buildTarget=target,maxTextureSize=4096,
            resizeAlgorithm=0,textureFormat=-1,textureCompression=0,compressionQuality=100,
            crunchedCompression=0,allowsAlphaSplitting=0,overridden=0,
            androidETC2FallbackOverride=0,forceMaximumCompressionQuality_BC6H_BC7=0)
            for target in ['DefaultTexturePlatform','Standalone','Android','iPhone']]
        path.write_text(yaml.safe_dump(m,sort_keys=False),encoding='utf-8')
        sprites[m['guid']]=(asset.stem,w,h)
    count=0
    for file in list(UI.glob('*.prefab'))+list((UI/'Items').glob('*.prefab')):
        p=Prefab(str(file.relative_to(UI).with_suffix('')));names={g['m_Name']:g for g in p.gos.values()}
        card=names.get('Card')
        if file.stem=='BlockOutAboutPopup':
            place(p,card,24,286,342,272)
            place(p,names['Heading'],16,20,310,36)
            place(p,names['Description'],24,76,294,88)
            component(p,names['Description'],'m_Text')['m_Text']='这块怎么出不去\n沿箭头移开方块，揭晓画作'
            place(p,names['AboutCloseBtn'],24,192,294,52)
        if file.stem=='BlockOutGuidePopup':
            place(p,card,24,262,342,320)
            place(p,names['Heading'],16,20,310,36)
            place(p,names['GuideBodyText'],24,78,294,136)
            component(p,names['GuideBodyText'],'m_Text')['m_Text']='轻点方块，沿箭头方向移出。\n前方有阻挡时，先移开其他块。\n清空棋盘即可揭晓画作。'
            place(p,names['GuideDismissBtn'],24,240,294,52)
            if 'GardenGuideMascot' in names:names['GardenGuideMascot']['m_IsActive']=0
        if file.stem=='BlockOutFailPopup':
            place(p,card,24,229,342,386)
            place(p,names['Heading'],16,20,310,36)
            place(p,names['FailReasonText'],24,68,294,30)
            place(p,names['FailReviveBtn'],24,116,294,56)
            place(p,names['FailReviveNote'],24,180,294,30)
            place(p,names['FailExhaustedNote'],24,116,294,90)
            names['FailExhaustedNote']['m_IsActive']=0
            place(p,names['FailRestartBtn'],24,230,294,52)
            place(p,names['FailQuitBtn'],24,294,294,52)
            place(p,names['FreeBadge'],244,101,64,24)
            for g in p.gos.values():
                if g['m_Name']=='GardenBrokenHeart':g['m_IsActive']=0
        if file.stem.startswith('Store'):
            if 'BuyBtn' in names:
                place(p,names['BuyBtn'],224,82,104,48)
                for ref in p.rect(names['BuyBtn'])['m_Children']:
                    child=p.gos[p.ids[ref['fileID']]['m_GameObject']['fileID']]
                    if component(p,child,'m_Text'):place(p,child,6,3,92,42)
                place(p,names['CoinText'],84,96,138,24)
                place(p,names['DescText'],84,43,238,38)
        if file.stem=='BlockOutSettlementPage':
            place(p,names['SettleHomeBtn'],16,48,64,48)
            place(p,names['SettleReplayBtn'],35,732,145,48)
            place(p,names['SettleCollectionBtn'],210,732,145,48)
        if file.stem=='BlockOutGameHud':
            for g in p.gos.values():
                if g['m_Name']=='Name':place(p,g,2,36,90,18)
                if g['m_Name']=='Cond':
                    place(p,g,1,54,92,18)
                    component(p,g,'m_Text')['m_FontData'].update(m_FontSize=14,m_BestFit=0)
                    old=component(p,g,'m_Text')['m_Text']
                    component(p,g,'m_Text')['m_Text']={'轮换高亮可飞块':'高亮可飞块','消除任意在场块':'消除一块'}.get(old,old)
                if g['m_Name']=='Icon':
                    pr=p.ids.get(p.rect(g)['m_Father']['fileID'])
                    if pr and p.gos[pr['m_GameObject']['fileID']]['m_Name'] in ['HintSlot','HammerSlot','MagicSlot']:
                        place(p,g,33,6,28,28)
            place(p,names['LevelSub'],75,72,240,20)
            place(p,names['ProgressText'],318,86,44,18)
        if file.stem=='BlockOutCollectionPage':
            component(p,names['CollectionChapterText'],'m_Text')['m_FontData'].update(m_FontSize=18,m_MaxSize=18,m_MinSize=16)
        if file.stem=='BlockOutPausePopup':
            place(p,card,24,250,342,344)
            place(p,names['Heading'],16,20,310,36)
            for name,y in [('PauseResumeBtn',76),('PauseRestartBtn',136),('PauseSettingsBtn',196),('PauseQuitBtn',256)]:
                place(p,names[name],24,y,294,52)
        if file.stem=='BlockOutSettingsPage':
            place(p,card,24,222,342,400)
            place(p,names['Heading'],16,20,310,36)
            for name,y in [('SettingsMusicSwitch',76),('SettingsSoundSwitch',136),('SettingsVibSwitch',196)]:
                place(p,names[name],24,y,294,52)
                for childref in p.rect(names[name])['m_Children']:
                    child=p.gos[p.ids[childref['fileID']]['m_GameObject']['fileID']]
                    if child['m_Name']=='Label':place(p,child,16,6,174,40)
            place(p,names['SettingsAboutBtn'],24,264,294,48)
            place(p,names['SettingsCloseBtn'],24,324,294,48)
        if file.stem=='BlockOutConfirmPopup':
            place(p,card,24,256,342,332)
            names['Heading']['m_IsActive']=0
            place(p,names['ConfirmTitle'],24,28,294,40)
            place(p,names['ConfirmBody'],28,88,286,120)
            place(p,names['ConfirmCancelBtn'],24,244,140,56)
            place(p,names['ConfirmOkBtn'],178,244,140,56)
            component(p,names['ConfirmTitle'],'m_Text')['m_FontData'].update(m_FontSize=26,m_BestFit=0)
            component(p,names['ConfirmBody'],'m_Text')['m_FontData'].update(m_FontSize=18,m_BestFit=0)
        for g in p.gos.values():
            im=component(p,g,'m_Sprite');tx=component(p,g,'m_Text');feedback=component(p,g,'Popup')
            if feedback is not None:center_pivot(p,g)
            if im:
                item=sprites.get(im.get('m_Sprite',{}).get('guid'))
                if item and im.get('m_Type')==1:
                    name,sw,sh=item;w,h=dimensions(p,g)
                    if name.startswith('button-') or name=='pill-cream':
                        im['m_PixelsPerUnitMultiplier']=sh/max(1,h)
                    elif name=='panel-cream':
                        im['m_PixelsPerUnitMultiplier']=max(3,160/max(1,min(w,h)*.42))
                    count+=1
                # A horizontal capsule is not a vertical progress rail.
                if g['m_Name']=='GardenPathRail':
                    im.update(m_Sprite={'fileID':0},m_Type=0,m_Color=dict(r=.95,g=.89,b=.71,a=.7))
                    place(p,g,192,120,6,475)
            if tx:
                f=tx['m_FontData'];size=f['m_FontSize']
                parent=p.ids.get(p.rect(g)['m_Father']['fileID'])
                pg=p.gos[parent['m_GameObject']['fileID']] if parent else None
                if pg and component(p,pg,'m_Interactable') is not None and g['m_Name']=='Text':
                    size=16 if 'Nav' in pg['m_Name'] else 20
                    f.update(m_FontSize=size,m_MaxSize=size,m_MinSize=16,m_BestFit=1)
                elif size<14:
                    f.update(m_FontSize=14,m_MaxSize=max(14,f.get('m_MaxSize',14)),m_MinSize=14)
                # Do not compound legacy outline/shadow with the illustrated font.
                for _,d in p.components(g):
                    if 'm_EffectDistance' in d:d['m_Enabled']=0
        p.save()
    print(json.dumps({'sliced_images_refined':count,'textures_uncompressed':len(sprites),'runtime':'not-run'}))

if __name__=='__main__':refine()
