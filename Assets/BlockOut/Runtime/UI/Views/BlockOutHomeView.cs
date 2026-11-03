using System;
using System.Reflection;
using UnityEngine;

namespace BlockOut.UI
{
    public sealed class BlockOutHomeView : BlockOutUIViewBase
    {
        public UnityEngine.UI.Button HomeCtaButton;
        public UnityEngine.UI.Text HomeCtaTitle;
        public UnityEngine.UI.Text HomeCtaSub;
        public UnityEngine.UI.Button HomeCtaSecondary;
        public UnityEngine.UI.Text HomeCoinText;
        public UnityEngine.UI.Text HomePieceBadge;
        public UnityEngine.UI.Text HomeChapterTitle;
        public UnityEngine.UI.Text HomePieceText;
        public UnityEngine.UI.Image HomeProgressFill;
        public UnityEngine.UI.Image[] HomeNodes;
        public UnityEngine.UI.Button HomeCollectionLink;
        public UnityEngine.UI.Button HomeSettingsBtn;
        public UnityEngine.UI.Image[] HomeRegionArts;
        public GameObject[] HomeRegionLocks;
        public GameObject HomeFailBox;
        public UnityEngine.UI.Button HomeRetryBtn;
        public UnityEngine.UI.Text HomeRetryExhausted;
        public GameObject HomePlaceholderTag;
        public RectTransform HomePreviewCard;
        public RectTransform HomeArtViewport;
        public UnityEngine.UI.Button NavHomeBtn;
        public UnityEngine.UI.Button NavCollectionBtn;
        public UnityEngine.UI.Button NavStoreBtn;
    }
}
