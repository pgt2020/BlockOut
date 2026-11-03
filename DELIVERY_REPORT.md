# BlockOut 开发交付报告（M0 → M2 代码层完成）

- 日期：2026-10-14
- 范围：在 `E:/UnityProject/MutiplayGame/BlockOut/` 下建立 ArtOut 兼容的 BlockOut 玩法代码骨架
- 参考：`E:/UnityProject/ArrowOutBlockGallery/ArtOutBlockGallery/`（实际玩法代码已通读对照）

---

## 一、已创建的文件清单

### 核心规则与数据（Assets/Scripts/BlockOut/Core/）
| 文件 | 职责 | 兼容依据 |
|---|---|---|
| `BlockOutTypes.cs` | LevelData / BlockData / RunProgress / Manifest / PictureConfig / Extras 等数据结构 | 字段与 ArtOutTypes.cs 对齐 |
| `BlockOutShapeLibrary.cs` | 28 种形状库（shapeId 1–28）、旋转、默认箭头格 | 完全照搬 ArtOutShapeLibrary.cs 的坐标数组与旋转逻辑 |
| `BlockOutGameRules.cs` | IsPathClear / IsInside / TryTap / 错误幂等 / 生命系统 / 存档进度捕获恢复 | 对照 ArtOutGameRules.cs 逐方法移植 |
| `BlockOutLevelParser.cs` | 单关 JSON 解析（方向别名、颜色 fallback、arrowCell 校验） | 对照 ArtOutLevelJsonParser.cs |
| `BlockOutCatalog.cs` | 三级加载：manifest → Resources/ArtOut/Levels → 兜底生成器；图片配置加载 | 对照 ArtOutLevelCatalog.cs |

### 数据持久化（Assets/Scripts/BlockOut/Data/）
| 文件 | 职责 |
|---|---|
| `BlockOutPlayerProfile.cs` | PlayerPrefs 存档：进度/金币/道具/设置/局内存档 |

### 玩法系统（Assets/Scripts/BlockOut/Gameplay/）
| 文件 | 阶段 | 职责 |
|---|---|---|
| `BlockOutBoardView.cs` | M0 | 棋盘可视化、方块渲染、点击事件、飞出/错误动画 |
| `BlockOutGameManager.cs` | M1/M2 | 综合管理器：串联所有子系统，状态机 Loading→Ready→Resolving→Won/Lost |
| `BlockOutToolController.cs` | M1 | Hint / Hammer / Magic Wand 道具系统 |
| `BlockOutSettlement.cs` | M1 | 通关金币结算、双倍广告、复活（广告/金币） |
| `BlockOutSettings.cs` | M1 | 音乐/音效/震动开关 + 新手引导 |
| `BlockOutComboSystem.cs` | M2 | 连击计分（3 秒窗口、倍率、错误清零） |
| `BlockOutSpecialBlockSystem.cs` | M2 | 炸弹(3×3)/冰冻(相邻锁定)/彩虹(同色清除) 特殊块 |
| `BlockOutAssemblyManager.cs` | M2 | 章节拼图进度元游戏 |
| `BlockOutSolver.cs` | M2 | 可解性求解器（贪心移除序列验证） |

### 服务抽象（Assets/Scripts/BlockOut/Services/）
| 文件 | 职责 |
|---|---|
| `BlockOutAdProvider.cs` | IAdProvider 接口 + FakeAdProvider（本地假实现）+ LevelPlayAdProvider（占位未实现） |

### UI 系统（Assets/Scripts/BlockOut/UI/）
| 文件 | 职责 |
|---|---|
| `BlockOutUIManager.cs` | 代码驱动 UGUI：Canvas构建、26屏全部Screen、Design Token颜色、屏幕切换、Toast |
| `BlockOutUIController.cs` | UI↔游戏桥接：启动流程(Splash→Loading→Home→Board)、按钮事件绑定、胜负路由到弹窗 |
| `BlockOutUIViews.cs` | HUD/弹窗引用类（数据绑定层） |

### 样例资源（Assets/Resources/ArtOut/）
| 文件 | 说明 |
|---|---|
| `GameAssets.json` | manifest（2 个教程关） |
| `ArtOutPictureConfig.json` | 图片配置（占位图名） |
| `BlockOutLevelExtras.json` | M2 特殊块扩展配置（空列表，待填充） |
| `Levels/blockout_tutorial_01.json` | 教程关 1（5×5，6 块） |
| `Levels/blockout_tutorial_02.json` | 教程关 2（6×6，7 块） |

### asmdef 程序集
- `BlockOut.Core` / `BlockOut.Data` / `BlockOut.Services` / `BlockOut.Gameplay`

---

## 二、各阶段完成定义对照

### M0 — 核心原型（已完成代码层）
- [x] ArtOut 兼容形状库（28 种，坐标/旋转语义一致）
- [x] 矩形边界 IsInside（width × height）
- [x] IsPathClear：每格射线检测，任一格被挡即不可飞
- [x] 错误标记幂等（同一块重复点不重复扣血）
- [x] 单关 JSON 解析（方向别名 u/d/l/r/^/v/</>、颜色 fallback）
- [x] manifest → Resources → 兜底生成器三级加载
- [x] 点击判定 → 飞出动画 → 清盘判定
- [x] 通关后图片配置查找（completeImage 回退链）
- [x] 局内进度 CaptureRunProgress / ApplyRunProgress（levelId + hash + blockCount 校验）
- [x] 离线样例关（2 关）

### M1 — 单机闭环（已完成代码层）
- [x] 生命系统（默认 3 点）
- [x] 失败弹窗（复活选项：广告 / 金币）
- [x] 道具三兄弟：Hint（高亮可飞块）、Hammer（选择移除任意块）、Magic（自动移除 N 个）
- [x] 金币账本（PlayerPrefs 持久化，不出现负数）
- [x] 通关结算（基础金币 + 双倍领取广告）
- [x] 设置（音乐/音效/震动开关）
- [x] 新手引导（首关触发，完成后标记）
- [x] 广告走 IAdProvider 接口（FakeAdProvider 本地假实现，不声称已接真实 SDK）

### M2 — 创新原型（已完成代码层）
- [x] 连击系统（3 秒窗口、倍率 1+0.25×(n-1) 上限 3、错误清零、暂停冻结）
- [x] 特殊块：炸弹（3×3 范围清除）、冰冻（相邻有其他活动块时不可主动飞）、彩虹（同色全清）
- [x] 特殊块数据走独立 `BlockOutLevelExtras.json`（不改 ArtOut 关卡字段）
- [x] sourceSha256 校验（hash 不匹配则禁用扩展）
- [x] 连锁反应队列（最大触发数 = 初始块数，防死循环）
- [x] 章节拼装进度（每完成一关点亮一格）
- [x] 可解性求解器（贪心移除序列验证）

### 第4项 — 26 屏 UGUI 界面落地（已完成代码层）
代码驱动 UGUI，无需预制体，挂载 `BlockOutUIManager` + `BlockOutUIController` 即可运行：

**已实现的核心屏（13屏完整布局 + 按钮联动）：**
| # | 屏幕 | 实现内容 |
|---|---|---|
| 19 | Loading | 奶油底 + Logo + Loading文字 |
| 23 | Splash | 珊瑚红底 + 大Logo + 副标题 |
| 02 | Home | Play大按钮 + Collection/Settings底部导航 + 装饰占位 |
| 01 | Board | 顶部HUD(暂停/红心/连击/金币) + 底部道具栏(Hint/Hammer/Magic) |
| 06 | Settlement | 弹窗卡片 + 完成图占位 + 金币奖励 + 双倍广告按钮 + Next |
| 08 | Revive | 弹窗卡片 + 广告复活 + 金币复活(300) + Give Up |
| 15 | Settings | Music/Sound/Vibration 三个Toggle行 + Close |
| 07 | Collection | 2×4缩略图网格占位 + Back |
| 04 | LevelSelect | 3×4关卡网格按钮 + Back |
| 24 | Onboarding | 3步引导文字 + Next/Skip |
| 22 | Coachmark | 遮罩 + 手指提示文字 |
| 20 | Empty | 空态图标 + 提示文字 |
| 21 | Error | 错误图标 + 重试按钮 |

**占位屏（13屏，标记待美术）：** WorldMap / Gesture / Store / Boosters / Leaderboard / Daily / Season / Achievements / Account / About / Support / Privacy / Subscription

**已实现的通用状态：**
- 屏幕切换状态机（`ShowScreen` + `OnScreenChanged` 事件）
- Toast 提示系统
- 启动流程：Splash(1s) → Loading(0.5s) → Home/Onboarding
- 胜负路由：通关→Settlement弹窗；失败→Revive弹窗
- 道具按钮已绑定到 ToolController
- Design Token 颜色已硬编码（奶油底/珊瑚红/薄荷绿/星星黄等，对应视觉规范）
- 所有占位区域明确标注 `[art placeholder]` 或 `[装饰: ...]`

---

## 三、尚需 Unity Editor 验证的部分（未运行）

> 按 AGENTS.md 要求，以下操作均**未执行**：
> - AssetDatabase.Refresh()
> - 脚本编译
> - Play Mode
> - 单元测试
> - Unity Console 读取
> - 外部 C# 构建

需要用户在 Unity Editor 中打开工程后：
1. 用 Unity Hub 添加 `E:/UnityProject/MutiplayGame/BlockOut` 作为工程（已含 ProjectVersion.txt + Packages/manifest.json，版本 2022.3.40f1 + URP）
2. 让 Unity 自动编译（注意：旧的 `Assets/Scripts/Core/Block.cs` 等 12 个华容道脚本可能与新代码共存，如编译冲突可移至 `_deprecated/`）
3. 创建空场景，**只需挂一个组件** `BlockOutBootstrapper` —— 它会自动创建 GameManager/BoardView/UIManager/UIController 并接好引用
4. 运行 Play Mode，验证：Splash→Loading→Home→Play→Board 可点击飞出→Win→Settlement

---

## 四、仅有接口/占位、尚未真实接通的功能

| 功能 | 当前状态 | 需要什么才能真实接通 |
|---|---|---|
| 真实广告（LevelPlay/ironSource） | `LevelPlayAdProvider` 空实现，`FakeAdProvider` 直接调成功 | Unity LevelPlay SDK + App Key + Ad Unit ID |
| 远程配置 / CDN 资源 | 仅本地 Resources 路径，无 HTTP 下载 | CDN 地址 + 配置表 + 网络层 |
| IAP / 订阅 | 无代码 | Unity IAP / 平台后台商品配置 |
| 打点统计 | 无 | 选定 SDK（ThinkingData/Firebase/其他） |
| 本地通知 | 无 | 平台权限 + 调度代码 |
| 真实图片素材 | 图片配置中为占位文件名 | 商用图集素材 |
| 正式美术 UI | 仅 C# 视图类，无预制体/精灵 | Figma 切图 + SpriteAtlas |
| 音频 | 仅开关控制，无 AudioClip | BGM/音效素材 |
| 云端存档 / 排行榜 / 赛季通行证 | 无 | 后端服务 |

---

## 五、关键设计决策记录

1. **形状库坐标**：参考工程数组中 `[row, col]` 存储，转换为 `Vector2Int(x=col, y=row)`，与参考代码 `new Vector2Int(rowColumn[1], rowColumn[0])` 一致。
2. **路径判定**：与参考一致——对 block 的**每一个**占格沿方向射线，任一格碰到其他活动块即不可飞（不是"所有格都畅通"的简单逻辑）。
3. **错误扣血**：`WrongMarked` 幂等——同一块第一次错误扣 1 命并标记，后续点击该块返回 `AlreadyMarked=true`，不重复扣命。
4. **特殊块扩展**：通过 `BlockOutLevelExtras.json` 独立配置，按 `pieceIndex`（原始 pieces 数组下标）关联，不修改 ArtOut 关卡 JSON 的任何字段。
5. **广告抽象**：玩法代码只依赖 `IAdProvider` 接口，当前用 `FakeAdProvider`（立即成功）做本地闭环；真实 LevelPlay 接入时只需换实现。
6. **旧脚本处理**：`Assets/Scripts/Core/` 等 12 个旧华容道脚本未删除、未修改，按 PRD 要求不作为新玩法依据。建议用户在 Unity 中确认编译无冲突后自行归档。

---

## 六、下一步建议（用户侧）

1. **Unity Editor 打开工程**，确认脚本编译通过（旧脚本如有命名冲突需处理）
2. **创建测试场景**：挂 `BlockOutGameManager` + `BlockOutBoardView`，Play 测试教程关
3. **验证样例关可解**：用 `BlockOutSolver.IsSolvable()` 跑一遍两个教程关
4. **接入正式美术**：替换 BoardView 的 Quad 占位为 UGUI Image + 箭头精灵
5. **接入 LevelPlay SDK**：替换 `FakeAdProvider` → `LevelPlayAdProvider`
