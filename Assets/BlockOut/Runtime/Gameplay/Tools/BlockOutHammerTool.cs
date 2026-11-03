using BlockOut.Core;
namespace BlockOut.Gameplay
{
    public sealed class BlockOutHammerTool
    {
        public bool Selecting { get; private set; }
        public bool Enter(int stock) { if(stock<=0 || Selecting) return false; Selecting=true; return true; }
        public void Cancel() { Selecting=false; }
        public void Restore(bool selecting) { Selecting=selecting; }
        public bool CanRemove(BlockOutBlockData block, int stock) => Selecting && stock>0 && block!=null && block.Active;
    }
}
