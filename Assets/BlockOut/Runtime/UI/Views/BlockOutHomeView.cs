using System;
using System.Reflection;
using UnityEngine;

namespace BlockOut.UI
{
    public sealed class BlockOutHomeView : BlockOutUIViewBase
    {
        // R2 首页：整屏背景是美术底，以下都是真控件（无透明点击热区）。
        public UnityEngine.UI.Button HomeCtaButton;
        public UnityEngine.UI.Text HomeCtaTitle;
        public UnityEngine.UI.Text HomeCtaSub;
        public UnityEngine.UI.Text HomeLevelTitle;
        public UnityEngine.UI.Button HomeCoinsButton;
        public UnityEngine.UI.Text HomeCoinText;
        public UnityEngine.UI.Button HomeSettingsBtn;
        public UnityEngine.UI.Button HomeGalleryBtn;
        public UnityEngine.UI.Button HomeSkinBtn;
        public UnityEngine.UI.Button HomeDailyBtn;
        public UnityEngine.UI.Button HomeAchievementBtn;
    }
}
