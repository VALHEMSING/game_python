from __future__ import annotations

from enum import Enum
from typing import Any

from mi_doom.config import MAX_AMMO, MAX_ARMOR, MAX_HEALTH

DOOR_TILES = {"D", "R", "B", "Y"}
SWITCH_TILE = "S"

DOOR_KEYS = {
    "D": None,
    "R": "red",
    "B": "blue",
    "Y": "yellow",
}

DOOR_KEY_NAMES = {
    "red": "roja",
    "blue": "azul",
    "yellow": "amarilla",
}


class Door:
    def __init__(self, x: int, y: int, tile: str) -> None:
        self.x = x
        self.y = y
        self.tile = tile
        self.required_key = DOOR_KEYS.get(tile)
        self.openness = 0.0
        self.opening = False

    @property
    def is_open(self) -> bool:
        return self.openness >= 1.0

    @property
    def is_passable(self) -> bool:
        return self.is_open

    def force_open(self) -> None:
        self.opening = True

    def update(self, dt: float) -> None:
        if not self.opening:
            return

        self.openness = min(1.0, self.openness + dt / 0.5)

        if self.openness >= 1.0:
            self.opening = False

    def try_open(self, player: Any) -> tuple[bool, str]:
        if self.is_open or self.opening:
            return True, "Puerta abierta"

        if self.required_key is not None and not player.has_key(self.required_key):
            key_name = DOOR_KEY_NAMES.get(self.required_key, self.required_key)
            return False, f"Necesitas la llave {key_name}"

        self.opening = True

        if self.required_key is None:
            return True, "Puerta abierta"

        return True, "Puerta abierta con llave"


class PickupKind(Enum):
    HEALTH = "health"
    ARMOR = "armor"
    AMMO_BULLETS = "ammo_bullets"
    AMMO_SHELLS = "ammo_shells"
    WEAPON_SHOTGUN = "weapon_shotgun"
    WEAPON_MACHINEGUN = "weapon_machinegun"
    KEY_RED = "key_red"
    KEY_BLUE = "key_blue"
    KEY_YELLOW = "key_yellow"


PICKUP_STATS = {
    PickupKind.HEALTH: {
        "scale": 0.35,
        "radius": 0.22,
    },
    PickupKind.ARMOR: {
        "scale": 0.35,
        "radius": 0.22,
    },
    PickupKind.AMMO_BULLETS: {
        "scale": 0.30,
        "radius": 0.20,
    },
    PickupKind.AMMO_SHELLS: {
        "scale": 0.30,
        "radius": 0.20,
    },
    PickupKind.WEAPON_SHOTGUN: {
        "scale": 0.45,
        "radius": 0.25,
    },
    PickupKind.WEAPON_MACHINEGUN: {
        "scale": 0.45,
        "radius": 0.25,
    },
    PickupKind.KEY_RED: {
        "scale": 0.28,
        "radius": 0.18,
    },
    PickupKind.KEY_BLUE: {
        "scale": 0.28,
        "radius": 0.18,
    },
    PickupKind.KEY_YELLOW: {
        "scale": 0.28,
        "radius": 0.18,
    },
}


class Pickup:
    def __init__(
        self,
        kind: PickupKind,
        x: float,
        y: float,
        sprite: Any = None,
    ) -> None:
        stats = PICKUP_STATS[kind]

        self.kind = kind
        self.x = x
        self.y = y
        self.sprite = sprite
        self.active = True
        self.radius = float(stats["radius"])
        self.scale = float(stats["scale"])

    @property
    def is_dead(self) -> bool:
        return not self.active

    def try_apply(self, player: Any) -> str | None:
        if not self.active:
            return None

        if self.kind == PickupKind.HEALTH:
            if player.health >= MAX_HEALTH:
                return None
            player.health = min(MAX_HEALTH, player.health + 25.0)
            self.active = False
            return "Salud +25"

        if self.kind == PickupKind.ARMOR:
            if player.armor >= MAX_ARMOR:
                return None
            player.armor = min(MAX_ARMOR, player.armor + 25.0)
            self.active = False
            return "Armadura +25"

        if self.kind == PickupKind.AMMO_BULLETS:
            if not player.add_ammo("bullets", 30):
                return None
            self.active = False
            return "Balas +30"

        if self.kind == PickupKind.AMMO_SHELLS:
            if not player.add_ammo("shells", 8):
                return None
            self.active = False
            return "Cartuchos +8"

        if self.kind == PickupKind.WEAPON_SHOTGUN:
            slot = 2
            ammo_type = "shells"
            ammo_amount = 8

            if player.has_weapon_slot(slot):
                if not player.add_ammo(ammo_type, ammo_amount):
                    return None
                self.active = False
                return "Cartuchos +8"

            player.give_weapon(slot)
            player.add_ammo(ammo_type, ammo_amount)
            self.active = False
            return "Escopeta obtenida"

        if self.kind == PickupKind.WEAPON_MACHINEGUN:
            slot = 3
            ammo_type = "bullets"
            ammo_amount = 40

            if player.has_weapon_slot(slot):
                if not player.add_ammo(ammo_type, ammo_amount):
                    return None
                self.active = False
                return "Balas +40"

            player.give_weapon(slot)
            player.add_ammo(ammo_type, ammo_amount)
            self.active = False
            return "Ametralladora obtenida"

        if self.kind == PickupKind.KEY_RED:
            if player.has_key("red"):
                return None
            player.add_key("red")
            self.active = False
            return "Llave roja"

        if self.kind == PickupKind.KEY_BLUE:
            if player.has_key("blue"):
                return None
            player.add_key("blue")
            self.active = False
            return "Llave azul"

        if self.kind == PickupKind.KEY_YELLOW:
            if player.has_key("yellow"):
                return None
            player.add_key("yellow")
            self.active = False
            return "Llave amarilla"

        return None
    