把新背景图放在这个文件夹，命名 bg_source.png（或 bg_source.jpg / .jpeg）。

- 任意尺寸都行：脚本会自动等比放大并居中裁成 1080×1920。
- 建议 1080×1920 或 2160×3840；9:16。
- 内容只要场景，不要任何 UI / 按钮 / 数字 / 文字 / 水印。
- 地平线尽量落在画面高度 55%~60% 处（节点坐标是按参考图固定的）。

放好后运行：  python tools/compose.py
输出：preview/rebuilt_home_1080x1920.png 与 preview/reference_vs_rebuilt.png
