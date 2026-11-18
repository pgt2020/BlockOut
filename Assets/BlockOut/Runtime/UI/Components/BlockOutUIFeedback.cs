using System;
using System.Collections;
using UnityEngine;
using UnityEngine.EventSystems;
using BlockOut.Gameplay;
namespace BlockOut.UI
{
    /// <summary>Button feedback uses clips; modal windows open with a centered, unscaled-time zoom.</summary>
    public sealed class BlockOutUIFeedback : MonoBehaviour,IPointerDownHandler,IPointerUpHandler,IPointerExitHandler
    {
        public bool Popup;
        private BlockOutAnimationPlayer player;
        private Vector3 restingScale;
        private Coroutine running;
        private bool buttonTween;
        private float buttonScale=1;
        private float popupScale=1;
        private void Awake() { restingScale=transform.localScale;player=GetComponent<BlockOutAnimationPlayer>();if(player==null)player=gameObject.AddComponent<BlockOutAnimationPlayer>(); }
        private void OnEnable() { if(Popup)Play("PopupOpen"); }
        private void LateUpdate() { if(player!=null)transform.localScale=restingScale*(Popup ? popupScale : buttonTween ? buttonScale : player.VisualScale); }
        private void OnDisable() { if(running!=null)StopCoroutine(running);running=null;buttonTween=false;buttonScale=popupScale=1;if(player!=null)player.Stop();transform.localScale=restingScale; }
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
            if(Popup && state=="PopupOpen")
            {
                player.Stop();
                running=StartCoroutine(OpenFromCenter());
                return;
            }
            buttonTween=false;buttonScale=1;running=StartCoroutine(PlayRoutine(state,null));
        }
        private IEnumerator OpenFromCenter()
        {
            var rect=transform as RectTransform;
            if(rect!=null)
            {
                // Preserve the authored resting rectangle while moving its scale origin.
                var center=new Vector2(.5f,.5f);
                rect.anchoredPosition+=Vector2.Scale(center-rect.pivot,rect.rect.size);
                rect.pivot=center;
            }
            popupScale=0;
            transform.localScale=Vector3.zero;
            const float duration=.2f;
            float elapsed=0;
            while(elapsed<duration)
            {
                yield return null;
                elapsed+=Time.unscaledDeltaTime;
                float t=Mathf.Clamp01(elapsed/duration);
                popupScale=1-Mathf.Pow(1-t,3);
                transform.localScale=restingScale*popupScale;
            }
            popupScale=1;
            transform.localScale=restingScale;
            running=null;
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
