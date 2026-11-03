using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
using BlockOut.Core;
namespace BlockOut.Gameplay
{
    internal sealed class BlockOutBoardPresentation
    {
        private readonly BlockOutBoardView view;
        internal BlockOutBoardPresentation(BlockOutBoardView view) { this.view=view; }
        internal IEnumerator FocusRoutine(Vector2 localTarget)
        {
            int token=view.runToken;
            if(view.zoomRoot==null)yield break;
            var gesture=view.GetComponentInParent<BlockOutBoardGesture>();
            float scale=view.MaximumZoom;
            float startScale=view.zoomRoot.localScale.x;
            Vector2 start=view.zoomRoot.anchoredPosition;
            Vector2 target=ClampFocus(-localTarget*scale,scale);
            float duration=Mathf.Max(.001f,BlockOut.Config.BlockOutGameplayConfig.Current.feel.hintFocusSeconds);
            float elapsed=0;
            while(elapsed<duration && token==view.runToken)
            {
                if(!view.IsPaused)
                {
                    elapsed+=Time.deltaTime;float p=Mathf.Clamp01(elapsed/duration);p=1-(1-p)*(1-p);
                    view.zoomRoot.localScale=Vector3.one/Mathf.Lerp(1f/startScale,1f/scale,p);
                    view.zoomRoot.anchoredPosition=Vector2.Lerp(start,target,p);
                }
                yield return null;
            }
            // ArtOut leaves the player at the focused view; no automatic return animation.
        }
        internal Vector2 ClampFocus(Vector2 p,float scale) => view.ClampPan(p,scale);
        internal void RestoreFocus()
        {
            if (view.zoomRoot != null)
            {
                view.zoomRoot.localScale = new Vector3(view.focusSavedScale, view.focusSavedScale, 1f);
                view.zoomRoot.anchoredPosition = view.focusSavedPos;
            }
            view.focusRoutine = null;
        }
        internal IEnumerator EntranceRoutine(float dur, float startScale, float inputDelay)
        {
            int myToken = view.runToken;
            var rt = (RectTransform)view.transform;
            Vector3 target = Vector3.one;
            rt.localScale = new Vector3(startScale, startScale, 1f);
            var player=view.GetComponent<BlockOutAnimationPlayer>();
            if(player==null)player=view.gameObject.AddComponent<BlockOutAnimationPlayer>();
            var animation=player.Play("Entrance",()=>view.IsPaused,1f/Mathf.Max(.001f,dur));
            try
            {
                while(animation.MoveNext())
                {
                    if(myToken!=view.runToken)yield break;
                    float scale=Mathf.Lerp(startScale,1,player.MotionBlend);
                    rt.localScale=new Vector3(scale,scale,1);
                    yield return animation.Current;
                }
            }
            finally { player.Stop(); }
            rt.localScale = target;
            // 输入延迟基线：缩放完成后仍保持锁定到 1.02s
            float waited = dur;
            while (waited < inputDelay)
            {
                if (myToken != view.runToken) yield break;
                while (view.paused)
                {
                    if (myToken != view.runToken) yield break;
                    yield return null;
                }
                waited += Time.deltaTime;
                yield return null;
            }
            if (myToken == view.runToken) view.SetInputLock(BlockOutInputLock.Entrance, false);
        }
        internal IEnumerator FlyRoutine(BlockOutBlockNode node, BlockOutDirection dir, Action onDone, Action onCancel)
        {
            int myToken = view.runToken;
            var rt = node.Container;
            if (rt == null) { if (onCancel != null) onCancel(); yield break; }
            Vector2 start = rt.anchoredPosition;
            Vector2 step = BlockOutGameRules.GetDirectionStep(dir);
            var feel = BlockOut.Config.BlockOutGameplayConfig.Current.feel;
            float zoom=Mathf.Max(.001f,view.GetZoomScale());
            float v0 = (feel != null ? feel.exitInitialSpeed : 6.24f) * view.unitScale/zoom;
            float acc = (feel != null ? feel.exitAcceleration : 15f) * view.unitScale/zoom;
            float vmax = (feel != null ? feel.exitMaxSpeed : 13f) * view.unitScale/zoom;

            // 终点：视口外 + 方块沿方向半宽 + 3.4 参考单位余量；下限 8 参考单位
            var rootRt = (RectTransform)view.transform;
            float halfW = rootRt.rect.width * 0.5f/zoom;
            float halfH = rootRt.rect.height * 0.5f/zoom;
            Vector2 center=-view.zoomRoot.anchoredPosition/zoom;
            float margin = 3.4f * view.unitScale/zoom;
            float minDist = 8f * view.unitScale/zoom;
            float blockHalf = Mathf.Max(rt.rect.width, rt.rect.height) * 0.5f;
            float distToEdge;
            if (Mathf.Abs(step.x) > Mathf.Abs(step.y))
                distToEdge = (step.x > 0f ? center.x+halfW - start.x : start.x-center.x + halfW) + blockHalf;
            else
                distToEdge = (step.y > 0f ? center.y+halfH - start.y : start.y-center.y + halfH) + blockHalf;
            float distance = Mathf.Max(minDist, distToEdge + margin);

            var authoredTrail=BlockOutAuthoredTrail.Create(view,node,step);
            // 加速移动（参考 ArtOutTween.MoveToAccelerated）
            float moved = 0f;
            float speed = Mathf.Max(0.01f, v0);
            bool cancelled = false;
            while (moved < distance)
            {
                if (myToken != view.runToken) { cancelled = true; break; }
                while (view.paused)
                {
                    if (myToken != view.runToken) { cancelled = true; break; }
                    yield return null;
                }
                if (cancelled) break;
                if (node == null || rt == null) { cancelled = true; break; }
                float stepLen = Mathf.Min(distance - moved, speed * Time.deltaTime);
                moved += stepLen;
                rt.anchoredPosition = start + step * moved;
                speed = Mathf.Min(Mathf.Max(speed, vmax), speed + acc * Time.deltaTime);

                yield return null;
            }

            if (cancelled || myToken != view.runToken)
            {
                if(authoredTrail!=null)UnityEngine.Object.Destroy(authoredTrail.gameObject);
                // 仅解除等待方，不移除节点、不改锁（属新局状态）
                if (onCancel != null) onCancel();
                yield break;
            }

            if(authoredTrail!=null)authoredTrail.Release(v0,acc,vmax);
            view.nodes.Remove(node);
            UnityEngine.Object.Destroy(node.gameObject);
            if (onDone != null) onDone();
        }

        internal IEnumerator StarTravelRoutine(Vector2 fromLocal,Vector2 toLocal,float seconds,int count,Action onArrived=null)
        {
            int token=view.runToken;
            var effect=view.Effects.PlayStar(fromLocal);
            float elapsed=0; float duration=Mathf.Max(.01f,seconds);
            Vector2 delta=toLocal-fromLocal;
            Vector2 side=new Vector2(-delta.y,delta.x).normalized;
            if(side.sqrMagnitude<.001f)side=Vector2.right;
            float distance=delta.magnitude/view.ReferenceWorldScale;
            float arc=Mathf.Clamp(distance*.28f,.8f,2.4f)*view.ReferenceWorldScale;
            float spread=Mathf.Clamp(distance*.12f,.25f,1f)*view.ReferenceWorldScale*(count%2==0 ? 1:-1);
            Vector2 control=(fromLocal+toLocal)*.5f+Vector2.up*arc+side*spread;
            while(elapsed<duration && token==view.runToken)
            {
                if(!view.IsPaused)
                {
                    elapsed+=Time.deltaTime;float t=Mathf.SmoothStep(0,1,Mathf.Clamp01(elapsed/duration));
                    view.Effects.Move(effect,(1-t)*(1-t)*fromLocal+2*(1-t)*t*control+t*t*toLocal);
                }
                yield return null;
            }
            view.Effects.Release(effect,0);
            if(token==view.runToken)onArrived?.Invoke();
        }
        internal IEnumerator StarRoutine(Vector2 localPos,int count)
        {
            var effect=view.Effects.PlayStar(localPos);
            view.Effects.Release(effect,.6f);
            yield break;
        }
    }
}
