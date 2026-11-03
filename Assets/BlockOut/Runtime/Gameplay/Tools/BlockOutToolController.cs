using System;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Config;
using BlockOut.Core;

namespace BlockOut.Gameplay
{
    public enum BlockOutToolId { Hint, Hammer, Magic }
    public enum BlockOutToolMode { None, Hammer }

    /// <summary>
    /// 道具控制器（阶段 C：语义对齐参考 ArtOut Tools/*）：
    /// 提示 = 轮换高亮"未提示过的可飞块"，全部提示过则重置集合；无目标不扣库存；
    ///      扣减成功才把目标记入本局集合；切关/重开由 <see cref="ResetHintCycle"/> 重置；无硬冷却。
    /// 锤子 = 选择态工具（进入不扣库存，可消任意在场块含受阻块，取消不扣库存）；
    ///      零库存时进入失败（参考 Activate 返回 Failure，由 UI 走购买路径）。
    /// 魔法棒 = 一次自动移除最多 <see cref="BlockOutContentConfig.MagicTargetCount"/>（6）个目标
    ///      （链式模拟逐次移除，允许"先 A 后 B 才可飞"）；无目标不扣库存；一次施法只扣 1 库存。
    /// 解锁关卡（全局号，ArtOut ToolUnlockConfig 基线）：提示 2 / 锤子 3 / 魔法棒 4。
    /// 零库存购买：<see cref="BlockOutContentConfig.ToolPackCost"/> 币 × <see cref="BlockOutContentConfig.ToolPackAmount"/> 个。
    /// </summary>
    public sealed class BlockOutToolController
    {
        private readonly BlockOutGameRules rules;
        private int hintCount, hammerCount, magicCount;
        // 本局已提示集合（参考 ArtOutHintTool.hintedRuntimeIndices，按 RuntimeIndex 记录）
        private readonly BlockOutHintTool hint = new BlockOutHintTool();
        private readonly BlockOutHammerTool hammer = new BlockOutHammerTool();
        private readonly BlockOutMagicTool magic = new BlockOutMagicTool();
        public BlockOutToolMode Mode => hammer.Selecting ? BlockOutToolMode.Hammer : BlockOutToolMode.None;

        public event Action OnToolStateChanged;
        public event Action<bool> OnHammerModeChanged;

        public BlockOutToolController(BlockOutGameRules gameRules, int hints, int hammers, int magic)
        {
            rules = gameRules;
            hintCount = Mathf.Max(0, hints);
            hammerCount = Mathf.Max(0, hammers);
            magicCount = Mathf.Max(0, magic);
        }

        public int GetCount(BlockOutToolId tool)
        {
            switch (tool)
            {
                case BlockOutToolId.Hint: return hintCount;
                case BlockOutToolId.Hammer: return hammerCount;
                case BlockOutToolId.Magic: return magicCount;
                default: return 0;
            }
        }

        /// <summary>按全局关号判断解锁（玩家实际进度，不以当前所在关误判）。</summary>
        public bool IsUnlocked(BlockOutToolId tool, int globalLevelNumber)
        {
            int unlockLevel = tool == BlockOutToolId.Hint ? BlockOutContentConfig.HintUnlockLevel
                            : tool == BlockOutToolId.Hammer ? BlockOutContentConfig.HammerUnlockLevel
                            : BlockOutContentConfig.MagicUnlockLevel;
            return Mathf.Max(1, globalLevelNumber) >= unlockLevel;
        }

        public static string UnlockCondText(BlockOutToolId tool)
        {
            int lv = tool == BlockOutToolId.Hint ? BlockOutContentConfig.HintUnlockLevel
                   : tool == BlockOutToolId.Hammer ? BlockOutContentConfig.HammerUnlockLevel
                   : BlockOutContentConfig.MagicUnlockLevel;
            return "第 " + lv + " 关解锁";
        }

        public bool IsHammerSelecting => Mode == BlockOutToolMode.Hammer;

        /// <summary>
        /// 提示（参考 ArtOutHintTool.Use）：轮换返回下一个"未提示过的可飞块"；
        /// 可飞块全部已提示过时重置集合再返回第一个；无可飞块返回 null 且不扣库存。
        /// <paramref name="isActionable"/> 由 GameManager 注入（可飞 + 未被冻结锁死，P2-5）。
        /// 扣减成功才把目标记入本局已提示集合。
        /// </summary>
        public BlockOutBlockData TryUseHint(Func<BlockOutBlockData, bool> isActionable = null)
        {
            if (hintCount <= 0 || rules == null) return null;
            var target = FindNextHintTarget(isActionable);
            if (target == null) return null;
            hintCount--;
            
            OnToolStateChanged?.Invoke();
            return target;
        }

        private BlockOutBlockData FindNextHintTarget(Func<BlockOutBlockData, bool> isActionable)
        { return hint.Select(rules, isActionable); }

        /// <summary>切关/重开重置提示轮换（参考 ToolController.ResetHintCycle）。</summary>
        public void ResetHintCycle()
        {
            hint.Reset();
        }

        public bool EnterHammerMode()
        {
            if (!hammer.Enter(hammerCount)) return false;
            OnHammerModeChanged?.Invoke(true);
            OnToolStateChanged?.Invoke();
            return true;
        }

        public void CancelHammerMode()
        {
            if (Mode == BlockOutToolMode.None) return;
            hammer.Cancel();
            OnHammerModeChanged?.Invoke(false);
            OnToolStateChanged?.Invoke();
        }

        /// <summary>锤子选择态下点块：消除并扣 1 库存（任意在场块，含受阻块）。</summary>
        public bool TryHammerRemove(BlockOutBlockData block)
        {
            if (!hammer.CanRemove(block, hammerCount)) return false;
            hammerCount--;
            rules.Remove(block);
            hammer.Cancel();
            OnHammerModeChanged?.Invoke(false);
            OnToolStateChanged?.Invoke();
            return true;
        }

        /// <summary>
        /// 魔法棒目标选取（参考 ArtOutMagicTool.Use + rules.PickMagicTargets）：
        /// 链式模拟逐次移除选最多 count 个（"先 A 后 B 才可飞"的目标链合法）。
        /// R03：冻结过滤（<paramref name="isActionable"/>）直接交给规则层，并入同一"模拟移除"状态裁决，
        /// 绝不在原棋盘以 CanMove 二次否决链式结果（否则 A→B→C 链只会消最外侧 1 块）。
        /// </summary>
        public List<BlockOutBlockData> PickMagicTargets(int count, Func<BlockOutBlockData, bool> isActionable = null)
        {
            if (rules == null) return new List<BlockOutBlockData>();
            // 把冻结过滤并入规则层链式模拟；规则层 IsPathClear(b, ignored) 已在"已选目标被模拟移除"的占用上裁决可动性。
            return magic.Select(rules, count, isActionable);
        }

        /// <summary>魔法棒施法扣 1 库存（在确认有目标后调用）。</summary>
        public bool ConsumeMagic()
        {
            if (magicCount <= 0) return false;
            magicCount--;
            OnToolStateChanged?.Invoke();
            return true;
        }

        public sealed class Snapshot
        {
            public int Hint, Hammer, Magic;
            public bool Selecting;
            public int[] Hinted;
        }
        public Snapshot Capture() => new Snapshot { Hint=hintCount, Hammer=hammerCount, Magic=magicCount, Selecting=hammer.Selecting, Hinted=hint.Capture() };
        public void Restore(Snapshot snapshot)
        {
            hintCount=snapshot.Hint; hammerCount=snapshot.Hammer; magicCount=snapshot.Magic;
            hint.Restore(snapshot.Hinted); hammer.Restore(snapshot.Selecting);
            OnHammerModeChanged?.Invoke(hammer.Selecting); OnToolStateChanged?.Invoke();
        }

        public void AddTool(BlockOutToolId tool, int count)
        {
            switch (tool)
            {
                case BlockOutToolId.Hint: hintCount += count; break;
                case BlockOutToolId.Hammer: hammerCount += count; break;
                case BlockOutToolId.Magic: magicCount += count; break;
            }
            OnToolStateChanged?.Invoke();
        }

        /// <summary>整体回写库存（R07：道具消费事务失败回滚内存 Tools，使其与已回滚的 Profile 一致）。</summary>
        public void SetCounts(int hint, int hammer, int magic)
        {
            hintCount = Mathf.Max(0, hint);
            hammerCount = Mathf.Max(0, hammer);
            magicCount = Mathf.Max(0, magic);
            OnToolStateChanged?.Invoke();
        }
    }
}
