"""
Generador procedural de niveles para mi-doom.

Utiliza el algoritmo BSP (Binary Space Partitioning) para crear
habitaciones conectadas por pasillos, garantizando estructura coherente
y validación de conectividad. Soporta semillas reproducibles y
dificultad progresiva.
"""
from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass
class Room:
    """Representa una habitación rectangular en el mapa."""
    x: int
    y: int
    width: int
    height: int

    @property
    def center_x(self) -> int:
        """Centro horizontal de la habitación."""
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        """Centro vertical de la habitación."""
        return self.y + self.height // 2

    @property
    def area(self) -> int:
        """Área de la habitación."""
        return self.width * self.height

    def intersects(self, other: Room, margin: int = 0) -> bool:
        """Comprueba si esta habitación se solapa con otra."""
        return (
            self.x - margin < other.x + other.width
            and self.x + self.width + margin > other.x
            and self.y - margin < other.y + other.height
            and self.y + self.height + margin > other.y
        )


@dataclass
class BSPNode:
    """Nodo del árbol BSP que representa una partición del mapa."""
    x: int
    y: int
    width: int
    height: int
    left: BSPNode | None = None
    right: BSPNode | None = None
    room: Room | None = None

    @property
    def is_leaf(self) -> bool:
        """Indica si el nodo es una hoja (sin hijos)."""
        return self.left is None and self.right is None


class LevelGenerator:
    """
    Generador procedural de niveles usando BSP.

    Genera mapas con habitaciones conectadas, puertas, llaves,
    enemigos, pickups y salida, garantizando conectividad completa.
    """

    WALL = "#"
    FLOOR = "."
    DOOR_NORMAL = "D"
    DOOR_RED = "R"
    DOOR_BLUE = "B"
    DOOR_YELLOW = "Y"
    SWITCH = "S"
    EXIT = "X"
    PLAYER_START = "P"

    DOOR_TILES = {DOOR_NORMAL, DOOR_RED, DOOR_BLUE, DOOR_YELLOW}

    def __init__(
        self,
        seed: int | None = None,
        width: int = 40,
        height: int = 40,
        min_room_size: int = 4,
        max_room_size: int = 8,
        difficulty: int = 1,
    ) -> None:
        """Inicializa el generador con parámetros de mapa y dificultad."""
        self.rng = random.Random(seed)
        self.width = width
        self.height = height
        self.min_room_size = min_room_size
        self.max_room_size = max_room_size
        self.difficulty = max(1, min(difficulty, 10))

        self.grid: list[list[str]] = []
        self.rooms: list[Room] = []
        self.root: BSPNode | None = None
        self.player_start: tuple[int, int] = (1, 1)
        self.exit_pos: tuple[int, int] = (1, 1)
        self.enemies: list[dict[str, Any]] = []
        self.pickups: list[dict[str, Any]] = []
        self.switches: list[dict[str, Any]] = []
        self.decorations: list[dict[str, Any]] = []
        self.seed_used = seed if seed is not None else self.rng.randint(0, 2**31)

    def generate(self) -> dict[str, Any]:
        """
        Genera un nivel completo y lo devuelve en formato compatible
        con el sistema de carga de niveles del juego.
        """
        self.rng = random.Random(self.seed_used)
        self._init_grid()
        self._build_bsp()
        self._create_rooms()
        self._connect_rooms()
        self._place_boundaries()
        self._validate_no_unintended_openings()
        self._place_player_and_exit()
        self._place_doors_and_keys()
        self._validate_door_connectivity()
        self._place_switches_and_secrets()
        self._place_enemies()
        self._place_pickups()
        self._place_decorations()
        self._ensure_exit_exists()

        return {
            "name": f"Nivel Procedural - Semilla {self.seed_used}",
            "player_start": [self.player_start[0] + 0.5, self.player_start[1] + 0.5],
            "grid": ["".join(row) for row in self.grid],
            "enemies": self.enemies,
            "pickups": self.pickups,
            "switches": self.switches,
            "decorations": self.decorations,
        }

    def _init_grid(self) -> None:
        """Inicializa el grid lleno de paredes."""
        self.grid = [
            [self.WALL for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def _build_bsp(self) -> None:
        """Construye el árbol BSP dividiendo recursivamente el mapa."""
        self.root = BSPNode(1, 1, self.width - 2, self.height - 2)
        self._split_node(self.root)

    def _split_node(self, node: BSPNode) -> None:
        """Divide un nodo en dos hijos si es posible."""
        if node.width < self.min_room_size * 2 and node.height < self.min_room_size * 2:
            return

        if node.width > node.height:
            split_horizontal = False
        elif node.height > node.width:
            split_horizontal = True
        else:
            split_horizontal = self.rng.random() < 0.5

        if split_horizontal:
            if node.height < self.min_room_size * 2:
                return
            split_pos = self.rng.randint(
                self.min_room_size,
                node.height - self.min_room_size
            )
            node.left = BSPNode(node.x, node.y, node.width, split_pos)
            node.right = BSPNode(node.x, node.y + split_pos, node.width, node.height - split_pos)
        else:
            if node.width < self.min_room_size * 2:
                return
            split_pos = self.rng.randint(
                self.min_room_size,
                node.width - self.min_room_size
            )
            node.left = BSPNode(node.x, node.y, split_pos, node.height)
            node.right = BSPNode(node.x + split_pos, node.y, node.width - split_pos, node.height)

        self._split_node(node.left)
        self._split_node(node.right)

    def _create_rooms(self) -> None:
        """Crea habitaciones en las hojas del árbol BSP."""
        self.rooms = []
        self._create_rooms_recursive(self.root)

    def _create_rooms_recursive(self, node: BSPNode | None) -> None:
        """Recorre el árbol creando habitaciones en las hojas."""
        if node is None:
            return

        if node.is_leaf:
            room = self._create_room_in_node(node)
            if room is not None:
                node.room = room
                self.rooms.append(room)
                self._carve_room(room)
        else:
            self._create_rooms_recursive(node.left)
            self._create_rooms_recursive(node.right)

    def _create_room_in_node(self, node: BSPNode) -> Room | None:
        """Crea una habitación aleatoria dentro de un nodo BSP."""
        max_w = min(node.width - 2, self.max_room_size)
        max_h = min(node.height - 2, self.max_room_size)

        if max_w < self.min_room_size or max_h < self.min_room_size:
            return None

        room_w = self.rng.randint(self.min_room_size, max_w)
        room_h = self.rng.randint(self.min_room_size, max_h)

        room_x = node.x + self.rng.randint(1, node.width - room_w - 1)
        room_y = node.y + self.rng.randint(1, node.height - room_h - 1)

        return Room(room_x, room_y, room_w, room_h)

    def _carve_room(self, room: Room) -> None:
        """Excava una habitación en el grid (coloca suelo)."""
        for y in range(room.y, room.y + room.height):
            for x in range(room.x, room.x + room.width):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.grid[y][x] = self.FLOOR

    def _connect_rooms(self) -> None:
        """Conecta las habitaciones hermanas en el árbol BSP con pasillos."""
        self._connect_recursive(self.root)

    def _connect_recursive(self, node: BSPNode | None) -> None:
        """Recorre el árbol conectando nodos hijos."""
        if node is None or node.is_leaf:
            return

        self._connect_recursive(node.left)
        self._connect_recursive(node.right)

        left_room = self._get_room_from_node(node.left)
        right_room = self._get_room_from_node(node.right)

        if left_room is not None and right_room is not None:
            self._carve_corridor(left_room, right_room)

    def _get_room_from_node(self, node: BSPNode | None) -> Room | None:
        """Obtiene una habitación de un nodo (buscando en hojas si es necesario)."""
        if node is None:
            return None
        if node.room is not None:
            return node.room
        if node.is_leaf:
            return None

        left_room = self._get_room_from_node(node.left)
        right_room = self._get_room_from_node(node.right)

        if left_room is not None and right_room is not None:
            return self.rng.choice([left_room, right_room])
        return left_room or right_room

    def _carve_corridor(self, room_a: Room, room_b: Room) -> None:
        """Excava un pasillo en L de ancho 1 entre dos habitaciones."""
        x1, y1 = room_a.center_x, room_a.center_y
        x2, y2 = room_b.center_x, room_b.center_y

        if self.rng.random() < 0.5:
            self._carve_h_corridor(x1, x2, y1)
            self._carve_v_corridor(y1, y2, x2)
        else:
            self._carve_v_corridor(y1, y2, x1)
            self._carve_h_corridor(x1, x2, y2)

    def _carve_h_corridor(self, x1: int, x2: int, y: int) -> None:
        """Excava un pasillo horizontal de ancho 1."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                if self.grid[y][x] == self.WALL:
                    self.grid[y][x] = self.FLOOR

    def _carve_v_corridor(self, y1: int, y2: int, x: int) -> None:
        """Excava un pasillo vertical de ancho 1."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                if self.grid[y][x] == self.WALL:
                    self.grid[y][x] = self.FLOOR

    def _place_boundaries(self) -> None:
        """Asegura que los bordes del mapa sean paredes sólidas."""
        for x in range(self.width):
            self.grid[0][x] = self.WALL
            self.grid[self.height - 1][x] = self.WALL

        for y in range(self.height):
            self.grid[y][0] = self.WALL
            self.grid[y][self.width - 1] = self.WALL

    def _validate_no_unintended_openings(self) -> None:
        """Valida que no haya aperturas no intencionales entre habitaciones."""
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if self.grid[y][x] != self.FLOOR:
                    continue

                floor_neighbors = 0
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = y + dy, x + dx
                    if self.grid[ny][nx] != self.WALL:
                        floor_neighbors += 1

                if floor_neighbors > 2 and not self._is_inside_any_room(x, y):
                    if not self._is_corridor_tile(x, y):
                        self.grid[y][x] = self.WALL

    def _is_inside_any_room(self, x: int, y: int) -> bool:
        """Verifica si una posición está dentro de alguna habitación."""
        for room in self.rooms:
            if (room.x <= x < room.x + room.width and
                    room.y <= y < room.y + room.height):
                return True
        return False

    def _is_corridor_tile(self, x: int, y: int) -> bool:
        """Verifica si un tile es parte de un corredor de ancho 1."""
        has_wall_up = self.grid[y-1][x] == self.WALL
        has_wall_down = self.grid[y+1][x] == self.WALL
        horizontal_corridor = has_wall_up and has_wall_down

        has_wall_left = self.grid[y][x-1] == self.WALL
        has_wall_right = self.grid[y][x+1] == self.WALL
        vertical_corridor = has_wall_left and has_wall_right

        return horizontal_corridor or vertical_corridor

    def _place_player_and_exit(self) -> None:
        """Coloca al jugador en la primera habitación y la salida en la más lejana."""
        if not self.rooms:
            return

        start_room = self.rooms[0]
        self.player_start = (start_room.center_x, start_room.center_y)
        self.grid[self.player_start[1]][self.player_start[0]] = self.PLAYER_START

        max_dist = 0
        exit_room = self.rooms[-1]

        for room in self.rooms:
            dist = (abs(room.center_x - self.player_start[0]) +
                    abs(room.center_y - self.player_start[1]))
            if dist > max_dist:
                max_dist = dist
                exit_room = room

        exit_pos = self._find_exit_position(exit_room)
        if exit_pos is not None:
            self.exit_pos = exit_pos
        else:
            self.exit_pos = (exit_room.center_x, exit_room.center_y)

        self.grid[self.exit_pos[1]][self.exit_pos[0]] = self.EXIT

    def _find_exit_position(self, room: Room) -> tuple[int, int] | None:
        """
        Encuentra una posición válida para la salida en el borde de una habitación.
        La salida debe estar en una pared adyacente a la habitación.
        """
        candidates = []

        for x in range(room.x, room.x + room.width):
            y = room.y - 1
            if self._is_valid_exit_spot(x, y):
                candidates.append((x, y))

            y = room.y + room.height
            if self._is_valid_exit_spot(x, y):
                candidates.append((x, y))

        for y in range(room.y, room.y + room.height):
            x = room.x - 1
            if self._is_valid_exit_spot(x, y):
                candidates.append((x, y))

            x = room.x + room.width
            if self._is_valid_exit_spot(x, y):
                candidates.append((x, y))

        if not candidates:
            return None

        return self.rng.choice(candidates)

    def _is_valid_exit_spot(self, x: int, y: int) -> bool:
        """
        Verifica si una posición es válida para la salida.
        Debe ser una pared adyacente a suelo.
        """
        if not (0 < x < self.width - 1 and 0 < y < self.height - 1):
            return False

        if self.grid[y][x] != self.WALL:
            return False

        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = y + dy, x + dx
            if self.grid[ny][nx] == self.FLOOR:
                return True

        return False

    def _place_doors_and_keys(self) -> None:
        """Coloca puertas de colores en posiciones válidas con paredes a ambos lados."""
        if len(self.rooms) < 4:
            return

        candidate_rooms = self.rooms[1:-1]
        self.rng.shuffle(candidate_rooms)

        door_types = [
            (self.DOOR_RED, "key_red"),
            (self.DOOR_BLUE, "key_blue"),
            (self.DOOR_YELLOW, "key_yellow"),
        ]

        placed_doors = 0
        max_doors = min(3, len(candidate_rooms), self.difficulty)

        for i in range(max_doors):
            if i >= len(candidate_rooms):
                break

            door_tile, key_type = door_types[i]
            room = candidate_rooms[i]

            door_pos = self._find_valid_door_position(room)
            if door_pos is not None:
                dx, dy = door_pos
                self.grid[dy][dx] = door_tile

                key_room = self._find_key_room(room)
                if key_room is not None:
                    kx, ky = key_room.center_x, key_room.center_y
                    if (kx, ky) != self.player_start and (kx, ky) != self.exit_pos:
                        self.pickups.append({
                            "type": key_type,
                            "x": kx + 0.5,
                            "y": ky + 0.5,
                        })
                placed_doors += 1

    def _find_key_room(self, door_room: Room) -> Room | None:
        """Encuentra una habitación adecuada para colocar la llave (lejana de la puerta)."""
        candidates = [
            r for r in self.rooms
            if r is not door_room
            and (r.center_x, r.center_y) != self.player_start
            and (r.center_x, r.center_y) != self.exit_pos
        ]

        if not candidates:
            return None

        candidates.sort(
            key=lambda r: (abs(r.center_x - door_room.center_x) +
                           abs(r.center_y - door_room.center_y)),
            reverse=True,
        )

        top_candidates = candidates[:3]
        return self.rng.choice(top_candidates)

    def _find_valid_door_position(self, room: Room) -> tuple[int, int] | None:
        """
        Encuentra una posición válida para una puerta donde haya paredes
        a ambos lados, asegurando que sea un punto de paso obligatorio.
        """
        candidates = []

        for x in range(room.x, room.x + room.width):
            y = room.y - 1
            if self._is_valid_door_spot(x, y):
                candidates.append((x, y))

            y = room.y + room.height
            if self._is_valid_door_spot(x, y):
                candidates.append((x, y))

        for y in range(room.y, room.y + room.height):
            x = room.x - 1
            if self._is_valid_door_spot(x, y):
                candidates.append((x, y))

            x = room.x + room.width
            if self._is_valid_door_spot(x, y):
                candidates.append((x, y))

        if not candidates:
            return None

        return self.rng.choice(candidates)

    def _is_valid_door_spot(self, x: int, y: int) -> bool:
        """
        Verifica si una posición es válida para una puerta.
        Debe ser suelo y tener paredes a ambos lados (formando un umbral).
        """
        if not (0 < x < self.width - 1 and 0 < y < self.height - 1):
            return False

        if self.grid[y][x] != self.FLOOR:
            return False

        has_wall_up = self.grid[y-1][x] == self.WALL
        has_wall_down = self.grid[y+1][x] == self.WALL
        horizontal_valid = has_wall_up and has_wall_down

        has_wall_left = self.grid[y][x-1] == self.WALL
        has_wall_right = self.grid[y][x+1] == self.WALL
        vertical_valid = has_wall_left and has_wall_right

        return horizontal_valid or vertical_valid

    def _validate_door_connectivity(self) -> None:
        """
        Valida que cada puerta sea un punto de articulación.
        Si hay caminos alternativos que rodean una puerta, los bloquea.
        """
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] in self.DOOR_TILES:
                    if not self._is_articulation_point(x, y):
                        self._block_alternative_paths(x, y)

    def _is_articulation_point(self, door_x: int, door_y: int) -> bool:
        """Verifica si una puerta es un punto de articulación."""
        start = self._find_nearest_floor(door_x, door_y)
        if start is None:
            return True

        visited_without_door = self._bfs_flood_fill(start, exclude=(door_x, door_y))

        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = door_y + dy, door_x + dx
            if (0 <= ny < self.height and 0 <= nx < self.width and
                    self.grid[ny][nx] != self.WALL and
                    (nx, ny) != (door_x, door_y)):
                if (nx, ny) not in visited_without_door:
                    return True

        return False

    def _find_nearest_floor(self, x: int, y: int) -> tuple[int, int] | None:
        """Encuentra el tile de suelo más cercano a una posición."""
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = y + dy, x + dx
            if (0 <= ny < self.height and 0 <= nx < self.width and
                    self.grid[ny][nx] != self.WALL):
                return (nx, ny)
        return None

    def _bfs_flood_fill(
        self,
        start: tuple[int, int],
        exclude: tuple[int, int] | None = None
    ) -> set[tuple[int, int]]:
        """Realiza un BFS desde una posición, opcionalmente excluyendo un tile."""
        visited = set()
        queue = deque([start])
        visited.add(start)

        while queue:
            cx, cy = queue.popleft()
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if (
                    0 <= nx < self.width and
                    0 <= ny < self.height and
                    self.grid[ny][nx] != self.WALL and
                    (nx, ny) not in visited and
                    (exclude is None or (nx, ny) != exclude)
                ):
                    visited.add((nx, ny))
                    queue.append((nx, ny))

        return visited

    def _block_alternative_paths(self, door_x: int, door_y: int) -> None:
        """Bloquea caminos alternativos que permiten rodear una puerta."""
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = door_y + dy, door_x + dx
            if (0 < ny < self.height - 1 and 0 < nx < self.width - 1):
                if self.grid[ny][nx] == self.FLOOR:
                    if not self._is_corridor_tile(nx, ny):
                        self.grid[ny][nx] = self.WALL

    def _place_switches_and_secrets(self) -> None:
        """Coloca interruptores que abren puertas secretas y pickups secretos."""
        if len(self.rooms) < 3:
            return

        candidate_rooms = self.rooms[1:-1]
        if not candidate_rooms:
            return

        switch_room = self.rng.choice(candidate_rooms)

        switch_pos = self._find_valid_door_position(switch_room)
        if switch_pos is None:
            return

        sx, sy = switch_pos

        secret_candidates = [
            r for r in self.rooms
            if r is not switch_room
            and (r.center_x, r.center_y) != self.player_start
            and (r.center_x, r.center_y) != self.exit_pos
        ]

        if not secret_candidates:
            return

        secret_room = self.rng.choice(secret_candidates)
        secret_pos = self._find_valid_door_position(secret_room)

        if secret_pos is None:
            return

        tx, ty = secret_pos

        self.grid[sy][sx] = self.SWITCH
        self.grid[ty][tx] = self.DOOR_NORMAL

        self.switches.append({
            "x": sx,
            "y": sy,
            "targets": [[tx, ty]],
        })

        secret_x = secret_room.center_x + self.rng.randint(-1, 1)
        secret_y = secret_room.center_y + self.rng.randint(-1, 1)

        if (
            0 < secret_x < self.width - 1 and
            0 < secret_y < self.height - 1 and
            self.grid[secret_y][secret_x] == self.FLOOR
        ):
            self.pickups.append({
                "type": "secret",
                "x": secret_x + 0.5,
                "y": secret_y + 0.5,
            })

    def _place_enemies(self) -> None:
        """Coloca enemigos en las habitaciones según la dificultad."""
        if not self.rooms:
            return

        base_count = 2 + self.difficulty * 2

        candidate_rooms = self.rooms[1:]
        self.rng.shuffle(candidate_rooms)

        placed = 0
        for room in candidate_rooms:
            if placed >= base_count:
                break

            if self.difficulty <= 3:
                enemy_type = self.rng.choice(["drone", "drone", "mutant"])
            elif self.difficulty <= 6:
                enemy_type = self.rng.choice(["drone", "mutant", "mutant", "beast"])
            else:
                enemy_type = self.rng.choice(["mutant", "beast", "beast"])

            offset_x = self.rng.randint(-1, 1)
            offset_y = self.rng.randint(-1, 1)

            ex = room.center_x + offset_x
            ey = room.center_y + offset_y

            if (
                0 < ex < self.width - 1 and
                0 < ey < self.height - 1 and
                self.grid[ey][ex] == self.FLOOR and
                (ex, ey) != self.player_start and
                (ex, ey) != self.exit_pos
            ):
                self.enemies.append({
                    "type": enemy_type,
                    "x": ex + 0.5,
                    "y": ey + 0.5,
                })
                placed += 1

    def _place_pickups(self) -> None:
        """Coloca pickups de salud, armadura y munición en las habitaciones."""
        if not self.rooms:
            return

        pickup_types = [
            "health", "health", "health",
            "armor", "armor",
            "ammo_bullets", "ammo_bullets", "ammo_bullets",
            "ammo_shells", "ammo_shells",
        ]

        pickup_count = 4 + self.difficulty

        candidate_rooms = self.rooms[1:]
        self.rng.shuffle(candidate_rooms)

        placed = 0
        for room in candidate_rooms:
            if placed >= pickup_count:
                break

            pickup_type = self.rng.choice(pickup_types)

            px = self.rng.randint(room.x + 1, room.x + room.width - 2)
            py = self.rng.randint(room.y + 1, room.y + room.height - 2)

            if (
                0 < px < self.width - 1 and
                0 < py < self.height - 1 and
                self.grid[py][px] == self.FLOOR and
                (px, py) != self.player_start and
                (px, py) != self.exit_pos
            ):
                self.pickups.append({
                    "type": pickup_type,
                    "x": px + 0.5,
                    "y": py + 0.5,
                })
                placed += 1

        if self.rooms:
            start_room = self.rooms[0]
            health_x = start_room.center_x + 1
            health_y = start_room.center_y

            if (
                0 < health_x < self.width - 1 and
                0 < health_y < self.height - 1 and
                self.grid[health_y][health_x] == self.FLOOR
            ):
                self.pickups.append({
                    "type": "health",
                    "x": health_x + 0.5,
                    "y": health_y + 0.5,
                })

    def _place_decorations(self) -> None:
        """Coloca decoraciones ambientales en las habitaciones."""
        if not self.rooms:
            return

        decoration_types = ["torch", "column", "barrel", "console", "skull"]

        for room in self.rooms:
            num_decorations = self.rng.randint(0, max(1, room.area // 12))

            for _ in range(num_decorations):
                deco_type = self.rng.choice(decoration_types)

                dx = self.rng.randint(room.x + 1, room.x + room.width - 2)
                dy = self.rng.randint(room.y + 1, room.y + room.height - 2)

                if (
                    0 < dx < self.width - 1 and
                    0 < dy < self.height - 1 and
                    self.grid[dy][dx] == self.FLOOR and
                    (dx, dy) != self.player_start and
                    (dx, dy) != self.exit_pos
                ):
                    self.decorations.append({
                        "type": deco_type,
                        "x": dx + 0.5,
                        "y": dy + 0.5,
                    })

    def _ensure_exit_exists(self) -> None:
        """
        Verificación final: asegura que la salida existe en el grid.
        Si no existe, la coloca en la habitación más lejana.
        """
        exit_found = False
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == self.EXIT:
                    exit_found = True
                    break
            if exit_found:
                break

        if not exit_found and self.rooms:
            max_dist = 0
            exit_room = self.rooms[-1]

            for room in self.rooms:
                dist = (abs(room.center_x - self.player_start[0]) +
                        abs(room.center_y - self.player_start[1]))
                if dist > max_dist:
                    max_dist = dist
                    exit_room = room

            self.exit_pos = (exit_room.center_x, exit_room.center_y)
            self.grid[self.exit_pos[1]][self.exit_pos[0]] = self.EXIT
