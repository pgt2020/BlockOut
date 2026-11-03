using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
namespace BlockOut.Gameplay
{
    public sealed class BlockOutCompletionPresentation : MonoBehaviour
    {
        private readonly Dictionary<Vector2Int,RectTransform> dots=new Dictionary<Vector2Int,RectTransform>();
        private GameObject dotRoot,pictureRoot;
        private BlockOutBoardView board;
        public void BuildDots(BlockOutBoardView owner)
        {
            Clear();board=owner;
            dotRoot=new GameObject("BoardDotGrid",typeof(RectTransform));dotRoot.transform.SetParent(board.GetZoomRoot(),false);dotRoot.transform.SetSiblingIndex(1);
            foreach(var block in board.rules.Blocks)foreach(var cell in block.GetOccupiedCells())
            {
                if(dots.ContainsKey(cell))continue;
                var go=new GameObject("Dot_"+cell.x+"_"+cell.y,typeof(RectTransform),typeof(Image));go.transform.SetParent(dotRoot.transform,false);
                var rt=(RectTransform)go.transform;rt.anchoredPosition=board.CellPos(cell.x,cell.y);rt.sizeDelta=Vector2.one*board.cellSize*.28f;
                var image=go.GetComponent<Image>();image.sprite=BlockOut.UI.BlockOutIconFactory.Asset("circle");image.color=new Color(.56f,.65f,.76f,.58f);image.raycastTarget=false;
                dots.Add(cell,rt);
            }
        }
        public IEnumerator Play(Texture2D texture)
        {
            if(board==null || texture==null)yield break;
            int token=board.runToken;var zoom=board.GetZoomRoot();float startScale=zoom.localScale.x;Vector2 startPosition=zoom.anchoredPosition;
            float height=((RectTransform)board.transform).rect.height;
            float fullHeight=board.unitScale*10f;
            float endScale=Mathf.Min(startScale,fullHeight/(3*Mathf.Max(board.boardWidth*board.cellSize,board.boardHeight*board.CellHeight)));
            float elapsed=0;
            while(elapsed<.08f) { if(token!=board.runToken)yield break;if(!board.IsPaused)elapsed+=Time.deltaTime;yield return null; }
            elapsed=0;
            while(elapsed<.8f)
            {
                if(token!=board.runToken)yield break;
                if(!board.IsPaused)
                {
                    elapsed+=Time.deltaTime;float t=Mathf.Clamp01(elapsed/.8f);t=1-(1-t)*(1-t);
                    // Camera interpolation is in orthographic size, so interpolate inverse scale.
                    float scale=1/Mathf.Lerp(1/startScale,1/endScale,t);
                    zoom.localScale=Vector3.one*scale;
                    zoom.anchoredPosition=Vector2.Lerp(startPosition/startScale,new Vector2(0,3*board.CellHeight),t)*scale;
                }
                yield return null;
            }
            pictureRoot=new GameObject("CompletePicture",typeof(RectTransform));pictureRoot.transform.SetParent(board.EffectSurfaceParent!=null ? board.EffectSurfaceParent : board.transform,false);
            var picture=(RectTransform)pictureRoot.transform;float maxSize=930f/2436f*fullHeight;
            Vector2 size=texture.width>=texture.height ? new Vector2(maxSize,maxSize*texture.height/texture.width) : new Vector2(maxSize*texture.width/texture.height,maxSize);
            picture.anchorMin=picture.anchorMax=picture.pivot=Vector2.one*.5f;
            picture.sizeDelta=size;picture.anchoredPosition=new Vector2(2,220)*(fullHeight/2436f);
            int w=board.boardWidth,h=board.boardHeight,corner=Random.Range(0,4);
            var pixels=new List<RawImage>();var delays=new List<float>();
            for(int y=0;y<h;y++)for(int x=0;x<w;x++)
            {
                var go=new GameObject("Pixel_"+x+"_"+y,typeof(RectTransform),typeof(RawImage));go.transform.SetParent(picture,false);
                var rt=(RectTransform)go.transform;rt.anchoredPosition=new Vector2((x+.5f)/w*size.x-size.x*.5f,(y+.5f)/h*size.y-size.y*.5f);rt.sizeDelta=new Vector2(size.x/w+.05f,size.y/h+.05f);
                var raw=go.GetComponent<RawImage>();raw.texture=texture;raw.uvRect=new Rect((float)x/w,(float)y/h,1f/w,1f/h);raw.raycastTarget=false;raw.color=new Color(1,1,1,0);pixels.Add(raw);
                int dx=(corner==2 || corner==3) ? x-w:x,dy=(corner==1 || corner==3) ? y-h:y;
                int radius=1;while(dx*dx+dy*dy>(corner==3 ? (radius+1)*(radius+1):radius*radius+2*radius))radius++;
                delays.Add((radius-1)*.05f);
            }
            float duration=Mathf.Ceil(Mathf.Sqrt(w*w+h*h))*.05f+.2f;elapsed=0;
            while(elapsed<duration)
            {
                if(token!=board.runToken)yield break;
                if(!board.IsPaused)
                {
                    elapsed+=Time.deltaTime;
                    for(int i=0;i<pixels.Count;i++)
                    {
                        float t=Mathf.Clamp01((elapsed-delays[i])/.2f);pixels[i].color=new Color(1,1,1,t);
                        if(dots.TryGetValue(new Vector2Int(i%w,i/w),out var dot) && dot!=null)dot.localScale=Vector3.one*(1-t);
                    }
                }
                yield return null;
            }
            var player=picture.gameObject.AddComponent<BlockOutAnimationPlayer>();var animation=player.Play("CompletePulse",()=>board.IsPaused);
            while(animation.MoveNext()) { if(token!=board.runToken)yield break;picture.localScale=Vector3.one*player.VisualScale;yield return animation.Current; }
            picture.localScale=Vector3.one;
        }
        public void HidePicture() { if(pictureRoot!=null)pictureRoot.SetActive(false); }
        public void Clear()
        {
            if(dotRoot!=null) { dotRoot.SetActive(false);Destroy(dotRoot); }if(pictureRoot!=null) { pictureRoot.SetActive(false);Destroy(pictureRoot); }dots.Clear();
        }
        private void OnDestroy() { Clear(); }
    }
}
