# UI v11 · 整屏贴图还原（用户方案 1）

## 你选的方案
整屏贴图：第一版原图**整张铺满屏幕**，透明热区管点击。放弃"能玩"（方块画死在图里）。
用户明确批评：切图→拼元件→擦字→动态镜像的旧管线每一步都在破坏原图，细节不可能 100% 还原。
本版把旧管线整个扔掉，**不切任何元件**。

## 做了什么
- 真源：`DesignAssets/UI_v7/reference_original/s1~s9`（你第一版原图，字节级原样复制，零缩放/零擦字/零重采样）。
- 资源：`Assets/BlockOut/Resources/UI/Reference/fullscreen/s1.png ~ s9.png`（9 张整图 + sprite meta）。
- prefab：`Assets/BlockOut/Resources/Prefabs/UI/Reference/ReferenceS1~S9.prefab`（覆盖旧版，旧版备份在 `Reference_backup_old/`）。
  - 结构极简：Root(PageLayout+ReferenceSkin) → Letterbox → DesignSurface → ReferenceSkin → **FullImage(整图) + 透明 Hotspot**。
  - **无切片元件、无挖空、无擦字、无 Dyn 动态文字**。
- 铺满：DesignSurface 用 390×844（实机 1125×2436 比例），FullImage anchor 0-1 stretch 铺满，热区按设计坐标比例映射。
- 代码：`BlockOutUIManager.cs` 的 ScreenSkinMap 补了 Home→s2、Collection→s3（原先只有 s1/s4/s7；s5/s6 是弹层、s8/s9 是独立页）。
- 生成器：`Tools/UIAuthoring/gen_fullscreen_skin.py`（可重跑，参数化）。

## 运行入口（映射）
| 屏 | 内容 | 触发 |
|---|---|---|
| s1 | 加载页 | Loading |
| s2 | 首页 | Home（本次新增） |
| s3 | 图库 | Collection（本次新增） |
| s4 | 游戏页 | Board |
| s5 | 结算 | SettlementLayer |
| s6 | 失败 | FailLayer |
| s7 | 皮肤商店 | Store |
| s8 | 每日 | 独立页 |
| s9 | 章节地图 | 独立页 |

## 需要你验证
用户要求：不自行运行 Unity，由用户运行并截图。请逐屏确认：
1. 整图是否铺满整屏（无上下留白、无"中间一条"）。
2. 9 屏内容是否 = 第一版原图（细节 100%）。
3. 透明热区能否点击跳转（首页开始/设置、游戏页暂停/道具、结算下一关/首页、失败复活/重开）。
4. 有无图像拉伸变形不可接受（原图 0.75 比例 → 屏幕 0.46 比例，stretch 会纵向拉伸；若不接受可改 aspect-fill，但会裁掉两侧）。

## 回滚
旧切图 prefab 完整备份在 `DesignAssets/UI_v11_fullscreen/Reference_backup_old/`（9 个）。
UIManager.cs 改动备份在 `Assets/BlockOut/Runtime/UI/Views/BlockOutUIManager.cs.bak_fullscreen`。
