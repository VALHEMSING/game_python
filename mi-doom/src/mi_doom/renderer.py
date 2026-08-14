from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Iterable

import numpy as np
import pygame
from pygame import surfarray

from mi_doom.config import (
    CEILING_COLOR,
    CROSSHAIR_COLOR,
    DEFAULT_WALL_COLOR,
    DOOR_COLORS,
    FLOOR_COLOR,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    MAX_RAY_DEPTH,
    MAX_RAY_STEPS,
    MIN_SHADE,
    PLANE_LENGTH,
    SWITCH_COLOR,
    WALL_COLORS,
    WINDOW_SIZE,
)
from mi_doom.entities import DOOR_TILES, SWITCH_TILE

if TYPE_CHECKING:
    from mi_doom.level import Level
    from mi_doom.player import Player


class Renderer:
    def __init__(self) -> None:
        self.width = INTERNAL_WIDTH
        self.height = INTERNAL_HEIGHT
        self.half_height = self.height // 2
        self.center_x = self.width // 2
        self.center_y = self.height // 2

        self.buffer = np.zeros((self.width, self.height, 3), dtype=np.uint8)
        self.zbuffer: list[float] = [MAX_RAY_DEPTH] * self.width

        self.ceiling_color = np.array(CEILING_COLOR, dtype=np.uint8)
        self.floor_color = np.array(FLOOR_COLOR, dtype=np.uint8)

    def render(
        self,
        screen: pygame.Surface,
        level: Level,
        player: Player,
        renderables: Iterable[Any],
    ) -> None:
        self._draw_flat_background()
        self._draw_walls(level, player)

        frame = surfarray.make_surface(self.buffer)

        self._draw_sprites(frame, player, renderables)

        if not player.is_dead:
            self._draw_weapon(frame, player)
            self._draw_crosshair(frame)

        scaled = pygame.transform.scale(frame, WINDOW_SIZE)
        screen.blit(scaled, (0, 0))

    def _draw_flat_background(self) -> None:
        self.buffer[:, : self.half_height] = self.ceiling_color
        self.buffer[:, self.half_height :] = self.floor_color

    def _draw_walls(self, level: Level, player: Player) -> None:
        self.zbuffer = [MAX_RAY_DEPTH] * self.width

        dir_x = math.cos(player.angle)
        dir_y = math.sin(player.angle)

        plane_x = -dir_y * PLANE_LENGTH
        plane_y = dir_x * PLANE_LENGTH

        for screen_x in range(self.width):
            camera_x = (2.0 * screen_x / self.width) - 1.0

            ray_dir_x = dir_x + plane_x * camera_x
            ray_dir_y = dir_y + plane_y * camera_x

            distance, side, tile, map_x, map_y = self._cast_ray(
                player.x,
                player.y,
                ray_dir_x,
                ray_dir_y,
                level,
            )

            self.zbuffer[screen_x] = distance

            full_line_height = int(self.height / max(distance, 0.0001))

            door = None
            if tile in DOOR_TILES:
                door = level.doors.get((map_x, map_y))

            if door is not None and door.openness > 0.0:
                visible_ratio = max(0.0, 1.0 - door.openness)
                line_height = int(full_line_height * visible_ratio)

                if line_height <= 0:
                    continue

                y0 = self.center_y - full_line_height // 2
                y1 = y0 + line_height

                y0 = max(0, y0)
                y1 = min(self.height, y1)
            else:
                line_height = full_line_height
                half_height = line_height // 2

                y0 = max(0, self.center_y - half_height)
                y1 = min(self.height, self.center_y + half_height)

            if y1 > y0:
                color = self._wall_color(tile, side, distance)
                self.buffer[screen_x, y0:y1] = color

    def _cast_ray(
        self,
        pos_x: float,
        pos_y: float,
        ray_dir_x: float,
        ray_dir_y: float,
        level: Level,
    ) -> tuple[float, int, str, int, int]:
        map_x = int(pos_x)
        map_y = int(pos_y)

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
            side_dist_x = (pos_x - float(map_x)) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (float(map_x) + 1.0 - pos_x) * delta_dist_x

        if ray_dir_y < 0.0:
            step_y = -1
            side_dist_y = (pos_y - float(map_y)) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (float(map_y) + 1.0 - pos_y) * delta_dist_y

        side = 0
        tile = "."

        for _ in range(MAX_RAY_STEPS):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1

            if level.is_solid(map_x, map_y):
                tile = level.tile_at(map_x, map_y)
                break
        else:
            return MAX_RAY_DEPTH, 0, ".", 0, 0

        if side == 0:
            perpendicular_distance = (
                float(map_x) - pos_x + (1.0 - float(step_x)) / 2.0
            ) / ray_dir_x
        else:
            perpendicular_distance = (
                float(map_y) - pos_y + (1.0 - float(step_y)) / 2.0
            ) / ray_dir_y

        perpendicular_distance = max(perpendicular_distance, 0.0001)
        return perpendicular_distance, side, tile, map_x, map_y

    def _wall_color(self, tile: str, side: int, distance: float) -> np.ndarray:
        if tile == ".":
            base = (0, 0, 0)
        elif tile in DOOR_COLORS:
            base = DOOR_COLORS[tile]
        elif tile == SWITCH_TILE:
            base = SWITCH_COLOR
        else:
            base = WALL_COLORS.get(tile, DEFAULT_WALL_COLOR)

        distance_factor = float(
            np.clip(1.0 - distance / MAX_RAY_DEPTH, MIN_SHADE, 1.0)
        )

        if side == 1:
            distance_factor *= 0.72

        color = np.array(base, dtype=np.float32)
        color *= distance_factor
        np.clip(color, 0, 255, out=color)

        return color.astype(np.uint8)

    def _draw_sprites(
        self,
        frame: pygame.Surface,
        player: Player,
        renderables: Iterable[Any],
    ) -> None:
        dir_x = math.cos(player.angle)
        dir_y = math.sin(player.angle)

        plane_x = -dir_y * PLANE_LENGTH
        plane_y = dir_x * PLANE_LENGTH

        inv_det = 1.0 / (plane_x * dir_y - dir_x * plane_y)

        visible_sprites: list[tuple[float, Any, int, int, int, int]] = []

        for entity in renderables:
            if getattr(entity, "is_dead", False):
                continue

            sprite = getattr(entity, "sprite", None)
            if sprite is None:
                continue

            rel_x = entity.x - player.x
            rel_y = entity.y - player.y

            transform_y = inv_det * (-plane_y * rel_x + plane_x * rel_y)

            if transform_y <= 0.08 or transform_y > MAX_RAY_DEPTH:
                continue

            transform_x = inv_det * (dir_y * rel_x - dir_x * rel_y)

            screen_x = int((self.width / 2.0) * (1.0 + transform_x / transform_y))

            base_height = abs(self.height / transform_y)
            sprite_height = int(base_height * float(getattr(entity, "scale", 0.7)))
            sprite_height = max(1, min(sprite_height, self.height * 3))

            aspect = sprite.get_width() / max(1, sprite.get_height())
            sprite_width = int(sprite_height * aspect)
            sprite_width = max(1, min(sprite_width, self.width * 3))

            if sprite_width <= 0 or sprite_height <= 0:
                continue

            wall_height = int(self.height / transform_y)
            floor_y = self.center_y + wall_height // 2
            top = floor_y - sprite_height

            # Si el sprite queda completamente fuera de pantalla por cercanía extrema,
            # se centra para evitar que desaparezca de forma extraña.
            if top >= self.height or top + sprite_height <= 0:
                top = self.center_y - sprite_height // 2

            visible_sprites.append(
                (
                    transform_y,
                    entity,
                    screen_x,
                    sprite_width,
                    sprite_height,
                    top,
                )
            )

        visible_sprites.sort(key=lambda item: item[0], reverse=True)

        for depth, entity, screen_x, sprite_width, sprite_height, top in visible_sprites:
            scaled = pygame.transform.scale(entity.sprite, (sprite_width, sprite_height))

            start_x = screen_x - sprite_width // 2
            end_x = start_x + sprite_width

            left = max(0, start_x)
            right = min(self.width, end_x)

            source_width = entity.sprite.get_width()

            for stripe in range(left, right):
                if depth < self.zbuffer[stripe]:
                    src_x = int((stripe - start_x) * source_width / sprite_width)

                    if 0 <= src_x < source_width:
                        frame.blit(
                            scaled,
                            (stripe, top),
                            (src_x, 0, 1, sprite_height),
                        )

    def _draw_weapon(self, frame: pygame.Surface, player: Player) -> None:
        weapon = player.current_weapon

        cooldown_ratio = min(
            1.0,
            weapon.cooldown / max(weapon.time_between_shots, 0.0001),
        )
        recoil = int(6 * cooldown_ratio)

        x = self.center_x
        y = self.height - 8 + recoil

        hand_color = (160, 120, 90)
        metal_color = (110, 110, 120)
        dark_color = (70, 70, 80)

        if weapon.id == "pistol":
            pygame.draw.rect(frame, hand_color, (x - 6, y - 8, 12, 12))
            pygame.draw.rect(frame, metal_color, (x - 3, y - 18, 6, 14))
            pygame.draw.rect(frame, dark_color, (x - 2, y - 24, 4, 8))

        elif weapon.id == "shotgun":
            pygame.draw.rect(frame, hand_color, (x - 10, y - 8, 20, 12))
            pygame.draw.rect(frame, dark_color, (x - 4, y - 22, 8, 18))
            pygame.draw.rect(frame, metal_color, (x - 6, y - 14, 12, 10))

        elif weapon.id == "machinegun":
            pygame.draw.rect(frame, hand_color, (x - 8, y - 8, 16, 12))
            pygame.draw.rect(frame, metal_color, (x - 8, y - 20, 16, 12))
            pygame.draw.rect(frame, dark_color, (x - 2, y - 28, 4, 10))

        if player.muzzle_flash_timer > 0.0:
            flash_y = y - 26
            pygame.draw.circle(frame, (255, 230, 120), (x, flash_y), 6)
            pygame.draw.circle(frame, (255, 255, 220), (x, flash_y), 3)

    def _draw_crosshair(self, frame: pygame.Surface) -> None:
        x = self.center_x
        y = self.center_y

        pygame.draw.line(frame, CROSSHAIR_COLOR, (x, y - 2), (x, y + 2))
        pygame.draw.line(frame, CROSSHAIR_COLOR, (x - 2, y), (x + 2, y))