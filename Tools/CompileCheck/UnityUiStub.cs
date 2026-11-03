// BlockOut 离线编译校验用 UnityEngine.UI / EventSystems 桩（仅编译期存在）。
using System;
using System.Collections.Generic;
using UnityEngine.EventSystems;

namespace UnityEngine.UI
{
    public class UIBehaviour : MonoBehaviour { public virtual void MarkDirty() { } }

    public class CanvasRenderer : Component
    {
        public void SetColor(Color c) { }
        public Color GetColor() => Color.white;
        public void SetAlpha(float a) { }
        public float GetAlpha() => 1f;
        public bool cull { get; set; }
        public int relativeDepth { get; set; }
    }

    public enum RenderMode { ScreenSpaceOverlay, ScreenSpaceCamera, WorldSpace }

    public class Canvas : UIBehaviour
    {
        public RenderMode renderMode { get; set; } = RenderMode.ScreenSpaceOverlay;
        public Camera worldCamera { get; set; }
        public Rect pixelRect { get; set; }
        public float planeDistance { get; set; } = 100f;
        public int sortingOrder { get; set; }
        public int targetDisplay { get; set; }
        public bool overrideSorting { get; set; }
        public string sortingLayerName { get; set; }
        public int cachedSortingLayerValue { get; set; }
        public float scaleFactor { get; set; } = 1f;
        public Vector2 referenceResolution { get; set; }
        public Canvas rootCanvas => null;
        public static Canvas FindCanvas(Transform t) => null;
        public CanvasRenderer GetComponent<T>() => null;
    }

    public class CanvasScaler : UIBehaviour
    {
        public enum ScaleMode { ConstantPixelSize, ScaleWithScreenSize, ConstantPhysicalSize }
        public enum ScreenMatchMode { MatchWidthOrHeight = 0, Expand = 1, Shrink = 2 }
        public enum Unit { Centimeters, Millimeters, Inches, Points, Picas }

        public ScaleMode uiScaleMode { get; set; } = ScaleMode.ConstantPixelSize;
        public float referencePixelsPerUnit { get; set; } = 100f;
        public float scaleFactor { get; set; } = 1f;
        public Vector2 referenceResolution { get; set; } = new Vector2(800f, 600f);
        public ScreenMatchMode screenMatchMode { get; set; }
        public float matchWidthOrHeight { get; set; } = 0.5f;
        public float dynamicPixelsPerUnit { get; set; } = 1f;
        public float physicalUnit { get; set; } = 1f;
        public Unit defaultSpriteDPI { get; set; }
        public float fallbackScreenDPI { get; set; } = 96f;
    }

    public class Graphic : UIBehaviour
    {
        public virtual Color color { get; set; } = Color.white;
        public bool raycastTarget { get; set; } = true;
        public virtual Material material { get; set; }
        public CanvasRenderer canvasRenderer => null;
        public bool useLegacyMeshGeneration { get; set; }
        public RectTransform rectTransform => (RectTransform)transform;
        public virtual void SetAllDirty() { }
        public virtual void SetVerticesDirty() { }
        public virtual void SetMaterialDirty() { }
        public virtual void SetLayoutDirty() { }
        public virtual void CrossFadeColor(Color c, float d, bool ig, bool ua) { }
        public virtual void CrossFadeAlpha(float a, float d, bool ig) { }
        public void Rebuild(CanvasUpdate u) { }
        public void RegisterDirtyLayoutCallback(Action<Graphic> a) { }
        public void UnregisterDirtyLayoutCallback(Action<Graphic> a) { }
        public void RegisterDirtyVerticesCallback(Action<Graphic> a) { }
        public void UnregisterDirtyVerticesCallback(Action<Graphic> a) { }
        public void RegisterDirtyMaterialCallback(Action<Material> a) { }
        public void UnregisterDirtyMaterialCallback(Action<Material> a) { }
    }

    public enum CanvasUpdate { Prelayout, Layout, PostLayout, PreRender, LatePreRender, MaxUpdateValue }

    public enum Type { Simple, Sliced, Tiled, Filled }
    public enum FillMethod { Horizontal, Vertical, Radial90, Radial180, Radial360 }
    public enum FillOrigin { HorizontalLeft = 0, Top = 0, VerticalBottom = 0, Radial90BottomLeft = 0 }

    public class Image : Graphic
    {
        public enum Type { Simple, Sliced, Tiled, Filled }
        public enum FillMethod { Horizontal, Vertical, Radial90, Radial180, Radial360 }
        public enum OriginHorizontal { Left, Right }
        public enum OriginVertical { Bottom, Top }
        public enum Origin90 { BottomLeft, TopLeft, TopRight, BottomRight }
        public enum Origin180 { Bottom, Left, Top, Right }
        public enum Origin360 { Bottom, Right, Top, Left }
        public enum FillOrigin
        {
            Bottom = 0, Right = 0, Top = 0, Left = 0,
            VerticalBottom = 0, VerticalTop = 1,
            HorizontalLeft = 0, HorizontalRight = 1,
            Radial90BottomLeft = 0, Radial90TopLeft = 1, Radial90TopRight = 2, Radial90BottomRight = 3,
            Radial180Bottom = 0, Radial180Left = 1, Radial180Top = 2, Radial180Right = 3,
            Radial360Bottom = 0, Radial360Right = 1, Radial360Top = 2, Radial360Left = 3
        }

        public Sprite sprite { get; set; }
        public Sprite overrideSprite { get; set; }
        public float fillAmount { get; set; } = 1f;
        public bool fillClockwise { get; set; } = true;
        public FillOrigin fillOrigin { get; set; }
        public FillMethod fillMethod { get; set; }
        public Type type { get; set; } = Type.Simple;
        public bool preserveAspect { get; set; }
        public bool useSpriteMesh { get; set; }
        public float pixelsPerUnitMultiplier { get; set; } = 1f;
        public Texture texture => null;
        public void SetNativeSize() { }
        public override Material material { get; set; }
        public float alphaHitMinimumThreshold { get; set; }
        public bool hasBorder { get; }
    }

    public enum FontStyle { Normal, Bold, Italic, BoldAndItalic }
    public enum HorizontalWrapMode { Wrap, Overflow }
    public enum VerticalWrapMode { Truncate, Overflow }
    public enum TextAnchor { UpperLeft, UpperCenter, UpperRight, MiddleLeft, MiddleCenter, MiddleRight, LowerLeft, LowerCenter, LowerRight }

    public class Text : Graphic
    {
        public string text { get; set; } = "";
        public Font font { get; set; }
        public int fontSize { get; set; } = 14;
        public FontStyle fontStyle { get; set; }
        public float lineSpacing { get; set; } = 1f;
        public bool supportRichText { get; set; }
        public TextAnchor alignment { get; set; } = TextAnchor.UpperLeft;
        public bool alignByGeometry { get; set; }
        public HorizontalWrapMode horizontalOverflow { get; set; }
        public VerticalWrapMode verticalOverflow { get; set; }
        public bool resizeTextForBestFit { get; set; }
        public int resizeTextMinSize { get; set; } = 10;
        public int resizeTextMaxSize { get; set; } = 100;
        public float preferredWidth => 0f;
        public float preferredHeight => 0f;
        public float flexibleWidth => 0f;
        public float flexibleHeight => 0f;
        public int minWidth => 0;
        public int minHeight => 0;
        public void CalculateLayoutInputHorizontal() { }
        public void CalculateLayoutInputVertical() { }
    }

    public class Button : Selectable
    {
        public ButtonClickedEvent onClick { get; } = new ButtonClickedEvent();
        public Graphic targetGraphic { get; set; }
        public bool interactable_ { get; set; }
        public void OnPointerClick(EventSystems.PointerEventData d) { }
        public void Submit() { }
    }

    public class ButtonClickedEvent : UnityEvent { }

    public class Toggle : Selectable
    {
        public ToggleTransition transition { get; set; }
        public Graphic graphic { get; set; }
        public ToggleGroup group { get; set; }
        public bool isOn { get; set; }
        public ToggleEvent onValueChanged { get; } = new ToggleEvent();
    }

    public enum ToggleTransition { None, Fade, ColorTint }
    public class ToggleEvent : UnityEvent<bool> { }

    public class ToggleGroup : UIBehaviour
    {
        public bool allowSwitchOff { get; set; }
        public IEnumerable<Toggle> ActiveToggles() => new Toggle[0];
        public Toggle GetFirstActiveToggle() => null;
        public bool AnyTogglesOn() => false;
        public void NotifyToggleOn(Toggle t) { }
        public void UnregisterToggle(Toggle t) { }
        public void RegisterToggle(Toggle t) { }
    }

    public enum Direction { LeftToRight, RightToLeft, BottomToTop, TopToBottom }

    public class Slider : Selectable
    {
        public float value { get; set; }
        public float minValue { get; set; }
        public float maxValue { get; set; } = 1f;
        public bool wholeNumbers { get; set; }
        public RectTransform fillRect { get; set; }
        public RectTransform handleRect { get; set; }
        public Direction direction { get; set; } = Direction.LeftToRight;
        public SliderEvent onValueChanged { get; } = new SliderEvent();
        public float normalizedValue { get; set; }
        public void SetValueWithoutNotify(float v) { }
        public void Rebuild(CanvasUpdate u) { }
    }

    public class SliderEvent : UnityEvent<float> { }

    public enum MovementType { Unrestricted, Elastic, Clamped }

    public class ScrollRect : UIBehaviour
    {
        public enum MovementType { Unrestricted, Elastic, Clamped }
        public enum ScrollbarVisibility { Permanent, AutoHide, AutoHideAndExpandViewport }

        public RectTransform content { get; set; }
        public RectTransform viewport { get; set; }
        public bool horizontal { get; set; }
        public bool vertical { get; set; } = true;
        public MovementType movementType { get; set; } = MovementType.Elastic;
        public float elasticity { get; set; } = 0.1f;
        public float scrollSensitivity { get; set; } = 10f;
        public float decelerationRate { get; set; } = 0.135f;
        public bool inertia { get; set; } = true;
        public float verticalNormalizedPosition { get; set; } = 1f;
        public float horizontalNormalizedPosition { get; set; }
        public Vector2 velocity { get; set; }
        public ScrollRectEvent onValueChanged { get; } = new ScrollRectEvent();
        public Scrollbar horizontalScrollbar { get; set; }
        public Scrollbar verticalScrollbar { get; set; }
        public ScrollbarVisibility horizontalScrollbarVisibility { get; set; }
        public ScrollbarVisibility verticalScrollbarVisibility { get; set; }
        public void StopMovement() { }
        public void ScrollToBottom() { }
        public void ScrollToTop() { }
        public void ScrollToLeft() { }
        public void ScrollToRight() { }
        public void SetContentNormalizedPosition(Vector2 p) { }
        public void Rebuild(CanvasUpdate u) { }
        public void OnBeginDrag(EventSystems.PointerEventData d) { }
        public void OnDrag(EventSystems.PointerEventData d) { }
        public void OnEndDrag(EventSystems.PointerEventData d) { }
    }

    public class ScrollRectEvent : UnityEvent<Vector2> { }

    public class Scrollbar : Selectable
    {
        public float value { get; set; }
        public float size { get; set; } = 0.5f;
        public int numberOfSteps { get; set; } = 1;
        public RectTransform handleRect { get; set; }
        public Direction direction { get; set; } = Direction.LeftToRight;
        public ScrollbarEvent onValueChanged { get; } = new ScrollbarEvent();
        public void SetValueWithoutNotify(float v) { }
        public void Rebuild(CanvasUpdate u) { }
    }

    public class ScrollbarEvent : UnityEvent<float> { }

    public class Selectable : UIBehaviour, IEventSystemHandler, IPointerEnterHandler, IPointerExitHandler, IPointerDownHandler, IPointerUpHandler, IPointerClickHandler, IMoveHandler, ISelectHandler, IDeselectHandler
    {
        public enum Transition { None, ColorTint, SpriteSwap, Animation }

        public bool interactable { get; set; } = true;
        public Graphic targetGraphic { get; set; }
        public Transition transition { get; set; } = Transition.ColorTint;
        public ColorBlock colors { get; set; } = ColorBlock.defaultColorBlock;
        public SpriteState spriteState { get; set; }
        public AnimationTriggers animationTriggers { get; set; }
        public Navigation navigation { get; set; } = Navigation.defaultNavigation;
        public Image image => null;
        public bool IsInteractable() => interactable;
        public Selectable FindSelectableOnLeft() => null;
        public Selectable FindSelectableOnRight() => null;
        public Selectable FindSelectableOnUp() => null;
        public Selectable FindSelectableOnDown() => null;
        public void Select() { }
        public void OnSelect(EventSystems.BaseEventData d) { }
        public void OnDeselect(EventSystems.BaseEventData d) { }
        public void OnPointerEnter(EventSystems.PointerEventData d) { }
        public void OnPointerExit(EventSystems.PointerEventData d) { }
        public void OnPointerDown(EventSystems.PointerEventData d) { }
        public void OnPointerUp(EventSystems.PointerEventData d) { }
        public void OnPointerClick(EventSystems.PointerEventData d) { }
        public void OnMove(EventSystems.AxisEventData d) { }
        public virtual void DoStateTransition(SelectionState s, bool instant) { }
        protected void InstantClearState() { }
        protected void OnEnable() { }
        protected void OnDisable() { }
        public bool IsHighlighted() => false;
        public bool IsPressed() => false;
        public bool IsSelected() => false;
    }

    public enum Transition { None, ColorTint, SpriteSwap, Animation }
    public enum SelectionState { Normal, Highlighted, Pressed, Selected, Disabled }

    public struct ColorBlock
    {
        public Color normalColor, highlightedColor, pressedColor, selectedColor, disabledColor;
        public float colorMultiplier, fadeDuration;
        public static ColorBlock defaultColorBlock => new ColorBlock
        {
            normalColor = Color.white, highlightedColor = Color.white, pressedColor = Color.white,
            selectedColor = Color.white, disabledColor = new Color(0.78f, 0.78f, 0.78f, 0.78f),
            colorMultiplier = 1f, fadeDuration = 0.1f,
        };
    }

    public struct SpriteState
    {
        public Sprite highlightedSprite, pressedSprite, selectedSprite, disabledSprite;
        public float fadeDuration;
    }

    public class AnimationTriggers
    {
        public string normalTrigger = "Normal";
        public string highlightedTrigger = "Highlighted";
        public string pressedTrigger = "Pressed";
        public string selectedTrigger = "Selected";
        public string disabledTrigger = "Disabled";
    }

    public struct Navigation
    {
        public Mode mode;
        public bool wrapAround;
        public Selectable selectOnLeft, selectOnRight, selectOnUp, selectOnDown;
        public static Navigation defaultNavigation => new Navigation { mode = Mode.Automatic };
    }

    public enum Mode { None, Automatic, Horizontal, Vertical, Explicit }

    public class GraphicRaycaster : BaseRaycaster
    {
        public bool ignoreReversedGraphics { get; set; } = true;
        public BlockingObjects blockingObjects { get; set; } = BlockingObjects.ThreeD;
        public int sortOrderPriority { get; set; }
        public int renderOrderPriority { get; set; }
        public int priority { get; set; }
        public override void Raycast(EventSystems.PointerEventData d, List<EventSystems.RaycastResult> r) { }
        public Canvas canvas => null;
    }

    public enum BlockingObjects { None, TwoD, ThreeD, All }

    public class Shadow : UIBehaviour, IMeshModifier
    {
        public Color effectColor { get; set; } = new Color(0f, 0f, 0f, 0.5f);
        public Vector2 effectDistance { get; set; } = new Vector2(1f, -1f);
        public bool useGraphicAlpha { get; set; }
        public void ModifyMesh(VertexHelper vh) { }
    }

    public class Outline : Shadow
    {
        public bool useGraphicAlpha2 { get; set; }
    }

    public interface IMeshModifier { void ModifyMesh(VertexHelper vh); }

    public class VertexHelper
    {
        public int currentVertCount => 0;
        public int currentIndexCount => 0;
        public void AddVert(Vector3 p, Color c, Vector2 uv) { }
        public void AddVert(Vector3 p, Color c, Vector2 uv0, Vector2 uv1, Vector2 uv2, Vector2 uv3, Vector3 n, Vector4 t) { }
        public void AddTriangle(int a, int b, int c) { }
        public void FillMesh(Mesh m) { }
        public void PopulateUIVertex(UIVertex v, int i) { }
        public UIVertex GetUIVertex(int i) => default;
    }

    public struct UIVertex
    {
        public Vector3 position; public Vector3 normal; public Color32 color; public Vector2 uv0; public Vector2 uv1; public Vector2 uv2; public Vector2 uv3; public Vector4 tangent;
        public static UIVertex simpleVert => default;
    }

    public class RectMask2D : UIBehaviour
    {
        public Vector4 padding { get; set; }
        public float softness { get; set; }
        public bool isMaskingGraphic { get; set; }
        public void PerformClipping() { }
    }

    public abstract class LayoutGroup : UIBehaviour
    {
        public RectOffset padding { get; set; } = new RectOffset();
        public TextAnchor childAlignment { get; set; } = TextAnchor.UpperLeft;
        public bool childForceExpandWidth { get; set; }
        public bool childForceExpandHeight { get; set; }
        public bool childControlWidth { get; set; }
        public bool childControlHeight { get; set; }
        public bool childScaleWidth { get; set; }
        public bool childScaleHeight { get; set; }
        public virtual void CalculateLayoutInputHorizontal() { }
        public virtual void CalculateLayoutInputVertical() { }
        public virtual void SetLayoutHorizontal() { }
        public virtual void SetLayoutVertical() { }
        public void SetDirty() { }
    }

    public class HorizontalOrVerticalLayoutGroup : LayoutGroup
    {
        public float spacing { get; set; }
        public bool childForceExpandWidth_ { get; set; }
        public bool childForceExpandHeight_ { get; set; }
        public bool childControlWidth_ { get; set; }
        public bool childControlHeight_ { get; set; }
        public bool childScaleWidth_ { get; set; }
        public bool childScaleHeight_ { get; set; }
        public bool reverseArrangement { get; set; }
    }

    public class HorizontalLayoutGroup : HorizontalOrVerticalLayoutGroup { }
    public class VerticalLayoutGroup : HorizontalOrVerticalLayoutGroup { }

    public enum Constraint { Flexible, FixedColumnCount, FixedRowCount }

    public class GridLayoutGroup : LayoutGroup
    {
        public Corner startCorner { get; set; }
        public Axis startAxis { get; set; }
        public Vector2 cellSize { get; set; } = new Vector2(100f, 100f);
        public Vector2 spacing { get; set; }
        public Constraint constraint { get; set; } = Constraint.Flexible;
        public int constraintCount { get; set; } = 2;
    }

    public enum Corner { UpperLeft, UpperRight, LowerLeft, LowerRight }
    public enum Axis { Horizontal, Vertical }

    public enum FitMode { Unconstrained, MinSize, PreferredSize }

    public class ContentSizeFitter : UIBehaviour
    {
        public FitMode horizontalFit { get; set; }
        public FitMode verticalFit { get; set; }
        public void SetLayoutVertical() { }
        public void SetLayoutHorizontal() { }
    }

    public enum AspectMode { None, WidthControlsHeight, HeightControlsWidth, FitInParent, EnvelopeParent }

    public class AspectRatioFitter : UIBehaviour
    {
        public AspectMode aspectMode { get; set; }
        public float aspectRatio { get; set; } = 1f;
        public RectTransform rectTransform => (RectTransform)transform;
        public void SetLayoutHorizontal() { }
        public void SetLayoutVertical() { }
    }

    public class CanvasGroup : UIBehaviour
    {
        public float alpha { get; set; } = 1f;
        public bool interactable { get; set; } = true;
        public bool blocksRaycasts { get; set; } = true;
        public bool ignoreParentGroups { get; set; }
        public void Rebuild() { }
    }

    public class LayoutRebuilder
    {
        public static void ForceRebuildLayoutImmediate(RectTransform t) { }
        public static void MarkLayoutForRebuild(RectTransform t) { }
    }

    public class RectOffset
    {
        public int left, right, top, bottom;
        public RectOffset() { }
        public RectOffset(int l, int r, int t, int b) { left = l; right = r; top = t; bottom = b; }
        public int horizontal => left + right;
        public int vertical => top + bottom;
    }

    public abstract class UnityEvent : UnityEventBase
    {
        public void AddListener(UnityAction call) { }
        public void RemoveListener(UnityAction call) { }
        public void RemoveAllListeners() { }
        public void Invoke() { }
    }

    public abstract class UnityEvent<T0> : UnityEventBase
    {
        public void AddListener(UnityAction<T0> call) { }
        public void RemoveListener(UnityAction<T0> call) { }
        public void RemoveAllListeners() { }
        public void Invoke(T0 a) { }
    }

    public abstract class UnityEvent<T0, T1> : UnityEventBase
    {
        public void AddListener(UnityAction<T0, T1> call) { }
        public void RemoveListener(UnityAction<T0, T1> call) { }
        public void RemoveAllListeners() { }
        public void Invoke(T0 a, T1 b) { }
    }

    public abstract class UnityEvent<T0, T1, T2> : UnityEventBase
    {
        public void AddListener(UnityAction<T0, T1, T2> call) { }
        public void RemoveListener(UnityAction<T0, T1, T2> call) { }
        public void RemoveAllListeners() { }
        public void Invoke(T0 a, T1 b, T2 c) { }
    }

    public abstract class UnityEvent<T0, T1, T2, T3> : UnityEventBase
    {
        public void AddListener(UnityAction<T0, T1, T2, T3> call) { }
        public void RemoveListener(UnityAction<T0, T1, T2, T3> call) { }
        public void RemoveAllListeners() { }
        public void Invoke(T0 a, T1 b, T2 c, T3 d) { }
    }

    public delegate void UnityAction();
    public delegate void UnityAction<T0>(T0 a);
    public delegate void UnityAction<T0, T1>(T0 a, T1 b);
    public delegate void UnityAction<T0, T1, T2>(T0 a, T1 b, T2 c);
    public delegate void UnityAction<T0, T1, T2, T3>(T0 a, T1 b, T2 c, T3 d);

    public class UnityEventBase { public override string ToString() => "()"; }
}

namespace UnityEngine.EventSystems
{
    public interface IEventSystemHandler { }

    public interface IPointerEnterHandler : IEventSystemHandler { void OnPointerEnter(PointerEventData d); }
    public interface IPointerExitHandler : IEventSystemHandler { void OnPointerExit(PointerEventData d); }
    public interface IPointerDownHandler : IEventSystemHandler { void OnPointerDown(PointerEventData d); }
    public interface IPointerUpHandler : IEventSystemHandler { void OnPointerUp(PointerEventData d); }
    public interface IPointerClickHandler : IEventSystemHandler { void OnPointerClick(PointerEventData d); }
    public interface IBeginDragHandler : IEventSystemHandler { void OnBeginDrag(PointerEventData d); }
    public interface IDragHandler : IEventSystemHandler { void OnDrag(PointerEventData d); }
    public interface IEndDragHandler : IEventSystemHandler { void OnEndDrag(PointerEventData d); }
    public interface IScrollHandler : IEventSystemHandler { void OnScroll(PointerEventData d); }
    public interface IMoveHandler : IEventSystemHandler { void OnMove(AxisEventData d); }
    public interface ISubmitHandler : IEventSystemHandler { void OnSubmit(BaseEventData d); }
    public interface ICancelHandler : IEventSystemHandler { void OnCancel(BaseEventData d); }
    public interface ISelectHandler : IEventSystemHandler { void OnSelect(BaseEventData d); }
    public interface IDeselectHandler : IEventSystemHandler { void OnDeselect(BaseEventData d); }
    public interface IUpdateSelectedHandler : IEventSystemHandler { void OnUpdateSelected(BaseEventData d); }
    public interface IInitializePotentialDragHandler : IEventSystemHandler { void OnInitializePotentialDrag(PointerEventData d); }

    public abstract class UIBehaviour : UnityEngine.MonoBehaviour { }

    public abstract class BaseInputModule : UIBehaviour
    {
        public BaseInput input => null;
        public bool IsModuleSupported() => true;
        public bool ShouldActivateModule() => true;
        public void Process() { }
        public bool SendUpdateEventToSelectedObject() => false;
    }

    public class PointerInputModule : BaseInputModule
    {
        public class ButtonState
        {
            public PointerEventData.InputButton button;
            public PointerEventData eventData;
        }
        public class MouseState
        {
            public List<ButtonState> GetButtonStates() => new List<ButtonState>();
        }
        public class MouseButtonEventData { public PointerEventData buttonData; public bool buttonState => false; }
    }

    public class BaseInput
    {
        public Vector2 mousePosition => Vector2.zero;
        public bool GetMouseButtonDown(int b) => false;
        public bool GetMouseButtonUp(int b) => false;
        public bool GetMouseButton(int b) => false;
        public float GetAxisRaw(string a) => 0f;
        public bool GetButtonDown(string b) => false;
    }

    public class PointerEventData
    {
        public GameObject pointerEnter { get; set; }
        public GameObject pointerPress { get; set; }
        public GameObject pointerDrag { get; set; }
        public GameObject rawPointerPress { get; set; }
        public GameObject lastPress { get; set; }
        public Vector2 position { get; set; }
        public Vector2 delta { get; set; }
        public Vector2 pressPosition { get; set; }
        public Vector2 scrollDelta { get; set; }
        public RaycastResult pointerCurrentRaycast { get; set; }
        public RaycastResult pointerPressRaycast { get; set; }
        public List<RaycastResult> hovered { get; } = new List<RaycastResult>();
        public bool eligibleForClick { get; set; }
        public bool dragging { get; set; }
        public bool used { get; set; }
        public bool useDragThreshold { get; set; } = true;
        public int clickCount { get; set; }
        public float clickTime { get; set; }
        public int pointerId { get; set; } = -1;
        public InputButton button { get; set; }
        public Camera enterEventCamera { get; set; }
        public Camera pressEventCamera { get; set; }
        public enum InputButton { Left = 0, Right = 1, Middle = 2 }
    }

    public class AxisEventData : BaseEventData
    {
        public Vector2 moveVector { get; set; }
        public MoveDirection moveDir { get; set; }
    }

    public enum MoveDirection { Left, Right, Up, Down, None }

    public class BaseEventData
    {
        public EventSystem currentInputModule => null;
        public GameObject selectedObject { get; set; }
        public bool used { get; set; }
        public void Reset() { }
        public void Use() { }
    }

    public struct RaycastResult
    {
        public GameObject gameObject { get; set; }
        public bool isVaild => gameObject != null;
        public BaseRaycaster module { get; set; }
        public float distance { get; set; }
        public int index { get; set; }
        public int depth { get; set; }
        public int sortingLayer { get; set; }
        public int sortingOrder { get; set; }
        public Vector3 worldPosition { get; set; }
        public Vector3 screenPosition { get; set; }
        public int displayIndex { get; set; }
    }

    public abstract class BaseRaycaster : UIBehaviour
    {
        public abstract void Raycast(PointerEventData d, List<RaycastResult> r);
        public virtual Camera eventCamera => null;
        public int priority { get; set; }
        public int renderOrderPriority { get; set; }
        public int sortOrderPriority { get; set; }
    }

    public static class ExecuteEvents
    {
        public static T ValidateEventData<T>(BaseEventData d) where T : class, new()
        { var e = new T(); if (d is T t) e = t; return e; }
        public static bool Execute<T>(GameObject g, BaseEventData d, EventFunction<T> f) where T : IEventSystemHandler => false;
        public static GameObject GetEventHandler<T>(GameObject root) => null;
        public static bool CanHandleEvent<T>(GameObject go) => false;
        public static GameObject ExecuteHierarchy<T>(GameObject root, BaseEventData d, EventFunction<T> f) where T : IEventSystemHandler => null;
    }

    public delegate void EventFunction<T>(T handler, BaseEventData data);

    public class EventSystem : UIBehaviour
    {
        public static EventSystem current => null;
        public GameObject firstSelectedGameObject { get; set; }
        public GameObject currentSelectedGameObject { get; set; }
        public GameObject lastSelectedGameObject { get; set; }
        public bool sendNavigationEvents { get; set; } = true;
        public int pixelDragThreshold { get; set; } = 5;
        public BaseInputModule currentInputModule => null;
        public void SetSelectedGameObject(GameObject g) { }
        public void SetSelectedGameObject(GameObject g, BaseEventData d) { }
        public void RaycastAll(PointerEventData d, List<RaycastResult> r) { }
        public bool IsPointerOverGameObject() => false;
        public bool IsPointerOverGameObject(int id) => false;
        public bool alreadySelecting { get; set; }
        public void UpdateModules() { }
        public void TickModules() { }
        public void OnApplicationFocus(bool f) { }
    }

    public class StandaloneInputModule : PointerInputModule
    {
        public string horizontalAxis = "Horizontal";
        public string verticalAxis = "Vertical";
        public string submitButton = "Submit";
        public string cancelButton = "Cancel";
        public float inputActionsPerSecond { get; set; } = 10f;
        public float repeatDelay { get; set; } = 0.5f;
        public bool forceModuleActive { get; set; }
    }
}
