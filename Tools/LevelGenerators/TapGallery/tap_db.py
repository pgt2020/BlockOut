import numpy as np
import random
import math
import time
import os
import glob
import argparse
from PIL import Image

# --- Constants ---
# Directions: 0: Up, 1: Right, 2: Down, 3: Left
UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3
DIRECTIONS = [UP, RIGHT, DOWN, LEFT]
# Delta for row, col changes corresponding to directions
DELTAS = {UP: (-1, 0), RIGHT: (0, 1), DOWN: (1, 0), LEFT: (0, -1)}
# Arrow characters for printing
ARROWS = {UP: "↑", RIGHT: "→", DOWN: "↓", LEFT: "←"}


class ArrowPuzzleSolver:
    """
    Solves the arrow puzzle by assigning directions to blocks to maximize complexity
    while ensuring solvability and avoiding undesirable patterns.
    Uses a Simulated Annealing approach with incremental updates for performance.
    """

    def __init__(self, grid, verbose=False, debug=False):
        """
        Initializes the solver with a given grid.
        :param grid: A 2D list or numpy array where 1 represents a block and 0 is empty space.
        :param verbose: If True, prints detailed logs for each step.
        :param debug: If True, prints detailed board information during progress reports.
        """
        if not isinstance(grid, np.ndarray):
            grid = np.array(grid, dtype=int)

        if grid.sum() == 0:
            raise ValueError("Input grid cannot be empty.")

        self.grid = grid
        self.rows, self.cols = grid.shape
        self.block_coords = list(zip(*np.where(self.grid == 1)))
        self.num_blocks = len(self.block_coords)
        self.verbose = verbose
        self.debug = debug

        # --- Dynamically Maintained State (from tap2.py optimization) ---
        self.p_value_cache = {}
        self.forward_graph = {}
        self.reverse_graph = {}

        # --- Solver state ---
        self.directions = np.full(self.grid.shape, -1, dtype=int)
        self.p_values = np.full(self.grid.shape, -1, dtype=int)

        # --- Best solution found ---
        self.best_directions = None
        self.best_score = -float("inf")
        self.best_p_values = None

    def solve(
        self, iterations=5000, initial_temp=10.0, cooling_rate=0.9998, debug=None
    ):
        """
        Main function to run the optimization algorithm.
        Uses the optimized approach from tap2.py with incremental updates.
        :param iterations: Number of iterations for the simulation.
        :param initial_temp: Starting temperature for simulated annealing.
        :param cooling_rate: Rate at which temperature decreases.
        :param debug: If specified, overrides the instance debug setting for this solve.
        :return: A tuple of (best_directions, best_p_values).
        """
        # Use debug parameter if provided, otherwise use instance setting
        use_debug = debug if debug is not None else self.debug

        print(
            f"Starting solver for a {self.rows}x{self.cols} grid with {self.num_blocks} blocks."
        )
        if use_debug:
            print("🐛 调试模式已启用 - 将显示详细的阶段性盘面信息")
        start_time = time.time()

        # 1. Generate a robust initial solution
        current_directions = self._generate_initial_solution()
        if current_directions is None:
            print("Error: Failed to generate an initial solvable solution.")
            return None, None

        # 2. Initialize all data structures for the main loop
        self._build_graphs(current_directions)
        self.p_value_cache = {}
        current_p_values = self._calculate_all_p_values(current_directions)
        current_score = self._calculate_score(current_directions, current_p_values)
        print(f"Initial solution generated with score: {current_score:.2f}")

        self.best_directions = current_directions.copy()
        self.best_p_values = current_p_values.copy()
        self.best_score = current_score

        temp = initial_temp

        # --- For printing intermediate solutions ---
        stages = [int(iterations * p) for p in [0.25, 0.50, 0.75, 1.0]]
        stage_idx = 0

        # 3. [EXTREME OPTIMIZATION] Main Simulated Annealing Loop
        for i in range(iterations):
            if i > 0 and i % 1000 == 0:
                print(
                    f"Iteration {i}/{iterations}... Best Score: {self.best_score:.2f}, Temp: {temp:.4f}"
                )
                # 打印当前最佳分配方案
                self._print_current_solution()

            # --- Step 1: Propose a change ---
            r, c = random.choice(self.block_coords)
            old_dir = current_directions[r, c]
            new_dir = random.choice([d for d in DIRECTIONS if d != old_dir])

            # --- Step 2: Ultra-fast incremental cycle check ---
            new_direct_deps = self._get_direct_deps_from_path((r, c), new_dir)
            is_cyclic = False
            for dep_coord in new_direct_deps:
                deps_of_new_target = self._get_dependency_set(
                    dep_coord, self.forward_graph, self.p_value_cache, set()
                )
                if (r, c) in deps_of_new_target:
                    is_cyclic = True
                    break
            if is_cyclic:
                continue  # Reject change immediately, no further computation needed

            # --- Step 3: Transactional Update ---
            # Create backups to enable rollback
            original_p_values = current_p_values.copy()

            # A. Incrementally update graphs
            old_direct_deps = self.forward_graph.get((r, c), [])
            self._update_graphs_incrementally((r, c), old_direct_deps, new_direct_deps)

            # B. Find all affected nodes ('dirty' nodes)
            dirty_nodes = self._get_dirty_nodes(
                (r, c), old_direct_deps, new_direct_deps
            )

            # C. Invalidate cache and re-calculate P-values for dirty nodes
            for node in dirty_nodes:
                if node in self.p_value_cache:
                    del self.p_value_cache[node]
            for node_r, node_c in dirty_nodes:
                current_p_values[node_r, node_c] = len(
                    self._get_dependency_set(
                        (node_r, node_c), self.forward_graph, self.p_value_cache, set()
                    )
                )

            # D. Update directions and calculate new score
            current_directions[r, c] = new_dir
            new_score = self._calculate_score(current_directions, current_p_values)

            # --- Step 4: Accept or Reject ---
            delta_score = new_score - current_score
            if delta_score > 0 or (
                temp > 0 and random.random() < math.exp(delta_score / temp)
            ):
                # Accept: Keep all changes
                current_score = new_score
                if current_score > self.best_score:
                    self.best_score = current_score
                    self.best_directions = current_directions.copy()
                    self.best_p_values = current_p_values.copy()
            else:
                # Reject: Rollback all changes
                self._update_graphs_incrementally(
                    (r, c), new_direct_deps, old_direct_deps
                )  # Revert graph
                current_directions[r, c] = old_dir  # Revert direction
                current_p_values = original_p_values  # Revert P-values
                self.p_value_cache = {}  # Clear cache as it's now inconsistent

            temp *= cooling_rate

            # --- Print stage solution ---
            while stage_idx < len(stages) and i >= stages[stage_idx] - 1:
                progress_percent = int(stages[stage_idx] / iterations * 100)

                if use_debug:
                    # 调试模式：显示详细信息和盘面
                    print("\n" + "=" * 60)
                    print(
                        f"🐛 调试进度报告 - {progress_percent}% 完成 (第 {i+1}/{iterations} 次迭代)"
                    )
                    print("=" * 60)
                    print(f"当前最佳得分: {self.best_score:.3f}")
                    print(f"当前温度: {temp:.6f}")
                    if self.best_p_values is not None:
                        avg_p = self.best_p_values[self.grid == 1].mean()
                        print(f"平均P值: {avg_p:.3f}")
                    print("-" * 60)
                    self.print_solution(is_final=False)
                    print("=" * 60)
                else:
                    # 非调试模式：仅显示基本统计信息
                    if self.best_p_values is not None:
                        avg_p = self.best_p_values[self.grid == 1].mean()
                    else:
                        avg_p = 0

                    # 显示方向分布统计
                    if self.best_directions is not None:
                        direction_counts = np.bincount(
                            self.best_directions[self.grid == 1], minlength=4
                        )
                        direction_names = ["↑", "→", "↓", "←"]
                        direction_dist = " | ".join(
                            [
                                f"{symbol}:{count}({count/self.num_blocks*100:.1f}%)"
                                for symbol, count in zip(
                                    direction_names, direction_counts
                                )
                            ]
                        )
                    else:
                        direction_dist = "未知"

                    print(
                        f"📊 进度 {progress_percent}%: 得分={self.best_score:.3f} | 平均P值={avg_p:.1f} | 温度={temp:.4f}"
                    )
                    print(f"   方向分布: {direction_dist}")

                stage_idx += 1

        end_time = time.time()
        print(f"\nSolver finished in {end_time - start_time:.2f} seconds.")
        print("\n" + "=" * 20 + " FINAL SOLUTION " + "=" * 20)
        self.directions = self.best_directions
        self.p_values = self.best_p_values
        self.print_solution(is_final=True)
        return self.best_directions, self.best_p_values

    # --- Graph and State Management Helpers (from tap2.py optimization) ---
    def _build_graphs(self, directions):
        """Builds the forward and reverse dependency graphs from scratch."""
        self.forward_graph = {coord: [] for coord in self.block_coords}
        self.reverse_graph = {coord: [] for coord in self.block_coords}
        for r, c in self.block_coords:
            direct_deps = self._get_direct_deps_from_path((r, c), directions[r, c])
            self.forward_graph[(r, c)] = direct_deps
            for dep_coord in direct_deps:
                self.reverse_graph[dep_coord].append((r, c))

    def _update_graphs_incrementally(self, source_node, old_deps, new_deps):
        """Incrementally updates graph edges."""
        self.forward_graph[source_node] = new_deps
        for dep in old_deps:
            self.reverse_graph[dep].remove(source_node)
        for dep in new_deps:
            self.reverse_graph[dep].append(source_node)

    def _get_direct_deps_from_path(self, source_coord, direction):
        """Traces a path and returns all blocks on it."""
        deps = []
        r, c = source_coord
        dr, dc = DELTAS[direction]
        nr, nc = r + dr, c + dc
        while 0 <= nr < self.rows and 0 <= nc < self.cols:
            if self.grid[nr, nc] == 1:
                deps.append((nr, nc))
            nr, nc = nr + dr, nc + dc
        return deps

    def _get_dirty_nodes(self, changed_node, old_deps, new_deps):
        """Finds all nodes whose P-values are affected by a change."""
        q = [changed_node]
        visited = {changed_node}

        # Start search from all old and new dependencies as well
        for dep in old_deps:
            if dep not in visited:
                q.append(dep)
                visited.add(dep)
        for dep in new_deps:
            if dep not in visited:
                q.append(dep)
                visited.add(dep)

        # BFS on the reverse graph to find all ancestors
        head = 0
        while head < len(q):
            curr = q[head]
            head += 1
            for parent in self.reverse_graph.get(curr, []):
                if parent not in visited:
                    visited.add(parent)
                    q.append(parent)
        return visited

    # --- Core Calculation and Logic Helpers (optimized from tap2.py) ---
    def _calculate_all_p_values(self, directions):
        """Calculates P-values for all blocks from scratch."""
        p_values = np.full(self.grid.shape, -1, dtype=int)
        for r, c in self.block_coords:
            p_values[r, c] = len(
                self._get_dependency_set(
                    (r, c), self.forward_graph, self.p_value_cache, set()
                )
            )
        return p_values

    def _get_dependency_set(self, block_coord, forward_graph, cache, recursion_path):
        """Recursively finds all dependencies for a block using the graph."""
        if block_coord in cache:
            return cache[block_coord]
        if block_coord in recursion_path:
            return set()

        new_recursion_path = recursion_path | {block_coord}
        all_dependencies = set()

        direct_dependencies = forward_graph.get(block_coord, [])
        all_dependencies.update(direct_dependencies)

        for dep_coord in direct_dependencies:
            indirect_deps = self._get_dependency_set(
                dep_coord, forward_graph, cache, new_recursion_path
            )
            all_dependencies.update(indirect_deps)

        cache[block_coord] = all_dependencies
        return all_dependencies

    def _calculate_score(self, directions, p_values):
        """Calculates the total score of a solution."""
        active_p_values = p_values[self.grid == 1]
        avg_p_score = active_p_values.mean() if active_p_values.size > 0 else 0
        penalty = 0

        # Penalties for undesirable patterns
        for r in range(self.rows):
            for c in range(self.cols - 2):
                if (
                    self.grid[r, c] == 1
                    and self.grid[r, c + 1] == 1
                    and self.grid[r, c + 2] == 1
                    and directions[r, c] == directions[r, c + 1] == directions[r, c + 2]
                ):
                    penalty += 0.5
        for c in range(self.cols):
            for r in range(self.rows - 2):
                if (
                    self.grid[r, c] == 1
                    and self.grid[r + 1, c] == 1
                    and self.grid[r + 2, c] == 1
                    and directions[r, c] == directions[r + 1, c] == directions[r + 2, c]
                ):
                    penalty += 0.5

        edge_penalty = 0
        if self.rows > 1:
            edge_penalty += np.sum((directions[0, :] == UP) & (self.grid[0, :] == 1))
            edge_penalty += np.sum(
                (directions[self.rows - 1, :] == DOWN)
                & (self.grid[self.rows - 1, :] == 1)
            )
        if self.cols > 1:
            edge_penalty += np.sum((directions[:, 0] == LEFT) & (self.grid[:, 0] == 1))
            edge_penalty += np.sum(
                (directions[:, self.cols - 1] == RIGHT)
                & (self.grid[:, self.cols - 1] == 1)
            )
        penalty += edge_penalty * 0.2

        dir_counts = np.bincount(directions[self.grid == 1], minlength=4)
        if self.num_blocks > 0:
            max_proportion = np.max(dir_counts) / self.num_blocks
            if max_proportion > 0.6:
                penalty += (max_proportion - 0.6) * 5

        return avg_p_score - penalty

    def _generate_initial_solution(self):
        """Generates a guaranteed solvable initial solution."""
        print("Generating a robust initial solution...")
        directions = np.full(self.grid.shape, -1, dtype=int)
        temp_grid = self.grid.copy()
        unassigned_coords = self.block_coords[:]
        for _ in range(self.num_blocks):
            clearable_blocks = [
                (
                    (r, c),
                    [
                        d
                        for d in DIRECTIONS
                        if self._is_path_clear((r, c), d, temp_grid)
                    ],
                )
                for r, c in unassigned_coords
            ]
            clearable_blocks = [item for item in clearable_blocks if item[1]]
            if not clearable_blocks:
                return None
            (r, c), clear_dirs = random.choice(clearable_blocks)
            directions[r, c] = random.choice(clear_dirs)
            temp_grid[r, c] = 0
            unassigned_coords.remove((r, c))
        return directions

    def _is_path_clear(self, source_coord, direction, grid):
        """Utility to check if a path is clear on a given grid."""
        r, c = source_coord
        dr, dc = DELTAS[direction]
        nr, nc = r + dr, c + dc
        while 0 <= nr < self.rows and 0 <= nc < self.cols:
            if grid[nr, nc] == 1:
                return False
            nr, nc = nr + dr, nc + dc
        return True

    def _print_current_solution(self):
        """
        打印当前最佳分配方案的简化版本
        """
        if self.best_directions is None:
            print("No current solution available.")
            return

        # 计算平均P值
        avg_p = (
            self.best_p_values[self.grid == 1].mean()
            if self.best_p_values is not None
            else 0
        )
        print(
            f"Current Best - Score: {self.best_score:.2f}, Average P-value: {avg_p:.2f}"
        )

        # 只对较小的网格显示完整方案，大网格只显示统计信息
        if self.rows <= 20 and self.cols <= 20:
            print("--- Current Best Arrows ---")
            for r in range(self.rows):
                print(
                    " ".join(
                        [
                            (
                                ARROWS[self.best_directions[r, c]]
                                if self.grid[r, c]
                                else "·"
                            )
                            for c in range(self.cols)
                        ]
                    )
                )
        else:
            # 对大网格显示方向分布统计
            direction_counts = np.bincount(
                self.best_directions[self.grid == 1], minlength=4
            )
            direction_names = ["UP", "RIGHT", "DOWN", "LEFT"]
            print("Direction distribution:", end=" ")
            for i, (name, count) in enumerate(zip(direction_names, direction_counts)):
                print(f"{name}:{count}", end=" " if i < 3 else "\n")

    def print_solution(self, is_final=True, is_intermediate=False):
        """
        Prints the solution in a human-readable format.
        [FIX] Always prints the best-known solution to avoid errors.
        """
        # Handle both parameter names for backward compatibility
        is_final = is_final if not is_intermediate else not is_intermediate

        # Always use the best-found attributes for printing.
        directions_to_print = self.best_directions
        p_values_to_print = self.best_p_values
        score_to_print = self.best_score

        if directions_to_print is None:
            print("当前没有可用的解决方案")
            return

        # Calculate avg_p from the best p_values matrix.
        p_values_active = p_values_to_print[self.grid == 1]
        avg_p = p_values_active.mean() if p_values_active.size > 0 else 0

        # 计算P25、P50、P75统计值（从大到小排序后的前25%、50%、75%的平均值）
        p25 = p50 = p75 = 0.0
        if p_values_active.size > 0:
            # 从大到小排序
            sorted_p = np.sort(p_values_active)[::-1]
            n = len(sorted_p)
            
            # 计算前25%的平均值
            count_25 = max(1, int(n * 0.25))
            p25 = sorted_p[:count_25].mean()
            
            # 计算前50%的平均值
            count_50 = max(1, int(n * 0.50))
            p50 = sorted_p[:count_50].mean()
            
            # 计算前75%的平均值
            count_75 = max(1, int(n * 0.75))
            p75 = sorted_p[:count_75].mean()

        # 显示基本统计信息
        if not is_final:
            print(f"当前解决方案概要:")
            print(f"  得分: {score_to_print:.3f}")
            print(f"  平均P值: {avg_p:.3f}")
            print(f"  P25 (前25%平均值): {p25:.3f}")
            print(f"  P50 (前50%平均值): {p50:.3f}")
            print(f"  P75 (前75%平均值): {p75:.3f}")

            # 显示方向分布统计
            direction_counts = np.bincount(
                directions_to_print[self.grid == 1], minlength=4
            )
            direction_names = ["↑", "→", "↓", "←"]
            print(f"  方向分布:", end=" ")
            for i, (symbol, count) in enumerate(zip(direction_names, direction_counts)):
                percentage = (
                    (count / self.num_blocks * 100) if self.num_blocks > 0 else 0
                )
                print(
                    f"{symbol}:{count}({percentage:.1f}%)", end=" " if i < 3 else "\n"
                )
        else:
            print(f"最终得分: {score_to_print:.3f}, 平均P值: {avg_p:.3f}")
            print(f"P25 (前25%平均值): {p25:.3f}")
            print(f"P50 (前50%平均值): {p50:.3f}")
            print(f"P75 (前75%平均值): {p75:.3f}")

        # Only print the full grid for smaller sizes to avoid flooding the console
        total_cells = self.rows * self.cols
        if total_cells <= 1500:  # 显示约40x40以下的网格
            print("箭头分配预览:")
            for r in range(self.rows):
                print(
                    " ".join(
                        [
                            (
                                ARROWS[directions_to_print[r, c]]
                                if self.grid[r, c]
                                else "·"
                            )
                            for c in range(self.cols)
                        ]
                    )
                )

            if (
                is_final and self.rows <= 20
            ):  # Only show P-values for small grids in final output
                print("P值矩阵:")
                for r in range(self.rows):
                    print(
                        " ".join(
                            [
                                (
                                    f"{p_values_to_print[r, c]:<3}"
                                    if self.grid[r, c]
                                    else "·  "
                                )
                                for c in range(self.cols)
                            ]
                        )
                    )
        else:
            print(f"网格尺寸 {self.rows}x{self.cols} 较大，隐藏详细显示以节省空间")

            # 对大网格显示更多统计信息
            if p_values_to_print is not None:
                if len(p_values_active) > 0:
                    print(
                        f"P值统计: 最小={p_values_active.min()}, 最大={p_values_active.max()}, 中位数={np.median(p_values_active):.2f}"
                    )

    @staticmethod
    def load_image_as_grid(image_path: str) -> np.ndarray:
        """
        从图片文件加载像素图并转换为网格
        透明或白色像素视为空白，其他像素视为有方块
        """
        try:
            img = Image.open(image_path)
            # 转换为RGBA模式以处理透明度
            img = img.convert("RGBA")
            width, height = img.size

            grid = np.zeros((height, width), dtype=int)
            for y in range(height):
                for x in range(width):
                    r, g, b, a = img.getpixel((x, y))
                    # 如果透明度为0或者是白色，视为空白
                    is_empty = (a == 0)
                    grid[y, x] = 0 if is_empty else 1  # True表示有方块

            return grid
        except Exception as e:
            print(f"加载图片 {image_path} 失败: {e}")
            return np.array([])

    def save_result_as_image(self, output_path: str) -> bool:
        """
        将箭头分配结果保存为PNG图片
        r=0,1,2,3分别对应上下左右方向
        alpha=0表示空的点
        """
        if self.best_directions is None:
            print("没有箭头分配结果，无法保存图片")
            return False

        try:
            # 创建RGBA图像
            img = Image.new("RGBA", (self.cols, self.rows), (0, 0, 0, 0))

            # 方向到颜色值的映射 (UP, RIGHT, DOWN, LEFT = 0, 1, 2, 3)
            for i in range(self.rows):
                for j in range(self.cols):
                    if self.grid[i, j] == 1 and self.best_directions[i, j] != -1:
                        # 有方块且已分配箭头
                        r_value = self.best_directions[i, j]
                        # 设置像素: (r值对应方向, g=0, b=0, alpha=255)
                        img.putpixel((j, i), (r_value, 0, 0, 255))
                    # 空白位置保持透明 (0, 0, 0, 0)

            img.save(output_path, "PNG")
            print(f"结果已保存到: {output_path}")
            return True

        except Exception as e:
            print(f"保存图片到 {output_path} 失败: {e}")
            return False

    def save_result_as_text(self, output_path: str) -> bool:
        """
        将箭头分配结果保存为文本文件，用箭头符号表示
        """
        if self.best_directions is None:
            print("没有箭头分配结果，无法保存文本文件")
            return False

        try:
            arrow_symbols = {0: "↑", 1: "→", 2: "↓", 3: "←"}
            p_values_active = self.best_p_values[self.grid == 1] if self.best_p_values is not None else np.array([])
            
            # 计算P25、P50、P75统计值
            p25 = p50 = p75 = 0.0
            if p_values_active.size > 0:
                # 从大到小排序
                sorted_p = np.sort(p_values_active)[::-1]
                n = len(sorted_p)
                
                count_25 = max(1, int(n * 0.25))
                p25 = sorted_p[:count_25].mean()
                
                count_50 = max(1, int(n * 0.50))
                p50 = sorted_p[:count_50].mean()
                
                count_75 = max(1, int(n * 0.75))
                p75 = sorted_p[:count_75].mean()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"箭头分配结果 - 网格大小: {self.rows}x{self.cols}\n")
                f.write(f"方块总数: {self.num_blocks}\n")
                f.write(f"最终得分: {self.best_score:.2f}\n")
                f.write(f"平均P值: {p_values_active.mean():.2f}\n" if p_values_active.size > 0 else "平均P值: N/A\n")
                f.write(f"P25 (前25%平均值): {p25:.2f}\n")
                f.write(f"P50 (前50%平均值): {p50:.2f}\n")
                f.write(f"P75 (前75%平均值): {p75:.2f}\n")
                f.write("=" * (self.cols * 3) + "\n\n")

                # 绘制箭头网格
                for i in range(self.rows):
                    row_str = ""
                    for j in range(self.cols):
                        if self.grid[i, j] == 1:
                            if self.best_directions[i, j] != -1:
                                symbol = arrow_symbols[self.best_directions[i, j]]
                                row_str += f" {symbol} "
                            else:
                                row_str += " ? "
                        else:
                            row_str += "   "
                    f.write(row_str + "\n")

                f.write("\n" + "=" * (self.cols * 3) + "\n\n")

                # 添加P值信息
                f.write("带P值的详细结果 (P值表示依赖数量):\n")
                f.write("=" * (self.cols * 6) + "\n")

                for i in range(self.rows):
                    row_str = ""
                    for j in range(self.cols):
                        if self.grid[i, j] == 1:
                            if self.best_directions[i, j] != -1:
                                symbol = arrow_symbols[self.best_directions[i, j]]
                                p_val = (
                                    self.best_p_values[i, j]
                                    if self.best_p_values is not None
                                    else 0
                                )
                                row_str += f"{symbol}({p_val:2d})"
                            else:
                                row_str += " ?(?) "
                        else:
                            row_str += "      "
                    f.write(row_str + "\n")

                f.write("=" * (self.cols * 6) + "\n\n")

                # 添加统计信息
                if self.best_p_values is not None:
                    p_values = self.best_p_values[self.grid == 1]
                    if len(p_values) > 0:
                        f.write(f"P值统计:\n")
                        f.write(f"  平均P值: {p_values.mean():.2f}\n")
                        f.write(f"  最大P值: {p_values.max()}\n")
                        f.write(f"  最小P值: {p_values.min()}\n")
                        f.write(f"  中位数: {np.median(p_values):.2f}\n")
                        f.write(f"  P25 (前25%平均值): {p25:.2f}\n")
                        f.write(f"  P50 (前50%平均值): {p50:.2f}\n")
                        f.write(f"  P75 (前75%平均值): {p75:.2f}\n")

            print(f"箭头文本结果已保存到: {output_path}")
            return True

        except Exception as e:
            print(f"保存文本文件到 {output_path} 失败: {e}")
            return False

    @staticmethod
    def batch_process_images(
        input_dir: str,
        output_dir: str,
        iterations: int = 5000,
        debug: bool = False,
    ):
        """
        批量处理目录中的所有图片

        Args:
            input_dir: 输入图片目录
            output_dir: 输出图片目录
            iterations: 每个图片的迭代次数
            debug: 是否启用调试模式（显示详细的阶段性盘面信息）
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 支持的图片格式
        image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif", "*.tiff"]

        # 获取所有图片文件
        image_files = []
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(input_dir, ext)))
            image_files.extend(glob.glob(os.path.join(input_dir, ext.upper())))

        if not image_files:
            print(f"在目录 {input_dir} 中没有找到图片文件")
            return

        print(f"找到 {len(image_files)} 个图片文件")
        print("=" * 60)

        success_count = 0
        total_count = len(image_files)

        for i, image_path in enumerate(image_files, 1):
            filename = os.path.basename(image_path)
            name_without_ext = os.path.splitext(filename)[0]
            output_image_path = os.path.join(
                output_dir, f"{name_without_ext}_arrows.png"
            )
            output_text_path = os.path.join(
                output_dir, f"{name_without_ext}_arrows.txt"
            )

            print(f"\n[{i}/{total_count}] 处理: {filename}")

            # 加载图片为网格
            grid = ArrowPuzzleSolver.load_image_as_grid(image_path)
            if grid.size == 0:
                print(f"跳过无效图片: {filename}")
                continue

            # 统计方块数量
            block_count = np.sum(grid)
            if block_count == 0:
                print(f"图片 {filename} 中没有方块，跳过")
                continue

            print(f"图片尺寸: {grid.shape[1]}x{grid.shape[0]}, 方块数量: {block_count}")

            # 创建求解器实例并求解
            try:
                solver = ArrowPuzzleSolver(grid, verbose=False, debug=debug)

                start_time = time.time()
                best_directions, best_p_values = solver.solve(iterations=iterations)
                end_time = time.time()

                if best_directions is not None:
                    # 保存图片结果
                    image_saved = solver.save_result_as_image(output_image_path)

                    # 保存文本结果
                    text_saved = solver.save_result_as_text(output_text_path)

                    if image_saved and text_saved:
                        success_count += 1
                        print(f"✓ 成功! 用时: {end_time - start_time:.2f}秒")
                        print(f"  最终得分: {solver.best_score:.2f}")
                        
                        # 计算并显示P值统计
                        if best_p_values is not None:
                            p_values = best_p_values[grid == 1]
                            if len(p_values) > 0:
                                avg_p = p_values.mean()
                                sorted_p = np.sort(p_values)[::-1]
                                n = len(sorted_p)
                                
                                p25 = sorted_p[:max(1, int(n * 0.25))].mean()
                                p50 = sorted_p[:max(1, int(n * 0.50))].mean()
                                p75 = sorted_p[:max(1, int(n * 0.75))].mean()
                                
                                print(f"  平均P值: {avg_p:.2f}")
                                print(f"  P25 (前25%平均值): {p25:.2f}")
                                print(f"  P50 (前50%平均值): {p50:.2f}")
                                print(f"  P75 (前75%平均值): {p75:.2f}")
                        
                        print(f"  图片: {output_image_path}")
                        print(f"  文本: {output_text_path}")
                    else:
                        print(
                            f"✗ 求解成功但保存失败 (图片:{image_saved}, 文本:{text_saved})"
                        )
                else:
                    print(f"✗ 求解失败, 用时: {end_time - start_time:.2f}秒")

            except Exception as e:
                print(f"✗ 处理出错: {e}")

        print("\n" + "=" * 60)
        print(f"批量处理完成: {success_count}/{total_count} 成功")
        print(f"成功率: {success_count/total_count*100:.1f}%")
        print(f"结果保存在: {output_dir}")


# --- Test Cases ---
def run_test_case(name, grid, iterations=20000, verbose=False, debug=False):
    """Runs a single test case."""
    if not isinstance(grid, np.ndarray):
        grid = np.array(grid, dtype=int)

    print("\n" + "=" * 50)
    print(f"RUNNING TEST CASE: {name}")
    print(
        f"Grid size: {grid.shape[0]}x{grid.shape[1]}, Blocks: {grid.sum()}, Iterations: {iterations}"
    )
    if debug:
        print("🐛 调试模式已启用")
    print("=" * 50)

    try:
        solver = ArrowPuzzleSolver(grid, verbose=verbose, debug=debug)
        solver.solve(iterations=iterations)
    except Exception as e:
        print(f"An error occurred during test case '{name}': {e}")


def create_test_grid(size: int, fill_rate: float = 1.0) -> np.ndarray:
    """
    创建测试用的网格
    :param size: 网格大小
    :param fill_rate: 填充率 (0.0-1.0)
    :return: numpy数组形式的网格
    """
    if fill_rate == 1.0:
        return np.ones((size, size), dtype=int)
    else:
        return (np.random.rand(size, size) < fill_rate).astype(int)


def batch_process_grids(
    sizes=[10, 20, 30], fill_rates=[1.0, 0.8, 0.6], iterations_per_size=None
):
    """
    批量处理不同大小和填充率的网格
    :param sizes: 要测试的网格大小列表
    :param fill_rates: 要测试的填充率列表
    :param iterations_per_size: 每个大小的迭代次数，如果为None则根据大小自动调整
    """
    print("\n" + "=" * 50)
    print("批量测试模式启动")
    print("=" * 50)

    for size in sizes:
        # 根据网格大小自动调整迭代次数
        if iterations_per_size is None:
            if size <= 10:
                iters = 5000
            elif size <= 20:
                iters = 5000
            else:
                iters = 10000

        for fill_rate in fill_rates:
            print(
                f"\n测试配置: {size}x{size} 网格, 填充率: {fill_rate*100}%, 迭代次数: {iters}"
            )
            print("-" * 50)

            grid = create_test_grid(size, fill_rate)
            print(f"创建 {size}x{size} 网格完成，实际填充块数: {np.sum(grid)}")

            try:
                solver = ArrowPuzzleSolver(grid, verbose=False)
                print("开始求解...")
                start_time = time.time()
                solver.solve(iterations=iters)
                end_time = time.time()
                print(f"求解耗时: {end_time - start_time:.2f} 秒")
            except Exception as e:
                print(f"处理出错: {e}")
            print("-" * 50)


def main():
    """主函数，支持命令行参数"""
    parser = argparse.ArgumentParser(description="箭头分配算法 - 模拟退火优化版")
    parser.add_argument(
        "--mode",
        choices=["test", "batch"],
        default="test",
        help="运行模式: test=测试模式, batch=批量处理图片",
    )
    parser.add_argument("--input", "-i", type=str, help="批量模式: 输入图片目录路径")
    parser.add_argument("--output", "-o", type=str, help="批量模式: 输出图片目录路径")
    parser.add_argument(
        "--iterations",
        type=int,
        default=5000,
        help="批量模式: 每个图片的迭代次数 (默认: 5000)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式 - 显示详细的阶段性盘面信息",
    )

    args = parser.parse_args()

    if args.mode == "test":
        print("运行测试模式...")
        run_test_case(
            "30x30 Full Grid",
            np.ones((30, 30), dtype=int),
            iterations=5000,
            debug=args.debug,
        )  # Increased iterations

    elif args.mode == "batch":
        if not args.input or not args.output:
            print("错误: 批量模式需要指定输入和输出目录")
            print("使用方法: python tapalgo.py --mode batch -i input_dir -o output_dir")
            return

        if not os.path.exists(args.input):
            print(f"错误: 输入目录不存在: {args.input}")
            return

        print("运行批量处理模式...")
        print(f"输入目录: {args.input}")
        print(f"输出目录: {args.output}")
        print(f"迭代次数: {args.iterations}")
        print(f"调试模式: {'🐛 启用' if args.debug else '❌ 禁用'}")
        print("-" * 50)

        ArrowPuzzleSolver.batch_process_images(
            args.input, args.output, args.iterations, args.debug
        )


if __name__ == "__main__":
    main()