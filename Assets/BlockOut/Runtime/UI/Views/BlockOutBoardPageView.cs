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
        public ToolSlotRefs HintSlot = new ToolSlotRefs();
        public ToolSlotRefs HammerSlot = new ToolSlotRefs();
        public ToolSlotRefs MagicSlot = new ToolSlotRefs();
    }
}
