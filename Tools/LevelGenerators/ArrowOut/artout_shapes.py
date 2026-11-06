from __future__ import annotations

import random
from typing import Iterable


BASIC_SHAPES: dict[int, list[tuple[int, int]]] = {
    1: [(0, 0)],
    2: [(0, 0), (0, 1)],
    3: [(0, 0), (1, 0)],
    4: [(0, 0), (1, 0), (1, 1)],
    5: [(0, 0), (0, 1), (1, 0)],
    6: [(0, 0), (0, 1), (0, 2)],
    7: [(0, 0), (1, 0), (2, 0)],
    8: [(0, 0), (0, 1), (0, 2), (0, 3)],
    9: [(0, 0), (1, 0), (2, 0), (3, 0)],
    10: [(0, 0), (0, 1), (1, 0), (1, 1)],
    11: [(0, 1), (1, 0), (1, 1), (1, 2)],
    12: [(0, 1), (1, 0), (1, 1), (2, 1)],
    13: [(0, 0), (0, 1), (0, 2), (1, 1)],
    14: [(0, 1), (0, 2), (1, 0), (1, 1)],
    15: [(0, 1), (1, 0), (1, 1), (2, 0)],
    16: [(0, 1), (1, 1), (2, 0), (2, 1)],
    17: [(0, 0), (0, 1), (1, 1), (2, 1)],
    18: [(0, 2), (1, 0), (1, 1), (1, 2)],
    19: [(0, 0), (0, 1), (0, 2), (1, 2)],
    20: [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    21: [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2)],
    22: [(0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
    23: [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0)],
    24: [(0, 0), (0, 1), (1, 1), (2, 1)],
    25: [(0, 0), (0, 1), (0, 2), (1, 1), (1, 2)],
    26: [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
    27: [(0, 0), (0, 1), (1, 1), (2, 0), (2, 1)],
    28: [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2)],
    29: [(0, 2), (1, 0), (1, 1), (1, 2), (2, 0)],
    30: [(0, 1), (0, 2), (1, 1), (2, 0), (2, 1)],
}


def normalize_shape(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    values = list(cells)
    if not values:
        return []

    min_row = min(row for row, _ in values)
    min_col = min(column for _, column in values)
    return sorted((row - min_row, column - min_col) for row, column in values)


def rotate_shape_clockwise(cells: Iterable[tuple[int, int]]) -> list[tuple[int, int]]:
    return normalize_shape((column, -row) for row, column in cells)


def unique_rotations(cells: Iterable[tuple[int, int]]) -> list[list[tuple[int, int]]]:
    rotations: list[list[tuple[int, int]]] = []
    current = normalize_shape(cells)
    for _ in range(4):
        if current not in rotations:
            rotations.append(current)
        current = rotate_shape_clockwise(current)
    return rotations


SHAPES_BY_AREA: dict[int, list[list[tuple[int, int]]]] = {}
SHAPE_ID_MAP: dict[tuple[tuple[int, int], ...], int] = {}
SHAPE_ROTATION_MAP: dict[tuple[tuple[int, int], ...], tuple[int, int]] = {}

for shape_id, base_cells in BASIC_SHAPES.items():
    shape = normalize_shape(base_cells)
    SHAPES_BY_AREA.setdefault(len(shape), []).append(shape)
    key = tuple(shape)
    SHAPE_ID_MAP[key] = shape_id
    SHAPE_ROTATION_MAP[key] = (shape_id, 0)


def get_shape_id(cells: Iterable[tuple[int, int]]) -> int:
    return SHAPE_ID_MAP.get(tuple(normalize_shape(cells)), 0)


def get_shape_id_and_rotation(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    return SHAPE_ROTATION_MAP.get(tuple(normalize_shape(cells)), (0, 0))


def get_shuffled_shapes_by_area_desc(rng: random.Random) -> list[tuple[int, list[list[tuple[int, int]]]]]:
    result: list[tuple[int, list[list[tuple[int, int]]]]] = []
    for area in sorted(SHAPES_BY_AREA.keys(), reverse=True):
        variants = list(SHAPES_BY_AREA[area])
        rng.shuffle(variants)
        result.append((area, variants))
    return result
