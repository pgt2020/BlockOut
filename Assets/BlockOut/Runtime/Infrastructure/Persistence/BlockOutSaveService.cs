using System;
using BlockOut.Config;
using BlockOut.Contracts;
using BlockOut.Core;
using UnityEngine;

namespace BlockOut.Infrastructure.Persistence
{
    /// <summary>
    /// 集中存档服务（R13）。职责：
    /// 1. 唯一读写入口（UI/Gameplay 不再各自调 Profile.Save）；
    /// 2. 版本迁移（v1 → v2，键名保持不变，旧档不丢）；
    /// 3. 失败可感知：Save 返回 bool，业务据此回滚；
    /// 4. 事务：<see cref="BlockOutProfileTransaction"/> 提供快照 + 失败回滚。
    ///
    /// 存档键与字段名属外部契约，**不得随重构改名**（R23）：`BlockOut_PlayerProfile_v1/v2`。
    /// </summary>
    public sealed class BlockOutSaveService
    {
        /// <summary>当前档案结构版本（键名后缀）。升级必须新增键，不覆写旧键语义。</summary>
        public const int SchemaVersion = 2;
        public const string SaveKeyV2 = "BlockOut_PlayerProfile_v2";
        public const string SaveKeyV1 = "BlockOut_PlayerProfile_v1";

        private readonly IProfileStore store;

        public BlockOutPlayerProfile Profile { get; private set; }

        /// <summary>最近一次保存失败信息（null 表示上次保存成功）。UI 可据此提示"存档失败"。</summary>
        public string LastSaveError { get; private set; }

        public event Action OnSaveFailed;

        public BlockOutSaveService() : this(new PlayerPrefsProfileStore()) { }

        public BlockOutSaveService(IProfileStore store)
        {
            this.store = store ?? new PlayerPrefsProfileStore();
        }

        /// <summary>加载并迁移。任何异常都退回到全新档案，绝不抛出到启动链之外。</summary>
        public BlockOutPlayerProfile Load()
        {
            Profile = LoadInternal();
            return Profile;
        }

        private BlockOutPlayerProfile LoadInternal()
        {
            try
            {
                if (store.Has(SaveKeyV2))
                {
                    var p = JsonUtility.FromJson<BlockOutPlayerProfile>(store.Get(SaveKeyV2));
                    if (p != null) { Normalize(p); return p; }
                }
                if (store.Has(SaveKeyV1))
                {
                    var p = JsonUtility.FromJson<BlockOutPlayerProfile>(store.Get(SaveKeyV1));
                    if (p != null)
                    {
                        // v1 → v2 迁移：补齐 MaxLevelReached（旧档没有该字段）
                        p.MaxLevelReached = Mathf.Max(1, p.CurrentLevelIndex + 1);
                        Normalize(p);
                        WriteThrough(p);      // 迁移结果立即落盘，旧键保留不删（可回退）
                        return p;
                    }
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("[BlockOut] Load profile failed: " + e.Message);
            }
            return CreateNew();
        }

        /// <summary>
        /// 新档案默认值。来源为生效的 <see cref="BlockOutGameplayConfig.newProfile"/>
        /// （ArtOut 基线：0 币 + 道具各 1）；未加载配置时用同一基线常量。
        /// 老档由 Load 原样读取，本方法只影响"没有存档"的新档，不覆盖用户资产。
        /// </summary>
        public static BlockOutPlayerProfile CreateNew()
        {
            return CreateNew(BlockOutGameplayConfig.Current);
        }

        /// <summary>按指定配置创建新档案（测试与启动链显式注入用）。</summary>
        public static BlockOutPlayerProfile CreateNew(BlockOutGameplayConfig config)
        {
            var cfg = config != null ? config : BlockOutGameplayConfig.Default();
            var np = cfg.newProfile;
            return new BlockOutPlayerProfile
            {
                CurrentLevelIndex = 0,
                CompletedLevelIds = new System.Collections.Generic.List<string>(),
                Coins = np != null ? np.coins : 0,
                HintCount = np != null ? np.hintCount : 1,
                HammerCount = np != null ? np.hammerCount : 1,
                MagicCount = np != null ? np.magicCount : 1,
                MaxLevelReached = 1,
            };
        }

        /// <summary>字段级兜底：旧档缺字段时给安全默认值，避免 null/负值进入业务。</summary>
        private static void Normalize(BlockOutPlayerProfile p)
        {
            if (p.CompletedLevelIds == null) p.CompletedLevelIds = new System.Collections.Generic.List<string>();
            if (p.Coins < 0) p.Coins = 0;
            if (p.HintCount < 0) p.HintCount = 0;
            if (p.HammerCount < 0) p.HammerCount = 0;
            if (p.MagicCount < 0) p.MagicCount = 0;
            p.MaxLevelReached = Mathf.Max(1, p.MaxLevelReached);
            if (p.RunRemoved == null) p.RunRemoved = new int[0];
            if (p.RunWrong == null) p.RunWrong = new int[0];
        }

        public bool Save()
        {
            if (Profile == null) return false;
            return WriteThrough(Profile);
        }

        /// <summary>兼容旧调用点语义：保存失败不抛异常，返回 false 由调用方回滚。</summary>
        public bool TrySave() { return Save(); }

        private bool WriteThrough(BlockOutPlayerProfile p)
        {
            try
            {
                store.Set(SaveKeyV2, JsonUtility.ToJson(p));
                if (!store.Commit())
                {
                    LastSaveError = "存储提交失败";
                    OnSaveFailed?.Invoke();
                    return false;
                }
                LastSaveError = null;
                return true;
            }
            catch (Exception e)
            {
                LastSaveError = e.Message;
                Debug.LogWarning("[BlockOut] Save profile failed: " + e.Message);
                OnSaveFailed?.Invoke();
                return false;
            }
        }

        /// <summary>开启事务：先做内存快照，Commit 失败自动回滚（购买/复活/结算统一走这里）。</summary>
        public BlockOutProfileTransaction BeginTransaction()
        {
            return new BlockOutProfileTransaction(this);
        }

        /// <summary>事务回滚用：读取存储中当前原文（无存档返回 null）。不改变任何状态。</summary>
        internal string PeekStored()
        {
            return store.Has(SaveKeyV2) ? store.Get(SaveKeyV2) : null;
        }

        /// <summary>事务回滚用：把存储缓存恢复到事务前原文（null = 删除键），不提交。</summary>
        internal void RestoreStored(string raw)
        {
            if (raw == null) store.Delete(SaveKeyV2);
            else store.Set(SaveKeyV2, raw);
        }
    }
}
