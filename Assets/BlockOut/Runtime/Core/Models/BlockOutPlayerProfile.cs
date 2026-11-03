using System;
using System.Collections.Generic;
using UnityEngine;

namespace BlockOut.Core
{
    /// <summary>
    /// 玩家档案（PlayerPrefs JSON）。金币/道具库存/通关集合/设置/局内存档。
    /// 存档键 v2：新增 MaxLevelReached（道具解锁按实际到达进度判断，回玩低关不误判为重新锁定）。
    /// v1 旧档自动迁移。
    /// </summary>
    [Serializable]
    public class BlockOutPlayerProfile
    {
        public int CurrentLevelIndex;
        public List<string> CompletedLevelIds = new List<string>();
        public int Coins = 300;
        public int HintCount = 3;
        public int HammerCount = 1;
        public int MagicCount = 0;
        public bool MusicOn = true;
        public bool SoundOn = true;
        public bool VibrationOn = true;
        public bool GuideCompleted;
        public int BestCombo;

        // 实际到达的最大全局关号（道具解锁判断依据）
        public int MaxLevelReached = 1;

        // Run-in-progress (mid-level save)
        public bool HasActiveRun;
        public string RunLevelId;
        public string RunLevelHash;
        public int RunBlockCount;
        public int RunLives;
        public int[] RunRemoved = new int[0];
        public int[] RunWrong = new int[0];
        public float RunTimeRemaining;

        /// <summary>本局失败模式：0=生命模式（默认，兼容旧存档），1=倒计时模式（P1-3）。
        /// 旧存档没有此字段时 JsonUtility 会给默认值 0，即按生命模式恢复，行为不变。</summary>
        public int RunFailMode;
        /// <summary>本局是否已处于失败态（含倒计时归零）。恢复时据此回到失败层，而不是可操作状态（P1-3）。</summary>
        public bool RunLost;
        /// <summary>失败原因文案（"生命耗尽"/"时间用尽"），恢复失败局时原样展示。</summary>
        public string RunFailReason;
        /// <summary>本局是否记录了倒计时数据。区分"剩余 0 秒"与"没有时间记录"（P1-3）：
        /// 0 秒是有效存档（已失败），不能当作无记录而重新给满时间。</summary>
        public bool RunHasTimeRecord;

        // 本局是否已使用过复活（恢复进行中局时还原；重开/放弃/通关后由 ClearActiveRun 重置）
        public bool RunReviveUsed;
        public int RunReviveCount;
        public int[] RunPendingMagicTargets=new int[0];

        private const string SaveKeyV2 = "BlockOut_PlayerProfile_v2";
        private const string SaveKeyV1 = "BlockOut_PlayerProfile_v1";

        public static BlockOutPlayerProfile Load()
        {
            try
            {
                if (PlayerPrefs.HasKey(SaveKeyV2))
                {
                    var json = PlayerPrefs.GetString(SaveKeyV2);
                    var p = JsonUtility.FromJson<BlockOutPlayerProfile>(json);
                    if (p != null) return p;
                }
                if (PlayerPrefs.HasKey(SaveKeyV1))
                {
                    // v1 → v2 迁移
                    var json = PlayerPrefs.GetString(SaveKeyV1);
                    var p = JsonUtility.FromJson<BlockOutPlayerProfile>(json);
                    if (p != null)
                    {
                        p.MaxLevelReached = Mathf.Max(1, p.CurrentLevelIndex + 1);
                        p.Save();
                        return p;
                    }
                }
            }
            catch (Exception e) { Debug.LogWarning("[BlockOut] Load profile failed: " + e.Message); }
            return new BlockOutPlayerProfile();
        }

        public void Save() { TrySave(); }

        /// <summary>购买事务需要知道是否真正写入成功，失败时由调用者回滚内存余额与库存。</summary>
        public bool TrySave()
        {
            try
            {
                var json = JsonUtility.ToJson(this);
                PlayerPrefs.SetString(SaveKeyV2, json);
                PlayerPrefs.Save();
                return true;
            }
            catch (Exception e) { Debug.LogWarning("[BlockOut] Save profile failed: " + e.Message); return false; }
        }

        public bool IsLevelCompleted(string id)
        {
            if(string.IsNullOrEmpty(id))return false;
            if(CompletedLevelIds.Contains(id))return true;
            return (id=="20260730_tutorial_Level1_easy" && CompletedLevelIds.Contains("blockout_tutorial_01"))
                || (id=="20260730_tutorial_Level2_easy" && CompletedLevelIds.Contains("blockout_tutorial_02"));
        }

        public void MarkLevelCompleted(string id)
        {
            if (string.IsNullOrEmpty(id)) return;
            if (!CompletedLevelIds.Contains(id)) CompletedLevelIds.Add(id);
            HasActiveRun = false;
        }

        public void AddCoins(int amount)
        {
            Coins = Mathf.Max(0, Coins + amount);
        }

        public bool SpendCoins(int amount)
        {
            if (Coins < amount) return false;
            Coins -= amount;
            return true;
        }

        /// <summary>增加道具库存（tool: 0=提示 1=锤子 2=魔法棒；与 BlockOutToolId 顺序一致）。</summary>
        public void AddToolCount(int tool, int n)
        {
            if (tool == 0) HintCount += n;
            else if (tool == 1) HammerCount += n;
            else if (tool == 2) MagicCount += n;
        }

        public void ClearActiveRun()
        {
            HasActiveRun = false;
            RunLevelId = null;
            RunReviveUsed = false;
            RunReviveCount = 0;
            RunPendingMagicTargets=new int[0];
            // 一并清掉失败态与倒计时记录：避免旧残留被下一次误读（P1-3）
            RunLost = false;
            RunFailReason = null;
            RunHasTimeRecord = false;
            RunTimeRemaining = 0f;
            RunFailMode = 0;
        }
    }
}
