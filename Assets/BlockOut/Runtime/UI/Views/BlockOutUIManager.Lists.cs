using System;
using System.Collections.Generic;
using System.Reflection;
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

        // ============================================================
        // 列表项 Prefab 引用兜底
        // 离线生成的 Prefab 中，这些字段指向「另一个 Prefab 内的组件」。
        // Unity 资产依赖边或导入缓存过期时该引用会被解析成空，
        // 导致启动阶段的 ValidateReferences 抛异常、整个界面初始化失败。
        // 这里在实例上按资源路径重新解析（仅在为空时），不改动 Prefab 资产。
        // ============================================================
        private const string ItemRoot = "Prefabs/UI/Items/";
        // 与 BlockOutStorePage 的 StoreItemPrefabs 序列化顺序一致
        private static readonly string[] StoreItemOrder =
        {
            ItemRoot + "StoreHint", ItemRoot + "StoreHammer", ItemRoot + "StoreMagic"
        };

        internal static void RestoreItemPrefabLinks(BlockOutUIViewBase view)
        {
            if (view == null) return;
            const BindingFlags flags = BindingFlags.Public | BindingFlags.Instance;
            foreach (var f in view.GetType().GetFields(flags))
            {
                if (f.IsLiteral || f.IsNotSerialized) continue;
                var t = f.FieldType;
                if (t.IsArray)
                {
                    var et = t.GetElementType();
                    if (et != typeof(BlockOutStoreItemView)) continue;
                    var arr = f.GetValue(view) as Array;
                    int wanted = StoreItemOrder.Length;
                    // Unity 丢弃无效引用时可能把数组截短，这里按配置长度补齐，避免商店少商品
                    if (arr == null || arr.Length < wanted)
                    {
                        var grown = Array.CreateInstance(et, wanted);
                        if (arr != null) Array.Copy(arr, grown, arr.Length);
                        arr = grown;
                        f.SetValue(view, arr);
                    }
                    for (int i = 0; i < arr.Length && i < wanted; i++)
                    {
                        if ((UnityEngine.Object)arr.GetValue(i) != null) continue;
                        var c = LoadItemView(StoreItemOrder[i], et);
                        if (c == null) continue;
                        arr.SetValue(c, i);
                        LogRestored(f.Name + "[" + i + "]");
                    }
                    continue;
                }
                if (!typeof(BlockOutUIViewBase).IsAssignableFrom(t)) continue;
                if ((UnityEngine.Object)f.GetValue(view) != null) continue;
                var name = f.Name;
                if (name.EndsWith("Prefab")) name = name.Substring(0, name.Length - "Prefab".Length);
                var item = LoadItemView(ItemRoot + name, t);
                if (item == null) continue;
                f.SetValue(view, item);
                LogRestored(f.Name);
            }
        }
        private static Component LoadItemView(string path, Type viewType)
        {
            var go = Resources.Load<GameObject>(path);
            return go != null ? go.GetComponent(viewType) : null;
        }
        private static void LogRestored(string field)
        {
            Debug.Log("[BlockOut][UI] 列表项引用已自动恢复：" + field + "（Prefab 导入缓存中的绑定为空）");
        }
    }
}
