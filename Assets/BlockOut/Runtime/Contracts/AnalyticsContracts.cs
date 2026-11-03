using System;
using System.Collections.Generic;

namespace BlockOut.Contracts
{
    /// <summary>统计事件名字面量。事件名属外部后台契约，不得随重构改名（R23）。</summary>
    public static class BlockOutAnalyticsEvents
    {
        public const string AppStart = "app_start";
        public const string LevelStart = "level_start";
        public const string LevelWin = "level_win";
        public const string LevelLose = "level_lose";
        public const string LevelRestart = "level_restart";
        public const string ReviveOffer = "revive_offer";
        public const string ReviveResult = "revive_result";
        public const string ToolUse = "tool_use";
        public const string ToolPurchase = "tool_purchase";
        public const string AdShow = "ad_show";
        public const string AdReward = "ad_reward";
        public const string SettlementSeen = "settlement_seen";
        public const string CollectionView = "collection_view";
        public const string SettingsChange = "settings_change";
    }

    /// <summary>一条语义化统计事件。业务只发语义事件，不感知任何 SDK。</summary>
    public sealed class AnalyticsEvent
    {
        public string Name;
        public readonly Dictionary<string, string> Parameters = new Dictionary<string, string>();

        public AnalyticsEvent(string name) { Name = name; }

        public AnalyticsEvent With(string key, string value)
        {
            if (!string.IsNullOrEmpty(key)) Parameters[key] = value ?? string.Empty;
            return this;
        }

        public AnalyticsEvent With(string key, int value) { return With(key, value.ToString()); }
        public AnalyticsEvent With(string key, float value) { return With(key, value.ToString("0.###")); }
        public AnalyticsEvent With(string key, bool value) { return With(key, value ? "1" : "0"); }
    }

    /// <summary>
    /// 统计/归因服务契约（R15）。业务只依赖本接口；
    /// 具体 SDK 适配层按"模块矩阵"决定是否安装，未启用时由空实现降级。
    /// </summary>
    public interface IAnalyticsService
    {
        bool IsEnabled { get; }
        void Track(AnalyticsEvent evt);
        void Track(string eventName);
        void SetUserId(string userId);
        void Flush();
    }

    /// <summary>未接入任何统计 SDK 时的空实现：不抛异常、不产生网络请求。</summary>
    public sealed class NullAnalyticsService : IAnalyticsService
    {
        public bool IsEnabled => false;
        public void Track(AnalyticsEvent evt) { }
        public void Track(string eventName) { }
        public void SetUserId(string userId) { }
        public void Flush() { }
    }
}
