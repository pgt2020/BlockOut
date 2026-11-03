using UnityEngine;
using UnityEngine.UI;
using System.Collections.Generic;
using BlockOut.Core;
namespace BlockOut.Gameplay
{
    // Uses the same projected-tail selection and distance growth as ArtOutBlockTrailEffect.
    // The gradient is a persisted PNG, never a runtime-generated texture.
    public sealed class BlockOutAuthoredTrail : MonoBehaviour
    {
        private BlockOutBoardView board;
        private RectTransform follow,rect;
        private Image visual;
        private Vector2 direction,offset,origin,position;
        private float initialLength,maxLength,width,fadeElapsed,speed,acceleration,maxSpeed;
        private bool released;
        public static BlockOutAuthoredTrail Create(BlockOutBoardView board,BlockOutBlockNode node,Vector2 direction)
        {
            var go=new GameObject("ArtOutDistanceTrail",typeof(RectTransform),typeof(Image),typeof(BlockOutAuthoredTrail));
            go.transform.SetParent(node.Container.parent,false);go.transform.SetAsFirstSibling();
            var trail=go.GetComponent<BlockOutAuthoredTrail>();trail.board=board;trail.follow=node.Container;
            trail.rect=(RectTransform)go.transform;trail.visual=go.GetComponent<Image>();
            trail.visual.sprite=BlockOut.UI.BlockOutIconFactory.Asset("trail");trail.visual.color=node.TargetBlock.Color;trail.visual.raycastTarget=false;
            trail.rect.pivot=new Vector2(1,.5f);trail.direction=direction;
            TryGetProjectedTailBounds(node.TargetBlock,node.TargetBlock.Direction,out int edge,out int start,out int end);
            bool horizontal=Mathf.Abs(direction.x)>.5f;
            Vector2Int min=new Vector2Int(int.MaxValue,int.MaxValue),max=new Vector2Int(int.MinValue,int.MinValue);
            foreach(var cell in node.TargetBlock.Cells) { min=Vector2Int.Min(min,cell);max=Vector2Int.Max(max,cell); }
            Vector2 center=((Vector2)min+(Vector2)max)*.5f;
            Vector2 anchor=horizontal ? new Vector2(edge,(start+end)*.5f) : new Vector2((start+end)*.5f,edge);
            trail.offset=Vector2.Scale(anchor-center,new Vector2(board.cellSize,board.CellHeight));trail.width=board.cellSize+(end-start)*(horizontal ? board.CellHeight:board.cellSize);
            trail.initialLength=board.cellSize*.5f;
            // Reference length 10.5 is measured in the block's local cell units.
            trail.maxLength=10.5f/.86f*board.cellSize;
            trail.position=trail.origin=node.Container.anchoredPosition+trail.offset;
            trail.rect.localRotation=Quaternion.Euler(0,0,Mathf.Atan2(direction.y,direction.x)*Mathf.Rad2Deg);
            trail.rect.anchoredPosition=trail.position;trail.rect.sizeDelta=new Vector2(trail.initialLength,trail.width);
            return trail;
        }
        public void Release(float initialSpeed,float acceleration,float maximumSpeed)
        {
            if(follow!=null)position=follow.anchoredPosition+offset;
            follow=null;released=true;speed=initialSpeed*1.05f;this.acceleration=acceleration*1.05f;maxSpeed=maximumSpeed;
        }
        private void LateUpdate()
        {
            if(board==null) { Destroy(gameObject);return; }
            if(board.IsPaused)return;
            if(follow!=null)position=follow.anchoredPosition+offset;
            else if(released) { position+=direction*speed*Time.deltaTime;speed=Mathf.Min(maxSpeed,speed+acceleration*Time.deltaTime); }
            else { Destroy(gameObject);return; }
            rect.anchoredPosition=position;
            float length=Mathf.Clamp(initialLength+Mathf.Max(0,Vector2.Dot(position-origin,direction)),initialLength,maxLength);
            rect.sizeDelta=new Vector2(length,width);
            if(length>=maxLength-.0001f)fadeElapsed+=Time.deltaTime;
            var color=visual.color;color.a=1-Mathf.SmoothStep(0,1,Mathf.Clamp01(fadeElapsed/.55f));visual.color=color;
            if(fadeElapsed>=.55f)Destroy(gameObject);
        }
        private static bool TryGetProjectedTailBounds(BlockOutBlockData block, BlockOutDirection direction, out int edgeCoordinate, out int crossStart, out int crossEnd)
        {
            edgeCoordinate = 0;
            crossStart = 0;
            crossEnd = 0;
            if (block == null)
            {
                return false;
            }

            List<Vector2Int> cells = new List<Vector2Int>();
            foreach (Vector2Int cell in block.Cells)
            {
                cells.Add(cell);
            }

            if (cells.Count == 0)
            {
                return false;
            }

            Vector2Int min = cells[0];
            Vector2Int max = cells[0];
            for (int i = 1; i < cells.Count; i++)
            {
                min = Vector2Int.Min(min, cells[i]);
                max = Vector2Int.Max(max, cells[i]);
            }

            bool horizontalMove = direction == BlockOutDirection.Left || direction == BlockOutDirection.Right;
            float shapeCrossCenter = horizontalMove
                ? (min.y + max.y) * 0.5f
                : (min.x + max.x) * 0.5f;
            Dictionary<int, List<int>> strips = new Dictionary<int, List<int>>();
            foreach (var cell in cells)
            {
                int stripIdx = horizontalMove ? cell.x : cell.y;
                int crossIdx = horizontalMove ? cell.y : cell.x;
                if (!strips.ContainsKey(stripIdx)) strips[stripIdx] = new List<int>();
                strips[stripIdx].Add(crossIdx);
            }

            int bestStripIdx = 0;
            int maxStripWidth = -1;
            int bestCrossStart = 0;
            int bestCrossEnd = 0;

            foreach (var kvp in strips)
            {
                int stripIdx = kvp.Key;
                List<int> crossIndices = kvp.Value;
                crossIndices.Sort();

                int runStart = crossIndices[0];
                int runEnd = crossIndices[0];
                for (int i = 1; i <= crossIndices.Count; i++)
                {
                    if (i < crossIndices.Count && crossIndices[i] <= runEnd + 1)
                    {
                        runEnd = Mathf.Max(runEnd, crossIndices[i]);
                        continue;
                    }

                    int stripWidth = runEnd - runStart + 1;
                    bool isBetter = false;
                    if (stripWidth > maxStripWidth)
                    {
                        isBetter = true;
                    }
                    else if (stripWidth == maxStripWidth)
                    {
                        isBetter = IsBetterTailRunTie(
                            direction,
                            stripIdx,
                            runStart,
                            runEnd,
                            bestStripIdx,
                            bestCrossStart,
                            bestCrossEnd,
                            shapeCrossCenter);
                    }

                    if (isBetter)
                    {
                        bestStripIdx = stripIdx;
                        maxStripWidth = stripWidth;
                        bestCrossStart = runStart;
                        bestCrossEnd = runEnd;
                    }

                    if (i < crossIndices.Count)
                    {
                        runStart = crossIndices[i];
                        runEnd = crossIndices[i];
                    }
                }
            }

            edgeCoordinate = bestStripIdx;
            crossStart = bestCrossStart;
            crossEnd = bestCrossEnd;
            return true;
        }

        private static bool IsBetterTailRunTie(
            BlockOutDirection direction,
            int stripIdx,
            int crossStart,
            int crossEnd,
            int bestStripIdx,
            int bestCrossStart,
            int bestCrossEnd,
            float shapeCrossCenter)
        {
            if (stripIdx != bestStripIdx)
            {
                switch (direction)
                {
                    case BlockOutDirection.Left:
                        return stripIdx > bestStripIdx;
                    case BlockOutDirection.Right:
                        return stripIdx < bestStripIdx;
                    case BlockOutDirection.Up:
                        return stripIdx < bestStripIdx;
                    case BlockOutDirection.Down:
                        return stripIdx > bestStripIdx;
                }
            }

            float crossCenter = (crossStart + crossEnd) * 0.5f;
            float bestCrossCenter = (bestCrossStart + bestCrossEnd) * 0.5f;
            return Mathf.Abs(crossCenter - shapeCrossCenter) < Mathf.Abs(bestCrossCenter - shapeCrossCenter);
        }

    }
}
