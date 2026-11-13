# BlockOut UI Design System v6 · 唯一真源

> 版本：2026-11-09 · 状态：**唯一有效视觉规范**
> 本文件取代此前全部 UI 规范、Brief、design_v3/v5 组件规格与出图说明。旧稿与旧规范已整体删除，
> 仅 `DesignAssets/ChapterMasks/` 保留美术源母版。`V5_ROUND_交付说明.md`、`DELIVERY_REPORT.md`
> 等属历史交付记录，**不作为设计依据**；`产品方案PRD.md`、`技术架构方案.md` 属产品/工程约束，不是视觉规范。
> 冲突时以本文件为准。

---

## 0. 设计定位（与前版的根本差异）

玩法是**箭头方块消除 = 空间路径推理 + 试错扣心**，长线驱动是**图集收集**。
前版把"可爱柔和"当第一目标，导致方向箭头、块边界、状态差异全部被低对比吃掉。v6 改为：

1. **信息优先于情绪**：箭头方向、块边界、可飞/被挡是最高视觉优先级，任何装饰不得与之竞争。
2. **真·干净扁平**：取消果冻假 3D（硬投影垫色、顶部 40% 白高光、纯渐变冒充材质）。统一 2px 描边 + 轻柔阴影 + 克制单层高光。不做软体黏土，也不做扁平假装立体。
3. **语义色专色专用**：红色只表示"危险/损失"，绝不用于主行动按钮。
4. **单关奖励可见**：1/12 揭晓必须被玩家看见，不能只靠数字变化。

生成链（改设计必须同步三处，缺一即回退）：
`Docs/DesignSystem.md`（本文件）→ `Runtime/Rendering/Tokens/BlockOutDesignTokens.cs`（Token）
→ `Runtime/UI/Views/BlockOutUIManager.Authoring.cs` + `Runtime/UI/Components/BlockOutWidgets.cs`（编辑器烘焙配方）
→ `Resources/Prefabs/UI/*.prefab`（烘焙产物，运行时由 `BlockOutUIPrefabRegistry` 加载）。

---

## 1. 色彩 Token

### 1.1 背景与表面
| Token | HEX | 用途 |
| --- | --- | --- |
| `bg.cream` | `#FFF8F0` | 页面主背景 |
| `bg.creamDeep` | `#FCEBD8` | 背景渐变底部 / 棋盘外区 |
| `surface.card` | `#FFFFFF` | 卡片、弹窗、工具条 |
| `surface.raised` | `#FFFDF8` | 浮层、次级面板 |
| `stroke.warm` | `#E7D2BE` | 卡片描边 2px |
| `stroke.grid` | `#DCC3AC` | 棋盘虚线格 |
| `stroke.board` | `#D9BFA6` | 棋盘外框 3px |

### 1.2 文字
| Token | HEX | 对比（对 `#FFF8F0`） | 用途 |
| --- | --- | --- | --- |
| `text.cocoa` | `#3B2A24` | 13.6:1 | 主文字、图标、暗底反白 |
| `text.secondary` | `#6E5449` | 6.6:1 | 次要文字、副题 |
| `text.disabled` | `#8A7568` | 4.6:1 | 禁用/锁定文字（**不得再降到 2.2:1**） |
| `text.onDark` | `#FFFFFF` | — | 深底文字 |

### 1.3 语义色（v6 核心修订）
| Token | HEX | 语义 | 允许用途 |
| --- | --- | --- | --- |
| `action.primary` | `#4A2F26` | **唯一主行动**（巧克力棕） | 主 CTA、导航激活、进度填充、开关开态 |
| `action.hover` | `#5C3B30` | 按下态 | 主 CTA 按下 |
| `state.go` | `#1E8F68` | 可飞 / 成功 / 已解锁 | 可飞块描边、勾、成功提示 |
| `state.goFlash` | `#2FB98A` | 提示闪烁（比 go 亮一档） | 提示态高亮，仅动效瞬时用 |
| `state.goBg` | `#DFF6EC` | 薄荷底 | 剩余块胶囊 |
| `state.goText` | `#14664A` | 薄荷上文字 | 状态文案 |
| `state.bad` | `#C62F45` | **危险 / 损失**（深莓红） | 受阻红描边、错误、失败、生命心 |
| `state.badBg` | `#FCE8EA` | 错误底 | 失败层浅底 |
| `state.lock` | `#8A7568` | 锁定 | 锁徽、置灰文字 |
| `state.lockIcon` | `#A08B7B` | 锁定图标灰 | 禁用态图标（非文字） |
| `reward.gold` | `#E8A20C` | 奖励 | 金币、奖励数字 |
| `reward.goldRim` | `#B87C05` | NEW 金边 | 本关揭晓区金边 |
| `reward.goldLight` | `#FFF0C2` | 金币亮部 | 金币内环 |
| `reward.goldText` | `#6B4700` | 金币文字 | 免费徽标 |
| `mask.dim` | `#3B2A24` @ 40% | 遮罩 | 弹层背板 |

> **兼容别名**：`BlockOutDesignTokens.cs` 中 `CtaCoral*` 三个字段是历史命名，值已全部指向
> `action.primary` / `action.hover`，**不代表珊瑚色**。新代码请直接用 `ActionPrimary` / `ActionHover`。

> **撞色禁令**：前版 `cta/coral #FF7568` 与 `berry/red #F45F70` 几乎同色，导致"继续"与"失败"共用红色信号。
> v6 规定：**红色不出现在任何主按钮、进度填充、导航激活态**；`action.primary` 与 `state.bad` 色相距离 ≥ 30°。

### 1.4 方块色（6 组，降明度以拉开奶油底）
顶→底竖向渐变，仅一层渐变、不加高光条、不加底部投影垫色：

| # | 色名 | 顶 | 底 |
| --- | --- | --- | --- |
| A | 橙 | `#F6B36A` | `#E08A3C` |
| B | 薄荷 | `#67C9A2` | `#2E9E75` |
| C | 紫 | `#A992E0` | `#7C63C4` |
| D | 粉 | `#F39BB4` | `#DC6A8C` |
| E | 黄 | `#F2CE63` | `#D9A622` |
| F | 蓝 | `#8FB8EE` | `#4A82CF` |

- **块边界**：1.5px `#3B2A24` @ 55% 外描边（替代前版 3px 纯白轮廓），是唯一块边界。
- **块内格线**：1px 白 @ 18%，两端内缩 6px（读作块内纹理，不读作块间分隔）。
- **箭头**：`#3B2A24` 填充 + 1.5px `#FFFFFF` 描边（paint-order: stroke fill），24×24 视框，最小渲染 20px。
  深色块（B/C/F）靠白描边保证形状，浅色块（A/E）靠深填充保证对比——两端都可读。
- **投影**：`0 4px 8px rgba(59,42,36,.12)`，全局统一光源方向，禁用硬偏移垫色。

> **⚠️ 运行时色链路（实现必读，2026-11-09 核查）**：对局棋盘 / 方块 / 箭头**不在任何 UI Prefab 里**，
> 而是 `BlockOutBoardView` 运行时实例化的 `BlockOutBlockNode`；方块色来自 608 个关卡 JSON 的
> `color` 字段（缺省回退 `BlockOutLevelParser.FallbackPalette`，均为 `#FFED00` / `#02B1FF` / `#36F5E7`
> 一类高饱和原色，与本色板脱节）。本节 6 组色当前只作用于首页玩具块预览。
> **禁止批量改关卡 JSON**（违反 ArtOut 数据字节级兼容约束）；正确做法是在表现层做色相重映射：
> `BlockOutBlockNode.LateUpdate` 写 `body.color` 前把 `TargetBlock.Color` 映射到本节色板，
> 箭头固定用 `ArrowFill` + 白描边材质，不再跟随块色。
> `BlockOutSolver.ComputeLevelHash` 只含 id / 宽高 / 块位 / 方向，**不含颜色**，故表现层重映射不影响存档兼容。
> 该项属 Unity 侧接线，列入 §8.1 待办。

### 1.5 状态表现（形状 + 颜色双通道，不靠颜色单独表达）
| 状态 | 颜色 | 形状/动效 |
| --- | --- | --- |
| 可飞（默认预判） | `state.go` 1.5px 描边 | 右上角小勾；设置可关闭，新手前 3 关默认开 |
| 受阻 / 错误 | `state.bad` 2px 描边 | 叉形角标 + 280ms 位移抖动 3 次 + Toast |
| 锁定 | `state.lock` | 锁徽 + 条件文字（"第 7 关解锁"） |
| 连击 | `reward.gold` | 数字弹跳 + 光晕 |
| 失败 / 生命耗尽 | `state.bad` | 心形空心 + 数字，不依赖色相 |

---

## 2. 字体

字体：`Source Han Sans CN Regular`（SIL OFL 1.1，随包），粗体由 UGUI `FontStyle.Bold` 合成。
**硬性下限：任何玩家可见文字 ≥ 11px；关键操作文字 ≥ 12px。** 前版 8/9/10px 全部淘汰。

| 层级 | 字号 / 字重 | 用途 |
| --- | --- | --- |
| HUD 关卡名 | 20 / 700 | 对局顶部主标题 |
| HUD 副题 | 12 / 400 | 章节主题名 |
| 剩余块 / 金币 | 13 / 700 | 胶囊数值 |
| CTA 主文案 | 18 / 800 | 唯一主按钮 |
| CTA 副文案 | 12 / 500 | 按钮副信息 |
| 卡片标题 | 13 / 700 | 进度卡、章节卡 |
| 卡片副文案 | 11 / 400 | 说明文字 |
| 工具名 / 导航 / 弹窗正文 / Toast | 12 / 500 | 通用 |
| 解锁条件 / 节点计数 | 11 / 400 | 最小号 |

- 数字使用 tabular-nums 对齐（计时、金币、剩余块）。
- 中英混排按 CJK 1.0em + 西文 0.55em 估算行宽；L10n 时 Body +2pt 不破版。

---

## 3. 间距、圆角、描边、阴影

- 8pt 栅格：`4 / 8 / 12 / 16 / 24 / 32 / 48`；屏边距 24（对局棋盘左右 18 为唯一例外）。
- 圆角：`sm 8` `md 12` `lg 16` `xl 24` `pill 999`。
- 描边统一 2px `stroke.warm`；按钮 1.5px；棋盘 3px。
- 阴影仅两级：`shadow.card = 0 4px 12px rgba(59,42,36,.10)`；`shadow.float = 0 8px 20px rgba(59,42,36,.14)`。
  对局屏不使用 `shadow.float`。**禁止 `0 7px 0 #xxx` 这类硬投影垫色。**
- 触控目标 ≥ 44×44；图标按钮 44，工具槽 56。

---

## 4. 组件库

| 组件 | 规格 | 状态 |
| --- | --- | --- |
| PrimaryButton | 342×88（360 档 312×88），圆角 24，`action.primary` 实底 + 白字 18/800；左侧 44×44 白色图标块；按下 `action.hover` + 0.98 缩放 | 默认 / 按下 / 禁用(`state.lock` 底) / 加载 |
| SecondaryButton | 232×44，圆角 20，白底 + `text.cocoa` 2px 描边 + 12/700 文字 | 同上 |
| IconButton | 44×44 圆，`surface.card` + `stroke.warm` 2px | 默认 / 按下 |
| Card | 白底圆角 24，`stroke.warm` 2px，`shadow.card`，内边距 16 | 默认 / 选中(`state.go` 2px 描边) |
| Pill | 高 30，圆角 pill，白底 + `stroke.warm` 1.5px | 金币 / 剩余块 / 计时 |
| ProgressBar | 高 10，`bg.creamDeep` 底，`action.primary` 填充 | 0% / 部分 / 满 |
| PieceNodes | 12 个 12px 圆，已解锁 `state.go` + 勾，未解锁空心 `stroke.board` | 逐格点亮 |
| Toolbar | 有可用道具时 104（三槽 56 圆钮）；**三道具全锁时压缩为 72**，三槽缩为 44 并保留锁徽 + "第 N 关解锁" 11px 条件文字。锁定态是有效的能力预告，不隐藏；要去掉的是 104 里的空白，不是道具本身 | 展开 / 压缩 |
| Toast | 深可可 88% 圆角 16，12/500 白字，底部 80 上浮 | 进 200 / 出 200 |
| Modal | 遮罩 `mask.dim`，卡片圆角 24 | 上滑 200 + 淡入 |
| BottomNav | 342×64（360 档 56），3 项，激活 `action.primary` | 激活 / 未激活 |

**状态色使用规则**：可交互元素的"激活"一律 `action.primary`；"成功/可飞"一律 `state.go`；
"失败/危险"一律 `state.bad`；"奖励"一律 `reward.gold`。四者不得互换。

---

## 5. 页面布局规格（390×844 基准，360 档等比）

### 5.1 首页 Home
- 顶部 24/30：logo 色块 44×44（`state.go` 底 + 白箭头）+ 标题 16/800 + 副题 11/400；右金币胶囊 + 设置圆钮。
- 预览卡 342×300 @ (24,148)：12 区揭晓图，**未解锁区用 `silhouette #DCC7B0` + 白雾 25%**；
  已解锁区必须用**完整饱和度**显示（前版整图薄雾导致 0/12 时看不出收集目标）。
  右上"拼片 N/12"胶囊，`action.primary` 底白字。
- 前景 2 个带箭头玩具块 + 点击涟漪 + 飞出轨迹，箭头同 §1.4 规格。
- 唯一主 CTA 342×88，紧贴预览卡下方，文案"继续第 N 关"。
- 进度卡 342×120：章节名 13/700 + 进度条 + 12 节点 + "还差 N 片"11/400。
- 底部导航 342×64 @ bottom 28。
- **禁止**在首页同时出现第三套进度表达。

### 5.2 对局 Board
- HUD 顶部：左 44 暂停钮；中 20/700 关卡名 + 12/400 副题；右 3 心（`state.bad` 空心心 + 数字）。
- 第二行右："剩余 N 块"薄荷胶囊（`state.goBg` 底 + `state.goText` 字）。
- 棋盘：左右 18，外框 3px `stroke.board`；6×6 虚线格 `stroke.grid`；
  **块足迹为非矩形多边形且带空洞，不得假设铺满**（玩法硬约束）。
- 可飞块默认显示 `state.go` 1.5px 描边 + 小勾（见 §1.5）；被点击且受阻才转 `state.bad`。
- 提示 pill：12/500，"轻点整块方块，沿箭头方向飞出"，位于棋盘下方 16。
- 工具条：全锁时压缩为 72（三槽 44 + 锁徽 + "第 N 关解锁" 条件文字），有可用道具时 104（三槽 56）。见 §4。
- 棋盘下沿与工具条之间留白 ≤ 24（前版约 100px 空档）。

### 5.3 结算 Settlement
- Card 铺满 SafeRoot，但**内容按空间分布**：标题区贴顶、揭晓区弹性伸展、按钮组贴底 24。
  禁止内容全挤在上 2/3 留底部大空白。
- 标题 17/800"新拼片解锁" + `state.goText` 12/700"拼片 N/12"。
- 揭晓区宽 = 屏宽−32，高 `clamp(屏高−330, 160, 360)`；
  **本关新揭晓的那一区必须加 `reward.gold` 2px 描边 + "NEW" 角标 + 局部放大动画 400ms**，
  让 1/12 的变化可见（前版只靠整图去雾，肉眼无感）。
- 奖励行：金币图形 + "首次通关 · 获得 40 金币" 12/700 `reward.goldText`。
- **章节拼片进度卡**（v6 新增）：进度条 + 12 节点 + "N / 12"，放在奖励行与按钮组之间。
  作用是把前版结算页中部的空白变成有效信息，同时强化长线收集钩子。
- 按钮组（3 个，不再 4 个）：主 CTA 通栏"下一关"；次级一行两枚"查看收藏 / 重玩本关"；
  "返回首页"改为顶部右上关闭 X（44×44）。
- 章末态：作品 contain 1:1 + 信笺边；下一章未发布时主 CTA 禁用并显示"新章节准备中"。

### 5.4 收藏 Collection
- 顶部：返回 44 + "收藏" 17/800 + 金币胶囊。
- 章节摘要卡：缩略图 + 章节名 + **一条**进度条 + "还差 N 片"（唯一进度表达）。
- 章节列表：当前章 `state.go` 2px 选中描边；未解锁 `state.lock` + 锁徽。
- 重复挑战网格：12 格（已通关勾 / 当前关 `state.bad` 数字 / 未解锁锁）。
- 底部导航。**去掉章节卡里重复的 "N/12" 文字**（前版同屏三套进度）。

### 5.5 设置 / 商店 / 弹层
沿用现有信息架构，统一替换 Token：开关开态 `action.primary`、商品主按钮 `action.primary`、
禁用态 `text.disabled` ≥ 4.6:1、遮罩 `mask.dim` 40%。弹层按钮不再使用红色主按钮。

---

## 6. 动效

| 动效 | 时长 | 缓动 |
| --- | --- | --- |
| 页面转场 | 240ms | ease-out |
| 方块飞出 | 360ms | cubic-bezier(.2,.8,.2,1) 加速 + 拖尾 |
| 错误抖动 | 280ms | ±6px 衰减 3 次 |
| 拼片揭晓（v6 新增） | 400ms | 放大 1.08 → 1 + 金边淡出 |
| 弹窗出现 | 200ms | 上滑 24 + 淡入 |
| Toast | 200 / 200ms | ease-out |

尊重系统"减少动态效果"：关闭后仅保留状态切换，去位移/缩放。

---

## 7. 无障碍（WCAG AA 基线）

- 正文文字对比 ≥ 4.5:1，大字/图标 ≥ 3:1；暗底文字 `#FFFFFF` 对 `action.primary` = 12.4:1。
- 所有状态颜色必须配形状或文字（勾 / 叉 / 锁 / NEW 角标），不得只靠色相。
- 玩家可见文字 ≥ 11px；关键操作 ≥ 12px；触控 ≥ 44×44。
- 焦点环 2px `state.go` + 2px offset；屏幕阅读器可读关卡号、生命、金币、道具数量。
- 色盲：可飞用勾形 + 描边，被挡用叉形 + 抖动，红绿色弱下仍可区分。

---

## 8. 验收清单（交付前逐项）

- [ ] `BlockOutDesignTokens.cs` 与本文件 §1/§2 全部数值一致。
- [ ] `BlockOutUIManager.Authoring.cs` / `BlockOutWidgets.cs` 无残留旧色值、无 <11px 字号。
- [ ] 13 个 `Resources/Prefabs/UI/*.prefab` 的 `m_Color` / `m_FontSize` 已按本文件刷新。
- [ ] 代码与注释中不再出现 `09_component_spec.md` / `design_v5` / 旧 DesignSystem 引用。
- [ ] **Unity 侧**：编辑器编译、Prefab 重新烘焙、Play Mode 逐屏像素级核对、360×640 / 390×844 / 390×932 三档实跑。
  （本文件由静态改造产出，上述 Unity 验证**未执行**，由项目负责人在本机完成。）

### 8.1 实现分层（2026-11-09 静态改造，勿把"设计已定"当成"已运行"）

| 层 | 本次已落地 | 需 Unity 重新烘焙 / 接线后才生效 |
| --- | --- | --- |
| 色彩与字号 | `BlockOutDesignTokens.cs` 全量 v6 值；13 个 Prefab 的 `m_Color` 批量刷新（174 处）；生成源 `Widgets.cs` / `Authoring.cs` / Controllers 硬编码收敛。Prefab `m_FontSize` 原值最小已为 11，**本轮未改动** | — |
| 语义色分工 | 生成源里主 CTA、导航、进度填充、开关全部改 `action.primary`；已解锁节点改 `state.go`；错误/生命保留 `state.bad` | Prefab 里由 `Sprite` 自身带色的元素（见 §8.2 P2）不受 `m_Color` 影响 |
| 布局 | 工具条全锁态由 104 压到 72（`LayoutMetrics.ToolbarHeightCompact` + Authoring）；结算 `revealH` 下限 120→160、按钮组贴底 | 解锁任意道具后由 `HudController` 把工具条切回 104 |
| 棋盘 / 方块 / 箭头 | 颜色表、箭头规格、描边规格已在 §1.4 定义；`ArrowFill` / `StrokeBlock` Token 已就位 | **表现层色相重映射**（见 §1.4 警示）、默认可飞块 `state.go` 描边 + 勾角标 |
| 结算页结构 | 揭晓区正方形 contain、按钮组贴底、本关揭晓区金边 NEW 的规格 | 实际新增"章节拼片进度卡"节点 + 3 按钮改版 + 顶部关闭 X（当前 Prefab 仍为 4 按钮，已在生成源按贴底排布） |
| 状态反馈 | 状态色 / 形状 / 动效规格 | 默认态可飞预判需 `BlockOutBlockNode` 接线；设置项开关、无障碍焦点环 |

### 8.2 静态核查结论与遗留问题（2026-11-09）

复现命令（只读）：`python -X utf8 Tools/Design/verify_v6_prefabs.py`

**通过项**
- 13 个 Prefab 的 268 个 `m_Color` 全部落在 §1 色板内，非调色板残留 **0**；174 处由
  `Tools/Design/apply_v6_to_prefabs.py` 改写，改前/改后每个文件行数与组件数完全一致。
- 按组件类型统计：`Text` 73 处可可色 / 19 处白字 / 2 处主行动色；`Image` 全部为白、奶油、
  描边米、主行动棕、状态绿、黑遮罩。**没有出现"浅色文字被改成浅底色"的语义错配**。
- 94 个 `Text` 的 `m_FontSize` 最小 11、最大 40，`m_BestFit` 全开；生成源里唯一一处 9px
  （收藏页关卡号 `Num`）已提升到 11。
- 全工程 `*.cs` 中 `design_v5` / `09_component_spec` / 旧规范名引用残留 **0**。
- `BlockOutDesignTokens` 的 54 个字段与全部调用点对应，无"使用未定义"符号；10 个改动过的 `.cs` 大括号平衡。
- **核查中额外发现并修复 5 处运行时白底白字**：`HomeController.SetCta` /
  `DialogsController.SetReviveButton` / `StoreController` 购买按钮 /
  `CollectionController` 查看大图按钮，四处都在 `Refresh` 里把 `targetGraphic.color`
  覆写成 `Color.white`，会覆盖生成源里的 `ActionPrimary` 深底；另 `MakeCoralMiniButton`
  缺 `img.color` 赋值（中性遮罩默认白）。均已改为 `ActionPrimary` / `GrayIconLocked`。
  这是静态色表核查查不出的"运行时二次覆写"，属于本轮最有价值的修复。

**遗留问题（按优先级）**

| # | 级别 | 问题 | 影响 / 处理 |
| --- | --- | --- | --- |
| P1 | 阻断验收 | **本轮全部是静态改造，未进 Unity**。未编译、未 Domain Reload、未重新烘焙 Prefab、未 Play Mode、未真机逐屏核对 | 需在本机 Unity 打开工程，跑一遍编译 + 重新烘焙 + 三档分辨率实跑；§8 的勾选框在此之前不能打勾 |
| P2 | 高 | **Prefab 是旧配方烘焙产物，与当前生成源不同步**：`HomeCtaButton` 的 `Image.color` 在 Prefab 里仍是白色、`m_Transition: 1`（ColorTint），而 `BlockOutWidgets.CoralButton()` 已写 `img.color = ActionPrimary` 且 `transition = None` | `m_Color` 批量改色只改了"由 Image.color 着色"的元素；按钮外观还受 `m_Sprite` 影响，重新烘焙前不能认为主 CTA 已经是 v6 巧克力棕 |
| P3 | 高 | 13 个 Prefab 仍引用 **12 处旧参考切图**（`Reference/RawImage/`）：`content_card.png` ×3、`tool_hammer.png` ×3、`btn_setting.png` ×2、`img-main-green.png` / `btn_blue_square.png` / `logo.png` / `btn_continue.png` 各 1 | 这些是带自身颜色的位图，不受 `m_Color` 控制，与 v6 干净扁平色板会撞。需在 Unity 内换成 `AuthoredSprites/round.png` 中性遮罩 + `Image.color` 着色，或重出正式切图 |
| P4 | 中 | **白底白字疑点 3 处**：`HomeCtaButton` 的 Title/Sub、`SettleNextBtn` 的 Title，Text 为 `#FFFFFF` 而其同节点 Image 的 `m_Color` 也是 `#FFFFFF`（静态对比度 1.0） | 实际显示色由 `m_Sprite` 决定（HomeCtaButton 指向 `img-main-green.png` 绿图），静态对比度不能直接判定不可读；但必须在 Play Mode 亲眼确认，属于 P2/P3 的连带验收项 |
| P5 | 中 | 结算页结构仍是旧版：Prefab 里 4 按钮、无"章节拼片进度卡"、无顶部关闭 X | 生成源 `BuildSettlementLayer()` 只做了贴底排布，结构改动必须在 Unity 内加节点；见 §8.1 |
| P6 | 中 | 对局方块色仍来自 608 个关卡 JSON 的高饱和 `color` 字段 / `FallbackPalette`，未做表现层色相重映射；箭头仍跟随块色 | 见 §1.4 警示，需在 `BlockOutBlockNode.LateUpdate` 接线；不改 JSON（数据字节级兼容） |
| P7 | 低 | `JellyTop` / `JellyBottom` 字段名沿用旧"果冻"命名，但值已是 §1.4 的降明度 6 组色 | 仅命名包袱，可择机重命名，不影响视觉 |
| P8 | 低 | `CtaCoral*` 兼容别名、`ToolbarHeightFor()` 等新接口尚未被运行时代理调用 | 无编译风险；接入 HUD 工具条状态切换时一并启用 |
