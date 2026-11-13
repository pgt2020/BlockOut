using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using BlockOut.Core;

namespace BlockOut.Gameplay
{
    /// <summary>
    /// UGUI 棋盘视图（Docs/DesignSystem.md 04/05）：
    /// 按参考安全视野适配关卡，方块加载持久化木块素材；
    /// 正常箭头按方块颜色混色；提示闪绿；受阻箭头红色交替并挤压回弹；锤子复制木块后敲碎。
    /// 贴图由 BlockOutIconFactory 加载，固定反馈由 Animator 播放。
    /// </summary>
    public sealed class BlockOutBoardView : MonoBehaviour
    {
        private BlockOutBoardPresentation presentation;
        private BlockOutBoardEffects effects;
        public RectTransform MagicOrigin;
        public Transform EffectSurfaceParent;
        internal float CellHeight => cellSize*248f/240f;
        internal float ReferenceWorldScale => cellSize/(.86f*Mathf.Min(1.18f,7f/Mathf.Max(boardWidth,boardHeight)));
        internal BlockOutBoardEffects Effects
        {
            get { if(effects==null) { effects=gameObject.AddComponent<BlockOutBoardEffects>();effects.Initialize(this,fxRoot); } return effects; }
        }
        public void PlayHammerEffect(BlockOutBlockData block) { Effects.PlayHammer(GetBlockLocalPosition(block),block.Color,nodes.Find(n=>n!=null && n.TargetBlock==block)); }

        private BlockOutBoardPresentation Presentation => presentation ?? (presentation=new BlockOutBoardPresentation(this));
        internal BlockOutGameRules rules;
        internal int boardWidth, boardHeight;
        internal readonly List<BlockOutBlockNode> nodes = new List<BlockOutBlockNode>();
        internal readonly BlockOutInputLocks inputLocks = new BlockOutInputLocks();
        internal bool paused;
        internal bool hammerSelectMode;
        internal int runToken;
        internal int nextFlightId;
        internal readonly Dictionary<int, Action> flightCancellations = new Dictionary<int, Action>();
        internal bool rebuildPending;

        internal float cellSize = 62f;
        internal float originX, originY;
        /// <summary>参考世界单位 → Canvas 局部单位换算（§7.1）：
        /// 参考相机半高 5 对应整屏半高，unitScale = 整屏高度 / 10。
        /// 飞出速度/加速度/上限与视口外余量都乘该系数，保证相同归一化屏幕距离耗时一致。</summary>
        internal float unitScale = 70f;
        internal Transform blocksRoot;
        internal Transform fxRoot;
        internal Image boardBg;
        /// <summary>点击抑制截止时刻（§7.4：手势结束后至少 0.16s 抑制点击）。</summary>
        internal float tapSuppressUntil;
        /// <summary>入场协程引用（重开/切关时终止，不留下旧动画锁）。</summary>
        internal Coroutine entranceRoutine;
        internal RectTransform zoomRoot;            // R09：缩放根，与入场缩放相互独立
        internal Coroutine focusRoutine;            // R10：视口聚焦协程
        internal Vector2 focusSavedPos;
        internal float focusSavedScale;

        public event Action<BlockOutBlockData> OnBlockTapped;
        public event Action OnBoardBackgroundTapped;

        internal const float CellTexPx = 128f;   // 贴图基准：每格 128px
        internal const float RingPad = 4f;       // 状态环外扩

        public void Setup(BlockOutGameRules gameRules, int width, int height)
        {
            rules = gameRules;
            boardWidth = Mathf.Max(1, width);
            boardHeight = Mathf.Max(1, height);
            // 新局初始化统一重置本视图的全部运行态（P1-2）：
            // 仅重置 GM.IsPaused 不够，paused/inputLocked 是本视图私有字段，
            // 暂停层"重开本关"后若不清理，协程会永久卡在 while(paused)。
            inputLocks.Clear();
            paused = false;
            hammerSelectMode = false;
            CancelAnimations();
            EnsureRoots();
            GetZoomRoot();
            ResetZoom();
            Rebuild();
        }

        internal void EnsureRoots()
        {
            if (blocksRoot != null) return;
            var rt = (RectTransform)transform;
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;

            // R09：所有棋盘内容挂在 zoomRoot 之下，捏合缩放只作用于 zoomRoot，与入场缩放独立。
            var zrt = GetZoomRoot();

            var bgGo = new GameObject("BoardBg", typeof(RectTransform), typeof(Image), typeof(Button));
            bgGo.transform.SetParent(zrt, false);
            var bgRt = (RectTransform)bgGo.transform;
            bgRt.anchorMin = Vector2.zero;
            bgRt.anchorMax = Vector2.one;
            bgRt.offsetMin = Vector2.zero;
            bgRt.offsetMax = Vector2.zero;
            boardBg = bgGo.GetComponent<Image>();
            boardBg.raycastTarget = true; // 棋盘空白处点击 → 取消锤子选择态
            var bgBtn = bgGo.GetComponent<Button>();
            bgBtn.targetGraphic = boardBg;
            bgBtn.transition = Selectable.Transition.None;
            bgBtn.onClick.AddListener(() => { if (OnBoardBackgroundTapped != null) OnBoardBackgroundTapped(); });

            var blocksGo = new GameObject("Blocks", typeof(RectTransform));
            blocksGo.transform.SetParent(zrt, false);
            var bRt = (RectTransform)blocksGo.transform;
            bRt.anchorMin = Vector2.zero;
            bRt.anchorMax = Vector2.one;
            bRt.offsetMin = Vector2.zero;
            bRt.offsetMax = Vector2.zero;
            blocksRoot = blocksGo.transform;

            var fxGo = new GameObject("Fx", typeof(RectTransform));
            fxGo.transform.SetParent(zrt, false);
            var fRt = (RectTransform)fxGo.transform;
            fRt.anchorMin = Vector2.zero;
            fRt.anchorMax = Vector2.one;
            fRt.offsetMin = Vector2.zero;
            fRt.offsetMax = Vector2.zero;
            fxRoot = fxGo.transform;
        }

        /// <summary>按父矩形重建棋盘（父矩形保持正方形；分辨率变化时由布局层调用）。</summary>
        public void Rebuild()
        {
            // 同局尺寸变化等待飞出结算，避免停止回调后 GM 永久停在 ResolvingMove。
            if (flightCancellations.Count > 0) { rebuildPending = true; return; }
            rebuildPending = false;
            ClearNodes();
            if (rules == null) return;
            EnsureRoots();

            var rt = (RectTransform)transform;
            float side = Mathf.Min(rt.rect.width, rt.rect.height);
            if (side <= 1f) side = 354f; // 首帧布局未完成时的基准值（390-36）
            int cells = Mathf.Max(boardWidth, boardHeight);
            cellSize = Mathf.Min(rt.rect.width*.9f/Mathf.Max(9.5f,boardWidth),rt.rect.height/(boardHeight*248f/240f));
            if(cellSize<=0)cellSize=side/Mathf.Max(9.5f,cells);
            // 参考世界单位 → 局部单位（§7.1）：可见半高 / 参考相机半高
            var feel = BlockOut.Config.BlockOutGameplayConfig.Current.feel;
            float refHalf = feel != null && feel.referenceCameraHalfHeight > 0f ? feel.referenceCameraHalfHeight : 5f;
            var canvas=GetComponentInParent<Canvas>();
            float fullHeight=rt.rect.height;
            if(canvas!=null)
            {
                var canvasRect=(RectTransform)canvas.rootCanvas.transform;
                fullHeight=transform.parent.InverseTransformVector(canvasRect.TransformVector(Vector3.up*canvasRect.rect.height)).magnitude;
            }
            unitScale=fullHeight/(2*refHalf);

            float totalW = boardWidth * cellSize;
            float totalH = boardHeight * CellHeight;
            originX = -totalW * 0.5f + cellSize * 0.5f;
            originY = -totalH * 0.5f + CellHeight * 0.5f;

            if (boardBg != null)
            {
                boardBg.sprite = BlockOut.UI.BlockOutIconFactory.BoardSprite(boardWidth, boardHeight);
                boardBg.type=Image.Type.Sliced;boardBg.color=Color.clear;
            }

            var completion=GetComponent<BlockOutCompletionPresentation>() ?? gameObject.AddComponent<BlockOutCompletionPresentation>();
            completion.BuildDots(this);
            foreach (var block in rules.Blocks)
            {
                if (block == null || !block.Active) continue;
                nodes.Add(CreateBlockNode(block));
            }
        }

        public float MaximumZoom => Mathf.Max(1,((RectTransform)transform).rect.width/Mathf.Max(.01f,9.5f*cellSize));
        public float MinimumZoom => Mathf.Min(1,((RectTransform)transform).rect.width*.9f/Mathf.Max(.01f,Mathf.Max(boardWidth*50f/44f,15.2f)*cellSize));
        public Vector2 ClampPan(Vector2 position,float scale)
        {
            // ArtOut PanLimitRatio=.5: camera center may reach each edge of the board.
            float x=boardWidth*cellSize*scale*.5f;
            float y=boardHeight*CellHeight*scale*.5f;
            return new Vector2(Mathf.Clamp(position.x,-x,x),Mathf.Clamp(position.y,-y,y));
        }
        internal Vector2 CellPos(int col, int row)
        {
            return new Vector2(originX + col * cellSize, originY + row * CellHeight);
        }

        internal BlockOutBlockNode CreateBlockNode(BlockOutBlockData block)
        {
            int minCol = int.MaxValue, maxCol = int.MinValue, minRow = int.MaxValue, maxRow = int.MinValue;
            foreach (var c in block.GetOccupiedCells())
            {
                minCol = Mathf.Min(minCol, c.x); maxCol = Mathf.Max(maxCol, c.x);
                minRow = Mathf.Min(minRow, c.y); maxRow = Mathf.Max(maxRow, c.y);
            }
            int cols = maxCol - minCol + 1;
            int rows = maxRow - minRow + 1;

            var go = new GameObject("Block_" + block.RuntimeIndex, typeof(RectTransform));
            go.transform.SetParent(blocksRoot, false);
            var rt = (RectTransform)go.transform;
            Vector2 c0 = CellPos(minCol, minRow);
            Vector2 c1 = CellPos(maxCol, maxRow);
            rt.anchoredPosition = new Vector2((c0.x + c1.x) * 0.5f, (c0.y + c1.y) * 0.5f);
            rt.sizeDelta = new Vector2(cols * cellSize, rows * CellHeight);

            var bodyGo=new GameObject("Body",typeof(RectTransform),typeof(Image));bodyGo.transform.SetParent(go.transform,false);
            var bodyRect=(RectTransform)bodyGo.transform;
            bool sideways=(block.Rotation%2)!=0;
            bodyRect.sizeDelta=sideways ? new Vector2(rows*cellSize,cols*cellSize) : rt.sizeDelta;
            bodyRect.localRotation=Quaternion.Euler(0,0,-90*block.Rotation);
            var bg=bodyGo.GetComponent<Image>();
            bg.material=Resources.Load<Material>("ArtOutPresentation/Reference/Bundles/Shaders/Custom_PerfectTint");
            bg.raycastTarget = false;
            bg.sprite = BlockOut.UI.BlockOutIconFactory.BlockSprite(block, cols, rows, CellTexPx);
            bg.color=block.Color;
            bodyRect.sizeDelta=new Vector2(bg.sprite.rect.width,bg.sprite.rect.height)*(cellSize/240f);

            // 每占格一个透明点击区（异形空洞不可点）
            foreach (var cell in block.GetOccupiedCells())
            {
                var cellGo = new GameObject("Cell_" + cell.x + "_" + cell.y, typeof(RectTransform), typeof(Image));
                cellGo.transform.SetParent(go.transform, false);
                var crt = (RectTransform)cellGo.transform;
                crt.anchorMin = new Vector2(0.5f, 0.5f);
                crt.anchorMax = new Vector2(0.5f, 0.5f);
                crt.pivot = new Vector2(0.5f, 0.5f);
                crt.sizeDelta = new Vector2(cellSize, cellSize);
                crt.anchoredPosition = CellPos(cell.x, cell.y) - rt.anchoredPosition;
                var img = cellGo.GetComponent<Image>();
                img.color = Color.clear;
                img.raycastTarget = true;
            }

            // 箭头（白填充 + 可可描边）
            var arrowLocal = block.GetArrowCellLocal();
            var arrowGlobal = new Vector2Int(block.Column + arrowLocal.x, block.Row + arrowLocal.y);
            var arrowGo = new GameObject("Arrow", typeof(RectTransform), typeof(Image));
            arrowGo.transform.SetParent(go.transform, false);
            var art = (RectTransform)arrowGo.transform;
            art.anchorMin = new Vector2(0.5f, 0.5f);
            art.anchorMax = new Vector2(0.5f, 0.5f);
            art.sizeDelta = new Vector2(cellSize * (.58f/.86f), cellSize * (.58f/.86f));
            art.anchoredPosition = CellPos(arrowGlobal.x, arrowGlobal.y) - rt.anchoredPosition;
            var arrowImg = arrowGo.GetComponent<Image>();
            arrowImg.raycastTarget = false;
            arrowImg.sprite = BlockOut.UI.BlockOutIconFactory.Arrow(block.Direction);

            // 状态环（提示/受阻/锤子，默认隐藏）
            var ringGo = new GameObject("StateRing", typeof(RectTransform), typeof(Image));
            ringGo.transform.SetParent(go.transform, false);
            var rrt = (RectTransform)ringGo.transform;
            rrt.anchorMin = Vector2.zero;
            rrt.anchorMax = Vector2.one;
            rrt.offsetMin = new Vector2(-RingPad, -RingPad);
            rrt.offsetMax = new Vector2(RingPad, RingPad);
            var ringImg = ringGo.GetComponent<Image>();
            ringImg.type=Image.Type.Sliced;
            ringImg.raycastTarget = false;
            ringImg.enabled = false;

            var node = go.AddComponent<BlockOutBlockNode>();
            node.Init(block, this, rt, bg, ringImg, rrt, cols * cellSize + RingPad * 2f, rows * cellSize + RingPad * 2f, arrowImg);
            if (hammerSelectMode) node.SetSelectRingVisible(true);
            return node;
        }

        // ------------------------------------------------------------
        // 对外交互 API
        // ------------------------------------------------------------

        public void SetInputEnabled(bool enabled) { SetInputLock(BlockOutInputLock.Legacy, !enabled); }
        public void SetInputLock(BlockOutInputLock reason, bool held) { inputLocks.Set(reason, held); }

        /// <summary>棋盘输入锁状态（计时器 CanStartTimeFailTimer 条件之一，参考 inputLocked）。</summary>
        public bool IsInputLocked => inputLocks.IsLocked;

        public void SetPaused(bool isPaused) { paused = isPaused; SetInputLock(BlockOutInputLock.Pause, isPaused); }
        public bool IsPaused => paused;
        public void SetPresentationPaused(bool value) { paused=value; }
        public void CancelMagicFeedback()
        {
            if(effects!=null)effects.ClearMagic();
            foreach(var n in nodes)if(n!=null)n.CancelFeedback();
            foreach(var node in nodes) if(node!=null && node.Container!=null) node.Container.localScale=Vector3.one;
            if(fxRoot!=null) for(int i=fxRoot.childCount-1;i>=0;i--)
                if(fxRoot.GetChild(i).name=="Star") Destroy(fxRoot.GetChild(i).gameObject);
        }

        // ------------------------------------------------------------
        // R09 棋盘缩放根（捏合 / 平移 / 滚轮作用对象，与入场缩放相互独立）
        // ------------------------------------------------------------

        /// <summary>获取缩放根。首次调用创建并置于 transform 之下；已有 Blocks/Bg/Fx 若存在则挂到其下（兜底）。</summary>
        public RectTransform GetZoomRoot()
        {
            if (zoomRoot == null)
            {
                var go = new GameObject("ZoomRoot", typeof(RectTransform));
                go.transform.SetParent(transform, false);
                var zrt = (RectTransform)go.transform;
                zrt.anchorMin = Vector2.zero;
                zrt.anchorMax = Vector2.one;
                zrt.offsetMin = Vector2.zero;
                zrt.offsetMax = Vector2.zero;
                zrt.localScale = Vector3.one;
                zoomRoot = zrt;
                if (boardBg != null) boardBg.transform.SetParent(zoomRoot, false);
                if (blocksRoot != null) blocksRoot.SetParent(zoomRoot, false);
                if (fxRoot != null) fxRoot.SetParent(zoomRoot, false);
            }
            return zoomRoot;
        }

        public float GetZoomScale() => zoomRoot != null ? zoomRoot.localScale.x : 1f;

        public void ResetZoom()
        {
            if (zoomRoot == null) return;
            zoomRoot.localScale = Vector3.one;
            zoomRoot.anchoredPosition = Vector2.zero;
        }

        /// <summary>R10 视口聚焦：把目标移到可见中心并短暂放大，runToken 保护，结束复位到聚焦前状态。</summary>
        public void FocusOn(Vector2 localTarget)
        {
            if (zoomRoot == null) return;
            if (focusRoutine != null) StopCoroutine(focusRoutine);
            focusSavedPos = zoomRoot.anchoredPosition;
            focusSavedScale = zoomRoot.localScale.x;
            focusRoutine = StartCoroutine(Presentation.FocusRoutine(localTarget));
        }







        /// <summary>取消全部进行中的动画协程并清理拖尾/星星等特效（P1-3）。
        /// 重建棋盘 / 切关 / 退出关卡时调用，防止旧协程在令牌失效后访问已销毁节点。</summary>
        public void CancelAnimations()
        {
            if (this == null) return;
            StopAllCoroutines();
            if(effects!=null)effects.Clear();
            var completion=GetComponent<BlockOutCompletionPresentation>();if(completion!=null)completion.Clear();
            rebuildPending = false;
            var callbacks = new List<Action>(flightCancellations.Values);
            flightCancellations.Clear();
            foreach (var callback in callbacks) callback?.Invoke();
            // 拖尾挂在 blocksRoot、星星挂在 fxRoot：整体清空，避免残留半透明拖影。
            if (blocksRoot != null)
                for (int i = blocksRoot.childCount - 1; i >= 0; i--)
                {
                    var child = blocksRoot.GetChild(i);
                    if (child != null && (child.name == "Trail" || child.name == "ArtOutDistanceTrail")) Destroy(child.gameObject);
                }
            if (fxRoot != null)
                for (int i = fxRoot.childCount - 1; i >= 0; i--)
                {
                    var child = fxRoot.GetChild(i);
                    if (child != null && child.name!="AuthoredEffects") Destroy(child.gameObject);
                }
            inputLocks.Clear();
            focusRoutine = null;
            tapSuppressUntil = 0f;
        }

        /// <summary>本局令牌：LoadLevel 每次自增，旧协程检测到令牌变更即安全退出（不触发新局胜利/解锁输入）。</summary>
        public void SetRunToken(int token) { runToken = token; }

        /// <summary>锤子选择态：全部在场块显示可可虚线选中环。</summary>
        public void SetHammerSelectMode(bool active)
        {
            hammerSelectMode = active;
            foreach (var n in nodes)
                if (n != null) n.SetSelectRingVisible(active);
        }

        public void NotifyTapped(BlockOutBlockData block)
        {
            if (IsInputLocked || paused) return;
            if (Time.time < tapSuppressUntil) return;   // 手势结束后 0.16s 抑制点击（§7.4）
            if (OnBlockTapped != null) OnBlockTapped(block);
        }

        /// <summary>手势结束后的点击抑制（§7.4，参考手势抑制 0.16s）。</summary>
        public void SuppressTaps(float seconds)
        {
            tapSuppressUntil = Mathf.Max(tapSuppressUntil, Time.time + Mathf.Max(0f, seconds));
        }

        /// <summary>受阻反馈：红色标记环 + 箭头闪 3 次 + 三段落位置演出（§7.2）。
        /// emptyCells 为到障碍前的真正空格数（不含自身占格，由 Rules.TryGetWrongMoveDistance 提供）。
        /// onReturned 在回位完成后回调（GM 据此按当前局状态释放输入锁，参考 HandleWrongMove）。</summary>
        public void MarkWrong(BlockOutBlockData block, int emptyCells, Action onReturned)
        {
            var node = nodes.Find(n => n != null && n.TargetBlock == block);
            if (node == null) { if (onReturned != null) onReturned(); return; }
            node.ShowWrongFeedback();
            if (node.PositionRoutine != null) StopCoroutine(node.PositionRoutine);   // 同节点不并发位置动画
            StartCoroutine(node.FlashArrowRoutine(BlockOut.Config.BlockOutGameplayConfig.Current.feel.wrongArrowFlashCount, BlockOut.Config.BlockOutGameplayConfig.Current.feel.wrongArrowFlashSeconds));
            Vector2 step = BlockOutGameRules.GetDirectionStep(block.Direction);
            var routine = StartCoroutine(node.WrongFeedbackRoutine(step, emptyCells, cellSize, onReturned));
            node.PositionRoutine = routine;
        }

        public Vector2 GetBlockLocalPosition(BlockOutBlockData block)
        {
            var node = nodes.Find(n => n != null && n.TargetBlock == block);
            return node != null ? node.Container.anchoredPosition : Vector2.zero;
        }

        /// <summary>魔法棒起点局部坐标（参考 GetMagicStartWorldPosition；本地占位 = 棋盘中心）。</summary>
        public Vector2 GetWandStartLocalPosition()
        {
            if(MagicOrigin==null || zoomRoot==null)return Vector2.zero;
            return zoomRoot.InverseTransformPoint(MagicOrigin.TransformPoint(MagicOrigin.rect.center));
        }

        /// <summary>提示高亮：闪烁 + 聚焦（§7.3，见 BlockOutBlockNode.ShowHintHighlight）。</summary>
        public void HighlightBlock(BlockOutBlockData block,float seconds)
        {
            var node=nodes.Find(n=>n!=null && n.TargetBlock==block);
            if(node==null)return;
            SetInputLock(BlockOutInputLock.Hint,true);
            focusRoutine=StartCoroutine(FocusAndFlash(node,runToken));
        }
        private IEnumerator FocusAndFlash(BlockOutBlockNode node,int token)
        {
            try
            {
                yield return Presentation.FocusRoutine(node.Container.anchoredPosition);
                if(token==runToken && node!=null)yield return node.HintFlashRoutine();
            }
            finally { if(token==runToken) { SetInputLock(BlockOutInputLock.Hint,false);focusRoutine=null; } }
        }

        /// <summary>魔法星星特效：从起点飞到目标点（默认 magicStarPathSeconds 秒）后缩放淡出（§7.3）。</summary>
        public void SpawnStarTravel(Vector2 fromLocal, Vector2 toLocal, float seconds, int count = 3)
        {
            StartCoroutine(Presentation.StarTravelRoutine(fromLocal, toLocal, seconds, count));
        }

        /// <summary>魔法棒星星特效（兼容旧调用）：在落点缩放 0.6→1.2→0 淡出，600ms。</summary>
        public void SpawnStars(Vector2 localPos, int count = 3)
        {
            StartCoroutine(Presentation.StarRoutine(localPos, count));
        }

        /// <summary>棋盘入场（§7.3）：0.9s 由 0.68 倍缩放至正常；输入延迟基线 1.02s。
        /// 切关/重开由 Setup→CancelAnimations 终止旧协程，不会留下旧动画锁。</summary>
        public void PlayEntrance()
        {
            var feel = BlockOut.Config.BlockOutGameplayConfig.Current.feel;
            float dur = feel != null ? feel.boardEntranceSeconds : 0.9f;
            float startScale = feel != null ? feel.boardEntranceStartScale : 0.68f;
            float inputDelay = feel != null ? feel.boardEntranceInputDelay : 1.02f;
            SetInputLock(BlockOutInputLock.Entrance, true);
            if (entranceRoutine != null) StopCoroutine(entranceRoutine);
            entranceRoutine = StartCoroutine(Presentation.EntranceRoutine(dur, startScale, inputDelay));
        }



        /// <summary>飞出动画。onDone 仅在"本局令牌有效且动画正常播完"时回调；
        /// 被取消（重开/切关/退出/重建）时只走 onCancel，绝不触发 onDone（P1-3）。</summary>
        public void FlyOutBlock(BlockOutBlockData block, Action onDone, Action onCancel = null)
        {
            var node = nodes.Find(n => n != null && n.TargetBlock == block);
            if (node == null) { if (onDone != null) onDone(); return; }
            node.SetHitEnabled(false);   // 逻辑移除已提交：禁用命中，飞行中不可重复提交（§4.2.1）
            int flightId = ++nextFlightId;
            flightCancellations.Add(flightId, onCancel);
            StartCoroutine(Presentation.FlyRoutine(node, block.Direction,
                () => FinishFlight(flightId, onDone),
                () => FinishFlight(flightId, onCancel)));
        }

        /// <summary>魔法命中脉冲入口（参考命中放大演出）。</summary>
        public IEnumerator PlayMagicArrival(BlockOutBlockData block,float seconds,int pathIndex=0)
        {
            int token=runToken;
            bool arrived=false;
            var hitNode=nodes.Find(n=>n!=null && n.TargetBlock==block);
            Vector2 target=hitNode!=null && hitNode.ArrowImage!=null ? (Vector2)zoomRoot.InverseTransformPoint(hitNode.ArrowImage.transform.position) : GetBlockLocalPosition(block);
            StartCoroutine(Presentation.StarTravelRoutine(GetWandStartLocalPosition(),target,seconds,pathIndex,()=>arrived=true));
            while(!arrived && token==runToken) yield return null;
            if(token!=runToken) yield break;
            var node=nodes.Find(n=>n!=null && n.TargetBlock==block);
            if(node!=null) yield return node.HitPulseRoutine();
        }

        public void MagicHitPulse(BlockOutBlockData block)
        {
            var node = nodes.Find(n => n != null && n.TargetBlock == block);
            if (node != null) node.MagicHitPulse();
        }

        internal void FinishFlight(int id, Action callback)
        {
            if (!flightCancellations.Remove(id)) return;
            callback?.Invoke();
            if (rebuildPending && flightCancellations.Count == 0) Rebuild();
        }

        public void RemoveInstant(BlockOutBlockData block)
        {
            var node = nodes.Find(n => n != null && n.TargetBlock == block);
            if (node == null) return;
            nodes.Remove(node);
            Destroy(node.gameObject);
        }

        internal void ClearNodes()
        {
            foreach (var n in nodes)
                if (n != null) Destroy(n.gameObject);
            nodes.Clear();
        }

        // ------------------------------------------------------------
        // 协程
        // ------------------------------------------------------------





        /// <summary>魔法星星飞行动画（§7.3）：默认同时出发，magicStarPathSeconds 秒路径到目标后缩放淡出。</summary>



    }
}
