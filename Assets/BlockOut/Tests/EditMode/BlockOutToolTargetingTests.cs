using System.Collections.Generic;
using BlockOut.Contracts;
using BlockOut.Core;
using BlockOut.Gameplay;
using BlockOut.Infrastructure.Ads;
using NUnit.Framework;
using UnityEngine;

namespace BlockOut.Tests.EditMode
{
    /// <summary>
    /// 道具目标选取与广告契约测试（R14/R17）。
    /// 重点：逐次重选、无目标不扣库存、奖励回调单次、关闭≠获奖、缺凭据安全降级。
    /// </summary>
    [TestFixture]
    public sealed class BlockOutToolTargetingTests
    {
        private static BlockOutLevelData SerialLevel()
        {
            var level = new BlockOutLevelData { Id = "t", Width = 3, Height = 1 };
            for (int i = 0; i < 3; i++)
                level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = i, Direction = BlockOutDirection.Right });
            return level;
        }

        [Test]
        public void 魔法目标_串行解锁逐次重选_上限3()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(SerialLevel());
            var tools = new BlockOutToolController(rules, 0, 0, 1);

            var picked = tools.PickMagicTargets(3);
            Assert.AreEqual(3, picked.Count);
            Assert.AreEqual(2, picked[0].Column, "第一目标必须是当前真能飞的那块");

            // 逐次提交：每轮按最新棋盘重选
            int removed = 0;
            foreach (var t in picked)
            {
                Assert.IsTrue(rules.CanMove(t), "被选目标在其轮次必须真的可飞");
                rules.Remove(t);
                removed++;
            }
            Assert.AreEqual(3, removed);
            Assert.IsTrue(rules.IsWon);
        }

        private static BlockOutLevelData DeadlockLevel()
        {
            // 2×1 棋盘两块互堵：A(0)Right 被 B 挡，B(1)Left 被 A 挡——两块都不可飞
            var level = new BlockOutLevelData { Id = "deadlock", Width = 2, Height = 1 };
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 1, Direction = BlockOutDirection.Left });
            return level;
        }

        [Test]
        public void 魔法目标_只有一块可飞时只选一块_不会凑数()
        {
            var level = new BlockOutLevelData { Id = "single", Width = 2, Height = 1 };
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 1, Direction = BlockOutDirection.Right });

            var rules = new BlockOutGameRules();
            rules.StartLevel(level);
            var tools = new BlockOutToolController(rules, 0, 0, 1);

            // 阶段 C：选目标改为参考语义——施法前链式模拟逐次移除（PickMagicTargets），
            // "先移除 B 后 A 才可飞"的目标链合法，因此两块都会被选入（不是凑数，是链式解锁）。
            var picked = tools.PickMagicTargets(3);
            Assert.AreEqual(2, picked.Count, "链式模拟覆盖逐次解锁的两块");
            Assert.AreEqual(1, picked[0].Column, "先选当前真能飞的 B");
            Assert.AreEqual(0, picked[1].Column, "再选移除 B 后才可飞的 A");
            foreach (var t in picked)
            {
                Assert.IsTrue(rules.CanMove(t), "被选目标在其轮次必须真的可飞");
                rules.Remove(t);
            }
            Assert.IsTrue(rules.IsWon);
        }

        [Test]
        public void 无目标_不扣库存()
        {
            // 互堵局面：两块都不可飞 → 无合法目标
            var rules = new BlockOutGameRules();
            rules.StartLevel(DeadlockLevel());
            var tools = new BlockOutToolController(rules, 0, 0, 1);

            Assert.IsFalse(rules.CanMove(rules.Blocks[0]), "互堵块不可飞");
            Assert.IsFalse(rules.CanMove(rules.Blocks[1]), "互堵块不可飞");
            Assert.AreEqual(0, tools.PickMagicTargets(3).Count, "无合法目标");
            Assert.AreEqual(1, tools.GetCount(BlockOutToolId.Magic), "无目标时不得扣库存");
        }

        [Test]
        public void 提示目标_必须是当前真能飞的块()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(SerialLevel());
            var tools = new BlockOutToolController(rules, 1, 0, 0);

            var hint = tools.TryUseHint();
            Assert.IsNotNull(hint);
            Assert.IsTrue(rules.CanMove(hint), "提示不得指向玩家点不动的块");
            Assert.AreEqual(0, tools.GetCount(BlockOutToolId.Hint), "使用后扣库存");
        }

        [Test]
        public void 锤子_可消任意在场块()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(DeadlockLevel());
            var tools = new BlockOutToolController(rules, 0, 1, 0);

            var blocked = rules.Blocks[0];
            Assert.IsFalse(rules.CanMove(blocked), "互堵块不可飞");
            Assert.IsTrue(tools.EnterHammerMode(), "先进选择态");
            Assert.IsTrue(tools.TryHammerRemove(blocked), "锤子应可移除被挡块");
            Assert.IsFalse(blocked.Active);
            Assert.IsFalse(tools.IsHammerSelecting, "命中后自动退出选择态");
            Assert.AreEqual(1, rules.RemainingBlocks);
            Assert.AreEqual(0, tools.GetCount(BlockOutToolId.Hammer), "命中扣 1 库存");
        }

        [Test]
        public void 锤子模式_进入与取消可切换()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(SerialLevel());
            var tools = new BlockOutToolController(rules, 0, 1, 0);

            Assert.IsTrue(tools.EnterHammerMode());
            Assert.IsTrue(tools.IsHammerSelecting);
            tools.CancelHammerMode();
            Assert.IsFalse(tools.IsHammerSelecting);
        }

        // ---- 广告契约（R14）----

        [Test]
        public void 缺凭据适配器_安全降级不假装就绪()
        {
            var adapter = new LevelPlayAdAdapter("", "", false);
            adapter.Init();
            Assert.IsFalse(adapter.IsReady(AdType.Rewarded));
            Assert.AreEqual(AdLoadState.NotLoaded, adapter.GetLoadState(AdType.Rewarded));

            bool failed = false;
            adapter.ShowRewarded("revive", AdShowCallbacks.Create(onShowFailed: () => failed = true));
            Assert.IsTrue(failed, "展示必须失败而不是假装成功");
        }

        // 依赖 Unity 运行时（广告适配器回调经协程/计时推进；离线桩 Time.time 不流动）——仅 Unity 编辑器运行
        [Test]
        [Category("UnityRuntime")]
        public void 奖励回调_同一请求只触发一次()
        {
            var adapter = new LevelPlayAdAdapter("key", "placement", false);
            adapter.Init();
            adapter.OnAdLoaded();
            // 直接驱动内部事件（SDK 接入后由 IronSourceEvents 调用）
            int rewarded = 0;
            adapter.ShowRewarded("revive", AdShowCallbacks.Create(onRewarded: () => rewarded++));
            adapter.OnAdRewarded();
            adapter.OnAdRewarded();     // 重复回调
            Assert.AreEqual(1, rewarded, "奖励回调必须单次生效");
        }

        // 依赖 Unity 运行时（广告适配器回调经协程/计时推进；离线桩 Time.time 不流动）——仅 Unity 编辑器运行
        [Test]
        [Category("UnityRuntime")]
        public void 关闭回调_不等于获奖()
        {
            var adapter = new LevelPlayAdAdapter("key", "placement", false);
            adapter.Init();
            adapter.OnAdLoaded();
            bool rewarded = false, closed = false;
            adapter.ShowRewarded("revive", AdShowCallbacks.Create(
                onRewarded: () => rewarded = true, onClosed: () => closed = true));
            adapter.OnAdClosed();
            Assert.IsTrue(closed);
            Assert.IsFalse(rewarded, "关闭本身不得发奖");
        }

        // 依赖 Unity 运行时（广告适配器回调经协程/计时推进；离线桩 Time.time 不流动）——仅 Unity 编辑器运行
        [Test]
        [Category("UnityRuntime")]
        public void 新展示请求_使旧请求失效_防跨局发奖()
        {
            var adapter = new LevelPlayAdAdapter("key", "placement", false);
            adapter.Init();
            adapter.OnAdLoaded();
            int firstReward = 0, secondReward = 0;
            adapter.ShowRewarded("revive", AdShowCallbacks.Create(onRewarded: () => firstReward++));
            // 模拟 SDK 再次报告可用，让第二次展示通过就绪检查并替换旧请求。
            adapter.OnAvailabilityChanged(true);
            adapter.ShowRewarded("revive", AdShowCallbacks.Create(onRewarded: () => secondReward++));

            adapter.OnAdRewarded();   // 只应作用于第二个请求
            Assert.AreEqual(0, firstReward, "被抢占的旧请求不得再发奖");
            Assert.AreEqual(1, secondReward);
        }

        [Test]
        public void 兼容签名_取消时不发奖()
        {
            var dev = new DevelopmentAdProvider { SimulateCancel = true, SimulateReward = true };
            dev.Init();
            bool result = true;
            dev.ShowRewarded("revive", success => result = success);
            Assert.IsFalse(result, "用户取消不得判为获奖");
        }

        [Test]
        public void 空广告提供者_任何请求都不就绪()
        {
            IAdProvider nullAds = new BlockOutNullAdProvider();
            nullAds.Init();
            Assert.IsFalse(nullAds.IsReady(AdType.Rewarded));
            bool failed = false;
            nullAds.ShowRewarded("revive", AdShowCallbacks.Create(onShowFailed: () => failed = true));
            Assert.IsTrue(failed);
        }
    }
}
