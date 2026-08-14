from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable

from mi_doom.combat import shoot_hitscan
from mi_doom.config import (
    KEYBOARD_TURN_SPEED,
    MAX_AMMO,
    MAX_ARMOR,
    MAX_HEALTH,
    MOUSE_SENSITIVITY,
    PLAYER_RADIUS,
    PLAYER_RUN_SPEED,
    PLAYER_WALK_SPEED,
)
from mi_doom.collision import circle_collides
from mi_doom.input import PlayerControls
from mi_doom.weapon import Weapon, create_default_weapons

if TYPE_CHECKING:
    from mi_doom.level import Level


def _create_start_weapons() -> dict[int, Weapon]:
    weapons = create_default_weapons()
    return {
        1: weapons[1],
    }


@dataclass
class Player:
    x: float
    y: float
    angle: float = 0.0

    health: float = MAX_HEALTH
    armor: float = 0.0

    ammo: dict[str, int] = field(
        default_factory=lambda: {
            "bullets": 0,
            "shells": 0,
        }
    )

    weapons: dict[int, Weapon] = field(default_factory=_create_start_weapons)
    current_weapon_slot: int = 1

    keys: set[str] = field(default_factory=set)

    speed: float = PLAYER_WALK_SPEED
    radius: float = PLAYER_RADIUS
    mouse_sensitivity: float = MOUSE_SENSITIVITY

    muzzle_flash_timer: float = 0.0
    damage_flash_timer: float = 0.0

    @property
    def position(self) -> tuple[float, float]:
        return (self.x, self.y)

    @property
    def current_weapon(self) -> Weapon:
        return self.weapons.get(self.current_weapon_slot, self.weapons[1])

    @property
    def is_dead(self) -> bool:
        return self.health <= 0.0

    def has_key(self, color: str) -> bool:
        return color in self.keys

    def add_key(self, color: str) -> None:
        self.keys.add(color)

    def has_weapon_slot(self, slot: int) -> bool:
        return slot in self.weapons

    def give_weapon(self, slot: int) -> None:
        if slot in self.weapons:
            return

        all_weapons = create_default_weapons()
        if slot not in all_weapons:
            return

        self.weapons[slot] = all_weapons[slot]
        self.current_weapon_slot = slot

    def add_ammo(self, ammo_type: str, amount: int) -> bool:
        current = self.ammo.get(ammo_type, 0)
        max_amount = MAX_AMMO.get(ammo_type, 999)
        new_amount = min(max_amount, current + amount)

        if new_amount == current:
            return False

        self.ammo[ammo_type] = new_amount
        return True

    def take_damage(self, amount: float) -> None:
        if self.is_dead:
            return

        absorbed = min(self.armor, amount * 0.5)
        self.armor -= absorbed
        self.health -= amount - absorbed
        self.damage_flash_timer = 0.3

        if self.health <= 0.0:
            self.health = 0.0

    def update(self, dt: float, level: Level, controls: PlayerControls) -> None:
        self._update_timers(dt)
        self._update_weapons(dt)
        self._update_rotation(dt, controls)
        self._update_movement(dt, level, controls)

    def update_combat(
        self,
        dt: float,
        controls: PlayerControls,
        enemies: Iterable[Any],
        level: Level,
    ) -> int:
        if self.is_dead:
            return 0

        weapon = self.current_weapon
        want_fire = controls.shoot_held if weapon.automatic else controls.shoot_pressed

        if not want_fire:
            return 0

        if weapon.can_fire(self.ammo):
            weapon.fire()
            weapon.consume_ammo(self.ammo)
            self.muzzle_flash_timer = 0.06

            return shoot_hitscan(
                level=level,
                enemies=enemies,
                x=self.x,
                y=self.y,
                angle=self.angle,
                spread=weapon.spread,
                max_range=weapon.range,
                damage=weapon.damage,
                pellet_count=weapon.pellets,
            )

        if weapon.ammo_type is not None:
            # Si el arma actual se queda sin munición, cambio automático a pistola.
            self.current_weapon_slot = 1

        return 0

    def _update_timers(self, dt: float) -> None:
        self.muzzle_flash_timer = max(0.0, self.muzzle_flash_timer - dt)
        self.damage_flash_timer = max(0.0, self.damage_flash_timer - dt)

    def _update_weapons(self, dt: float) -> None:
        for weapon in self.weapons.values():
            weapon.update(dt)

    def _update_rotation(self, dt: float, controls: PlayerControls) -> None:
        self.angle += controls.mouse_dx * self.mouse_sensitivity
        self.angle += controls.turn_delta * KEYBOARD_TURN_SPEED * dt
        self.angle %= math.tau

    def _update_movement(self, dt: float, level: Level, controls: PlayerControls) -> None:
        forward = controls.move_forward
        strafe = controls.move_strafe

        if forward == 0.0 and strafe == 0.0:
            return

        length = math.hypot(forward, strafe)
        if length > 0.0:
            forward /= length
            strafe /= length

        speed = self.speed
        if controls.run:
            speed = PLAYER_RUN_SPEED

        dir_x = math.cos(self.angle)
        dir_y = math.sin(self.angle)

        right_x = -dir_y
        right_y = dir_x

        dx = (dir_x * forward + right_x * strafe) * speed * dt
        dy = (dir_y * forward + right_y * strafe) * speed * dt

        self._move_with_collision(dx, dy, level)

    def _move_with_collision(self, dx: float, dy: float, level: Level) -> None:
        if dx != 0.0:
            new_x = self.x + dx
            if not circle_collides(level, new_x, self.y, self.radius):
                self.x = new_x

        if dy != 0.0:
            new_y = self.y + dy
            if not circle_collides(level, self.x, new_y, self.radius):
                self.y = new_y