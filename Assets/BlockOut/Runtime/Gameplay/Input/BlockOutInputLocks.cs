using System;
namespace BlockOut.Gameplay
{
    [Flags]
    public enum BlockOutInputLock { None=0, Entrance=1, Pause=2, Lost=4, Modal=8, Tool=16, WrongFeedback=32, Inactive=64, Legacy=128, Hint=256, Completion=512 }
    public sealed class BlockOutInputLocks
    {
        public BlockOutInputLock Reasons { get; private set; }
        public bool IsLocked => Reasons != BlockOutInputLock.None;
        public void Set(BlockOutInputLock reason, bool held) { if (held) Reasons |= reason; else Reasons &= ~reason; }
        public void Clear() { Reasons = BlockOutInputLock.None; }
    }
}
