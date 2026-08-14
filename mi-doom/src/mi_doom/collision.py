from __future__ import annotations

import math
from typing import Any


def circle_collides(level: Any, x: float, y: float, radius: float) -> bool:
    """
    Comprueba colisión entre un círculo y los tiles sólidos del nivel.
    """
    min_x = int(math.floor(x - radius))
    max_x = int(math.floor(x + radius))
    min_y = int(math.floor(y - radius))
    max_y = int(math.floor(y + radius))

    radius_sq = radius * radius

    for tile_y in range(min_y, max_y + 1):
        for tile_x in range(min_x, max_x + 1):
            if not level.is_solid(tile_x, tile_y):
                continue

            rect_left = float(tile_x)
            rect_top = float(tile_y)
            rect_right = float(tile_x + 1)
            rect_bottom = float(tile_y + 1)

            closest_x = max(rect_left, min(x, rect_right))
            closest_y = max(rect_top, min(y, rect_bottom))

            dx = x - closest_x
            dy = y - closest_y

            if dx * dx + dy * dy < radius_sq:
                return True

    return False


def line_of_sight(
    level: Any,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> bool:
    """
    Comprueba si hay línea de visión entre dos puntos usando DDA.
    """
    start_x = int(math.floor(x0))
    start_y = int(math.floor(y0))
    end_x = int(math.floor(x1))
    end_y = int(math.floor(y1))

    if start_x == end_x and start_y == end_y:
        return True

    dx = x1 - x0
    dy = y1 - y0
    distance = math.hypot(dx, dy)

    if distance < 1e-6:
        return True

    ray_dir_x = dx / distance
    ray_dir_y = dy / distance

    map_x = start_x
    map_y = start_y

    if ray_dir_x == 0.0:
        delta_dist_x = 1e30
    else:
        delta_dist_x = abs(1.0 / ray_dir_x)

    if ray_dir_y == 0.0:
        delta_dist_y = 1e30
    else:
        delta_dist_y = abs(1.0 / ray_dir_y)

    if ray_dir_x < 0.0:
        step_x = -1
        side_dist_x = (x0 - float(map_x)) * delta_dist_x
    else:
        step_x = 1
        side_dist_x = (float(map_x) + 1.0 - x0) * delta_dist_x

    if ray_dir_y < 0.0:
        step_y = -1
        side_dist_y = (y0 - float(map_y)) * delta_dist_y
    else:
        step_y = 1
        side_dist_y = (float(map_y) + 1.0 - y0) * delta_dist_y

    for _ in range(512):
        if side_dist_x < side_dist_y:
            side_dist_x += delta_dist_x
            map_x += step_x
            side = 0
        else:
            side_dist_y += delta_dist_y
            map_y += step_y
            side = 1

        if level.is_solid(map_x, map_y):
            if side == 0:
                wall_dist = (
                    float(map_x) - x0 + (1.0 - float(step_x)) / 2.0
                ) / ray_dir_x
            else:
                wall_dist = (
                    float(map_y) - y0 + (1.0 - float(step_y)) / 2.0
                ) / ray_dir_y

            return wall_dist >= distance - 1e-3

        if map_x == end_x and map_y == end_y:
            return True

    return False