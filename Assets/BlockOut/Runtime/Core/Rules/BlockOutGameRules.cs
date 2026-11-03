using System;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Config;

namespace BlockOut.Core
{
    /// <summary>
    /// Pure game rules, compatible with ArtOutGameRules.
    /// Board boundary = rectangle width x height. A block can fly if for EVERY occupied cell,
    /// the ray along its direction until leaving the board hits no other active block.
    /// </summary>
    public sealed class BlockOutGameRules
    {
        private readonly List<BlockOutBlockData> blocks = new List<BlockOutBlockData>();
        private BlockOutLevelData level;

        public IReadOnlyList<BlockOutBlockData> Blocks => blocks;
        /// <summary>最大生命数来自配置（BlockOutContentConfig.MaxLives，R02 经 JSON 同步），不在规则层硬编码。</summary>
        public int MaxLives => BlockOutContentConfig.MaxLives;
        public int Lives { get; private set; }
        public int RemainingBlocks { get; private set; }
        public bool IsWon => RemainingBlocks == 0 && blocks.Count > 0;
        public bool IsLost => Lives <= 0;

        public void StartLevel(BlockOutLevelData levelData)
        {
            this.level = levelData;
            blocks.Clear();
            for (int i = 0; i < levelData.Blocks.Count; i++)
            {
                var src = levelData.Blocks[i];
                var clone = src.Clone();
                clone.RuntimeIndex = i;
                clone.Active = true;
                clone.WrongMarked = false;
                blocks.Add(clone);
            }
            Lives = MaxLives;
            RemainingBlocks = blocks.Count;
        }

        public BlockOutRunProgress CaptureRunProgress(string levelId, string levelHash)
        {
            var removed = new List<int>();
            var wrong = new List<int>();
            foreach (var b in blocks)
            {
                if (b == null) continue;
                if (!b.Active) removed.Add(b.RuntimeIndex);
                if (b.Active && b.WrongMarked) wrong.Add(b.RuntimeIndex);
            }
            return new BlockOutRunProgress
            {
                LevelId = levelId,
                LevelHash = levelHash,
                BlockCount = blocks.Count,
                Lives = Lives,
                RemovedBlockIndices = removed.ToArray(),
                WrongBlockIndices = wrong.ToArray()
            };
        }

        public bool ApplyRunProgress(BlockOutRunProgress progress)
        {
            if (progress == null || progress.BlockCount != blocks.Count) return false;
            var removed = new HashSet<int>(progress.RemovedBlockIndices ?? new int[0]);
            var wrong = new HashSet<int>(progress.WrongBlockIndices ?? new int[0]);
            int remaining = 0;
            foreach (var b in blocks)
            {
                bool active = !removed.Contains(b.RuntimeIndex);
                b.Active = active;
                b.WrongMarked = active && wrong.Contains(b.RuntimeIndex);
                if (active) remaining++;
            }
            Lives = Mathf.Clamp(progress.Lives, 0, MaxLives);
            RemainingBlocks = remaining;
            return true;
        }

        public bool CanMove(BlockOutBlockData block)
        {
            return IsPathClear(block);
        }

        /// <summary>
        /// Returns number of empty cells before first blocker along direction (for feedback).
        /// Returns false if no blocker (path is clear).
        /// **只计真正空格，不计本块自身占格**（文档 §7.2；与参考
        /// ArtOutGameRules.TryGetWrongMoveFeedbackDistance 语义一致：自身格既不算 blocker 也不计 empty）。
        /// </summary>
        public bool TryGetWrongMoveDistance(BlockOutBlockData block, out int emptyCellsToBlocker)
        {
            emptyCellsToBlocker = 0;
            if (block == null || !block.Active) return false;
            var occ = BuildOccupancy(null);
            var step = GetDirectionStep(block.Direction);
            int nearest = int.MaxValue;
            foreach (var origin in block.GetOccupiedCells())
            {
                int empty = 0;
                var cursor = origin + step;
                while (IsInside(cursor))
                {
                    if (occ.TryGetValue(cursor, out var blocker))
                    {
                        if (blocker != block)
                        {
                            nearest = Mathf.Min(nearest, empty);
                            break;
                        }
                        // 自身占格：不计入空格距离（多格块沿自身轴向移动时射线会穿过自己的格子）
                    }
                    else
                    {
                        empty++;
                    }
                    cursor += step;
                }
            }
            if (nearest == int.MaxValue) return false;
            emptyCellsToBlocker = nearest;
            return true;
        }

        /// <summary>
        /// 判定一次点击是否成立。**成功时不立即移除方块**——移除是"延迟提交"，
        /// 由 GameManager 在飞出动画完成的回调里调用 <see cref="Remove"/>（P1-6）。
        /// 原因：若点击即移除，最后一块在动画途中切后台/杀进程时，存档里已经"全部移除"，
        /// 重启会恢复成空棋盘且永不结算。延迟提交让存档只落在"稳定局面"上。
        /// 错误点击（扣心/标记）仍是同步生效，不涉及动画。
        /// </summary>
        public BlockOutMoveResult TryTap(BlockOutBlockData block, bool consumeLifeOnWrong = true)
        {
            if (block == null || !block.Active)
                return new BlockOutMoveResult(false, false, false);

            if (CanMove(block))
                return new BlockOutMoveResult(true, false, false);

            if (block.WrongMarked)
                return new BlockOutMoveResult(false, false, true);

            block.WrongMarked = true;
            if (consumeLifeOnWrong) Lives--;
            return new BlockOutMoveResult(false, consumeLifeOnWrong, false);
        }

        public void Remove(BlockOutBlockData block)
        {
            if (block == null || !block.Active) return;
            block.Active = false;
            RemainingBlocks--;
        }

        public void AddLives(int count)
        {
            Lives = Mathf.Clamp(Lives + count, 0, MaxLives);
        }

        public BlockOutBlockData FindMovableBlock()
        {
            foreach (var b in blocks)
                if (b.Active && CanMove(b)) return b;
            return null;
        }

        public List<BlockOutBlockData> PickMagicTargets(int count)
        {
            return PickMagicTargets(count, null);
        }

        /// <summary>
        /// 魔法棒链式目标选取（参考 ArtOutMagicTool.Use）：在"已选目标被模拟移除"的占用上逐次选最多
        /// <paramref name="count"/> 个（"先 A 后 B 才可飞"的目标链合法）。
        /// <paramref name="extraFilter"/>（如"未被冻结锁死"）并入同一模拟状态裁决；被否决的块仍作为障碍保留、
        /// 不作为目标，但不会被错误地当作"已移除"从而让后续块穿过它（R03）。
        /// 注意：可动性由本方法的 <see cref="IsPathClear(BlockOutBlockData, HashSet{BlockOutBlockData})"/>（基于 ignored）裁决，
        /// 调用方不得再用原棋盘 CanMove 二次否决链式结果。
        /// </summary>
        public List<BlockOutBlockData> PickMagicTargets(int count, Func<BlockOutBlockData, bool> extraFilter)
        {
            var targets = new List<BlockOutBlockData>();
            if (count <= 0) return targets;
            var ignored = new HashSet<BlockOutBlockData>();      // 已选目标：模拟移除
            var considered = new HashSet<BlockOutBlockData>();   // 已扫描但被 extraFilter 否决的块（仍作障碍，不作为目标）
            while (targets.Count < count)
            {
                BlockOutBlockData found = null;
                foreach (var b in blocks)
                {
                    if (b.Active && !ignored.Contains(b) && !considered.Contains(b) && IsPathClear(b, ignored))
                    { found = b; break; }
                }
                if (found == null) break;
                if (extraFilter != null && !extraFilter(found)) { considered.Add(found); continue; }
                targets.Add(found);
                ignored.Add(found);
            }
            return targets;
        }

        // ---- internal ----
        private bool IsPathClear(BlockOutBlockData block) => IsPathClear(block, null);

        private bool IsPathClear(BlockOutBlockData block, HashSet<BlockOutBlockData> ignored)
        {
            var occ = BuildOccupancy(ignored);
            var step = GetDirectionStep(block.Direction);
            foreach (var origin in block.GetOccupiedCells())
            {
                var cursor = origin + step;
                while (IsInside(cursor))
                {
                    if (occ.TryGetValue(cursor, out var blocker) && blocker != block)
                        return false;
                    cursor += step;
                }
            }
            return true;
        }

        private Dictionary<Vector2Int, BlockOutBlockData> BuildOccupancy(HashSet<BlockOutBlockData> ignored)
        {
            var occ = new Dictionary<Vector2Int, BlockOutBlockData>();
            foreach (var b in blocks)
            {
                if (!b.Active || (ignored != null && ignored.Contains(b))) continue;
                foreach (var cell in b.GetOccupiedCells())
                    occ[cell] = b;
            }
            return occ;
        }

        private bool IsInside(Vector2Int cell)
        {
            return level != null && cell.x >= 0 && cell.y >= 0 && cell.x < level.Width && cell.y < level.Height;
        }

        public static Vector2Int GetDirectionStep(BlockOutDirection dir)
        {
            switch (dir)
            {
                case BlockOutDirection.Up: return Vector2Int.up;
                case BlockOutDirection.Down: return Vector2Int.down;
                case BlockOutDirection.Left: return Vector2Int.left;
                default: return Vector2Int.right;
            }
        }

        /// <summary>Build a simple hash of level data for save validation.</summary>
        public static string BuildLevelRunHash(BlockOutLevelData level)
        {
            if (level == null) return string.Empty;
            unchecked
            {
                int h = 17;
                h = h * 31 + (level.Id?.GetHashCode() ?? 0);
                h = h * 31 + level.Width;
                h = h * 31 + level.Height;
                h = h * 31 + level.Blocks.Count;
                foreach (var b in level.Blocks)
                {
                    h = h * 31 + b.ShapeId;
                    h = h * 31 + b.Column;
                    h = h * 31 + b.Row;
                    h = h * 31 + (int)b.Direction;
                }
                return h.ToString("X8");
            }
        }
    }
}
