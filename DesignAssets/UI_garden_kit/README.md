# 花园地图 · UI 切图包 v1

> 方向：柔和 3D 绘本花园 + 奶油质感 UI + 纵向关卡地图
> 源图：`source/reference.jpg`（941×1672）
> 状态：**待检查**。只处理这一张地图/首页界面，未接入 Unity、未编译、未运行。

---

## 先看这三张

| 文件 | 用途 |
| --- | --- |
| `preview/rebuilt_screen.png` | 用生成背景 + 切图拼回的整屏，验证资产能直接落地 |
| `preview/contact_sheet.png` | 全部资产的透明底对照表，按“切图 / 生成”分组 |
| `preview/node_bases_demo.png` | 无文字节点底座 + 数字叠层演示 |

---

## 目录

```
UI_garden_kit/
├─ background/          生成的无 UI 花园底图（3 个尺寸）
├─ ui/                  从参考图切出的 18 个透明/半透明元素
├─ generated/           生成的 15 个补充件（空底座、空按钮、徽章、路径）
├─ preview/             还原图、对照表、节点演示
├─ source/              参考原图
├─ tools/               背景生成 / 切图脚本（可复现）
├─ manifest.json        每个文件的尺寸、类型、源裁切框、备注
└─ README.md
```

---

## A. 从参考图切出（18）

| 文件 | 尺寸 | 说明 |
| --- | --- | --- |
| `ui/btn_settings.png` | 108×108 | 圆形奶油底 + 齿轮 |
| `ui/pill_currency.png` | 254×92 | 票券 + 数量 + 加号，复合胶囊 |
| `ui/btn_task.png` | 175×200 | 任务按钮：圆盘 + 标签（“任务”烘焙） |
| `ui/btn_achievement.png` | 175×202 | 成就按钮：圆盘 + 标签（“成就”烘焙） |
| `ui/node_locked_40.png` | 170×175 | 灰锁节点（数字 40 烘焙） |
| `ui/node_locked_39.png` | 170×160 | 灰锁节点（数字 39 烘焙） |
| `ui/node_star_38.png` | 176×178 | 紫星节点（数字 38 烘焙） |
| `ui/node_current_37.png` | 210×226 | 当前关卡绿节点 + 下指箭头 |
| `ui/node_fail_36.png` | 157×157 | 失败红节点 + 骷髅 |
| `ui/node_challenge.png` | 167×157 | 挑战红节点 + 骷髅 |
| `ui/bubble_current.png` | 147×93 | “当前关卡”气泡（文字烘焙） |
| `ui/mascot_arrow.png` | 152×136 | 黄色方块角色 + 绿箭头，按轮廓遮罩 |
| `ui/btn_primary.png` | 546×216 | 主按钮完整版（“第 37 关”文字烘焙） |
| `ui/nav_bar.png` | 844×234 | 底部导航整条（四个 tab 已烘焙） |
| `ui/tab_home.png` | 184×170 | 首页 tab，带导航奶油底 |
| `ui/tab_gallery.png` | 184×170 | 图库 tab，带导航奶油底 |
| `ui/tab_skin.png` | 184×170 | 皮肤 tab，带导航奶油底 |
| `ui/tab_daily.png` | 184×170 | 每日 tab，带导航奶油底 |

> 切图规则：按元素轮廓做 alpha 遮罩，再对天空蓝色做去边，避免透明区带蓝边。
> 元素自带的投影只保留少量；正式进 Unity 时建议再补一层统一的软阴影。

---

## B. 生成补充（15）

| 文件 | 尺寸 | 说明 |
| --- | --- | --- |
| `generated/node_base_locked.png` | 256×256 | 灰锁节点底座，无数字 |
| `generated/node_base_current.png` | 256×256 | 当前节点底座，无数字，带金色外发光 |
| `generated/node_base_star.png` | 256×256 | 紫星节点底座，无数字 |
| `generated/node_base_fail.png` | 256×256 | 失败红节点底座，无数字 |
| `generated/node_base_challenge.png` | 256×256 | 挑战红节点底座，无数字 |
| `generated/btn_primary_empty.png` | 512×200 | 无文字主按钮，文字/图标另叠 |
| `generated/nav_bar_empty.png` | 450×125 | 空导航条，tab 另叠 |
| `generated/bubble_current_empty.png` | 220×140 | 空气泡，文字另叠 |
| `generated/badge_lock.png` | 128×128 | 独立锁徽章 |
| `generated/badge_star.png` | 128×128 | 独立星星徽章 |
| `generated/badge_skull.png` | 128×128 | 独立骷髅徽章 |
| `generated/badge_plus.png` | 128×128 | 加号徽章 |
| `generated/badge_alert.png` | 128×128 | 红点提醒 |
| `generated/path_vertical.png` | 96×640 | 纵向路径条，可上下平铺 |
| `generated/path_horizontal.png` | 320×56 | 横向连接条 |

> 节点底座已做成“无文字 + 独立徽章”的结构，关卡数字、锁、星、骷髅都可以单独叠。

---

## C. 背景（3）

| 文件 | 尺寸 | 说明 |
| --- | --- | --- |
| `background/bg_garden_1080x1920.png` | 1080×1920 | 主用尺寸 |
| `background/bg_garden_2160x3840.png` | 2160×3840 | 2× 渲染 |
| `background/bg_garden_941x1672.png` | 941×1672 | 与参考图同尺寸，方便 1:1 对位 |

> 背景是**生成的同风格插画**，不是参考图原背景。原图 UI 覆盖面积太大，无法干净还原；
> 生成版保留了天空、云、左侧画廊、右侧画架、花丛和中央石径的构图，建筑和画架的细节做了简化。
> 如果有分层源文件，建议直接用正式背景替换，UI 切图不需要改。

---

## 使用说明

### 1. 尺寸与坐标

- 参考图 941×1672，UI 切图保持原像素尺寸。
- 目标 1080×1920 时，整体缩放约 **1.148×**；390×844 设计档约 **0.414×**。
- `preview/rebuilt_screen.png` 就是用 1.148× 把切图贴到 1080×1920 背景上的结果。
- `manifest.json` 里有每个切图的 `source_box`，可直接还原到参考图坐标。

### 2. 文字烘焙与空壳

以下资产带**已烘焙中文**，换语言/换关卡号时需要替换：

| 带文字资产 | 替代方案 |
| --- | --- |
| `node_*` 的 40/39/38/37/36/挑战 | `generated/node_base_*` + 字体数字 |
| `btn_primary` 的“第 37 关” | `generated/btn_primary_empty` + 文字 |
| `bubble_current` 的“当前关卡” | `generated/bubble_current_empty` + 文字 |
| `nav_bar` 的四个 tab | `generated/nav_bar_empty` + `tab_*` 或自绘 tab |
| `btn_task` / `btn_achievement` 的“任务/成就” | 本轮未出空标签版，需要可再补 |

字体建议选圆润超粗黑体（如 Baloo 2 ExtraBold、Nunito ExtraBold、站酷快乐体），
数字用白色 + 右下柔和阴影，不要用硬描边。

### 3. 推荐 z-order

```
背景
→ path_vertical（纵向平铺）
→ path_horizontal（当前关卡横向连接）
→ 节点（40/39/38/37/36/挑战）
→ bubble_current
→ mascot_arrow
→ btn_settings / pill_currency / btn_task / btn_achievement
→ btn_primary
→ nav_bar（或 nav_bar_empty + tabs）
```

### 4. 路径

- `path_vertical.png` 是 96×640，左右有柔和渐变，上下可平铺；按屏宽缩放到约 60–70px。
- `path_horizontal.png` 是 320×56，用于当前节点下方、吉祥物一排的横向连接；建议 40–55% 不透明度。

### 5. 阴影

- 切图按轮廓裁切，原图右侧的投影只保留了一部分（36/挑战最明显）。
- 进 Unity 后建议统一加一层 `0 4px 10px rgba(50,60,30,.18)` 的软阴影，避免和背景脱节。
- 生成的节点底座/徽章已带内置软阴影。

---

## 已知限制

1. **背景是生成占位**：构图和配色对，但不是原图画质；建筑/画架细节简化。
2. **部分切图含少量烘焙环境**：`mascot_arrow` 四角可能带一点地面，`node_fail_36`/`node_challenge` 右侧带一点节点投影；放大 2× 以上能看出来。
3. **切图是 1×**：源图只有 941×1672，没有更高分辨率可切；2× 使用会变软。
4. **文字烘焙**：任务/成就标签、tab 文字、货币数字“3”已烘焙。
5. 未做九宫格、Atlas、Prefab、Unity 导入设置。
6. 未编译、未进入 Unity、未做真机适配。

---

## 下一步可选

- 定这版后：补 `@2x` 切图、九宫格、Atlas、空任务/成就标签、英文版文字。
- 用同一套风格继续做：对局棋盘、通关结算、图库、皮肤、每日。
- 如果背景需要完全还原参考图：需要分层源文件或重新出图，UI 切图可直接复用。

---

## 复现

- `tools/gen_bg.py`：生成花园背景（输出 `tools/bg_scene.html`，用 Chrome 截图）。
- `tools/slice_assets.py`：按 `manifest.json` 的裁切框重新切图、生成底座/徽章/路径。
- 依赖：Python + Pillow + OpenCV + numpy；背景渲染用本机 Chrome。
