using System;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;
namespace BlockOut.UI
{
    internal sealed class BlockOutStoreController
    {
        private readonly BlockOutUIController owner;
        internal BlockOutStoreController(BlockOutUIController owner) { this.owner=owner; }
        internal void RefreshStore()
        {
            if (owner.GM == null || owner.GM.Profile == null) return;
            if (owner.UI.StoreCoinText != null) owner.UI.StoreCoinText.text = owner.GM.Profile.Coins.ToString();
            if (owner.UI.StoreProducts == null) return;

            int coins = owner.GM.Profile.Coins;
            bool insufficient = coins < BlockOutContentConfig.ToolPackCost;
            for (int i = 0; i < owner.UI.StoreProducts.Length; i++)
            {
                var p = owner.UI.StoreProducts[i];
                if (p == null) continue;
                int index=i; owner.Bind(p.BuyBtn,()=>OnStoreBuyClicked(index));
                int count = p.Tool == BlockOutToolId.Hint ? owner.GM.Profile.HintCount
                    : p.Tool == BlockOutToolId.Hammer ? owner.GM.Profile.HammerCount : owner.GM.Profile.MagicCount;
                bool unlocked = owner.GM.IsToolUnlocked(p.Tool);
                string desc;
                if (!unlocked)
                    desc = "第 " + BlockOutUIController.StoreUnlockLevel(p.Tool) + " 关解锁 · 解锁前暂不可购买";
                else
                    desc = BlockOutUIController.StoreDesc(p.Tool) + " · 库存 " + count;
                // 四态：未解锁（禁买）/ 金币不足（置灰）/ 购买中（禁用）/ 可购买
                bool buying = owner.storePurchasing[BlockOutUIController.StoreIndex(p.Tool)];
                bool canBuy = unlocked && !insufficient && !buying;
                SetProductVisual(p, unlocked, desc, canBuy, buying);
            }
        }
        internal void SetProductVisual(StoreProductRefs p, bool unlocked, string desc, bool canBuy, bool buying)
        {
            if (p.CardImg != null)
                p.CardImg.color = unlocked ? BlockOutDesignTokens.SurfaceCard : new Color(0.953f, 0.925f, 0.894f);
            if (p.IconImg != null)
                p.IconImg.color = unlocked ? Color.white : BlockOutDesignTokens.GrayIconLocked;
            if (p.LockBadge != null) p.LockBadge.SetActive(!unlocked);
            if (p.NameText != null)
                p.NameText.color = unlocked ? BlockOutDesignTokens.TextCocoa : BlockOutDesignTokens.GrayLocked;
            if (p.DescText != null) p.DescText.text = desc;
            if(p.CoinText!=null) p.CoinText.text=BlockOutContentConfig.ToolPackCost+" 金币";
            if (p.CoinText != null)
                p.CoinText.color = unlocked ? BlockOutDesignTokens.GoldText : BlockOutDesignTokens.GrayLocked;
            if (p.BuyBtn != null) p.BuyBtn.interactable = canBuy;
            if (p.BuyText != null) p.BuyText.text = !unlocked ? "禁买" : (buying ? "…" : "购买");
            if (p.BuyBtn != null && p.BuyBtn.targetGraphic is Image buyImg)
                buyImg.color = canBuy ? Color.white : new Color(0.91f, 0.86f, 0.82f);
        }
        internal void OnStoreBuyClicked(int idx)
        {
            if (owner.UI.StoreProducts == null || idx < 0 || idx >= owner.UI.StoreProducts.Length) return;
            var p = owner.UI.StoreProducts[idx];
            if (p == null) return;
            if (owner.storePurchasing[(int)p.Tool]) return;                       // 防重复点击
            if (!owner.GM.IsToolUnlocked(p.Tool)) return;                 // 未解锁禁买（按钮本就禁用）
            if (owner.GM.Profile.Coins < BlockOutContentConfig.ToolPackCost)
            {
                owner.UI.ShowToast("金币不足 · 通关可获取");                // 仅提示，不扣币不跳
                return;
            }
            owner.storePurchasing[(int)p.Tool] = true;
            RefreshStore();                                         // 立即进入"购买中"禁用态
            owner.StartCoroutine(StorePurchaseRoutine(idx, p.Tool));
        }
        internal IEnumerator StorePurchaseRoutine(int idx, BlockOutToolId tool)
        {
            yield return new WaitForSeconds(0.4f);                  // 保留短暂购买反馈；实际交易仅在本地执行
            var res = owner.GM.PurchaseTool(tool);                       // 原子扣币+发奖，防重复扣币/发奖
            owner.storePurchasing[(int)tool] = false;
            switch (res)
            {
                case BlockOutGameManager.BlockOutPurchaseResult.Ok:
                    owner.GM.Settings.PlaySound("sfx_coin");
                    owner.UI.ShowToast("购买成功");
                    break;
                case BlockOutGameManager.BlockOutPurchaseResult.InsufficientCoins:
                    owner.UI.ShowToast("金币不足");
                    break;
                case BlockOutGameManager.BlockOutPurchaseResult.Locked:
                    owner.UI.ShowToast("道具未解锁");
                    break;
                default:
                    owner.UI.ShowToast("购买失败，请重试");
                    break;
            }
            RefreshStore();
            owner.Hud.RefreshCoins(owner.GM.Profile.Coins);
        }
    }
}
