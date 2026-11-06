# BlockOut 关卡生成工具

本目录按来源分开保存两个项目的关卡工具，复制时保留了原始算法和依赖，避免与 BlockOut 现有运行时代码混淆。

## ArrowOut

路径：`Tools/LevelGenerators/ArrowOut/`

这是完整的图片/像素图转 ArtOut 关卡 JSON 流程：

- `generate_artout_levels.py`：从图片生成棋盘、拆分方块、分配方向并输出 JSON。
- `generate_levels_from_config.py`：根据已有图片配置重新生成已有关卡。
- `board_splitter.py`、`artout_shapes.py`：拆分和形状依赖。
- `audit_levels.py`：验证边界、重叠和形状编号。
- `UnityRuntime/ArtOutPieceLevelGenerator.cs`：原项目中的 C# 随机关卡生成器参考实现。

原始流程依赖 Pillow：

```powershell
python -m pip install pillow
python Tools/LevelGenerators/ArrowOut/generate_artout_levels.py input.png --picture-id sample --chapter 0 --levels-per-picture 12
```

脚本仍保留原始 ArtOut 输出结构和参数；正式写入 BlockOut 的 `Assets/Resources/ArtOut/Levels` 前，应根据实际输入输出路径传参或再做一层适配。

要生成全部单格方块，应在生成逻辑中限制 `shape_id` 为 `1`。

## TapGallery

路径：`Tools/LevelGenerators/TapGallery/`

- `tap_db.py`：读取已有图片/网格，使用模拟退火为方块分配可解方向，并输出箭头结果图片和文本。

它是方向求解和关卡辅助生成器，不直接输出 BlockOut 的 ArtOut JSON。运行示例：

```powershell
python Tools/LevelGenerators/TapGallery/tap_db.py --mode batch --input input-images --output output-arrows --iterations 5000
```

该脚本依赖 `numpy` 和 `Pillow`。两个工具都只是复制到 BlockOut 的工具目录，未自动执行，也未修改 Unity 场景或资源。
