using System;
using System.Collections.Generic;
using UnityEngine;
using BlockOut.Core;
namespace BlockOut.UI
{
    /// <summary>Persistent presentation assets. No textures are rasterized while playing.</summary>
    public static class BlockOutIconFactory
    {
        private static readonly Dictionary<string,Sprite> cache=new Dictionary<string,Sprite>();
        public static Sprite Asset(string name)
        {
            if(cache.TryGetValue(name,out var sprite) && sprite!=null) return sprite;
            sprite=Resources.Load<Sprite>("ArtOutPresentation/Sprites/"+name);
            if(sprite==null) throw new InvalidOperationException("Missing presentation sprite: "+name);
            cache[name]=sprite; return sprite;
        }
        public static Sprite Coin() => Asset("coin");
        public static Sprite Gear() => Asset("gear");
        public static Sprite Bulb() => Asset("bulb");
        public static Sprite HammerIcon() => Asset("hammer");
        public static Sprite Wand() => Asset("wand");
        public static Sprite LockIcon() => Asset("lock");
        public static Sprite HomeIcon() => Asset("home");
        public static Sprite BookIcon() => Asset("book");
        public static Sprite BagIcon() => Asset("bag");
        public static Sprite PauseIcon() => Asset("pause");
        public static Sprite HeartIcon() => Asset("heart");
        public static Sprite StarIcon() => Asset("star");
        public static Sprite PlayIcon() => Asset("play");
        public static Sprite AdIcon() => Asset("ad");
        public static Sprite BrokenImageIcon() => Asset("broken");
        public static Sprite MintCheck() => Asset("check");
        public static Sprite Arrow(BlockOutDirection dir) => Resources.Load<Sprite>("ArtOutPresentation/Reference/Bundles/Sprites/Arrow/"+dir.ToString().ToLowerInvariant());
        public static Sprite BoardSprite(int width,int height) => Asset("board");
        public static Sprite BlockSprite(BlockOutBlockData block,int cols,int rows,float cellPx)
        {
            var sprite=Resources.Load<Sprite>("ArtOutPresentation/Reference/Bundles/Sprites/WoodBlockHDR/"+block.ShapeId);
            if(sprite==null)throw new InvalidOperationException("Missing wood block sprite "+block.ShapeId);
            return sprite;
        }
        public static Sprite Ring(int w,int h,Color color,float width,float dashOn,float dashOff,float glow) => Asset(dashOn>0 ? "selection" : "ring");
        // These compatibility APIs return neutral authored masks; callers own their Image tint.
        public static Sprite RoundedSlice(float radius,Color fill,Color stroke,float strokeWidth,Color? top) => Asset("round");
        public static Sprite RoundedPlain(int w,int h,float radius,Color fill,Color stroke,float strokeWidth) => Asset("round");
        public static Sprite Circle(Color fill,Color stroke,float strokeWidth) => Asset("circle");
    }
}
