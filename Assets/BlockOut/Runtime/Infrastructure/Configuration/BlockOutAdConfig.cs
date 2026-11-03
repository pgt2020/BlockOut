using System;
using BlockOut.Contracts;
using UnityEngine;

namespace BlockOut.Infrastructure.Configuration
{
    /// <summary>
    /// LevelPlay（ironSource）广告配置（R14）。
    /// App Key / Rewarded Placement / 测试模式集中在此资产，**不写死在代码里**，
    /// 也不复用参考工程凭据。缺配置时开发版走替身、正式版由发布门禁拦截。
    /// </summary>
    [CreateAssetMenu(menuName = "BlockOut/Ad Config (LevelPlay)", fileName = "BlockOutAdConfig")]
    public sealed class BlockOutAdConfig : ScriptableObject
    {
        [Tooltip("LevelPlay 应用 Key（ironSource App Key）。留空 = 未配置。")]
        public string levelPlayAppKey = "";

        [Tooltip("激励广告位 ID（Rewarded Video Placement）。留空 = 未配置。")]
        public string rewardedPlacementId = "";

        [Tooltip("LevelPlay 测试模式。仅开发/测试包开启。")]
        public bool levelPlayTestMode;

        [Tooltip("本期是否启用广告（激励复活）。关闭时 ReviveWithAd 直接返回未就绪。")]
        public bool adsEnabled;

        [Tooltip("SDK 是否已导入。未导入时适配器保持未就绪，不模拟成功。")]
        public bool sdkImported;

        public bool HasCredentials =>
            !string.IsNullOrEmpty(levelPlayAppKey) && !string.IsNullOrEmpty(rewardedPlacementId);

        /// <summary>供发布门禁与检查工具读取的缺项描述（不输出完整敏感值）。</summary>
        public string DescribeMissing(out bool missingAppKey, out bool missingPlacement, out bool missingSdk)
        {
            missingAppKey = string.IsNullOrEmpty(levelPlayAppKey);
            missingPlacement = string.IsNullOrEmpty(rewardedPlacementId);
            missingSdk = !sdkImported;
            if (!missingAppKey && !missingPlacement && !missingSdk) return "配置完整";
            var parts = new System.Text.StringBuilder();
            if (missingAppKey) parts.Append("App Key;");
            if (missingPlacement) parts.Append("Rewarded Placement;");
            if (missingSdk) parts.Append("SDK 未导入;");
            return parts.ToString().TrimEnd(';');
        }

        public static BlockOutAdConfig CreateDefault()
        {
            var c = CreateInstance<BlockOutAdConfig>();
            c.levelPlayAppKey = "";
            c.rewardedPlacementId = "";
            c.levelPlayTestMode = false;
            c.adsEnabled = false;
            c.sdkImported = false;
            return c;
        }
    }
}
