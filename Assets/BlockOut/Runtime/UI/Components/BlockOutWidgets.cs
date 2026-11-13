using System;
using UnityEngine;
using UnityEngine.UI;

namespace BlockOut.UI
{
    public enum UIAnchorPreset
    {
        TopLeft, TopCenter, TopRight,
        MiddleLeft, MiddleCenter, MiddleRight,
        BottomLeft, BottomCenter, BottomRight,
        Stretch,
    }

    /// <summary>
    /// 通用 UGUI 组件工厂：按 Docs/DesignSystem.md v6 Token 构建（无 emoji、无占位文本）。
    /// 按钮/胶囊/Toast/弹窗框使用持久化 9-slice Sprite（§4 组件库）。
    /// </summary>
    public static class BlockOutWidgets
    {
        public static void EnsureReady()
        {
            BlockOutDesignTokens.EnsureFont();
        }

        public static void ApplyAnchor(RectTransform rt, UIAnchorPreset preset)
        {
            switch (preset)
            {
                case UIAnchorPreset.TopLeft: rt.anchorMin = new Vector2(0, 1); rt.anchorMax = new Vector2(0, 1); rt.pivot = new Vector2(0, 1); break;
                case UIAnchorPreset.TopCenter: rt.anchorMin = new Vector2(0.5f, 1); rt.anchorMax = new Vector2(0.5f, 1); rt.pivot = new Vector2(0.5f, 1); break;
                case UIAnchorPreset.TopRight: rt.anchorMin = new Vector2(1, 1); rt.anchorMax = new Vector2(1, 1); rt.pivot = new Vector2(1, 1); break;
                case UIAnchorPreset.MiddleLeft: rt.anchorMin = new Vector2(0, 0.5f); rt.anchorMax = new Vector2(0, 0.5f); rt.pivot = new Vector2(0, 0.5f); break;
                case UIAnchorPreset.MiddleCenter: rt.anchorMin = new Vector2(0.5f, 0.5f); rt.anchorMax = new Vector2(0.5f, 0.5f); rt.pivot = new Vector2(0.5f, 0.5f); break;
                case UIAnchorPreset.MiddleRight: rt.anchorMin = new Vector2(1, 0.5f); rt.anchorMax = new Vector2(1, 0.5f); rt.pivot = new Vector2(1, 0.5f); break;
                case UIAnchorPreset.BottomLeft: rt.anchorMin = new Vector2(0, 0); rt.anchorMax = new Vector2(0, 0); rt.pivot = new Vector2(0, 0); break;
                case UIAnchorPreset.BottomCenter: rt.anchorMin = new Vector2(0.5f, 0); rt.anchorMax = new Vector2(0.5f, 0); rt.pivot = new Vector2(0.5f, 0); break;
                case UIAnchorPreset.BottomRight: rt.anchorMin = new Vector2(1, 0); rt.anchorMax = new Vector2(1, 0); rt.pivot = new Vector2(1, 0); break;
                default: rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.pivot = new Vector2(0.5f, 0.5f); break;
            }
        }

        /// <summary>放置元素：x/y 为相对锚点的偏移（Top* 预设 y 向下为正）。</summary>
        public static RectTransform Place(Transform parent, string name, UIAnchorPreset preset, float x = 0, float y = 0, float w = 0, float h = 0)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = (RectTransform)go.transform;
            ApplyAnchor(rt, preset);
            float posY = y;
            if (preset == UIAnchorPreset.TopLeft || preset == UIAnchorPreset.TopCenter || preset == UIAnchorPreset.TopRight)
                posY = -y;
            rt.anchoredPosition = new Vector2(x, posY);
            rt.sizeDelta = new Vector2(w, h);
            return rt;
        }

        public static Image Panel(Transform parent, string name, Color color, UIAnchorPreset preset = UIAnchorPreset.Stretch,
            float x = 0, float y = 0, float w = 0, float h = 0)
        {
            var rt = Place(parent, name, preset, x, y, w, h);
            var img = rt.gameObject.AddComponent<Image>();
            img.color = color;
            return img;
        }

        public static Image SpriteImage(Transform parent, string name, Sprite sprite, UIAnchorPreset preset,
            float x = 0, float y = 0, float w = 0, float h = 0)
        {
            var rt = Place(parent, name, preset, x, y, w, h);
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = sprite;
            return img;
        }

        public static Text Label(Transform parent, string name, string text, int fontSize, int weight, Color color,
            TextAnchor anchor, UIAnchorPreset preset = UIAnchorPreset.Stretch, float x = 0, float y = 0, float w = 0, float h = 0)
        {
            var rt = Place(parent, name, preset, x, y, w, h);
            var txt = rt.gameObject.AddComponent<Text>();
            txt.font = BlockOutDesignTokens.UIFont;
            txt.text = text ?? string.Empty;
            txt.fontSize = fontSize;
            txt.fontStyle = weight >= 700 ? FontStyle.Bold : FontStyle.Normal;
            txt.alignment = anchor;
            txt.color = color;
            txt.horizontalOverflow = HorizontalWrapMode.Overflow;
            txt.verticalOverflow = VerticalWrapMode.Overflow;
            txt.raycastTarget = false;
            return txt;
        }

        /// <summary>主 CTA（v6 巧克力棕实底 + 可选图标/副文案/右箭头）。</summary>
        public static Button CoralButton(Transform parent, string name, string title, string sub, Action onClick = null,
            Sprite icon = null, bool arrow = true)
        {
            var rt = Place(parent, name, UIAnchorPreset.TopLeft, 0, 0, 342, 88);
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = BlockOutIconFactory.RoundedSlice(24f, BlockOutDesignTokens.ActionPrimary,
                Color.clear, 0f, BlockOutDesignTokens.ActionHover);
            img.color=BlockOutDesignTokens.ActionPrimary;
            img.type = Image.Type.Sliced;
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = img;
            btn.transition = Selectable.Transition.None;
            if (onClick != null) btn.onClick.AddListener(() => onClick());

            float textLeft = 24f;
            if (icon != null)
            {
                var iconBg = Panel(rt, "IconBg", BlockOutDesignTokens.White, UIAnchorPreset.MiddleLeft, 22, 0, 44, 44);
                iconBg.sprite = BlockOutIconFactory.RoundedSlice(14f, BlockOutDesignTokens.White, Color.clear, 0f, null);
                iconBg.type = Image.Type.Sliced;
                var iconImg = SpriteImage(rt, "Icon", icon, UIAnchorPreset.MiddleLeft, 30, 0, 28, 28);
                iconImg.color = BlockOutDesignTokens.ActionPrimary;
                textLeft = 82f;
            }
            var titleTxt = Label(rt, "Title", title, BlockOutDesignTokens.FontCtaTitle, 900, BlockOutDesignTokens.White,
                TextAnchor.MiddleCenter);
            titleTxt.rectTransform.offsetMin = new Vector2(textLeft, sub != null ? 32 : 8);
            titleTxt.rectTransform.offsetMax = new Vector2(arrow ? -48 : -24, -8);
            if (sub != null)
            {
                var subtitle = Label(rt, "Sub", sub, BlockOutDesignTokens.FontCtaSub, 400,
                    new Color(1f, 1f, 1f, .88f), TextAnchor.MiddleCenter);
                subtitle.rectTransform.offsetMin = new Vector2(textLeft, 12);
                subtitle.rectTransform.offsetMax = new Vector2(arrow ? -48 : -24, -52);
            }
            if (arrow)
                SpriteImage(rt, "Arrow", BlockOutIconFactory.PlayIcon(), UIAnchorPreset.MiddleRight, -30, 0, 14, 18);
            return btn;
        }

        /// <summary>次级按钮（白底 + 暖棕描边 + 可可文字）。</summary>
        public static Button SecondaryButton(Transform parent, string name, string label, Action onClick,
            UIAnchorPreset preset = UIAnchorPreset.TopCenter, float x = 0, float y = 0, float w = 232, float h = 38)
        {
            var rt = Place(parent, name, preset, x, y, w, h);
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = BlockOutIconFactory.RoundedSlice(19f, BlockOutDesignTokens.White,
                BlockOutDesignTokens.StrokeBoard, 1.5f, null);
            img.type = Image.Type.Sliced;
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = img;
            btn.transition = Selectable.Transition.None;
            if (onClick != null) btn.onClick.AddListener(() => onClick());
            Label(rt, "Text", label, BlockOutDesignTokens.FontButton, 800, BlockOutDesignTokens.TextCocoa, TextAnchor.MiddleCenter);
            return btn;
        }

        /// <summary>胶囊（金币/剩余块/计时）。</summary>
        public static RectTransform Pill(Transform parent, string name, float w, float h, Color fill, Color stroke,
            UIAnchorPreset preset, float x, float y)
        {
            var rt = Place(parent, name, preset, x, y, w, h);
            var img = rt.gameObject.AddComponent<Image>();
            float radius = h * 0.5f;
            img.sprite = BlockOutIconFactory.RoundedSlice(radius, fill, stroke, 1.5f, null);
            img.color=fill;
            img.type = Image.Type.Sliced;
            return rt;
        }

        /// <summary>圆形图标按钮（暂停/设置等）。</summary>
        public static Button CircleIconButton(Transform parent, string name, Sprite icon, float diameter, Action onClick,
            Color bg, Color stroke)
        {
            var rt = Place(parent, name, UIAnchorPreset.TopLeft, 0, 0, diameter, diameter);
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = BlockOutIconFactory.Circle(bg, stroke, 1.5f);
            img.color=bg;
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = img;
            btn.transition = Selectable.Transition.None;
            if (onClick != null) btn.onClick.AddListener(() => onClick());
            var iconImg = SpriteImage(rt, "Icon", icon, UIAnchorPreset.Stretch);
            iconImg.rectTransform.offsetMin = new Vector2(diameter * 0.28f, diameter * 0.28f);
            iconImg.rectTransform.offsetMax = new Vector2(-diameter * 0.28f, -diameter * 0.28f);
            iconImg.color = BlockOutDesignTokens.TextCocoa;
            return btn;
        }

        /// <summary>底部导航项。</summary>
        public static Button NavItem(Transform parent, string name, Sprite icon, string label, bool active, Action onClick)
        {
            var rt = Place(parent, name, UIAnchorPreset.Stretch);
            var hit = rt.gameObject.AddComponent<Image>();
            hit.color = Color.clear;
            var color = active ? BlockOutDesignTokens.ActionPrimary : BlockOutDesignTokens.GrayLocked;
            var iconImg = SpriteImage(rt, "Icon", icon, UIAnchorPreset.TopCenter, 0, 10, 24, 24);
            iconImg.color = color;
            var txt = Label(rt, "Text", label, BlockOutDesignTokens.FontNav, 800, color, TextAnchor.MiddleCenter,
                UIAnchorPreset.TopCenter, 0, 40, 80, 12);
            txt.rectTransform.anchoredPosition = new Vector2(0, -42);
            var dot = Panel(rt, "Dot", color, UIAnchorPreset.BottomCenter, 0, 4, 4, 4);
            dot.sprite = BlockOutIconFactory.Circle(color, Color.clear, 0f);
            dot.gameObject.SetActive(active);
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = hit;
            iconImg.raycastTarget = false;
            btn.transition = Selectable.Transition.None;
            if (onClick != null) btn.onClick.AddListener(() => onClick());
            return btn;
        }

        /// <summary>底部导航项激活态切换（图标 / 文字 / 圆点三处同步）。</summary>
        public static void SetNavActive(Button navBtn, bool active)
        {
            if (navBtn == null) return;
            var on = BlockOutDesignTokens.ActionPrimary;
            var off = BlockOutDesignTokens.GrayLocked;
            var icon = navBtn.transform.Find("Icon")?.GetComponent<Image>();
            if (icon != null) icon.color = active ? on : off;
            var txt = navBtn.transform.Find("Text")?.GetComponent<Text>();
            if (txt != null) txt.color = active ? on : off;
            var dot = navBtn.transform.Find("Dot");
            if (dot != null) dot.gameObject.SetActive(active);
        }

        /// <summary>开关行（设置页）：标签 + 轨道 + 滑块。</summary>
        public static Button SwitchRow(Transform parent, string label, string name, bool initial, Action<bool> onChanged)
        {
            var rt = Place(parent, name, UIAnchorPreset.TopLeft, 0, 0, 302, 52);
            var hit = rt.gameObject.AddComponent<Image>();
            hit.color = Color.clear;
            Label(rt, "Label", label, BlockOutDesignTokens.FontButton, 400, BlockOutDesignTokens.TextCocoa,
                TextAnchor.MiddleLeft, UIAnchorPreset.MiddleLeft, 0, 0, 150, 24);
            var track = Panel(rt, "Track", initial ? BlockOutDesignTokens.ActionPrimary : BlockOutDesignTokens.GrayIconLocked,
                UIAnchorPreset.MiddleRight, -8, 0, 44, 24);
            track.sprite = BlockOutIconFactory.RoundedSlice(12f, initial ? BlockOutDesignTokens.ActionPrimary : BlockOutDesignTokens.GrayIconLocked,
                Color.clear, 0f, null);
            track.type = Image.Type.Sliced;
            var knob = Panel(rt, "Knob", BlockOutDesignTokens.White, UIAnchorPreset.MiddleRight,
                initial ? -10 : -30, 0, 20, 20);
            knob.sprite = BlockOutIconFactory.Circle(BlockOutDesignTokens.White, Color.clear, 0f);
            var btn = rt.gameObject.AddComponent<Button>();
            btn.targetGraphic = hit;
            track.raycastTarget = false;
            knob.raycastTarget = false;
            btn.transition = Selectable.Transition.None;
            bool value = initial;
            btn.onClick.AddListener(() =>
            {
                value = !value;
                var on = value ? BlockOutDesignTokens.ActionPrimary : BlockOutDesignTokens.GrayIconLocked;
                track.color = on;
                track.sprite = BlockOutIconFactory.RoundedSlice(12f, on, Color.clear, 0f, null);
                knob.rectTransform.anchoredPosition = new Vector2(value ? -10 : -30, 0);
                if (onChanged != null) onChanged(value);
            });
            return btn;
        }

        /// <summary>Toast 背景（v6 深可可 88% 圆角条，9-slice）。</summary>
        public static RectTransform ToastBar(Transform parent, string name)
        {
            var rt = Place(parent, name, UIAnchorPreset.BottomCenter, 0, 0, 460, 32);
            var img = rt.gameObject.AddComponent<Image>();
            var c = BlockOutDesignTokens.MaskWarm; c.a = 0.88f;
            img.sprite = BlockOutIconFactory.RoundedSlice(16f, c, Color.clear, 0f, null);
            img.color=c;
            img.type = Image.Type.Sliced;
            img.raycastTarget = false;
            var txt = Label(rt, "Text", string.Empty, BlockOutDesignTokens.FontToast, 400, BlockOutDesignTokens.White, TextAnchor.MiddleCenter);
            txt.rectTransform.offsetMin = new Vector2(16, 0);
            txt.rectTransform.offsetMax = new Vector2(-16, 0);
            return rt;
        }

        /// <summary>卡片（surface 底 + 暖棕描边，9-slice 圆角 24）。</summary>
        public static Image Card(Transform parent, string name, float w, float h,
            UIAnchorPreset preset = UIAnchorPreset.MiddleCenter, float x = 0, float y = 0)
        {
            var rt = Place(parent, name, preset, x, y, w, h);
            var img = rt.gameObject.AddComponent<Image>();
            img.sprite = BlockOutIconFactory.RoundedSlice(24f, BlockOutDesignTokens.SurfaceCard,
                BlockOutDesignTokens.StrokeWarm, 2f, null);
            img.color=BlockOutDesignTokens.SurfaceCard;
            img.type = Image.Type.Sliced;
            return img;
        }

        /// <summary>弹窗遮罩（v6 40% 可可 #3B2A24）。</summary>
        public static Image Dim(Transform parent, string name)
        {
            var rt = Place(parent, name, UIAnchorPreset.Stretch);
            var c = BlockOutDesignTokens.MaskWarm;
            c.a = 0.40f;
            var img = rt.gameObject.AddComponent<Image>();
            img.color = c;
            img.raycastTarget = true;
            return img;
        }

        /// <summary>外部设置 SwitchRow 开关值（打开设置层时同步真实设置）。</summary>
        public static void SetSwitch(Button switchBtn, bool value)
        {
            if (switchBtn == null) return;
            var track = switchBtn.transform.Find("Track")?.GetComponent<Image>();
            var knob = switchBtn.transform.Find("Knob")?.GetComponent<RectTransform>();
            var on = BlockOutDesignTokens.ActionPrimary;
            var off = BlockOutDesignTokens.GrayIconLocked;
            if (track != null)
            {
                track.color = value ? on : off;
                track.sprite = BlockOutIconFactory.RoundedSlice(12f, value ? on : off, Color.clear, 0f, null);
            }
            if (knob != null)
                knob.anchoredPosition = new Vector2(value ? -10 : -30, 0);
        }
    }
}
