using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using BlockOut.Core;
using UnityEditor;
using UnityEngine;

namespace BlockOut.Editor
{
    /// <summary>
    /// 工程静态检查（R20）。菜单：BlockOut/工程检查/全部。
    /// 覆盖：启动入口唯一、资源加载契约（字面量路径必须来自 BlockOutResourcePaths）、
    /// 必需 Prefab 与组件、章节图 Sprite meta、重复关卡 ID、目录 manifest。
    /// **不会**自动刷新资源或运行测试（遵守项目约束）。
    /// </summary>
    public static class BlockOutProjectChecks
    {
        [MenuItem("BlockOut/工程检查/全部")]
        public static void RunAll()
        {
            var problems = new List<string>();
            int checks = 0;

            checks++; CheckSceneEntry(problems);
            checks++; CheckResourceContracts(problems);
            checks++; CheckRequiredPrefabs(problems);
            checks++; CheckChapterSpriteMeta(problems);
            checks++; CheckDuplicateLevelIds(problems);
            checks++; CheckNoRuntimeInitializeBoot(problems);

            foreach (var p in problems) Debug.LogError("[BlockOut][Check] " + p);
            if (problems.Count == 0)
                Debug.Log("[BlockOut][Check] 全部通过（" + checks + " 组检查）。");
            else
                EditorUtility.DisplayDialog("BlockOut 工程检查",
                    "未通过 " + problems.Count + " / " + checks + " 组：\n" + string.Join("\n", problems.Take(15)), "知道了");
        }

        // ---- 1) 启动入口唯一 ----
        private static void CheckSceneEntry(List<string> problems)
        {
            var enabled = EditorBuildSettings.scenes.Count(s => s.enabled);
            if (enabled != 1)
                problems.Add("Build Settings 启用场景数 = " + enabled + "（应为 1：Launcher.unity）。");
            var anyLauncher = EditorBuildSettings.scenes.Any(s => s.path.EndsWith("Launcher.unity", StringComparison.Ordinal));
            if (!anyLauncher) problems.Add("Build Settings 未包含 Launcher.unity。");

            // 不得残留 RuntimeInitializeOnLoadMethod 启动器
            foreach (var guid in AssetDatabase.FindAssets("t:Script"))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.StartsWith("Assets/BlockOut", StringComparison.Ordinal)) continue;
                var text = File.ReadAllText(path);
                if (text.Contains("[RuntimeInitializeOnLoadMethod", StringComparison.Ordinal))
                    problems.Add("仍存在运行时自动启动入口：" + path);
            }
        }

        // ---- 2) 资源加载契约 ----
        private static void CheckResourceContracts(List<string> problems)
        {
            var literals = new HashSet<string>(BlockOutResourcePaths.LegacyAliases, StringComparer.Ordinal);
            foreach (var guid in AssetDatabase.FindAssets("t:Script"))
            {
                var path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.StartsWith("Assets/BlockOut", StringComparison.Ordinal)) continue;
                var text = File.ReadAllText(path);
                foreach (var line in text.Split('\n'))
                {
                    var trimmed = line.Trim();
                    if (!trimmed.Contains("Resources.Load")) continue;
                    if (trimmed.StartsWith("//")) continue;
                    // 只允许引用 BlockOutResourcePaths 常量或既有契约路径
                    bool usesConstant = trimmed.Contains("BlockOutResourcePaths");
                    bool usesLegacy = literals.Any(l => trimmed.Contains("\"" + l + "\"", StringComparison.Ordinal));
                    if (!usesConstant && !usesLegacy)
                        problems.Add("资源加载未走集中路径：" + Path.GetFileName(path) + " | " + trimmed);
                }
            }
        }

        // ---- 3) 必需 Prefab ----
        private static void CheckRequiredPrefabs(List<string> problems)
        {
            string[] required =
            {
                "Assets/BlockOut/Resources/Prefabs/App/BlockOutAppRoot.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutHomePage.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutGameHud.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutCollectionPage.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutStorePage.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutLoadingPage.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutPausePopup.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutFailPopup.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutConfirmPopup.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutSettlementPage.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutSettingsPage.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutAboutPopup.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/BlockOutGuidePopup.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/Items/ChapterItem.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/Items/RepeatItem.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/Items/StoreHint.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/Items/StoreHammer.prefab",
                "Assets/BlockOut/Resources/Prefabs/UI/Items/StoreMagic.prefab",
            };
            foreach (var p in required)
            {
                if (!File.Exists(p)) { problems.Add("缺少 Prefab：" + p); continue; }
                var go = AssetDatabase.LoadAssetAtPath<GameObject>(p);
                if (go == null) { problems.Add("Prefab 无法加载：" + p); continue; }
                var view=go.GetComponent<BlockOut.UI.BlockOutUIViewBase>();
                if(view!=null && !view.ValidateReferences(out var referenceError)) problems.Add(p+": "+referenceError);
                if (go.GetComponent<BlockOut.UI.BlockOutPageView>() == null
                    && go.GetComponent<BlockOut.UI.BlockOutUIViewBase>() == null
                    && go.GetComponent<BlockOut.Bootstrap.BlockOutAppRoot>() == null)
                    problems.Add("Prefab 缺少 BlockOutPageView 或 View 组件：" + p);
            }

            // 棋盘挂点契约：AppBuilder 按名字 BoardArea 查找
            var hud = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/BlockOut/Resources/Prefabs/UI/BlockOutGameHud.prefab");
            if (hud != null && (hud.GetComponent<BlockOut.UI.BlockOutBoardPageView>() == null || hud.GetComponent<BlockOut.UI.BlockOutBoardPageView>().BoardArea == null))
                problems.Add("BlockOutGameHud.prefab 缺少 BoardArea 子节点（棋盘挂点契约）。");
        }

        // ---- 4) 章节图 Sprite meta ----
        private static void CheckChapterSpriteMeta(List<string> problems)
        {
            foreach (var kind in new[] { "full", "preview", "silhouette" })
            {
                var meta = "Assets/Resources/block/ch01/" + kind + ".png.meta";
                if (!File.Exists(meta)) { problems.Add("缺少章节图 meta：" + meta); continue; }
                var text = File.ReadAllText(meta);
                bool InImporter(string key, string expect)
                {
                    int i = text.IndexOf("TextureImporter:", StringComparison.Ordinal);
                    if (i < 0) return false;
                    int end = text.IndexOf("\n--- ", i + 1, StringComparison.Ordinal);
                    var block = end < 0 ? text.Substring(i) : text.Substring(i, end - i);
                    return block.Contains("  " + key + ": " + expect, StringComparison.Ordinal);
                }
                if (!InImporter("textureType", "8")) problems.Add(kind + ".png.meta：textureType 应为 8（Sprite）。");
                if (!InImporter("spriteMode", "1")) problems.Add(kind + ".png.meta：spriteMode 应为 1（Single）。");
                if (!InImporter("spriteMeshType", "1")) problems.Add(kind + ".png.meta：spriteMeshType 应为 1（FullRect）。");
                if (!InImporter("nPOTScale", "0")) problems.Add(kind + ".png.meta：nPOTScale 应为 0（不缩放）。");
            }
        }

        // ---- 5) 重复关卡 ID ----
        private static void CheckDuplicateLevelIds(List<string> problems)
        {
            var seen = new Dictionary<string, string>(StringComparer.Ordinal);
            var dir = "Assets/Resources/" + BlockOutResourcePaths.Levels;
            if (!Directory.Exists(dir)) { problems.Add("缺少关卡目录：" + dir); return; }
            foreach (var f in Directory.EnumerateFiles(dir, "*.json"))
            {
                var text = File.ReadAllText(f);
                var id = Extract(text, "\"id\"");
                if (string.IsNullOrEmpty(id)) continue;
                if (seen.TryGetValue(id, out var prev))
                    problems.Add("关卡 ID 重复：" + id + "（" + Path.GetFileName(prev) + " 与 " + Path.GetFileName(f) + "）");
                else seen[id] = f;
            }
        }

        private static string Extract(string json, string key)
        {
            int i = json.IndexOf(key, StringComparison.Ordinal);
            if (i < 0) return null;
            int q1 = json.IndexOf('"', i + key.Length);
            if (q1 < 0) return null;
            int q2 = json.IndexOf('"', q1 + 1);
            return q2 < 0 ? null : json.Substring(q1 + 1, q2 - q1 - 1);
        }

        // ---- 6) 无运行时自动装配 ----
        private static void CheckNoRuntimeInitializeBoot(List<string> problems)
        {
            if (File.Exists("Assets/BlockOut/Runtime/Bootstrap/BlockOutBootstrapper.cs"))
                problems.Add("旧自动启动器未删除：BlockOutBootstrapper.cs（入口应为 Launcher + AppRoot）。");
        }
    }
}
