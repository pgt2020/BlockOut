# BlockOut 对齐 ArtOut 玩法与手感 · 实现记录

> 依据 `Docs/ArtOut玩法与手感对齐实施说明_2026-10-20.md`。
> 状态口径：**已实现**（写了代码）/ **静态已检查**（离线编译、规则契约、JSON 校验等只读证据）/
> **待运行**（需要 Unity 编辑器或真机，按用户授权执行）/ **未完成**（含原因）。
> 离线证据目录：`Tools/CompileCheck/logs/`、`Tools/LevelVerify/logs/`、`Tools/TestRunner/TestResult.xml`。
> 所有离线检查**不启动 Unity、不触发刷新/编译/Domain Reload/Play Mode**。

## 0. 总览

| 阶段 | 状态 | 说明 |
|---|---|---|
| A 基线修复 | 已实现 + 静态已检查 | 21 处编译阻塞、Prefab fileID、C05/C06/C07 事务与档案注入、启动顺序 |
| B 配置/内容 | 已实现 + 静态已检查 | GameplayConfig JSON+DTO+加载器；第一章 12 个固定关卡（2 本地教学 + 10 参考移植）；manifest/图片关联；关闭占位补齐路径 |
| C 规则/工具 | 已实现 + 静态已检查 | 连点立即移除+在途计数+胜机收口；提示轮换；锤子/魔法参考语义；复活不限次数；计时全条件 |
| D 手感 | 已实现 + 静态已检查 | 飞出加速（feel 6.24/15/13 + 视口外余量 + 拖尾）、误点三段 clamp、箭头闪 3×0.04、提示 #83F851 两轮+0.7s 聚焦、魔法星路径 1s+命中脉冲、入场 0.9/0.68/1.02、失败 0.58、手势抑制 0.16、棋盘缩放 |
| E 回交 | 本文档 + 验收用例 | 阶段 E 验收用例代码化见 §7；手动验收步骤见 §6；未运行项如实标注 |
| F 复查整改 R01–R11 | 代码已实现 + 静态已检查 | 2026-10-20 复查清单指出的 R01–R11 已全部落码（详见 §9）；按用户要求本轮回交只更新文档、不补测试用例；运行时验证待授权 |

---

## 1. 阶段 A：基线修复（已完成）

| 项 | 状态 | 证据/说明 |
|---|---|---|
| 编译阻塞 21 处 | 已实现 | StoreContracts 缺 using、Catalog readonly 初始化器、命名空间歧义（Resources/Object）、IconFactory 向量混算、UIManager 类型错误等；离线全量编译 0 错误 |
| Prefab/Scene fileID | 已实现 | 10 个 Prefab + Launcher.unity 小 fileID → 锚点计数器方案；PageView 拆分后 9 个 prefab m_Script guid 同步 |
| C05 事务半成功 | 已实现 | Commit 保存失败才闭合；失败真实恢复内存快照 + 存储缓存（PeekStored/RestoreStored） |
| C06 档案注入一致性 | 已实现 | Settings/Guide/Assembly BindProfile |
| C07 结算/复活/购买事务化 | 已实现 | OnSaveFailed 事件 + CommitProfileChange 单一入口 |
| 启动顺序 | 已实现 | LocalConfig→ApplicationConfig→**GameplayConfig**→ProfileMigration→ContentCatalog |

## 2. 阶段 B：配置/内容（已完成）

### 2.1 GameplayConfig（文档 §6 契约）

- `Assets/Resources/BlockOut/GameplayConfig.json` + `BlockOutGameplayConfig` DTO + 加载器：
  缺字段保留默认、任何失败（缺失/坏 JSON/版本不支持/非法值）**整体回退 Default** 并 LogWarning 明确路径与原因。
- 启动序列第 3 步加载并 Activate；`BlockOutContentConfig.Apply` 同步桥；远程桥接不再覆盖回旧常量。

### 2.2 第一章 12 个固定关卡

- 清单：`Assets/Resources/ArtOut/GameAssets.json`（version `blockout-local-v2-artout-c1`，12 条，gametime 120）。
- 构成：1-2 关 = 既有本地教学关（保留 ID，旧存档兼容）；**3-12 关 = 参考工程真实关卡移植**
  （参考 manifest 第 3-12 项，`Assets/Bundles/Main/ArtOutLevels/*.bytes` gzip JSON 解压移植）。
- 移植规则（`Tools/port_artout_levels.py` 可复现）：
  - pieces/颜色/arrowCell/dataVersion/rewardCoins/chapter 逐字保留；ID 与参考一致（稳定唯一）。
  - `difficulty`：参考 JSON 是数值 1，参考运行时靠 id 后缀 `_easy` 推断（JsonUtility 数值→字符串字段落空后走
    id/displayName/pictureId 推断）；移植件**显式写 "easy"**，结果与参考运行时一致且确定。
  - `displayName`：参考值是设计工具产物（如"前10关重排候选 1"），参考 HUD 实际显示 `"Level " + (index+1)`，
    故改写为 `Level 1..12`（HUD 文案对齐参考，中文 UI 下保留英文关名与既有教学关一致）。
  - `gametime`：120，与参考 606 关清单一致；仅在远程开启倒计时模式时生效（默认生命模式），
    **不把 120 冒充成配置里的 30 秒**（`rules.gameTimeSeconds=30` 是无 gametime 时的兜底）。
- 形状库：`BlockOutShapeLibrary` 补齐 **29/30**（与参考 1..30 逐字一致；移植关 `20260817_v1_Level8_easy`
  用到 29）；修正 2/3、6/7、8/9 三对朝向注释（数据未动）。
- 修复既有 `blockout_tutorial_02` 越界块（右侧水平多米诺 column 5→4；shape 2 实为水平块，6 宽棋盘放不下）。
- 图片关联：`ArtOutPictureConfig.json` 新增 10 条移植关条目 → `block/ch01` 插画（pic_tutorial 同模式，
  本地体验占位，已在配置 `_comment` 标记）。
- **关闭"生成占位关填满正式章节"路径**（文档 §8）：正式关不足不再暗中补随机关；零关卡兜底改 LogError
  明示内容错误（仅防永久 Loading）。
- 奖励语义：`GetLevelReward` 改为**奖励表优先**（对齐 `ArtOutWinRewardConfig.GetRewardCoins`：
  关卡自带值仅兜底）；easy 关发 10 而非关卡自带 25+。

### 2.3 阶段 B 静态证据（Tools/LevelVerify，真实 Runtime 代码 + 桩，可复跑）

- 12 关全部通过：manifest↔文件一一对应；真实 `BlockOutLevelParser.Parse` 成功；边界/不重叠/
  arrowCell 合法/shapeId∈1..30；**可解性**：游戏内 `BlockOutSolver.IsSolvable`（贪心）与 runner
  回溯求解（权威判定，且与 `BlockOutGameRules.CanMove` 交叉核对）均 True，逐关记录解序列与
  `BuildLevelRunHash`；图片条目与插画文件落盘；章节位公式复算；结构签名互异（排除仅改颜色）；
  覆盖 27 种形状、四向飞出、棋盘 5x5..12x18、块数 6..44。
- 全量离线编译（Runtime+Tests+Editor）0 错误 0 警告。

## 3. 阶段 C：规则/工具（已实现，GM 生命周期场景待 Unity 运行）

### 3.1 连续点击（文档 §4.2）— `BlockOutGameManager`

- 成功点击**立即 `Rules.Remove`** 逻辑移除 + `FlyOutBlock` 独立飞出协程；**不再**进入
  `ResolvingMove` 串行化输入；`!block.Active` 守卫保证同一块不可重复提交（快速点 A 两次只处理一次）。
- `inFlightFlyOuts` 在途计数；`MaybeWin()` 胜机收口：逻辑清空后仍须等在途飞出与魔法演出完成
  才 `OnLevelWon`；失败/已胜局短路；损坏关卡（Blocks==0）不会误胜（§4.1）。
- 飞出取消（重开/切关/退出/重建）：逻辑移除不恢复，仅放弃视觉；令牌失效不碰新局。
- 存档记录已承诺的逻辑移除（`CaptureRunProgress` 原本就按 Active=false 记录）；恢复全移除局
  仍走 `CompletePendingWin` 补结算且只一次。
- 旧 P1-6"延迟提交"设计按文档 §4.2.6 显式废弃（存档只落稳定局面的目标由"提交即落盘 + 补结算"达成）。

### 3.2 道具（文档 §5）— `BlockOutToolController` + GM

- 提示：参考 `ArtOutHintTool` 轮换语义——优先未提示过的可飞块，全部提示过重置集合；
  无目标不扣库存；扣减成功才记入本局集合；切关/重开 `ResetHintCycle`；**移除 2.5s 硬冷却**。
- 锤子：选择态进入不扣库存、命中扣 1、可消受阻块、取消不扣库存、命中自动退选择态；
  零库存进入失败（参考 Activate Failure），由商店购买路径补给。
- 魔法棒：施法前一次性链式模拟选目标（最多 `MagicTargetCount`=6，允许"先 A 后 B 才可飞"），
  有目标才扣 1 库存；**多目标并行施法**（星路径 → 命中缩放脉冲 → 逻辑移除 → 独立飞出），
  替换旧"逐块串行等待"；工具锁（`ResolvingMove` + 棋盘输入锁）独立于普通点击锁。
- 购买：`ToolPackCost=300` / `ToolPackAmount=2`（参考 ToolPackCost/ToolPackAmount），
  档案事务原子扣币+发货+落盘；商店 UI 文案同步（零库存槽位指向商店）。

### 3.3 复活与经济（文档 §5）

- **移除 `ReviveUsedThisRun` 资格硬阻断**（字段保留，存档兼容）；免费复活 = 全局 1-10 关
  **不限次数**、补满 `MaxLives`（参考 `ReviveByFree` 传 MaxLives）；金币复活 = 300 币补 1 心、
  不限次数；倒计时模式两种均 +20s 并重置计时器状态（参考 `AddTimeFailReviveSeconds`）。

### 3.4 计时（文档 §5，参考 `UpdateTimeFailTimer` 全条件）

- 前置闸：非倒计时模式/无关卡/无棋盘/`RemainingBlocks<=0`/已到期失败 → 不计时。
- `CanStartTimeFailTimer`：聚焦 && 无广告 && 棋盘输入未锁 && 无引导 && 无模态弹窗 && 非胜利流程。
- `ShouldTickTimeFailTimer`：聚焦 && 无广告 && 无引导 && 无模态弹窗 && 非胜利流程
  （**不含 inputLocked**——普通飞出不停表，快速点击不能拖长限时）。
- 到期只失败一次（`timeExpiredFailShown`），锁输入 + 落盘 + 失败层；低时间预警阈值走配置（10s）。
- 模态弹窗标志由 UI 层在弹窗开闭时同步（`SyncModalFlag`）。

### 3.5 阶段 C 静态证据

- 离线测试运行器（Tools/TestRunner，NUnitLite + 真实 Runtime + 桩）：
  **62/62 通过**（`--where "cat!=UnityRuntime"`），新增 `BlockOutStageCRulesTests`
  （连点规则层证据、误点去重、提示轮换、锤子零库存、魔法链+过滤、工具包配置、复活经济数值、奖励表优先）。
- 3 个广告回调用例标注 `[Category("UnityRuntime")]`：依赖适配器协程/计时推进，桩环境
  `Time.time` 不流动，仅 Unity 编辑器运行（如实标注，不冒充通过）。
- 修复 5 个**从未运行过的既有测试**的错误前提/旧语义（1x1"挡块"其实可飞、同块连点不会扣 3 心、
  魔法选目标旧语义、重启二次发奖断言对象错误、旧键返回值语义）。

## 4. 阶段 D：手感（已实现，演出时序待 Unity 运行确认）

| 项 | 状态 | 说明 |
|---|---|---|
| 飞出加速模型（6.24/15/13、cameraSize 5） | 已实现 | `BoardView.FlyRoutine` 改恒定加速模型：`v0=exitInitialSpeed×unit`、`a=exitAcceleration×unit`、`vmax=exitMaxSpeed×unit`，视口外余量 + 拖尾 1.05；旧 cubic-out 已弃 |
| 误点 clamp 公式（travel/impact/return） | 已实现 | `BlockOutBlockNode.WrongFeedbackRoutine` 三段时长全部来自 `feel`：`travel=clamp(0.08+0.06√n,0.12,0.24)`、`impact=0.05`、`return=clamp(0.12+0.04√n,0.16,0.28)`；`MarkWrong` 入口接红环 + 箭头闪 |
| 箭头闪 0.04s×3 | 已实现 | `FlashArrowRoutine(3, 0.04f)`（§7.2） |
| 提示 #83F851 两轮 0.2s 渐入渐出 + 0.7s 聚焦 | 已实现 | `ShowHintHighlight` 用 `feel.hintFlashStepSeconds/Loops/FocusSeconds`；闪烁色 `DesignTokens.HintFlash=#83F851`；聚焦环 + 轻微放大呼吸 |
| 魔法星路径 1s 并行 + 命中放大 | 已实现 | `SpawnStarTravel`（星从棒端起点飞向目标，默认 `magicStarPathSeconds=1s`）→ `MagicHitPulse`（放大 1.15×0.12s×2）→ 逻辑移除 → 独立飞出；`MagicTargetRoutine` 多目标并行；`GameManager` 工具锁独立 |
| 锤子 0.35s 音效延迟 | 已实现 | `GameManager` 命中音效延迟 `feel.hammerImpactSoundDelay=0.35s`（特效寿命 2.1s ≠ 锁输入 2.1s） |
| 入场 0.9s/0.68 缩放/输入延迟 1.02s | 已实现 | `PlayEntrance` 缩放 0.68→1（cubic ease-out 0.9s）+ 输入延迟基线 1.02s；切关/重开由 `runToken` 终止旧协程 |
| 失败弹层延迟 0.58s | 已实现 | `UIController.HandleLevelLost` 碎心演出后延迟 `feel.failPopupDelaySeconds=0.58s` 再开失败层；`failLayerOpenedAt` 驱动广告兜底 |
| 手势抑制 0.16s + 棋盘缩放 | 已实现 | `tapSuppressUntil`（点击后 0.16s 抑制，§7.4）；入场缩放/输入延迟同上 |
| 通关图片收藏闭环 | 已实现（流程既有） | `LoadCompletionImage` 已通 `block/ch01`；收藏页 12 片 / 大图查看 / 重复挑战既有（§6.10） |

### 4.1 阶段 D 静态证据

- 离线全量编译（Runtime+Tests+Editor，含新增 `BlockOutAcceptanceTests`）0 错误 0 警告。
- 手感配置契约由 `BlockOutAcceptanceTests.验收_手感配置_默认对齐文档约定` 断言（GameplayFeelConfig.Default 全部字段对齐实施说明 §7）。
- 误点距离修正：`BlockOutGameRules.TryGetWrongMoveDistance` 计数空格不含自身占格（多格块轴向穿过自身格不计入），由 `BlockOutAcceptanceTests.验收_误点距离_不含自身占格` 断言。

## 5. 偏差清单（与参考的差异及原因）

1. **displayName 改写**：参考值是设计工具产物；按参考 HUD 实际显示改 `Level N`。
2. **difficulty 显式化**：参考靠 id 后缀推断；移植件写字符串，结果一致。
3. **无游戏内工具确认弹窗**：参考零库存走游戏内确认弹窗（300 币×2 或看广告×2）；本地版
   零库存槽位提示并指向首页商店购买（广告接入不在本期）。购买数值与参考一致。
4. **魔法星动效**：已实现星从起点（棒端占位 = 棋盘中心）飞向目标的 `SpawnStarTravel` 1s 路径 + 命中放大脉冲；棒端精确世界坐标待视觉细调（逻辑不受影响）。
5. **广告复活/道具广告奖励**：本期不接广告（接口保留，资格逻辑已对齐）。

## 6. 手动验收步骤（需 Unity 编辑器/设备，按用户授权）

1. 打开 Unity 让工程刷新编译，确认 Console 无报错后进入 Play Mode（首关）。
2. 连点：点一块飞出途中立刻点另一块可响应；快速点同一块两次只消一次；最后一块动画播完才弹胜利。
3. 误点：同一受阻块连点三次只扣 1 心；三块不同受阻块耗尽 3 心失败。
4. 提示：第 2 关起连点提示按钮，高亮目标轮换不重复；无可飞块时不扣库存。
5. 锤子：第 3 关起进入选择态点受阻块消除，点空白/再点锤子取消不扣库存。
6. 魔法：第 4 关起施法，确认并行多星、最多 6 块、一次扣 1。
7. 复活：第 5 关失败后免费复活可反复用且补满 3 心；第 11 关金币复活扣 300 补 1 心。
8. 计时：远程开 `use_time_fail_mode` 后验证 30s、10s 预警、复活 +20s、切后台冻结、
   普通飞出不停表。
9. 商店：300 币购买得 2 个道具；金币不足禁买。
10. 关卡：首页第一章 12 关逐关可打，最后一关通关后有明确结束状态；通关插图→收藏→下一关闭环。
11. 旧存档：用带进行中局的旧档启动，确认失配重开/全移除局补结算不重复发奖。

## 7. 复跑命令（离线证据）

```bash
# 全量静态编译（Runtime + Tests + Editor，0 错误 0 警告）
dotnet build Tools/CompileCheck/BlockOutCompileCheck.csproj

# 关卡集校验（12 关可解/边界/图片/奖励/覆盖）
dotnet run --project Tools/LevelVerify/LevelVerify.csproj -- <BlockOut 工程根>

# EditMode 规则契约测试（默认排除 [Category("UnityRuntime")]；离线 62/62，3 个广告用例需 Unity 运行时）
dotnet run --project Tools/TestRunner/TestRunner.csproj   # 默认已排除 UnityRuntime，可用 --where 覆盖

## 8. 阶段 E：验收用例代码化与证据汇总

### 8.1 验收测试文件
- `Assets/BlockOut/Tests/EditMode/BlockOutAcceptanceTests.cs`（新增）：对齐 §6 手动验收清单 + 阶段 D 手感契约。
  - 可离线验证的逻辑/配置用例（连点同块只一次、误点距离不含自身占格、提示轮换不重复、锤子零库存失败、
    魔法目标上限、道具包 300/2、复活经济数值、奖励表优先、手感配置默认契约）正常编写，离线 NUnitLite 可跑。
  - 依赖 Unity 资源/协程/UI 的用例（通关图片收藏闭环）标注 `[Category("UnityRuntime")]`，仅 Unity 编辑器运行。
  - 按用户要求"只写不跑"：本次仅做 `Tools/CompileCheck` 静态编译校验（0 错误 0 警告），实际运行交 Unity Test Runner。

### 8.2 离线证据（截至 2026-10-20）
| 工具 | 结果 |
|---|---|
| CompileCheck（Runtime+Tests+Editor 全量编译） | 0 错误 0 警告 |
| LevelVerify（12 关可解/边界/图片/奖励/覆盖） | 12/12 通过，0 failures |
| TestRunner（NUnitLite，默认排除 UnityRuntime） | 62/62 通过，0 失败；3 个广告用例按类别排除 |
| BlockOutAcceptanceTests 编译 | 通过（静态，未执行） |

### 8.3 回交状态口径（区分三档）
- **写了代码**：阶段 A–D 全部实现 + 阶段 E 验收用例文件；离线静态已检查。
- **静态已检查**：全量编译、关卡校验、规则契约测试、手感配置契约均已离线跑通。
- **待实际运行（需 Unity 编辑器/真机）**：§6 手动验收步骤中依赖协程演出/UI 时序/资源加载的项
  （连点时序、误点扣心、入场/失败/手势演出观感、收藏页 12 片展示、旧存档恢复闭环）。
  这些项未在沙箱内运行，按用户授权执行，不冒充通过。
```

## 9. 复查整改 R01–R11（2026-10-20 复查清单后，本轮落码）

> 来源：`Docs/ArtOut玩法对齐复查整改清单_2026-10-20.md`。
> 本轮回交口径：按用户要求**只更新实现记录、不补测试用例**；所有项均为**代码已实现 + 静态已检查**
> （离线阅读源码/配置，不启动 Unity、不编译/Play Mode、不跑外部 C# 构建），运行时/真机行为验证列为"待运行"，
> 由用户授权执行，不冒充通过。

| 项 | 状态 | 修改文件 / 实际调用路径 | 失败 / 中断处理 | 待运行验证 |
|---|---|---|---|---|
| R01 复活恢复输入 + 模态标记 | 代码已实现 | `BlockOutGameManager.CompleteReviveSuccess`：复活成功 `boardView.SetInputEnabled(true)`；`BlockOutUIController.CloseFailLayer`→`SyncModalFlag`（Free/Ad/Coins 三条成功路径均走） | 仅释放失败锁，不误触暂停/工具锁；`runToken` 变更由新局接管 | 生命/时间两种模式、三种复活各验证可点可计时、再失败再复活；恢复失败存档同语义 |
| R02 配置真正生效 | 代码已实现（前期） | `BlockOutContentConfig.Apply`→`BlockOutGameManager.LoadLevel` 读 `ConfigUseTimeFailMode`/`GameTimeSeconds`；`FinalizeRemoval` 用 `enableCombo/enableSpecialBlocks` 开关；复活常量走 `BlockOutContentConfig`；`GetLevelReward` 保留 0 为合法禁发值 | JSON 加载失败整体回退 Default 并 LogWarning（明确路径与原因） | 仅改 JSON 即可开时间模式/改费用加时；无 gametime 用兜底；默认关连击与特殊块 |
| R03 魔法链不被二次否决 | 代码已实现 | `BlockOutToolController.PickMagicTargets(count, extraFilter)`：链式模拟中 `ignored`（已选=模拟移除）与 `considered`（被否决但作障碍）并入同一状态，正确选 A→B→C；`BlockOutGameManager.UseMagic` 传 `IsMagicTargetSelectable`（仅排除冻结锁死），不再原棋盘 `CanMove` 二次否决 | 无目标 `return 0` 不扣库存 | 生产路径验证 3 连/6 连正确消除、只扣一次库存 |
| R04 魔法动画可暂停/失败取消/统一胜利 | 代码已实现 | `MagicRoutine`：`pendingHits` 归零即解工具锁（飞出可继续，R04）；`hitFailed` 停止后续目标并解锁输入；失败局不改回 Ready；胜利经 `MaybeWin` 统一入口。`MagicTargetRoutine`：`while(IsPaused) yield return null` 冻结；`State==Lost` 取消；命中后 `PersistProgressAndTools()` 取 `saved`，失败 `yield break` 不再飞出 | `myToken` 令牌保护重开/切关/退出；`OnLevelWon` 幂等守卫 | 星路径/命中阶段分别暂停、切后台、超时、重开；旧回调不消块/不解锁新局；普通飞出与魔法重叠只在应有时机结算一次 |
| R05 金币复活原子事务 | 代码已实现 | `ReviveWithCoins`：内存 `ApplyReviveState`→`CommitProfileChange(() => { SpendCoins; WriteActiveRunToProfile })` 一次性提交；失败 `RestoreReviveSnapshot` 回滚且不关失败层 | `OnSaveFailed` 通知 UI；回滚后 `ReviveUsedThisRun`/生命/时间/`restoredLost` 全部复位 | 注入提交失败：金币与失败局完整保留；重载一致、下次合法复活仍可 |
| R06 结算失败 UI 引导（不假报） | 代码已实现（本轮） | `BlockOutUIController.SubscribeGameEvents` 订阅 `GM.OnSaveFailed`→`HandleSaveFailed` Toast；`HandleLevelWon` 检测 `GM.SettlementSaveFailed`：禁用 Next/Replay、改写 `SettleNoteText/SettleRewardText` 为"未保存/未发放"、保留单关图片展示、不显示奖励成功 | `GM.OnLevelWon` 失败分支已回滚 Profile（进度/奖励/拼片未落盘），置 `SettlementSaveFailed=true` 并触发 `OnSaveFailed`；提供 `RetrySettlement()` 幂等重提 | 保存失败不假报领奖；返回首页重进本关重试不重复发奖、不丢结算 |
| R07 道具/魔法消块失败回滚 + 及时存档 | 代码已实现 | `PersistProgressAndTools()` 返回 `committed`；失败 `Tools.SetCounts(Profile...)` 回滚内存库存（新增 `BlockOutToolController.SetCounts`）；魔法每个目标命中后即时 `PersistProgressAndTools`（工具 + RunRemoved 同提交） | 中途保存失败 `hitFailed=true` 停止后续目标、解锁输入，不强行结算/胜利 | 提示/锤子/魔法消费保存失败均无半成功；魔法中途重启已付费与已承诺消除匹配 |
| R08 重复误点反馈 + 持久标记 | 代码已实现 | `BlockOutGameManager.HandleBlockTapped`/`FeedbackWrongTap`：重复误点仍走 `FeedbackWrongTap`（撞击+音效+持久红环），仅文案区分首次/重复、不重复扣心；`OnBlockWrongMarked` 区分提示 | 反馈动画受 `runToken` 保护；回位回调仅当 Ready && !Paused 解锁 | 同块三次误点只扣 1 心、三次有反馈；错误标记与存档一致；暂停误点不错误解锁 |
| R09 棋盘手势/缩放接入 | 代码已实现（本轮） | 新增 `BlockOutBoardGesture`（IPointer* 手势：双指捏合缩放 / 单指平移 / 结束后 `SuppressTaps` / 弹窗暂停输入锁 `Blocked` 屏蔽 / 桌面滚轮 / 双指转单指防跳位）；`BlockOutBoardView` 新增 `zoomRoot` + `GetZoomRoot/GetZoomScale/ResetZoom` + `FocusOn`；`BlockOutAppBuilder` 在 `boardArea` 挂手势并注入 `GM/BoardView/Viewport` | 弹窗/暂停/输入锁时 `Blocked` 复位手势、不穿透；`ResetZoom` 切关/重开复位 | 游戏页双指缩放可用；拖动/双指变单指不消块不跳位；弹窗期间不穿透 |
| R10 锤子/提示演出 | 代码已实现（本轮） | 锤子：`BlockOutGameManager.HandleBlockTapped` 命中 `SpawnStars` + `PlayHammerHitSoundDelayed`（带 `tapToken`）；提示：`BlockOutBoardView.HintFlashRoutine` 块体颜色 `#83F851` 闪烁 + `FocusRoutine` 视口聚焦目标居中放大 1.18× | 延迟音效 `tapToken` 校验防旧局播放；聚焦 `runToken` 终止 | 锤子命中声画同步、最后一块不提前结算；提示远处块聚焦、重开不播旧局延迟声 |
| R11 单关通关图片反馈 | 代码已实现（本轮） | `BlockOutUIManager` 新增 `SettleLevelImage`（260×216，默认 disable）；`BlockOutUIController.RefreshSettleReveal(chapter, showSingleLevelImage)`：单关经 `GM.LoadCompletionImage()` 取纹理 `Sprite.Create` 赋图并 enable，隐藏章节拼片网格；章末才展示章节拼片 | 取纹理失败回落 disable，不阻塞结算 | 完成任意一关即展示该关关联图；收藏/重进关联一致，不必先通 12 关 |

### 9.1 对原记录超称项的更正说明
- **"棋盘缩放已实现"**：复查清单 R09 判定当时未接入；本轮已通过 `BlockOutBoardGesture` + `BlockOutBoardView.GetZoomRoot` 实际接入**游戏棋盘**（非仅收藏页 `PinchZoom`），该声称现已成立。
- **"事务化 / 配置统一来源"**：R05/R02 已分别落实金币复活原子事务与 JSON→消费者链路，声称成立；复查中"魔法过滤测试用 `_ => true` 绕过生产过滤器"的问题，本轮已通过 R03 在生产路径上消除二次否决（测试不在本轮补，按用户要求只改文档）。
- **无条件 Ignore 的收藏测试**：按用户要求本轮回交不补测试用例；该收藏闭环改列为"待 Unity 运行时验证"（见 §6 第 10 项），不再记为已完成测试。

### 9.2 本轮回交边界
- 不修改只读参考工程；保留现有关卡、存档键、资产 GUID。
- 不主动执行 Unity 刷新/编译/Play Mode/测试/Console/外部 C# 构建；以上运行时验证项均离线静态已检查，待用户授权运行。
- 不补测试用例（R12 用户调整为只更新文档）。

