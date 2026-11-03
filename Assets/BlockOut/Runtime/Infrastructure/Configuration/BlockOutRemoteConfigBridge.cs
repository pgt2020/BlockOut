using System;
using BlockOut.Config;
using UnityEngine;

namespace BlockOut.Infrastructure.Configuration
{
    /// <summary>
    /// 远程配置桥（R05/R09）。把远程/本地配置值写入既有 <see cref="BlockOutContentConfig"/>，
    /// **不新造一套键名**：远程键沿用现有命名，旧键继续兼容读取（R23 契约）。
    /// 当前无服务端实现，提供本地默认值注入与结构占位；接入远程时只改本类内部来源。
    ///
    /// 被覆盖字段在 <see cref="BlockOutContentConfig"/> 中已由 const 改为 static（读取方无需改动），
    /// 默认值保留为 Default* 常量，便于测试断言与回退比对。
    /// </summary>
    public static class BlockOutRemoteConfigBridge
    {
        /// <summary>远程键名（外部后台契约，不得随重构改名）。</summary>
        public const string KeyUseTimeFailMode = "use_time_fail_mode";
        /// <summary>旧键（历史后台契约）：与新键等价，保留兼容读取，避免远程开关失效。</summary>
        public const string LegacyKeyUseTimeFailMode = "ArtOutUseTimeFailMode";
        public const string KeyMagicTargetCount = "magic_target_count";
        public const string KeyAdSimulatedLoadSeconds = "ad_simulated_load_seconds";
        public const string KeyToolUnlockHint = "tool_unlock_hint";
        public const string KeyToolUnlockHammer = "tool_unlock_hammer";
        public const string KeyToolUnlockMagic = "tool_unlock_magic";

        /// <summary>所有已登记远程键（供检查工具与文档核对，防止键名漂移）。</summary>
        public static readonly string[] AllKeys =
        {
            KeyUseTimeFailMode, KeyMagicTargetCount, KeyAdSimulatedLoadSeconds,
            KeyToolUnlockHint, KeyToolUnlockHammer, KeyToolUnlockMagic,
            LegacyKeyUseTimeFailMode,
        };

        /// <summary>
        /// 应用本地默认配置。行为与已加载的 <see cref="BlockOutGameplayConfig"/> 同步
        /// （ArtOut 对齐基线），不会把 JSON 值覆盖回旧 design_v5 常量。
        /// 返回是否发生了任何覆盖，便于启动日志与测试断言。
        /// </summary>
        public static bool ApplyLocalDefaults()
        {
            // 以生效配置为唯一来源同步桥接字段（含 MagicTargetCount / 解锁关卡 / 计时模式），
            // 不再把字段写回 Default* 旧常量，避免覆盖 GameplayConfig.json。
            BlockOutContentConfig.Apply(BlockOutGameplayConfig.Current);
            bool changed = false;
            changed |= TrySet(ref BlockOutContentConfig.AdSimulatedLoadSeconds, BlockOutContentConfig.DefaultAdSimulatedLoadSeconds);
            return changed;
        }

        /// <summary>按远程键名应用覆盖。未知键忽略，绝不抛异常中断启动。</summary>
        public static bool ApplyRemoteValue(string key, string value)
        {
            if (string.IsNullOrEmpty(key)) return false;
            try
            {
                switch (key)
                {
                    case KeyUseTimeFailMode:
                    case LegacyKeyUseTimeFailMode:
                        return TrySetBool(ref BlockOutContentConfig.UseTimeFailModeDefault, value);
                    case KeyMagicTargetCount:
                        if (int.TryParse(value, out var mc) && mc > 0)
                            return TrySet(ref BlockOutContentConfig.MagicTargetCount, mc);
                        return false;
                    case KeyAdSimulatedLoadSeconds:
                        if (float.TryParse(value, out var sec) && sec >= 0f)
                            return TrySet(ref BlockOutContentConfig.AdSimulatedLoadSeconds, sec);
                        return false;
                    case KeyToolUnlockHint:
                        if (int.TryParse(value, out var uh) && uh > 0)
                            return TrySet(ref BlockOutContentConfig.HintUnlockLevel, uh);
                        return false;
                    case KeyToolUnlockHammer:
                        if (int.TryParse(value, out var uhm) && uhm > 0)
                            return TrySet(ref BlockOutContentConfig.HammerUnlockLevel, uhm);
                        return false;
                    case KeyToolUnlockMagic:
                        if (int.TryParse(value, out var um) && um > 0)
                            return TrySet(ref BlockOutContentConfig.MagicUnlockLevel, um);
                        return false;
                    default:
                        return false;
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("[BlockOut] remote config '" + key + "' rejected: " + e.Message);
                return false;
            }
        }

        private static bool TrySet<T>(ref T field, T value) where T : struct
        {
            if (field.Equals(value)) return false;
            field = value;
            return true;
        }

        private static bool TrySetBool(ref bool field, string value)
        {
            if (bool.TryParse(value, out var b)) return TrySet(ref field, b);
            if (value == "1") return TrySet(ref field, true);
            if (value == "0") return TrySet(ref field, false);
            return false;
        }
    }
}
