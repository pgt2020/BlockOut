using System;
using System.Collections;
using UnityEngine;
using UnityEngine.EventSystems;
using BlockOut.Gameplay;
namespace BlockOut.UI
{
    /// <summary>Prefab-owned feedback: editable Animator clips, no generated images or tween curves.</summary>
    public sealed class BlockOutUIFeedback : MonoBehaviour,IPointerDownHandler,IPointerUpHandler,IPointerExitHandler
    {
        public bool Popup;
        private BlockOutAnimationPlayer player;
        private Vector3 restingScale;
        private Coroutine running;
        private bool buttonTween;
        private float buttonScale=1;
        private void Awake() { restingScale=transform.localScale;player=GetComponent<BlockOutAnimationPlayer>();if(player==null)player=gameObject.AddComponent<BlockOutAnimationPlayer>(); }
        private void OnEnable() { if(Popup)Play("PopupOpen"); }
        private void LateUpdate() { if(player!=null)transform.localScale=restingScale*(buttonTween ? buttonScale : player.VisualScale); }
        private void OnDisable() { if(running!=null)StopCoroutine(running);running=null;buttonTween=false;buttonScale=1;if(player!=null)player.Stop();transform.localScale=restingScale; }
        public void OnPointerDown(PointerEventData data)
        {
            var button=GetComponent<UnityEngine.UI.Button>();
            if(!Popup && button!=null && button.IsInteractable())TweenButton(.9f);
        }
        public void OnPointerUp(PointerEventData data) { if(!Popup)TweenButton(1); }
        public void OnPointerExit(PointerEventData data) { if(!Popup)TweenButton(1); }
        private void TweenButton(float target)
        {
            if(running!=null)StopCoroutine(running);
            buttonTween=true;running=StartCoroutine(ButtonRoutine(target));
        }
        private IEnumerator ButtonRoutine(float target)
        {
            float start=buttonScale;var animation=player.Play("ButtonTween");
            while(animation.MoveNext()) { buttonScale=Mathf.Lerp(start,target,player.MotionBlend);yield return animation.Current; }
            buttonScale=target;running=null;
        }
        public void Play(string state)
        {
            if(running!=null)StopCoroutine(running);
            buttonTween=false;buttonScale=1;running=StartCoroutine(PlayRoutine(state,null));
        }
        public void Close(Action complete)
        {
            if(running!=null)StopCoroutine(running);
            running=null;player.Stop();complete?.Invoke();
        }
        private IEnumerator PlayRoutine(string state,Action complete)
        {
            yield return player.Play(state);running=null;complete?.Invoke();
        }
    }
}
