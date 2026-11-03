using System;
using System.Collections.Generic;
using System.IO;
using BlockOut.Core;
using BlockOut.UI;
using UnityEditor;
using UnityEngine;

namespace BlockOut.Editor
{
    /// <summary>
    /// Prefab 生成 / 校验工具（R11）。菜单：BlockOut/Prefab/生成页面骨架、BlockOut/Prefab/校验。
    ///
    /// 与离线生成器 <c>Tools/gen_blockout_assets.py</c> 的关系：
    /// - 离线脚本负责产出**已提交的 Prefab 资产**（YAML，稳定可复查）；
    /// - 本工具负责在 Unity 内**重建同一结构**（改结构时使用）与**校验既有 Prefab**；
    /// - 两者结构一致：根节点 + BlockOutPageView + 命名子容器（TopBar/Body/BoardArea/…）。
    /// 生成只创建空容器层级，**不生成任何游戏内容**——页面内容由既有工厂在运行时填充，
    /// 因此不存在"Prefab 与旧工厂同时生成同一页"的问题。
    /// </summary>
    public static class BlockOutPrefabGenerator
    {
        private const string UiRoot = "Assets/BlockOut/Resources/Prefabs/UI";
        private const string AppRootDir = "Assets/BlockOut/Resources/Prefabs/App";
        private const string BoardRootDir = "Assets/BlockOut/Resources/Prefabs/Board";

        [MenuItem("BlockOut/Prefab/生成页面骨架")]
        public static void GenerateSkeletons()
        {
            Debug.LogError("[BlockOut] 页面骨架生成已停用，避免覆盖完整 UI。现有 Prefab 可直接编辑；仅需重新生成时使用“烘焙完整页面与弹窗”。");
        }

        [MenuItem("BlockOut/Prefab/校验")]
        public static void Validate()
        {
            var problems = new List<string>();
            foreach (var guid in AssetDatabase.FindAssets("t:Prefab", new[] { "Assets/BlockOut/Resources/Prefabs" }))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                var go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (go == null) { problems.Add(path + "：无法加载"); continue; }
                var view = go.GetComponent<BlockOutPageView>();
                if (view == null)
                {
                    // 完整 Prefab（带 View 控件绑定）没有 PageView/锚点名，属正常，跳过锚点校验
                    var full=go.GetComponent<BlockOutUIViewBase>();
                    string error;
                    if(full!=null && !full.ValidateReferences(out error)) problems.Add(path+": "+error);
                    else if(full==null && go.GetComponent<BlockOut.Bootstrap.BlockOutAppRoot>()==null)
                        problems.Add(path+"：缺少页面 View 或 AppRoot");
                    continue;
                }
                var so = new SerializedObject(view);
                var anchors = so.FindProperty("anchorNames");
                if (anchors == null || anchors.arraySize == 0) continue;
                for (int i = 0; i < anchors.arraySize; i++)
                {
                    var name = anchors.GetArrayElementAtIndex(i).stringValue;
                    if (string.IsNullOrEmpty(name)) continue;
                    if (go.transform.Find(name) == null) problems.Add(path + "：锚点缺失 → " + name);
                }
            }
            foreach (var p in problems) Debug.LogError("[BlockOut][Prefab] " + p);
            if (problems.Count == 0) Debug.Log("[BlockOut][Prefab] 校验通过。");
        }

        // ---- 构建辅助 ----

        private sealed class ChildSpec
        {
            public string Name;
            public Vector2 Amin = Vector2.zero;
            public Vector2 Amax = Vector2.one;
            public Vector2 Pos = Vector2.zero;
            public Vector2 Size = Vector2.zero;
        }

        private static ChildSpec Child(string name, Vector2 amin = default(Vector2), Vector2 amax = default(Vector2),
            Vector2 pos = default(Vector2), Vector2 size = default(Vector2))
        {
            return new ChildSpec
            {
                Name = name,
                Amin = amin == default(Vector2) ? Vector2.zero : amin,
                Amax = amax == default(Vector2) ? Vector2.one : amax,
                Pos = pos,
                Size = size,
            };
        }

        private static GameObject CreatePage(string name, BlockOutScreenId screen, params ChildSpec[] children)
        {
            var go = new GameObject(name, typeof(RectTransform));
            var view = go.AddComponent<BlockOutPageView>();
            var anchorNames = new string[children.Length];
            for (int i = 0; i < children.Length; i++)
            {
                var c = children[i];
                anchorNames[i] = c.Name;
                var child = new GameObject(c.Name, typeof(RectTransform));
                child.transform.SetParent(go.transform, false);
                var rt = (RectTransform)child.transform;
                rt.anchorMin = c.Amin;
                rt.anchorMax = c.Amax;
                rt.anchoredPosition = c.Pos;
                rt.sizeDelta = c.Size;
            }
            var so = new SerializedObject(view);
            so.FindProperty("screenId").enumValueIndex = (int)screen;
            var prop = so.FindProperty("anchorNames");
            for (int i = 0; i < anchorNames.Length; i++)
            {
                prop.arraySize = anchorNames.Length;
                prop.GetArrayElementAtIndex(i).stringValue = anchorNames[i];
            }
            so.ApplyModifiedPropertiesWithoutUndo();
            return go;
        }

        private static int Save(GameObject go, string path)
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            var existing = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (existing != null)
            {
                PrefabUtility.SaveAsPrefabAssetAndConnect(go, path, InteractionMode.AutomatedAction);
                UnityEngine.Object.DestroyImmediate(go);
                return 0;
            }
            PrefabUtility.SaveAsPrefabAsset(go, path);
            UnityEngine.Object.DestroyImmediate(go);
            return 1;
        }
    }
}
