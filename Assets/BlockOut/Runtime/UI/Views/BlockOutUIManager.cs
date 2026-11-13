using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;

[assembly: System.Runtime.CompilerServices.InternalsVisibleTo("BlockOut.Editor")]

namespace BlockOut.UI
{
    /// <summary>Screen identifiers（保留历史枚举；未构建的屏幕不显示）。</summary>
    public enum BlockOutScreenId
    {
        Splash,
        Loading,
        Home,
        WorldMap,
        LevelSelect,
        Board,
        Gesture,
        Settlement,
        Collection,
        Revive,
        Store,
        Boosters,
        Leaderboard,
        Daily,
        Season,
        Achievements,
        Settings,
        Account,
        About,
        Support,
        Empty,
        Error,
        Coachmark,
        Onboarding,
        Privacy,
        Subscription
    }

    /// <summary>工具槽引用（控制器据此刷新三态）。</summary>
    [System.Serializable]
    public sealed class ToolSlotRefs
    {
        public Button Button;
        public Image Icon;
        public Text CountText;
        public GameObject CountBadge;
        public GameObject LockBadge;
        public Text NameText;
        public Text CondText;
        public RectTransform Rect;
    }

    /// <summary>商店商品卡引用（控制器据此刷新四态：可购买/未解锁/金币不足/购买中/成功/失败）。</summary>
    [System.Serializable]
    public sealed class StoreProductRefs
    {
        public BlockOutToolId Tool;
        public GameObject CardRoot;
        public Image CardImg;
        public Image IconImg;
        public GameObject LockBadge;
        public Text NameText;
        public Text DescText;
        public Text CoinText;
        public Button BuyBtn;
        public Text BuyText;
    }

    /// <summary>
    /// Prefab 驱动的页面引用与导航管理器。
    /// Build() 实例化页面与弹窗资源并绑定序列化引用；固定界面生成配方仅用于编辑器。
    /// </summary>
    public sealed partial class BlockOutUIManager : MonoBehaviour
    {
        private Coroutine shakeRoutine;
        private Coroutine toastRoutine;
        private RectTransform shakingSlot;
        private Vector2 shakingOrigin;
        private readonly Dictionary<string,RectTransform> safeRoots=new Dictionary<string,RectTransform>();
        internal GameObject ScreenRoot(BlockOutScreenId id) => GetScreenGO(id);
        internal GameObject LayerRoot(string name) => layers.TryGetValue(name,out var go) ? go : null;
        private Canvas canvas;
        private readonly Dictionary<BlockOutScreenId, GameObject> screens = new Dictionary<BlockOutScreenId, GameObject>();
        private readonly Dictionary<string, GameObject> layers = new Dictionary<string, GameObject>();
        private BlockOutScreenId currentScreen;

        // ---------- 参考图 1:1 还原层 ----------
        private static readonly Dictionary<BlockOutScreenId, string> ScreenSkinMap =
            new Dictionary<BlockOutScreenId, string>
            {
                { BlockOutScreenId.Loading,    "s1" },
                { BlockOutScreenId.Board,      "s4" },
                { BlockOutScreenId.Store,      "s7" },
            };
        private static readonly Dictionary<string, string> LayerSkinMap =
            new Dictionary<string, string>
            {
                { "SettlementLayer", "s5" },
                { "FailLayer",       "s6" },
            };
        private readonly Dictionary<string, BlockOutReferenceSkin> referenceSkins =
            new Dictionary<string, BlockOutReferenceSkin>();
        private float nextSkinSync;
        // s8 每日 / s9 地图在现有业务 Prefab 里没有对应页面，按需打开的独立还原页
        private GameObject standaloneReferenceSkin;
        private BlockOutLayoutMetrics metrics;
        /// <summary>当前布局度量（安全区 + 断点 + 组件尺寸），供控制器换算封面容器尺寸等。</summary>
        public BlockOutLayoutMetrics Metrics => metrics;

        /// <summary>棋盘视图（Bootstrapper 创建后赋值；布局变化时据此重建，避免运行时查找）。</summary>
        public BlockOut.Gameplay.BlockOutBoardView BoardView;

        private RectTransform toastRect;
        private Text toastText;
        private float toastBottomOffset = 90f;

        public event Action<BlockOutScreenId> OnScreenChanged;
        public event Action OnToastShown;
        public event Action OnLayersChanged;
        private readonly Dictionary<string,int> layerVersions=new Dictionary<string,int>();

        // ---------- Home refs ----------
        public Button HomeCtaButton;
        public Text HomeCtaTitle;
        public Text HomeCtaSub;
        public Button HomeCtaSecondary;
        public Text HomeCoinText;
        public Text HomePieceBadge;
        public Text HomeChapterTitle;
        public Text HomePieceText;
        public Image HomeProgressFill;
        public Image[] HomeNodes;
        public Button HomeCollectionLink;
        public Button HomeSettingsBtn;
        public Image[] HomeRegionArts;
        public GameObject[] HomeRegionLocks;
        public GameObject HomeFailBox;
        public Button HomeRetryBtn;
        public Text HomeRetryExhausted;
        public GameObject HomePlaceholderTag;
        public RectTransform HomePreviewCard;
        public RectTransform HomeArtViewport;
        public Button NavHomeBtn;
        public Button NavCollectionBtn;
        public Button NavStoreBtn;

        // ---------- Board refs ----------
        public Button BoardPauseBtn;
        public Text BoardLevelTitle;
        public Text BoardLevelSub;
        public Image[] BoardHearts;
        public RectTransform BoardTimerPill;
        public Text BoardTimerText;
        public Text BoardRemainingText;
        public Text BoardHintPill;
        public ToolSlotRefs HintSlot = new ToolSlotRefs();
        public ToolSlotRefs HammerSlot = new ToolSlotRefs();
        public ToolSlotRefs MagicSlot = new ToolSlotRefs();

        // ---------- Layer refs ----------
        public Button PauseResumeBtn;
        public Button PauseRestartBtn;
        public Button PauseQuitBtn;
        public Button PauseSettingsBtn;

        public Text FailReasonText;
        public Text FailReviveLabel;
        public Text FailReviveNote;
        public Text FailExhaustedNote;
        public Button FailReviveBtn;
        public Button FailRestartBtn;
        public Button FailQuitBtn;
        public GameObject FailFreeBadge;

        public Text ConfirmTitle;
        public Text ConfirmBody;
        public Button ConfirmCancelBtn;
        public Button ConfirmOkBtn;

        public Text SettlePieceText;
        public Text SettleRewardText;
        public Button SettleNextBtn;
        public Button SettleReplayBtn;
        public Button SettleHomeBtn;
        public Text SettleTitleText;
        public Button SettleCollectionBtn;

        /// <summary>结算层拼片揭晓图：4×3 区域网格（13/17 首次/重复/章末揭晓；正式素材缺失时同结构占位）。</summary>
        public RectTransform SettleRevealRoot;
        public Image[] SettleRevealRegions;
        /// <summary>R11：单关通关图片（该关关联插画）；普通通关即展示，章末仍走章节拼片网格。默认隐藏。</summary>
        public Image SettleLevelImage;
        /// <summary>结算层说明（章末/首次/重复的差异文案）。</summary>
        public Text SettleNoteText;

        /// <summary>收藏页加载失败重试条（P2-10）。</summary>
        public RectTransform CollectionRetryBar;
        public Button CollectionRetryBtn;
        public Text CollectionRetryText;

        public Button SettingsCloseBtn;
        public Button SettingsMusicSwitch;
        public Button SettingsSoundSwitch;
        public Button SettingsVibSwitch;
        /// <summary>设置页"关于"入口（16 稿）。</summary>
        public Button SettingsAboutBtn;
        /// <summary>关于弹层关闭键。</summary>
        public Button AboutCloseBtn;

        // ---------- Collection refs ----------
        public Button CollectionBackBtn;
        public Text CollectionCoinText;
        public Text CollectionChapterText;
        public Text CollectionPieceText;
        public Text CollectionEmptyText;
        public Image CollectionProgressFill;
        public RectTransform CollectionThumbRoot;
        public Image[] CollectionThumbRegions;
        public Button CollectionViewBigBtn;
        public GameObject CollectionBigLayer;
        public RectTransform CollectionBigRoot;
        public Image[] CollectionBigRegions;
        public Button CollectionBigCloseBtn;
        public RectTransform CollectionChapterList;
        public RectTransform CollectionContent;
        public ScrollRect collectionScroll;
        public BlockOutPinchZoom CollectionZoom;
        public RectTransform bigCard;
        public RectTransform CollectionRepeatGrid;

        // ---------- Store refs ----------
        public Button StoreBackBtn;
        public Text StoreCoinText;
        public StoreProductRefs[] StoreProducts;
        public Button StoreNavHomeBtn;
        public Button StoreNavCollectionBtn;
        public Button StoreNavStoreBtn;
        public Button CollectionNavHomeBtn;
        public Button CollectionNavCollectionBtn;
        public Button CollectionNavStoreBtn;

        // ---------- Guide (新手引导教学界面) ----------
        public GameObject GuideLayer;
        public Text GuideBodyText;
        public Button GuideDismissBtn;

        public RectTransform BoardArea;
        public BlockOutChapterItemView ChapterItemPrefab;
        public BlockOutRepeatItemView RepeatItemPrefab;
        public RectTransform RepeatListRoot;
        public BlockOutStoreItemView[] StoreItemPrefabs;
        public RectTransform StoreListRoot;
        public UnityEngine.UI.Text StoreEmptyText;
        private GameObject canvasGo;
        private void BuildCanvas()
        {
            canvasGo = new GameObject("BlockOutCanvas",
                typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster),
                typeof(BlockOutLayoutMetrics));
            canvasGo.transform.SetParent(transform, false);
            canvas = canvasGo.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(390, 844);
            scaler.matchWidthOrHeight = 0f; // 固定390设计宽；断点按画布高度判断，与物理像素密度无关。

            // 页面背景：奶油顶 → 奶油深底（竖向渐变贴图拉伸）
            var bg = BlockOutWidgets.Panel(canvasGo.transform, "BG", BlockOutDesignTokens.BgCream);
            bg.sprite=BlockOutIconFactory.Asset("background");
            bg.color=Color.white;
            bg.type = Image.Type.Simple;
        }
        private void BuildToast()
        {
            var go = new GameObject("Toast", typeof(RectTransform));
            go.transform.SetParent(canvasGo.transform, false);
            toastRect = BlockOutWidgets.ToastBar(go.transform, "ToastBar");
            toastText = toastRect.Find("Text").GetComponent<Text>();
            toastRect.gameObject.SetActive(false);
        }
        public void ShakeSlot(BlockOutToolId tool)
        {
            var slot=tool==BlockOutToolId.Hint ? HintSlot : tool==BlockOutToolId.Hammer ? HammerSlot:MagicSlot;
            if(slot==null || slot.Button==null)return;
            var feedback=slot.Button.GetComponent<BlockOutUIFeedback>();
            if(feedback!=null)feedback.Play("ToolLocked");
        }
        private System.Collections.IEnumerator ShakeRoutine(RectTransform rt)
        {
            Vector2 origin = rt.anchoredPosition;
            const float dur = 0.28f;
            float t = 0f;
            while (t < dur)
            {
                float p = Mathf.Clamp01(t / dur);
                // 阻尼衰减抖动：左右各 5pt 起手快速衰减
                float amp = 5f * (1f - p) * (1f - p);
                float dx = Mathf.Sin(p * Mathf.PI * 2f * 3f) * amp;
                rt.anchoredPosition = origin + new Vector2(dx, 0f);
                t += Time.unscaledDeltaTime;
                yield return null;
            }
            rt.anchoredPosition = origin;
            shakeRoutine = null;
        }
        public void LayoutArtwork(RectTransform viewport, bool contain)
        {
            if (viewport == null) return;
            var artwork = viewport.Find("Artwork") as RectTransform;
            if (artwork == null) return;
            float side = contain ? Mathf.Min(viewport.rect.width, viewport.rect.height)
                                 : Mathf.Max(viewport.rect.width, viewport.rect.height);
            BlockOutWidgets.ApplyAnchor(artwork, UIAnchorPreset.MiddleCenter);
            artwork.anchoredPosition = Vector2.zero;
            artwork.sizeDelta = new Vector2(side, side);
            for (int i = 0; i < 12; i++)
                SetTopLeft(artwork, "Region_" + i, i % 4 * side / 4f, i / 4 * side / 3f, side / 4f, side / 3f);
        }
        private void ApplySafeArea(RectTransform rt)
        {
            if (rt == null || metrics == null) return;
            float w = metrics.CanvasWidth, h = metrics.CanvasHeight;
            float l = Mathf.Min(metrics.SafeLeft, w * 0.25f);
            float r = Mathf.Min(metrics.SafeRight, w * 0.25f);
            float t = Mathf.Min(metrics.SafeTop, h * 0.25f);
            float b = Mathf.Min(metrics.SafeBottom, h * 0.25f);
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.offsetMin = new Vector2(l, b);
            rt.offsetMax = new Vector2(-r, -t);
        }



        // ============================================================
        // 首页（06 / 07）
        // ============================================================



        // ============================================================
        // 游戏页（04 / 05）
        // ============================================================










        // ============================================================
        // 布局（安全区 + 断点）
        // ============================================================

        public void Build()
        {
            if(canvas!=null) return;
            BlockOutWidgets.EnsureReady();
            BuildCanvas();
            try
            {
                foreach(var id in BlockOutUIPrefabRegistry.DeliveredScreens())
                {
                    var prefab=BlockOutUIPrefabRegistry.Load(id);
                    RequireView(prefab,BlockOutUIPrefabRegistry.ViewTypeForScreen(id));
                    var go=Instantiate(prefab,canvasGo.transform,false);
                    go.GetComponent<BlockOutUIViewBase>().ApplyTo(this);
                    screens[id]=go; go.SetActive(false);
                }
                foreach(var key in new[]{"PauseLayer","FailLayer","ConfirmLayer","SettlementLayer","SettingsLayer","AboutLayer","GuideLayer"})
                {
                    var prefab=BlockOutUIPrefabRegistry.LoadLayer(key);
                    RequireView(prefab,BlockOutUIPrefabRegistry.ViewTypeForLayer(key));
                    var go=Instantiate(prefab,canvasGo.transform,false);
                    go.GetComponent<BlockOutUIViewBase>().ApplyTo(this);
                    layers[key]=go; go.SetActive(false);
                }
                AttachReferenceSkins();
                BuildDynamicLists(); BuildToast();
                metrics=canvasGo.GetComponent<BlockOutLayoutMetrics>();
                metrics.Attach(canvasGo.GetComponent<RectTransform>());
                metrics.Changed+=Relayout;
                Relayout(); ShowScreen(BlockOutScreenId.Loading);
            }
            catch { canvasGo.SetActive(false); throw; }
        }
        private static void RequireView(GameObject prefab,Type expected)
        {
            if(prefab==null || expected==null) throw new InvalidOperationException("缺少 UI Prefab 或 View 类型");
            var view=prefab.GetComponent(expected) as BlockOutUIViewBase;
            if(view==null) throw new InvalidOperationException(prefab.name+" 缺少 "+expected.Name);
            string error;
            if(!view.ValidateReferences(out error)) throw new InvalidOperationException(prefab.name+": "+error);
        }
        private void OnDestroy() { if(metrics!=null) metrics.Changed-=Relayout; }
        public void Relayout()
        {
            if(canvasGo==null) return;
            foreach(var layout in canvasGo.GetComponentsInChildren<BlockOutPageLayout>(true)) layout.Apply();
        }

        // ============================================================
        // 参考图 1:1 还原层：默认接线 / 热区转发 / 动态字段镜像
        // 视觉层置顶覆盖业务页面，但所有元件 raycastTarget=0，
        // 点击由 Hotspot_* 透明热区转发到业务 Button，业务绑定一行不改。
        // ============================================================

        private static readonly HashSet<string> ScreenSkinIds = new HashSet<string>(ScreenSkinMap.Values);

        private void AttachReferenceSkins()
        {
            // screen 类插在最后一个页面之后、所有弹层之前：盖住页面，不盖弹层
            int insertAt = 0;
            foreach (var s in screens.Values)
                if (s != null) insertAt = Mathf.Max(insertAt, s.transform.GetSiblingIndex() + 1);

            foreach (var kv in ScreenSkinMap)
            {
                var go = BlockOutUIPrefabRegistry.AttachReferenceSkin(kv.Value, canvasGo.transform);
                if (go == null)
                {
                    Debug.LogWarning("[BlockOut][UI] 还原层资源缺失: " + kv.Value);
                    continue;
                }
                go.transform.SetSiblingIndex(insertAt++);
                var skin = go.GetComponent<BlockOutReferenceSkin>();
                if (skin != null)
                {
                    referenceSkins[kv.Value] = skin;
                    BindSkinHotspots(kv.Value, skin);
                }
                go.SetActive(false);
            }
            // layer 类挂在对应弹层内，随 ShowLayer / HideLayer 自动开关
            foreach (var kv in LayerSkinMap)
            {
                GameObject layer;
                if (!layers.TryGetValue(kv.Key, out layer) || layer == null) continue;
                var go = BlockOutUIPrefabRegistry.AttachReferenceSkin(kv.Value, layer.transform);
                if (go == null) continue;
                var skin = go.GetComponent<BlockOutReferenceSkin>();
                if (skin != null)
                {
                    referenceSkins[kv.Value] = skin;
                    BindSkinHotspots(kv.Value, skin);
                }
            }
            SyncReferenceSkins();
        }

        private void BindSkinHotspots(string sid, BlockOutReferenceSkin skin)
        {
            switch (sid)
            {
                case "s2":
                    skin.Bind("HomeCtaButton", HomeCtaButton);
                    skin.Bind("HomeSettingsBtn", HomeSettingsBtn);
                    skin.Bind("HomeCollectionLink", HomeCollectionLink);
                    skin.Bind("NavStoreBtn", NavStoreBtn);
                    break;
                case "s3":
                    skin.Bind("CollectionBackBtn", CollectionBackBtn);
                    break;
                case "s4":
                    skin.Bind("BoardPauseBtn", BoardPauseBtn);
                    if (HintSlot != null) skin.Bind("HintSlot.Button", HintSlot.Button);
                    if (HammerSlot != null) skin.Bind("HammerSlot.Button", HammerSlot.Button);
                    if (MagicSlot != null) skin.Bind("MagicSlot.Button", MagicSlot.Button);
                    break;
                case "s5":
                    skin.Bind("SettleNextBtn", SettleNextBtn);
                    skin.Bind("SettleHomeBtn", SettleHomeBtn);
                    break;
                case "s6":
                    skin.Bind("FailReviveBtn", FailReviveBtn);
                    skin.Bind("FailRestartBtn", FailRestartBtn);
                    skin.Bind("FailQuitBtn", FailQuitBtn);
                    break;
            }
        }

        /// <summary>把业务层真实数值镜像到还原层 Text，避免切图里烧死的静态数字。</summary>
        private void SyncReferenceSkins()
        {
            BlockOutReferenceSkin s;
            if (referenceSkins.TryGetValue("s2", out s) && s != null && HomeCoinText != null)
                s.SetText("coins", HomeCoinText.text);

            if (referenceSkins.TryGetValue("s4", out s) && s != null)
            {
                if (BoardLevelTitle != null) s.SetText("level", ShortLevel(BoardLevelTitle.text));
                if (HintSlot != null && HintSlot.CountText != null)
                    s.SetText("hint_count", Digits(HintSlot.CountText.text));
                if (HammerSlot != null && HammerSlot.CountText != null)
                    s.SetText("hammer_count", Digits(HammerSlot.CountText.text));
                if (MagicSlot != null && MagicSlot.CountText != null)
                    s.SetText("bomb_count", Digits(MagicSlot.CountText.text));
                if (BoardHearts != null)
                {
                    int lives = 0;
                    for (int i = 0; i < BoardHearts.Length; i++)
                        if (BoardHearts[i] != null && BoardHearts[i].sprite != null &&
                            BoardHearts[i].sprite.name == "heart") lives++;
                    s.SetHearts(lives);
                }
                s.BindInteractable("HintSlot.Button", HintSlot != null && HintSlot.Button != null && HintSlot.Button.interactable);
                s.BindInteractable("HammerSlot.Button", HammerSlot != null && HammerSlot.Button != null && HammerSlot.Button.interactable);
                s.BindInteractable("MagicSlot.Button", MagicSlot != null && MagicSlot.Button != null && MagicSlot.Button.interactable);
            }
        }

        private static string ShortLevel(string s)
        {
            if (string.IsNullOrEmpty(s)) return null;
            int i = s.LastIndexOf(" · ", StringComparison.Ordinal);
            return i >= 0 ? s.Substring(i + 3) : s;
        }

        private static string Digits(string s)
        {
            if (string.IsNullOrEmpty(s)) return null;
            var sb = new System.Text.StringBuilder();
            foreach (var c in s) if (c >= '0' && c <= '9') sb.Append(c);
            return sb.Length > 0 ? sb.ToString() : null;
        }

        private void LateUpdate()
        {
            if (referenceSkins.Count == 0) return;
            if (Time.unscaledTime < nextSkinSync) return;
            nextSkinSync = Time.unscaledTime + 0.1f;
            SyncReferenceSkins();
        }

        private bool settlementContain;
        public void SetSettlementArtworkMode(bool contain)
        {
            settlementContain = contain;
            LayoutArtwork(SettleRevealRoot, contain);
        }



        // ---- 布局辅助 ----

        private RectTransform SetTopLeft(Transform parent, string name, float x, float y, float w, float h)
        {
            var rt = parent != null ? parent.Find(name) as RectTransform : null;
            if (rt == null) return null;
            BlockOutWidgets.ApplyAnchor(rt, UIAnchorPreset.TopLeft);
            rt.anchoredPosition = new Vector2(x, -y);
            rt.sizeDelta = new Vector2(w, h);
            return rt;
        }

        private RectTransform SetTopRight(Transform parent, string name, float x, float y, float w, float h)
        {
            var rt = parent != null ? parent.Find(name) as RectTransform : null;
            if (rt == null) return null;
            BlockOutWidgets.ApplyAnchor(rt, UIAnchorPreset.TopRight);
            rt.anchoredPosition = new Vector2(-x, -y);
            rt.sizeDelta = new Vector2(w, h);
            return rt;
        }

        private RectTransform SetTopCenter(Transform parent, string name, float x, float y, float w, float h)
        {
            var rt = parent != null ? parent.Find(name) as RectTransform : null;
            if (rt == null) return null;
            BlockOutWidgets.ApplyAnchor(rt, UIAnchorPreset.TopCenter);
            rt.anchoredPosition = new Vector2(x, -y);
            rt.sizeDelta = new Vector2(w, h);
            return rt;
        }

        private RectTransform SetBottomLeft(Transform parent, string name, float x, float y, float w, float h)
        {
            var rt = parent != null ? parent.Find(name) as RectTransform : null;
            if (rt == null) return null;
            BlockOutWidgets.ApplyAnchor(rt, UIAnchorPreset.BottomLeft);
            rt.anchoredPosition = new Vector2(x, y);
            rt.sizeDelta = new Vector2(w, h);
            return rt;
        }

        // ============================================================
        // 屏幕 / 弹层 / Toast
        // ============================================================

        public void ShowScreen(BlockOutScreenId id)
        {
            HideReferenceStandalone();
            foreach (var kv in screens)
                if (kv.Value != null) kv.Value.SetActive(kv.Key == id);
            string wantSkin;
            ScreenSkinMap.TryGetValue(id, out wantSkin);
            foreach (var kv in referenceSkins)
                if (ScreenSkinIds.Contains(kv.Key) && kv.Value != null)
                    kv.Value.gameObject.SetActive(kv.Key == wantSkin);
            if (id == BlockOutScreenId.Board) HideAllBoardLayers();
            currentScreen = id;
            SyncReferenceSkins();
            // Toast 位置：游戏页位于工具条上方，其余页面位于底部导航上方
            SetToastBottomOffset(id == BlockOutScreenId.Board ? 116f : 90f);
            if (OnScreenChanged != null) OnScreenChanged(id);
        }

        public BlockOutScreenId CurrentScreen => currentScreen;

        /// <summary>
        /// 打开独立还原页（s8 每日挑战 / s9 章节地图）。这两屏在现有业务 Prefab 中
        /// 没有对应页面，故不进 ScreenSkinMap，改为显式按需挂载到当前 Canvas 并置顶；
        /// 不切换业务页面，关闭后回到原界面。切屏时自动关闭。
        /// </summary>
        public bool ShowReferenceStandalone(string screenId)
        {
            if (canvasGo == null) return false;
            if (screenId != "s8" && screenId != "s9") return false;
            HideReferenceStandalone();
            var go = BlockOutUIPrefabRegistry.AttachReferenceSkin(screenId, canvasGo.transform);
            if (go == null) return false;
            go.transform.SetAsLastSibling();
            standaloneReferenceSkin = go;
            return true;
        }

        public void HideReferenceStandalone()
        {
            if (standaloneReferenceSkin == null) return;
            UnityEngine.Object.Destroy(standaloneReferenceSkin);
            standaloneReferenceSkin = null;
        }

        public bool HasStandaloneReferenceSkin => standaloneReferenceSkin != null;

        /// <summary>
        /// 业务侧覆盖还原层任意动态字段。progress / reward / ticket 在设计稿里是
        /// 示例值（60% / +60 / 3），按 1:1 还原口径默认保留原图数值；业务若拿到
        /// 真实数据，调用本方法即可覆盖，不必改 Prefab 或切图。
        /// </summary>
        public void SetReferenceText(string key, string value)
        {
            if (string.IsNullOrEmpty(key)) return;
            foreach (var kv in referenceSkins)
                if (kv.Value != null) kv.Value.SetText(key, value);
        }

        /// <summary>按枚举取屏幕 GameObject（控制器据此定位动态构建的子节点，如章节行）。</summary>
        public GameObject GetScreenGO(BlockOutScreenId id)
        {
            GameObject g;
            return screens.TryGetValue(id, out g) ? g : null;
        }

        public void HideAllBoardLayers()
        {
            foreach(var name in new[]{"PauseLayer","FailLayer","ConfirmLayer","SettlementLayer","GuideLayer"})HideLayerImmediately(name);
        }

        public void SetLayerActive(string name,bool active)
        {
            GameObject layer;
            if(!layers.TryGetValue(name,out layer) || layer==null)return;
            int version=layerVersions.TryGetValue(name,out var previous) ? previous+1:1;
            layerVersions[name]=version;
            if(active)
            {
                layer.SetActive(true);
                var feedback=FindPopupFeedback(layer);
                if(feedback!=null && feedback.Popup)feedback.Play("PopupOpen");
                OnLayersChanged?.Invoke();return;
            }
            var popup=FindPopupFeedback(layer);
            if(!layer.activeSelf || popup==null) { layer.SetActive(false);OnLayersChanged?.Invoke();return; }
            popup.Close(()=> { if(layerVersions[name]!=version)return;layer.SetActive(false);OnLayersChanged?.Invoke(); });
        }
        private static BlockOutUIFeedback FindPopupFeedback(GameObject layer)
        {
            foreach(var feedback in layer.GetComponentsInChildren<BlockOutUIFeedback>(true))if(feedback.Popup)return feedback;
            return null;
        }
        public void HideLayerImmediately(string name)
        {
            if(!layers.TryGetValue(name,out var layer) || layer==null)return;
            layerVersions[name]=layerVersions.TryGetValue(name,out var version) ? version+1:1;
            layer.SetActive(false);OnLayersChanged?.Invoke();
        }

        public bool IsLayerActive(string name)
        {
            GameObject layer;
            return layers.TryGetValue(name, out layer) && layer != null && layer.activeSelf;
        }

        /// <summary>Toast 底部偏移（游戏页 = 工具条上方；其他页面 = 底部导航上方）。</summary>
        public void SetToastBottomOffset(float offset)
        {
            toastBottomOffset = offset;
            if (toastRect != null && metrics != null)
                toastRect.anchoredPosition = new Vector2(0, metrics.SafeBottom + toastBottomOffset);
        }

        public void ShowToast(string message, float duration = 2f)
        {
            if (toastText == null || toastRect == null) return;
            OnToastShown?.Invoke();
            toastText.text = message ?? string.Empty;
            toastRect.gameObject.SetActive(true);
            if(toastRoutine!=null) StopCoroutine(toastRoutine);
            toastRoutine=StartCoroutine(HideToastAfter(duration));
        }

        private IEnumerator HideToastAfter(float duration)
        {
            yield return new WaitForSeconds(duration);
            if (toastRect != null) toastRect.gameObject.SetActive(false);
        }

        public T GetScreenElement<T>(BlockOutScreenId screen, string childName) where T : Component
        {
            GameObject go;
            if (!screens.TryGetValue(screen, out go) || go == null) return null;
            var found = go.transform.Find(childName);
            return found != null ? found.GetComponent<T>() : null;
        }
    }
}
