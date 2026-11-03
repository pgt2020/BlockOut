using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Contracts;
namespace BlockOut.Gameplay
{
    internal sealed class BlockOutLevelFlow
    {
        private readonly BlockOutGameManager owner;
        internal BlockOutLevelFlow(BlockOutGameManager owner) { this.owner=owner; }
        internal void LoadLevel(int index, bool restoreRun = false)
        {
            owner.CurrentLevelIndex = Mathf.Clamp(index, 0, Mathf.Max(0, owner.Catalog.LevelCount - 1));
            owner.CurrentLevel = owner.Catalog.GetLevel(owner.CurrentLevelIndex);
            if (owner.CurrentLevel == null || owner.CurrentLevel.Blocks.Count == 0)
            {
                Debug.LogError("[BlockOut] Level " + index + " is empty.");
                owner.State = BlockOutGameState.Loading;
                owner.runPlayable = false;
                return;
            }

            // 本局令牌自增：重开/切关/退出后旧协程将在下一帧检测到令牌变更而安全退出
            owner.activeRunToken++;
            owner.StopAllCoroutines(); owner.magicArrivals.Clear();
            // 有效对局建立（此前若有已放弃的对局，其存档已在 GiveUp 中清除）
            owner.runPlayable = true;
            // 新挑战：复活资格重置（重开或放弃后同样重置，见 RestartLevel/GiveUp）
            owner.ReviveUsedThisRun = false;
            owner.reviveCountThisRun = 0;
            owner.settlementCommitted = false;
            owner.SettlementSaveFailed = false;
            owner.reviveAdPending = false;
            owner.magicRunning = false;
            owner.pendingMagicTargets.Clear();
            owner.inFlightFlyOuts = 0;
            owner.restoredLost = false;   // 新挑战/重开都不继承失败态；仅 restoreRun 命中时置回
            owner.pendingWinRestore = false;   // 同理，胜利恢复只由 restoreRun 分支置位
            // 倒计时状态按新局重置（参考 ResetTimeFailTimer 的 timerStarted 部分）；
            // timeExpiredFailShown 需等 timeRemaining 计算后按剩余时间置位（见下方）
            owner.timerStarted = false;
            // 新挑战使用配置模式（首发默认生命模式）；进行中对局的模式由存档双向覆盖（P2-4）。
            // R02：配置来源由 BlockOutContentConfig.UseTimeFailModeDefault 经 JSON 同步，不再读恒为 false 的字段。
            owner.ConfigUseTimeFailMode = BlockOutContentConfig.UseTimeFailModeDefault;
            owner.UseTimeFailMode = owner.ConfigUseTimeFailMode;

            owner.Rules.StartLevel(owner.CurrentLevel);
            owner.Tools = new BlockOutToolController(owner.Rules, owner.Profile.HintCount, owner.Profile.HammerCount, owner.Profile.MagicCount);
            if (owner.Tools != null)
            {
                owner.Tools.OnToolStateChanged += () => { owner.EmitOnToolStateChanged(); };
                owner.Tools.OnHammerModeChanged += (active) =>
                {
                    if (owner.boardView != null) owner.boardView.SetHammerSelectMode(active);
                    owner.EmitOnToolStateChanged();
                };
            }
            owner.Combo.Reset();
            if (owner.Tools != null) owner.Tools.ResetHintCycle();   // 提示轮换集合按新局重置（参考 ResetHintCycle）
            // R02：无关卡自带时长时回退到配置兜底（GameplayConfig.rules.gameTimeSeconds，经 Apply 同步）
            owner.GameTimeSeconds = BlockOutContentConfig.GameTimeSeconds;
            owner.timeRemaining = owner.CurrentLevel.GameTime > 0 ? owner.CurrentLevel.GameTime : owner.GameTimeSeconds;
            owner.lastDisplayedSecond = -1;
            // 参考 ResetTimeFailTimer：恢复 0 秒的失败局不得重新开始计时
            owner.timeExpiredFailShown = owner.UseTimeFailMode && owner.timeRemaining <= 0f;

            // M2 extras
            owner.Specials.LoadExtras(owner.CurrentLevel,null,"");
            var extrasAsset = Resources.Load<TextAsset>("ArtOut/BlockOutLevelExtras");
            if (extrasAsset != null)
            {
                var extras = JsonUtility.FromJson<BlockOutLevelExtrasConfig>(extrasAsset.text);
                string hash = BlockOutSolver.ComputeLevelHash(owner.CurrentLevel);
                owner.Specials.LoadExtras(owner.CurrentLevel, extras, hash);
            }

            // Restore run progress if resuming — validate levelId and hash
            if (restoreRun)
            {
                string expectedHash = BlockOutSolver.ComputeLevelHash(owner.CurrentLevel);
                bool valid = owner.CurrentLevel.Id == owner.Profile.RunLevelId
                          && owner.Profile.RunBlockCount == owner.CurrentLevel.Blocks.Count
                          && owner.Profile.RunLevelHash == expectedHash;
                if (valid)
                {
                    var progress = new BlockOutRunProgress
                    {
                        LevelId = owner.Profile.RunLevelId,
                        LevelHash = owner.Profile.RunLevelHash,
                        BlockCount = owner.Profile.RunBlockCount,
                        Lives = owner.Profile.RunLives,
                        RemovedBlockIndices = owner.Profile.RunRemoved ?? new int[0],
                        WrongBlockIndices = owner.Profile.RunWrong ?? new int[0]
                    };
                    owner.Rules.ApplyRunProgress(progress);
                    if(owner.Profile.RunPendingMagicTargets!=null) owner.pendingMagicTargets.AddRange(owner.Profile.RunPendingMagicTargets);
                    owner.reviveCountThisRun = Mathf.Max(owner.Profile.RunReviveCount, owner.Profile.RunReviveUsed ? 1 : 0);
                    owner.ReviveUsedThisRun = owner.Profile.RunReviveUsed; // 还原局内复活资格（避免复活后退出重进再获资格）

                    // 失败模式：按存档**双向**恢复本局模式（0=生命 → false，1=倒计时 → true）。
                    // 只在 ==1 时置 true 会让"旧的/生命模式对局"沿用当前开关值被按倒计时恢复（P2-4）。
                    // 旧存档没有 RunFailMode 时 JsonUtility 给 0，即生命模式，行为与之前一致。
                    owner.UseTimeFailMode = owner.Profile.RunFailMode == 1;

                    // 倒计时恢复：RunHasTimeRecord 区分"0 秒（已失败）"与"没有时间记录"（P1-3）。
                    // 旧存档没有该字段 → false → 不恢复时间，保持按关卡默认值起算。
                    if (owner.UseTimeFailMode && owner.Profile.RunHasTimeRecord)
                        owner.timeRemaining = Mathf.Max(0f, owner.Profile.RunTimeRemaining);

                    // 恢复失败态：不能只看 Rules.IsLost（那只判断生命）。
                    // 倒计时归零的失败局若按 Ready 恢复，玩家会重新获得时间并可操作 = 绕过失败与复活规则（P1-3）。
                    if (owner.Profile.RunLost || owner.Rules.IsLost)
                    {
                        owner.restoredLost = true;
                        owner.LastFailReason = !string.IsNullOrEmpty(owner.Profile.RunFailReason)
                            ? owner.Profile.RunFailReason
                            : (owner.UseTimeFailMode ? "时间用尽" : "生命耗尽");
                    }
                    // P1-6 空棋盘存档：修复前"点击即移除"会留下"全部方块已移除但没结算"的存档。
                    // 现在正常路径是延迟提交（动画完成才移除），存档只会落在稳定局面；
                    // 但**已存在的旧存档**、以及魔法/锤子等其它路径仍可能命中"规则层已清空"。
                    // 这里显式识别为"待结算胜利"，交由 CompletePendingWin() 走完整结算，而不是恢复成空棋盘 Ready。
                    else if (!owner.restoredLost && owner.Rules.IsWon)
                    {
                        owner.pendingWinRestore = true;
                    }
                }
                else
                {
                    Debug.LogWarning("[BlockOut] Save mismatch for " + owner.CurrentLevel.Id + ", starting fresh.");
                    owner.Profile.ClearActiveRun();
                    owner.SaveProfile();
                }
            }

            // Wire board view
            if (owner.boardView != null)
            {
                // 新局统一重置视图运行态：暂停层"重开本关"后不得残留 paused（P1-2）
                owner.boardView.SetPaused(false);
                owner.boardView.SetInputLock(BlockOutInputLock.Pause, false);
                owner.boardView.SetHammerSelectMode(false);
                owner.boardView.OnBlockTapped -= owner.OnBoardBlockTapped;
                owner.boardView.OnBlockTapped += owner.OnBoardBlockTapped;
                owner.boardView.OnBoardBackgroundTapped -= owner.HandleBoardBackgroundTapped;
                owner.boardView.OnBoardBackgroundTapped += owner.HandleBoardBackgroundTapped;
                owner.boardView.SetRunToken(owner.activeRunToken);
                owner.boardView.Setup(owner.Rules, owner.CurrentLevel.Width, owner.CurrentLevel.Height);
                owner.boardView.SetPresentationPaused(owner.ModalPopupOpen);
                // 入场演出（§7.3）：0.9s 0.68→1 缩放 + 1.02s 输入延迟；切关/重开经 Setup→CancelAnimations 终止旧协程
                owner.boardView.PlayEntrance();
            }

            // 实际到达进度（道具解锁依据）
            if (owner.CurrentLevelNumber > owner.Profile.MaxLevelReached)
            {
                owner.Profile.MaxLevelReached = owner.CurrentLevelNumber;
                owner.SaveProfile();
            }

            owner.State = (owner.restoredLost || owner.Rules.IsLost) ? BlockOutGameState.Lost : BlockOutGameState.Ready;
            owner.IsPaused = false;
            if(owner.boardView!=null)
            {
                owner.boardView.SetInputLock(BlockOutInputLock.Lost, owner.State==BlockOutGameState.Lost);
                owner.boardView.SetInputLock(BlockOutInputLock.Modal, owner.ModalPopupOpen);
            }
            owner.EmitOnStateChanged();
            owner.EmitOnLivesChanged(owner.Rules.Lives);
            owner.EmitOnCoinsChanged(owner.Profile.Coins);
            owner.EmitOnRemainingBlocksChanged(owner.Rules.RemainingBlocks);
            owner.EmitOnTimeChanged(owner.timeRemaining);
            owner.EmitOnToolStateChanged();
            owner.EmitOnLevelLoaded(owner.CurrentLevel);

            // P1-6：存档已满足胜利条件 → 先把空棋盘状态落盘（保持"未结算"的原始语义），
            // 紧接着走一次完整结算。结算内会 MarkLevelCompleted + 发奖 + ClearActiveRun，
            // 因此不会再写出"空棋盘 + HasActiveRun"的坏存档。
            if (owner.pendingWinRestore)
            {
                // 不落"空棋盘 + HasActiveRun"的存档：直接结算。
                // 结算内 MarkLevelCompleted → 发奖 → ClearActiveRun，一步到位把存档失效。
                owner.pendingWinRestore = false;
                CompletePendingWin();
                return;
            }

            SaveActiveRun();
            if(owner.HasPendingMagic)owner.StartCoroutine(owner.ResumePendingMagicAfterEntrance(owner.activeRunToken));
        }
        internal void CompletePendingWin()
        {
            // 已通关/已失败的对局不再持有"有效进行中"状态
            owner.runPlayable = false;
            owner.OnLevelWon();
        }
        internal void WriteActiveRunToProfile()
        {
            if (!owner.runPlayable || owner.CurrentLevel == null) return;
            var progress = owner.Rules.CaptureRunProgress(owner.CurrentLevel.Id, BlockOutSolver.ComputeLevelHash(owner.CurrentLevel));
            owner.Profile.HasActiveRun = true;
            owner.Profile.RunLevelId = progress.LevelId;
            owner.Profile.RunLevelHash = progress.LevelHash;
            owner.Profile.RunBlockCount = progress.BlockCount;
            owner.Profile.RunLives = progress.Lives;
            owner.Profile.RunRemoved = progress.RemovedBlockIndices;
            owner.Profile.RunWrong = progress.WrongBlockIndices;
            owner.Profile.RunTimeRemaining = owner.timeRemaining;
            owner.Profile.RunReviveUsed = owner.ReviveUsedThisRun;
            owner.Profile.RunReviveCount = owner.reviveCountThisRun;
            owner.Profile.RunPendingMagicTargets=owner.pendingMagicTargets.ToArray();
            // 失败模式 / 失败态 / 原因一并存档（P1-3）：恢复时据此回到失败层
            owner.Profile.RunFailMode = owner.UseTimeFailMode ? 1 : 0;
            owner.Profile.RunHasTimeRecord = owner.UseTimeFailMode;   // 只有倒计时模式才有"时间"可恢复
            owner.Profile.RunLost = owner.State == BlockOutGameState.Lost || owner.restoredLost || owner.Rules.IsLost
                              || (owner.UseTimeFailMode && owner.timeRemaining <= 0f);
            owner.Profile.RunFailReason = owner.Profile.RunLost
                ? (string.IsNullOrEmpty(owner.LastFailReason)
                    ? (owner.UseTimeFailMode ? "时间用尽" : "生命耗尽")
                    : owner.LastFailReason)
                : null;
        }
        internal void SaveActiveRun()
        {
            // 已放弃/已通关/尚未开局的对局一律不再落盘（P1-5）。
            // 覆盖"失败后退出 → GoHome → Pause()"与"暂停后退出 → Pause()"两条路径：
            // 之前 Pause 无条件把 HasActiveRun 写回 true，导致已放弃的局被重新存进 PlayerPrefs。
            if (!owner.runPlayable || owner.CurrentLevel == null) return;
            if(!owner.CommitProfileChange(WriteActiveRunToProfile)) owner.EmitOnSaveFailed();
        }
        internal int FindLevelIndexById(string id)
        {
            for (int i = 0; i < owner.Catalog.LevelCount; i++)
            {
                if (owner.Catalog.GetLevelMetadata(i) != null && owner.Catalog.GetLevelMetadata(i).Id == id) return i;
            }
            return -1;
        }
    }
}
