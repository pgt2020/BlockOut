using System.Collections.Generic;
using System.Text;
using BlockOut.Contracts;
using BlockOut.Infrastructure.Ads;
using BlockOut.Infrastructure.Analytics;
using BlockOut.Infrastructure.Configuration;
using UnityEditor;
using UnityEngine;

namespace BlockOut.Editor
{
    /// <summary>
    /// LevelPlay 配置与统计模块矩阵检查（R14/R15）。菜单：BlockOut/广告与统计/检查配置。
    /// 只读检查，不写入任何凭据；不输出完整敏感值（只报"缺失/已配置"）。
    /// </summary>
    public static class BlockOutAdConfigValidator
    {
        private const string AdConfigPath = "Assets/BlockOut/Settings/BlockOutAdConfig.asset";

        [MenuItem("BlockOut/广告与统计/检查配置")]
        public static void Check()
        {
            var sb = new StringBuilder();
            sb.AppendLine("=== LevelPlay 配置 ===");
            var cfg = AssetDatabase.LoadAssetAtPath<BlockOutAdConfig>(AdConfigPath);
            if (cfg == null)
            {
                sb.AppendLine("未找到 " + AdConfigPath);
            }
            else
            {
                var missing = cfg.DescribeMissing(out var missKey, out var missPlacement, out var missSdk);
                sb.AppendLine("adsEnabled      : " + cfg.adsEnabled);
                sb.AppendLine("App Key         : " + (missKey ? "缺失" : "已配置"));
                sb.AppendLine("Rewarded Placement : " + (missPlacement ? "缺失" : "已配置"));
                sb.AppendLine("SDK 导入        : " + (missSdk ? "未导入" : "已导入"));
                sb.AppendLine("测试模式        : " + cfg.levelPlayTestMode);
                sb.AppendLine("汇总            : " + missing);
                if (cfg.adsEnabled && (missKey || missPlacement))
                    sb.AppendLine("→ 结论：正式包会被发布门禁阻止；开发档将使用未就绪实现（不模拟成功）。");
            }

            sb.AppendLine();
            sb.AppendLine("=== 统计/归因模块矩阵 ===");
            foreach (var m in BlockOutAnalyticsModuleMatrix.Modules)
                sb.AppendLine("  " + m.Name.PadRight(34) + " " + m.Status + "  |  " + m.Note);
            var gaps = BlockOutAnalyticsModuleMatrix.CollectGaps();
            if (gaps.Count > 0)
            {
                sb.AppendLine();
                sb.AppendLine("待补缺口：");
                foreach (var g in gaps) sb.AppendLine("  - " + g);
            }

            Debug.Log(sb.ToString());
            EditorUtility.DisplayDialog("BlockOut 广告与统计", sb.ToString(), "知道了");
        }

        [MenuItem("BlockOut/广告与统计/生成配置资产（若缺失）")]
        public static void CreateIfMissing()
        {
            if (AssetDatabase.LoadAssetAtPath<BlockOutAdConfig>(AdConfigPath) != null)
            {
                Debug.Log("[BlockOut] 广告配置已存在：" + AdConfigPath);
                return;
            }
            var asset = BlockOutAdConfig.CreateDefault();
            AssetDatabase.CreateAsset(asset, AdConfigPath);
            AssetDatabase.SaveAssets();
            Debug.Log("[BlockOut] 已创建空配置（凭据留空，不编造）：" + AdConfigPath);
        }

        /// <summary>运行期自检：确认适配器在缺凭据时不会假装就绪（供测试与发布检查共用）。</summary>
        public static bool AdapterDegradesSafely(string appKey, string placement, bool testMode)
        {
            var adapter = new LevelPlayAdAdapter(appKey, placement, testMode);
            adapter.Init();
            if (adapter.IsReady(AdType.Rewarded)) return false;
            bool failed = false;
            adapter.ShowRewarded("revive", BlockOut.Contracts.AdShowCallbacks.Create(onShowFailed: () => failed = true));
            return failed;
        }
    }
}
