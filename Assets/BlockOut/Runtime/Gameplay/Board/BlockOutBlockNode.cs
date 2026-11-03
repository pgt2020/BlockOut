using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using BlockOut.Core;

namespace BlockOut.Gameplay
{

    /// <summary>单个方块节点：容器 + 体色贴图 + 状态环 + 点击转发。</summary>
    public sealed class BlockOutBlockNode : MonoBehaviour, IPointerClickHandler
    {
        public BlockOutBlockData TargetBlock { get; private set; }
        public RectTransform Container { get; private set; }
        public Sprite BodySprite { get; private set; }
        /// <summary>箭头 Image（误点闪 3 次 / 提示闪烁用）。</summary>
        public Image ArrowImage { get; private set; }
        /// <summary>当前占位中位置动画（误点 travel/return）：同节点不并发，避免漂移（§7.2）。</summary>
        public Coroutine PositionRoutine { get; set; }

        private BlockOutBoardView owner;
        private Image body;
        private Image ring;
        private float ringWUnits, ringHUnits;
        private Coroutine pulseCoroutine;
        private BlockOutAnimationPlayer animationPlayer;
        private bool selected,magicTint;
        private Material arrowOverlay,arrowDarker;
        private void ApplyArrowTint()
        {
            if(ArrowImage==null)return;
            bool darker=magicTint || (TargetBlock.WrongMarked && animationPlayer.ArrowAlpha>.5f);
            ArrowImage.material=darker ? arrowDarker:arrowOverlay;
            ArrowImage.color=magicTint ? new Color(1,216f/255,61f/255,1) : darker ? new Color(1,49f/255,68f/255,1):TargetBlock.Color;
        }
        private void LateUpdate()
        {
            if(animationPlayer==null) return;
            if(body!=null) body.color=Color.Lerp(TargetBlock.Color,new Color(131f/255,248f/255,81f/255,1),animationPlayer.HintBlend);
            ApplyArrowTint();
            if(Container!=null && PositionRoutine==null) Container.localScale=Vector3.one*animationPlayer.VisualScale;
        }

        public void Init(BlockOutBlockData block, BlockOutBoardView view, RectTransform container, Image bodyImage,
            Image ringImage, RectTransform ringTransform, float ringW, float ringH, Image arrowImage = null)
        {
            TargetBlock = block;
            owner = view;
            Container = container;
            body = bodyImage;
            BodySprite = bodyImage.sprite;
            ring = ringImage;
            ringWUnits = ringW;
            ringHUnits = ringH;
            ArrowImage = arrowImage;
            animationPlayer=gameObject.AddComponent<BlockOutAnimationPlayer>();
            arrowOverlay=Resources.Load<Material>("ArtOutPresentation/Reference/Bundles/Shaders/Custom_OverlayTint");
            arrowDarker=Resources.Load<Material>("ArtOutPresentation/Reference/Bundles/Shaders/Custom_PlusDarkerTint");ApplyArrowTint();
        }

        public void OnPointerClick(PointerEventData eventData)
        {
            if (owner != null) owner.NotifyTapped(TargetBlock);
        }

        /// <summary>禁用/恢复本块命中（§4.2.1）：成功点击逻辑移除后立即禁用，
        /// 飞行中的同一块不可能被重复提交。</summary>
        public void SetHitEnabled(bool enabled)
        {
            if (body != null) body.raycastTarget = enabled;
        }

        /// <summary>魔法命中脉冲（参考 MagicBlockHitScale：放大 1.15× 0.12s ×2 后回落）。</summary>
        public void CancelFeedback() { magicTint=false;if(animationPlayer!=null)animationPlayer.Stop();ApplyArrowTint(); }
        public void MagicHitPulse()
        {
            if (gameObject.activeInHierarchy)
                StartCoroutine(HitPulseRoutine());
        }

        public IEnumerator HitPulseRoutine()
        {
            magicTint=true;ApplyArrowTint();
            var feel=BlockOut.Config.BlockOutGameplayConfig.Current.feel;
            yield return animationPlayer.Play("MagicHit",()=>owner==null || owner.IsPaused,.12f/Mathf.Max(.001f,feel.magicHitScaleSeconds));
        }

        // ---- 状态环 ----

        private void SetRing(Sprite sprite, bool visible)
        {
            if (ring == null) return;
            ring.sprite = sprite;
            ring.enabled = visible;
        }

        private Sprite MakeRing(Color color,float widthPx,float dashOn,float dashOff,float glowAlpha)
        {
            if(ring!=null)ring.color=color;
            return BlockOut.UI.BlockOutIconFactory.Asset(dashOn>0 ? "selection" : "ring");
        }

        public void SetSelectRingVisible(bool visible)
        {
            selected=visible;
            if(visible)SetRing(null,false);
            else if(TargetBlock!=null && TargetBlock.WrongMarked)ShowWrongFeedback();
            else SetRing(null,false);
        }

        public void ShowHintHighlight(float seconds)
        {
            if(pulseCoroutine!=null)StopCoroutine(pulseCoroutine);
            pulseCoroutine=StartCoroutine(HintFlashRoutine(seconds));
        }

        public IEnumerator HintFlashRoutine(float ignored=0)
        {
            var feel=BlockOut.Config.BlockOutGameplayConfig.Current.feel;
            for(int i=0;i<Mathf.Max(1,feel.hintFlashLoops);i++)
                yield return animationPlayer.Play("Hint",()=>owner==null || owner.IsPaused,.2f/Mathf.Max(.001f,feel.hintFlashStepSeconds));
            pulseCoroutine=null;
        }

        /// <summary>箭头闪烁：0.04s 间隔闪 3 次（§7.2，参考错误箭头反馈）。</summary>
        public IEnumerator FlashArrowRoutine(int count,float interval)
        {
            yield return animationPlayer.Play("WrongFlash",()=>owner==null || owner.IsPaused,.04f/Mathf.Max(.001f,interval));
        }

        /// <summary>
        /// 误点三段落（§7.2，参考 PlayWrongFeedback）：
        /// 朝箭头方向前进至障碍前（时长 clamp(0.08+0.06√n,0.12,0.24)）→ 撞击挤压 0.05s →
        /// 回原位（时长 clamp(0.12+0.04√n,0.16,0.28)）。无前进空间也要有撞击反馈。
        /// 距离只含真正空格（emptyCells 由 GM 经 Rules.TryGetWrongMoveDistance 提供，不含自身占格）。
        /// </summary>
        public IEnumerator WrongFeedbackRoutine(Vector2 dirStep, int emptyCells, float cellSize, Action onReturned)
        {
            if (Container == null) { onReturned(); yield break; }
            var cfg = BlockOut.Config.BlockOutGameplayConfig.Current;
            float travelBase = cfg != null ? cfg.feel.wrongTravelBaseSeconds : 0.08f;
            float travelPerSqrt = cfg != null ? cfg.feel.wrongTravelPerSqrtCell : 0.06f;
            float travelMin = cfg != null ? cfg.feel.wrongTravelMinSeconds : 0.12f;
            float travelMax = cfg != null ? cfg.feel.wrongTravelMaxSeconds : 0.24f;
            float returnBase = cfg != null ? cfg.feel.wrongReturnBaseSeconds : 0.12f;
            float returnPerSqrt = cfg != null ? cfg.feel.wrongReturnPerSqrtCell : 0.04f;
            float returnMin = cfg != null ? cfg.feel.wrongReturnMinSeconds : 0.16f;
            float returnMax = cfg != null ? cfg.feel.wrongReturnMaxSeconds : 0.28f;
            float impact = cfg != null ? cfg.feel.wrongImpactSeconds : 0.05f;
            float sqrt = Mathf.Sqrt(Mathf.Max(0, emptyCells));
            float travelDur = Mathf.Clamp(travelBase + travelPerSqrt * sqrt, travelMin, travelMax);
            float returnDur = Mathf.Clamp(returnBase + returnPerSqrt * sqrt, returnMin, returnMax);

            Vector2 orig = Container.anchoredPosition;
            Vector2 offset = new Vector2(dirStep.x*cellSize, dirStep.y*owner.CellHeight) * emptyCells;
            Vector3 baseScale = Container.localScale;

            bool horizontal=Mathf.Abs(dirStep.x)>.5f;
            Vector3 squeezed=Vector3.Scale(baseScale,horizontal ? new Vector3(.84f,1.06f,1) : new Vector3(1.06f,.84f,1));
            Vector2 push=dirStep*(horizontal ? Container.rect.width : Container.rect.height)*.08f;
            if(emptyCells>0)
            {
                yield return AnimateWrongPose(baseScale,orig+offset,travelDur);
                yield return AnimateWrongPose(squeezed,orig+offset+push,impact);
                yield return AnimateWrongPose(baseScale,orig,returnDur);
            }
            else
            {
                yield return AnimateWrongPose(squeezed,orig+push,.08f);
                yield return AnimateWrongPose(baseScale,orig,.14f);
            }
            Container.anchoredPosition=orig;Container.localScale=baseScale;
            PositionRoutine = null;
            if (onReturned != null) onReturned();
        }

        private IEnumerator AnimateWrongPose(Vector3 scale,Vector2 position,float duration)
        {
            Vector3 startScale=Container.localScale;Vector2 start=Container.anchoredPosition;float elapsed=0;
            while(elapsed<duration)
            {
                while(owner!=null && owner.IsPaused)yield return null;
                elapsed+=Time.deltaTime;float t=Mathf.Clamp01(elapsed/Mathf.Max(.001f,duration));
                Container.localScale=Vector3.Lerp(startScale,scale,t);Container.anchoredPosition=Vector2.Lerp(start,position,t);yield return null;
            }
        }

        public void ShowWrongFeedback()
        {
            // 持续错误视觉（N02）：红色错误环保持显示，不自动消失；
            // 随块移除（节点销毁）或被提示/选择环覆盖而清除。
            if(ArrowImage!=null)ArrowImage.color=BlockOut.UI.BlockOutDesignTokens.BerryRed;
            SetRing(null,false);ApplyArrowTint();
        }

        public void SetBodyAlpha(float alpha)
        {
            if (body == null) return;
            var c = body.color;
            c.a = alpha;
            body.color = c;
        }
    }
}
