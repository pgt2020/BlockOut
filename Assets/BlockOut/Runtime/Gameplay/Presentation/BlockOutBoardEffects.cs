using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
namespace BlockOut.Gameplay
{
    /// <summary>Render the original world-space Animator/particle prefabs into the UGUI board.
    /// The isolated camera keeps the authored shaders, animation paths and particle modules intact.</summary>
    public sealed class BlockOutBoardEffects : MonoBehaviour
    {
        private const string Reference="ArtOutPresentation/Reference/Bundles/Main/Prefabs/";
        private sealed class Effect { public GameObject Root; public Transform Follow; public float Remaining; public Vector2 Position; public Vector3 BaseScale; public bool ScaleWithBoard; public GameObject WoodCopy; public float WoodSeconds; public Vector2 Velocity; public Vector2 Direction; public float Acceleration; public float MaximumSpeed; public Animator[] Animators; public ParticleSystem[] Particles; }
        private readonly List<Effect> effects=new List<Effect>();
        private BlockOutBoardView board;
        private Transform stage;
        private Camera effectCamera;
        private RawImage surface;
        private RenderTexture target;
        private bool wasPaused;
        public void Initialize(BlockOutBoardView owner,Transform parent)
        {
            board=owner;
            stage=new GameObject("BlockOutEffectStage").transform;
            stage.position=new Vector3(20000,20000,20000);
            var cameraGo=new GameObject("EffectCamera",typeof(Camera)); cameraGo.transform.SetParent(stage,false);
            cameraGo.transform.localPosition=new Vector3(0,0,-20);
            effectCamera=cameraGo.GetComponent<Camera>(); effectCamera.orthographic=true;
            effectCamera.clearFlags=CameraClearFlags.SolidColor; effectCamera.backgroundColor=Color.clear;
            effectCamera.cullingMask=1<<31; effectCamera.nearClipPlane=.1f; effectCamera.farClipPlane=50;
            effectCamera.allowHDR=false; effectCamera.allowMSAA=false;
            target=new RenderTexture(Mathf.Clamp(Screen.width,256,2048),Mathf.Clamp(Screen.height,256,2048),24,RenderTextureFormat.ARGB32); target.name="BlockOutEffects"; target.Create();
            effectCamera.targetTexture=target;
            var go=new GameObject("AuthoredEffects",typeof(RectTransform),typeof(RawImage));
            go.transform.SetParent(owner.EffectSurfaceParent!=null ? owner.EffectSurfaceParent : parent,false);
            go.transform.SetSiblingIndex(1);
            surface=go.GetComponent<RawImage>(); surface.texture=target; surface.raycastTarget=false;
            surface.material=Resources.Load<Material>("ArtOutPresentation/EffectsComposite");
            var rt=surface.rectTransform; rt.anchorMin=Vector2.zero;rt.anchorMax=Vector2.one;rt.offsetMin=rt.offsetMax=Vector2.zero;
        }
        public GameObject PlayHammer(Vector2 position,Color color,BlockOutBlockNode source)
        {
            var root=Spawn(Reference+"Effect/ArtOut/ruanfan/daoju/prefab/HammerAni_Ani",position,2.1f,5f/12f*.7f);
            foreach(var ps in root.GetComponentsInChildren<ParticleSystem>(true))
                if(ps.name.IndexOf("suipian",StringComparison.OrdinalIgnoreCase)>=0 || ps.name.IndexOf("shard",StringComparison.OrdinalIgnoreCase)>=0)
                { var main=ps.main;main.startColor=color;main.startSizeMultiplier*=.5f;main.startSpeedMultiplier*=.5f; }
            if(source!=null)
            {
                var item=effects[effects.Count-1];
                item.WoodCopy=new GameObject("HammerWoodBlock");item.WoodCopy.transform.SetParent(root.transform,false);item.WoodSeconds=.35f;
                foreach(var img in source.GetComponentsInChildren<Image>(true))
                {
                    if(img.sprite==null || !img.enabled || img.color.a<=0 || (img.name!="Body" && img.name!="Arrow"))continue;
                    var copy=new GameObject(img.name,typeof(SpriteRenderer));copy.layer=31;copy.transform.SetParent(item.WoodCopy.transform,false);
                    var renderer=copy.GetComponent<SpriteRenderer>();renderer.sprite=img.sprite;renderer.color=img.color;renderer.sortingOrder=img.name=="Arrow" ? 3:2;
                    renderer.sharedMaterial=img.name=="Arrow" ? img.material : Resources.Load<Material>("ArtOutPresentation/Reference/Bundles/Shaders/ArtOutToolAlphaTint");
                    Vector3 mapped=Map(board.GetZoomRoot().InverseTransformPoint(img.transform.position));
                    copy.transform.position=stage.TransformPoint(mapped);copy.transform.rotation=img.transform.rotation;
                    Vector3 scale=surface.rectTransform.InverseTransformVector(img.transform.TransformVector(Vector3.right));
                    float w=img.rectTransform.rect.width*scale.magnitude/board.unitScale;
                    float h=img.rectTransform.rect.height*surface.rectTransform.InverseTransformVector(img.transform.TransformVector(Vector3.up)).magnitude/board.unitScale;
                    copy.transform.localScale=new Vector3(w/Mathf.Max(.001f,img.sprite.bounds.size.x)/root.transform.localScale.x,h/Mathf.Max(.001f,img.sprite.bounds.size.y)/root.transform.localScale.y,1);
                }
                foreach(var renderer in root.GetComponentsInChildren<Renderer>(true))if(!renderer.transform.IsChildOf(item.WoodCopy.transform))renderer.sortingOrder=Mathf.Max(4,renderer.sortingOrder);
            }
            return root;
        }
        public GameObject PlayStar(Vector2 position)
        {
            var root=Spawn(Reference+"Effect/ArtOut/ruanfan/daoju/prefab/star",position,3f,5f/12f*board.ReferenceWorldScale/board.unitScale);
            effects[effects.Count-1].ScaleWithBoard=true;return root;
        }

        public void Move(GameObject effect,Vector2 local)
        {
            var item=effects.Find(e=>e.Root==effect);
            if(item!=null)item.Position=local;
            if(effect!=null)effect.transform.localPosition=Map(local);
        }
        private Vector3 Map(Vector2 local)
        {
            var world=board.GetZoomRoot().TransformPoint(local);
            var point=surface.rectTransform.InverseTransformPoint(world);
            return new Vector3(point.x/board.unitScale,point.y/board.unitScale,0);
        }
        public void ClearMagic()
        {
            for(int i=effects.Count-1;i>=0;i--)if(effects[i].Root!=null && effects[i].Root.name.StartsWith("star")) { effects[i].Root.SetActive(false);Destroy(effects[i].Root);effects.RemoveAt(i); }
        }

        public void Release(GameObject effect,float seconds=.55f)
        {
            var item=effects.Find(e=>e.Root==effect);if(item==null)return;
            item.Follow=null;item.Remaining=seconds;
            foreach(var ps in item.Particles) if(ps!=null) ps.Stop(false,ParticleSystemStopBehavior.StopEmitting);
        }
        private GameObject Spawn(string path,Vector2 local,float lifetime,float scale)
        {
            var prefab=Resources.Load<GameObject>(path);
            if(prefab==null) throw new InvalidOperationException("Missing authored effect "+path);
            var go=Instantiate(prefab,stage,false);go.SetActive(true);
            go.transform.localScale*=scale;Move(go,local);
            foreach(var t in go.GetComponentsInChildren<Transform>(true))t.gameObject.layer=31;
            foreach(var renderer in go.GetComponentsInChildren<Renderer>(true))renderer.sortingLayerID=0;
            var item=new Effect { Root=go,Remaining=lifetime,Position=local,BaseScale=go.transform.localScale,Animators=go.GetComponentsInChildren<Animator>(true),Particles=go.GetComponentsInChildren<ParticleSystem>(true) };
            foreach(var a in item.Animators) { a.cullingMode=AnimatorCullingMode.AlwaysAnimate; a.speed=board.IsPaused ? 0:1; }
            foreach(var p in item.Particles) if(p.gameObject.activeInHierarchy) { p.Play(false); if(board.IsPaused)p.Pause(false); }
            effects.Add(item);return go;
        }
        private void LateUpdate()
        {
            if(board==null || effectCamera==null)return;
            var rect=surface.rectTransform.rect;
            effectCamera.orthographicSize=Mathf.Max(.1f,rect.height/(2*board.unitScale));
            effectCamera.aspect=rect.height>0 ? rect.width/rect.height : 1;
            bool paused=board.IsPaused;
            for(int i=effects.Count-1;i>=0;i--)
            {
                var item=effects[i];
                if(item.Root==null) { effects.RemoveAt(i);continue; }
                if(item.Follow!=null)item.Position=((RectTransform)item.Follow).anchoredPosition;
                if(!paused && item.Velocity.sqrMagnitude>0)
                {
                    item.Position+=item.Velocity*Time.deltaTime;
                    item.Velocity=item.Direction*Mathf.Min(item.MaximumSpeed,item.Velocity.magnitude+item.Acceleration*Time.deltaTime);
                }
                item.Root.transform.localPosition=Map(item.Position);
                float scale=surface.rectTransform.InverseTransformVector(board.GetZoomRoot().TransformVector(Vector3.right)).magnitude;
                item.Root.transform.localScale=item.BaseScale*(item.ScaleWithBoard ? scale : 1f);
                if(paused!=wasPaused)
                {
                    foreach(var a in item.Animators) if(a!=null)a.speed=paused ? 0:1;
                    foreach(var ps in item.Particles) if(ps!=null && ps.gameObject.activeInHierarchy)
                    { if(paused)ps.Pause(false);else if(ps.isPaused)ps.Play(false); }
                }
                if(!paused)
                {
                    item.Remaining-=Time.deltaTime;
                    if(item.WoodCopy!=null) { item.WoodSeconds-=Time.deltaTime;if(item.WoodSeconds<=0)item.WoodCopy.SetActive(false); }
                }
                if(item.Remaining<=0) { Destroy(item.Root); effects.RemoveAt(i); }
            }
            wasPaused=paused;
        }
        public void Clear() { foreach(var e in effects) if(e.Root!=null) { e.Root.SetActive(false);Destroy(e.Root); } effects.Clear(); }
        private void OnDisable() { if(stage!=null)stage.gameObject.SetActive(false); }
        private void OnEnable() { if(stage!=null)stage.gameObject.SetActive(true); }
        private void OnDestroy()
        {
            Clear(); if(stage!=null)Destroy(stage.gameObject);
            if(surface!=null)Destroy(surface.gameObject);
            if(target!=null) { target.Release();Destroy(target); }
        }
    }
}
