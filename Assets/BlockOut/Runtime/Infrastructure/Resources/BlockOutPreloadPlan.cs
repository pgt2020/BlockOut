using System;
using System.Collections.Generic;
using BlockOut.Core;
using UnityEngine;

namespace BlockOut.Infrastructure.Resources
{
    /// <summary>预热阶段（R10）：与启动步骤一一对应。</summary>
    public enum PreloadStage { FirstScreen, Level, Deferred }

    /// <summary>
    /// 分阶段预热计划（R10，参考 ArtOutStartupPrefabLoadPlan 的组织方式）。
    /// 三类资源分清：首屏必需 / 进入关卡必需 / 延后（章节大图、特效）。
    /// 必需失败 → 明确报错并可重试；可选失败 → 降级继续，不阻塞启动。
    /// </summary>
    [Serializable]
    public sealed class BlockOutPreloadPlan
    {
        [Header("首屏必需（失败阻断启动）")]
        public string[] requiredFirstScreenPrefabs = new string[0];
        public string[] requiredFirstScreenSprites = new string[0];

        [Header("首屏可选（失败降级）")]
        public string[] optionalFirstScreenSprites = new string[0];

        [Header("进入关卡必需")]
        public string[] levelRequiredSprites = new string[0];

        [Header("延后预热（空闲帧分摊，失败仅记录）")]
        public string[] deferredSprites = new string[0];
        public string[] deferredAudio = new string[0];

        /// <summary>
        /// 默认计划。章节大图**不**在首屏一次性加载（R10：不一次加载全部章节大图），
        /// 第一章 3 张 1080×1080 放延后段，进入收藏页时按需加载。
        /// </summary>
        public static BlockOutPreloadPlan CreateDefault()
        {
            // C01：普通 [Serializable] 类不是 ScriptableObject，没有 CreateInstance；用 new 构造。
            var plan = new BlockOutPreloadPlan();
            plan.requiredFirstScreenPrefabs = new[]
            {
                "Prefabs/UI/BlockOutHomePage",
                "Prefabs/UI/BlockOutGameHud",
                "Prefabs/UI/BlockOutPopupLayer",
            };
            plan.optionalFirstScreenSprites = new[]
            {
                "block/ch01/preview",
                "block/ch01/silhouette",
            };
            plan.deferredSprites = new[]
            {
                "block/ch01/full",
            };
            plan.deferredAudio = new string[0];
            return plan;
        }

        public IEnumerable<string> Enumerate(PreloadStage stage)
        {
            switch (stage)
            {
                case PreloadStage.FirstScreen:
                    foreach (var p in requiredFirstScreenPrefabs) yield return p;
                    foreach (var p in optionalFirstScreenSprites) yield return p;
                    yield break;
                case PreloadStage.Level:
                    foreach (var p in levelRequiredSprites) yield return p;
                    yield break;
                default:
                    foreach (var p in deferredSprites) yield return p;
                    yield break;
            }
        }
    }
}
