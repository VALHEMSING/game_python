"""
Punto de entrada principal de la aplicación mi-doom.
"""
import sys
from pathlib import Path

# Ajuste dinámico del PYTHONPATH para permitir la ejecución directa del script.
_SRC_DIR = Path(__file__).resolve().parent.parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# pylint: disable=wrong-import-position
from mi_doom.game import Game


def main() -> None:
    """Inicializa y ejecuta el bucle principal del juego."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
