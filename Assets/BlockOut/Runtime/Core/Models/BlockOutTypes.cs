using System;
using System.Collections.Generic;
using UnityEngine;

namespace BlockOut.Core
{
    public enum BlockOutDirection
    {
        Up,
        Down,
        Left,
        Right
    }

    public enum BlockOutGameState
    {
        Loading,
        Ready,
        ResolvingMove,
        Won,
        Lost
    }

    [Serializable]
    public sealed class BlockOutLevelData
    {
        public string Id;
        public string PictureId;
        public string Difficulty = "normal";
        public int DataVersion = 1;
        public int Chapter;
        public int LevelInChapter;
        public string DisplayName;
        public int Width;
        public int Height;
        public int RewardCoins;
        public int GameTime;
        public readonly List<BlockOutBlockData> Blocks = new List<BlockOutBlockData>();
    }

    [Serializable]
    public sealed class BlockOutBlockData
    {
        public int RuntimeIndex = -1;
        public int Row;
        public int Column;
        public int ShapeId = 1;
        public int Rotation;
        public Vector2Int ArrowCell;
        public bool HasArrowCell;
        public BlockOutDirection Direction;
        public Color Color = Color.white;
        public readonly List<Vector2Int> Cells = new List<Vector2Int>();
        public bool Active = true;
        public bool WrongMarked;

        public BlockOutBlockData Clone()
        {
            var clone = new BlockOutBlockData
            {
                Row = Row,
                Column = Column,
                RuntimeIndex = RuntimeIndex,
                ShapeId = ShapeId,
                Rotation = Rotation,
                ArrowCell = ArrowCell,
                HasArrowCell = HasArrowCell,
                Direction = Direction,
                Color = Color,
                Active = Active,
                WrongMarked = WrongMarked
            };
            clone.Cells.AddRange(Cells);
            return clone;
        }

        public IEnumerable<Vector2Int> GetLocalCells()
        {
            if (Cells.Count == 0)
            {
                yield return Vector2Int.zero;
                yield break;
            }
            foreach (var cell in Cells) yield return cell;
        }

        public IEnumerable<Vector2Int> GetOccupiedCells()
        {
            foreach (var cell in GetLocalCells())
                yield return new Vector2Int(Column + cell.x, Row + cell.y);
        }

        public Vector2Int GetArrowCellLocal()
        {
            if (HasArrowCell)
            {
                foreach (var cell in GetLocalCells())
                {
                    if (cell == ArrowCell) return ArrowCell;
                }
            }
            return BlockOutShapeLibrary.GetDefaultArrowCell(ShapeId, Rotation);
        }
    }

    [Serializable]
    public sealed class BlockOutRunProgress
    {
        public string LevelId;
        public string LevelHash;
        public int BlockCount;
        public int Lives;
        public int[] RemovedBlockIndices = new int[0];
        public int[] WrongBlockIndices = new int[0];
        public bool UseTimeFailMode;
        public float TimeRemainingSeconds;
        public float TimeCapacitySeconds;
    }

    public readonly struct BlockOutMoveResult
    {
        public readonly bool CanMove;
        public readonly bool LifeLost;
        public readonly bool AlreadyMarked;

        public BlockOutMoveResult(bool canMove, bool lifeLost, bool alreadyMarked)
        {
            CanMove = canMove;
            LifeLost = lifeLost;
            AlreadyMarked = alreadyMarked;
        }
    }

    [Serializable]
    public class BlockOutPictureEntry
    {
        public string id;
        public string name;
        public float alphaThreshold = 0.1f;
        public string sourceImage;
        public string texturePath;
        public string shapeImage;
        public string previewImage;
        public string completeImage;
        public string[] shapeRows;
    }

    [Serializable]
    public class BlockOutPictureConfig
    {
        public List<BlockOutPictureEntry> pictures = new List<BlockOutPictureEntry>();
    }

    [Serializable]
    public class BlockOutManifestEntry
    {
        public string id;
        public int gametime;
    }

    [Serializable]
    public class BlockOutManifest
    {
        public string version = "local";
        public List<BlockOutManifestEntry> levels = new List<BlockOutManifestEntry>();
    }

    // === BlockOut innovation layer: extras config (does NOT modify ArtOut level format) ===
    public enum BlockOutSpecialType
    {
        None,
        Bomb,
        Frozen,
        Rainbow
    }

    [Serializable]
    public class BlockOutPieceExtra
    {
        public int pieceIndex;
        public string type; // bomb | frozen | rainbow
        public int radius = 1; // 3x3 => radius=1
    }

    [Serializable]
    public class BlockOutLevelExtra
    {
        public string levelId;
        public string sourceSha256;
        public List<BlockOutPieceExtra> pieces = new List<BlockOutPieceExtra>();
    }

    [Serializable]
    public class BlockOutLevelExtrasConfig
    {
        public List<BlockOutLevelExtra> levels = new List<BlockOutLevelExtra>();
    }
}
