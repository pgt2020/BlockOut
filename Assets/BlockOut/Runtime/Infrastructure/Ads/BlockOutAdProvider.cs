using System;
using BlockOut.Contracts;
using UnityEngine;

namespace BlockOut.Infrastructure.Ads
{
    /// <summary>
    /// 旧版开发替身（保留类名兼容既有调用，语义与 <see cref="DevelopmentAdProvider"/> 一致）。
    /// 禁止进入正式构建：构建前检查会扫描本类型并被 <see cref="DevelopmentAdProvider.IsDevelopmentOnly"/> 标记拦截。
    /// </summary>
    public sealed class FakeAdProvider : AdProviderBase
    {
        public bool SimulateCancel;
        public float SimulatedLoadSeconds = 1.2f;

        private float loadTimer = -1f;
        private int requestSeq;
        private int activeRequestId;
        private AdShowCallbacks activeCallbacks;
        private bool rewardFired;

        public bool IsDevelopmentOnly => true;

        public override void Init()
        {
            loadTimer = SimulatedLoadSeconds;
            Debug.Log("[BlockOut][Ads] FakeAdProvider initialized (no real ads). Rewarded ad 'loading' for "
                + loadTimer + "s to exercise loading state.");
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
            return loadTimer > 0f ? AdLoadState.Loading : AdLoadState.Loaded;
        }

        public override void ShowRewarded(string placement, AdShowCallbacks callbacks)
        {
            if (!IsReady(AdType.Rewarded))
            {
                Debug.Log("[BlockOut] Fake rewarded ad not ready for '" + placement + "'.");
                callbacks?.OnShowFailed?.Invoke();
                return;
            }
            requestSeq++;
            activeRequestId = requestSeq;
            activeCallbacks = callbacks;
            rewardFired = false;

            bool success = !SimulateCancel;
            Debug.Log("[BlockOut] Fake rewarded ad shown for '" + placement + "'. Result: " + success);
            callbacks?.OnShown?.Invoke();
            if (success)
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
            Debug.Log("[BlockOut] Fake interstitial for '" + placement + "'. Closing.");
            onClosed?.Invoke();
        }

        public override void ShowBanner() { Debug.Log("[BlockOut] Fake banner shown."); }
        public override void HideBanner() { }
    }
}
