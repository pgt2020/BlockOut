using System.Collections.Generic;

namespace TestRunner
{
    internal static class Program
    {
        private static int Main(string[] args)
        {
            // 离线运行环境无 Unity 协程/计时驱动，排除依赖 Unity 运行时的用例（[Category("UnityRuntime")]，
            // 如广告 SDK 回调）。若命令行显式传入 --where 则尊重用户意图。
            var effective = new List<string>(args);
            bool explicitWhere = false;
            for (int i = 0; i < effective.Count; i++)
            {
                if (effective[i] == "--where" || effective[i].StartsWith("--where="))
                {
                    explicitWhere = true;
                    break;
                }
            }
            if (!explicitWhere) effective.Add("--where=cat != UnityRuntime");
            return new NUnitLite.AutoRun().Execute(effective.ToArray());
        }
    }
}
