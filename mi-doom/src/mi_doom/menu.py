from __future__ import annotations

from dataclasses import dataclass

import pygame

from mi_doom.input import MenuControls

TITLE_COLOR = (220, 70, 50)
SUBTITLE_COLOR = (220, 220, 220)
NORMAL_COLOR = (200, 200, 200)
SELECTED_COLOR = (255, 220, 80)
DISABLED_COLOR = (110, 110, 110)


@dataclass
class MenuItem:
    label: str
    action: str
    enabled: bool = True


class Menu:
    def __init__(
        self,
        title: str,
        items: list[MenuItem],
        subtitle: str = "",
    ) -> None:
        self.title = title
        self.subtitle = subtitle
        self.items = items
        self.selected = 0

        self._ensure_enabled_selected()

    def reset(self) -> None:
        self.selected = 0
        self._ensure_enabled_selected()

    def handle_controls(self, controls: MenuControls) -> str | None:
        if not self.items:
            return None

        if controls.up:
            self._move(-1)

        if controls.down:
            self._move(1)

        if controls.confirm:
            item = self.items[self.selected]
            if item.enabled:
                return item.action

        return None

    def _ensure_enabled_selected(self) -> None:
        if not self.items:
            return

        if self.items[self.selected].enabled:
            return

        self._move(1)

    def _move(self, direction: int) -> None:
        if not self.items:
            return

        for _ in range(len(self.items)):
            self.selected = (self.selected + direction) % len(self.items)
            if self.items[self.selected].enabled:
                return

    def draw(
        self,
        screen: pygame.Surface,
        title_font: pygame.font.Font,
        item_font: pygame.font.Font,
    ) -> None:
        center_x = screen.get_width() // 2

        if self.title:
            title_surface = title_font.render(self.title, True, TITLE_COLOR)
            title_rect = title_surface.get_rect(center=(center_x, 130))
            screen.blit(title_surface, title_rect)

        if self.subtitle:
            subtitle_surface = item_font.render(self.subtitle, True, SUBTITLE_COLOR)
            subtitle_rect = subtitle_surface.get_rect(center=(center_x, 200))
            screen.blit(subtitle_surface, subtitle_rect)

        y = 280

        for index, item in enumerate(self.items):
            selected = index == self.selected

            if not item.enabled:
                color = DISABLED_COLOR
            elif selected:
                color = SELECTED_COLOR
            else:
                color = NORMAL_COLOR

            label = f"> {item.label}" if selected else item.label
            item_surface = item_font.render(label, True, color)
            item_rect = item_surface.get_rect(center=(center_x, y))
            screen.blit(item_surface, item_rect)

            y += 48