from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Iterable

from mi_doom.entities import (
    DOOR_TILES,
    EXIT_TILE,
    SWITCH_TILE,
    Door,
    Pickup,
    PickupKind,
)

DEFAULT_GRID = [
    "########################",
    "#P.....#........#......#",
    "#......#..####..#......#",
    "#......#........#......#",
    "#......................#",
    "#......#........#......#",
    "#......#..####..#......#",
    "#......#........#......#",
    "#......#...##...#......#",
    "#......................#",
    "########################",
]

DEFAULT_ENEMY_SPAWNS: list[dict[str, Any]] = [
    {
        "type": "drone",
        "x": 8.5,
        "y": 2.5,
    },
    {
        "type": "mutant",
        "x": 12.5,
        "y": 4.5,
    },
    {
        "type": "beast",
        "x": 18.5,
        "y": 8.5,
    },
]

WALKABLE_TILES = {".", "P"}


class Level:
    def __init__(
        self,
        grid: Iterable[str],
        player_start: tuple[float, float] | None = None,
        name: str = "Level",
        enemy_spawns: list[dict[str, Any]] | None = None,
        pickup_spawns: list[dict[str, Any]] | None = None,
        switch_links: list[dict[str, Any]] | None = None,
    ) -> None:
        rows = [str(row) for row in grid]
        if not rows:
            raise ValueError("Level grid cannot be empty.")

        width = max(len(row) for row in rows)
        self.grid: list[str] = [row.ljust(width, "#") for row in rows]
        self.width = width
        self.height = len(self.grid)
        self.name = name

        self.enemy_spawns = list(enemy_spawns) if enemy_spawns else []

        self.doors: dict[tuple[int, int], Door] = {}
        self.switches: set[tuple[int, int]] = set()
        self.activated_switches: set[tuple[int, int]] = set()
        self.switch_links: dict[tuple[int, int], list[tuple[int, int]]] = {}

        self._scan_tiles()

        self.pickups = self._create_pickups(pickup_spawns or [])
        self._parse_switch_links(switch_links or [])

        grid_start = self._extract_start_from_grid()

        if player_start is None:
            player_start = grid_start or self._first_walkable_position()

        if player_start is None or not self._is_acceptable_start(player_start):
            fallback = self._first_walkable_position()
            if fallback is None:
                raise ValueError("Level has no walkable tile.")
            player_start = fallback

        self.player_start = player_start

    @classmethod
    def load(cls, path: Path | str) -> Level:
        file_path = Path(path)

        if not file_path.exists():
            return cls.default()

        data = json.loads(file_path.read_text(encoding="utf-8"))
        grid = data.get("grid")

        if not grid:
            return cls.default()

        raw_start = data.get("player_start")
        start: tuple[float, float] | None = None

        if raw_start is not None and len(raw_start) >= 2:
            start = (float(raw_start[0]), float(raw_start[1]))

        raw_enemy_spawns = data.get("enemies", [])
        enemy_spawns = raw_enemy_spawns if isinstance(raw_enemy_spawns, list) else []

        raw_pickup_spawns = data.get("pickups", [])
        pickup_spawns = raw_pickup_spawns if isinstance(raw_pickup_spawns, list) else []

        raw_switch_links = data.get("switches", [])
        switch_links = raw_switch_links if isinstance(raw_switch_links, list) else []

        return cls(
            grid=grid,
            player_start=start,
            name=str(data.get("name", file_path.stem)),
            enemy_spawns=enemy_spawns,
            pickup_spawns=pickup_spawns,
            switch_links=switch_links,
        )

    @classmethod
    def default(cls) -> Level:
        return cls(
            DEFAULT_GRID,
            name="Default",
            enemy_spawns=DEFAULT_ENEMY_SPAWNS,
            pickup_spawns=[],
            switch_links=[],
        )

    def update(self, dt: float) -> None:
        for door in self.doors.values():
            door.update(dt)

    def _scan_tiles(self) -> None:
        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                if tile in DOOR_TILES:
                    self.doors[(x, y)] = Door(x, y, tile)
                elif tile == SWITCH_TILE:
                    self.switches.add((x, y))

    def _create_pickups(
        self,
        raw_spawns: list[dict[str, Any]],
    ) -> list[Pickup]:
        pickups: list[Pickup] = []

        if not isinstance(raw_spawns, list):
            return pickups

        for raw in raw_spawns:
            try:
                kind = PickupKind(str(raw.get("type", "")))
                x = float(raw.get("x", 0.0))
                y = float(raw.get("y", 0.0))
            except (ValueError, TypeError):
                continue

            tile_x = int(math.floor(x))
            tile_y = int(math.floor(y))

            if self.is_solid(tile_x, tile_y):
                continue

            pickups.append(Pickup(kind=kind, x=x, y=y))

        return pickups

    def _parse_switch_links(self, raw_links: list[dict[str, Any]]) -> None:
        if not isinstance(raw_links, list):
            return

        for raw in raw_links:
            try:
                x = int(raw.get("x", 0))
                y = int(raw.get("y", 0))
                raw_targets = raw.get("targets", [])
            except (TypeError, ValueError):
                continue

            targets: list[tuple[int, int]] = []

            if isinstance(raw_targets, list):
                for target in raw_targets:
                    try:
                        targets.append((int(target[0]), int(target[1])))
                    except (TypeError, ValueError, IndexError):
                        continue

            if targets:
                self.switch_links[(x, y)] = targets

    def _extract_start_from_grid(self) -> tuple[float, float] | None:
        start: tuple[float, float] | None = None
        clean_rows: list[str] = []

        for y, row in enumerate(self.grid):
            if "P" in row:
                x = row.index("P")
                if start is None:
                    start = (x + 0.5, y + 0.5)
                row = row.replace("P", ".")
            clean_rows.append(row)

        self.grid = clean_rows
        return start

    def _first_walkable_position(self) -> tuple[float, float] | None:
        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                if tile in WALKABLE_TILES:
                    return (x + 0.5, y + 0.5)
        return None

    def _is_acceptable_start(self, start: tuple[float, float]) -> bool:
        x, y = start
        tile_x = int(math.floor(x))
        tile_y = int(math.floor(y))
        return not self.is_solid(tile_x, tile_y)

    def tile_at(self, x: int, y: int) -> str:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return "#"
        return self.grid[y][x]

    def is_walkable(self, x: int, y: int) -> bool:
        tile = self.tile_at(x, y)

        if tile in DOOR_TILES:
            door = self.doors.get((x, y))
            return door is not None and door.is_passable

        if tile == SWITCH_TILE:
            return False

        if tile == EXIT_TILE:
            return False

        return tile in WALKABLE_TILES

    def is_solid(self, x: int, y: int) -> bool:
        return not self.is_walkable(x, y)

    def find_interactable_in_front(self, player: Any) -> tuple[int, int] | None:
        distances = (0.5, 0.9, 1.3, 1.7)

        for distance in distances:
            probe_x = player.x + math.cos(player.angle) * distance
            probe_y = player.y + math.sin(player.angle) * distance

            tile_x = int(math.floor(probe_x))
            tile_y = int(math.floor(probe_y))

            tile = self.tile_at(tile_x, tile_y)

            if tile in DOOR_TILES:
                door = self.doors.get((tile_x, tile_y))
                if door is not None and not door.is_open:
                    return (tile_x, tile_y)
                continue

            if tile == SWITCH_TILE:
                return (tile_x, tile_y)

            if tile == EXIT_TILE:
                return (tile_x, tile_y)

            if self.is_solid(tile_x, tile_y):
                break

        return None

    def try_open_door_at(
        self,
        position: tuple[int, int],
        player: Any,
    ) -> tuple[bool, str]:
        door = self.doors.get(position)
        if door is None:
            return False, ""

        return door.try_open(player)

    def activate_switch(self, position: tuple[int, int]) -> bool:
        if position not in self.switches:
            return False

        if position in self.activated_switches:
            return False

        self.activated_switches.add(position)

        targets = self.switch_links.get(position, [])

        if targets:
            for target in targets:
                door = self.doors.get(target)
                if door is not None:
                    door.force_open()
        else:
            # Sin objetivos explícitos, el interruptor abre puertas normales.
            for door in self.doors.values():
                if door.required_key is None:
                    door.force_open()

        return True