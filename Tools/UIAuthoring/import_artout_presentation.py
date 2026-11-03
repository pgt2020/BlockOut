from pathlib import Path
import re,shutil,json,uuid,yaml
from PIL import Image,ImageDraw,ImageFilter
R=Path(r'E:/UnityProject/MutiplayGame/BlockOut'); REF=Path(r'E:/UnityProject/ArrowOutBlockGallery/ArtOutBlockGallery/Assets'); D=R/'Assets/BlockOut/Resources/ArtOutPresentation'
def meta(p):
 m=Path(str(p)+'.meta')
 if not m.exists():m.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\n',encoding='utf-8')
 return re.search(r'guid: (\w+)',m.read_text(encoding='utf-8-sig'))[1]
def png(name,im,border=0):
 p=D/'Sprites'/f'{name}.png';p.parent.mkdir(parents=True,exist_ok=True);im.save(p);g=meta(p)
 m={'fileFormatVersion':2,'guid':g,'TextureImporter':{'internalIDToNameTable':[],'externalObjects':{},'serializedVersion':12,'mipmaps':{'enableMipMap':0},'isReadable':0,'textureType':8,'textureShape':1,'sRGBTexture':1,'alphaIsTransparency':1,'spriteMode':1,'spritePixelsToUnits':100,'spriteMeshType':1,'spriteAlignment':0,'spritePivot':{'x':.5,'y':.5},'spriteBorder':dict.fromkeys(['x','y','z','w'],border),'textureSettings':{'serializedVersion':2,'filterMode':1,'aniso':1,'mipBias':0,'wrapU':1,'wrapV':1,'wrapW':1},'maxTextureSize':2048,'nPOTScale':0,'spriteSheet':{'serializedVersion':2,'sprites':[],'outline':[],'physicsShape':[],'bones':[],'spriteID':uuid.uuid5(uuid.NAMESPACE_URL,'blockout-art:'+name).hex,'internalID':0,'vertices':[],'indices':'','edges':[],'weights':[],'secondaryTextures':[],'nameFileIdTable':{}},'platformSettings':[]}}
 Path(str(p)+'.meta').write_text(yaml.safe_dump(m,sort_keys=False),encoding='utf-8')
 return g
# Keep dependency GUIDs, copying only the closure needed by the two effects and a real trail.
index={}
for p in REF.rglob('*.meta'):
 m=re.search(r'^guid: (\w+)',p.read_text(encoding='utf-8-sig',errors='ignore'),re.M)
 if m:index[m[1]]=Path(str(p)[:-5])
local={}
for p in (R/'Assets').rglob('*.meta'):
 m=re.search(r'^guid: (\w+)',p.read_text(encoding='utf-8-sig',errors='ignore'),re.M)
 if m:local[m[1]]=Path(str(p)[:-5])
seeds=[REF/'Bundles/Main/Prefabs/Effect/ArtOut/ruanfan/daoju/prefab'/n for n in ['HammerAni_Ani.prefab','star.prefab']]
seeds += [REF/'Bundles/Main/Prefabs/Obj/Trail_yellow.prefab']
queue=seeds[:];seen=set();copied=[]
while queue:
 p=queue.pop()
 if p in seen or not p.is_file():continue
 seen.add(p);g=meta(p)
 dst=D/'Reference'/p.relative_to(REF)
 if g not in local:
  dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst);shutil.copy2(str(p)+'.meta',str(dst)+'.meta');local[g]=dst;copied.append(str(p.relative_to(REF)))
 elif local[g]!=dst: print('reuse',p.name,local[g])
 if p.suffix.lower() in ['.prefab','.mat','.anim','.controller','.asset','.shader','.shadergraph','.fbx']:
  for dep in set(re.findall(r'guid: ([0-9a-f]{32})',p.read_text(encoding='utf-8-sig',errors='ignore'))):
   if dep in index:queue.append(index[dep])
# Author static UI sprites from reference images rather than runtime drawing.
for name,source in {'bulb':'PlayGameUi/tool_hint_icon.png','hammer':'PlayGameUi/tool_hammer_icon.png','wand':'PlayGameUi/img-wand.png','heart':'PlayGameUi/heart.png','heart_disabled':'PlayGameUi/heart_disabled.png','lock':'PlayGameUi/lock_icon.png'}.items():
 with Image.open(REF/'RawImage'/source) as im:png(name,im.convert('RGBA'))
# Extract the reference guide hand atlas region offline; runtime uses a saved sprite.
with Image.open(REF/'Resources/Animation/tu/xinshou_dianji.png') as im:
 png('guide_hand',im.convert('RGBA').crop((343,196,519,338)).transpose(Image.Transpose.ROTATE_270))
# Existing delivered graphics remain editable files.
old=R/'Assets/BlockOut/Resources/Prefabs/UI/AuthoredSprites'
for name in ['round','check']:
 with Image.open(old/(name+'.png')) as im:png(name,im.convert('RGBA'),32 if name=='round' else 0)
# Neutral white state textures are tinted by Image, never rasterized at runtime.
for name in ['ring','selection','circle','board','background','trail']:
 im=Image.new('RGBA',(128,128));d=ImageDraw.Draw(im)
 if name=='ring':d.rounded_rectangle((5,5,122,122),radius=22,outline='white',width=5)
 elif name=='selection':
  for x in range(20,110,18):d.line((x,5,x+9,5),fill='white',width=4);d.line((x,122,x+9,122),fill='white',width=4)
  for y in range(20,110,18):d.line((5,y,5,y+9),fill='white',width=4);d.line((122,y,122,y+9),fill='white',width=4)
 elif name=='circle':d.ellipse((2,2,125,125),fill='white')
 elif name=='board':d.rounded_rectangle((1,1,126,126),radius=14,fill='#FFFAF4',outline='#E8CDBB',width=2)
 elif name=='background':
  d.rectangle((0,0,127,127),fill='#D8ECFF')
 else:
  im=Image.new('RGBA',(64,1));d=ImageDraw.Draw(im)
  for x in range(64):d.point((x,0),fill=(255,255,255,round(255*.9*(x/63)**1.25)))
 png(name,im,24 if name in ['ring','selection','board'] else 0)
# Shape library supports all 30 shapes and rotations; bake silhouettes once, not once per block/frame.
s=(R/'Assets/BlockOut/Runtime/Core/Rules/BlockOutShapeLibrary.cs').read_text(encoding='utf-8-sig'); shapes=[]
for line in s.splitlines():
 if 'new[] { new[]' in line:shapes.append([(int(x),int(y)) for y,x in re.findall(r'new\[\] \{ (\d+), (\d+) \}',line)])
keys=set()
for cells in shapes:
 for rotation in range(4):
  minx=min(x for x,y in cells);miny=min(y for x,y in cells);cells=sorted([(x-minx,y-miny) for x,y in cells],key=lambda v:(v[1],v[0]));key='_'.join(f'{x}-{y}' for x,y in cells)
  if key not in keys:
   keys.add(key);w=max(x for x,y in cells)+1;h=max(y for x,y in cells)+1
   mask=Image.new('L',(w*128,h*128));dr=ImageDraw.Draw(mask)
   for x,y in cells:dr.rectangle((x*128+4,(h-1-y)*128+4,(x+1)*128-5,(h-y)*128-5),fill=255)
   # close internal seams, round the exterior consistently
   for x,y in cells:
    if (x+1,y) in cells:dr.rectangle((x*128+64,(h-1-y)*128+4,(x+1)*128+64,(h-y)*128-5),fill=255)
    if (x,y+1) in cells:dr.rectangle((x*128+4,(h-2-y)*128+64,(x+1)*128-5,(h-1-y)*128+64),fill=255)
   mask=mask.filter(ImageFilter.GaussianBlur(3)).point(lambda v:255 if v>120 else 0)
   im=Image.new('RGBA',mask.size,'white');im.putalpha(mask);png('Shapes/'+key,im)
  cells=[(y,-x) for x,y in cells]
# All simple UI glyphs as persistent sprites.
for name in ['coin','gear','home','book','bag','pause','star','play','ad','broken','arrow_Right','arrow_Left','arrow_Up','arrow_Down']:
 im=Image.new('RGBA',(128,128));d=ImageDraw.Draw(im)
 if name.startswith('arrow_'):
  d.polygon([(18,48),(73,48),(73,25),(111,64),(73,103),(73,80),(18,80)],fill='white');angle={'Right':0,'Up':90,'Left':180,'Down':270}[name[6:]];im=im.rotate(angle)
 elif name=='star':
  import math
  d.polygon([(64+math.cos(i*math.pi/5-math.pi/2)*(58 if i%2==0 else 25),64+math.sin(i*math.pi/5-math.pi/2)*(58 if i%2==0 else 25)) for i in range(10)],fill='white')
 elif name=='coin':d.ellipse((8,8,120,120),fill='#FFD66B',outline='#C38B20',width=7);d.line((64,32,64,96),fill='#C38B20',width=8)
 elif name=='pause':d.rounded_rectangle((30,18,53,110),8,fill='white');d.rounded_rectangle((75,18,98,110),8,fill='white')
 elif name in ['play','ad']:d.polygon([(35,15),(112,64),(35,113)],fill='white')
 elif name=='home':d.polygon([(10,60),(64,10),(118,60),(102,60),(102,115),(26,115),(26,60)],fill='white')
 elif name=='gear':d.regular_polygon((64,64,57),8,fill='white');d.ellipse((45,45,83,83),fill=(0,0,0,0))
 else:d.rounded_rectangle((15,20,113,111),12,outline='white',width=10);d.line((64,25,64,105),fill='white',width=7)
 png(name,im)
manifest_path=D/'ReferenceImport.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {}
manifest['source']=str(REF)
manifest['assets']=sorted(set(manifest.get('assets',[])+copied))
manifest_path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for p in sorted(D.rglob('*')):
 if p.is_dir():meta(p)
meta(D)
print('Imported reference assets:',len(copied),'shape sprites:',len(keys))
