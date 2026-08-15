from __future__ import annotations

import math
import random
from typing import Any


class Particle:
    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        ttl: float,
        sprite: Any,
        scale: float,
    ) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.ttl = ttl
        self.age = 0.0
        self.sprite = sprite
        self.scale = scale

    @property
    def is_dead(self) -> bool:
        return self.age >= self.ttl

    def update(self, dt: float) -> None:
        self.age += dt

        damping = max(0.0, 1.0 - 2.2 * dt)
        self.vx *= damping
        self.vy *= damping

        self.x += self.vx * dt
        self.y += self.vy * dt


class ParticleSystem:
    def __init__(self) -> None:
        self.particles: list[Particle] = []

    def clear(self) -> None:
        self.particles.clear()

    def spawn_burst(
        self,
        x: float,
        y: float,
        sprite: Any,
        count: int = 8,
        speed: float = 1.6,
        ttl: float = 0.35,
        scale: float = 0.12,
    ) -> None:
        for _ in range(count):
            angle = random.uniform(0.0, math.tau)
            velocity = random.uniform(speed * 0.35, speed)

            particle_ttl = random.uniform(ttl * 0.6, ttl * 1.3)
            particle_scale = random.uniform(scale * 0.7, scale * 1.3)

            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * velocity,
                    vy=math.sin(angle) * velocity,
                    ttl=particle_ttl,
                    sprite=sprite,
                    scale=particle_scale,
                )
            )

    def update(self, dt: float) -> None:
        for particle in self.particles:
            particle.update(dt)

        self.particles = [
            particle for particle in self.particles if not particle.is_dead
        ]
