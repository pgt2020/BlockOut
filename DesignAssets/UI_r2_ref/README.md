# BlockOut UI R2 —— 按用户提供的参考图重做

## 本轮定位

**推翻 R1（`UI_r1_board`）的方向。** 用户明确指出两点：
1. 按他给的两张参考图实现（`ref/01_user_map.jpg` 关卡地图、`ref/02_user_8screens.jpg` 八屏拼图）；
2. R1 的米色点阵平面背景完全不符合要求。

R2 以用户图为唯一准绳：**真实 3D 花园/画廊场景背景 + 厚软胶浮层 UI + 彩色立体方块**。
注意：用户参考图本身就大量使用高光、渐变、胶囊按钮，因此本轮以明确参考为准，推翻此前"避免高光渐变"的泛化要求。

## 已完成（2 个代表页，待用户评审）

| 页 | 文件 | 说明 |
|---|---|---|
| 关卡地图 | `out/map_2x.png` | 蓝天花园画廊 3D 场景背景；40/39 灰锁、38 紫星、37 绿当前带气泡、36/挑战红骷髅；黄色方块吉祥物带绿箭头；任务/成就悬浮圆钮；绿色"第 37 关"CTA；底部 4 独立卡片 tab |
| 对局页 | `out/game_2x.png` | 浅奶油点阵底；真实关卡 `Level12_easy`（12×12 / 43 块 / 已飞 8）驱动棋盘；绿橙蓝红四主色软胶方块带白箭头；心+进度 HUD；提示/锤子/炸弹三道具卡 |

- 对比图：`preview/compare_map.png`、`preview/compare_game.png`（左=用户参考，右=R2）
- 手机尺寸预览：`preview/map_phone.png`、`preview/game_phone.png`

## 复用的资产（未新花生图积分）

- `assets/bg_garden_clean.png`：来自 `UI_v10/bg/Vertical_mobile_game_backgroun_2026-11-16T07-30-06.png`，裁掉右下水印后铺满。构图贴合用户参考图（左侧画廊建筑、中间石板路、右侧花丛画架、蓝天白云）。
- 棋盘数据：`data/board.json`，从 `UI_r1_board` 复制，源头是项目真实关卡 JSON。

## 与项目真实规则的关系（重要）

用户参考图的方块看起来是"每格一个独立方块、每格一个箭头"。项目 BlockOut 的真实规则是**多格连体块、一块一个箭头**（见 `Core/Rules/BlockOutShapeLibrary.cs` 与关卡 JSON 的 `shapeId`）。
R2 对局页**保留真实规则**：按 `shapeId` 还原多格形状，箭头放在该块唯一的 arrow 格。这是刻意的，不能为了像参考图而改玩法。

## 与 DesignSystem v6 的冲突（待裁决）

`Docs/DesignSystem.md` v6 §0 写的是"真·干净扁平，不做立体"。R2 是厚软胶立体，与 v6 冲突。用户尚未裁决；未修改 DesignSystem.md。

## 尚未执行（按项目约定，非用户明确要求不做）

- 未接入 Unity（`Assets/` 未改动）、未编译、未 Domain Reload、未 Play Mode、未读 Console、未外部构建。
- 未做静态检查以外的任何运行验证。
- 未切图、未做九宫格、未延展其他 6 屏（加载/图库/结算/失败/皮肤/每日）。
- 未做组件重组对比。

## 状态

`awaiting-user-review` —— 两页设计稿已出，等用户确认风格基准后再延展整套、切图与 Unity 还原。
