using BlockOut.Infrastructure.Configuration;
using UnityEngine;
using UnityEngine.UI;

namespace BlockOut.Bootstrap
{
    /// <summary>
    /// 启动器（R03）：挂在 Launcher 场景唯一 GameObject 上，是**唯一正式组装入口**。
    /// 取代旧 <c>RuntimeInitializeOnLoadMethod</c> 自动启动：
    /// - 重复入口防护（场景里放两个 / 直接打开业务场景都不会起第二套应用）；
    /// - 应用配置（帧率/输入/日志）来自 StartupConfig 资产；
    /// - 显式启动步骤（进度/超时/失败处理）；
    /// - 就绪后创建 AppRoot 并装配 GameManager/UI/Controller。
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class BlockOutLauncher : MonoBehaviour
    {
        [Header("启动配置资产（Editor/Development/Release 三档）")]
        [SerializeField] private BlockOutStartupConfig startupConfig;
        [SerializeField] private BlockOutAdConfig adConfig;

        [Header("AppRoot Prefab（为空则代码创建）")]
        [SerializeField] private GameObject appRootPrefab;

        [Header("启动页")]
        [SerializeField] private bool showSplash = true;

        private BlockOutStartupSequence sequence;
        private bool booted;

        /// <summary>启动是否成功（检查工具/测试读取）。</summary>
        public bool BootSucceeded => sequence != null && sequence.Succeeded;

        void Awake()
        {
            // 重复入口防护：同场景第二个 Launcher 自毁；已有 AppRoot 说明本进程已启动过。
            var others = FindObjectsOfType<BlockOutLauncher>();
            if (others.Length > 1)
            {
                foreach (var o in others) if (o != this) { Destroy(o.gameObject); break; }
            }
            if (BlockOutAppRoot.Instance != null) { Destroy(gameObject); return; }
            DontDestroyOnLoad(gameObject);
        }

        void Start()
        {
            if (booted) return;
            booted = true;
            StartCoroutine(BootRoutine());
        }

        private System.Collections.IEnumerator BootRoutine()
        {
            // 1) 应用根（服务注册表容器）
            var root = BlockOutAppRoot.Ensure(appRootPrefab);
            root.Configure(startupConfig, adConfig);

            // 2) 显式启动序列
            sequence = new BlockOutStartupSequence(startupConfig, adConfig, root.Services);
            if (showSplash) BuildSplash();

            var runner = sequence.Run();
            while (true)
            {
                bool moved;
                try { moved = runner.MoveNext(); }
                catch (System.Exception e)
                {
                    Debug.LogError("[BlockOut] 启动序列异常：" + e.Message);
                    ShowBootFailure("启动异常：" + e.Message);
                    yield break;
                }
                if (!moved) break;
                UpdateSplash();
                yield return runner.Current;
            }

            if (!sequence.Succeeded)
            {
                ShowBootFailure(sequence.FailureReason);
                yield break;
            }

            // 3) 装配业务对象（服务已就绪，GM/UI 只消费服务）
            BlockOutAppBuilder.Build(root);
            root.MarkReady();
            HideSplash();
            Debug.Log("[BlockOut] 启动完成（" + (startupConfig != null ? startupConfig.EnvironmentName : "?") + "）。");
        }

        // ---- 启动页（轻量：不占用 UI Prefab 资产，避免与游戏页面抢资源）----

        private GameObject splashGo;
        private UnityEngine.UI.Text splashText;

        private void BuildSplash()
        {
            if (!showSplash || startupConfig == null || !startupConfig.showStartupSplash) return;
            splashGo = new GameObject("BlockOut_StartupSplash", typeof(RectTransform), typeof(Canvas), typeof(UnityEngine.UI.CanvasScaler));
            var canvas = splashGo.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 999;
            var scaler = splashGo.GetComponent<UnityEngine.UI.CanvasScaler>();
            scaler.uiScaleMode = UnityEngine.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(390, 844);

            var labelGo = new GameObject("Label", typeof(RectTransform), typeof(UnityEngine.UI.Text));
            labelGo.transform.SetParent(splashGo.transform, false);
            var rt = (RectTransform)labelGo.transform;
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = Vector2.zero; rt.offsetMax = Vector2.zero;
            splashText = labelGo.GetComponent<UnityEngine.UI.Text>();
            splashText.alignment = TextAnchor.MiddleCenter;
            splashText.fontSize = 18;
            splashText.color = new Color(0.36f, 0.22f, 0.13f);
            splashText.text = "BlockOut\n启动中… 0%";
        }

        private void UpdateSplash()
        {
            if (splashText == null || sequence == null) return;
            int done = sequence.CompletedSteps;
            int total = System.Math.Max(1, sequence.TotalSteps);
            float pct = (done + sequence.CurrentStepProgress) / total * 100f;
            splashText.text = "BlockOut\n" + (sequence.CurrentStepName ?? "启动中") + " " + Mathf.RoundToInt(pct) + "%";
        }

        private void HideSplash()
        {
            if (splashGo != null) { Destroy(splashGo); splashGo = null; splashText = null; }
        }

        private void ShowBootFailure(string reason)
        {
            Debug.LogError("[BlockOut] 启动失败：" + reason);
            if (splashText != null)
                splashText.text = "启动失败\n" + reason + "\n\n请重试或查看日志";
        }
    }
}
