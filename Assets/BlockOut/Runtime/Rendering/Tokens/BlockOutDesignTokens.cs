using UnityEngine;

namespace BlockOut.UI
{
    /// <summary>
    /// design_v5 09_component_spec.md §1 色彩 Token（生产值唯一来源）+ §2 字体层级。
    /// 旧 DesignSystem.md 的 #FFF5EB/#FFAA80/#7ED9A6 已作废，禁止引用。
    /// </summary>
    public static class BlockOutDesignTokens
    {
        public static readonly Color BgCream = Hex("#FFFAF4");
        public static readonly Color BgCreamDeep = Hex("#FFF1E3");
        public static readonly Color SurfaceCard = Hex("#FFFDF8");
        public static readonly Color StrokeWarm = Hex("#F0DCCB");
        public static readonly Color StrokeGrid = Hex("#E9CFC0");
        public static readonly Color StrokeBoard = Hex("#E8CDBB");
        public static readonly Color TextCocoa = Hex("#553B36");
        public static readonly Color TextCocoa60 = Hex("#8A6E62");
        public static readonly Color CtaCoralTop = Hex("#FF8B7E");
        public static readonly Color CtaCoralBottom = Hex("#FF6B5C");
        public static readonly Color CtaCoral = Hex("#FF7568");
        public static readonly Color MintFly = Hex("#62CFA7");
        /// <summary>提示闪烁色（§7.3，参考提示闪烁 #83F851）。</summary>
        public static readonly Color HintFlash = Hex("#83F851");
        public static readonly Color MintDeep = Hex("#3BB98E");
        public static readonly Color MintBg = Hex("#DFF6EC");
        public static readonly Color MintText = Hex("#2E7C5B");
        public static readonly Color BerryRed = Hex("#F45F70");
        public static readonly Color GoldCoin = Hex("#FFC53D");
        public static readonly Color GoldRim = Hex("#E3A22E");
        public static readonly Color GoldLight = Hex("#FFE9B0");
        public static readonly Color GoldText = Hex("#7A4A00");
        public static readonly Color Silhouette = Hex("#EBD9C6");
        public static readonly Color GrayLocked = Hex("#B9A79B");
        public static readonly Color GrayIconLocked = Hex("#C9B8AC");
        public static readonly Color LockBadge = Hex("#8A6E62");
        public static readonly Color MistWarm = Hex("#FFF7EF");
        public static readonly Color MaskWarm = Hex("#674138");
        public static readonly Color White = Color.white;

        // 果冻块体色（竖向渐变 顶→底，09 §1 教学样板色）
        public static readonly Color[] JellyTop =
        {
            Hex("#F8CCA0"), Hex("#A9E8CF"), Hex("#CFC2F2"),
            Hex("#FABCD0"), Hex("#FAE49B"), Hex("#B9D2F7"),
        };
        public static readonly Color[] JellyBottom =
        {
            Hex("#F0AC6E"), Hex("#79D2B2"), Hex("#AC95E2"),
            Hex("#F193AF"), Hex("#F2C957"), Hex("#84B4EB"),
        };

        public static Color Hex(string h)
        {
            ColorUtility.TryParseHtmlString(h, out var c);
            return c;
        }

        /// <summary>
        /// 优先加载随包交付的思源黑体 CN Regular（SIL OFL 1.1，见 Fonts/LICENSE.txt）。
        /// 资源缺失时仅为开发环境回退系统字体与 LegacyRuntime。
        /// </summary>
        public static Font UIFont { get; private set; }

        public static void EnsureFont()
        {
            if (UIFont != null) return;
            UIFont = Resources.Load<Font>("Fonts/SourceHanSansCN-Regular");
            if (UIFont != null) return;
            try
            {
                UIFont = Font.CreateDynamicFontFromOSFont(new[] { "Microsoft YaHei", "PingFang SC" }, 16);
            }
            catch { UIFont = null; }
            if (UIFont == null)
                UIFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        }

        // §2 本项目实际取值（pt）
        public const int FontHudLevel = 18;      // HUD 关卡名 18/700
        public const int FontHudSub = 10;        // 副题 10/400
        public const int FontRemaining = 12;     // 剩余块 12/700
        public const int FontToolName = 10;      // 工具名 10.5/400（Text 仅支持整数，取 10）
        public const int FontToolCond = 9;       // 解锁条件 9/400
        public const int FontCtaTitle = 17;      // CTA 主文案 17/900
        public const int FontCtaSub = 9;         // CTA 副文案 9/400
        public const int FontHintPill = 10;      // 提示 pill 10.5/400
        public const int FontNodeCount = 9;      // 节点计数 9/400
        public const int FontHomeLogo = 15;      // 首页 logo 15/900
        public const int FontHomeLogoSub = 8;    // 首页 logo 副 7.5/400
        public const int FontCoin = 12;          // 金币数 12/900
        public const int FontCardTitle = 11;     // 卡片标题 11/800
        public const int FontCardSub = 9;        // 卡片副文案 9/400
        public const int FontNav = 9;            // 底部导航 9/800
        public const int FontPopupTitle = 15;    // 弹窗主标题 15-17/900
        public const int FontPopupBody = 9;      // 弹窗正文 9/400
        public const int FontButton = 11;        // 次级按钮 11/800
        public const int FontToast = 10;         // Toast 10.5/400
    }
}
