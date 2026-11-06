#!/usr/bin/env python3
"""Validate ArtOut level JSON files against the runtime shape rules."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from generate_artout_levels import PROJECT_ROOT, direction_step, shape_cells


def expected_cells_from_rows(rows: list[str]) -> set[tuple[int, int]]:
    return {
        (column, row)
        for row, values in enumerate(rows)
        for column, value in enumerate(values)
        if value == "1"
    }


def audit_level(level: dict, picture_rows: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    width = max(1, int(level.get("width", 1)))
    height = max(1, int(level.get("height", 1)))
    occupied: dict[tuple[int, int], int] = {}

    for index, piece in enumerate(level.get("pieces", [])):
        column = max(0, int(piece.get("column", 0)))
        row = max(0, int(piece.get("row", 0)))
        shape_id = int(piece.get("shapeId", 1))
        rotation = int(piece.get("rotation", 0)) % 4
        if rotation != 0:
            errors.append(f"piece {index} rotation must be 0; use the matching shapeId orientation instead")

        for x, y in shape_cells(shape_id, rotation):
            cell = (column + x, row + y)
            if cell[0] < 0 or cell[1] < 0 or cell[0] >= width or cell[1] >= height:
                errors.append(f"piece {index} out of bounds at {cell}")
                continue

            if cell in occupied:
                errors.append(f"piece {index} overlaps piece {occupied[cell]} at {cell}")
                continue

            occupied[cell] = index

    if picture_rows:
        expected = expected_cells_from_rows(picture_rows)
        actual = set(occupied.keys())
        expected_width = max((len(row) for row in picture_rows), default=width)
        expected_height = len(picture_rows)
        if width != expected_width or height != expected_height:
            errors.append(f"size {width}x{height} does not match picture shape {expected_width}x{expected_height}")
        for cell in sorted(expected - actual)[:12]:
            errors.append(f"missing block at picture cell {cell}")
        extra_cells = sorted(actual - expected)
        for cell in extra_cells[:12]:
            errors.append(f"block outside picture shape at {cell}")
        if len(expected - actual) > 12:
            errors.append(f"... {len(expected - actual) - 12} more missing cells")
        if len(extra_cells) > 12:
            errors.append(f"... {len(extra_cells) - 12} more outside-shape cells")

    solve_errors = audit_solvability(level)
    errors.extend(solve_errors)

    return errors


def piece_cells(piece: dict) -> set[tuple[int, int]]:
    column = max(0, int(piece.get("column", 0)))
    row = max(0, int(piece.get("row", 0)))
    shape_id = int(piece.get("shapeId", 1))
    rotation = int(piece.get("rotation", 0)) % 4
    return {
        (column + x, row + y)
        for x, y in shape_cells(shape_id, rotation)
    }


def can_move(piece: dict, active: list[dict], width: int, height: int) -> bool:
    occupancy: dict[tuple[int, int], dict] = {}
    for active_piece in active:
        for cell in piece_cells(active_piece):
            occupancy[cell] = active_piece

    step_x, step_y = direction_step(str(piece.get("direction", "Right")))
    for origin_x, origin_y in piece_cells(piece):
        cursor = (origin_x + step_x, origin_y + step_y)
        while 0 <= cursor[0] < width and 0 <= cursor[1] < height:
            blocker = occupancy.get(cursor)
            if blocker is not None and blocker is not piece:
                return False
            cursor = (cursor[0] + step_x, cursor[1] + step_y)
    return True


def audit_solvability(level: dict) -> list[str]:
    width = max(1, int(level.get("width", 1)))
    height = max(1, int(level.get("height", 1)))
    active = list(level.get("pieces", []))
    removed = 0
    while active:
        movable_index = next((index for index, piece in enumerate(active) if can_move(piece, active, width, height)), -1)
        if movable_index < 0:
            preview = [
                f"#{index}:{piece.get('direction')}@({piece.get('column')},{piece.get('row')})"
                for index, piece in enumerate(active[:8])
            ]
            return [f"unsolvable after {removed} removals; stuck pieces: {', '.join(preview)}"]

        active.pop(movable_index)
        removed += 1

    return []


def iter_level_paths(levels_path: Path) -> list[Path]:
    if levels_path.is_file():
        return [levels_path]
    return sorted(levels_path.glob("*.json"))


def load_picture_rows(config_path: Path) -> dict[str, list[str]]:
    if not config_path.exists():
        return {}

    config = json.loads(config_path.read_text(encoding="utf-8"))
    return {
        picture.get("id"): picture.get("shapeRows", [])
        for picture in config.get("pictures", [])
        if picture.get("id")
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit ArtOut level JSON for overlaps and bounds errors.")
    parser.add_argument("levels", type=Path, nargs="?", default=PROJECT_ROOT / "Assets/Resources/ArtOut/Levels")
    parser.add_argument("--picture-config", type=Path, default=PROJECT_ROOT / "Assets/Bundles/Main/Json/ArtOutPictureConfig.json")
    args = parser.parse_args()

    bad_count = 0
    level_paths = iter_level_paths(args.levels)
    picture_rows = load_picture_rows(args.picture_config)
    for path in level_paths:
        level = json.loads(path.read_text(encoding="utf-8"))
        errors = audit_level(level, picture_rows.get(level.get("pictureId")))
        if errors:
            bad_count += 1
            print(f"FAIL {path.name}:")
            for error in errors[:12]:
                print(f"  - {error}")
            if len(errors) > 12:
                print(f"  - ... {len(errors) - 12} more")
        else:
            print(f"OK   {path.name}")

    print(f"audited {len(level_paths)} levels, bad {bad_count}")
    return 1 if bad_count else 0


if __name__ == "__main__":
    sys.exit(main())
