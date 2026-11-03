using System;

namespace BlockOut.Contracts
{
    /// <summary>广告类型。本期只启用激励广告（复活），Banner/插屏不默认开启。</summary>
    public enum AdType { Rewarded, Interstitial, Banner }

    /// <summary>
    /// 广告加载状态（R14：加载与展示必须分别建模）。
    /// 不能只用 bool 表示就绪——"加载中"与"未加载"对 UI 提示完全不同。
    /// </summary>
    public enum AdLoadState { NotLoaded, Loading, Loaded, Failed }

    /// <summary>
    /// 激励广告展示的显式回调集合（R14）。
    /// 五类事件分别建模，语义互不重叠：
    /// - OnLoaded     广告资源已就绪（可展示前）
    /// - OnShown      广告已 actually 显示在屏幕上
    /// - OnShowFailed 展示失败（未就绪/无填充/被其他展示抢占）
    /// - OnClosed     广告关闭——**不等于获奖**，关闭回调本身绝不发奖
    /// - OnRewarded   奖励回调——**唯一**的发奖依据，每次 Show 至多触发一次
    /// </summary>
    public sealed class AdShowCallbacks
    {
        public Action OnLoaded;
        public Action OnShown;
        public Action OnShowFailed;
        public Action OnClosed;
        public Action OnRewarded;

        public static AdShowCallbacks Create(
            Action onLoaded = null, Action onShown = null, Action onShowFailed = null,
            Action onClosed = null, Action onRewarded = null)
        {
            return new AdShowCallbacks
            {
                OnLoaded = onLoaded,
                OnShown = onShown,
                OnShowFailed = onShowFailed,
                OnClosed = onClosed,
                OnRewarded = onRewarded,
            };
        }
    }

    /// <summary>
    /// 广告 Provider 抽象（既有契约，保持兼容）。
    /// 正式实现包装 Unity LevelPlay（ironSource）；开发版可用明确标注的替身。
    /// 实现必须保证：<see cref="AdShowCallbacks.OnRewarded"/> 每次 Show 至多触发一次，
    /// 且跨局/重复回调不得被调用方当作第二次获奖（由调用方令牌 + 本接口的单次保证共同防护）。
    /// </summary>
    public interface IAdProvider
    {
        void Init();
        void Tick(float deltaTime);

        bool IsReady(AdType type);
        AdLoadState GetLoadState(AdType type);

        /// <summary>兼容签名：仅区分"是否获奖"。内部转调显式回调版本，关闭/失败均视为未获奖。</summary>
        void ShowRewarded(string placement, Action<bool> onDone);

        /// <summary>显式回调版本：加载/展示/展示失败/关闭/奖励分别通知。</summary>
        void ShowRewarded(string placement, AdShowCallbacks callbacks);

        void ShowInterstitial(string placement, Action onClosed);
        void ShowBanner();
        void HideBanner();
    }
}
