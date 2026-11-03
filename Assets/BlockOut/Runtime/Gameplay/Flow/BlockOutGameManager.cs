using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Config;
using BlockOut.Contracts;
using BlockOut.Core;
using BlockOut.Infrastructure.Ads;

namespace BlockOut.Gameplay
{
    /// <summary>
    /// 集成游戏管理器：目录 / 规则 / 棋盘视图 / 道具 / 结算 / 连击 / 特殊块 / 设置 / 引导 / 存档恢复。
    /// v5 规则：全局递增关号（第一章 1-12 / 第二章 13-24）；生命模式默认（3 心），
    /// 倒计时模式默认关闭（远程开关键 use_time_fail_mode，旧键 ArtOutUseTimeFailMode 兼容读取，
    /// 见 BlockOutRemoteConfigBridge），HUD 互斥；
    /// 复活上限由配置决定；次数随对局保存，0 表示不限次。
    /// </summary>
    public sealed class BlockOutGameManager : MonoBehaviour
    {
        private BlockOutLevelFlow levelFlow;
        internal BlockOutLevelFlow LevelFlow => levelFlow ?? (levelFlow=new BlockOutLevelFlow(this));
        private BlockOutReviveFlow reviveFlow;
        internal BlockOutReviveFlow ReviveFlow => reviveFlow ?? (reviveFlow=new BlockOutReviveFlow(this));
        private BlockOutSettlementFlow settlementFlow;
        internal BlockOutSettlementFlow SettlementFlow => settlementFlow ?? (settlementFlow=new BlockOutSettlementFlow(this));

        [Header("References (assign in Inspector)")]
        public BlockOutBoardView boardView;

        // Core
        public BlockOutCatalog Catalog { get; internal set; }
        public BlockOutGameRules Rules { get; internal set; }
        public BlockOutPlayerProfile Profile { get; internal set; }

        // Systems
        public BlockOutToolController Tools { get; internal set; }
        public BlockOutSettlement Settlement { get; internal set; }
        public BlockOutSettings Settings { get; internal set; }
        public BlockOutGuideSystem Guide { get; internal set; }
        public BlockOutComboSystem Combo { get; internal set; }
        public BlockOutSpecialBlockSystem Specials { get; internal set; }
        public BlockOutAssemblyManager Assembly { get; internal set; }

        // Services
        public IAdProvider Ads { get; internal set; }

        /// <summary>集中存档服务（R09/R13）。由 Bootstrap 注入；未注入时退回档案直存（兼容旧装配）。</summary>
        public BlockOut.Infrastructure.Persistence.BlockOutSaveService SaveService { get; internal set; }

        /// <summary>
        /// 服务注入（R09）：由 Bootstrap 在 AddComponent 之后、Start 之前调用。
        /// 不改变任何玩法，只把"广告实现/存档读写"从 GameManager 里拆出去。
        /// </summary>
        public void BindServices(IAdProvider ads, BlockOut.Infrastructure.Persistence.BlockOutSaveService saveService)
        {
            if (ads != null) Ads = ads;
            if (saveService != null)
            {
                SaveService = saveService;
                Profile = saveService.Profile ?? Profile;
                // R09/R13/C06：所有档案消费者必须跟着服务档案走，否则设置/引导/收藏
                // 会写到 Awake 时的旧对象上，被服务档案的整体落盘覆写（数据丢失）。
                if (Settlement != null) Settlement.BindProfile(Profile);
                if (Settings != null) { Settings.BindProfile(Profile); Settings.BindCommit(CommitProfileMutation); }
                if (Guide != null) { Guide.BindProfile(Profile); Guide.BindCommit(CommitProfileMutation); }
                if (Assembly != null) Assembly.BindProfile(Profile);
            }
        }

        /// <summary>统一保存入口：有存档服务走服务（可感知失败），否则退回档案直存。</summary>
        internal bool SaveProfile()
        {
            // C01：Profile.Save() 返回 void，不能用于 bool 表达式；直存路径用 TrySave()。
            return SaveService != null ? SaveService.Save() : (Profile != null && Profile.TrySave());
        }

        internal bool TrySaveProfile()
        {
            return SaveService != null ? SaveService.TrySave() : (Profile != null && Profile.TrySave());
        }

        /// <summary>
        /// 档案变更提交（C07）：mutate 只改内存，提交走存档事务——
        /// 有服务时失败自动回滚内存档案与存储缓存；无服务（旧装配）退回直存并返回 false。
        /// 购买/复活/结算/道具消耗统一走这里，禁止"扣了没存/存了没扣"的半成功状态。
        /// </summary>
        internal bool CommitProfileChange(Action mutate)
        {
            if (mutate == null || Profile == null) return false;
            if (SaveService != null)
            {
                using (var tx = SaveService.BeginTransaction())
                {
                    mutate();
                    return tx.Commit();
                }
            }
            string before=JsonUtility.ToJson(Profile);
            try { mutate(); if(TrySaveProfile()) return true; }
            catch(Exception e) { Debug.LogError("[BlockOut] 保存变更失败: "+e.Message); }
            JsonUtility.FromJsonOverwrite(before,Profile);
            // Restore PlayerPrefs cache as well as the live profile in the compatibility path.
            Profile.TrySave();
            return false;
        }

        /// <summary>N07：UI/设置等经统一存档入口提交档案变更（事务 + 失败回滚 + OnSaveFailed 通知）。
        /// 禁止 UI 直接调用 Profile.Save 绕过统一保存与错误处理。</summary>
        public bool CommitProfileMutation(Action mutate)
        {
            bool success=CommitProfileChange(mutate);
            if(!success) OnSaveFailed?.Invoke();
            return success;
        }

        internal void EmitOnStateChanged() { OnStateChanged?.Invoke(); }
        internal void EmitOnLivesChanged(int arg0) { OnLivesChanged?.Invoke(arg0); }
        internal void EmitOnCoinsChanged(int arg0) { OnCoinsChanged?.Invoke(arg0); }
        internal void EmitOnComboChanged(int arg0) { OnComboChanged?.Invoke(arg0); }
        internal void EmitOnLevelWinned() { OnLevelWinned?.Invoke(); }
        internal void EmitOnLevelLosed() { OnLevelLosed?.Invoke(); }
        internal void EmitOnBlockRemovedVisual(BlockOutBlockData arg0) { OnBlockRemovedVisual?.Invoke(arg0); }
        internal void EmitOnBlockWrongMarked(BlockOutBlockData arg0, bool arg1) { OnBlockWrongMarked?.Invoke(arg0, arg1); }
        internal void EmitOnRemainingBlocksChanged(int arg0) { OnRemainingBlocksChanged?.Invoke(arg0); }
        internal void EmitOnTimeChanged(float arg0) { OnTimeChanged?.Invoke(arg0); }
        internal void EmitOnToolStateChanged() { OnToolStateChanged?.Invoke(); }
        internal void EmitOnPauseChanged(bool arg0) { OnPauseChanged?.Invoke(arg0); }
        internal void EmitOnAppForegrounded() { OnAppForegrounded?.Invoke(); }
        internal void EmitOnReviveStateChanged() { OnReviveStateChanged?.Invoke(); }
        internal void EmitOnLevelLoaded(BlockOutLevelData arg0) { OnLevelLoaded?.Invoke(arg0); }
        internal void EmitOnSaveFailed() { OnSaveFailed?.Invoke(); }

        // State
        public BlockOutGameState State { get; internal set; }
        public bool IsPaused { get; internal set; }
        public int CurrentLevelIndex { get; internal set; }
        public BlockOutLevelData CurrentLevel { get; internal set; }

        /// <summary>在途飞出计数（§4.2.2）：每块动画独立登记，普通飞出不锁整盘输入。
        /// 胜机判定（<see cref="MaybeWin"/>）要求计数归零，保证"最后一块动画播完才结算"。</summary>
        internal int inFlightFlyOuts;

        /// <summary>倒计时是否已开始（参考 timerStarted）。未开始时须先过 CanStartTimeFailTimer 全条件。</summary>
        internal bool timerStarted;
        /// <summary>倒计时到期失败是否已展示（参考 timerExpiredFailShown）：避免重复弹失败层/重复扣结算。</summary>
        internal bool timeExpiredFailShown;
        /// <summary>应用是否聚焦（参考 applicationFocused）：切后台冻结计时。</summary>
        internal bool applicationFocused = true;
        /// <summary>广告是否正在展示（参考 adDisplayActive）：本地无广告接入，恒 false，保留条件对齐。</summary>
        internal bool adDisplayActive;
        /// <summary>模态弹窗是否打开（参考 IsModalPopupOpen：暂停/失败/胜利/设置/引导层）。
        /// 由 UI 层在弹窗开闭时同步；计时启动与流逝都要求无模态弹窗。</summary>
        internal bool modalPopupOpen;
        public bool ModalPopupOpen
        {
            get => modalPopupOpen;
            set { modalPopupOpen=value; if(boardView!=null) { boardView.SetInputLock(BlockOutInputLock.Modal,value); boardView.SetPresentationPaused(IsPaused || value); } }
        }

        // Config（远程开关占位：首发默认生命模式）
        /// <summary>新挑战的默认失败模式（配置/远程开关来源）。新建对局时才应用，
        /// 进行中对局一律以存档记录的 <see cref="UseTimeFailMode"/> 为准，避免互相污染。</summary>
        public bool ConfigUseTimeFailMode = false;   // 兼容旧引用占位（实际以 BlockOutContentConfig.UseTimeFailModeDefault 为准，见 LoadLevel）
        /// <summary>当前进行中对局实际生效的失败模式。恢复存档时按存档双向恢复（0→false，1→true）。</summary>
        public bool UseTimeFailMode = false;
        public float GameTimeSeconds = 120f;
        internal float timeRemaining;
        internal int lastDisplayedSecond = -1;
        /// <summary>本局由存档恢复为失败态（倒计时归零等）。为 true 时必须保持失败层，
        /// 不得按 Ready 恢复可操作状态，否则等于绕过失败与复活规则（P1-3）。</summary>
        internal bool restoredLost;

        /// <summary>P1-6：恢复的存档里规则层已无在场方块（已满足胜利条件但结算未完成）。
        /// 由 <see cref="CompletePendingWin"/> 在建局收尾时走一次完整结算，而不是恢复成空棋盘 Ready。
        /// 防重复：结算走的是与 <see cref="OnLevelWon"/> 相同的标记 + ClearActiveRun 路径，
        /// 且 MarkLevelCompleted / CurrentLevelIndex 均为幂等写法，重进不会二次发奖。</summary>
        internal bool pendingWinRestore;

        /// <summary>当前是否持有"有效进行中对局"。为 false 时（未开局 / 已通关 / 已放弃）
        /// 任何路径都不得再写回 HasActiveRun——否则失败后退出 → 回首页 → Pause() 会把
        /// 已放弃的对局重新存回 PlayerPrefs，下次启动又被当成"恢复旧局"（P1-5）。</summary>
        internal bool runPlayable;

        /// <summary>本局是否仍可操作（UI 延迟弹层时据此放弃已失效的弹层，如延迟期间放弃/重开）。</summary>
        public bool IsRunPlayable => runPlayable;

        /// <summary>本次暂停是否由"切后台/失焦"触发。仅用于回到前台时弹出暂停层；
        /// 玩家自己点的暂停不置位，回前台不得无条件替他恢复（P1-2）。</summary>
        internal bool pausedByAppBackground;

        // Events for UI layer
        public event Action OnStateChanged;
        public event Action<int> OnLivesChanged;
        public event Action<int> OnCoinsChanged;
        public event Action<int> OnComboChanged;
        public event Action OnLevelWinned;
        public event Action OnLevelLosed;
        public event Action<BlockOutBlockData> OnBlockRemovedVisual;
        public event Action<BlockOutBlockData, bool> OnBlockWrongMarked;
        public event Action<int> OnRemainingBlocksChanged;
        public event Action<float> OnTimeChanged;
        public event Action OnToolStateChanged;
        public event Action<bool> OnPauseChanged;
        /// <summary>由"切后台/失焦"暂停的对局，在回到前台时触发一次。
        /// UI 订阅它来决定是否补开暂停层（P1-2）；玩家主动暂停不会触发。</summary>
        public event Action OnAppForegrounded;
        public event Action OnReviveStateChanged;
        public event Action<BlockOutLevelData> OnLevelLoaded;
        /// <summary>档案保存失败（事务已回滚）。UI 据此提示"存档失败"，不得显示已成功（C07）。</summary>
        public event Action OnSaveFailed;
        /// <summary>本次胜利是否已成功提交（R06：避免重复结算/重复发奖）。</summary>
        internal bool settlementCommitted;
        /// <summary>结算保存是否失败（R06：UI 据此展示"未保存"并禁止进入下一关，提供重试）。</summary>
        public bool SettlementSaveFailed { get; internal set; }

        // Revive eligibility (per challenge; reset on load/restart/give-up)
        public bool ReviveUsedThisRun { get; internal set; }
        /// <summary>本局已复活次数（R02：limitPerRun>0 时作为每局上限；0=不限制）。</summary>
        internal int reviveCountThisRun;
        public string LastFailReason { get; internal set; } = "生命耗尽";
        public int LastRewardCoins { get; internal set; }

        /// <summary>最近一次通关是否为首通（用于结算区分首通/重复奖励文案与章末提示）。</summary>
        public bool LastWinWasFirstClear { get; internal set; }

        /// <summary>商店购买结果（本地金币事务，无服务端确认，原型边界）。</summary>
        public enum BlockOutPurchaseResult { Ok, Locked, InsufficientCoins, Failed }

        internal bool magicRunning;
        internal Coroutine magicSequence;
        internal readonly List<Coroutine> magicArrivals=new List<Coroutine>();
        internal readonly List<int> pendingMagicTargets=new List<int>();
        public bool HasPendingMagic => pendingMagicTargets.Count>0;
        public bool CanStartTool => runPlayable && State==BlockOutGameState.Ready && !IsPaused && !ModalPopupOpen
            && !GuideInputActive && !magicRunning && inFlightFlyOuts==0 && (boardView==null || !boardView.IsInputLocked);
        private sealed class MagicCast { public int Pending; public bool Failed; }
        internal IEnumerator ResumePendingMagicAfterEntrance(int token)
        {
            while(token==activeRunToken && HasPendingMagic && !CanStartTool)yield return null;
            if(token==activeRunToken && HasPendingMagic)UseMagic();
        }
        internal bool reviveAdPending;
        internal int activeRunToken;
        public int ActiveRunToken => activeRunToken;

        /// <summary>本次启动是否真的要恢复"启动前已存在"的旧对局（P1-1）。
        /// 绝不能用初始化后的 HasActiveRun 判断：本进程任何 LoadLevel 都会把它置 true。</summary>
        public bool ResumeSavedRunOnBoot { get; internal set; }

        /// <summary>当前是否处于"结算/施法/切关"的不可操作期（P1-9 统一操作锁，UI 与 GM 共用）。</summary>
        public bool GuideInputActive { get; set; }
        public BlockOutBlockData GuideTarget { get; set; }
        public bool HasFlyingBlocks => inFlightFlyOuts > 0;
        public bool IsBusyResolving => magicRunning || State == BlockOutGameState.ResolvingMove;

        void Awake()
        {
            Catalog = new BlockOutCatalog();
            Rules = new BlockOutGameRules();
            // R09/R13：存档由集中服务管理；Bootstrap 会在 BindServices 时覆盖为服务档案。
            Profile = BlockOutPlayerProfile.Load();
            SaveService = null;
            // R09：广告实现由 Bootstrap 注入；未注入时用空实现（绝不默认启用模拟广告）。
            Ads = new BlockOut.Infrastructure.Ads.BlockOutNullAdProvider();
            Settings = new BlockOutSettings(Profile, transform);
            Settlement = new BlockOutSettlement(Profile);
            Combo = new BlockOutComboSystem();
            Combo.OnComboChanged += (c) => OnComboChanged?.Invoke(c);
            Specials = new BlockOutSpecialBlockSystem(Rules);
            Assembly = new BlockOutAssemblyManager(Profile);
            Guide = new BlockOutGuideSystem(Profile);
            State = BlockOutGameState.Loading;
        }

        void Start()
        {
            Catalog.Load();
            Ads.Init();

            // 恢复"启动前就已存在"的进行中对局（须在本次启动任何建局动作之前判定）。
            // 校验 levelId + blockCount + hash 任一不符即视为无存档，按新用户冷启动进首页。
            ResumeSavedRunOnBoot = false;
            if (Profile.HasActiveRun && !string.IsNullOrEmpty(Profile.RunLevelId))
            {
                int idx = FindLevelIndexById(Profile.RunLevelId);
                if (idx >= 0)
                {
                    var savedLevel = Catalog.GetLevel(idx);
                    ResumeSavedRunOnBoot = savedLevel != null
                        && Profile.RunBlockCount == savedLevel.Blocks.Count
                        && Profile.RunLevelHash == BlockOutSolver.ComputeLevelHash(savedLevel);
                    if (!ResumeSavedRunOnBoot) { Profile.ClearActiveRun(); SaveProfile(); }
                    if (ResumeSavedRunOnBoot) { LoadLevel(idx, restoreRun: true); return; }
                }
                Profile.ClearActiveRun();
                SaveProfile();
            }

            // 无存档：仅初始化到进度关卡，**不建对局、不写 HasActiveRun**（P1-1）。
            // 对局由玩家点击 CTA / 进入关卡时才创建，避免新用户被误判为"恢复旧局"而跳过首页。
            CurrentLevelIndex = Mathf.Clamp(Profile.CurrentLevelIndex, 0, Mathf.Max(0, Catalog.LevelCount - 1));
            CurrentLevel = Catalog.GetLevel(CurrentLevelIndex);
            State = BlockOutGameState.Ready;
        }

        internal int FindLevelIndexById(string id)
        { return LevelFlow.FindLevelIndexById(id); }

        // ---- v5 编号与章节 ----

        /// <summary>全局关号（1 起，第一章 1-12 / 第二章 13-24）。</summary>
        public int CurrentLevelNumber => CurrentLevelIndex + 1;

        /// <summary>章节号（1 起）。</summary>
        public int CurrentChapterNumber => (CurrentLevel != null ? CurrentLevel.Chapter : 0) + 1;

        /// <summary>章内序号 K（第二章起副题加注"本章第 K 关"）。</summary>
        public int LevelWithinChapter => (CurrentLevelIndex % BlockOutContentConfig.LevelsPerChapter) + 1;

        public string LevelTitleText
        {
            get { return "第 " + CurrentChapterNumber + " 章 · 第 " + CurrentLevelNumber + " 关"; }
        }

        public string LevelSubtitleText
        {
            get
            {
                string theme = BlockOutContentConfig.ChapterThemeName(CurrentChapterNumber - 1);
                if (CurrentChapterNumber >= 2)
                    return theme + " · 本章第 " + LevelWithinChapter + " 关";
                return theme;
            }
        }

        /// <summary>道具解锁判断用的实际进度（回玩低关不误判为重新锁定）。</summary>
        public int EffectiveLevelNumber
        {
            get { return Mathf.Max(CurrentLevelNumber, Mathf.Max(1, Profile.MaxLevelReached)); }
        }

        public bool IsToolUnlocked(BlockOutToolId tool)
        {
            int unlockLevel = tool == BlockOutToolId.Hint ? BlockOutContentConfig.HintUnlockLevel
                : tool == BlockOutToolId.Hammer ? BlockOutContentConfig.HammerUnlockLevel
                : BlockOutContentConfig.MagicUnlockLevel;
            return EffectiveLevelNumber >= unlockLevel;
        }

        public int Lives => Rules != null ? Rules.Lives : 0;
        public int RemainingBlocks => Rules != null ? Rules.RemainingBlocks : 0;
        public float TimeRemaining => timeRemaining;
        public int ChapterCompletedCount
        {
            get { return Catalog.GetCompletedCountInChapter(CurrentLevel != null ? CurrentLevel.Chapter : 0, Profile); }
        }

        public bool IsCurrentChapterComplete
        {
            get { return CurrentLevel!=null && ChapterCompletedCount >= Catalog.ChapterLevelCount(CurrentLevel.Chapter); }
        }

        // ---- 关卡加载 ----

        public void LoadLevel(int index, bool restoreRun = false)
        { LevelFlow.LoadLevel(index,restoreRun); }

        /// <summary>P1-6：完成"恢复自空棋盘存档"的通关结算。
        /// 复用 <see cref="OnLevelWon"/> 的全部逻辑（标记通关、发金币、推进主线、拼片、清存档），
        /// 因此奖励/拼片/关卡推进与正常通关完全一致，且同样只执行一次：
        /// <see cref="Profile.MarkLevelCompleted"/> 内部 Contains 去重、
        /// CurrentLevelIndex 取 Max、结算结束 ClearActiveRun 让存档失效。</summary>
        internal void CompletePendingWin()
        { LevelFlow.CompletePendingWin(); }

        /// <summary>把当前对局状态写入 Profile 字段（不落盘）。事务内复用，避免重复保存（R05/R07）。</summary>
        internal void WriteActiveRunToProfile()
        { LevelFlow.WriteActiveRunToProfile(); }

        internal void SaveActiveRun()
        { LevelFlow.SaveActiveRun(); }

        // ---- 点击处理 ----

        internal void OnBoardBlockTapped(BlockOutBlockData block)
        {
            HandleBlockTapped(block);
        }

        /// <summary>Player tapped a block.
        /// 连续点击语义（对齐参考 OnBlockClicked，文档 §4.2）：
        /// 成功点击**立即逻辑移除**（rules.Remove）并禁用目标命中，再启动独立飞出协程；
        /// 普通飞出不锁整盘输入，同一块因 Active=false 不可能重复提交；
        /// 最后一块逻辑移除后停在 Ready 等所有在途飞出完成，再由 <see cref="MaybeWin"/> 统一结算。</summary>
        public BlockOutMoveResult HandleBlockTapped(BlockOutBlockData block)
        {
            var rejected = new BlockOutMoveResult(false,false,false);
            if (!runPlayable || State!=BlockOutGameState.Ready || block==null || !block.Active || IsPaused
                || ModalPopupOpen || HasPendingMagic || (boardView!=null && boardView.IsInputLocked)) return rejected;
            if(GuideInputActive && block!=GuideTarget)return rejected;
            Settings.PlaySound("sfx_tap_block");
            if (Tools!=null && Tools.Mode==BlockOutToolMode.Hammer)
            {
                List<BlockOutBlockData> removed;
                if(!TryCommitRemoval(new[]{block}, () => Tools.TryHammerRemove(block), true, out removed)) return rejected;
                inFlightFlyOuts++;
                boardView?.SetInputLock(BlockOutInputLock.Tool,true);
                StartCoroutine(HammerImpactRoutine(removed,activeRunToken));
                return new BlockOutMoveResult(true,false,false);
            }
            if(BlockOutContentConfig.EnableSpecialBlocks && Specials!=null && Specials.IsBlockedByFrozen(block)) return rejected;
            if(Rules.CanMove(block))
            {
                List<BlockOutBlockData> removed;
                if(!TryCommitRemoval(new[]{block}, null, true, out removed)) return rejected;
                StartCommittedFlyouts(removed);
                Guide.OnPlayerAction();
                return new BlockOutMoveResult(true,false,false);
            }
            var before=Rules.CaptureRunProgress(CurrentLevel.Id, "");
            var result=Rules.TryTap(block,!UseTimeFailMode);
            if(!PersistProgressAndTools())
            {
                Rules.ApplyRunProgress(before); OnSaveFailed?.Invoke(); return rejected;
            }
            FeedbackWrongTap(block,result.AlreadyMarked);
            if(Rules.IsLost) OnLevelLost();
            return result;
        }

        /// <summary>锤子命中音效延迟（§7.3，参考 0.35s；2.1s 特效寿命不等于锁输入 2.1s）。
        /// 携带对局令牌：重开/切关/退出后不再播放延迟锤声（R10）。</summary>
        internal IEnumerator HammerImpactRoutine(List<BlockOutBlockData> removed,int token)
        {
            foreach(var block in removed)
            {
                if(boardView==null)continue;
                boardView.PlayHammerEffect(block);
                boardView.RemoveInstant(block);
            }
            yield return WaitForPresentation(BlockOutGameplayConfig.Current.feel.hammerImpactSoundDelay,token);
            if(token!=activeRunToken)yield break;
            Settings.PlaySound("sfx_hammer");
            foreach(var block in removed)boardView?.RemoveInstant(block);
            boardView?.SetInputLock(BlockOutInputLock.Tool,false);
            inFlightFlyOuts=Mathf.Max(0,inFlightFlyOuts-1);MaybeWin();
        }

        internal IEnumerator WaitForPresentation(float seconds, int token)
        {
            float elapsed=0;
            while(elapsed<seconds && token==activeRunToken)
            {
                if(!IsPaused && !ModalPopupOpen) elapsed+=Time.deltaTime;
                yield return null;
            }
        }

        internal void StartCommittedFlyouts(List<BlockOutBlockData> removed)
        {
            int token=activeRunToken;
            inFlightFlyOuts+=removed.Count;
            foreach(var block in removed)
            {
                if(boardView!=null) boardView.FlyOutBlock(block,()=>OnFlyOutComplete(token),()=>OnFlyOutCancelled(token));
                else OnFlyOutComplete(token);
            }
            MaybeWin();
        }

        internal void FeedbackWrongTap(BlockOutBlockData block, bool isRepeat)
        {
            if (boardView == null) return;
            int tapToken = activeRunToken;
            // 误点距离只计真正空格（不含自身占格，§7.2；GameRules.TryGetWrongMoveDistance 已修）
            int empty = 0;
            Rules.TryGetWrongMoveDistance(block, out empty);
            // 参考 HandleWrongMove：反馈期间锁棋盘输入，回位后按当前局状态释放
            boardView.SetInputLock(BlockOutInputLock.WrongFeedback,true);
            boardView.MarkWrong(block, empty, () =>
            {
                if (tapToken != activeRunToken) return;   // 期间重开/切关/退出：由新局自行接管
                // 回位后仅当本局仍可操作才解锁（失败/通关/暂停态保持锁定语义由状态机负责）
                boardView.SetInputLock(BlockOutInputLock.WrongFeedback,false);
            });
            Combo.OnError();
            Settings.PlayVibration();
            Settings.PlaySound("sfx_error");
            OnBlockWrongMarked?.Invoke(block, isRepeat);
            OnLivesChanged?.Invoke(Rules.Lives);
            SaveActiveRun();
        }

        internal void HandleBoardBackgroundTapped()
        {
            // 锤子选择态下点击棋盘空白处取消（不扣库存）
            if (Tools != null && Tools.Mode == BlockOutToolMode.Hammer)
                Tools.CancelHammerMode();
        }

        /// <summary>飞出被取消（重开/切关/退出/重建）：逻辑移除早已提交，取消只放弃视觉，
        /// 不恢复棋盘、不改状态（普通点击期间状态恒为 Ready）。令牌已变说明是新局，由新局自行接管（P1-3）。</summary>
        internal void OnFlyOutCancelled(int callbackToken)
        {
            if (callbackToken != activeRunToken) return;
            inFlightFlyOuts = Mathf.Max(0, inFlightFlyOuts - 1);
            // 若逻辑层已清空（最后一块提交后在途被取消），仍须补结算，只执行一次由 MaybeWin 保证
            MaybeWin();
        }

        /// <summary>Called after fly-out animation finishes.
        /// 逻辑移已在点击时提交（§4.2.1），这里只做在途计数递减、音效与胜机判定。
        /// callbackToken 为发起本次移动时的本局令牌：不一致说明期间发生了重开/切关/退出，必须直接返回（P1-3）。</summary>
        internal void OnFlyOutComplete(int callbackToken)
        {
            if (callbackToken != activeRunToken) return;   // 旧局回调，绝不处理新一局
            inFlightFlyOuts = Mathf.Max(0, inFlightFlyOuts - 1);
            Settings.PlaySound("sfx_fly_out");
            MaybeWin();
        }

        /// <summary>
        /// 胜机判定（文档 §4.2.3）：逻辑层清空后仍须等**所有在途飞出与工具演出**完成才展示胜利；
        /// 失败/已胜局不再触发；由 MayBeWin 的调用方保证只执行一次（OnLevelWon 置 Won 后短路）。
        /// </summary>
        internal void MaybeWin()
        {
            if (CurrentLevel == null) return;
            if (State == BlockOutGameState.Lost || State == BlockOutGameState.Won) return;
            if (!Rules.IsWon) return;                      // 含 blocks.Count==0 的损坏关卡不会误胜（§4.1）
            if (inFlightFlyOuts > 0 || magicRunning) return;   // 等在途飞出 / 魔法演出
            OnLevelWon();
        }

        /// <summary>
        /// 消除后的统一收尾（P2-5）：普通点击 / 锤子 / 魔法棒三条路径共用。
        /// 负责：连击计分 → 特殊块连锁 → 库存回写 → 剩余数通知 → 存档。
        /// **不再复位状态**：普通点击期间状态恒为 Ready（连续点击，§4.2）；
        /// 魔法棒的忙态由 MagicRoutine 自行收口。胜机判定统一走 <see cref="MaybeWin"/>。
        /// isPlayerAction=true 表示这是玩家主动消除（普通点击/锤子），计入连击递增；
        /// 魔法棒由协程自行计分，此处置 false 只计分不递增。
        /// </summary>
        internal bool TryCommitRemoval(IEnumerable<BlockOutBlockData> targets,Func<bool> consume,bool playerAction,out List<BlockOutBlockData> removed)
        {
            var transaction=new BlockOutRunCommitter(Rules,Tools,Specials,PersistProgressAndTools);
            if(!transaction.Remove(targets,consume,out removed)) { OnSaveFailed?.Invoke(); return false; }
            if(BlockOutContentConfig.EnableCombo)
                for(int i=0;i<removed.Count;i++) Combo.OnSuccessfulRemove(!playerAction || i>0);
            OnRemainingBlocksChanged?.Invoke(Rules.RemainingBlocks);
            OnToolStateChanged?.Invoke();
            return true;
        }

        /// <summary>Persist current tool counts back to profile within a transaction;
        /// on save failure the in-memory Tools counts are restored from the rolled-back Profile (R07).</summary>
        internal bool ToolsToProfile()
        {
            if(Tools==null) return false;
            return CommitProfileChange(() => {
                Profile.HintCount=Tools.GetCount(BlockOutToolId.Hint);
                Profile.HammerCount=Tools.GetCount(BlockOutToolId.Hammer);
                Profile.MagicCount=Tools.GetCount(BlockOutToolId.Magic);
            });
        }

        /// <summary>R07：道具库存与对局进度（RunRemoved）一次性提交。
        /// 已承诺消除立即落盘，避免中途退出出现"已扣道具却丢失已完成消除"；
        /// 保存失败则回滚内存 Tools 与 RunRemoved（事务回滚 Profile）。返回是否提交成功。</summary>
        internal bool PersistProgressAndTools()
        {
            if(!runPlayable || CurrentLevel==null) return false;
            return CommitProfileChange(() => {
                if(Tools!=null) {
                    Profile.HintCount=Tools.GetCount(BlockOutToolId.Hint);
                    Profile.HammerCount=Tools.GetCount(BlockOutToolId.Hammer);
                    Profile.MagicCount=Tools.GetCount(BlockOutToolId.Magic);
                }
                WriteActiveRunToProfile();
            });
        }

        // ---- 道具 ----

        /// <summary>提示（对齐参考 ArtOutHintTool + UseHint）：
        /// 轮换高亮"未提示过的可飞块"，全部提示过则重置集合再取第一个；
        /// 无目标不扣库存；扣减成功才把目标记入本局已提示集合；**无 2.5s 硬冷却**（文档 §5）。
        /// 冻结规则（P2-5）：提示目标必须是玩家实际能点掉的块（可飞 + 未被冻结锁死）。</summary>
        public BlockOutBlockData UseHint()
        {
            if (Tools == null || !IsToolUnlocked(BlockOutToolId.Hint) || !CanStartTool || HasPendingMagic) return null;
            if (boardView != null && boardView.IsInputLocked) return null;   // 入场/误点反馈期间（参考 inputLocked）
            var before=Tools.Capture();
            var target = Tools.TryUseHint(IsPlayerActionable);
            if (target == null) return null;   // 无目标（含被冻结锁死）不扣库存
            if(!ToolsToProfile()) { Tools.Restore(before); OnSaveFailed?.Invoke(); return null; }
            Tools.CancelHammerMode();
            boardView.HighlightBlock(target, BlockOutContentConfig.HintHighlightSeconds);
            OnToolStateChanged?.Invoke();
            return target;
        }

        /// <summary>玩家实际可操作判定（提示/魔法共用，P2-5）：可飞且未被冻结锁死。
        /// 提示轮换与魔法选目标都经此过滤，避免给出玩家做不到的目标。</summary>
        internal bool IsPlayerActionable(BlockOutBlockData block)
        {
            if (block == null || !block.Active || !Rules.CanMove(block)) return false;
            return !BlockOutContentConfig.EnableSpecialBlocks || Specials == null || !Specials.IsBlockedByFrozen(block);
        }

        /// <summary>魔法目标过滤（R03）：只排除"玩家实际无法操作"的块（被冻结锁死），
        /// 可动性交由规则层在"模拟移除"状态下裁决，不在原棋盘以 CanMove 二次否决链式结果。</summary>
        internal bool IsMagicTargetSelectable(BlockOutBlockData block)
        {
            if (block == null || !block.Active) return false;
            return !BlockOutContentConfig.EnableSpecialBlocks || Specials == null || !Specials.IsBlockedByFrozen(block);
        }

        public bool EnterHammerMode()
        {
            if (Tools == null || !IsToolUnlocked(BlockOutToolId.Hammer) || !CanStartTool || HasPendingMagic) return false;
            if (boardView != null && boardView.IsInputLocked) return false;  // 入场/误点反馈期间（参考 inputLocked）
            return Tools.EnterHammerMode();
        }

        public void CancelHammerMode()
        {
            if (Tools != null) Tools.CancelHammerMode();
        }

        /// <summary>魔法棒（对齐参考 UseMagic + RemoveMagicTargets）：
        /// 施法前一次性选取目标（链式模拟逐次移除，最多 <see cref="BlockOutContentConfig.MagicTargetCount"/>=6 个，
        /// 允许"先 A 后 B 才可飞"的目标链）；有目标才扣 1 库存；随后**多颗星并行**飞向各目标，
        /// 命中缩放后逐一逻辑移除并飞出，不是逐块串行等待。
        /// 冻结规则（P2-5）：只选"玩家实际可操作"的块，不选冻结块。
        /// 施法全程进入 ResolvingMove 忙态（P1-9）：提示/锤子/普通点击/计时启动均被锁。</summary>
        public int UseMagic()
        {
            if(Tools==null || !IsToolUnlocked(BlockOutToolId.Magic) || !CanStartTool)return 0;
            var targets=new List<BlockOutBlockData>();
            if(HasPendingMagic)
            {
                foreach(var block in Rules.Blocks)if(pendingMagicTargets.Contains(block.RuntimeIndex) && block.Active)targets.Add(block);
                if(targets.Count==0)
                {
                    var journal=pendingMagicTargets.ToArray();pendingMagicTargets.Clear();
                    if(!PersistProgressAndTools()) { pendingMagicTargets.AddRange(journal);OnSaveFailed?.Invoke(); }
                    else { OnToolStateChanged?.Invoke();MaybeWin(); }
                    return 0;
                }
            }
            else
            {
                if(Tools.GetCount(BlockOutToolId.Magic)<=0)return 0;
                targets=Tools.PickMagicTargets(BlockOutContentConfig.MagicTargetCount,IsMagicTargetSelectable);
                if(targets.Count==0)return 0;
                var before=Tools.Capture();
                foreach(var block in targets)pendingMagicTargets.Add(block.RuntimeIndex);
                if(!Tools.ConsumeMagic() || !PersistProgressAndTools())
                {
                    Tools.Restore(before);pendingMagicTargets.Clear();OnSaveFailed?.Invoke();return 0;
                }
            }
            // The durable intent pays once. Each subsequent hit commits its own removal;
            // an interrupted/failed cast resumes remaining targets without paying again.
            Tools.CancelHammerMode();magicRunning=true;State=BlockOutGameState.ResolvingMove;
            boardView?.SetInputLock(BlockOutInputLock.Tool,true);
            OnToolStateChanged?.Invoke();OnStateChanged?.Invoke();
            magicSequence=StartCoroutine(MagicRoutine(targets));return targets.Count;
        }

        /// <summary>魔法棒协程（并行施法，对齐参考 RemoveMagicTargets + RemoveMagicBlockWithStarRoutine）：
        /// 所有目标并行启动（星路径 → 命中缩放脉冲 → 逻辑移除 → 飞出）；
        /// 全部"命中/逻辑移除"完成后解除工具锁，飞出动画继续时玩家即可操作（参考：星命中处理完解除工具锁、飞出可继续，R04）；
        /// 飞出完成后经 <see cref="MaybeWin"/> 统一胜利入口（等待所有在途演出，R04）。
        /// 保留：令牌保护（重开/切关/退出立即放弃）、一次施法只扣一次库存（已在 UseMagic 完成）、
        /// 冻结限制（选取时已过滤）、失败/暂停时不推进逻辑消块（R04）。</summary>
        internal IEnumerator MagicRoutine(List<BlockOutBlockData> targets)
        {
            int token=activeRunToken;magicArrivals.Clear();
            Settings.PlaySound("sfx_wand");
            var cast=new MagicCast { Pending=targets.Count };
            int pathIndex=0;
            foreach(var target in targets)
            {
                magicArrivals.Add(StartCoroutine(ResolveMagicTarget(target,token,cast,pathIndex++)));
                float stagger=BlockOutGameplayConfig.Current.feel.magicStarStaggerSeconds;
                if(stagger>0)yield return WaitForPresentation(stagger,token);
                if(token!=activeRunToken)yield break;
            }
            while(cast.Pending>0 && token==activeRunToken)yield return null;
            if(token!=activeRunToken)yield break;
            magicRunning=false;magicArrivals.Clear();magicSequence=null;
            if(State!=BlockOutGameState.Lost)State=BlockOutGameState.Ready;
            boardView?.SetInputLock(BlockOutInputLock.Tool,false);
            OnToolStateChanged?.Invoke();OnStateChanged?.Invoke();MaybeWin();
        }
        private IEnumerator ResolveMagicTarget(BlockOutBlockData target,int token,MagicCast cast,int pathIndex)
        {
            try
            {
                if(boardView!=null)yield return boardView.PlayMagicArrival(target,BlockOutGameplayConfig.Current.feel.magicStarPathSeconds,pathIndex);
                while(token==activeRunToken && (IsPaused || ModalPopupOpen))yield return null;
                if(token!=activeRunToken || State==BlockOutGameState.Lost || cast.Failed)yield break;
                var journal=pendingMagicTargets.ToArray();
                pendingMagicTargets.Remove(target.RuntimeIndex);
                if(!target.Active)
                {
                    if(!PersistProgressAndTools()) { pendingMagicTargets.Clear();pendingMagicTargets.AddRange(journal);cast.Failed=true;OnSaveFailed?.Invoke(); }
                    yield break;
                }
                List<BlockOutBlockData> removed;
                if(!TryCommitRemoval(new[]{target},null,false,out removed))
                {
                    pendingMagicTargets.Clear();pendingMagicTargets.AddRange(journal);cast.Failed=true;
                    boardView?.CancelMagicFeedback();yield break;
                }
                StartCommittedFlyouts(removed);
            }
            finally { cast.Pending=Mathf.Max(0,cast.Pending-1); }
        }

        /// <summary>单个魔法目标的演出（对齐参考 RemoveMagicBlockWithStarRoutine）：
        /// 星路径（配置秒数，星从魔法按钮飞向目标）→ 命中缩放脉冲 → 逻辑移除 → 独立飞出 → 完成回调。
        /// R04：星路径/命中阶段同样受暂停冻结（不推进逻辑消块）；若本局已失败则取消后续逻辑提交；
        /// 令牌失效（重开/切关/退出）时立即收尾，绝不修改新一局。
        /// R07：命中后的逻辑移除经 <see cref="PersistProgressAndTools"/> 立即持久化（工具+对局进度），
        /// 保存失败停止后续目标。</summary>


        // ---- 胜负 ----

        internal void OnLevelWon()
        { SettlementFlow.OnLevelWon(); }

        /// <summary>R06：结算保存失败后由 UI "重试" 调用，重新提交同一结算（幂等：
        /// MarkLevelCompleted/CurrentLevelIndex 取 Max，不会二次发奖由 settlementCommitted 守卫）。</summary>
        public void RetrySettlement()
        { SettlementFlow.RetrySettlement(); }

        internal void OnLevelLost()
        { SettlementFlow.OnLevelLost(); }

        // ---- 复活（对齐参考 ArtOutReviveConfig：不设单局一次上限） ----
        // 参考语义：免费复活 = 全局 1-10 关每次失败都可恢复满心（传 MaxLives）；
        // 金币复活 = 300 币补 1 心（默认档），不限次数；倒计时模式两种都加 20 秒。
        // ReviveUsedThisRun 字段保留（存档兼容 / 统计用），但不再作为资格硬阻断。

        /// <summary>免费复活资格：全局 1-10 关（参考 DefaultFreeReviveLevelNum=10）。</summary>
        public bool CanReviveThisRun => runPlayable && State==BlockOutGameState.Lost && !reviveAdPending
            && (BlockOutContentConfig.ReviveLimitPerRun<=0 || reviveCountThisRun<BlockOutContentConfig.ReviveLimitPerRun);

        public bool FreeReviveAvailable
        {
            get { return CanReviveThisRun && CurrentLevelNumber <= BlockOutContentConfig.FreeReviveMaxLevel; }
        }

        /// <summary>金币复活资格：金币足够即可（不限次数）。</summary>
        public bool CanReviveWithCoins
        {
            get { return CanReviveThisRun && Profile != null && Profile.Coins >= BlockOutContentConfig.CoinReviveCost; }
        }

        /// <summary>是否存在任一复活路径（免费 / 金币 / 广告）。</summary>
        public bool ReviveAvailableAtAll
        {
            get { return FreeReviveAvailable || CanReviveWithCoins || AdReviveReady; }
        }

        public bool AdReviveReady
        {
            get { return CanReviveThisRun && Ads != null && Ads.IsReady(AdType.Rewarded); }
        }

        /// <summary>激励广告复活：取消/失败不扣币、不消耗资格；回调防重复处理。
        /// 参考 ReviveByAd：广告复活补 <see cref="BlockOutContentConfig.ReviveLifeBonus"/> 心，不限次数。
        /// 事务内提交"内存复活态 + 写回对局进度"，失败整体回滚（R05）。</summary>
        public void ReviveWithAd(Action<bool> onComplete)
        { ReviveFlow.ReviveWithAd(onComplete); }

        /// <summary>金币复活：不足返回 false（不扣币）。扣币、生命/时间、清失败态与对局快照同一次事务提交；
        /// 失败整体回滚内存与档案，不关闭失败层（R05）。</summary>
        public bool ReviveWithCoins()
        { return ReviveFlow.ReviveWithCoins(); }

        /// <summary>免费复活（全局 1-10 关）：补满 <see cref="BlockOutContentConfig.FreeReviveLifeCount"/> 心
        /// （参考 ReviveByFree 补满）；受 limitPerRun 上限约束（R02，0=不限制），不限次数。</summary>
        public bool ReviveFree()
        { return ReviveFlow.ReviveFree(); }

        /// <summary>捕获复活前的可回滚基准（R05：事务失败时恢复内存状态与档案一致）。</summary>
        internal ReviveSnapshot CaptureReviveSnapshot()
        { return ReviveFlow.CaptureReviveSnapshot(); }

        internal void RestoreReviveSnapshot(ReviveSnapshot s)
        { ReviveFlow.RestoreReviveSnapshot(s); }

        internal sealed class ReviveSnapshot
        {
            public int Lives;
            public float Time;
            public bool RestoredLost;
            public BlockOutGameState State;
            public bool Used;
            public int Count;
            public bool TimerStarted, TimeExpired;
        }

        /// <summary>纯内存复活状态变更（不落盘、不触发事件）：倒计时不限时加时、生命模式补心、切 Ready。
        /// 扣币/写盘由调用方在事务内负责（R05）。</summary>
        internal void ApplyReviveState(int livesToAdd)
        { ReviveFlow.ApplyReviveState(livesToAdd); }

        /// <summary>复活成功收尾：恢复棋盘输入（R01）+ 触发事件。
        /// 仅恢复失败造成的输入锁，不误解开暂停或工具锁（暂停/工具锁由各模块独立管理）。</summary>
        internal void CompleteReviveSuccess()
        { ReviveFlow.CompleteReviveSuccess(); }

        // ---- 流程控制 ----

        /// <summary>Player gives up after failing: clear active run (pieces & coins kept).</summary>
        public void GiveUp()
        {
            ReviveUsedThisRun = false;
            // 退出本关同样要终止旧动画并解锁视图，避免回到首页后残留协程（P1-3）
            activeRunToken++;
            magicRunning = false;
            if (boardView != null)
            {
                boardView.CancelAnimations();
                boardView.SetPaused(false);
                boardView.SetInputLock(BlockOutInputLock.Inactive,true);
            }
            // 状态归位：若退出发生在飞出/施法途中，State 会停在 ResolvingMove。
            // 不归位的话，之后从首页 Resume() 会带着"结算中"状态恢复对局，输入与胜利判定都错。
            if (State == BlockOutGameState.ResolvingMove)
            {
                State = BlockOutGameState.Ready;
                OnStateChanged?.Invoke();
            }
            // 放弃后本局不再有效：后续 GoHome→Pause()、切后台、失焦都不允许再保存（P1-5）
            runPlayable = false;
            Profile.ClearActiveRun();
            SaveProfile();
        }

        /// <summary>重开本关：重置棋盘/生命/计时/工具选择态与复活资格；已消耗道具与已扣金币不返还。</summary>
        public void RestartLevel()
        {
            Profile.ClearActiveRun();
            SaveProfile();
            LoadLevel(CurrentLevelIndex);   // LoadLevel 内部已重置视图 paused / 取消旧动画（P1-2/P1-3）
        }

        public bool IsLastLevel => CurrentLevelIndex >= Catalog.LevelCount - 1;

        public void NextLevel()
        {
            if (IsLastLevel)
            {
                Debug.Log("[BlockOut] Reached last level. Content end.");
                return;
            }
            LoadLevel(CurrentLevelIndex + 1);
        }

        public void Pause()
        {
            // 玩家主动暂停：清掉"切后台暂停"标记，回前台时不得替他自动恢复（P1-2）
            pausedByAppBackground = false;
            DoPause();
        }

        internal void DoPause()
        {
            if (IsPaused) return;
            IsPaused = true;
            Combo.FreezeTimer();
            if (boardView != null)
            {
                boardView.SetPaused(true);
                boardView.SetInputLock(BlockOutInputLock.Pause,true);
            }
            // 暂停时落一次盘：倒计时剩余时间、失败态、复活资格都写进存档（P1-3）。
            // SaveActiveRun 内部已按 runPlayable 拦截：已放弃/已通关的局不会被写回（P1-5）。
            if (CurrentLevel != null && State != BlockOutGameState.Won) SaveActiveRun();
            OnPauseChanged?.Invoke(true);
        }

        /// <summary>切后台/失焦专用：置"切后台暂停"标记后再暂停。标记只用于回到前台时
        /// 补开暂停层，不会自动 Resume（P1-2）。已是暂停态（如玩家自己暂停过）则不重复标记。</summary>
        internal void PauseByBackground()
        {
            // 失败局：只补一次落盘，不改暂停态。失败层本身就是前台该看到的界面（P1-2）
            if (State == BlockOutGameState.Lost) { SaveActiveRun(); return; }
            if (!runPlayable || CurrentLevel == null || State == BlockOutGameState.Won) return;
            if (IsPaused) return;
            pausedByAppBackground = true;
            DoPause();
        }

        /// <summary>切后台/失焦：与暂停同等对待，先落盘再等系统挂起（P1-3/P1-2）。
        /// 只处理"仍有有效对局"的情况；已放弃/已通关的局不会被重新写回存档（P1-5）。</summary>
        internal void OnApplicationPause(bool paused)
        {
            if (paused) { PauseByBackground(); return; }
            HandleAppForegrounded();
        }

        internal void OnApplicationFocus(bool hasFocus)
        {
            applicationFocused = hasFocus;   // 参考 applicationFocused：失焦即冻结倒计时
            if (!hasFocus) { PauseByBackground(); return; }
            HandleAppForegrounded();
        }

        /// <summary>回到前台：仅当"本次暂停由切后台触发、且仍是有效进行中对局"时通知 UI 补开暂停层（P1-2）。
        /// 不调用 Resume——玩家必须显式点"继续"。玩家主动暂停的局不满足 pausedByAppBackground，不受影响。
        /// 失败态保持失败层（不弹暂停层），首页/商店/收藏等非对局页面由 UI 自行判断不处理。</summary>
        internal void HandleAppForegrounded()
        {
            if (!pausedByAppBackground) return;
            pausedByAppBackground = false;
            if (!IsPaused) return;                       // 期间已被 Resume（例如点了继续）
            if (!runPlayable || CurrentLevel == null) return;   // 已放弃/已通关：不必打断
            if (State == BlockOutGameState.Won) return;
            OnAppForegrounded?.Invoke();
        }

        public void Resume()
        {
            pausedByAppBackground = false;
            if (!IsPaused) return;
            IsPaused = false;
            Combo.ResumeTimer();
            if (boardView != null)
            {
                boardView.SetPaused(false);
                boardView.SetPresentationPaused(ModalPopupOpen);
                boardView.SetInputLock(BlockOutInputLock.Pause, false);
            }
            OnPauseChanged?.Invoke(false);
        }

        /// <summary>商店购买道具：本地金币事务（无服务端确认，原型边界）。
        /// 未解锁禁买；金币不足返回 InsufficientCoins 且不扣币；成功按工具包扣
        /// <see cref="BlockOutContentConfig.ToolPackCost"/> 币 + 发 <see cref="BlockOutContentConfig.ToolPackAmount"/> 个
        /// （参考 ToolPackCost=300 / ToolPackAmount=2）+ 持久化并同步进行中局 Tools。
        /// 扣币/加库存/落盘在同一档案事务里，保存失败整体回滚（C07）。</summary>
        public BlockOutPurchaseResult PurchaseTool(BlockOutToolId tool)
        {
            if (!IsToolUnlocked(tool)) return BlockOutPurchaseResult.Locked;
            if (Profile.Coins < BlockOutContentConfig.ToolPackCost) return BlockOutPurchaseResult.InsufficientCoins;
            bool committed = CommitProfileChange(() =>
            {
                Profile.SpendCoins(BlockOutContentConfig.ToolPackCost);
                Profile.AddToolCount((int)tool, BlockOutContentConfig.ToolPackAmount);
            });
            if (!committed)
            {
                Debug.LogError("[BlockOut] 道具购买保存失败，已回滚（未扣币）");
                OnSaveFailed?.Invoke();
                return BlockOutPurchaseResult.Failed;
            }
            if (Tools != null) Tools.AddTool(tool, BlockOutContentConfig.ToolPackAmount);
            OnCoinsChanged?.Invoke(Profile.Coins);
            return BlockOutPurchaseResult.Ok;
        }

        public void SpendCoins(int amount)
        {
            if (!CommitProfileChange(() => Profile.SpendCoins(amount))) return;
            OnCoinsChanged?.Invoke(Profile.Coins);
        }

        /// <summary>Loads and returns the complete artwork texture for the current level (if available).</summary>
        public Texture2D LoadCompletionImage()
        {
            if (CurrentLevel == null) return null;
            var pic = Catalog.FindPicture(CurrentLevel.PictureId);
            if (pic == null || string.IsNullOrEmpty(pic.completeImage)) return null;
            var tex = Resources.Load<Texture2D>(pic.completeImage);
            if (tex != null) return tex;
            if (!string.IsNullOrEmpty(pic.texturePath))
                tex = Resources.Load<Texture2D>(pic.texturePath);
            return tex;
        }

        void Update()
        {
            if (Ads != null) Ads.Tick(Time.deltaTime);
            if (IsPaused) return;
            if (Combo != null) Combo.Tick(Time.deltaTime);
            UpdateTimeFailTimer();
        }

        /// <summary>倒计时更新（条件逐条对齐参考 UpdateTimeFailTimer）：
        /// 非倒计时模式 / 无关卡 / 无棋盘 / 逻辑层已清空 / 已到期失败 → 直接返回；
        /// 未开始时须先满足 CanStartTimeFailTimer 全条件才启动；启动后按 ShouldTickTimeFailTimer 流逝。
        /// 注意：**普通块飞出不在任何阻塞条件里**——快速点击不能靠飞出动画拖长限时（文档 §5）。</summary>
        internal void UpdateTimeFailTimer()
        {
            if (!UseTimeFailMode || CurrentLevel == null || boardView == null
                || Rules.RemainingBlocks <= 0 || timeExpiredFailShown)
                return;

            if (!timerStarted)
            {
                if (!CanStartTimeFailTimer()) return;
                timerStarted = true;
            }

            if (!ShouldTickTimeFailTimer()) return;

            timeRemaining -= Time.deltaTime;
            if (timeRemaining <= 0f)
            {
                timeRemaining = 0f;
                timeExpiredFailShown = true;   // 只失败一次（参考 timerExpiredFailShown）
                OnTimeChanged?.Invoke(timeRemaining);
                Settings.PlaySound("sfx_countdown_end");
                if (boardView != null) boardView.SetInputLock(BlockOutInputLock.Lost,true);
                SaveActiveRun();
                OnLevelLost();
                return;
            }
            int sec = Mathf.CeilToInt(timeRemaining);
            if (sec != lastDisplayedSecond)
            {
                lastDisplayedSecond = sec;
                int warn = Mathf.CeilToInt(BlockOutGameplayConfig.Current.rules.warningThresholdSeconds);
                if (sec <= warn) Settings.PlaySound("sfx_countdown_tick");
                OnTimeChanged?.Invoke(timeRemaining);
            }
        }

        /// <summary>参考 CanStartTimeFailTimer：聚焦、无广告、棋盘输入未锁、无引导、无模态弹窗、未进入胜利流程。</summary>
        internal bool CanStartTimeFailTimer()
        {
            return applicationFocused
                && !adDisplayActive
                && !boardInputLocked
                && !guideActive
                && !ModalPopupOpen
                && State != BlockOutGameState.Won;
        }

        /// <summary>参考 ShouldTickTimeFailTimer：已启动后不因 inputLocked 停表，
        /// 但聚焦/广告/引导/模态弹窗/胜利流程仍冻结流逝。</summary>
        internal bool ShouldTickTimeFailTimer()
        {
            return applicationFocused
                && !adDisplayActive
                && !guideActive
                && !ModalPopupOpen
                && State != BlockOutGameState.Won;
        }

        internal bool boardInputLocked { get { return boardView != null && boardView.IsInputLocked; } }
        internal bool guideActive { get { return Guide != null && Guide.IsGuideActive; } }
    }
}
