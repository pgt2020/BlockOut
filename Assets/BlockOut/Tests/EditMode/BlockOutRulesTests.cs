using System.Collections.Generic;
using BlockOut.Core;
using NUnit.Framework;

namespace BlockOut.Tests.EditMode
{
    /// <summary>
    /// 规则层行为测试（R17）。重点是"有行为意义"的断言，不镜像实现：
    /// 延迟提交、错误扣心、串行解锁、通关判定、存档 hash 稳定性。
    /// </summary>
    [TestFixture]
    public sealed class BlockOutRulesTests
    {
        private static BlockOutLevelData SerialLevel()
        {
            // 3×1 棋盘，三块都朝右：只有最右可飞，形成 C → B → A 的串行解锁
            var level = new BlockOutLevelData
            {
                Id = "test_serial",
                Width = 3,
                Height = 1,
                Chapter = 0,
                LevelInChapter = 1,
            };
            for (int i = 0; i < 3; i++)
            {
                level.Blocks.Add(new BlockOutBlockData
                {
                    Row = 0,
                    Column = i,
                    ShapeId = 1,
                    Direction = BlockOutDirection.Right,
                });
            }
            return level;
        }

        private static BlockOutGameRules NewRules()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(SerialLevel());
            return rules;
        }

        [Test]
        public void TryTap_纯判定不移除_移除由调用方立即提交()
        {
            // 阶段 C（§4.2.1）：成功点击的逻辑移除发生在 GameManager.HandleBlockTapped
            // （立即 Rules.Remove + 独立飞出协程）；规则层 TryTap 保持纯判定，不自行移除。
            var rules = NewRules();
            var movable = rules.FindMovableBlock();
            Assert.IsNotNull(movable, "应存在可飞块");

            var result = rules.TryTap(movable);
            Assert.IsTrue(result.CanMove, "应判定可飞");
            Assert.IsTrue(movable.Active, "TryTap 本身不移除");
            Assert.AreEqual(3, rules.RemainingBlocks, "剩余数在调用方提交前不变");
            Assert.IsFalse(rules.IsWon, "未提交不得判胜");
        }

        [Test]
        public void Remove_提交后剩余数递减_清空即胜利()
        {
            var rules = NewRules();
            var movable = rules.FindMovableBlock();
            rules.TryTap(movable);
            rules.Remove(movable);

            Assert.IsFalse(movable.Active);
            Assert.AreEqual(2, rules.RemainingBlocks);
            Assert.IsFalse(rules.IsWon);

            // 依次提交剩余两块
            var second = rules.FindMovableBlock();
            Assert.IsNotNull(second, "移除后应解锁下一块");
            rules.Remove(second);
            var third = rules.FindMovableBlock();
            Assert.IsNotNull(third, "应继续解锁最后一块");
            rules.Remove(third);

            Assert.AreEqual(0, rules.RemainingBlocks);
            Assert.IsTrue(rules.IsWon, "全部移除即胜利");
        }

        [Test]
        public void TryTap_被挡块首次扣心_重复点击不重复扣心()
        {
            var rules = NewRules();
            var blocked = rules.Blocks[0];   // 最左块被挡住
            Assert.IsFalse(rules.CanMove(blocked), "最左块应被挡");

            var first = rules.TryTap(blocked);
            Assert.IsFalse(first.CanMove);
            Assert.IsTrue(first.LifeLost, "首次错误点击应扣心");
            Assert.AreEqual(2, rules.Lives);

            var second = rules.TryTap(blocked);
            Assert.IsFalse(second.LifeLost, "已标记块不得重复扣心");
            Assert.IsTrue(second.AlreadyMarked);
            Assert.AreEqual(2, rules.Lives, "生命不重复扣除");
        }

        [Test]
        public void TryTap_生命耗尽即失败()
        {
            // 三个互阻塞的块（A 被 B 挡、B 被 A/C 挡、C 被 B 挡）：误点三个不同块各扣 1 心
            var level = new BlockOutLevelData { Id = "deadlock", Width = 3, Height = 1 };
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 1, Direction = BlockOutDirection.Left });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 2, Direction = BlockOutDirection.Left });
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);

            for (int i = 0; i < 3; i++)
            {
                Assert.IsFalse(rules.CanMove(rules.Blocks[i]), "三个块互堵，均不可飞");
                rules.TryTap(rules.Blocks[i]);
            }
            Assert.AreEqual(0, rules.Lives, "三个不同受阻块各扣 1 心");
            Assert.IsTrue(rules.IsLost);
        }

        [Test]
        public void PickMagicTargets_串行解锁局面按最新棋盘逐次选取()
        {
            var rules = NewRules();
            var targets = rules.PickMagicTargets(3);
            Assert.AreEqual(3, targets.Count, "串行解锁应能选满 3 个");

            // 顺序必须是"当前可飞者优先"：C(2) → B(1) → A(0)
            Assert.AreEqual(2, targets[0].Column);
            Assert.AreEqual(1, targets[1].Column);
            Assert.AreEqual(0, targets[2].Column);

            // 只选 1 个时不得把后续块也算进去
            var one = rules.PickMagicTargets(1);
            Assert.AreEqual(1, one.Count);
            Assert.AreEqual(2, one[0].Column);
        }

        [Test]
        public void PickMagicTargets_上限大于可解锁数时返回实际数量()
        {
            var rules = NewRules();
            var many = rules.PickMagicTargets(99);
            Assert.AreEqual(3, many.Count, "不得返回超过实际可解锁的数量");
        }

        [Test]
        public void CaptureApplyRunProgress_往返一致()
        {
            var rules = NewRules();
            var movable = rules.FindMovableBlock();
            rules.TryTap(movable);
            rules.Remove(movable);
            var progress = rules.CaptureRunProgress("test_serial", BlockOutGameRules.BuildLevelRunHash(SerialLevel()));

            var restored = new BlockOutGameRules();
            restored.StartLevel(SerialLevel());
            Assert.IsTrue(restored.ApplyRunProgress(progress), "同 blockCount 的存档应可应用");
            Assert.AreEqual(rules.RemainingBlocks, restored.RemainingBlocks);
            Assert.AreEqual(rules.Lives, restored.Lives);
        }

        [Test]
        public void ApplyRunProgress_存档_保持胜利态可判定()
        {
            var rules = NewRules();
            for (int i = 0; i < 3; i++)
            {
                var m = rules.FindMovableBlock();
                rules.Remove(m);
            }
            var progress = rules.CaptureRunProgress("test_serial", "hash");

            var restored = new BlockOutGameRules();
            restored.StartLevel(SerialLevel());
            restored.ApplyRunProgress(progress);
            Assert.IsTrue(restored.IsWon, "旧空棋盘存档恢复后必须可判定胜利（补结算前提）");
        }

        [Test]
        public void BuildLevelRunHash_同数据同hash_改数据变hash()
        {
            var a = BlockOutGameRules.BuildLevelRunHash(SerialLevel());
            var b = BlockOutGameRules.BuildLevelRunHash(SerialLevel());
            Assert.AreEqual(a, b, "同关卡数据必须得到同 hash（否则旧存档全部失效）");

            var modified = SerialLevel();
            modified.Blocks[1].Column = 2;
            var c = BlockOutGameRules.BuildLevelRunHash(modified);
            Assert.AreNotEqual(a, c, "关卡数据变化必须反映到 hash");
        }

        [Test]
        public void StartLevel_重置生命与剩余_并克隆关卡数据()
        {
            var level = SerialLevel();
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);
            rules.TryTap(rules.Blocks[0]);
            rules.TryTap(rules.Blocks[0]);
            rules.TryTap(rules.Blocks[0]);

            rules.StartLevel(level);
            Assert.AreEqual(3, rules.Lives, "重开必须重置生命");
            Assert.AreEqual(3, rules.RemainingBlocks);
            Assert.IsFalse(rules.IsLost);
            Assert.IsFalse(level.Blocks[0].WrongMarked, "不得把运行时标记写回关卡模板");
        }
    }
}
