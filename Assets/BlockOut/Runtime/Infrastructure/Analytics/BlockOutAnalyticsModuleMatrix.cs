using System;
using System.Collections.Generic;
using BlockOut.Contracts;
using UnityEngine;

namespace BlockOut.Infrastructure.Analytics
{
    /// <summary>统计/归因模块矩阵条目（R15）。</summary>
    public sealed class AnalyticsModuleInfo
    {
        public string Name;
        public bool Required;       // 项目是否确需
        public bool Installed;      // SDK 程序集是否已在工程内
        public bool Initialized;    // 启动期是否成功初始化
        public bool Configured;     // App ID / Token 是否已配置
        public bool Verified;       // 是否真机验证过事件上报
        public string Note;

        public AnalyticsModuleInfo(string name, bool required, string note)
        {
            Name = name; Required = required; Note = note;
        }

        public string Status =>
            !Required ? "不需要" :
            !Installed ? "未安装" :
            !Configured ? "缺配置" :
            !Initialized ? "未初始化" :
            !Verified ? "初始化成功，待真机验证" : "已验证";
    }

    /// <summary>
    /// 统计/归因模块矩阵（R15）。**不批量搬入**参考工程的 SDK：
    /// 只有"项目确需 + 已有有效配置"的模块才会被启用；当前全部为未安装状态，
    /// 因此运行时使用 <see cref="NullAnalyticsService"/> / 本地聚合实现降级。
    /// </summary>
    public static class BlockOutAnalyticsModuleMatrix
    {
        public static readonly AnalyticsModuleInfo[] Modules = new[]
        {
            new AnalyticsModuleInfo("Firebase Analytics", false, "无既定需求与配置，不启用；不复制参考工程 App ID"),
            new AnalyticsModuleInfo("Adjust", false, "归因需求未定，不启用"),
            new AnalyticsModuleInfo("Facebook SDK", false, "无社交/归因需求，不启用"),
            new AnalyticsModuleInfo("ThinkingData", false, "无配置，不启用"),
            new AnalyticsModuleInfo("LevelPlay（广告）", true, "激励复活唯一入口；适配器已写，SDK 包与凭据待补（见 BlockOutAdConfig）"),
            new AnalyticsModuleInfo("本地语义事件（BlockOutAnalyticsService）", true, "已实现：仅本地聚合 + 开发档日志，无网络请求"),
        };

        /// <summary>是否有任何模块需要但未就绪（供发布检查与文档汇总）。</summary>
        public static List<string> CollectGaps()
        {
            var gaps = new List<string>();
            foreach (var m in Modules)
            {
                if (!m.Required) continue;
                if (!m.Installed || !m.Configured || !m.Initialized || !m.Verified)
                    gaps.Add(m.Name + "：" + m.Status);
            }
            return gaps;
        }

        public static void LogMatrix()
        {
            var sb = new System.Text.StringBuilder();
            sb.AppendLine("[BlockOut][Analytics] 模块矩阵：");
            foreach (var m in Modules)
                sb.Append("  - ").Append(m.Name).Append(" | 需要=").Append(m.Required)
                  .Append(" | 状态=").Append(m.Status).Append(" | ").Append(m.Note).AppendLine();
            Debug.Log(sb.ToString());
        }
    }
}
