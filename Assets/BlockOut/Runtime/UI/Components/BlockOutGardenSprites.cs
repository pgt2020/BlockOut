using System.Collections.Generic;
using UnityEngine;

namespace BlockOut.UI
{
    internal static class BlockOutGardenSprites
    {
        private static readonly Dictionary<string, Sprite> Cache = new Dictionary<string, Sprite>();
        internal static Sprite Get(string name)
        {
            if (!Cache.TryGetValue(name, out var sprite) || sprite == null)
                Cache[name] = sprite = Resources.Load<Sprite>("UI/Garden/" + name);
            return sprite;
        }
    }
}
