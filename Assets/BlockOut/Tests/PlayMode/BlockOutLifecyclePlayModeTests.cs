using System.Collections;
using BlockOut.Bootstrap;
using BlockOut.Contracts;
using BlockOut.Gameplay;
using BlockOut.Infrastructure.Persistence;
using BlockOut.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace BlockOut.Tests.PlayMode
{
    /// <summary>
    /// 生命周期与装配 PlayMode 测试（R19）。
    /// 覆盖：AppRoot 单例与显式销毁、服务注册表、主动暂停 vs 切后台暂停、
    /// 页面 Prefab 真实实例化与锚点绑定。
    /// 多指手势、真机切后台、真实广告回调**无法自动覆盖**，见交付文档手动验收清单。
    /// </summary>
    [TestFixture]
    public sealed class BlockOutLifecyclePlayModeTests
    {
        [TearDown]
        public void TearDown()
        {
            if (BlockOutAppRoot.Instance != null) BlockOutAppRoot.Instance.Shutdown();
        }

        [UnityTest]
        public IEnumerator AppRoot_Ensure返回单例_Shutdown后可重建()
        {
            var a = BlockOutAppRoot.Ensure(null);
            Assert.IsNotNull(a);
            var b = BlockOutAppRoot.Ensure(null);
            Assert.AreSame(a, b, "同一进程只允许一个 AppRoot");

            a.Shutdown();
            Assert.IsNull(BlockOutAppRoot.Instance, "Shutdown 后应清空单例");
            yield return null;
        }

        [Test]
        public void ServiceRegistry_注册解析与释放()
        {
            var reg = new BlockOutServiceRegistry();
            var store = new InMemoryProfileStore();
            reg.Register(store);
            Assert.IsTrue(reg.TryResolve(out IProfileStore resolved));
            Assert.AreSame(store, resolved);
            Assert.IsTrue(reg.IsRegistered<IProfileStore>());

            reg.DisposeAll();
            Assert.IsFalse(reg.IsRegistered<IProfileStore>());
        }

        [UnityTest]
        public IEnumerator 主动暂停_返回前台不擅自恢复()
        {
            var gm = new GameObject("GM_Test").AddComponent<BlockOutGameManager>();
            var life = new GameObject("Life_Test").AddComponent<BlockOutAppLifecycle>();
            life.Bind(gm);
            yield return null;   // 让 Awake/Start 跑完

            life.RequestUserPause();
            Assert.IsTrue(gm.IsPaused, "主动暂停应锁住输入");
            Assert.AreEqual(AppLifecycleState.UserPaused, life.State);
            Assert.IsFalse(life.WasAutoPaused);

            // 切回前台：不得自动 Resume 玩家主动暂停的对局
            life.NotifyAppResumed();
            yield return null;
            Assert.IsTrue(gm.IsPaused, "玩家主动暂停不得被前台回调解除");
            Assert.IsFalse(life.WasAutoPaused);

            // 玩家点"继续"才恢复
            life.RequestResume();
            Assert.IsFalse(gm.IsPaused);
            Assert.AreEqual(AppLifecycleState.Playing, life.State);

            Object.DestroyImmediate(gm.gameObject);
            Object.DestroyImmediate(life.gameObject);
        }

        [UnityTest]
        public IEnumerator 切后台暂停_标记自动暂停_回前台只请求暂停层()
        {
            var gm = new GameObject("GM_Test2").AddComponent<BlockOutGameManager>();
            var life = new GameObject("Life_Test2").AddComponent<BlockOutAppLifecycle>();
            bool pauseLayerRequested = false;
            life.OnAutoPauseNeedsPauseLayer += () => pauseLayerRequested = true;
            life.Bind(gm);
            yield return null;

            life.NotifyAppPaused();
            Assert.IsTrue(life.WasAutoPaused, "切后台必须置自动暂停标记");
            Assert.AreEqual(AppLifecycleState.AutoPaused, life.State);

            life.NotifyAppResumed();
            Assert.IsTrue(pauseLayerRequested, "回前台应请求补开暂停层");
            Assert.IsFalse(life.WasAutoPaused, "标记应被消费");

            Object.DestroyImmediate(gm.gameObject);
            Object.DestroyImmediate(life.gameObject);
            yield return null;
        }

        [UnityTest]
        public IEnumerator 广告覆盖层_退出后恢复原状态()
        {
            var gm = new GameObject("GM_Test3").AddComponent<BlockOutGameManager>();
            var life = new GameObject("Life_Test3").AddComponent<BlockOutAppLifecycle>();
            life.Bind(gm);
            yield return null;

            life.NotifyPlaying();
            Assert.AreEqual(AppLifecycleState.Playing, life.State);
            life.EnterAdOverlay();
            Assert.AreEqual(AppLifecycleState.AdOverlay, life.State);
            life.ExitAdOverlay();
            Assert.AreEqual(AppLifecycleState.Playing, life.State, "广告关闭后应回到原状态");

            Object.DestroyImmediate(gm.gameObject);
            Object.DestroyImmediate(life.gameObject);
        }

        [UnityTest]
        public IEnumerator 页面Prefab_可实例化且锚点可解析()
        {
            var prefab = BlockOutUIPrefabRegistry.Load(BlockOutScreenId.Board);
            if (prefab == null)
            {
                Assert.Ignore("BlockOutGameHud.prefab 尚未导入（需先在 Unity 中刷新资源）。");
                yield break;
            }
            var instance = Object.Instantiate(prefab);
            var view = instance.GetComponent<BlockOutPageView>();
            Assert.IsNotNull(view, "页面 Prefab 必须挂 BlockOutPageView");
            Assert.AreEqual(BlockOutScreenId.Board, view.ScreenId);
            Assert.IsTrue(view.HasAnchor("BoardArea"), "BoardArea 锚点必须存在（棋盘挂点契约）");
            Assert.IsTrue(view.HasAnchor("TopHUD"));
            Assert.IsTrue(view.HasAnchor("Toolbar"));
            Object.DestroyImmediate(instance);
            yield return null;
        }

        [UnityTest]
        public IEnumerator 启动序列_必选步骤失败即整体失败()
        {
            var root = BlockOutAppRoot.Ensure(null);
            root.Configure(null, null);   // 缺配置 → LocalConfig 必选步骤应失败
            var seq = new BlockOutStartupSequence(null, null, root.Services);
            var runner = seq.Run();
            while (runner.MoveNext()) yield return runner.Current;
            Assert.IsFalse(seq.Succeeded, "缺启动配置必须判失败，不能静默放行");
            Assert.IsNotNull(seq.FailureReason);
        }
    }
}
