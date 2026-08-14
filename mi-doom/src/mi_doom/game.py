from __future__ import annotations

import math

import pygame

from mi_doom.collision import circle_collides
from mi_doom.config import (
    FPS,
    LEVEL1_PATH,
    MESSAGE_COLOR,
    WINDOW_HEIGHT,
    WINDOW_SIZE,
    WINDOW_WIDTH,
)
from mi_doom.enemy import Enemy, EnemyKind
from mi_doom.entities import DOOR_TILES, SWITCH_TILE, PickupKind
from mi_doom.input import InputHandler
from mi_doom.level import Level
from mi_doom.player import Player
from mi_doom.renderer import Renderer
from mi_doom.sprite_factory import create_enemy_sprite, create_pickup_sprite


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("mi-doom - FASE 3")

        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)

        self.input = InputHandler()

        self.enemy_sprites = {
            EnemyKind.DRONE: create_enemy_sprite(EnemyKind.DRONE),
            EnemyKind.MUTANT: create_enemy_sprite(EnemyKind.MUTANT),
            EnemyKind.BEAST: create_enemy_sprite(EnemyKind.BEAST),
        }

        self.pickup_sprites = {
            PickupKind.HEALTH: create_pickup_sprite(PickupKind.HEALTH),
            PickupKind.ARMOR: create_pickup_sprite(PickupKind.ARMOR),
            PickupKind.AMMO_BULLETS: create_pickup_sprite(PickupKind.AMMO_BULLETS),
            PickupKind.AMMO_SHELLS: create_pickup_sprite(PickupKind.AMMO_SHELLS),
            PickupKind.WEAPON_SHOTGUN: create_pickup_sprite(PickupKind.WEAPON_SHOTGUN),
            PickupKind.WEAPON_MACHINEGUN: create_pickup_sprite(PickupKind.WEAPON_MACHINEGUN),
            PickupKind.KEY_RED: create_pickup_sprite(PickupKind.KEY_RED),
            PickupKind.KEY_BLUE: create_pickup_sprite(PickupKind.KEY_BLUE),
            PickupKind.KEY_YELLOW: create_pickup_sprite(PickupKind.KEY_YELLOW),
        }

        self.level = Level.load(LEVEL1_PATH)
        self._assign_pickup_sprites()

        start_x, start_y = self.level.player_start
        self.player = Player(x=start_x, y=start_y, angle=0.0)

        self.renderer = Renderer()
        self.enemies = self._create_enemies()

        self.running = True
        self.paused = False
        self.death_handled = False

        self.message = ""
        self.message_timer = 0.0

        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def run(self) -> None:
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000.0
                dt = min(dt, 0.05)

                self.message_timer = max(0.0, self.message_timer - dt)

                self.input.process_events()
                controls = self.input.get_controls()

                self._handle_system_events()

                if not self.running:
                    break

                if not self.paused:
                    if not self.player.is_dead:
                        self.player.update(dt, self.level, controls)
                        self.player.update_combat(
                            dt=dt,
                            controls=controls,
                            enemies=self.enemies,
                            level=self.level,
                        )

                        self.level.update(dt)

                        if controls.interact:
                            self._handle_interact()

                        self._update_pickups()

                        for enemy in self.enemies:
                            enemy.update(dt, self.level, self.player)

                        self.enemies = [
                            enemy for enemy in self.enemies if not enemy.is_dead
                        ]

                        self.level.pickups = [
                            pickup for pickup in self.level.pickups if pickup.active
                        ]

                if self.player.is_dead and not self.death_handled:
                    self.death_handled = True
                    pygame.mouse.set_visible(True)
                    pygame.event.set_grab(False)

                renderables = self.enemies + self.level.pickups

                self.renderer.render(
                    self.screen,
                    self.level,
                    self.player,
                    renderables,
                )

                if not self.player.is_dead and self.player.damage_flash_timer > 0.0:
                    self._draw_damage_flash()

                if not self.player.is_dead and self.message_timer > 0.0:
                    self._draw_message()

                if self.player.is_dead:
                    self._draw_death()
                elif self.paused:
                    self._draw_pause()
                else:
                    self._draw_help()

                pygame.display.flip()
        finally:
            pygame.quit()

    def _handle_system_events(self) -> None:
        if self.input.quit_requested:
            self.running = False

        if self.input.restart_requested:
            if self.player.is_dead:
                self._reset_level()
            self.input.restart_requested = False

        if self.input.toggle_pause_requested:
            if not self.player.is_dead:
                self.paused = not self.paused
                pygame.event.set_grab(not self.paused)
                pygame.mouse.set_visible(self.paused)
            self.input.toggle_pause_requested = False

    def _assign_pickup_sprites(self) -> None:
        for pickup in self.level.pickups:
            pickup.sprite = self.pickup_sprites.get(pickup.kind)

    def _create_enemies(self) -> list[Enemy]:
        enemies: list[Enemy] = []

        for spawn in self.level.enemy_spawns:
            try:
                kind = EnemyKind(str(spawn.get("type", "drone")))
                x = float(spawn.get("x", 1.5))
                y = float(spawn.get("y", 1.5))
            except (ValueError, TypeError):
                continue

            if circle_collides(self.level, x, y, 0.25):
                continue

            enemies.append(
                Enemy(
                    kind=kind,
                    x=x,
                    y=y,
                    sprite=self.enemy_sprites.get(kind),
                )
            )

        return enemies

    def _reset_level(self) -> None:
        self.level = Level.load(LEVEL1_PATH)
        self._assign_pickup_sprites()

        start_x, start_y = self.level.player_start
        self.player = Player(x=start_x, y=start_y, angle=0.0)

        self.enemies = self._create_enemies()

        self.paused = False
        self.death_handled = False
        self.message = ""
        self.message_timer = 0.0

        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def _handle_interact(self) -> None:
        target = self.level.find_interactable_in_front(self.player)

        if target is None:
            return

        tile_x, tile_y = target
        tile = self.level.tile_at(tile_x, tile_y)

        if tile in DOOR_TILES:
            _, message = self.level.try_open_door_at(target, self.player)
            if message:
                self._show_message(message)

        elif tile == SWITCH_TILE:
            activated = self.level.activate_switch(target)
            if activated:
                self._show_message("Interruptor activado")
            else:
                self._show_message("Interruptor ya activado")

    def _update_pickups(self) -> None:
        for pickup in self.level.pickups:
            if not pickup.active:
                continue

            dx = pickup.x - self.player.x
            dy = pickup.y - self.player.y
            distance = math.hypot(dx, dy)

            if distance <= self.player.radius + pickup.radius + 0.05:
                message = pickup.try_apply(self.player)
                if message is not None:
                    self._show_message(message)

    def _show_message(self, text: str, duration: float = 2.2) -> None:
        self.message = text
        self.message_timer = duration

    def _draw_help(self) -> None:
        text = self.font.render(
            "WASD mover | raton girar | click disparar | E interactuar | 1/2/3 armas | ESC pausa | Q salir",
            True,
            (220, 220, 220),
        )
        self.screen.blit(text, (10, 8))

    def _draw_message(self) -> None:
        text = self.font.render(self.message, True, MESSAGE_COLOR)
        rect = text.get_rect(center=(WINDOW_WIDTH // 2, 70))
        self.screen.blit(text, rect)

    def _draw_pause(self) -> None:
        overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.font.render("PAUSED", True, (240, 240, 240))
        hint = self.font.render("ESC resume - Q quit", True, (200, 200, 200))

        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10))

        self.screen.blit(title, title_rect)
        self.screen.blit(hint, hint_rect)

    def _draw_damage_flash(self) -> None:
        ratio = min(1.0, self.player.damage_flash_timer / 0.3)
        alpha = int(100 * ratio)

        if alpha <= 0:
            return

        overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        overlay.fill((200, 30, 20, alpha))
        self.screen.blit(overlay, (0, 0))

    def _draw_death(self) -> None:
        overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        title = self.font.render("YOU DIED", True, (230, 60, 60))
        hint = self.font.render("R restart - Q quit", True, (220, 220, 220))

        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10))

        self.screen.blit(title, title_rect)
        self.screen.blit(hint, hint_rect)