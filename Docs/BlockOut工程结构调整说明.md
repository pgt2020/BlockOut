> 2026-10-21 更新：本文保留历史实施记录。后续流程拆分、实际预制体交付与验证边界见 [剩余整改交付记录](剩余整改交付_2026-10-21.md)。旧文中的“尚未拆分/待烘焙/运行时回退”等描述不代表当前实现。

# BlockOut 工程结构调整说明

> 生成日期：2026-10-20
> 目标工程：`E:/UnityProject/MutiplayGame/BlockOut/`
> 只读参考工程：`E:/UnityProject/ArrowOutBlockGallery/ArtOutBlockGallery/`（仅借鉴模块组织思想，未迁入任何 TK/广告/打点/登录/支付/无关插件）
> 验证方式：**仅静态检查**（读源码、目录与 .meta、asmdef、git 状态），**未触发 Unity 刷新/编译/Play Mode/测试/真机**。

---

## 0. 概述与范围

本轮结构调整遵循任务书六步执行顺序，已完成低风险且可静态验证的部分，并把高风险的"行为级深拆"显式列为待办（见 §9），避免在无法编译验证的情况下盲目重构、破坏已恢复的对局玩法。

已完成（均通过静态核对，调用关系保持单一、无新旧两套实现）：

- **S01 目录归类（Core 按职责）**：规则/内容/配置/模型拆分到 `Core/Rules`、`Core/Content`、`Core/Configuration`、`Core/Models`。
- **S09 最小迁移**：所有 `.cs` 与对应 `.meta` 一起移动，**GUID 全部保留**（见 §8）。
- **S04 棋盘/方块视图拆分**：`BlockOutBlockNode` 从 `BlockOutBoardView.cs` 拆为独立脚本 `Gameplay/Board/BlockOutBlockNode.cs`。
- **S05 游戏输入集中**：`BlockOutBoardGesture` 归入 `Gameplay/Input/`，命名空间由误写的 `BlockOut.UI` 修正为 `BlockOut.Gameplay`，与物理程序集一致。
- **R09/R10 数据恢复**：结构调整过程中一次 `git checkout` 误覆盖了 BoardView 的 R09/R10 改动，已按原设计重建（见附录 A）。

显式待办（属 S02/S03/S06/S08 的行为级深拆，需 Unity 编译验证，见 §9）：GameManager 流程抽取、工具类细拆（Hint/Hammer/Magic）、演出层独立、UI 控制器按页拆分、配置加载器下沉到 Infrastructure/Configuration。

---

## 1. 实际调整后的目录树（Runtime 关键部分）

```
Assets/BlockOut/Runtime/
├─ Bootstrap/                        启动装配（未移动，沿用）
│   ├─ BlockOutAppBuilder.cs
│   ├─ BlockOutStartupSequence.cs
│   └─ …（Launcher / AppRoot / ServiceRegistry / …）
├─ Contracts/                        跨程序集接口（未移动）
├─ Core/                             规则/模型/内容/配置（按职责归类）
│   ├─ BlockOut.Core.asmdef
│   ├─ Models/
│   │   ├─ BlockOutTypes.cs
│   │   └─ BlockOutPlayerProfile.cs
│   ├─ Rules/
│   │   ├─ BlockOutGameRules.cs
│   │   ├─ BlockOutShapeLibrary.cs
│   │   └─ BlockOutSolver.cs
│   ├─ Content/
│   │   ├─ BlockOutCatalog.cs
│   │   ├─ BlockOutLevelParser.cs
│   │   └─ BlockOutResourcePaths.cs
│   └─ Configuration/
│       ├─ BlockOutGameplayConfig.cs
│       └─ BlockOutContentConfig.cs
├─ Gameplay/
│   ├─ BlockOut.Gameplay.asmdef
│   ├─ Flow/                         GameManager/结算/装配（对局协调入口）
│   │   ├─ BlockOutGameManager.cs
│   │   ├─ BlockOutSettlement.cs
│   │   └─ BlockOutAssemblyManager.cs
│   ├─ Tools/                        道具库存协调与统一使用入口
│   │   └─ BlockOutToolController.cs
│   ├─ Board/                        棋盘视图 + 方块节点（已拆）
│   │   ├─ BlockOutBoardView.cs
│   │   └─ BlockOutBlockNode.cs       ← 本轮从 BoardView 抽取
│   ├─ Input/                        游戏棋盘手势（双指缩放/单指平移/抑制）
│   │   └─ BlockOutBoardGesture.cs    ← 本轮由 UI/ 迁入，命名空间修正
│   ├─ Settings/                     音频与震动设置、引导状态
│   │   └─ BlockOutSettings.cs
│   └─ Extensions/                   默认关闭的连击/特殊块扩展
│       ├─ BlockOutComboSystem.cs
│       └─ BlockOutSpecialBlockSystem.cs
├─ UI/
│   ├─ BlockOut.UI.asmdef
│   ├─ Navigation/                   页面切换/弹层管理/注册
│   │   ├─ BlockOutPageView.cs
│   │   └─ BlockOutUIPrefabRegistry.cs
│   ├─ Views/                        页面与弹层视图、控件引用绑定
│   │   ├─ BlockOutUIManager.cs
│   │   └─ BlockOutUIViews.cs
│   ├─ Controllers/                  控制器（仍单体，待 §9 拆分）
│   │   └─ BlockOutUIController.cs
│   └─ Components/                   通用控件/布局适配/作品查看缩放
│       ├─ BlockOutWidgets.cs
│       ├─ BlockOutLayoutMetrics.cs
│       ├─ BlockOutPinchZoom.cs
│       └─ BlockOutChapterArtProvider.cs
├─ Rendering/                        设计参数/程序绘图（命名空间仍 BlockOut.UI，属 Rendering 程序集）
│   ├─ BlockOut.Rendering.asmdef
│   ├─ Tokens/BlockOutDesignTokens.cs
│   └─ Graphics/BlockOutIconFactory.cs
└─ Infrastructure/
    ├─ Persistence/                  SaveService / ProfileTransaction（统一保存入口）
    ├─ Configuration/                 BlockOutGameplayConfigLoader.cs（S01：Resources.Load 归 Infrastructure）
    ├─ Resources/ Audio/ Ads/ Analytics/
```

说明：任务书推荐的 `Progression/`、`Presentation/` 目录尚未新建——`Progression`（章节与收藏进度）当前由 `BlockOutCatalog`(Core/Content) + `BlockOutGameManager`/`BlockOutSettlement` 承载；`Presentation`（演出层）的动画协程仍位于 `BlockOutBoardView`/`BlockOutBlockNode` 内（见 §9）。不新建空目录，符合"不为目录数量拆分、不新增空目录"的要求。

---

## 2. 旧文件 → 新文件迁移表

> 所有移动均 `.cs` 与 `.meta` 成对迁移，GUID 不变。"RM" 表示"重命名+此前未提交的玩法改动"，"R" 表示纯重命名，"新增" 表示本轮新建。

| 旧路径（相对 Runtime） | 新路径 | 类型 |
|---|---|---|
| `Core/BlockOutGameRules.cs` | `Core/Rules/BlockOutGameRules.cs` | RM |
| `Core/BlockOutShapeLibrary.cs` | `Core/Rules/BlockOutShapeLibrary.cs` | RM |
| `Core/BlockOutSolver.cs` | `Core/Rules/BlockOutSolver.cs` | RM |
| `Core/BlockOutCatalog.cs` | `Core/Content/BlockOutCatalog.cs` | R |
| `Core/BlockOutLevelParser.cs` | `Core/Content/BlockOutLevelParser.cs` | R |
| `Core/BlockOutResourcePaths.cs` | `Core/Content/BlockOutResourcePaths.cs` | R |
| `Core/BlockOutContentConfig.cs` | `Core/Configuration/BlockOutContentConfig.cs` | RM |
| `Core/BlockOutGameplayConfig.cs` | `Core/Configuration/BlockOutGameplayConfig.cs` | 新增（原未提交，随移动落位） |
| `Core/BlockOutGameplayConfig.cs`（内嵌 `BlockOutGameplayConfigLoader`） | `Infrastructure/Configuration/BlockOutGameplayConfigLoader.cs` | 跨程序集下沉（S01：Resources.Load 归 Infrastructure） |
| `Core/BlockOutPlayerProfile.cs` | `Core/Models/BlockOutPlayerProfile.cs` | R |
| `Core/BlockOutTypes.cs` | `Core/Models/BlockOutTypes.cs` | R |
| `Gameplay/BlockOutGameManager.cs` | `Gameplay/Flow/BlockOutGameManager.cs` | RM |
| `Gameplay/BlockOutSettlement.cs` | `Gameplay/Flow/BlockOutSettlement.cs` | RM |
| `Gameplay/BlockOutAssemblyManager.cs` | `Gameplay/Flow/BlockOutAssemblyManager.cs` | RM |
| `Gameplay/BlockOutToolController.cs` | `Gameplay/Tools/BlockOutToolController.cs` | RM |
| `Gameplay/BlockOutSettings.cs` | `Gameplay/Settings/BlockOutSettings.cs` | RM |
| `Gameplay/BlockOutBoardView.cs` | `Gameplay/Board/BlockOutBoardView.cs` | RM |
| `Gameplay/Board/BlockOutBlockNode.cs` | `Gameplay/Board/BlockOutBlockNode.cs` | 新增（从 BoardView 抽取） |
| `Gameplay/BlockOutComboSystem.cs` | `Gameplay/Extensions/BlockOutComboSystem.cs` | R |
| `Gameplay/BlockOutSpecialBlockSystem.cs` | `Gameplay/Extensions/BlockOutSpecialBlockSystem.cs` | R |
| `UI/BlockOutBoardGesture.cs` | `Gameplay/Input/BlockOutBoardGesture.cs` | 新增（原未提交，跨程序集迁入） |
| `UI/BlockOutUIController.cs` | `UI/Controllers/BlockOutUIController.cs` | RM |
| `UI/BlockOutUIManager.cs` | `UI/Views/BlockOutUIManager.cs` | RM |
| `UI/BlockOutUIViews.cs` | `UI/Views/BlockOutUIViews.cs` | RM |
| `UI/BlockOutUIPrefabRegistry.cs` | `UI/Navigation/BlockOutUIPrefabRegistry.cs` | RM |
| `UI/BlockOutPageView.cs` | `UI/Navigation/BlockOutPageView.cs` | 新增（原未提交，随移动落位） |
| `UI/BlockOutWidgets.cs` | `UI/Components/BlockOutWidgets.cs` | RM |
| `UI/BlockOutLayoutMetrics.cs` | `UI/Components/BlockOutLayoutMetrics.cs` | RM |
| `UI/BlockOutPinchZoom.cs` | `UI/Components/BlockOutPinchZoom.cs` | RM |
| `UI/BlockOutChapterArtProvider.cs` | `UI/Components/BlockOutChapterArtProvider.cs` | RM |
| `Rendering/BlockOutDesignTokens.cs` | `Rendering/Tokens/BlockOutDesignTokens.cs` | RM |
| `Rendering/BlockOutIconFactory.cs` | `Rendering/Graphics/BlockOutIconFactory.cs` | RM |

注意 `BlockOutGameplayConfig.cs`、`BlockOutPageView.cs`、`BlockOutBoardGesture.cs`、`BlockOutBlockNode.cs` 为**此前未提交**文件，移动后在新路径以未跟踪状态存在；其 `.meta` 一并随 `mv` 迁移，GUID 不变。

---

## 3. 拆分前后各核心类职责

| 类 | 位置 | 拆分后职责 | 拆分前 |
|---|---|---|---|
| `BlockOutGameManager` | `Gameplay/Flow/` | 对局协调入口：当前关卡/生命周期、装配规则/工具/视图/存档、发布状态事件、接收玩家操作协调流程。**仍含**提示/锤子/魔法/复活/结算的协调逻辑（行为级深拆见 §9） | 同左（未再搬移逻辑） |
| `BlockOutToolController` | `Gameplay/Tools/` | 道具库存权威源、选择模式、统一使用入口；`SetCounts` 回滚内存库存；`PersistProgressAndTools` 失败回滚 | 同左（R07 已补） |
| `BlockOutBoardView` | `Gameplay/Board/` | 创建/绑定/更新方块视图、坐标换算、布局适配、缩放根(zoomRoot)、输入锁、聚焦/抑制、飞出/星/震动/提示协程 | 同左；**额外**：R09 缩放根 + R10 聚焦/抑制/体色闪烁（本轮重建） |
| `BlockOutBlockNode` | `Gameplay/Board/`（独立） | 单块图片/箭头/状态环/可点击状态；提供演出所需引用；`FlashBody` 体色闪烁 | 此前为 BoardView 同文件内兄弟类 |
| `BlockOutBoardGesture` | `Gameplay/Input/` | 双指捏合缩放、单指平移（仅放大后）、松手抑制、弹窗/暂停/输入锁屏蔽；作用对象为 `BoardView.GetZoomRoot()` | 此前在 UI/，命名空间误写 `BlockOut.UI` |
| `BlockOutSettlement` | `Gameplay/Flow/` | 通关奖励/进度/通关身份/有效对局清理 | 同左 |
| `BlockOutUIController` | `UI/Controllers/` | 统一控制器（首页/HUD/失败/结算/收藏/商店/设置事件）；订阅 GM 事件；结算失败引导（R06） | 同左（待按页拆） |
| `BlockOutUIManager`/`BlockOutUIViews` | `UI/Views/` | 控件引用绑定与显示更新 | 同左 |
| `BlockOutCatalog` | `Core/Content/` | 关卡目录、图片配置、清单/关卡 JSON 加载（`Resources.Load` 经 `ResourcePaths`） | 同左 |
| `BlockOutGameRules`/`Solver`/`ShapeLibrary` | `Core/Rules/` | 移动判定、求解、形状库 | 同左 |
| `BlockOutContentConfig`/`BlockOutGameplayConfig` | `Core/Configuration/` | 玩法配置 DTO、默认值、校验、Apply 桥 | 同左 |
| `BlockOutPlayerProfile`/`BlockOutTypes` | `Core/Models/` | 玩家档案数据模型、对局/方块类型 | 同左 |

---

## 4. GameManager → 工具/演出 → 视图 调用关系

当前（已恢复且一致）的调用链路：

1. **入口装配**：`BlockOutAppBuilder`（Bootstrap）在 `boardArea` 上 `AddComponent<BlockOutBoardGesture>()`，注入 `GM / BoardView / Viewport`；GameManager `Setup` 装配 `Rules / Tools / BoardView / SaveService`。
2. **玩家操作 → GM 协调**：点击 `BlockOutBlockNode.OnPointerClick` → `BoardView.NotifyTapped` → `GM.OnBlockTapped` → 规则判定与消除流程。
3. **道具 → 工具 → 演出 → 视图**：GM `UseHint/UseHammer/UseMagic` → `ToolController` 选择/扣库存 → 调用 `BoardView.HighlightBlock / FlyOutBlock / SpawnStars / MarkWrong` 等演出 API；演出协程以 `runToken` 守护，结束回调通知 GM（不自行发奖/扣币/存档）。
4. **存档**：GM 经 `BlockOutSaveService` + `BlockOutProfileTransaction`（整段提交失败回滚）统一写档；UI/Settings 不再各自直写 `Profile.Save`。

待 §9 完成后，工具逻辑将进一步下沉到 `HintTool/HammerTool/MagicTool`，演出协程下沉到 `Presentation/`，GM 只做编排。

---

## 5. 输入锁、对局令牌、暂停、取消 的归属

- **输入锁（能否点普通块）**：`BoardView.inputLocked`（私有）+ 对外只读 `BoardView.IsInputLocked`；由 `SetInputEnabled` 设置。手势 `Blocked` 聚合：`GM.ModalPopupOpen || GM.IsPaused || BoardView.IsInputLocked`。
- **能否使用工具**：GM 用 `State==Ready && !IsPaused && !IsBusyResolving` 守卫（`IsToolUnlocked` 判断），未与"能否点普通块"混为单一 bool。
- **对局令牌（取消/重开安全）**：`BoardView.runToken`（每次 `LoadLevel` 自增）与 `GM.activeRunToken`；所有演出协程首行取令牌，失效即 `yield break` 且只走 onCancel，**绝不**触发新局胜利或解锁新局输入（P1-3）。
- **暂停**：`BoardView.paused`（入场/误点回弹期间）+ `GM.IsPaused`（暂停层）；协程内 `while(paused) yield return null` 冻结，恢复后继续。
- **手势抑制**：`BoardView.tapSuppressUntil`（`SuppressTaps` 设置），`NotifyTapped` 在抑制期内直接忽略，杜绝"拖动/双指变单指"误消块。
- **锁/回调清理**：`CancelAnimations()` 在切关/重开/退出时 `StopAllCoroutines` + 清理拖尾/星星 + 复位 `inputLocked/focusRoutine/tapSuppressUntil`；新局 `Setup` 先 `CancelAnimations` 再 `EnsureRoots + GetZoomRoot + ResetZoom + Rebuild`，明确清除旧局锁与旧回调。

---

## 6. 配置与档案的唯一数据源

- **玩家档案唯一源**：`Core/Models/BlockOutPlayerProfile`（数据结构） + `Infrastructure/Persistence/BlockOutSaveService` + `BlockOutProfileTransaction`（原子提交/回滚）。不复制 Profile 形成多套档案；UI/Settings 不绕过统一入口直写 `PlayerPrefs`/`Profile.Save`。
- **玩法配置唯一源**：`Core/Configuration/BlockOutGameplayConfig`（JSON DTO，源自 `Assets/Resources/BlockOut/GameplayConfig.json`）经 `BlockOutContentConfig.Apply` 同步为规则/复活/奖励的运行时桥。**R02 已落实**：业务消费者读 `ContentConfig` 而非散落字面量/旧常量。
- **配置读取归属（S01，本轮已下沉）**：`Resources.Load` + 校验 + 回退默认由 `Infrastructure/Configuration/BlockOutGameplayConfigLoader.cs` 承担（命名空间 `BlockOut.Infrastructure.Configuration`）；DTO/默认值/校验仍归 `Core/Configuration`。`BlockOutGameplayConfig.cs` 内已无 Resources.Load。`BlockOutStartupSequence`（Bootstrap）早已 `using BlockOut.Infrastructure.Configuration`，调用方无需改动；Core 不再触碰资源读取，进一步满足"Core 不依赖上层"。
- **资源路径唯一源**：`Core/Content/BlockOutResourcePaths`；所有 `Resources.Load` 经此常量，业务类不写字面量。
- **道具库存唯一源**：`BlockOutToolController`（内存）与 `Profile` 的工具计数在每次提交后保持一致；扣库存/效果提交/失败回滚走 `PersistProgressAndTools` 单一边界（R07）。

---

## 7. asmdef 是否调整及原因

- **未新增任何 asmdef**：所有移动均在既有 `BlockOut.Core / .Gameplay / .UI / .Rendering / .Bootstrap / .Contracts / .Infrastructure.*` 边界内完成。
- **唯一跨程序集搬移**：`BlockOutGameplayConfigLoader` 由 `Core/Configuration`（`BlockOut.Config` 命名空间内的嵌套类）迁到 `Infrastructure/Configuration/BlockOutGameplayConfigLoader.cs`（`BlockOut.Infrastructure.Configuration`），使 Core 不再做 `Resources.Load`。该 asmdef 已引用 `BlockOut.Core`；`BlockOutStartupSequence`（Bootstrap）已 `using BlockOut.Infrastructure.Configuration`，调用方零改动。方向为 Core←Infrastructure，未反向。
- **关键边界核对**：
  - `BlockOut.Core` 不反向引用 Gameplay/UI/Bootstrap/Infrastructure（本轮加载器下沉后，Core 内的 `Resources.Load` 也已移除，Core 仅依赖 UnityEngine）。
  - `BlockOut.Rendering` 的 `DesignTokens`/`IconFactory` 物理迁到 `Rendering/Tokens`、`Rendering/Graphics`，仍属 `BlockOut.Rendering.dll`，命名空间保留 `BlockOut.UI`（符合"以 asmdef 为准、不仅凭命名空间判断"的要求）。
  - `BlockOutBoardGesture` 物理位于 `Gameplay/Input/`，归入 `BlockOut.Gameplay.dll`（该 asmdef 无 `include` 限制，覆盖 `Gameplay/**`）；命名空间由 `BlockOut.UI` 修正为 `BlockOut.Gameplay`，消除"UI 命名空间却编进 Gameplay 程序集"的歧义。
  - `BlockOut.Gameplay` 不引用 `BlockOut.UI`（其用到的 `BlockOut.UI.IconFactory`/`DesignTokens` 实为 Rendering 程序集类型，经全限定名 + Rendering 引用解析）。

---

## 8. 资源路径和 GUID 的兼容情况

- **GUID**：所有移动文件的 `.meta` 与 `.cs` 一并迁移，**GUID 100% 保留**。Prefab/Scene 对 MonoScript 的绑定按 GUID 解析，不会因路径变更产生 Missing Script（已用 `git status` 核对 `R`/`RM` 均携带 `.meta`）。
- **新增文件 GUID**：`BlockOutBlockNode.cs`、`BlockOutGameplayConfig.cs`、`BlockOutPageView.cs`、`BlockOutBoardGesture.cs`、`BlockOutGameplayConfigLoader.cs` 为未跟踪文件，已附带手工生成 `.meta`（合法 `guid` + `MonoImporter`），Unity 导入后将沿用。
- **`BlockOutBlockNode` 无 Prefab 绑定风险**：它仅由 `BoardView.CreateBlockNode` 运行时 `AddComponent` 创建，不序列化于任何 Prefab，抽取为独立脚本不影响资源引用。
- **资源路径**：`Assets/Resources/BlockOut/GameplayConfig.json`、`Assets/Resources/ArtOut/*` 关卡与图片路径**未改名**；加载全部经 `BlockOutResourcePaths` 或配置 `ResourcePath` 常量，无散落字面量被改动。
- **Docs**：`ArtOut玩法对齐复查整改清单_2026-10-20.md`、`ArtOut玩法对齐实现记录.md` 保留。

---

## 9. 尚未整理/未完成的模块及原因

> 说明：S01/S04/S05/S07 已完成（含配置加载器下沉）。以下 S02/S03/S06/S08 的**行为级深拆**本轮**未执行**，理由见各项。

1. **S02 GameManager 流程抽取（未做）**：提示轮换、锤子选取、魔法施法、复活资格/提交、通关奖励事务、动画协程仍集中在 `BlockOutGameManager`。建议：以 `partial` 仅用于确紧密共享状态的小流程；道具与演出优先拆独立职责。**未做原因**：与 `runToken`/存档/状态事件/`BoardView` 强耦合，且本会话无 Unity 编译验证；盲拆易破坏 R03/R04/R07 已修复逻辑，违背任务书"不以结构调整替代功能修复/不延误关键玩法修复"。
2. **S03 工具类三拆（未做，硬性要求已满足）**：`HintTool/HammerTool/MagicTool` 未各自独立成类。**未做原因**：S03 硬性要求"库存只有一个权威来源，不让各工具分别维护互相不同步的数量"；若三工具各持计数即违反该要求，若仅转发调用则沦为任务书禁止的"无意义包装"。当前 `BlockOutToolController`（Gameplay/Tools）已集中库存权威源、选择模式、统一使用入口、`SetCounts`/`PersistProgressAndTools` 统一回滚边界，且不依赖具体 UI 页面、动画交由 BoardView——S03 硬性要求已达成，故不拆。
3. **S06 演出层独立（未做）**：飞出/撞击/提示/锤子/魔法/入场协程仍在 `BlockOutBoardView` 与 `BlockOutBlockNode` 内。建议：抽到 `Gameplay/Presentation/`，以 `BoardView` 暴露的最小表面驱动。**未做原因**：协程直接访问 `nodes/blocksRoot/fxRoot/flightCancellations/inputLocked/zoomRoot/runToken/paused` 等私有状态，抽出须先大量暴露或反向移交所有权，属高风险重构，需编译验证；盲目抽动会波及 R03/R04/R07/R10 的动画收尾与令牌保护。
4. **S08 UI 控制器按页拆分（未做）**：`BlockOutUIController` 仍单体承载首页/HUD/失败/结算/收藏/商店/设置；事件订阅/解除已成对（`OnDestroy` 反订阅）。建议：拆 `Home/Hud/Fail/Settle/Collection/Shop/Settings` 子控制器，由统一导航协调，先确认无重复订阅入口。**未做原因**：涉及按钮订阅与视图绑定，盲拆易出现重复订阅/漏绑定，需 Unity 侧验证。
5. **Progression 目录（未建）**：章节/收藏进度未单独建 `Gameplay/Progression/`，由 `BlockOutCatalog`(Core/Content) + GM/Settlement 承载，功能完整；任务书允许"某模块简单时不强行建目录"，故不拆。

> 以上未做项**不影响**：现有功能逻辑、单一数据源、资源 GUID、asmdef 边界。均在"可 Unity 编译验证"的会话中执行更安全；按用户要求，功能逻辑实际验证交由另一 AI 检查。若需在本会话强行推进 S02/S06/S08 之一，请在知晓"无编译验证、可能需二次修复"的前提下指定具体项。

---

## 附录 A. 本次结构操作的数据安全说明

1. **操作方式**：目录归类与文件移动使用 `git mv`（已跟踪文件）或 `mv`（未跟踪文件），`.cs` 与 `.meta` 成对迁移；未触发 Unity 任何刷新/编译/运行。
2. **一次误操作与恢复**：在抽取 `BlockOutBlockNode` 的脚本出现 brace-match bug 后，曾执行 `git checkout -- BlockOutBoardView.cs` 试图还原，但该文件的工作树含有**此前未提交的 R09/R10 改动**（缩放根/聚焦/抑制/体色闪烁），`checkout` 将其恢复为旧提交版本，导致 R09/R10 对 BoardView 的改动**丢失**。
   - 恢复手段：从 `BlockOutBoardGesture.cs`（仍在磁盘、未受影响）反向提取其期望的 `BoardView` API 签名，并结合既有的设计记录，重新实现 `zoomRoot/GetZoomRoot/GetZoomScale/ResetZoom/SuppressTaps/IsInputLocked/FocusOn/FocusRoutine` 以及 `BlockOutBlockNode.FlashBody` 体色闪烁、`HighlightBlock` 调用聚焦。重建后已静态核对手势所需 API 全部就位、AppBuilder 手势接线未变、`BlockOutDesignTokens.HintFlash`(#83F851) 可用。
   - 教训：未提交改动不应经 `git checkout` 还原；抽取类应使用稳健的括号匹配并先备份。后续同类操作将先 `git stash`/复制备份再执行。
3. **当前编译风险点（静态已核对，待 Unity 验证）**：`BlockOutBoardGesture` 跨程序集迁入 `Gameplay.Input` 后与 `BlockOutBoardView` 的缩放接口一致；`BlockOutBlockNode` 为运行时 `AddComponent`，无 Prefab 绑定；所有移动文件 `.meta` 保留。除上述 R09/R10 重建需真机确认观感外，无其它已知语法/引用断裂。

---

## 附录 B. 二次复查（2026-10-20《玩法与结构二次复查》）整改状态

> 根因：上次 `git checkout -- BlockOutBoardView.cs` 把 BoardView 退回**更旧的提交版**，丢失远不止 R09/R10，而是 R04–R11 整段配置化玩法与演出；GM（未回退）仍在调用，导致编译断裂 + 玩法丢失。恢复源为上一会话完整记录中抽出的 BoardView 全文快照。**均只静态核对，未 Unity 编译/运行。**

| 编号 | 项 | 状态 | 实际修改 |
|---|---|---|---|
| N01/P0 | BoardView 接口断裂 | **已修** | 从会话记录恢复完整 BoardView：补回 `PlayEntrance()`、`GetWandStartLocalPosition()`、`SpawnStarTravel(from,to,sec)`、`MagicHitPulse(block)`、`MarkWrong(block,int emptyCells,Action onReturned)` 重载；均为完整实现，非空桩。 |
| N02/P1 | 连续点击/加速飞出/误点回退 | **已修** | 恢复 `feel.exit*` 配置化加速飞出（普通飞出不锁整盘）；`MarkWrong` 三段落（前进→撞击挤压→回位，时长按 feel 配置 clamp）；`PlayEntrance`/`SpawnStarTravel`/命中脉冲；错误环改**持续显示**（删 0.28s 自动隐藏，随块移除/被提示·选择环覆盖而清除）。 |
| N06/P1 | 手势 awaitAllRelease 不清除 / OnDrag 不查 Blocked | **已修** | `BlockOutBoardGesture`：加 `ResetGestureState()`；`Update` 在 `touchCount==0` 清除 awaitAllRelease（修"捏合后单指平移永久失效"）；`OnDrag` 入口查 `Blocked`；抑制时间读 `feel.gestureTapSuppressSeconds`。 |
| N07/P1 | 统一保存入口 | **已修** | Settings 三 setter + GuideSystem.OnPlayerAction + UI 引导关闭按钮不再直写 `Profile.Save()`；改经 GM `CommitProfileChange`（事务+回滚+`OnSaveFailed`）。Settings/Guide 增 `BindCommit`，GM `BindServices` 注入，新增公共 `GM.CommitProfileMutation(Action)`。 |
| N03/P1 | 魔法/道具保存失败半成功与卡死 | **待办** | 需在业务操作前建快照，`PersistProgressAndTools` 失败时恢复 Rules/视图/选择态/State（非仅库存）；`hitFailed` 需把 State 移出 ResolvingMove；并行魔法目标需检查共享取消状态。属 GM 深层改动。 |
| N04/P1 | 魔法解锁/暂停时序/连击开关 | **待办** | 命中后应分离"普通点击资格/工具资格/结算在途"，改 Ready 而非仅 SetInputEnabled；星路径/脉冲用实际演出回调而非 WaitForSeconds 猜时长；`Combo.OnSuccessfulRemove` 遵 `enableCombo` 配置。 |
| N05/P1 | 输入锁按原因持有 | **待办** | `SetInputEnabled` 仍覆盖单一 `inputLocked`；需按原因（入场/暂停/失败/模态/工具/误点回弹/手势）持锁释放，一个模块只放自己的锁。 |
| N08 | S02/S03/S06/S08 结构拆分 | **待办** | GameManager 流程抽取、Hint/Hammer/Magic 独立类（共享库存服务）、Presentation 演出层、UI 按页拆控制器。 |
| N09/P2 | 锤子音效时序 / 提示聚焦 | 部分 | 聚焦已修（FocusRoutine 真正用 localTarget 居中 + 配置时长）；锤子"先移除后响锤声、最后一块先结算"时序仍待办（需纳入结算在途等待）。 |
| N10/P2 | 复活次数配置 | **待办** | `limitPerRun` 需所有复活入口与 UI 共用资格判定，次数随对局事务保存/恢复；或明确只支持不限次并拒绝非零配置。 |

**移交/运行验证**：N01–N02 恢复后需 Unity 编译确认无断裂；N03–N05/N08/N10 需在可编译会话逐项实现并静态核对；N09 锤声时序、N10 复活次数需真机验证。
