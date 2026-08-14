from __future__ import annotations

import pygame
from PIL import Image, ImageDraw

from mi_doom.enemy import EnemyKind
from mi_doom.entities import PickupKind


def create_enemy_sprite(kind: EnemyKind) -> pygame.Surface:
    """
    Genera sprites originales de enemigos en tiempo de ejecución usando Pillow.
    """
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if kind == EnemyKind.DRONE:
        draw.ellipse(
            (14, 24, 50, 48),
            fill=(70, 170, 210, 255),
            outline=(15, 50, 70, 255),
            width=2,
        )
        draw.rectangle(
            (28, 10, 36, 26),
            fill=(120, 220, 255, 255),
            outline=(20, 60, 80, 255),
            width=2,
        )
        draw.ellipse(
            (28, 32, 36, 40),
            fill=(240, 80, 80, 255),
        )

    elif kind == EnemyKind.MUTANT:
        draw.rectangle(
            (22, 18, 42, 54),
            fill=(70, 160, 70, 255),
            outline=(20, 60, 20, 255),
            width=2,
        )
        draw.ellipse(
            (24, 6, 40, 22),
            fill=(110, 200, 110, 255),
            outline=(20, 60, 20, 255),
            width=2,
        )
        draw.rectangle(
            (14, 22, 22, 40),
            fill=(60, 140, 60, 255),
            outline=(20, 60, 20, 255),
            width=2,
        )
        draw.rectangle(
            (42, 22, 50, 40),
            fill=(60, 140, 60, 255),
            outline=(20, 60, 20, 255),
            width=2,
        )
        draw.ellipse(
            (27, 11, 31, 15),
            fill=(220, 60, 60, 255),
        )
        draw.ellipse(
            (33, 11, 37, 15),
            fill=(220, 60, 60, 255),
        )

    elif kind == EnemyKind.BEAST:
        draw.ellipse(
            (8, 18, 56, 58),
            fill=(170, 50, 40, 255),
            outline=(60, 15, 10, 255),
            width=3,
        )
        draw.polygon(
            ((14, 22), (8, 6), (24, 16)),
            fill=(190, 70, 50, 255),
        )
        draw.polygon(
            ((50, 22), (56, 6), (40, 16)),
            fill=(190, 70, 50, 255),
        )
        draw.ellipse(
            (20, 30, 28, 38),
            fill=(255, 220, 60, 255),
        )
        draw.ellipse(
            (36, 30, 44, 38),
            fill=(255, 220, 60, 255),
        )
        draw.rectangle(
            (24, 46, 40, 52),
            fill=(80, 10, 10, 255),
        )

    return pygame.image.frombytes(image.tobytes(), image.size, image.mode).convert_alpha()


def create_pickup_sprite(kind: PickupKind) -> pygame.Surface:
    """
    Genera sprites originales de pickups en tiempo de ejecución usando Pillow.
    """
    size = 32
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if kind == PickupKind.HEALTH:
        draw.rectangle((4, 8, 28, 24), fill=(220, 220, 220, 255), outline=(40, 40, 40, 255), width=2)
        draw.rectangle((14, 10, 18, 22), fill=(200, 40, 40, 255))
        draw.rectangle((10, 14, 22, 18), fill=(200, 40, 40, 255))

    elif kind == PickupKind.ARMOR:
        draw.polygon(
            ((16, 3), (27, 8), (24, 26), (16, 30), (8, 26), (5, 8)),
            fill=(60, 140, 80, 255),
            outline=(15, 50, 25, 255),
            width=2,
        )
        draw.polygon(
            ((16, 8), (22, 11), (20, 22), (16, 25), (12, 22), (10, 11)),
            fill=(110, 200, 130, 255),
        )

    elif kind == PickupKind.AMMO_BULLETS:
        draw.rectangle((5, 12, 27, 24), fill=(70, 60, 50, 255), outline=(30, 25, 20, 255), width=2)
        for x in (8, 13, 18, 23):
            draw.rectangle((x, 8, x + 2, 18), fill=(220, 190, 60, 255))

    elif kind == PickupKind.AMMO_SHELLS:
        draw.rectangle((5, 12, 27, 24), fill=(70, 40, 35, 255), outline=(30, 15, 10, 255), width=2)
        for x in (8, 14, 20):
            draw.rectangle((x, 8, x + 4, 18), fill=(190, 50, 40, 255))
            draw.rectangle((x, 8, x + 4, 11), fill=(220, 190, 60, 255))

    elif kind == PickupKind.WEAPON_SHOTGUN:
        draw.rectangle((4, 18, 28, 24), fill=(110, 70, 40, 255), outline=(40, 25, 10, 255), width=2)
        draw.rectangle((6, 12, 26, 18), fill=(90, 90, 100, 255), outline=(30, 30, 35, 255), width=2)
        draw.rectangle((20, 8, 26, 12), fill=(60, 60, 70, 255))

    elif kind == PickupKind.WEAPON_MACHINEGUN:
        draw.rectangle((4, 16, 28, 22), fill=(80, 80, 90, 255), outline=(25, 25, 30, 255), width=2)
        draw.rectangle((8, 10, 24, 16), fill=(110, 110, 120, 255), outline=(25, 25, 30, 255), width=2)
        draw.rectangle((14, 22, 18, 28), fill=(70, 70, 80, 255))

    elif kind in (PickupKind.KEY_RED, PickupKind.KEY_BLUE, PickupKind.KEY_YELLOW):
        if kind == PickupKind.KEY_RED:
            color = (210, 50, 40, 255)
        elif kind == PickupKind.KEY_BLUE:
            color = (60, 100, 220, 255)
        else:
            color = (230, 200, 60, 255)

        draw.ellipse((5, 8, 17, 20), outline=color, width=3)
        draw.rectangle((15, 12, 28, 16), fill=color)
        draw.rectangle((22, 16, 24, 21), fill=color)
        draw.rectangle((26, 16, 28, 20), fill=color)

    return pygame.image.frombytes(image.tobytes(), image.size, image.mode).convert_alpha()