using System.Globalization;
using BlockOut.Infrastructure.Configuration;
using UnityEngine;

namespace BlockOut.Bootstrap
{
    /// <summary>
    /// 应用级运行时配置应用器（R03/R05）。
    /// 对应参考工程 GameLauncher.Awake 的职责，但值来自 <see cref="BlockOutStartupConfig"/> 资产，
    /// 开发/发布切换不改代码。全部为幂等操作，可重复调用。
    /// </summary>
    public static class BlockOutAppRuntimeConfig
    {
        public static void Apply(BlockOutStartupConfig config)
        {
            int frameRate = config != null ? config.targetFrameRate : 60;
            bool runInBackground = config != null && config.runInBackground;
            bool invariant = config == null || config.forceInvariantCulture;
            bool verbose = config == null || config.verboseLog;

            Application.targetFrameRate = frameRate;
            Application.runInBackground = runInBackground;
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            Input.multiTouchEnabled = true;          // 游戏区双指缩放
            if (invariant)
            {
                // 部分语言小数分隔符不是 "."，强制 en-US 避免字符串转 float 报错
                CultureInfo.DefaultThreadCurrentCulture = new CultureInfo("en-US");
            }
            Debug.unityLogger.logEnabled = verbose;
        }

        /// <summary>恢复编辑器默认（测试用）。</summary>
        public static void ResetForTests()
        {
            Application.targetFrameRate = 60;
            Application.runInBackground = false;
            Debug.unityLogger.logEnabled = true;
        }
    }
}
