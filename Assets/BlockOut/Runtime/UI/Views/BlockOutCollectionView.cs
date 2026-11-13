using System;
using System.Reflection;
using UnityEngine;

namespace BlockOut.UI
{
    public sealed class BlockOutCollectionView : BlockOutUIViewBase
    {
        public BlockOutChapterItemView ChapterItemPrefab;
        public BlockOutRepeatItemView RepeatItemPrefab;
        public RectTransform RepeatListRoot;
        public UnityEngine.UI.ScrollRect collectionScroll;
        public UnityEngine.UI.Button CollectionBackBtn;
        public UnityEngine.UI.Text CollectionCoinText;
        public UnityEngine.UI.Text CollectionChapterText;
        public UnityEngine.UI.Text CollectionPieceText;
        public UnityEngine.UI.Text CollectionEmptyText;
        public UnityEngine.UI.Image CollectionProgressFill;
        public RectTransform CollectionChapterList;
        public RectTransform CollectionContent;
        public RectTransform CollectionRepeatGrid;
        public UnityEngine.UI.Button CollectionNavHomeBtn;
        public UnityEngine.UI.Button CollectionNavCollectionBtn;
        public UnityEngine.UI.Button CollectionNavStoreBtn;
    }
}
