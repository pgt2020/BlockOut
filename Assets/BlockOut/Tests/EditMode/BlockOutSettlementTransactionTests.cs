using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;
using BlockOut.Infrastructure.Configuration;
using BlockOut.Infrastructure.Persistence;
using NUnit.Framework;
using UnityEngine;

namespace BlockOut.Tests.EditMode
{
    /// <summary>
    /// 结算事务测试（R13/R17）。不实例化 GameManager（MonoBehaviour 私有启动流不可驱动），
    /// 而是按 <see cref="BlockOutGameManager.OnLevelWon"/> 的真实序列在
    /// 档案 + 结算 + 存档服务 + 事务的组合层复演，断言行为契约：
    /// 首通一次写全、恢复不二次发奖、合法重玩不倒退、结算失败整体回滚、放弃不恢复。
    /// </summary>
    [TestFixture]
    public sealed class BlockOutSettlementTransactionTests
    {
        private InMemoryProfileStore store;
        private BlockOutSaveService save;
        private BlockOutSettlement settlement;
        private BlockOutLevelData level;

        [SetUp]
        public void SetUp()
        {
            store = new InMemoryProfileStore();
            save = new BlockOutSaveService(store);
            save.Load();
            settlement = new BlockOutSettlement(save.Profile);
            level = new BlockOutLevelData
            {
                Id = "c1_l1",
                Difficulty = "normal",
                RewardCoins = 0,   // 走可配置奖励表 → normal = 20（ArtOut 基线）
                Chapter = 0,
                LevelInChapter = 0,
            };
        }

        [TearDown]
        public void TearDown()
        {
            settlement = null;
            save = null;
            store = null;
        }

        /// <summary>复演 GameManager.OnLevelWon 的结算序列（R13 单点落盘版）。</summary>
        private int SettleLevel(int levelIndex)
        {
            var profile = save.Profile;
            profile.MarkLevelCompleted(level.Id);
            profile.CurrentLevelIndex = Mathf.Max(profile.CurrentLevelIndex, levelIndex + 1);
            int reward = settlement.SettleWin(level);
            profile.ClearActiveRun();
            return reward;
        }

        [Test]
        public void 首通结算_奖励与通关标记一次写全()
        {
            using (var tx = save.BeginTransaction())
            {
                int reward = SettleLevel(0);
                Assert.AreEqual(20, reward, "normal 难度按 ArtOut 奖励表取 20");
                Assert.IsTrue(tx.Commit());
            }

            // 模拟重启：从同一存储重新加载
            var afterRestart = new BlockOutSaveService(store).Load();
            Assert.AreEqual(20, afterRestart.Coins, "奖励必须随通关一起落盘（新档 0 币 + 奖励 20）");
            Assert.IsTrue(afterRestart.IsLevelCompleted("c1_l1"));
            Assert.AreEqual(1, afterRestart.CurrentLevelIndex, "主线推进到下一关");
            Assert.IsFalse(afterRestart.HasActiveRun, "通关后不得残留进行中对局");
        }

        [Test]
        public void 恢复已通关存档_不二次发奖()
        {
            using (var tx = save.BeginTransaction())
            {
                SettleLevel(0);
                Assert.IsTrue(tx.Commit());
            }

            // 重启加载：加载本身不得触发任何结算
            var afterRestart = new BlockOutSaveService(store).Load();
            Assert.AreEqual(20, afterRestart.Coins, "仅因重启重新加载不得二次发奖");
            Assert.AreEqual(1, afterRestart.CompletedLevelIds.Count);
            // 用重启后的档案新建结算器：加载路径本身不得留下待发奖励
            var freshSettlement = new BlockOutSettlement(afterRestart);
            Assert.IsFalse(freshSettlement.HasPendingReward, "未调用 SettleWin 不得有待发奖励");
        }

        [Test]
        public void 合法重玩_奖励可再拿_进度不倒退()
        {
            using (var tx = save.BeginTransaction())
            {
                SettleLevel(0);
                Assert.IsTrue(tx.Commit());
            }

            // 合法重玩同一关：奖励允许再拿（设计如此），但进度与通关集合不得重复/倒退
            using (var tx = save.BeginTransaction())
            {
                int replay = SettleLevel(0);
                Assert.AreEqual(20, replay, "重玩奖励照常发放");
                Assert.IsTrue(tx.Commit());
            }

            var p = save.Profile;
            Assert.AreEqual(40, p.Coins);
            Assert.AreEqual(1, p.CompletedLevelIds.Count, "重复通关只记一次");
            Assert.AreEqual(1, p.CurrentLevelIndex, "主线索引取 Max，不得倒退");
        }

        [Test]
        public void 结算失败_整体回滚不半扣()
        {
            // 先制造一个进行中对局，验证回滚会把对局状态也还原
            save.Profile.HasActiveRun = true;
            save.Profile.RunLevelId = "c1_l1";
            save.Profile.RunBlockCount = 8;
            save.Save();
            store.CommitShouldFail = true;

            using (var tx = save.BeginTransaction())
            {
                SettleLevel(0);
                Assert.IsFalse(tx.Commit(), "存档失败时提交返回 false");
            }

            Assert.AreEqual(0, save.Profile.Coins, "奖励必须回滚");
            Assert.IsFalse(save.Profile.IsLevelCompleted("c1_l1"), "通关标记必须回滚");
            Assert.AreEqual(0, save.Profile.CurrentLevelIndex, "主线推进必须回滚");
            Assert.IsTrue(save.Profile.HasActiveRun, "对局状态必须还原，不得把进行中局清掉");

            // 按 GameManager 购买事务的既有模式：失败后补一次成功保存，
            // 把存储里已写入的中间态也纠正回来，重启后不得读到半套状态
            store.CommitShouldFail = false;
            Assert.IsTrue(save.Save());
            var afterRestart = new BlockOutSaveService(store).Load();
            Assert.AreEqual(0, afterRestart.Coins, "重启后不得读到回滚前的半套状态");
            Assert.IsFalse(afterRestart.IsLevelCompleted("c1_l1"));
            Assert.IsTrue(afterRestart.HasActiveRun, "进行中局必须原样恢复");
        }

        [Test]
        public void 放弃对局_不恢复已退出对局()
        {
            // 进行中：存档有效对局
            save.Profile.HasActiveRun = true;
            save.Profile.RunLevelId = "c1_l1";
            save.Profile.RunBlockCount = 8;
            save.Save();

            // 放弃：ClearActiveRun + 保存（GM.GoHome 序列）
            save.Profile.ClearActiveRun();
            save.Save();

            // 重启加载：已放弃的对局不得被恢复
            var afterRestart = new BlockOutSaveService(store).Load();
            Assert.IsFalse(afterRestart.HasActiveRun, "放弃后不得残留进行中对局");
            Assert.IsTrue(string.IsNullOrEmpty(afterRestart.RunLevelId));
        }

        [Test]
        public void 重启_不重复解锁()
        {
            using (var tx = save.BeginTransaction())
            {
                SettleLevel(0);
                save.Profile.MaxLevelReached = 2;
                Assert.IsTrue(tx.Commit());
            }

            var afterRestart = new BlockOutSaveService(store).Load();
            Assert.AreEqual(2, afterRestart.MaxLevelReached);

            // 重启后再次标记同一关（重复回调/重复进入）：解锁与进度均幂等
            afterRestart.MarkLevelCompleted("c1_l1");
            afterRestart.CurrentLevelIndex = Mathf.Max(afterRestart.CurrentLevelIndex, 1);
            Assert.AreEqual(1, afterRestart.CompletedLevelIds.Count, "重启不重复解锁");
            Assert.AreEqual(2, afterRestart.MaxLevelReached, "到达进度不回退");
        }

        [Test]
        public void 倒计时与生命模式_存档双向恢复()
        {
            // 倒计时失败局：剩余 0 秒是有效存档，不得当作无记录重新给满时间
            save.Profile.HasActiveRun = true;
            save.Profile.RunLevelId = "c1_l1";
            save.Profile.RunBlockCount = 8;
            save.Profile.RunFailMode = 1;
            save.Profile.RunHasTimeRecord = true;
            save.Profile.RunTimeRemaining = 0f;
            save.Profile.RunLost = true;
            save.Profile.RunFailReason = "时间用尽";
            save.Save();

            var t1 = new BlockOutSaveService(store).Load();
            Assert.AreEqual(1, t1.RunFailMode, "倒计时模式必须能恢复");
            Assert.IsTrue(t1.RunHasTimeRecord, "有时间记录标志必须保留（0 秒 ≠ 无记录）");
            Assert.AreEqual(0f, t1.RunTimeRemaining);
            Assert.IsTrue(t1.RunLost, "失败态必须恢复，回不到可操作状态");
            Assert.AreEqual("时间用尽", t1.RunFailReason);

            // 生命模式局：反向恢复
            save.Profile.RunFailMode = 0;
            save.Profile.RunHasTimeRecord = false;
            save.Profile.RunTimeRemaining = 90f;
            save.Profile.RunLost = false;
            save.Profile.RunFailReason = null;
            save.Save();

            var t2 = new BlockOutSaveService(store).Load();
            Assert.AreEqual(0, t2.RunFailMode);
            Assert.IsFalse(t2.RunHasTimeRecord);
            Assert.AreEqual(90f, t2.RunTimeRemaining);
            Assert.IsFalse(t2.RunLost);
        }
    }

    /// <summary>
    /// 启动配置与远程键契约测试（R05/R23）。远程键名属外部后台契约，不得漂移；
    /// 静态配置字段在用例间共享，SetUp 统一复位为本地默认值。
    /// </summary>
    [TestFixture]
    public sealed class BlockOutStartupConfigTests
    {
        private readonly System.Collections.Generic.List<BlockOutStartupConfig> created = new System.Collections.Generic.List<BlockOutStartupConfig>();

        [SetUp]
        public void SetUp()
        {
            BlockOutRemoteConfigBridge.ApplyLocalDefaults();
        }

        [TearDown]
        public void TearDown()
        {
            BlockOutRemoteConfigBridge.ApplyLocalDefaults();
            foreach (var c in created)
                if (c != null) Object.DestroyImmediate(c);
            created.Clear();
        }

        private BlockOutStartupConfig NewConfig()
        {
            var c = BlockOutStartupConfig.CreateEditorDefault();
            created.Add(c);
            return c;
        }

        [Test]
        public void 本地默认值_复位后等于契约默认()
        {
            Assert.IsFalse(BlockOutRemoteConfigBridge.ApplyLocalDefaults(), "已在默认值时不应报告变更");
            Assert.IsFalse(BlockOutContentConfig.UseTimeFailModeDefault, "默认生命模式");
            Assert.AreEqual(BlockOutContentConfig.DefaultMagicTargetCount, BlockOutContentConfig.MagicTargetCount);
            Assert.AreEqual(BlockOutContentConfig.DefaultHintUnlockLevel, BlockOutContentConfig.HintUnlockLevel);
            Assert.AreEqual(BlockOutContentConfig.DefaultHammerUnlockLevel, BlockOutContentConfig.HammerUnlockLevel);
            Assert.AreEqual(BlockOutContentConfig.DefaultMagicUnlockLevel, BlockOutContentConfig.MagicUnlockLevel);
        }

        [Test]
        public void 远程覆盖_合法值生效()
        {
            Assert.IsTrue(BlockOutRemoteConfigBridge.ApplyRemoteValue("use_time_fail_mode", "true"));
            Assert.IsTrue(BlockOutContentConfig.UseTimeFailModeDefault);

            Assert.IsTrue(BlockOutRemoteConfigBridge.ApplyRemoteValue("magic_target_count", "5"));
            Assert.AreEqual(5, BlockOutContentConfig.MagicTargetCount);

            Assert.IsTrue(BlockOutRemoteConfigBridge.ApplyRemoteValue("ad_simulated_load_seconds", "2.5"));
            Assert.AreEqual(2.5f, BlockOutContentConfig.AdSimulatedLoadSeconds, 0.001f);

            Assert.IsTrue(BlockOutRemoteConfigBridge.ApplyRemoteValue("tool_unlock_hint", "9"));
            Assert.AreEqual(9, BlockOutContentConfig.HintUnlockLevel);
        }

        [Test]
        public void 非法值_拒绝且不改变字段()
        {
            BlockOutRemoteConfigBridge.ApplyRemoteValue("magic_target_count", "5");

            Assert.IsFalse(BlockOutRemoteConfigBridge.ApplyRemoteValue("magic_target_count", "abc"), "非数字必须拒绝");
            Assert.IsFalse(BlockOutRemoteConfigBridge.ApplyRemoteValue("magic_target_count", "-3"), "非正数必须拒绝");
            Assert.IsFalse(BlockOutRemoteConfigBridge.ApplyRemoteValue("use_time_fail_mode", "maybe"), "非法布尔必须拒绝");
            Assert.IsFalse(BlockOutRemoteConfigBridge.ApplyRemoteValue("不存在的键", "1"), "未知键必须忽略");
            Assert.IsFalse(BlockOutRemoteConfigBridge.ApplyRemoteValue("", "1"), "空键必须忽略");

            Assert.AreEqual(5, BlockOutContentConfig.MagicTargetCount, "非法值不得改动字段");
            Assert.IsFalse(BlockOutContentConfig.UseTimeFailModeDefault);
        }

        [Test]
        public void 旧键兼容_与新键等价()
        {
            // 旧键必须仍被识别并可写（ApplyRemoteValue 语义=是否发生变更）
            Assert.IsTrue(BlockOutRemoteConfigBridge.ApplyRemoteValue(
                BlockOutRemoteConfigBridge.LegacyKeyUseTimeFailMode, "1"), "旧键必须仍可写");
            Assert.IsTrue(BlockOutContentConfig.UseTimeFailModeDefault);

            // 本地默认（生命模式）复位后，旧键写 "0" 是无变更 → 返回 false，但字段必须保持 false
            BlockOutRemoteConfigBridge.ApplyLocalDefaults();
            Assert.IsFalse(BlockOutContentConfig.UseTimeFailModeDefault, "本地默认=生命模式");
            BlockOutRemoteConfigBridge.ApplyRemoteValue(
                BlockOutRemoteConfigBridge.LegacyKeyUseTimeFailMode, "0");
            Assert.IsFalse(BlockOutContentConfig.UseTimeFailModeDefault);

            // 旧键再次写 "1" 必须仍能倒转到倒计时模式
            Assert.IsTrue(BlockOutRemoteConfigBridge.ApplyRemoteValue(
                BlockOutRemoteConfigBridge.LegacyKeyUseTimeFailMode, "1"), "旧键必须仍可写");
            Assert.IsTrue(BlockOutContentConfig.UseTimeFailModeDefault);
        }

        [Test]
        public void 键名集合_稳定不得漂移()
        {
            // 远程键名属外部后台契约：数量与取值都必须与登记表一致，防重构改名
            var expected = new[]
            {
                BlockOutRemoteConfigBridge.KeyUseTimeFailMode,
                BlockOutRemoteConfigBridge.KeyMagicTargetCount,
                BlockOutRemoteConfigBridge.KeyAdSimulatedLoadSeconds,
                BlockOutRemoteConfigBridge.KeyToolUnlockHint,
                BlockOutRemoteConfigBridge.KeyToolUnlockHammer,
                BlockOutRemoteConfigBridge.KeyToolUnlockMagic,
                BlockOutRemoteConfigBridge.LegacyKeyUseTimeFailMode,
            };
            Assert.AreEqual(expected.Length, BlockOutRemoteConfigBridge.AllKeys.Length, "键数量漂移");
            foreach (var key in expected)
            {
                Assert.Contains(key, BlockOutRemoteConfigBridge.AllKeys, "键 '" + key + "' 丢失");
            }

            // 每个已登记键至少要被 ApplyRemoteValue 识别（不抛异常、有确定语义）
            foreach (var key in BlockOutRemoteConfigBridge.AllKeys)
            {
                Assert.DoesNotThrow(() => BlockOutRemoteConfigBridge.ApplyRemoteValue(key, "1"));
            }
        }

        [Test]
        public void Release配置自检_拦截开发替身与详细日志()
        {
            var editor = NewConfig();
            Assert.AreEqual(BlockOutStartupConfig.Environment.Editor, editor.environment);
            Assert.IsTrue(editor.ValidateRelease(out _), "Editor 档不适用 Release 规则");

            var release = NewConfig();
            release.environment = BlockOutStartupConfig.Environment.Release;
            release.allowFakeServices = true;
            release.verboseLog = true;
            Assert.IsFalse(release.ValidateRelease(out var error), "Release 不允许开发替身");
            Assert.IsNotNull(error);

            release.allowFakeServices = false;
            release.verboseLog = false;
            Assert.IsTrue(release.ValidateRelease(out _), "干净的 Release 配置必须通过");
        }
    }
}
