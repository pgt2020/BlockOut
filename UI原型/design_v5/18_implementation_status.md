# 本轮实现与交付状态（2026-10-16）

本表同步程序与设计当前状态。**代码已修改 ≠ 静态检查通过 ≠ Unity 编译通过 ≠ 运行验收通过**，四档独立判定。

| 档位 | 含义 | 本轮状态 |
| --- | --- | --- |
| 代码已修改 | 源码已按要求改到磁盘 | ✅ 第十三轮 R01–R23 全部条目文件已实现（15 程序集 / 63 脚本 / 14 资产） |
| 静态检查通过 | 括号配平 + 类内裸调用可解析 + 私有方法未使用 + 事件订阅配对 + asmdef 闭环 + 资产 GUID 完整 | ✅ 通过（`Tools/static_check.py`，**不等于能编译**） |
| Unity 编译通过 | 编辑器 Console 无 error | ❌ **未验证**（按项目要求未触发 Unity） |
| 运行验收通过 | Play Mode / 真机逐项确认 | ❌ **未验证** |

## 第十三轮 · 工程化重构交付（2026-10-16）

`工程化重构需求与实现表.md` R01–R23 全部条目已文件级实现并静态核对。**逐项状态见该表 §4 与 `Docs/重构交付与验收.md`。** 本轮要点：

| 项目 | 内容 | 状态 |
|---|---|---|
| 唯一启动入口 | `Launcher.unity`（唯一启用场景，guid `a289df1e153c4b67a295ab66a07c2d4e`）→ `BlockOutLauncher`（重复入口防护）→ `BlockOutStartupSequence` 8 步显式启动 → `BlockOutAppRoot`（服务注册表 + 生命周期状态机）→ `BlockOutAppBuilder` 装配；旧 `RuntimeInitializeOnLoadMethod` 启动器 / `Boot.unity` / 旧华容道 11 文件已删（零引用验证） | 文件已实现 + 静态已核对；运行未验证 |
| 分层与程序集 | 28 个 .cs 迁入 `Assets/BlockOut/Runtime/{Bootstrap,Contracts,Core,Gameplay,UI,Rendering,Infrastructure/*}`，.meta/GUID 随迁保留；15 个 asmdef 无环闭环 | 静态已核对 |
| 存档与事务 | `BlockOutSaveService`（v2 键不变、v1→v2 迁移保留旧键）+ `BlockOutProfileTransaction`（JSON 快照、失败自动回滚、未提交=放弃）；旧空棋盘补结算 / 延迟提交 / 放弃不恢复等既有修复全部保留 | 静态已核对；测试未运行 |
| LevelPlay 广告 | `LevelPlayAdAdapter` 按 ironSource 官方 API 写好五回调建模、requestId 单次获奖、关闭≠获奖、缺凭据安全降级不模拟成功；由 Bootstrap 按 `BlockOutAdConfig` 注入 | 静态已核对；**SDK 包/App Key/Placement 外部配置待补** |
| UI Prefab | 10 个实际 Prefab（8 页面 + AppRoot + BoardRoot）由 `Tools/gen_blockout_assets.py` 生成；`MakeScreen` 正常路径走 Prefab 注册表实例化，无双重生成 | 静态已核对；运行未验证 |
| 测试 | 56 个用例（EditMode 49 + PlayMode 7）：规则 10 / 道具与广告契约 12 / 存档事务 14 / 结算事务与配置 13 / 生命周期 7 | 已写未运行 |
| 编辑器工具 | `BlockOutBuildPreflight`（IPreprocessBuildWithReport 发布门禁）/ `BlockOutProjectChecks` / `BlockOutPrefabGenerator` / `BlockOutAdConfigValidator` | 已写未在 Unity 内执行 |
| **本轮修复的注入缺陷** | `BlockOutSettlement` 原持有 Awake 旧 Profile 对象，服务注入后奖励会被旧对象直写 + 服务档案覆写而**丢失**；已修：`Settlement.BindProfile` 跟随服务档案 + 去掉内部直写，统一由 GM 单点落盘 | 代码已修改 + 静态已核对；运行待验证 |
| **测试文件重建** | `BlockOutPersistenceTests.cs`（14 用例）与 `BlockOutSettlementTransactionTests.cs`（13 用例）曾丢失，本轮按既有测试风格重建，远程键名集合断言已含旧键 `ArtOutUseTimeFailMode` | 已写未运行 |

> 本节不构成 Unity 编译或运行验收通过。运行验收步骤见 `Docs/重构交付与验收.md` §11。

## 第十二轮 · 设计收尾复核（2026-10-16）

针对上轮评审四项收尾问题的修复与验证。**全部结论来自渲染后 PNG 的像素级断言（`verify_round4.py` 215 项 ALL PASS）——不是“脚本执行成功”；像素/文案/几何检查通过同样不等于程序运行验收通过。**

| # | 问题 | 修复 | 验证证据 |
|---|---|---|---|
| 1 | 普通结算稿与程序结构不一致（脚本称“按程序实际结构绘制”，实画 300×500 居中弹窗 + 260×216 揭晓区 + 三个次级按钮纵排） | `gen_clean_pages.py` 结算段重写：`settle_geom(W,H,st,sb)` 严格按 `09_component_spec.md` §5.1 / 程序 `LayoutFullPages` 公式计算几何（Card 铺满安全区、`revealH=clamp(H−330,120,360)`、CollectionBtn x=16 与 ReplayBtn x=width/2+6 半宽并排、HomeBtn 通栏），内置断言（revealH 范围 / 内容底≤卡底 / 按钮不重叠）；四态交付 —— `clean_settlement`（首通）、`clean_settlement_repeat`（重复通关）、`clean_settlement_chapter`（章末 contain）、`clean_settlement_short`（360×640 短屏，安全区接下限 24/16，卡 312×600、揭晓区 280×270）；删除“已经与程序实际结构一致”错误说明，脚本 docstring 注明几何/文案/奖励的源码行号出处与“Unity 内实际运行效果仍未验证”口径 | H 节逐项：卡白底铺满安全区、上下安全区带为非卡底色、标题/拼片/注记/金币/奖励文字墨痕在位、作品区与 PIL cover 期望 meanabsdiff<12、章末 contain 1:1（meanabsdiff<2）+ 信笺边 #FFF7EF、NextBtn 珊瑚/禁用灰两态、次级行同一 y 两枚等宽（SVG 精确几何字符串断言 x=40 / x=201、y=600、149×44）、HomeBtn 通栏、内容底 700≤卡底 810（390 档）/ 610≤624（360 档） |
| 2 | 设置页纯界面残留“二级页面：不显示底部导航；返回上一层”（开发说明混入玩家界面） | `strip_annotations` 增加**多行注释**状态机（`<!--` 起 `-->` 止整段剔除）——两行注释正是上一轮 clean_collection 未重新生成的同一根因；新增 `SETTINGS_EXTRA_RULES` 剔除含该说明的行；规格版 16 完整保留该注释；SVG 与 PNG 均重新导出 | I 节：clean_settings.svg 无“二级页面”且规格版 16 保留、对应 PNG 渲染带无墨痕；I3 全套 clean_*.svg 渲染文本禁用词扫描（二级页面/不显示/入口见/刷金币/道具/+N/TODO/未实现/待定/示意/规格/标注/开发/设计说明）0 残留 |
| 3 | 收藏页承诺未实现的道具奖励（“已通关关卡可重复进入（刷金币/道具）…”） | 14 号规格源稿第 134 行改为“重玩已通关关卡可获得金币，拼片不会重复解锁；未通关关卡锁定”，纯界面版从源稿**重新提取**保证两版一致；13 号规格稿同步去“+N”、去“（刷金币/道具）”，底部规则框加高并注明“结算 = 程序 LayoutFullPages 真实布局……本页弹窗仅为结构示意，终版见 clean_settlement / 17”；**未为配合文案新增任何未确定的道具机制** | I 节：clean_collection 无“道具”/“刷金币”字样、新文案在位；渲染文本扫描 0 残留 |
| 4 | 章末结算与普通结算两份结构、17 旧稿元素错位 | `gen_chapter_end.py` 全文重写：改为 `from gen_clean_pages import settle_geom, settlement_page, SETTLE_DEFS` 同源同几何；17 三态 A/B/C 直接调用 `settlement_page()` 绘制；删除旧自绘的查看大图入口/奖励卡/264×264 作品盒；17 SVG 输出 SETTLE_DEFS（否则珊瑚按钮/背景渐变/金币图标无定义渲染为空白）；按钮标签统一为程序标签“重玩本关” | C 节：17 三态 contain 信笺边、主按钮三态颜色（珊瑚/禁用灰/珊瑚）、次级行一行两枚等宽、页外图注探针 y=26/906/1786、无安全区虚线/查看大图/+N；PNG 尺寸 780×5348 不变 |

配套资产：`gen_cover_crops.py` 新增 `contain_fit` 与 `assets/r12_310x360_contain.png`（310×310 作品居中 + 上下 25px #FFF7EF 信笺边）、`assets/r04_310x360.png`、`assets/r04_280x270.png`（两档 cover 裁切），`r04_260x216.png` 标注 deprecated。

回归：`verify_structure.py` PASS（棋盘几何与 04 一致）、`verify_regions.py` PASS（12 区变化率 10.0–27.4% / 平均 17.0%）。**本轮仍未触发 Unity**：全部结论限于设计稿层面（像素 + SVG 文案 + 精确几何 + 禁用词扫描四层）。

> **交付给开发**：有效稿路径 + Prefab 接入后视觉对照基准见 `README.md`「开发接入交付索引（视觉对照基准）」。两条强制声明（ART_DRAFT 标记 / 设计图≠Unity 运行验收）已写入该索引顶部。


## 第十一轮 · 存档与结算修复（2026-10-16）

> 本轮只改代码与规格，**未改任何设计纯界面图**。

| 项目 | 本轮处理 | 状态 |
|---|---|---|
| **最后一块动画中存档 → 重启空棋盘无法结算（P1，上一轮提出但未真正修复）** | 改为**延迟提交**：`BlockOutGameRules.TryTap` 成功时**不再 `Remove`**，只做判定；移除移到 `BlockOutGameManager.OnFlyOutComplete` 的提交点（`if (block.Active) Rules.Remove(block)`）。存档因此只会落在两种稳定局面——"动画开始前"（该块仍在）或"提交完成后"（移除+连锁+胜利判定已跑完），不再存在"主块已消失但结算未完成"的中间态。`Remove → FinalizeRemoval(含 ProcessRemovalChain) → SaveActiveRun` 三者在同一调用栈同步完成，普通块连锁不会漏 | **代码已修改 + 静态检查通过；运行待验证** |
| **恢复端补胜利分支** | `LoadLevel` 的 restoreRun 分支新增 `else if (!restoredLost && Rules.IsWon) pendingWinRestore = true;`，用于识别**上一轮之前已写入的空棋盘旧存档**。收尾处消费该标记 → `CompletePendingWin()` → 直接复用 `OnLevelWon()`。防重复靠三重保证：`MarkLevelCompleted` 内部 `Contains` 去重（拼片不重复解锁）、`CurrentLevelIndex` 取 `Mathf.Max`（推进幂等）、结算末尾 `runPlayable = false` + `ClearActiveRun()` + `Save()`（存档失效，下次启动不再进此路径）。`pendingWinRestore` 在 `LoadLevel` 开头无条件重置，新挑战/重开不继承 | **代码已修改 + 静态检查通过；运行待验证** |
| **`BootSequence` 同步** | `BlockOutUIController.BootSequence` 的恢复分支条件由 `Ready \|\| Lost` 扩为 `Ready \|\| Lost \|\| Won`，并在 `Lost` 之后加 `else if (Won) HandleLevelWon()`。顺序仍是先 `UI.ShowScreen(Board)`（内部 `HideAllBoardLayers`）再开结算层，避免刚结算出的界面被 `GoHome()` 顶掉 | **代码已修改 + 静态检查通过；运行待验证** |
| **普通结算页与 `clean_settlement.png` 结构不一致（P2）** | 两套结构确实不同：旧图 300×500 固定居中弹窗 / 260×216 揭晓图 / 查看收藏·重玩·返回首页纵排；程序为 Card Stretch 铺满 `SafeRoot` / 揭晓高 `clamp(屏高−330,120,360)` / 收藏与重玩**左右并排**、返回首页另起一行通栏。**统一到程序现行结构**，在 `09_component_spec.md` 新增 **§5.1「普通关卡结算页结构（唯一基准）」**（容器层级 + 9 个元素逐条宽高 y 坐标 + 与旧图差异表 + "以本节为准、纯界面图需重绘"裁决），§5 组件表、§8 跳转表、§9 定稿条目同步指向 §5.1。程序侧**不改**结构 | 规格已统一（代码已修改 + 静态检查通过）；纯界面图重绘**已于第十二轮完成**（四态 + 短屏均已交付并经像素验证，见下节） |

### 第十一轮待运行验证

- 普通块动画**尚未提交移除**时切后台并结束应用（飞出约 40% 处）→ 重启后该块**仍在棋盘上**、可继续点击（第十一轮延迟提交后的正确预期：动画中途保存的不是"块已消失"快照）。
- 动画**提交完成前**切后台 → 与上一条同理，重启后应看到该块仍在、可继续点。
- 恢复**旧的空棋盘存档**（第十一轮之前写入的存档）→ 应走一次结算并把存档失效；这是唯一走"恢复补结算"的路径。
- 补结算后**再次重启** → 不得重复发奖、不得重复解锁拼片、不得重复推进关卡。
- 炸弹块点击后立刻切后台 → 重启连锁要么完整生效、要么完全没发生，**不出现"主块没了但邻居还在"**。
- 魔法棒动画中保存（`SaveActiveRun` 早于本次 `Rules.Remove` 提交）→ 恢复后仍是**有效棋盘**、该目标块仍在，不得产生空棋盘 Ready，也不得丢失该次施法后的连锁结果。
- 重开本关 / 放弃本关（含失败后退出、暂停后退出）后再切后台或重启 → 不得恢复已退出的对局（`runPlayable` 约束，需回归确认未被本轮改动破坏）。
- 结算页结构：按 §5.1 核对 Card 铺满安全区、揭晓高度随屏高变化、收藏/重玩并排、返回首页通栏；360×640 档 revealH 应落到下限 120。

## 第十轮 · 设计交付复核（2026-10-16）

针对上轮评审四项交付问题的修复与验证结果。**全部结论来自渲染后 PNG 的像素级断言（`verify_round4.py`），不是"脚本执行成功"**。

| # | 问题 | 修复 | 验证证据 |
|---|---|---|---|
| 1 | 360×640 适配图实际用 716 高排版，不能证明 640 适配 | `gen_adapt.py` 重写：`adapt()` 用**真实设备高度**（640/844/932）；导航/CTA/进度卡自下向上按真实剩余高度布局，预览卡 `min(cap, 余高)` 压缩；说明区单独追加在页面之外（独立底色 + 边界线），不参与导航/安全区计算；生成时布局断言（无重叠、不越安全区、无负高） | 三档页面边界像素级恰在 H 处（720×1460 / 780×1868 / 780×2044 画布）；360 档导航底 612 ≤ 620（安全区上沿）；H−3 处仍是页面底色（未被加长）；安全区虚线正向对照在 st / H−sb 行 |
| 2 | `preserveAspectRatio="none"` 拉伸作品 | 新增 `gen_cover_crops.py`：所有展示图从统一 1080 源画布按容器**精确比例**重新裁切导出（r03_300×204 / r04_260×216 …），SVG 改 `xMidYMid slice` 双保险；26 张既有裁切图逐像素复验 = center-cover；r12_117×100 为 contain 预渲染成图，按 1:1 放置（已验证两侧信笺边存在） | 渲染容器 vs PIL center-cover 期望 meanabsdiff 6.90–7.06（重采样噪声级）；远离历史 none 拉伸参照物（11.8 vs 7.1）与母版压扁参照物（10.9–13.2 vs 6.9）；圆形糖果/轮廓随等比裁切保持 |
| 3 | 纯界面交付不完整、17 clean 仍带标注 | 新增 `gen_clean_pages.py`：导出 clean_game / clean_collection / clean_store / clean_settings（从规格稿提取页面主体，剔除安全区虚线/示意带/文字、手势条、滚动区示意、热区虚线、页外图注与注释）；按程序实际结构新绘 clean_settlement；`gen_chapter_end.py` clean 版删除页内状态徽章与安全区标注，A/B/C 名称移到**页外**图注区 | 10 张 clean 页安全区行带红线 0 像素；17 clean 三页虚线带 0、徽章 0、手势条 0、页外图注存在；结算页卡白底/珊瑚主按钮/260×216 揭晓区/ Dim 遮罩均通过。**⚠ 其中"结算页 260×216 揭晓区"是按当时程序值画的；该图已由第十二轮按 §5.1 重绘为四态（首通/重复/章末/短屏），旧结构图已删除** |
| 4 | 首页 12/12 缺"下一章未发布"态 | `gen_clean_ui.py` 拆两态：`clean_home_12`（已发布示例）/ `clean_home_12_preparing`（未发布，主 CTA 禁用"新章节准备中"，与程序 PublishedChapters=1 一致）；12/12 进度文案改"完整作品已解锁" | preparing 主 CTA 像素 = 禁用灰 (222,209,196)，已发布示例 = 珊瑚红 (255,123,109) |

回归：`verify_structure.py` PASS（棋盘几何与 04 一致）、`verify_regions.py` PASS（12 区变化率 10.0–27.4% / 平均 17.0%，剪影区分度 17.0%）、既有 26 张裁切图母版一致性 ALL PASS。**本轮未触发 Unity**：适配通过指"设计稿在真实设备高度下排版成立且经像素验证"，不等于程序在真机验证。

| 项目 | 本轮处理 | 状态 |
|---|---|---|
| **编译阻塞修复** | `BlockOutGameManager.OnApplicationPause` 调用了不存在的 `PauseByAppBackground()`（类中声明为 `PauseByBackground()`），C# 直接报 CS0103，工程无法编译。已统一为 `PauseByBackground()`，与 `OnApplicationFocus` 共用同一后台暂停入口；全库 0 处残留 | **代码已修改 + 静态检查通过；Unity 编译与运行均未验证** |
| **静态检查覆盖补齐** | 新增"类内裸调用 `Foo(` 必须解析到本文件可见符号"检查项（本项直接捕获上述编译错误）；特性调用与 `new Type(` 不再误报；新增私有方法未使用检查；事件 `+=`/`-=` 按宿主+事件名配对统计 | 代码已修改，检查脚本为一次性工具，用后已删除 |
| **事件订阅现状** | `OnAppForegrounded` 声明/触发/订阅/取消订阅四处一致（GM 声明 82 行、触发 899 行；UI 订阅 135 行、处理器 321 行、取消订阅 347 行 `OnDestroy` 内）。剩余 8 条未配对订阅全为 lambda（`GM.OnLivesChanged`/`OnCoinsChanged`/`OnRemainingBlocksChanged`/`OnTimeChanged`/`OnBlockWrongMarked`、`Combo.OnComboChanged`、`Tools.OnToolStateChanged`/`OnHammerModeChanged`），是**既有写法非本轮引入**，生命周期与订阅方一致，不影响正确性 | 代码已修改；如需彻底治理须改具名 handler，属独立重构 |

| 项目 | 本轮处理 | 状态 |
|---|---|---|
| UI 工厂调用 | Card/Panel/SpriteImage 返回 Image，父节点一律取 `.rectTransform`；全量扫描确认无 Image 当 Transform 用、无漏参、无重复 Image | 已改代码，待编译 |
| 动画与重建 | 取消/成功回调分离；`OnFlyOutCancelled` 在令牌仍有效时把 ResolvingMove 放回 Ready；`GiveUp` 归位状态并解视图；Rebuild 有 rebuildPending 闭环 | 已改代码，待运行 |
| 商店 | 解锁按 EffectiveLevelNumber（档案 MaxLevelReached，冷启动未进关卡也正确）；库存读档案；`PurchaseTool` 保存失败回滚；Tools 仅在成功后同步 | 已改代码，待运行 |
| 图片揭晓 | 1080 源画布固定 4×3 裁切；先组整张 Artwork 再整体 cover/contain；不读 CPU 纹理；缺剪影回 null 由 UI 显示中性遮罩 | 已改代码，待视觉验收 |
| 收藏 | 内容区 ScrollRect（顶栏/导航固定）；关卡独立 44×44 射线热区；12/12 才开放当前章节大图；切章节复位缩放 | 已改代码，待运行 |
| 大图手势 | RectMask2D 固定裁切视口；1–3 倍缩放；拖动限位换算画布坐标；双击复位；关闭/切章/再开复位 | 已改代码，待真机验收 |
| 设置 | 画布级完整页（音乐/音效/震动 + 关于弹层）；回到暂停层保持暂停；两条返回路径；玩家页面无开发说明文字 | 已改代码，待视觉验收 |
| 结算 | 揭晓图 + 奖励 + 下一关/下一章/收藏/重玩/返回首页；章末切 contain 与"进入下一章"/"新章节准备中"。**结构基准见 `09_component_spec.md` §5.1**（安全区完整页；收藏/重玩并排、返回首页通栏），设计纯界面图已按 §5.1 重绘（第十二轮：首通/重复/章末/短屏四态，与程序现行结构一致） | 代码已修改，待视觉验收；**设计图已同步** |
| 布局居中 | 设置页/结算页改用**统一安全区根节点 `SafeRoot`**（Stretch + 按 safeArea 内缩），Card 挂其下铺满，不再做位置补偿；`ClampCardWidth` 改递归查找 | 已改代码，待多分辨率验收 |
| **章节图导入配置** | 三个 `.meta`：`textureType` 8(Sprite)；**`spriteMode` 1(Single)**（上一轮误写 0=None，Single 应为 1）；`spriteMeshType:1`(FullRect 完整矩形)；`nPOTScale:0`(1080 不缩放)；关 mipmap、Clamp、不压缩；**末尾误追加在 `TextureImporter` 块外的顶层导入字段已全部删除**；GUID 未变 | 已改配置，待 Unity 导入验收（`Resources.Load<Sprite>` 实际取图必须验证） |
| **切后台回前台** | 新增 `pausedByAppBackground` 标记 + `OnAppForegrounded` 事件；`Pause()`（玩家主动）清标记，`PauseByBackground()` 置标记；回前台由 UI `HandleAppForegrounded` 补开 `PauseLayer`，**不自动 Resume**；首页/商店/收藏及已开着的设置/确认/失败/结算层不叠层；失败局只落盘不弹层 | 已改代码，待真机切后台验收 |
| **魔法棒逐次重选** | `UseMagic` 施法前只探测"是否有目标"（无目标不扣库存、只扣一次库存）；`MagicRoutine(int)` 改为 while 循环：每轮按最新棋盘 `PickActionableTargets(1)` 重选一个目标 → 飞出 → 移除 → 计分 → 特殊块连锁 → 下一轮重选，直到 3 块上限/无目标/被取消/已胜利；保留令牌、暂停、冻结限制 | 已改代码，待运行（需串行解锁局面才能验证连消 3 块） |
| **失败模式双向恢复** | 拆分 `ConfigUseTimeFailMode`（新挑战配置）与 `UseTimeFailMode`（进行中对局实际模式）；`LoadLevel` 新局用配置值，恢复有效对局改为 `UseTimeFailMode = Profile.RunFailMode == 1`（0→false / 1→true），不再只在 ==1 时置 true | 已改代码，待运行（需造两种存档分别验证） |
| **放弃后不写回存档** | 新增 `runPlayable` 约束所有落盘入口：`SaveActiveRun` 首行拦截；`LoadLevel` 建局置 true；`GiveUp`/`OnLevelWon` 置 false；`PauseByBackground` 对无有效对局直接返回。覆盖"失败后退出"与"暂停后退出"两条路径 | 已改代码，待运行（退出后重启应冷启动进首页） |
| **章节图非正式标记** | 新增 `block/ch01/ART_DRAFT.txt`；三张图为程序化矢量稿，命中标记时 `Status=Placeholder`、`IsDraftArtwork=true`，不计入正式素材；美术交付最终图后删文件即转 `Loaded` | 已改代码，待运行 |
| **倒计时存档** | 新增 `RunFailMode/RunLost/RunFailReason/RunHasTimeRecord`；0 秒是有效存档不再被当作"无记录"；恢复失败局直接进失败层不可操作；复活后清 `restoredLost`；`Pause`/`OnApplicationPause`/`OnApplicationFocus` 均落盘；旧存档默认生命模式不受影响 | 已改代码，待运行 |
| **道具反馈** | 锁定/零库存不再 `interactable=false`（否则点击不触发）；新增 `TryUseTool` 分流未解锁→提示+轻抖、零库存→提示+轻抖、暂停/忙态→静默拦截、确无目标→"没有可用目标" | 已改代码，待运行 |
| **特殊块规则统一** | 新增 `FinalizeRemoval` 集中"连锁→剩余数→胜利→存档→状态复位"，普通点击/锤子/魔法三路径共用；魔法补连锁；`PickActionableTargets` 让提示与魔法只选可操作块；规则：锤子可消冻结块，提示/魔法不可选冻结块 | 已改代码，待运行 |
| **大图手势衔接** | 新增 `awaitAllRelease`：双指结束后仍有手指未抬起时禁止建立拖动基准与拖动，全部手指抬起后自动解锁并重建基准，消除画面跳回 | 已改代码，待真机验收 |
| 小屏 | CanvasScaler 固定 390 设计宽；小屏按**画布单位高 ≤700** 判定；预览按余高；收藏滚动不压热区 | 已改代码，待多分辨率验收 |
| 启动链 | Boot.unity（空场景）+ Build Settings 唯一场景 + `RuntimeInitializeOnLoadMethod` 自动引导，三者一致；`ResumeSavedRunOnBoot` 独立标记 | 已核对一致，待运行 |
| 字体 | SourceHanSansCN-Regular.otf + Adobe SIL OFL 1.1 + SOURCE.md；代码优先 `Resources.Load("Fonts/SourceHanSansCN-Regular")`，失败回退系统字体 | 已交付，导入/显示待 Unity 验收 |
| 声音接入 | 2 个 AudioSource + AudioListener + `Resources.Load("audio/"+id)`；开关即时生效 | 已改代码 |
| **章节插画（设计侧交付）** | full/preview/silhouette 各 1080×1080 同画布同构图；preview 与 full 同像素；可编辑 SVG 源 + `PROVENANCE.md` 授权记录；`.meta` 已在 `TextureImporter` 块内配 `textureType: 8`（Sprite）+ **`spriteMode: 1`（Single）** + `spriteMeshType: 1`（FullRect）+ `nPOTScale: 0`（不缩放），末尾误追加的顶层导入字段已删除、GUID 未变 | **B 资源文件已交付，但为程序化矢量稿（`ART_DRAFT` 标记），最终美术未完成**；`Resources.Load<Sprite>` 能否取到仍**必须在 Unity 内验证** |
| **音频（设计侧交付）** | 17 音效 + 3 BGM/章末音乐共 20 个 WAV（44100Hz/16bit/单声道）；文件名与资源契约逐一对齐；响度与循环接缝已客观校验 | **B 正式资源已交付**；Unity 播放效果待验收 |
| 正式内容 | 人工精修插画、完整人工设计关卡 3–12、真实广告 SDK、**特殊块实际关卡配置（extras 为空）** | **未完成；不得宣称上线就绪** |

## 四项交付口径（必须分开表述，不得合并成"全部完成"）

| # | 口径 | 判定标准 | 当前状态 |
|---|---|---|---|
| 1 | **资源文件是否存在** | 文件实际存在于磁盘/包内 | ✅ 存在：章节插画 3 张 + 可编辑源 + 12 张 region 遮罩 + fail 占位 + 对应表 + 字体（含 OFL）+ 20 个音频文件；设计侧另有 4/12 揭晓母版与各容器等比裁切图（`assets/`，含 reveal_04 / r03_300x204 / r04_310x360 / r04_280x270 / r12_310x360_contain） |
| 2 | **是否为当前选定的最终版本** | 是否为本轮修订后的选定稿 | ✅ 插画为 v3 精修版（`gen_ch01_art_v3.py`）；设计稿字体栈/内格线/禁用色已统一；章末三态已统一为完整页；**纯界面交付集为 14 张**：clean_home×5 / clean_game / clean_collection / clean_store / clean_settings / **clean_settlement（首通）+ _repeat（重复）+ _chapter（章末 contain）+ _short（360×640 短屏）** / 17_chapter_end_clean；适配图改为真实设备高度 + 等比裁切；结算图几何与程序 §5.1 一致并经像素验证 |
| 3 | **程序是否已接入** | 代码是否存在对应实现 | ✅ 代码已改（揭晓管线、大图缩放、商店本地事务、音频加载、字体加载、切后台回前台、魔法逐次重选、放弃后不写回存档）；❌ 关卡 3–12 仍为 `gen_placeholder_*`（`GameAssets.json` 仅登记 2 关）、❌ 广告仍 `FakeAdProvider`、❌ `BlockOutLevelExtras.json` 仍为 `{"levels": []}` |
| 4 | **Unity 内是否已验证** | 是否在编辑器/真机跑通并逐屏核对 | ❌ **未验证**：本轮未执行 Unity 刷新、编译、Domain Reload、Play Mode、测试、Console 读取。**C# 代码当前处于"已修改但未编译"状态** |

> **1 + 2 + 3 ≠ 4。** 文件存在且是最终版本、代码也已接入，**不等于运行效果已验证**。
> 同理，**静态检查通过 ≠ 编译通过** —— 第八轮就因为扫描范围不足，漏掉了 `PauseByAppBackground` 这条真实的 CS0103 编译错误。任何"静态扫描通过 = 无编译问题"的表述都与事实不符。
> 同理，**像素/文案检查通过 ≠ 设计交付全部通过** —— 第十一轮 `verify_round4.py` 曾 ALL PASS，但设置页开发说明残留、收藏奖励文案错误、结算图与程序结构不一致三项目视问题仍在（验证项没覆盖到的维度就是会漏）。检查范围本身必须随交付物逐轮扩张。

### 三档交付范围（补充说明）

| 档位 | 范围 |
|---|---|
| **A 设计定稿** | 04–09 + 12–17 全部页面与状态；遮罩几何基准；适配与手势规则；**纯界面交付集（14 张）**：clean_home / _00 / _11 / _12 / _12_preparing / clean_game / clean_collection / clean_store / clean_settings / **clean_settlement / _repeat / _chapter / _short** / 17_chapter_end_clean，规格标注版与纯界面版分清 |
| **B 正式资源已交付** | 章节插画 3 张 + 可编辑源 + 12 张 region 遮罩 + fail 占位 + 对应表 + 字体（含 OFL 授权）+ 20 个音频文件 + 程序绘制图标 |
| **C 程序待验收** | 全部运行效果：图片揭晓、收藏滚动与热区、大图缩放、字体显示、音频播放、多分辨率适配 |

## 资源契约

- 正式章节插画：Assets/Resources/block/ch01/{preview,full,silhouette}，三张共用1080×1080坐标；导入为 Sprite（`textureType: 8` + `spriteMode: 1` Single + `spriteMeshType: 1` FullRect，禁止旋转/紧密裁切）。代码按Sprite矩形裁固定4×3区域，不读取CPU纹理像素。**三张文件已交付**（同画布同构图，preview 与 full 同像素），来源与授权见 `block/ch01/.source/PROVENANCE.md`。**导入配置的最终判定必须在 Unity 内完成**：静态检查只能确认 `.meta` 文本正确，不能证明 `Resources.Load<Sprite>` 已取到图。
- full缺失时暂用preview查看；preview缺失时继续使用程序占位；silhouette缺失时显示中性色，不用原图替代。
- mask PNG是固定源坐标的几何交付基准；程序当前直接按相同矩形裁区域，不声称已支持任意美术alpha边界。后续若改柔边遮罩，需同步渲染实现。12 张遮罩已逐像素校验：1,166,400 像素每点恰好覆盖 1 次。
- 音频：Assets/Resources/audio/{sfx_tap_block,sfx_fly_out,sfx_error,sfx_hint,sfx_hammer,sfx_wand,sfx_star_hit,sfx_coin,sfx_ui_tap,sfx_popup,sfx_toast,sfx_piece_reveal,sfx_level_win,sfx_level_fail,sfx_revive,sfx_countdown_tick,sfx_countdown_end,bgm_home,bgm_game,bgm_chapter_complete}.wav。**20 个文件已交付**，格式 44100Hz/16bit/单声道，峰值 ≤−1dBFS，音效统一 RMS −15dBFS（极差 2.9dB），循环 BGM −19dBFS；bgm_home/bgm_game 接缝首尾跳变 0.00000 且头尾非静音（无爆音无断点），bgm_chapter_complete 为一次性 sting。来源与授权见 `audio/SOURCE.md`。
- 字体：Assets/Resources/Fonts/SourceHanSansCN-Regular.otf；授权原文与来源同目录。度量实测 upem 1000 / CFF OpenType / usWeightClass 400；包内仅 Regular，粗体由 `FontStyle.Bold` 合成，如需观感更佳可补 `SourceHanSansCN-Bold.otf`（同 OFL 1.1）。
- 本地包内关卡只有 blockout_tutorial_01/02；3–12仍为gen_placeholder_003–012。CSV用content_status标明。保持这些ID以兼容现有通关存档。补关卡时必须沿用 CSV 的 `level_id`，否则旧存档 `RunLevelId` 失配会降级为新开局。
- 广告仍使用FakeAdProvider；`Assets/Plugins` 下无任何广告 SDK 程序集，也没有 App ID / 广告位配置，不能写成真实激励广告已接通。接真实广告需先引入 SDK 包。
- 特殊块：`BlockOutLevelExtras.json` 为 `{"levels": []}`，**没有任何关卡配置炸弹/冻结/彩虹**。规则代码已统一（普通点击/锤子/魔法走同一收尾），但因无实际关卡数据，特殊块**不属于本期可验收范围**。补齐时按 `BlockOutLevelExtra`（`levelId` + `sourceSha256` + `pieces[].type` = bomb/frozen/rainbow）填入，hash 不匹配会被忽略。

## 资源文件 ↔ 程序加载路径对应表

| 资源 | 实际路径 | 程序加载代码 | 加载 id / 路径 | 状态 |
|---|---|---|---|---|
| 章节完整图 full | `Assets/Resources/block/ch01/full.png` | `BlockOutGameManager.LoadCompletionImage()` → `Resources.Load<Texture2D>(pic.completeImage)` | `ArtOutPictureConfig.completeImage = "block/ch01/full"` | ✅ 文件在位；Unity 内显示未验证 |
| 首页预览图 preview | `Assets/Resources/block/ch01/preview.png` | `ArtOutUIController`（预览卡） | `previewImage = "block/ch01/preview"` | ✅ 文件在位；未验证 |
| 剪影 silhouette | `Assets/Resources/block/ch01/silhouette.png` | `BlockOutChapterArtProvider`（未揭晓区） | `shapeImage = "block/ch01/silhouette"` | ✅ 文件在位；未验证 |
| 12 张 region 遮罩 | `UI原型/design_v5/assets/region_01..12.png`（**设计侧基准**） | 程序按 Sprite 矩形固定裁 1080 源画布 4×3，**不读 mask PNG** | 无独立加载路径 | ✅ 几何基准一致（逐像素校验）；程序不消费此文件 |
| fail 占位 | `UI原型/design_v5/assets/ch01_fail_placeholder.png`（设计侧基准） | 程序缺剪影时显示中性遮罩 | 无独立加载路径 | ✅ 基准在位；程序用中性色不读此文件 |
| region↔关卡对应表 | `UI原型/design_v5/assets/region_level_map.csv` | 策划/工具导入用 | `content_status` 标明 bundled / generated_placeholder | ✅ 在位；导入流程未定 |
| 字体 | `Assets/Resources/Fonts/SourceHanSansCN-Regular.otf` | `Resources.Load("Fonts/SourceHanSansCN-Regular")`，失败回退系统字体 | — | ✅ 文件在位；Unity 导入/中文显示未验证 |
| 17 音效 + 3 BGM | `Assets/Resources/audio/*.wav`（20 个） | `BlockOutSettings.cs:49` `Resources.Load<AudioClip>("audio/" + id)` | 文件名即 id，已逐一对齐 | ✅ 文件在位；播放/循环未验证 |
| 章节图片配置 | `Assets/Resources/ArtOut/ArtOutPictureConfig.json` | `BlockOutCatalog.cs:80` `Resources.Load<TextAsset>("ArtOut/ArtOutPictureConfig")` | 已由 `placeholder_*.png`（不存在）改为 `block/ch01/*`（实际存在） | ✅ 已指向实际文件；未验证 |
| 关卡清单 | `Assets/Resources/ArtOut/GameAssets.json` | `Resources.Load<TextAsset>("ArtOut/GameAssets")` | — | ⚠ 仅 2 关 tutorial，3–12 仍为 `gen_placeholder_*` |

> **要点**：region 遮罩 PNG 是**设计侧交付基准**，程序按 Sprite 矩形在 1080 源画布上固定裁切，不读取这些 PNG。
> 两者的作用是保证「设计稿的 4×3 网格」与「程序的裁切区域」完全一致。

## 布局补充

画布固定390设计宽；360×640等比例设备得到约390×693画布，短屏分支正确命中；高DPI相同比例设备得到相同布局。常规首页预览上限300，短屏预览上限210，章末次级CTA按余高缩小，极矮屏优先保留按钮和导航。收藏采用滚动内容区；两行重复关卡热区固定44，不能通过压缩触控范围来容纳更多章节。

部分收集的大图入口禁用；12/12才开放。双击行为统一为复位，不是阶梯缩放。结算按 `09_component_spec.md` §5.1 铺满安全区（Card Stretch + 揭晓高 `clamp(屏高−330,120,360)` + 收藏/重玩并排 + 返回首页通栏），交付首通/重复/章末（contain + 下一章状态）/短屏（360×640，revealH 落下限 120）四态。

## 本轮检查边界

已做（第十二轮·设计收尾复核）：结算四态几何按程序 `LayoutFullPages` / §5.1 公式重算并断言（390×844 卡 342×786、揭晓区 310×360、内容底 700≤810；360×640 卡 312×600、揭晓区 280×270、内容底 610≤624）；渲染 PNG 像素断言（卡铺满安全区、上下安全区带非卡底色、标题/拼片/注记/金币/奖励文字墨痕、作品区 vs PIL cover 期望 meanabsdiff<12、章末 contain 1:1 meanabsdiff<2 + 信笺边 #FFF7EF、NextBtn 珊瑚/禁用灰两态、次级行同一 y 两枚等宽且几何字符串精确匹配、HomeBtn 通栏）；SVG 文案逐条对应程序 `HandleLevelWon` 四态、无 300×500/查看大图/+N 残留；设置页/收藏页 SVG 源 + 渲染带 + 全文禁用词扫描三层清理；全套 clean_*.svg 渲染文本禁用词扫描；`gen_chapter_end.py` 改为与 `gen_clean_pages.py` 同源同几何（17 三态复算）；`verify_round4.py` 215 项 ALL PASS（复跑确认）；`verify_structure.py` / `verify_regions.py` 回归 PASS。**注意：以上全部是设计稿层面的检查，未触发 Unity，不构成程序运行证据。**

已做（第十轮·设计交付复核）：三档适配图重排为真实设备高度并逐像素验证页面边界/导航位置/CTA 未压缩/组件无重叠；预览容器渲染结果与 PIL center-cover 期望比对（meanabsdiff 6.90–7.06）并排除 none 拉伸与母版压扁参照物；26 张既有裁切图逐像素复验为 center-cover；17 clean 三页徽章/安全区虚线/手势条 0 像素、页外图注在位；首页 12/12 两态主按钮灰/珊瑚像素判定；4 张提取型纯界面（game/collection/store/settings）与结算纯界面全量 XML 校验 + 标注剔除行数断言；`verify_structure.py` / `verify_regions.py` 回归 PASS。**该轮结算图后经第十一轮 §5.1 统一、第十二轮按真实布局重绘，本章末的"1 张按程序结构新绘"以第十二轮四态为准。**

已做（第九轮）：项目脚本（28 个 .cs）剥离注释与字符串后大括号/圆括号/方括号全量配平；**类内裸调用 `Foo(` 逐条验证能解析到本文件可见符号（成员声明、形参、局部变量、`foreach`/`catch` 变量、lambda 形参）——`UNDEFINED-CALL` 0 条**，这一项是本轮新增、也是捕获 `PauseByAppBackground` 编译错误的那一项；私有方法未使用检查 `UNUSED-PRIVATE` 0 条；特性调用与 `new Type(...)` 构造调用已排除误报；事件 `+=`/`-=` 按"宿主对象 + 事件名"配对统计，剩余 8 条未配对项经确认全部为 lambda 订阅（既有写法，生命周期一致，不影响正确性）；控制器对 `UI.* / GM.* / Tools.* / Profile.* / Catalog.* / artProvider.* / BlockOutContentConfig.* / DesignTokens.* / IconFactory.* / Widgets.*` 的引用逐条核对 0 处缺失；UI 工厂返回类型与父节点用法全量扫描（`Card/Panel/SpriteImage/Dim` 返回 `Image`，作父节点必须取 `.rectTransform`）；`Boot.unity` / `EditorBuildSettings.asset` / `BlockOutBootstrapper` 启动链三方一致性核对；字体文件与授权文本存在性核对；音频 20 个 WAV 与 `.meta`（AudioImporter）存在性及 `Resources.Load("audio/"+id)` 路径一致性核对；关卡 JSON 的 ID 与 `gen_placeholder_*` 生成路径核对；玩家可见文案中开发/交付说明文字扫描（0 处残留）；章节图 PNG 逐 chunk CRC 校验（1080×1080，无损）；三个 `.meta` 逐文件断言（顶层键仅 `fileFormatVersion`/`guid`/`TextureImporter`、缩进块内 `spriteMode: 1`、FullRect、`nPOTScale: 0`、GUID 未变）；本轮新增符号 `ConfigUseTimeFailMode` / `runPlayable` / `pausedByAppBackground` / `DoPause` / `PauseByBackground` / `OnAppForegrounded` / `MagicRoutine(int)` 的声明↔调用点一一对应；已删符号（`PauseByAppBackground`、`AfterBlockRemoved`、`Tools.TryUseHint()`）无残留引用。一次性检查脚本用后已删除，不作为项目文件留存。

**没有执行**（第十二轮同第十轮、第九轮）：Unity 刷新、编译、Domain Reload、Play Mode、测试、Console 读取、外部 C# 构建、真机手势与切后台测试、真机多分辨率实跑。因此本轮只能给出"代码已修改"与"静态检查通过"两级结论；**"Unity 编译通过"与"运行验收通过"一律无法声明**。适配图与纯界面图的"验证通过"仅限于设计稿层面（真实设备高度排版成立、等比裁切成立、渲染像素与 SVG 文案/几何符合预期）。

运行验收重点（全部待验证）：**第一步是打开 Unity 确认 Console 无编译错误（这是当前最高优先级，先于一切功能验证）**；然后：三张章节图导入后 `Resources.Load<Sprite>` 是否真的取到图、区域是否仍对齐固定 4×3 坐标；冷启动进首页与商店解锁态；有效旧局恢复与无效存档降级；倒计时归零后退出再进应回到失败层而非可操作状态、复活后才恢复；生命模式存档 + 倒计时开关已打开时，恢复后 HUD 应为心而非计时；暂停与切后台后剩余时间是否落盘；真机切后台再回前台，暂停层是否如期出现、"继续"能否恢复输入；首页/设置页/确认层切后台回来是否保持原页面不被暂停层顶掉；玩家主动暂停的对局回前台不得被自动恢复；失败后退出、暂停后退出各一次后重启，应冷启动进首页而不是恢复到上一局；串行解锁局面（只有 A 可飞→移走后 B 可飞→移走后 C 可飞）下魔法棒应连消 3 块且只扣 1 次库存、无目标时不扣库存；飞出/施法中暂停超过 2 秒再继续；重开/退出/改分辨率后无残留 ResolvingMove 与输入锁；道具未解锁/零库存点击是否出现提示+轻抖且不扣库存；炸弹/彩虹在锤子与魔法路径是否同样触发连锁（需先补 extras 配置）；购买成功才同步库存、保存失败回滚；重玩低关不倒退主线进度；收藏滚动与 44 热区；大图仅 12/12 开放、缩放裁切与切章复位；双指缩放抬起一指后画面是否跳回；360×640 / 390×844 / 390×932 及对应高 DPI 下安全区、按钮、文字、导航不重叠；正式资源导入后的揭晓一致性、字体与声音。
