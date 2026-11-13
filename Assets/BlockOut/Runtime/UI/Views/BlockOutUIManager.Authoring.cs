#if UNITY_EDITOR
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;
namespace BlockOut.UI
{
    // Editor-only generation recipe. No fixed-layout construction is compiled into players.
    public sealed partial class BlockOutUIManager
    {
        internal void BuildAuthoring()
        {
            if (canvas != null) return; // idempotent
            BlockOutWidgets.EnsureReady();
            BuildCanvas();
            canvas.renderMode=RenderMode.WorldSpace;
            canvasGo.GetComponent<RectTransform>().sizeDelta=new Vector2(390,844);
            BuildAllScreens();

            var board=ScreenRoot(BlockOutScreenId.Board);
            BuildPauseLayer(board); BuildFailLayer(board); BuildConfirmLayer(board); BuildSettlementLayer(board);
            BuildSettingsLayer(); BuildGuideLayer();
            BuildToast();
            metrics = canvasGo.GetComponent<BlockOutLayoutMetrics>();
            metrics.SetAuthoringSize();
            
            LayoutAuthoring();
            ShowScreen(BlockOutScreenId.Loading);
        }

        private GameObject MakeScreen(string name)
        {
            var go=new GameObject("Screen_"+name,typeof(RectTransform));
            go.transform.SetParent(canvasGo.transform,false);
            BlockOutWidgets.ApplyAnchor((RectTransform)go.transform,UIAnchorPreset.Stretch);
            return go;
        }

        private void BuildAllScreens()
        {
            screens[BlockOutScreenId.Loading] = BuildLoadingScreen();
            screens[BlockOutScreenId.Home] = BuildHomeScreen();
            screens[BlockOutScreenId.Board] = BuildBoardScreen();
            screens[BlockOutScreenId.Collection] = BuildCollectionScreen();
            screens[BlockOutScreenId.Store] = BuildStoreScreen();
            foreach (var kv in screens) kv.Value.SetActive(false);
        }

        private GameObject BuildHomeScreen()
        {
            var go = MakeScreen("Home");

            // ---- 顶部：logo | 金币 | 设置 ----
            var logoTile = BlockOutWidgets.Panel(go.transform, "LogoTile", BlockOutDesignTokens.MintFly,
                UIAnchorPreset.TopLeft, 24, 30, 36, 36);
            logoTile.sprite = BlockOutIconFactory.RoundedSlice(11f, BlockOutDesignTokens.MintFly, Color.clear, 0f, null);
            logoTile.type = Image.Type.Sliced;
            var logoArrow = BlockOutWidgets.SpriteImage(go.transform, "LogoArrow", BlockOutIconFactory.Arrow(Core.BlockOutDirection.Right),
                UIAnchorPreset.TopLeft, 31, 37, 22, 22);
            logoArrow.color = BlockOutDesignTokens.White;
            BlockOutWidgets.Label(go.transform, "LogoTitle", "BlockOut", BlockOutDesignTokens.FontHomeLogo, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 70, 30, 150, 18);
            BlockOutWidgets.Label(go.transform, "LogoSub", "箭头方块消除", BlockOutDesignTokens.FontHomeLogoSub, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 70, 48, 150, 12);

            var coinPill = BlockOutWidgets.Pill(go.transform, "CoinPill", 94, 30, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, UIAnchorPreset.TopRight, -138, 33);
            BlockOutWidgets.SpriteImage(coinPill, "CoinIcon", BlockOutIconFactory.Coin(),
                UIAnchorPreset.MiddleLeft, 9, 0, 18, 18);
            HomeCoinText = BlockOutWidgets.Label(coinPill, "CoinText", "0", BlockOutDesignTokens.FontCoin, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft, UIAnchorPreset.Stretch, 0, 0, 0, 0);
            HomeCoinText.rectTransform.offsetMin = new Vector2(33, 0);
            HomeCoinText.rectTransform.offsetMax = new Vector2(-8, 0);
            HomeSettingsBtn = BlockOutWidgets.CircleIconButton(go.transform, "SettingsBtn", BlockOutIconFactory.Gear(), 36, null,
                BlockOutDesignTokens.SurfaceCard, BlockOutDesignTokens.StrokeWarm);

            // ---- 中央：遮罩作品预览卡（06：插画满铺 + 标题/徽章浮层） ----
            HomePreviewCard = BlockOutWidgets.Place(go.transform, "PreviewCard", UIAnchorPreset.TopLeft, 24, 148, 342, 300);
            var cardImg = HomePreviewCard.gameObject.AddComponent<Image>();
            cardImg.sprite = BlockOutIconFactory.RoundedSlice(24f, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, 2f, null);
            cardImg.type = Image.Type.Sliced;

            // 插画区（06：mist 30,154,330×288 → 卡内 6,6,330,288；标题/徽章浮于其上）
            var artRoot = BlockOutWidgets.Place(HomePreviewCard, "ArtRoot", UIAnchorPreset.TopLeft, 6, 6, 330, 288);
            HomeRegionArts = BuildRegionGrid(artRoot, "ArtworkViewport", 0, 0, 330, 288, out HomeArtViewport);
            HomeRegionLocks = new GameObject[12];
            for (int i = 0; i < HomeRegionArts.Length; i++)
            {
                var art = HomeRegionArts[i];
                var mist = BlockOutWidgets.Panel(art.transform, "Mist", BlockOutDesignTokens.WithAlpha(BlockOutDesignTokens.White, 0.25f));
                mist.raycastTarget = false;
                var lockImg = BlockOutWidgets.SpriteImage(art.transform, "LockDot", BlockOutIconFactory.LockIcon(),
                    UIAnchorPreset.MiddleCenter, 0, 0, 14, 12);
                lockImg.raycastTarget = false;
                lockImg.color = new Color(1f, 1f, 1f, .55f);
                HomeRegionLocks[i] = lockImg.gameObject;
            }

            // 前景玩具块（玩法预览）
            BuildDecoToys(artRoot);

            // 图片加载失败态（07-C）
            HomeFailBox = BlockOutWidgets.Panel(artRoot, "FailBox", BlockOutDesignTokens.MistWarm, UIAnchorPreset.Stretch).gameObject;
            var failImg = HomeFailBox.GetComponent<Image>();
            failImg.sprite = BlockOutIconFactory.RoundedSlice(12f, BlockOutDesignTokens.MistWarm,
                BlockOutDesignTokens.GrayLocked, 1.5f, null);
            failImg.type = Image.Type.Sliced;
            BlockOutWidgets.SpriteImage(HomeFailBox.transform, "BrokenIcon", BlockOutIconFactory.BrokenImageIcon(),
                UIAnchorPreset.TopCenter, 0, 26, 40, 32).color = BlockOutDesignTokens.GrayLocked;
            BlockOutWidgets.Label(HomeFailBox.transform, "FailText", "图片加载失败", 11, 700,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 64, 160, 12);
            HomeRetryBtn = BlockOutWidgets.SecondaryButton(HomeFailBox.transform, "RetryBtn", "重试", null,
                UIAnchorPreset.TopCenter, 0, 84, 80, 24);
            HomeRetryExhausted = BlockOutWidgets.Label(HomeFailBox.transform, "ExhaustedText", "稍后再试", 11, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 88, 160, 12);
            HomeFailBox.SetActive(false);

            // 标题与拼片徽章（浮层：创建于插画区之后 = 绘制在上层）
            BlockOutWidgets.Label(HomePreviewCard, "CardTitle", "第一章 · 作品预览", 11, 800,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 18, 18, 160, 12);
            var pieceBadge = BlockOutWidgets.Pill(HomePreviewCard, "PieceBadge", 62, 20, BlockOutDesignTokens.CtaCoral,
                BlockOutDesignTokens.CtaCoral, UIAnchorPreset.TopRight, -10, 12);
            pieceBadge.GetComponent<Image>().color = BlockOutDesignTokens.ActionPrimary; // v6 #4A2F26
            HomePieceBadge = BlockOutWidgets.Label(pieceBadge, "Text", "通关 0/12", 11, 900,
                BlockOutDesignTokens.White, TextAnchor.MiddleCenter);   // v6: 深棕徽底必须配白字

            HomePlaceholderTag = BlockOutWidgets.Label(HomePreviewCard, "PlaceholderTag", "作品预览", 11, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleRight, UIAnchorPreset.BottomRight, -8, -6, 150, 10).gameObject;
            HomePlaceholderTag.SetActive(false);

            // ---- 唯一最强 CTA ----
            HomeCtaButton = BlockOutWidgets.CoralButton(go.transform, "CTA", "开始第 1 关", "第一章 · 甜点星球", null,
                BlockOutIconFactory.PlayIcon(), true);
            HomeCtaTitle = HomeCtaButton.transform.Find("Title").GetComponent<Text>();
            HomeCtaSub = HomeCtaButton.transform.Find("Sub").GetComponent<Text>();
            HomeCtaSecondary = BlockOutWidgets.SecondaryButton(go.transform, "CTASecondary", "重玩本章关卡", null,
                UIAnchorPreset.TopCenter, 0, 0, 232, 38);
            HomeCtaSecondary.gameObject.SetActive(false);

            // ---- 进度卡：12 拼片节点 ----
            var prog = BlockOutWidgets.Place(go.transform, "ProgressCard", UIAnchorPreset.TopLeft, 24, 524, 342, 120);
            var progImg = prog.gameObject.AddComponent<Image>();
            progImg.sprite = BlockOutIconFactory.RoundedSlice(20f, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, 2f, null);
            progImg.type = Image.Type.Sliced;
            HomeChapterTitle = BlockOutWidgets.Label(prog, "ChapterTitle", "第一章 · 甜点星球",
                BlockOutDesignTokens.FontCardTitle, 800, BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft,
                UIAnchorPreset.TopLeft, 18, 16, 200, 14);
            HomeCollectionLink = BlockOutWidgets.SecondaryButton(prog, "CollectionLink", "查看关卡", null,
                UIAnchorPreset.TopRight, -12, 12, 72, 18);
            var barBg = BlockOutWidgets.Panel(prog, "BarBg", BlockOutDesignTokens.BgCreamDeep,
                UIAnchorPreset.TopLeft, 18, 38, 306, 10);
            barBg.sprite = BlockOutIconFactory.RoundedSlice(5f, BlockOutDesignTokens.BgCreamDeep, Color.clear, 0f, null);
            barBg.type = Image.Type.Sliced;
            HomeProgressFill = BlockOutWidgets.Panel(prog, "BarFill", BlockOutDesignTokens.ActionPrimary,
                UIAnchorPreset.TopLeft, 18, 38, 306, 10);
            HomeProgressFill.type = Image.Type.Filled;
            HomeProgressFill.fillMethod = Image.FillMethod.Horizontal;
            HomeProgressFill.fillOrigin = (int)Image.OriginHorizontal.Left;
            HomeProgressFill.fillAmount = 0f;
            HomeNodes = new Image[12];
            for (int i = 0; i < 12; i++)
            {
                var node = BlockOutWidgets.Panel(prog, "Node_" + i, BlockOutDesignTokens.SurfaceCard,
                    UIAnchorPreset.TopLeft, 18 + i * 26.7f, 64, 12, 12);
                node.sprite = BlockOutIconFactory.Circle(BlockOutDesignTokens.SurfaceCard, BlockOutDesignTokens.StrokeBoard, 1.5f);
                HomeNodes[i] = node;
            }
            HomePieceText = BlockOutWidgets.Label(prog, "PieceText", "通关 0/12 · 还差 12 关完成本章",
                BlockOutDesignTokens.FontCardSub, 400, BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter,
                UIAnchorPreset.TopCenter, 0, 94, 306, 12);

            // ---- 底部三导航 ----
            var nav = BlockOutWidgets.Place(go.transform, "BottomNav", UIAnchorPreset.BottomLeft, 24, 28, 342, 64);
            var navImg = nav.gameObject.AddComponent<Image>();
            navImg.sprite = BlockOutIconFactory.RoundedSlice(22f, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, 2f, null);
            navImg.type = Image.Type.Sliced;
            for (int i = 0; i < 3; i++)
            {
                var slot = BlockOutWidgets.Panel(nav, "Slot_" + i, Color.clear, UIAnchorPreset.Stretch);
                slot.rectTransform.anchorMin = new Vector2(i / 3f, 0);
                slot.rectTransform.anchorMax = new Vector2((i + 1) / 3f, 1);
                slot.rectTransform.offsetMin = Vector2.zero;
                slot.rectTransform.offsetMax = Vector2.zero;
            }
            NavHomeBtn = BlockOutWidgets.NavItem(nav.transform.Find("Slot_0"), "HomeNav", BlockOutIconFactory.HomeIcon(), "首页", true, null);
            NavCollectionBtn = BlockOutWidgets.NavItem(nav.transform.Find("Slot_1"), "CollectionNav", BlockOutIconFactory.BookIcon(), "图鉴", false, null);
            NavStoreBtn = BlockOutWidgets.NavItem(nav.transform.Find("Slot_2"), "StoreNav", BlockOutIconFactory.BagIcon(), "商店", false, null);

            return go;
        }

        private void BuildDecoToys(Transform artRoot) { }

        private GameObject BuildBoardScreen()
        {
            var go = MakeScreen("Board");

            // ---- HUD 第一行：暂停 | 关卡 | 生命/计时 ----
            var hud = BlockOutWidgets.Panel(go.transform, "TopHUD", Color.clear, UIAnchorPreset.Stretch);
            hud.raycastTarget = false; // 全屏面板不拦截棋盘点击
            BoardPauseBtn = BlockOutWidgets.CircleIconButton(hud.transform, "PauseBtn", BlockOutIconFactory.PauseIcon(), 44, null,
                BlockOutDesignTokens.White, BlockOutDesignTokens.StrokeWarm);
            BoardLevelTitle = BlockOutWidgets.Label(hud.transform, "LevelTitle", "第一章 · 第 1 关",
                BlockOutDesignTokens.FontHudLevel, 700, BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter,
                UIAnchorPreset.TopCenter, 0, 0, 220, 22);
            BoardLevelSub = BlockOutWidgets.Label(hud.transform, "LevelSub", "甜点星球",
                BlockOutDesignTokens.FontHudSub, 400, BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter,
                UIAnchorPreset.TopCenter, 0, 24, 220, 14);

            // 生命（3 心，互斥于计时）
            var livesRow = BlockOutWidgets.Place(hud.transform, "LivesRow", UIAnchorPreset.TopRight, -66, 14, 55, 15);
            BoardHearts = new Image[3];
            for (int i = 0; i < 3; i++)
            {
                var heart = BlockOutWidgets.SpriteImage(livesRow, "Heart_" + i, BlockOutIconFactory.HeartIcon(),
                    UIAnchorPreset.TopLeft, i * 20, 0, 15, 15);
                BoardHearts[i] = heart;
            }
            // 计时胶囊（倒计时模式专用）
            BoardTimerPill = BlockOutWidgets.Pill(hud.transform, "TimerPill", 64, 20, BlockOutDesignTokens.BgCreamDeep,
                BlockOutDesignTokens.GoldCoin, UIAnchorPreset.TopRight, -70, 11);
            BoardTimerText = BlockOutWidgets.Label(BoardTimerPill, "TimerText", "01:23", 11, 900,
                BlockOutDesignTokens.GoldRim, TextAnchor.MiddleCenter);
            BoardTimerPill.gameObject.SetActive(false);

            // ---- 剩余块数胶囊 ----
            var remainPill = BlockOutWidgets.Pill(hud.transform, "RemainingPill", 110, 30, BlockOutDesignTokens.MintBg,
                BlockOutDesignTokens.MintFly, UIAnchorPreset.TopRight, -110, 48);
            var sq1 = BlockOutWidgets.Panel(remainPill, "Sq1", BlockOutDesignTokens.MintText,
                UIAnchorPreset.MiddleLeft, 11, 3, 9, 9);
            sq1.sprite = BlockOutIconFactory.RoundedSlice(2.5f, BlockOutDesignTokens.MintText, Color.clear, 0f, null);
            sq1.type = Image.Type.Sliced;
            var sq2 = BlockOutWidgets.Panel(remainPill, "Sq2", BlockOutDesignTokens.CtaCoral,
                UIAnchorPreset.MiddleLeft, 22, -3, 9, 9);
            sq2.sprite = BlockOutIconFactory.RoundedSlice(2.5f, BlockOutDesignTokens.CtaCoral, Color.clear, 0f, null);
            sq2.type = Image.Type.Sliced;
            BoardRemainingText = BlockOutWidgets.Label(remainPill, "RemainingText", "剩余 0 块",
                BlockOutDesignTokens.FontRemaining, 700, BlockOutDesignTokens.MintText, TextAnchor.MiddleLeft,
                UIAnchorPreset.Stretch);
            BoardRemainingText.rectTransform.offsetMin = new Vector2(38, 0);
            BoardRemainingText.rectTransform.offsetMax = new Vector2(-8, 0);

            // ---- 棋盘区（正方形；BoardView 由 Bootstrapper 挂入） ----
            BlockOutWidgets.Place(go.transform, "BoardArea", UIAnchorPreset.MiddleCenter, 0, 0, 354, 354);

            // ---- 操作提示 pill（Docs/DesignSystem.md：固定 220×26 居中，不缩放） ----
            var hintPill = BlockOutWidgets.Pill(go.transform, "HintPill", 220, 26, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, UIAnchorPreset.TopCenter, 0, 0);
            BlockOutWidgets.SpriteImage(hintPill, "Bulb", BlockOutIconFactory.Bulb(),
                UIAnchorPreset.MiddleLeft, 12, 0, 16, 16).color = BlockOutDesignTokens.GoldCoin;
            BoardHintPill = BlockOutWidgets.Label(hintPill, "HintText", "轻点整块方块，沿箭头方向飞出",
                BlockOutDesignTokens.FontHintPill, 400, BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft,
                UIAnchorPreset.Stretch);
            BoardHintPill.rectTransform.offsetMin = new Vector2(34, 0);
            BoardHintPill.rectTransform.offsetMax = new Vector2(-10, 0);

            // ---- 底部工具条：提示 / 锤子 / 魔法棒（Docs/DesignSystem.md：342×104；槽位区左右各内缩 26） ----
            var toolbar = BlockOutWidgets.Place(go.transform, "BottomToolbar", UIAnchorPreset.BottomLeft, 24, 28, 342, 72);
            var tbImg = toolbar.gameObject.AddComponent<Image>();
            tbImg.sprite = BlockOutIconFactory.RoundedSlice(26f, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, 2f, null);
            tbImg.type = Image.Type.Sliced;
            var slots = BlockOutWidgets.Place(toolbar, "Slots", UIAnchorPreset.Stretch);
            BuildToolSlot(slots, "HintSlot", BlockOutIconFactory.Bulb(), "提示", "点击高亮可飞块", HintSlot);
            BuildToolSlot(slots, "HammerSlot", BlockOutIconFactory.HammerIcon(), "锤子", "消除任意在场块", HammerSlot);
            BuildToolSlot(slots, "MagicSlot", BlockOutIconFactory.Wand(), "魔法棒", "飞走最多 3 块", MagicSlot);

            // 弹层（暂停/失败/确认/结算）改由 Build() 经 LoadOrBuildPopup 独立加载/构建，
            // 以便作为可复用 Prefab；此处不再内联构建，避免与 Prefab 路径重复生成。

            return go;
        }

        private void BuildToolSlot(Transform toolbar, string name, Sprite icon, string toolName, string condNormal, ToolSlotRefs slot)
        {
            int index = name == "HintSlot" ? 0 : (name == "HammerSlot" ? 1 : 2);
            var rootImg = BlockOutWidgets.Panel(toolbar, name, Color.clear, UIAnchorPreset.Stretch);
            rootImg.raycastTarget = true;
            var root = rootImg.rectTransform;
            root.anchorMin = new Vector2(index / 3f, 0);
            root.anchorMax = new Vector2((index + 1) / 3f, 1);
            root.offsetMin = Vector2.zero;
            root.offsetMax = Vector2.zero;

            // 图标 24×24 直接落于工具条卡片（04：图标 24pt，工具条内 y=34..58；无白底圆）
            slot.Icon = BlockOutWidgets.SpriteImage(root, "Icon", icon, UIAnchorPreset.TopCenter, 0, 34, 24, 24);
            slot.Icon.color = BlockOutDesignTokens.GrayIconLocked; // 默认置灰，控制器按三态覆写

            // 数量徽标（正常态）：右上珊瑚圆 + 计数（04：徽章中心 = 图标中心 + (20.5,-20)）
            slot.CountBadge = BlockOutWidgets.Panel(root, "CountBadge", BlockOutDesignTokens.CtaCoral,
                UIAnchorPreset.TopCenter, 20.5f, 15.5f, 21, 21).gameObject;
            slot.CountBadge.GetComponent<Image>().sprite = BlockOutIconFactory.Circle(BlockOutDesignTokens.CtaCoral, Color.clear, 0f);
            slot.CountText = BlockOutWidgets.Label(slot.CountBadge.transform, "Count", "0", 11, 900,
                BlockOutDesignTokens.White, TextAnchor.MiddleCenter);

            // 锁徽章（未解锁态）：#6E5449 圆底 + 白色锁形（Docs/DesignSystem.md）
            slot.LockBadge = BlockOutWidgets.Panel(root, "LockBadge", BlockOutDesignTokens.LockBadge,
                UIAnchorPreset.TopCenter, 20.5f, 15.5f, 21, 21).gameObject;
            slot.LockBadge.GetComponent<Image>().sprite = BlockOutIconFactory.Circle(BlockOutDesignTokens.LockBadge, Color.clear, 0f);
            var lockImg = BlockOutWidgets.SpriteImage(slot.LockBadge.transform, "Lock", BlockOutIconFactory.LockIcon(),
                UIAnchorPreset.Stretch);
            lockImg.rectTransform.offsetMin = new Vector2(6, 6);
            lockImg.rectTransform.offsetMax = new Vector2(-6, -6);
            lockImg.color = BlockOutDesignTokens.White;
            slot.LockBadge.SetActive(false);

            slot.NameText = BlockOutWidgets.Label(root, "Name", toolName, BlockOutDesignTokens.FontToolName, 400,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 75, 100, 12);
            slot.CondText = BlockOutWidgets.Label(root, "Cond", condNormal, BlockOutDesignTokens.FontToolCond, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 89, 110, 11);
            slot.Button = rootImg.gameObject.AddComponent<Button>();
            slot.Button.targetGraphic = rootImg;
            slot.Button.transition = Selectable.Transition.None;
            slot.Rect = root;
        }

        private void BuildPauseLayer(GameObject board)
        {
            var layer = MakeLayer(board, "PauseLayer");
            BlockOutWidgets.Dim(layer.transform, "Dim");
            var card = BlockOutWidgets.Card(layer.transform, "Card", 280, 252).rectTransform;
            BlockOutWidgets.Label(card, "Title", "已暂停", BlockOutDesignTokens.FontPopupTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 18, 200, 20);
            PauseResumeBtn = BlockOutWidgets.CoralButton(card, "ResumeBtn", "继续游戏", null, null);
            var rr = (RectTransform)PauseResumeBtn.transform;
            BlockOutWidgets.ApplyAnchor(rr, UIAnchorPreset.TopCenter);
            rr.anchoredPosition = new Vector2(0, -52);
            rr.sizeDelta = new Vector2(232, 42);
            PauseRestartBtn = BlockOutWidgets.SecondaryButton(card, "RestartBtn", "重开本关", null,
                UIAnchorPreset.TopCenter, 0, 102, 232, 38);
            PauseQuitBtn = BlockOutWidgets.SecondaryButton(card, "QuitBtn", "退出本关", null,
                UIAnchorPreset.TopCenter, 0, 146, 232, 38);
            PauseSettingsBtn = BlockOutWidgets.SecondaryButton(card, "SettingsBtn", "设置", null,
                UIAnchorPreset.TopCenter, 0, 190, 232, 38);
            BlockOutWidgets.Label(card, "FreezeNote", "暂停期间计时 / 动画 / 输入全部冻结", 11, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter, UIAnchorPreset.BottomCenter, 0, 10, 240, 12);
            layer.SetActive(false);
        }

        private void BuildFailLayer(GameObject board)
        {
            var layer = MakeLayer(board, "FailLayer");
            BlockOutWidgets.Dim(layer.transform, "Dim");
            // 280×150：05 失败卡（标题/原因/复活按钮/说明行/重开+退出并排）
            var card = BlockOutWidgets.Card(layer.transform, "Card", 280, 150).rectTransform;
            BlockOutWidgets.Label(card, "Title", "挑战失败", BlockOutDesignTokens.FontPopupTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 14, 200, 20);
            FailReasonText = BlockOutWidgets.Label(card, "ReasonText", "生命耗尽", 11, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 36, 200, 12);

            // 复活主按钮：标签按资格切换（免费 / 激励广告 / 300 金币 / 加载中 / 置灰）；免费徽章仅免费态显示
            FailReviveBtn = BlockOutWidgets.CoralButton(card, "ReviveBtn", "复活 · 免费", null, null, null, false);
            var rr = (RectTransform)FailReviveBtn.transform;
            BlockOutWidgets.ApplyAnchor(rr, UIAnchorPreset.TopCenter);
            rr.anchoredPosition = new Vector2(0, -52);
            rr.sizeDelta = new Vector2(232, 38);
            FailFreeBadge = BlockOutWidgets.Panel(FailReviveBtn.transform, "FreeBadge", BlockOutDesignTokens.GoldCoin,
                UIAnchorPreset.TopRight, -8, -7, 34, 14).gameObject;
            FailFreeBadge.GetComponent<Image>().sprite = BlockOutIconFactory.RoundedSlice(7f, BlockOutDesignTokens.GoldCoin, Color.clear, 0f, null);
            FailFreeBadge.GetComponent<Image>().type = Image.Type.Sliced;
            BlockOutWidgets.Label(FailFreeBadge.transform, "Text", "免费", 11, 900,
                BlockOutDesignTokens.GoldText, TextAnchor.MiddleCenter);
            FailFreeBadge.SetActive(false);
            FailReviveLabel = FailReviveBtn.transform.Find("Title").GetComponent<Text>();

            FailReviveNote = BlockOutWidgets.Label(card, "ReviveNote", "生命模式补 1 心 · 倒计时模式 +30 秒；单次挑战唯一一次复活", 11, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 94, 240, 11);
            FailExhaustedNote = BlockOutWidgets.Label(card, "ExhaustedNote", "复活机会已用完，只能重开或退出本关", 11, 700,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 94, 240, 11);
            FailExhaustedNote.gameObject.SetActive(false);

            FailRestartBtn = BlockOutWidgets.SecondaryButton(card, "RestartBtn", "重开本关", null,
                UIAnchorPreset.TopLeft, 20, 110, 116, 32);
            FailQuitBtn = BlockOutWidgets.SecondaryButton(card, "QuitBtn", "退出本关", null,
                UIAnchorPreset.TopRight, -20, 110, 116, 32);
            layer.SetActive(false);
        }

        private void BuildConfirmLayer(GameObject board)
        {
            var layer = MakeLayer(board, "ConfirmLayer");
            BlockOutWidgets.Dim(layer.transform, "Dim");
            var card = BlockOutWidgets.Card(layer.transform, "Card", 280, 158).rectTransform;
            ConfirmTitle = BlockOutWidgets.Label(card, "Title", "重开本关？", BlockOutDesignTokens.FontPopupTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 16, 240, 20);
            ConfirmBody = BlockOutWidgets.Label(card, "Body", string.Empty, 11, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 44, 240, 36);
            ConfirmCancelBtn = BlockOutWidgets.SecondaryButton(card, "CancelBtn", "取消", null,
                UIAnchorPreset.TopLeft, 20, 100, 100, 28);
            ConfirmOkBtn = BlockOutWidgets.CoralButton(card, "OkBtn", "确认", null);
            var ok = (RectTransform)ConfirmOkBtn.transform;
            BlockOutWidgets.ApplyAnchor(ok, UIAnchorPreset.TopRight);
            ok.anchoredPosition = new Vector2(-20, -100);
            ok.sizeDelta = new Vector2(100, 28);
            layer.SetActive(false);
        }

        private void BuildSettlementLayer(GameObject board)
        {
            var layer = MakeLayer(board, "SettlementLayer");
            BlockOutWidgets.Dim(layer.transform, "Dim");
            // 统一安全区根节点：与设置页同一套做法，弹层内容不落到刘海/手势区（P1-2）
            var settleSafeRoot = MakeSafeRoot(layer.transform, "SafeRoot");
            var card = BlockOutWidgets.Card(settleSafeRoot, "Card", 300, 500).rectTransform;
            SettleTitleText = BlockOutWidgets.Label(card, "Title", "关卡完成", BlockOutDesignTokens.FontPopupTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 14, 260, 20);

            // ---- 拼片揭晓图（13/17：首次/重复/章末揭晓效果；正式素材缺失时同结构占位）----
            SettleRevealRegions = BuildRegionGrid(card, "RevealRoot", 20, 44, 260, 216, out SettleRevealRoot);
            var revealFrame = BlockOutWidgets.Panel(card, "RevealFrame", Color.clear, UIAnchorPreset.TopLeft, 20, 44, 260, 216);
            var rfImg = revealFrame.gameObject.GetComponent<Image>();
            if (rfImg != null)
            {
                rfImg.sprite = BlockOutIconFactory.RoundedSlice(16f, BlockOutDesignTokens.SurfaceCard,
                    BlockOutDesignTokens.StrokeWarm, 1.5f, null);
                rfImg.type = Image.Type.Sliced;
                // 置于区域网格之下作为底板
                revealFrame.transform.SetSiblingIndex(0);
            }

            // R11：单关通关图片（该关关联插画）——覆盖在拼片网格之上，默认隐藏；
            // 普通通关由 UIController 按 LoadCompletionImage 显示，章末仍走章节拼片网格。
            var levelImgGo = new GameObject("LevelImage", typeof(RectTransform), typeof(Image));
            levelImgGo.transform.SetParent(card, false);
            var liRT = (RectTransform)levelImgGo.transform;
            BlockOutWidgets.ApplyAnchor(liRT, UIAnchorPreset.TopLeft);
            liRT.anchoredPosition = new Vector2(20, 44);
            liRT.sizeDelta = new Vector2(260, 216);
            var liImg = levelImgGo.GetComponent<Image>();
            liImg.color = Color.white;
            liImg.preserveAspect = true;
            liImg.enabled = false;   // 默认隐藏，由 HandleLevelWon 决定是否展示
            levelImgGo.transform.SetSiblingIndex(SettleRevealRoot.transform.GetSiblingIndex() + 1);   // 置于网格之上
            SettleLevelImage = liImg;

            SettlePieceText = BlockOutWidgets.Label(card, "PieceText", "通关 0/12", BlockOutDesignTokens.FontCardTitle, 800,
                BlockOutDesignTokens.MintText, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 270, 260, 14);
            SettleNoteText = BlockOutWidgets.Label(card, "NoteText", "本关进度已保存", BlockOutDesignTokens.FontCardSub, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 318, 260, 12);
            var coinRow = BlockOutWidgets.Place(card, "CoinRow", UIAnchorPreset.TopCenter, 0, 292, 200, 24);
            BlockOutWidgets.SpriteImage(coinRow, "CoinIcon", BlockOutIconFactory.Coin(),
                UIAnchorPreset.MiddleLeft, 12, 0, 22, 22);
            SettleRewardText = BlockOutWidgets.Label(coinRow, "RewardText", "获得 0 金币", BlockOutDesignTokens.FontCardTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft, UIAnchorPreset.MiddleLeft, 44, 0, 190, 20);

            SettleTitleText.fontSize = 22;
            SettleNextBtn = BlockOutWidgets.CoralButton(card, "NextBtn", "下一关", null);
            var nr = (RectTransform)SettleNextBtn.transform;
            BlockOutWidgets.ApplyAnchor(nr, UIAnchorPreset.TopCenter);
            nr.anchoredPosition = new Vector2(0, -340);
            nr.sizeDelta = new Vector2(260, 40);
            SettleCollectionBtn = BlockOutWidgets.SecondaryButton(card, "CollectionBtn", "查看关卡", null,
                UIAnchorPreset.TopCenter, 0, 388, 260, 32);
            SettleReplayBtn = BlockOutWidgets.SecondaryButton(card, "ReplayBtn", "重玩本关", null,
                UIAnchorPreset.TopCenter, 0, 422, 260, 32);
            SettleHomeBtn = BlockOutWidgets.SecondaryButton(card, "HomeBtn", "返回首页", null,
                UIAnchorPreset.TopCenter, 0, 456, 260, 32);
            layer.SetActive(false);
        }

        private void BuildSettingsLayer()
        {
            var layer = new GameObject("SettingsLayer", typeof(RectTransform));
            layer.transform.SetParent(canvasGo.transform, false);
            BlockOutWidgets.ApplyAnchor((RectTransform)layer.transform, UIAnchorPreset.Stretch);
            BlockOutWidgets.Panel(layer.transform, "Background", BlockOutDesignTokens.BgCream);
            // 统一安全区根节点：Card 挂在其下，卡片内所有元素（返回/标题/开关/关于）天然落在安全区内（P1-2）
            var safeRoot = MakeSafeRoot(layer.transform, "SafeRoot");
            var card = BlockOutWidgets.Place(safeRoot, "Card", UIAnchorPreset.MiddleCenter, 0, 0, 342, 780);
            BlockOutWidgets.Label(card, "Title", "设置", 22, 900, BlockOutDesignTokens.TextCocoa,
                TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 16, 200, 28);
            SettingsCloseBtn = BlockOutWidgets.SecondaryButton(card, "CloseBtn", "返回", null,
                UIAnchorPreset.TopLeft, 0, 8, 64, 44);
            var audio = BlockOutWidgets.Card(card, "AudioCard", 342, 260, UIAnchorPreset.TopLeft, 0, 84).rectTransform;
            BlockOutWidgets.Label(audio, "Heading", "音频与反馈", 14, 800, BlockOutDesignTokens.TextCocoa60,
                TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 20, 20, 200, 24);
            SettingsMusicSwitch = BlockOutWidgets.SwitchRow(audio, "音乐", "MusicSwitch", true, null);
            SettingsSoundSwitch = BlockOutWidgets.SwitchRow(audio, "音效", "SoundSwitch", true, null);
            SettingsVibSwitch = BlockOutWidgets.SwitchRow(audio, "震动", "VibSwitch", true, null);
            SettingsAboutBtn = BlockOutWidgets.SecondaryButton(card, "AboutBtn", "关于  ›", null,
                UIAnchorPreset.BottomCenter, 0, 40, 342, 64);
            layer.SetActive(false);
            layers["SettingsLayer"] = layer;
            BuildAboutLayer();
        }

        private void BuildAboutLayer()
        {
            var layer = new GameObject("AboutLayer", typeof(RectTransform));
            layer.transform.SetParent(canvasGo.transform, false);
            BlockOutWidgets.ApplyAnchor((RectTransform)layer.transform, UIAnchorPreset.Stretch);
            BlockOutWidgets.Dim(layer.transform, "Dim");
            var card = BlockOutWidgets.Card(layer.transform, "Card", 300, 300).rectTransform;
            BlockOutWidgets.Label(card, "Title", "关于", BlockOutDesignTokens.FontPopupTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 16, 240, 20);
            BlockOutWidgets.Label(card, "Body",
                "BlockOut\n版本 " + Application.version + "\n\n沿箭头送出方块，挑战关卡，\n逐步完成更多关卡。",
                BlockOutDesignTokens.FontCardSub, 400,
                BlockOutDesignTokens.TextCocoa, TextAnchor.UpperCenter, UIAnchorPreset.TopCenter, 0, 48, 256, 200);
            AboutCloseBtn = BlockOutWidgets.SecondaryButton(card, "CloseBtn", "关闭", null,
                UIAnchorPreset.TopCenter, 0, 254, 260, 36);
            layer.SetActive(false);
            layers["AboutLayer"] = layer;
        }

        private void BuildGuideLayer()
        {
            var layer = new GameObject("GuideLayer", typeof(RectTransform));
            layer.transform.SetParent(canvasGo.transform, false);
            BlockOutWidgets.ApplyAnchor((RectTransform)layer.transform, UIAnchorPreset.Stretch);
            BlockOutWidgets.Dim(layer.transform, "Dim");
            var card = BlockOutWidgets.Card(layer.transform, "Card", 280, 176).rectTransform;
            BlockOutWidgets.Label(card, "Title", "玩法引导", BlockOutDesignTokens.FontPopupTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 16, 200, 20);
            GuideBodyText = BlockOutWidgets.Label(card, "Body",
                "轻点整块方块，沿箭头方向飞出，把全部方块送出屏幕即可通关。\n受阻时方块会红色抖动并扣 1 颗心。",
                BlockOutDesignTokens.FontCardSub, 400, BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter,
                UIAnchorPreset.TopCenter, 0, 46, 240, 64);
            GuideDismissBtn = BlockOutWidgets.SecondaryButton(card, "DismissBtn", "开始挑战", null,
                UIAnchorPreset.TopCenter, 0, 128, 200, 38);
            layer.SetActive(false);
            GuideLayer = layer;
        }

        private GameObject MakeLayer(GameObject board, string name)
        {
            var layer = new GameObject(name, typeof(RectTransform));
            layer.transform.SetParent(board.transform, false);
            BlockOutWidgets.ApplyAnchor((RectTransform)layer.transform, UIAnchorPreset.Stretch);
            layers[name] = layer;
            return layer;
        }

        private RectTransform MakeSafeRoot(Transform parent, string name)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            BlockOutWidgets.ApplyAnchor(rt, UIAnchorPreset.Stretch);
            ApplySafeArea(rt);
            safeRoots[name] = rt;
            return rt;
        }

        private GameObject BuildLoadingScreen()
        {
            var go = MakeScreen("Loading");
            var bg = BlockOutWidgets.Panel(go.transform, "BG", BlockOutDesignTokens.BgCream);
            BlockOutWidgets.Label(go.transform, "Title", "BlockOut", 40, 900,
                BlockOutDesignTokens.CtaCoral, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 300, 300, 50);
            BlockOutWidgets.Label(go.transform, "Sub", "加载中…", 14, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 360, 200, 20);
            return go;
        }

        private GameObject BuildCollectionScreen()
        {
            var go = MakeScreen("Collection");

            // ---- 顶部栏：返回 + 标题 + 余额（14 顶部栏） ----
            CollectionBackBtn = BlockOutWidgets.CircleIconButton(go.transform, "BackBtn",
                BlockOutIconFactory.Arrow(Core.BlockOutDirection.Left), 36, null,
                BlockOutDesignTokens.SurfaceCard, BlockOutDesignTokens.StrokeWarm);
            BlockOutWidgets.Label(go.transform, "Title", "关卡", BlockOutDesignTokens.FontPopupTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 36, 200, 26);
            var coinPill = BlockOutWidgets.Pill(go.transform, "CoinPill", 94, 30, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, UIAnchorPreset.TopCenter, 0, 80);
            BlockOutWidgets.SpriteImage(coinPill, "CoinIcon", BlockOutIconFactory.Coin(),
                UIAnchorPreset.MiddleLeft, 9, 0, 18, 18);
            CollectionCoinText = BlockOutWidgets.Label(coinPill, "CoinText", "0", BlockOutDesignTokens.FontCoin, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft, UIAnchorPreset.Stretch);
            CollectionCoinText.rectTransform.offsetMin = new Vector2(33, 0);
            CollectionCoinText.rectTransform.offsetMax = new Vector2(-8, 0);

            // ---- 第一章摘要卡（342×148，rx24） ----
            var card = BlockOutWidgets.Place(go.transform, "SummaryCard", UIAnchorPreset.TopLeft, 24, 84, 342, 148);
            var cardImg = card.gameObject.AddComponent<Image>();
            cardImg.sprite = BlockOutIconFactory.RoundedSlice(24f, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, 2f, null);
            cardImg.type = Image.Type.Sliced;
            // 左侧缩略（12 区域局部揭晓，不泄露完整图）
            CollectionThumbRegions = BuildRegionGrid(card, "ThumbRoot", 12, 12, 120, 124, out CollectionThumbRoot);
            // 右侧信息
            CollectionChapterText = BlockOutWidgets.Label(card, "ChapterText", "第一章 · 甜点星球",
                BlockOutDesignTokens.FontCardTitle, 800, BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft,
                UIAnchorPreset.TopLeft, 144, 18, 180, 14);
            var progBg = BlockOutWidgets.Panel(card, "ProgBg", BlockOutDesignTokens.BgCreamDeep,
                UIAnchorPreset.TopLeft, 144, 38, 180, 10);
            progBg.sprite = BlockOutIconFactory.RoundedSlice(5f, BlockOutDesignTokens.BgCreamDeep, Color.clear, 0f, null);
            progBg.type = Image.Type.Sliced;
            var progFill = BlockOutWidgets.Panel(card, "ProgFill", BlockOutDesignTokens.ActionPrimary,
                UIAnchorPreset.TopLeft, 144, 38, 180, 10);
            progFill.type = Image.Type.Filled;
            progFill.fillMethod = Image.FillMethod.Horizontal;
            progFill.fillOrigin = (int)Image.OriginHorizontal.Left;
            progFill.fillAmount = 0f;
            CollectionProgressFill = progFill;
            CollectionPieceText = BlockOutWidgets.Label(card, "PieceText", "通关 0/12 · 还差 12 片",
                BlockOutDesignTokens.FontCardSub, 700, BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft,
                UIAnchorPreset.TopLeft, 144, 54, 180, 12);
            CollectionViewBigBtn = MakeCoralMiniButton(card, "ViewBigBtn", "查看大图", 144, 72, 120, 30);
            BlockOutWidgets.Label(card, "BigNote", "集齐12片后查看完整作品",
                BlockOutDesignTokens.FontToast, 400, BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleLeft,
                UIAnchorPreset.TopLeft, 144, 108, 180, 10);

            CollectionEmptyText = BlockOutWidgets.Label(go.transform, "EmptyText", "还没有拼片，去完成第一章的关卡解锁作品吧",
                BlockOutDesignTokens.FontCardSub, 400, BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter,
                UIAnchorPreset.TopCenter, 0, 244, 300, 12);

            // ---- 加载失败重试条（P2-10：默认隐藏，失败时显示，耗尽重试后转"稍后再试"）----
            var retryBar = BlockOutWidgets.Place(go.transform, "RetryBar", UIAnchorPreset.TopLeft, 24, 246, 342, 40);
            CollectionRetryBar = retryBar;
            var rbImg = retryBar.gameObject.AddComponent<Image>();
            rbImg.sprite = BlockOutIconFactory.RoundedSlice(12f, BlockOutDesignTokens.GoldLight,
                BlockOutDesignTokens.StrokeWarm, 1.5f, null);
            rbImg.type = Image.Type.Sliced;
            CollectionRetryText = BlockOutWidgets.Label(retryBar, "RetryText", "章节图加载失败 · 点此重试",
                BlockOutDesignTokens.FontCardSub, 400, BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft,
                UIAnchorPreset.MiddleLeft, 12, 0, 240, 14);
            CollectionRetryBtn = BlockOutWidgets.SecondaryButton(retryBar, "RetryBtn", "重试", null,
                UIAnchorPreset.MiddleRight, -10, 0, 76, 28);
            retryBar.gameObject.SetActive(false);

            // ---- 章节列表（已发布章 + 1 个"新章节准备中"占位） ----
            BlockOutWidgets.Label(go.transform, "ChapterLabel", "章节", BlockOutDesignTokens.FontCardTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 24, 296, 120, 16);
            int published = BlockOutContentConfig.PublishedChapters;
            for (int c = 0; c < published; c++)
                BuildChapterRow(go.transform, c, true);
            BuildChapterRow(go.transform, published, false); // 新章节准备中

            // ---- 重复挑战 · 关卡网格（12 格） ----
            var repeatCard = BlockOutWidgets.Place(go.transform, "RepeatCard", UIAnchorPreset.TopLeft, 24, 512, 342, 140);
            var rcImg = repeatCard.gameObject.AddComponent<Image>();
            rcImg.sprite = BlockOutIconFactory.RoundedSlice(16f, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, 2f, null);
            rcImg.type = Image.Type.Sliced;
            CollectionRepeatGrid = repeatCard;
            BlockOutWidgets.Label(repeatCard, "RepeatLabel", "重复挑战 · 第一章", BlockOutDesignTokens.FontCardTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 12, 14, 240, 16);
            for (int i = 0; i < 12; i++)
            {
                // 格容器 = 触控热区（P1-8：≥44×44，由 LayoutRepeatCells 定位）；Bg = 视觉底板
                var cell = BlockOutWidgets.Place(repeatCard, "RepeatCell_" + i, UIAnchorPreset.TopLeft, 12, 44, 44, 44);
                var hit = cell.gameObject.AddComponent<Image>();
                hit.color = Color.clear;
                var btn = cell.gameObject.AddComponent<Button>();
                btn.transition = Selectable.Transition.None;
                var bg = BlockOutWidgets.Panel(cell, "Bg", BlockOutDesignTokens.MintBg, UIAnchorPreset.MiddleCenter, 0, 0, 26, 26);
                bg.sprite = BlockOutIconFactory.RoundedSlice(8f, BlockOutDesignTokens.MintBg, BlockOutDesignTokens.MintFly, 1.2f, null);
                bg.type = Image.Type.Sliced;
                btn.targetGraphic = hit;
                bg.raycastTarget = false;
                BlockOutWidgets.SpriteImage(cell, "Mark", BlockOutIconFactory.MintCheck(), UIAnchorPreset.MiddleCenter, 0, 0, 16, 16);
                BlockOutWidgets.SpriteImage(cell, "Lock", BlockOutIconFactory.LockIcon(), UIAnchorPreset.MiddleCenter, 0, 0, 14, 14);
                var lockImg = cell.Find("Lock") != null ? cell.Find("Lock").GetComponent<Image>() : null;
                if (lockImg != null) lockImg.color = BlockOutDesignTokens.GrayLocked;
                BlockOutWidgets.Label(cell, "Num", (i + 1).ToString(), 11, 900,
                    BlockOutDesignTokens.CtaCoralBottom, TextAnchor.MiddleCenter, UIAnchorPreset.MiddleCenter, 0, 0, 26, 26);
            }
            BlockOutWidgets.Label(repeatCard, "RepeatNote", "已通关关卡可重复进入（刷金币/道具）；未通关关卡锁定",
                BlockOutDesignTokens.FontToast, 400, BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleLeft,
                UIAnchorPreset.TopLeft, 12, 116, 318, 10);

            // ---- 底部导航（图鉴激活） ----
            var nav = BlockOutWidgets.Place(go.transform, "BottomNav", UIAnchorPreset.BottomLeft, 24, 28, 342, 64);
            var navImg = nav.gameObject.AddComponent<Image>();
            navImg.sprite = BlockOutIconFactory.RoundedSlice(22f, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, 2f, null);
            navImg.type = Image.Type.Sliced;
            for (int i = 0; i < 3; i++)
            {
                var slot = BlockOutWidgets.Panel(nav, "Slot_" + i, Color.clear, UIAnchorPreset.Stretch);
                slot.rectTransform.anchorMin = new Vector2(i / 3f, 0);
                slot.rectTransform.anchorMax = new Vector2((i + 1) / 3f, 1);
                slot.rectTransform.offsetMin = Vector2.zero;
                slot.rectTransform.offsetMax = Vector2.zero;
            }
            CollectionNavHomeBtn = BlockOutWidgets.NavItem(nav.transform.Find("Slot_0"), "HomeNav",
                BlockOutIconFactory.HomeIcon(), "首页", false, null);
            CollectionNavCollectionBtn = BlockOutWidgets.NavItem(nav.transform.Find("Slot_1"), "CollectionNav",
                BlockOutIconFactory.BookIcon(), "图鉴", true, null);
            CollectionNavStoreBtn = BlockOutWidgets.NavItem(nav.transform.Find("Slot_2"), "StoreNav",
                BlockOutIconFactory.BagIcon(), "商店", false, null);

            var viewport = BlockOutWidgets.Place(go.transform, "ContentViewport", UIAnchorPreset.TopLeft, 24, 84, 342, 600);
            var hitSurface = viewport.gameObject.AddComponent<Image>();
            hitSurface.color = Color.clear;
            viewport.gameObject.AddComponent<RectMask2D>();
            CollectionContent = BlockOutWidgets.Place(viewport, "Content", UIAnchorPreset.TopLeft, 0, 0, 342, 800);
            collectionScroll = viewport.gameObject.AddComponent<ScrollRect>();
            collectionScroll.viewport = viewport;
            collectionScroll.content = CollectionContent;
            collectionScroll.horizontal = false;
            collectionScroll.movementType = ScrollRect.MovementType.Clamped;
            var move = new List<Transform>();
            foreach (Transform child in go.transform)
                if (child.name == "SummaryCard" || child.name == "EmptyText" || child.name == "RetryBar"
                    || child.name == "ChapterLabel" || child.name == "RepeatCard" || child.name.StartsWith("ChapterRow_")) move.Add(child);
            foreach (var child in move) child.SetParent(CollectionContent, false);

            // ---- 大图查看层（默认隐藏） ----
            BuildCollectionBigLayer(go);

            // 初始定位（Relayout 会按安全区重排）
            SetTopLeft(go.transform, "BackBtn", 24, 36, 36, 36);
            SetTopCenter(go.transform, "Title", 0, 36, 200, 26);
            SetTopRight(go.transform, "CoinPill", 24, 36, 94, 30);
            SetTopLeft(go.transform, "SummaryCard", 24, 84, 342, 148);
            SetTopCenter(go.transform, "EmptyText", 0, 244, 300, 12);
            SetTopLeft(go.transform, "ChapterLabel", 24, 256, 120, 16);
            SetTopLeft(go.transform, "RepeatCard", 24, 512, 342, 140);
            SetBottomLeft(go.transform, "BottomNav", 24, 28, 342, 64);

            return go;
        }

        private Image[] BuildRegionGrid(Transform parent, string name, float x, float y, float w, float h, out RectTransform rootRt)
        {
            rootRt = BlockOutWidgets.Place(parent, name, UIAnchorPreset.TopLeft, x, y, w, h);
            var background = rootRt.gameObject.AddComponent<Image>();
            background.color = BlockOutDesignTokens.MistWarm;
            background.raycastTarget = false;
            rootRt.gameObject.AddComponent<RectMask2D>();
            var artwork = BlockOutWidgets.Place(rootRt, "Artwork", UIAnchorPreset.MiddleCenter, 0, 0, w, w);
            var images = new Image[12];
            for (int i = 0; i < images.Length; i++)
            {
                images[i] = BlockOutWidgets.Panel(artwork, "Region_" + i, BlockOutDesignTokens.Silhouette,
                    UIAnchorPreset.TopLeft, 0, 0, 1, 1);
                images[i].raycastTarget = false;
            }
            LayoutArtwork(rootRt, false);
            return images;
        }

        private void BuildChapterRow(Transform parent, int chapter, bool unlocked)
        {
            float y = 266 + chapter * 80;
            var row = BlockOutWidgets.Place(parent, "ChapterRow_" + chapter, UIAnchorPreset.TopLeft, 24, y, 342, 72);
            var img = row.gameObject.AddComponent<Image>();
            img.sprite = BlockOutIconFactory.RoundedSlice(16f, BlockOutDesignTokens.SurfaceCard,
                unlocked ? BlockOutDesignTokens.MintFly : BlockOutDesignTokens.StrokeWarm, 1.5f, null);
            img.type = Image.Type.Sliced;
            // 已发布章可点击切换关卡查看的章节（P2-10：章节行切换交互）
            if (unlocked)
            {
                var rowBtn = row.gameObject.AddComponent<Button>();
                rowBtn.targetGraphic = img;
                rowBtn.transition = Selectable.Transition.None;
            }
            // 左侧缩略圆
            var thumb = BlockOutWidgets.Panel(row, "Thumb", unlocked ? BlockOutDesignTokens.MintFly : BlockOutDesignTokens.Silhouette,
                UIAnchorPreset.TopLeft, 12, 10, 52, 52);
            thumb.sprite = BlockOutIconFactory.Circle(unlocked ? BlockOutDesignTokens.MintFly : BlockOutDesignTokens.Silhouette,
                BlockOutDesignTokens.White, 2.5f);
            if (!unlocked)
            {
                var lockIcon = BlockOutWidgets.SpriteImage(thumb.transform, "Lock", BlockOutIconFactory.LockIcon(), UIAnchorPreset.Stretch);
                lockIcon.rectTransform.offsetMin = new Vector2(15, 15);
                lockIcon.rectTransform.offsetMax = new Vector2(-15, -15);
                lockIcon.color = BlockOutDesignTokens.GrayLocked;
            }
            BlockOutWidgets.Label(row, "Title", unlocked ? "第一章 · 甜点星球" : "新章节准备中",
                BlockOutDesignTokens.FontCardTitle, 800, unlocked ? BlockOutDesignTokens.TextCocoa : BlockOutDesignTokens.GrayLocked,
                TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 76, 14, 200, 14);
            BlockOutWidgets.Label(row, "Sub", unlocked ? "0/12 · 进行中" : "新章节发布时间待定 · 不可进入",
                BlockOutDesignTokens.FontCardSub, 400, BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleLeft,
                UIAnchorPreset.TopLeft, 76, 34, 240, 12);
        }

        private Button MakeCoralMiniButton(Transform parent, string name, string label, float x, float y, float w, float h)
        {
            var rt = BlockOutWidgets.Place(parent, name, UIAnchorPreset.TopLeft, x, y, w, h);
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = BlockOutIconFactory.RoundedSlice(Mathf.Min(h * 0.5f, 18f), BlockOutDesignTokens.CtaCoralBottom,
                Color.clear, 0f, BlockOutDesignTokens.CtaCoralTop);
            img.type = Image.Type.Sliced;
            img.color = BlockOutDesignTokens.ActionPrimary;   // v6：中性遮罩 + 深棕 tint，白字才可读
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = img;
            btn.transition = Selectable.Transition.None;
            BlockOutWidgets.Label(rt, "Text", label, BlockOutDesignTokens.FontButton, 900, BlockOutDesignTokens.White, TextAnchor.MiddleCenter);
            return btn;
        }

        private void BuildCollectionBigLayer(GameObject screen)
        {
            var layer = new GameObject("CollectionBigLayer", typeof(RectTransform));
            layer.transform.SetParent(screen.transform, false);
            BlockOutWidgets.ApplyAnchor((RectTransform)layer.transform, UIAnchorPreset.Stretch);
            BlockOutWidgets.Dim(layer.transform, "Dim");
            bigCard = BlockOutWidgets.Card(layer.transform, "Card", 342, 400).rectTransform;
            CollectionBigRegions = BuildRegionGrid(bigCard, "Viewport", 16, 64, 310, 264, out CollectionBigRoot);
            CollectionBigRoot.GetComponent<Image>().raycastTarget = true;
            CollectionZoom = CollectionBigRoot.gameObject.AddComponent<BlockOutPinchZoom>();
            CollectionZoom.Target = CollectionBigRoot.Find("Artwork") as RectTransform;
            CollectionBigCloseBtn = BlockOutWidgets.SecondaryButton(bigCard, "CloseBtn", "返回", null,
                UIAnchorPreset.TopRight, -16, 12, 80, 44);
            BlockOutWidgets.Label(bigCard, "BigNote", "双指缩放 · 拖动查看 · 双击复位",
                BlockOutDesignTokens.FontToast, 400, BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleCenter,
                UIAnchorPreset.BottomCenter, 0, 12, 300, 20);
            layer.SetActive(false);
            CollectionBigLayer = layer;
        }

        private GameObject BuildStoreScreen()
        {
            var go = MakeScreen("Store");

            // ---- 顶部栏：返回 + 标题 + 余额（15 顶部栏） ----
            StoreBackBtn = BlockOutWidgets.CircleIconButton(go.transform, "BackBtn",
                BlockOutIconFactory.Arrow(Core.BlockOutDirection.Left), 36, null,
                BlockOutDesignTokens.SurfaceCard, BlockOutDesignTokens.StrokeWarm);
            BlockOutWidgets.Label(go.transform, "Title", "商店", BlockOutDesignTokens.FontPopupTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter, UIAnchorPreset.TopCenter, 0, 36, 200, 26);
            var coinPill = BlockOutWidgets.Pill(go.transform, "CoinPill", 94, 30, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, UIAnchorPreset.TopCenter, 0, 80);
            BlockOutWidgets.SpriteImage(coinPill, "CoinIcon", BlockOutIconFactory.Coin(),
                UIAnchorPreset.MiddleLeft, 9, 0, 18, 18);
            StoreCoinText = BlockOutWidgets.Label(coinPill, "CoinText", "0", BlockOutDesignTokens.FontCoin, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft, UIAnchorPreset.Stretch);
            StoreCoinText.rectTransform.offsetMin = new Vector2(33, 0);
            StoreCoinText.rectTransform.offsetMax = new Vector2(-8, 0);

            // ---- 三商品卡（342×112，rx20；y=84/208/332） ----
            StoreProducts = new StoreProductRefs[3];
            StoreProducts[0] = MakeStoreProduct(go.transform, 84, BlockOutToolId.Hint,
                BlockOutIconFactory.Bulb(), "提示", "高亮可飞块 2.5 秒", BlockOutContentConfig.HintUnlockLevel);
            StoreProducts[1] = MakeStoreProduct(go.transform, 208, BlockOutToolId.Hammer,
                BlockOutIconFactory.HammerIcon(), "锤子", "消除任意在场块", BlockOutContentConfig.HammerUnlockLevel);
            StoreProducts[2] = MakeStoreProduct(go.transform, 332, BlockOutToolId.Magic,
                BlockOutIconFactory.Wand(), "魔法棒", "自动飞出最多 3 个可飞块", BlockOutContentConfig.MagicUnlockLevel);

            // ---- 金币获取说明卡（15 底部说明） ----
            var note = BlockOutWidgets.Place(go.transform, "CoinNote", UIAnchorPreset.TopLeft, 24, 554, 342, 86);
            var noteImg = note.gameObject.AddComponent<Image>();
            noteImg.sprite = BlockOutIconFactory.RoundedSlice(16f, BlockOutDesignTokens.MintBg,
                BlockOutDesignTokens.StrokeWarm, 1.5f, null);
            noteImg.type = Image.Type.Sliced;
            BlockOutWidgets.SpriteImage(note, "CoinIcon", BlockOutIconFactory.Coin(), UIAnchorPreset.TopLeft, 16, 16, 20, 20);
            BlockOutWidgets.Label(note, "NoteTitle", "金币获取", BlockOutDesignTokens.FontCardTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 44, 16, 160, 16);
            BlockOutWidgets.Label(note, "NoteBody", "通关和重复挑战可获得金币", BlockOutDesignTokens.FontCardSub, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 16, 42, 310, 12);

            // ---- 底部导航（商店激活） ----
            var nav = BlockOutWidgets.Place(go.transform, "BottomNav", UIAnchorPreset.BottomLeft, 24, 28, 342, 64);
            var navImg = nav.gameObject.AddComponent<Image>();
            navImg.sprite = BlockOutIconFactory.RoundedSlice(22f, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, 2f, null);
            navImg.type = Image.Type.Sliced;
            for (int i = 0; i < 3; i++)
            {
                var slot = BlockOutWidgets.Panel(nav, "Slot_" + i, Color.clear, UIAnchorPreset.Stretch);
                slot.rectTransform.anchorMin = new Vector2(i / 3f, 0);
                slot.rectTransform.anchorMax = new Vector2((i + 1) / 3f, 1);
                slot.rectTransform.offsetMin = Vector2.zero;
                slot.rectTransform.offsetMax = Vector2.zero;
            }
            StoreNavHomeBtn = BlockOutWidgets.NavItem(nav.transform.Find("Slot_0"), "HomeNav",
                BlockOutIconFactory.HomeIcon(), "首页", false, null);
            StoreNavCollectionBtn = BlockOutWidgets.NavItem(nav.transform.Find("Slot_1"), "CollectionNav",
                BlockOutIconFactory.BookIcon(), "图鉴", false, null);
            StoreNavStoreBtn = BlockOutWidgets.NavItem(nav.transform.Find("Slot_2"), "StoreNav",
                BlockOutIconFactory.BagIcon(), "商店", true, null);

            return go;
        }

        private StoreProductRefs MakeStoreProduct(Transform parent, float cardY, BlockOutToolId tool,
            Sprite icon, string name, string desc, int unlockLevel)
        {
            var card = BlockOutWidgets.Place(parent, "Product_" + tool, UIAnchorPreset.TopLeft, 24, cardY, 342, 112);
            var refs = new StoreProductRefs { Tool = tool, CardRoot = card.gameObject };
            var cardImg = card.gameObject.AddComponent<Image>();
            cardImg.sprite = BlockOutIconFactory.RoundedSlice(20f, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, 2f, null);
            cardImg.type = Image.Type.Sliced;
            refs.CardImg = cardImg;

            // 图标圆（左 40 / 上 16 / 52×52）
            var iconCircle = BlockOutWidgets.Panel(card, "IconBg", BlockOutDesignTokens.MistWarm, UIAnchorPreset.TopLeft, 40, 16, 52, 52);
            iconCircle.sprite = BlockOutIconFactory.Circle(BlockOutDesignTokens.MistWarm, BlockOutDesignTokens.StrokeWarm, 1.5f);
            iconCircle.type = Image.Type.Sliced;
            refs.IconImg = BlockOutWidgets.SpriteImage(card, "Icon", icon, UIAnchorPreset.TopLeft, 52, 28, 28, 28);
            refs.IconImg.color = BlockOutDesignTokens.TextCocoa;

            // 锁徽章（未解锁态：#6E5449 圆底 + 白色锁形）
            var lockBadge = new GameObject("LockBadge", typeof(RectTransform), typeof(Image));
            lockBadge.transform.SetParent(card, false);
            var lrt = (RectTransform)lockBadge.transform;
            BlockOutWidgets.ApplyAnchor(lrt, UIAnchorPreset.TopLeft);
            lrt.anchoredPosition = new Vector2(74, 12);
            lrt.sizeDelta = new Vector2(20, 20);
            var lockImg = lockBadge.GetComponent<Image>();
            lockImg.sprite = BlockOutIconFactory.Circle(BlockOutDesignTokens.LockBadge, Color.clear, 0f);
            var lockIcon = BlockOutWidgets.SpriteImage(lockBadge.transform, "Lock", BlockOutIconFactory.LockIcon(), UIAnchorPreset.Stretch);
            lockIcon.rectTransform.offsetMin = new Vector2(5, 5);
            lockIcon.rectTransform.offsetMax = new Vector2(-5, -5);
            lockIcon.color = BlockOutDesignTokens.White;
            lockBadge.SetActive(false);
            refs.LockBadge = lockBadge;

            refs.NameText = BlockOutWidgets.Label(card, "Name", name, BlockOutDesignTokens.FontCardTitle, 900,
                BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 102, 18, 160, 16);
            refs.DescText = BlockOutWidgets.Label(card, "Desc", desc, BlockOutDesignTokens.FontCardSub, 400,
                BlockOutDesignTokens.TextCocoa60, TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 102, 40, 160, 24);
            BlockOutWidgets.SpriteImage(card, "Coin", BlockOutIconFactory.Coin(), UIAnchorPreset.TopLeft, 102, 64, 14, 14);
            refs.CoinText = BlockOutWidgets.Label(card, "CoinText", "300 金币", 11, 700,
                BlockOutDesignTokens.GoldText, TextAnchor.MiddleLeft, UIAnchorPreset.TopLeft, 120, 62, 100, 16);

            // 购买按钮（72×36，rx18；左下 254 / 上 28）
            var buyRt = BlockOutWidgets.Place(card, "BuyBtn", UIAnchorPreset.TopLeft, 254, 28, 72, 36);
            var buyImg = buyRt.gameObject.AddComponent<Image>();
            buyImg.sprite = BlockOutIconFactory.RoundedSlice(18f, BlockOutDesignTokens.CtaCoralBottom,
                Color.clear, 0f, BlockOutDesignTokens.CtaCoralTop);
            buyImg.type = Image.Type.Sliced;
            buyImg.color = BlockOutDesignTokens.ActionPrimary;   // v6: 白字必须有深底
            var buyBtn = buyRt.gameObject.AddComponent<Button>();
            buyBtn.targetGraphic = buyImg;
            buyBtn.transition = Selectable.Transition.None;
            refs.BuyBtn = buyBtn;
            refs.BuyText = BlockOutWidgets.Label(buyRt, "BuyText", "购买", 11, 900,
                BlockOutDesignTokens.White, TextAnchor.MiddleCenter);

            return refs;
        }

        private void LayoutRepeatCells(RectTransform repCard, float cardW, float cardH)
        {
            const int Cols = 6, Rows = 2;
            const float MinTouch = 44f;
            const float PadX = 12f;
            const float Top = 40f;          // 标题下方起始
            const float BottomPad = 26f;    // 底部注释上方留白

            float availW = Mathf.Max(0f, cardW - PadX * 2f);
            float colPitch = availW / Cols;
            // 热区取 min(44, 列距)，保证 6 个热区并排后不互相覆盖
            float touchW = Mathf.Min(MinTouch, colPitch);
            float touchH = MinTouch;
            float availH = Mathf.Max(Rows * MinTouch, cardH - Top - BottomPad);
            float rowPitch = availH / Rows;
            touchH = Mathf.Min(touchH, rowPitch);

            float visual = Mathf.Min(26f, touchW - 8f);
            if (visual < 16f) visual = 16f;

            for (int i = 0; i < 12; i++)
            {
                int col = i % Cols, row = i / Cols;
                float x = PadX + col * colPitch + (colPitch - touchW) * 0.5f;
                float y = Top + row * rowPitch + (rowPitch - touchH) * 0.5f;
                var cell = repCard.Find("RepeatCell_" + i) as RectTransform;
                if (cell == null) continue;
                cell.anchorMin = new Vector2(0, 1);
                cell.anchorMax = new Vector2(0, 1);
                cell.pivot = new Vector2(0, 1);
                cell.sizeDelta = new Vector2(touchW, touchH);
                cell.anchoredPosition = new Vector2(x, -y);

                // 视觉底板在热区内居中，尺寸保持 26
                var bg = cell.Find("Bg") as RectTransform;
                if (bg != null)
                {
                    bg.anchorMin = new Vector2(0.5f, 0.5f);
                    bg.anchorMax = new Vector2(0.5f, 0.5f);
                    bg.pivot = new Vector2(0.5f, 0.5f);
                    bg.sizeDelta = new Vector2(visual, visual);
                    bg.anchoredPosition = Vector2.zero;
                }
                var num = cell.Find("Num") as RectTransform;
                if (num != null)
                {
                    num.anchorMin = new Vector2(0.5f, 0.5f);
                    num.anchorMax = new Vector2(0.5f, 0.5f);
                    num.pivot = new Vector2(0.5f, 0.5f);
                    num.sizeDelta = new Vector2(visual, visual);
                    num.anchoredPosition = Vector2.zero;
                }
            }
        }

        private void LayoutCollectionViewer(float width, float availableHeight)
        {
            if (bigCard == null) return;
            float w = Mathf.Min(390, width);
            float h = Mathf.Min(600, availableHeight);
            bigCard.sizeDelta = new Vector2(w, h);
            SetTopLeft(bigCard, "Viewport", 16, 64, w - 32, Mathf.Max(80, h - 108));
            LayoutArtwork(CollectionBigRoot, true);
            CollectionZoom.ResetView();
        }

        private void LayoutRegions(RectTransform artRt, float artW, float artH)
        {
            SetTopLeft(artRt, "ArtworkViewport", 0, 0, artW, artH);
            LayoutArtwork(HomeArtViewport, false);
        }

        private void LayoutDeco(RectTransform artRt, float artW, float artH)
        {
            float c = 22f;
            var toyB = artRt.Find("ToyB") as RectTransform;
            if (toyB != null)
            {
                toyB.anchorMin = new Vector2(0, 1);
                toyB.anchorMax = new Vector2(0, 1);
                toyB.pivot = new Vector2(0, 1);
                toyB.sizeDelta = new Vector2(c, c * 2);
                toyB.anchoredPosition = new Vector2(artW * 0.14f, -artH * 0.42f);
            }
            var ripple = artRt.Find("Ripple") as RectTransform;
            if (ripple != null)
            {
                ripple.anchorMin = new Vector2(0, 1);
                ripple.anchorMax = new Vector2(0, 1);
                ripple.pivot = new Vector2(0.5f, 0.5f);
                ripple.sizeDelta = new Vector2(28, 28);
                ripple.anchoredPosition = new Vector2(artW * 0.14f + c * 0.5f, -artH * 0.42f + c * 0.5f - 18);
            }
            var toyA = artRt.Find("ToyA") as RectTransform;
            if (toyA != null)
            {
                toyA.anchorMin = new Vector2(0, 1);
                toyA.anchorMax = new Vector2(0, 1);
                toyA.pivot = new Vector2(0, 1);
                toyA.sizeDelta = new Vector2(c * 2, c * 2);
                toyA.anchoredPosition = new Vector2(artW * 0.62f, -artH * 0.44f);
            }
            for (int i = 0; i < 3; i++)
            {
                var dot = artRt.Find("TrailDot_" + i) as RectTransform;
                if (dot == null) continue;
                dot.anchorMin = new Vector2(0, 1);
                dot.anchorMax = new Vector2(0, 1);
                dot.pivot = new Vector2(0, 1);
                dot.sizeDelta = new Vector2(4, 4);
                dot.anchoredPosition = new Vector2(artW * 0.62f + c * 2 + 6 + i * 9, -artH * 0.44f + c * 1.6f - i * 4);
            }
        }

        private void LayoutFullPages(float width, float height)
        {
            // 卡片已挂在 SafeRoot（已按安全区内缩）之下，因此这里只做"铺满安全区"，
            // 不再对位置做任何 (SafeTop-SafeBottom) 二次补偿——补偿交给 SafeRoot 统一处理（P1-2）。
            if (layers.TryGetValue("SettingsLayer", out var settings))
            {
                var safeRoot = settings.transform.Find("SafeRoot") as RectTransform;
                if (safeRoot != null) ApplySafeArea(safeRoot);
                var card = settings.transform.Find("Card") as RectTransform;
                if (card == null) card = safeRoot != null ? safeRoot.Find("Card") as RectTransform : null;
                if (card != null)
                {
                    // 铺满安全区（Stretch + 零内缩），卡片内容自然全在安全区内
                    card.anchorMin = Vector2.zero;
                    card.anchorMax = Vector2.one;
                    card.pivot = new Vector2(0.5f, 0.5f);
                    card.offsetMin = Vector2.zero;
                    card.offsetMax = Vector2.zero;
                    card.anchoredPosition = Vector2.zero;
                }
                if (card == null) return;
                var audio = SetTopLeft(card, "AudioCard", 0, 84, width, 260);
                SetTopLeft(audio, "MusicSwitch", 20, 64, width - 40, 52);
                SetTopLeft(audio, "SoundSwitch", 20, 124, width - 40, 52);
                SetTopLeft(audio, "VibSwitch", 20, 184, width - 40, 52);
                // 「关于」行贴卡片底部：按安全区可用高度自上而下定位，
                // 不用构建时的 BottomCenter 锚点（锚点不一致会导致换算后错位）。
                SetTopLeft(card, "AboutBtn", 0, height - 64 - 20, width, 64);
            }
            if (layers.TryGetValue("SettlementLayer", out var settlement))
            {
                var sSafe = settlement.transform.Find("SafeRoot") as RectTransform;
                if (sSafe != null) ApplySafeArea(sSafe);
                var card = settlement.transform.Find("Card") as RectTransform;
                if (card == null) card = sSafe != null ? sSafe.Find("Card") as RectTransform : null;
                if (card != null)
                {
                    card.anchorMin = Vector2.zero;
                    card.anchorMax = Vector2.one;
                    card.pivot = new Vector2(0.5f, 0.5f);
                    card.offsetMin = Vector2.zero;
                    card.offsetMax = Vector2.zero;
                    card.anchoredPosition = Vector2.zero;
                }
                if (card == null) return;
                float revealH = Mathf.Clamp(height - 330, 160, 360);
                SetTopCenter(card, "Title", 0, 16, width - 32, 28);
                SetTopCenter(card, "PieceText", 0, 52, width - 32, 20);
                SetTopLeft(card, "RevealRoot", 16, 84, width - 32, revealH);
                SetTopLeft(card, "RevealFrame", 16, 84, width - 32, revealH);
                float y = 84 + revealH;
                SetTopCenter(card, "NoteText", 0, y + 10, width - 32, 18);
                SetTopCenter(card, "CoinRow", 0, y + 34, 240, 24);
                // v6 §5.3：按钮组贴底，消除旧版底部约 1/4 空白。
                // 揭晓区保持正方形 contain，图下方留白作为图片呼吸区，不拉伸变形。
                float nextY = Mathf.Max(y + 72, height - 24f - 160f);
                SetTopCenter(card, "NextBtn", 0, nextY, width - 32, 48);
                SetTopLeft(card, "CollectionBtn", 16, nextY + 60, (width - 44) / 2, 44);
                SetTopLeft(card, "ReplayBtn", width / 2 + 6, nextY + 60, (width - 44) / 2, 44);
                SetTopCenter(card, "HomeBtn", 0, nextY + 116, width - 32, 44);
                LayoutArtwork(SettleRevealRoot, settlementContain);
            }
        }

        private void ClampCardWidth(Dictionary<string, GameObject> layerDict, string name, float cw)
        {
            GameObject layer;
            if (!layerDict.TryGetValue(name, out layer) || layer == null) return;
            var card = FindDeep(layer.transform, "Card") as RectTransform;
            if (card == null) return;
            // 卡片为居中/拉伸锚点，仅收缩宽度（小屏不溢出内容区）
            card.sizeDelta = new Vector2(Mathf.Min(card.sizeDelta.x, cw), card.sizeDelta.y);
        }

        private static Transform FindDeep(Transform root, string name)
        {
            if (root == null) return null;
            var direct = root.Find(name);
            if (direct != null) return direct;
            for (int i = 0; i < root.childCount; i++)
            {
                var found = FindDeep(root.GetChild(i), name);
                if (found != null) return found;
            }
            return null;
        }

        internal void LayoutAuthoring()
        {
            if (metrics == null || canvas == null) return;
            var m = metrics;
            float H = m.CanvasHeight;
            float L = m.SafeLeft, R = m.SafeRight, T = m.SafeTop, B = m.SafeBottom;
            float cw = m.ContentWidth;
            bool small = m.IsSmallScreen;
            bool longScreen = m.IsLongScreen;

            // ---- Home（06 纵向节奏：顶栏 42 / 卡 148 / CTA 468 / 进度 586；长屏 CTA 吸底） ----
            GameObject home;
            if (screens.TryGetValue(BlockOutScreenId.Home, out home) && home != null)
            {
                // 顶栏（06：图标垂直中心 T+36；金币胶囊右缘距右 72 = 设计 x224..318）
                SetTopLeft(home.transform, "LogoTile", L, T + 18, 36, 36);
                SetTopLeft(home.transform, "LogoArrow", L + 7, T + 25, 22, 22);
                SetTopLeft(home.transform, "LogoTitle", L + 46, T + 26, 150, 18);
                SetTopLeft(home.transform, "LogoSub", L + 46, T + 44, 150, 12);
                SetTopRight(home.transform, "CoinPill", 72, T + 21, 94, 30);
                SetTopRight(home.transform, "SettingsBtn", R, T + 18, 36, 36);

                // 预览卡：插画满铺 + 标题/徽章浮层
                // 高度按"扣除安全区 + 顶栏 + CTA(含次级) + 进度卡 + 底部导航"后的余高计算（P1-7）
                float navBottomHome = B;
                float navTopHome = H - navBottomHome - m.NavHeight;
                float progHHome = small ? 104f : 120f;
                bool secondaryVisibleHome = (home.transform.Find("CTASecondary") as RectTransform) != null
                                            && home.transform.Find("CTASecondary").gameObject.activeSelf;
                float topBarH = 56f;                       // 顶栏 logo 区高度
                float ctaBlockH = m.CtaHeight + (secondaryVisibleHome ? 16f + 38f : 0f);
                float cardH = m.ComputePreviewCardHeight(topBarH, ctaBlockH, progHHome);
                float cardY = T + topBarH + (small ? 8f : 24f);
                var cardRt = SetTopLeft(home.transform, "PreviewCard", L, cardY, cw, cardH);
                var artRt = SetTopLeft(cardRt, "ArtRoot", 6, 6, cw - 12, cardH - 12);
                LayoutRegions(artRt, cw - 12, cardH - 12);
                LayoutDeco(artRt, cw - 12, cardH - 12);
                SetTopLeft(cardRt, "CardTitle", 18, 18, 160, 12);
                SetTopRight(cardRt, "PieceBadge", 10, 12, 62, 20);

                // 次级 CTA（重玩本章关卡）：仅章节完成时显示，位于 CTA 正下方
                var secondary = home.transform.Find("CTASecondary") as RectTransform;
                bool secondaryVisible = secondary != null && secondary.gameObject.activeSelf;
                float secondaryH = 38f;

                float navBottom = navBottomHome;                       // Docs/DesignSystem.md：底部组件止于安全区上方
                float navTop = navTopHome;
                float progH = progHHome;

                // CTA：默认贴预览卡；长屏（Docs/DesignSystem.md）CTA/导航吸底、中部留白
                float ctaY = cardY + cardH + (small ? 8f : 20f);
                if (longScreen)
                {
                    float progTop = navTop - 8 - progH;
                    float ctaBlock = m.CtaHeight + (secondaryVisible ? 16f + secondaryH : 0f);
                    ctaY = progTop - (small ? 12f : 24f) - ctaBlock;
                    float minCtaY = cardY + cardH + 8;
                    if (ctaY < minCtaY) ctaY = minCtaY;
                }
                SetTopLeft(home.transform, "CTA", L, ctaY, cw, m.CtaHeight);
                if (secondary != null)
                {
                    BlockOutWidgets.ApplyAnchor(secondary, UIAnchorPreset.TopCenter);
                    secondary.anchoredPosition = new Vector2(0, -(ctaY + m.CtaHeight + 16));
                    secondary.sizeDelta = new Vector2(232, secondaryH);
                }
                float ctaBottom = ctaY + m.CtaHeight;

                float afterCta = ctaBottom + (secondaryVisible ? 16f + secondaryH : 0f);
                float progY;
                if (longScreen) progY = navTop - 8 - progH;
                else
                {
                    progY = afterCta + (small ? 8f : 30f);
                    if (progY + progH > navTop - 8)
                        progY = Mathf.Max(afterCta + 8, navTop - 8 - progH);
                }
                var progRt = SetTopLeft(home.transform, "ProgressCard", L, progY, cw, progH);
                SetTopLeft(progRt, "ChapterTitle", 18, 16, 200, 14);
                SetTopRight(progRt, "CollectionLink", 12, 12, 72, 18);
                SetTopLeft(progRt, "BarBg", 18, 38, cw - 36, 10);
                SetTopLeft(progRt, "BarFill", 18, 38, cw - 36, 10);
                float nodeSpan = cw - 36 - 12;   // 06：节点中心 24..318（卡内），均分一行
                for (int i = 0; i < 12; i++)
                    SetTopLeft(progRt, "Node_" + i, 18 + nodeSpan * i / 11f, 64, 12, 12);
                SetTopCenter(progRt, "PieceText", 0, progH - 22, cw - 36, 12);

                var navRt = SetBottomLeft(home.transform, "BottomNav", L, navBottom, cw, m.NavHeight);
                for (int i = 0; i < 3; i++)
                {
                    var slot = navRt.Find("Slot_" + i) as RectTransform;
                    if (slot != null)
                    {
                        slot.anchorMin = new Vector2(i / 3f, 0);
                        slot.anchorMax = new Vector2((i + 1) / 3f, 1);
                        slot.offsetMin = Vector2.zero;
                        slot.offsetMax = Vector2.zero;
                    }
                }
            }

            // ---- Board（04 HUD + Docs/DesignSystem.md：棋盘 W-36 居中 / 提示 pill 220×26 / 工具条 342×104 吸底） ----
            GameObject board;
            if (screens.TryGetValue(BlockOutScreenId.Board, out board) && board != null)
            {
                var hud = board.transform.Find("TopHUD") as RectTransform;
                SetTopLeft(hud, "PauseBtn", L, T + 4, 44, 44);
                SetTopCenter(hud, "LevelTitle", 0, T + 2, 220, 22);
                SetTopCenter(hud, "LevelSub", 0, T + 24, 220, 14);
                SetTopRight(hud, "LivesRow", R, T + 10, 55, 15);
                SetTopRight(hud, "TimerPill", R, T + 9, 64, 20);
                SetTopRight(hud, "RemainingPill", R, T + 48, 110, 30);

                float toolbarH = m.ToolbarHeightCompact;   // v6: 全锁态 72；解锁后由 HudController 切到 104          // 固定 104（Docs/DesignSystem.md）
                float toolbarBottom = B;                   // 止于安全区上方
                const float PillH = 26f;                   // 提示 pill 固定高（Docs/DesignSystem.md）
                float boardTop = T + 116f;                 // HUD 第二行（剩余块胶囊）之下 38（04）
                float boardBottomLimit = H - toolbarBottom - toolbarH - 12f - PillH - 12f;
                float side = Mathf.Min(m.BoardSideByWidth, boardBottomLimit - boardTop);
                side = Mathf.Max(side, 120f);
                float centerY = (boardTop + boardBottomLimit) * 0.5f;
                var area = board.transform.Find("BoardArea") as RectTransform;
                if (area != null)
                {
                    area.anchorMin = new Vector2(0.5f, 0.5f);
                    area.anchorMax = new Vector2(0.5f, 0.5f);
                    area.pivot = new Vector2(0.5f, 0.5f);
                    area.sizeDelta = new Vector2(side, side);
                    area.anchoredPosition = new Vector2(0, H * 0.5f - centerY);
                }

                var hintPill = board.transform.Find("HintPill") as RectTransform;
                if (hintPill != null)
                {
                    hintPill.anchorMin = new Vector2(0.5f, 0.5f);
                    hintPill.anchorMax = new Vector2(0.5f, 0.5f);
                    hintPill.pivot = new Vector2(0.5f, 1);
                    hintPill.sizeDelta = new Vector2(220, PillH);
                    hintPill.anchoredPosition = new Vector2(0, H * 0.5f - (centerY + side * 0.5f + 12f));
                }

                var toolbar = board.transform.Find("BottomToolbar") as RectTransform;
                if (toolbar != null)
                {
                    toolbar.anchorMin = new Vector2(0, 0);
                    toolbar.anchorMax = new Vector2(0, 0);
                    toolbar.pivot = new Vector2(0, 0);
                    toolbar.sizeDelta = new Vector2(cw, toolbarH);   // Docs/DesignSystem.md：342×104（内容宽）
                    toolbar.anchoredPosition = new Vector2(L, toolbarBottom);
                    var slots = toolbar.Find("Slots") as RectTransform;
                    if (slots != null)
                    {
                        slots.anchorMin = Vector2.zero;
                        slots.anchorMax = Vector2.one;
                        slots.offsetMin = new Vector2(26, 0);       // 04：槽位中心 97/195/293
                        slots.offsetMax = new Vector2(-26, 0);
                    }
                }

                // 暂停/失败/确认/结算卡片随内容宽度自适应
                ClampCardWidth(layers, "PauseLayer", cw);
                ClampCardWidth(layers, "FailLayer", cw);
                ClampCardWidth(layers, "ConfirmLayer", cw);
                ClampCardWidth(layers, "SettlementLayer", cw);
                ClampCardWidth(layers, "SettingsLayer", cw);
            }

            // 关卡内容滚动，顶栏和底部导航固定；不压缩关卡触控面积。
            GameObject collection;
            if (screens.TryGetValue(BlockOutScreenId.Collection, out collection) && CollectionContent != null)
            {
                SetTopLeft(collection.transform, "BackBtn", L, T + 8, 44, 44);
                SetTopCenter(collection.transform, "Title", 0, T + 18, 160, 26);
                SetTopRight(collection.transform, "CoinPill", R, T + 12, 94, 30);
                float viewportTop = T + 64;
                float navTop = H - B - m.NavHeight;
                SetTopLeft(collection.transform, "ContentViewport", L, viewportTop, cw, Mathf.Max(80, navTop - viewportTop - 12));
                var content = CollectionContent;
                SetTopLeft(content, "SummaryCard", 0, 0, cw, 148);
                SetTopCenter(content, "EmptyText", 0, 162, cw, 20);
                SetTopLeft(content, "RetryBar", 0, 190, cw, 44);
                SetTopLeft(content, "ChapterLabel", 0, 250, 120, 20);
                int rows = 0;
                while (content.Find("ChapterRow_" + rows) != null)
                {
                    SetTopLeft(content, "ChapterRow_" + rows, 0, 280 + rows * 80, cw, 72);
                    rows++;
                }
                float repeatY = 280 + rows * 80 + 12;
                const float repeatH = 168;
                SetTopLeft(content, "RepeatCard", 0, repeatY, cw, repeatH);
                content.sizeDelta = new Vector2(cw, repeatY + repeatH + 12);
                SetBottomLeft(collection.transform, "BottomNav", L, B, cw, m.NavHeight);
                var summary = content.Find("SummaryCard");
                SetTopLeft(summary, "ThumbRoot", 12, 12, 120, 124);
                SetTopLeft(summary, "ChapterText", 144, 18, cw - 156, 14);
                SetTopLeft(summary, "ProgBg", 144, 38, cw - 156, 10);
                SetTopLeft(summary, "ProgFill", 144, 38, cw - 156, 10);
                SetTopLeft(summary, "PieceText", 144, 54, cw - 156, 12);
                SetTopLeft(summary, "ViewBigBtn", 144, 72, cw - 156, 44);
                SetTopLeft(summary, "BigNote", 144, 122, cw - 156, 12);
                LayoutArtwork(CollectionThumbRoot, false);
                var repeat = content.Find("RepeatCard") as RectTransform;
                LayoutRepeatCells(repeat, cw, repeatH);
                SetTopLeft(repeat, "RepeatNote", 12, repeatH - 24, cw - 24, 14);
                LayoutCollectionViewer(cw, H - T - B);
            }

            // ---- Store（15：顶部栏 + 三商品卡 + 说明 + 底部导航） ----
            GameObject store;
            if (screens.TryGetValue(BlockOutScreenId.Store, out store) && store != null)
            {
                SetTopLeft(store.transform, "BackBtn", L, T + 18, 36, 36);
                SetTopCenter(store.transform, "Title", 0, T + 36, 200, 26);
                SetTopRight(store.transform, "CoinPill", R, T + 18, 94, 30);
                for (int i = 0; i < 3; i++)
                    SetTopLeft(store.transform, "Product_" + (BlockOutToolId)(i), L, T + 48 + i * 124, cw, 112);
                SetTopLeft(store.transform, "CoinNote", L, T + 48 + 3 * 124 + 6, cw, 86);
                SetBottomLeft(store.transform, "BottomNav", L, B, cw, m.NavHeight);
                // 商品卡内部相对布局
                for (int i = 0; i < 3; i++)
                {
                    var card = store.transform.Find("Product_" + (BlockOutToolId)(i)) as RectTransform;
                    if (card == null) continue;
                    SetTopLeft(card, "IconBg", 16, 20, 48, 48);
                    SetTopLeft(card, "Icon", 26, 30, 28, 28);
                    SetTopLeft(card, "LockBadge", 48, 14, 20, 20);
                    SetTopLeft(card, "Name", 76, 14, cw - 92, 16);
                    SetTopLeft(card, "Desc", 76, 36, cw - 92, 32);
                    card.Find("Desc").GetComponent<Text>().horizontalOverflow = HorizontalWrapMode.Wrap;
                    SetTopLeft(card, "Coin", 76, 82, 14, 14);
                    SetTopLeft(card, "CoinText", 94, 80, 100, 18);
                    SetTopLeft(card, "BuyBtn", cw - 88, 68, 72, 44);
                }
            }

            LayoutFullPages(cw, H - T - B);

            // ---- Toast ----
            if (toastRect != null)
            {
                toastRect.anchorMin = new Vector2(0.5f, 0);
                toastRect.anchorMax = new Vector2(0.5f, 0);
                toastRect.pivot = new Vector2(0.5f, 0);
                toastRect.sizeDelta = new Vector2(Mathf.Min(460f, cw), 32);
                toastRect.anchoredPosition = new Vector2(0, m.SafeBottom + toastBottomOffset);
            }

            // BoardView 尺寸变化后重建（缓存引用，避免运行时查找）
            if (BoardView != null) BoardView.Rebuild();
        }
    }
}
#endif
