from __future__ import annotations

import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    """
    Permite ejecutar directamente con:

        python src/mi_doom/main.py

    sin necesidad de instalar el paquete.
    """
    src_dir = Path(__file__).resolve().parents[1]
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


def main() -> None:
    _ensure_src_on_path()

    from mi_doom.game import Game

    Game().run()


if __name__ == "__main__":
    main()