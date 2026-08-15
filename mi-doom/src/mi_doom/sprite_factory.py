"""
Módulo encargado de la generación procedural de sprites para enemigos,
pickups y partículas utilizando Pillow y Pygame.
"""
# pylint: disable=no-member

from __future__ import annotations

import pygame
from PIL import Image, ImageDraw

from mi_doom.enemy import EnemyKind
from mi_doom.entities import PickupKind


def create_enemy_sprite(kind: EnemyKind) -> pygame.Surface:
    """
    Genera sprites originales de enemigos en tiempo de ejecución usando Pillow.
    Versión mejorada con más detalles y mejor aspecto visual.
    """
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if kind == EnemyKind.DRONE:
        # Drone: robot volador con forma de disco y ojo central
        # Cuerpo principal (disco)
        draw.ellipse(
            (12, 20, 52, 44),
            fill=(60, 140, 180, 255),
            outline=(30, 80, 110, 255),
            width=2,
        )
        # Cúpula superior
        draw.ellipse(
            (20, 12, 44, 28),
            fill=(100, 180, 220, 255),
            outline=(40, 100, 140, 255),
            width=2,
        )
        # Ojo central (rojo brillante)
        draw.ellipse(
            (26, 28, 38, 40),
            fill=(255, 50, 50, 255),
            outline=(180, 20, 20, 255),
            width=1,
        )
        # Brillo del ojo
        draw.ellipse(
            (29, 31, 35, 37),
            fill=(255, 150, 150, 255),
        )
        # Propulsores laterales
        draw.rectangle((8, 30, 14, 38), fill=(80, 160, 200, 255), outline=(40, 90, 120, 255))
        draw.rectangle((50, 30, 56, 38), fill=(80, 160, 200, 255), outline=(40, 90, 120, 255))
        # Antena
        draw.line([(32, 12), (32, 6)], fill=(200, 220, 240, 255), width=2)
        draw.ellipse((30, 4, 34, 8), fill=(255, 200, 50, 255))
        # Luces de propulsión (inferior)
        draw.ellipse((22, 42, 28, 48), fill=(100, 200, 255, 200))
        draw.ellipse((36, 42, 42, 48), fill=(100, 200, 255, 200))

    elif kind == EnemyKind.MUTANT:
        # Mutant: humanoide verde con cabeza grande y brazos largos
        # Cuerpo
        draw.rectangle(
            (22, 24, 42, 52),
            fill=(80, 160, 60, 255),
            outline=(40, 90, 30, 255),
            width=2,
        )
        # Cabeza (más grande que el cuerpo)
        draw.ellipse(
            (18, 4, 46, 26),
            fill=(100, 190, 80, 255),
            outline=(50, 110, 40, 255),
            width=2,
        )
        # Ojos (grandes y rojos)
        draw.ellipse((24, 10, 32, 18), fill=(255, 60, 60, 255), outline=(180, 30, 30, 255))
        draw.ellipse((34, 10, 42, 18), fill=(255, 60, 60, 255), outline=(180, 30, 30, 255))
        # Brillo de los ojos
        draw.ellipse((26, 12, 30, 16), fill=(255, 180, 180, 255))
        draw.ellipse((36, 12, 40, 16), fill=(255, 180, 180, 255))
        # Boca
        draw.rectangle((28, 20, 38, 24), fill=(40, 80, 30, 255))
        # Brazos largos
        draw.rectangle((12, 26, 20, 48), fill=(70, 140, 50, 255), outline=(40, 90, 30, 255), width=1)
        draw.rectangle((44, 26, 52, 48), fill=(70, 140, 50, 255), outline=(40, 90, 30, 255), width=1)
        # Garras
        draw.polygon(((12, 48), (8, 56), (16, 52)), fill=(200, 180, 100, 255))
        draw.polygon(((52, 48), (56, 56), (48, 52)), fill=(200, 180, 100, 255))
        # Piernas
        draw.rectangle((24, 52, 30, 62), fill=(70, 140, 50, 255), outline=(40, 90, 30, 255))
        draw.rectangle((34, 52, 40, 62), fill=(70, 140, 50, 255), outline=(40, 90, 30, 255))
        # Manchas de mutación
        draw.ellipse((26, 32, 34, 40), fill=(120, 220, 100, 180))
        draw.ellipse((34, 38, 40, 46), fill=(120, 220, 100, 150))

    elif kind == EnemyKind.BEAST:
        # Beast: criatura grande y musculosa con cuernos
        # Cuerpo masivo
        draw.ellipse(
            (6, 16, 58, 58),
            fill=(180, 60, 40, 255),
            outline=(100, 30, 20, 255),
            width=3,
        )
        # Pecho/cabeza
        draw.ellipse(
            (14, 8, 50, 32),
            fill=(200, 80, 50, 255),
            outline=(120, 40, 25, 255),
            width=2,
        )
        # Cuernos
        draw.polygon(((16, 12), (8, 0), (22, 8)), fill=(240, 220, 180, 255), outline=(180, 160, 120, 255))
        draw.polygon(((48, 12), (56, 0), (42, 8)), fill=(240, 220, 180, 255), outline=(180, 160, 120, 255))
        # Ojos (amarillos brillantes)
        draw.ellipse((20, 16, 30, 26), fill=(255, 220, 50, 255), outline=(200, 170, 30, 255), width=2)
        draw.ellipse((34, 16, 44, 26), fill=(255, 220, 50, 255), outline=(200, 170, 30, 255), width=2)
        # Pupilas
        draw.ellipse((24, 20, 28, 24), fill=(20, 20, 20, 255))
        draw.ellipse((38, 20, 42, 24), fill=(20, 20, 20, 255))
        # Boca con dientes
        draw.rectangle((22, 28, 42, 34), fill=(80, 20, 10, 255))
        # Dientes
        for tx in range(24, 40, 4):
            draw.polygon(((tx, 28), (tx + 2, 32), (tx + 4, 28)), fill=(255, 255, 240, 255))
        # Brazos musculosos
        draw.ellipse((2, 24, 18, 44), fill=(170, 55, 35, 255), outline=(100, 30, 20, 255), width=2)
        draw.ellipse((46, 24, 62, 44), fill=(170, 55, 35, 255), outline=(100, 30, 20, 255), width=2)
        # Garras
        for gx in [(4, 44), (52, 44)]:
            draw.polygon(((gx[0], gx[1]), (gx[0] - 4, gx[1] + 10), (gx[0] + 6, gx[1] + 4)), fill=(240, 220, 180, 255))
        # Cicatrices
        draw.line([(28, 36), (36, 44)], fill=(120, 40, 25, 255), width=2)
        draw.line([(30, 44), (38, 36)], fill=(120, 40, 25, 255), width=2)
        # Piernas
        draw.rectangle((16, 54, 26, 64), fill=(160, 50, 30, 255), outline=(100, 30, 20, 255), width=2)
        draw.rectangle((38, 54, 48, 64), fill=(160, 50, 30, 255), outline=(100, 30, 20, 255), width=2)

    return pygame.image.frombytes(image.tobytes(), image.size, image.mode).convert_alpha()


def create_pickup_sprite(kind: PickupKind) -> pygame.Surface:
    """
    Genera sprites originales de pickups en tiempo de ejecución usando Pillow.
    """
    size = 32
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if kind == PickupKind.HEALTH:
        draw.rectangle(
            (4, 8, 28, 24),
            fill=(220, 220, 220, 255),
            outline=(40, 40, 40, 255),
            width=2,
        )
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
        draw.rectangle(
            (5, 12, 27, 24),
            fill=(70, 60, 50, 255),
            outline=(30, 25, 20, 255),
            width=2,
        )
        for x in (8, 13, 18, 23):
            draw.rectangle((x, 8, x + 2, 18), fill=(220, 190, 60, 255))

    elif kind == PickupKind.AMMO_SHELLS:
        draw.rectangle(
            (5, 12, 27, 24),
            fill=(70, 40, 35, 255),
            outline=(30, 15, 10, 255),
            width=2,
        )
        for x in (8, 14, 20):
            draw.rectangle((x, 8, x + 4, 18), fill=(190, 50, 40, 255))
            draw.rectangle((x, 8, x + 4, 11), fill=(220, 190, 60, 255))

    elif kind == PickupKind.WEAPON_SHOTGUN:
        draw.rectangle(
            (4, 18, 28, 24),
            fill=(110, 70, 40, 255),
            outline=(40, 25, 10, 255),
            width=2,
        )
        draw.rectangle(
            (6, 12, 26, 18),
            fill=(90, 90, 100, 255),
            outline=(30, 30, 35, 255),
            width=2,
        )
        draw.rectangle((20, 8, 26, 12), fill=(60, 60, 70, 255))

    elif kind == PickupKind.WEAPON_MACHINEGUN:
        draw.rectangle(
            (4, 16, 28, 22),
            fill=(80, 80, 90, 255),
            outline=(25, 25, 30, 255),
            width=2,
        )
        draw.rectangle(
            (8, 10, 24, 16),
            fill=(110, 110, 120, 255),
            outline=(25, 25, 30, 255),
            width=2,
        )
        draw.rectangle((14, 22, 18, 28), fill=(70, 70, 80, 255))

    elif kind == PickupKind.SECRET:
        draw.polygon(
            ((16, 2), (28, 16), (16, 30), (4, 16)),
            fill=(240, 220, 80, 255),
            outline=(120, 100, 20, 255),
            width=2,
        )

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


def create_particle_surface(color: tuple[int, int, int]) -> pygame.Surface:
    """
    Genera una superficie pequeña y semitransparente para ser usada como partícula.
    """
    surface = pygame.Surface((6, 6), pygame.SRCALPHA)

    pygame.draw.circle(surface, color, (3, 3), 3)
    pygame.draw.circle(surface, (255, 255, 255), (3, 3), 1)

    return surface.convert_alpha()

def create_decoration_sprite(kind: str) -> pygame.Surface:
    """Genera sprites de decoraciones ambientales."""
    size = 32
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    if kind == "torch":
        # Antorcha: palo con llama
        draw.rectangle((14, 12, 18, 30), fill=(120, 80, 40, 255), outline=(80, 50, 20, 255))
        # Llama
        draw.ellipse((10, 2, 22, 16), fill=(255, 150, 30, 255), outline=(200, 100, 10, 255))
        draw.ellipse((12, 4, 20, 14), fill=(255, 220, 80, 255))
        draw.ellipse((14, 6, 18, 12), fill=(255, 255, 200, 255))
        # Soporte
        draw.rectangle((12, 28, 20, 32), fill=(80, 80, 90, 255))

    elif kind == "column":
        # Columna: pilar de piedra
        draw.rectangle((10, 4, 22, 30), fill=(140, 130, 120, 255), outline=(90, 85, 80, 255), width=2)
        # Capitel
        draw.rectangle((8, 2, 24, 6), fill=(160, 150, 140, 255), outline=(100, 95, 90, 255))
        # Base
        draw.rectangle((8, 28, 24, 32), fill=(160, 150, 140, 255), outline=(100, 95, 90, 255))
        # Estrías
        for x in range(12, 22, 3):
            draw.line([(x, 6), (x, 28)], fill=(120, 110, 100, 255), width=1)

    elif kind == "barrel":
        # Barril: cilindro de madera
        draw.ellipse((8, 4, 24, 12), fill=(160, 100, 40, 255), outline=(100, 60, 20, 255))
        draw.rectangle((8, 8, 24, 26), fill=(150, 95, 35, 255), outline=(100, 60, 20, 255))
        draw.ellipse((8, 22, 24, 30), fill=(140, 85, 30, 255), outline=(100, 60, 20, 255))
        # Aros metálicos
        draw.line([(8, 12), (24, 12)], fill=(120, 120, 130, 255), width=2)
        draw.line([(8, 22), (24, 22)], fill=(120, 120, 130, 255), width=2)

    elif kind == "console":
        # Consola/Computadora
        draw.rectangle((6, 10, 26, 28), fill=(60, 70, 80, 255), outline=(30, 35, 40, 255), width=2)
        # Pantalla
        draw.rectangle((8, 12, 24, 22), fill=(20, 80, 60, 255), outline=(10, 40, 30, 255))
        # Texto en pantalla
        for y in range(14, 20, 3):
            draw.line([(10, y), (20, y)], fill=(50, 200, 100, 255), width=1)
        # Botones
        draw.rectangle((10, 24, 14, 26), fill=(200, 50, 50, 255))
        draw.rectangle((16, 24, 20, 26), fill=(50, 200, 50, 255))

    elif kind == "skull":
        # Calavera decorativa
        draw.ellipse((8, 4, 24, 18), fill=(230, 220, 200, 255), outline=(180, 170, 150, 255), width=1)
        # Ojos
        draw.ellipse((11, 8, 15, 12), fill=(20, 20, 20, 255))
        draw.ellipse((17, 8, 21, 12), fill=(20, 20, 20, 255))
        # Nariz
        draw.polygon(((15, 12), (16, 16), (17, 12)), fill=(20, 20, 20, 255))
        # Mandíbula
        draw.rectangle((10, 18, 22, 24), fill=(220, 210, 190, 255), outline=(170, 160, 140, 255))
        # Dientes
        for x in range(12, 22, 3):
            draw.rectangle((x, 18, x + 2, 22), fill=(240, 235, 220, 255))

    return pygame.image.frombytes(image.tobytes(), image.size, image.mode).convert_alpha()
