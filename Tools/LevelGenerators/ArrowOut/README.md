# ArtOut Level Generator

This tool converts a pixel image into ArtOut level JSON that the current Unity project can parse.
The splitter follows the reference workflow in `../关卡说明/ArtOutBlockGallery/拆分算法`: it first finds same-color connected regions, then covers those regions with the approved ArtOut block shapes using area, boundary-fit, and local-diversity scoring.

## Setup

```bash
python -m pip install pillow
```

## Generate

```bash
python generate_artout_levels.py ./input/music_note.png --picture-id music_note --chapter 0 --levels-per-picture 12
```

If the home grid and collection page should use the BrilliantSort collection artwork instead of the per-level pixel image, pass the collection shape and preview explicitly:

```bash
python generate_artout_levels.py ./input/music_note.png --picture-id music_note --chapter 0 --levels-per-picture 12 --shape-image Collections_01_shape.png --preview-image Collections_01.png
```

Outputs:

- `Assets/Resources/ArtOut/Levels/{picture_id}_{index}.json`
- `Assets/Bundles/Main/Json/ArtOutPictureConfig.json`

The generated level uses the same `shapeId`, `direction`, `color`, and `arrowCell` fields read by `ArtOutLevelJsonParser`. Shape ids are aligned with the 28 sprites in `Assets/Bundles/Sprites/WoodBlockHDR/{shapeId}.exr`; keep that numbering stable when adding or replacing block art. Do not write `rotation` in new level JSON because wood lighting and shadows are baked into each `{shapeId}.exr`; final block orientation is represented directly by the 1-28 `shapeId` set. The picture config now separates `shapeImage`, `previewImage`, and `completeImage`: the home grid uses `shapeImage` (`Collections_XX_shape.png`), the collection page uses the full preview image (`Collections_XX.png`), and the post-win Tap-to-continue page uses `completeImage` (defaults to the generated per-level pixel image).

## Audit

```bash
python audit_levels.py ../../Assets/Resources/ArtOut/Levels
```

The audit expands every piece with the same shape rules used by Unity. It fails if any block cell is out of bounds, overlaps another block, or uses a non-zero legacy `rotation`.

## Regenerate From Existing Picture Config

```bash
python generate_levels_from_config.py
```

This rewrites the existing level JSON files from `ArtOutPictureConfig.shapeRows`, keeping the same level ids, chapter indices, and rewards. Since `shapeRows` does not contain real pixel colors, this path splits the whole filled picture area first and applies display colors after the split. Use this when picture-grid data is already correct but the block placement data needs to be rebuilt.

## Update Compatibility

Keep `pictureId` stable when updating a picture. Increase `--data-version` when the generated layout changes. Runtime progress is saved by level id, so unchanged level ids keep completion after an overwrite install, while removed level ids are ignored.

## BlockOut 复制说明

本目录是从 ArrowOutBlockGallery 复制到 BlockOut 的独立工具副本。原始脚本默认按 ArrowOut 工程目录解析输入输出路径；在 BlockOut 中运行时请显式传入路径，或先按上级 `Tools/LevelGenerators/README.md` 进行适配。需要生成全部单格方块时，将生成逻辑中的形状选择限制为 `shape_id = 1`。
