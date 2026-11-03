using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace BlockOut.Gameplay
{
    /// <summary>
    /// 游戏棋盘手势控制器（R09）：双指捏合缩放、单指平移（与参考一致，缩小状态也可平移）、手势结束后抑制点击、
    /// 弹窗/暂停/输入锁期间不穿透。设计为挂在棋盘 <c>BoardArea</c> 视口上，作为棋盘方块的祖先，
    /// 借 UGUI 事件冒泡接收拖动；捏合直接读取 <see cref="Input.touchCount"/>（参考 BlockOutPinchZoom）。
    /// 实际缩放/平移作用对象为 <see cref="BlockOutBoardView.GetZoomRoot"/>（与入场缩放相互独立）。
    /// </summary>
    [RequireComponent(typeof(RectTransform))]
    public sealed class BlockOutBoardGesture : MonoBehaviour, IPointerDownHandler, IPointerUpHandler,
        IBeginDragHandler, IDragHandler, IEndDragHandler
    {
        public BlockOutGameManager GM;
        public BlockOutBoardView BoardView;
        public RectTransform Viewport;
        public float MinScale = 1f;
        public float MaxScale = 3f;
        public float TapSuppressSeconds = 0.16f;

        private RectTransform target;
        private bool pinching, awaitAllRelease, moved;
        private float startDistance, startScale;
        private Vector2 startPointer, startPosition;

        private Camera EventCamera
        {
            get
            {
                var canvas = GetComponentInParent<Canvas>();
                if (canvas == null) return null;
                return canvas.rootCanvas.renderMode == RenderMode.ScreenSpaceOverlay
                    ? null : canvas.rootCanvas.worldCamera;
            }
        }

        /// <summary>弹窗/暂停/输入锁期间屏蔽手势，避免穿透到棋盘（R09）。</summary>
        private bool Blocked
        {
            get
            {
                if (GM != null && GM.GuideInputActive) return true;
                if (GM != null && GM.ModalPopupOpen) return true;
                if (GM != null && GM.IsPaused) return true;
                if (BoardView != null && BoardView.IsInputLocked) return true;
                return false;
            }
        }

        void Start()
        {
            if (BoardView != null) target = BoardView.GetZoomRoot();
            // N06：抑制时间读配置（feel.gestureTapSuppressSeconds），非零才覆盖默认值
            var cfg = BlockOut.Config.BlockOutGameplayConfig.Current;
            if (cfg != null && cfg.feel != null && cfg.feel.gestureTapSuppressSeconds > 0f)
                TapSuppressSeconds = cfg.feel.gestureTapSuppressSeconds;
        }

        /// <summary>N06：统一收尾手势状态（全部松手 / 被屏蔽 / 切关重开时调用）。</summary>
        private void ResetGestureState()
        {
            pinching = false;
            awaitAllRelease = false;
            moved = false;
        }

        public void OnPointerDown(PointerEventData e)
        {
            if (Blocked) return;
            // 双指转单指遗留手指：不重置手势基准，等全部抬起再重新开始（P2-6）
            if (awaitAllRelease && Input.touchCount > 0) return;
            moved = false;
        }

        public void OnPointerUp(PointerEventData e)
        {
            if (Blocked) return;
            // 发生过拖动/捏合：结束抑制一次点击，避免"拖动/双指变单指"误消块（R09）
            if (moved || pinching)
            {
                if (BoardView != null) BoardView.SuppressTaps(TapSuppressSeconds);
                moved = false;
            }
        }

        public void OnBeginDrag(PointerEventData e)
        {
            if (Blocked) return;
            if (awaitAllRelease) return;   // 双指遗留手指：不建立拖动基准（P2-6）
            moved = true;
            if (target == null && BoardView != null) target = BoardView.GetZoomRoot();
            if (target == null) return;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(Viewport, e.position, e.pressEventCamera, out startPointer);
            startPosition = target.anchoredPosition;
        }

        public void OnDrag(PointerEventData e)
        {
            if (Blocked) { ResetGestureState(); return; }   // N06：模态/暂停/锁出现时立即停止位移并收尾
            if (target == null || pinching || awaitAllRelease) return;
            if (Input.touchCount > 1) return;
            // 与参考一致，缩小状态也可拖动，边界由相机视野统一限制。

            RectTransformUtility.ScreenPointToLocalPointInRectangle(Viewport, e.position, e.pressEventCamera, out var point);
            target.anchoredPosition += point - startPointer;
            startPointer=point;
            BoardView?.SuppressTaps(TapSuppressSeconds);
            ClampPosition();
        }

        public void OnEndDrag(PointerEventData e) { BoardView?.SuppressTaps(TapSuppressSeconds); }

        void Update()
        {
            if (target == null)
            {
                if (BoardView != null) target = BoardView.GetZoomRoot();
                if (target == null) return;
            }
            // 弹窗/暂停/输入锁期间：放弃手势、复位状态，避免穿透（R09）
            if (Blocked)
            {
                ResetGestureState();
                return;
            }

            // 桌面端滚轮缩放（便于验证；移动端走双指）
            float wheel = Input.GetAxis("Mouse ScrollWheel");
            if (wheel != 0f && Viewport != null
                && RectTransformUtility.RectangleContainsScreenPoint(Viewport, Input.mousePosition, EventCamera))
            {
                ZoomAroundCenter(wheel > 0f ? 1.1f : 0.9f);
            }

            if (Input.touchCount != 2)
            {
                if (Input.touchCount == 0)
                {
                    // N06：全部手指松开 → 明确清除"等待全部抬起"，避免后续单指拖动被永久拦截
                    ResetGestureState();
                    return;
                }
                if (pinching)
                {
                    pinching = false;
                    // 双指刚结束：进入"等待全部抬起"，避免剩余手指沿用旧基准拖动（P2-6）
                    if (Input.touchCount > 0) awaitAllRelease = true;
                }
                return;
            }
            var a = Input.GetTouch(0);
            var b = Input.GetTouch(1);
            if (!pinching)
            {
                // 不接受在其他控件开始、随后滑进来的手势
                if (a.phase != TouchPhase.Began && b.phase != TouchPhase.Began) return;
                if (Viewport != null && (!RectTransformUtility.RectangleContainsScreenPoint(Viewport, a.position, EventCamera)
                    || !RectTransformUtility.RectangleContainsScreenPoint(Viewport, b.position, EventCamera))) return;
                pinching = true;
                moved = true;
                if (BoardView != null) BoardView.SuppressTaps(TapSuppressSeconds);   // 捏合期间抑制点击（R09）
                startDistance = Vector2.Distance(a.position, b.position);
                startScale = BoardView != null ? BoardView.GetZoomScale() : 1f;
            }
            if (startDistance < 1f) return;
            float distance=Vector2.Distance(a.position,b.position);
            float factor=1+(distance-startDistance)*.0008f*2;
            float scale=Mathf.Clamp(target.localScale.x*Mathf.Max(.01f,factor),BoardView.MinimumZoom,BoardView.MaximumZoom);
            startDistance=distance;
            BoardView.SuppressTaps(TapSuppressSeconds);
            if (target != null) target.localScale = new Vector3(scale, scale, 1f);
            ClampPosition();
        }

        private void ZoomAroundCenter(float factor)
        {
            if (target == null || BoardView == null) return;
            float scale = Mathf.Clamp(BoardView.GetZoomScale() * factor, BoardView.MinimumZoom, BoardView.MaximumZoom);
            target.localScale = new Vector3(scale, scale, 1f);
            ClampPosition();
        }

        private void ClampPosition()
        {
            if(target==null || BoardView==null)return;
            target.anchoredPosition=BoardView.ClampPan(target.anchoredPosition,target.localScale.x);
        }
    }
}
