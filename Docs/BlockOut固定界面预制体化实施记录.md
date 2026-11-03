> 2026-10-21 更新：本文保留历史实施记录。后续流程拆分、实际预制体交付与验证边界见 [剩余整改交付记录](剩余整改交付_2026-10-21.md)。旧文中的“尚未拆分/待烘焙/运行时回退”等描述不代表当前实现。

# BlockOut 固定界面预制体化实施记录 V1

> 目标：把运行时由 `BlockOutUIManager` 代码创建的固定页面/弹窗，迁移为可在 Prefab 编辑模式查看调整的完整 UI；
> 实例化后脚本只绑事件/更新数据/控制状态。本文严格区分「静态检查完成」与「待 Unity 实际验收」。
> **沙箱内无 Unity：本轮回合未执行刷新/编译/Play Mode；Prefab 由新增的编辑器烘焙器在 Unity 内一键生成。**

---

## 0. 关键结论与迁移策略

- **现状勘定**：各 `BuildXxxScreen/BuildXxxLayer` 方法只建「固定骨架」、赋给 UIManager 公开字段，**不做任何数据/事件绑定**（已核验：构建区无 `.text=`/`AddListener`/profile 读取）；绑定全在 `BlockOutUIController`，经 `UI.XXX` 读公开字段。→ 骨架与绑定天然分离，迁移风险低。
- **迁移方案（安全、响亮回退）**：
  1. 每个页面/弹窗配一个 **View 组件**（序列化字段 = UIManager 公开控件引用）；
  2. 新增 **Editor 烘焙器**在 Unity 内跑一次 `Build()`，把各页/弹窗连同「吸收」了控件引用的 View 存为**完整 Prefab**；
  3. 运行时 `LoadOrBuildScreen/LoadOrBuildPopup` **优先实例化完整 Prefab** 并把 View 引用回填 UIManager 公开字段；**缺/旧骨架则响亮报错（含资源路径）并回退代码构建**——游戏不中断、不静默；
  4. 控制器零改动（仍读 `UI.XXX`）。
- **为什么保留代码构建回退**：Prefab 必须由 Unity 生成，沙箱无法产出/校验；响亮回退保证「未烘焙也能跑」，并把缺失 Prefab 明确暴露。**待 Unity 烘焙并验收通过后，需删除回退路径以达成「无双系统」终态**（见 §6 已知问题 K1）。

---

## 1. 页面/弹窗 → Prefab 路径 → View → 打开入口 对应表（UI-05 验收表）

| 页面/弹窗 | Prefab 资源路径（Resources 下） | View 组件 | 打开入口 | 静态状态 |
|---|---|---|---|---|
| Loading | Prefabs/UI/BlockOutLoadingPage | BlockOutLoadingView | `ShowScreen(Loading)`（Build 起始） | 机制就绪·待烘焙 |
| Home | Prefabs/UI/BlockOutHomePage | BlockOutHomeView | `ShowScreen(Home)` | 机制就绪·待烘焙 |
| GameHud(棋盘) | Prefabs/UI/BlockOutGameHud | BlockOutBoardPageView | `ShowScreen(Board)`（进关卡） | 机制就绪·待烘焙 |
| Collection | Prefabs/UI/BlockOutCollectionPage | BlockOutCollectionView | `ShowScreen(Collection)` | 机制就绪·待烘焙 |
| Store | Prefabs/UI/BlockOutStorePage | BlockOutStoreView | `ShowScreen(Store)` | 机制就绪·待烘焙 |
| 暂停 | Prefabs/UI/BlockOutPausePopup | BlockOutPauseView | `BoardPauseBtn`→`SetLayerActive("PauseLayer")` | 机制就绪·待烘焙 |
| 失败 | Prefabs/UI/BlockOutFailPopup | BlockOutFailView | 失败流程 `SetLayerActive("FailLayer")` | 机制就绪·待烘焙 |
| 确认 | Prefabs/UI/BlockOutConfirmPopup | BlockOutConfirmView | `AskConfirm(...)` | 机制就绪·待烘焙 |
| 结算 | Prefabs/UI/BlockOutSettlementPage（**复用既有资产·保 GUID**） | BlockOutSettlementView | 通关结算 | 机制就绪·待烘焙 |
| 设置 | Prefabs/UI/BlockOutSettingsPage（**复用既有资产·保 GUID**） | BlockOutSettingsView | `OpenSettings(...)` | 机制就绪·待烘焙 |
| 关于 | Prefabs/UI/BlockOutAboutPopup | BlockOutAboutView | `SettingsAboutBtn` | 机制就绪·待烘焙 |
| 引导展示层 | Prefabs/UI/BlockOutGuidePopup | BlockOutGuideView | 首次进第 1 关 | 机制就绪·待烘焙 |

> 「机制就绪」= 代码路径/View/注册表/烘焙器已接好；「待烘焙」= 需在 Unity 执行菜单生成实际 Prefab 资产后才能运行验收。

---

## 2. 修改/新增的文件

**新增（Runtime）**
- `Runtime/UI/Views/BlockOutUIViews.cs`（重写）：`BlockOutUIViewBase`（反射同名同型字段互传 `AbsorbFrom/ApplyTo`）+ 12 个 View 组件；**删除原 5 个无用占位 stub**（BlockOutHUD/WinPopup/FailPopup/SettingsPopup/HomeView，已核验无运行时引用）。
- `Runtime/UI/Navigation/BlockOutUIPrefabRegistry.cs`（重写）：新增弹窗资源名 `LayerResourceName`、`LoadLayer`、`IsFullPrefab`（带 View 判定）、`ReportMissing`（含路径明确报错）、`ClearCache`。

**新增（Editor）**
- `Editor/BlockOutUIPrefabBaker.cs`：菜单 `BlockOut/Prefab/烘焙完整页面与弹窗`。临时 `UIManager`+`ForceCodeBuild` 跑 `Build()`→弹窗脱离父级→逐页/逐弹窗挂 View、`AbsorbFrom`、`SaveAsPrefabAsset`（同路径保存保 GUID）。

**修改（Runtime）**
- `Runtime/UI/Views/BlockOutUIManager.cs`：
  - 加 `[assembly: InternalsVisibleTo("BlockOut.Editor")]`；
  - 新增内部访问器 `ScreenRoot/LayerRoot`、`ForceCodeBuild`、`LoadOrBuildScreen/LoadOrBuildPopup/FixupScreenRefs`；
  - `BuildAllScreens` 改走 `LoadOrBuildScreen`（Prefab 优先+响亮回退）；
  - `BuildBoardScreen` **移除内联 4 弹窗构建**（改由 `Build()` 独立加载，便于弹窗独立复用）；
  - `Build()` 增补弹窗 `LoadOrBuildPopup`（暂停/失败/确认/结算父=Board；设置/关于/引导父=画布；设置缺 Prefab 时回退 `BuildSettingsLayer` 连带建关于）；
  - `MakeScreen` 在 `ForceCodeBuild` 时不加载磁盘 Prefab（保证烘焙按当前代码从零产出，防再烘焙叠加）。

**修改（Editor，避免误报）**
- `Editor/BlockOutPrefabGenerator.cs`、`Editor/BlockOutProjectChecks.cs`：校验容忍「带 View 的完整 Prefab」（不再强求 `BlockOutPageView`）。

---

## 3. 删除/替换的运行时固定 UI 创建逻辑清单

- **替换为主路径**：`MakeScreen` 不再是页面根的主要来源；页面/弹窗改由 `LoadOrBuildScreen/LoadOrBuildPopup` 优先实例化完整 Prefab 并回填引用。
- **结构调整**：`BuildBoardScreen` 不再内联建暂停/失败/确认/结算（移至 `Build()` 独立加载）。
- **暂未删除（响亮回退，见 K1）**：`BuildHomeScreen/BuildBoardScreen/BuildLoadingScreen/BuildCollectionScreen/BuildStoreScreen` 与 `BuildPauseLayer/BuildFailLayer/BuildConfirmLayer/BuildSettlementLayer/BuildSettingsLayer/BuildAboutLayer/BuildGuideLayer` 仍作为「缺 Prefab 时的回退 + 烘焙器数据源」保留。**UI-01 实施要求第 5 条（删除已被 Prefab 替代的固定控件创建逻辑）标记为「机制就绪、终态待烘焙验收后执行」**，以避免在无 Unity 校验下直接删空导致白屏。
- **孤儿资产**：`BlockOutPopupLayer.prefab`（原暂停/失败/确认空容器骨架）不再接入；按需求「明确保留为容器、不计为弹窗完成」处理。

---

## 4. 保留运行时动态生成的内容清单及原因

| 内容 | 位置 | 保留原因 |
|---|---|---|
| 棋盘格子/在场块 | BoardArea（`BlockOutBoardView`） | 玩法层动态内容，随关卡数据生成 |
| 收藏缩略图/章节行/重复格 | Collection 页 Content | 数据驱动列表 |
| 商店商品卡 | Store 页（`MakeStoreProduct`） | 数据驱动、按工具四态刷新 |
| Toast | 画布级 | 瞬时提示，非固定页 |
| 引导显示层 | GuideLayer | 仅迁移「显示层」为 Prefab；**引导规则未改**（符合 UI-02 #6） |

> **UI-04（列表条目 Prefab 化）未在本轮完成**：收藏/商店条目仍运行时生成（见 §6 K3）。

---

## 5. 各需求完成状态（UI-01 ~ UI-06）

| 需求 | 状态 | 说明 |
|---|---|---|
| UI-01 五固定页面迁移 | **机制就绪·待烘焙验收** | View+注册表+烘焙器+运行时 Prefab 优先已接；实际 Prefab 资产待 Unity 烘焙；「删除代码建控件」终态待验收后执行 |
| UI-02 固定弹窗迁移 | **机制就绪·待烘焙验收** | 7 弹窗均配 Prefab 路径+View；结算/设置复用既有资产保 GUID；确认弹窗复用**已用 `pendingConfirm` 单监听模式，不叠监听**（UI-02 #5 已满足）；引导仅迁显示层 |
| UI-03 明确控件引用 | **静态完成** | 固定控件全部经 View 序列化字段绑定；不依赖全局 Find（Relayout 按名定位属重排，非控件获取）；View 不碰业务；事件由控制器 `Bind`（先 Remove 后加） |
| UI-04 列表条目迁移 | **未完成（下轮）** | 收藏/商店条目仍运行时生成；需做条目 Prefab + 复用/清理 + 空态 |
| UI-05 统一加载 | **静态完成** | 页面/弹窗统一走 `BlockOutUIPrefabRegistry`；缺资源 `ReportMissing` 含路径明确报错；不静默回退；页面加载失败不走依赖其引用的代码（回退代码构建仍产出有效引用） |
| UI-06 屏幕适配/点击区 | **部分（沿用既有+待设备验收）** | 既有 `MakeSafeRoot/ApplySafeArea`（弹层统一安全区根）、遮罩 `Dim` 铺满、`BlockOutWidgets` 点击区；9:16 / 9:19.5 / 3:4 及安全区需真机验证 |

---

## 6. 待 Unity 实际确认的验收步骤 + 已知问题

**验收步骤（在 Unity 编辑器）**
1. 菜单 `BlockOut/Prefab/烘焙完整页面与弹窗` → 看 Console「烘焙完成：共 12 个完整 Prefab」。
2. 菜单 `BlockOut/Prefab/校验` → 应通过（完整 Prefab 带 View，不再强求 PageView）。
3. 进 Prefab 编辑模式抽查 Home/GameHud/Collection/Store/Pause/Confirm：应见**完整固定控件**（非空容器）；改一个固定按钮位置→进 Play→位置生效不被初始化覆盖。
4. Play：连续进出同页 5 次无重复控件；确认弹窗先 A 后 B，点确认只执行 B 一次；弹窗打开时点遮罩不误触棋盘；结算显示真实结果、重开不重复发奖。
5. 切 9:16 / 9:19.5 / 3:4 + 顶部/底部安全区，查按钮可见可点、金币栏/标题/返回不重叠、棋盘与底栏不挡、弹窗确认/取消可达、收藏/商店可滚到末尾。
6. 烘焙通过后，删除 §3 的代码构建回退，复跑 3–5。

**已知问题（不得将未验证项写成已通过）**
- **K1（重要）**：代码构建回退尚未删除——在烘焙并验收通过前，游戏靠回退运行（Console 会有「缺少 UI Prefab 资源…」错误日志，属预期提示）。达成「无双系统」终态需验收后删回退。
- **K2**：`AbsorbFrom/ApplyTo` 依赖 Unity 对反射写入的公开字段正常序列化（标准行为，但需在 Unity 复核 Prefab 里 View 引用非空）。
- **K3**：UI-04 列表条目 Prefab 化未做；收藏/商店条目仍运行时生成，空态/复用/清理逻辑沿用既有代码，未按条目 Prefab 验收。
- **K4**：UI-06 多宽高比/安全区未真机验证。
- **K5**：`BlockOutPopupLayer.prefab` 成为未接入容器资产（保留，未计弹窗完成）。
- **K6**：全程未编译/运行，以上均为静态检查结论；语法/引用需 Unity 编译最终确认。

---

## 7. 复查整改（第二轮）逐项状态

> 状态口径：**A** 已实现且静态检查通过；**B** 尚未实现或只完成部分；**C** 等待 Unity 生成资源；**D** 已实现、等待 Unity 编译/运行验收。不把 B/C 写成“只剩打开 Unity 检查”，不把未执行的检查写成通过。

| 编号 | 状态 | 修改文件与入口 | 实现后具体行为 | 静态检查 | 待 Unity 验收 | 仍存问题/依赖 |
|---|---|---|---|---|---|---|
| U01 | **A** | `BlockOutUIManager.cs`（ToolSlotRefs/StoreProductRefs 加 `[Serializable]`）；`BlockOutUIViewBase.cs`（`ReportMissingRefs`）；`BlockOutUIPrefabBaker.cs`（`ValidateComposite`） | 组合引用可序列化；直接/数组引用缺失按“页面(View 类型)+字段名”报错；道具槽(Button/Rect)、商品卡(BuyBtn/CardRoot)关键子字段校验，缺失即停交付 | 通过：仅 2 个自定义类型已加 `[Serializable]`，其余 View 字段均为 Unity 可序列化类型/数组 | 保存→卸载→重载 Prefab 后引用不丢失 | 无（静态层） |
| U02 | **A** | 新增 12 个 `BlockOut*View.cs` + `BlockOutUIViewBase.cs`，各带 `.meta`；删除合并旧文件 | 每个需挂载 View 独立脚本、类名=文件名、独立 GUID meta；无重复定义 | 通过：12 View 类名=文件名；括号平衡 | 组件挂载/保存/重载识别正常 | 无（静态层） |
| U03 | **D** | `Editor/BlockOutUIPrefabBaker.cs`（`PersistGeneratedSprites`） | 程序生成 Sprite 纹理编码 PNG、按**内容哈希命名去重**存资产、按 Sprite 模式（九宫格 border/像素单位/过滤/alpha）导入并回引 Image；Prefab 引持久资产 | 代码就位、括号平衡 | 编辑器重启后图片完整；重复烘焙不堆积文件 | 需 Unity 烘焙验证；sliced 边框保真、个别 pivot 待核 |
| U04 | **B** | —（未改） | 未做：`Relayout` 仍按节点名重写大量固定控件位置/尺寸，会覆盖 Prefab 固定布局 | — | — | 架构冲突：UI 全代码驱动响应式布局；需把固定布局职责迁到 Prefab/布局组件、仅留安全区与动态适配，大改，未做 |
| U05 | **A** | `Editor/BlockOutUIPrefabBaker.cs`（重写） | 全部临时对象统一登记、`finally` 全清（含脱离弹窗）；每次保存校验返回；成功/失败计数+具体失败资源；缺根/缺 View/组合引用缺失即停交付报错 | 通过：清理路径完备、保存结果已核、无未核验即计成功 | 重复执行不污染当前场景 | 无（静态层） |
| U06 | **C** | 依赖 U03/U05 烘焙器 + 菜单 `BlockOut/Prefab/烘焙完整页面与弹窗` | 12 个完整页面/弹窗 Prefab **尚未实际生成**（沙箱无 Unity） | — | 需在 Unity 执行烘焙，产出并核对 12 个含固定控件+View 的 Prefab；设置/结算复用既有路径保 GUID | **阻塞：无 Unity 无法生成资源**；不标“资源完成” |
| U07 | **B** | —（未改） | 收藏/商店条目仍运行时代码生成，未条目 Prefab 化 | — | — | 未实现：需条目 View + 烘焙条目 Prefab + 运行时实例化/复用/清理/空态 |
| U08 | **B（类型校验部分 A）** | `BlockOutUIPrefabRegistry.cs`（`ViewTypeForScreen/ViewTypeForLayer/HasCorrectView`）；`BlockOutUIManager.cs` 4 处加载点 | 加载时校验“资源存在 + View **类型正确** + 引用完整”，失败停依赖该页初始化并响亮报错（含路径）；棋盘/数据列表动态生成保留 | 通过：4 处均由 IsFullPrefab 升级为 HasCorrectView(期望类型) | — | 回退移除阻塞于 U06（无资源删回退会白屏）；资源交付验收后需删回退达“无双系统”终态 |
| N03 | **B** | — | 魔法/道具保存失败半成功与卡死未处理 | — | — | GM 大改：快照/回滚、协程取消态、ResolvingMove 收尾；未做 |
| N04 | **B** | — | 魔法解锁/暂停时序/连击开关未处理 | — | — | GM 大改；未做 |
| N05 | **B** | — | 输入锁仍单一 bool，未按原因持锁 | — | — | GM/BoardView 大改；未做 |
| N08 | **B** | — | GM 流程/工具类/演出层/UI 分页控制器未拆分 | — | — | 结构性大改；未做 |
| N09 | **B** | — | 锤击音效与结算时序未梳理 | — | — | 需纳入结算在途等待；未做 |
| N10 | **B** | — | 复活次数未统一资格/存档恢复 | — | — | 需统一入口+事务保存；未做 |

**本轮净增量**：U01/U02/U05 由缺陷/未处理 → **A**；U03 → **D**；U08 类型校验由 B → 部分 **A**。**仍未完成**：U04/U07（代码未做）、U06 与 U08-回退移除（阻塞于 Unity 资源生成）、N03/N04/N05/N08/N09/N10（GM 大改，未做）。
