using System;
using BlockOut.Config;
using UnityEngine;

namespace BlockOut.Infrastructure.Configuration
{
    /// <summary>
    /// GameplayConfig 加载器（S01：Resources.Load 等读取工作归 Infrastructure/Configuration）。
    /// 从 Resources 读 JSON，解析后整份校验；任何失败（缺失/非法/版本不支持）都给出明确路径与原因，
    /// 并整体回退默认配置。DTO 与默认值仍归 <see cref="BlockOutGameplayConfig"/>（Core/Configuration）。
    /// </summary>
    public static class BlockOutGameplayConfigLoader
    {
        public const string ResourcePath = "BlockOut/GameplayConfig";

        /// <summary>加载并设置 <see cref="BlockOutGameplayConfig.Active"/>；绝不抛出，绝不部分应用。</summary>
        public static BlockOutGameplayConfig LoadAndActivate()
        {
            var cfg = Load();
            BlockOutGameplayConfig.Active = cfg;
            return cfg;
        }

        /// <summary>加载（不设置 Active）。失败时返回 <see cref="BlockOutGameplayConfig.Default"/>。</summary>
        public static BlockOutGameplayConfig Load()
        {
            var asset = Resources.Load<TextAsset>(ResourcePath);
            if (asset == null)
            {
                Debug.LogWarning("[BlockOut][GameplayConfig] 缺少 Resources/" + ResourcePath + ".json，采用完整 ArtOut 默认配置");
                return BlockOutGameplayConfig.Default();
            }
            try
            {
                // 先用默认值铺底，再叠加 JSON：缺字段保留默认值，不会把缺失当 0/false。
                var cfg = BlockOutGameplayConfig.Default();
                JsonUtility.FromJsonOverwrite(asset.text, cfg);
                var error = cfg.Validate();
                if (error != null)
                {
                    Debug.LogWarning("[BlockOut][GameplayConfig] Resources/" + ResourcePath + ".json 校验失败：" + error + "，采用完整 ArtOut 默认配置");
                    return BlockOutGameplayConfig.Default();
                }
                return cfg;
            }
            catch (Exception e)
            {
                Debug.LogWarning("[BlockOut][GameplayConfig] Resources/" + ResourcePath + ".json 解析异常：" + e.Message + "，采用完整 ArtOut 默认配置");
                return BlockOutGameplayConfig.Default();
            }
        }
    }
}
