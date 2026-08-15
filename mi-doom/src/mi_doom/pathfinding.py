"""
Módulo de pathfinding para mi-doom.
Implementa el algoritmo A* para encontrar rutas en el grid del nivel.
"""
from __future__ import annotations

import heapq
from typing import Any


def heuristic(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Distancia Manhattan entre dos puntos."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path(
    level: Any,
    start: tuple[int, int],
    end: tuple[int, int],
    max_steps: int = 300,
) -> list[tuple[int, int]] | None:
    """
    Encuentra el camino más corto entre start y end usando A*.
    Devuelve una lista de posiciones (x, y) o None si no hay camino.
    """
    if start == end:
        return [start]

    if not _is_walkable(level, end[0], end[1]):
        return None

    open_set: list[tuple[float, tuple[int, int]]] = []
    heapq.heappush(open_set, (0.0, start))

    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score: dict[tuple[int, int], float] = {start: 0.0}

    closed_set: set[tuple[int, int]] = set()
    steps = 0

    while open_set and steps < max_steps:
        steps += 1
        _, current = heapq.heappop(open_set)

        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        if current in closed_set:
            continue
        closed_set.add(current)

        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            neighbor = (current[0] + dx, current[1] + dy)

            if neighbor in closed_set:
                continue

            if not _is_walkable(level, neighbor[0], neighbor[1]):
                continue

            tentative_g = g_score[current] + 1.0

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor, end)
                heapq.heappush(open_set, (f, neighbor))

    return None


def _is_walkable(level: Any, x: int, y: int) -> bool:
    """Verifica si una posición es transitable en el nivel."""
    if x < 0 or y < 0 or x >= level.width or y >= level.height:
        return False
    tile = level.tile_at(x, y)
    return tile not in ("#", "D", "R", "B", "Y", "S", "X")
