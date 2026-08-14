from __future__ import annotations

import math
import random
from enum import Enum, auto
from typing import Any

import pygame

from mi_doom.collision import circle_collides, line_of_sight


class EnemyState(Enum):
    IDLE = auto()
    PATROL = auto()
    CHASE = auto()
    ATTACK = auto()
    HURT = auto()
    DEAD = auto()


class EnemyKind(Enum):
    DRONE = "drone"
    MUTANT = "mutant"
    BEAST = "beast"


ENEMY_STATS: dict[EnemyKind, dict[str, float | int | bool]] = {
    EnemyKind.DRONE: {
        "health": 25.0,
        "speed": 1.9,
        "radius": 0.24,
        "scale": 0.52,
        "detect_range": 10.0,
        "attack_range": 6.0,
        "attack_damage": 6,
        "attack_interval": 1.4,
        "ranged": True,
    },
    EnemyKind.MUTANT: {
        "health": 55.0,
        "speed": 2.3,
        "radius": 0.30,
        "scale": 0.75,
        "detect_range": 12.0,
        "attack_range": 8.0,
        "attack_damage": 9,
        "attack_interval": 1.6,
        "ranged": True,
    },
    EnemyKind.BEAST: {
        "health": 130.0,
        "speed": 3.3,
        "radius": 0.38,
        "scale": 1.0,
        "detect_range": 14.0,
        "attack_range": 1.35,
        "attack_damage": 18,
        "attack_interval": 1.0,
        "ranged": False,
    },
}


class Enemy:
    def __init__(
        self,
        kind: EnemyKind,
        x: float,
        y: float,
        sprite: pygame.Surface | None = None,
    ) -> None:
        stats = ENEMY_STATS[kind]

        self.kind = kind
        self.x = x
        self.y = y
        self.sprite = sprite

        self.health = float(stats["health"])
        self.speed = float(stats["speed"])
        self.radius = float(stats["radius"])
        self.scale = float(stats["scale"])
        self.detect_range = float(stats["detect_range"])
        self.attack_range = float(stats["attack_range"])
        self.attack_damage = int(stats["attack_damage"])
        self.attack_interval = float(stats["attack_interval"])
        self.ranged = bool(stats["ranged"])

        self.state = EnemyState.PATROL
        self.angle = random.uniform(0.0, math.tau)
        self.dir_angle = self.angle
        self.patrol_timer = random.uniform(1.0, 3.0)
        self.attack_timer = random.uniform(0.2, 0.8)
        self.hurt_timer = 0.0
        self.attack_anim_timer = 0.0
        self.alerted = False

    @property
    def is_dead(self) -> bool:
        return self.state == EnemyState.DEAD

    def take_damage(
        self,
        amount: float,
        source_pos: tuple[float, float] | None = None,
    ) -> bool:
        if self.is_dead:
            return False

        self.health -= amount
        self.alerted = True

        if self.health <= 0.0:
            self.health = 0.0
            self.state = EnemyState.DEAD
            return True

        self.hurt_timer = 0.18
        self.state = EnemyState.HURT
        return False

    def update(self, dt: float, level: Any, player: Any) -> None:
        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.hurt_timer = max(0.0, self.hurt_timer - dt)
        self.attack_anim_timer = max(0.0, self.attack_anim_timer - dt)

        if self.is_dead:
            return

        if getattr(player, "is_dead", False):
            self.state = EnemyState.IDLE
            return

        if self.state == EnemyState.HURT:
            if self.hurt_timer <= 0.0:
                self.state = EnemyState.CHASE
            return

        dx = player.x - self.x
        dy = player.y - self.y
        distance_to_player = math.hypot(dx, dy)

        detect_range = self.detect_range
        if self.alerted:
            detect_range = max(detect_range, 20.0)

        can_see_player = (
            distance_to_player <= detect_range
            and line_of_sight(level, self.x, self.y, player.x, player.y)
        )

        if can_see_player:
            self.alerted = True

        if self.state == EnemyState.IDLE:
            if can_see_player:
                self.state = EnemyState.CHASE
            elif random.random() < 0.25 * dt:
                self.state = EnemyState.PATROL
                self.dir_angle = random.uniform(0.0, math.tau)
                self.patrol_timer = random.uniform(1.5, 3.5)

        elif self.state == EnemyState.PATROL:
            self._update_patrol(dt, level, can_see_player)

        elif self.state == EnemyState.CHASE:
            if can_see_player and distance_to_player <= self.attack_range:
                self.state = EnemyState.ATTACK
            else:
                self._move_toward(player.x, player.y, dt, level)

                if not can_see_player and not self.alerted:
                    self.state = EnemyState.PATROL
                    self.patrol_timer = 0.0

        elif self.state == EnemyState.ATTACK:
            if not can_see_player or distance_to_player > self.attack_range * 1.2:
                self.state = EnemyState.CHASE
            else:
                self._face_point(player.x, player.y)

                if self.attack_timer <= 0.0:
                    player.take_damage(self.attack_damage)
                    self.attack_timer = self.attack_interval
                    self.attack_anim_timer = 0.18

    def _update_patrol(self, dt: float, level: Any, can_see_player: bool) -> None:
        if can_see_player:
            self.state = EnemyState.CHASE
            return

        self.patrol_timer -= dt

        if self.patrol_timer <= 0.0:
            self.dir_angle = random.uniform(0.0, math.tau)
            self.patrol_timer = random.uniform(1.5, 3.5)

        dx = math.cos(self.dir_angle) * self.speed * 0.45 * dt
        dy = math.sin(self.dir_angle) * self.speed * 0.45 * dt

        if not self._move(dx, dy, level):
            self.dir_angle = random.uniform(0.0, math.tau)
            self.patrol_timer = random.uniform(0.8, 2.0)

    def _move_toward(self, target_x: float, target_y: float, dt: float, level: Any) -> None:
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance < 0.2:
            return

        dx /= distance
        dy /= distance

        self._move(dx * self.speed * dt, dy * self.speed * dt, level)

    def _face_point(self, target_x: float, target_y: float) -> None:
        self.angle = math.atan2(target_y - self.y, target_x - self.x)

    def _move(self, dx: float, dy: float, level: Any) -> bool:
        moved = False

        if dx != 0.0:
            new_x = self.x + dx
            if not circle_collides(level, new_x, self.y, self.radius):
                self.x = new_x
                moved = True

        if dy != 0.0:
            new_y = self.y + dy
            if not circle_collides(level, self.x, new_y, self.radius):
                self.y = new_y
                moved = True

        return moved