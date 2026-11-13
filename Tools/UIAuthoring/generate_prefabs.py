"""Deterministic, editor-independent UI asset authoring. Does not launch or refresh Unity.

Run from any directory with Python, PyYAML and Pillow. Existing prefab GUIDs are kept.
The editor baker is an alternative authoring path; do not rebake after hand-editing layouts.
"""
from pathlib import Path
import re, uuid, yaml
from PIL import Image, ImageDraw

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self,data): return True

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI'
RUNTIME = ROOT / 'Assets/BlockOut/Runtime/UI'
PACKAGE = next((ROOT / 'Library/PackageCache').glob('com.unity.ugui@*'))
WHITE = (1, 1, 1, 1)
CREAM = (1, .963, .925, 1)
INK = (.32, .22, .18, 1)
CORAL = (.97, .43, .37, 1)
MINT = (.66, .86, .76, 1)
MUTED = (.88, .85, .80, 1)

def guid(path):
    meta = Path(str(path) + '.meta')
    if not meta.exists():
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_text('fileFormatVersion: 2\nguid: ' + uuid.uuid4().hex + '\n', encoding='utf-8')
    return re.search(r'guid: (\w+)', meta.read_text(encoding='utf-8-sig'))[1]

def script(name):
    paths = list(RUNTIME.rglob(name + '.cs')) or list(PACKAGE.rglob(name + '.cs'))
    if not paths: raise ValueError(name)
    return {'fileID': 11500000, 'guid': guid(paths[0]), 'type': 3}

def ref(n): return {'fileID': n}
def vec(x=0, y=0): return {'x': x, 'y': y}
def rgba(c): return dict(zip(('r','g','b','a'), c))
def ext(path, file_id): return {'fileID': file_id, 'guid': guid(path), 'type': 3}

def sprite(name, draw):
    path = DEST / 'AuthoredSprites' / (name + '.png')
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new('RGBA', (128,128)); d = ImageDraw.Draw(im); draw(d); im.save(path)
    g = guid(path)
    meta = {'fileFormatVersion':2,'guid':g,'TextureImporter':{
        'internalIDToNameTable':[], 'externalObjects':{}, 'serializedVersion':12,
        'mipmaps':{'enableMipMap':0}, 'isReadable':0, 'textureType':8,
        'textureShape':1,'sRGBTexture':1,'alphaIsTransparency':1,'spriteMode':1,
        'spritePixelsToUnits':100,'spriteMeshType':1,'spriteAlignment':0,
        'spritePivot':vec(.5,.5),'spriteBorder':{'x':32,'y':32,'z':32,'w':32} if name=='round' else {'x':0,'y':0,'z':0,'w':0},
        'textureSettings':{'serializedVersion':2,'filterMode':1,'aniso':1,'mipBias':0,'wrapU':1,'wrapV':1,'wrapW':1},
        'maxTextureSize':2048,'nPOTScale':0,'spriteSheet':{'serializedVersion':2,'sprites':[], 'outline':[], 'physicsShape':[], 'bones':[], 'spriteID':uuid.uuid5(uuid.NAMESPACE_URL,'blockout:'+name).hex,'internalID':0,'vertices':[], 'indices':'','edges':[], 'weights':[],'secondaryTextures':[],'nameFileIdTable':{}},
        'platformSettings':[], 'userData':'','assetBundleName':'','assetBundleVariant':''}}
    Path(str(path)+'.meta').write_text(yaml.safe_dump(meta,sort_keys=False),encoding='utf-8')
    return ext(path,21300000)

ROUND=sprite('round',lambda d:d.rounded_rectangle((0,0,127,127),radius=30,fill='white'))
CHECK=sprite('check',lambda d:d.line([(25,65),(52,90),(105,35)],fill='white',width=13))
LOCK=sprite('lock',lambda d:(d.rounded_rectangle((36,54,92,110),radius=8,fill='white'),d.arc((40,20,88,80),180,360,fill='white',width=10)))
HEART=sprite('heart',lambda d:(d.ellipse((15,22,69,76),fill='white'),d.ellipse((59,22,113,76),fill='white'),d.polygon([(18,60),(110,60),(64,114)],fill='white')))
BULB=sprite('bulb',lambda d:(d.ellipse((30,12,98,80),fill='white'),d.rectangle((48,70,80,94),fill='white'),d.line([(48,105),(80,105)],fill='white',width=9)))
HAMMER=sprite('hammer',lambda d:(d.line([(35,110),(83,35)],fill='white',width=16),d.polygon([(52,18),(65,2),(112,35),(98,54)],fill='white')))
WAND=sprite('wand',lambda d:(d.line([(22,111),(84,45)],fill='white',width=12),d.polygon([(89,8),(97,27),(118,29),(102,43),(107,64),(88,53),(68,63),(73,42),(58,28),(80,27)],fill='white')))
FONT=ext(ROOT/'Assets/Resources/Fonts/SourceHanSansCN-Regular.otf',12800000)

class Node:
    def __init__(self,page,name,parent=None,box=(0,0,390,844),color=None,active=True):
        self.p=page; self.go=page.alloc(); self.rt=page.alloc(); self.children=[]; self.components=[self.rt]
        self.name=name; self.parent=parent; self.box=box; self.active=active
        if parent: parent.children.append(self)
        self.anchor_min=vec(0,1);self.anchor_max=vec(0,1);self.pivot=vec(0,1)
        self.position=vec(box[0],-box[1]); self.size=vec(box[2],box[3]); self.scale={'x':1,'y':1,'z':1}
        page.nodes.append(self)
        self.image=self.img(color) if color else None
    def component(self,name,fields):
        cid=self.p.alloc(); self.components.append(cid)
        data={'m_ObjectHideFlags':0,'m_CorrespondingSourceObject':ref(0),'m_PrefabInstance':ref(0),'m_PrefabAsset':ref(0),
              'm_GameObject':ref(self.go),'m_Enabled':1,'m_EditorHideFlags':0,'m_Script':script(name),'m_Name':'','m_EditorClassIdentifier':''}
        data.update(fields);self.p.docs.append((114,cid,'MonoBehaviour',data));return cid
    def renderer(self):
        cid=self.p.alloc();self.components.append(cid)
        self.p.docs.append((222,cid,'CanvasRenderer',{'m_ObjectHideFlags':0,'m_CorrespondingSourceObject':ref(0),'m_PrefabInstance':ref(0),'m_PrefabAsset':ref(0),'m_GameObject':ref(self.go),'m_CullTransparentMesh':1}))
    def img(self,color=WHITE,sp=ROUND,hit=False,filled=False):
        self.renderer()
        return self.component('Image',{'m_Material':ref(0),'m_Color':rgba(color),'m_RaycastTarget':int(hit),'m_Maskable':1,'m_OnCullStateChanged':{'m_PersistentCalls':{'m_Calls':[]}},'m_Sprite':sp or ref(0),'m_Type':3 if filled else (1 if sp==ROUND else 0),'m_PreserveAspect':0,'m_FillCenter':1,'m_FillMethod':0,'m_FillAmount':1,'m_FillClockwise':1,'m_FillOrigin':0,'m_UseSpriteMesh':0,'m_PixelsPerUnitMultiplier':1})
    def text(self,value,size=16,color=INK,align=4):
        self.renderer()
        return self.component('Text',{'m_Material':ref(0),'m_Color':rgba(color),'m_RaycastTarget':0,'m_Maskable':1,'m_FontData':{'m_Font':FONT,'m_FontSize':size,'m_FontStyle':0,'m_BestFit':1,'m_MinSize':max(9,size-3),'m_MaxSize':size,'m_Alignment':align,'m_AlignByGeometry':0,'m_RichText':1,'m_HorizontalOverflow':0,'m_VerticalOverflow':0,'m_LineSpacing':1},'m_Text':value})
    def enable_hit(self):
        for doc in self.p.docs:
            if doc[1]==self.image: doc[3]['m_RaycastTarget']=1
    def button(self):
        if not self.image:self.image=self.img(CORAL,hit=True)
        else:
            for doc in self.p.docs:
                if doc[1]==self.image:doc[3]['m_RaycastTarget']=1
        return self.component('Button',{'m_Navigation':{'m_Mode':0,'m_WrapAround':0,'m_SelectOnUp':ref(0),'m_SelectOnDown':ref(0),'m_SelectOnLeft':ref(0),'m_SelectOnRight':ref(0)},'m_Transition':1,'m_Colors':{'m_NormalColor':rgba(WHITE),'m_HighlightedColor':rgba(WHITE),'m_PressedColor':rgba((.88,.88,.88,1)),'m_SelectedColor':rgba(WHITE),'m_DisabledColor':rgba((.65,.65,.65,.5)),'m_ColorMultiplier':1,'m_FadeDuration':.1},'m_Interactable':1,'m_TargetGraphic':ref(self.image),'m_OnClick':{'m_PersistentCalls':{'m_Calls':[]}}})

class Page:
    def __init__(self,name,view,popup=False,item=False):
        self.name=name;self.view=view;self.next=100000;self.nodes=[];self.docs=[];self.fields={};self.item=item
        self.root=Node(self,name,box=(0,0,390,844))
        self.root.anchor_min=vec();self.root.anchor_max=vec(1,1);self.root.pivot=vec(.5,.5);self.root.position=vec();self.root.size=vec()
        if popup:self.root.img((0,0,0,.35),None,True)
        self.surface=Node(self,'DesignSurface',self.root,color=None if popup else CREAM) if not item else self.root
        if not item:
            self.surface.anchor_min=self.surface.anchor_max=vec(.5,.5);self.surface.pivot=vec(.5,.5);self.surface.position=vec()
            self.root.component('BlockOutPageLayout',{'Surface':ref(self.surface.rt),'DesignSize':vec(390,844),'RespectSafeArea':1})
    def alloc(self):self.next+=1;return self.next
    def node(self,name,box,parent=None,color=None,active=True):return Node(self,name,parent or self.surface,box,color,active)
    def label(self,key,text,box,parent=None,size=16,color=INK,align=4):
        n=self.node(key,box,parent);cid=n.text(text,size,color,align);self.fields[key]=ref(cid);return n,cid
    def button(self,key,text,box,parent=None,color=CORAL):
        n=self.node(key,box,parent,color);cid=n.button();self.fields[key]=ref(cid)
        title=Node(self,'Text',n,(8,4,box[2]-16,box[3]-8));tid=title.text(text,16,WHITE if color==CORAL else INK)
        return n,cid,tid
    def image(self,key,box,parent=None,color=MINT,sp=ROUND,active=True,filled=False):
        n=self.node(key,box,parent,active=active);cid=n.img(color,sp,filled=filled);self.fields[key]=ref(cid);return n,cid
    def nav(self,prefix=''):
        parent=self.node('BottomNav',(24,744,342,72),color=WHITE)
        for i,(key,title) in enumerate([('Home','首页'),('Collection','图鉴'),('Store','商店')]):
            self.button(prefix+'Nav'+key+'Btn',title,(i*114+4,8,106,56),parent,MINT if i==0 else WHITE)
    def art(self,rootkey,arraykey,box,parent=None):
        viewport=self.node(rootkey,box,parent,color=MUTED);viewport.component('RectMask2D',{'m_Padding':{'x':0,'y':0,'z':0,'w':0},'m_Softness':vec()})
        art=Node(self,'Artwork',viewport,(0,0,box[2],box[3]));self.fields[rootkey]=ref(viewport.rt)
        images=[]
        for i in range(12):
            n=Node(self,'Region_'+str(i),art,(i%4*box[2]/4,i//4*box[3]/3,box[2]/4,box[3]/3));images.append(ref(n.img(MUTED,None)))
        self.fields[arraykey]=images;return viewport,art
    def scroll(self,name,box,parent=None):
        viewport=self.node(name,box,parent);viewport.img((0,0,0,0),None,True);viewport.component('RectMask2D',{'m_Padding':{'x':0,'y':0,'z':0,'w':0},'m_Softness':vec()})
        content=Node(self,'Content',viewport,(0,0,box[2],0));content.anchor_max=vec(1,1);content.size=vec(0,0)
        cid=viewport.component('ScrollRect',{'m_Content':ref(content.rt),'m_Horizontal':0,'m_Vertical':1,'m_MovementType':2,'m_Elasticity':.1,'m_Inertia':1,'m_DecelerationRate':.135,'m_ScrollSensitivity':25,'m_Viewport':ref(viewport.rt),'m_HorizontalScrollbar':ref(0),'m_VerticalScrollbar':ref(0),'m_OnValueChanged':{'m_PersistentCalls':{'m_Calls':[]}}})
        vertical(content);return content,cid
    def save(self):
        # Every serialized view field must be bound; unrelated helper fields stay off the View.
        source=next(RUNTIME.rglob(self.view+'.cs')).read_text(encoding='utf-8-sig')
        required=[]
        for declaration in re.findall(r'public\s+[\w.\[\]]+\s+([^;{}]+);',source):
            required.extend(part.split('=')[0].strip() for part in declaration.split(','))
        missing=set(required)-set(self.fields)
        if missing:raise ValueError(self.name+': '+str(missing))
        vid=self.root.component(self.view,{k:self.fields[k] for k in required})
        docs=[]
        for n in self.nodes:
            docs.append((1,n.go,'GameObject',{'m_ObjectHideFlags':0,'m_CorrespondingSourceObject':ref(0),'m_PrefabInstance':ref(0),'m_PrefabAsset':ref(0),'serializedVersion':6,'m_Component':[{'component':ref(c)} for c in n.components],'m_Layer':5,'m_Name':n.name,'m_TagString':'Untagged','m_IsActive':int(n.active)}))
            docs.append((224,n.rt,'RectTransform',{'m_ObjectHideFlags':0,'m_CorrespondingSourceObject':ref(0),'m_PrefabInstance':ref(0),'m_PrefabAsset':ref(0),'m_GameObject':ref(n.go),'m_LocalRotation':{'x':0,'y':0,'z':0,'w':1},'m_LocalPosition':{'x':0,'y':0,'z':0},'m_LocalScale':n.scale,'m_Children':[ref(c.rt) for c in n.children],'m_Father':ref(n.parent.rt if n.parent else 0),'m_LocalEulerAnglesHint':{'x':0,'y':0,'z':0},'m_AnchorMin':n.anchor_min,'m_AnchorMax':n.anchor_max,'m_AnchoredPosition':n.position,'m_SizeDelta':n.size,'m_Pivot':n.pivot}))
        path=DEST/(('Items/' if self.item else '')+self.name+'.prefab');path.parent.mkdir(parents=True,exist_ok=True)
        text='%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'
        for kind,cid,label,data in docs+self.docs:text+='--- !u!'+str(kind)+' &'+str(cid)+'\n'+yaml.dump({label:data},Dumper=NoAliasDumper,allow_unicode=True,sort_keys=False,width=120)
        path.write_text(text,encoding='utf-8');guid(path)
        return ext(path,vid)

def vertical(n):
    n.component('VerticalLayoutGroup',{'m_Padding':{'m_Left':0,'m_Right':0,'m_Top':0,'m_Bottom':0},'m_ChildAlignment':0,'m_Spacing':12,'m_ChildForceExpandWidth':1,'m_ChildForceExpandHeight':0,'m_ChildControlWidth':1,'m_ChildControlHeight':1,'m_ChildScaleWidth':0,'m_ChildScaleHeight':0,'m_ReverseArrangement':0})
    n.component('ContentSizeFitter',{'m_HorizontalFit':0,'m_VerticalFit':2})
def height(n,h):n.component('LayoutElement',{'m_IgnoreLayout':0,'m_MinWidth':-1,'m_MinHeight':h,'m_PreferredWidth':-1,'m_PreferredHeight':h,'m_FlexibleWidth':-1,'m_FlexibleHeight':0,'m_LayoutPriority':1})

def make_items():
    p=Page('ChapterItem','BlockOutChapterItemView',item=True);r=p.root;r.size=vec(342,72);r.image=r.img(WHITE);p.fields['Button']=ref(r.button());height(r,72)
    p.label('Title','章节',(76,10,250,24),r);p.label('Subtitle','章节进度',(76,36,250,24),r,size=12)
    p.image('Thumbnail',(12,10,52,52),r);n,_=p.image('LockIcon',(28,24,22,22),r,INK,LOCK);p.fields['Locked']=ref(n.go)
    chapter=p.save()
    p=Page('RepeatItem','BlockOutRepeatItemView',item=True);r=p.root;r.size=vec(44,44);r.image=r.img((0,0,0,0),None,True);p.fields['Button']=ref(r.button())
    p.image('Background',(4,4,36,36),r);p.label('Number','1',(8,8,28,28),r,size=12)
    for key,sp in [('Mark',CHECK),('Locked',LOCK)]:n,_=p.image(key,(13,13,18,18),r,INK,sp);p.fields[key]=ref(n.go)
    repeat=p.save();stores=[]
    for i,(name,title,desc) in enumerate([('Hint','提示','高亮可飞出的方块'),('Hammer','锤子','消除任意在场方块'),('Magic','魔法棒','自动消除一组方块')]):
        p=Page('Store'+name,'BlockOutStoreItemView',item=True);r=p.root;r.size=vec(342,112);r.image=r.img(WHITE);height(r,112)
        product={'Tool':i,'CardRoot':ref(r.go),'CardImg':ref(r.image)}
        _,cid=p.image('Icon',(20,26,44,44),r,MINT,[BULB,HAMMER,WAND][i]);product['IconImg']=ref(cid)
        n,_=p.image('LockBadge',(50,12,20,20),r,INK,LOCK);product['LockBadge']=ref(n.go)
        for key,text,box,size in [('NameText',title,(84,12,160,24),18),('DescText',desc,(84,38,160,36),12),('CoinText','300 金币',(84,78,150,20),12)]:_,cid=p.label(key,text,box,r,size);product[key]=ref(cid)
        _,cid,tid=p.button('BuyBtn','购买',(252,38,76,40),r);product['BuyBtn']=ref(cid);product['BuyText']=ref(tid)
        p.fields['Product']=product;stores.append(p.save())
    return chapter,repeat,stores

def common_header(p,prefix,title):
    p.button(prefix+'BackBtn','返回',(24,28,64,44),color=WHITE)
    p.label('PageTitle',title,(100,30,150,40),size=22)
    p.label(prefix+'CoinText','0',(270,32,96,36),size=18)

def make_pages(chapter,repeat,stores):
    p=Page('BlockOutLoadingPage','BlockOutLoadingView');p.label('Title','BlockOut',(45,310,300,60),size=40,color=CORAL);p.label('Sub','加载中…',(95,384,200,30));p.save()
    p=Page('BlockOutHomePage','BlockOutHomeView')
    p.label('Logo','BlockOut',(24,28,180,42),size=28,color=CORAL)
    p.label('HomeCoinText','300',(224,34,82,30),size=18);p.button('HomeSettingsBtn','设置',(314,28,52,44),color=WHITE)
    card=p.node('PreviewCard',(24,100,342,288),color=WHITE);p.fields['HomePreviewCard']=ref(card.rt)
    art,root=p.art('HomeArtViewport','HomeRegionArts',(12,12,318,264),card)
    locks=[]
    for i in range(12):n=Node(p,'Lock_'+str(i),root,(i%4*79.5+30,i//4*88+32,20,24));n.img(INK,LOCK);locks.append(ref(n.go))
    p.fields['HomeRegionLocks']=locks
    p.label('HomePieceBadge','0/12',(250,14,74,26),card,size=12)
    fail=p.node('FailBox',(12,12,318,264),card,MUTED,False);p.fields['HomeFailBox']=ref(fail.go)
    p.button('HomeRetryBtn','重试',(99,130,120,44),fail);p.label('HomeRetryExhausted','稍后再试',(79,180,160,24),fail)
    tag,_=p.label('HomePlaceholderTag','作品预览',(110,246,130,24),card,size=12);p.fields['HomePlaceholderTag']=ref(tag.go)
    n,cid,tid=p.button('HomeCtaButton','开始游戏',(24,412,342,80));p.fields['HomeCtaTitle']=ref(tid)
    p.label('HomeCtaSub','第 1 关',(24,48,294,24),n,size=12,color=WHITE)
    # Keep title and subtitle separate inside the CTA.
    n.children[0].size=vec(326,36)
    p.button('HomeCtaSecondary','重玩本章',(79,504,232,40),color=WHITE)
    p.label('HomeChapterTitle','第一章',(24,562,220,24));p.button('HomeCollectionLink','查看图鉴',(274,556,92,36),color=WHITE)
    p.image('HomeProgressFill',(24,598,342,10),color=CORAL,filled=True)
    nodes=[]
    for i in range(12):_,cid=p.image('Node_'+str(i),(24+i*29,626,18,18),color=MINT);nodes.append(ref(cid))
    p.fields['HomeNodes']=nodes;p.label('HomePieceText','拼片 0/12',(24,662,342,28));p.nav();p.save()
    p=Page('BlockOutGameHud','BlockOutBoardPageView')
    p.button('BoardPauseBtn','暂停',(24,24,60,44),color=WHITE)
    p.label('BoardLevelTitle','第 1 章 · 第 1 关',(92,24,274,28),size=20);p.label('BoardLevelSub','沿箭头方向移除方块',(92,54,274,24),size=12)
    hearts=[]
    heartrow=p.node('Hearts',(146,94,100,28))
    for i in range(3):_,cid=p.image('Heart'+str(i),(i*36,0,28,28),heartrow,color=CORAL,sp=HEART);hearts.append(ref(cid))
    p.fields['BoardHearts']=hearts
    timer=p.node('Timer',(145,90,100,36),color=WHITE);p.fields['BoardTimerPill']=ref(timer.rt);p.label('BoardTimerText','02:00',(0,0,100,36),timer)
    p.label('BoardRemainingText','剩余 0 块',(24,142,342,28))
    area=p.node('BoardArea',(18,188,354,354));p.fields['BoardArea']=ref(area.rt)
    p.label('BoardHintPill','轻点整块方块，沿箭头方向飞出',(24,562,342,44),size=13)
    for i,(key,title) in enumerate([('HintSlot','提示'),('HammerSlot','锤子'),('MagicSlot','魔法棒')]):
        root=p.node(key,(24+i*116,644,110,144),color=WHITE);slot={'Rect':ref(root.rt),'Button':ref(root.button())}
        _,cid=p.image('Icon',(37,26,36,36),root,MINT,[BULB,HAMMER,WAND][i]);slot['Icon']=ref(cid)
        badge=p.node('CountBadge',(74,8,28,24),root,CORAL);slot['CountBadge']=ref(badge.go);_,cid=p.label('Count','0',(0,0,28,24),badge,12,WHITE);slot['CountText']=ref(cid)
        lock,_=p.image('LockBadge',(76,8,22,24),root,INK,LOCK);slot['LockBadge']=ref(lock.go)
        for field,text,y in [('NameText',title,72),('CondText','',106)]:_,cid=p.label(field,text,(4,y,102,28),root,12);slot[field]=ref(cid)
        p.fields[key]=slot
    p.save()
    p=Page('BlockOutStorePage','BlockOutStoreView');common_header(p,'Store','商店');p.nav('Store')
    content,_=p.scroll('StoreViewport',(24,92,342,624));p.fields['StoreListRoot']=ref(content.rt);p.fields['StoreItemPrefabs']=stores
    p.label('StoreEmptyText','暂无商品',(24,330,342,36));p.save()
    p=Page('BlockOutCollectionPage','BlockOutCollectionView');common_header(p,'Collection','收藏');p.nav('Collection')
    content,sc=p.scroll('ContentViewport',(24,92,342,624));p.fields['CollectionContent']=ref(content.rt);p.fields['collectionScroll']=ref(sc)
    summary=p.node('SummaryCard',(0,0,342,190),content,WHITE);height(summary,190)
    p.art('CollectionThumbRoot','CollectionThumbRegions',(12,12,120,156),summary)
    p.label('CollectionChapterText','第一章',(144,14,180,32),summary,14);p.label('CollectionPieceText','拼片 0/12',(144,52,180,30),summary,12)
    p.image('CollectionProgressFill',(144,94,180,10),summary,CORAL,filled=True);p.button('CollectionViewBigBtn','查看大图',(144,124,180,44),summary)
    n,_=p.label('CollectionEmptyText','还没有拼片，去完成关卡吧',(0,0,342,40),content,13);height(n,40)
    retry=p.node('RetryBar',(0,0,342,60),content,WHITE,False);height(retry,60);p.fields['CollectionRetryBar']=ref(retry.rt)
    p.label('CollectionRetryText','图片加载失败',(8,8,226,44),retry,12);p.button('CollectionRetryBtn','重试',(244,8,90,44),retry)
    rows=p.node('ChapterList',(0,0,342,0),content);vertical(rows);p.fields['CollectionChapterList']=ref(rows.rt);p.fields['ChapterItemPrefab']=chapter
    repeatcard=p.node('RepeatCard',(0,0,342,172),content,WHITE);height(repeatcard,172);p.fields['CollectionRepeatGrid']=ref(repeatcard.rt)
    p.label('RepeatLabel','重复挑战',(12,8,318,28),repeatcard)
    grid=p.node('Cells',(12,42,318,96),repeatcard);grid.component('GridLayoutGroup',{'m_Padding':{'m_Left':0,'m_Right':0,'m_Top':0,'m_Bottom':0},'m_ChildAlignment':1,'m_StartCorner':0,'m_StartAxis':0,'m_CellSize':vec(44,44),'m_Spacing':vec(8,4),'m_Constraint':1,'m_ConstraintCount':6})
    p.fields['RepeatListRoot']=ref(grid.rt);p.fields['RepeatItemPrefab']=repeat
    p.label('RepeatNote','已通关关卡可重复挑战',(12,142,318,22),repeatcard,11)
    big=p.node('CollectionBigLayer',(0,0,390,844),color=(0,0,0,.4),active=False);p.fields['CollectionBigLayer']=ref(big.go);big.enable_hit()
    card=p.node('Card',(24,100,342,624),big,WHITE);p.fields['bigCard']=ref(card.rt)
    viewport,art=p.art('CollectionBigRoot','CollectionBigRegions',(16,68,310,460),card)
    viewport.enable_hit()
    p.fields['CollectionZoom']=ref(viewport.component('BlockOutPinchZoom',{'Target':ref(art.rt),'MinScale':1,'MaxScale':3}))
    p.button('CollectionBigCloseBtn','返回',(16,548,310,48),card);p.save()

def make_popups():
    for name,view,title in [('PausePopup','Pause','暂停'),('FailPopup','Fail','再试一次'),('ConfirmPopup','Confirm','请确认'),('SettingsPage','Settings','设置'),('AboutPopup','About','关于'),('GuidePopup','Guide','玩法说明'),('SettlementPage','Settlement','关卡完成')]:
        p=Page('BlockOut'+name,'BlockOut'+view+'View',popup=True)
        full=view in ('Settings','Settlement');box=(24,36,342,772) if full else (24,200,342,444)
        card=p.node('Card',box,color=CREAM)
        p.label('Heading',title,(16,24,310,36),card,26)
        if view=='Pause':
            for key,text,y in [('PauseResumeBtn','继续游戏',104),('PauseRestartBtn','重开本关',176),('PauseSettingsBtn','设置',248),('PauseQuitBtn','返回首页',320)]:p.button(key,text,(24,y,294,52),card)
        elif view=='Fail':
            p.label('FailReasonText','生命耗尽',(24,78,294,32),card)
            _,cid,tid=p.button('FailReviveBtn','复活',(24,142,294,56),card);p.fields['FailReviveLabel']=ref(tid)
            p.label('FailReviveNote','恢复后继续当前关卡',(24,206,294,26),card,12)
            p.label('FailExhaustedNote','本局暂不可复活，请重试',(24,126,294,80),card,14)
            badge=p.node('FreeBadge',(244,126,64,24),card,MINT);p.fields['FailFreeBadge']=ref(badge.go);Node(p,'Text',badge,(0,0,64,24)).text('免费',12)
            p.button('FailRestartBtn','重开本关',(24,260,294,52),card);p.button('FailQuitBtn','返回首页',(24,332,294,52),card,color=WHITE)
        elif view=='Confirm':
            p.label('ConfirmTitle','请确认',(24,72,294,36),card,20);p.label('ConfirmBody','确认继续操作？',(24,128,294,124),card,16)
            p.button('ConfirmCancelBtn','取消',(24,310,140,52),card,color=WHITE);p.button('ConfirmOkBtn','确认',(178,310,140,52),card)
        elif view=='Settings':
            p.button('SettingsCloseBtn','返回',(24,680,294,52),card,color=WHITE)
            for key,title,y in [('SettingsMusicSwitch','背景音乐',124),('SettingsSoundSwitch','游戏音效',208),('SettingsVibSwitch','振动反馈',292)]:
                n=p.node(key,(24,y,294,64),card,WHITE);p.fields[key]=ref(n.button());Node(p,'Label',n,(16,12,174,40)).text(title,18,INK,3)
                track=Node(p,'Track',n,(0,0,44,24));track.anchor_min=track.anchor_max=vec(1,.5);track.pivot=vec(1,.5);track.position=vec(-8,0);track.img(MINT)
                knob=Node(p,'Knob',n,(0,0,20,20));knob.anchor_min=knob.anchor_max=vec(1,.5);knob.pivot=vec(1,.5);knob.position=vec(-10,0);knob.img(WHITE)
            p.button('SettingsAboutBtn','关于',(24,440,294,52),card,color=WHITE)
        elif view=='About':
            p.label('Description','BlockOut\n箭头方块消除',(24,104,294,120),card,20);p.button('AboutCloseBtn','返回',(24,318,294,52),card)
        elif view=='Guide':
            p.fields['GuideLayer']=ref(p.root.go);p.label('GuideBodyText','轻点方块，沿箭头方向飞出。\n清空棋盘即可过关。\n受阻方块会标红并扣除生命。',(24,104,294,140),card,18);p.button('GuideDismissBtn','开始挑战',(24,318,294,52),card)
        else:
            p.label('SettleTitleText','关卡完成',(16,68,310,36),card,24);p.label('SettlePieceText','获得新拼片',(16,108,310,30),card)
            viewport,_=p.art('SettleRevealRoot','SettleRevealRegions',(16,154,310,280),card)
            p.image('SettleLevelImage',(16,154,310,280),card,WHITE,None,True)
            p.label('SettleNoteText','作品已收集',(16,448,310,42),card,14);p.label('SettleRewardText','奖励金币',(16,496,310,28),card)
            p.button('SettleNextBtn','下一关',(16,542,310,52),card);p.button('SettleReplayBtn','重玩',(16,612,148,48),card,color=WHITE)
            p.button('SettleCollectionBtn','查看收藏',(178,612,148,48),card,color=WHITE);p.button('SettleHomeBtn','返回首页',(16,684,310,48),card,color=WHITE)
        p.save()

if __name__=='__main__':
    make_pages(*make_items());make_popups()
    import runpy
    runpy.run_path(str(Path(__file__).with_name('bind_authored_feedback.py')))
    runpy.run_path(str(Path(__file__).with_name('align_artout_layout.py')))
    print('Authored 12 complete pages/popups and 5 item prefabs. Unity was not launched.')

# Keep delivered layouts free of removed chapter artwork.
if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).with_name('remove_chapter_art_layout.py')))
