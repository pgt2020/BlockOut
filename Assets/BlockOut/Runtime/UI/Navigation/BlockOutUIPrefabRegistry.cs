using System;
using System.Collections.Generic;
using BlockOut.Core;
using UnityEngine;

namespace BlockOut.UI
{
    /// <summary>
    /// UI Prefab 注册表（UI-05）：页面与弹窗 Prefab 统一放 Assets/BlockOut/Resources/Prefabs/UI/，
    /// 命名约定 页面=BlockOut{ScreenId}Page / 弹窗=BlockOut{Name}Popup（结算/设置复用既有 Page 资产保 GUID）。
    /// <para>
    /// “完整 Prefab”判定：资产根上带有 <see cref="BlockOutUIViewBase"/> 派生组件（由烘焙器写入）。
    /// 旧骨架只有 <see cref="BlockOutPageView"/>，不算完整；运行时报告缺失并中止界面初始化。
    /// </para>
    /// </summary>
    public static class BlockOutUIPrefabRegistry
    {
        private const string PrefabRoot = "Prefabs/UI/";
        private static readonly Dictionary<BlockOutScreenId, GameObject> cache =
            new Dictionary<BlockOutScreenId, GameObject>();
        private static readonly Dictionary<string, GameObject> layerCache =
            new Dictionary<string, GameObject>();

        /// <summary>屏幕 → Prefab 资源名（不含目录与扩展名）。</summary>
        public static string ResourceName(BlockOutScreenId screen)
        {
            switch (screen)
            {
                case BlockOutScreenId.Loading: return PrefabRoot + "BlockOutLoadingPage";
                case BlockOutScreenId.Home: return PrefabRoot + "BlockOutHomePage";
                case BlockOutScreenId.Board: return PrefabRoot + "BlockOutGameHud";
                case BlockOutScreenId.Collection: return PrefabRoot + "BlockOutCollectionPage";
                case BlockOutScreenId.Store: return PrefabRoot + "BlockOutStorePage";
                default: return null;
            }
        }

        /// <summary>弹窗层名 → Prefab 资源名。结算/设置复用既有资产（保留 GUID）。</summary>
        public static string LayerResourceName(string layer)
        {
            switch (layer)
            {
                case "PauseLayer": return PrefabRoot + "BlockOutPausePopup";
                case "FailLayer": return PrefabRoot + "BlockOutFailPopup";
                case "ConfirmLayer": return PrefabRoot + "BlockOutConfirmPopup";
                case "SettlementLayer": return PrefabRoot + "BlockOutSettlementPage";   // 复用既有资产
                case "SettingsLayer": return PrefabRoot + "BlockOutSettingsPage";       // 复用既有资产
                case "AboutLayer": return PrefabRoot + "BlockOutAboutPopup";
                case "GuideLayer": return PrefabRoot + "BlockOutGuidePopup";
                default: return null;
            }
        }

        public static GameObject Load(BlockOutScreenId screen)
        {
            if (cache.TryGetValue(screen, out var hit)) return hit;
            var name = ResourceName(screen);
            if (name == null) return null;
            var prefab = Resources.Load<GameObject>(name);
            if (prefab != null) cache[screen] = prefab;
            return prefab;
        }

        public static GameObject LoadLayer(string layer)
        {
            if (layerCache.TryGetValue(layer, out var hit)) return hit;
            var name = LayerResourceName(layer);
            if (name == null) return null;
            var prefab = Resources.Load<GameObject>(name);
            if (prefab != null) layerCache[layer] = prefab;
            return prefab;
        }

        public static bool Has(BlockOutScreenId screen) { return Load(screen) != null; }
        public static bool HasLayer(string layer) { return LoadLayer(layer) != null; }

        /// <summary>是否为“完整 Prefab”（带 View 组件，由烘焙器产出）。旧骨架返回 false。</summary>
        public static bool IsFullPrefab(GameObject prefab)
        {
            return prefab != null && prefab.GetComponent<BlockOutUIViewBase>() != null;
        }

        /// <summary>U08：屏幕对应的期望 View 类型（用于校验 Prefab 挂的 View 类型是否正确，而非任意 View）。</summary>
        public static Type ViewTypeForScreen(BlockOutScreenId screen)
        {
            switch (screen)
            {
                case BlockOutScreenId.Loading: return typeof(BlockOutLoadingView);
                case BlockOutScreenId.Home: return typeof(BlockOutHomeView);
                case BlockOutScreenId.Board: return typeof(BlockOutBoardPageView);
                case BlockOutScreenId.Collection: return typeof(BlockOutCollectionView);
                case BlockOutScreenId.Store: return typeof(BlockOutStoreView);
                default: return null;
            }
        }

        /// <summary>U08：弹窗层对应的期望 View 类型。</summary>
        public static Type ViewTypeForLayer(string layer)
        {
            switch (layer)
            {
                case "PauseLayer": return typeof(BlockOutPauseView);
                case "FailLayer": return typeof(BlockOutFailView);
                case "ConfirmLayer": return typeof(BlockOutConfirmView);
                case "SettlementLayer": return typeof(BlockOutSettlementView);
                case "SettingsLayer": return typeof(BlockOutSettingsView);
                case "AboutLayer": return typeof(BlockOutAboutView);
                case "GuideLayer": return typeof(BlockOutGuideView);
                default: return null;
            }
        }

        /// <summary>U08：Prefab 是否“存在且挂了正确类型的 View”。</summary>
        public static bool HasCorrectView(GameObject prefab, Type expectedView)
        {
            return prefab != null && expectedView != null && prefab.GetComponent(expectedView) != null;
        }

        /// <summary>UI-05：资源缺失时输出含路径的明确错误（调用方据此中止初始化）。</summary>
        public static void ReportMissing(string resourceName)
        {
            Debug.LogError("[BlockOut][UI] 缺少 UI Prefab 资源：Assets/BlockOut/Resources/" + resourceName +
                           ".prefab —— 请运行菜单 BlockOut/Prefab/烘焙完整页面与弹窗 生成后再验证。");
        }

        /// <summary>已交付完整 Prefab 的屏幕清单（检查工具用）。</summary>
        public static IEnumerable<BlockOutScreenId> DeliveredScreens()
        {
            yield return BlockOutScreenId.Loading;
            yield return BlockOutScreenId.Home;
            yield return BlockOutScreenId.Board;
            yield return BlockOutScreenId.Collection;
            yield return BlockOutScreenId.Store;
        }

        /// <summary>清空缓存（编辑器烘焙后调用，保证加载到最新资产）。</summary>
        public static void ClearCache()
        {
            cache.Clear();
            layerCache.Clear();
        }
    }
}
