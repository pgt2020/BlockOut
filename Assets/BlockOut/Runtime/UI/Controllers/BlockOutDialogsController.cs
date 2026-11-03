using System;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;
namespace BlockOut.UI
{
    internal sealed class BlockOutDialogsController
    {
        private readonly BlockOutUIController owner;
        internal BlockOutDialogsController(BlockOutUIController owner) { this.owner=owner; }
        internal void SyncModalFlag()
        {
            if (owner.GM == null || owner.UI == null) return;
            owner.GM.ModalPopupOpen = owner.UI.IsLayerActive("PauseLayer")
                || owner.UI.IsLayerActive("FailLayer")
                || owner.UI.IsLayerActive("SettlementLayer")
                || owner.UI.IsLayerActive("SettingsLayer")
                || owner.UI.IsLayerActive("ConfirmLayer")
                || owner.UI.IsLayerActive("AboutLayer")
                || (owner.UI.GuideLayer != null && owner.UI.GuideLayer.activeInHierarchy);
        }
        internal void OpenPauseLayer()
        {
            owner.GM.Settings.PlaySound("sfx_popup");
            owner.GM.Pause();
            owner.UI.SetLayerActive("PauseLayer", true);
            SyncModalFlag();
        }
        internal void AskConfirm(string title, string body, Action onOk)
        {
            if (owner.UI.ConfirmTitle != null) owner.UI.ConfirmTitle.text = title;
            if (owner.UI.ConfirmBody != null) owner.UI.ConfirmBody.text = body;
            owner.pendingConfirm = onOk;
            owner.UI.SetLayerActive("ConfirmLayer", true);
            SyncModalFlag();
        }
        internal void OpenSettings(string returnTo)
        {
            owner.settingsReturn = returnTo;
            SyncSettingsSwitches();
            owner.UI.SetLayerActive("SettingsLayer", true);
            SyncModalFlag();
        }
        internal void SyncSettingsSwitches()
        {
            BlockOutWidgets.SetSwitch(owner.UI.SettingsMusicSwitch, owner.GM.Settings.MusicOn);
            BlockOutWidgets.SetSwitch(owner.UI.SettingsSoundSwitch, owner.GM.Settings.SoundOn);
            BlockOutWidgets.SetSwitch(owner.UI.SettingsVibSwitch, owner.GM.Settings.VibrationOn);
        }
        internal void HandleLevelLost()
        {
            owner.GM.Settings.PlaySound("sfx_popup");
            owner.coinShortageToastDone = false;
            // 碎心演出延迟 0.58s 后再开失败层（§7.2，参考 ShowFail 时机）；
            // 延迟期间放弃/重开/复活 → 本局不再可操作，放弃弹层
            owner.StartCoroutine(ShowFailLayerAfterDelay());
        }
        internal IEnumerator ShowFailLayerAfterDelay()
        {
            float delay = BlockOut.Config.BlockOutGameplayConfig.Current.feel != null
                ? BlockOut.Config.BlockOutGameplayConfig.Current.feel.failPopupDelaySeconds : 0.58f;
            if (delay > 0f) yield return new WaitForSeconds(delay);
            if (owner.GM == null) yield break;
            if (owner.GM.State != BlockOutGameState.Lost || !owner.GM.IsRunPlayable) yield break;   // 延迟期间已放弃/重开
            owner.failLayerOpenedAt = Time.time;
            RefreshFailLayer();
            owner.UI.SetLayerActive("FailLayer", true);
            SyncModalFlag();
        }
        internal void RefreshFailLayer()
        {
            if (owner.GM == null) return;
            if (owner.UI.FailReasonText != null) owner.UI.FailReasonText.text = owner.GM.LastFailReason;

            bool exhausted = !owner.GM.ReviveAvailableAtAll;
            if (owner.UI.FailReviveBtn != null) owner.UI.FailReviveBtn.gameObject.SetActive(!exhausted);
            if (owner.UI.FailReviveNote != null) owner.UI.FailReviveNote.gameObject.SetActive(!exhausted);
            if (owner.UI.FailExhaustedNote != null) owner.UI.FailExhaustedNote.gameObject.SetActive(exhausted);
            if (exhausted) return;

            // 优先级：免费（全局 1-10 关，不限次数）> 激励广告 > 金币；广告未就绪且未超时 → 加载中
            if (owner.GM.FreeReviveAvailable)
            {
                SetReviveButton("复活 · 免费", true, true);
                return;
            }
            bool adTimedOut = owner.failLayerOpenedAt >= 0f && Time.time - owner.failLayerOpenedAt > BlockOutUIController.AdLoadFallbackSeconds;
            if (owner.GM.AdReviveReady)
            {
                SetReviveButton("复活 · 激励广告", true, false);
                return;
            }
            if (!adTimedOut)
            {
                SetReviveButton("广告加载中", false, false);
                return;
            }
            if (owner.GM.CanReviveWithCoins)
            {
                SetReviveButton("复活 · " + BlockOutContentConfig.CoinReviveCost + " 金币", true, false);
                return;
            }
            // 金币不足：置灰 + Toast 提示（仅提示，不跳商店）
            SetReviveButton("复活 · " + BlockOutContentConfig.CoinReviveCost + " 金币", false, false);
            if (!owner.coinShortageToastDone)
            {
                owner.coinShortageToastDone = true;
                owner.UI.ShowToast("金币不足 · 通关可获取金币");
            }
        }
        internal void SetReviveButton(string label, bool interactable, bool freeBadge)
        {
            owner.lastReviveLabel = label;
            if (owner.UI.FailReviveLabel != null) owner.UI.FailReviveLabel.text = label;
            if (owner.UI.FailReviveBtn == null) return;
            owner.UI.FailReviveBtn.interactable = interactable;
            if (owner.UI.FailFreeBadge != null) owner.UI.FailFreeBadge.SetActive(freeBadge);
            var img = owner.UI.FailReviveBtn.targetGraphic as Image;
            if (img != null) img.color = interactable ? Color.white : new Color(0.80f, 0.76f, 0.73f);
            if (owner.UI.FailReviveLabel != null)
                owner.UI.FailReviveLabel.color = interactable ? BlockOutDesignTokens.White : new Color(1f, 1f, 1f, 0.85f);
        }
        internal void CloseFailLayer()
        {
            owner.UI.SetLayerActive("FailLayer", false);
            SyncModalFlag();
        }
        internal void OnReviveClicked()
        {
            if (owner.GM.FreeReviveAvailable)
            {
                if (owner.GM.ReviveFree()) CloseFailLayer();
                else owner.UI.ShowToast("复活失败，请重试");
                return;
            }
            if (owner.GM.AdReviveReady)
            {
                owner.GM.ReviveWithAd(applied =>
                {
                    if (applied) CloseFailLayer();
                    else owner.UI.ShowToast("广告未完成 · 未消耗金币与复活资格");
                });
                return;
            }
            if (owner.GM.CanReviveWithCoins)
            {
                if (owner.GM.ReviveWithCoins()) CloseFailLayer();
                else owner.UI.ShowToast("金币不足");
                return;
            }
            owner.UI.ShowToast("金币不足 · 通关可获取金币");
        }
        private Coroutine completionRoutine;
        internal void HandleLevelWon()
        {
            if(completionRoutine!=null)owner.StopCoroutine(completionRoutine);
            completionRoutine=owner.StartCoroutine(PresentWin());
        }
        private IEnumerator PresentWin()
        {
            int token=owner.GM.ActiveRunToken;
            owner.UI.BoardView?.SetInputLock(BlockOutInputLock.Completion,true);
            var hud=owner.UI.GetScreenGO(BlockOutScreenId.Board)?.GetComponent<BlockOutHudIntro>();
            if(hud!=null && !owner.GM.SettlementSaveFailed)hud.HideForCompletion();
            var presentation=owner.UI.BoardView!=null ? owner.UI.BoardView.GetComponent<BlockOutCompletionPresentation>() : null;
            if(!owner.GM.SettlementSaveFailed && presentation!=null)
                yield return presentation.Play(owner.GM.LoadCompletionImage());
            if(token!=owner.GM.ActiveRunToken)yield break;
            if(presentation!=null)presentation.HidePicture();
            completionRoutine=null;ShowWinResults();
        }
        private void ShowWinResults()
        {
            int chapter = owner.GM.CurrentLevel != null ? owner.GM.CurrentLevel.Chapter : 0;
            int completed = owner.GM.ChapterCompletedCount;
            int total = owner.GM.Catalog.ChapterLevelCount(chapter);
            bool chapterComplete = owner.GM.IsCurrentChapterComplete;
            // 章末判断：本章已集齐且当前关是章末关（下一关属新章）
            bool isChapterEnd = chapterComplete
                && owner.GM.CurrentLevelIndex + 1 == chapter * BlockOutContentConfig.LevelsPerChapter + total;
            bool firstClear = owner.GM.LastWinWasFirstClear;

            // R11：单关通关图片优先展示（普通通关立即反馈）；章末才用章节拼片网格。
            // 成败都展示，避免结算层黑屏。
            RefreshSettleReveal(chapter, true);

            // R06：结算保存失败——存档已回滚（进度/奖励/拼片均未落盘）。
            // 严禁假报领奖成功；禁用"下一关/重玩"，给出返回重试引导。
            if (owner.GM.SettlementSaveFailed)
            {
                if (owner.UI.SettleTitleText != null) owner.UI.SettleTitleText.text = "关卡完成 · 进度未保存";
                if (owner.UI.SettlePieceText != null) owner.UI.SettlePieceText.text = "本关已通过，但存档写入失败";
                if (owner.UI.SettleNoteText != null)
                    owner.UI.SettleNoteText.text = "存档保存失败，奖励与拼片未发放 · 请点击重试保存";
                if (owner.UI.SettleRewardText != null) owner.UI.SettleRewardText.text = "存档失败 · 奖励未发放";
                if (owner.UI.SettleNextBtn != null) { BlockOutUIController.SetButtonLabel(owner.UI.SettleNextBtn, "重试保存"); owner.UI.SettleNextBtn.interactable = true; }
                if (owner.UI.SettleReplayBtn != null) { BlockOutUIController.SetButtonLabel(owner.UI.SettleReplayBtn, "暂不可用"); owner.UI.SettleReplayBtn.interactable = false; }
                owner.UI.SetLayerActive("SettlementLayer", true);
                SyncModalFlag();
                return;
            }

            if(owner.UI.SettleReplayBtn!=null) { owner.UI.SettleReplayBtn.interactable=true; BlockOutUIController.SetButtonLabel(owner.UI.SettleReplayBtn,"重玩本关"); }
            // ---- 标题（13/17：首次通关 / 重复通关 / 章末通关 三态）----
            if (owner.UI.SettleTitleText != null)
            {
                if (isChapterEnd) owner.UI.SettleTitleText.text = firstClear ? "本章通关" : "本章已完成";
                else owner.UI.SettleTitleText.text = firstClear ? "新拼片解锁" : "关卡完成";
            }
            if (owner.UI.SettlePieceText != null)
                owner.UI.SettlePieceText.text = chapterComplete ? "拼片 "+total+"/"+total+" · 本章作品已集齐" : "拼片 " + completed + "/"+total;

            if (owner.UI.SettleNoteText != null)
            {
                if (isChapterEnd)
                    owner.UI.SettleNoteText.text = firstClear
                        ? "本章 "+total+" 片拼片全部揭晓 · 完整作品已解锁"
                        : "重复通关 · 拼片不重复解锁，可继续刷金币";
                else
                    owner.UI.SettleNoteText.text = firstClear
                        ? "本次新揭晓 1 片拼片"
                        : "重复通关 · 拼片不重复解锁";
            }
            if (owner.UI.SettleRewardText != null)
                owner.UI.SettleRewardText.text = (firstClear ? "首次通关 · 获得 " : "重复通关 · 获得 ")
                    + owner.GM.LastRewardCoins + " 金币";

            // 下一关进入条件：下一关存在、其所属章节已发布且目录有数据（不只以 LevelCount 判断，避免进入空关）
            int next = owner.GM.CurrentLevelIndex + 1;
            bool hasNext = false;
            bool nextIsNewChapter = false;
            if (next < owner.GM.Catalog.LevelCount)
            {
                var nlv = owner.GM.Catalog.GetLevel(next);
                if (nlv != null && BlockOutContentConfig.IsChapterPublished(nlv.Chapter) && owner.GM.Catalog.HasChapterData(nlv.Chapter))
                {
                    hasNext = true;
                    nextIsNewChapter = nlv.Chapter != chapter;
                }
            }
            if (owner.UI.SettleNextBtn != null)
            {
                // 章末且下一章未发布 → 显示"新章节准备中"（P1-4：不是"进入下一章"禁用）
                // 章末且下一章已发布 → "进入下一章"
                string label;
                if (!hasNext) label = "新章节准备中";
                else if (isChapterEnd) label = "进入下一章";
                else if (nextIsNewChapter) label = "进入下一章";
                else label = "下一关";
                BlockOutUIController.SetButtonLabel(owner.UI.SettleNextBtn, label);
                owner.UI.SettleNextBtn.interactable = hasNext;
            }
            owner.UI.SetLayerActive("SettlementLayer", true);
            SyncModalFlag();
        }
        internal void RefreshSettleReveal(int chapter, bool showSingleLevelImage)
        {
            // R11：单关关联图片（LoadCompletionImage）—— 普通通关立即展示该关图片反馈
            if (owner.UI.SettleLevelImage != null)
            {
                if (!showSingleLevelImage) { owner.UI.SettleLevelImage.enabled = false; }
                else
                {
                    var tex = owner.GM.LoadCompletionImage();
                    if (tex != null)
                    {
                        var spr = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(0.5f, 0.5f));
                        var previous=owner.UI.SettleLevelImage.sprite;
                        owner.UI.SettleLevelImage.sprite = spr;
                        owner.UI.SettleLevelImage.preserveAspect=true;
                        if(previous!=null) UnityEngine.Object.Destroy(previous);
                        owner.UI.SettleLevelImage.enabled = true;
                    }
                    else owner.UI.SettleLevelImage.enabled = false;
                }
            }
            if (showSingleLevelImage)
            {
                // 单关反馈：隐藏章节拼片网格（"查看收藏"入口仍保留），避免章节拼片替代单关反馈（R11）
                if (owner.UI.SettleRevealRoot != null) owner.UI.SettleRevealRoot.gameObject.SetActive(false);
                return;
            }
            // 章末：展示章节拼片（contain 完整作品）
            if (owner.UI.SettleRevealRoot != null) owner.UI.SettleRevealRoot.gameObject.SetActive(true);
            if (owner.UI.SettleRevealRegions == null) return;
            if (owner.loadedArtChapter != chapter) { owner.artProvider.LoadChapter(chapter); owner.loadedArtChapter = chapter; }
            if (owner.artProvider.Status == ChapterArtStatus.Failed)
            {
                for (int i = 0; i < owner.UI.SettleRevealRegions.Length; i++)
                    if (owner.UI.SettleRevealRegions[i] != null) owner.UI.SettleRevealRegions[i].sprite = null;
                return;
            }
            for (int i = 0; i < owner.UI.SettleRevealRegions.Length; i++)
                BlockOutUIController.SetRegionImage(owner.UI.SettleRevealRegions[i], owner.artProvider.RegionSprite(owner.Collection.IsRegionRevealed(chapter, i), i, true));
            owner.UI.SetSettlementArtworkMode(true);
        }
    }
}
