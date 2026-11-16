using System;
using System.Reflection;
using UnityEngine;

namespace BlockOut.UI
{
    public sealed class BlockOutBoardPageView : BlockOutUIViewBase
    {
        public RectTransform BoardArea;
        public UnityEngine.UI.Button BoardPauseBtn;
        public UnityEngine.UI.Text BoardLevelTitle;
        public UnityEngine.UI.Text BoardLevelSub;
        public UnityEngine.UI.Image[] BoardHearts;
        public RectTransform BoardTimerPill;
        public UnityEngine.UI.Text BoardTimerText;
        public UnityEngine.UI.Text BoardRemainingText;
        public UnityEngine.UI.Text BoardHintPill;
        /// <summary>R2 参考新增：本关推进条填充层（真实数据：已飞/总数）。</summary>
        public UnityEngine.UI.Image BoardProgressFill;
        /// <summary>R2 参考新增：推进条百分比文字。</summary>
        public UnityEngine.UI.Text BoardProgressText;
        /// <summary>R2 参考新增：棋盘奶油托盘。</summary>
        public RectTransform BoardTray;
        public ToolSlotRefs HintSlot = new ToolSlotRefs();
        public ToolSlotRefs HammerSlot = new ToolSlotRefs();
        public ToolSlotRefs MagicSlot = new ToolSlotRefs();
    }
}
