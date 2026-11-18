# 这块怎么出不去 · BlockOut

Unity 6000.2.7f2，UGUI，竖屏小游戏。点击方块，让它沿箭头方向飞出；前方有阻挡会损失生命。同一受阻方块不会重复扣心。全部消除后揭晓对应像素图片，并保存关卡进度、金币和道具。

## 打开与体验

使用 Unity 6000.2.7f2 打开本目录，运行 `Assets/BlockOut/Scenes/Launcher.unity`。

- 首次进入直接体验首关手指引导；之后从首页继续，已有半局可恢复。
- 首页只提供关卡、道具、设置和开始入口。章节插画、皮肤商店、每日任务及成就不是当前功能。
- 已交付 606 关，分为 51 章，末章 6 关；关卡页可以继续当前关卡或重玩已完成关卡。
- 提示、锤子、魔法分别从第 2、3、4 关解锁。提示寻找可飞块，锤子选中消除一块，魔法链式消除最多配置数量的方块。
- 默认生命模式；前 10 关免费复活。后续广告取决于实际广告服务配置，未接入时回退金币路径。
- 退出本关需确认，清除半局进度；金币、库存和通关记录保留。暂停及切后台保留半局。

## 界面与资源维护

页面位于 `Assets/BlockOut/Resources/Prefabs/UI`，正式流程使用真实 UGUI 控件，不叠加整页参考稿。
`Tools/UIAuthoring/polish_player_experience.py` 维护本轮修订；勿单独执行旧的参考覆盖脚本恢复历史界面。

静态检查：

```powershell
python Tools/UIAuthoring/verify_pages.py
python Tools/UIAuthoring/verify_home_page.py
python Tools/UIAuthoring/verify_board_page.py
python Tools/UIAuthoring/audit_player_content.py
```

最后一项以 C# 运行时形状表检查全部关卡的边界、重叠、箭头、无道具可解性及 30 种贴图占格。旧关卡生成器形状表有历史差异，不应代替该校验。

Unity 测试：`BlockOut.Tests.EditMode`；玩家流程：`BlockOutPlayerJourneyTests`，使用内存存档，输出真实 Unity 渲染图到 `design/ui/player-polish-20261117/runtime`。测试渲染覆盖常规、短屏、长屏，不代表手机实际触控和广告 SDK 验收。

本轮记录见 `Docs/玩家体验整修_2026-11-17.md`。历史华容道说明移至 `Docs/历史README_华容道.md`，不再作为当前产品说明。

## 仓库

只同步至 GitHub `pgt2020/BlockOut` 的 `main`，遵循 AGENTS.md。未明确要求提交时不提交或推送。
