"""Offline preview of serialized UGUI geometry, NOT a Unity render.
Uses actual prefabs, sprite borders and fonts. No editor access.
"""
from pathlib import Path
import re,sys,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps
from polish_player_experience import Prefab,ROOT,UI
from integrate_garden_ui import comp,children,parent

OUT=ROOT/'design/ui/garden-suite-20261117/integration-previews'
OUT.mkdir(exist_ok=True)
ASSETS={}
for directory in [ROOT/'Assets/BlockOut/Resources/UI',ROOT/'Assets/BlockOut/Resources/ArtOutPresentation/Sprites',UI/'AuthoredSprites',ROOT/'Assets/Resources/Fonts']:
    for meta in directory.rglob('*.meta'):
        m=re.search(r'guid: (\w+)',meta.read_text(encoding='utf-8-sig',errors='ignore'))
        if m:ASSETS[m[1]]=Path(str(meta)[:-5])

def sliced(im,size,border,multiplier=1):
    w,h=im.size;tw,th=size;l,b,r,t=border
    if not any(border):return im.resize(size,Image.Resampling.LANCZOS)
    factor=min(1/max(1,multiplier),tw/max(1,l+r),th/max(1,t+b));dl,dr,dt,db=[int(v*factor) for v in (l,r,t,b)]
    xs=[0,l,w-r,w];ys=[0,t,h-b,h];dx=[0,dl,tw-dr,tw];dy=[0,dt,th-db,th]
    o=Image.new('RGBA',size)
    for j in range(3):
        for i in range(3):
            sw,sh=dx[i+1]-dx[i],dy[j+1]-dy[j]
            if sw>0 and sh>0:o.paste(im.crop((xs[i],ys[j],xs[i+1],ys[j+1])).resize((sw,sh),Image.Resampling.LANCZOS),(dx[i],dy[j]))
    return o

def preview(name,root_size=(390,844)):
    p=Prefab(name);o=Image.new('RGBA',root_size,(239,232,216,0 if name.startswith('Items/') else 255));boxes={};records=[]
    if name=='BlockOutStorePage':p.go('StoreEmptyText')['m_IsActive']=0
    def draw(g,box,forced=None):
        if not g.get('m_IsActive',1):return
        rt=p.rect(g);px,py,pw,ph=box;a=rt['m_AnchorMin'];b=rt['m_AnchorMax'];pivot=rt['m_Pivot'];pos=rt['m_AnchoredPosition'];sz=rt['m_SizeDelta']
        if rt['m_Father']['fileID']==0:x,y,w,h=0,0,*root_size
        elif g['m_Name']=='DesignSurface':x,y,w,h=0,0,390,844
        else:
            w=pw*(b['x']-a['x'])+sz['x'];h=ph*(b['y']-a['y'])+sz['y']
            x=px+pw*a['x']+pos['x']-pivot['x']*sz['x'];y=py+ph*(1-a['y'])-pos['y']-(1-pivot['y'])*h-pivot['y']*ph*(b['y']-a['y'])
        if forced:x,y,w,h=forced
        if g['m_Name']=='Content' and h<=0:h=624
        boxes[g['m_Name']]=(x,y,w,h)
        if w<=0 or h<=0:return
        imd=comp(p,g,'m_Sprite');td=comp(p,g,'m_Text')
        if imd:
            color=imd.get('m_Color',dict(r=1,g=1,b=1,a=1));size=(max(1,round(w)),max(1,round(h)));path=ASSETS.get(imd.get('m_Sprite',{}).get('guid'))
            if path and path.exists():
                im=Image.open(path).convert('RGBA')
                if g['m_Name']=='GardenBackdrop':im=ImageOps.fit(im,size)
                elif imd.get('m_Type')==1:
                    import yaml
                    m=yaml.safe_load(Path(str(path)+'.meta').read_text());bdr=m['TextureImporter']['spriteBorder'];im=sliced(im,size,[int(bdr.get(k,0)) for k in ('x','y','z','w')],imd.get('m_PixelsPerUnitMultiplier',1))
                elif imd.get('m_PreserveAspect'):
                    im.thumbnail(size,Image.Resampling.LANCZOS);layer=Image.new('RGBA',size);layer.paste(im,((size[0]-im.width)//2,(size[1]-im.height)//2));im=layer
                else:im=im.resize(size,Image.Resampling.LANCZOS)
                arr=np.array(im).astype(float);arr*=np.array([color[k] for k in ('r','g','b','a')]);im=Image.fromarray(arr.clip(0,255).astype('uint8'))
            else:im=Image.new('RGBA',size,tuple(round(color[k]*255) for k in ('r','g','b','a')))
            o.alpha_composite(im,(round(x),round(y)))
        if td:
            text=td['m_Text'];fontpath=ASSETS.get(td['m_FontData']['m_Font'].get('guid'),ROOT/'Assets/Resources/Fonts/SourceHanSansCN-Regular.otf')
            fs=td['m_FontData']['m_FontSize'];font=ImageFont.truetype(str(fontpath),fs)
            while font.getlength(text.replace('\n',''))>w and '\n' not in text and fs>td['m_FontData'].get('m_MinSize',12) and td['m_FontData'].get('m_BestFit'):
                fs-=1;font=ImageFont.truetype(str(fontpath),fs)
            lines=[]
            for line in text.split('\n'):
                current=''
                for ch in line:
                    if font.getlength(current+ch)>w and current:lines.append(current);current=ch
                    else:current+=ch
                lines.append(current)
            align=td['m_FontData'].get('m_Alignment',4);col=tuple(round(td['m_Color'][k]*255) for k in ('r','g','b','a'));height=len(lines)*fs*1.15
            yy=y if align<3 else y+(h-height)/2 if align<6 else y+h-height
            for line in lines:
                xx=x if align%3==0 else x+(w-font.getlength(line))/2 if align%3==1 else x+w-font.getlength(line)
                ImageDraw.Draw(o).text((xx,yy),line,font=font,fill=col,anchor='lt');yy+=fs*1.15
            records.append((g['m_Name'],text,x,y,w,h))
        layout=comp(p,g,'m_ChildForceExpandHeight')
        yy=y
        for ch in children(p,g):
            if layout and ch.get('m_IsActive',1):
                element=comp(p,ch,'m_PreferredHeight');hh=element['m_PreferredHeight'] if element and element['m_PreferredHeight']>0 else max(0,p.rect(ch)['m_SizeDelta']['y'])
                draw(ch,(x,y,w,h),(x,yy,w,hh));yy+=hh+layout.get('m_Spacing',0)
            else:draw(ch,(x,y,w,h))
    root=next(g for g in p.gos.values() if p.rect(g)['m_Father']['fileID']==0);draw(root,(0,0,390,844))
    # Lists are runtime instantiated; previews deliberately keep serialized geometry only.
    if name=='BlockOutStorePage':
        for i,item in enumerate(['StoreHint','StoreHammer','StoreMagic']):o.alpha_composite(preview('Items/'+item,(342,136)),(24,92+i*148))
    if name=='BlockOutCollectionPage':
        # Example rows/cells use actual item prefabs, not simulated runtime state.
        box=boxes.get('Cells')
        if box:
            for i in range(12):o.alpha_composite(preview('Items/RepeatItem',(44,44)),(round(box[0])+i%6*52,round(box[1])+i//6*48))
        for i in range(3):o.alpha_composite(preview('Items/ChapterItem',(342,76)),(24,440+i*86))
    o.convert('RGB').save(OUT/(name.replace('/','-')+'.jpg'))
    return o

if __name__=='__main__':
    names=['BlockOutHomePage','BlockOutGameHud','BlockOutSettlementPage','BlockOutStorePage','BlockOutCollectionPage','BlockOutPausePopup','BlockOutFailPopup','BlockOutSettingsPage','BlockOutConfirmPopup','BlockOutGuidePopup','BlockOutAboutPopup','BlockOutLoadingPage']
    sheet=Image.new('RGB',(390*4,884*3),'#293643');d=ImageDraw.Draw(sheet)
    for i,n in enumerate(names):
        im=preview(n);x=i%4*390;y=i//4*884;sheet.paste(im.convert('RGB'),(x,y+32));d.text((x+12,y+8),n,fill='white')
    sheet.save(OUT/'all-pages-offline.jpg')
    print(OUT)
