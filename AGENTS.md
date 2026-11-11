# BlockOut 协作规则

## BlockOut 仅同步 GitHub（2026-11-11 更新）

- 唯一提交与推送目标：`https://github.com/pgt2020/BlockOut.git`，`main` 分支，项目内容放仓库根目录。
- 不再提交到 Gitee。主仓库中的本地 `BlockOut/` 保留但取消跟踪并忽略；不要强制添加。
- 本地开发目录：`E:/UnityProject/MutiplayGame/BlockOut`；独立 GitHub 克隆：`E:/UnityProject/BlockOut-GitHub`。
- 同步前获取 GitHub 最新提交，保留已有历史与远程独有修改；不强制推送，不修改主仓库 origin。
- 同步源码、资源及 `.meta`、Packages、ProjectSettings、工具源码与文档，包括明确删除的文件；不上传 Unity 缓存、本地用户设置、bin/obj、临时测试报告或凭据。
- 提交信息和变更说明使用中文，完成后核对 GitHub main 并报告提交哈希。

## Unity 验证偏好

- 除非用户明确要求验证或刷新，不主动触发 AssetDatabase 刷新、脚本编译、Domain Reload、Play Mode、测试、Unity Console 读取或外部 C# 构建。
- 编译、运行和视觉验证默认由用户执行，交付时明确说明未执行这些检查。
