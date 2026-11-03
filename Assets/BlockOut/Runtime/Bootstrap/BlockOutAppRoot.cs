using BlockOut.Contracts;
using BlockOut.Core;
using BlockOut.Infrastructure.Configuration;
using BlockOut.Infrastructure.Persistence;
using BlockOut.Infrastructure.Resources;
using UnityEngine;

namespace BlockOut.Bootstrap
{
    /// <summary>
    /// 唯一应用根（R03）。持有服务注册表与应用生命周期协调器，
    /// 跨场景对象全部挂在其下，替代过去多个互不归属的 DontDestroyOnLoad 对象。
    /// 支持显式销毁（编辑器停止/测试清理）。
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class BlockOutAppRoot : MonoBehaviour
    {
        public static BlockOutAppRoot Instance { get; private set; }

        /// <summary>启动配置快照（只读视图暴露给业务）。</summary>
        public BlockOutStartupConfig StartupConfig { get; private set; }
        public BlockOutAdConfig AdConfig { get; private set; }

        public BlockOutServiceRegistry Services { get; } = new BlockOutServiceRegistry();
        public BlockOutAppLifecycle Lifecycle { get; private set; }

        /// <summary>装配是否完成（业务只在 true 后接受输入）。</summary>
        public bool IsReady { get; private set; }

        public static BlockOutAppRoot Ensure(GameObject prefab)
        {
            if (Instance != null) return Instance;
            GameObject go = prefab != null
                ? Object.Instantiate(prefab)
                : new GameObject("BlockOut_AppRoot");
            go.name = "BlockOut_AppRoot";
            Instance = go.GetComponent<BlockOutAppRoot>() ?? go.AddComponent<BlockOutAppRoot>();
            Object.DontDestroyOnLoad(go);
            return Instance;
        }

        public void Configure(BlockOutStartupConfig startupConfig, BlockOutAdConfig adConfig)
        {
            StartupConfig = startupConfig;
            AdConfig = adConfig;
        }

        public void AttachLifecycle(BlockOutAppLifecycle lifecycle)
        {
            Lifecycle = lifecycle;
        }

        public void MarkReady()
        {
            IsReady = true;
        }

        /// <summary>显式销毁：释放服务订阅与跨场景对象（编辑器停止/测试用）。</summary>
        public void Shutdown()
        {
            if (Lifecycle != null) Lifecycle.Unbind();
            Services.DisposeAll();
            if (Instance == this) Instance = null;
            if (Application.isPlaying) Destroy(gameObject);
            else DestroyImmediate(gameObject);
        }

        void OnDestroy()
        {
            if (Instance == this) Instance = null;
        }

        // ---- 便捷访问（业务少写字面量解析）----

        public T Service<T>() where T : class { return Services.Resolve<T>(); }

        public BlockOutSaveService Save => Services.Resolve<BlockOutSaveService>();
        public BlockOutResourceService Resources => Services.Resolve<BlockOutResourceService>();
        public IAudioService Audio => Services.Resolve<IAudioService>();
        public IAdProvider Ads => Services.Resolve<IAdProvider>();
        public IAnalyticsService Analytics => Services.Resolve<IAnalyticsService>();
        public BlockOutCatalog Catalog => Services.Resolve<BlockOutCatalog>();
        public IAppConfigView ConfigView => StartupConfig;
    }
}
