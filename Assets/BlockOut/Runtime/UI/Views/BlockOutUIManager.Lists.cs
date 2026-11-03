using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;
namespace BlockOut.UI
{
    public sealed partial class BlockOutUIManager
    {
        public readonly List<BlockOutChapterItemView> ChapterItems=new List<BlockOutChapterItemView>();
        public readonly List<BlockOutRepeatItemView> RepeatItems=new List<BlockOutRepeatItemView>();
        private readonly List<BlockOutStoreItemView> storeItems=new List<BlockOutStoreItemView>();
        private void BuildDynamicLists() { SetStoreItems(StoreItemPrefabs); }
        public void SetStoreItems(IReadOnlyList<BlockOutStoreItemView> prefabs)
        {
            foreach(var item in storeItems) if(item!=null) { item.gameObject.SetActive(false); Destroy(item.gameObject); }
            storeItems.Clear();
            int count=prefabs!=null ? prefabs.Count : 0;
            StoreProducts=new StoreProductRefs[count];
            for(int i=0;i<count;i++)
            {
                var item=Instantiate(prefabs[i],StoreListRoot,false);
                string error;
                if(!item.ValidateReferences(out error)) throw new InvalidOperationException(error);
                item.gameObject.SetActive(true); storeItems.Add(item); StoreProducts[i]=item.Product;
            }
            StoreEmptyText.gameObject.SetActive(count==0);
            LayoutRebuilder.ForceRebuildLayoutImmediate(StoreListRoot);
        }
        public void EnsureChapterItems(int count)
        {
            Resize(ChapterItems,ChapterItemPrefab,CollectionChapterList,count);
            LayoutRebuilder.ForceRebuildLayoutImmediate(CollectionContent);
        }
        public void EnsureRepeatItems(int count) { Resize(RepeatItems,RepeatItemPrefab,RepeatListRoot,count); }
        private static void Resize<T>(List<T> items,T prefab,Transform parent,int count) where T:BlockOutUIViewBase
        {
            count=Mathf.Max(0,count);
            while(items.Count>count)
            {
                var item=items[items.Count-1]; items.RemoveAt(items.Count-1);
                item.gameObject.SetActive(false); UnityEngine.Object.Destroy(item.gameObject);
            }
            while(items.Count<count)
            {
                var item=UnityEngine.Object.Instantiate(prefab,parent,false);
                string error;
                if(!item.ValidateReferences(out error)) throw new InvalidOperationException(error);
                item.gameObject.SetActive(true); items.Add(item);
            }
        }
    }
}
