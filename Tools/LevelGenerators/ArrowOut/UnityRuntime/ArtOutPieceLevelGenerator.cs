using System;
using System.Collections.Generic;
using UnityEngine;

namespace ArtOut
{
    public sealed class ArtOutPieceLevelGenerator
    {
        private readonly Color[] palette =
        {
            new Color(0.43f, 0.18f, 0.68f),
            new Color(0.18f, 0.48f, 0.84f),
            new Color(0.96f, 0.33f, 0.34f),
            new Color(0.19f, 0.67f, 0.5f),
            new Color(0.95f, 0.62f, 0.18f)
        };

        public List<ArtOutLevelData> Generate(int levelCount, int levelsPerChapter)
        {
            List<ArtOutLevelData> levels = new List<ArtOutLevelData>();
            levels.Add(CreateMusicalNoteLevel());

            for (int i = 1; i < levelCount; i++)
            {
                levels.Add(CreateGeneratedLevel(i, i / levelsPerChapter, i % levelsPerChapter));
            }

            return levels;
        }

        private ArtOutLevelData CreateMusicalNoteLevel()
        {
            ArtOutLevelData level = CreateBase("artout_001", 0, 0, "Musical Note", 7, 8);
            AddPiece(level, 3, 5, ArtOutDirection.Up, 0, 3, 0, new Vector2Int(1, 0));
            AddPiece(level, 3, 3, ArtOutDirection.Left, 0, 3, 0, new Vector2Int(0, 0));
            AddPiece(level, 2, 2, ArtOutDirection.Right, 0, 2, 0, new Vector2Int(1, 0));
            AddPiece(level, 2, 1, ArtOutDirection.Down, 0, 2, 0, new Vector2Int(0, 0));
            AddPiece(level, 0, 1, ArtOutDirection.Left, 0, 3, 0, new Vector2Int(0, 1));
            AddPiece(level, 5, 1, ArtOutDirection.Down, 0, 3, 0, new Vector2Int(1, 0));
            return level;
        }

        private ArtOutLevelData CreateGeneratedLevel(int index, int chapter, int levelInChapter)
        {
            int width = 6 + Mathf.Min(3, index / 8);
            int height = 7 + Mathf.Min(3, index / 10);
            ArtOutLevelData level = CreateBase("artout_" + (index + 1).ToString("000"), chapter, levelInChapter, "Gallery " + (index + 1), width, height);
            bool[,] occupied = new bool[width, height];
            System.Random random = new System.Random(7301 + index * 97);
            int targetPieces = Mathf.Min(8 + index / 3, 18);

            for (int pieceIndex = 0; pieceIndex < targetPieces; pieceIndex++)
            {
                int shapeId = random.Next(1, ArtOutShapeLibrary.ShapeCount + 1);
                int rotation = 0;
                List<Vector2Int> shape = ArtOutShapeLibrary.GetCells(shapeId, rotation);
                TryPlacePiece(level, occupied, random, shapeId, rotation, shape, pieceIndex);
            }

            return level;
        }

        private ArtOutLevelData CreateBase(string id, int chapter, int levelInChapter, string displayName, int width, int height)
        {
            return new ArtOutLevelData
            {
                Id = id,
                Chapter = chapter,
                LevelInChapter = levelInChapter,
                DisplayName = displayName,
                Width = width,
                Height = height,
                RewardCoins = 25 + levelInChapter * 5
            };
        }

        private bool TryPlacePiece(ArtOutLevelData level, bool[,] occupied, System.Random random, int shapeId, int rotation, List<Vector2Int> shape, int pieceIndex)
        {
            Vector2Int bounds = GetShapeBounds(shape);
            for (int attempt = 0; attempt < 80; attempt++)
            {
                int column = random.Next(0, Mathf.Max(1, level.Width - bounds.x + 1));
                int row = random.Next(0, Mathf.Max(1, level.Height - bounds.y + 1));
                if (!CanPlace(occupied, shape, column, row))
                {
                    continue;
                }

                MarkOccupied(occupied, shape, column, row);
                AddPiece(level, column, row, PickDirection(level, shape, column, row, random), pieceIndex, shapeId, rotation, ArtOutShapeLibrary.GetDefaultArrowCell(shapeId, rotation));
                return true;
            }

            return false;
        }

        private bool CanPlace(bool[,] occupied, List<Vector2Int> shape, int column, int row)
        {
            foreach (Vector2Int cell in shape)
            {
                if (occupied[column + cell.x, row + cell.y])
                {
                    return false;
                }
            }

            return true;
        }

        private void MarkOccupied(bool[,] occupied, List<Vector2Int> shape, int column, int row)
        {
            foreach (Vector2Int cell in shape)
            {
                occupied[column + cell.x, row + cell.y] = true;
            }
        }

        private void AddPiece(ArtOutLevelData level, int column, int row, ArtOutDirection direction, int pieceIndex, int shapeId, int rotation, Vector2Int arrowCell)
        {
            ArtOutBlockData piece = new ArtOutBlockData
            {
                Row = row,
                Column = column,
                ShapeId = shapeId,
                Rotation = rotation,
                ArrowCell = arrowCell,
                HasArrowCell = true,
                Direction = direction,
                Color = palette[pieceIndex % palette.Length]
            };

            piece.Cells.AddRange(ArtOutShapeLibrary.GetCells(shapeId, rotation));
            level.Blocks.Add(piece);
        }

        private ArtOutDirection PickDirection(ArtOutLevelData level, List<Vector2Int> shape, int column, int row, System.Random random)
        {
            Vector2 center = GetShapeCenter(shape) + new Vector2(column, row);
            float dx = center.x - (level.Width - 1) * 0.5f;
            float dy = center.y - (level.Height - 1) * 0.5f;
            if (Mathf.Abs(dx) > Mathf.Abs(dy))
            {
                return dx < 0f ? ArtOutDirection.Left : ArtOutDirection.Right;
            }

            if (Mathf.Abs(dy) > 0.2f)
            {
                return dy < 0f ? ArtOutDirection.Down : ArtOutDirection.Up;
            }

            return random.Next(2) == 0 ? ArtOutDirection.Left : ArtOutDirection.Right;
        }

        private Vector2Int GetShapeBounds(List<Vector2Int> shape)
        {
            Vector2Int max = Vector2Int.zero;
            foreach (Vector2Int cell in shape)
            {
                max = Vector2Int.Max(max, cell);
            }

            return new Vector2Int(max.x + 1, max.y + 1);
        }

        private Vector2 GetShapeCenter(List<Vector2Int> shape)
        {
            Vector2Int max = Vector2Int.zero;
            foreach (Vector2Int cell in shape)
            {
                max = Vector2Int.Max(max, cell);
            }

            return new Vector2(max.x * 0.5f, max.y * 0.5f);
        }

    }
}
