using System;
using BlockOut.Core;
using UnityEngine;

namespace BlockOut.Infrastructure.Persistence
{
    /// <summary>
    /// 档案事务（R13）。用法：
    /// <code>
    /// using (var tx = save.BeginTransaction()) {
    ///     save.Profile.SpendCoins(300);
    ///     if (!tx.Commit()) { /* 已自动回滚，UI 提示失败 */ }
    /// }
    /// </code>
    /// 回滚通过 JSON 快照还原内存档案，并把存储缓存恢复到事务前原文，
    /// 保证金币/道具/拼片/进度/对局状态一致，不会只回滚一半（C05）。
    /// </summary>
    public sealed class BlockOutProfileTransaction : IDisposable
    {
        private readonly BlockOutSaveService service;
        private readonly BlockOutPlayerProfile snapshot;
        private readonly string previousRaw;
        private bool finished;

        internal BlockOutProfileTransaction(BlockOutSaveService service)
        {
            this.service = service;
            this.snapshot = service.Profile != null
                ? JsonUtility.FromJson<BlockOutPlayerProfile>(JsonUtility.ToJson(service.Profile))
                : null;
            // 事务开始时的存储原文：提交失败时恢复缓存，避免失败后残留脏值被下次保存写出。
            this.previousRaw = service.PeekStored();
        }

        /// <summary>提交。保存失败时自动回滚（内存 + 存储缓存）并返回 false。</summary>
        public bool Commit()
        {
            if (finished) return false;
            if (service.Save())
            {
                finished = true;   // 只有保存成功才闭合事务
                return true;
            }
            RestoreSnapshot();     // 失败：真实恢复快照，再闭合
            finished = true;
            return false;
        }

        /// <summary>显式回滚到事务开始时的档案快照（不写盘，仅恢复存储缓存）。</summary>
        public void Rollback()
        {
            if (finished) return;
            RestoreSnapshot();
            finished = true;
        }

        /// <summary>内存档案还原为快照；存储缓存还原为事务前原文。</summary>
        private void RestoreSnapshot()
        {
            if (snapshot != null && service.Profile != null)
            {
                JsonUtility.FromJsonOverwrite(JsonUtility.ToJson(snapshot), service.Profile);
            }
            service.RestoreStored(previousRaw);
        }

        public void Dispose()
        {
            if (!finished) Rollback();   // 未提交即释放 = 放弃本次修改
        }
    }
}
