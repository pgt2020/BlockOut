# BlockOut C 方案 · 全量 Hi-Fi 界面交付包

> 设计方向：**星形糖果可爱风**（C 方案最终版，2026-10-14 用户确认）。此前 ABC、写实沉浸、霓虹玻璃、艺术馆、心形/圆形等方案已归档至 `../_discarded/`，不再维护。

## 目录结构
```
design_v3_final/
├── assets/
│   ├── style.css        # 设计系统 CSS（Design Token + 组件库，与 视觉规范DesignSystem.md 对应）
│   └── scripts.js       # 通用脚本（散景/装饰/HUD/星形棋盘/Banner）
├── screens/             # 26 个界面的 HTML 源文件（375×812，可直接浏览器打开）
├── exports/             # 26 张渲染好的 PNG（Chrome headless 批量截图）
└── batch_screenshot.py  # 批量渲染脚本（改 HTML 后重跑即可刷新全部 PNG）
```

## 界面清单（26 屏）

### 核心闭环（7 屏）
| # | 文件 | 界面 |
|---|---|---|
| 01 | `01-board.html` | 对局棋盘（星形 footprint + 果冻块 + HUD，**不显底图**） |
| 02 | `02-home.html` | 首页（Play + 章节进度 + 图集网格 + 底部导航） |
| 03 | `03-worldmap.html` | 世界画布（章节星座节点导航） |
| 04 | `04-levelselect.html` | 选关（关卡网格 + 锁关 + 星星） |
| 05 | `05-gesture.html` | 交互手势（选中放大 / 被挡红抖 / 手指指示） |
| 06 | `06-settlement.html` | 结算（作品揭示 + 金币/星星奖励 + 双倍领取） |
| 07 | `07-collection.html` | 收藏/图集（章节进度 + 缩略图） |

### 失败与变现（3 屏）
| # | 文件 | 界面 |
|---|---|---|
| 08 | `08-revive.html` | 失败/复活弹窗（看广告 LevelPlay / 金币复活） |
| 09 | `09-store.html` | 商店（金币包/去广告/订阅/礼包） |
| 10 | `10-boosters.html` | 道具获取弹窗（激励视频 / 金币购买） |

### 社交与长线（4 屏）
| # | 文件 | 界面 |
|---|---|---|
| 11 | `11-leaderboard.html` | 排行榜（周/总/好友榜 + 前三 podium） |
| 12 | `12-daily.html` | 每日挑战（种子关 + 连胜 + 奖励） |
| 13 | `13-season.html` | 赛季通行证（免费/付费双轨道） |
| 14 | `14-achievements.html` | 成就列表 |

### 系统与账号（4 屏）
| # | 文件 | 界面 |
|---|---|---|
| 15 | `15-settings.html` | 设置（音效/音乐/震动/语言/云存档） |
| 16 | `16-account.html` | 账号/登录/云同步 |
| 17 | `17-about.html` | 关于/隐私/条款（含 LevelPlay 声明） |
| 18 | `18-support.html` | 客服/反馈 |

### 启动流与通用状态（8 屏）
| # | 文件 | 界面 |
|---|---|---|
| 19 | `19-loading.html` | 加载态 |
| 20 | `20-empty.html` | 空态 |
| 21 | `21-error.html` | 错误态 |
| 22 | `22-coachmark.html` | 新手引导高亮 |
| 23 | `23-splash.html` | 启动页 |
| 24 | `24-onboarding.html` | 首启玩法引导（3 步演示第 1 步） |
| 25 | `25-privacy.html` | 隐私授权弹窗 |
| 26 | `26-subscription.html` | 订阅/礼包弹窗 |

## 设计语言速查
- **背景**：奶油底 `#FFF5EB` → `#FFEFE4` 渐变 + 散景光斑 + 细点纹理 + 漂浮装饰（纸杯蛋糕/蓝莓/星星/爪印/糖果）
- **方块**：草莓红 `#FF6B6B` / 柑橘橙 `#FFB347` / 柠檬黄 `#FFE066` / 薄荷绿 `#7ED9A6` / 葡萄紫 `#9B7ED9` / 蓝莓蓝 `#6B9FFF`，顶部高光 + 底部投影的果冻质感，圆角 12–16
- **棋盘**：星形 footprint（带自然空洞），游玩中不显底图
- **HUD**：顶部胶囊——暂停键、红心+数量、五段彩色星星进度条（红/橙/黄/绿/蓝）、金币
- **按钮**：Primary = 桃→珊瑚渐变 + 底部 3D 投影；Ghost = 奶油底 + 糖果描边
- **状态色**：可飞 = 薄荷绿 glow + 微抬；被挡 = 草莓红 + 抖动；锁定 = 灰棕糖霜

## 给美术的下一步
1. 按本包 + `视觉规范DesignSystem.md` 出正式 Figma 组件库
2. 替换所有 emoji 占位（图集缩略图、装饰物、图标）为正式插画/SVG
3. 输出切图与 SpriteAtlas；章节换皮 Theme Token 见视觉规范 §12

## 给开发的下一步
1. `assets/style.css` 的 Token 直接映射为 UGUI 样式表 / `ThemeSO`
2. 星形 footprint 数据见 `assets/scripts.js` 的 `DEFAULT_STAR`（9×11 网格，0=空洞）
3. 广告位统一走 LevelPlay（Banner/插屏/激励视频）
