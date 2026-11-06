#!/usr/bin/env python3
"""Regenerate existing ArtOut levels from ArtOutPictureConfig shapeRows."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from generate_artout_levels import (
    PROJECT_ROOT,
    Cell,
    Piece,
    build_level,
    cover_grid,
    validate_level,
)

DEFAULT_COLORS = [
    (111, 197, 35),
    (83, 213, 43),
    (210, 160, 16),
    (255, 157, 32),
    (199, 113, 62),
    (247, 120, 37),
]


def parse_color(value: str | None) -> tuple[int, int, int] | None:
    if not value:
        return None
    match = re.fullmatch(r"#?([0-9a-fA-F]{6})", value.strip())
    if not match:
        return None
    raw = match.group(1)
    return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))


def load_config(config_path: Path) -> dict[str, dict]:
    data = json.loads(config_path.read_text(encoding="utf-8-sig"))
    return {picture["id"]: picture for picture in data.get("pictures", []) if picture.get("id")}


def rows_to_grid(rows: list[str], palette: list[tuple[int, int, int]]) -> list[list[Cell]]:
    grid: list[list[Cell]] = []
    for row_index, row in enumerate(rows):
        cells: list[Cell] = []
        for column_index, value in enumerate(row):
            filled = value == "1"
            cells.append(Cell(filled=filled, color=(255, 255, 255)))
        grid.append(cells)
    return grid


def apply_palette(pieces: list[Piece], palette: list[tuple[int, int, int]]) -> list[Piece]:
    colors = palette or DEFAULT_COLORS
    tinted: list[Piece] = []
    for index, piece in enumerate(pieces):
        color = colors[(piece.row * 7 + piece.column * 3 + index * 5) % len(colors)]
        tinted.append(
            Piece(
                column=piece.column,
                row=piece.row,
                shape_id=piece.shape_id,
                rotation=piece.rotation,
                direction=piece.direction,
                color=color,
                arrow_cell=piece.arrow_cell,
            )
        )
    return tinted


def existing_level_paths(levels_path: Path) -> list[Path]:
    return sorted(levels_path.glob("*.json"))


def load_existing_levels(levels_path: Path) -> list[tuple[Path, dict]]:
    levels: list[tuple[Path, dict]] = []
    for path in existing_level_paths(levels_path):
        levels.append((path, json.loads(path.read_text(encoding="utf-8-sig"))))

    levels.sort(key=lambda item: (int(item[1].get("chapter", 0)), int(item[1].get("levelInChapter", 0)), item[1].get("id", item[0].stem)))
    return levels


def collect_palette(existing_levels: list[tuple[Path, dict]]) -> dict[str, list[tuple[int, int, int]]]:
    palettes: dict[str, list[tuple[int, int, int]]] = defaultdict(list)
    for _, level in existing_levels:
        picture_id = level.get("pictureId")
        if not picture_id:
            continue
        for piece in level.get("pieces", []):
            color = parse_color(piece.get("color"))
            if color and color not in palettes[picture_id]:
                palettes[picture_id].append(color)
    return palettes


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate current ArtOut levels from picture shapeRows.")
    parser.add_argument("--levels", type=Path, default=PROJECT_ROOT / "Assets/Resources/ArtOut/Levels")
    parser.add_argument("--picture-config", type=Path, default=PROJECT_ROOT / "Assets/Bundles/Main/Json/ArtOutPictureConfig.json")
    parser.add_argument("--seed", type=int, default=1729)
    parser.add_argument("--data-version", type=int)
    args = parser.parse_args()

    picture_config = load_config(args.picture_config)
    existing_levels = load_existing_levels(args.levels)
    palettes = collect_palette(existing_levels)
    generated = 0

    for global_index, (path, old_level) in enumerate(existing_levels):
        picture_id = old_level.get("pictureId")
        picture = picture_config.get(picture_id)
        if not picture:
            print(f"skip {path.name}: missing picture config for {picture_id}")
            continue

        grid = rows_to_grid(picture.get("shapeRows", []), palettes.get(picture_id, []))
        pieces = apply_palette(cover_grid(grid, args.seed + global_index), palettes.get(picture_id, []))
        level = build_level(
            picture_id=picture_id,
            display_name=picture.get("name", picture_id),
            chapter=int(old_level.get("chapter", 0)),
            level_in_chapter=int(old_level.get("levelInChapter", global_index)),
            grid=grid,
            pieces=pieces,
            data_version=args.data_version or int(old_level.get("dataVersion", 1) or 1),
        )
        level["id"] = old_level.get("id", path.stem)
        level["displayName"] = f"{picture.get('name', picture_id)} {int(level['levelInChapter']) + 1:03d}"
        level["rewardCoins"] = int(old_level.get("rewardCoins", level["rewardCoins"]))
        validate_level(level)
        path.write_text(json.dumps(level, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        generated += 1
        print(f"wrote {path.name} ({len(pieces)} pieces)")

    print(f"regenerated {generated} levels")
    return 0


if __name__ == "__main__":
    sys.exit(main())

