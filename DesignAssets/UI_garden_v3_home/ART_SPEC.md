# 首页美术出图规格（给生图/美术用）

目标：一张**干净背景**就能把首页还原度从 ~60% 拉到 ~90%。UI 组件已就绪，不需要重画。

---

## 1. 背景图（最关键，1 张）

| 项 | 要求 |
| --- | --- |
| 尺寸 | 1080×1920（最好 2160×3840） |
| 内容 | **只有场景，没有任何 UI、按钮、数字、文字** |
| 风格 | 3D 软胶绘本 / clay render，柔和体积光，暖阳光，浅景深；参考图同款（奶油色 + 马卡龙色 + 草绿） |
| 构图 | 左侧 0–38%：石造拱廊建筑（拱券、柱子、马赛克画、台阶），被画面左边缘裁切<br>右侧 68–100%：木质画架 + 画布（画布上是像素画）<br>中央：纵向浅色石径，从底部延伸至地平线（约 y=58%）<br>前景 60–100%：成片花丛（大朵花 + 叶片层次，高低错落，左右两侧密、中间让开石径）<br>上方 0–45%：天空 + 云（云要分离、有体积，不要糊成一条） |
| 禁止 | 不要 UI、按钮、关卡节点、文字、水印；不要在中央放主体物（要被 UI 盖住） |
| 色彩 | 天空 #6EC6F0 → #CFEAF7；草地 #7CBB4F；石径 #F0E1BC；建筑奶油 #FBF1D8；花：粉 #F27FB0 / 黄 #FFD766 / 白 #FFF6E8 |

**提示词参考**
```
3D clay render, storybook mobile game background, soft pastel garden,
warm afternoon sunlight from upper left, shallow depth of field,
left: cream stone arcade building with arched doorway, columns and a mosaic painting, cropped by frame edge,
right: wooden easel with a pixel-art canvas,
center: vertical light stone path leading to a soft green horizon,
foreground: lush flower beds with big rounded petals and leaves on both sides,
sky: bright blue with separated volumetric clouds,
no UI, no buttons, no text, no watermark, vertical 9:16, 1080x1920
```

---

## 2. 组件图（可选，想更贴合再做）

现状：节点/按钮是 three.js 渲染的，材质语言对，但比参考更"塑料"。
如果要从 75% 提到 95%，按下面出图（**透明底 PNG**，每张单独）：

| 文件 | 尺寸 | 说明 |
| --- | --- | --- |
| `node_locked` | 600×600 | 灰色未解锁节点，无数字 |
| `node_current` | 600×600 | 绿色当前节点，带暖色外发光，无数字、无下方箭头 |
| `node_star` | 600×600 | 紫色节点，无数字、无星徽章 |
| `node_fail` | 600×600 | 珊瑚红节点，无数字、无骷髅 |
| `btn_primary` | 1200×500 | 绿色主按钮，奶油外框 + 细金线，无文字 |
| `badge_lock` / `badge_star` / `badge_skull` | 200×200 | 独立徽章 |

关键要求：**不要烘焙任何文字/数字**；边缘留 8px 透明边；光照统一从左上。

---

## 3. 交付方式

- 背景：放到 `art/bg_source.png`（或 `.jpg`），任意尺寸会自动 cover 裁切；我重跑 `python tools/compose.py`（1 分钟）。
- 组件：放到 `art/` 按上表命名，同样重跑。
- 我会自动：按参考坐标落位、叠加中文/数字、导出 1080×1920 还原图与对照图。
