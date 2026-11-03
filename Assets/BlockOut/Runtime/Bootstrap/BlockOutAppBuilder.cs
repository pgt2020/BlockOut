using BlockOut.Core;
using BlockOut.Gameplay;
using BlockOut.Infrastructure.Persistence;
using BlockOut.UI;
using UnityEngine;
using UnityEngine.EventSystems;

namespace BlockOut.Bootstrap
{
    /// <summary>
    /// 应用对象装配器（R03）。取代旧 <c>BlockOutBootstrapper</c> 的 Awake 装配逻辑：
    /// 相机 / EventSystem / GameManager / UIManager / BoardView / UIController / 生命周期协调器
    /// 全部挂到 <see cref="BlockOutAppRoot"/> 下，**只创建一份**（重复检测后销毁多余者）。
    /// 服务（广告/存档/资源）由启动序列注册，本类不 new 任何 SDK 实现。
    /// </summary>
    public static class BlockOutAppBuilder
    {
        public static BlockOutGameManager Build(BlockOutAppRoot root)
        {
            var registry = root != null ? root.Services : new BlockOutServiceRegistry();

            EnsureCamera(root);
            EnsureEventSystem(root);

            // ---- GameManager（玩法协调；SDK/存档由外部注入）----
            var gmGo = CreateChild(root, "BlockOut_GameManager");
            var gm = gmGo.AddComponent<BlockOutGameManager>();
            gm.BindServices(registry.Resolve<Contracts.IAdProvider>(), registry.Resolve<BlockOutSaveService>());
            registry.Register(gm);

            // ---- UI ----
            var uiGo = CreateChild(root, "BlockOut_UIManager");
            var ui = uiGo.AddComponent<BlockOutUIManager>();
            ui.Build();
            registry.Register(ui);

            var boardArea = ui.BoardArea;
            if (boardArea != null)
            {
                var boardGo = new GameObject("BlockOut_BoardView", typeof(RectTransform));
                boardGo.transform.SetParent(boardArea, false);
                var rt = boardGo.GetComponent<RectTransform>();
                rt.anchorMin = Vector2.zero;
                rt.anchorMax = Vector2.one;
                rt.offsetMin = Vector2.zero;
                rt.offsetMax = Vector2.zero;
                gm.boardView = boardGo.AddComponent<BlockOutBoardView>();
                ui.BoardView = gm.boardView;
                gm.boardView.MagicOrigin=ui.MagicSlot.Rect;
                gm.boardView.EffectSurfaceParent=boardArea.parent;
                boardArea.SetAsFirstSibling();
                // R09：游戏棋盘手势（双指缩放 / 单指平移 / 结束后抑制点击 / 弹窗不穿透），挂在 BoardArea 上。
                var gesture = boardArea.gameObject.AddComponent<BlockOutBoardGesture>();
                gesture.GM = gm;
                gesture.BoardView = gm.boardView;
                gesture.Viewport = boardArea;
            }

            var ctrlGo = CreateChild(root, "BlockOut_UIController");
            var ctrl = ctrlGo.AddComponent<BlockOutUIController>();
            ctrl.UI = ui;
            ctrl.GM = gm;
            registry.Register(ctrl);

            // ---- 生命周期协调器（R06）----
            var lifeGo = CreateChild(root, "BlockOut_AppLifecycle");
            var life = lifeGo.AddComponent<BlockOutAppLifecycle>();
            life.Bind(gm);
            registry.Register(life);
            if (root != null) root.AttachLifecycle(life);

            return gm;
        }

        private static GameObject CreateChild(BlockOutAppRoot root, string name)
        {
            var go = new GameObject(name);
            if (root != null) go.transform.SetParent(root.transform, false);
            return go;
        }

        private static void EnsureCamera(BlockOutAppRoot root)
        {
            if (Camera.main != null)
            {
                // C01：静态类不继承 UnityEngine.Object 的静态成员，必须显式限定类型。
                if (UnityEngine.Object.FindFirstObjectByType<AudioListener>() == null) Camera.main.gameObject.AddComponent<AudioListener>();
                return;
            }
            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            if (UnityEngine.Object.FindFirstObjectByType<AudioListener>() == null) camGo.AddComponent<AudioListener>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(1f, 0.96f, 0.92f);
            cam.orthographic = true;
            cam.orthographicSize = 5f;
            cam.transform.position = new Vector3(0, 0, -10);
            if (root != null) camGo.transform.SetParent(root.transform, false);
            Object.DontDestroyOnLoad(camGo);
        }

        private static void EnsureEventSystem(BlockOutAppRoot root)
        {
            if (UnityEngine.Object.FindFirstObjectByType<EventSystem>() != null) return;
            var esGo = new GameObject("EventSystem");
            esGo.AddComponent<EventSystem>();
            esGo.AddComponent<StandaloneInputModule>();
            if (root != null) esGo.transform.SetParent(root.transform, false);
            Object.DontDestroyOnLoad(esGo);
        }
    }
}
