using System;
using System.Collections.Generic;
using BlockOut.Core;
namespace BlockOut.Gameplay
{
    public sealed class BlockOutHintTool
    {
        private readonly HashSet<int> hinted = new HashSet<int>();
        public int[] Capture() { var ids=new int[hinted.Count]; hinted.CopyTo(ids); return ids; }
        public void Restore(int[] ids) { hinted.Clear(); if(ids!=null) foreach(var id in ids) hinted.Add(id); }
        public void Reset() { hinted.Clear(); }
        public BlockOutBlockData Select(BlockOutGameRules rules, Func<BlockOutBlockData,bool> filter)
        {
            BlockOutBlockData first=null;
            foreach(var b in rules.Blocks)
            {
                if(b==null || !b.Active || (filter!=null ? !filter(b) : !rules.CanMove(b))) continue;
                if(first==null) first=b;
                if(!hinted.Contains(b.RuntimeIndex)) { hinted.Add(b.RuntimeIndex); return b; }
            }
            if(first!=null) { hinted.Clear(); hinted.Add(first.RuntimeIndex); }
            return first;
        }
    }
}
