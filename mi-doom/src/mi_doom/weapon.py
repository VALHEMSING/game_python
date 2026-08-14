from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Weapon:
    slot: int
    id: str
    name: str
    damage: float
    fire_rate: float
    ammo_type: str | None
    ammo_cost: int
    range: float
    spread: float
    pellets: int = 1
    automatic: bool = False
    cooldown: float = 0.0

    @property
    def time_between_shots(self) -> float:
        return 1.0 / max(self.fire_rate, 0.0001)

    def update(self, dt: float) -> None:
        self.cooldown = max(0.0, self.cooldown - dt)

    def can_fire(self, ammo: dict[str, int]) -> bool:
        if self.cooldown > 0.0:
            return False

        if self.ammo_type is None:
            return True

        return ammo.get(self.ammo_type, 0) >= self.ammo_cost

    def fire(self) -> None:
        self.cooldown = self.time_between_shots

    def consume_ammo(self, ammo: dict[str, int]) -> None:
        if self.ammo_type is None or self.ammo_cost <= 0:
            return

        ammo[self.ammo_type] = max(0, ammo.get(self.ammo_type, 0) - self.ammo_cost)


def create_default_weapons() -> dict[int, Weapon]:
    return {
        1: Weapon(
            slot=1,
            id="pistol",
            name="Pistola",
            damage=12.0,
            fire_rate=3.2,
            ammo_type=None,
            ammo_cost=0,
            range=18.0,
            spread=0.012,
            pellets=1,
            automatic=False,
        ),
        2: Weapon(
            slot=2,
            id="shotgun",
            name="Escopeta",
            damage=8.0,
            fire_rate=1.1,
            ammo_type="shells",
            ammo_cost=1,
            range=9.0,
            spread=0.13,
            pellets=7,
            automatic=False,
        ),
        3: Weapon(
            slot=3,
            id="machinegun",
            name="Ametralladora",
            damage=7.0,
            fire_rate=9.0,
            ammo_type="bullets",
            ammo_cost=1,
            range=18.0,
            spread=0.05,
            pellets=1,
            automatic=True,
        ),
    }