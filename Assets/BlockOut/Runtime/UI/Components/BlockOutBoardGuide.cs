using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using BlockOut.Core;
using BlockOut.Gameplay;
namespace BlockOut.UI
{
    /// <summary>Reference first-level guided tap; authored hand sprite and Animator clip.</summary>
    public sealed class BlockOutBoardGuide : MonoBehaviour
    {
        private BlockOutGameManager game;
        private BlockOutBoardView board;
        private BlockOutHudIntro hud;
        private RectTransform hand;
        private BlockOutAnimationPlayer player;
        public void Configure(BlockOutGameManager gm,BlockOutBoardView view,BlockOutHudIntro intro)
        {
            ResetGuide();game=gm;board=view;hud=intro;
            if(game.CurrentLevelIndex!=0 || game.Profile.GuideCompleted || game.State!=BlockOutGameState.Ready)return;
            // A resumed partially played board must not restart the first-tap tutorial.
            if(game.Rules.RemainingBlocks!=game.Rules.Blocks.Count)return;
            game.GuideInputActive=true;hud?.SetGuideHidden(true);StartCoroutine(Run());
        }
        private IEnumerator Run()
        {
            int token=game.ActiveRunToken;float elapsed=0;
            while(elapsed<1.07f)
            {
                if(token!=game.ActiveRunToken) { ResetGuide();yield break; }
                if(!game.IsPaused && !game.ModalPopupOpen)elapsed+=Time.deltaTime;
                yield return null;
            }
            BlockOutBlockData target=null;
            foreach(var block in game.Rules.Blocks)
            {
                if(!block.Active || !game.Rules.CanMove(block))continue;
                if(target==null || block.Row<target.Row || (block.Row==target.Row && (block.Column<target.Column || (block.Column==target.Column && block.RuntimeIndex<target.RuntimeIndex))))target=block;
            }
            if(target==null) { Complete();yield break; }
            game.GuideTarget=target;
            var go=new GameObject("GuideHand",typeof(RectTransform),typeof(Image),typeof(BlockOutAnimationPlayer));
            hand=(RectTransform)go.transform;hand.SetParent(board.GetZoomRoot(),false);hand.SetAsLastSibling();
            hand.pivot=new Vector2(0,1);hand.sizeDelta=new Vector2(64,79);hand.anchoredPosition=board.GetBlockLocalPosition(target)+new Vector2(7,-3);
            var image=go.GetComponent<Image>();image.sprite=BlockOutIconFactory.Asset("guide_hand");image.raycastTarget=false;image.preserveAspect=true;
            player=go.GetComponent<BlockOutAnimationPlayer>();
            while(target.Active && token==game.ActiveRunToken)
            {
                var animation=player.Play("GuideTap",()=>game.IsPaused || game.ModalPopupOpen);
                while(target.Active && token==game.ActiveRunToken && animation.MoveNext())
                { hand.localScale=Vector3.one*player.VisualScale;yield return animation.Current; }
            }
            if(hand!=null)hand.gameObject.SetActive(false);
            hud?.SetGuideHidden(false);hud?.Play();game.GuideTarget=null;
            while(token==game.ActiveRunToken && game.HasFlyingBlocks)yield return null;
            if(token==game.ActiveRunToken)Complete();else ResetGuide();
        }
        private void Complete()
        {
            game.CommitProfileMutation(()=>game.Profile.GuideCompleted=true);
            ResetGuide();
        }
        private void ResetGuide()
        {
            StopAllCoroutines();
            if(game!=null) { game.GuideInputActive=false;game.GuideTarget=null; }
            hud?.SetGuideHidden(false);
            if(hand!=null) { hand.gameObject.SetActive(false);Destroy(hand.gameObject); }hand=null;
        }
        private void OnDisable() { ResetGuide(); }
    }
}
