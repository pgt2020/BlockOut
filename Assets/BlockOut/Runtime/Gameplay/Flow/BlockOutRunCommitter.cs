using System;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Core;
using BlockOut.Config;
namespace BlockOut.Gameplay
{
    /// <summary>Synchronous mutation boundary. No visual changes or reward events before a durable save.</summary>
    internal sealed class BlockOutRunCommitter
    {
        private readonly BlockOutGameRules rules;
        private readonly BlockOutToolController tools;
        private readonly BlockOutSpecialBlockSystem specials;
        private readonly Func<bool> commit;
        internal BlockOutRunCommitter(BlockOutGameRules rules,BlockOutToolController tools,BlockOutSpecialBlockSystem specials,Func<bool> commit)
        { this.rules=rules; this.tools=tools; this.specials=specials; this.commit=commit; }
        internal bool Remove(IEnumerable<BlockOutBlockData> targets,Func<bool> consume,out List<BlockOutBlockData> removed)
        {
            removed=new List<BlockOutBlockData>();
            var before=rules.CaptureRunProgress("","");
            var inventory=tools?.Capture();
            var active=new List<BlockOutBlockData>();
            foreach(var b in rules.Blocks) if(b.Active) active.Add(b);
            bool saved=false;
            try
            {
                if(consume!=null && !consume()) return false;
                foreach(var b in targets)
                {
                    rules.Remove(b);
                    if(BlockOutContentConfig.EnableSpecialBlocks && specials!=null) specials.ProcessRemovalChain(b,false);
                }
                foreach(var b in active) if(!b.Active) removed.Add(b);
                saved=commit();
                return saved;
            }
            catch(Exception e) { Debug.LogError("[BlockOut] 消除事务失败: "+e); return false; }
            finally
            {
                if(!saved) { rules.ApplyRunProgress(before); if(inventory!=null) tools.Restore(inventory); removed.Clear(); }
            }
        }
    }
}
