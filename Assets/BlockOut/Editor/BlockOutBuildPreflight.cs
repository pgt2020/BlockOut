using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using BlockOut.Infrastructure.Ads;
using BlockOut.Infrastructure.Configuration;
using UnityEditor;
using UnityEditor.Build;
using UnityEngine;

namespace BlockOut.Editor
{
    /// <summary>
    /// 发布门禁（R16）。在构建前自动执行，失败即阻止出包：
    /// - 正式包不得启用开发替身广告（FakeAdProvider / DevelopmentAdProvider）；
    /// - Release 配置不得开启详细日志与 allowFakeServices；
    /// 广告启用但缺 LevelPlay App Key / Placement 时给出明确错误（缺配置不得静默放行）。
    /// 菜单：BlockOut/发布检查/运行全部检查。
    /// C01：接口实现要求实例方法，静态类不能实现接口——本类改为可实例化类，
    /// 菜单入口保留静态方法（内部 new 实例），构建回调由 Unity 直接调用实例方法。
    /// </summary>
    public sealed class BlockOutBuildPreflight : IPreprocessBuildWithReport
    {
        private const string MenuPath = "BlockOut/发布检查/运行全部检查";
        private const string StrictMenuPath = "BlockOut/发布检查/切换正式门禁(严格)";

        private static bool strictMode;

        [MenuItem(MenuPath)]
        public static void RunAllChecks()
        {
            var report = new BlockOutBuildPreflight().Collect();
            foreach (var line in report.Lines) Debug.Log(line);
            if (report.HasError)
            {
                Debug.LogError("[BlockOut] 发布检查未通过（" + report.Errors.Count + " 项错误）。");
                EditorUtility.DisplayDialog("BlockOut 发布检查", "未通过：\n" + string.Join("\n", report.Errors.Take(12)), "知道了");
            }
            else
            {
                Debug.Log("[BlockOut] 发布检查通过。");
                EditorUtility.DisplayDialog("BlockOut 发布检查", "全部通过。", "好");
            }
        }

        [MenuItem(StrictMenuPath, false)]
        public static void ToggleStrict()
        {
            strictMode = !strictMode;
            Menu.SetChecked(StrictMenuPath, strictMode);
            Debug.Log("[BlockOut] 严格门禁 = " + strictMode);
        }

        public int callbackOrder => -100;

        public void OnPreprocessBuild(UnityEditor.Build.Reporting.BuildReport report)
        {
            var result = Collect();
            foreach (var line in result.Lines) Debug.Log(line);
            if (result.HasError)
                throw new BuildFailedException("[BlockOut] 发布检查未通过，已阻止构建：\n" +
                                               string.Join("\n", result.Errors));
        }

        public sealed class CheckReport
        {
            public readonly List<string> Lines = new List<string>();
            public readonly List<string> Errors = new List<string>();
            public readonly List<string> Warnings = new List<string>();
            public bool HasError => Errors.Count > 0;

            public void Ok(string msg) { Lines.Add("[OK] " + msg); }
            public void Warn(string msg) { Lines.Add("[WARN] " + msg); Warnings.Add(msg); }
            public void Error(string msg) { Lines.Add("[ERROR] " + msg); Errors.Add(msg); }
        }

        public CheckReport Collect()
        {
            var r = new CheckReport();

            // 1) 启动场景唯一且为 Launcher
            var scenes = EditorBuildSettings.scenes.Where(s => s.enabled).ToArray();
            if (scenes.Length == 0) r.Error("Build Settings 没有启用任何场景。");
            else if (scenes.Length > 1) r.Warn("Build Settings 启用了多个场景：首发入口应为唯一 Launcher。");
            var launcher = scenes.FirstOrDefault(s => s.path.EndsWith("Launcher.unity", StringComparison.Ordinal));
            if (launcher == null) r.Error("未找到启动场景 Assets/BlockOut/Scenes/Launcher.unity。");
            else r.Ok("启动场景 = " + launcher.path);

            // 2) 启动配置存在且 Release 不自相矛盾
            var devCfg = AssetDatabase.LoadAssetAtPath<BlockOutStartupConfig>("Assets/BlockOut/Settings/BlockOutStartupConfig_Development.asset");
            var relCfg = AssetDatabase.LoadAssetAtPath<BlockOutStartupConfig>("Assets/BlockOut/Settings/BlockOutStartupConfig_Release.asset");
            if (devCfg == null) r.Error("缺少开发档启动配置 BlockOutStartupConfig_Development.asset。");
            if (relCfg == null) r.Error("缺少发布档启动配置 BlockOutStartupConfig_Release.asset。");
            if (relCfg != null && !relCfg.ValidateRelease(out var cfgErr)) r.Error("Release 配置非法：" + cfgErr);

            // 3) 开发替身不得进入正式包（扫描资产引用）
            bool releaseBuild = relCfg != null && relCfg.environment == BlockOutStartupConfig.Environment.Release;
            var fakeGuids = FindTypeGuids(typeof(FakeAdProvider), typeof(DevelopmentAdProvider));
            if (fakeGuids.Count > 0)
            {
                if (releaseBuild || strictMode)
                    r.Error("工程内仍引用开发替身广告（" + string.Join(", ", fakeGuids) + "），正式包禁止。");
                else
                    r.Warn("工程内引用开发替身广告（仅开发档允许）：" + string.Join(", ", fakeGuids));
            }
            else r.Ok("无开发替身广告引用。");

            // 4) LevelPlay 配置完整性（仅在启用广告时强制）
            var adCfg = AssetDatabase.LoadAssetAtPath<BlockOutAdConfig>("Assets/BlockOut/Settings/BlockOutAdConfig.asset");
            if (adCfg == null) r.Error("缺少 LevelPlay 广告配置 BlockOutAdConfig.asset。");
            else
            {
                var missing = adCfg.DescribeMissing(out var missKey, out var missPlacement, out var missSdk);
                if (adCfg.adsEnabled && (missKey || missPlacement))
                    r.Error("广告已启用但配置不完整：" + missing + "（请在 BlockOutAdConfig.asset 填写，不要写死在代码里）");
                else if (!adCfg.adsEnabled)
                    r.Ok("广告未启用（激励复活将返回未就绪）。");
                else if (missSdk)
                    r.Warn("LevelPlay 配置已填写但 SDK 未导入（sdkImported=false），初始化会保持未就绪。");
                else r.Ok("LevelPlay 配置完整。");
            }

            // 5) 目录 manifest（关键目录必须存在）
            string[] requiredDirs =
            {
                "Assets/BlockOut/Runtime/Bootstrap",
                "Assets/BlockOut/Runtime/Contracts",
                "Assets/BlockOut/Runtime/Core",
                "Assets/BlockOut/Runtime/Gameplay",
                "Assets/BlockOut/Runtime/UI",
                "Assets/BlockOut/Runtime/Infrastructure/Ads",
                "Assets/BlockOut/Runtime/Infrastructure/Persistence",
                "Assets/BlockOut/Editor",
                "Assets/BlockOut/Scenes",
                "Assets/BlockOut/Settings",
            };
            foreach (var d in requiredDirs)
                if (!AssetDatabase.IsValidFolder(d)) r.Error("缺少目标目录：" + d);
            if (!r.HasError) r.Ok("目录 manifest 完整（" + requiredDirs.Length + " 项）。");

            return r;
        }

        /// <summary>在工程内搜索引用指定类型的资产（脚本/场景/Prefab/资产）。</summary>
        private static List<string> FindTypeGuids(params Type[] types)
        {
            var hits = new List<string>();
            var scriptGuids = new HashSet<string>();
            foreach (var t in types)
            {
                var scriptPath = FindScriptPath(t);
                if (scriptPath == null) continue;
                var guid = AssetDatabase.AssetPathToGUID(scriptPath);
                if (!string.IsNullOrEmpty(guid)) scriptGuids.Add(guid);
            }
            if (scriptGuids.Count == 0) return hits;

            var searchRoots = new[] { "Assets/BlockOut", "Assets/Resources" };
            foreach (var root in searchRoots)
            {
                if (!AssetDatabase.IsValidFolder(root)) continue;
                foreach (var path in Directory.EnumerateFiles(root, "*.*", SearchOption.AllDirectories))
                {
                    if (!path.EndsWith(".prefab") && !path.EndsWith(".unity") && !path.EndsWith(".asset")) continue;
                    string text;
                    try { text = File.ReadAllText(path); }
                    catch { continue; }
                    foreach (var g in scriptGuids)
                        if (text.Contains(g, StringComparison.Ordinal)) { hits.Add(Path.GetFileName(path) + " → " + g); break; }
                }
            }
            return hits;
        }

        private static string FindScriptPath(Type t)
        {
            var guids = AssetDatabase.FindAssets(t.Name + " t:Script");
            foreach (var g in guids)
            {
                var p = AssetDatabase.GUIDToAssetPath(g);
                var text = File.ReadAllText(p);
                if (text.Contains("class " + t.Name, StringComparison.Ordinal)) return p;
            }
            return null;
        }
    }
}
