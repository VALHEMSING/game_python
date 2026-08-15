"""
Módulo encargado del renderizado del mundo 3D mediante raycasting,
así como el dibujo de sprites, partículas, armas y efectos de pantalla.
"""
# pylint: disable=no-member

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, Iterable

import numpy as np
import pygame
from pygame import surfarray

from mi_doom.assets import TextureManager
from mi_doom.config import (
    CEILING_COLOR,
    CROSSHAIR_COLOR,
    FLOOR_COLOR,
    INTERNAL_HEIGHT,
    INTERNAL_WIDTH,
    MAX_RAY_DEPTH,
    MAX_RAY_STEPS,
    MIN_SHADE,
    PLANE_LENGTH,
    WINDOW_SIZE,
)
from mi_doom.entities import DOOR_TILES, EXIT_TILE, SWITCH_TILE

if TYPE_CHECKING:
    from mi_doom.level import Level
    from mi_doom.player import Player


class Renderer:
    """Gestiona el búfer de pantalla y el renderizado de todos los elementos visuales."""

    def __init__(self, textures: TextureManager) -> None:
        """Inicializa el renderizador, el z-buffer y carga el gestor de texturas."""
        self.width = INTERNAL_WIDTH
        self.height = INTERNAL_HEIGHT
        self.half_height = self.height // 2
        self.center_x = self.width // 2
        self.center_y = self.height // 2

        self.buffer = np.zeros((self.width, self.height, 3), dtype=np.uint8)
        self.zbuffer: list[float] = [MAX_RAY_DEPTH] * self.width

        # Colores base para techo y suelo (usados como fallback o base para gradientes)
        self.ceiling_color = np.array(CEILING_COLOR, dtype=np.float32)
        self.floor_color = np.array(FLOOR_COLOR, dtype=np.float32)

        # Texturas procedurales (opcionales, cargadas desde TextureManager)
        self.floor_texture: np.ndarray | None = None
        self.ceiling_texture: np.ndarray | None = None

        self.textures = textures

    def load_floor_ceiling_textures(self, texture_manager: TextureManager) -> None:
        """Carga las texturas de suelo y techo desde el gestor de texturas."""
        self.floor_texture = texture_manager.get("floor")
        self.ceiling_texture = texture_manager.get("ceiling")

    def render(
        self,
        screen: pygame.Surface,
        level: Level,
        player: Player,
        renderables: Iterable[Any],
        screen_shake_offset: tuple[int, int] = (0, 0),
    ) -> None:
        """Orquesta el renderizado completo de un frame del juego."""
        self._draw_flat_background()
        self._draw_walls(level, player)

        frame = surfarray.make_surface(self.buffer)

        self._draw_sprites(frame, player, renderables)

        if not player.is_dead:
            self._draw_weapon(frame, player)
            self._draw_crosshair(frame)

        scaled = pygame.transform.scale(frame, WINDOW_SIZE)

        screen.fill((0, 0, 0))
        screen.blit(scaled, screen_shake_offset)

    def _draw_flat_background(self) -> None:
        """Dibuja suelo y techo texturizados usando floor/ceiling casting."""
        if self.floor_texture is None or self.ceiling_texture is None:
            # Fallback: gradientes si no hay texturas cargadas
            self._draw_gradient_floor_ceiling()
            return

        self._draw_gradient_floor_ceiling()

    def _draw_gradient_floor_ceiling(self) -> None:
        """Dibuja suelo y techo con gradiente de distancia para dar profundidad."""
        # Techo: gradiente de oscuro (arriba, lejos) a más claro (centro, cerca del horizonte)
        for y in range(self.half_height):
            ratio = y / max(1, self.half_height)
            shade = 0.3 + 0.7 * ratio
            color = (self.ceiling_color * shade).astype(np.uint8)
            self.buffer[:, y] = color

        # Suelo: gradiente de más claro (centro, cerca del horizonte) a oscuro (abajo, cerca)
        for y in range(self.half_height, self.height):
            ratio = (y - self.half_height) / max(1, self.half_height)
            shade = 1.0 - 0.6 * ratio
            color = (self.floor_color * shade).astype(np.uint8)
            self.buffer[:, y] = color

    def _draw_walls(self, level: Level, player: Player) -> None:
        """Lanza los rayos para dibujar las paredes, puertas y texturas."""
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

            texture_name = self._texture_name_for_tile(tile, map_x, map_y)
            texture = self.textures.get(texture_name)

            if side == 0:
                wall_x = player.y + distance * ray_dir_y
            else:
                wall_x = player.x + distance * ray_dir_x

            wall_x -= math.floor(wall_x)

            texture_height, texture_width, _ = texture.shape
            texture_x = int(wall_x * texture_width)
            texture_x = max(0, min(texture_x, texture_width - 1))

            shade = float(np.clip(1.0 - distance / MAX_RAY_DEPTH, MIN_SHADE, 1.0))
            if side == 1:
                shade *= 0.72

            door = None
            if tile in DOOR_TILES:
                door = level.doors.get((map_x, map_y))

            if door is not None and door.openness > 0.0:
                visible_height = int(
                    full_line_height * max(0.0, 1.0 - door.openness)
                )

                if visible_height <= 0:
                    continue

                top = float(self.center_y - full_line_height // 2)
                draw_start = max(0, int(top))
                draw_end = min(self.height, int(top + visible_height))

                self._blit_texture_column(
                    screen_x=screen_x,
                    texture=texture,
                    texture_x=texture_x,
                    top=top,
                    mapping_height=visible_height,
                    draw_start=draw_start,
                    draw_end=draw_end,
                    shade=shade,
                )
            else:
                top = float(self.center_y - full_line_height // 2)
                draw_start = max(0, int(top))
                draw_end = min(self.height, int(top + full_line_height))

                self._blit_texture_column(
                    screen_x=screen_x,
                    texture=texture,
                    texture_x=texture_x,
                    top=top,
                    mapping_height=full_line_height,
                    draw_start=draw_start,
                    draw_end=draw_end,
                    shade=shade,
                )

    def _blit_texture_column(
        self,
        screen_x: int,
        texture: np.ndarray,
        texture_x: int,
        top: float,
        mapping_height: float,
        draw_start: int,
        draw_end: int,
        shade: float,
    ) -> None:
        """Dibuja una columna vertical de una textura en el búfer de pantalla."""
        if draw_end <= draw_start:
            return

        texture_height, _, _ = texture.shape

        screen_ys = np.arange(draw_start, draw_end, dtype=np.float32)
        texture_ys = (
            (screen_ys - top) * texture_height / max(1.0, float(mapping_height))
        ).astype(np.int32)

        np.clip(texture_ys, 0, texture_height - 1, out=texture_ys)

        pixels = texture[texture_ys, texture_x].astype(np.float32)
        pixels *= shade
        np.clip(pixels, 0, 255, out=pixels)

        self.buffer[screen_x, draw_start:draw_end] = pixels.astype(np.uint8)

    def _texture_name_for_tile(self, tile: str, map_x: int, map_y: int) -> str:
        """Determina qué textura procedural debe usarse para un tile específico."""
        if tile == "D":
            return "door_d"
        if tile == "R":
            return "door_r"
        if tile == "B":
            return "door_b"
        if tile == "Y":
            return "door_y"
        if tile == SWITCH_TILE:
            return "switch"
        if tile == EXIT_TILE:
            return "exit"

        variants = (
            "concrete",
            "stone",
            "metal",
            "tech",
            "dark_wall",
        )

        return variants[(map_x * 7 + map_y * 13) % len(variants)]

    def _cast_ray(
        self,
        pos_x: float,
        pos_y: float,
        ray_dir_x: float,
        ray_dir_y: float,
        level: Level,
    ) -> tuple[float, int, str, int, int]:
        """Lanza un rayo usando DDA hasta encontrar una pared sólida."""
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

    def _draw_sprites(
        self,
        frame: pygame.Surface,
        player: Player,
        renderables: Iterable[Any],
    ) -> None:
        """Proyecta y dibuja los sprites ordenados por profundidad usando el z-buffer."""
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

            screen_x = int(
                (self.width / 2.0) * (1.0 + transform_x / transform_y)
            )

            base_height = abs(self.height / transform_y)
            sprite_height = int(
                base_height * float(getattr(entity, "scale", 0.7))
            )
            sprite_height = max(1, min(sprite_height, self.height * 3))

            aspect = sprite.get_width() / max(1, sprite.get_height())
            sprite_width = int(sprite_height * aspect)
            sprite_width = max(1, min(sprite_width, self.width * 3))

            if sprite_width <= 0 or sprite_height <= 0:
                continue

            # Centrar el sprite verticalmente en la pantalla (alineado con crosshair)
            top = self.center_y - sprite_height // 2

            if sprite_height > self.height:
                top = self.center_y - self.height // 2

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

        for (
            depth,
            entity,
            screen_x,
            sprite_width,
            sprite_height,
            top,
        ) in visible_sprites:
            scaled = pygame.transform.scale(
                entity.sprite, (sprite_width, sprite_height)
            )

            distance_shade = max(0.35, min(1.0, 1.0 - depth / MAX_RAY_DEPTH))
            if distance_shade < 0.95:
                scaled.set_alpha(int(255 * distance_shade))

            start_x = screen_x - sprite_width // 2
            end_x = start_x + sprite_width

            left = max(0, start_x)
            right = min(self.width, end_x)

            source_width = entity.sprite.get_width()

            # OPTIMIZACIÓN: Agrupar columnas contiguas visibles
            stripe = left
            while stripe < right:
                if depth < self.zbuffer[stripe]:
                    chunk_start = stripe
                    src_x_start = int(
                        (stripe - start_x) * source_width / sprite_width
                    )

                    while stripe < right and depth < self.zbuffer[stripe]:
                        stripe += 1

                    chunk_end = stripe
                    src_x_end = int(
                        (chunk_end - start_x) * source_width / sprite_width
                    )

                    chunk_width = src_x_end - src_x_start
                    if chunk_width > 0:
                        frame.blit(
                            scaled,
                            (chunk_start, top),
                            (src_x_start, 0, chunk_width, sprite_height),
                        )
                else:
                    stripe += 1

    def _draw_weapon(self, frame: pygame.Surface, player: Player) -> None:
        """Dibuja el arma equipada en la parte inferior con retroceso y balanceo."""
        weapon = player.current_weapon

        cooldown_ratio = min(
            1.0,
            weapon.cooldown / max(weapon.time_between_shots, 0.0001),
        )
        recoil = int(6 * cooldown_ratio)

        moving = bool(getattr(player, "is_moving", False))
        bob_time = float(getattr(player, "bob_time", 0.0))

        if moving:
            bob_x = int(math.sin(bob_time) * 4.0)
            bob_y = int(abs(math.cos(bob_time)) * 3.0)
        else:
            bob_x = 0
            bob_y = 0

        x = self.center_x + bob_x
        y = self.height - 8 + recoil + bob_y

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
        """Dibuja el punto de mira en el centro de la pantalla."""
        x = self.center_x
        y = self.center_y

        pygame.draw.line(frame, CROSSHAIR_COLOR, (x, y - 2), (x, y + 2))
        pygame.draw.line(frame, CROSSHAIR_COLOR, (x - 2, y), (x + 2, y))
