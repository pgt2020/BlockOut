using System;
using BlockOut.Contracts;
using UnityEngine;

namespace BlockOut.Infrastructure.Ads
{
    /// <summary>
    /// 未配置广告时的空实现（R14/R16）：任何请求都走"未就绪 / 展示失败"，绝不模拟成功。
    /// 正式包缺 LevelPlay 凭据时使用本实现 + 发布门禁报错，二者叠加保证不会静默放行。
    /// </summary>
    public sealed class BlockOutNullAdProvider : AdProviderBase
    {
        public override void Init() { Debug.Log("[BlockOut][Ads] 广告未启用（NullAdProvider）。"); }
        public override bool IsReady(AdType type) { return false; }
        public override AdLoadState GetLoadState(AdType type) { return AdLoadState.NotLoaded; }
        public override void ShowRewarded(string placement, AdShowCallbacks callbacks) { callbacks?.OnShowFailed?.Invoke(); }
        public override void ShowInterstitial(string placement, Action onClosed) { onClosed?.Invoke(); }
        public override void ShowBanner() { }
        public override void HideBanner() { }
    }
}
