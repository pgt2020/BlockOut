# BlockOut 首页与结算 · 代码对齐分析（出图前必读）

> **产品裁决（2026-11）**：结算揭晓以 **方案 A** 为准 —— 弹层主槽位为单关 `SettleLevelImage`（`LoadCompletionImage`），12 格 region 网格在结算层默认隐藏；棋盘层 `CompletionPresentation` 为先播演出。  
> 目的：在改视觉或出 HTML/Figma **之前**，锁定程序真实行为。  
> 依据：`BlockOutHomeController`、`BlockOutDialogsController`、`BlockOutUIManager.Authoring`、`BlockOutContentConfig`（2026-11 工作区快照）。  
> **本文件不包含新视觉稿**，只描述「必须画对什么」。

---

## 1. 玩法与 UI 的硬边界

| 规则 | 代码/文档依据 |
|------|----------------|
| 点击**一整块**多格方块，沿**块上唯一箭头**飞出；路径被挡 → 错误（生命模式扣心） | `BlockOutGameRules`、About 文案 |
| 对局棋盘**不显示**章节插画/拼片底图 | `BuildBoardScreen`、Completion 在**清空后**才播 |
| 一章 **12 关 = 12 个 region**（4×3 固定几何，1080×1080 源画布） | `BlockOutChapterArtProvider` |
| 全局关号递增；`CurrentLevelIndex` 驱动进度 | `BlockOutGameManager`、`LevelsPerChapter = 12` |
| 首页章节 = `CurrentLevelIndex / 12`，夹在已发布章节内 | `HomeChapterIndex` |

---

## 2. 首页：控件树与数据绑定

实现入口：`BuildHomeScreen()` + `BlockOutHomeController.RefreshHome()` / `RefreshHomeArt()`。

### 2.1 自上而下结构（程序已建好）

```
Home
├─ 顶栏：LogoTile + LogoArrow + LogoTitle/Sub | CoinPill | SettingsBtn
├─ PreviewCard（圆角卡，高度 Relayout 动态）
│  ├─ ArtRoot → ArtworkViewport：12 格 Region 图（Image[] HomeRegionArts）
│  │    每格：Mist 遮罩 + LockDot（未揭晓）
│  ├─ BuildDecoToys：玩具块 A(L+→)、B(竖+↑)、飞出轨迹点（纯装饰，非按钮）
│  ├─ FailBox：加载失败 + 重试 / 稍后再试（不阻塞开局）
│  ├─ CardTitle（静态文案「第一章 · 作品预览」— 刷新逻辑未改此字段）
│  └─ PieceBadge（动态「拼片 n/12」）
├─ CTA：HomeCtaTitle / HomeCtaSub（珊瑚主按钮 + Play 图标）
├─ CTASecondary：「重玩本章关卡」（仅本章通完且下一章未发布时显示）
├─ ProgressCard：HomeChapterTitle | HomeCollectionLink | 进度条 | 12×HomeNodes | HomePieceText
└─ BottomNav：首页 / 图鉴 / 商店
```

### 2.2 CTA 状态机（必须全覆盖）

| 条件 | 主标题 | 副标题 | 可点 | 点击目标 |
|------|--------|--------|------|----------|
| 本章未完成 & 0 通关 | 开始第 {全局N} 关 | 第 X 章 · {主题} | ✓ | 本章首个未完成 index |
| 本章未完成 & 有进度 | 继续第 {全局N} 关 | …已通关 k 关 | ✓ | 同上 |
| 本章完成 & 下一章已发布 | 进入下一章 | 第 Y 章 · {主题} | ✓ | 下一章首关 index |
| 本章完成 & 下一章未发布 | 新章节准备中 | …已通关 12 关 | ✗ | — |
| 次级 | 重玩本章关卡 | — | 章完且未发布时显示 | 本章第 1 关 index |

主题名来源：`BlockOutContentConfig.ChapterThemeName`（当前配置数组仅 **`像素画廊`**，与旧文档「甜点星球」不一致，出图需跟配置或先改配置）。

### 2.3 拼片预览

- `RefreshHomeArt()`：`Collection.IsRegionRevealed(chapter, i)` → `RegionSprite(revealed, i)`；未揭晓 Mist + Lock。
- 加载失败：`ChapterArtStatus.Failed` → 清空 region 图、显示 FailBox；**仍可点 CTA 进关**。
- 首页章节索引：`HomeChapterIndex = Clamp(CurrentLevelIndex/12, 0, PublishedChapters-1)`（**不是**收藏页那种手动切章）。

### 2.4 出图常犯错误（此前 HTML 踩坑）

1. 把箭头画成 **方向键/D-pad** — 程序里是 **Decor 多格果冻 + 一条飞出轨迹**。  
2. 主视觉只放「整张图」而无 **12 region 网格语义** — 与 `BuildRegionGrid` 不符。  
3. 忽略 **CTASecondary**、**FailBox**、**禁用态 CTA** 三态。  
4. 写死「甜点星球」— 与当前 `ChapterThemeNames` 不符。  
5. 金币写 300 — 当前 `InitialCoins = 0`（老档另论）。

---

## 3. 结算：两段式体验（易与旧 §5.1 文档混淆）

### 3.1 第一段：仍在棋盘层（`PresentWin`）

1. HUD 收起（`HideForCompletion`）。  
2. `BlockOutCompletionPresentation.Play(LoadCompletionImage())`：棋盘格点阵 → **逐格渐显关卡关联 completion 图**（在 `Board` 上，非 Settlement 层）。  
3. 动画结束后隐藏 picture，再进入第二段。

设计含义：**结算弹层不是「第一次看见图」**；弹层侧重 **文案、金币、去下一关**。棋盘演出应在对局页规格里单画，不宜在结算稿里重复一大块 morph 动效（可作注释「此前已在棋盘播放」）。

### 3.2 第二段：SettlementLayer（`ShowWinResults`）

布局：`Dim` + `SafeRoot` + **Card Stretch**；`LayoutFullPages` 计算：

- `revealH = clamp(屏高 - 330, 120, 360)`
- `RevealRoot` 与 `RevealFrame` 同矩形
- 按钮：`Next` 通栏；`Collection` | `Replay` **同一 y 左右半宽**；`Home` 下一行通栏

**揭晓区实际逻辑（以代码为准）**：

```csharp
RefreshSettleReveal(chapter, showSingleLevelImage: true); // ShowWinResults 里写死 true
```

- `true` → **隐藏** `SettleRevealRoot`（12 格拼片网），**显示** `SettleLevelImage`（`LoadCompletionImage()` 贴图，preserveAspect）。  
- 注释写「章末走拼片网格」，但当前调用**始终 true** — 与 `09_component_spec`「普通关 region cover」设计稿有偏差；新 UI 要么跟代码（单关 completion 图），要么产品决定改代码后再画 12 格章末。

### 3.3 文案与按钮状态机

**存档失败**（`SettlementSaveFailed`）：

- 标题「关卡完成 · 进度未保存」；奖励「存档失败 · 奖励未发放」  
- 主按钮「重试保存」；重玩禁用  

**正常**：

| 维度 | 条件 | 表现 |
|------|------|------|
| 标题 | 首通 / 重复 / 章末首通 / 章末重复 | 新拼片解锁 / 关卡完成 / 本章通关 / 本章已完成 |
| PieceText | 章内进度或 12/12 已集齐 | `拼片 k/12` 或「本章作品已集齐」 |
| NoteText | 首通 vs 重复、是否章末 | 见 `BlockOutDialogsController` 216–225 行 |
| Reward | | `首次通关 · 获得 n 金币` / `重复通关 · 获得 n 金币` |
| Next | 无下一关 / 章末有下一章 / 普通下一关 | 新章节准备中(禁) / 进入下一章 / 下一关 |

下一关判定：下一 index 存在 **且** 其章 `IsChapterPublished` **且** `HasChapterData`（防空章）。

### 3.4 结算出图必须包含的状态

1. 首通（有 LevelImage）  
2. 重复通关  
3. 本章通关（标题/Note 不同）  
4. 下一章未发布（主按钮禁用文案）  
5. **存档失败**（常被设计遗漏）  

---

## 4. 与 design_v5 规格的差异（改稿前先裁决）

| 项 | design_v5 / 旧 HTML | 当前程序 |
|----|---------------------|----------|
| 结算揭晓 | 强调 12 region 网格 cover | 普通通关 **单关 LevelImage**，网格隐藏 |
| 棋盘通关演出 | 多在结算稿画大图 | **先在 Board Completion 播放** |
| 首页 CardTitle | 「第一章 · 作品预览」 | 进度条用 `HomeChapterTitle` 动态，预览卡标题未刷新 |
| 主题名 / 初始金币 | 甜点星球、300 | 像素画廊、0 |

**建议**：产品确认「结算层是否恢复 region 网格」后，再定稿结算视觉；否则新图应对齐 **LevelImage 槽位 + 动态 revealH**。

---

## 5. 视觉方向（2026-11 更新）

旧 design_v5 / 星形糖果 / 索引白稿 **废止**。新基准：[UI原型/ui_warm_3d/DESIGN_SPEC.md](../UI原型/ui_warm_3d/DESIGN_SPEC.md)（暖米底 + Tap Block Out 类厚块 + 参考图 HUD）。逻辑仍遵守本文 §2–§3 与结算方案 A。

## 6. 新 UI 出图流程（下一步）

1. **你确认**上表「程序为准 vs 要改程序」的裁决（尤其结算揭晓形态）。  
2. **选定视觉方向**（与 v5 奶油珊瑚脱钩的独立 mood board；信息架构仍遵守 §2/§3）。  
3. 再产出：**状态清单表 → 线框 → 高保真 / HTML**，每屏对照本文件 checkbox 验收。

---

## 6. 文件索引（便于自查）

| 主题 | 路径 |
|------|------|
| 首页刷新 | `Assets/BlockOut/Runtime/UI/Controllers/BlockOutHomeController.cs` |
| 结算 | `Assets/BlockOut/Runtime/UI/Controllers/BlockOutDialogsController.cs` |
| 首页/结算搭建 | `Assets/BlockOut/Runtime/UI/Views/BlockOutUIManager.Authoring.cs` |
| Region 几何 | `Assets/BlockOut/Runtime/UI/Components/BlockOutChapterArtProvider.cs` |
| 通关事务 | `Assets/BlockOut/Runtime/Gameplay/Flow/BlockOutSettlementFlow.cs` |
| 棋盘完成动画 | `Assets/BlockOut/Runtime/Gameplay/Presentation/BlockOutCompletionPresentation.cs` |
| 内容配置 | `Assets/BlockOut/Runtime/Core/Configuration/BlockOutContentConfig.cs` |
