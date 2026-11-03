using System;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;
using BlockOut.Config;
using BlockOut.Core;
using BlockOut.Gameplay;
namespace BlockOut.UI
{
    internal sealed class BlockOutHudController
    {
        private readonly BlockOutUIController owner;
        internal BlockOutHudController(BlockOutUIController owner) { this.owner=owner; }
        internal void OnBlockWrongMarked(BlockOutBlockData block, bool isRepeat)
        {
            // 受阻反馈：生命模式扣心并提示；计时模式只震动（HUD 互斥，不扣心）。
            // R08：重复误点仍反馈，但文案区分"已扣 1 颗心"与"重复误点，不重复扣心"。
            if (owner.GM.UseTimeFailMode)
                owner.UI.ShowToast(isRepeat ? "受阻 · 重复误点，计时模式仅震动" : "受阻 · 计时模式仅震动，沿箭头方向才能飞出");
            else
                owner.UI.ShowToast(isRepeat ? "受阻 · 重复误点，不重复扣心" : "受阻 · 已扣 1 颗心，沿箭头方向才能飞出");
        }
        internal void RefreshHearts(int lives)
        {
            if (owner.UI.BoardHearts == null) return;
            for (int i = 0; i < owner.UI.BoardHearts.Length; i++)
            {
                var heart = owner.UI.BoardHearts[i];
                if (heart == null) continue;
                bool alive = i < lives;
                heart.sprite=BlockOutIconFactory.Asset(alive ? "heart" : "heart_disabled");
                heart.color=Color.white;
            }
        }
        internal void RefreshTimer(float seconds)
        {
            if (owner.UI.BoardTimerText == null) return;
            int total = Mathf.Max(0, Mathf.CeilToInt(seconds));
            owner.UI.BoardTimerText.text = string.Format("{0:00}:{1:00}", total / 60, total % 60);
        }
        internal void RefreshCoins(int coins)
        {
            if (owner.UI.HomeCoinText != null) owner.UI.HomeCoinText.text = coins.ToString();
            if (owner.UI.StoreCoinText != null) owner.UI.StoreCoinText.text = coins.ToString();
        }
        internal void RefreshHintPill()
        {
            if (owner.UI.BoardHintPill == null) return;
            bool hammer = owner.GM.Tools != null && owner.GM.Tools.IsHammerSelecting;
            owner.UI.BoardHintPill.text = hammer ? BlockOutUIController.HintPillHammer : BlockOutUIController.HintPillNormal;
        }
        internal void RefreshToolStates()
        {
            RefreshToolSlot(owner.UI.HintSlot, BlockOutToolId.Hint, BlockOutContentConfig.HintUnlockLevel, "轮换高亮可飞块");
            RefreshToolSlot(owner.UI.HammerSlot, BlockOutToolId.Hammer, BlockOutContentConfig.HammerUnlockLevel, "消除任意在场块");
            RefreshToolSlot(owner.UI.MagicSlot, BlockOutToolId.Magic, BlockOutContentConfig.MagicUnlockLevel, "飞走最多 " + BlockOutContentConfig.MagicTargetCount + " 块");
            RefreshHintPill();
        }
        internal void RefreshToolSlot(ToolSlotRefs slot, BlockOutToolId tool, int unlockLevel, string condNormal)
        {
            if (slot == null || owner.GM.Tools == null) return;
            bool unlocked = owner.GM.IsToolUnlocked(tool);
            int count = owner.GM.Tools.GetCount(tool);
            if(tool==BlockOutToolId.Magic && owner.GM.HasPendingMagic)
            {
                SetSlotVisual(slot,false,count,"继续未完成施法 · 不重复扣除");slot.Button.interactable=true;return;
            }

            if (!unlocked)
            {
                SetSlotVisual(slot, true, 0, "第 " + unlockLevel + " 关解锁");
                // 不能置灰禁用：设计要求点击有反馈（轻抖 + 提示解锁关卡），禁用后点击事件根本不触发（P2-4）
                slot.Button.interactable = true;
                return;
            }
            if (count <= 0)
            {
                SetSlotVisual(slot, false, 0, "数量不足 · 商店可购");
                // 同上：零库存也要能点，点了提示"库存不足"，不能静默无响应（P2-4）
                slot.Button.interactable = true;
                return;
            }
            // 锤子选择态：条件文案切换为操作提示
            string cond = condNormal;
            if (tool == BlockOutToolId.Hammer && owner.GM.Tools.IsHammerSelecting)
                cond = "选择要消除的方块";
            SetSlotVisual(slot, false, count, cond);
            slot.Button.interactable = true;   // 暂停/忙碌态在点击处理里拦截（P2-4）
        }
        internal bool TryUseTool(BlockOutToolId tool, Func<bool> action, Func<bool> cancelAction = null)
        {
            if (owner.GM == null || owner.GM.Tools == null) return false;

            // 暂停 / 结算中 / 失败 / 施法忙态：阻止实际操作，也不弹库存类提示（P2-4 第 4 点）
            if (!owner.GM.CanStartTool)
                return false;

            if (!owner.GM.IsToolUnlocked(tool))
            {
                owner.UI.ShowToast("第 " + BlockOutUIController.ToolUnlockLevel(tool) + " 关解锁");
                owner.UI.ShakeSlot(tool);
                return false;
            }
            if(owner.GM.HasPendingMagic)
            {
                if(tool==BlockOutToolId.Magic)return action();
                owner.UI.ShowToast("请先点击魔法继续上次施法");return false;
            }
            if (owner.GM.Tools.GetCount(tool) <= 0)
            {
                string name=tool==BlockOutToolId.Hint ? "提示" : tool==BlockOutToolId.Hammer ? "锤子" : "魔法";
                int run=owner.GM.CurrentLevelIndex;
                owner.Dialogs.AskConfirm("补充"+name,BlockOutContentConfig.ToolPackCost+" 金币购买 "+BlockOutContentConfig.ToolPackAmount+" 个，购买后使用一次。",()=>
                {
                    if(owner.GM.CurrentLevelIndex!=run || !owner.GM.CanStartTool)return;
                    var result=owner.GM.PurchaseTool(tool);
                    if(result==BlockOutGameManager.BlockOutPurchaseResult.Ok) { action();RefreshToolStates(); }
                    else owner.UI.ShowToast(result==BlockOutGameManager.BlockOutPurchaseResult.InsufficientCoins ? "金币不足" : "购买失败，请重试");
                });
                return false;
            }

            // 锤子处于选择态时，本次点击是"取消"
            if (cancelAction != null && tool == BlockOutToolId.Hammer && owner.GM.Tools.IsHammerSelecting)
            {
                if (!cancelAction()) return false;
                owner.UI.ShowToast("已取消选择");
                return true;
            }

            if (!action())
            {
                // 走到这里说明"确实可执行但当前局面没有目标"，这才是"没有可用目标"（P2-4 第 3 点）
                owner.UI.ShowToast("当前没有可飞出的方块");
                return false;
            }
            return true;
        }
        internal void SetSlotVisual(ToolSlotRefs slot, bool locked, int count, string cond)
        {
            if (slot.Icon != null)
                slot.Icon.color = (!locked && count > 0)
                    ? Color.white
                    : BlockOutDesignTokens.GrayIconLocked;
            if (slot.CountBadge != null) slot.CountBadge.SetActive(!locked);
            if (slot.CountText != null) slot.CountText.text = count.ToString();
            if (slot.LockBadge != null) slot.LockBadge.SetActive(locked);
            if (slot.CondText != null) slot.CondText.text = cond;
        }
    }
}
