using System;
using UnityEngine;

namespace BlockOut.Config
{
    /// <summary>
    /// 本地玩法配置（ArtOut 对齐基线）。唯一数据来源：
    /// <see cref="Assets/Resources/BlockOut/GameplayConfig.json"/>。
    /// 结构对应 Docs/ArtOut玩法与手感对齐实施说明 §6 契约；
    /// JsonUtility 可序列化（不用 Dictionary），缺字段保留默认值，
    /// 缺失/非法/版本不支持时整体回退到 <see cref="Default"/>，禁止部分应用。
    /// </summary>
    [Serializable]
    public sealed class BlockOutGameplayConfig
    {
        public const int SupportedSchemaVersion = 1;

        public int schemaVersion;
        public string preset;
        public GameplayRulesConfig rules;
        public NewProfileConfig newProfile;
        public ToolsConfig tools;
        public ReviveConfig revive;
        public RewardsConfig rewards;
        public GameplayFeelConfig feel;

        /// <summary>启动时加载并生效的配置（null = 未加载，消费方回退 <see cref="Default"/>）。</summary>
        public static BlockOutGameplayConfig Active;

        /// <summary>完整 ArtOut 默认配置（与 GameplayConfig.json 基线一致）。</summary>
        public static BlockOutGameplayConfig Default()
        {
            return new BlockOutGameplayConfig
            {
                schemaVersion = SupportedSchemaVersion,
                preset = "artout_local",
                rules = new GameplayRulesConfig
                {
                    maxLives = 3,
                    useTimeFailMode = false,
                    gameTimeSeconds = 30f,
                    warningThresholdSeconds = 10f,
                    enableCombo = false,
                    enableSpecialBlocks = false,
                },
                newProfile = new NewProfileConfig { coins = 0, hintCount = 1, hammerCount = 1, magicCount = 1 },
                tools = new ToolsConfig
                {
                    hintUnlockLevel = 2,
                    hammerUnlockLevel = 3,
                    magicUnlockLevel = 4,
                    magicTargetCount = 6,
                    toolPackCost = 300,
                    toolPackAmount = 2,
                },
                revive = new ReviveConfig
                {
                    freeThroughLevel = 10,
                    freeLifeCount = 3,
                    lifeCount = 1,
                    coinCost = 300,
                    addTimeSeconds = 20f,
                    limitPerRun = 0,
                },
                rewards = new RewardsConfig { easy = 10, normal = 20, hard = 30, extreme = 40 },
                feel = GameplayFeelConfig.Default(),
            };
        }

        /// <summary>当前生效配置（未加载时给默认值，绝不返回 null）。</summary>
        public static BlockOutGameplayConfig Current { get { return Active ?? Default(); } }

        /// <summary>按难度档取通关奖励；expert/insane 映射第四档（extreme）。</summary>
        public int GetReward(string difficulty)
        {
            switch (difficulty)
            {
                case "easy": return rewards.easy;
                case "normal": return rewards.normal;
                case "hard": return rewards.hard;
                case "extreme": return rewards.extreme;
                case "expert":
                case "insane": return rewards.extreme;
                default: return rewards.normal;
            }
        }

        /// <summary>
        /// 校验有限数值、正数时长、解锁级别与计数范围。
        /// 返回 null 表示通过；否则返回带路径与原因的描述（调用方整体回退默认配置）。
        /// </summary>
        public string Validate()
        {
            if (schemaVersion != SupportedSchemaVersion)
                return "schemaVersion=" + schemaVersion + " 不支持（仅支持 " + SupportedSchemaVersion + "）";

            if (rules == null) return "rules 缺失";
            if (rules.maxLives < 1 || rules.maxLives > 9) return "rules.maxLives=" + rules.maxLives + " 必须在 1..9";
            if (!IsFinite(rules.gameTimeSeconds) || rules.gameTimeSeconds <= 0f) return "rules.gameTimeSeconds=" + rules.gameTimeSeconds + " 必须为正数";
            if (rules.gameTimeSeconds > 600f) return "rules.gameTimeSeconds=" + rules.gameTimeSeconds + " 超过上限 600";
            if (!IsFinite(rules.warningThresholdSeconds) || rules.warningThresholdSeconds < 0f) return "rules.warningThresholdSeconds=" + rules.warningThresholdSeconds + " 必须为非负";
            if (rules.warningThresholdSeconds >= rules.gameTimeSeconds) return "rules.warningThresholdSeconds=" + rules.warningThresholdSeconds + " 必须小于 gameTimeSeconds";

            if (newProfile == null) return "newProfile 缺失";
            if (newProfile.coins < 0) return "newProfile.coins=" + newProfile.coins + " 必须为非负";
            if (newProfile.hintCount < 0) return "newProfile.hintCount=" + newProfile.hintCount + " 必须为非负";
            if (newProfile.hammerCount < 0) return "newProfile.hammerCount=" + newProfile.hammerCount + " 必须为非负";
            if (newProfile.magicCount < 0) return "newProfile.magicCount=" + newProfile.magicCount + " 必须为非负";

            if (tools == null) return "tools 缺失";
            if (tools.hintUnlockLevel < 1) return "tools.hintUnlockLevel=" + tools.hintUnlockLevel + " 必须 ≥1";
            if (tools.hammerUnlockLevel < 1) return "tools.hammerUnlockLevel=" + tools.hammerUnlockLevel + " 必须 ≥1";
            if (tools.magicUnlockLevel < 1) return "tools.magicUnlockLevel=" + tools.magicUnlockLevel + " 必须 ≥1";
            if (tools.magicTargetCount < 1 || tools.magicTargetCount > 6) return "tools.magicTargetCount=" + tools.magicTargetCount + " 必须在 1..6";
            if (tools.toolPackCost < 0) return "tools.toolPackCost=" + tools.toolPackCost + " 必须为非负";
            if (tools.toolPackAmount < 1) return "tools.toolPackAmount=" + tools.toolPackAmount + " 必须 ≥1";

            if (revive == null) return "revive 缺失";
            if (revive.freeThroughLevel < 0) return "revive.freeThroughLevel=" + revive.freeThroughLevel + " 必须为非负";
            if (revive.freeLifeCount < 1) return "revive.freeLifeCount=" + revive.freeLifeCount + " 必须 ≥1";
            if (revive.lifeCount < 1) return "revive.lifeCount=" + revive.lifeCount + " 必须 ≥1";
            if (revive.coinCost < 0) return "revive.coinCost=" + revive.coinCost + " 必须为非负";
            if (!IsFinite(revive.addTimeSeconds) || revive.addTimeSeconds < 0f) return "revive.addTimeSeconds=" + revive.addTimeSeconds + " 必须为非负";
            if (revive.limitPerRun < 0) return "revive.limitPerRun=" + revive.limitPerRun + " 必须为非负（0 = 不限制）";

            if (rewards == null) return "rewards 缺失";
            if (rewards.easy < 0) return "rewards.easy=" + rewards.easy + " 必须为非负";
            if (rewards.normal < 0) return "rewards.normal=" + rewards.normal + " 必须为非负";
            if (rewards.hard < 0) return "rewards.hard=" + rewards.hard + " 必须为非负";
            if (rewards.extreme < 0) return "rewards.extreme=" + rewards.extreme + " 必须为非负";

            if (feel == null) return "feel 缺失";
            var feelError = feel.Validate();
            if (feelError != null) return "feel." + feelError;
            return null;
        }

        private static bool IsFinite(float v) { return !float.IsNaN(v) && !float.IsInfinity(v); }
    }

    [Serializable]
    public sealed class GameplayRulesConfig
    {
        public int maxLives;
        public bool useTimeFailMode;
        public float gameTimeSeconds;
        public float warningThresholdSeconds;
        public bool enableCombo;
        public bool enableSpecialBlocks;
    }

    [Serializable]
    public sealed class NewProfileConfig
    {
        public int coins;
        public int hintCount;
        public int hammerCount;
        public int magicCount;
    }

    [Serializable]
    public sealed class ToolsConfig
    {
        public int hintUnlockLevel;
        public int hammerUnlockLevel;
        public int magicUnlockLevel;
        public int magicTargetCount;
        // 零库存购买（参考 ToolPackCost/ToolPackAmount：300 币 = 1 包 ×2 个，购买后立即使用）
        public int toolPackCost;
        public int toolPackAmount;
    }

    [Serializable]
    public sealed class ReviveConfig
    {
        public int freeThroughLevel;
        public int freeLifeCount;
        public int lifeCount;
        public int coinCost;
        public float addTimeSeconds;
        public int limitPerRun;
    }

    [Serializable]
    public sealed class RewardsConfig
    {
        public int easy;
        public int normal;
        public int hard;
        public int extreme;
    }

    [Serializable]
    public sealed class GameplayFeelConfig
    {
        public float referenceCameraHalfHeight;
        public float exitInitialSpeed;
        public float exitAcceleration;
        public float exitMaxSpeed;
        public float boardEntranceSeconds;
        public float boardEntranceStartScale;
        public float boardEntranceInputDelay;
        public float wrongTravelBaseSeconds;
        public float wrongTravelPerSqrtCell;
        public float wrongTravelMinSeconds;
        public float wrongTravelMaxSeconds;
        public float wrongImpactSeconds;
        public float wrongReturnBaseSeconds;
        public float wrongReturnPerSqrtCell;
        public float wrongReturnMinSeconds;
        public float wrongReturnMaxSeconds;
        public float wrongArrowFlashSeconds;
        public int wrongArrowFlashCount;
        public float hintFlashStepSeconds;
        public int hintFlashLoops;
        public float hintFocusSeconds;
        public float magicStarPathSeconds;
        public float magicHitScale;
        public float magicHitScaleSeconds;
        public float magicStarStaggerSeconds;
        public float hammerImpactSoundDelay;
        public float failPopupDelaySeconds;
        public float gestureTapSuppressSeconds;

        public static GameplayFeelConfig Default()
        {
            return new GameplayFeelConfig
            {
                referenceCameraHalfHeight = 5f,
                exitInitialSpeed = 6.24f,
                exitAcceleration = 15f,
                exitMaxSpeed = 13f,
                boardEntranceSeconds = 0.9f,
                boardEntranceStartScale = 0.68f,
                boardEntranceInputDelay = 1.02f,
                wrongTravelBaseSeconds = 0.08f,
                wrongTravelPerSqrtCell = 0.06f,
                wrongTravelMinSeconds = 0.12f,
                wrongTravelMaxSeconds = 0.24f,
                wrongImpactSeconds = 0.05f,
                wrongReturnBaseSeconds = 0.12f,
                wrongReturnPerSqrtCell = 0.04f,
                wrongReturnMinSeconds = 0.16f,
                wrongReturnMaxSeconds = 0.28f,
                wrongArrowFlashSeconds = 0.04f,
                wrongArrowFlashCount = 3,
                hintFlashStepSeconds = 0.2f,
                hintFlashLoops = 2,
                hintFocusSeconds = 0.7f,
                magicStarPathSeconds = 1f,
                magicHitScale = 1.15f,
                magicHitScaleSeconds = 0.12f,
                magicStarStaggerSeconds = 0f,
                hammerImpactSoundDelay = 0.35f,
                failPopupDelaySeconds = 0.58f,
                gestureTapSuppressSeconds = 0.16f,
            };
        }

        public string Validate()
        {
            if (!Positive(referenceCameraHalfHeight)) return "referenceCameraHalfHeight=" + referenceCameraHalfHeight + " 必须为正数";
            if (!Positive(exitInitialSpeed)) return "exitInitialSpeed=" + exitInitialSpeed + " 必须为正数";
            if (!Positive(exitAcceleration)) return "exitAcceleration=" + exitAcceleration + " 必须为正数";
            if (!Positive(exitMaxSpeed)) return "exitMaxSpeed=" + exitMaxSpeed + " 必须为正数";
            if (!Positive(boardEntranceSeconds)) return "boardEntranceSeconds=" + boardEntranceSeconds + " 必须为正数";
            if (!InRange(boardEntranceStartScale, 0.01f, 2f)) return "boardEntranceStartScale=" + boardEntranceStartScale + " 必须在 0.01..2";
            if (!NonNegative(boardEntranceInputDelay)) return "boardEntranceInputDelay=" + boardEntranceInputDelay + " 必须为非负";
            if (!NonNegative(wrongTravelBaseSeconds)) return "wrongTravelBaseSeconds=" + wrongTravelBaseSeconds + " 必须为非负";
            if (!NonNegative(wrongTravelPerSqrtCell)) return "wrongTravelPerSqrtCell=" + wrongTravelPerSqrtCell + " 必须为非负";
            if (!Positive(wrongTravelMinSeconds)) return "wrongTravelMinSeconds=" + wrongTravelMinSeconds + " 必须为正数";
            if (!Positive(wrongTravelMaxSeconds)) return "wrongTravelMaxSeconds=" + wrongTravelMaxSeconds + " 必须为正数";
            if (wrongTravelMaxSeconds < wrongTravelMinSeconds) return "wrongTravelMaxSeconds < wrongTravelMinSeconds";
            if (!NonNegative(wrongImpactSeconds)) return "wrongImpactSeconds=" + wrongImpactSeconds + " 必须为非负";
            if (!NonNegative(wrongReturnBaseSeconds)) return "wrongReturnBaseSeconds=" + wrongReturnBaseSeconds + " 必须为非负";
            if (!NonNegative(wrongReturnPerSqrtCell)) return "wrongReturnPerSqrtCell=" + wrongReturnPerSqrtCell + " 必须为非负";
            if (!Positive(wrongReturnMinSeconds)) return "wrongReturnMinSeconds=" + wrongReturnMinSeconds + " 必须为正数";
            if (!Positive(wrongReturnMaxSeconds)) return "wrongReturnMaxSeconds=" + wrongReturnMaxSeconds + " 必须为正数";
            if (wrongReturnMaxSeconds < wrongReturnMinSeconds) return "wrongReturnMaxSeconds < wrongReturnMinSeconds";
            if (!Positive(wrongArrowFlashSeconds)) return "wrongArrowFlashSeconds=" + wrongArrowFlashSeconds + " 必须为正数";
            if (wrongArrowFlashCount < 1) return "wrongArrowFlashCount=" + wrongArrowFlashCount + " 必须 ≥1";
            if (!Positive(hintFlashStepSeconds)) return "hintFlashStepSeconds=" + hintFlashStepSeconds + " 必须为正数";
            if (hintFlashLoops < 1) return "hintFlashLoops=" + hintFlashLoops + " 必须 ≥1";
            if (!NonNegative(hintFocusSeconds)) return "hintFocusSeconds=" + hintFocusSeconds + " 必须为非负";
            if (!Positive(magicStarPathSeconds)) return "magicStarPathSeconds=" + magicStarPathSeconds + " 必须为正数";
            if (!InRange(magicHitScale, 1f, 3f)) return "magicHitScale=" + magicHitScale + " 必须在 1..3";
            if (!Positive(magicHitScaleSeconds)) return "magicHitScaleSeconds=" + magicHitScaleSeconds + " 必须为正数";
            if (!NonNegative(magicStarStaggerSeconds)) return "magicStarStaggerSeconds=" + magicStarStaggerSeconds + " 必须为非负";
            if (!NonNegative(hammerImpactSoundDelay)) return "hammerImpactSoundDelay=" + hammerImpactSoundDelay + " 必须为非负";
            if (!NonNegative(failPopupDelaySeconds)) return "failPopupDelaySeconds=" + failPopupDelaySeconds + " 必须为非负";
            if (!NonNegative(gestureTapSuppressSeconds)) return "gestureTapSuppressSeconds=" + gestureTapSuppressSeconds + " 必须为非负";
            return null;
        }

        private static bool Positive(float v) { return !float.IsNaN(v) && !float.IsInfinity(v) && v > 0f; }
        private static bool NonNegative(float v) { return !float.IsNaN(v) && !float.IsInfinity(v) && v >= 0f; }
        private static bool InRange(float v, float lo, float hi) { return NonNegative(v) && v >= lo && v <= hi; }
    }
}
