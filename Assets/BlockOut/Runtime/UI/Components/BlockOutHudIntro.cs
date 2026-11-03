using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Gameplay;
namespace BlockOut.UI
{
    public sealed class BlockOutHudIntro : MonoBehaviour
    {
        private BlockOutAnimationPlayer player;
        private BlockOutGameManager game;
        private bool hidden,guideHidden;
        public void SetGuideHidden(bool value) { guideHidden=value;Apply(); }
        private readonly List<CanvasGroup> top=new List<CanvasGroup>(),tools=new List<CanvasGroup>();
        public void Configure(BlockOutUIManager ui,BlockOutGameManager gm)
        {
            game=gm;player=GetComponent<BlockOutAnimationPlayer>() ?? gameObject.AddComponent<BlockOutAnimationPlayer>();
            top.Clear();tools.Clear();
            Add(top,ui.BoardLevelTitle);Add(top,ui.BoardLevelSub);Add(top,ui.BoardPauseBtn);Add(top,ui.BoardTimerPill);Add(top,ui.BoardRemainingText);
            if(ui.BoardHearts!=null)foreach(var heart in ui.BoardHearts)Add(top,heart);
            Add(tools,ui.HintSlot.Rect);Add(tools,ui.HammerSlot.Rect);Add(tools,ui.MagicSlot.Rect);
        }
        private static void Add(List<CanvasGroup> list,Component target)
        { if(target!=null)list.Add(target.GetComponent<CanvasGroup>() ?? target.gameObject.AddComponent<CanvasGroup>()); }
        public void Play()
        {
            hidden=false;StopAllCoroutines();player.HudAlpha=player.ToolAlpha=0;Apply();StartCoroutine(Run());
        }
        private IEnumerator Run()
        {
            yield return player.Play("HudIntro",()=>game!=null && (game.IsPaused || game.ModalPopupOpen));Apply();
        }
        public void HideForCompletion() { StopAllCoroutines();StartCoroutine(Hide()); }
        private IEnumerator Hide()
        {
            yield return player.Play("HudOutro");hidden=true;Apply();
        }
        private void LateUpdate() { Apply(); }
        private void Apply()
        {
            if(player==null)return;
            foreach(var group in top)Set(group,(hidden || guideHidden) ? 0:player.HudAlpha);
            foreach(var group in tools)Set(group,(hidden || guideHidden) ? 0:player.HudAlpha*player.ToolAlpha);
        }
        private static void Set(CanvasGroup group,float alpha)
        { if(group==null)return;group.alpha=alpha;group.interactable=group.blocksRaycasts=alpha>.99f; }
        private void OnDisable() { StopAllCoroutines();if(player!=null)player.Stop();Apply(); }
    }
}
