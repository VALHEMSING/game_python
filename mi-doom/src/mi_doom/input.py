from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class PlayerControls:
    move_forward: float = 0.0
    move_strafe: float = 0.0
    turn_delta: float = 0.0
    mouse_dx: float = 0.0
    run: bool = False
    interact: bool = False
    shoot_pressed: bool = False
    shoot_held: bool = False
    weapon_slot: int | None = None


class InputHandler:
    def __init__(self) -> None:
        self.quit_requested = False
        self.toggle_pause_requested = False
        self.restart_requested = False

        self._interact_pressed = False
        self._shoot_pressed = False
        self._weapon_slot: int | None = None

    def process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.toggle_pause_requested = True

                elif event.key == pygame.K_q:
                    self.quit_requested = True

                elif event.key == pygame.K_r:
                    self.restart_requested = True

                elif event.key == pygame.K_e:
                    self._interact_pressed = True

                elif event.key == pygame.K_SPACE:
                    self._shoot_pressed = True

                elif event.key == pygame.K_1:
                    self._weapon_slot = 1

                elif event.key == pygame.K_2:
                    self._weapon_slot = 2

                elif event.key == pygame.K_3:
                    self._weapon_slot = 3

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._shoot_pressed = True

    def get_controls(self) -> PlayerControls:
        keys = pygame.key.get_pressed()

        move_forward = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_forward += 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_forward -= 1.0

        move_strafe = 0.0
        if keys[pygame.K_d]:
            move_strafe += 1.0
        if keys[pygame.K_a]:
            move_strafe -= 1.0

        turn_delta = 0.0
        if keys[pygame.K_RIGHT]:
            turn_delta += 1.0
        if keys[pygame.K_LEFT]:
            turn_delta -= 1.0

        run = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

        mouse_dx = float(pygame.mouse.get_rel()[0])
        mouse_buttons = pygame.mouse.get_pressed()
        shoot_held = bool(mouse_buttons[0] or keys[pygame.K_SPACE])

        controls = PlayerControls(
            move_forward=move_forward,
            move_strafe=move_strafe,
            turn_delta=turn_delta,
            mouse_dx=mouse_dx,
            run=run,
            interact=self._interact_pressed,
            shoot_pressed=self._shoot_pressed,
            shoot_held=shoot_held,
            weapon_slot=self._weapon_slot,
        )

        # Acciones de un solo frame se consumen aquí.
        self._interact_pressed = False
        self._shoot_pressed = False
        self._weapon_slot = None

        return controls