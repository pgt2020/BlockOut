using System;
using BlockOut.Contracts;
using UnityEngine;

namespace BlockOut.Infrastructure.Configuration
{
    /// <summary>
    /// 启动配置（R05）。区分 Editor / Development / Release 三档，
    /// 开发切换只改资产、不改业务代码。资产位置：Assets/BlockOut/Settings/。
    /// </summary>
    [CreateAssetMenu(menuName = "BlockOut/Startup Config", fileName = "BlockOutStartupConfig")]
    public sealed class BlockOutStartupConfig : ScriptableObject, IAppConfigView
    {
        public enum Environment { Editor, Development, Release }

        [Header("环境")]
        public Environment environment = Environment.Development;

        [Header("应用")]
        public int targetFrameRate = 60;
        public bool runInBackground;
        [Tooltip("多语言设备下强制 en-US 小数文化，避免字符串转 float 报错")]
        public bool forceInvariantCulture = true;
        public bool verboseLog = true;

        [Header("启动")]
        [Tooltip("单步超时（秒）。可选 SDK 超时不阻塞启动。")]
        public float startupStepTimeoutSeconds = 10f;
        [Tooltip("就绪后是否在空闲帧继续延后预热")]
        public bool deferredPreload = true;

        [Header("资源")]
        [Tooltip("是否预热章节大图（第一章仅 3 张 1080x1080，默认开）")]
        public bool preloadChapterArt = true;
        [Tooltip("首屏是否预热全部音效")]
        public bool preloadAudio = true;

        [Header("服务（开发替身）")]
        [Tooltip("允许使用开发替身（假广告等）。Release 必须为 false，发布门禁会拦截。")]
        public bool allowFakeServices = true;
        public bool adsEnabled;

        [Header("启动页")]
        public bool showStartupSplash = true;
        [Tooltip("启动页最短展示时长（秒），避免进度条一闪而过")]
        public float splashMinSeconds = 0.6f;

        public string EnvironmentName => environment.ToString();
        public bool EnableVerboseLog => verboseLog;
        public bool AllowFakeServices => allowFakeServices;
        public int TargetFrameRate => targetFrameRate;
        public bool RunInBackground => runInBackground;
        public bool PreloadChapterArt => preloadChapterArt;
        public float StartupStepTimeoutSeconds => startupStepTimeoutSeconds;
        public bool AdsEnabled => adsEnabled;

        /// <summary>发布配置自检：Release 档不允许开发替身与详细日志。</summary>
        public bool ValidateRelease(out string error)
        {
            error = null;
            if (environment != Environment.Release) return true;
            if (allowFakeServices) { error = "Release 配置不允许 allowFakeServices=true（会启用模拟广告）"; return false; }
            if (verboseLog) { error = "Release 配置不允许 verboseLog=true（开发日志）"; return false; }
            return true;
        }

        /// <summary>Editor 档默认值：等价于历史行为（60fps、后台运行关、日志开）。</summary>
        public static BlockOutStartupConfig CreateEditorDefault()
        {
            var c = CreateInstance<BlockOutStartupConfig>();
            c.environment = Environment.Editor;
            c.targetFrameRate = 60;
            c.runInBackground = false;
            c.verboseLog = true;
            c.allowFakeServices = true;
            c.adsEnabled = false;
            c.startupStepTimeoutSeconds = 10f;
            c.deferredPreload = true;
            c.preloadChapterArt = true;
            c.preloadAudio = true;
            c.showStartupSplash = true;
            c.splashMinSeconds = 0.6f;
            return c;
        }
    }
}
