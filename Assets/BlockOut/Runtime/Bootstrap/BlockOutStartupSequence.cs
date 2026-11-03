using System;
using System.Collections;
using System.Collections.Generic;
using BlockOut.Config;
using BlockOut.Contracts;
using BlockOut.Core;
using BlockOut.Infrastructure.Ads;
using BlockOut.Infrastructure.Analytics;
using BlockOut.Infrastructure.Configuration;
using BlockOut.Infrastructure.Persistence;
using BlockOut.Infrastructure.Resources;
using UnityEngine;

namespace BlockOut.Bootstrap
{
    /// <summary>
    /// 显式启动序列（R04）。步骤顺序固定、可报告进度、可超时、失败策略明确。
    /// 由 <see cref="BlockOutLauncher"/> 驱动协程；本身不是 MonoBehaviour，便于测试复用。
    /// </summary>
    public sealed class BlockOutStartupSequence
    {
        private readonly List<BlockOutStartupStep> steps = new List<BlockOutStartupStep>();
        private readonly StartupStepContext ctx = new StartupStepContext();

        public BlockOutStartupConfig Config { get; private set; }
        public BlockOutAdConfig AdConfig { get; private set; }
        public BlockOutServiceRegistry Services { get; private set; }

        public bool EnableVerboseLog { get; set; }
        public int TotalSteps => steps.Count;
        public int CompletedSteps { get; private set; }
        public float CurrentStepProgress { get; set; }
        public string CurrentStepName { get; private set; }
        public bool Succeeded { get; private set; }
        public string FailureReason { get; private set; }
        public IReadOnlyList<BlockOutStartupStep> Steps => steps;

        public BlockOutStartupSequence(BlockOutStartupConfig config, BlockOutAdConfig adConfig, BlockOutServiceRegistry services)
        {
            Config = config;
            AdConfig = adConfig;
            Services = services;
            ctx.Owner = this;
            ctx.Services = services;
            EnableVerboseLog = config != null && config.EnableVerboseLog;
            BuildSteps();
        }

        private void BuildSteps()
        {
            float timeout = Config != null ? Config.StartupStepTimeoutSeconds : 10f;

            steps.Add(new BlockOutStartupStep("LocalConfig", "本地启动配置", false, timeout, ctx2 =>
            {
                ctx2.ReportProgress(0.2f);
                if (Config == null) throw new InvalidOperationException("缺少 BlockOutStartupConfig 资产");
                ctx2.ReportProgress(1f);
                return Empty();
            }));

            steps.Add(new BlockOutStartupStep("ApplicationConfig", "帧率 / 输入 / 生命周期配置", false, timeout, ctx2 =>
            {
                BlockOutAppRuntimeConfig.Apply(Config);
                ctx2.ReportProgress(1f);
                return Empty();
            }));

            // GameplayConfig 必须在 ProfileMigration（新档创建）之前生效：
            // 新档金币/道具库存、解锁关卡、复活与奖励数值都以本地 JSON 为唯一来源；
            // 后续 ApplyLocalDefaults 只做同步，不再覆盖回旧常量。
            steps.Add(new BlockOutStartupStep("GameplayConfig", "本地玩法配置（ArtOut 对齐基线）", false, timeout, ctx2 =>
            {
                var gameplayConfig = BlockOutGameplayConfigLoader.LoadAndActivate();
                BlockOutContentConfig.Apply(gameplayConfig);
                Services.Register(gameplayConfig);
                ctx2.ReportProgress(1f);
                return Empty();
            }));

            steps.Add(new BlockOutStartupStep("ProfileMigration", "存档加载与版本迁移", false, timeout, ctx2 =>
            {
                var save = new BlockOutSaveService();
                save.Load();
                Services.Register(save);
                ctx2.ReportProgress(1f);
                return Empty();
            }));

            steps.Add(new BlockOutStartupStep("ContentCatalog", "关卡清单与内容配置", false, timeout, ctx2 =>
            {
                BlockOutRemoteConfigBridge.ApplyLocalDefaults();
                var catalog = new BlockOutCatalog();
                catalog.Load();
                Services.Register(catalog);
                ctx2.ReportProgress(1f);
                return Empty();
            }));

            steps.Add(new BlockOutStartupStep("OptionalServices", "广告 / 统计服务（可选）", true, timeout, ctx2 =>
            {
                // 广告：按配置注入 LevelPlay 适配器；缺凭据时开发档用替身，正式档保持未就绪。
                IAdProvider ads = CreateAds();
                Services.Register(ads);
                ads.Init();

                // 统计：本地语义事件实现（未接 SDK），模块矩阵记录缺口。
                var analytics = new BlockOutAnalyticsService(EnableVerboseLog);
                Services.Register(analytics);
                BlockOutAnalyticsModuleMatrix.LogMatrix();
                ctx2.ReportProgress(1f);
                return Empty();
            }));

            steps.Add(new BlockOutStartupStep("Resources", "资源服务与预热计划", false, timeout, ctx2 =>
            {
                var resources = new BlockOutResourceService();
                Services.Register(resources);
                Services.Register<IAudioService>(resources);
                Services.Register(new BlockOutPreloadPlanHolder(BlockOutPreloadPlan.CreateDefault()));
                ctx2.ReportProgress(1f);
                return Empty();
            }));

            steps.Add(new BlockOutStartupStep("AppReady", "应用就绪", false, timeout, ctx2 =>
            {
                Succeeded = true;
                ctx2.ReportProgress(1f);
                return Empty();
            }));

            steps.Add(new BlockOutStartupStep("DeferredPreload", "延后预热（章节大图 / 音频）", true, timeout, ctx2 =>
            {
                if (Config == null || !Config.deferredPreload) { ctx2.ReportProgress(1f); return Empty(); }
                return DeferredPreloadRoutine(ctx2);
            }));
        }

        private IAdProvider CreateAds()
        {
            bool devAllowsFake = Config != null && Config.AllowFakeServices;
            bool adsEnabled = AdConfig != null && AdConfig.adsEnabled;

            if (AdConfig != null && AdConfig.HasCredentials)
            {
                var adapter = new LevelPlayAdAdapter(AdConfig.levelPlayAppKey, AdConfig.rewardedPlacementId, AdConfig.levelPlayTestMode);
                Services.Register(adapter);
                return adapter;
            }
            if (adsEnabled && devAllowsFake)
            {
                // 明确标注的开发替身；发布门禁会阻止其进入正式包。
                return new DevelopmentAdProvider();
            }
            if (adsEnabled)
            {
                Debug.LogWarning("[BlockOut][Ads] 广告已启用但缺 LevelPlay 配置，保持未就绪（不模拟成功）。");
            }
            return new BlockOut.Infrastructure.Ads.BlockOutNullAdProvider();
        }

        private IEnumerator DeferredPreloadRoutine(StartupStepContext ctx2)
        {
            if (!Services.TryResolve<BlockOutResourceService>(out var res))
            {
                ctx2.ReportProgress(1f);
                yield break;
            }
            var holder = Services.Resolve<BlockOutPreloadPlanHolder>();
            var plan = holder != null ? holder.Plan : null;
            if (plan == null) { ctx2.ReportProgress(1f); yield break; }

            var paths = new List<string>();
            foreach (var p in plan.deferredSprites) paths.Add(p);
            foreach (var p in plan.deferredAudio) paths.Add(BlockOutResourcePaths.BlockOutAudio + "/" + p);

            for (int i = 0; i < paths.Count; i++)
            {
                res.Load<Sprite>(paths[i]);
                ctx2.ReportProgress(paths.Count == 0 ? 1f : (i + 1f) / paths.Count);
                yield return null;   // 空闲帧分摊，避免启动卡顿
            }
            ctx2.ReportProgress(1f);
        }

        private static IEnumerator Empty() { yield break; }

        public IEnumerator Run()
        {
            Succeeded = false;
            FailureReason = null;
            CompletedSteps = 0;
            for (int i = 0; i < steps.Count; i++)
            {
                var step = steps[i];
                CurrentStepName = step.DisplayName;
                CurrentStepProgress = 0f;
                float elapsed = 0f;
                bool timedOut = false;

                var runner = step.Invoke(ctx);
                while (true)
                {
                    bool moved;
                    try { moved = runner.MoveNext(); }
                    catch (Exception e)
                    {
                        step.State = StartupStepState.Failed;
                        step.Error = e.Message;
                        break;
                    }
                    if (!moved) break;
                    elapsed += Time.deltaTime;
                    if (elapsed > step.TimeoutSeconds)
                    {
                        timedOut = true;
                        step.State = StartupStepState.TimedOut;
                        step.Error = "超时 " + step.TimeoutSeconds + "s";
                        break;
                    }
                    yield return runner.Current;
                }

                if (step.State == StartupStepState.Succeeded || step.State == StartupStepState.Skipped)
                {
                    CompletedSteps++;
                    continue;
                }
                if (step.Optional)
                {
                    Debug.LogWarning("[BlockOut][Startup] 可选步骤 '" + step.Id + "' " + step.State + "：" + step.Error + "（降级继续）");
                    step.State = StartupStepState.Skipped;
                    CompletedSteps++;
                    continue;
                }
                FailureReason = "启动步骤 '" + step.Id + "' " + step.State + "：" + step.Error;
                yield break;
            }
        }
    }

    /// <summary>预热计划持有者（避免把 ScriptableObject 依赖塞进注册表层）。</summary>
    public sealed class BlockOutPreloadPlanHolder
    {
        public BlockOutPreloadPlan Plan { get; }
        public BlockOutPreloadPlanHolder(BlockOutPreloadPlan plan) { Plan = plan; }
    }
}
