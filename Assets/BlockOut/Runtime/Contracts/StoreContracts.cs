using System;
using System.Collections.Generic;

namespace BlockOut.Contracts
{
    /// <summary>
    /// 存档存储抽象（R13）。PlayerPrefs 实现见 BlockOut.Infrastructure.Persistence；
    /// 测试可注入内存实现以模拟"保存失败"。
    /// </summary>
    public interface IProfileStore
    {
        bool Has(string key);
        string Get(string key);
        void Set(string key, string value);
        void Delete(string key);
        /// <summary>提交到持久介质。返回 false 表示写入失败（调用方必须回滚内存状态）。</summary>
        bool Commit();
    }

    /// <summary>
    /// 只读配置视图（R05/R09）。业务代码只读快照，不直接持有 ScriptableObject 资产，
    /// 以便开发/发布切换不需要改业务代码，也便于测试替换。
    /// </summary>
    public interface IAppConfigView
    {
        string EnvironmentName { get; }
        bool EnableVerboseLog { get; }
        bool AllowFakeServices { get; }
        int TargetFrameRate { get; }
        bool RunInBackground { get; }
        bool PreloadChapterArt { get; }
        float StartupStepTimeoutSeconds { get; }
        bool AdsEnabled { get; }
    }

    /// <summary>
    /// 音频服务契约（R10 预热 + 播放辅助）。
    /// 既有 BlockOutSettings 继续负责开关与即时生效；本服务负责预热与统一播放入口。
    /// </summary>
    public interface IAudioService
    {
        void Warmup(IEnumerable<string> clipIds);
        void Play(string clipId, float volumeScale = 1f);
        void PlayMusic(string clipId);
        void StopMusic();
        void Release(string clipId);
        void ReleaseAll();
    }
}
