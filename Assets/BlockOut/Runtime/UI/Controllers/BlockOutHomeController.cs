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

            // ---- 顶栏与卡片 ----
            if (owner.UI.HomeCoinText != null) owner.UI.HomeCoinText.text = profile.Coins.ToString();
            if (owner.UI.HomeChapterTitle != null) owner.UI.HomeChapterTitle.text = "第 " + (chapter + 1) + " 章 · " + theme;

            int completed = owner.GM.Catalog.GetCompletedCountInChapter(chapter, profile);
            int total=owner.GM.Catalog.ChapterLevelCount(chapter);
            int remain = Mathf.Max(0, total - completed);
            if (owner.UI.HomePieceBadge != null) owner.UI.HomePieceBadge.text = "通关 " + completed + "/"+total;
            if (owner.UI.HomePieceText != null)
                owner.UI.HomePieceText.text = remain > 0
                    ? "通关 " + completed + "/"+total+" · 还差 " + remain + " 关完成本章"
                    : "通关 "+total+"/"+total+" · 本章已完成";
            if (owner.UI.HomeProgressFill != null) owner.UI.HomeProgressFill.fillAmount = completed / (float)Mathf.Max(1,total);
            for (int i = 0; i < 12 && owner.UI.HomeNodes != null && i < owner.UI.HomeNodes.Length; i++)
            {
                var node = owner.UI.HomeNodes[i];
                if (node == null) continue;
                bool done = i < completed;
                node.color=done ? BlockOutDesignTokens.MintFly : BlockOutDesignTokens.SurfaceCard;
                node.sprite = BlockOutIconFactory.Circle(
                    done ? BlockOutDesignTokens.MintFly : BlockOutDesignTokens.SurfaceCard,
                    done ? BlockOutDesignTokens.MintFly : BlockOutDesignTokens.StrokeBoard, 1.5f);
            }

            RefreshHomeCta(chapter, theme, completed);
            owner.UI.Relayout();
            BlockOutWidgets.SetNavActive(owner.UI.NavHomeBtn, true);
        }
        internal void RefreshHomeCta(int chapter, string theme, int completed)
        {
            int firstUncompleted = owner.GM.Catalog.GetFirstUncompletedIndexInChapter(chapter, owner.GM.Profile);
            bool chapterComplete = firstUncompleted < 0;

            int nextChapter = chapter + 1;
            bool nextPublished = BlockOutContentConfig.IsChapterPublished(nextChapter)
                                  && owner.GM.Catalog.HasChapterData(nextChapter);

            // 次级 CTA：仅"本章已完成且下一章未发布"时提供重玩入口
            if (owner.UI.HomeCtaSecondary != null)
                owner.UI.HomeCtaSecondary.gameObject.SetActive(chapterComplete && !nextPublished);

            if (chapterComplete)
            {
                if (nextPublished)
                {
                    SetCta("进入下一章", "第 " + (nextChapter + 1) + " 章 · "
                        + BlockOutContentConfig.ChapterThemeName(nextChapter), true);
                    owner.ctaTargetIndex = nextChapter * BlockOutContentConfig.LevelsPerChapter;
                }
                else
                {
                    SetCta("新章节准备中", "第 " + (chapter + 1) + " 章 · " + theme + " · 已通关 "+owner.GM.Catalog.ChapterLevelCount(chapter)+" 关", false);
                    owner.ctaTargetIndex = chapter * BlockOutContentConfig.LevelsPerChapter;
                }
            }
            else
            {
                int levelNumber = firstUncompleted + 1; // 全局关号
                if (completed <= 0)
                    SetCta("开始第 " + levelNumber + " 关", "第 " + (chapter + 1) + " 章 · " + theme, true);
                else
                    SetCta("继续第 " + levelNumber + " 关",
                        "第 " + (chapter + 1) + " 章 · " + theme + " · 已通关 " + completed + " 关", true);
                owner.ctaTargetIndex = firstUncompleted;
            }
        }
        internal void SetCta(string title, string sub, bool interactable)
        {
            if (owner.UI.HomeCtaTitle != null) owner.UI.HomeCtaTitle.text = title;
            if (owner.UI.HomeCtaSub != null) owner.UI.HomeCtaSub.text = sub;
            if (owner.UI.HomeCtaButton == null) return;
            owner.UI.HomeCtaButton.interactable = interactable;
            var img = owner.UI.HomeCtaButton.targetGraphic as Image;
            // v6：CTA 标题/副题是白字，可点击态必须保持 action.primary 深底。
            if (img != null) img.color = interactable ? BlockOutDesignTokens.ActionPrimary
                                                      : BlockOutDesignTokens.GrayIconLocked;
            if (owner.UI.HomeCtaTitle != null)
                owner.UI.HomeCtaTitle.color = interactable ? BlockOutDesignTokens.White : new Color(1f, 1f, 1f, 0.85f);
            if (owner.UI.HomeCtaSub != null)
                owner.UI.HomeCtaSub.color = interactable ? new Color(1f, 1f, 1f, 0.88f) : new Color(1f, 1f, 1f, 0.6f);
        }

    }
}
