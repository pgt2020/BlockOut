using UnityEngine;

namespace BlockOut.Config
{
    /// <summary>
    /// 首发内容与经济配置。
    /// 规则值唯一来源已切换为 <see cref="BlockOutGameplayConfig"/>（本地 JSON，ArtOut 对齐基线）；
    /// 本类作为兼容桥保留：启动时由 <see cref="Apply"/> 把已加载配置同步进来，
    /// 保证既有消费者（UI/Gameplay/测试）读到同一份值，不会出现"JSON 一套、常量一套"。
    /// 无 JSON 时各默认值即 ArtOut 基线，行为与加载默认配置一致。
    /// </summary>
    public static class BlockOutContentConfig
    {
        public const int LevelsPerChapter = 12;
        public static int PublishedChapters = 51; // 第二章未发布 → 首页显示"新章节准备中"

        // 新档默认库存（ArtOut 基线：0 币 + 道具各 1）。老档值不被覆盖，
        // 由 BlockOutSaveService.CreateNew 从 GameplayConfig.newProfile 读取后写入。
        public const int InitialCoins = 0;
        public const int InitialHintCount = 1;
        public const int InitialHammerCount = 1;
        public const int InitialMagicCount = 1;

        // 道具解锁关卡（全局关号，ArtOut ToolUnlockConfig 基线 2/3/4）
        // 说明：这几项 + MagicTargetCount / AdSimulatedLoadSeconds 由 const 改为 static 可变字段，
        // 以便 BlockOutRemoteConfigBridge 与 GameplayConfig 覆盖（键名见该桥接类，属外部契约）。
        // 读取方无需改动；默认值常量保留为 Default*，便于测试断言与回退比对。
        public const int DefaultHintUnlockLevel = 2;
        public const int DefaultHammerUnlockLevel = 3;
        public const int DefaultMagicUnlockLevel = 4;
        public const int DefaultMagicTargetCount = 6;
        public const int DefaultToolPackCost = 300;
        public const int DefaultToolPackAmount = 2;
        public const float DefaultAdSimulatedLoadSeconds = 1.2f;

        public static int HintUnlockLevel = DefaultHintUnlockLevel;
        public static int HammerUnlockLevel = DefaultHammerUnlockLevel;
        public static int MagicUnlockLevel = DefaultMagicUnlockLevel;
        public static int MagicTargetCount = DefaultMagicTargetCount;
        // 零库存购买（参考 ToolPackCost=300 / ToolPackAmount=2：300 币 1 包 ×2 个，购买后立即使用）
        public static int ToolPackCost = DefaultToolPackCost;
        public static int ToolPackAmount = DefaultToolPackAmount;
        public static float AdSimulatedLoadSeconds = DefaultAdSimulatedLoadSeconds;

        /// <summary>新挑战默认失败模式（false=生命模式）。与"进行中对局存档模式"分离（P1-3/R13）。</summary>
        public static bool UseTimeFailModeDefault = false;

        // 复活规则（ArtOut ReviveConfig 基线）—— 全部来自 GameplayConfig.revive，启动经 Apply 同步。
        // 改为 static 可变字段：JSON 消费者缺失时仍回退默认值，但"配置支持的值"会真实生效（R02）。
        public static int CoinReviveCost = 300;
        public static int FreeReviveMaxLevel = 10; // 全局 1-10 关免费复活（revive.freeThroughLevel）
        public static int ReviveLifeBonus = 1;     // 金币复活补心数（revive.lifeCount）
        public static int FreeReviveLifeCount = 3;  // 免费复活补满的心数（revive.freeLifeCount）
        public static float ReviveTimeBonusSeconds = 20f; // 倒计时复活加时（revive.addTimeSeconds）
        public static int ReviveLimitPerRun = 0;    // 每局复活上限（0=不限制，revive.limitPerRun）

        // 规则值（ArtOut rules 基线）—— 来自 GameplayConfig.rules，启动经 Apply 同步（R02）。
        public static int MaxLives = 3;            // rules.maxLives
        public static float GameTimeSeconds = 30f; // 无关卡自带时长时的兜底（rules.gameTimeSeconds）
        public static bool EnableCombo = false;     // rules.enableCombo
        public static bool EnableSpecialBlocks = false; // rules.enableSpecialBlocks

        public const float HintHighlightSeconds = 1.5f; // 提示演出总时长（闪 2×0.2s×2 + 聚焦 0.7s，阶段D按配置拆分）
        public const float FlyOutSeconds = 0.36f;      // 旧 cubic-out 飞出时长（阶段D替换为加速模型）
        public const float WrongFeedbackSeconds = 0.28f; // 旧误点反馈时长（阶段D替换为 clamp 公式）

        /// <summary>章节主题名（第一章 = 甜点星球；新章节发布时在此追加）。</summary>
        public static readonly string[] ChapterThemeNames = { "像素画廊" };

        public static string ChapterThemeName(int chapterIndex)
        {
            if (chapterIndex >= 0 && chapterIndex < ChapterThemeNames.Length)
                return ChapterThemeNames[chapterIndex];
            return "像素画廊";
        }

        public static bool IsChapterPublished(int chapterIndex)
        {
            return chapterIndex >= 0 && chapterIndex < PublishedChapters;
        }

        /// <summary>
        /// 把已加载的 <see cref="BlockOutGameplayConfig"/> 同步到本桥。
        /// 启动序列在 GameplayConfig 步骤调用；ContentCatalog 步骤的
        /// <see cref="BlockOutRemoteConfigBridge.ApplyLocalDefaults"/> 也改为经此同步，
        /// 不会再把 JSON 覆盖回旧常量。
        /// </summary>
        public static void Apply(BlockOutGameplayConfig cfg)
        {
            if (cfg == null) return;
            HintUnlockLevel = cfg.tools.hintUnlockLevel;
            HammerUnlockLevel = cfg.tools.hammerUnlockLevel;
            MagicUnlockLevel = cfg.tools.magicUnlockLevel;
            MagicTargetCount = cfg.tools.magicTargetCount;
            ToolPackCost = cfg.tools.toolPackCost;
            ToolPackAmount = cfg.tools.toolPackAmount;
            UseTimeFailModeDefault = cfg.rules.useTimeFailMode;
            // R02：补齐规则/复活配置 → 业务链路，避免"JSON 一套、常量一套"导致配置静默失效。
            MaxLives = cfg.rules.maxLives;
            GameTimeSeconds = cfg.rules.gameTimeSeconds;
            EnableCombo = cfg.rules.enableCombo;
            EnableSpecialBlocks = cfg.rules.enableSpecialBlocks;
            if (cfg.revive != null)
            {
                CoinReviveCost = cfg.revive.coinCost;
                FreeReviveMaxLevel = cfg.revive.freeThroughLevel;
                ReviveLifeBonus = cfg.revive.lifeCount;
                FreeReviveLifeCount = cfg.revive.freeLifeCount;
                ReviveTimeBonusSeconds = cfg.revive.addTimeSeconds;
                ReviveLimitPerRun = cfg.revive.limitPerRun;
            }
        }

        /// <summary>关卡自带奖励值优先（沿用现有值），否则按难度档取奖励表（expert/insane 映射第四档）。</summary>
        /// <summary>
        /// 通关奖励取值（语义对齐 ArtOut <c>ArtOutWinRewardConfig.GetRewardCoins</c>）：
        /// 可配置奖励表按难度取值优先（easy/normal/hard/extreme，expert/insane 并入 extreme 档）；
        /// 仅当奖励表不可用（取不到正值）时，才回退到关卡自带 <paramref name="levelDefinedReward"/>。
        /// 参考实现中关卡 JSON 的 rewardCoins 只是远端奖励配置解析失败时的兜底，不参与正常发奖。
        /// </summary>
        public static int GetLevelReward(string difficulty, int levelDefinedReward)
        {
            int tableReward = BlockOutGameplayConfig.Current.GetReward(difficulty);
            // R02：0 是合法的禁发奖励值，不得错误回退到关卡自带奖励；
            // 奖励表恒定可用（GetReward 始终返回 >=0），表值即权威来源。
            return Mathf.Max(0, tableReward);
        }
    }
}
