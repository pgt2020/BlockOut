using System.Collections.Generic;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;
using NUnit.Framework;

namespace BlockOut.Tests.EditMode
{
    /// <summary>
    /// 阶段 E 验收用例清单（对齐 Docs/ArtOut玩法与手感对齐实施说明 §6 手动验收步骤 + 阶段 D 手感契约）。
    /// 纯逻辑/配置契约用例可离线 NUnitLite 验证；依赖 Unity 运行时（Resources/Catalog 资源加载、
    /// 协程演出、UI 时序）的用例标注 [Category("UnityRuntime")]，仅 Unity 编辑器内运行。
    /// 按用户要求"只写不跑"：本文件仅做离线静态编译校验（Tools/CompileCheck），实际运行交 Unity Test Runner。
    /// </summary>
    [TestFixture]
    public sealed class BlockOutAcceptanceTests
    {
        // ---------- 阶段 D：手感配置契约（核心证据，纯静态，对齐实施说明 §7） ----------
        [Test]
        public void 验收_手感配置_默认对齐文档约定()
        {
            var feel = GameplayFeelConfig.Default();
            Assert.AreEqual(5f, feel.referenceCameraHalfHeight, "相机半高 5");
            Assert.AreEqual(6.24f, feel.exitInitialSpeed, "飞出初速 6.24");
            Assert.AreEqual(15f, feel.exitAcceleration, "加速度 15");
            Assert.AreEqual(13f, feel.exitMaxSpeed, "上限 13");
            Assert.AreEqual(0.9f, feel.boardEntranceSeconds, "入场 0.9s");
            Assert.AreEqual(0.68f, feel.boardEntranceStartScale, "入场起始缩放 0.68");
            Assert.AreEqual(1.02f, feel.boardEntranceInputDelay, "入场输入延迟 1.02s");
            Assert.AreEqual(0.08f, feel.wrongTravelBaseSeconds, "误点 travel 基线");
            Assert.AreEqual(0.06f, feel.wrongTravelPerSqrtCell, "误点 travel 每√格");
            Assert.AreEqual(0.12f, feel.wrongTravelMinSeconds, "误点 travel 下限");
            Assert.AreEqual(0.24f, feel.wrongTravelMaxSeconds, "误点 travel 上限");
            Assert.AreEqual(0.05f, feel.wrongImpactSeconds, "误点 impact");
            Assert.AreEqual(0.12f, feel.wrongReturnBaseSeconds, "误点 return 基线");
            Assert.AreEqual(0.04f, feel.wrongReturnPerSqrtCell, "误点 return 每√格");
            Assert.AreEqual(0.16f, feel.wrongReturnMinSeconds, "误点 return 下限");
            Assert.AreEqual(0.28f, feel.wrongReturnMaxSeconds, "误点 return 上限");
            Assert.AreEqual(0.04f, feel.wrongArrowFlashSeconds, "箭头闪 0.04s");
            Assert.AreEqual(3, feel.wrongArrowFlashCount, "箭头闪 3 次");
            Assert.AreEqual(0.2f, feel.hintFlashStepSeconds, "提示每轮 0.2s");
            Assert.AreEqual(2, feel.hintFlashLoops, "提示两轮");
            Assert.AreEqual(0.7f, feel.hintFocusSeconds, "提示聚焦 0.7s");
            Assert.AreEqual(1f, feel.magicStarPathSeconds, "魔法星路径 1s");
            Assert.AreEqual(1.15f, feel.magicHitScale, "魔法命中放大 1.15");
            Assert.AreEqual(0.12f, feel.magicHitScaleSeconds, "魔法命中 0.12s");
            Assert.AreEqual(0.35f, feel.hammerImpactSoundDelay, "锤子音效延迟 0.35s");
            Assert.AreEqual(0.58f, feel.failPopupDelaySeconds, "失败弹层延迟 0.58s");
            Assert.AreEqual(0.16f, feel.gestureTapSuppressSeconds, "手势抑制 0.16s");
        }

        // ---------- §6.2 连点：同一块逻辑移除只一次（逻辑层守卫） ----------
        [Test]
        public void 验收_连点_同块逻辑移除只一次()
        {
            var level = new BlockOutLevelData { Id = "conn", Width = 3, Height = 1 };
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 1, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 2, Direction = BlockOutDirection.Right });
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);
            var a = rules.Blocks[0];
            Assert.IsTrue(rules.CanMove(a));
            rules.Remove(a);
            Assert.IsFalse(rules.CanMove(a), "移除后不可再飞");
            rules.Remove(a);                       // 第二次无效：不抛、不重复计数
            Assert.IsFalse(rules.IsWon, "只移除 1 块不应胜");
            Assert.AreEqual(2, rules.RemainingBlocks);
        }

        // ---------- §6.3 / 阶段 D 修正：误点距离不含自身占格 ----------
        [Test]
        public void 验收_误点距离_不含自身占格()
        {
            var edge = new BlockOutLevelData { Id = "edge", Width = 2, Height = 1 };
            edge.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 1, Direction = BlockOutDirection.Right });
            var r1 = new BlockOutGameRules();
            r1.StartLevel(edge);
            Assert.IsFalse(r1.TryGetWrongMoveDistance(r1.Blocks[0], out int e0), "贴边无空格：不可演示距离");
            Assert.AreEqual(0, e0);

            var blocked = new BlockOutLevelData { Id = "blk", Width = 4, Height = 1 };
            blocked.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, Direction = BlockOutDirection.Right });
            blocked.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 2, Direction = BlockOutDirection.Right });
            var r2 = new BlockOutGameRules();
            r2.StartLevel(blocked);
            Assert.IsTrue(r2.TryGetWrongMoveDistance(r2.Blocks[0], out int e2), "受阻可演示距离");
            Assert.AreEqual(1, e2, "空格数不含自身占格（列0→列1空→列2占）");
        }

        // ---------- §6.4 提示轮换不重复 ----------
        [Test]
        public void 验收_提示轮换_不重复已提示块()
        {
            var level = new BlockOutLevelData { Id = "hint", Width = 3, Height = 1 };
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 1, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 2, Direction = BlockOutDirection.Right });
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);
            var tools = new BlockOutToolController(rules, 3, 0, 0);
            var seen = new List<BlockOutBlockData>();
            BlockOutBlockData cur;
            while ((cur = tools.TryUseHint()) != null && seen.Count < 3)
            {
                Assert.IsFalse(seen.Contains(cur), "不得重复提示同一块");
                seen.Add(cur);
            }
            Assert.AreEqual(3, seen.Count, "3 块均被提示一次");
        }

        // ---------- §6.5 锤子零库存进入失败 ----------
        [Test]
        public void 验收_锤子零库存_进入失败()
        {
            var level = new BlockOutLevelData { Id = "hammer", Width = 3, Height = 1 };
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, Direction = BlockOutDirection.Right });
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);
            var tools = new BlockOutToolController(rules, 0, 0, 0);   // 锤子 0
            Assert.IsFalse(tools.EnterHammerMode(), "零库存进入失败");
            Assert.IsFalse(tools.IsHammerSelecting);
        }

        // ---------- §6.6 魔法目标上限 ----------
        [Test]
        public void 验收_魔法目标_不超过上限()
        {
            var level = new BlockOutLevelData { Id = "magic", Width = 3, Height = 1 };
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 0, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 1, Direction = BlockOutDirection.Right });
            level.Blocks.Add(new BlockOutBlockData { Row = 0, Column = 2, Direction = BlockOutDirection.Right });
            var rules = new BlockOutGameRules();
            rules.StartLevel(level);
            var tools = new BlockOutToolController(rules, 0, 0, 1);
            var all = tools.PickMagicTargets(6);
            Assert.AreEqual(3, all.Count, "受块数约束，全选 3 块且不超过上限 6");
            Assert.LessOrEqual(all.Count, 6);
            var two = tools.PickMagicTargets(2);
            Assert.AreEqual(2, two.Count, "不超过上限 2");
        }

        // ---------- §6.9 商店：300 币得 2 个道具 ----------
        [Test]
        public void 验收_道具包_300币2个()
        {
            var t = BlockOutGameplayConfig.Default().tools;
            Assert.AreEqual(300, t.toolPackCost, "ToolPackCost=300");
            Assert.AreEqual(2, t.toolPackAmount, "ToolPackAmount=2");
            Assert.AreEqual(300, BlockOutContentConfig.DefaultToolPackCost);
            Assert.AreEqual(2, BlockOutContentConfig.DefaultToolPackAmount);
        }

        // ---------- §6.7 复活经济数值契约 ----------
        [Test]
        public void 验收_复活经济_数值契约()
        {
            var rev = BlockOutGameplayConfig.Default().revive;
            Assert.AreEqual(10, rev.freeThroughLevel, "免费复活覆盖 1-10 关");
            Assert.AreEqual(300, rev.coinCost, "金币复活 300 币");
            Assert.AreEqual(1, rev.lifeCount, "金币复活补 1 心");
            Assert.AreEqual(20f, rev.addTimeSeconds, "复活 +20s（倒计时模式）");
            Assert.AreEqual(3, rev.freeLifeCount, "免费复活补满 MaxLives=3");
        }

        // ---------- §2.2 奖励表优先 ----------
        [Test]
        public void 验收_奖励表优先_easy发10()
        {
            // 关卡自带值 35 仅兜底；easy 表值 10 优先
            Assert.AreEqual(10, BlockOutContentConfig.GetLevelReward("easy", 35));
            Assert.AreEqual(10, BlockOutContentConfig.GetLevelReward("easy", 0));
        }

        // ---------- §6.10 通关图片收藏闭环（依赖 Resources/Catalog，仅 Unity 运行） ----------
        [Test]
        [Category("UnityRuntime")]
        public void 验收_通关图片收藏_12关均有关联图片()
        {
            // 依赖 Unity 资源加载（ArtOutPictureConfig + 插画），离线桩 Resources.Load 返回 null。
            // Unity Test Runner 验收：进入收藏页确认第一章 12 片齐全且可查看大图（§6.10）。
            Assert.Ignore("通关图片收藏闭环需 Unity 资源加载，按 §6.10 在 Unity 内手动验收");
        }
    }
}
