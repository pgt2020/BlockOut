using System;
using UnityEngine;
using BlockOut.Config;
using BlockOut.Core;

namespace BlockOut.Gameplay
{
    /// <summary>
    /// 通关奖励结算（可配置奖励表 + 现有关卡值）。
    /// 复活/双倍奖励等商业化流程按 v5 边界不在本期实现（接口见 GameManager.ReviveWithAd/ReviveWithCoins）。
    /// </summary>
    public sealed class BlockOutSettlement
    {
        public event Action<int> OnWinSettled;

        // C01：去掉 readonly——BindProfile 需要在服务注入后重绑档案对象。
        private BlockOutPlayerProfile profile;

        public int LastReward { get; private set; }
        public bool HasPendingReward { get; private set; }

        public BlockOutSettlement(BlockOutPlayerProfile playerProfile)
        {
            profile = playerProfile;
        }

        /// <summary>
        /// 服务注入后重新绑定档案（R09/R13）：Bootstrap 注入集中存档服务时，
        /// GameManager.Profile 被换成服务档案对象，Settlement 必须跟着换，
        /// 否则奖励会加到 Awake 时加载的旧对象上，被服务档案的整体落盘覆写（金币丢失）。
        /// 事件订阅与中间状态保留。
        /// </summary>
        public void BindProfile(BlockOutPlayerProfile playerProfile)
        {
            if (playerProfile != null) profile = playerProfile;
        }

        /// <summary>通关发奖：奖励 = 关卡自带值优先，否则按难度取可配置奖励表。
        /// 只改内存档案，**不在此处落盘**：由 GameManager 在结算序列末尾统一
        /// <see cref="BlockOutGameManager"/> 单点保存（失败可感知、可随事务回滚），
        /// 避免"旧对象直写 PlayerPrefs → 服务档案覆写"把奖励写丢。</summary>
        public int SettleWin(BlockOutLevelData level)
        {
            int reward=CalculateReward(level);
            profile?.AddCoins(reward);
            return reward;
        }
        public int CalculateReward(BlockOutLevelData level)
        {
            return BlockOutContentConfig.GetLevelReward(level!=null ? level.Difficulty : "normal",level!=null ? level.RewardCoins : 0);
        }
        public void ConfirmWin(int reward)
        {
            LastReward=reward; HasPendingReward=true; OnWinSettled?.Invoke(reward);
        }

        public void Reset()
        {
            HasPendingReward = false;
            LastReward = 0;
        }
    }
}
