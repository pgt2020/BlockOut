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
        public RectTransform bigCard;
        public UnityEngine.UI.Button CollectionBackBtn;
        public UnityEngine.UI.Text CollectionCoinText;
        public UnityEngine.UI.Text CollectionChapterText;
        public UnityEngine.UI.Text CollectionPieceText;
        public UnityEngine.UI.Text CollectionEmptyText;
        public UnityEngine.UI.Image CollectionProgressFill;
        public RectTransform CollectionThumbRoot;
        public UnityEngine.UI.Image[] CollectionThumbRegions;
        public UnityEngine.UI.Button CollectionViewBigBtn;
        public GameObject CollectionBigLayer;
        public RectTransform CollectionBigRoot;
        public UnityEngine.UI.Image[] CollectionBigRegions;
        public UnityEngine.UI.Button CollectionBigCloseBtn;
        public RectTransform CollectionChapterList;
        public RectTransform CollectionContent;
        public BlockOutPinchZoom CollectionZoom;
        public RectTransform CollectionRepeatGrid;
        public RectTransform CollectionRetryBar;
        public UnityEngine.UI.Button CollectionRetryBtn;
        public UnityEngine.UI.Text CollectionRetryText;
        public UnityEngine.UI.Button CollectionNavHomeBtn;
        public UnityEngine.UI.Button CollectionNavCollectionBtn;
        public UnityEngine.UI.Button CollectionNavStoreBtn;
    }
}
