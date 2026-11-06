#!/usr/bin/env python3
"""Generate ArtOut level json files from pixel images.

Requires Pillow:
    python -m pip install pillow

Example:
    python generate_artout_levels.py input/music_note.png ^
        --output-levels ../../Assets/Resources/ArtOut/Levels ^
        --output-picture-config ../../Assets/Bundles/Main/Json/ArtOutPictureConfig.json ^
        --picture-id music_note --chapter 0 --levels-per-picture 12
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from artout_shapes import BASIC_SHAPES
from board_splitter import split_board_into_shapes

try:
    from PIL import Image
except ImportError:  # pragma: no cover - exercised by users without Pillow.
    Image = None


SHAPES = BASIC_SHAPES

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PICTURE_TEXTURE_BUNDLE_ROOT = "Main/Textures/ArtOutPictures"


@dataclass(frozen=True)
class Cell:
    filled: bool
    color: tuple[int, int, int]


@dataclass(frozen=True)
class Piece:
    column: int
    row: int
    shape_id: int
    rotation: int
    direction: str
    color: tuple[int, int, int]
    arrow_cell: tuple[int, int]


def normalize(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    values = list(cells)
    min_x = min(x for x, _ in values)
    min_y = min(y for _, y in values)
    return sorted(((x - min_x, y - min_y) for x, y in values), key=lambda item: (item[1], item[0]))


def rotate_clockwise(cells: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return normalize((y, -x) for x, y in cells)


def shape_cells(shape_id: int, rotation: int) -> list[tuple[int, int]]:
    # SHAPES follows Brilliant's (row, column) convention. Runtime C# uses
    # Vector2Int(x=column, y=row), so convert here before placement.
    cells = normalize((column, row) for row, column in SHAPES.get(shape_id, SHAPES[1]))
    for _ in range(rotation % 4):
        cells = rotate_clockwise(cells)
    return cells


def default_arrow_cell(cells: list[tuple[int, int]]) -> tuple[int, int]:
    min_x = min(x for x, _ in cells)
    max_x = max(x for x, _ in cells)
    min_y = min(y for _, y in cells)
    max_y = max(y for _, y in cells)
    center_x = (min_x + max_x) * 0.5
    center_y = (min_y + max_y) * 0.5
    return min(cells, key=lambda cell: (cell[0] - center_x) ** 2 + (cell[1] - center_y) ** 2)


def css_color(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def average_color(colors: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    if not colors:
        return (170, 122, 66)
    return tuple(int(sum(color[i] for color in colors) / len(colors)) for i in range(3))


def sample_image(path: Path, max_width: int, max_height: int, alpha_threshold: int) -> list[list[Cell]]:
    if Image is None:
        raise RuntimeError("Pillow is required. Install it with: python -m pip install pillow")

    image = Image.open(path).convert("RGBA")
    scale = max(1, math.ceil(max(image.width / max_width, image.height / max_height)))
    width = max(1, math.ceil(image.width / scale))
    height = max(1, math.ceil(image.height / scale))
    pixels = image.load()
    rows: list[list[Cell]] = []
    for row in range(height):
        cells: list[Cell] = []
        for column in range(width):
            colors: list[tuple[int, int, int]] = []
            filled = False
            for y in range(row * scale, min(image.height, (row + 1) * scale)):
                for x in range(column * scale, min(image.width, (column + 1) * scale)):
                    r, g, b, a = pixels[x, y]
                    if a >= alpha_threshold:
                        filled = True
                        colors.append((r, g, b))
            cells.append(Cell(filled=filled, color=average_color(colors)))
        rows.append(cells)
    return rows


def shape_rows(grid: list[list[Cell]]) -> list[str]:
    return ["".join("1" if cell.filled else "." for cell in row) for row in grid]


def direction_step(direction: str) -> tuple[int, int]:
    if direction == "Up":
        return (0, 1)
    if direction == "Down":
        return (0, -1)
    if direction == "Left":
        return (-1, 0)
    return (1, 0)


def occupied_cells(piece: Piece) -> set[tuple[int, int]]:
    return {
        (piece.column + x, piece.row + y)
        for x, y in shape_cells(piece.shape_id, piece.rotation)
    }


def can_exit(piece: Piece, direction: str, active: list[Piece], width: int, height: int) -> bool:
    occupancy: dict[tuple[int, int], Piece] = {}
    for active_piece in active:
        for cell in occupied_cells(active_piece):
            occupancy[cell] = active_piece

    step_x, step_y = direction_step(direction)
    for origin_x, origin_y in occupied_cells(piece):
        cursor = (origin_x + step_x, origin_y + step_y)
        while 0 <= cursor[0] < width and 0 <= cursor[1] < height:
            blocker = occupancy.get(cursor)
            if blocker is not None and blocker is not piece:
                return False
            cursor = (cursor[0] + step_x, cursor[1] + step_y)
    return True


def choose_direction(column: int, row: int, cells: list[tuple[int, int]], width: int, height: int, rng: random.Random) -> str:
    min_x = min(column + x for x, _ in cells)
    max_x = max(column + x for x, _ in cells)
    min_y = min(row + y for _, y in cells)
    max_y = max(row + y for _, y in cells)
    options = [
        ("Left", min_x),
        ("Right", width - 1 - max_x),
        ("Down", min_y),
        ("Up", height - 1 - max_y),
    ]
    best_distance = min(distance for _, distance in options)
    best = [name for name, distance in options if distance == best_distance]
    return rng.choice(best)


def assign_solvable_directions(pieces: list[Piece], width: int, height: int, rng: random.Random) -> list[Piece]:
    active = pieces[:]
    directions: dict[Piece, str] = {}
    while active:
        candidates: list[tuple[int, int, Piece, str]] = []
        for index, piece in enumerate(active):
            cells = shape_cells(piece.shape_id, piece.rotation)
            direction_order = ["Left", "Right", "Down", "Up"]
            rng.shuffle(direction_order)
            for direction in direction_order:
                if not can_exit(piece, direction, active, width, height):
                    continue

                min_x = min(piece.column + x for x, _ in cells)
                max_x = max(piece.column + x for x, _ in cells)
                min_y = min(piece.row + y for _, y in cells)
                max_y = max(piece.row + y for _, y in cells)
                distance = {
                    "Left": min_x,
                    "Right": width - 1 - max_x,
                    "Down": min_y,
                    "Up": height - 1 - max_y,
                }[direction]
                candidates.append((distance, index, piece, direction))

        if not candidates:
            raise ValueError("generated layout has no removable piece; try smaller shapes or a different seed")

        candidates.sort(key=lambda item: (item[0], item[1]))
        _, _, selected, direction = candidates[0]
        directions[selected] = direction
        active.remove(selected)

    return [
        Piece(
            column=piece.column,
            row=piece.row,
            shape_id=piece.shape_id,
            rotation=piece.rotation,
            direction=directions[piece],
            color=piece.color,
            arrow_cell=piece.arrow_cell,
        )
        for piece in pieces
    ]


def cover_grid(grid: list[list[Cell]], seed: int) -> list[Piece]:
    rng = random.Random(seed)
    height = len(grid)
    width = len(grid[0]) if height else 0
    valid_cells = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column].filled
    }
    board_colors = [
        [grid[row][column].color for column in range(width)]
        for row in range(height)
    ]
    blocks, _ = split_board_into_shapes(board_colors, valid_cells, seed)

    pieces: list[Piece] = []
    for block in blocks:
        min_row = min(row for row, _ in block.cells)
        min_column = min(column for _, column in block.cells)
        colors = [grid[row][column].color for row, column in block.cells]
        cells = shape_cells(block.shape_id, 0)
        pieces.append(
            Piece(
                column=min_column,
                row=min_row,
                shape_id=block.shape_id,
                rotation=0,
                direction=choose_direction(min_column, min_row, cells, width, height, rng),
                color=average_color(colors),
                arrow_cell=default_arrow_cell(cells),
            )
        )

    return assign_solvable_directions(pieces, width, height, rng)


def build_level(
    picture_id: str,
    display_name: str,
    chapter: int,
    level_in_chapter: int,
    grid: list[list[Cell]],
    pieces: list[Piece],
    data_version: int,
) -> dict:
    return {
        "id": f"{picture_id}_{level_in_chapter + 1:03d}",
        "displayName": f"{display_name} {level_in_chapter + 1:03d}",
        "pictureId": picture_id,
        "dataVersion": data_version,
        "chapter": chapter,
        "levelInChapter": level_in_chapter,
        "width": len(grid[0]) if grid else 1,
        "height": len(grid),
        "rewardCoins": 25 + level_in_chapter * 5,
        "pieces": [
            {
                "column": piece.column,
                "row": piece.row,
                "shapeId": piece.shape_id,
                "direction": piece.direction,
                "color": css_color(piece.color),
                "arrowCell": {"x": piece.arrow_cell[0], "y": piece.arrow_cell[1]},
            }
            for piece in pieces
        ],
    }


def validate_level(level: dict) -> None:
    width = max(1, int(level.get("width", 1)))
    height = max(1, int(level.get("height", 1)))
    occupied: dict[tuple[int, int], int] = {}
    for index, piece in enumerate(level.get("pieces", [])):
        column = max(0, int(piece.get("column", 0)))
        row = max(0, int(piece.get("row", 0)))
        shape_id = max(1, min(max(SHAPES), int(piece.get("shapeId", 1))))
        rotation = int(piece.get("rotation", 0)) % 4
        if rotation != 0:
            raise ValueError(f"{level['id']} piece {index} rotation must be 0; use the matching shapeId orientation instead")

        for x, y in shape_cells(shape_id, rotation):
            cell = (column + x, row + y)
            if cell[0] < 0 or cell[1] < 0 or cell[0] >= width or cell[1] >= height:
                raise ValueError(f"{level['id']} piece {index} out of bounds at {cell}")
            if cell in occupied:
                raise ValueError(f"{level['id']} piece {index} overlaps piece {occupied[cell]} at {cell}")
            occupied[cell] = index


def write_picture_texture(grid: list[list[Cell]], texture_root: Path, picture_id: str) -> tuple[str, str]:
    if Image is None:
        raise RuntimeError("Pillow is required. Install it with: python -m pip install pillow")

    asset_name = f"{picture_id}.png"
    texture_root.mkdir(parents=True, exist_ok=True)
    width = max(1, len(grid[0]) if grid else 1)
    height = max(1, len(grid))
    image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    for row, cells in enumerate(grid):
        for column, cell in enumerate(cells):
            r, g, b = cell.color
            image.putpixel((column, row), (r, g, b, 255 if cell.filled else 0))

    image.save(texture_root / asset_name)
    return asset_name, f"{PICTURE_TEXTURE_BUNDLE_ROOT}/{asset_name}"


def update_picture_config(
    config_path: Path,
    picture_id: str,
    display_name: str,
    rows: list[str],
    alpha_threshold: float,
    source_image: str,
    texture_path: str,
    shape_image: str | None,
    preview_image: str | None,
    complete_image: str | None,
) -> None:
    config = {"pictures": []}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
    pictures = config.setdefault("pictures", [])
    pictures = [picture for picture in pictures if picture.get("id") != picture_id]
    pictures.append(
        {
            "id": picture_id,
            "name": display_name,
            "texturePath": texture_path,
            "sourceImage": source_image,
            "shapeImage": shape_image or source_image,
            "previewImage": preview_image or source_image,
            "completeImage": complete_image or source_image,
            "shapeRows": rows,
            "alphaThreshold": alpha_threshold,
        }
    )
    config["pictures"] = pictures
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ArtOut json levels from a pixel image.")
    parser.add_argument("image", type=Path)
    parser.add_argument("--output-levels", type=Path, default=PROJECT_ROOT / "Assets/Resources/ArtOut/Levels")
    parser.add_argument("--output-picture-config", type=Path, default=PROJECT_ROOT / "Assets/Bundles/Main/Json/ArtOutPictureConfig.json")
    parser.add_argument("--output-picture-textures", type=Path, default=PROJECT_ROOT / "Assets/Bundles/Main/Textures/ArtOutPictures")
    parser.add_argument("--picture-id", required=True)
    parser.add_argument("--display-name")
    parser.add_argument("--shape-image", help="Home grid shape image file name, for example Collections_01_shape.png.")
    parser.add_argument("--preview-image", help="Collection preview image file name, for example Collections_01.png.")
    parser.add_argument("--complete-image", help="Post-win complete image file name. Defaults to the generated source image.")
    parser.add_argument("--chapter", type=int, default=0)
    parser.add_argument("--levels-per-picture", type=int, default=1)
    parser.add_argument("--max-width", type=int, default=12)
    parser.add_argument("--max-height", type=int, default=14)
    parser.add_argument("--alpha-threshold", type=int, default=32)
    parser.add_argument("--data-version", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args()

    display_name = args.display_name or args.picture_id.replace("_", " ").title()
    grid = sample_image(args.image, args.max_width, args.max_height, args.alpha_threshold)
    rows = shape_rows(grid)
    source_image, texture_path = write_picture_texture(grid, args.output_picture_textures, args.picture_id)
    args.output_levels.mkdir(parents=True, exist_ok=True)
    for index in range(max(1, args.levels_per_picture)):
        pieces = cover_grid(grid, args.seed + index)
        level = build_level(args.picture_id, display_name, args.chapter, index, grid, pieces, args.data_version)
        validate_level(level)
        output_path = args.output_levels / f"{level['id']}.json"
        output_path.write_text(json.dumps(level, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {output_path} ({len(pieces)} pieces)")

    update_picture_config(
        args.output_picture_config,
        args.picture_id,
        display_name,
        rows,
        max(0.0, min(1.0, args.alpha_threshold / 255.0)),
        source_image,
        texture_path,
        args.shape_image,
        args.preview_image,
        args.complete_image,
    )
    print(f"updated {args.output_picture_config}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

