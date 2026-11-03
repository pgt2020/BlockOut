using System;
using System.Collections.Generic;
using BlockOut.Core;
namespace BlockOut.Gameplay
{
    public sealed class BlockOutMagicTool
    {
        public List<BlockOutBlockData> Select(BlockOutGameRules rules, int count, Func<BlockOutBlockData,bool> filter)
        {
            return rules!=null ? rules.PickMagicTargets(count,filter) : new List<BlockOutBlockData>();
        }
    }
}
