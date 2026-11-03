using System;
using System.Collections;
using UnityEngine;
namespace BlockOut.Gameplay
{
    /// <summary>Animation Clips own fixed timing/curves; callers await Animator completion.</summary>
    public sealed class BlockOutAnimationPlayer : MonoBehaviour
    {
        public float HudAlpha=1,ToolAlpha=1;
        public float MotionBlend=1;
        public float HintBlend;
        public float ArrowAlpha=1;
        public float VisualScale=1;
        private Animator animator;
        private Func<bool> paused;
        private void Ensure()
        {
            if(animator!=null) return;
            animator=GetComponent<Animator>();
            if(animator==null) animator=gameObject.AddComponent<Animator>();
            animator.runtimeAnimatorController=Resources.Load<RuntimeAnimatorController>("ArtOutPresentation/Animations/Feedback");
            if(animator.runtimeAnimatorController==null) throw new InvalidOperationException("Missing Feedback AnimatorController");
            animator.cullingMode=AnimatorCullingMode.AlwaysAnimate;
            animator.enabled=false;
        }
        public IEnumerator Play(string state,Func<bool> isPaused=null,float speed=1)
        {
            Ensure(); paused=isPaused;
            animator.enabled=true; animator.speed=(paused!=null && paused()) ? 0 : speed;
            animator.Play(state,0,0);
            animator.Update(0f);
            yield return null;
            while(animator!=null && animator.enabled)
            {
                animator.speed=(paused!=null && paused()) ? 0 : speed;
                var current=animator.GetCurrentAnimatorStateInfo(0);
                if(current.IsName(state) && current.normalizedTime>=1) break;
                yield return null;
            }
            Stop();
        }
        public void Stop()
        {
            if(animator!=null) animator.enabled=false;
            HudAlpha=ToolAlpha=1; MotionBlend=1; HintBlend=0; ArrowAlpha=1; VisualScale=1; paused=null;
        }
        private void OnDisable() { Stop(); }
    }
}
