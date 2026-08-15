from __future__ import annotations

import random
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageDraw

from mi_doom.config import TEXTURE_SIZE, TEXTURES_DIR

MATERIAL_NAMES = (
    "metal",
    "stone",
    "concrete",
    "tech",
    "dark_wall",
)

REQUIRED_TEXTURE_NAMES = (
    *MATERIAL_NAMES,
    "door_d",
    "door_r",
    "door_b",
    "door_y",
    "switch",
    "exit",
    "floor",
    "ceiling",
)


def ensure_asset_directories() -> None:
    TEXTURES_DIR.mkdir(parents=True, exist_ok=True)


def generate_all_assets() -> None:
    generate_all_textures(force=True)


def generate_all_textures(force: bool = False) -> None:
    ensure_asset_directories()

    for name in REQUIRED_TEXTURE_NAMES:
        path = TEXTURES_DIR / f"{name}.png"

        if path.exists() and not force:
            continue

        image = generate_texture_image(name)
        image.save(path)


def load_texture_array(name: str) -> np.ndarray:
    path = TEXTURES_DIR / f"{name}.png"

    try:
        if path.exists():
            image = Image.open(path).convert("RGB")
        else:
            image = generate_texture_image(name)
    except Exception:
        image = generate_texture_image(name)

    return np.array(image, dtype=np.uint8)


class TextureManager:
    def __init__(self) -> None:
        self.textures: dict[str, np.ndarray] = {}

        for name in REQUIRED_TEXTURE_NAMES:
            self.textures[name] = load_texture_array(name)

    def get(self, name: str) -> np.ndarray:
        return self.textures.get(name, self.textures["concrete"])


def generate_texture_image(name: str) -> Image.Image:
    if name == "metal":
        return _generate_metal()

    if name == "stone":
        return _generate_stone()

    if name == "concrete":
        return _generate_concrete()

    if name == "tech":
        return _generate_tech()

    if name == "dark_wall":
        return _generate_dark_wall()

    if name == "door_d":
        return _generate_door((120, 90, 60))

    if name == "door_r":
        return _generate_door((190, 50, 40))

    if name == "door_b":
        return _generate_door((60, 95, 190))

    if name == "door_y":
        return _generate_door((210, 190, 60))
    if name == "floor":
        return _generate_floor()
    if name == "ceiling":
        return _generate_ceiling()
    if name == "switch":
        return _generate_switch()

    if name == "exit":
        return _generate_exit()

    return _generate_concrete()


def _base_image(color: tuple[int, int, int]) -> Image.Image:
    return Image.new("RGB", (TEXTURE_SIZE, TEXTURE_SIZE), color)


def _add_noise(
    draw: ImageDraw.ImageDraw,
    rng: random.Random,
    count: int,
    colors: Iterable[tuple[int, int, int]],
) -> None:
    colors = tuple(colors)

    for _ in range(count):
        x = rng.randint(0, TEXTURE_SIZE - 1)
        y = rng.randint(0, TEXTURE_SIZE - 1)
        draw.point((x, y), fill=rng.choice(colors))


def _generate_metal() -> Image.Image:
    image = _base_image((88, 92, 100))
    draw = ImageDraw.Draw(image)
    rng = random.Random(101)

    for y in range(0, TEXTURE_SIZE, 8):
        draw.line([(0, y), (TEXTURE_SIZE, y)], fill=(70, 74, 82), width=1)

    for x in range(0, TEXTURE_SIZE, 16):
        draw.line([(x, 0), (x, TEXTURE_SIZE)], fill=(104, 108, 116), width=1)

    rivet_positions = [
        (4, 4),
        (TEXTURE_SIZE - 5, 4),
        (4, TEXTURE_SIZE - 5),
        (TEXTURE_SIZE - 5, TEXTURE_SIZE - 5),
    ]

    for x, y in rivet_positions:
        draw.ellipse(
            (x - 2, y - 2, x + 2, y + 2),
            fill=(130, 134, 142),
            outline=(50, 54, 62),
        )

    _add_noise(
        draw,
        rng,
        260,
        [
            (110, 114, 122),
            (66, 70, 78),
            (130, 134, 142),
        ],
    )

    return image
def _generate_floor() -> Image.Image:
    """Genera una textura de suelo con aspecto de concreto/piedra."""
    size = TEXTURE_SIZE
    image = Image.new("RGB", (size, size), (70, 65, 60))
    draw = ImageDraw.Draw(image)
    rng = random.Random(789)

    # Base con variaciones de color
    for _ in range(200):
        x = rng.randint(0, size - 1)
        y = rng.randint(0, size - 1)
        shade = rng.randint(55, 85)
        draw.point((x, y), fill=(shade, shade - 3, shade - 6))

    # Juntas entre baldosas
    tile_size = size // 4
    for ty in range(0, size, tile_size):
        for tx in range(0, size, tile_size):
            draw.rectangle(
                (tx, ty, tx + tile_size - 1, ty + tile_size - 1),
                outline=(50, 45, 40),
            )

    # Manchas y desgaste
    for _ in range(8):
        x = rng.randint(0, size - 8)
        y = rng.randint(0, size - 8)
        w = rng.randint(3, 8)
        h = rng.randint(3, 8)
        shade = rng.randint(45, 60)
        draw.ellipse((x, y, x + w, y + h), fill=(shade, shade - 2, shade - 5))

    return image


def _generate_ceiling() -> Image.Image:
    """Genera una textura de techo con aspecto de paneles metálicos."""
    size = TEXTURE_SIZE
    image = Image.new("RGB", (size, size), (55, 58, 65))
    draw = ImageDraw.Draw(image)
    rng = random.Random(456)

    # Base con variaciones
    for _ in range(150):
        x = rng.randint(0, size - 1)
        y = rng.randint(0, size - 1)
        shade = rng.randint(45, 70)
        draw.point((x, y), fill=(shade, shade + 2, shade + 5))

    # Paneles metálicos
    panel_size = size // 2
    for py in range(0, size, panel_size):
        for px in range(0, size, panel_size):
            draw.rectangle(
                (px + 1, py + 1, px + panel_size - 2, py + panel_size - 2),
                outline=(70, 75, 82),
            )
            # Remaches en las esquinas
            for rx, ry in [(px + 3, py + 3), (px + panel_size - 4, py + 3),
                           (px + 3, py + panel_size - 4), (px + panel_size - 4, py + panel_size - 4)]:
                draw.ellipse((rx - 1, ry - 1, rx + 1, ry + 1), fill=(90, 95, 100))

    # Conductos y cables
    for _ in range(3):
        x1 = rng.randint(0, size)
        y1 = rng.randint(0, size)
        x2 = x1 + rng.randint(-20, 20)
        y2 = y1 + rng.randint(-20, 20)
        draw.line([(x1, y1), (x2, y2)], fill=(40, 42, 48), width=2)

    return image


def _generate_stone() -> Image.Image:
    image = _base_image((112, 102, 92))
    draw = ImageDraw.Draw(image)
    rng = random.Random(202)

    brick_height = 16
    brick_width = 32

    for row, y in enumerate(range(0, TEXTURE_SIZE, brick_height)):
        offset = 0 if row % 2 == 0 else brick_width // 2

        for x in range(-brick_width, TEXTURE_SIZE + brick_width, brick_width):
            left = x + offset + 1
            top = y + 1
            right = left + brick_width - 3
            bottom = top + brick_height - 3

            draw.rectangle(
                (left, top, right, bottom),
                outline=(72, 64, 58),
                width=2,
            )

    _add_noise(
        draw,
        rng,
        360,
        [
            (130, 118, 106),
            (86, 78, 70),
            (142, 130, 118),
        ],
    )

    return image


def _generate_concrete() -> Image.Image:
    image = _base_image((122, 122, 120))
    draw = ImageDraw.Draw(image)
    rng = random.Random(303)

    for _ in range(14):
        x = rng.randint(0, TEXTURE_SIZE)
        y = rng.randint(0, TEXTURE_SIZE)
        radius = rng.randint(3, 9)
        shade = rng.randint(92, 108)

        draw.ellipse(
            (x - radius, y - radius, x + radius, y + radius),
            fill=(shade, shade, shade - 2),
        )

    _add_noise(
        draw,
        rng,
        420,
        [
            (140, 140, 138),
            (96, 96, 94),
            (160, 158, 156),
        ],
    )

    return image


def _generate_tech() -> Image.Image:
    image = _base_image((38, 58, 66))
    draw = ImageDraw.Draw(image)
    rng = random.Random(404)

    for x in range(0, TEXTURE_SIZE, 16):
        draw.line([(x, 0), (x, TEXTURE_SIZE)], fill=(24, 40, 48), width=2)

    for y in range(0, TEXTURE_SIZE, 16):
        draw.line([(0, y), (TEXTURE_SIZE, y)], fill=(24, 40, 48), width=2)

    for _ in range(10):
        x = rng.randint(2, TEXTURE_SIZE - 10)
        y = rng.randint(2, TEXTURE_SIZE - 10)
        draw.rectangle((x, y, x + 5, y + 3), fill=(70, 200, 170))

    _add_noise(
        draw,
        rng,
        220,
        [
            (52, 82, 92),
            (22, 36, 44),
            (80, 140, 150),
        ],
    )

    return image


def _generate_dark_wall() -> Image.Image:
    image = _base_image((46, 42, 46))
    draw = ImageDraw.Draw(image)
    rng = random.Random(505)

    for _ in range(12):
        x = rng.randint(0, TEXTURE_SIZE)
        y = rng.randint(0, TEXTURE_SIZE)
        length_x = rng.randint(-18, 18)
        length_y = rng.randint(-18, 18)

        draw.line(
            [(x, y), (x + length_x, y + length_y)],
            fill=(24, 22, 24),
            width=1,
        )

    _add_noise(
        draw,
        rng,
        300,
        [
            (64, 58, 64),
            (30, 28, 30),
            (84, 76, 84),
        ],
    )

    return image


def _generate_door(color: tuple[int, int, int]) -> Image.Image:
    image = _generate_metal()
    draw = ImageDraw.Draw(image)

    draw.rectangle((18, 0, 46, TEXTURE_SIZE), fill=color)
    draw.rectangle((18, 0, 46, TEXTURE_SIZE), outline=(20, 20, 20), width=2)

    draw.line([(32, 0), (32, TEXTURE_SIZE)], fill=(20, 20, 20), width=2)
    draw.rectangle((30, 28, 36, 36), fill=(25, 25, 25))

    return image


def _generate_switch() -> Image.Image:
    image = _generate_concrete()
    draw = ImageDraw.Draw(image)

    draw.rectangle((18, 18, 46, 46), fill=(40, 120, 60), outline=(10, 40, 20), width=3)
    draw.rectangle((26, 26, 38, 38), fill=(120, 220, 140))

    return image


def _generate_exit() -> Image.Image:
    image = _base_image((20, 24, 20))
    draw = ImageDraw.Draw(image)

    draw.rectangle((8, 16, 56, 48), outline=(60, 220, 120), width=3)

    draw.polygon(
        (
            (20, 32),
            (38, 20),
            (38, 28),
            (48, 28),
            (48, 36),
            (38, 36),
            (38, 44),
        ),
        fill=(60, 220, 120),
    )

    return image
