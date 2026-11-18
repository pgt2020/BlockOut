using System.Collections;
using System.IO;
using System.Linq;
using BlockOut.Bootstrap;
using BlockOut.Core;
using BlockOut.Gameplay;
using BlockOut.Infrastructure.Persistence;
using BlockOut.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace BlockOut.Tests.PlayMode
{
    public sealed class BlockOutPlayerJourneyTests
    {
        [UnityTest]
        public IEnumerator RealPages_ProgressPauseRestoreAndWin()
        {
            var root=BlockOutAppRoot.Ensure(null);
            var save=new BlockOutSaveService(new InMemoryProfileStore());
            save.Load();save.Profile.GuideCompleted=true;
            root.Services.Register(save);
            var gm=BlockOutAppBuilder.Build(root);
            var ui=root.Service<BlockOutUIManager>();
            yield return new WaitForSeconds(1);
            Assert.AreEqual(BlockOutScreenId.Home,ui.CurrentScreen);
            Assert.AreEqual("第 1 关",ui.HomeLevelTitle.text);
            Assert.IsFalse(ui.HomeDailyBtn.gameObject.activeInHierarchy);
            Assert.IsFalse(ui.HomeAchievementBtn.gameObject.activeInHierarchy);
            Assert.AreEqual(0,root.GetComponentsInChildren<BlockOutReferenceSkin>(true).Length);
            Capture(ui,"home");
            ui.HomeSkinBtn.onClick.Invoke();yield return null;
            Assert.AreEqual(BlockOutScreenId.Store,ui.CurrentScreen);Capture(ui,"store");
            ui.StoreBackBtn.onClick.Invoke();ui.HomeGalleryBtn.onClick.Invoke();yield return null;
            Assert.IsTrue(ui.RepeatItems[0].Button.interactable);Capture(ui,"levels");
            ui.RepeatItems[0].Button.onClick.Invoke();yield return new WaitForSeconds(1.4f);
            Assert.AreEqual(BlockOutScreenId.Board,ui.CurrentScreen);Capture(ui,"board");
            Capture(ui,"board-short",360,640);Capture(ui,"board-tall",390,932);
            var first=gm.Rules.Blocks.First(b=>b.Active && gm.Rules.CanMove(b));
            gm.HandleBlockTapped(first);yield return new WaitForSeconds(1.2f);
            Assert.Less(gm.RemainingBlocks,gm.CurrentLevel.Blocks.Count);
            string progress=ui.BoardProgressText.text;
            gm.LoadLevel(0,true);yield return new WaitForSeconds(1.4f);
            Assert.AreEqual(progress,ui.BoardProgressText.text,"恢复半局不能重置进度条");
            ui.BoardPauseBtn.onClick.Invoke();yield return new WaitForSeconds(.3f);
            Assert.IsTrue(gm.IsPaused);Capture(ui,"pause");
            ui.PauseResumeBtn.onClick.Invoke();Assert.IsFalse(gm.IsPaused);
            int guard=0;
            while(gm.RemainingBlocks>0 && guard++<100)
            {
                var block=gm.Rules.Blocks.FirstOrDefault(b=>b.Active && gm.Rules.CanMove(b));
                Assert.IsNotNull(block,"首关必须可无道具通关");
                gm.HandleBlockTapped(block);yield return new WaitForSeconds(1.1f);
            }
            yield return new WaitForSeconds(4);
            Assert.IsTrue(ui.IsLayerActive("SettlementLayer"));
            Assert.IsTrue(ui.SettleNoteText.gameObject.activeInHierarchy);
            Assert.IsNotNull(ui.SettleLevelImage.sprite);Capture(ui,"win");
            ui.SettleHomeBtn.onClick.Invoke();yield return null;
            Assert.AreEqual("第 2 关",ui.HomeLevelTitle.text);
            Capture(ui,"home-progress");
            ui.HomeCtaButton.onClick.Invoke();yield return new WaitForSeconds(1.4f);
            // Exercise failure and free revive through real gameplay and buttons.
            for(int attempt=0;attempt<3;attempt++)
            {
                var wrong=gm.Rules.Blocks.FirstOrDefault(b=>b.Active && !b.WrongMarked && !gm.Rules.CanMove(b));
                Assert.IsNotNull(wrong);
                gm.HandleBlockTapped(wrong);yield return new WaitForSeconds(1.8f);
            }
            Assert.AreEqual(BlockOutGameState.Lost,gm.State);
            Assert.IsTrue(ui.IsLayerActive("FailLayer"));Capture(ui,"fail");
            gm.Pause(); // 模拟失败期间看广告/切后台后的暂停状态。
            ui.FailReviveBtn.onClick.Invoke();yield return null;
            Assert.AreEqual(BlockOutGameState.Ready,gm.State);
            Assert.IsFalse(gm.IsPaused,"复活必须解除后台暂停锁");
            Assert.IsFalse(ui.IsLayerActive("FailLayer"));Assert.Greater(gm.Lives,0);
            // Unlocked hint actually consumes one item and resumes normal input.
            int hints=gm.Profile.HintCount;
            ui.HintSlot.Button.onClick.Invoke();yield return new WaitForSeconds(2);
            Assert.AreEqual(hints-1,gm.Profile.HintCount);
            ui.BoardPauseBtn.onClick.Invoke();ui.PauseQuitBtn.onClick.Invoke();
            Assert.IsTrue(ui.IsLayerActive("ConfirmLayer"));
            ui.ConfirmCancelBtn.onClick.Invoke();Assert.IsTrue(ui.IsLayerActive("PauseLayer"));
            ui.PauseQuitBtn.onClick.Invoke();ui.ConfirmOkBtn.onClick.Invoke();yield return null;
            Assert.AreEqual(BlockOutScreenId.Home,ui.CurrentScreen);Assert.IsFalse(gm.Profile.HasActiveRun);
            root.Shutdown();yield return null;
        }

        [UnityTest]
        public IEnumerator FirstLaunch_GuideThenToolsAndPurchase()
        {
            var root=BlockOutAppRoot.Ensure(null);
            var save=new BlockOutSaveService(new InMemoryProfileStore());save.Load();
            root.Services.Register(save);
            var gm=BlockOutAppBuilder.Build(root);var ui=root.Service<BlockOutUIManager>();
            yield return new WaitForSeconds(2);
            Assert.AreEqual(BlockOutScreenId.Board,ui.CurrentScreen);
            Assert.IsTrue(gm.GuideInputActive);Assert.IsNotNull(gm.GuideTarget);Capture(ui,"guide");
            gm.HandleBlockTapped(gm.GuideTarget);yield return new WaitForSeconds(1.5f);
            Assert.IsTrue(gm.Profile.GuideCompleted);Assert.IsFalse(gm.GuideInputActive);
            gm.LoadLevel(3);yield return new WaitForSeconds(1.4f);
            int blocks=gm.RemainingBlocks,magic=gm.Profile.MagicCount;
            ui.MagicSlot.Button.onClick.Invoke();yield return new WaitForSeconds(3);
            Assert.AreEqual(magic-1,gm.Profile.MagicCount);Assert.Less(gm.RemainingBlocks,blocks);
            Assert.IsFalse(gm.HasPendingMagic);
            int hammer=gm.Profile.HammerCount;
            ui.HammerSlot.Button.onClick.Invoke();Assert.IsTrue(gm.Tools.IsHammerSelecting);
            ui.HammerSlot.Button.onClick.Invoke();Assert.IsFalse(gm.Tools.IsHammerSelecting);
            Assert.AreEqual(hammer,gm.Profile.HammerCount,"取消选择不能扣道具");
            ui.HammerSlot.Button.onClick.Invoke();gm.HandleBlockTapped(gm.Rules.Blocks.First(b=>b.Active));
            yield return new WaitForSeconds(2.3f);Assert.AreEqual(hammer-1,gm.Profile.HammerCount);
            gm.CommitProfileMutation(()=>gm.Profile.Coins=600);
            int before=gm.Profile.HintCount;
            Assert.AreEqual(BlockOutGameManager.BlockOutPurchaseResult.Ok,gm.PurchaseTool(BlockOutToolId.Hint));
            Assert.AreEqual(300,gm.Profile.Coins);Assert.AreEqual(before+2,gm.Profile.HintCount);
            root.Shutdown();yield return null;
        }

        private static void Capture(BlockOutUIManager ui,string name,int width=390,int height=844)
        {
            var canvas=ui.GetScreenGO(ui.CurrentScreen).GetComponentInParent<Canvas>();
            var camera=Camera.main;
            var target=new RenderTexture(width,height,24);
            var oldMode=canvas.renderMode;var oldCamera=canvas.worldCamera;
            var oldTarget=camera.targetTexture;
            canvas.renderMode=RenderMode.ScreenSpaceCamera;canvas.worldCamera=camera;canvas.planeDistance=10;
            camera.targetTexture=target;Canvas.ForceUpdateCanvases();camera.Render();
            var oldActive=RenderTexture.active;RenderTexture.active=target;
            var texture=new Texture2D(width,height,TextureFormat.RGB24,false);
            texture.ReadPixels(new Rect(0,0,width,height),0,0);texture.Apply();
            string folder=Path.GetFullPath("design/ui/player-polish-20261117/runtime");Directory.CreateDirectory(folder);
            File.WriteAllBytes(Path.Combine(folder,name+".png"),texture.EncodeToPNG());
            RenderTexture.active=oldActive;camera.targetTexture=oldTarget;
            canvas.renderMode=oldMode;canvas.worldCamera=oldCamera;
            Object.Destroy(texture);Object.Destroy(target);
        }

        [UnityTest]
        public IEnumerator FailedSettlement_CanRetryWithoutLosingReward()
        {
            var root=BlockOutAppRoot.Ensure(null);var store=new InMemoryProfileStore();
            var save=new BlockOutSaveService(store);save.Load();save.Profile.GuideCompleted=true;
            root.Services.Register(save);var gm=BlockOutAppBuilder.Build(root);var ui=root.Service<BlockOutUIManager>();
            yield return new WaitForSeconds(.8f);ui.HomeCtaButton.onClick.Invoke();yield return new WaitForSeconds(1.4f);
            while(gm.RemainingBlocks>1)
            {
                gm.HandleBlockTapped(gm.Rules.Blocks.First(b=>b.Active && gm.Rules.CanMove(b)));
                yield return new WaitForSeconds(1.1f);
            }
            int coins=gm.Profile.Coins;
            LogAssert.Expect(LogType.Error,"[BlockOut] 通关结算保存失败，档案已回滚（进度/奖励未落盘）");
            gm.HandleBlockTapped(gm.Rules.Blocks.First(b=>b.Active));store.CommitShouldFail=true;
            yield return new WaitForSeconds(2);
            Assert.IsTrue(gm.SettlementSaveFailed);Assert.AreEqual(coins,gm.Profile.Coins);
            Assert.IsFalse(ui.SettleHomeBtn.interactable);Assert.IsFalse(ui.SettleCollectionBtn.interactable);
            Assert.IsTrue(ui.SettleNoteText.gameObject.activeInHierarchy);Capture(ui,"save-failed");
            store.CommitShouldFail=false;ui.SettleNextBtn.onClick.Invoke();yield return new WaitForSeconds(4);
            Assert.IsFalse(gm.SettlementSaveFailed);Assert.Greater(gm.Profile.Coins,coins);
            int rewarded=gm.Profile.Coins;gm.RetrySettlement();Assert.AreEqual(rewarded,gm.Profile.Coins);
            root.Shutdown();yield return null;
        }

        [UnityTest]
        public IEnumerator FailedExitOrRestart_KeepsPausedRunUntilSaveSucceeds()
        {
            var root=BlockOutAppRoot.Ensure(null);
            var store=new InMemoryProfileStore();
            var save=new BlockOutSaveService(store);save.Load();save.Profile.GuideCompleted=true;
            root.Services.Register(save);
            var gm=BlockOutAppBuilder.Build(root);var ui=root.Service<BlockOutUIManager>();
            yield return new WaitForSeconds(.8f);
            ui.HomeCtaButton.onClick.Invoke();yield return new WaitForSeconds(1.4f);
            ui.BoardPauseBtn.onClick.Invoke();yield return new WaitForSeconds(.3f);
            int token=gm.ActiveRunToken,remaining=gm.RemainingBlocks;
            string level=gm.Profile.RunLevelId;
            store.CommitShouldFail=true;
            ui.PauseRestartBtn.onClick.Invoke();ui.ConfirmOkBtn.onClick.Invoke();
            yield return new WaitForSeconds(.3f);
            Assert.AreEqual(token,gm.ActiveRunToken);
            Assert.AreEqual(remaining,gm.RemainingBlocks);
            Assert.IsTrue(ui.IsLayerActive("PauseLayer"));
            ui.PauseQuitBtn.onClick.Invoke();ui.ConfirmOkBtn.onClick.Invoke();
            yield return new WaitForSeconds(.3f);
            Assert.AreEqual(BlockOutScreenId.Board,ui.CurrentScreen);
            Assert.IsTrue(gm.IsPaused);Assert.IsTrue(gm.Profile.HasActiveRun);
            Assert.AreEqual(level,gm.Profile.RunLevelId);
            store.CommitShouldFail=false;
            ui.PauseQuitBtn.onClick.Invoke();ui.ConfirmOkBtn.onClick.Invoke();
            yield return new WaitForSeconds(.3f);
            Assert.AreEqual(BlockOutScreenId.Home,ui.CurrentScreen);
            Assert.IsFalse(gm.Profile.HasActiveRun);
            root.Shutdown();yield return null;
        }

        [UnityTearDown]
        public IEnumerator Cleanup()
        {
            if(BlockOutAppRoot.Instance!=null)BlockOutAppRoot.Instance.Shutdown();
            yield return null;
        }

        [UnityTest]
        public IEnumerator ChapterSelectionAndSettings_ReturnToExpectedContext()
        {
            var root=BlockOutAppRoot.Ensure(null);
            var save=new BlockOutSaveService(new InMemoryProfileStore());save.Load();
            save.Profile.GuideCompleted=true;root.Services.Register(save);
            var gm=BlockOutAppBuilder.Build(root);var ui=root.Service<BlockOutUIManager>();
            yield return new WaitForSeconds(.8f);
            ui.HomeGalleryBtn.onClick.Invoke();yield return null;
            ui.collectionScroll.verticalNormalizedPosition=0;
            ui.ChapterItems[0].Button.onClick.Invoke();yield return null;
            Assert.That(ui.collectionScroll.verticalNormalizedPosition,Is.EqualTo(1f).Within(.01f));
            Assert.IsTrue(ui.RepeatItems[0].Button.interactable);
            ui.RepeatItems[0].Button.onClick.Invoke();yield return new WaitForSeconds(1.4f);
            ui.BoardPauseBtn.onClick.Invoke();ui.PauseSettingsBtn.onClick.Invoke();
            Assert.IsTrue(gm.IsPaused);
            Assert.IsFalse(ui.IsLayerActive("PauseLayer"));
            Assert.IsTrue(ui.IsLayerActive("SettingsLayer"));
            ui.SettingsAboutBtn.onClick.Invoke();ui.AboutCloseBtn.onClick.Invoke();
            Assert.IsTrue(ui.IsLayerActive("SettingsLayer"));
            ui.SettingsCloseBtn.onClick.Invoke();
            Assert.IsTrue(ui.IsLayerActive("PauseLayer"));Assert.IsTrue(gm.IsPaused);
            ui.PauseResumeBtn.onClick.Invoke();
            Assert.IsFalse(gm.IsPaused);Assert.IsFalse(gm.ModalPopupOpen);
            ui.BoardPauseBtn.onClick.Invoke();ui.PauseQuitBtn.onClick.Invoke();
            ui.ConfirmOkBtn.onClick.Invoke();yield return null;
            Assert.AreEqual(BlockOutScreenId.Home,ui.CurrentScreen);
            foreach(var layer in new[]{"PauseLayer","SettingsLayer","AboutLayer","ConfirmLayer","FailLayer","SettlementLayer"})
                Assert.IsFalse(ui.IsLayerActive(layer),layer);
        }

    }
}
