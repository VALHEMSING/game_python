"""
Módulo que define las entidades interactivas del nivel,
como puertas, interruptores y pickups (objetos recogibles).
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from mi_doom.config import MAX_AMMO, MAX_ARMOR, MAX_HEALTH

DOOR_TILES = {"D", "R", "B", "Y"}
SWITCH_TILE = "S"
EXIT_TILE = "X"

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
    """Representa una puerta interactiva que puede abrirse."""

    def __init__(self, x: int, y: int, tile: str) -> None:
        """Inicializa la puerta en su posición y estado cerrada."""
        self.x = x
        self.y = y
        self.tile = tile
        self.required_key = DOOR_KEYS.get(tile)
        self.openness = 0.0
        self.opening = False

    @property
    def is_open(self) -> bool:
        """Indica si la puerta está completamente abierta."""
        return self.openness >= 1.0

    @property
    def is_passable(self) -> bool:
        """Indica si el jugador puede atravesar la puerta."""
        return self.is_open

    def force_open(self) -> None:
        """Inicia la animación de apertura forzada (ej. por un interruptor)."""
        self.opening = True

    def update(self, dt: float) -> None:
        """Actualiza la animación de apertura de la puerta."""
        if not self.opening:
            return

        self.openness = min(1.0, self.openness + dt / 0.5)

        if self.openness >= 1.0:
            self.opening = False

    def try_open(self, player: Any) -> tuple[bool, str]:
        """Intenta abrir la puerta comprobando si el jugador tiene la llave requerida."""
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
    """Tipos de objetos recogibles disponibles en el juego."""
    HEALTH = "health"
    ARMOR = "armor"
    AMMO_BULLETS = "ammo_bullets"
    AMMO_SHELLS = "ammo_shells"
    WEAPON_SHOTGUN = "weapon_shotgun"
    WEAPON_MACHINEGUN = "weapon_machinegun"
    KEY_RED = "key_red"
    KEY_BLUE = "key_blue"
    KEY_YELLOW = "key_yellow"
    SECRET = "secret"


PICKUP_STATS = {
    PickupKind.HEALTH: {"scale": 0.35, "radius": 0.22},
    PickupKind.ARMOR: {"scale": 0.35, "radius": 0.22},
    PickupKind.AMMO_BULLETS: {"scale": 0.30, "radius": 0.20},
    PickupKind.AMMO_SHELLS: {"scale": 0.30, "radius": 0.20},
    PickupKind.WEAPON_SHOTGUN: {"scale": 0.45, "radius": 0.25},
    PickupKind.WEAPON_MACHINEGUN: {"scale": 0.45, "radius": 0.25},
    PickupKind.KEY_RED: {"scale": 0.28, "radius": 0.18},
    PickupKind.KEY_BLUE: {"scale": 0.28, "radius": 0.18},
    PickupKind.KEY_YELLOW: {"scale": 0.28, "radius": 0.18},
    PickupKind.SECRET: {"scale": 0.40, "radius": 0.22},
}


class Pickup:
    """Representa un objeto recogible en el mapa."""

    def __init__(
        self,
        kind: PickupKind,
        x: float,
        y: float,
        sprite: Any = None,
    ) -> None:
        """Inicializa el pickup con su tipo, posición y propiedades físicas."""
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
        """Indica si el pickup ya ha sido recogido."""
        return not self.active

    def try_apply(self, player: Any) -> str | None:
        """Aplica el efecto del pickup al jugador si es posible."""
        if not self.active:
            return None

        if self.kind == PickupKind.HEALTH:
            if player.health >= MAX_HEALTH:
                return None
            player.health = min(MAX_HEALTH, player.health + 20.0)
            self.active = False
            return "Salud +20"

        if self.kind == PickupKind.ARMOR:
            if player.armor >= MAX_ARMOR:
                return None
            player.armor = min(MAX_ARMOR, player.armor + 20.0)
            self.active = False
            return "Armadura +20"

        if self.kind == PickupKind.AMMO_BULLETS:
            if not player.add_ammo("bullets", 20):
                return None
            self.active = False
            return "Balas +20"

        if self.kind == PickupKind.AMMO_SHELLS:
            if not player.add_ammo("shells", 6):
                return None
            self.active = False
            return "Cartuchos +6"

        if self.kind == PickupKind.WEAPON_SHOTGUN:
            slot = 2
            ammo_type = "shells"
            ammo_amount = 6

            if player.has_weapon_slot(slot):
                if not player.add_ammo(ammo_type, ammo_amount):
                    return None
                self.active = False
                return "Cartuchos +6"

            player.give_weapon(slot)
            player.add_ammo(ammo_type, ammo_amount)
            self.active = False
            return "Escopeta obtenida"

        if self.kind == PickupKind.WEAPON_MACHINEGUN:
            slot = 3
            ammo_type = "bullets"
            ammo_amount = 30

            if player.has_weapon_slot(slot):
                if not player.add_ammo(ammo_type, ammo_amount):
                    return None
                self.active = False
                return "Balas +30"

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

        if self.kind == PickupKind.SECRET:
            self.active = False
            return "¡SECRETO ENCONTRADO! +500"

        return None

class DecorationKind(Enum):
    """Tipos de decoraciones ambientales."""
    TORCH = "torch"
    COLUMN = "column"
    BARREL = "barrel"
    CONSOLE = "console"
    SKULL = "skull"


class Decoration:
    """Representa una decoración ambiental que no bloquea el paso."""

    def __init__(
        self,
        kind: DecorationKind,
        x: float,
        y: float,
        sprite: Any = None,
    ) -> None:
        """Inicializa la decoración con su tipo, posición y sprite."""
        self.kind = kind
        self.x = x
        self.y = y
        self.sprite = sprite
        self.active = True
        self.scale = self._get_scale()
        self.radius = 0.1  # Radio pequeño, no bloquea el paso

    @property
    def is_dead(self) -> bool:
        """Las decoraciones nunca mueren."""
        return not self.active

    def _get_scale(self) -> float:
        """Devuelve la escala según el tipo de decoración."""
        scales = {
            DecorationKind.TORCH: 0.6,
            DecorationKind.COLUMN: 0.9,
            DecorationKind.BARREL: 0.4,
            DecorationKind.CONSOLE: 0.5,
            DecorationKind.SKULL: 0.2,
        }
        return scales.get(self.kind, 0.5)
