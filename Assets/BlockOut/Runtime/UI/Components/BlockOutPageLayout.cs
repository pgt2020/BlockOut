using UnityEngine;
namespace BlockOut.UI
{
    /// <summary>Only transforms the page's design surface; never rewrites child layout authored in the prefab.</summary>
    public sealed class BlockOutPageLayout : MonoBehaviour
    {
        public RectTransform Surface;
        public Vector2 DesignSize = new Vector2(390,844);
        public bool RespectSafeArea = true;
        private void OnEnable() { Apply(); }
        private void OnRectTransformDimensionsChange() { Apply(); }
        public void Apply()
        {
            if(Surface==null || DesignSize.x<=0 || DesignSize.y<=0) return;
            var root=transform as RectTransform;
            if(root==null || root.rect.width<=0 || root.rect.height<=0) return;
            var canvas=GetComponentInParent<Canvas>();
            Rect area=root.rect;
            // All top-level pages/popups have a full-canvas wrapper.
            if(RespectSafeArea && canvas!=null && Screen.width>0 && Screen.height>0)
            {
                var safe=Screen.safeArea;
                area=new Rect(root.rect.xMin+safe.xMin/Screen.width*root.rect.width,
                    root.rect.yMin+safe.yMin/Screen.height*root.rect.height,
                    safe.width/Screen.width*root.rect.width,safe.height/Screen.height*root.rect.height);
            }
            float scale=Mathf.Min(area.width/DesignSize.x,area.height/DesignSize.y);
            Surface.anchorMin=Surface.anchorMax=new Vector2(0.5f,0.5f);
            Surface.pivot=new Vector2(0.5f,0.5f);
            Surface.sizeDelta=DesignSize;
            Surface.anchoredPosition=area.center-root.rect.center;
            Surface.localScale=new Vector3(scale,scale,1);
        }
    }
}
