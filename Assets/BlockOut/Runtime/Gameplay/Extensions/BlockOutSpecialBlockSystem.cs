using System;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Core;

namespace BlockOut.Gameplay
{
    /// <summary>
    /// Applies BlockOut innovation: special blocks (Bomb, Frozen, Rainbow).
    /// Special block data comes from a separate BlockOutLevelExtrasConfig —
    /// it does NOT modify the ArtOut level JSON format.
    /// </summary>
    public sealed class BlockOutSpecialBlockSystem
    {
        public enum SpecialType { None, Bomb, Frozen, Rainbow }

        private readonly Dictionary<int, SpecialType> pieceSpecials = new Dictionary<int, SpecialType>();
        private readonly BlockOutGameRules rules;

        public event Action<BlockOutBlockData, SpecialType> OnSpecialTriggered;
        public event Action OnExtrasLoaded;
        public bool HasExtras { get; private set; }

        public BlockOutSpecialBlockSystem(BlockOutGameRules gameRules)
        {
            rules = gameRules;
        }

        /// <summary>Load extras for a given level. Validates by levelId + sha256 hash.</summary>
        public void LoadExtras(BlockOutLevelData level, BlockOutLevelExtrasConfig config, string sourceHash)
        {
            pieceSpecials.Clear();
            HasExtras = false;
            if (config?.levels == null || level == null) return;

            foreach (var extra in config.levels)
            {
                if (extra.levelId != level.Id) continue;
                if (!string.IsNullOrEmpty(extra.sourceSha256) && extra.sourceSha256 != sourceHash)
                {
                    Debug.LogWarning($"[BlockOutSpecial] Hash mismatch for {level.Id}. Extras ignored.");
                    return;
                }
                if (extra.pieces == null) continue;
                foreach (var p in extra.pieces)
                {
                    if (p.pieceIndex < 0 || p.pieceIndex >= level.Blocks.Count) continue;
                    pieceSpecials[p.pieceIndex] = ParseType(p.type);
                }
                HasExtras = pieceSpecials.Count > 0;
                break;
            }
            OnExtrasLoaded?.Invoke();
        }

        public SpecialType GetSpecialType(int runtimeIndex)
        {
            return pieceSpecials.TryGetValue(runtimeIndex, out var t) ? t : SpecialType.None;
        }

        /// <summary>
        /// After a block is removed, process special effects.
        /// Returns list of blocks additionally removed by chain reactions.
        /// </summary>
        public List<BlockOutBlockData> ProcessRemovalChain(BlockOutBlockData removedBlock, bool notify = true)
        {
            var additionalRemoved = new List<BlockOutBlockData>();
            if (removedBlock == null) return additionalRemoved;

            var type = GetSpecialType(removedBlock.RuntimeIndex);
            if (type == SpecialType.None) return additionalRemoved;

            if(notify) OnSpecialTriggered?.Invoke(removedBlock, type);

            switch (type)
            {
                case SpecialType.Bomb:
                    additionalRemoved.AddRange(ProcessBomb(removedBlock));
                    break;
                case SpecialType.Rainbow:
                    additionalRemoved.AddRange(ProcessRainbow(removedBlock));
                    break;
                case SpecialType.Frozen:
                    // Frozen blocks can't be actively tapped; they can only be removed by chain.
                    // No effect when removed.
                    break;
            }

            // Recursively process chain up to max blocks
            int maxChain = rules.Blocks.Count;
            int processed = 0;
            var queue = new List<BlockOutBlockData>(additionalRemoved);
            additionalRemoved.Clear();
            var processedSet = new HashSet<int>();

            while (queue.Count > 0 && processed < maxChain)
            {
                var b = queue[0];
                queue.RemoveAt(0);
                if (processedSet.Contains(b.RuntimeIndex)) continue;
                processedSet.Add(b.RuntimeIndex);
                processed++;

                if (b.Active)
                {
                    rules.Remove(b);
                    additionalRemoved.Add(b);
                    var nextType = GetSpecialType(b.RuntimeIndex);
                    if (nextType == SpecialType.Bomb)
                        queue.AddRange(ProcessBomb(b));
                    else if (nextType == SpecialType.Rainbow)
                        queue.AddRange(ProcessRainbow(b));
                }
            }

            return additionalRemoved;
        }

        /// <summary>Frozen blocks cannot be actively tapped. Returns true if blocked.</summary>
        public bool IsBlockedByFrozen(BlockOutBlockData block)
        {
            if (block == null || GetSpecialType(block.RuntimeIndex) != SpecialType.Frozen) return false;
            // Check if any orthogonal neighbor has an active block
            var stepDirections = new[] { Vector2Int.up, Vector2Int.down, Vector2Int.left, Vector2Int.right };
            // Build occupancy
            var occ = new Dictionary<Vector2Int, BlockOutBlockData>();
            foreach (var b in rules.Blocks)
            {
                if (!b.Active) continue;
                foreach (var cell in b.GetOccupiedCells()) occ[cell] = b;
            }
            foreach (var cell in block.GetOccupiedCells())
            {
                foreach (var step in stepDirections)
                {
                    var neighbor = cell + step;
                    if (occ.TryGetValue(neighbor, out var other) && other != block && other.Active)
                        return true;
                }
            }
            return false;
        }

        private List<BlockOutBlockData> ProcessBomb(BlockOutBlockData bombBlock)
        {
            var result = new List<BlockOutBlockData>();
            // 3x3 around each occupied cell of the bomb
            var affected = new HashSet<Vector2Int>();
            foreach (var cell in bombBlock.GetOccupiedCells())
            {
                for (int dx = -1; dx <= 1; dx++)
                    for (int dy = -1; dy <= 1; dy++)
                        affected.Add(new Vector2Int(cell.x + dx, cell.y + dy));
            }
            // Build occupancy
            var occ = new Dictionary<Vector2Int, BlockOutBlockData>();
            foreach (var b in rules.Blocks)
            {
                if (!b.Active || b == bombBlock) continue;
                foreach (var cell in b.GetOccupiedCells()) occ[cell] = b;
            }
            var toRemove = new HashSet<BlockOutBlockData>();
            foreach (var cell in affected)
            {
                if (occ.TryGetValue(cell, out var other) && other != bombBlock)
                    toRemove.Add(other);
            }
            result.AddRange(toRemove);
            return result;
        }

        private List<BlockOutBlockData> ProcessRainbow(BlockOutBlockData rainbowBlock)
        {
            var result = new List<BlockOutBlockData>();
            Color targetColor = rainbowBlock.Color;
            foreach (var b in rules.Blocks)
            {
                if (!b.Active || b == rainbowBlock) continue;
                if (ColorsApproxEqual(b.Color, targetColor))
                    result.Add(b);
            }
            return result;
        }

        private static bool ColorsApproxEqual(Color a, Color b)
        {
            return Mathf.Abs(a.r - b.r) < 0.05f && Mathf.Abs(a.g - b.g) < 0.05f && Mathf.Abs(a.b - b.b) < 0.05f;
        }

        private static SpecialType ParseType(string type)
        {
            if (string.IsNullOrEmpty(type)) return SpecialType.None;
            switch (type.Trim().ToLowerInvariant())
            {
                case "bomb": return SpecialType.Bomb;
                case "frozen": return SpecialType.Frozen;
                case "rainbow": return SpecialType.Rainbow;
                default: return SpecialType.None;
            }
        }
    }
}
