"""Deterministic matte HUD refinement. Files only; never invokes Unity."""
from pathlib import Path
import copy, re, uuid
import yaml
from PIL import Image, ImageDraw
from polish_player_experience import Prefab, ROOT
ART=ROOT/'Assets/BlockOut/Resources/UI/Quality'
INK=dict(r=.23,g=.20,b=.17,a=1)
SECONDARY=dict(r=.40,g=.36,b=.31,a=1)
def comp(p,g,key):
    return next((d for _,d in p.components(g) if key in d),None)
def make_assets():
    ART.mkdir(parents=True,exist_ok=True)
    folder=Path(str(ART)+'.meta')
    if not folder.exists():folder.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid5(uuid.NAMESPACE_URL,'BlockOut/UI/Quality').hex+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
    template=yaml.safe_load((ROOT/'Assets/BlockOut/Resources/UI/Garden/panel-cream.png.meta').read_text())
    result={}
    for name,fill,edge in [('matte-panel','#FFF8ED','#D8CCB8'),('matte-tool','#F7F2E7','#E1D7C5')]:
        # Supersampled geometry, not an upscaled old bitmap. Flat center permits safe 9-slicing.
        im=Image.new('RGBA',(768,768));d=ImageDraw.Draw(im)
        d.rounded_rectangle((9,15,759,765),radius=96,fill=(62,48,30,20))
        d.rounded_rectangle((9,6,759,750),radius=96,fill=edge)
        d.rounded_rectangle((15,12,753,744),radius=90,fill=fill)
        im.resize((256,256),Image.Resampling.LANCZOS).save(ART/(name+'.png'))
        meta=copy.deepcopy(template);guid=uuid.uuid5(uuid.NAMESPACE_URL,'BlockOut/UI/Quality/'+name).hex;meta['guid']=guid
        t=meta['TextureImporter'];t.update(spriteBorder=dict(x=36,y=36,z=36,w=36),maxTextureSize=512,textureCompression=0)
        t.setdefault('textureSettings',{})['filterMode']=1
        for platform in t.get('platformSettings',[]):platform['maxTextureSize']=512
        (ART/(name+'.png.meta')).write_text(yaml.safe_dump(meta,sort_keys=False))
        result[name]=guid
    return result
def apply():
    sprites=make_assets();p=Prefab('BlockOutGameHud')
    font=re.search(r'guid: (\w+)',(ROOT/'Assets/Resources/Fonts/SourceHanSansCN-Regular.otf.meta').read_text())[1]
    for g in p.gos.values():
        name=g['m_Name'];r=p.rect(g);pr=p.ids.get(r['m_Father']['fileID']);pg=p.gos[pr['m_GameObject']['fileID']] if pr else None
        pn=pg['m_Name'] if pg else ''
        tx=comp(p,g,'m_Text')
        if tx:
            size={'LevelTitle':22,'LevelSub':16,'TimerText':16,'ProgressText':14,'RemainingText':16,'HintText':16,'Name':18,'Cond':14,'CountText':14}.get(name,16)
            tx['m_FontData'].update(m_Font=dict(fileID=12800000,guid=font,type=3),m_FontSize=size,m_MinSize=size,m_MaxSize=size,m_BestFit=0,m_FontStyle=0)
            # Dynamic inventory must fit its badge, even at large counts.
            if name=='CountText':tx['m_FontData'].update(m_BestFit=1,m_MinSize=10)
            tx['m_Color']=dict(SECONDARY if name in ('LevelSub','RemainingText','Cond') else INK)
            if name=='CountText':tx['m_Color']=dict(r=1,g=1,b=1,a=1)
            if name=='HintText':tx['m_Text']='沿箭头方向，依次移出方块'
            for _,c in p.components(g):
                if 'm_EffectDistance' in c:c['m_Enabled']=0
        im=comp(p,g,'m_Sprite')
        if im and (name in ('GardenHudPlate','HintPill') or name=='Stroke' and pn in ('BoardTray','BottomToolbar','HintSlot','HammerSlot','MagicSlot')):
            asset='matte-tool' if pn in ('HintSlot','HammerSlot','MagicSlot') else 'matte-panel'
            im.update(m_Sprite=dict(fileID=21300000,guid=sprites[asset],type=3),m_Type=1,m_PreserveAspect=0,m_PixelsPerUnitMultiplier=2,m_Color=dict(r=1,g=1,b=1,a=1))
        if name in ('Shadow','Fill') and pn in ('BoardTray','BottomToolbar','HintSlot','HammerSlot','MagicSlot'):g['m_IsActive']=0
        if name=='Gloss' and pn=='ProgressBar':g['m_IsActive']=0
    p.save()
if __name__=='__main__':apply();print('Matte HUD applied; Unity not invoked.')
