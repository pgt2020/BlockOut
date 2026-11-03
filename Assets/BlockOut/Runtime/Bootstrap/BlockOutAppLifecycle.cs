using System;
using BlockOut.Contracts;
using BlockOut.Gameplay;
using UnityEngine;

namespace BlockOut.Bootstrap
{
    /// <summary>统一应用生命周期状态（R06）。</summary>
    public enum AppLifecycleState
    {
        Booting,
        Playing,
        UserPaused,
        AutoPaused,
        AdOverlay,
        Restarting,
        Quitting,
    }

    /// <summary>
    /// 统一生命周期协调器（R06）。替代"多个脚本各自改暂停状态"：
    /// - 主动暂停（<see cref="RequestUserPause"/>）与切后台自动暂停（<see cref="NotifyAppPaused"/>）分开建模；
    /// - 回前台只补开暂停层，**不擅自 Resume 用户主动暂停的对局**；
    /// - 广告展示期间进入 <see cref="AppLifecycleState.AdOverlay"/>，关闭后恢复原状态；
    /// - 重开/退出置 <see cref="AppLifecycleState.Restarting"/> / <see cref="AppLifecycleState.Quitting"/>，
    ///   由 GameManager 的 activeRunToken 保证旧回调与协程不影响新局。
    /// </summary>
    public sealed class BlockOutAppLifecycle : MonoBehaviour
    {
        public AppLifecycleState State { get; private set; } = AppLifecycleState.Booting;

        /// <summary>切后台导致的自动暂停标记（与玩家主动暂停互斥）。</summary>
        public bool WasAutoPaused { get; private set; }

        public event Action<AppLifecycleState> OnStateChanged;
        public event Action OnAutoPauseNeedsPauseLayer;

        private BlockOutGameManager game;

        public void Bind(BlockOutGameManager gameManager)
        {
            game = gameManager;
            if (game != null)
            {
                game.OnPauseChanged += HandleGamePauseChanged;
                game.OnAppForegrounded += HandleGameForegrounded;
            }
            Enter(AppLifecycleState.Playing);
        }

        public void Unbind()
        {
            if (game != null)
            {
                game.OnPauseChanged -= HandleGamePauseChanged;
                game.OnAppForegrounded -= HandleGameForegrounded;
            }
            game = null;
        }

        // ---- 状态转换 ----

        public void RequestUserPause()
        {
            if (game == null) return;
            WasAutoPaused = false;             // 主动暂停：清掉后台标记
            game.Pause();
            Enter(AppLifecycleState.UserPaused);
        }

        public void RequestResume()
        {
            if (game == null) return;
            game.Resume();
            Enter(AppLifecycleState.Playing);
        }

        /// <summary>应用切后台/失焦：置自动暂停标记，由 GameManager 落盘并锁输入。</summary>
        public void NotifyAppPaused()
        {
            if (State == AppLifecycleState.Quitting || State == AppLifecycleState.Restarting) return;
            if (game == null || game.CurrentLevel == null) return;
            WasAutoPaused = true;
            Enter(AppLifecycleState.AutoPaused);
        }

        /// <summary>回到前台：**不自动 Resume**，只在需要时请求打开暂停层。</summary>
        public void NotifyAppResumed()
        {
            if (State == AppLifecycleState.Quitting || State == AppLifecycleState.Restarting) return;
            if (WasAutoPaused)
            {
                WasAutoPaused = false;
                OnAutoPauseNeedsPauseLayer?.Invoke();
            }
            if (game != null && !game.IsPaused) Enter(AppLifecycleState.Playing);
        }

        public void EnterAdOverlay()
        {
            if (State == AppLifecycleState.AdOverlay) return;
            adReturnState = State;
            Enter(AppLifecycleState.AdOverlay);
        }

        public void ExitAdOverlay()
        {
            if (State != AppLifecycleState.AdOverlay) return;
            Enter(adReturnState == AppLifecycleState.AdOverlay ? AppLifecycleState.Playing : adReturnState);
        }

        public void NotifyRestarting()
        {
            Enter(AppLifecycleState.Restarting);
        }

        public void NotifyPlaying()
        {
            if (State == AppLifecycleState.Restarting || State == AppLifecycleState.AdOverlay) return;
            Enter(AppLifecycleState.Playing);
        }

        public void NotifyQuitting()
        {
            Enter(AppLifecycleState.Quitting);
        }

        // ---- 内部 ----

        private AppLifecycleState adReturnState = AppLifecycleState.Playing;

        private void HandleGamePauseChanged(bool paused)
        {
            if (paused)
            {
                if (State != AppLifecycleState.UserPaused && State != AppLifecycleState.AutoPaused)
                    Enter(WasAutoPaused ? AppLifecycleState.AutoPaused : AppLifecycleState.UserPaused);
            }
            else
            {
                if (State == AppLifecycleState.UserPaused || State == AppLifecycleState.AutoPaused)
                    Enter(AppLifecycleState.Playing);
            }
        }

        private void HandleGameForegrounded()
        {
            NotifyAppResumed();
        }

        private void Enter(AppLifecycleState next)
        {
            if (State == next) return;
            State = next;
            OnStateChanged?.Invoke(next);
        }

        /// <summary>真机/编辑器应用暂停入口：与 GameManager 的 OnApplicationPause 对齐，
        /// 由本类统一转发，避免两处各自处理导致状态分裂。</summary>
        private void OnApplicationPause(bool paused)
        {
            if (paused) NotifyAppPaused();
            else NotifyAppResumed();
        }

        private void OnApplicationFocus(bool hasFocus)
        {
            if (!hasFocus) NotifyAppPaused();
            else NotifyAppResumed();
        }

        private void OnDestroy()
        {
            Unbind();
        }
    }
}
