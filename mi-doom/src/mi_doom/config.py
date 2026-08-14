from __future__ import annotations

import math
from pathlib import Path

# Ventana
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
INTERNAL_WIDTH = 320
INTERNAL_HEIGHT = 200

WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
INTERNAL_SIZE = (INTERNAL_WIDTH, INTERNAL_HEIGHT)

# Game loop
FPS = 60

# Raycasting
FOV = math.radians(66.0)
PLANE_LENGTH = math.tan(FOV / 2.0)
MAX_RAY_DEPTH = 40.0
MAX_RAY_STEPS = 512

# Input
MOUSE_SENSITIVITY = 0.0026
KEYBOARD_TURN_SPEED = 2.6

# Jugador
PLAYER_RADIUS = 0.22
PLAYER_WALK_SPEED = 3.2
PLAYER_RUN_SPEED = 5.0

MAX_HEALTH = 100.0
MAX_ARMOR = 100.0

MAX_AMMO = {
    "bullets": 300,
    "shells": 50,
}

# Renderizado
MIN_SHADE = 0.12

# Rutas
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEVELS_DIR = PROJECT_ROOT / "levels"
LEVEL1_PATH = LEVELS_DIR / "level1.json"

# Colores base
CEILING_COLOR = (36, 34, 42)
FLOOR_COLOR = (58, 52, 46)
CROSSHAIR_COLOR = (230, 230, 230)

WALL_COLORS = {
    "#": (148, 142, 132),
    "D": (120, 90, 60),
}

DEFAULT_WALL_COLOR = (120, 120, 120)

DOOR_COLORS = {
    "D": (120, 90, 60),
    "R": (190, 50, 40),
    "B": (60, 95, 190),
    "Y": (210, 190, 60),
}

SWITCH_COLOR = (90, 170, 90)
MESSAGE_COLOR = (240, 220, 120)