"""Deterministic, editor-independent UI asset authoring. Does not launch or refresh Unity.

Run from any directory with Python, PyYAML and Pillow. Existing prefab GUIDs are kept.
The editor baker is an alternative authoring path; do not rebake after hand-editing layouts.
"""
from pathlib import Path
import re, sys, uuid, yaml
from PIL import Image, ImageDraw

class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self,data): return True

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'Assets/BlockOut/Resources/Prefabs/UI'
RUNTIME = ROOT / 'Assets/BlockOut/Runtime/UI'
ART = ROOT / 'Assets/BlockOut/Resources/ArtOutPresentation/Sprites'
PACKAGE = next((ROOT / 'Library/PackageCache').glob('com.unity.ugui@*'))
# 命令行传入页面名时只落盘该页，避免覆盖其它已定稿页面（其余页仍然计算引用，不写文件）。
ONLY = sys.argv[1] if len(sys.argv) > 1 else None
WHITE = (1, 1, 1, 1)
CREAM = (1, .963, .925, 1)
INK = (.32, .22, .18, 1)
CORAL = (.97, .43, .37, 1)
MINT = (.66, .86, .76, 1)
MUTED = (.88, .85, .80, 1)

# ---- R2 参考（软胶厚卡）用到的 Token 同值色，与 BlockOutDesignTokens 保持一致 ----
SURFACE_RAISED = (1.0, .992, .973, 1)      # #FFFDF8
BG_CREAM_DEEP = (.988, .922, .847, 1)      # #FCEBD8
STROKE_WARM = (.906, .824, .745, 1)        # #E7D2BE
TEXT_COCOA = (.231, .165, .141, 1)         # #3B2A24
TEXT_COCOA60 = (.431, .329, .286, 1)       # #6E5449
TEXT_DISABLED = (.541, .459, .408, 1)      # #8A7568
MINT_FLY = (.118, .561, .408, 1)           # #1E8F68
GOLD_COIN = (.910, .635, .047, 1)          # #E8A20C
GOLD_TEXT = (.420, .278, 0, 1)             # #6B4700
BERRY_RED = (.776, .184, .271, 1)          # #C62F45
LOCK_BADGE = (.431, .329, .286, 1)         # #6E5449
SHADOW_TINT = (.40, .27, .13, .34)

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
        if ONLY and self.name!=ONLY:
            # 只生成单页时：仍返回正确的资源引用（其它页面会引用本页 prefab），但不落盘。
            return ext(path,vid)
        text='%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n'
        for kind,cid,label,data in docs+self.docs:text+='--- !u!'+str(kind)+' &'+str(cid)+'\n'+yaml.dump({label:data},Dumper=NoAliasDumper,allow_unicode=True,sort_keys=False,width=120)
        path.write_text(text,encoding='utf-8');guid(path)
        return ext(path,vid)

def vertical(n):
    n.component('VerticalLayoutGroup',{'m_Padding':{'m_Left':0,'m_Right':0,'m_Top':0,'m_Bottom':0},'m_ChildAlignment':0,'m_Spacing':12,'m_ChildForceExpandWidth':1,'m_ChildForceExpandHeight':0,'m_ChildControlWidth':1,'m_ChildControlHeight':1,'m_ChildScaleWidth':0,'m_ChildScaleHeight':0,'m_ReverseArrangement':0})
    n.component('ContentSizeFitter',{'m_HorizontalFit':0,'m_VerticalFit':2})
def height(n,h):n.component('LayoutElement',{'m_IgnoreLayout':0,'m_MinWidth':-1,'m_MinHeight':h,'m_PreferredWidth':-1,'m_PreferredHeight':h,'m_FlexibleWidth':-1,'m_FlexibleHeight':0,'m_LayoutPriority':1})

# ============================================================
# R2 参考：软胶厚卡的作者侧构件
# 单层 Image 无法同时表达「白描边 + 彩色面」（Image.color 会把两者乘成同色），
# 故与 BlockOutWidgets.SoftCard 保持同一套分层：Shadow → Stroke → Fill →（可选点阵）。
# ============================================================
def spr(name):return ext(ART/(name+'.png'),21300000)
SP_ROUND=spr('round');SP_CIRCLE=spr('circle');SP_SHADOW=spr('card_soft_shadow');SP_DOTS=spr('tray_dots')
SP_ICON={n:spr(n) for n in ('heart','bulb','hammer','wand','pause','lock')}

ANCH={'tl':((0,1),(0,1)),'tc':((.5,1),(.5,1)),'tr':((1,1),(1,1)),
      'ml':((0,.5),(0,.5)),'mc':((.5,.5),(.5,.5)),'mr':((1,.5),(1,.5)),
      'bl':((0,0),(0,0)),'bc':((.5,0),(.5,0)),'br':((1,0),(1,0)),
      'st':((0,0),(1,1))}
def place(node,preset,x,y,w,h):
    """preset 语义与 BlockOutWidgets.UIAnchorPreset 一致：Top* 的 y 向下为正，Bottom* 与 Middle* 的 y 向上为正。"""
    a,pv=ANCH[preset]
    node.anchor_min=vec(*a);node.anchor_max=vec(*a);node.pivot=vec(*pv)
    node.position=vec(-x if preset in ('tr','mr','br') else x,
                      -y if preset in ('tl','tc','tr') else y)
    node.size=vec(w,h)
    return node

def _patch(node,cid,**kv):
    for doc in node.p.docs:
        if doc[1]==cid:
            for k,v in kv.items():doc[3][k]=v
            return

def image_node(p,parent,name,box=None,off=None,color=WHITE,sp=None,ty=0,raycast=0,preserve=0,preset=None):
    """box 走左上角定位；off=(l,b,r,t) 走拉伸锚点；preset 指定锚点后 box=(x,y,w,h)。"""
    node=p.node(name,box if box else (0,0,0,0),parent)
    if off is not None:
        node.anchor_min=vec(0,0);node.anchor_max=vec(1,1);node.pivot=vec(.5,.5)
        node.position=vec((off[0]+off[2])*.5,(off[1]+off[3])*.5)
        node.size=vec(off[2]-off[0],off[3]-off[1])
    elif preset:
        place(node,preset,*box)
    cid=node.img(color,sp)
    node.image=cid                      # Node.__init__ 不回写，不回写会让 button() 再叠一层不透明 Image
    _patch(node,cid,m_Type=ty,m_RaycastTarget=raycast,m_PreserveAspect=preserve)
    return node,cid

def soft_card(p,parent,name,box=None,off=None,fill=CREAM,stroke=WHITE,sw=3,pad=9,hit=True,dots=False,preset=None):
    root,_=image_node(p,parent,name,box,off,(0,0,0,0),None,0,1 if hit else 0,preset=preset)
    image_node(p,root,'Shadow',None,(-pad,-pad-2,pad,pad),SHADOW_TINT,SP_SHADOW,1,0)
    image_node(p,root,'Stroke',None,(0,0,0,0),stroke,SP_ROUND,1,0)
    image_node(p,root,'Fill',None,(sw,sw,-sw,-sw),fill,SP_ROUND,1,0)
    if dots:image_node(p,root,'Dots',None,(14,14,-14,-14),WHITE,SP_DOTS,2,0)
    return root

def text_node(p,field,name,text,box,parent,size=16,color=INK,align=4,preset=None):
    """field 写进 View 序列化字段，节点名可与字段名不同（运行时 Relayout 按节点名查找）。"""
    node=p.node(name,box,parent)
    if preset:place(node,preset,*box)
    cid=node.text(text,size,color,align)
    p.fields[field]=ref(cid);return node,cid

def stretch_node(p,parent,name,off=(0,0,0,0)):
    node=p.node(name,(0,0,0,0),parent)
    node.anchor_min=vec(0,0);node.anchor_max=vec(1,1);node.pivot=vec(.5,.5)
    node.position=vec((off[0]+off[2])*.5,(off[1]+off[3])*.5)
    node.size=vec(off[2]-off[0],off[3]-off[1])
    return node

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
    # ============================================================
    # 对局页（R2 参考）。层级自下而上：棋盘托盘 → 棋盘挂点 → HUD → 提示 → 底部道具
    # 坐标 = 390×844 设计基线，box=(x, y 自上而下, w, h)，与 BlockOutWidgets.Place 的 Top* 预设同义。
    # 运行时 Relayout 按节点名重排，故节点名必须与 BuildBoardScreen 一致（不是字段名）。
    # ============================================================
    p=Page('BlockOutGameHud','BlockOutBoardPageView')

    # ---- 棋盘挂点：Board 屏的直接子节点，名字必须是 BoardArea，轴心保持 0.5/0.5 ----
    area=p.node('BoardArea',(36,147,318,404))
    area.anchor_min=area.anchor_max=vec(.5,.5);area.pivot=vec(.5,.5)
    area.position=vec(0,73);area.size=vec(318,404)          # 中心 (195,349)
    p.fields['BoardArea']=ref(area.rt)

    # ---- 棋盘奶油托盘：作为 BoardArea 的子节点，而不是兄弟节点 ----
    # BlockOutAppBuilder 运行时会把 BoardArea SetAsFirstSibling；若托盘是兄弟节点，
    # 走到首位后托盘会压在棋盘之上把方块盖住。挂在棋盘下则一起下沉，方块自然在其上。
    # 拉伸外扩 (-12,-13,12,13) → 342×430，与设计稿托盘一致。
    tray=soft_card(p,area,'BoardTray',off=(-12,-13,12,13),fill=SURFACE_RAISED,stroke=WHITE,
                   sw=3,pad=9,hit=False,dots=True)
    p.fields['BoardTray']=ref(tray.rt)

    # ---- 顶部 HUD：全屏透明面板，不拦截棋盘手势 ----
    hud=stretch_node(p,p.surface,'TopHUD')
    hid=hud.img((0,0,0,0),None);_patch(hud,hid,m_Type=0,m_RaycastTarget=0)

    text_node(p,'BoardLevelTitle','LevelTitle','第 1 关',(0,46,240,26),hud,20,TEXT_COCOA,4,preset='tc')
    text_node(p,'BoardLevelSub','LevelSub','甜点星球',(0,72,240,14),hud,12,TEXT_COCOA60,4,preset='tc')

    # 暂停：右上 40×40 白圆 + 咖色图标
    pause,_=image_node(p,hud,'PauseBtn',(24,46,40,40),None,WHITE,SP_CIRCLE,0,1,preset='tr')
    p.fields['BoardPauseBtn']=ref(pause.button())
    image_node(p,pause,'Icon',None,(11,11,-11,-11),TEXT_COCOA,SP_ICON['pause'],0,0,1)

    # 心（左）/ 推进条（中）/ 百分比（右）同一行
    lives=place(p.node('LivesRow',(0,0,56,16),hud),'tl',24,88,56,16);hearts=[]
    for i in range(3):
        _,cid=image_node(p,lives,'Heart_'+str(i),(i*18,0,16,16),None,WHITE,SP_ICON['heart'],0,0,1)
        hearts.append(ref(cid))
    p.fields['BoardHearts']=hearts

    # 计时胶囊（倒计时模式专用，与心互斥 → 默认隐藏）
    timer,_=image_node(p,hud,'TimerPill',(24,85,64,22),None,BG_CREAM_DEEP,SP_ROUND,1,0,preset='tl')
    timer.active=False;p.fields['BoardTimerPill']=ref(timer.rt)
    text_node(p,'BoardTimerText','TimerText','01:23',(0,0,64,22),timer,12,GOLD_TEXT,4)

    # 本关推进条：真实数据（已飞块数 / 本关总块数），填充层由 SetProgressBar 改锚点宽度
    track,_=image_node(p,hud,'ProgressBar',(0,88,196,13),None,BG_CREAM_DEEP,SP_ROUND,1,0,preset='tc')
    _,bar_cid=image_node(p,track,'Bar',None,(3,3,-3,-3),MINT_FLY,SP_ROUND,1,0)
    image_node(p,track,'Gloss',None,(4,5.98,-4,-2.5),(1,1,1,.30),SP_ROUND,1,0)
    p.fields['BoardProgressFill']=ref(bar_cid)   # ProgressBar 返回的是 Bar 而非根节点
    text_node(p,'BoardProgressText','ProgressText','0%',(318,87,44,15),hud,12,TEXT_COCOA60,3,preset='tl')

    # 剩余块数：托盘右下角内侧（真实数据）
    rem=place(p.node('RemainingText',(0,0,140,16)),'tr',42,546,140,16)
    p.fields['BoardRemainingText']=ref(rem.text('剩余 0 块',13,TEXT_DISABLED,5))

    # 操作提示 pill（棋盘与道具之间）
    # 托盘底 564 与道具条顶 748 之间共 184 的空档，提示条在中间居中（上下各 78），
    # 贴棋盘会留下 176 的空洞，贴着道具又像道具的标题，居中读作呼吸留白。
    hint,_=image_node(p,p.surface,'HintPill',(0,642,288,28),None,WHITE,SP_ROUND,1,0,preset='tc')
    image_node(p,hint,'Bulb',(12,5,18,18),None,WHITE,SP_ICON['bulb'],0,0,1)
    hint_text=stretch_node(p,hint,'HintText',(36,0,-10,0))
    p.fields['BoardHintPill']=ref(hint_text.text('轻点整块方块，沿箭头方向飞出',12,TEXT_COCOA,3))

    # ---- 底部道具容器：一整条奶油容器 + 三张独立内卡（94×66，中心距 106.3） ----
    # 容器吸底（BottomCenter, y=12）；内卡用容器内的左上角坐标，容器内左右各留 6.2 内边距。
    toolbar=soft_card(p,p.surface,'BottomToolbar',(0,12,319,84),fill=BG_CREAM_DEEP,stroke=WHITE,
                      sw=3,pad=8,hit=True,preset='bc')
    for i,(key,icon,title,cond) in enumerate([('HintSlot','bulb','提示','轮换高亮可飞块'),
                                              ('HammerSlot','hammer','锤子','消除任意在场块'),
                                              ('MagicSlot','wand','炸弹','飞走最多 3 块')]):
        card=soft_card(p,toolbar,key,(6.2+i*106.3,6,94,72),fill=SURFACE_RAISED,stroke=WHITE,sw=2,pad=5,hit=True)
        slot={'Rect':ref(card.rt),'Button':ref(card.button())}
        _,icon_cid=image_node(p,card,'Icon',(31,8,32,32),None,WHITE,SP_ICON[icon],0,0,1);slot['Icon']=ref(icon_cid)
        # 数量徽标（正常态）
        badge,_=image_node(p,card,'CountBadge',(70,5,18,18),None,BERRY_RED,SP_CIRCLE,0,0)
        slot['CountBadge']=ref(badge.go)
        slot['CountText']=ref(badge.text('0',10,WHITE,4))
        # 锁徽章（未解锁态，默认隐藏）
        lock,_=image_node(p,card,'LockBadge',(70,5,18,18),None,LOCK_BADGE,SP_CIRCLE,0,0)
        lock.active=False;slot['LockBadge']=ref(lock.go)
        image_node(p,lock,'Lock',None,(5,5,-5,-5),WHITE,SP_ICON['lock'],0,0,1)
        # 卡高 72：图标 8..40 / 名称 43..56 / 条件 57..67（卡底留 5px，别贴边）
        name_node=p.node('Name',(2,43,90,13),card)
        slot['NameText']=ref(name_node.text(title,12,TEXT_COCOA,4))
        cond_node=p.node('Cond',(1,57,92,10),card)
        slot['CondText']=ref(cond_node.text(cond,10,TEXT_DISABLED,4))
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
    import runpy
    make_pages(*make_items());make_popups()
    # 反馈组件是幂等补齐（已挂过的节点跳过），单页模式下仍需跑，否则新按钮没有按压反馈。
    runpy.run_path(str(Path(__file__).with_name('bind_authored_feedback.py')))
    if not ONLY:
        # 版面对齐脚本是「整体覆盖式」的，单页模式下不跑，避免回灌旧版式。
        runpy.run_path(str(Path(__file__).with_name('align_artout_layout.py')))
        runpy.run_path(str(Path(__file__).with_name('remove_chapter_art_layout.py')))
        print('Authored 12 complete pages/popups and 5 item prefabs. Unity was not launched.')
