using System;
using System.Collections;
using UnityEngine;

namespace BlockOut.Bootstrap
{
    public enum StartupStepState { Pending, Running, Succeeded, Failed, Skipped, TimedOut }

    /// <summary>单步启动上下文：供步骤读取服务与上报进度。</summary>
    public sealed class StartupStepContext
    {
        public BlockOutServiceRegistry Services;
        public BlockOutStartupSequence Owner;

        /// <summary>上报 0..1 进度。</summary>
        public void ReportProgress(float p)
        {
            if (Owner != null) Owner.CurrentStepProgress = Mathf.Clamp01(p);
        }

        public void Log(string message)
        {
            if (Owner != null && Owner.EnableVerboseLog) Debug.Log("[BlockOut][Startup] " + message);
        }
    }

    /// <summary>
    /// 一个显式启动步骤（R04）。每步有状态、进度、超时与失败策略：
    /// - <see cref="Optional"/> = true 时失败/超时不阻塞启动，仅记录降级原因；
    /// - 必选步骤失败 → 启动失败，由 Launcher 展示重试/退出。
    /// </summary>
    public sealed class BlockOutStartupStep
    {
        public readonly string Id;
        public readonly string DisplayName;
        public readonly bool Optional;
        public readonly float TimeoutSeconds;

        private readonly Func<StartupStepContext, IEnumerator> routine;

        public StartupStepState State { get; internal set; }
        public float Progress { get; internal set; }
        public string Error { get; internal set; }

        public BlockOutStartupStep(string id, string displayName, bool optional, float timeoutSeconds,
            Func<StartupStepContext, IEnumerator> routine)
        {
            Id = id;
            DisplayName = displayName;
            Optional = optional;
            TimeoutSeconds = timeoutSeconds;
            this.routine = routine;
        }

        internal IEnumerator Invoke(StartupStepContext ctx)
        {
            State = StartupStepState.Running;
            Progress = 0f;
            Error = null;
            IEnumerator inner = null;
            try
            {
                inner = routine(ctx);
            }
            catch (Exception e)
            {
                Error = e.Message;
                State = StartupStepState.Failed;
                yield break;
            }
            while (true)
            {
                object current;
                try
                {
                    if (inner == null) break;
                    if (!inner.MoveNext()) break;
                    current = inner.Current;
                }
                catch (Exception e)
                {
                    Error = e.Message;
                    State = StartupStepState.Failed;
                    yield break;
                }
                yield return current;
            }
            if (State == StartupStepState.Running)
            {
                State = StartupStepState.Succeeded;
                Progress = 1f;
            }
        }
    }
}
