from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Iterable

from artout_shapes import get_shape_id, get_shape_id_and_rotation, get_shuffled_shapes_by_area_desc, normalize_shape


Color = tuple[int, int, int]
CellCoord = tuple[int, int]  # row, column


@dataclass
class SplitBlock:
    block_id: int
    cells: list[CellCoord]
    color: Color
    area: int
    shape_id: int
    rotation: int


@dataclass
class ShapeCandidate:
    cells: list[CellCoord]
    shape_id: int
    rotation: int
    area: int
    score: float = 0.0


class BoardSplitter:
    DIRECTIONS_4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    DIVERSITY_CHECK_RADIUS = 2
    SAME_SHAPE_PENALTY = -500
    AREA_BONUS_WEIGHT = 15
    BOUNDARY_BONUS_WEIGHT = 3
    TOP_CANDIDATES_COUNT = 2

    def __init__(self, board_colors: list[list[Color]], valid_cells: Iterable[CellCoord], seed: int = 0):
        self.board_colors = board_colors
        self.valid_cells = set(valid_cells)
        self.height = len(board_colors)
        self.width = len(board_colors[0]) if board_colors else 0
        self.rng = random.Random(seed)
        self.blocks: list[SplitBlock] = []
        self.assigned: set[CellCoord] = set()
        self.shape_id_of_block: dict[int, int] = {}
        self.block_at_cell: dict[CellCoord, int] = {}
        self.color_of_block: dict[int, Color] = {}

    def split(self) -> list[SplitBlock]:
        block_id = 0
        for region in self._get_color_regions():
            color = region["color"]
            region_cells = set(region["cells"])
            remaining = set(region_cells)

            while remaining:
                anchor = min(remaining)
                candidates = self._get_candidate_shapes(anchor, remaining)
                if not candidates:
                    candidates = [self._single_cell_candidate(anchor)]

                for candidate in candidates:
                    candidate.score = self._calculate_shape_score(candidate, remaining, region_cells, color)

                candidates.sort(key=lambda item: item.score, reverse=True)
                filtered = [
                    candidate
                    for candidate in candidates[: self.TOP_CANDIDATES_COUNT]
                    if candidate.score > self.SAME_SHAPE_PENALTY
                ]
                chosen = self.rng.choice(filtered) if filtered else candidates[0]
                self._add_block(block_id, chosen.cells, color, chosen.shape_id, chosen.rotation)

                for cell in chosen.cells:
                    remaining.discard(cell)
                    self.assigned.add(cell)
                    self.block_at_cell[cell] = block_id

                block_id += 1

        self._post_process_merge()
        self.blocks.sort(key=lambda item: min(item.cells))
        return self.blocks

    def get_coverage_stats(self) -> dict:
        shape_usage: dict[int, int] = {}
        for block in self.blocks:
            shape_usage[block.area] = shape_usage.get(block.area, 0) + 1

        return {
            "total_cells": len(self.valid_cells),
            "covered_cells": len(self.assigned),
            "coverage_rate": len(self.assigned) / len(self.valid_cells) if self.valid_cells else 0,
            "block_count": len(self.blocks),
            "shape_usage": shape_usage,
        }

    def _get_color_regions(self) -> list[dict]:
        visited: set[CellCoord] = set()
        regions: list[dict] = []

        for row in range(self.height):
            for column in range(self.width):
                cell = (row, column)
                if cell not in self.valid_cells or cell in visited:
                    continue

                color = self.board_colors[row][column]
                cells: list[CellCoord] = []
                queue = deque([cell])
                visited.add(cell)

                while queue:
                    current = queue.popleft()
                    cells.append(current)
                    for delta_row, delta_col in self.DIRECTIONS_4:
                        neighbor = (current[0] + delta_row, current[1] + delta_col)
                        if not self._is_unvisited_same_color(neighbor, color, visited):
                            continue
                        visited.add(neighbor)
                        queue.append(neighbor)

                regions.append({"color": color, "cells": cells})

        return regions

    def _is_unvisited_same_color(self, cell: CellCoord, color: Color, visited: set[CellCoord]) -> bool:
        row, column = cell
        return (
            0 <= row < self.height
            and 0 <= column < self.width
            and cell in self.valid_cells
            and cell not in visited
            and self.board_colors[row][column] == color
        )

    def _get_candidate_shapes(self, anchor: CellCoord, available: set[CellCoord]) -> list[ShapeCandidate]:
        candidates: list[ShapeCandidate] = []
        anchor_row, anchor_col = anchor
        for area, variants in get_shuffled_shapes_by_area_desc(self.rng):
            if area > len(available):
                continue

            for variant in variants:
                cells = [(anchor_row + row, anchor_col + column) for row, column in variant]
                if all(cell in available for cell in cells):
                    shape_id, rotation = get_shape_id_and_rotation(variant)
                    if shape_id <= 0:
                        continue

                    candidates.append(ShapeCandidate(cells=cells, shape_id=shape_id, rotation=rotation, area=area))

        return candidates

    def _single_cell_candidate(self, anchor: CellCoord) -> ShapeCandidate:
        return ShapeCandidate(cells=[anchor], shape_id=1, rotation=0, area=1)

    def _calculate_shape_score(
        self,
        candidate: ShapeCandidate,
        available: set[CellCoord],
        region_cells: set[CellCoord],
        color: Color,
    ) -> float:
        score = candidate.area * self.AREA_BONUS_WEIGHT
        score += self._calculate_boundary_bonus(candidate.cells, available, region_cells) * self.BOUNDARY_BONUS_WEIGHT
        same_shape_count = self._count_nearby_same_shape(candidate.shape_id, candidate.cells, color)
        score += self.SAME_SHAPE_PENALTY * same_shape_count
        return score

    def _calculate_boundary_bonus(
        self,
        cells: list[CellCoord],
        available: set[CellCoord],
        region_cells: set[CellCoord],
    ) -> int:
        cell_set = set(cells)
        bonus = 0
        for row, column in cells:
            for delta_row, delta_col in self.DIRECTIONS_4:
                neighbor = (row + delta_row, column + delta_col)
                if neighbor not in region_cells:
                    bonus += 1
                elif neighbor not in available and neighbor not in cell_set:
                    bonus += 1
        return bonus

    def _count_nearby_same_shape(self, shape_id: int, cells: list[CellCoord], color: Color) -> int:
        count = 0
        checked: set[CellCoord] = set()
        for row, column in cells:
            for delta_row in range(-self.DIVERSITY_CHECK_RADIUS, self.DIVERSITY_CHECK_RADIUS + 1):
                for delta_col in range(-self.DIVERSITY_CHECK_RADIUS, self.DIVERSITY_CHECK_RADIUS + 1):
                    if delta_row == 0 and delta_col == 0:
                        continue

                    neighbor = (row + delta_row, column + delta_col)
                    if neighbor in checked:
                        continue
                    checked.add(neighbor)

                    block_id = self.block_at_cell.get(neighbor)
                    if block_id is None:
                        continue
                    if self.shape_id_of_block.get(block_id) == shape_id and self.color_of_block.get(block_id) == color:
                        count += 1

        return count

    def _add_block(self, block_id: int, cells: list[CellCoord], color: Color, shape_id: int, rotation: int) -> None:
        block = SplitBlock(
            block_id=block_id,
            cells=list(cells),
            color=color,
            area=len(cells),
            shape_id=shape_id,
            rotation=rotation,
        )
        self.blocks.append(block)
        self.shape_id_of_block[block_id] = shape_id
        self.color_of_block[block_id] = color

    def _post_process_merge(self) -> None:
        for _ in range(500):
            merged = False
            small_blocks = [block for block in self.blocks if block.area <= 2]
            for block in small_blocks:
                if merged:
                    break
                for other in list(self.blocks):
                    if block.block_id == other.block_id or block.color != other.color:
                        continue
                    if not self._are_adjacent(block.cells, other.cells):
                        continue

                    combined = block.cells + other.cells
                    local = normalize_shape(combined)
                    shape_id, rotation = get_shape_id_and_rotation(local)
                    if shape_id <= 0:
                        continue

                    if self._is_merge_diverse(shape_id, combined, block.color) or (block.area == 1 and other.area == 1):
                        block.cells = combined
                        block.area = len(combined)
                        block.shape_id = shape_id
                        block.rotation = rotation
                        self.shape_id_of_block[block.block_id] = shape_id
                        for cell in other.cells:
                            self.block_at_cell[cell] = block.block_id
                        self.blocks.remove(other)
                        self.shape_id_of_block.pop(other.block_id, None)
                        self.color_of_block.pop(other.block_id, None)
                        merged = True
                        break

            if not merged:
                break

    def _are_adjacent(self, left: list[CellCoord], right: list[CellCoord]) -> bool:
        right_set = set(right)
        for row, column in left:
            for delta_row, delta_col in self.DIRECTIONS_4:
                if (row + delta_row, column + delta_col) in right_set:
                    return True
        return False

    def _is_merge_diverse(self, shape_id: int, cells: list[CellCoord], color: Color) -> bool:
        cell_set = set(cells)
        checked: set[CellCoord] = set()
        for row, column in cells:
            for delta_row in range(-self.DIVERSITY_CHECK_RADIUS, self.DIVERSITY_CHECK_RADIUS + 1):
                for delta_col in range(-self.DIVERSITY_CHECK_RADIUS, self.DIVERSITY_CHECK_RADIUS + 1):
                    if delta_row == 0 and delta_col == 0:
                        continue

                    neighbor = (row + delta_row, column + delta_col)
                    if neighbor in checked or neighbor in cell_set:
                        continue
                    checked.add(neighbor)

                    block_id = self.block_at_cell.get(neighbor)
                    if block_id is None:
                        continue
                    if self.shape_id_of_block.get(block_id) == shape_id and self.color_of_block.get(block_id) == color:
                        return False
        return True


def split_board_into_shapes(
    board_colors: list[list[Color]],
    valid_cells: Iterable[CellCoord],
    seed: int = 0,
) -> tuple[list[SplitBlock], dict]:
    splitter = BoardSplitter(board_colors, valid_cells, seed)
    blocks = splitter.split()
    return blocks, splitter.get_coverage_stats()
