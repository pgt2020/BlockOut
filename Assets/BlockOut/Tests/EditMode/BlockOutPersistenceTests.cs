using BlockOut.Core;
using BlockOut.Infrastructure.Persistence;
using NUnit.Framework;
using UnityEngine;

namespace BlockOut.Tests.EditMode
{
    /// <summary>
    /// 存档与事务测试（R13/R17）。全部使用 <see cref="InMemoryProfileStore"/>，
    /// 不碰真实 PlayerPrefs。重点是行为契约：
    /// 旧档可读可迁移、保存失败可感知、事务整体回滚、对局状态语义不被污染。
    /// </summary>
    [TestFixture]
    public sealed class BlockOutPersistenceTests
    {
        private InMemoryProfileStore store;
        private BlockOutSaveService save;

        [SetUp]
        public void SetUp()
        {
            store = new InMemoryProfileStore();
            save = new BlockOutSaveService(store);
        }

        [TearDown]
        public void TearDown()
        {
            save = null;
            store = null;
        }

        [Test]
        public void 新档案_默认值为ArtOut基线()
        {
            var p = save.Load();
            Assert.AreEqual(0, p.CurrentLevelIndex);
            Assert.AreEqual(0, p.Coins, "ArtOut 对齐：新档 0 币（老档值不被覆盖）");
            Assert.AreEqual(1, p.HintCount, "ArtOut 对齐：新档道具各 1");
            Assert.AreEqual(1, p.HammerCount);
            Assert.AreEqual(1, p.MagicCount);
            Assert.AreEqual(1, p.MaxLevelReached);
            Assert.IsFalse(p.HasActiveRun, "新档案不得携带进行中对局");
            Assert.AreEqual(0, p.RunFailMode, "旧档无失败模式字段时按生命模式（0）");
        }

        [Test]
        public void v1旧档_加载后迁移到v2且保留旧键可回退()
        {
            // v1 存档没有 MaxLevelReached 字段（旧版结构）
            store.Set(BlockOutSaveService.SaveKeyV1,
                "{\"CurrentLevelIndex\":3,\"CompletedLevelIds\":[\"c1_l1\"],\"Coins\":500," +
                "\"HintCount\":2,\"HammerCount\":1,\"MagicCount\":0}");

            var p = save.Load();
            Assert.AreEqual(4, p.MaxLevelReached, "迁移应按 CurrentLevelIndex+1 补齐");
            Assert.AreEqual(500, p.Coins, "旧档经济数据不得丢失");
            Assert.IsTrue(p.IsLevelCompleted("c1_l1"), "旧档通关记录不得丢失");

            Assert.IsTrue(store.Has(BlockOutSaveService.SaveKeyV2), "迁移结果应立即落盘到 v2 键");
            Assert.IsTrue(store.Has(BlockOutSaveService.SaveKeyV1), "旧键保留不删，保证可回退");
        }

        [Test]
        public void v1旧档_无对局字段时不虚假恢复()
        {
            store.Set(BlockOutSaveService.SaveKeyV1,
                "{\"CurrentLevelIndex\":2,\"Coins\":100,\"CompletedLevelIds\":[]}");

            var p = save.Load();
            Assert.IsFalse(p.HasActiveRun, "旧档没有局内字段，不得被误判为进行中对局");
            Assert.IsFalse(p.RunLost);
            Assert.IsFalse(p.RunHasTimeRecord);
        }

        [Test]
        public void 保存失败_返回false并暴露错误()
        {
            save.Load();
            store.CommitShouldFail = true;

            bool failedEvent = false;
            save.OnSaveFailed += () => failedEvent = true;

            Assert.IsFalse(save.Save(), "提交失败必须返回 false 让调用方回滚");
            Assert.IsTrue(failedEvent, "失败必须可感知");
            Assert.IsNotNull(save.LastSaveError, "失败原因必须可读取");
        }

        [Test]
        public void 事务_提交失败整体回滚且存储缓存恢复()
        {
            save.Load();
            store.CommitShouldFail = true;

            using (var tx = save.BeginTransaction())
            {
                save.Profile.AddCoins(100);
                save.Profile.MarkLevelCompleted("c1_l1");
                Assert.IsFalse(tx.Commit(), "保存失败时提交返回 false");
            }

            Assert.AreEqual(0, save.Profile.Coins, "金币必须回到事务前状态");
            Assert.IsFalse(save.Profile.IsLevelCompleted("c1_l1"), "通关标记必须一并回滚，不得只回滚一半");
            // C05：提交失败后存储缓存不得残留失败事务写入的脏值
            var reload = new BlockOutSaveService(store).Load();
            Assert.AreEqual(0, reload.Coins, "失败事务的脏值不得留在存储缓存里被下次保存写出");
        }

        [Test]
        public void 事务_提交成功落盘()
        {
            save.Load();

            using (var tx = save.BeginTransaction())
            {
                save.Profile.AddCoins(100);
                Assert.IsTrue(tx.Commit());
            }

            Assert.AreEqual(100, save.Profile.Coins);
            Assert.IsTrue(store.Has(BlockOutSaveService.SaveKeyV2), "成功后必须落盘");

            // 模拟重启：新服务从同一存储加载，结果一致
            var reloaded = new BlockOutSaveService(store).Load();
            Assert.AreEqual(100, reloaded.Coins, "重启后事务结果不得丢失");
        }

        [Test]
        public void 事务_未提交即释放视为放弃()
        {
            save.Load();

            using (var tx = save.BeginTransaction())
            {
                save.Profile.AddCoins(999);
            }   // 未调用 Commit 直接释放 = 放弃

            Assert.AreEqual(0, save.Profile.Coins, "未提交的修改不得保留");
        }

        [Test]
        public void 空棋盘旧存档_加载后保留待结算语义()
        {
            // 旧版本缺陷存档：已满足胜利条件但结算未完成（HasActiveRun + 0 块）
            store.Set(BlockOutSaveService.SaveKeyV2,
                "{\"CurrentLevelIndex\":5,\"Coins\":300,\"CompletedLevelIds\":[]," +
                "\"HasActiveRun\":true,\"RunLevelId\":\"gen_placeholder_006\",\"RunBlockCount\":0," +
                "\"RunLives\":3,\"RunRemoved\":[],\"RunWrong\":[]}");

            var p = save.Load();
            Assert.IsTrue(p.HasActiveRun, "待结算语义必须在存档里保留，供恢复补结算判定");
            Assert.AreEqual(0, p.RunBlockCount, "空棋盘状态必须原样保留");
            Assert.IsFalse(p.IsLevelCompleted("gen_placeholder_006"), "旧档未标记通关，补结算后才能标记");
        }

        [Test]
        public void ClearActiveRun_清空对局与失败态残留()
        {
            var p = save.Load();
            p.HasActiveRun = true;
            p.RunLevelId = "c1_l3";
            p.RunReviveUsed = true;
            p.RunLost = true;
            p.RunFailReason = "生命耗尽";
            p.RunHasTimeRecord = true;
            p.RunTimeRemaining = 12f;
            p.RunFailMode = 1;

            p.ClearActiveRun();

            Assert.IsFalse(p.HasActiveRun);
            Assert.IsNull(p.RunLevelId);
            Assert.IsFalse(p.RunReviveUsed);
            Assert.IsFalse(p.RunLost, "失败态残留不得留到下一局");
            Assert.IsNull(p.RunFailReason);
            Assert.IsFalse(p.RunHasTimeRecord);
            Assert.AreEqual(0f, p.RunTimeRemaining);
            Assert.AreEqual(0, p.RunFailMode);
        }

        [Test]
        public void MarkLevelCompleted_重复标记去重()
        {
            var p = save.Load();
            p.HasActiveRun = true;

            p.MarkLevelCompleted("c1_l1");
            p.MarkLevelCompleted("c1_l1");
            p.MarkLevelCompleted("c1_l1");

            Assert.AreEqual(1, p.CompletedLevelIds.Count, "同一关卡重复通关只记一次");
            Assert.IsFalse(p.HasActiveRun, "通关后对局不再进行中");
        }

        [Test]
        public void AddCoins_下限为0()
        {
            var p = save.Load();
            p.AddCoins(-99999);
            Assert.AreEqual(0, p.Coins, "金币不得为负");
            p.AddCoins(50);
            Assert.AreEqual(50, p.Coins);
        }

        [Test]
        public void SpendCoins_不足时不动余额()
        {
            var p = save.Load();
            p.AddCoins(300);
            Assert.IsFalse(p.SpendCoins(301), "余额不足必须失败");
            Assert.AreEqual(300, p.Coins, "失败扣币不得改动余额");
            Assert.IsTrue(p.SpendCoins(300));
            Assert.AreEqual(0, p.Coins);
        }

        [Test]
        public void Normalize_旧档负值与缺数组被兜底()
        {
            store.Set(BlockOutSaveService.SaveKeyV2,
                "{\"CurrentLevelIndex\":0,\"Coins\":-50,\"HintCount\":-1,\"HammerCount\":-2," +
                "\"MagicCount\":-3,\"MaxLevelReached\":0}");

            var p = save.Load();
            Assert.AreEqual(0, p.Coins);
            Assert.AreEqual(0, p.HintCount);
            Assert.AreEqual(0, p.HammerCount);
            Assert.AreEqual(0, p.MagicCount);
            Assert.AreEqual(1, p.MaxLevelReached, "到达进度至少为 1");
            Assert.IsNotNull(p.CompletedLevelIds, "集合字段不得为 null");
            Assert.IsNotNull(p.RunRemoved, "局内数组字段不得为 null");
            Assert.IsNotNull(p.RunWrong);
        }

        [Test]
        public void 加载损坏JSON_退回到新档案不抛异常()
        {
            store.Set(BlockOutSaveService.SaveKeyV2, "{ 这不是合法 JSON ");

            var p = save.Load();
            Assert.IsNotNull(p, "损坏存档必须兜底为新档案，绝不抛出到启动链之外");
            Assert.AreEqual(0, p.Coins, "兜底新档走 ArtOut 基线（0 币）");
        }
    }
}
