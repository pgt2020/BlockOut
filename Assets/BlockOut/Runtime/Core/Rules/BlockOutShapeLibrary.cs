using System.Collections.Generic;
using UnityEngine;

namespace BlockOut.Core
{
    /// <summary>
    /// Shape library compatible with ArtOut shapeId 1..30.
    /// Coordinate semantics: local (x = column right, y = row up).
    /// The reference array stores [row, col] pairs; we convert to Vector2Int(col=x, row=y).
    /// Table is verbatim-identical to ArtOutShapeLibrary.ShapeIdToCoords (shapeId 1..30),
    /// so reference level JSON ports 1:1 without shape remapping.
    /// </summary>
    public static class BlockOutShapeLibrary
    {
        // index 0 is null placeholder; shapeId 1..28 are valid.
        private static readonly int[][][] ShapeIdToCoords =
        {
            null,
            new[] { new[] { 0, 0 } },                                                    // 1  single
            new[] { new[] { 0, 0 }, new[] { 0, 1 } },                                    // 2  horizontal domino
            new[] { new[] { 0, 0 }, new[] { 1, 0 } },                                    // 3  vertical domino
            new[] { new[] { 0, 0 }, new[] { 1, 0 }, new[] { 1, 1 } },                    // 4  L (corner down-right)
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 0 } },                    // 5  L (other corner)
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 } },                    // 6  horizontal triomino
            new[] { new[] { 0, 0 }, new[] { 1, 0 }, new[] { 2, 0 } },                    // 7  vertical triomino
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 }, new[] { 0, 3 } },     // 8  horizontal I-4
            new[] { new[] { 0, 0 }, new[] { 1, 0 }, new[] { 2, 0 }, new[] { 3, 0 } },     // 9  vertical I-4
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 } },     // 10 O square
            new[] { new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 } },     // 11 T (vertical stem)
            new[] { new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 2, 1 } },     // 12 T (horizontal stem)
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 1 } },     // 13 T (pointing down)
            new[] { new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 1 } },     // 14 S/Z
            new[] { new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 2, 0 } },     // 15 S/Z other
            new[] { new[] { 0, 1 }, new[] { 1, 1 }, new[] { 2, 0 }, new[] { 2, 1 } },     // 16 Z
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 1 }, new[] { 2, 1 } },     // 17 L long
            new[] { new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 } },     // 18 J long
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 2 } },     // 19 L corner 4
            new[] { new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 }, new[] { 2, 1 } }, // 20 X / plus
            new[] { new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 } }, // 21 P
            new[] { new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 2, 0 }, new[] { 2, 1 } }, // 22 U-ish
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 2, 0 } }, // 23 P variant
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 1 }, new[] { 2, 1 } },     // 24 L-4 tail
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 1 }, new[] { 1, 2 } }, // 25
            new[] { new[] { 0, 0 }, new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 } }, // 26
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 1 }, new[] { 2, 0 }, new[] { 2, 1 } }, // 27
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 2 } }, // 28 U pentomino
            new[] { new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 }, new[] { 2, 0 } }, // 29
            new[] { new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 1 }, new[] { 2, 0 }, new[] { 2, 1 } }  // 30
        };

        public static int ShapeCount => ShapeIdToCoords.Length - 1;

        public static List<Vector2Int> GetCells(int shapeId, int rotation)
        {
            var cells = new List<Vector2Int>();
            if (shapeId < 1 || shapeId >= ShapeIdToCoords.Length)
            {
                cells.Add(Vector2Int.zero);
                return cells;
            }

            var current = new List<Vector2Int>();
            foreach (int[] rc in ShapeIdToCoords[shapeId])
            {
                // rc[0] = row (y), rc[1] = column (x)
                current.Add(new Vector2Int(rc[1], rc[0]));
            }

            current = Normalize(current);
            int turns = ((rotation % 4) + 4) % 4;
            for (int i = 0; i < turns; i++)
                current = RotateClockwise(current);

            cells.AddRange(current);
            return cells;
        }

        public static Vector2Int GetDefaultArrowCell(int shapeId, int rotation)
        {
            var cells = GetCells(shapeId, rotation);
            Vector2 center = GetBoundsCenter(cells);
            Vector2Int best = cells[0];
            float bestDist = float.MaxValue;
            foreach (var cell in cells)
            {
                float d = ((Vector2)cell - center).sqrMagnitude;
                if (d < bestDist) { bestDist = d; best = cell; }
            }
            return best;
        }

        private static List<Vector2Int> RotateClockwise(List<Vector2Int> cells)
        {
            var rotated = new List<Vector2Int>(cells.Count);
            foreach (var cell in cells)
                rotated.Add(new Vector2Int(cell.y, -cell.x));
            return Normalize(rotated);
        }

        private static List<Vector2Int> Normalize(List<Vector2Int> cells)
        {
            int minX = int.MaxValue, minY = int.MaxValue;
            foreach (var c in cells) { minX = Mathf.Min(minX, c.x); minY = Mathf.Min(minY, c.y); }
            for (int i = 0; i < cells.Count; i++)
                cells[i] = new Vector2Int(cells[i].x - minX, cells[i].y - minY);
            cells.Sort((a, b) => a.y != b.y ? a.y.CompareTo(b.y) : a.x.CompareTo(b.x));
            return cells;
        }

        private static Vector2 GetBoundsCenter(List<Vector2Int> cells)
        {
            var min = cells[0]; var max = cells[0];
            foreach (var c in cells) { min = Vector2Int.Min(min, c); max = Vector2Int.Max(max, c); }
            return new Vector2((min.x + max.x) * 0.5f, (min.y + max.y) * 0.5f);
        }
    }
}
