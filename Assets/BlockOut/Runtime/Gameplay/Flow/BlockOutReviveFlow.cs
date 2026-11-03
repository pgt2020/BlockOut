using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Contracts;
namespace BlockOut.Gameplay
{
    internal sealed class BlockOutReviveFlow
    {
        private readonly BlockOutGameManager owner;
        internal BlockOutReviveFlow(BlockOutGameManager owner) { this.owner=owner; }
        internal void ReviveWithAd(Action<bool> onComplete)
        {
            if (!owner.CanReviveThisRun) { if (onComplete != null) onComplete(false); return; }
            if (owner.Ads == null || !owner.Ads.IsReady(AdType.Rewarded)) { if (onComplete != null) onComplete(false); return; }
            owner.reviveAdPending = true;
            int adRunToken = owner.activeRunToken;
            owner.Ads.ShowRewarded("revive", (success) =>
            {
                if (adRunToken != owner.activeRunToken) { onComplete?.Invoke(false); return; }
                if (!owner.reviveAdPending) { if (onComplete != null) onComplete(false); return; }
                owner.reviveAdPending = false;
                if (!success || !owner.CanReviveThisRun) { if (onComplete != null) onComplete(false); return; }
                // 广告成功 → 内存先改，再一次性提交（补心 + 写回对局进度）
                var snap = CaptureReviveSnapshot();
                ApplyReviveState(BlockOutContentConfig.ReviveLifeBonus);
                bool committed = owner.CommitProfileChange(() => owner.WriteActiveRunToProfile());
                if (!committed)
                {
                    RestoreReviveSnapshot(snap);
                    owner.EmitOnSaveFailed();
                    if (onComplete != null) onComplete(false);
                    return;
                }
                CompleteReviveSuccess();
                if (onComplete != null) onComplete(true);
            });
        }
        internal bool ReviveWithCoins()
        {
            if (owner.State != BlockOutGameState.Lost || !owner.CanReviveWithCoins) return false;
            int cost = BlockOutContentConfig.CoinReviveCost;
            var snap = CaptureReviveSnapshot();
            ApplyReviveState(BlockOutContentConfig.ReviveLifeBonus);   // 内存先改（失败可回滚）
            bool committed = owner.CommitProfileChange(() =>
            {
                owner.Profile.SpendCoins(cost);
                owner.WriteActiveRunToProfile();   // 失败态/生命/时间/对局进度一并落盘
            });
            if (!committed)
            {
                RestoreReviveSnapshot(snap);   // 内存回滚（Profile 已由事务回滚）
                Debug.LogError("[BlockOut] 金币复活提交失败，已回滚（未扣币、未复活）");
                owner.EmitOnSaveFailed();
                return false;
            }
            CompleteReviveSuccess();
            return true;
        }
        internal bool ReviveFree()
        {
            if (owner.State != BlockOutGameState.Lost || !owner.FreeReviveAvailable) return false;
            if (BlockOutContentConfig.ReviveLimitPerRun > 0 && owner.reviveCountThisRun >= BlockOutContentConfig.ReviveLimitPerRun) return false;
            var snap = CaptureReviveSnapshot();
            ApplyReviveState(BlockOutContentConfig.FreeReviveLifeCount);   // 补满（AddLives 钳制到 MaxLives）
            bool committed = owner.CommitProfileChange(() => owner.WriteActiveRunToProfile());
            if (!committed)
            {
                RestoreReviveSnapshot(snap);
                Debug.LogError("[BlockOut] 免费复活提交失败，已回滚");
                owner.EmitOnSaveFailed();
                return false;
            }
            CompleteReviveSuccess();
            return true;
        }
        internal BlockOutGameManager.ReviveSnapshot CaptureReviveSnapshot()
        {
            return new BlockOutGameManager.ReviveSnapshot
            {
                Lives = owner.Rules.Lives,
                Time = owner.timeRemaining,
                RestoredLost = owner.restoredLost,
                State = owner.State,
                Used = owner.ReviveUsedThisRun,
                Count = owner.reviveCountThisRun, TimerStarted=owner.timerStarted, TimeExpired=owner.timeExpiredFailShown,
            };
        }
        internal void RestoreReviveSnapshot(BlockOutGameManager.ReviveSnapshot s)
        {
            owner.Rules.AddLives(s.Lives - owner.Rules.Lives);   // 钳制回原值
            owner.timeRemaining = s.Time;
            owner.restoredLost = s.RestoredLost;
            owner.State = s.State;
            owner.ReviveUsedThisRun = s.Used;
            owner.reviveCountThisRun = s.Count; owner.timerStarted=s.TimerStarted; owner.timeExpiredFailShown=s.TimeExpired;
        }
        internal void ApplyReviveState(int livesToAdd)
        {
            owner.reviveCountThisRun++;
            owner.ReviveUsedThisRun = true;   // 仅记录（兼容旧存档字段），不再作为资格阻断
            if (owner.UseTimeFailMode)
            {
                owner.timeRemaining = Mathf.Max(0f, owner.timeRemaining) + BlockOutContentConfig.ReviveTimeBonusSeconds;
                owner.timeExpiredFailShown = false;   // 复活后重新计时（参考 AddTimeFailReviveSeconds）
                owner.timerStarted = false;
            }
            else owner.Rules.AddLives(livesToAdd);
            owner.State = BlockOutGameState.Ready;
            owner.restoredLost = false;   // 复活后本局不再是失败态（P1-3：恢复失败局不能绕过复活，复活后则正常可操作）
        }
        internal void CompleteReviveSuccess()
        {
            owner.Settings.PlaySound("sfx_revive");
            // R01：复活统一恢复棋盘输入与计时可运行态（失败锁在失败反馈/倒计时失败时置位）
            if (owner.boardView != null) owner.boardView.SetInputLock(BlockOutInputLock.Lost,false);
            owner.EmitOnLivesChanged(owner.Rules.Lives);
            owner.EmitOnTimeChanged(owner.timeRemaining);
            owner.EmitOnReviveStateChanged();
            if(owner.HasPendingMagic)owner.StartCoroutine(owner.ResumePendingMagicAfterEntrance(owner.activeRunToken));
        }
    }
}
