using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace BlockOut.UI
{
    /// <summary>固定裁切视口内缩放作品；手势必须从视口开始，拖动统一换算为画布坐标。
    /// 双指结束到单指抬起之间**不重建拖动基准也不允许拖动**（P2-6）：
    /// 否则剩余手指会带着双指开始前的 startPointer/startPosition 拖动，画面瞬间跳回旧位置。</summary>
    [RequireComponent(typeof(RectTransform))]
    public sealed class BlockOutPinchZoom : MonoBehaviour, IPointerDownHandler, IPointerUpHandler,
        IBeginDragHandler, IDragHandler, IEndDragHandler
    {
        public RectTransform Target;
        public float MinScale = 1f;
        public float MaxScale = 3f;
        private RectTransform viewport;
        private bool pinching;
        private bool moved;
        /// <summary>本轮手势曾进入双指：必须等所有手指抬起后才允许新的单指拖动。</summary>
        private bool awaitAllRelease;
        private float startDistance;
        private float startScale;
        private float lastTap = -1f;
        private Vector2 startPointer, startPosition;

        private void Awake() { viewport = (RectTransform)transform; }
        private Camera EventCamera => GetComponentInParent<Canvas>().rootCanvas.renderMode == RenderMode.ScreenSpaceOverlay
            ? null : GetComponentInParent<Canvas>().rootCanvas.worldCamera;

        public void ResetView()
        {
            if (Target == null) return;
            Target.localScale = Vector3.one;
            Target.anchoredPosition = Vector2.zero;
            pinching = false;
            moved = false;
            awaitAllRelease = false;
            lastTap = -1f;
        }

        private void OnDisable() { ResetView(); }
        public void OnPointerDown(PointerEventData e)
        {
            // 还有手指未抬起（双指转单指）时，不重置手势基准，等全部抬起再重新开始（P2-6）
            if (awaitAllRelease && Input.touchCount > 0) return;
            moved = false;
        }
        public void OnPointerUp(PointerEventData e)
        {
            if (moved || pinching) { lastTap = -1f; return; }
            if (Time.unscaledTime - lastTap < .28f) ResetView();
            else lastTap = Time.unscaledTime;
        }
        public void OnBeginDrag(PointerEventData e)
        {
            if (awaitAllRelease) return;   // 双指遗留手指：不建立拖动基准（P2-6）
            moved = true;
            RectTransformUtility.ScreenPointToLocalPointInRectangle(viewport, e.position, e.pressEventCamera, out startPointer);
            if (Target != null) startPosition = Target.anchoredPosition;
        }
        public void OnDrag(PointerEventData e)
        {
            if (Target == null || pinching || awaitAllRelease) return;
            if (Input.touchCount > 1) return;
            if (Target.localScale.x <= 1f) return;   // 未放大时无需拖动（1× 即完整画面）
            RectTransformUtility.ScreenPointToLocalPointInRectangle(viewport, e.position, e.pressEventCamera, out var point);
            Target.anchoredPosition = startPosition + point - startPointer;
            ClampPosition();
        }
        public void OnEndDrag(PointerEventData e) { }

        private void Update()
        {
            if (Target == null) return;

            // 所有手指都已抬起 → 解除双指遗留锁，允许下一轮单指拖动（P2-6）
            if (awaitAllRelease && Input.touchCount == 0) awaitAllRelease = false;

            if (Input.touchCount != 2)
            {
                if (pinching)
                {
                    pinching = false;
                    // 双指刚结束：进入"等待全部抬起"，避免剩余手指沿用旧基准拖动
                    if (Input.touchCount > 0) awaitAllRelease = true;
                }
                return;
            }
            var a = Input.GetTouch(0);
            var b = Input.GetTouch(1);
            if (!pinching)
            {
                // 不接受在其他控件开始、随后滑进来的手势。
                if (a.phase != TouchPhase.Began && b.phase != TouchPhase.Began) return;
                if (!RectTransformUtility.RectangleContainsScreenPoint(viewport, a.position, EventCamera)
                    || !RectTransformUtility.RectangleContainsScreenPoint(viewport, b.position, EventCamera)) return;
                pinching = true;
                moved = true;
                lastTap = -1f;
                startDistance = Vector2.Distance(a.position, b.position);
                startScale = Target.localScale.x;
            }
            if (startDistance < 1f) return;
            float scale = Mathf.Clamp(startScale * Vector2.Distance(a.position, b.position) / startDistance, MinScale, MaxScale);
            Target.localScale = new Vector3(scale, scale, 1);
            ClampPosition();
        }

        private void ClampPosition()
        {
            float x = Mathf.Max(0, (Target.rect.width * Target.localScale.x - viewport.rect.width) * .5f);
            float y = Mathf.Max(0, (Target.rect.height * Target.localScale.y - viewport.rect.height) * .5f);
            var p = Target.anchoredPosition;
            Target.anchoredPosition = new Vector2(Mathf.Clamp(p.x, -x, x), Mathf.Clamp(p.y, -y, y));
        }
    }
}
