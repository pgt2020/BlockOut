using UnityEngine;

namespace ArtOut
{
    public sealed class ArtOutPictureShape
    {
        private readonly bool[,] valid;
        private readonly Color[,] colors;

        private ArtOutPictureShape(bool[,] valid, Color[,] colors, int validCount)
        {
            this.valid = valid;
            this.colors = colors;
            ValidCount = validCount;
        }

        public int Rows => valid.GetLength(0);
        public int Columns => valid.GetLength(1);
        public int ValidCount { get; }

        public bool IsValid(int column, int row)
        {
            return column >= 0 &&
                   column < Columns &&
                   row >= 0 &&
                   row < Rows &&
                   valid[row, column];
        }

        public Color GetColor(int column, int row)
        {
            if (column < 0 || column >= Columns || row < 0 || row >= Rows)
            {
                return Color.white;
            }

            return colors[row, column];
        }

        public static ArtOutPictureShape FromRows(string[] rows, Color fallbackColor)
        {
            int rowCount = Mathf.Max(1, rows != null ? rows.Length : 0);
            int columnCount = 1;
            if (rows != null)
            {
                for (int i = 0; i < rows.Length; i++)
                {
                    columnCount = Mathf.Max(columnCount, string.IsNullOrEmpty(rows[i]) ? 0 : rows[i].Length);
                }
            }

            bool[,] valid = new bool[rowCount, columnCount];
            Color[,] colors = new Color[rowCount, columnCount];
            int validCount = 0;
            for (int row = 0; row < rowCount; row++)
            {
                string value = rows != null && row < rows.Length ? rows[row] : string.Empty;
                for (int column = 0; column < columnCount; column++)
                {
                    bool isValid = column < value.Length && IsFilled(value[column]);
                    valid[row, column] = isValid;
                    colors[row, column] = fallbackColor;
                    if (isValid)
                    {
                        validCount++;
                    }
                }
            }

            if (validCount == 0)
            {
                valid[0, 0] = true;
                validCount = 1;
            }

            return new ArtOutPictureShape(valid, colors, validCount);
        }

        public static ArtOutPictureShape FromTexture(Texture2D texture, float alphaThreshold, Color fallbackColor)
        {
            if (texture == null)
            {
                return null;
            }

            int rowCount = Mathf.Max(1, texture.height);
            int columnCount = Mathf.Max(1, texture.width);
            bool[,] valid = new bool[rowCount, columnCount];
            Color[,] colors = new Color[rowCount, columnCount];
            int validCount = 0;
            float threshold = Mathf.Clamp01(alphaThreshold);

            try
            {
                Color32[] pixels = texture.GetPixels32();
                for (int row = 0; row < rowCount; row++)
                {
                    int textureY = texture.height - 1 - row;
                    for (int column = 0; column < columnCount; column++)
                    {
                        Color color = pixels[textureY * texture.width + column];
                        bool isValid = color.a > threshold;
                        valid[row, column] = isValid;
                        color.a = 1f;
                        colors[row, column] = isValid ? color : fallbackColor;
                        if (isValid)
                        {
                            validCount++;
                        }
                    }
                }
            }
            catch (UnityException exception)
            {
                Debug.LogWarning("[ArtOutPictureShape] Texture is not readable: " + texture.name + ", " + exception.Message);
                return null;
            }

            if (validCount == 0)
            {
                return null;
            }

            return new ArtOutPictureShape(valid, colors, validCount);
        }

        private static bool IsFilled(char value)
        {
            return value != '.' && value != '0' && value != ' ';
        }
    }
}
