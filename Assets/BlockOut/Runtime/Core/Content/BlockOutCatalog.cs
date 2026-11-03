using System;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Config;

namespace BlockOut.Core
{
    /// <summary>
    /// 关卡目录加载（优先级：GameAssets.json manifest → Resources 单关 JSON → 兜底生成）。
    /// 本地 manifest 与参考工程顺序一致，共 606 关；目录先载入元信息，玩法数据按需解析。
    /// </summary>
    public sealed class BlockOutCatalog
    {
        public const int LevelsPerChapter = BlockOutContentConfig.LevelsPerChapter;
        // 路径集中到 BlockOutResourcePaths（R10/R23）：此处不再写字面量，迁移只改一处。
        private const string ManifestResourcePath = BlockOutResourcePaths.Manifest;
        private const string LevelsResourcePath = BlockOutResourcePaths.Levels;
        private const string PictureConfigResourcePath = BlockOutResourcePaths.PictureConfig;

        private readonly List<BlockOutLevelData> levels = new List<BlockOutLevelData>();
        private BlockOutPictureConfig pictureConfig;

        public IReadOnlyList<BlockOutLevelData> Levels => levels;
        public BlockOutPictureConfig Pictures => pictureConfig;
        public int LevelCount => levels.Count;
        public int ChapterCount => levels.Count == 0 ? 0 : (levels[levels.Count - 1].Chapter + 1);

        public void Load()
        {
            levels.Clear();
            LoadPictureConfig();

            var manifest = LoadManifest();
            if (manifest != null && manifest.levels != null && manifest.levels.Count > 0)
            {
                BuildFromManifest(manifest);
            }

            if (levels.Count == 0)
            {
                LoadFromResourcesFolder();
            }


            // Last resort for missing content; shipped manifest contains 606 authored levels.
            if (levels.Count == 0)
            {
                Debug.LogError("[BlockOutCatalog] No level data found (manifest and Resources both empty or invalid). "
                    + "Using procedural fallback ONLY to avoid a permanent Loading hang; this is a content error, fix the level JSONs.");
                levels.AddRange(BlockOutFallbackGenerator.GenerateSet(count: 12));
            }
            BlockOutContentConfig.PublishedChapters=ChapterCount;
        }

        private void LoadPictureConfig()
        {
            var asset = Resources.Load<TextAsset>(PictureConfigResourcePath);
            if (asset != null && !string.IsNullOrEmpty(asset.text))
            {
                try { pictureConfig = JsonUtility.FromJson<BlockOutPictureConfig>(asset.text); }
                catch (Exception e) { Debug.LogWarning("[BlockOutCatalog] Picture config parse failed: " + e.Message); }
            }
            if (pictureConfig == null) pictureConfig = new BlockOutPictureConfig();
        }

        private BlockOutManifest LoadManifest()
        {
            var asset = Resources.Load<TextAsset>(ManifestResourcePath);
            if (asset == null || string.IsNullOrEmpty(asset.text)) return null;
            try
            {
                var json = asset.text.TrimStart('\uFEFF');
                return JsonUtility.FromJson<BlockOutManifest>(json);
            }
            catch (Exception e)
            {
                Debug.LogWarning("[BlockOutCatalog] Manifest parse failed: " + e.Message);
                return null;
            }
        }

        private void BuildFromManifest(BlockOutManifest manifest)
        {
            foreach(var entry in manifest.levels)
            {
                if(entry==null || string.IsNullOrEmpty(entry.id))continue;
                int index=levels.Count;
                levels.Add(new BlockOutLevelData { Id=entry.id,DisplayName=entry.id,Chapter=index/LevelsPerChapter,LevelInChapter=index%LevelsPerChapter,GameTime=entry.gametime });
            }
        }

        private BlockOutLevelData TryLoadLevelJsonById(string id)
        {
            var asset = Resources.Load<TextAsset>(LevelsResourcePath + "/" + id);
            if (asset != null && !string.IsNullOrEmpty(asset.text))
            {
                try { return BlockOutLevelParser.Parse(asset.text); }
                catch (Exception e) { Debug.LogWarning("[BlockOutCatalog] Parse " + id + " failed: " + e.Message); }
            }
            return null;
        }

        private void LoadFromResourcesFolder()
        {
            var assets = Resources.LoadAll<TextAsset>(LevelsResourcePath);
            if (assets == null) return;
            var parsed = new List<BlockOutLevelData>();
            foreach (var asset in assets)
            {
                if (asset == null || string.IsNullOrEmpty(asset.text) || asset.name.StartsWith("tutorial", StringComparison.OrdinalIgnoreCase)) continue;
                try
                {
                    var level = BlockOutLevelParser.Parse(asset.text);
                    if (level != null && !string.IsNullOrEmpty(level.Id)) parsed.Add(level);
                }
                catch (Exception e) { Debug.LogWarning("[BlockOutCatalog] Skip invalid level: " + e.Message); }
            }
            parsed.Sort((a, b) =>
            {
                int c = a.Chapter.CompareTo(b.Chapter);
                if (c != 0) return c;
                int l = a.LevelInChapter.CompareTo(b.LevelInChapter);
                if (l != 0) return l;
                return string.CompareOrdinal(a.Id, b.Id);
            });
            levels.AddRange(parsed);
        }

        public BlockOutLevelData GetLevel(int index)
        {
            var level=GetLevelMetadata(index);if(level==null)return null;
            index=Mathf.Clamp(index,0,levels.Count-1);
            if(level.Blocks.Count==0)
            {
                var loaded=TryLoadLevelJsonById(level.Id);
                if(loaded!=null)
                {
                    loaded.Chapter=level.Chapter;loaded.LevelInChapter=level.LevelInChapter;
                    if(level.GameTime>0)loaded.GameTime=level.GameTime;
                    levels[index]=level=loaded;
                }
            }
            return level;
        }
        public BlockOutLevelData GetLevelMetadata(int index)
        {
            return index<0 || index>=levels.Count ? null:levels[index];
        }

        public BlockOutPictureEntry FindPicture(string pictureId)
        {
            if (pictureConfig == null || pictureConfig.pictures == null || string.IsNullOrEmpty(pictureId)) return null;
            foreach (var p in pictureConfig.pictures)
                if (p.id == pictureId) return p;
            return null;
        }

        // ---- v5 章节结构辅助 ----

        /// <summary>该章在目录中是否有关卡数据（第二章无数据 → 未发布）。</summary>
        public bool HasChapterData(int chapterIndex)
        {
            foreach (var l in levels)
                if (l.Chapter == chapterIndex) return true;
            return false;
        }

        public int ChapterLevelCount(int chapterIndex)
        {
            int count = 0;
            foreach (var l in levels)
                if (l.Chapter == chapterIndex) count++;
            return count;
        }

        /// <summary>章节是否已解锁：前章 12/12（按档案通关集合推导，重复通关不重复解锁）。</summary>
        public bool IsChapterUnlocked(int chapterIndex, BlockOutPlayerProfile profile)
        {
            if (chapterIndex <= 0) return true;
            if (profile == null) return false;
            int prev = chapterIndex - 1;
            int start = prev * LevelsPerChapter;
            int completed = 0;
            for (int i = start; i < start + LevelsPerChapter; i++)
            {
                if (i >= levels.Count) break;
                var lv = GetLevelMetadata(i);
                if (lv != null && profile.IsLevelCompleted(lv.Id)) completed++;
            }
            return completed >= LevelsPerChapter;
        }

        /// <summary>章节内已通关数（拼片进度，一关一片）。</summary>
        public int GetCompletedCountInChapter(int chapterIndex, BlockOutPlayerProfile profile)
        {
            if (profile == null) return 0;
            int start = chapterIndex * LevelsPerChapter;
            int completed = 0;
            for (int i = start; i < start + LevelsPerChapter; i++)
            {
                if (i >= levels.Count) break;
                var lv = GetLevelMetadata(i);
                if (lv != null && profile.IsLevelCompleted(lv.Id)) completed++;
            }
            return completed;
        }

        /// <summary>章节内第一个未通关的全局索引；全部通关返回 -1。</summary>
        public int GetFirstUncompletedIndexInChapter(int chapterIndex, BlockOutPlayerProfile profile)
        {
            int start = chapterIndex * LevelsPerChapter;
            for (int i = start; i < start + LevelsPerChapter && i < levels.Count; i++)
            {
                var lv = GetLevelMetadata(i);
                if (lv == null || !profile.IsLevelCompleted(lv.Id)) return i;
            }
            return -1;
        }
    }

    /// <summary>
    /// 兜底生成器：仅在没有正式关卡数据时使用，保证可解性由调用方校验。
    /// </summary>
    public static class BlockOutFallbackGenerator
    {
        public static List<BlockOutLevelData> GenerateSet(int count)
        {
            var result = new List<BlockOutLevelData>();
            var rng = new System.Random(7301);
            for (int i = 0; i < count; i++)
            {
                result.Add(GenerateOne(i, rng));
            }
            return result;
        }

        public static BlockOutLevelData GenerateOne(int index, System.Random rng)
        {
            int width = 7, height = 8;
            int targetBlocks = 8 + (index % 4);
            var level = new BlockOutLevelData
            {
                Id = "fallback_" + index.ToString("D3"),
                DisplayName = "Fallback Level " + (index + 1),
                PictureId = "fallback_" + index.ToString("D3"),
                Difficulty = "easy",
                Chapter = index / BlockOutCatalog.LevelsPerChapter,
                LevelInChapter = index % BlockOutCatalog.LevelsPerChapter,
                Width = width,
                Height = height,
                RewardCoins = 25 + index * 5,
                GameTime = 120
            };

            var occupied = new HashSet<Vector2Int>();
            int paletteCount = BlockOutShapeLibrary.ShapeCount;
            for (int b = 0; b < targetBlocks; b++)
            {
                int shapeId = rng.Next(1, Math.Min(6, paletteCount + 1));
                var cells = BlockOutShapeLibrary.GetCells(shapeId, 0);
                for (int attempt = 0; attempt < 50; attempt++)
                {
                    int col = rng.Next(0, width - 2);
                    int row = rng.Next(0, height - 2);
                    bool fits = true;
                    foreach (var c in cells)
                    {
                        var world = new Vector2Int(col + c.x, row + c.y);
                        if (world.x < 0 || world.x >= width || world.y < 0 || world.y >= height || occupied.Contains(world))
                        { fits = false; break; }
                    }
                    if (!fits) continue;

                    foreach (var c in cells) occupied.Add(new Vector2Int(col + c.x, row + c.y));
                    var dirs = new[] { BlockOutDirection.Up, BlockOutDirection.Down, BlockOutDirection.Left, BlockOutDirection.Right };
                    var colors = new[] { "#FF6B6B", "#FFB347", "#FFE066", "#7ED9A6", "#9B7ED9", "#6B9FFF" };
                    // Cells 是 readonly 字段：对象初始化器不能赋值，构造后 AddRange（C01 修复）
                    var block = new BlockOutBlockData
                    {
                        Column = col,
                        Row = row,
                        ShapeId = shapeId,
                        Rotation = 0,
                        Direction = dirs[rng.Next(0, 4)],
                        Color = HexToColor(colors[rng.Next(0, colors.Length)]),
                        HasArrowCell = true,
                        ArrowCell = BlockOutShapeLibrary.GetDefaultArrowCell(shapeId, 0)
                    };
                    block.Cells.AddRange(cells);
                    level.Blocks.Add(block);
                    break;
                }
            }
            return level;
        }

        private static Color HexToColor(string hex)
        {
            ColorUtility.TryParseHtmlString(hex, out var c);
            return c;
        }
    }
}
