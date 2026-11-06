using System;
using System.Collections.Generic;
using UnityEngine;

namespace ArtOut
{
    [Serializable]
    internal sealed class ArtOutLevelJson
    {
        public string id;
        public string displayName;
        public string pictureId;
        public int dataVersion;
        public int chapter;
        public int levelInChapter;
        public int width;
        public int height;
        public int rewardCoins;
        public List<ArtOutPieceJson> pieces;
    }

    [Serializable]
    internal sealed class ArtOutPieceJson
    {
        public int column;
        public int row;
        public int shapeId = 1;
        public string direction;
        public string color;
        public ArtOutVector2IntJson arrowCell;
    }

    [Serializable]
    internal sealed class ArtOutVector2IntJson
    {
        public int x;
        public int y;
    }

    public static class ArtOutLevelJsonParser
    {
        public static ArtOutLevelData Parse(string json)
        {
            if (string.IsNullOrWhiteSpace(json))
            {
                throw new ArgumentException("ArtOut level json is empty.");
            }

            ArtOutLevelJson source = JsonUtility.FromJson<ArtOutLevelJson>(json);
            if (source == null || string.IsNullOrEmpty(source.id))
            {
                throw new ArgumentException("ArtOut level json is missing id.");
            }

            ArtOutLevelData level = new ArtOutLevelData
            {
                Id = source.id,
                PictureId = source.pictureId,
                DataVersion = source.dataVersion > 0 ? source.dataVersion : 1,
                DisplayName = string.IsNullOrEmpty(source.displayName) ? source.id : source.displayName,
                Chapter = Mathf.Max(0, source.chapter),
                LevelInChapter = Mathf.Max(0, source.levelInChapter),
                Width = Mathf.Max(1, source.width),
                Height = Mathf.Max(1, source.height),
                RewardCoins = source.rewardCoins > 0 ? source.rewardCoins : 25 + Mathf.Max(0, source.levelInChapter) * 5
            };

            if (source.pieces == null)
            {
                return level;
            }

            for (int i = 0; i < source.pieces.Count; i++)
            {
                ArtOutPieceJson pieceJson = source.pieces[i];
                if (pieceJson == null)
                {
                    continue;
                }

                ArtOutBlockData block = new ArtOutBlockData
                {
                    Column = Mathf.Max(0, pieceJson.column),
                    Row = Mathf.Max(0, pieceJson.row),
                    ShapeId = Mathf.Clamp(pieceJson.shapeId, 1, ArtOutShapeLibrary.ShapeCount),
                    Rotation = 0,
                    Direction = ParseDirection(pieceJson.direction),
                    Color = ParseColor(pieceJson.color, i)
                };

                block.Cells.AddRange(ArtOutShapeLibrary.GetCells(block.ShapeId, block.Rotation));
                if (pieceJson.arrowCell != null)
                {
                    Vector2Int arrowCell = new Vector2Int(pieceJson.arrowCell.x, pieceJson.arrowCell.y);
                    if (ContainsCell(block.Cells, arrowCell))
                    {
                        block.ArrowCell = arrowCell;
                        block.HasArrowCell = true;
                    }
                }

                if (!block.HasArrowCell)
                {
                    block.ArrowCell = ArtOutShapeLibrary.GetDefaultArrowCell(block.ShapeId, block.Rotation);
                    block.HasArrowCell = true;
                }

                level.Blocks.Add(block);
            }

            return level;
        }

        private static bool ContainsCell(List<Vector2Int> cells, Vector2Int target)
        {
            foreach (Vector2Int cell in cells)
            {
                if (cell == target)
                {
                    return true;
                }
            }

            return false;
        }

        private static ArtOutDirection ParseDirection(string value)
        {
            if (string.IsNullOrEmpty(value))
            {
                return ArtOutDirection.Right;
            }

            switch (value.Trim().ToLowerInvariant())
            {
                case "up":
                case "u":
                case "^":
                    return ArtOutDirection.Up;
                case "down":
                case "d":
                case "v":
                    return ArtOutDirection.Down;
                case "left":
                case "l":
                case "<":
                    return ArtOutDirection.Left;
                default:
                    return ArtOutDirection.Right;
            }
        }

        private static Color ParseColor(string value, int index)
        {
            if (!string.IsNullOrEmpty(value) && ColorUtility.TryParseHtmlString(value, out Color color))
            {
                return color;
            }

            Color[] fallback =
            {
                new Color(0.43f, 0.18f, 0.68f),
                new Color(0.18f, 0.48f, 0.84f),
                new Color(0.96f, 0.33f, 0.34f),
                new Color(0.19f, 0.67f, 0.5f),
                new Color(0.95f, 0.62f, 0.18f)
            };
            return fallback[Mathf.Abs(index) % fallback.Length];
        }
    }
}
