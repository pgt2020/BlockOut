using System;
using System.Reflection;
using UnityEngine;

namespace BlockOut.UI
{
    public sealed class BlockOutFailView : BlockOutUIViewBase
    {
        public UnityEngine.UI.Text FailReasonText;
        public UnityEngine.UI.Text FailReviveLabel;
        public UnityEngine.UI.Text FailReviveNote;
        public UnityEngine.UI.Text FailExhaustedNote;
        public UnityEngine.UI.Button FailReviveBtn;
        public UnityEngine.UI.Button FailRestartBtn;
        public UnityEngine.UI.Button FailQuitBtn;
        public GameObject FailFreeBadge;
    }
}
