using System.Collections.Generic;
using UnityEngine;
using BlockOut.Core;

namespace BlockOut.UI
{
    public enum ChapterArtStatus
    {
        Loaded,        // 正式章节图集命中
        Placeholder,   // 正式素材缺失 → 程序占位（明确标注，不当正式交付）
        Failed,        // 加载失败（07-C）：重试 2 次后转"稍后再试"
    }

    /// <summary>
    /// 章节插画提供者（拼片模型：一章一张完整插画 + 12 个揭晓区域，09 §0 / 11 §1）。
    /// 资源路径规则（11 §0）：block/ch{NN}/&lt;full|preview|region_01..12|fail|silhouette&gt;。
    /// 正式素材未就绪时使用程序占位图；占位资源不当正式交付，路径与替换接口集中于此。
    /// </summary>
    public sealed class BlockOutChapterArtProvider : System.IDisposable
    {
        public const int RegionColumns = 4;
        public const int RegionRows = 3;
        public const int RegionCount = 12;

        /// <summary>统一源画布边长（11 §1：完整图/预览图/剪影/12 区域共用 1080×1080）。
        /// region 几何一律按此画布固定切分，绝不按显示容器反算（P1-6）。</summary>
        public const float SourceCanvas = 1080f;
        public const float SourceRegionW = SourceCanvas / RegionColumns;   // 270
        public const float SourceRegionH = SourceCanvas / RegionRows;      // 360

        /// <summary>开发开关：置 true 演练 07-C 图片加载失败态（默认 false，不进入正式构建）。</summary>
        public static bool ForceFailNextLoad = false;

        public ChapterArtStatus Status { get; private set; } = ChapterArtStatus.Placeholder;
        public int LoadAttempts { get; private set; }
        public bool RetryExhausted { get; private set; }
        public Sprite ArtSprite { get; private set; }
        public Sprite SilhouetteSprite { get; private set; }
        public Sprite FullSprite { get; private set; }
        private readonly List<Object> owned = new List<Object>();
        public bool IsProceduralPlaceholder { get; private set; }
        /// <summary>图片存在但标记为构图草稿（ART_DRAFT）：可见、可用，但不算最终美术。</summary>
        public bool IsDraftArtwork { get; private set; }

        private int chapterIndex = -1;
        private readonly Dictionary<string, Sprite> regionCache = new Dictionary<string, Sprite>();

        public static string PreviewResourcePath(int chapterIdx) => $"block/ch{chapterIdx + 1:00}/preview";
        public static string FullResourcePath(int chapterIdx) => $"block/ch{chapterIdx + 1:00}/full";
        public static string RegionResourcePath(int chapterIdx, int region) => $"block/ch{chapterIdx + 1:00}/region_{region + 1:00}";

        /// <summary>同目录下存在该文本文件 = 该章图片为"构图稿/草稿"，不是最终美术。
        /// 美术交付最终图时删除此文件即可，代码会自动按正式素材处理。</summary>
        public static string DraftMarkerResourcePath(int chapterIdx) => $"block/ch{chapterIdx + 1:00}/ART_DRAFT";

        /// <summary>是否命中草稿标记。命中时仍显示图片，但状态记为 Placeholder，不当正式素材统计。</summary>
        private static bool IsDraftArt(int chapterIdx)
        {
            var ta = Resources.Load<TextAsset>(DraftMarkerResourcePath(chapterIdx));
            return ta != null && !string.IsNullOrEmpty(ta.text.Trim());
        }

        /// <summary>加载章节预览图：正式资源 → 程序占位；ForceFailNextLoad → 失败态。</summary>
        public void LoadChapter(int chapterIdx)
        {
            chapterIndex = chapterIdx;
            LoadAttempts = 1;
            RetryExhausted = false;
            AttemptLoad();
        }

        /// <summary>重试（07-C）：重新拉取；失败 2 次后转"稍后再试"，不弹阻断窗。</summary>
        public void Retry()
        {
            if (RetryExhausted) return;
            if (LoadAttempts >= 3)
            {
                RetryExhausted = true;
                Status = ChapterArtStatus.Failed;
                return;
            }
            LoadAttempts++;
            AttemptLoad();
            RetryExhausted = Status == ChapterArtStatus.Failed && LoadAttempts >= 3;
        }

        private void AttemptLoad()
        {
            Dispose();
            IsProceduralPlaceholder = false;
            IsDraftArtwork = false;

            if (ForceFailNextLoad)
            {
                Status = ChapterArtStatus.Failed;
                return;
            }

            var real = Resources.Load<Sprite>(PreviewResourcePath(chapterIndex));
            if (real != null)
            {
                ArtSprite = real;
                FullSprite = Resources.Load<Sprite>(FullResourcePath(chapterIndex)) ?? real;
                SilhouetteSprite = Resources.Load<Sprite>($"block/ch{chapterIndex + 1:00}/silhouette");

                // 命中草稿标记 → 图能用但不是最终美术，不得记为正式素材（IsProceduralPlaceholder 保持 false，
                // 因为它确实是磁盘上的图片资源；但 Status 记 Placeholder，交付统计不会误算为正式美术）
                bool draft = IsDraftArt(chapterIndex);
                IsDraftArtwork = draft;
                Status = draft ? ChapterArtStatus.Placeholder : ChapterArtStatus.Loaded;
                return;
            }

            // Missing chapter artwork is an explicit content failure, never generated at runtime.
            ArtSprite=null; FullSprite=null; SilhouetteSprite=null;
            IsProceduralPlaceholder=false;
            Status=ChapterArtStatus.Failed;
        }

        /// <summary>只裁固定源区域。容器的 cover/contain 由整个 Artwork 节点统一处理。</summary>
        public Sprite RegionSprite(bool revealed, int region, bool full = false)
        {
            if (region < 0 || region >= RegionCount) return null;
            var src = revealed ? (full ? FullSprite : ArtSprite) : SilhouetteSprite;
            if (src == null) return null; // 缺少剪影时由 UI 显示中性遮罩，绝不泄露原图。
            string key = $"{src.GetInstanceID()}-{region}";
            if (regionCache.TryGetValue(key, out var cached)) return cached;
            // 使用 sprite 自身的矩形，支持矩形图集中非零原点的 Sprite。
            Rect bounds = src.rect;
            float w = bounds.width / RegionColumns;
            float h = bounds.height / RegionRows;
            var rect = new Rect(bounds.x + region % RegionColumns * w,
                bounds.y + (RegionRows - 1 - region / RegionColumns) * h, w, h);
            var result = Sprite.Create(src.texture, rect, new Vector2(0.5f, 0.5f), src.pixelsPerUnit);
            regionCache.Add(key, result);
            owned.Add(result);
            return result;
        }

        public void Dispose()
        {
            foreach (var resource in owned) if (resource != null) Object.Destroy(resource);
            owned.Clear();
            regionCache.Clear();
            ArtSprite = null;
            FullSprite = null;
            SilhouetteSprite = null;
        }

        // ------------------------------------------------------------
        // 首页预览卡前景装饰：玩具块 + 涟漪 + 飞出轨迹（06 默认稿）
        // ------------------------------------------------------------

        public Sprite ToyCell(Color color)
        {
            var data = new BlockOutBlockData { Color = color, Cells = { Vector2Int.zero } };
            return BlockOutIconFactory.BlockSprite(data, 1, 1, 128f);
        }

        public Sprite RippleSprite()
        {
            return BlockOutIconFactory.Circle(new Color(1f, 1f, 1f, 0f), new Color(1f, 1f, 1f, 0.85f), 2f);
        }
    }
}
