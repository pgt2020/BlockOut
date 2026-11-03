using System.Collections.Generic;
using BlockOut.Core;
using UnityEngine;

namespace BlockOut.UI
{
    /// <summary>
    /// 页面视图组件（R11）：挂在页面 Prefab 根节点上，提供命名锚点解析，
    /// 使控制器/检查工具不必依赖深层名字 Find。页面内容由既有工厂填充，
    /// 视图只做绑定与自描述，不重复生成任何元素。
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class BlockOutPageView : MonoBehaviour
    {
        [SerializeField] private BlockOutScreenId screenId;
        [SerializeField] private string[] anchorNames = new string[0];

        private readonly Dictionary<string, Transform> anchors = new Dictionary<string, Transform>();

        public BlockOutScreenId ScreenId => screenId;

        void Awake()
        {
            ResolveAnchors();
        }

        /// <summary>按名字取子节点锚点（仅在 Prefab 显式登记的名单内查找）。</summary>
        public Transform Anchor(string name)
        {
            if (string.IsNullOrEmpty(name)) return null;
            if (anchors.Count == 0) ResolveAnchors();
            return anchors.TryGetValue(name, out var t) ? t : null;
        }

        public bool HasAnchor(string name) { return Anchor(name) != null; }

        private void ResolveAnchors()
        {
            anchors.Clear();
            if (anchorNames == null) return;
            foreach (var n in anchorNames)
            {
                if (string.IsNullOrEmpty(n)) continue;
                var found = transform.Find(n);
                if (found != null) anchors[n] = found;
            }
        }

        /// <summary>编辑器/检查工具：把直接子节点名登记为锚点（生成 Prefab 时调用）。</summary>
        public void RegisterChildAnchors()
        {
            var names = new List<string>();
            for (int i = 0; i < transform.childCount; i++) names.Add(transform.GetChild(i).name);
            anchorNames = names.ToArray();
            ResolveAnchors();
        }
    }
}
