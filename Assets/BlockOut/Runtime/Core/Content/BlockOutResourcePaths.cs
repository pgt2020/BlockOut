namespace BlockOut.Core
{
    /// <summary>
    /// 集中资源目录映射（R10/R23）。
    /// 所有 <c>Resources.Load</c> 路径必须经由此处，禁止在业务类里写字面量。
    ///
    /// R23 命名清理：历史目录 <c>Resources/ArtOut</c> 属"旧项目名残留"，
    /// 但它同时是**已发布存档与关卡 ID 的加载契约**，因此：
    /// - 现行值保持 <c>ArtOut/...</c> 不变（不丢档、不破坏关卡 ID）；
    /// - 同时登记 <see cref="Aliases"/>，将来迁到 <c>BlockOut/...</c> 时只改这里 + 保留旧目录兼容读取；
    /// - 新增资源一律使用 <see cref="BlockOutBlock"/> / <see cref="BlockOutAudio"/> 等 BlockOut 语义前缀。
    /// </summary>
    public static class BlockOutResourcePaths
    {
        // ---- 关卡与内容（旧契约路径，保持兼容）----
        public const string Manifest = "ArtOut/GameAssets";
        public const string Levels = "ArtOut/Levels";
        public const string PictureConfig = "ArtOut/ArtOutPictureConfig";
        public const string LevelExtras = "ArtOut/BlockOutLevelExtras";

        // ---- BlockOut 语义资源 ----
        public const string BlockOutBlock = "block";
        public const string BlockOutFont = "Fonts/SourceHanSansCN-Regular";
        public const string BlockOutAudio = "audio";

        /// <summary>章节图根路径：block/ch{chapterIndex+1}/{full|preview|silhouette}。</summary>
        public static string ChapterArt(int chapterIndex, string kind)
        {
            return BlockOutBlock + "/ch" + (chapterIndex + 1).ToString("00") + "/" + kind;
        }

        /// <summary>
        /// 旧路径别名登记表（迁移时启用）：新键 = 旧键。
        /// 仅作为迁移记录与检查工具输入，当前不改变任何加载行为。
        /// </summary>
        public static readonly string[] LegacyAliases =
        {
            "ArtOut/GameAssets",
            "ArtOut/Levels",
            "ArtOut/ArtOutPictureConfig",
            "ArtOut/BlockOutLevelExtras",
        };
    }
}
