using System;
using BlockOut.Contracts;

namespace BlockOut.Infrastructure.Ads
{
    /// <summary>
    /// 开发/测试替身广告 Provider（R16：**禁止进入正式构建**）。
    /// 与旧 FakeAdProvider 的区别：
    /// - 显式标注 <see cref="IsDevelopmentOnly"/>，构建前检查会拦截；
    /// - 五类回调分别触发，可演练"加载中 / 展示 / 关闭 / 奖励"全流程；
    /// - 默认不自动发奖（SimulateReward=false），必须显式打开，避免误把模拟成功当正式广告成功。
    /// </summary>
    public sealed class DevelopmentAdProvider : AdProviderBase
    {
        public const string DevelopmentOnlyMarker = "DEVELOPMENT_ONLY_AD_PROVIDER";

        public bool IsDevelopmentOnly => true;
        public bool SimulateCancel;
        public bool SimulateReward = true;
        public float SimulatedLoadSeconds = 1.2f;

        private float loadTimer = -1f;
        private int requestSeq;
        private int activeRequestId;
        private AdShowCallbacks activeCallbacks;
        private bool rewardFired;

        public override void Init()
        {
            loadTimer = SimulatedLoadSeconds;
            UnityEngine.Debug.Log("[BlockOut][Ads] DevelopmentAdProvider 已启用（仅开发版，正式包必须替换为 LevelPlay）。");
        }

        public override void Tick(float deltaTime)
        {
            if (loadTimer > 0f) loadTimer -= deltaTime;
        }

        public override bool IsReady(AdType type)
        {
            return type == AdType.Rewarded && loadTimer <= 0f;
        }

        public override AdLoadState GetLoadState(AdType type)
        {
            if (type != AdType.Rewarded) return AdLoadState.NotLoaded;
            if (loadTimer > 0f) return AdLoadState.Loading;
            return AdLoadState.Loaded;
        }

        public override void ShowRewarded(string placement, AdShowCallbacks callbacks)
        {
            if (!IsReady(AdType.Rewarded))
            {
                callbacks?.OnShowFailed?.Invoke();
                return;
            }
            requestSeq++;
            activeRequestId = requestSeq;
            activeCallbacks = callbacks;
            rewardFired = false;

            callbacks?.OnShown?.Invoke();
            if (SimulateReward && !SimulateCancel)
            {
                rewardFired = true;
                callbacks?.OnRewarded?.Invoke();
            }
            callbacks?.OnClosed?.Invoke();
            activeRequestId = 0;
            activeCallbacks = null;
        }

        public override void ShowInterstitial(string placement, Action onClosed)
        {
            onClosed?.Invoke();
        }

        public override void ShowBanner() { }
        public override void HideBanner() { }
    }
}
