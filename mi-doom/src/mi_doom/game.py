"""
Módulo principal del juego. Contiene la clase Game que orquesta el bucle principal,
los estados, los menús y la integración de todos los sistemas del motor.
"""
# pylint: disable=no-member

from __future__ import annotations

import json
import math
import random
import tempfile
from enum import Enum, auto
from pathlib import Path

import pygame

from mi_doom.assets import TextureManager
from mi_doom.audio import AudioManager
from mi_doom.collision import circle_collides
from mi_doom.config import (
    FPS,
    LEVEL1_PATH,
    LEVEL_FILENAMES,
    LEVELS_DIR,
    MESSAGE_COLOR,
    MOUSE_SENSITIVITY,
    SAMPLE_RATE,
    WINDOW_HEIGHT,
    WINDOW_SIZE,
    WINDOW_WIDTH,
)
from mi_doom.enemy import Enemy, EnemyKind
from mi_doom.entities import (
    DOOR_TILES,
    EXIT_TILE,
    SWITCH_TILE,
    Decoration,
    DecorationKind,
    PickupKind,
)
from mi_doom.input import InputHandler, MenuControls, PlayerControls
from mi_doom.level import Level
from mi_doom.level_generator import LevelGenerator
from mi_doom.menu import Menu, MenuItem
from mi_doom.particles import ParticleSystem
from mi_doom.player import Player
from mi_doom.renderer import Renderer
from mi_doom.sprite_factory import (
    create_decoration_sprite,
    create_enemy_sprite,
    create_particle_surface,
    create_pickup_sprite,
)


class GameState(Enum):
    """Enumeración de los posibles estados del flujo del juego."""
    MAIN_MENU = auto()
    LEVEL_SELECT = auto()
    OPTIONS = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class Game:
    """Clase principal que gestiona el bucle del juego, estados y renderizado."""

    def __init__(self) -> None:
        """Inicializa Pygame, carga assets, configura menús y prepara el nivel inicial."""
        # Inicialización explícita de atributos para evitar W0201
        self.screen: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.title_font: pygame.font.Font | None = None
        self.menu_font: pygame.font.Font | None = None
        self.hud_font: pygame.font.Font | None = None
        self.message_font: pygame.font.Font | None = None

        self.input: InputHandler | None = None
        self.audio: AudioManager | None = None
        self.texture_manager: TextureManager | None = None
        self.renderer: Renderer | None = None

        self.enemy_sprites: dict[EnemyKind, pygame.Surface] = {}
        self.pickup_sprites: dict[PickupKind, pygame.Surface] = {}
        self.particle_sprites: dict[str, pygame.Surface] = {}
        self.decoration_sprites: dict[str, pygame.Surface] = {}

        self.level_paths: list[Path] = []
        self.level: Level | None = None
        self.player: Player | None = None
        self.enemies: list[Enemy] = []
        self.particles: ParticleSystem | None = None
        self.decorations: list[Decoration] = []

        self.main_menu: Menu | None = None
        self.level_select_menu: Menu | None = None
        self.options_menu: Menu | None = None
        self.pause_menu: Menu | None = None
        self.game_over_menu: Menu | None = None
        self.victory_menu: Menu | None = None

        self.score: int = 0
        self.score_at_level_start: int = 0
        self.current_level_index: int = 0
        self.mouse_sensitivity: float = MOUSE_SENSITIVITY

        self.message: str = ""
        self.message_timer: float = 0.0

        self.running: bool = False
        self.state: GameState = GameState.MAIN_MENU

        # Inicializar mixer antes de pygame.init()
        try:
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        pygame.init()
        pygame.display.set_caption("mi-doom - FASE 10")

        # PRIMERO: Inicializar display (necesario para convert_alpha)
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()

        # SEGUNDO: Crear fuentes
        self.title_font = pygame.font.Font(None, 96)
        self.menu_font = pygame.font.Font(None, 48)
        self.hud_font = pygame.font.Font(None, 32)
        self.message_font = pygame.font.Font(None, 40)

        # TERCERO: Crear handlers y managers
        self.input = InputHandler()
        self.audio = AudioManager()
        self.texture_manager = TextureManager()

        # CUARTO: Crear todos los sprites (AHORA el display ya existe)
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
            PickupKind.SECRET: create_pickup_sprite(PickupKind.SECRET),
        }

        self.particle_sprites = {
            "red": create_particle_surface((220, 70, 50)),
            "yellow": create_particle_surface((240, 220, 90)),
            "green": create_particle_surface((110, 220, 120)),
        }

        self.decoration_sprites = {
            "torch": create_decoration_sprite("torch"),
            "column": create_decoration_sprite("column"),
            "barrel": create_decoration_sprite("barrel"),
            "console": create_decoration_sprite("console"),
            "skull": create_decoration_sprite("skull"),
        }

        # QUINTO: Continuar con la inicialización
        self.level_paths = [LEVELS_DIR / name for name in LEVEL_FILENAMES]
        self.particles = ParticleSystem()

        self._create_menus()
        self._load_level(0)

        self.renderer = Renderer(self.texture_manager)
        self.renderer.load_floor_ceiling_textures(self.texture_manager)

        self.running = True
        self._set_state(GameState.MAIN_MENU)

    def run(self) -> None:
        """Ejecuta el bucle principal del juego hasta que se solicite salir."""
        try:
            while self.running:
                dt = self.clock.tick(FPS) / 1000.0
                dt = min(dt, 0.05)

                self.message_timer = max(0.0, self.message_timer - dt)
                self.input.process_events()

                if self.state == GameState.PLAYING:
                    controls = self.input.get_controls()
                    self._handle_gameplay(dt, controls)

                    if not self.running:
                        break

                    if self.state == GameState.PLAYING:
                        self._render_world()
                        self._draw_muzzle_flash_overlay()
                        self._draw_hud()

                        if self.player.damage_flash_timer > 0.0:
                            self._draw_damage_flash()

                        if self.message_timer > 0.0:
                            self._draw_message()

                elif self.state == GameState.PAUSED:
                    controls = self.input.get_menu_controls()
                    self._handle_pause_menu(controls)

                    if not self.running:
                        break

                    if self.state == GameState.PAUSED:
                        self._render_world()
                        self._draw_dark_overlay(160)
                        self.pause_menu.draw(
                            self.screen, self.title_font, self.menu_font
                        )

                elif self.state == GameState.GAME_OVER:
                    controls = self.input.get_menu_controls()
                    self._handle_game_over_menu(controls)

                    if not self.running:
                        break

                    if self.state == GameState.GAME_OVER:
                        self._render_world()
                        self._draw_dark_overlay(190)
                        self.game_over_menu.draw(
                            self.screen, self.title_font, self.menu_font
                        )

                elif self.state == GameState.VICTORY:
                    controls = self.input.get_menu_controls()
                    self._handle_victory_menu(controls)

                    if not self.running:
                        break

                    if self.state == GameState.VICTORY:
                        self.screen.fill((0, 0, 0))
                        self.victory_menu.draw(
                            self.screen, self.title_font, self.menu_font
                        )

                else:
                    controls = self.input.get_menu_controls()

                    if self.state == GameState.MAIN_MENU:
                        self._handle_main_menu(controls)
                    elif self.state == GameState.LEVEL_SELECT:
                        self._handle_level_select_menu(controls)
                    elif self.state == GameState.OPTIONS:
                        self._handle_options_menu(controls)

                    if not self.running:
                        break

                    if self.state == GameState.MAIN_MENU:
                        self._draw_menu_background()
                        self.main_menu.draw(
                            self.screen, self.title_font, self.menu_font
                        )
                    elif self.state == GameState.LEVEL_SELECT:
                        self._draw_menu_background()
                        self.level_select_menu.draw(
                            self.screen, self.title_font, self.menu_font
                        )
                    elif self.state == GameState.OPTIONS:
                        self._draw_menu_background()
                        self.options_menu.draw(
                            self.screen, self.title_font, self.menu_font
                        )

                pygame.display.flip()
        finally:
            pygame.quit()

    def _set_state(self, state: GameState) -> None:
        """Cambia el estado actual del juego y ajusta la captura del ratón."""
        self.state = state

        if state == GameState.PLAYING:
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
        else:
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)

        self._update_music()

    def _update_music(self) -> None:
        """Reproduce o detiene la música de fondo según el estado actual."""
        if self.state in (
            GameState.MAIN_MENU,
            GameState.LEVEL_SELECT,
            GameState.OPTIONS,
            GameState.PLAYING,
            GameState.PAUSED,
            GameState.GAME_OVER,
            GameState.VICTORY,
        ):
            self.audio.play_music("theme")
        else:
            self.audio.stop_music()

    def _goto_main_menu(self) -> None:
        """Resetea el menú principal y cambia el estado a MAIN_MENU."""
        self.main_menu.reset()
        self._set_state(GameState.MAIN_MENU)

    def _start_level(self, index: int, reset_score: bool = False) -> None:
        """Inicia un nivel específico, opcionalmente reiniciando la puntuación."""
        if reset_score:
            self.score = 0

        self.score_at_level_start = self.score
        self._load_level(index)

        self.message = ""
        self.message_timer = 0.0

        self._set_state(GameState.PLAYING)

    def _start_random_level(self, seed: int | None = None) -> None:
        """Inicia un nivel generado proceduralmente."""
        if self.current_level_index >= 0:
            difficulty = self.current_level_index + 1
        else:
            difficulty = 1
        difficulty = max(1, difficulty)

        generator = LevelGenerator(
            seed=seed,
            width=32,
            height=32,
            difficulty=difficulty,
        )
        level_data = generator.generate()

        temp_dir = tempfile.gettempdir()
        temp_path = (
            Path(temp_dir) / f"mi_doom_procedural_{generator.seed_used}.json"
        )

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(level_data, f)

        self.score_at_level_start = self.score
        self._load_level_from_path(temp_path)

        self.message = f"Nivel Procedural - Semilla {generator.seed_used}"
        self.message_timer = 3.0

        self._set_state(GameState.PLAYING)

    def _restart_level(self) -> None:
        """Reinicia el nivel actual y restaura la puntuación al inicio del mismo."""
        self.score = self.score_at_level_start

        if self.current_level_index == -1 and self.level is not None:
            seed = None
            if "Semilla" in self.level.name:
                try:
                    seed = int(self.level.name.split("Semilla")[-1].strip())
                except ValueError:
                    pass
            self._start_random_level(seed)
        else:
            self._load_level(self.current_level_index)

        self.message = ""
        self.message_timer = 0.0

        self._set_state(GameState.PLAYING)

    def _complete_level(self) -> None:
        """Gestiona la finalización de un nivel, pasando al siguiente o a la victoria."""
        self.score += 1000

        if self.current_level_index == -1:
            self.current_level_index += 1
            self._start_random_level()
            return

        if (
            not self.level_paths
            or self.current_level_index >= len(self.level_paths) - 1
        ):
            self.victory_menu.subtitle = f"YOU WIN - SCORE: {self.score:06d}"
            self.victory_menu.reset()
            self._set_state(GameState.VICTORY)
        else:
            self._start_level(self.current_level_index + 1, reset_score=False)

    def _load_level(self, index: int) -> None:
        """Carga un nivel desde disco, instanciando jugador, enemigos y pickups."""
        if not self.level_paths:
            path = LEVEL1_PATH
            index = 0
        else:
            index = max(0, min(index, len(self.level_paths) - 1))
            path = self.level_paths[index]

        self.current_level_index = index
        self.level = Level.load(path)
        self._assign_pickup_sprites()

        start_x, start_y = self.level.player_start
        self.player = Player(
            x=start_x,
            y=start_y,
            angle=0.0,
            mouse_sensitivity=self.mouse_sensitivity,
        )

        self.enemies = self._create_enemies()
        self.decorations = self._create_decorations()
        self.particles.clear()

    def _load_level_from_path(self, path: Path) -> None:
        """Carga un nivel desde una ruta de archivo específica."""
        self.current_level_index = -1
        self.level = Level.load(path)
        self._assign_pickup_sprites()

        start_x, start_y = self.level.player_start
        self.player = Player(
            x=start_x,
            y=start_y,
            angle=0.0,
            mouse_sensitivity=self.mouse_sensitivity,
        )

        self.enemies = self._create_enemies()
        self.decorations = self._create_decorations()
        self.particles.clear()

    def _assign_pickup_sprites(self) -> None:
        """Asocia los sprites generados a los pickups del nivel actual."""
        for pickup in self.level.pickups:
            pickup.sprite = self.pickup_sprites.get(pickup.kind)

    def _create_enemies(self) -> list[Enemy]:
        """Instancia los enemigos definidos en el nivel actual."""
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

    def _create_decorations(self) -> list[Decoration]:
        """Instancia decoraciones definidas en el nivel actual."""
        decorations: list[Decoration] = []

        if not hasattr(self.level, "decorations"):
            return decorations

        for deco_data in self.level.decorations:
            try:
                kind_str = str(deco_data.get("type", "torch"))
                x = float(deco_data.get("x", 1.5))
                y = float(deco_data.get("y", 1.5))
            except (ValueError, TypeError):
                continue

            sprite = self.decoration_sprites.get(kind_str)
            if sprite is not None:
                decorations.append(
                    Decoration(
                        kind=DecorationKind(kind_str),
                        x=x,
                        y=y,
                        sprite=sprite,
                    )
                )

        return decorations

    def _create_menus(self) -> None:
        """Construye todas las instancias de los menús del juego."""
        self.main_menu = Menu(
            "MI-DOOM",
            [
                MenuItem("NEW GAME", "new_game"),
                MenuItem("RANDOM LEVEL", "random_level"),
                MenuItem("SELECT LEVEL", "level_select"),
                MenuItem("OPTIONS", "options"),
                MenuItem("QUIT", "quit"),
            ],
        )

        self.level_select_menu = self._create_level_select_menu()

        self.options_menu = Menu(
            "OPTIONS",
            [
                MenuItem(self._sensitivity_label(), "sensitivity"),
                MenuItem("BACK", "back"),
            ],
        )

        self.pause_menu = Menu(
            "PAUSED",
            [
                MenuItem("RESUME", "resume"),
                MenuItem("RESTART LEVEL", "restart_level"),
                MenuItem("MAIN MENU", "main_menu"),
            ],
        )

        self.game_over_menu = Menu(
            "YOU DIED",
            [
                MenuItem("RESTART", "restart_level"),
                MenuItem("MAIN MENU", "main_menu"),
            ],
        )

        self.victory_menu = Menu(
            "MISSION COMPLETE",
            [
                MenuItem("MAIN MENU", "main_menu"),
                MenuItem("QUIT", "quit"),
            ],
            subtitle="YOU WIN",
        )

    def _create_level_select_menu(self) -> Menu:
        """Construye el menú de selección de nivel basado en los archivos existentes."""
        items: list[MenuItem] = []

        for index, path in enumerate(self.level_paths):
            items.append(
                MenuItem(
                    f"LEVEL {index + 1}",
                    f"start_level_{index}",
                    enabled=path.exists(),
                )
            )

        items.append(MenuItem("BACK", "back"))

        return Menu("SELECT LEVEL", items)

    def _sensitivity_label(self) -> str:
        """Genera la cadena de texto para la opción de sensibilidad en el menú."""
        return f"MOUSE SENSITIVITY: {self.mouse_sensitivity:.4f}"

    def _update_options_label(self) -> None:
        """Actualiza la etiqueta de sensibilidad en el menú de opciones."""
        if self.options_menu.items:
            self.options_menu.items[0].label = self._sensitivity_label()

    def _handle_main_menu(self, controls: MenuControls) -> None:
        """Procesa la entrada y las acciones del menú principal."""
        if self.input.quit_requested or controls.back:
            self.input.quit_requested = False
            self.running = False
            return

        action = self.main_menu.handle_controls(controls)

        if action:
            self.audio.play_sfx("menu")

        if action == "new_game":
            self._start_level(0, reset_score=True)

        elif action == "random_level":
            self._start_random_level()

        elif action == "level_select":
            self.level_select_menu.reset()
            self._set_state(GameState.LEVEL_SELECT)

        elif action == "options":
            self._update_options_label()
            self.options_menu.reset()
            self._set_state(GameState.OPTIONS)

        elif action == "quit":
            self.running = False

    def _handle_level_select_menu(self, controls: MenuControls) -> None:
        """Procesa la entrada y las acciones del menú de selección de nivel."""
        if self.input.quit_requested or controls.back:
            self.input.quit_requested = False
            self._goto_main_menu()
            return

        action = self.level_select_menu.handle_controls(controls)

        if action:
            self.audio.play_sfx("menu")

        if action == "back":
            self._goto_main_menu()

        elif action is not None and action.startswith("start_level_"):
            try:
                level_index = int(action.split("_")[-1])
            except ValueError:
                level_index = 0

            self._start_level(level_index, reset_score=True)

    def _handle_options_menu(self, controls: MenuControls) -> None:
        """Procesa la entrada y las acciones del menú de opciones."""
        if self.input.quit_requested or controls.back:
            self.input.quit_requested = False
            self._goto_main_menu()
            return

        if controls.left:
            self.mouse_sensitivity = max(
                0.0010, self.mouse_sensitivity - 0.0005
            )
            self._update_options_label()

            if hasattr(self, "player") and self.player is not None:
                self.player.mouse_sensitivity = self.mouse_sensitivity

        if controls.right:
            self.mouse_sensitivity = min(
                0.0060, self.mouse_sensitivity + 0.0005
            )
            self._update_options_label()

            if hasattr(self, "player") and self.player is not None:
                self.player.mouse_sensitivity = self.mouse_sensitivity

        action = self.options_menu.handle_controls(controls)

        if action:
            self.audio.play_sfx("menu")

        if action == "back":
            self._goto_main_menu()

    def _handle_pause_menu(self, controls: MenuControls) -> None:
        """Procesa la entrada y las acciones del menú de pausa."""
        if self.input.quit_requested:
            self.input.quit_requested = False
            self.running = False
            return

        if controls.back:
            self._set_state(GameState.PLAYING)
            return

        action = self.pause_menu.handle_controls(controls)

        if action:
            self.audio.play_sfx("menu")

        if action == "resume":
            self._set_state(GameState.PLAYING)

        elif action == "restart_level":
            self._restart_level()

        elif action == "main_menu":
            self._goto_main_menu()

    def _handle_game_over_menu(self, controls: MenuControls) -> None:
        """Procesa la entrada y las acciones del menú de Game Over."""
        if self.input.quit_requested:
            self.input.quit_requested = False
            self.running = False
            return

        if controls.back:
            self._goto_main_menu()
            return

        action = self.game_over_menu.handle_controls(controls)

        if action:
            self.audio.play_sfx("menu")

        if action == "restart_level":
            self._restart_level()

        elif action == "main_menu":
            self._goto_main_menu()

    def _handle_victory_menu(self, controls: MenuControls) -> None:
        """Procesa la entrada y las acciones del menú de victoria."""
        if self.input.quit_requested:
            self.input.quit_requested = False
            self.running = False
            return

        if controls.back:
            self._goto_main_menu()
            return

        action = self.victory_menu.handle_controls(controls)

        if action:
            self.audio.play_sfx("menu")

        if action == "main_menu":
            self._goto_main_menu()

        elif action == "quit":
            self.running = False

    def _handle_gameplay(self, dt: float, controls: PlayerControls) -> None:
        """Gestiona la lógica principal de un frame de juego activo."""
        if self.input.quit_requested:
            self.input.quit_requested = False
            self.running = False
            return

        if self.input.toggle_pause_requested:
            self.input.toggle_pause_requested = False
            self.pause_menu.reset()
            self._set_state(GameState.PAUSED)
            return

        if controls.weapon_slot is not None:
            if controls.weapon_slot in self.player.weapons:
                self.player.current_weapon_slot = controls.weapon_slot
            else:
                self._show_message("Arma no disponible")

        self.player.update(dt, self.level, controls)

        fired, hit_count, killed_count, hit_targets = self.player.update_combat(
            dt=dt,
            controls=controls,
            enemies=self.enemies,
            level=self.level,
        )

        if fired:
            self.audio.play_sfx(self.player.current_weapon.id)

        if hit_count > 0:
            self.audio.play_sfx("impact")
            self._spawn_hit_particles(hit_targets)

        if killed_count > 0:
            self.score += killed_count * 100
            self.audio.play_sfx("death")

        self.level.update(dt)

        if controls.interact:
            self._handle_interact()

            if self.state != GameState.PLAYING:
                return

        self._update_pickups()

        for enemy in self.enemies:
            enemy.update(dt, self.level, self.player)

        if self.player.damage_sound_requested:
            self.audio.play_sfx("damage")
            self.player.damage_sound_requested = False

        self.particles.update(dt)

        self.enemies = [enemy for enemy in self.enemies if not enemy.is_dead]
        self.level.pickups = [
            pickup for pickup in self.level.pickups if pickup.active
        ]

        if self.player.is_dead:
            self.game_over_menu.reset()
            self._set_state(GameState.GAME_OVER)

    def _handle_interact(self) -> None:
        """Gestiona la interacción del jugador con puertas, interruptores y salidas."""
        target = self.level.find_interactable_in_front(self.player)

        if target is None:
            return

        tile_x, tile_y = target
        tile = self.level.tile_at(tile_x, tile_y)

        if tile in DOOR_TILES:
            opened, message = self.level.try_open_door_at(target, self.player)

            if message:
                self._show_message(message)

            if opened:
                self.audio.play_sfx("door")

        elif tile == SWITCH_TILE:
            activated = self.level.activate_switch(target)

            if activated:
                self._show_message("Interruptor activado")
                self.audio.play_sfx("switch")
            else:
                self._show_message("Interruptor ya activado")

        elif tile == EXIT_TILE:
            self.audio.play_sfx("exit")
            self._complete_level()

    def _update_pickups(self) -> None:
        """Comprueba colisiones con pickups y aplica sus efectos al jugador."""
        for pickup in self.level.pickups:
            if not pickup.active:
                continue

            dx = pickup.x - self.player.x
            dy = pickup.y - self.player.y
            distance = math.hypot(dx, dy)

            if distance <= self.player.radius + pickup.radius + 0.05:
                message = pickup.try_apply(self.player)

                if message is not None:
                    if pickup.kind == PickupKind.SECRET:
                        self.score += 500
                        self.audio.play_sfx("key")
                        self._show_message(
                            "¡SECRETO ENCONTRADO! +500", duration=3.0
                        )
                    else:
                        self.score += 10
                        if pickup.kind in (
                            PickupKind.KEY_RED,
                            PickupKind.KEY_BLUE,
                            PickupKind.KEY_YELLOW,
                        ):
                            self.audio.play_sfx("key")
                        else:
                            self.audio.play_sfx("pickup")
                        self._show_message(message)

    def _spawn_hit_particles(self, targets: list[object]) -> None:
        """Genera partículas de impacto o muerte en las posiciones de los enemigos."""
        for target in targets:
            if getattr(target, "is_dead", False):
                self.particles.spawn_burst(
                    x=target.x,
                    y=target.y,
                    sprite=self.particle_sprites["red"],
                    count=14,
                    speed=2.6,
                    ttl=0.45,
                    scale=0.16,
                )
            else:
                self.particles.spawn_burst(
                    x=target.x,
                    y=target.y,
                    sprite=self.particle_sprites["red"],
                    count=6,
                    speed=1.8,
                    ttl=0.30,
                    scale=0.11,
                )

    def _show_message(self, text: str, duration: float = 2.2) -> None:
        """Muestra un mensaje temporal en la parte superior de la pantalla."""
        self.message = text
        self.message_timer = duration

    def _render_world(self) -> None:
        """Orquesta el renderizado del mundo 3D, sprites y partículas."""
        offset = self._get_screen_shake_offset()
        renderables = (
            self.enemies
            + self.level.pickups
            + self.decorations
            + self.particles.particles
        )

        self.renderer.render(
            self.screen,
            self.level,
            self.player,
            renderables,
            screen_shake_offset=offset,
        )

    def _get_screen_shake_offset(self) -> tuple[int, int]:
        """Calcula el desplazamiento aleatorio para el efecto de screen shake."""
        if self.state != GameState.PLAYING:
            return (0, 0)

        if self.player.damage_flash_timer <= 0.0:
            return (0, 0)

        ratio = min(1.0, self.player.damage_flash_timer / 0.3)
        magnitude = int(6 * ratio)

        if magnitude <= 0:
            return (0, 0)

        return (
            random.randint(-magnitude, magnitude),
            random.randint(-magnitude, magnitude),
        )

    def _draw_menu_background(self) -> None:
        """Dibuja el fondo y los bordes decorativos de los menús."""
        self.screen.fill((10, 10, 14))

        pygame.draw.rect(
            self.screen,
            (80, 20, 15),
            (0, 0, WINDOW_WIDTH, 8),
        )
        pygame.draw.rect(
            self.screen,
            (80, 20, 15),
            (0, WINDOW_HEIGHT - 8, WINDOW_WIDTH, 8),
        )

    def _draw_dark_overlay(self, alpha: int) -> None:
        """Dibuja una capa oscura semitransparente sobre la pantalla."""
        overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

    def _draw_damage_flash(self) -> None:
        """Dibuja un flash rojo cuando el jugador recibe daño."""
        ratio = min(1.0, self.player.damage_flash_timer / 0.3)
        alpha = int(100 * ratio)

        if alpha <= 0:
            return

        overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        overlay.fill((200, 30, 20, alpha))
        self.screen.blit(overlay, (0, 0))

    def _draw_muzzle_flash_overlay(self) -> None:
        """Dibuja un flash blanco sutil al disparar."""
        if self.player.muzzle_flash_timer <= 0.0:
            return

        ratio = min(1.0, self.player.muzzle_flash_timer / 0.06)
        alpha = int(28 * ratio)

        if alpha <= 0:
            return

        overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        overlay.fill((255, 255, 255, alpha))
        self.screen.blit(overlay, (0, 0))

    def _draw_message(self) -> None:
        """Dibuja el mensaje temporal actual en la parte superior."""
        if not self.message:
            return

        text = self.message_font.render(self.message, True, MESSAGE_COLOR)
        rect = text.get_rect(center=(WINDOW_WIDTH // 2, 90))
        self.screen.blit(text, rect)

    def _draw_hud(self) -> None:
        """Dibuja la interfaz de usuario (HUD) con salud, armadura, munición, etc."""
        if self.current_level_index == -1:
            level_name = "RANDOM"
        else:
            level_name = f"LEVEL {self.current_level_index + 1}"

        level_surface = self.hud_font.render(
            level_name,
            True,
            (210, 210, 210),
        )
        self.screen.blit(level_surface, (12, 10))

        bar_height = 72
        bar_top = WINDOW_HEIGHT - bar_height

        overlay = pygame.Surface((WINDOW_WIDTH, bar_height), pygame.SRCALPHA)
        overlay.fill((8, 8, 10, 205))
        self.screen.blit(overlay, (0, bar_top))

        weapon = self.player.current_weapon

        if weapon.ammo_type is None:
            ammo_text = "INF"
        else:
            ammo_text = f"{self.player.ammo.get(weapon.ammo_type, 0):03d}"

        entries = [
            f"HP {int(self.player.health):03d}",
            f"ARMOR {int(self.player.armor):03d}",
            f"AMMO {ammo_text}",
            f"WEAPON {weapon.id.upper()}",
            f"SCORE {self.score:06d}",
        ]

        x = 24
        y = bar_top + 22

        for entry in entries:
            surface = self.hud_font.render(entry, True, (220, 220, 220))
            self.screen.blit(surface, (x, y))
            x += surface.get_width() + 48

        key_x = WINDOW_WIDTH - 170

        key_colors = {
            "red": (210, 50, 40),
            "blue": (60, 100, 220),
            "yellow": (230, 200, 60),
        }

        for key_name, color in key_colors.items():
            if self.player.has_key(key_name):
                pygame.draw.rect(
                    self.screen, color, (key_x, y + 2, 22, 22)
                )
                pygame.draw.rect(
                    self.screen, (20, 20, 20), (key_x, y + 2, 22, 22), 2
                )
                key_x += 34
