using System;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;
namespace BlockOut.UI
{
    internal sealed class BlockOutCollectionController
    {
        private readonly BlockOutUIController owner;
        internal BlockOutCollectionController(BlockOutUIController owner) { this.owner=owner; }
        internal void RefreshCollection()
        {
            if (owner.GM == null || owner.GM.Profile == null) return;
            int chapter = Mathf.Clamp(owner.collectionChapter, 0, Mathf.Max(0, BlockOutContentConfig.PublishedChapters - 1));
            owner.collectionChapter = chapter;
            string theme = BlockOutContentConfig.ChapterThemeName(chapter);
            int completed = owner.GM.Catalog.GetCompletedCountInChapter(chapter, owner.GM.Profile);
            int total=owner.GM.Catalog.ChapterLevelCount(chapter);
            int remain = Mathf.Max(0, total - completed);

            if (owner.UI.CollectionCoinText != null) owner.UI.CollectionCoinText.text = owner.GM.Profile.Coins.ToString();
            if (owner.UI.CollectionChapterText != null)
                owner.UI.CollectionChapterText.text = "第 " + (chapter + 1) + " 章 · " + theme;
            if (owner.UI.CollectionPieceText != null)
                owner.UI.CollectionPieceText.text = "通关 " + completed + "/"+total+" · " + (remain > 0 ? "还差 " + remain + " 关" : "本章已完成");
            if (owner.UI.CollectionProgressFill != null) owner.UI.CollectionProgressFill.fillAmount = completed / (float)Mathf.Max(1,total);
            if (owner.UI.CollectionEmptyText != null)
            {
                owner.UI.CollectionEmptyText.gameObject.SetActive(completed <= 0);
                owner.UI.CollectionEmptyText.text = chapter > owner.HomeChapterIndex
                    ? "先完成前面的关卡，再来开启本章" : "点击绿色关卡开始挑战";
            }

            RefreshChapterRows(chapter, completed);
            owner.repeatChapter = chapter;
            RefreshRepeatGrid(chapter);
            LayoutRebuilder.ForceRebuildLayoutImmediate(owner.UI.CollectionContent);
            if (owner.UI.collectionScroll != null)
            {
                owner.UI.collectionScroll.StopMovement();
                owner.UI.collectionScroll.verticalNormalizedPosition = 1f;
            }

        }
        internal void RefreshChapterRows(int chapter,int completed)
        {
            int published=Mathf.Max(0,BlockOutContentConfig.PublishedChapters);
            owner.UI.EnsureChapterItems(published+1);
            for(int c=0;c<owner.UI.ChapterItems.Count;c++)
            {
                int index=c;
                var row=owner.UI.ChapterItems[c];
                bool ready=c<published && owner.GM.Catalog.HasChapterData(c);
                int done=ready ? owner.GM.Catalog.GetCompletedCountInChapter(c,owner.GM.Profile) : 0;
                row.Title.text=ready ? "第 "+(c+1)+" 章 · "+BlockOutContentConfig.ChapterThemeName(c) : "新章节准备中";
                row.Subtitle.text=ready ? done+"/"+owner.GM.Catalog.ChapterLevelCount(c)+(done>=owner.GM.Catalog.ChapterLevelCount(c) ? " · 已完成" : c > owner.HomeChapterIndex ? " · 待开启" : " · 进行中") : "新章节发布时间待定";
                row.Locked.SetActive(!ready);
                row.Button.interactable=ready;
                var image = row.Button.targetGraphic as Image;
                if (image != null) image.color = c == chapter ? new Color(.88f,1f,.88f,1f) : Color.white;
                owner.Bind(row.Button,()=>OnCollectionChapterRowClicked(index));
            }
        }
        internal void RefreshRepeatGrid(int chapter)
        {
            int count=Mathf.Clamp(owner.GM.Catalog.LevelCount-chapter*BlockOutContentConfig.LevelsPerChapter,0,BlockOutContentConfig.LevelsPerChapter);
            owner.UI.EnsureRepeatItems(count);
            int first=owner.GM.Catalog.GetFirstUncompletedIndexInChapter(chapter,owner.GM.Profile);
            for(int i=0;i<count;i++)
            {
                int index=i;
                var cell=owner.UI.RepeatItems[i];
                int global=chapter*BlockOutContentConfig.LevelsPerChapter+i;
                var level=owner.GM.Catalog.GetLevel(global);
                bool done=level!=null && owner.GM.Profile.IsLevelCompleted(level.Id);
                bool current=!done && global==first && global<=owner.GM.Profile.CurrentLevelIndex;
                cell.Mark.SetActive(false); cell.Number.gameObject.SetActive(done || current); cell.Locked.SetActive(!done&&!current);
                cell.Number.text=(global+1).ToString();
                cell.Background.sprite=BlockOutGardenSprites.Get(current ? "tile-green" : done ? "tile-purple" : "tile-grey");
                cell.Background.color=Color.white;
                cell.Number.color=Color.white;
                cell.Button.interactable=done || current;
                owner.Bind(cell.Button,()=>OnRepeatCellClicked(index));
            }
        }

        internal void OnCollectionChapterRowClicked(int chapter)
        {
            if (chapter < 0 || chapter >= BlockOutContentConfig.PublishedChapters) return;
            owner.collectionChapter = chapter;
            RefreshCollection();
        }


        internal void OnRepeatCellClicked(int i)
        {
            if (owner.GM == null) return;
            int global = owner.repeatChapter * BlockOutContentConfig.LevelsPerChapter + i;
            if (global >= owner.GM.Catalog.LevelCount) return;
            var lv = owner.GM.Catalog.GetLevel(global);
            if (lv == null) return;
            if (!owner.GM.Profile.IsLevelCompleted(lv.Id) && global>owner.GM.Profile.CurrentLevelIndex)
            {
                owner.UI.ShowToast("该关卡尚未通关，无法重复挑战");
                return;
            }
            owner.EnterLevel(global); // 重复挑战：已通关关无进行中局，等同新开一局
        }

    }
}
