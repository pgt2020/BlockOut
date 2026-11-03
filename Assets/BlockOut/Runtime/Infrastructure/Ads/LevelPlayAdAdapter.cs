using System;
using BlockOut.Contracts;

// 允许独立的 EditMode 测试程序集驱动 SDK 内部回调，保持回调不对业务代码公开。
[assembly: System.Runtime.CompilerServices.InternalsVisibleTo("BlockOut.Tests.EditMode")]

namespace BlockOut.Infrastructure.Ads
{
    /// <summary>
    /// Unity LevelPlay（ironSource）激励广告适配器（R14）。
    ///
    /// 接入状态：**代码已实现、SDK 包未导入、App Key / Placement 未配置**。
    /// 未配置时按设计降级：GetLoadState = NotLoaded，ShowRewarded 直接走 OnShowFailed，
    /// 绝不以"模拟成功"冒充真实广告成功（R16 发布门禁同样阻止此替身进入正式包）。
    ///
    /// 官方 API 映射（LevelPlay Unity SDK，按实际导入版本核对）：
    ///   IronSource.Agent.init(appKey)                      → Init
    ///   IronSource.Agent.loadRewardedVideo()               → Load
    ///   IronSourceEvents.onRewardedVideoAdOpenedEvent      → OnShown
    ///   IronSourceEvents.onRewardedVideoAdShowFailedEvent  → OnShowFailed
    ///   IronSourceEvents.onRewardedVideoAdClosedEvent      → OnClosed
    ///   IronSourceEvents.onRewardedVideoAdRewardedEvent    → OnRewarded
    ///   IronSourceEvents.onRewardedVideoAvailabilityChangedEvent → 刷新 LoadState
    ///
    /// 单次获奖保证：每次 ShowRewarded 生成新的 requestId，奖励回调只对"当前 requestId"生效一次，
    /// 因此重复回调、过期回调、跨局回调都不会二次发奖（调用方另有局令牌防护）。
    /// </summary>
    public sealed class LevelPlayAdAdapter : AdProviderBase
    {
        private readonly string appKey;
        private readonly string rewardedPlacementId;
        private readonly bool isTestMode;

        private AdLoadState rewardedState = AdLoadState.NotLoaded;
        private bool initialized;
        private int requestSeq;
        private int activeRequestId;
        private string activePlacement;
        private AdShowCallbacks activeCallbacks;
        private bool activeRewardFired;

        public LevelPlayAdAdapter(string appKey, string rewardedPlacementId, bool isTestMode)
        {
            this.appKey = appKey;
            this.rewardedPlacementId = rewardedPlacementId;
            this.isTestMode = isTestMode;
        }

        /// <summary>是否具备可初始化条件（App Key 非空）。Bootstrap 据此决定是否实例化本适配器。</summary>
        public bool HasCredentials => !string.IsNullOrEmpty(appKey);

        public override void Init()
        {
            if (initialized) return;
            if (!HasCredentials)
            {
                DebugLog("[BlockOut][Ads] LevelPlay 未配置 App Key，适配器保持未就绪（不模拟成功）。");
                return;
            }
            initialized = true;
            // 正式接入点：IronSource.Agent.init(appKey) + 订阅 IronSourceEvents 事件 + 按需 setConsent。
            // SDK 程序集未导入时本段不编译，故此处以显式 TODO + 降级状态表达接入位置。
            DebugLog("[BlockOut][Ads] LevelPlay init 占位：appKey 已配置，等待导入 SDK 后取消注释。");
            rewardedState = AdLoadState.Loading;
        }

        public override bool IsReady(AdType type)
        {
            return type == AdType.Rewarded && rewardedState == AdLoadState.Loaded;
        }

        public override AdLoadState GetLoadState(AdType type)
        {
            return type == AdType.Rewarded ? rewardedState : AdLoadState.NotLoaded;
        }

        public override void ShowRewarded(string placement, AdShowCallbacks callbacks)
        {
            if (!HasCredentials || !initialized)
            {
                DebugLog("[BlockOut][Ads] LevelPlay 未就绪，展示失败降级。");
                callbacks?.OnShowFailed?.Invoke();
                return;
            }
            if (rewardedState != AdLoadState.Loaded)
            {
                callbacks?.OnShowFailed?.Invoke();
                return;
            }

            // 抢占语义：新一次 Show 立即使旧请求失效，旧回调不会再收到任何事件（防跨局/重复发奖）。
            InvalidateActiveRequest();
            requestSeq++;
            activeRequestId = requestSeq;
            activePlacement = string.IsNullOrEmpty(placement) ? rewardedPlacementId : placement;
            activeCallbacks = callbacks;
            activeRewardFired = false;

            rewardedState = AdLoadState.Loading;   // 展示期间视为不可再展示
            // 正式接入点：IronSource.Agent.showRewardedVideo(activePlacement)
            DebugLog("[BlockOut][Ads] LevelPlay showRewardedVideo 占位：" + activePlacement);
            OnAdShown();
        }

        public override void ShowInterstitial(string placement, Action onClosed)
        {
            // 本期不启用插屏（R14：仅完成激励复活）。保留接口以满足契约。
            onClosed?.Invoke();
        }

        public override void ShowBanner() { DebugLog("[BlockOut][Ads] Banner 本期不启用。"); }
        public override void HideBanner() { }

        public override void Tick(float deltaTime)
        {
            // 正式接入时用于轮询可用性 / 超时保护；当前无 SDK 轮询为空实现。
        }

        // ---- 以下方法在接入 SDK 后由 IronSourceEvents 对应事件调用 ----

        internal void OnAdLoaded()
        {
            if (rewardedState == AdLoadState.Loading) rewardedState = AdLoadState.Loaded;
        }

        internal void OnAdShown()
        {
            activeCallbacks?.OnShown?.Invoke();
        }

        internal void OnAdShowFailed()
        {
            rewardedState = AdLoadState.Loaded;
            var cb = activeCallbacks;
            InvalidateActiveRequest();
            cb?.OnShowFailed?.Invoke();
        }

        internal void OnAdClosed()
        {
            rewardedState = AdLoadState.Loaded;
            var cb = activeCallbacks;
            bool rewarded = activeRewardFired;
            InvalidateActiveRequest();
            cb?.OnClosed?.Invoke();
            // 关闭回调本身不发奖；是否获奖完全由 OnAdRewarded 单独决定。
            _ = rewarded;
        }

        /// <summary>奖励回调：唯一发奖依据，对同一 requestId 只生效一次。</summary>
        internal void OnAdRewarded()
        {
            if (activeRequestId == 0) return;              // 无进行中请求
            if (activeRewardFired) return;                 // 重复回调，忽略
            activeRewardFired = true;
            var cb = activeCallbacks;
            cb?.OnRewarded?.Invoke();
        }

        /// <summary>可用性变化（onRewardedVideoAvailabilityChanged）。</summary>
        internal void OnAvailabilityChanged(bool available)
        {
            rewardedState = available ? AdLoadState.Loaded : AdLoadState.NotLoaded;
        }

        private void InvalidateActiveRequest()
        {
            activeRequestId = 0;
            activeCallbacks = null;
            activeRewardFired = false;
            activePlacement = null;
        }

        /// <summary>测试模式日志（实例方法：静态方法无法访问实例字段 isTestMode，C01）。</summary>
        private void DebugLog(string message)
        {
            if (isTestMode) UnityEngine.Debug.Log(message);
        }
    }
}
