using System;
using BlockOut.Contracts;
using BlockOut.Core;
using UnityEngine;

namespace BlockOut.Infrastructure.Analytics
{
    /// <summary>
    /// 统计服务默认实现（R15）。当前未安装任何统计 SDK，
    /// 因此本实现只做本地聚合与日志（开发档可见），不产生任何网络请求。
    /// 接入 SDK 时新增适配器实现 <see cref="IAnalyticsService"/>，由 Bootstrap 注入，业务代码不变。
    /// </summary>
    public sealed class BlockOutAnalyticsService : IAnalyticsService
    {
        private readonly bool verbose;
        private readonly System.Collections.Generic.Queue<AnalyticsEvent> pending =
            new System.Collections.Generic.Queue<AnalyticsEvent>();

        public bool IsEnabled => true;
        public int PendingCount => pending.Count;

        public BlockOutAnalyticsService(bool verbose)
        {
            this.verbose = verbose;
        }

        public void Track(AnalyticsEvent evt)
        {
            if (evt == null) return;
            pending.Enqueue(evt);
            if (pending.Count > 200) pending.Dequeue();   // 防无限增长
            if (verbose)
            {
                var sb = new System.Text.StringBuilder();
                sb.Append("[BlockOut][Analytics] ").Append(evt.Name);
                foreach (var kv in evt.Parameters) sb.Append(' ').Append(kv.Key).Append('=').Append(kv.Value);
                Debug.Log(sb.ToString());
            }
        }

        public void Track(string eventName)
        {
            Track(new AnalyticsEvent(eventName));
        }

        public void SetUserId(string userId)
        {
            // 无 SDK 时仅记录；接入后转给 SDK 的 setUserId。
            if (verbose) Debug.Log("[BlockOut][Analytics] setUserId (no sdk): " + (userId ?? "<null>"));
        }

        public void Flush()
        {
            pending.Clear();
        }
    }
}
