using System;
using System.Reflection;
using UnityEngine;

namespace BlockOut.UI
{
    public sealed class BlockOutStoreView : BlockOutUIViewBase
    {
        public UnityEngine.UI.Button StoreBackBtn;
        public UnityEngine.UI.Text StoreCoinText;
        public BlockOutStoreItemView[] StoreItemPrefabs;
        public RectTransform StoreListRoot;
        public UnityEngine.UI.Text StoreEmptyText;

        public UnityEngine.UI.Button StoreNavHomeBtn;
        public UnityEngine.UI.Button StoreNavCollectionBtn;
        public UnityEngine.UI.Button StoreNavStoreBtn;
    }
}
