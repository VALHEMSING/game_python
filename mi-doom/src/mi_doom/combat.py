from __future__ import annotations

import math
import random
from typing import Any, Iterable

from mi_doom.collision import line_of_sight


def normalize_angle(angle: float) -> float:
    return (angle + math.pi) % math.tau - math.pi


def angle_difference(angle_a: float, angle_b: float) -> float:
    return abs(normalize_angle(angle_a - angle_b))


def shoot_hitscan(
    level: Any,
    enemies: Iterable[Any],
    x: float,
    y: float,
    angle: float,
    spread: float,
    max_range: float,
    damage: float,
    pellet_count: int = 1,
) -> tuple[int, int, list[Any]]:
    """
    Dispara uno o varios perdigones usando hitscan.

    Devuelve:
    - cantidad de impactos
    - cantidad de enemigos eliminados
    - lista de enemigos impactados
    """
    hit_count = 0
    killed_count = 0
    hit_targets: list[Any] = []

    for _ in range(max(1, pellet_count)):
        shot_angle = angle + random.uniform(-spread, spread)
        target = _find_hitscan_target(
            level=level,
            enemies=enemies,
            x=x,
            y=y,
            shot_angle=shot_angle,
            max_range=max_range,
        )

        if target is not None:
            hit_count += 1

            if target not in hit_targets:
                hit_targets.append(target)

            if target.take_damage(damage, (x, y)):
                killed_count += 1

    return hit_count, killed_count, hit_targets


def _find_hitscan_target(
    level: Any,
    enemies: Iterable[Any],
    x: float,
    y: float,
    shot_angle: float,
    max_range: float,
) -> Any | None:
    best_target = None
    best_distance = max_range

    for enemy in enemies:
        if getattr(enemy, "is_dead", False):
            continue

        dx = enemy.x - x
        dy = enemy.y - y
        distance = math.hypot(dx, dy)

        if distance < 0.15 or distance > max_range:
            continue

        if not line_of_sight(level, x, y, enemy.x, enemy.y):
            continue

        angle_to_enemy = math.atan2(dy, dx)
        diff = angle_difference(shot_angle, angle_to_enemy)

        enemy_radius = float(getattr(enemy, "radius", 0.3))
        angular_radius = math.atan2(enemy_radius, distance) + 0.02

        if diff <= angular_radius and distance < best_distance:
            best_target = enemy
            best_distance = distance

    return best_target
