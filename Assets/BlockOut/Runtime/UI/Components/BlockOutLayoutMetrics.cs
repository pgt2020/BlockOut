using UnityEngine;

namespace BlockOut.UI
{
    /// <summary>
    /// 画布布局度量：读取 Screen.safeArea，换算为画布单位（pt），
    /// 按 Docs/DesignSystem.md 断点（390×844 基准 / 360×640 小屏 / ≥390×932 长屏）输出组件尺寸。
    /// 挂在 Canvas 根物体上，分辨率或安全区变化时触发 Changed 事件。
    /// </summary>
    public sealed class BlockOutLayoutMetrics : MonoBehaviour
    {
        public static BlockOutLayoutMetrics Instance { get; private set; }

        public float CanvasWidth { get; private set; } = 390f;
        public float CanvasHeight { get; private set; } = 844f;
        public float SafeLeft { get; private set; } = 24f;
        public float SafeRight { get; private set; } = 24f;
        public float SafeTop { get; private set; } = 24f;
        public float SafeBottom { get; private set; } = 16f;
        public bool IsSmallScreen { get; private set; }
        public bool IsLongScreen { get; private set; }

        public event System.Action Changed;

        private RectTransform canvasRect;
        private float lastW = -1f, lastH = -1f;
        private int lastSW = -1, lastSH = -1;
        private Rect lastSafe;

#if UNITY_EDITOR
        public void SetAuthoringSize()
        {
            CanvasWidth=390; CanvasHeight=844;
            SafeLeft=24; SafeRight=24; SafeTop=24; SafeBottom=16;
            IsSmallScreen=false; IsLongScreen=false; enabled=false;
        }
#endif
        public void Attach(RectTransform canvas)
        {
            canvasRect = canvas;
            Instance = this;
            Recompute(true);
        }

        void Update()
        {
            Recompute(false);
        }

        private void Recompute(bool force)
        {
            if (canvasRect == null) return;
            float w = canvasRect.rect.width;
            float h = canvasRect.rect.height;
            var safe = Screen.safeArea;
            bool dirty = force
                || !Mathf.Approximately(w, lastW) || !Mathf.Approximately(h, lastH)
                || Screen.width != lastSW || Screen.height != lastSH
                || safe != lastSafe;
            if (!dirty) return;

            lastW = w; lastH = h; lastSW = Screen.width; lastSH = Screen.height; lastSafe = safe;
            CanvasWidth = w;
            CanvasHeight = h;

            // ScreenSpaceOverlay：画布单位 ↔ 像素 的换算按宽度比例
            float unitsPerPixel = w / Mathf.Max(1, Screen.width);
            SafeLeft = Mathf.Max(24f, safe.xMin * unitsPerPixel);
            SafeRight = Mathf.Max(24f, (Screen.width - safe.xMax) * unitsPerPixel);
            SafeTop = Mathf.Max(24f, (Screen.height - safe.yMax) * unitsPerPixel);
            SafeBottom = Mathf.Max(16f, safe.yMin * unitsPerPixel);

            // 小屏判定必须用**画布单位（设计坐标）**，不能用 Screen.width 物理像素（P1-7）：
            // 1080×2340 手机物理宽是 1080，但对应 390 设计宽，属常规屏而非 360 小屏；
            // 反之 360×640 设备在 CanvasScaler(match=0.5) 下画布单位宽会被反向放大到约 430。
            // 统一以画布单位高判定：360×640 档画布高 ≈ 640-700，常规 390×844 档 ≈ 844。
            IsSmallScreen = CanvasHeight <= 700f;    // 画布单位高 ≤700 → 命中 360×640 设计档
            IsLongScreen = h > 900f;    // ≥390×932 长屏
            Changed?.Invoke();
        }

        public float ContentWidth => Mathf.Max(0f, CanvasWidth - SafeLeft - SafeRight);

        /// <summary>底部导航高：小屏 64→56 是唯一允许压缩的底部组件。</summary>
        public float NavHeight => IsSmallScreen ? 56f : 64f;

        /// <summary>工具条高：三道具全锁时 72，解锁任意道具后 104（v6 §4）。不随屏宽缩放。</summary>
        public float ToolbarHeight => 104f;
        public float ToolbarHeightCompact => 72f;
        public float ToolbarHeightFor(bool hasUnlockedTool) => hasUnlockedTool ? 104f : 72f;

        /// <summary>CTA 高 88 不压缩（Docs/DesignSystem.md）。</summary>
        public float CtaHeight => 88f;

        /// <summary>预览卡高：按"扣掉安全区 + 顶栏 + CTA（含次级按钮）+ 进度卡 + 底部导航"后的**剩余高度**计算（P1-7）。
        /// 参数由调用方（Relayout）传入已确定的各段高度，避免本类反查布局造成循环依赖。
        /// 短屏常规上限210，常规屏上限300；极矮可用区允许进一步缩小以保留操作区。</summary>
        public float ComputePreviewCardHeight(float topBarH, float ctaBlockH, float progressH)
        {
            float gaps = IsSmallScreen ? 32f : 82f;
            float remain = CanvasHeight - SafeTop - SafeBottom - NavHeight - topBarH - ctaBlockH - progressH - gaps;
            // 极矮屏/额外CTA优先保住按钮与导航，插画允许进一步缩小。
            return Mathf.Clamp(remain, 120f, IsSmallScreen ? 210f : 300f);
        }

        /// <summary>游戏页棋盘边长 = 屏宽 − 36（Docs/DesignSystem.md 书面规则；04 视觉稿为 372，差异见交付说明）。</summary>
        public float BoardSideByWidth => Mathf.Max(120f, CanvasWidth - 36f);
    }
}
