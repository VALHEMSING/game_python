from __future__ import annotations

import sys
from pathlib import Path

# Detectar dinámicamente la ubicación del paquete mi_doom
script_path = Path(__file__).resolve()
search_dir = script_path.parent

while search_dir != search_dir.parent:
    if (search_dir / "mi_doom").is_dir() and (search_dir / "mi_doom" / "__init__.py").exists():
        sys.path.insert(0, str(search_dir))
        break
    if (search_dir / "src" / "mi_doom").is_dir() and (search_dir / "src" / "mi_doom" / "__init__.py").exists():
        sys.path.insert(0, str(search_dir / "src"))
        break
    search_dir = search_dir.parent

from mi_doom.audio import generate_all_audio


def main() -> None:
    generate_all_audio(force=True)
    print("Audio procedural generado correctamente en assets/sounds y assets/music")


if __name__ == "__main__":
    main()
