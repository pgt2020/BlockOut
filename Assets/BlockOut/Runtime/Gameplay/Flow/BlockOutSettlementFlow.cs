using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Contracts;
namespace BlockOut.Gameplay
{
    internal sealed class BlockOutSettlementFlow
    {
        private readonly BlockOutGameManager owner;
        internal BlockOutSettlementFlow(BlockOutGameManager owner) { this.owner=owner; }
        internal void OnLevelWon()
        {
            // R06：先提交事务，成功后才通知领奖成功；失败保留可重试的待结算状态并阻止下一关覆盖现场。
            if (owner.settlementCommitted)
            {
                owner.EmitOnLevelWinned();
                return;
            }
            int reward = 0;
            bool wasCompleted = owner.CurrentLevel != null && owner.Profile.IsLevelCompleted(owner.CurrentLevel.Id);
            // 结算整体走档案事务（C07）：通关标记、进度、奖励、清局要么全部落盘，要么全部回滚。
            bool wasPlayable=owner.runPlayable;
            bool committed = owner.CommitProfileChange(() =>
            {
                if (owner.CurrentLevel != null)
                {
                    owner.Profile.MarkLevelCompleted(owner.CurrentLevel.Id);
                    owner.Profile.CurrentLevelIndex = Mathf.Max(owner.Profile.CurrentLevelIndex, owner.CurrentLevelIndex + 1);

                    reward = owner.Settlement.SettleWin(owner.CurrentLevel);
                }
                // 通关后本局不再"进行中"：随后的 Pause/切后台不得再写回存档（P1-5）
                owner.runPlayable = false;
                owner.Profile.ClearActiveRun();
            });
            if (!committed)
            {
                // 失败：档案已回滚（进度/奖励/清局均未落盘）。保留可重试待结算态：
                // 仍展示结算层避免黑屏，但 UI 标记"未保存"并禁止进入下一关（R06）。
                Debug.LogError("[BlockOut] 通关结算保存失败，档案已回滚（进度/奖励未落盘）");
                owner.runPlayable=wasPlayable;
                owner.SettlementSaveFailed = true;
                owner.EmitOnSaveFailed();
                owner.State = BlockOutGameState.Won;
                owner.EmitOnLevelWinned();   // UI 据 SettlementSaveFailed 展示失败态
                return;
            }
            owner.Settlement.ConfirmWin(reward);
            if(!wasCompleted && owner.CurrentLevel!=null) owner.Assembly.OnLevelCompleted(owner.CurrentLevel.Chapter, owner.Catalog.ChapterLevelCount(owner.CurrentLevel.Chapter));
            owner.settlementCommitted = true;
            owner.SettlementSaveFailed = false;
            owner.State = BlockOutGameState.Won;
            owner.LastWinWasFirstClear = !wasCompleted;
            owner.LastRewardCoins = reward;
            owner.Settings.PlaySound("sfx_level_win");
            owner.EmitOnCoinsChanged(owner.Profile.Coins);
            owner.Settings.PlaySound("sfx_piece_reveal");
            if (owner.IsCurrentChapterComplete) owner.Settings.PlaySound("bgm_chapter_complete");
            owner.EmitOnLevelWinned();
        }
        internal void RetrySettlement()
        {
            if (!owner.SettlementSaveFailed) return;
            owner.settlementCommitted = false;   // 允许重新提交（仍经 CommitProfileChange 校验）
            owner.SettlementSaveFailed = false;
            OnLevelWon();
        }
        internal void OnLevelLost()
        {
            owner.State = BlockOutGameState.Lost;
            bool cancelledMagic=owner.magicRunning;
            if(owner.magicSequence!=null) owner.StopCoroutine(owner.magicSequence);
            foreach(var arrival in owner.magicArrivals) if(arrival!=null) owner.StopCoroutine(arrival);
            owner.magicArrivals.Clear(); owner.magicRunning=false;
            if(cancelledMagic) { owner.boardView?.CancelMagicFeedback(); owner.boardView?.SetInputLock(BlockOutInputLock.Tool,false); }
            owner.boardView?.SetInputLock(BlockOutInputLock.Lost,true);
            owner.LastFailReason = owner.UseTimeFailMode ? "时间用尽" : "生命耗尽";
            owner.Settings.PlaySound("sfx_level_fail");
            owner.SaveActiveRun();
            owner.EmitOnLevelLosed();
        }
    }
}
