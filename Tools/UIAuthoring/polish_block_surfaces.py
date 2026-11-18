"""Relight the existing exact silhouettes as continuous pieces, without changing alpha.
Requires numpy, scipy, Pillow, PyYAML. No Unity or image-generation API is used.
"""
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from PIL import Image
import yaml

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'Assets/BlockOut/Resources/ArtOutPresentation/Reference/Bundles/Sprites/BlockSoft'

def relight(image):
    a=np.asarray(image.convert('RGBA')).copy()
    # Pad so even a silhouette touching the image boundary has a real outside.
    mask=np.pad(a[:,:,3]>127,32)
    distance=distance_transform_edt(mask)-distance_transform_edt(~mask)
    smooth=gaussian_filter(distance,2)
    gy,gx=np.gradient(smooth)
    magnitude=np.maximum(np.hypot(gx,gy),.001)
    light=(gy*.86+gx*.36)/magnitude
    bevel=np.exp(-np.maximum(distance,0)/11)
    # One shared light from upper left. No per-cell gradients or internal seams.
    shade=.86+bevel*(.13*np.maximum(light,0)-.22*np.maximum(-light,0))
    shade-=.055*np.exp(-np.maximum(distance,0)/2.5)
    shade=shade[32:-32,32:-32]
    a[:,:,:3]=np.round(np.clip(shade,0,1)*255).astype('uint8')[:,:,None]
    return Image.fromarray(a)

def main():
    for i in range(1,31):
        path=ART/f'{i}.png';before=Image.open(path).convert('RGBA');after=relight(before)
        assert np.array_equal(np.asarray(before)[:,:,3],np.asarray(after)[:,:,3])
        after.save(path)
        meta=Path(str(path)+'.meta');m=yaml.safe_load(meta.read_text(encoding='utf-8'));t=m['TextureImporter']
        t.update(textureCompression=0,crunchedCompression=0,maxTextureSize=2048,nPOTScale=0)
        t['mipmaps']['enableMipMap']=0
        t['platformSettings']=[dict(serializedVersion=3,buildTarget=target,maxTextureSize=2048,
            textureFormat=-1,textureCompression=0,compressionQuality=100,crunchedCompression=0,
            overridden=0,allowsAlphaSplitting=0) for target in ['DefaultTexturePlatform','Standalone','Android','iPhone']]
        meta.write_text(yaml.safe_dump(m,sort_keys=False),encoding='utf-8')
    print('30 continuous block surfaces rebuilt; all alpha masks unchanged. Unity not invoked.')

if __name__=='__main__':main()
