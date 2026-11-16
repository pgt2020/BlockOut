# BlockOut · 花园奶油风 UI 套件 v2（首页）

> 参考图：`source_reference.jpg`（941×1672，微信截图原图）
> 目标档位：1080×1920，缩放系数 **1.1477**
> 状态：**设计稿 + 切图 + 组件，未接入 Unity、未编译、未真机验证**（按项目约定，验证由你执行）

---

## 先看这三张

| 文件 | 看什么 |
| --- | --- |
| `preview/reference_vs_rebuilt.png` | 左原图 / 右还原图，一眼看差距与还原度 |
| `preview/rebuilt_home_1080x1920.png` | 可直接在全屏尺寸看效果 |
| `preview/contact_sheet.png` | 全部资产对照：A 切图 / B 组件 |

另：`preview/node_states.png` 是关卡节点六种状态 + 换数字的演示。

---

## 一句话结论

**风格可以整套替换，但要分两类件走：**

- **静态件（不会变文案的）** → 从这张截图 1:1 切，够用，我来切；
- **动态件（关卡号、货币、文案会变的）** → **不能靠切图**。原图上的“40/39/37/第37关/3”是烘焙在像素里的，从单张截图去字 4 种算法都试过（几何遮罩、GrabCut、中值滤波、渐变补洞），
  都会留下补丁或把 3D 渐变抹平，达不到可交付质量。所以动态件改成**同风格程序化组件**（`components/`），文案任意换、可出 2x、可九宫格。

这套 UI 的价值不在“切图”，而在于**把这套美术语言抽象成一套可换文案的组件**。这一轮已经把组件库跑通了。

---

## 目录

```
UI_garden_kit_v2/
├─ source_reference.jpg     参考原图
├─ background/              花园底图（占位，见“已知限制”）
├─ ui/                      从原图切出的 18 个静态件（1x，含烘焙文字）
├─ components/              同风格组件 19 个（2x，无文字，九宫格参数在 json 里）
├─ preview/                 对照图 / 还原图 / 节点状态图 / 资产表
├─ tools/                   全部可复现脚本
├─ manifest.json            切图裁切框 + 组件九宫格参数
└─ README.md
```

### A. `ui/` 切自原图（1x，静态）

`btn_settings` `pill_currency` `btn_task` `btn_achievement` `nav_bar` `tab_home/gallery/skin/daily`
`mascot_arrow` `bubble_current` `btn_primary` `node_locked_40/39` `node_star_38` `node_current_37` `node_fail_36` `node_challenge`

> 这批件**带烘焙文字**，只适合“文案永远不变”的位置：设置、任务、成就、底栏 tab、吉祥物。
> 节点类是参考件——右侧边缘能看到原图投影被切掉的一点痕迹，**正式做关卡列表请用 `components/node_*`**。

### B. `components/` 程序化组件（2x，文案随便换）

节点六态：`node_locked / completed / current / star / fail / challenge`
按钮底：`btn_primary` `capsule` `plate_label` `circle_button` `bubble` `tab_active` `nav_bar` `node_pointer`
徽章：`badge_lock / star / skull / plus / alert`

`components.json`（也合并进了 `manifest.json`）里带 `nine_slice = [left, bottom, right, top]`，Unity 里直接填 Sprite 的 Border。

---

## 尺寸 / 坐标 / 导入

- 原图 941×1672 → 1080×1920 缩放 **1.1477**；所有 `ui/` 件的 `source_box` 在 `manifest.json`，可直接还原到原图坐标。
- 组件按 1080 档位设计、按 **2x（2160 宽）导出**，Unity 里 `Pixels Per Unit = 100`、`Sprite (2D and UI)`、`Mesh Type = Full Rect`、九宫格按 json 填。
- 文字：中文用**圆润超粗黑体**（站酷快乐体 / 思源黑体 Heavy / 微软雅黑 Bold 兜底），数字白色 + 下方柔阴影（offset 约 6px、blur 6、透明度 60%），**不要硬描边**。
- 阴影：组件已带内置柔阴影；切图件建议在 Unity 里统一补 `0 6px 14px rgba(40,60,30,.18)`，否则会和背景脱开。

---

## 已知限制（重要）

1. **背景是占位图**：`background/bg_garden_1080x1920.png` 是按构图重画的，不是原图背景。还原图里最大的差距就在这里（原图是暖阳光 + 写实花丛，占位图偏平）。
   要 1:1 需要**分层源文件或重新出图**，UI 切图/组件不用改。
2. **切图只有 1x**：源图 941 宽，2x 屏会发虚。要高清只能重绘或用组件。
3. **文字烘焙**：A 类件的中文不可换。
4. **节点切图有轻微边缘缺陷**（原图投影被切），只作参考。
5. 未做 Atlas、未做 Prefab、未接 Inkroom/v6 DesignSystem。

---

## 整套替换怎么落地

参考图（8 屏）只覆盖了部分界面，项目实际有 19 个界面。建议按这套组件库延展，而不是逐屏切图：

| 项目界面 | 参考图对应 | 能否直接切图 | 做法 |
| --- | --- | --- | --- |
| Loading | 加载 | ✗（面板仅 363×497） | 组件拼：logo + 进度条 + 背景 |
| Home | 画架主页 | ✗ | 组件 + 画架画作（游戏数据） |
| WorldMap / LevelSelect | **关卡地图（941×1672）** | 静态件可切 | **本轮已出** |
| Board | 对局 | ✗ | 棋盘用 tile kit（v7 tilekit 可复用）+ 软胶方块 |
| Settlement | 完成 | ✗ | 组件 + 彩带 + 画作 |
| Revive | 生命用完弹窗 | ✗ | 组件 + 心形图标 |
| Collection | 图库 | ✗ | 网格 + 像素缩略图（游戏数据） |
| Store / Boosters | 皮肤 / 道具 | ✗ | 色卡/道具卡组件，可批量生成 |
| Daily / Achievements | 每日/成就 | ✗ | 组件 + 进度条 + 图标 |
| Settings / About / Account / Leaderboard / Season | 参考图没有 | ✗ | 用同一组件库延展设计 |

**推荐顺序：**
1. 定这轮首页效果（颜色/圆角/厚度/字号）。
2. 用 `components/` 把首页接进 `BlockOutHomePage`，验证 1080×1920 与安全区。
3. 补图标库（齿轮/票券/剪贴板/奖杯/房子/画框/调色盘/日历）——原图这几个图标是 3D 渲染，1x 抠图边缘不干净，建议**按同样风格重绘或出 2x**。
4. 逐屏替换，每屏只换皮不动逻辑（视图脚本里的字段不用改）。
5. 背景最后出（2 张分层背景：花园、画廊走廊）。

---

## 复现

```bash
python tools/build.py             # 切图 + 九宫格底板
python tools/export_components.py # 组件 2x 导出
python tools/build_preview.py     # 1080x1920 还原图
python tools/make_docs.py         # 对照表 / 节点状态 / 对比图
```

依赖：Python + Pillow + OpenCV + numpy；字体 `C:/Windows/Fonts/msyhbd.ttc`。

---

## 切图自检结果（2026-11-16 修完）

**已修好的硬伤**——原因都是轮廓没对准，不是算法不行：

| 文件 | 原因 | 处理 |
| --- | --- | --- |
| `node_challenge` / `node_fail_36` | 上边多切 24px、右边多切 12px，把背景铺装带进来 | 按 10px 网格重对轮廓 |
| `node_locked_40/39` | 下边少切 11–14px，奶油边被切掉 | 同上 |
| `node_current_37` | 下边少切 24px，尾巴脱开 | 补到实际下沿（923） |
| `btn_primary` | 圆角半径给小了（74 vs 实际 104），两端露出背景 | 半径改 104，收窄左右 |
| `nav_bar` / `tab_*` | 上沿吃进草地阴影 | 重对边缘 + 5–7px 草色带清除 |
| `tab_daily` | 裁切框超出导航条右端 | 收到 878 |

**目前剩余**：`nav_bar` 上沿约 2px 草色发丝线、`tab_daily` 右上角约 2px 缺角。
1x 放在草地上**不可见**，只在纯色底放大看得到。

**自动检查**：孔洞 0、贴边裁断 0、天空串色 0。

**结论**：切图能“正常”，但靠的是**按像素对轮廓 + 逐件放大复核**，不是换个算法。
四种自动方案都试过：几何遮罩（切进背景）、GrabCut（保留背景条）、中值滤波（抹平渐变）、
边缘洪泛（吃掉奶油边）。奶油边是低对比柔边，机器分不出来——这也是生产里切图都靠美工钢笔工具的原因。

**自己复查的方法**：`preview/contact_sheet.png` 是全部资产；要放大看单件，用
`ui/<name>.png` 叠在深色底上（透明边缘在深底最明显）。

### 想自己微调某个切图

轮廓定义在 `tools/kit_defs.py` 的 `ELEMENTS`（`('rr', x1,y1,x2,y2,r)` / `('circle',cx,cy,r)`），
改完重跑 `python tools/build.py` 即可。`manifest.json` 里的 `source_box` 是裁切框。

## 关于 SVG

- **切图这件事，SVG 帮不上**：SVG 是矢量描述，不会帮你从像素里分离前景/背景。上限由源图决定（941px、文字烘焙、阴影压平）。
- **但组件应该用 SVG 画**：边缘天然干净、任意倍率清晰、改色/圆角只改参数、九宫格直接从矢量算。`components/` 现在是 PIL 栅格脚本，缺矢量源——这是它的短板。
- `svg/` 里是本轮做的 3 个矢量样件（`node_current` / `btn_primary` / `nav_bar`）+ Chrome 渲染结果，对比图见 `preview/png_vs_svg.png`。
- 注意：参考图是 3D 渲染（软胶高光/渐变/投影），SVG 只能渐变+模糊近似，**做不到 1:1**；要完全一致必须有 3D 源或分层 PSD。
- Unity 侧：SVG 需要 Vector Graphics 包，或按 2x/3x 预渲染 PNG 导入（推荐后者，兼容性最好）。
