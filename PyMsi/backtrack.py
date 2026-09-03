"""
backtrack.py — 回溯算法暴力引擎 (v1.8.0)

轻量级、高性能的回溯搜索框架, 纯 Python 零依赖.
暴力的时间极短 — 1毫秒一次尝试, 1秒就是 1000 次, 100秒就是 10万次.

核心思想:
  回溯 = 深度优先搜索 (DFS) + 剪枝
  每一步尝试所有可能的选择, 如果走不通就回退, 换一条路
  虽然是"暴力", 但在小数据量下极快 — 毫秒级出结果

内置经典问题:
  1. 排列 (Permutations)         — n! 种排列
  2. 组合 (Combinations)         — C(n,k) 种组合
  3. 子集 (Subsets)              — 2^n 个子集
  4. N皇后 (N-Queens)            — N×N 棋盘放皇后
  5. 数独求解 (Sudoku)           — 9×9 数独
  6. 迷宫寻路 (Maze)             — 从起点到终点
  7. 0-1背包 (Knapsack)          — 最大价值不超重
  8. 单词拆分 (Word Break)       — 用字典里的词拼句子
  9. 组合总和 (Combination Sum)  — 和为 target 的组合
  10. 全排列 II (去重排列)        — 含重复元素的排列

通用框架:
  result = backtrack(
      choices=[...],      # 可选列表
      is_valid=lambda path, choice: ...,  # 约束条件
      is_goal=lambda path: ...,            # 目标条件
      find_all=True,                       # 找所有解还是第一个
  )

用法:
  import PyMsi as PM

  # 内置经典问题
  PM.backtrack.permute([1,2,3])              # 全排列
  PM.backtrack.combine(4, 2)                 # C(4,2) 组合
  PM.backtrack.subsets([1,2,3])              # 所有子集
  PM.backtrack.n_queens(4)                   # 4皇后
  PM.backtrack.solve_sudoku(board)           # 数独求解
  PM.backtrack.maze_path(maze, start, end)   # 迷宫寻路
  PM.backtrack.knapsack(items, capacity)     # 0-1背包
  PM.backtrack.combination_sum(cands, target) # 组合总和

  # 通用框架 — 自定义问题
  PM.backtrack.solve(choices, is_valid, is_goal)

  # 性能基准
  PM.backtrack.benchmark()
  PM.backtrack.demo()
"""

import time
import random
from copy import deepcopy


# ═══════════════════════════════════════════════════════════════
# 1. 通用回溯框架
# ═══════════════════════════════════════════════════════════════

class BacktrackEngine:
    """通用回溯搜索引擎

    模板方法模式: 用户提供 choices + is_valid + is_goal, 引擎负责暴力搜索.

    Args:
        choices: 可选的选择列表 (每次递归从这里选)
        is_valid: 函数(path, choice) → bool, 判断当前选择是否合法
        is_goal: 函数(path) → bool, 判断是否达到目标
        find_all: 是否找所有解 (False 找到第一个就返回)
        max_solutions: 最多找多少个解 (防止爆内存)
        max_steps: 最多尝试多少次 (防止无限递归)

    Returns:
        list of paths — 每个 path 是一个解 (选择序列)
    """

    def __init__(self, max_solutions=100000, max_steps=10_000_000):
        self.max_solutions = max_solutions
        self.max_steps = max_steps
        self._step_count = 0
        self._solutions = []

    def solve(self, choices, is_valid, is_goal, find_all=True,
              start_path=None, prune=None):
        """执行回溯搜索

        Args:
            choices: 可选列表 (list)
            is_valid: func(path, choice) → bool, 约束条件
            is_goal: func(path) → bool, 目标条件
            find_all: True=找所有解, False=找第一个就停
            start_path: 初始路径 (默认空列表)
            prune: func(path) → bool, 提前剪枝 (返回 True 就剪掉这条路)

        Returns:
            list of paths, 每个 path 是 tuple
        """
        self._solutions = []
        self._step_count = 0
        path = list(start_path) if start_path is not None else []

        self._dfs(path, list(choices), is_valid, is_goal,
                  find_all, prune)

        return self._solutions

    def _dfs(self, path, remaining, is_valid, is_goal, find_all, prune):
        """深度优先搜索 — 核心递归"""
        # 达到尝试上限, 强制停止
        if self._step_count >= self.max_steps:
            return
        if len(self._solutions) >= self.max_solutions:
            return

        # 剪枝: 这条路不可能到达目标, 直接放弃
        if prune and prune(path):
            return

        # 检查是否达到目标
        if is_goal(path):
            self._solutions.append(tuple(path))
            if not find_all:
                return

        # 尝试每一个选择
        for i, choice in enumerate(remaining):
            self._step_count += 1

            # 约束检查: 这个选择合不合法
            if not is_valid(path, choice):
                continue

            # 做选择: 把 choice 加入路径
            path.append(choice)
            # 剩下的选择 (不重复使用)
            new_remaining = remaining[:i] + remaining[i+1:]
            # 递归
            self._dfs(path, new_remaining, is_valid, is_goal, find_all, prune)
            # 撤销选择: 回溯
            path.pop()

            # 找到第一个就不继续了
            if not find_all and self._solutions:
                return

    @property
    def steps(self):
        """返回尝试次数"""
        return self._step_count


# ═══════════════════════════════════════════════════════════════
# 2. 排列 (Permutations)
# ═══════════════════════════════════════════════════════════════

def permute(nums):
    """全排列 — 返回 nums 的所有排列

    时间复杂度: O(n × n!)
    空间复杂度: O(n)

    示例:
        PM.backtrack.permute([1,2,3])
        → [(1,2,3), (1,3,2), (2,1,3), (2,3,1), (3,1,2), (3,2,1)]
    """
    engine = BacktrackEngine()

    def is_valid(path, choice):
        return True  # 排列没有额外约束, 只要不重复就行 (引擎自动保证)

    def is_goal(path):
        return len(path) == len(nums)

    return engine.solve(nums, is_valid, is_goal, find_all=True)


def permute_unique(nums):
    """含重复元素的全排列 (去重)

    示例:
        PM.backtrack.permute_unique([1,1,2])
        → [(1,1,2), (1,2,1), (2,1,1)]
    """
    engine = BacktrackEngine()
    nums_sorted = sorted(nums)

    def is_valid(path, choice):
        # 去重: 如果当前元素和前一个相同且前一个没用过, 跳过
        return True

    def is_goal(path):
        return len(path) == len(nums_sorted)

    # 用索引代替值来去重
    n = len(nums_sorted)
    indices = list(range(n))
    used = [False] * n
    result = []

    def backtrack(path):
        if len(path) == n:
            result.append(tuple(nums_sorted[i] for i in path))
            return
        for i in range(n):
            if used[i]:
                continue
            # 去重: 相同的数, 前一个没用过就跳过 (保证按顺序使用)
            if i > 0 and nums_sorted[i] == nums_sorted[i-1] and not used[i-1]:
                continue
            used[i] = True
            path.append(i)
            backtrack(path)
            path.pop()
            used[i] = False

    backtrack([])
    return result


# ═══════════════════════════════════════════════════════════════
# 3. 组合 (Combinations)
# ═══════════════════════════════════════════════════════════════

def combine(n, k):
    """从 1..n 中选 k 个数的所有组合 C(n,k)

    示例:
        PM.backtrack.combine(4, 2)
        → [(1,2), (1,3), (1,4), (2,3), (2,4), (3,4)]
    """
    result = []

    def backtrack(start, path):
        if len(path) == k:
            result.append(tuple(path))
            return
        # 剪枝: 剩下的数不够了就不用搜了
        for i in range(start, n + 1 - (k - len(path)) + 1):
            path.append(i)
            backtrack(i + 1, path)
            path.pop()

    backtrack(1, [])
    return result


def combine_from_list(lst, k):
    """从列表中选 k 个元素的所有组合

    示例:
        PM.backtrack.combine_from_list(['a','b','c'], 2)
        → [('a','b'), ('a','c'), ('b','c')]
    """
    result = []

    def backtrack(start, path):
        if len(path) == k:
            result.append(tuple(path))
            return
        for i in range(start, len(lst) - (k - len(path)) + 1):
            path.append(lst[i])
            backtrack(i + 1, path)
            path.pop()

    backtrack(0, [])
    return result


# ═══════════════════════════════════════════════════════════════
# 4. 子集 (Subsets)
# ═══════════════════════════════════════════════════════════════

def subsets(nums):
    """返回 nums 的所有子集 (幂集)

    共 2^n 个子集

    示例:
        PM.backtrack.subsets([1,2,3])
        → [(), (1,), (2,), (3,), (1,2), (1,3), (2,3), (1,2,3)]
    """
    result = []

    def backtrack(start, path):
        result.append(tuple(path))  # 每一步都是一个子集
        for i in range(start, len(nums)):
            path.append(nums[i])
            backtrack(i + 1, path)
            path.pop()

    backtrack(0, [])
    return result


def subsets_with_dup(nums):
    """含重复元素的子集 (去重)

    示例:
        PM.backtrack.subsets_with_dup([1,2,2])
        → [(), (1,), (2,), (1,2), (2,2), (1,2,2)]
    """
    nums_sorted = sorted(nums)
    result = []

    def backtrack(start, path):
        result.append(tuple(path))
        for i in range(start, len(nums_sorted)):
            if i > start and nums_sorted[i] == nums_sorted[i-1]:
                continue  # 跳过重复
            path.append(nums_sorted[i])
            backtrack(i + 1, path)
            path.pop()

    backtrack(0, [])
    return result


# ═══════════════════════════════════════════════════════════════
# 5. N皇后 (N-Queens)
# ═══════════════════════════════════════════════════════════════

def n_queens(n):
    """N皇后问题 — 在 N×N 棋盘上放 N 个皇后, 互不攻击

    返回所有解, 每个解是一个元组, 表示每行皇后在第几列 (0-indexed)

    示例:
        PM.backtrack.n_queens(4)
        → [(1,3,0,2), (2,0,3,1)]

    皇后攻击规则: 同行、同列、同对角线都不行
    因为我们按行放, 所以只需要检查列和对角线
    """
    result = []
    cols = set()       # 已占用的列
    diag1 = set()      # 左上→右下对角线 (row - col 为定值)
    diag2 = set()      # 右上→左下对角线 (row + col 为定值)

    def backtrack(row, path):
        if row == n:
            result.append(tuple(path))
            return
        for col in range(n):
            # 检查是否可以放
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            # 放皇后
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            path.append(col)
            # 递归下一行
            backtrack(row + 1, path)
            # 回溯
            path.pop()
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)

    backtrack(0, [])
    return result


def n_queens_count(n):
    """N皇后 — 只统计解的数量, 不保存具体解 (更快)"""
    count = 0
    cols = set()
    diag1 = set()
    diag2 = set()

    def backtrack(row):
        nonlocal count
        if row == n:
            count += 1
            return
        for col in range(n):
            if col in cols or (row - col) in diag1 or (row + col) in diag2:
                continue
            cols.add(col)
            diag1.add(row - col)
            diag2.add(row + col)
            backtrack(row + 1)
            cols.remove(col)
            diag1.remove(row - col)
            diag2.remove(row + col)

    backtrack(0)
    return count


def print_queens(solution):
    """可视化 N皇后 解

    示例:
        for sol in PM.backtrack.n_queens(4):
            PM.backtrack.print_queens(sol)
            print()
    """
    n = len(solution)
    lines = []
    for row in range(n):
        line = ""
        for col in range(n):
            if solution[row] == col:
                line += "Q "
            else:
                line += ". "
        lines.append(line)
    print("\n".join(lines))
    return lines


# ═══════════════════════════════════════════════════════════════
# 6. 数独求解 (Sudoku)
# ═══════════════════════════════════════════════════════════════

def solve_sudoku(board):
    """解数独 — 9×9 棋盘, 0 或 '.' 表示空格

    Args:
        board: 9×9 二维列表, 0 或 '.' 表示空格, 1-9 表示已有数字

    Returns:
        解后的 board (list of lists), 无解返回 None

    示例:
        board = [
            [5,3,0,0,7,0,0,0,0],
            [6,0,0,1,9,5,0,0,0],
            [0,9,8,0,0,0,0,6,0],
            [8,0,0,0,6,0,0,0,3],
            [4,0,0,8,0,3,0,0,1],
            [7,0,0,0,2,0,0,0,6],
            [0,6,0,0,0,0,2,8,0],
            [0,0,0,4,1,9,0,0,5],
            [0,0,0,0,8,0,0,7,9],
        ]
        solved = PM.backtrack.solve_sudoku(board)
    """
    # 标准化: 转成整数, '.' 和 0 都是空
    b = []
    for row in board:
        new_row = []
        for cell in row:
            if cell == '.' or cell == 0 or cell == '0':
                new_row.append(0)
            else:
                new_row.append(int(cell))
        b.append(new_row)

    # 找空格
    def find_empty():
        for i in range(9):
            for j in range(9):
                if b[i][j] == 0:
                    return i, j
        return None

    # 检查 num 放在 (row, col) 是否合法
    def is_valid(row, col, num):
        # 检查行
        for j in range(9):
            if b[row][j] == num:
                return False
        # 检查列
        for i in range(9):
            if b[i][col] == num:
                return False
        # 检查 3×3 宫
        box_row = (row // 3) * 3
        box_col = (col // 3) * 3
        for i in range(3):
            for j in range(3):
                if b[box_row + i][box_col + j] == num:
                    return False
        return True

    def backtrack():
        pos = find_empty()
        if pos is None:
            return True  # 全填满了, 找到解
        row, col = pos

        for num in range(1, 10):
            if is_valid(row, col, num):
                b[row][col] = num
                if backtrack():
                    return True
                b[row][col] = 0  # 回溯
        return False

    if backtrack():
        return b
    return None


def print_sudoku(board):
    """打印数独棋盘"""
    lines = []
    for i, row in enumerate(board):
        if i % 3 == 0 and i != 0:
            lines.append("-" * 21)
        line = ""
        for j, cell in enumerate(row):
            if j % 3 == 0 and j != 0:
                line += "| "
            line += (str(cell) if cell != 0 else ".") + " "
        lines.append(line)
    print("\n".join(lines))
    return lines


# ═══════════════════════════════════════════════════════════════
# 7. 迷宫寻路 (Maze Pathfinding)
# ═══════════════════════════════════════════════════════════════

def maze_path(maze, start, end):
    """迷宫寻路 — 从 start 到 end 的所有路径

    Args:
        maze: 二维列表, 0=通路, 1=墙
        start: (row, col) 起点
        end: (row, col) 终点

    Returns:
        list of paths, 每个 path 是 [(r,c), (r,c), ...] 的坐标序列

    示例:
        maze = [
            [0, 0, 1, 0],
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
        ]
        paths = PM.backtrack.maze_path(maze, (0,0), (3,3))
    """
    rows = len(maze)
    cols = len(maze[0]) if rows > 0 else 0
    result = []
    visited = [[False] * cols for _ in range(rows)]
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # 右、下、左、上

    def backtrack(r, c, path):
        # 到达终点
        if (r, c) == end:
            result.append(tuple(path))
            return

        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            # 边界检查
            if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                continue
            # 墙检查
            if maze[nr][nc] == 1:
                continue
            # 已访问检查
            if visited[nr][nc]:
                continue
            # 走
            visited[nr][nc] = True
            path.append((nr, nc))
            backtrack(nr, nc, path)
            # 回溯
            path.pop()
            visited[nr][nc] = False

    sr, sc = start
    if 0 <= sr < rows and 0 <= sc < cols and maze[sr][sc] == 0:
        visited[sr][sc] = True
        backtrack(sr, sc, [(sr, sc)])

    return result


def maze_shortest_path(maze, start, end):
    """迷宫最短路径 (BFS, 非回溯, 但作为辅助函数提供)

    注意: BFS 找最短路径比回溯快得多, 回溯适合找所有路径
    """
    from collections import deque
    rows = len(maze)
    cols = len(maze[0]) if rows > 0 else 0
    visited = [[False] * cols for _ in range(rows)]
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    sr, sc = start
    if maze[sr][sc] == 1:
        return None

    queue = deque([(sr, sc, [(sr, sc)])])
    visited[sr][sc] = True

    while queue:
        r, c, path = queue.popleft()
        if (r, c) == end:
            return path
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if (0 <= nr < rows and 0 <= nc < cols
                    and not visited[nr][nc] and maze[nr][nc] == 0):
                visited[nr][nc] = True
                queue.append((nr, nc, path + [(nr, nc)]))
    return None


# ═══════════════════════════════════════════════════════════════
# 8. 0-1 背包 (Knapsack)
# ═══════════════════════════════════════════════════════════════

def knapsack(items, capacity):
    """0-1背包 — 选物品使总价值最大且不超重

    Args:
        items: [(weight, value), ...] 物品列表
        capacity: 背包容量 (最大重量)

    Returns:
        (max_value, selected_indices) — 最大价值和选中的物品索引

    示例:
        items = [(2, 3), (3, 4), (4, 5), (5, 6)]
        value, selected = PM.backtrack.knapsack(items, 8)
    """
    best_value = 0
    best_selected = []

    def backtrack(idx, current_w, current_v, selected):
        nonlocal best_value, best_selected

        # 更新最优解
        if current_v > best_value:
            best_value = current_v
            best_selected = list(selected)

        # 所有物品都考虑过了
        if idx >= len(items):
            return

        # 剪枝: 就算把剩下的全装了也超不过当前最优, 就不用搜了
        remaining_v = sum(items[i][1] for i in range(idx, len(items)))
        if current_v + remaining_v <= best_value:
            return

        w, v = items[idx]

        # 选: 装得下才选
        if current_w + w <= capacity:
            selected.append(idx)
            backtrack(idx + 1, current_w + w, current_v + v, selected)
            selected.pop()

        # 不选
        backtrack(idx + 1, current_w, current_v, selected)

    # 按价值密度排序 (提高剪枝效率)
    sorted_indices = sorted(range(len(items)),
                            key=lambda i: items[i][1] / items[i][0] if items[i][0] > 0 else 0,
                            reverse=True)
    sorted_items = [items[i] for i in sorted_indices]

    best_value_local = 0
    best_selected_local = []

    def backtrack_sorted(idx, current_w, current_v, selected_local):
        nonlocal best_value_local, best_selected_local

        if current_v > best_value_local:
            best_value_local = current_v
            best_selected_local = list(selected_local)

        if idx >= len(sorted_items):
            return

        # 剪枝
        remaining_v = sum(sorted_items[i][1] for i in range(idx, len(sorted_items)))
        if current_v + remaining_v <= best_value_local:
            return

        w, v = sorted_items[idx]

        if current_w + w <= capacity:
            selected_local.append(idx)
            backtrack_sorted(idx + 1, current_w + w, current_v + v, selected_local)
            selected_local.pop()

        backtrack_sorted(idx + 1, current_w, current_v, selected_local)

    backtrack_sorted(0, 0, 0, [])

    # 把排序后的索引映射回原始索引
    best_selected_original = [sorted_indices[i] for i in best_selected_local]
    return best_value_local, sorted(best_selected_original)


# ═══════════════════════════════════════════════════════════════
# 9. 组合总和 (Combination Sum)
# ═══════════════════════════════════════════════════════════════

def combination_sum(candidates, target):
    """组合总和 — candidates 中的数可重复使用, 和为 target 的所有组合

    示例:
        PM.backtrack.combination_sum([2,3,6,7], 7)
        → [(2,2,3), (7)]
    """
    result = []
    cands = sorted(candidates)

    def backtrack(start, path, remaining):
        if remaining == 0:
            result.append(tuple(path))
            return
        if remaining < 0:
            return
        for i in range(start, len(cands)):
            if cands[i] > remaining:
                break  # 剪枝: 后面更大, 不用看了
            path.append(cands[i])
            backtrack(i, path, remaining - cands[i])  # i 不变, 可重复使用
            path.pop()

    backtrack(0, [], target)
    return result


def combination_sum_no_reuse(candidates, target):
    """组合总和 II — 每个数只能用一次, 且去重

    示例:
        PM.backtrack.combination_sum_no_reuse([10,1,2,7,6,1,5], 8)
        → [(1,1,6), (1,2,5), (1,7), (2,6)]
    """
    result = []
    cands = sorted(candidates)

    def backtrack(start, path, remaining):
        if remaining == 0:
            result.append(tuple(path))
            return
        if remaining < 0:
            return
        for i in range(start, len(cands)):
            if i > start and cands[i] == cands[i-1]:
                continue  # 去重
            if cands[i] > remaining:
                break
            path.append(cands[i])
            backtrack(i + 1, path, remaining - cands[i])
            path.pop()

    backtrack(0, [], target)
    return result


# ═══════════════════════════════════════════════════════════════
# 10. 单词拆分 (Word Break)
# ═══════════════════════════════════════════════════════════════

def word_break(s, word_dict):
    """单词拆分 — 用字典里的词能否拼出 s (返回所有拆分方式)

    示例:
        PM.backtrack.word_break("catsanddog", ["cat","cats","and","sand","dog"])
        → [('cat', 'sand', 'dog'), ('cats', 'and', 'dog')]
    """
    word_set = set(word_dict)
    result = []

    def backtrack(start, path):
        if start == len(s):
            result.append(tuple(path))
            return
        for end in range(start + 1, len(s) + 1):
            word = s[start:end]
            if word in word_set:
                path.append(word)
                backtrack(end, path)
                path.pop()

    backtrack(0, [])
    return result


def word_break_possible(s, word_dict):
    """单词拆分 — 只判断是否可能 (更快, 找到一个就返回)"""
    word_set = set(word_dict)
    memo = {}

    def dfs(start):
        if start == len(s):
            return True
        if start in memo:
            return memo[start]
        for end in range(start + 1, len(s) + 1):
            if s[start:end] in word_set and dfs(end):
                memo[start] = True
                return True
        memo[start] = False
        return False

    return dfs(0)


# ═══════════════════════════════════════════════════════════════
# 11. 通用 solve 接口
# ═══════════════════════════════════════════════════════════════

def solve(choices, is_valid, is_goal, find_all=True,
          start_path=None, prune=None, max_solutions=100000, max_steps=10_000_000):
    """通用回溯求解器

    Args:
        choices: 可选列表
        is_valid: func(path, choice) → bool, 约束条件
        is_goal: func(path) → bool, 目标条件
        find_all: 是否找所有解
        start_path: 初始路径
        prune: func(path) → bool, 剪枝 (True 就剪)
        max_solutions: 最多解数
        max_steps: 最多尝试次数

    Returns:
        list of tuples (解列表)

    示例:
        # 自定义: 找所有和为 5 的子集
        nums = [1,2,3,4,5]
        results = PM.backtrack.solve(
            choices=nums,
            is_valid=lambda path, c: sum(path) + c <= 5,
            is_goal=lambda path: sum(path) == 5,
            find_all=True,
        )
    """
    engine = BacktrackEngine(max_solutions=max_solutions, max_steps=max_steps)
    return engine.solve(choices, is_valid, is_goal, find_all=find_all,
                        start_path=start_path, prune=prune)


# ═══════════════════════════════════════════════════════════════
# 12. 性能基准测试
# ═══════════════════════════════════════════════════════════════

def benchmark():
    """回溯算法性能基准测试

    测量不同问题的暴力速度, 验证"1毫秒一次尝试"的水平
    """
    print()
    print("=" * 60)
    print("  回溯算法性能基准测试")
    print("  暴力搜索到底有多快?")
    print("=" * 60)

    results = {}

    # 1. 排列
    print("\n  [1] 排列 permute(8) = 40320 种排列")
    t0 = time.perf_counter()
    perms = permute(list(range(8)))
    t = time.perf_counter() - t0
    attempts = len(perms)
    print(f"      解数: {len(perms)}")
    print(f"      用时: {t*1000:.2f}ms")
    print(f"      速度: {attempts/t:,.0f} 解/秒 ({t*1000000/attempts:.2f} μs/解)")
    results['permutations_8'] = {'solutions': len(perms), 'time_ms': t*1000}

    # 2. 组合
    print("\n  [2] 组合 C(20,10) = 184756 种组合")
    t0 = time.perf_counter()
    combs = combine(20, 10)
    t = time.perf_counter() - t0
    print(f"      解数: {len(combs)}")
    print(f"      用时: {t*1000:.2f}ms")
    print(f"      速度: {len(combs)/t:,.0f} 解/秒 ({t*1000000/len(combs):.2f} μs/解)")
    results['combinations_20_10'] = {'solutions': len(combs), 'time_ms': t*1000}

    # 3. N皇后
    print("\n  [3] N皇后 n=8 (92 个解)")
    t0 = time.perf_counter()
    q_solutions = n_queens(8)
    t = time.perf_counter() - t0
    print(f"      解数: {len(q_solutions)}")
    print(f"      用时: {t*1000:.2f}ms")
    print(f"      速度: {len(q_solutions)/t:,.0f} 解/秒 ({t*1000000/len(q_solutions):.2f} μs/解)")
    results['nqueens_8'] = {'solutions': len(q_solutions), 'time_ms': t*1000}

    # 4. N皇后计数 (n=12)
    print("\n  [4] N皇后计数 n=12 (14200 个解)")
    t0 = time.perf_counter()
    q_count = n_queens_count(12)
    t = time.perf_counter() - t0
    print(f"      解数: {q_count}")
    print(f"      用时: {t*1000:.2f}ms")
    print(f"      速度: {q_count/t:,.0f} 解/秒 ({t*1000000/q_count:.2f} μs/解)")
    results['nqueens_12_count'] = {'solutions': q_count, 'time_ms': t*1000}

    # 5. 子集
    print("\n  [5] 子集 subsets(20) = 2^20 = 1,048,576 个子集")
    t0 = time.perf_counter()
    subs = subsets(list(range(20)))
    t = time.perf_counter() - t0
    print(f"      解数: {len(subs):,}")
    print(f"      用时: {t*1000:.2f}ms")
    print(f"      速度: {len(subs)/t:,.0f} 子集/秒 ({t*1000000/len(subs):.3f} μs/个)")
    results['subsets_20'] = {'solutions': len(subs), 'time_ms': t*1000}

    # 6. 数独
    print("\n  [6] 数独求解 (经典难题)")
    hard_board = [
        [8,0,0,0,0,0,0,0,0],
        [0,0,3,6,0,0,0,0,0],
        [0,7,0,0,9,0,2,0,0],
        [0,5,0,0,0,7,0,0,0],
        [0,0,0,0,4,5,7,0,0],
        [0,0,0,1,0,0,0,3,0],
        [0,0,1,0,0,0,0,6,8],
        [0,0,8,5,0,0,0,1,0],
        [0,9,0,0,0,0,4,0,0],
    ]
    t0 = time.perf_counter()
    solved = solve_sudoku(hard_board)
    t = time.perf_counter() - t0
    print(f"      用时: {t*1000:.2f}ms")
    print(f"      有解: {solved is not None}")
    results['sudoku_hard'] = {'time_ms': t*1000, 'solved': solved is not None}

    # 总结
    print("\n" + "-" * 60)
    print("  总结:")
    print(f"    subsets(20): 100万子集 / {results['subsets_20']['time_ms']:.0f}ms "
          f"= {1000/results['subsets_20']['time_ms']*1000:,.0f} 子集/秒")
    print(f"    nqueens(8): 92解 / {results['nqueens_8']['time_ms']:.2f}ms "
          f"= {92/results['nqueens_8']['time_ms']*1000:,.0f} 解/秒")
    print(f"    permute(8): 40320解 / {results['permutations_8']['time_ms']:.2f}ms "
          f"= {40320/results['permutations_8']['time_ms']*1000:,.0f} 解/秒")
    print()
    print("  结论: 暴力回溯极快 — 简单问题百万级/秒, 复杂问题千级/秒")
    print("  1毫秒 = 一次复杂尝试, 1秒 = 1000次复杂搜索")
    print("=" * 60)

    return results


# ═══════════════════════════════════════════════════════════════
# 13. 演示
# ═══════════════════════════════════════════════════════════════

def demo():
    """回溯算法演示"""
    print()
    print("=" * 60)
    print("  回溯算法演示 — 暴力的艺术")
    print("  1毫秒一次尝试, 1秒就是 1000 次")
    print("=" * 60)

    # 1. 排列
    print("\n  [1] 全排列 permute([1,2,3])")
    perms = permute([1, 2, 3])
    print(f"      共 {len(perms)} 种: {perms}")

    # 2. 组合
    print("\n  [2] 组合 combine(4, 2) = C(4,2)")
    combs = combine(4, 2)
    print(f"      共 {len(combs)} 种: {combs}")

    # 3. 子集
    print("\n  [3] 子集 subsets([1,2,3])")
    subs = subsets([1, 2, 3])
    print(f"      共 {len(subs)} 个: {subs}")

    # 4. N皇后
    print("\n  [4] 4皇后 n_queens(4)")
    queens = n_queens(4)
    print(f"      共 {len(queens)} 个解:")
    for i, q in enumerate(queens):
        print(f"      解 {i+1}: {q}")
        print_queens(q)
        print()

    # 5. 数独
    print("\n  [5] 数独求解")
    board = [
        [5,3,0,0,7,0,0,0,0],
        [6,0,0,1,9,5,0,0,0],
        [0,9,8,0,0,0,0,6,0],
        [8,0,0,0,6,0,0,0,3],
        [4,0,0,8,0,3,0,0,1],
        [7,0,0,0,2,0,0,0,6],
        [0,6,0,0,0,0,2,8,0],
        [0,0,0,4,1,9,0,0,5],
        [0,0,0,0,8,0,0,7,9],
    ]
    print("      题目:")
    for line in print_sudoku(board):
        print("      " + line)
    print()
    solved = solve_sudoku(board)
    print("      答案:")
    for line in print_sudoku(solved):
        print("      " + line)

    # 6. 迷宫
    print("\n  [6] 迷宫寻路")
    maze = [
        [0, 0, 1, 0],
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
    ]
    paths = maze_path(maze, (0, 0), (3, 3))
    print(f"      从 (0,0) 到 (3,3) 共 {len(paths)} 条路径:")
    for i, p in enumerate(paths):
        print(f"      路径 {i+1}: {p}")

    # 7. 组合总和
    print("\n  [7] 组合总和 combination_sum([2,3,6,7], 7)")
    cs = combination_sum([2, 3, 6, 7], 7)
    print(f"      共 {len(cs)} 种: {cs}")

    print("\n" + "=" * 60)
    print("  演示完成! 运行 PM.backtrack.benchmark() 看性能测试")
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# 14. PyMsi 集成层
# ═══════════════════════════════════════════════════════════════

class _BacktrackModule:
    """PyMsi.backtrack — 回溯算法暴力引擎

    轻量级高性能回溯搜索, 纯Python零依赖:
      1毫秒一次尝试, 1秒1000次, 100秒10万次

    内置经典问题:
      PM.backtrack.permute([1,2,3])              # 全排列
      PM.backtrack.permute_unique([1,1,2])        # 去重排列
      PM.backtrack.combine(4, 2)                 # 组合 C(n,k)
      PM.backtrack.subsets([1,2,3])              # 所有子集
      PM.backtrack.subsets_with_dup([1,2,2])      # 去重子集
      PM.backtrack.n_queens(4)                   # N皇后
      PM.backtrack.n_queens_count(8)             # N皇后计数
      PM.backtrack.print_queens(solution)         # 打印皇后
      PM.backtrack.solve_sudoku(board)            # 数独求解
      PM.backtrack.print_sudoku(board)            # 打印数独
      PM.backtrack.maze_path(maze, s, e)          # 迷宫所有路径
      PM.backtrack.maze_shortest_path(maze,s,e)  # 迷宫最短路径(BFS)
      PM.backtrack.knapsack(items, capacity)     # 0-1背包
      PM.backtrack.combination_sum(cands, tgt)    # 组合总和(可重复)
      PM.backtrack.combination_sum_no_reuse(c,t) # 组合总和(不重复)
      PM.backtrack.word_break(s, word_dict)      # 单词拆分
      PM.backtrack.word_break_possible(s, wd)    # 单词拆分判断

    通用框架:
      PM.backtrack.solve(choices, is_valid, is_goal)

    测试/演示:
      PM.backtrack.demo()
      PM.backtrack.benchmark()
    """

    def __init__(self):
        pass

    def __repr__(self):
        return "<PyMsi.backtrack [回溯算法引擎] v1.8.0>"

    # --- 排列 ---
    def permute(self, nums):
        """全排列"""
        return permute(nums)

    def permute_unique(self, nums):
        """去重全排列"""
        return permute_unique(nums)

    # --- 组合 ---
    def combine(self, n, k):
        """组合 C(n,k)"""
        return combine(n, k)

    def combine_from_list(self, lst, k):
        """从列表选 k 个的组合"""
        return combine_from_list(lst, k)

    # --- 子集 ---
    def subsets(self, nums):
        """所有子集"""
        return subsets(nums)

    def subsets_with_dup(self, nums):
        """去重子集"""
        return subsets_with_dup(nums)

    # --- N皇后 ---
    def n_queens(self, n):
        """N皇后所有解"""
        return n_queens(n)

    def n_queens_count(self, n):
        """N皇后解数"""
        return n_queens_count(n)

    def print_queens(self, solution):
        """打印N皇后解"""
        return print_queens(solution)

    # --- 数独 ---
    def solve_sudoku(self, board):
        """解数独"""
        return solve_sudoku(board)

    def print_sudoku(self, board):
        """打印数独"""
        return print_sudoku(board)

    # --- 迷宫 ---
    def maze_path(self, maze, start, end):
        """迷宫所有路径"""
        return maze_path(maze, start, end)

    def maze_shortest_path(self, maze, start, end):
        """迷宫最短路径 (BFS)"""
        return maze_shortest_path(maze, start, end)

    # --- 背包 ---
    def knapsack(self, items, capacity):
        """0-1背包"""
        return knapsack(items, capacity)

    # --- 组合总和 ---
    def combination_sum(self, candidates, target):
        """组合总和 (可重复使用)"""
        return combination_sum(candidates, target)

    def combination_sum_no_reuse(self, candidates, target):
        """组合总和 (不可重复, 去重)"""
        return combination_sum_no_reuse(candidates, target)

    # --- 单词拆分 ---
    def word_break(self, s, word_dict):
        """单词拆分 (所有拆分方式)"""
        return word_break(s, word_dict)

    def word_break_possible(self, s, word_dict):
        """单词拆分 (是否可能)"""
        return word_break_possible(s, word_dict)

    # --- 通用 ---
    def solve(self, choices, is_valid, is_goal, find_all=True,
              start_path=None, prune=None, max_solutions=100000, max_steps=10_000_000):
        """通用回溯求解器"""
        return solve(choices, is_valid, is_goal, find_all=find_all,
                     start_path=start_path, prune=prune,
                     max_solutions=max_solutions, max_steps=max_steps)

    # --- 演示/测试 ---
    def demo(self):
        """运行演示"""
        return demo()

    def benchmark(self):
        """性能基准测试"""
        return benchmark()
