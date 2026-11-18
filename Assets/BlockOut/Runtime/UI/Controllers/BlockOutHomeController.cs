using System;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;
namespace BlockOut.UI
{
    internal sealed class BlockOutHomeController
    {
        private readonly BlockOutUIController owner;
        internal BlockOutHomeController(BlockOutUIController owner) { this.owner=owner; }
        internal void GoHome()
        {
            // 离开对局即冻结（计时/连击/输入），继续关卡时由 LoadLevel 重置
            if (owner.GM != null && !owner.GM.IsPaused) owner.GM.Pause();
            owner.UI.ShowScreen(BlockOutScreenId.Home);
            RefreshHome();
        }
        internal void RefreshHome()
        {
            if (owner.GM == null || owner.GM.Profile == null) return;
            var profile = owner.GM.Profile;
            int chapter = owner.HomeChapterIndex;
            string theme = BlockOutContentConfig.ChapterThemeName(chapter);

            if (owner.UI.HomeCoinText != null) owner.UI.HomeCoinText.text = profile.Coins.ToString();

            int completed = owner.GM.Catalog.GetCompletedCountInChapter(chapter, profile);
            RefreshHomeCta(chapter, theme, completed);
            if (owner.UI.HomeLevelTitle != null)
                owner.UI.HomeLevelTitle.text = "第 " + (owner.ctaTargetIndex + 1) + " 关";
            if (owner.UI.HomeCtaButton != null)
            {
                var path = owner.UI.HomeCtaButton.GetComponentInParent<BlockOutGardenHomePath>();
                if (path != null)
                    path.Refresh(owner.ctaTargetIndex, owner.GM.Catalog.LevelCount,
                        index => { var level = owner.GM.Catalog.GetLevel(index); return level != null && profile.IsLevelCompleted(level.Id); },
                        index => owner.EnterLevel(index));
                if (owner.UI.HomeCtaTitle != null)
                {
                    var target = owner.GM.Catalog.GetLevelMetadata(owner.ctaTargetIndex);
                    bool replay = target != null && profile.IsLevelCompleted(target.Id);
                    owner.UI.HomeCtaTitle.text = (replay ? "重玩第 " : "第 ") + (owner.ctaTargetIndex + 1) + " 关";
                }
            }
            owner.UI.Relayout();
        }

        /// <summary>CTA 文案仍然来自真实关卡进度；R2 版式只显示主标题。</summary>
        internal void RefreshHomeCta(int chapter, string theme, int completed)
        {
            int firstUncompleted = owner.GM.Catalog.GetFirstUncompletedIndexInChapter(chapter, owner.GM.Profile);
            bool chapterComplete = firstUncompleted < 0;
            int nextChapter = chapter + 1;
            bool nextPublished = BlockOutContentConfig.IsChapterPublished(nextChapter)
                                  && owner.GM.Catalog.HasChapterData(nextChapter);

            if (chapterComplete)
            {
                if (nextPublished)
                {
                    SetCta("开始", "第 " + (nextChapter + 1) + " 章 · "
                        + BlockOutContentConfig.ChapterThemeName(nextChapter), true);
                    owner.ctaTargetIndex = nextChapter * BlockOutContentConfig.LevelsPerChapter;
                }
                else
                {
                    SetCta("再玩一局", "全部通关 · 重温喜欢的关卡", true);
                    owner.ctaTargetIndex = chapter * BlockOutContentConfig.LevelsPerChapter;
                }
            }
            else
            {
                int levelNumber = firstUncompleted + 1;
                SetCta("开始", "第 " + (chapter + 1) + " 章 · 已完成 " + completed + "/" + owner.GM.Catalog.ChapterLevelCount(chapter), true);
                owner.ctaTargetIndex = firstUncompleted;
            }
        }

        internal void SetCta(string title, string sub, bool interactable)
        {
            if (owner.UI.HomeCtaTitle != null) owner.UI.HomeCtaTitle.text = title;
            if (owner.UI.HomeCtaSub != null) owner.UI.HomeCtaSub.text = sub;
            if (owner.UI.HomeCtaButton == null) return;
            owner.UI.HomeCtaButton.interactable = interactable;
            // 绿色渐变是贴图本身，别再用 Image.color 把它刷成 v6 的深棕。
            var img = owner.UI.HomeCtaButton.targetGraphic as Image;
            if (img != null)
            {
                img.color = interactable ? Color.white : new Color(1f, 1f, 1f, 0.65f);
                img.material = null;
            }
            if (owner.UI.HomeCtaTitle != null)
                owner.UI.HomeCtaTitle.color = interactable ? Color.white : new Color(1f, 1f, 1f, 0.75f);
        }

    }
}
