"""
Módulo que define las clases y constantes para los enemigos del juego,
incluyendo su IA, estados, estadísticas base y pathfinding.
"""
from __future__ import annotations

import math
import random
from enum import Enum, auto
from typing import Any

import pygame

from mi_doom.collision import circle_collides, line_of_sight
from mi_doom.pathfinding import find_path


class EnemyState(Enum):
    """Posibles estados de la máquina de estados de un enemigo."""
    IDLE = auto()
    PATROL = auto()
    ALERT = auto()
    CHASE = auto()
    ATTACK = auto()
    HURT = auto()
    DEAD = auto()


class EnemyKind(Enum):
    """Tipos de enemigos disponibles en el juego."""
    DRONE = "drone"
    MUTANT = "mutant"
    BEAST = "beast"


ENEMY_STATS: dict[EnemyKind, dict[str, float | int | bool]] = {
    EnemyKind.DRONE: {
        "health": 20.0,
        "speed": 2.4,
        "radius": 0.24,
        "scale": 0.52,
        "detect_range": 12.0,
        "attack_range": 7.0,
        "attack_damage": 5,
        "attack_interval": 1.2,
        "ranged": True,
        "vision_angle": math.radians(270),
    },
    EnemyKind.MUTANT: {
        "health": 50.0,
        "speed": 2.6,
        "radius": 0.30,
        "scale": 0.75,
        "detect_range": 14.0,
        "attack_range": 9.0,
        "attack_damage": 8,
        "attack_interval": 1.5,
        "ranged": True,
        "vision_angle": math.radians(220),
    },
    EnemyKind.BEAST: {
        "health": 120.0,
        "speed": 3.5,
        "radius": 0.38,
        "scale": 1.0,
        "detect_range": 16.0,
        "attack_range": 1.35,
        "attack_damage": 20,
        "attack_interval": 0.9,
        "ranged": False,
        "vision_angle": math.radians(180),
    },
}


class Enemy:
    """Representa a un enemigo en el juego con IA mejorada y pathfinding."""

    def __init__(
        self,
        kind: EnemyKind,
        x: float,
        y: float,
        sprite: pygame.Surface | None = None,
    ) -> None:
        """Inicializa al enemigo con sus estadísticas base y posición."""
        stats = ENEMY_STATS[kind]

        self.kind = kind
        self.x = x
        self.y = y
        self.sprite = sprite

        self.health = float(stats["health"])
        self.max_health = float(stats["health"])
        self.speed = float(stats["speed"])
        self.radius = float(stats["radius"])
        self.scale = float(stats["scale"])
        self.detect_range = float(stats["detect_range"])
        self.attack_range = float(stats["attack_range"])
        self.attack_damage = int(stats["attack_damage"])
        self.attack_interval = float(stats["attack_interval"])
        self.ranged = bool(stats["ranged"])
        self.vision_angle = float(stats.get("vision_angle", math.radians(180)))

        self.state = EnemyState.PATROL
        self.angle = random.uniform(0.0, math.tau)
        self.dir_angle = self.angle
        self.patrol_timer = random.uniform(1.0, 3.0)
        self.attack_timer = random.uniform(0.2, 0.8)
        self.hurt_timer = 0.0
        self.attack_anim_timer = 0.0
        self.alerted = False

        # Pathfinding
        self.path: list[tuple[int, int]] = []
        self.path_index = 0
        self.path_recalculate_timer = 0.0
        self.path_recalculate_interval = 0.5
        self.last_known_player_pos: tuple[float, float] | None = None

        # Puntos de patrulla
        self.patrol_points: list[tuple[float, float]] = []
        self.patrol_target_index = 0

    @property
    def is_dead(self) -> bool:
        """Indica si el enemigo ha sido eliminado."""
        return self.state == EnemyState.DEAD

    def take_damage(
        self,
        amount: float,
        source_pos: tuple[float, float] | None = None,
    ) -> bool:
        """Aplica daño al enemigo y gestiona su transición a estado HURT o DEAD."""
        if self.is_dead:
            return False

        self.health -= amount
        self.alerted = True

        if source_pos is not None:
            self.last_known_player_pos = source_pos

        if self.health <= 0.0:
            self.health = 0.0
            self.state = EnemyState.DEAD
            return True

        self.hurt_timer = 0.18
        self.state = EnemyState.HURT
        return False

    def update(self, dt: float, level: Any, player: Any) -> None:
        """Actualiza la IA y el estado del enemigo en cada frame."""
        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.hurt_timer = max(0.0, self.hurt_timer - dt)
        self.attack_anim_timer = max(0.0, self.attack_anim_timer - dt)
        self.path_recalculate_timer = max(0.0, self.path_recalculate_timer - dt)

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

        can_see_player = self._can_see_player(level, player, distance_to_player)

        if can_see_player:
            self.alerted = True
            self.last_known_player_pos = (player.x, player.y)

        if self.state == EnemyState.IDLE:
            self._update_idle(dt, can_see_player)

        elif self.state == EnemyState.PATROL:
            self._update_patrol(dt, level, can_see_player)

        elif self.state == EnemyState.ALERT:
            self._update_alert(dt, level, player, can_see_player, distance_to_player)

        elif self.state == EnemyState.CHASE:
            self._update_chase(dt, level, player, can_see_player, distance_to_player)

        elif self.state == EnemyState.ATTACK:
            self._update_attack(dt, level, player, can_see_player, distance_to_player)

    def _can_see_player(self, level: Any, player: Any, distance: float) -> bool:
        """
        Verifica si el enemigo puede ver al jugador.
        Considera distancia, línea de visión y ángulo de visión.
        """
        if distance > self.detect_range:
            return False

        if not line_of_sight(level, self.x, self.y, player.x, player.y):
            return False

        # Verificar ángulo de visión
        dx = player.x - self.x
        dy = player.y - self.y
        angle_to_player = math.atan2(dy, dx)
        angle_diff = abs(self._normalize_angle(angle_to_player - self.angle))

        return angle_diff <= self.vision_angle / 2.0

    def _normalize_angle(self, angle: float) -> float:
        """Normaliza un ángulo al rango [-pi, pi]."""
        while angle > math.pi:
            angle -= math.tau
        while angle < -math.pi:
            angle += math.tau
        return angle

    # ------------------------------------------------------------------
    # Estados de IA
    # ------------------------------------------------------------------

    def _update_idle(self, dt: float, can_see_player: bool) -> None:
        """Estado IDLE: el enemigo espera y puede pasar a PATROL o CHASE."""
        if can_see_player:
            self.state = EnemyState.CHASE
            return

        self.patrol_timer -= dt
        if self.patrol_timer <= 0.0:
            self.state = EnemyState.PATROL
            self.dir_angle = random.uniform(0.0, math.tau)
            self.patrol_timer = random.uniform(1.5, 3.5)

    def _update_patrol(self, dt: float, level: Any, can_see_player: bool) -> None:
        """Estado PATROL: el enemigo recorre puntos de patrulla o se mueve aleatoriamente."""
        if can_see_player:
            self.state = EnemyState.CHASE
            return

        if self.patrol_points:
            self._patrol_with_points(dt, level)
        else:
            self._patrol_random(dt, level)

    def _patrol_with_points(self, dt: float, level: Any) -> None:
        """Patrulla usando puntos de patrulla definidos."""
        if not self.patrol_points:
            return

        target_x, target_y = self.patrol_points[self.patrol_target_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance < 0.5:
            self.patrol_target_index = (self.patrol_target_index + 1) % len(self.patrol_points)
            return

        dx /= distance
        dy /= distance
        self.angle = math.atan2(dy, dx)

        self._move(dx * self.speed * 0.5 * dt, dy * self.speed * 0.5 * dt, level)

    def _patrol_random(self, dt: float, level: Any) -> None:
        """Patrulla moviéndose aleatoriamente."""
        self.patrol_timer -= dt

        if self.patrol_timer <= 0.0:
            self.dir_angle = random.uniform(0.0, math.tau)
            self.patrol_timer = random.uniform(1.5, 3.5)

        dx = math.cos(self.dir_angle) * self.speed * 0.4 * dt
        dy = math.sin(self.dir_angle) * self.speed * 0.4 * dt
        self.angle = self.dir_angle

        if not self._move(dx, dy, level):
            self.dir_angle = random.uniform(0.0, math.tau)
            self.patrol_timer = random.uniform(0.8, 2.0)

    def _update_alert(
        self,
        dt: float,
        level: Any,
        player: Any,
        can_see_player: bool,
        distance: float,
    ) -> None:
        """Estado ALERT: el enemigo investiga la última posición conocida del jugador."""
        if can_see_player:
            self.state = EnemyState.CHASE
            return

        if self.last_known_player_pos is None:
            self.state = EnemyState.PATROL
            return

        # Moverse hacia la última posición conocida usando pathfinding
        target_x, target_y = self.last_known_player_pos
        dx = target_x - self.x
        dy = target_y - self.y
        distance_to_target = math.hypot(dx, dy)

        if distance_to_target < 1.0:
            # Llegó a la última posición conocida, volver a patrullar
            self.state = EnemyState.PATROL
            self.patrol_timer = random.uniform(2.0, 4.0)
            return

        self._move_toward_with_pathfinding(dt, level, target_x, target_y)

    def _update_chase(
        self,
        dt: float,
        level: Any,
        player: Any,
        can_see_player: bool,
        distance: float,
    ) -> None:
        """Estado CHASE: el enemigo persigue al jugador usando pathfinding."""
        if not can_see_player and not self.alerted:
            self.state = EnemyState.ALERT
            return

        if can_see_player and distance <= self.attack_range:
            self.state = EnemyState.ATTACK
            return

        if can_see_player:
            # Persecución directa si tiene línea de visión
            dx = player.x - self.x
            dy = player.y - self.y
            if distance > 0.1:
                dx /= distance
                dy /= distance
                self.angle = math.atan2(dy, dx)
                self._move(dx * self.speed * dt, dy * self.speed * dt, level)
        else:
            # Usar pathfinding para encontrar al jugador
            self._move_toward_with_pathfinding(dt, level, player.x, player.y)

    def _update_attack(
        self,
        dt: float,
        level: Any,
        player: Any,
        can_see_player: bool,
        distance: float,
    ) -> None:
        """Estado ATTACK: el enemigo ataca al jugador."""
        if not can_see_player or distance > self.attack_range * 1.3:
            self.state = EnemyState.CHASE
            return

        # Mirar al jugador
        dx = player.x - self.x
        dy = player.y - self.y
        if distance > 0.1:
            self.angle = math.atan2(dy, dx)

        if self.attack_timer <= 0.0:
            player.take_damage(self.attack_damage)
            self.attack_timer = self.attack_interval
            self.attack_anim_timer = 0.18

    # ------------------------------------------------------------------
    # Movimiento con pathfinding
    # ------------------------------------------------------------------

    def _move_toward_with_pathfinding(
        self,
        dt: float,
        level: Any,
        target_x: float,
        target_y: float,
    ) -> None:
        """Mueve al enemigo hacia un objetivo usando pathfinding A*."""
        # Recalcular ruta periódicamente
        if self.path_recalculate_timer <= 0.0 or not self.path:
            start = (int(self.x), int(self.y))
            end = (int(target_x), int(target_y))

            new_path = find_path(level, start, end)
            if new_path is not None and len(new_path) > 1:
                self.path = new_path
                self.path_index = 1
            self.path_recalculate_timer = self.path_recalculate_interval

        if not self.path or self.path_index >= len(self.path):
            # Sin ruta válida, mover directamente
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.hypot(dx, dy)
            if distance > 0.1:
                dx /= distance
                dy /= distance
                self.angle = math.atan2(dy, dx)
                self._move(dx * self.speed * dt, dy * self.speed * dt, level)
            return

        # Seguir el siguiente nodo de la ruta
        node_x, node_y = self.path[self.path_index]
        target_node_x = node_x + 0.5
        target_node_y = node_y + 0.5

        dx = target_node_x - self.x
        dy = target_node_y - self.y
        distance_to_node = math.hypot(dx, dy)

        if distance_to_node < 0.4:
            self.path_index += 1
            return

        dx /= distance_to_node
        dy /= distance_to_node
        self.angle = math.atan2(dy, dx)

        self._move(dx * self.speed * dt, dy * self.speed * dt, level)

    # ------------------------------------------------------------------
    # Movimiento y colisiones
    # ------------------------------------------------------------------

    def _move(self, dx: float, dy: float, level: Any) -> bool:
        """Intenta desplazar al enemigo aplicando detección de colisiones."""
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
