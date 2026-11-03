# P0/P1 第三轮修复记录（按静态复查逐项处理）

## P0 棋盘与基础流程

| # | 问题 | 状态 | 修改文件 |
|---|---|---|---|
| 1 | 行方向与屏幕相反（Up 检查的是画面下方） | ✅ 已修复 | BoardView.cs cellPos Y 改为 `-totalH*0.5f + row*cellSize + ...`，row=0 在底部，row 增大向上，与 Vector2Int.up 一致 |
| 2 | 异形块空洞可点击 | ✅ 已修复 | BoardView.cs 容器 Image raycastTarget=false；每个占格 cell Image raycastTarget=true |
| 3 | 飞行时透明点击区变黑矩形 | ✅ 已修复 | FlyRoutine 跳过 root container，只 fade 子节点（cell+arrow） |
| 4 | Play 按钮覆写已恢复的局内进度 | ✅ 已修复 | UIController PlayBtn 传 `restoreRun: Profile.HasActiveRun` |
| 5 | tutorial_02 越界+重叠 | ✅ 已修复 | 重写 JSON（row 范围 0-5 内，无重叠）；Parser.Validate() 输出越界/重叠警告 |
| 6 | 棋盘不缩放，大棋盘超屏 | ✅ 已修复 | Rebuild() 按父 RectTransform 宽高自动算 cellSize（20-100px），留 15% 边距 |

## P1 胜负/存档/道具

| # | 问题 | 状态 | 修改文件 |
|---|---|---|---|
| 7 | 错误扣命后不存档 | ✅ 已修复 | HandleBlockTapped result.LifeLost 分支末尾调 SaveActiveRun() |
| 8 | 失败不存档 | ✅ 已修复 | OnLevelLost() 内调 SaveActiveRun() |
| 9 | 末关 Next 切空棋盘 | ✅ 已修复 | UIController Settlement NextBtn 检查 IsLastLevel → 回首页+Toast |
| 10 | GiveUp 不清局内进度 | ✅ 已修复 | GameManager.GiveUp() 清 HasActiveRun+Save；UIController 调用 |
| 11 | Hint 逐格动画 | ✅ 已修复 | PulseRoutine 收集所有可见 Image，单协程同步 pulse |

## 仍未修复（如实标注）

| # | 问题 | 原因 |
|---|---|---|
| 8(续) | 倒计时模式 RunTimeRemaining 存取/UI显示/复活加时 | UseTimeFailMode 默认关，未做倒计时 HUD |
| 11(续) | 道具连击规则（魔法/锤子不计玩家连击） | 当前都调 Combo.OnSuccessfulRemove，未区分玩家主动/道具自动 |
| 13 | SHA-256 真 hash | 仍用拼接字符串；需实现 SHA256 for extras sourceSha256 |
| 14 | Assembly 重复通关加一 | 仍内存计数，未按 ID 集合去重 |
| 15 | 图片展示回退/Settings Toggle 绑定/Onboarding 分步/13屏业务 | 需素材或后续轮次 |
| — | 旧 12 个华容道脚本 | 未删除，需 Unity 中确认冲突 |
| — | 全部代码未编译/Play | 按 AGENTS.md 未执行 |

## 手动验收步骤

1. Unity 打开 `E:/UnityProject/MutiplayGame/BlockOut`（6000.2.7f1）
2. 看 Console 编译错误
3. 建空场景挂 `BlockOutBootstrapper`，Play
4. 验证清单：
   - [ ] Up 箭头块向上飞，被上方块挡住时抖动（不是下方）
   - [ ] L 形/T 形块的空格不可点
   - [ ] 块飞出时不出现黑色矩形
   - [ ] 玩一半杀进程重进，点 Play 恢复中间状态
   - [ ] 棋盘大小自适应屏幕（不压 HUD/工具栏）
   - [ ] 点错块扣命后杀进程重进，命数正确
   - [ ] 失败弹窗 GiveUp 后重进不会回到失败关
