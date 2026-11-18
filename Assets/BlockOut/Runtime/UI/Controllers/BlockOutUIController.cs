using System;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;

namespace BlockOut.UI
{
    public sealed class BlockOutUIController : MonoBehaviour
    {
        internal BlockOutHomeController Home;
        internal BlockOutHudController Hud;
        internal BlockOutDialogsController Dialogs;
        internal BlockOutCollectionController Collection;
        internal BlockOutStoreController Store;
        private void Awake()
        {
            Home=new BlockOutHomeController(this);
            Hud=new BlockOutHudController(this);
            Dialogs=new BlockOutDialogsController(this);
            Collection=new BlockOutCollectionController(this);
            Store=new BlockOutStoreController(this);
        }
        public BlockOutUIManager UI;
        public BlockOutGameManager GM;

        // 章节插画（首页预览卡 / 收藏页共用；正式素材到位后仅替换资源路径）

        // 设置层返回路径：null = 首页；"PauseLayer" = 暂停层（返回后仍暂停）
        internal string settingsReturn;

        // 通用二次确认
        internal Action pendingConfirm;

        // 失败层状态机（广告加载中超时回退 300 金币）
        internal float failLayerOpenedAt = -1f;
        internal bool coinShortageToastDone;
        internal string lastReviveLabel;
        private float nextFailRefresh;

        // 首页 CTA 目标关卡索引（RefreshHomeCta 计算）
        internal int ctaTargetIndex;

        internal const float AdLoadFallbackSeconds = 2.5f;
        internal const string HintPillNormal = "轻点整块方块，沿箭头方向飞出";
        internal const string HintPillHammer = "点击任意方块消除 · 再点锤子取消";

        // 商店购买中状态（防重复点击 / 防重复扣币）
        internal readonly bool[] storePurchasing = new bool[3];
        // 收藏页当前展示的重复挑战章节
        internal int repeatChapter;
        internal int collectionChapter;

        internal static int StoreUnlockLevel(BlockOutToolId t)
        {
            if (t == BlockOutToolId.Hint) return BlockOutContentConfig.HintUnlockLevel;
            if (t == BlockOutToolId.Hammer) return BlockOutContentConfig.HammerUnlockLevel;
            return BlockOutContentConfig.MagicUnlockLevel;
        }
        internal static string StoreDesc(BlockOutToolId t)
        {
            if (t == BlockOutToolId.Hint) return "轮换高亮可飞块";
            if (t == BlockOutToolId.Hammer) return "消除任意在场块";
            return "自动飞出最多 " + BlockOutContentConfig.MagicTargetCount + " 个可飞块";
        }
        internal static int StoreIndex(BlockOutToolId t) => (int)t;

        void Start()
        {
            if (UI == null || GM == null)
            {
                Debug.LogError("[BlockOutUI] Controller missing UI or GM reference.");
                return;
            }
            UI.OnScreenChanged += HandleScreenChanged;
            UI.OnToastShown += HandleToastShown;
            UI.OnLayersChanged += Dialogs.SyncModalFlag;
            SubscribeGameEvents();
            WireButtons();
            StartCoroutine(BootSequence());
        }

        void Update()
        {
            if (UI != null && GM != null && Input.GetKeyDown(KeyCode.Escape)) HandleBack();
            // 失败层打开期间低频检查广告/金币状态，不依赖游戏计时。
            if (UI == null || GM == null || !UI.IsLayerActive("FailLayer")) return;
            // Lack of coins/readiness is temporary, not an exhausted revive entitlement.
            if (Time.unscaledTime < nextFailRefresh) return;
            nextFailRefresh = Time.unscaledTime + .25f;
            Dialogs.RefreshFailLayer();
        }

        private void HandleBack()
        {
            if (UI.IsLayerActive("AboutLayer")) { UI.AboutCloseBtn.onClick.Invoke(); return; }
            if (UI.IsLayerActive("ConfirmLayer")) { UI.ConfirmCancelBtn.onClick.Invoke(); return; }
            if (UI.IsLayerActive("GuideLayer")) { UI.GuideDismissBtn.onClick.Invoke(); return; }
            if (UI.IsLayerActive("SettingsLayer")) { UI.SettingsCloseBtn.onClick.Invoke(); return; }
            if (UI.IsLayerActive("PauseLayer")) { UI.PauseResumeBtn.onClick.Invoke(); return; }
            if (UI.IsLayerActive("FailLayer") || UI.IsLayerActive("SettlementLayer")) return;
            if (UI.CurrentScreen == BlockOutScreenId.Board) Dialogs.OpenPauseLayer();
            else if (UI.CurrentScreen != BlockOutScreenId.Home && UI.CurrentScreen != BlockOutScreenId.Loading) Home.GoHome();
        }

        // ============================================================
        // 启动序列
        // ============================================================

        internal IEnumerator BootSequence()
        {
            UI.ShowScreen(BlockOutScreenId.Loading);
            float t = 0f;
            while (GM.State == BlockOutGameState.Loading && t < 5f)
            {
                t += Time.deltaTime;
                yield return null;
            }
            yield return new WaitForSeconds(0.3f);

            // 恢复进行中局：仅当 GM 明确标记"启动前确实存在旧存档"时才直接进棋盘（P1-1）。
            // 绝不能用 Profile.HasActiveRun 判断——本次进程任何 LoadLevel 都会把它置 true，
            // 新用户冷启动会被误判为恢复对局而跳过首页。
            if (GM != null && GM.ResumeSavedRunOnBoot
                && (GM.State == BlockOutGameState.Ready
                    || GM.State == BlockOutGameState.Lost
                    || GM.State == BlockOutGameState.Won))
            {
                UI.ShowScreen(BlockOutScreenId.Board);
                HandleLevelLoaded(GM.CurrentLevel);
                Hud.RefreshCoins(GM.Profile.Coins);
                if (GM.State == BlockOutGameState.Lost) Dialogs.HandleLevelLost();
                // P1-6：恢复的空棋盘存档已完成结算 → 停在 Won，必须补开结算层，
                // 否则会掉进 GoHome() 把刚结算出来的界面顶掉。
                else if (GM.State == BlockOutGameState.Won) Dialogs.HandleLevelWon();
                yield break;
            }
            if(GM!=null && GM.Profile!=null && !GM.Profile.GuideCompleted && GM.CurrentLevelIndex==0) { EnterLevel(0);yield break; }
            Home.GoHome();
        }

        // ============================================================
        // 事件订阅
        // ============================================================

        internal void RefreshRemaining(int n)
        {
            if (UI.BoardRemainingText != null) UI.BoardRemainingText.text = "剩余 " + n + " 块";
            UpdateBoardProgress(n);
        }

        /// <summary>本关推进条：已飞块数 / 本关总块数（真实数据，不造百分比）。</summary>
        private int boardTotalBlocks = -1;

        internal void UpdateBoardProgress(int remaining)
        {
            if (boardTotalBlocks <= 0) return;
            float done = 1f - Mathf.Clamp01((float)remaining / boardTotalBlocks);
            if (UI.BoardProgressFill != null) BlockOutWidgets.SetProgressBar(UI.BoardProgressFill, done);
            if (UI.BoardProgressText != null) UI.BoardProgressText.text = Mathf.RoundToInt(done * 100f) + "%";
        }
        internal void SubscribeGameEvents()
        {
            GM.OnLevelLoaded += HandleLevelLoaded;
            GM.OnLivesChanged += Hud.RefreshHearts;
            GM.OnCoinsChanged += Hud.RefreshCoins;
            GM.OnRemainingBlocksChanged += RefreshRemaining;
            GM.OnTimeChanged += Hud.RefreshTimer;
            GM.OnToolStateChanged += Hud.RefreshToolStates;
            GM.OnStateChanged += Hud.RefreshToolStates;
            GM.OnPauseChanged += HandlePauseChanged;
            GM.OnAppForegrounded += HandleAppForegrounded;
            GM.OnLevelWinned += Dialogs.HandleLevelWon;
            GM.OnLevelLosed += Dialogs.HandleLevelLost;
            GM.OnSaveFailed += HandleSaveFailed;
            GM.OnBlockWrongMarked += Hud.OnBlockWrongMarked;
        }

        // ============================================================
        // 首页
        // ============================================================

        internal int HomeChapterIndex
        {
            get
            {
                int idx = GM.Profile != null ? GM.Profile.CurrentLevelIndex / BlockOutContentConfig.LevelsPerChapter : 0;
                int published = BlockOutContentConfig.PublishedChapters;
                return Mathf.Clamp(idx, 0, Mathf.Max(0, published - 1));
            }
        }



        internal void HandleToastShown() { GM.Settings.PlaySound("sfx_toast"); }

        internal void HandleScreenChanged(BlockOutScreenId screen)
        {
            Dialogs.SyncModalFlag();
            SetNav(UI.CollectionNavHomeBtn,false);SetNav(UI.CollectionNavCollectionBtn,true);SetNav(UI.CollectionNavStoreBtn,false);
            SetNav(UI.StoreNavHomeBtn,false);SetNav(UI.StoreNavCollectionBtn,false);SetNav(UI.StoreNavStoreBtn,true);
            if (GM != null) GM.Settings.PlayMusic(screen == BlockOutScreenId.Board ? "bgm_game" : "bgm_home");
        }

        private static void SetNav(Button button,bool selected)
        {
            if(button==null)return;
            if(button.targetGraphic is Image image)
            {
                image.sprite = BlockOutGardenSprites.Get(selected ? "button-green" : "button-cream");
                image.color = Color.white;
            }
            var label=button.GetComponentInChildren<Text>(true);
            if(label!=null)label.color=selected ? Color.white : BlockOutDesignTokens.TextCocoa;
        }

        internal void HandlePauseChanged(bool paused) { Hud.RefreshToolStates(); }

        internal void HandleAppForegrounded()
        {
            if (UI == null || GM == null) return;
            if (UI.CurrentScreen != BlockOutScreenId.Board) return;          // 首页/商店/收藏：保持现状
            if (!GM.IsPaused) return;
            if (UI.IsLayerActive("PauseLayer")) return;                    // 已经有暂停层
            if (UI.IsLayerActive("SettingsLayer") || UI.IsLayerActive("AboutLayer")) return;
            if (UI.IsLayerActive("ConfirmLayer")) return;
            if (UI.IsLayerActive("FailLayer") || UI.IsLayerActive("SettlementLayer")) return;
            UI.SetLayerActive("PauseLayer", true);
            Dialogs.SyncModalFlag();
            Hud.RefreshToolStates();
        }

        internal void HandleSaveFailed()
        {
            if (UI == null) return;
            UI.ShowToast(GM!=null && GM.HasPendingMagic ? "存档保存失败 · 点击魔法继续剩余目标，不重复扣道具" : "存档保存失败，请稍后重试");
        }

        internal void OnDestroy()
        {
            if (UI != null)
            {
                UI.OnScreenChanged -= HandleScreenChanged;
                UI.OnToastShown -= HandleToastShown;
                UI.OnLayersChanged -= Dialogs.SyncModalFlag;
            }
            if (GM == null) return;
            GM.OnLivesChanged -= Hud.RefreshHearts;
            GM.OnCoinsChanged -= Hud.RefreshCoins;
            GM.OnTimeChanged -= Hud.RefreshTimer;
            GM.OnBlockWrongMarked -= Hud.OnBlockWrongMarked;
            GM.OnRemainingBlocksChanged -= RefreshRemaining;
            GM.OnLevelLoaded -= HandleLevelLoaded;
            GM.OnToolStateChanged -= Hud.RefreshToolStates;
            GM.OnStateChanged -= Hud.RefreshToolStates;
            GM.OnPauseChanged -= HandlePauseChanged;
            GM.OnAppForegrounded -= HandleAppForegrounded;
            GM.OnLevelWinned -= Dialogs.HandleLevelWon;
            GM.OnLevelLosed -= Dialogs.HandleLevelLost;
            GM.OnSaveFailed -= HandleSaveFailed;
        }

        internal void EnterLevel(int index)
        {
            if (GM == null || GM.Profile == null || GM.Catalog == null || GM.Catalog.LevelCount == 0)
            {
                UI.ShowToast("关卡数据尚未就绪，请稍后重试");
                return;
            }
            if (GM.SettlementSaveFailed)
            {
                UI.ShowToast("请先重试保存，保留本次通关奖励");
                return;
            }
            int target = Mathf.Clamp(index, 0, Mathf.Max(0, GM.Catalog.LevelCount - 1));
            var targetLevel = GM.Catalog.GetLevel(target);
            if (targetLevel == null || targetLevel.Blocks == null || targetLevel.Blocks.Count == 0)
            {
                UI.ShowToast("该关卡暂时无法加载，请选择其他关卡");
                return;
            }
            if (target > GM.Profile.CurrentLevelIndex && !GM.Profile.IsLevelCompleted(targetLevel.Id))
            {
                UI.ShowToast("请先完成当前关卡");
                return;
            }
            // 进行中的局仅当与目标关卡一致时恢复（退出不保留本局，见 GiveUp）
            bool restore = false;
            if (GM.Profile.HasActiveRun && !string.IsNullOrEmpty(GM.Profile.RunLevelId))
            {
                for (int i = 0; i < GM.Catalog.LevelCount; i++)
                {
                    var lv = GM.Catalog.GetLevelMetadata(i);
                    if (lv != null && lv.Id == GM.Profile.RunLevelId) { restore = i == target; break; }
                }
            }
            UI.ShowScreen(BlockOutScreenId.Board);
            GM.Resume();
            GM.LoadLevel(target, restoreRun: restore);
        }

        // ============================================================
        // 游戏页 HUD
        // ============================================================

        internal void HandleLevelLoaded(BlockOutLevelData level)
        {
            if (UI.BoardLevelTitle != null) UI.BoardLevelTitle.text = GM.LevelTitleText;
            if (UI.BoardLevelSub != null) UI.BoardLevelSub.text = GM.LevelSubtitleText;

            // 生命 / 计时互斥（首发默认生命模式）
            bool timeMode = GM.UseTimeFailMode;
            if (UI.BoardTimerPill != null) UI.BoardTimerPill.gameObject.SetActive(timeMode);
            var firstHeart = UI.BoardHearts != null && UI.BoardHearts.Length > 0 ? UI.BoardHearts[0] : null;
            if (firstHeart != null && firstHeart.transform.parent != null)
                firstHeart.transform.parent.gameObject.SetActive(!timeMode);

            Hud.RefreshHearts(GM.Lives);
            Hud.RefreshTimer(GM.TimeRemaining);
            Hud.RefreshToolStates();
            Hud.RefreshHintPill();

            // 推进条基准：关卡加载时的剩余块数即本关总数
            boardTotalBlocks = Mathf.Max(1, level != null ? level.Blocks.Count : GM.RemainingBlocks);
            RefreshRemaining(GM.RemainingBlocks);
            var page=UI.GetScreenGO(BlockOutScreenId.Board);
            if(page!=null && page.activeInHierarchy)
            {
                var intro=page.GetComponent<BlockOutHudIntro>() ?? page.AddComponent<BlockOutHudIntro>();
                intro.Configure(UI,GM);intro.Play();
            }
            ShowGuideIfNeeded();
            Dialogs.SyncModalFlag();
        }

        internal void ShowGuideIfNeeded()
        {
            if (GM == null || GM.Profile == null || UI.BoardView == null || !UI.BoardView.gameObject.activeInHierarchy) return;
            if (UI.GuideLayer != null) UI.GuideLayer.SetActive(false);
            var guide=UI.BoardView.GetComponent<BlockOutBoardGuide>() ?? UI.BoardView.gameObject.AddComponent<BlockOutBoardGuide>();
            var page=UI.GetScreenGO(BlockOutScreenId.Board);
            guide.Configure(GM,UI.BoardView,page!=null ? page.GetComponent<BlockOutHudIntro>() : null);
            Dialogs.SyncModalFlag();
        }

        // ============================================================
        // 道具三态（未解锁 / 正常 / 数量为 0）
        // ============================================================

        internal static int ToolUnlockLevel(BlockOutToolId tool)
        {
            switch (tool)
            {
                case BlockOutToolId.Hint: return BlockOutContentConfig.HintUnlockLevel;
                case BlockOutToolId.Hammer: return BlockOutContentConfig.HammerUnlockLevel;
                default: return BlockOutContentConfig.MagicUnlockLevel;
            }
        }

        // ============================================================
        // 暂停 / 设置 / 二次确认
        // ============================================================

        // ============================================================
        // 失败 / 复活（阶段 C：不限次数——参考无单局上限；资格六态）
        // ============================================================

        // ============================================================
        // 胜利临时结算（可配置奖励表；章末结算接口预留）
        // ============================================================

        internal static void SetButtonLabel(Button btn,string text)
        {
            if(btn==null) return;
            var label=btn.GetComponentInChildren<Text>(true);
            if(label!=null) label.text=text;
        }

        // ============================================================
        // 按钮接线
        // ============================================================

        internal void WireButtons()
        {
            // ---- 首页 ----
            Bind(UI.HomeCtaButton, () =>
            {
                if (ctaTargetIndex < 0) return;
                EnterLevel(ctaTargetIndex);
            });
            Bind(UI.HomeSettingsBtn, () => Dialogs.OpenSettings(null));

            // R2 四个入口：图库/皮肤接到项目已有的 Collection/Store；每日与成就暂无页面，
            // 保留控件与点击反馈但不跳转，避免造出项目里不存在的功能。
            Bind(UI.HomeGalleryBtn, () => { collectionChapter=HomeChapterIndex; UI.ShowScreen(BlockOutScreenId.Collection); Collection.RefreshCollection(); });
            Bind(UI.HomeSkinBtn, () => { UI.ShowScreen(BlockOutScreenId.Store); Store.RefreshStore(); });
            Bind(UI.HomeCoinsButton, () => UI.ShowToast("通关可获得金币，用于补充道具和复活"));
            Bind(UI.HomeDailyBtn, null);
            Bind(UI.HomeAchievementBtn, null);

            // ---- 游戏页 HUD ----
            Bind(UI.BoardPauseBtn, Dialogs.OpenPauseLayer);

            // ---- 暂停层 ----
            Bind(UI.PauseResumeBtn, () =>
            {
                UI.SetLayerActive("PauseLayer", false);
                Dialogs.SyncModalFlag();
                GM.Resume();
            });
            Bind(UI.PauseRestartBtn, () => Dialogs.AskConfirm("重开本关？",
                "棋盘、生命与计时将重置；已消耗的道具与金币不返还，复活资格随重开重置。",
                () => { if (GM.TryRestartLevel()) UI.HideAllBoardLayers(); }));
            Bind(UI.PauseQuitBtn, () => Dialogs.AskConfirm("退出本关？",
                "本局进度不保留；通关记录、金币与道具库存保留。",
                () => { if (GM.TryGiveUp()) { UI.HideAllBoardLayers(); Home.GoHome(); } }));
            Bind(UI.PauseSettingsBtn, () => Dialogs.OpenSettings("PauseLayer"));

            // ---- 失败层 ----
            Bind(UI.FailReviveBtn, Dialogs.OnReviveClicked);
            Bind(UI.FailRestartBtn, () => Dialogs.AskConfirm("重开本关？",
                "棋盘、生命与计时将重置；已消耗的道具与金币不返还，复活资格随重开重置。",
                () => { if (GM.TryRestartLevel()) UI.HideAllBoardLayers(); }));
            Bind(UI.FailQuitBtn, () => Dialogs.AskConfirm("退出本关？",
                "本局进度不保留；通关记录、金币与道具库存保留。",
                () => { if (GM.TryGiveUp()) { UI.HideAllBoardLayers(); Home.GoHome(); } }));

            // ---- 通用确认层 ----
            Bind(UI.ConfirmCancelBtn, () =>
            {
                pendingConfirm = null;
                UI.SetLayerActive("ConfirmLayer", false);
                Dialogs.SyncModalFlag();
            });
            Bind(UI.ConfirmOkBtn, () =>
            {
                UI.HideLayerImmediately("ConfirmLayer");
                Dialogs.SyncModalFlag();
                var action = pendingConfirm;
                pendingConfirm = null;
                if (action != null) action();
            });

            // ---- 胜利临时结算 ----
            Bind(UI.SettleNextBtn, () =>
            {
                if(GM.SettlementSaveFailed) { GM.RetrySettlement(); return; }
                int next = GM.CurrentLevelIndex + 1;
                var nextLevel = next < GM.Catalog.LevelCount ? GM.Catalog.GetLevelMetadata(next) : null;
                if (nextLevel != null && BlockOutContentConfig.IsChapterPublished(nextLevel.Chapter)
                    && GM.Catalog.HasChapterData(nextLevel.Chapter)) EnterLevel(next);
                else Home.GoHome();
            });
            Bind(UI.SettleReplayBtn, () =>
            {
                if (GM.SettlementSaveFailed) { UI.ShowToast("请先重试保存，保留本次通关奖励"); return; }
                if (GM.TryRestartLevel()) UI.HideAllBoardLayers();
            });
            Bind(UI.SettleCollectionBtn, () =>
            {
                if (GM.SettlementSaveFailed) { UI.ShowToast("请先重试保存，保留本次通关奖励"); return; }
                // 查看收藏：切到收藏页查看关卡进度（返回路径由收藏页导航处理）
                UI.HideAllBoardLayers();
                collectionChapter = GM.CurrentLevel.Chapter;
                UI.ShowScreen(BlockOutScreenId.Collection);
                Collection.RefreshCollection();
            });
            Bind(UI.SettleHomeBtn, () =>
            {
                if (GM.SettlementSaveFailed) { UI.ShowToast("请先重试保存，保留本次通关奖励"); return; }
                UI.HideAllBoardLayers();
                Home.GoHome();
            });

            // ---- 设置层（画布级） ----
            Bind(UI.SettingsMusicSwitch, () =>
            {
                GM.Settings.MusicOn = !GM.Settings.MusicOn;
                BlockOutWidgets.SetSwitch(UI.SettingsMusicSwitch, GM.Settings.MusicOn);
            });
            Bind(UI.SettingsSoundSwitch, () =>
            {
                GM.Settings.SoundOn = !GM.Settings.SoundOn;
                BlockOutWidgets.SetSwitch(UI.SettingsSoundSwitch, GM.Settings.SoundOn);
            });
            Bind(UI.SettingsVibSwitch, () =>
            {
                GM.Settings.VibrationOn = !GM.Settings.VibrationOn;
                BlockOutWidgets.SetSwitch(UI.SettingsVibSwitch, GM.Settings.VibrationOn);
            });
            Bind(UI.SettingsCloseBtn, () =>
            {
                UI.SetLayerActive("SettingsLayer", false);
                Dialogs.SyncModalFlag();
                // 从暂停层进入 → 返回暂停层（保持暂停）；从首页进入 → 留在首页
                if (settingsReturn == "PauseLayer") UI.SetLayerActive("PauseLayer", true);
            });
            // ---- 关于（16 稿）：设置页二级弹层，关闭后回设置页 ----
            Bind(UI.SettingsAboutBtn, () =>
            {
                UI.SetLayerActive("AboutLayer", true);
                UI.HideLayerImmediately("SettingsLayer");
            });
            Bind(UI.AboutCloseBtn, () =>
            {
                UI.SetLayerActive("SettingsLayer", true);
                UI.SetLayerActive("AboutLayer", false);
            });

            // ---- 道具（统一走 TryUseTool：解锁/库存/暂停/忙碌先判定，再执行）----
            Bind(UI.HintSlot != null ? UI.HintSlot.Button : null, () =>
            {
                Hud.TryUseTool(BlockOutToolId.Hint, () => GM.UseHint() != null);
            });
            Bind(UI.HammerSlot != null ? UI.HammerSlot.Button : null, () =>
            {
                Hud.TryUseTool(BlockOutToolId.Hammer, () => GM.EnterHammerMode(),
                    () => { GM.CancelHammerMode(); return true; });
            });
            Bind(UI.MagicSlot != null ? UI.MagicSlot.Button : null, () =>
            {
                Hud.TryUseTool(BlockOutToolId.Magic, () => GM.UseMagic() > 0);
            });

            // ---- 商店（15：三商品购买 + 底部导航） ----
            Bind(UI.StoreBackBtn, Home.GoHome);
            Bind(UI.StoreNavHomeBtn, Home.GoHome);
            Bind(UI.StoreNavCollectionBtn, () => { collectionChapter=HomeChapterIndex; UI.ShowScreen(BlockOutScreenId.Collection); Collection.RefreshCollection(); });
            Bind(UI.StoreNavStoreBtn, null);
            if (UI.StoreProducts != null)
                for (int i = 0; i < UI.StoreProducts.Length; i++)
                {
                    int idx = i;
                    Bind(UI.StoreProducts[i] != null ? UI.StoreProducts[i].BuyBtn : null, () => Store.OnStoreBuyClicked(idx));
                }

            // ---- 收藏（14：返回 + 导航 + 查看大图 + 大图关闭 + 重复挑战网格） ----
            Bind(UI.CollectionBackBtn, Home.GoHome);
            Bind(UI.CollectionNavHomeBtn, Home.GoHome);
            Bind(UI.CollectionNavCollectionBtn, () => { UI.ShowScreen(BlockOutScreenId.Collection); Collection.RefreshCollection(); });
            Bind(UI.CollectionNavStoreBtn, () => { UI.ShowScreen(BlockOutScreenId.Store); Store.RefreshStore(); });


            // ---- 新手引导（首次进入第 1 关弹出，关闭后写入存档） ----
            Bind(UI.GuideDismissBtn, () =>
            {
                if(GM.Profile==null || !GM.CommitProfileMutation(()=>GM.Profile.GuideCompleted=true)) return;
                if (UI.GuideLayer != null) UI.GuideLayer.SetActive(false);
                Dialogs.SyncModalFlag();
            });
        }

        internal void Bind(Button btn, Action action)
        {
            if (btn == null) return;
            btn.onClick.RemoveAllListeners();
            btn.onClick.AddListener(() =>
            {
                GM.Settings.PlaySound("sfx_ui_tap");
                if (action != null) action();
            });
        }

        // ============================================================
        // 收藏 / 商店（数据绑定；布局待 14/15 修订稿）
        // ============================================================

        internal GameObject CollectionScreen => UI.GetScreenGO(BlockOutScreenId.Collection);

    }
}
