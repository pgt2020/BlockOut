# BlockOut · 花园奶油风 v3（首页）

> 目标：**只做首页**，走 A 路线——背景用生图工具出，UI 组件用 three.js 真 3D 渲染，最后合成整屏并切好资产。
> 状态：设计稿 / 资产，**未接 Unity、未编译、未真机验证**。

---

## 看这两张

| 文件 | 说明 |
| --- | --- |
| `preview/rebuilt_home_1080x1920.png` | 整屏效果 |
| `preview/reference_vs_rebuilt.png` | 左参考 / 右还原 |
| `preview/components_sheet_dark.png` | 18 个组件（深底看透明边） |

---

## 这版怎么来的

1. **背景**：CogView-3-Flash 出图（768×1344，按 `ART_SPEC.md` 的构图），
   去水印 → 1080×1920 cover 裁切 → 锐化 → 轻调色。
   生成原图留在 `gen/`，最终采用 `gen/bg_v1.png`，处理结果 `art/bg_source.png`。
2. **UI 组件**：three.js 渲染（`MeshPhysicalMaterial` + 暖光 + 软阴影），
   节点六态/主按钮/胶囊/底栏/气泡/徽章等 18 个，全部 RGBA、无文字。
3. **合成**：`tools/compose.py` 按参考图坐标落位、叠加中文与数字、导出整屏和组件。

## 目录

```
UI_garden_v3_home/
├─ art/               渲染/处理的源图（bg_source 为采用背景）
├─ components/        切好的组件 RGBA + components.json（九宫格）
├─ sliced/            参考图 1x 切图（设置/货币/任务/成就/底栏/吉祥物）
├─ preview/           整屏 / 对比 / 组件表
├─ gen/               生图原图
├─ tools/render/      three.js 渲染工程（clay.html / garden.html + vendor）
├─ tools/prep_bg.py   去水印 + 存成 bg_source.png
├─ tools/compose.py   合成 + 导出组件
├─ ART_SPEC.md        出图规格（再用更好）
└─ manifest.json
```

## 自评（对参考）

| 部分 | 还原度 |
| --- | --- |
| 背景 | ~85%：构图/配色/暖光到位；细节仍是"绘本 3D"而非参考的精细渲染 |
| 节点/按钮 | ~80%：体积、奶油边、软阴影对；主按钮边框略偏灰 |
| 排版比例 | ~90%：按参考坐标对齐 |
| 整体 | **~80%** |

## 已知差异（还差什么）

- 当前节点缺少参考那颗**向下小箭头**。
- 主按钮外框两侧偏灰（3D 侧壁受光），参考更亮更平。
- 吉祥物仍是参考图 1x 切图，比 3D 节点略软。
- 背景是 768×1344 生成后放大到 1080，细节不如原生 2K。

## 怎么改

- 换背景：替换 `art/bg_source.png`（任意尺寸自动 cover）或 `gen/bg_v*.png` 里挑一张，重跑 `tools/prep_bg.py` + `tools/compose.py`。
- 改组件：`tools/render/clay.html` 里调尺寸/材质/配色，按 README 的命令重渲染。
- 改文案/关卡号：`tools/compose.py` 顶部 `NODES` 列表。

## 复现

```bash
cd tools/render && python -m http.server 8778     # ES module 需要 http
# clay.html?c=node_current&s=current&w=760&h=760&fit=2.3
cd ../.. && python tools/prep_bg.py gen/bg_v1.png && python tools/compose.py
```
