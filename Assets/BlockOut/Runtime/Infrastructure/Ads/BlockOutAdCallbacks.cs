using System;
using BlockOut.Contracts;

namespace BlockOut.Infrastructure.Ads
{
    /// <summary>
    /// Provider 公共基类：把兼容签名 <see cref="IAdProvider.ShowRewarded(string, Action{bool})"/>
    /// 转成显式五回调版本，避免每个实现各写一遍"关闭/失败都算未获奖"的规则。
    /// </summary>
    public abstract class AdProviderBase : IAdProvider
    {
        public abstract void Init();
        public virtual void Tick(float deltaTime) { }
        public abstract bool IsReady(AdType type);
        public abstract AdLoadState GetLoadState(AdType type);
        public abstract void ShowRewarded(string placement, AdShowCallbacks callbacks);
        public abstract void ShowInterstitial(string placement, Action onClosed);
        public abstract void ShowBanner();
        public abstract void HideBanner();

        /// <summary>兼容签名：只有 OnRewarded 会给出 true；关闭与展示失败一律 false。</summary>
        public void ShowRewarded(string placement, Action<bool> onDone)
        {
            bool rewarded = false;
            var cb = AdShowCallbacks.Create(
                onRewarded: () => rewarded = true,
                onClosed: () => { onDone?.Invoke(rewarded); },
                onShowFailed: () => { onDone?.Invoke(false); });
            ShowRewarded(placement, cb);
        }
    }
}
