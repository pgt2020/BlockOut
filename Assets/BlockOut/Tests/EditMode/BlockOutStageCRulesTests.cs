using System.Collections.Generic;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;
using NUnit.Framework;
using UnityEngine;

namespace BlockOut.Tests.EditMode
{
    /// <summary>
    /// 阶段 C 规则/工具对齐边界测试（只写不跑；运行按用户授权，见 Docs/ArtOut玩法对齐实现记录.md）。
    /// 覆盖文档 §4（核心规则与连续点击）与 §5（道具、失败和经济数值）中可离线验证的部分：
    /// 连续点击的规则层证据、误点扣心去重、提示轮换、锤子零库存、魔法链 + 过滤、
    /// 工具包购买配置、复活与经济数值、奖励表优先。
    /// GameManager 生命周期相关场景（在途计数/胜机等待/计时全条件）需要 Unity 编辑器运行，
    /// 列入手动验收步骤，不在本文件用无法运行的生命周期断言冒充通过。
    /// </summary>
    [TestFixture]
    public sealed class BlockOutStageCRulesTests
    {
        private static BlockOutLevelData RowLevel(int count, int width)
        {
            var level = new BlockOutLevelData { Id = "row", Width = width, Height = 1 };
            for (int i = 0; i < count; i++)
                level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = i, Direction = BlockOutDirection.Right });
            return level;
        }

        private static BlockOutLevelData DeadlockLevel()
        {
            // 2×1 棋盘两块互堵：A(0)Right 被 B 挡，B(1)Left 被 A 挡——两块都不可飞
            var level = new BlockOutLevelData { Id = "deadlock", Width = 2, Height = 1 };
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 1, Direction = BlockOutDirection.Left });
            return level;
        }

        // ---- §4.2 连续点击：规则层证据 ----

        [Test]
        public void 逻辑移除立即生效_后续判定看到已释放路径()
        {
            // 2 块横排：左块被右块挡住；移除右块后左块立即可飞（无需等任何动画）
            var level = RowLevel(2, 2);
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);

            var left = rules.Blocks[0];
            var right = rules.Blocks[1];
            Assert.IsFalse(rules.CanMove(left), "左块初始被挡");

            rules.Remove(right);   // 模拟 HandleBlockTapped 成功路径的立即逻辑移除
            Assert.IsTrue(rules.CanMove(left), "移除后路径必须立即释放");
            Assert.AreEqual(1, rules.RemainingBlocks);
        }

        [Test]
        public void 误点扣心去重_同块二次误点不再扣心()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(DeadlockLevel());

            var first = rules.TryTap(rules.Blocks[0], consumeLifeOnWrong: true);
            Assert.IsTrue(first.LifeLost, "首次误点扣 1 心");
            Assert.AreEqual(2, rules.Lives);

            var second = rules.TryTap(rules.Blocks[0], consumeLifeOnWrong: true);
            Assert.IsTrue(second.AlreadyMarked, "二次误点只标记不扣心");
            Assert.AreEqual(2, rules.Lives, "同一受阻块不得重复扣心");
        }

        [Test]
        public void 倒计时模式_误点不扣心仍标记()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(DeadlockLevel());

            var result = rules.TryTap(rules.Blocks[0], consumeLifeOnWrong: false);
            Assert.IsFalse(result.LifeLost, "倒计时模式不扣心");
            Assert.IsFalse(result.AlreadyMarked, "首次仍要走反馈分支");
            Assert.IsTrue(rules.Blocks[0].WrongMarked, "仍要标记");
            Assert.AreEqual(3, rules.Lives);
        }

        [Test]
        public void 误点距离_只计空格不含自身占格()
        {
            // 2 格竖块（shape 3）贴底朝上，上方 1 格空 + 1 格阻挡 → 空格数 = 1
            var level = new BlockOutLevelData { Id = "dist", Width = 1, Height = 3 };
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, ShapeId = 3, Direction = BlockOutDirection.Up });
            level.Blocks.Add(new BlockOutBlockData { Row = 2, Column = 0, Direction = BlockOutDirection.Up });
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);

            Assert.IsTrue(rules.TryGetWrongMoveDistance(rules.Blocks[0], out int empty));
            Assert.AreEqual(1, empty, "只数到阻挡前的空格，不含自身占格");
        }

        // ---- §5 提示：轮换 ----

        [Test]
        public void 提示轮换_未提示优先_耗尽后重置()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(RowLevel(2, 2));   // 仅 column=1 可飞
            var tools = new BlockOutToolController(rules, 3, 0, 0);

            var first = tools.TryUseHint();
            Assert.AreEqual(1, first.Column, "首个可飞块");
            rules.Remove(first);

            var second = tools.TryUseHint();
            Assert.AreEqual(0, second.Column, "移除后轮到下一个可飞块");
            Assert.AreEqual(1, tools.GetCount(BlockOutToolId.Hint), "第二次扣库存");

            // 已提示集合耗尽：重置后仍返回当前可飞块（此处已无可飞块 → null 且不扣）
            rules.Remove(second);
            Assert.IsNull(tools.TryUseHint(), "无可飞块不扣库存");
            Assert.AreEqual(1, tools.GetCount(BlockOutToolId.Hint));
        }

        [Test]
        public void 提示轮换_同局面两次提示给不同块()
        {
            // 两块分居两行各自可飞：首次给 A，二次给 B，三次重置回 A
            var level = new BlockOutLevelData { Id = "two", Width = 2, Height = 2 };
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 1, Column = 0, Direction = BlockOutDirection.Right });
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);
            var tools = new BlockOutToolController(rules, 3, 0, 0);

            var a = tools.TryUseHint();
            var b = tools.TryUseHint();
            Assert.AreNotSame(a, b, "连续两次提示必须轮换到不同块");
            var c = tools.TryUseHint();
            Assert.AreSame(a, c, "全部提示过 → 重置集合后回到第一块");
            Assert.AreEqual(0, tools.GetCount(BlockOutToolId.Hint));
        }

        [Test]
        public void 提示_切关重置轮换集合()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(RowLevel(2, 2));
            var tools = new BlockOutToolController(rules, 3, 0, 0);
            tools.TryUseHint();
            tools.ResetHintCycle();
            // 重置后首个提示仍指向当前第一个可飞块（不跳过）
            var again = tools.TryUseHint();
            Assert.AreEqual(1, again.Column);
        }

        // ---- §5 锤子 / 魔法 ----

        [Test]
        public void 锤子_零库存不能进入选择态()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(RowLevel(2, 2));
            var tools = new BlockOutToolController(rules, 0, 0, 0);
            Assert.IsFalse(tools.EnterHammerMode(), "零库存按参考 Activate 失败（走购买路径）");
            Assert.IsFalse(tools.IsHammerSelecting);
        }

        [Test]
        public void 锤子_取消不进库存扣减()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(RowLevel(2, 2));
            var tools = new BlockOutToolController(rules, 0, 1, 0);
            Assert.IsTrue(tools.EnterHammerMode());
            tools.CancelHammerMode();
            Assert.AreEqual(1, tools.GetCount(BlockOutToolId.Hammer), "取消不扣库存");
        }

        [Test]
        public void 魔法_过滤后的目标不包含被过滤块()
        {
            var rules = new BlockOutGameRules();
            rules.StartLevel(RowLevel(2, 2));   // 链式模拟可选满 2 个（B 先飞，再 A）
            var tools = new BlockOutToolController(rules, 0, 0, 1);

            var none = tools.PickMagicTargets(6, _ => false);
            Assert.AreEqual(0, none.Count, "全部被过滤 → 无目标");

            var all = tools.PickMagicTargets(6, _ => true);
            Assert.AreEqual(2, all.Count, "不被过滤时按链式模拟选满");
        }

        [Test]
        public void 魔法_目标上限来自配置6()
        {
            Assert.AreEqual(6, BlockOutContentConfig.MagicTargetCount, "参考 DefaultMagicTargetCount=6");
            Assert.AreEqual(6, BlockOutContentConfig.DefaultMagicTargetCount);
        }

        // ---- §5 经济与购买 ----

        [Test]
        public void 工具包_默认300币2个且可校验()
        {
            Assert.AreEqual(300, BlockOutContentConfig.ToolPackCost);
            Assert.AreEqual(2, BlockOutContentConfig.ToolPackAmount);
            Assert.AreEqual(300, BlockOutGameplayConfig.Default().tools.toolPackCost);
            Assert.AreEqual(2, BlockOutGameplayConfig.Default().tools.toolPackAmount);
            Assert.IsNull(BlockOutGameplayConfig.Default().Validate(), "默认配置必须通过校验");
        }

        [Test]
        public void 工具包_非法值被校验拒绝()
        {
            var bad = BlockOutGameplayConfig.Default();
            bad.tools.toolPackCost = -1;
            Assert.IsNotNull(bad.Validate(), "负数价格必须拒绝");
            var bad2 = BlockOutGameplayConfig.Default();
            bad2.tools.toolPackAmount = 0;
            Assert.IsNotNull(bad2.Validate(), "零数量必须拒绝");
        }

        [Test]
        public void 复活与经济数值_对齐参考基线()
        {
            Assert.AreEqual(300, BlockOutContentConfig.CoinReviveCost, "参考 DefaultCoinCost=300");
            Assert.AreEqual(10, BlockOutContentConfig.FreeReviveMaxLevel, "参考 DefaultFreeReviveLevelNum=10");
            Assert.AreEqual(1, BlockOutContentConfig.ReviveLifeBonus, "金币复活补 1 心");
            Assert.AreEqual(3, BlockOutContentConfig.FreeReviveLifeCount, "免费复活补满 3 心");
            Assert.AreEqual(20f, BlockOutContentConfig.ReviveTimeBonusSeconds, "倒计时复活 +20s");
            Assert.AreEqual(3, BlockOutContentConfig.MaxLives);
            Assert.AreEqual(2, BlockOutContentConfig.HintUnlockLevel);
            Assert.AreEqual(3, BlockOutContentConfig.HammerUnlockLevel);
            Assert.AreEqual(4, BlockOutContentConfig.MagicUnlockLevel);
        }

        [Test]
        public void 奖励表优先_关卡自带值不覆盖()
        {
            // 移植关 rewardCoins=25+，但 easy 必须按奖励表发 10（参考 GetRewardCoins 语义）
            Assert.AreEqual(10, BlockOutContentConfig.GetLevelReward("easy", 25));
            Assert.AreEqual(20, BlockOutContentConfig.GetLevelReward("normal", 0));
            Assert.AreEqual(30, BlockOutContentConfig.GetLevelReward("hard", 99));
            Assert.AreEqual(40, BlockOutContentConfig.GetLevelReward("insane", 5), "expert/insane 并入第四档");
        }

        [Test]
        public void 魔法链_先A后B才可飞_目标链合法()
        {
            // 三块横排朝右：只有最右可飞；链式模拟应能选满 3 个（逐次移除后逐个解锁）
            var rules = new BlockOutGameRules();
            rules.StartLevel(RowLevel(3, 3));
            var picked = rules.PickMagicTargets(6);
            Assert.AreEqual(3, picked.Count, "链式选取应覆盖逐次解锁的三个块");
            foreach (var t in picked)
            {
                Assert.IsTrue(rules.CanMove(t), "每个被选目标在其轮次必须真的可飞");
                rules.Remove(t);
            }
            Assert.IsTrue(rules.IsWon);
        }
    }
}
