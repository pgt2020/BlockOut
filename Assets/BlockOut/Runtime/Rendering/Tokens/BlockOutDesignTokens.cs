using UnityEngine;

namespace BlockOut.UI
{
    /// <summary>
    /// BlockOut UI Design System v6 色彩 / 字号 Token。
    /// 唯一真源：BlockOut/Docs/DesignSystem.md（§1 色彩、§2 字体）。
    /// 旧 Docs/DesignSystem.md / Docs/DesignSystem.md / 旧 DesignSystem.md 已删除，禁止再引用。
    ///
    /// v6 修订要点：
    ///  - 语义色专色专用：红色只表示危险/损失，主行动改巧克力棕；
    ///    CtaCoral* 三个旧字段名保留以兼容既有调用，语义已变为 action.primary，请勿按字面理解。
    ///  - 方块色整体降明度、箭头改深填充 + 白描边，保证路径推理可读。
    ///  - 任何玩家可见文字 >= 11px，关键操作 >= 12px（旧 8/9/10px 全部淘汰）。
    /// </summary>
    public static class BlockOutDesignTokens
    {
        // ---- 背景与表面 (§1.1) ----
        public static readonly Color BgCream = Hex("#FFF8F0");
        public static readonly Color BgCreamDeep = Hex("#FCEBD8");
        public static readonly Color SurfaceCard = Hex("#FFFFFF");
        public static readonly Color SurfaceRaised = Hex("#FFFDF8");
        public static readonly Color StrokeWarm = Hex("#E7D2BE");
        public static readonly Color StrokeGrid = Hex("#DCC3AC");
        public static readonly Color StrokeBoard = Hex("#D9BFA6");

        // ---- 文字 (§1.2) ----
        public static readonly Color TextCocoa = Hex("#3B2A24");       // 13.6:1
        public static readonly Color TextCocoa60 = Hex("#6E5449");     // 6.6:1（旧名保留，语义为 secondary）
        public static readonly Color TextDisabled = Hex("#8A7568");    // 4.6:1
        public static readonly Color White = Color.white;

        // ---- 主行动 (§1.3) ----
        public static readonly Color ActionPrimary = Hex("#4A2F26");
        public static readonly Color ActionHover = Hex("#5C3B30");
        // 兼容别名：旧调用点仍写 CtaCoral*，值已改为巧克力棕，语义 = action.primary。
        public static readonly Color CtaCoralTop = Hex("#5C3B30");
        public static readonly Color CtaCoralBottom = Hex("#4A2F26");
        public static readonly Color CtaCoral = Hex("#4A2F26");

        // ---- 状态 (§1.3 / §1.5) ----
        public static readonly Color MintFly = Hex("#1E8F68");         // 可飞 / 成功 / 已解锁
        public static readonly Color HintFlash = Hex("#2FB98A");       // 提示闪烁（比 state.go 亮一档）
        public static readonly Color MintDeep = Hex("#14664A");
        public static readonly Color MintBg = Hex("#DFF6EC");
        public static readonly Color MintText = Hex("#14664A");
        public static readonly Color BerryRed = Hex("#C62F45");        // 危险 / 失败 / 生命
        public static readonly Color BadBg = Hex("#FCE8EA");
        public static readonly Color GoldCoin = Hex("#E8A20C");
        public static readonly Color GoldRim = Hex("#B87C05");
        public static readonly Color GoldLight = Hex("#FFF0C2");
        public static readonly Color GoldText = Hex("#6B4700");
        public static readonly Color Silhouette = Hex("#DCC7B0");
        public static readonly Color GrayLocked = Hex("#8A7568");
        public static readonly Color GrayIconLocked = Hex("#A08B7B");
        public static readonly Color LockBadge = Hex("#6E5449");
        public static readonly Color MistWarm = Hex("#FFFDF8");
        public static readonly Color MaskWarm = Hex("#3B2A24");
        public static readonly Color ArrowFill = Hex("#3B2A24");

        /// <summary>方块外描边（§1.4）：可可 55%，替代旧 3px 纯白轮廓。</summary>
        public static readonly Color StrokeBlock = WithAlpha(TextCocoa, 0.55f);

        // ---- 方块体色 (§1.4)：竖向渐变 顶→底，降明度以拉开奶油底 ----
        public static readonly Color[] JellyTop =
        {
            Hex("#F6B36A"), Hex("#67C9A2"), Hex("#A992E0"),
            Hex("#F39BB4"), Hex("#F2CE63"), Hex("#8FB8EE"),
        };
        public static readonly Color[] JellyBottom =
        {
            Hex("#E08A3C"), Hex("#2E9E75"), Hex("#7C63C4"),
            Hex("#DC6A8C"), Hex("#D9A622"), Hex("#4A82CF"),
        };

        public static Color Hex(string h)
        {
            ColorUtility.TryParseHtmlString(h, out var c);
            return c;
        }

        public static Color WithAlpha(Color c, float a) { c.a = a; return c; }

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

        // ---- 字号 (§2)：玩家可见 >= 11px，关键操作 >= 12px ----
        public const int FontHudLevel = 20;
        public const int FontHudSub = 12;
        public const int FontRemaining = 13;
        public const int FontToolName = 12;
        public const int FontToolCond = 11;
        public const int FontCtaTitle = 18;
        public const int FontCtaSub = 12;
        public const int FontHintPill = 12;
        public const int FontNodeCount = 11;
        public const int FontHomeLogo = 16;
        public const int FontHomeLogoSub = 11;
        public const int FontCoin = 13;
        public const int FontCardTitle = 13;
        public const int FontCardSub = 11;
        public const int FontNav = 12;
        public const int FontPopupTitle = 17;
        public const int FontPopupBody = 12;
        public const int FontButton = 12;
        public const int FontToast = 12;
    }
}
