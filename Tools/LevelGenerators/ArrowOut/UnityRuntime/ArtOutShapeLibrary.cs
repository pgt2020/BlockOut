using System.Collections.Generic;
using UnityEngine;

namespace ArtOut
{
    public static class ArtOutShapeLibrary
    {
        public const float ReferenceCellWidth = 0.86f;
        public const float ReferenceCellHeight = 0.86f;
        public const float WoodSourceCellPixels = 120f;
        public const float WoodHorizontalGapPixels = -2f;
        public const float WoodVerticalGapPixels = -8f;
        public const float WoodSourceHorizontalStepPixels = WoodSourceCellPixels + WoodHorizontalGapPixels;
        public const float WoodSourceVerticalStepPixels = WoodSourceCellPixels + WoodVerticalGapPixels;
        public const float VisualCellPitchX = ReferenceCellWidth * WoodSourceHorizontalStepPixels / WoodSourceCellPixels;
        public const float VisualCellPitchY = ReferenceCellHeight * WoodSourceVerticalStepPixels / WoodSourceCellPixels;

        private static readonly int[][][] ShapeIdToCoords =
        {
            null,
            new[] { new[] { 0, 0 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 } },
            new[] { new[] { 0, 0 }, new[] { 1, 0 } },
            new[] { new[] { 0, 0 }, new[] { 1, 0 }, new[] { 1, 1 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 0 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 }, new[] { 0, 3 } },
            new[] { new[] { 0, 0 }, new[] { 1, 0 }, new[] { 2, 0 }, new[] { 3, 0 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 } },
            new[] { new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 } },
            new[] { new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 2, 1 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 1 } },
            new[] { new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 1 } },
            new[] { new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 2, 0 } },
            new[] { new[] { 0, 1 }, new[] { 1, 1 }, new[] { 2, 0 }, new[] { 2, 1 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 0 }, new[] { 2, 0 } },
            new[] { new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 2 } },
            new[] { new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 }, new[] { 2, 1 } },
            new[] { new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 } },
            new[] { new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 2, 0 }, new[] { 2, 1 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 2, 0 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 1 }, new[] { 1, 2 } },
            new[] { new[] { 0, 0 }, new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 1, 1 }, new[] { 2, 0 }, new[] { 2, 1 } },
            new[] { new[] { 0, 0 }, new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 2 } },
            new[] { new[] { 0, 2 }, new[] { 1, 0 }, new[] { 1, 1 }, new[] { 1, 2 }, new[] { 2, 0 } },
            new[] { new[] { 0, 1 }, new[] { 0, 2 }, new[] { 1, 1 }, new[] { 2, 0 }, new[] { 2, 1 } }
        };

        public static int ShapeCount => ShapeIdToCoords.Length - 1;

        public static List<Vector2Int> GetCells(int shapeId, int rotation)
        {
            List<Vector2Int> cells = new List<Vector2Int>();
            if (shapeId < 1 || shapeId >= ShapeIdToCoords.Length)
            {
                cells.Add(Vector2Int.zero);
                return cells;
            }

            List<Vector2Int> current = new List<Vector2Int>();
            foreach (int[] rowColumn in ShapeIdToCoords[shapeId])
            {
                current.Add(new Vector2Int(rowColumn[1], rowColumn[0]));
            }

            current = Normalize(current);
            int turns = ((rotation % 4) + 4) % 4;
            for (int i = 0; i < turns; i++)
            {
                current = RotateClockwise(current);
            }

            cells.AddRange(current);
            return cells;
        }

        public static Vector2Int GetDefaultArrowCell(int shapeId, int rotation)
        {
            List<Vector2Int> cells = GetCells(shapeId, rotation);
            Vector2 center = GetBoundsCenter(cells);
            Vector2Int best = cells[0];
            float bestDistance = float.MaxValue;
            foreach (Vector2Int cell in cells)
            {
                float distance = ((Vector2)cell - center).sqrMagnitude;
                if (distance < bestDistance)
                {
                    bestDistance = distance;
                    best = cell;
                }
            }

            return best;
        }

        public static Vector2 ToVisualLocal(Vector2Int cell)
        {
            return new Vector2(cell.x * VisualCellPitchX, cell.y * VisualCellPitchY);
        }

        public static Vector2 GetVisualBoundsCenter(IEnumerable<Vector2Int> cells)
        {
            bool found = false;
            Vector2Int min = Vector2Int.zero;
            Vector2Int max = Vector2Int.zero;
            foreach (Vector2Int cell in cells)
            {
                if (!found)
                {
                    min = cell;
                    max = cell;
                    found = true;
                    continue;
                }

                min = Vector2Int.Min(min, cell);
                max = Vector2Int.Max(max, cell);
            }

            if (!found)
            {
                return Vector2.zero;
            }

            return new Vector2(
                (min.x + max.x) * VisualCellPitchX * 0.5f,
                (min.y + max.y) * VisualCellPitchY * 0.5f);
        }

        private static List<Vector2Int> RotateClockwise(List<Vector2Int> cells)
        {
            List<Vector2Int> rotated = new List<Vector2Int>(cells.Count);
            foreach (Vector2Int cell in cells)
            {
                rotated.Add(new Vector2Int(cell.y, -cell.x));
            }

            return Normalize(rotated);
        }

        private static List<Vector2Int> Normalize(List<Vector2Int> cells)
        {
            int minX = int.MaxValue;
            int minY = int.MaxValue;
            foreach (Vector2Int cell in cells)
            {
                minX = Mathf.Min(minX, cell.x);
                minY = Mathf.Min(minY, cell.y);
            }

            for (int i = 0; i < cells.Count; i++)
            {
                cells[i] = new Vector2Int(cells[i].x - minX, cells[i].y - minY);
            }

            cells.Sort((left, right) => left.y != right.y ? left.y.CompareTo(right.y) : left.x.CompareTo(right.x));
            return cells;
        }

        private static Vector2 GetBoundsCenter(List<Vector2Int> cells)
        {
            Vector2Int min = cells[0];
            Vector2Int max = cells[0];
            foreach (Vector2Int cell in cells)
            {
                min = Vector2Int.Min(min, cell);
                max = Vector2Int.Max(max, cell);
            }

            return new Vector2((min.x + max.x) * 0.5f, (min.y + max.y) * 0.5f);
        }
    }
}
