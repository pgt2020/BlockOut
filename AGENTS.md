# BlockOut 协作规则

## 双端同步提交

- 用户要求今后提交或上传 BlockOut 更新时，必须同时提交并推送到以下两个目标：
  - Gitee：`https://gitee.com/pgangtao/merge-game.git`，`master` 分支，项目位于 `BlockOut/`。
  - GitHub：`https://github.com/pgt2020/BlockOut.git`，`main` 分支，项目位于仓库根目录。
- 使用各自独立的克隆目录，保留两端已有历史，不修改主仓库 origin，不强制推送。同步相同的源码、资源、配置、工具和文档，并处理本次明确删除的文件；不要混入其他项目。
- 不上传 Unity 缓存、本地用户设置、工具 bin/obj、临时测试报告或凭据。保留工具源码及其项目文件。
- 提交信息及面向用户的变更说明默认使用中文。完成后核对两端远程分支并报告各自提交哈希；若仅一端成功，明确报告另一端失败原因，不得宣称全部完成。

## Unity 验证偏好

- 除非用户明确要求验证或刷新，不主动触发 AssetDatabase 刷新、脚本编译、Domain Reload、Play Mode、测试、Unity Console 读取或外部 C# 构建。
- 编译、运行和视觉验证默认由用户执行，交付时明确说明未执行这些检查。
