# BlockOut v5 当前交付说明（2026-10-16）

当前代码与设计已按第十轮静态复查清单修订，并已完成第十三轮工程化重构（R01–R23 全部条目文件级实现），但**尚未通过 Unity 编译、运行和视觉验收**。不要把"代码已修改"表述为"项目全部完成"，更不要把"静态检查通过"表述为"无编译问题"。

本文把状态拆成四档，**逐档独立判定，任何一档都不能替代下一档**：

| 档位 | 含义 | 本轮状态 |
| --- | --- | --- |
| **代码已修改** | 源码已按要求改到磁盘上 | ✅ 第十三轮 R01–R23 全部条目（15 程序集 / 63 脚本 / 14 资产） |
| **静态检查通过** | 括号配平 + 类内裸调用可解析 + 私有方法未使用 + 事件订阅配对 + asmdef 闭环 + 资产 GUID 完整 | ✅ 本轮通过（`Tools/static_check.py`，但**这不等于能编译**） |
| **Unity 编译通过** | 编辑器 Console 无 error | ❌ **未验证**：按项目要求未触发 Unity 刷新/编译 |
| **运行验收通过** | Play Mode / 真机逐项确认 | ❌ **未验证**：未运行、未测试 |

> 第八轮曾把"静态扫描通过"直接写成"无编译问题"，随后就被发现 `OnApplicationPause` 调用了不存在的方法 `PauseByAppBackground`——**说明静态扫描的覆盖范围此前不足**。第九轮已补上"类内裸调用必须能解析到声明"的检查项，本轮沿用。

完整状态与待办以 [18_implementation_status.md](UI原型/design_v5/18_implementation_status.md) 为准；规则以 [09_component_spec.md](UI原型/design_v5/09_component_spec.md) 为准（**普通关卡结算页结构基准见该文档 §5.1**）；工程化重构逐项交付与验收以 [重构交付与验收.md](Docs/重构交付与验收.md) 为准。

## 第十三轮 · 工程化重构交付（2026-10-16）

需求表 R01–R23 全部条目已文件级实现。给设计/策划侧的关键变化：

- **启动入口唯一化**：`Boot.unity` + `RuntimeInitializeOnLoadMethod` 已删除，改为 `Assets/BlockOut/Scenes/Launcher.unity`（唯一启用场景）显式启动。设计稿里的"启动页"对应 `BlockOutLauncher` 自带轻量启动页（最短展示时长可在 `BlockOutStartupConfig` 配置）。
- **UI 全部页面已迁入 Prefab**：首页/游戏 HUD/收藏/商店/设置/结算/弹层/加载页共 8 个页面 Prefab（`Assets/BlockOut/Resources/Prefabs/UI/`），页面根挂 `BlockOutPageView`（screenId + 锚点），棋盘容器为 `BoardArea` 锚点。**纯界面稿仍是视觉对照基准**（`UI原型/design_v5/` clean_* 系列），Prefab 接入后的像素级验收未执行。
- **普通结算页**：Prefab 骨架已建（`BlockOutSettlementPage`），界面层未接入，终版以 `clean_settlement` 四态 + 09 §5.1 为基准，待设计重绘后接入。
- **存档与远程键契约不变**：`BlockOut_PlayerProfile_v2/v1` 键、关卡 ID/hash、远程键 `use_time_fail_mode`（旧键 `ArtOutUseTimeFailMode` 兼容读取）全部保留，旧档可迁移可回退。
- **广告**：正式聚合为 Unity LevelPlay（ironSource）适配层，非 Fake；缺凭据时开发替身可用、正式发布被门禁拦截。真实广告接通待 SDK 包与凭据。

## 启动与界面

Build Settings 已配置 Assets/Scenes/Boot.unity（工程内唯一场景）。BlockOutBootstrapper 通过 `RuntimeInitializeOnLoadMethod` 在启动时创建相机、音频监听器、EventSystem、GameManager、UGUI与控制器，三方启动链一致。新用户无存档进入首页；有效旧对局才恢复棋盘。旧华容道菜单不用于装配本项目。

## 本轮修订（第十轮）

### 一、【P1】最后一块动画中存档导致重启空棋盘无法结算

这是上一轮已提出但**未真正修复**的问题。本轮从**存档语义**入手重做，不是补一个判断分支。

**修改文件**

- `Core/BlockOutGameRules.cs`（`TryTap`）
- `Gameplay/BlockOutGameManager.cs`（`OnFlyOutComplete`、`LoadLevel`、新增 `pendingWinRestore` / `CompletePendingWin`）
- `UI/BlockOutUIController.cs`（`BootSequence`）

**原问题链**

1. `Rules.TryTap` 成功时**立即** `Remove(block)` → `RemainingBlocks--`；
2. 随后才播飞出动画，动画完成才走通关结算；
3. 切后台时 `Pause → SaveActiveRun` 把"已移除"的状态写进存档；
4. `LoadLevel` 恢复时只在 `Lost` / `Ready` 二选一，没有 `Rules.IsWon` 分支；
5. `BootSequence` 也只处理 `Ready` / `Lost`。

结果：最后一块飞出途中切后台并结束应用，存档已是"全部方块移除"，重启恢复为 **Ready + 空棋盘**，玩家看到空棋盘且永远触发不了结算。

**修复方案：延迟提交（把"移除"变成一个提交点）**

**1）`TryTap` 不再移除方块**（`BlockOutGameRules.cs`）

```csharp
public BlockOutMoveResult TryTap(BlockOutBlockData block, bool consumeLifeOnWrong = true)
{
    if (block == null || !block.Active)
        return new BlockOutMoveResult(false, false, false);

    if (CanMove(block))
        return new BlockOutMoveResult(true, false, false);   // ← 只判定，不移除
    ...
}
```

**2）移除移到动画完成回调**（`OnFlyOutComplete`）

```csharp
if (block.Active) Rules.Remove(block);   // 提交点
Guide.OnPlayerAction();
Settings.PlaySound("sfx_fly_out");
FinalizeRemoval(block, isPlayerAction: true);
```

**这三点合起来才成立**：

- **存档语义明确**：切后台/杀进程只可能落在两种稳定局面——"动画开始前"（该块仍在棋盘上）或"提交完成后"（该块已移除且连锁/胜利判定已跑完）。**不存在"主块已消失但结算未完成"的中间态**。
- **普通块连锁不漏**：`Rules.Remove` → `FinalizeRemoval`（内含 `Specials.ProcessRemovalChain`）→ `SaveActiveRun` 三者在**同一个调用栈内同步完成**，中间没有任何可打断点（`ProcessRemovalChain` 内的连锁 `rules.Remove` 也是同步的）。因此不会出现"保存了主块消失却永久漏掉连锁"。
- **动画途中存档不再丢块**：动画期间该块在规则层仍是 `Active`，存档记录它在场；恢复后玩家看到它还在、还能再点一次。

**3）恢复端补 `Rules.IsWon` 分支**（`LoadLevel`）

延迟提交后新存档不会再命中"空棋盘"，但**上一轮之前已经写进 PlayerPrefs 的旧存档**仍可能是空棋盘，因此显式识别：

```csharp
else if (!restoredLost && Rules.IsWon)
{
    pendingWinRestore = true;
}
```

`pendingWinRestore` 在建局收尾处消费：

```csharp
if (pendingWinRestore)
{
    pendingWinRestore = false;
    CompletePendingWin();   // runPlayable = false; OnLevelWon();
    return;
}
```

**4）`CompletePendingWin` 防重复**

直接复用 `OnLevelWon()`，不另写一套结算：

- `Profile.MarkLevelCompleted` 内部 `CompletedLevelIds.Contains` 去重 → 拼片不重复解锁；
- `Profile.CurrentLevelIndex = Mathf.Max(当前, CurrentLevelIndex + 1)` → 推进幂等，重进不会倒退也不会跳关；
- `Settlement.SettleWin` 只在这一次调用中执行 → 金币不重复发放；
- 结算末尾 `runPlayable = false` + `Profile.ClearActiveRun()` + `Profile.Save()` → 存档失效，下次启动不会再进这条路径；
- `pendingWinRestore` 本身在 `LoadLevel` 开头（`restoreRun` 判定之前）就被重置为 false，新挑战/重开不会继承。

**5）`BootSequence` 同步**（`BlockOutUIController.cs`）

```csharp
if (GM != null && GM.ResumeSavedRunOnBoot
    && (GM.State == BlockOutGameState.Ready
        || GM.State == BlockOutGameState.Lost
        || GM.State == BlockOutGameState.Won))       // ← 新增 Won
{
    UI.ShowScreen(BlockOutScreenId.Board);
    HandleLevelLoaded(GM.CurrentLevel);
    RefreshCoins(GM.Profile.Coins);
    if (GM.State == BlockOutGameState.Lost) HandleLevelLost();
    else if (GM.State == BlockOutGameState.Won) HandleLevelWon();   // ← 新增：避免结算被 GoHome 覆盖
    yield break;
}
```

`UI.ShowScreen(Board)` 内部会 `HideAllBoardLayers()`，所以必须**先切 Board 再开结算层**——现有顺序已经满足。结算完成后玩家走"下一关 / 查看收藏 / 重玩 / 返回首页"，不会看到空棋盘。

**待运行验证**：普通块动画**尚未提交移除**时（飞出约 40% 处）切后台并杀进程 → 重启后该块**仍在棋盘上**、可继续点击（延迟提交后的正确预期，不再是"直接看到结算页"）；恢复**旧的空棋盘存档** → 应走一次结算并把存档失效；补结算后再次重启 → 不得重复发奖/重复解锁拼片/重复推进关卡；炸弹块点击后立刻切后台 → 重启连锁要么完整生效要么完全没发生，不出现"主块没了但邻居还在"。

### 二、【P2】普通结算页：设计与程序不一致，改为单一规格基准

**问题**：`clean_settlement.svg`（300×500 固定居中弹窗 / 260×216 揭晓图 / 查看收藏·重玩·返回首页**纵向**三按钮）与程序 `BuildSettlementLayer` + `LayoutFullPages`（Card **Stretch 铺满 SafeRoot** / 揭晓区高度按剩余空间 `clamp(屏高−330, 120, 360)` / 查看收藏与重玩**左右并排**、返回首页另起一行）是两套结构。此前文档把二者混为一谈。

**处理：统一到程序现行结构，由设计重绘纯界面图**（按要求不各维护一套）：

- **修改文件**：`UI原型/design_v5/09_component_spec.md`。
- 新增 **§5.1「普通关卡结算页结构（唯一基准）」**：写清容器层级（`SettlementLayer → Dim + SafeRoot → Card Stretch`）、9 个元素逐条的宽度/高度/y 坐标，以及"以本节为准，纯界面图需重绘"的裁决规则。
- §5 组件表「关卡结算揭晓框」一行改为指向 §5.1 的安全区完整页描述；§9 定稿状态条目 1 与 §8 跳转表同步标注"结构基准见 §5.1"。
- **明确差异表**：卡片尺寸、揭晓框尺寸、查看收藏/重玩排列、返回首页行宽，逐项列出旧图 vs 现行基准。
- **程序侧不改**：现有实现即作为基准，`clean_settlement.svg/.png` 标记为需按 §5.1 重绘（含 360×640 小屏 revealH 落到下限 120 的表现），重绘后只做核对、不再改结构。

**因此本轮不能写"设计与程序已经一致"** —— 事实是：程序结构已定并作为基准，**设计纯界面图尚未重绘**，这是一项明确的设计侧待办。

### 三、交付状态：仍为未完成（不并入"完整交付"）

- **正式关卡**：`GameAssets.json` 仅登记 `blockout_tutorial_01`、`blockout_tutorial_02`；第 3–12 关仍为 `gen_placeholder_003..012` 生成占位。**第一章正式关卡未齐**。
- **广告**：`Assets/Plugins` 无任何广告 SDK 程序集，`FakeAdProvider` 为模拟实现。**真实广告未接入**。
- **特殊块**：`BlockOutLevelExtras.json` 为 `{"levels": []}`，规则代码已统一但无实际关卡数据，**不属于本期可验收范围**。
- **章节最终美术**：仍为程序化矢量稿（`ART_DRAFT` 标记）。
- 另有经济表数值、第二章排期未定稿。


界面仍使用代码构建UGUI；本轮没有迁移为Prefab，也不声称已交付Prefab资源。Rendering程序集存放BlockOutDesignTokens和BlockOutIconFactory，避免Gameplay与UI互相依赖。

## 本轮修订（第九轮：修复编译阻塞 + 补齐静态检查覆盖）

> 已被第十轮取代，保留备查。其中第六节的 `PauseByAppBackground` 编译错误已在第九轮修复。

### 一、`PauseByAppBackground` 编译阻塞已修复（P1）

- 修改文件：`Assets/Scripts/BlockOut/Gameplay/BlockOutGameManager.cs`（`OnApplicationPause`）。
- 原问题：第 879 行 `if (paused) { PauseByAppBackground(); return; }` 调用的方法名多了 `App`，**类中实际声明的是 `PauseByBackground()`**。C# 找不到该方法即为编译错误（CS0103），整个工程无法通过编译。所有此前"静态扫描通过"的结论都被这一处证伪。
- 现做法：`OnApplicationPause` 改为调用 `PauseByBackground()`，与 `OnApplicationFocus` 走**同一套后台暂停入口**：
  ```
  private void OnApplicationPause(bool paused)
  {
      if (paused) { PauseByBackground(); return; }
      HandleAppForegrounded();
  }

  private void OnApplicationFocus(bool hasFocus)
  {
      if (!hasFocus) { PauseByBackground(); return; }
      HandleAppForegrounded();
  }
  ```
- 暂停职责分层保持不变：`Pause()`（玩家主动，清切后台标记）→ `DoPause()`（实际落盘与锁输入）；`PauseByBackground()`（置标记后调 `DoPause()`）。
- 全库检索确认 `PauseByAppBackground` 已 0 处残留。

### 二、静态检查覆盖范围补齐（本轮工具侧改进）

此前只做括号配平 + 部分跨文件成员核对，**漏掉了本类内部的未定义方法调用**，因此漏掉了上面这条编译错误。第九轮把检查项扩到：

1. 剥离注释与字符串后的 `{}` / `()` / `[]` 配平；
2. **类内裸调用 `Foo(` 必须能解析到本文件可见符号**（成员声明、形参、局部变量、`foreach` 变量、`catch` 变量、lambda 形参），解析不到即报 `UNDEFINED-CALL` —— 这一项直接捕获了 `PauseByAppBackground`；
3. 特性调用（`[Header(...)]`、`[RequireComponent(...)]`、`[RuntimeInitializeOnLoadMethod(...)]`）与 `new Type(...)` 构造调用不再误报；
4. 私有方法"声明了但从未被调用"单独报 `UNUSED-PRIVATE`（本轮 0 条）；
5. 事件 `+=` / `-=` 按"宿主对象 + 事件名"配对统计，具名委托不成对会报出来。

收敛结果：`UNDEFINED-CALL` 0、`UNDEFINED-PRIVATE` 0、括号全部配平。**仍然只有 8 条 `EVENT-UNPAIRED`，全部是 lambda 订阅**（`GM.OnLivesChanged`、`OnCoinsChanged`、`OnRemainingBlocksChanged`、`OnTimeChanged`、`OnBlockWrongMarked`，以及 GM 侧 `Combo.OnComboChanged`、`Tools.OnToolStateChanged`、`Tools.OnHammerModeChanged`）。这些是**已知的既有写法，不是本轮引入**：它们用 lambda 订阅，无法用方法名取消，且订阅方与被订阅方生命周期一致（`Combo` 随 GM 存活，`Tools` 每次 `LoadLevel` 重建因而旧实例连同其订阅一起被丢弃）。本轮不改这些行为，以免牵动已验收的刷新逻辑；如需彻底治理应改为具名 handler，属独立重构项。

### 三、本轮之前 5 项修改的复核结论（按要求不改写、只确认）

以下五项经重新静态核对，声明与调用一致，未做改动：

| # | 项 | 复核点 | 结果 |
| --- | --- | --- | --- |
| 1 | 章节图 Sprite Single 配置 | 三个 `.meta` 块内 `spriteMode: 1`、`spriteMeshType: 1`(FullRect)、`nPOTScale: 0`；顶层键仅 3 个；GUID 未变 | ✅ 静态通过，取图仍待 Unity 验证 |
| 2 | 魔法棒按最新棋盘逐次选目标 | `UseMagic` 只探测目标、`MagicRoutine(int)` 单签名、循环内重调 `PickActionableTargets(1)`；旧 `MagicRoutine(List<>)` 无残留 | ✅ 静态通过，连消 3 块待运行验证 |
| 3 | 新挑战配置与存档失败模式分离 | `ConfigUseTimeFailMode`（第 48 行）/ `UseTimeFailMode`（第 50 行）；第 244 行新局用配置值、第 294 行恢复用存档值 | ✅ 静态通过，HUD 互斥待运行验证 |
| 4 | `runPlayable` 防止放弃后重新保存 | 声明 1 处；赋值 4 处（空关卡 false / 建局 true / 通关 false / 放弃 false）；`SaveActiveRun` 第 359 行首行拦截 | ✅ 静态通过，两条退出路径待运行验证 |
| 5 | `OnAppForegrounded` 事件及 UI 暂停层处理 | GM 声明 1 处、触发 1 处；UI 订阅 1 处（135 行）、处理器 1 处（321 行）、取消订阅 1 处（347 行，在 `OnDestroy` 内） | ✅ 静态通过，真机切后台待验证 |

### 四、交付范围未变（仍为未完成）

- 第一章 3–12 关正式关卡：`GameAssets.json` 仅登记 `blockout_tutorial_01`、`blockout_tutorial_02`，其余为 `gen_placeholder_003..012`。
- 真实广告 SDK：`Assets/Plugins` 无 SDK 程序集，仍 `FakeAdProvider`。
- 特殊块配置：`BlockOutLevelExtras.json` 为 `{"levels": []}`，规则代码已统一但无数据，不属于本期可验收范围。
- 章节最终美术：仍为程序化矢量稿（`ART_DRAFT` 标记）。

## 状态分级说明

阅读本文时请区分四种状态，不要混用：

| 状态 | 含义 |
| --- | --- |
| **文件已交付** | 磁盘上确实存在该文件（代码 / 资源 / 文档） |
| **代码已修改** | 源码已按要求改完，但**未经编译** |
| **静态检查通过** | 本地脚本扫描无告警。**只覆盖语法形态与符号可解析性，不等于能编译，更不等于能运行** |
| **Unity 编译 / 运行已验证** | 必须在编辑器里真实编译、Play Mode、真机确认 —— **本轮全部为空** |

## 尚未完成

- **Unity 编译**：未执行。按项目要求未触发 Unity 刷新、编译、Domain Reload、Console 读取。**当前所有 C# 改动均为"待编译"状态**。
- **正式章节 full/preview/silhouette 最终美术**（当前为设计侧程序化矢量稿，已用 `ART_DRAFT` 标记）。
- **第一章完整人工关卡**（仅 2 份真实 JSON，3–12 为生成占位）。
- **真实广告 SDK 接入**（`Assets/Plugins` 无 SDK 程序集，`FakeAdProvider` 为模拟实现）。
- **特殊块实际关卡配置**（extras 为空，不属于本期可验收范围）。
- **`clean_settlement.svg/.png` 重绘**：普通结算纯界面图仍是 300×500 固定弹窗 + 三按钮纵排的旧结构，需按 `09_component_spec.md` §5.1 重绘（安全区完整页 + 收藏/重玩并排 + 返回首页通栏）。**这是设计侧待办，不是程序待办**。
- 经济表数值与第二章排期未定稿。
- 音频文件已交付（20 个 WAV），播放效果未在 Unity 中验证。

## 验证

- 本轮只做**静态检查**：28 个脚本剥离注释与字符串后括号全部配平；类内裸调用全部可解析到声明（`UNDEFINED-CALL` 0）；私有方法无未使用（`UNUSED-PRIVATE` 0）；事件 `+=`/`-=` 配对统计完成，剩余 8 条均为 lambda 订阅（既有写法，已说明原因）。
- 本轮新增符号定向核对：`pendingWinRestore`（声明 1 / 置位 2 / 消费 1）、`CompletePendingWin`（声明 1 / 调用 1）、`Rules.Remove` 在 GM 内的两个提交点（普通点击 524 行、魔法 683 行）、`TryTap` 唯一调用点（GM 455 行）、`BootSequence` 的 `Won` 分支（UI 112 / 120 行）全部一致。
- 上一轮的三个 `.meta`（顶层键、块内 `spriteMode: 1`、FullRect、不缩放、GUID）本轮未改动，仍有效。
- **未执行**：Unity 刷新、编译、Domain Reload、Play Mode、测试、Console 读取、外部 C# 构建、真机手势与切后台测试。
- **因此本轮只能给出"代码已修改 + 静态检查通过"两级结论，"Unity 编译通过"与"运行验收通过"均无法声明。**
- 未提交、未 push。

## 第八轮修订记录（已被本轮取代，保留备查）

> 以下为第八轮（2026-10-16 上午）的处理内容。其中"静态检查通过"的表述**当时就是过强的**——它没有覆盖类内未定义方法调用，因而漏掉了 `PauseByAppBackground` 这条编译错误。第八轮的五项源码修改本身经复核仍然成立，不需要重写。

### 一、章节图片 Sprite 模式与误追加的外层字段（P1）

- 修改文件：`Assets/Resources/block/ch01/full.png.meta`、`preview.png.meta`、`silhouette.png.meta`。
- 原问题：上一轮只在 `TextureImporter` 块内把 `textureType` 改成 8，但 **`spriteMode` 仍是 0**（0 = None，不是 Single；Single 应为 1）。同时在 `.meta` **文件末尾追加了一整组顶层的 `textureType / spriteMode / spriteMeshType / nPOTScale / alignment / enableMipMap / alphaIsTransparency / alphaUsage / spriteGenerateFallbackPhysicsShape / wrapU / wrapV / aniso / textureCompression`**。这些顶层键不在 `TextureImporter:` 缩进块内，Unity 反序列化时**不会写回导入器设置**，属于无效字段；且 `spriteMode: 0` 出现在两处，反而强化了"配的是 Single"的错觉。`BlockOutChapterArtProvider` 用 `Resources.Load<Sprite>`，`spriteMode = None` 时该调用拿不到精灵。
- 现做法：
  1. 三个文件的 `TextureImporter:` 块内 `spriteMode: 0` → **`spriteMode: 1`（Single）**；
  2. **删除文件末尾那一整组顶层误追加字段**，只保留 `fileFormatVersion` / `guid` / `TextureImporter` 三个顶层键；
  3. 保留稳定 GUID（`638de75ef443a5441ab6fa07247cdfd8` / `68a23a2fce6a436479d4a57ce736d881` / `d3ab21f287a513b42a44cdbc37d6bf09`），未破坏任何已有引用；
  4. 保留 `textureType: 8`（Sprite）、`spriteMeshType: 1`（**FullRect 完整矩形**，保证固定 4×3 区域坐标不被紧密裁切破坏）、`nPOTScale: 0`（1080×1080 不缩放）、`alignment: 0`、`enableMipMap: 0`、`wrapU/V: 0`（Clamp，`textureSettings` 块内）、`textureCompression: 0`（`platformSettings` 块内）。
- 静态核对方式：不只看 `textureType=8`，而是逐文件断言 —— 顶层键仅 3 个、`spriteMode` 在缩进块内且值为 1、FullRect 与不缩放仍在位、GUID 未变。
- **仍属待验证**：`Resources.Load<Sprite>` 的实际取图结果需在 Unity 中确认；`ART_DRAFT` 标记仍在，最终美术未交付（见第七条）。

### 二、切后台回前台的界面恢复流程（P1）

- 修改文件：`Gameplay/BlockOutGameManager.cs`、`UI/BlockOutUIController.cs`。
- 原问题：`OnApplicationPause/OnApplicationFocus` 在失焦时调用 `Pause()`（`IsPaused = true` + 锁棋盘），回前台直接 `return`；`HandlePauseChanged` 只刷新道具状态。结果：玩家切回游戏看到的是正常棋盘但点不动，也看不到"继续"按钮，必须自己再点一次暂停入口才能恢复。
- 现做法：
  - GM 侧新增 `pausedByAppBackground` 标记与 `OnAppForegrounded` 事件。`Pause()`（玩家主动）会**清掉**该标记；新增的 `PauseByBackground()` 只在"由切后台/失焦触发"时置位并调用内部 `DoPause()`。
  - `PauseByBackground()` 会拦掉三种情况：已是暂停态（玩家自己暂停过）、无有效对局（`runPlayable == false`）、已通关；失败局只补一次落盘，不改暂停态（失败层本身就是回前台该看到的界面）。
  - 回前台（`OnApplicationPause(false)` / `OnApplicationFocus(true)`）统一进 `HandleAppForegrounded()`：标记未置位直接返回；置位则清标记、确认仍在暂停中且是有效对局，然后**只发事件，不调用 `Resume()`** —— 必须玩家显式点"继续"。
  - UI 侧 `HandleAppForegrounded()`：仅当当前在 `Board` 页且没有已开着的暂停层/设置层/关于层/确认层/失败层/结算层时，补开 `PauseLayer` 并刷新道具态。首页、商店、收藏等非对局页保持当前页面不动，不会被暂停层顶掉。
  - 玩家主动点暂停的局不满足 `pausedByAppBackground`，回前台不会被无条件自动恢复。
- 待验证：真机切后台/来电/控制中心切换后回前台，暂停层是否如期出现且"继续"可恢复输入。

### 三、魔法棒逐次重新判断目标（P2）

- 修改文件：`Gameplay/BlockOutGameManager.cs`（`UseMagic` / `MagicRoutine` / `PickActionableTargets`）。
- 原问题：`PickActionableTargets` 只在施法开始时遍历一次 `Rules.Blocks`，把当时可飞的块一次性锁成列表；**没有把已选块视为移除，也没有在每次消除及连锁后重新选下一块**。"A 可飞 → A 移走后 B 可飞 → B 移走后 C 可飞"这种局面只能消掉 A 就结束，达不到规定的最多连续移除 3 块。
- 现做法：
  - `UseMagic()` 施法前只做一次"**是否存在目标**"探测（`PickActionableTargets(1).Count == 0` 则**不扣库存**直接返回 0）；扣除库存仍只发生一次；成功后启动 `MagicRoutine(BlockOutContentConfig.MagicTargetCount)`。
  - `MagicRoutine(int maxCount)` 改为循环：每轮都用 `PickActionableTargets(1)` 基于**最新棋盘**重选一个目标 → 飞出动画 → `Rules.Remove` → 计分 → `Specials.ProcessRemovalChain`（炸弹/彩虹连锁）→ 刷新剩余数 → 下一轮重选；直到达到上限、**当前棋盘已无合法目标**、动画被取消、或已胜利。
  - 循环守卫：`myToken != activeRunToken`（重开/切关/退出）立即放弃；`IsPaused` / `State == Lost` / `State == Won` 时停止挑目标；`Rules.IsWon` 时跳出并走胜利结算。
  - 冻结限制保留在 `PickActionableTargets` 内（`Specials.IsBlockedByFrozen` 的块不作为目标）。
  - `PickActionableTargets` 的注释已更正：它**只反映当前棋盘快照**，不再宣称"把已选块视为移除"；逐次重判由协程反复调用实现。
  - 返回值语义改为"本次施法已启动"（1），实际消除数量由协程决定。
- 待验证：需要构造串行解锁局面（例如 3 块依次可飞）才能确认连续消除 3 块生效；单帧只有 1 块可飞时仍只消 1 块。

### 四、失败模式双向恢复（P2）

- 修改文件：`Gameplay/BlockOutGameManager.cs`。
- 原问题：恢复存档处只有 `if (Profile.RunFailMode == 1) UseTimeFailMode = true;`。存档记录为生命模式（`RunFailMode = 0`）时**没有显式恢复为 `false`**，若当前开关已把 `UseTimeFailMode` 打开，旧的/生命模式对局会被按倒计时恢复，与"按存档恢复本局模式"的注释不一致。
- 现做法：
  - 区分两个概念：新增 `ConfigUseTimeFailMode`（**新挑战的配置/远程开关来源**，`LoadLevel` 建新局时应用）；`UseTimeFailMode`（**当前进行中对局实际生效的模式**）。
  - 恢复有效对局时改为**双向**恢复：`UseTimeFailMode = Profile.RunFailMode == 1;`（0 → false，1 → true）。
  - 旧存档兼容不变：`RunFailMode` 缺省为 0，即按生命模式恢复，行为与之前一致。
  - 恢复后 `timeRemaining`、`LastFailReason`、`State` 的判定都读同一个 `UseTimeFailMode`，三者不再互相打架。
- 待验证：需要分别造"生命模式存档 + 开关打开"和"倒计时模式存档"两种存档，确认恢复后的 HUD（心 / 计时）互斥正确。

### 五、已放弃的对局不得被写回存档（P1）

- 修改文件：`Gameplay/BlockOutGameManager.cs`。
- 原调用链问题：失败层退出确认 → `GiveUp()` → `GoHome()` → `Pause()` → `SaveActiveRun()`。`GiveUp()` 清了 `HasActiveRun`，但 `CurrentLevel` 仍保留、失败局通常也没处于 `IsPaused`，于是 `GoHome()` 里的 `GM.Pause()` 会触发新增的保存逻辑，把 `HasActiveRun` **重新写回 true**。下次启动又被当成"恢复旧局"。
- 现做法：引入明确的 `runPlayable` 状态表示"当前是否持有有效进行中对局"，用它统一约束所有落盘入口：
  - `SaveActiveRun()` 首行 `if (!runPlayable || CurrentLevel == null) return;`；
  - `LoadLevel()` 成功建局时置 `true`（空关卡分支置 `false`）；
  - `GiveUp()`（放弃）与 `OnLevelWon()`（通关）置 `false`；
  - `PauseByBackground()` 对 `runPlayable == false` 直接返回，不再暂停也不再落盘。
- 覆盖两条路径：**失败后退出**（`FailQuit` → `GiveUp` → `GoHome` → `Pause`）与**暂停后退出**（`PauseQuit` → `GiveUp` → `GoHome`）。放弃后首页暂停、失焦、切后台都不再保存已放弃的对局。
- 待验证：两条退出路径各退出一次后重启，确认按冷启动进首页而不是恢复到上一局。

### 六、交付范围澄清（不写成已完成）

以下三项**均为未完成**，详见"尚未完成"一节：第一章第 3–12 关正式关卡、真实广告 SDK、特殊块实际关卡配置（`BlockOutLevelExtras.json` 为 `{"levels": []}`，规则代码已统一但无数据，不属于本期可验收范围）。`GameAssets.json` 目前只有 `blockout_tutorial_01`、`blockout_tutorial_02` 两关。

## 状态分级说明

阅读本文时请区分三种状态，不要混用：

| 状态 | 含义 |
| --- | --- |
| **文件已交付** | 磁盘上确实存在该文件（代码 / 资源 / 文档） |
| **代码已实现** | 源码已按要求修改并通过静态检查，**尚未在 Unity 中编译运行** |
| **运行已验证** | 已在 Unity 中编译 / Play Mode / 真机确认通过 —— **本轮为空，全部待验证** |

## 尚未完成

- **正式章节 full/preview/silhouette 最终美术**（当前为设计侧程序化矢量稿，已用 `ART_DRAFT` 标记为非正式素材；构图与 4×3 坐标基准可直接沿用）。
- **第一章完整人工关卡**：`Assets/Resources/ArtOut/GameAssets.json` 目前仅登记 `blockout_tutorial_01`、`blockout_tutorial_02` 两关，`Assets/Resources/ArtOut/Levels/` 只有这两份 JSON，第 3–12 关为 `gen_placeholder_003..012` 生成占位。后续章节排期未定。
- **真实广告 SDK 接入**：`Assets/Plugins` 无任何广告 SDK 程序集，`FakeAdProvider` 为模拟实现（注释已写明禁止进入正式构建），无 App ID / 广告位配置。
- **特殊块实际关卡配置**：`BlockOutLevelExtras.json` 为 `{"levels": []}`，无任何关卡使用炸弹/冻结/彩虹。规则代码已统一（普通点击 / 锤子 / 魔法共用连锁），但因无数据，**不属于本期可验收范围**。补齐时按 `BlockOutLevelExtra`（`levelId` + `sourceSha256` + `pieces[].type` = bomb/frozen/rainbow）填入，hash 不匹配会被忽略。
- 经济表数值与第二章排期未定稿。
- 音频文件已交付（20 个 WAV，见下），但**实际播放效果未在 Unity 中验证**。

### 已交付但待验证的音频

`Assets/Resources/audio/` 下 20 个 WAV 确实存在且 `.meta` 已配置为 `AudioImporter`（44100Hz / `loadType: 0` / 压缩格式 1）；加载代码 `BlockOutSettings.cs:49` 走 `Resources.Load<AudioClip>("audio/" + id)`，路径一致。仍待验证：Unity 导入后能否正常播放、音量与循环点表现、开关是否即时生效。

## 验证

- 本轮只做**静态检查**：28 个项目脚本剥离注释与字符串后大括号/圆括号/方括号全部配平；`ConfigUseTimeFailMode` / `runPlayable` / `pausedByAppBackground` / `OnAppForegrounded` / `MagicRoutine(int)` 的声明与调用点一一对应，`MagicRoutine(List<>)` 旧签名无残留引用；三个 `.meta` 逐文件核对顶层键、缩进块内 `spriteMode: 1`、FullRect、不缩放与 GUID。
- **未执行**：Unity 刷新、编译、Domain Reload、Play Mode、测试、Console 读取、外部 C# 构建、真机手势与切后台测试。**所有"代码已实现"项均为待验证。**
- 未提交、未 push。

## 第七轮修订记录（已被本轮取代，保留备查）

### 一、章节图片导入配置（P1，上一轮部分不成立）

- 上一轮声称已改为 `textureType: 8`、`spriteMode: 0`（Single）、`spriteMeshType: 1`、`nPOTScale: 0` 并"已解决加载问题"。**该结论本轮已推翻**：`spriteMode: 0` 不是 Single（Single 应为 1），且当时还误追加了一组无效的顶层字段。因此上一轮不能算"图片加载问题已解决"，本轮按第一条重新修正。

### 二、设置页与结算页安全区（P1）

- 修改文件：`UI/BlockOutUIManager.cs`（新增 `MakeSafeRoot` / `ApplySafeArea` / `FindDeep`，改 `BuildSettingsLayer`、`BuildSettlementLayer`、`LayoutFullPages`、`ClampCardWidth`）。
- 原问题：卡片高度减去了上下安全区，但仍挂在**全屏父节点**上零偏移居中；上下安全区不对称时整页位置不等于安全区位置。上一轮曾误把居中补偿改成"零偏移必然正确"，注释与结论都是错的，已更正。
- 现做法：为设置页与结算页新增**统一安全区根节点 `SafeRoot`**（Stretch + 按 `Screen.safeArea` 内缩），`Card` 挂在 `SafeRoot` 下并铺满。位置补偿全部交给根节点，卡片内不再做任何二次偏移。`ClampCardWidth` 原用 `transform.Find("Card")`（直接子级），`Card` 下移一层后会取空 → 改为递归 `FindDeep`。

### 三、倒计时存档与失败恢复（P1）

- 修改文件：`Core/BlockOutPlayerProfile.cs`、`Gameplay/BlockOutGameManager.cs`。
- 已加存档字段：`RunFailMode`（0=生命/1=倒计时）、`RunLost`、`RunFailReason`、`RunHasTimeRecord`。
- 恢复逻辑：按 `RunHasTimeRecord` 判定是否恢复时间（**0 秒是有效存档**，恢复后仍是失败态）；`RunLost || Rules.IsLost` 时置 `restoredLost` 并保留失败原因，`State = Lost` 直接进失败层；复活后 `ApplyRevive` 清 `restoredLost`。失败模式的双向恢复在本轮第四条补齐。
- `ClearActiveRun()` 一并清空新增字段，避免残留被误读。

### 四、道具锁定与零库存反馈（P2）

- 修改文件：`UI/BlockOutUIController.cs`（`RefreshToolSlot`、新增 `TryUseTool` / `ToolUnlockLevel`）、`UI/BlockOutUIManager.cs`（新增 `ShakeSlot` / `ShakeRoutine`）。
- 锁定与零库存都保持 `interactable = true`，改由 `TryUseTool` 统一分流：未解锁 → Toast「第 N 关解锁」+ 轻抖；零库存 → Toast「库存不足 · 通关可获取」+ 轻抖，**不跳商店**；暂停 / 非 Ready / 施法忙态 → 直接返回；只有确实可执行但局面无目标时才提示「当前没有可飞出的方块」。

### 五、特殊块与道具规则统一（P2）

- 修改文件：`Gameplay/BlockOutGameManager.cs`、`Gameplay/BlockOutToolController.cs`。
- 普通点击：能飞且未被冻结锁死才可点；锤子：**可消任意在场块，包含冻结块与被冻结块**；魔法棒与提示：只选"玩家实际可操作"的块。
- 统一收尾：`FinalizeRemoval(primary, isPlayerAction)` 集中处理"连锁 → 剩余数 → 胜利判定 → 存档 → 状态复位"；旧的 `AfterBlockRemoved` 已删除，无残留调用。
- 提示扣减拆分为 `ToolController.ConsumeHint()`，避免目标检查与扣减分离导致漏扣。

### 六、大图手势衔接（P2）

- 修改文件：`UI/BlockOutPinchZoom.cs`。
- 新增 `awaitAllRelease` 锁——双指结束时若仍有手指未抬起则置位，期间 `OnBeginDrag` 不建立拖动基准、`OnDrag` 直接返回、`OnPointerDown` 不重置手势；**所有手指抬起后（`touchCount == 0`）自动解锁**。保留 1–3 倍缩放、拖动限位、双击复位、切章复位。

### 七、章节图资源标记

新增 `Assets/Resources/block/ch01/ART_DRAFT.txt` 标记文件。三张图是设计侧程序化矢量稿（构图基准，非最终美术），命中标记时 `Status = Placeholder`、`IsDraftArtwork = true`，不计入正式素材。美术交付最终图后删除该文件即自动转为 `Loaded`。
