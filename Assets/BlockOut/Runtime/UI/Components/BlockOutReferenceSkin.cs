using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace BlockOut.UI
{
    /// <summary>
    /// 参考图 1:1 还原层的运行时驱动器（由 Tools/UIAuthoring/apply_reference_skin.py 生成并挂在根节点）。
    ///
    /// 分层约定：
    ///  · 视觉层置顶，所有元件 Image 的 raycastTarget = 0 —— 不遮挡、不吞点击；
    ///  · 透明热区节点按原图按钮 bbox 摆放（raycastTarget = 1），命名 Hotspot_&lt;bind&gt;，
    ///    点击时转发到业务层同名 Button，业务 View / Controller 一行都不用改；
    ///  · 烧死在切图里的静态数字已在 prepare_reference_skin.py 里擦除，
    ///    由 Dyn_&lt;key&gt; 的 Text 节点镜像业务层真实数值，避免静态值与双影。
    ///
    /// 本组件不持有任何业务引用；找不到目标时静默降级为「视觉层 + 点击穿透」。
    /// </summary>
    public sealed class BlockOutReferenceSkin : MonoBehaviour
    {
        /// <summary>参考图屏号 s1..s9。</summary>
        public string ScreenId;

        /// <summary>s4 为 true：棋盘区域已挖空，运行时真棋盘透出，不生成组件化格子。</summary>
        public bool PassthroughBoard;

        private readonly Dictionary<string, Button> hotspots = new Dictionary<string, Button>();
        private readonly Dictionary<string, Text> labels = new Dictionary<string, Text>();
        private readonly Dictionary<string, string> lastText = new Dictionary<string, string>();
        private Sprite heartOn, heartOff;
        private readonly List<Image> heartCells = new List<Image>();
        private int lastHearts = -1;

        private void Awake()
        {
            foreach (var b in GetComponentsInChildren<Button>(true))
            {
                if (b.name.StartsWith("Hotspot_"))
                    hotspots[b.name.Substring("Hotspot_".Length)] = b;
            }
            foreach (var t in GetComponentsInChildren<Text>(true))
            {
                if (t.name.StartsWith("Dyn_"))
                    labels[t.name.Substring("Dyn_".Length)] = t;
            }
            for (int i = 0; i < 4; i++)
            {
                var tr = transform.Find("DesignSurface/ReferenceSkin/Heart_" + i);
                if (tr != null)
                {
                    var img = tr.GetComponent<Image>();
                    if (img != null) heartCells.Add(img);
                }
            }
        }

        /// <summary>把业务按钮的 onClick 转接到镜像热区；重复调用不会重复注册。</summary>
        public void Bind(string key, Button target)
        {
            if (string.IsNullOrEmpty(key) || target == null) return;
            Button src;
            if (!hotspots.TryGetValue(key, out src) || src == null) return;
            src.onClick.RemoveAllListeners();
            var t = target;
            src.onClick.AddListener(delegate { if (t != null) t.onClick.Invoke(); });
            src.interactable = target.interactable;
        }

        /// <summary>刷新热区的可用态（业务按钮禁用时热区同步置灰，不吃点击）。</summary>
        public void BindInteractable(string key, bool interactable)
        {
            Button src;
            if (string.IsNullOrEmpty(key) || !hotspots.TryGetValue(key, out src) || src == null) return;
            src.interactable = interactable;
        }

        /// <summary>写动态文字；值未变化时跳过，避免每帧重建 Text 网格。</summary>
        public void SetText(string key, string value)
        {
            if (string.IsNullOrEmpty(key)) return;
            Text t;
            if (!labels.TryGetValue(key, out t) || t == null) return;
            string v = value ?? string.Empty;
            string prev;
            if (lastText.TryGetValue(key, out prev) && prev == v) return;
            lastText[key] = v;
            t.text = v;
        }

        /// <summary>按剩余生命数切换实心 / 空心心形；sprite 从 Resources 惰性加载。</summary>
        public void SetHearts(int count)
        {
            if (!PassthroughBoard || heartCells.Count == 0 || count == lastHearts) return;
            lastHearts = count;
            if (heartOn == null) heartOn = Resources.Load<Sprite>("UI/Reference/tiles/heart_on");
            if (heartOff == null) heartOff = Resources.Load<Sprite>("UI/Reference/tiles/heart_off");
            if (heartOn == null || heartOff == null) return;
            for (int i = 0; i < heartCells.Count; i++)
                heartCells[i].sprite = i < count ? heartOn : heartOff;
        }

        /// <summary>按绑定键读取当前镜像文字（供自检 / 调试）。</summary>
        public string GetText(string key)
        {
            Text t;
            return labels.TryGetValue(key, out t) && t != null ? t.text : null;
        }
    }
}
