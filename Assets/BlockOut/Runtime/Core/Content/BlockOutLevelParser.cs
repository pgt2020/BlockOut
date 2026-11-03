using System;
using System.Collections.Generic;
using UnityEngine;

namespace BlockOut.Core
{
    [Serializable]
    internal class BlockOutLevelJson
    {
        public string id;
        public string displayName;
        public string pictureId;
        public string difficulty;
        public int dataVersion;
        public int chapter;
        public int levelInChapter;
        public int width;
        public int height;
        public int rewardCoins;
        public List<BlockOutPieceJson> pieces;
    }

    [Serializable]
    internal class BlockOutPieceJson
    {
        public int column;
        public int row;
        public int shapeId = 1;
        public string direction;
        public string color;
        public BlockOutVec2Json arrowCell;
    }

    [Serializable]
    internal class BlockOutVec2Json
    {
        public int x;
        public int y;
    }

    /// <summary>
    /// Parses ArtOut-compatible level JSON into BlockOutLevelData.
    /// Field semantics are identical to the reference project.
    /// </summary>
    public static class BlockOutLevelParser
    {
        public static BlockOutLevelData Parse(string json)
        {
            if (string.IsNullOrWhiteSpace(json))
                throw new ArgumentException("Level json is empty.");

            var source = JsonUtility.FromJson<BlockOutLevelJson>(json);
            if (source == null || string.IsNullOrEmpty(source.id))
                throw new ArgumentException("Level json missing id.");

            var level = new BlockOutLevelData
            {
                Id = source.id,
                PictureId = source.pictureId,
                Difficulty = NormalizeDifficulty(source.difficulty,source.id,source.displayName,source.pictureId),
                DataVersion = source.dataVersion > 0 ? source.dataVersion : 1,
                DisplayName = string.IsNullOrEmpty(source.displayName) ? source.id : source.displayName,
                Chapter = Mathf.Max(0, source.chapter),
                LevelInChapter = Mathf.Max(0, source.levelInChapter),
                Width = Mathf.Max(1, source.width),
                Height = Mathf.Max(1, source.height),
                RewardCoins = source.rewardCoins > 0 ? source.rewardCoins : 25 + Mathf.Max(0, source.levelInChapter) * 5
            };

            if (source.pieces == null) return level;

            for (int i = 0; i < source.pieces.Count; i++)
            {
                var p = source.pieces[i];
                if (p == null) continue;

                var block = new BlockOutBlockData
                {
                    Column = Mathf.Max(0, p.column),
                    Row = Mathf.Max(0, p.row),
                    ShapeId = Mathf.Clamp(p.shapeId, 1, BlockOutShapeLibrary.ShapeCount),
                    Rotation = 0,
                    Direction = ParseDirection(p.direction),
                    Color = ParseColor(p.color, i)
                };
                block.Cells.AddRange(BlockOutShapeLibrary.GetCells(block.ShapeId, block.Rotation));

                if (p.arrowCell != null)
                {
                    var ac = new Vector2Int(p.arrowCell.x, p.arrowCell.y);
                    if (ContainsCell(block.Cells, ac))
                    {
                        block.ArrowCell = ac;
                        block.HasArrowCell = true;
                    }
                }
                if (!block.HasArrowCell)
                {
                    block.ArrowCell = BlockOutShapeLibrary.GetDefaultArrowCell(block.ShapeId, block.Rotation);
                    block.HasArrowCell = true;
                }
                level.Blocks.Add(block);
            }

            Validate(level);
            return level;
        }

        /// <summary>Validates blocks are in-bounds and non-overlapping. Logs warnings for invalid data.</summary>
        public static void Validate(BlockOutLevelData level)
        {
            var occupied = new HashSet<Vector2Int>();
            for (int i = 0; i < level.Blocks.Count; i++)
            {
                var b = level.Blocks[i];
                foreach (var c in b.GetOccupiedCells())
                {
                    if (c.x < 0 || c.x >= level.Width || c.y < 0 || c.y >= level.Height)
                        Debug.LogWarning($"[BlockOutParser] Level {level.Id}: block {i} cell ({c.x},{c.y}) out of bounds ({level.Width}x{level.Height})");
                    if (!occupied.Add(c))
                        Debug.LogWarning($"[BlockOutParser] Level {level.Id}: overlapping cell ({c.x},{c.y}) at block {i}");
                }
            }
        }

        private static bool ContainsCell(List<Vector2Int> cells, Vector2Int target)
        {
            foreach (var c in cells) if (c == target) return true;
            return false;
        }

        public static BlockOutDirection ParseDirection(string value)
        {
            if (string.IsNullOrEmpty(value)) return BlockOutDirection.Right;
            switch (value.Trim().ToLowerInvariant())
            {
                case "up": case "u": case "^": return BlockOutDirection.Up;
                case "down": case "d": case "v": return BlockOutDirection.Down;
                case "left": case "l": case "<": return BlockOutDirection.Left;
                default: return BlockOutDirection.Right;
            }
        }

        private static string NormalizeDifficulty(string value, params string[] fallbackSources)
        {
            if (!string.IsNullOrEmpty(value))
            {
                string normalized = NormalizeDifficultyToken(value);
                if (!string.IsNullOrEmpty(normalized))
                {
                    return normalized;
                }
            }

            if (fallbackSources != null)
            {
                for (int i = 0; i < fallbackSources.Length; i++)
                {
                    string inferred = InferDifficultyFromText(fallbackSources[i]);
                    if (!string.IsNullOrEmpty(inferred))
                    {
                        return inferred;
                    }
                }
            }

            return "normal";
        }

        private static string NormalizeDifficultyToken(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return null;
            }

            switch (value.Trim().ToLowerInvariant())
            {
                case "easy":
                case "normal":
                case "hard":
                case "extreme":
                case "expert":
                case "insane":
                    return value.Trim().ToLowerInvariant();
                default:
                    return null;
            }
        }

        private static string InferDifficultyFromText(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return null;
            }

            string[] parts = value.Split(new[] { '_', '-', ' ', '.', '/', '\\' }, StringSplitOptions.RemoveEmptyEntries);
            for (int i = parts.Length - 1; i >= 0; i--)
            {
                string normalized = NormalizeDifficultyToken(parts[i]);
                if (!string.IsNullOrEmpty(normalized))
                {
                    return normalized;
                }
            }

            return null;
        }

        private static readonly Color[] FallbackPalette =
        {
            new Color(0.43f, 0.18f, 0.68f),
            new Color(0.18f, 0.48f, 0.84f),
            new Color(0.96f, 0.33f, 0.34f),
            new Color(0.19f, 0.67f, 0.50f),
            new Color(0.95f, 0.62f, 0.18f)
        };

        private static Color ParseColor(string value, int index)
        {
            if (!string.IsNullOrEmpty(value) && ColorUtility.TryParseHtmlString(value, out var c))
                return c;
            return FallbackPalette[Mathf.Abs(index) % FallbackPalette.Length];
        }
    }
}
