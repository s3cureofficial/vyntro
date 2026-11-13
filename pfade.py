"""Wo Vyntro seine Daten ablegt und seine Bilder findet – auf macOS und Windows.

- Eigene Daten (Listen, Depot, Alarme, Notizen, Zwischenspeicher):
  * Windows: %APPDATA%\\Vyntro
  * macOS (installiert über install.sh): neben app.py in ~/Library/Application Support/…
  * als gepacktes Programm (PyInstaller) auf macOS: ~/Library/Application Support/Vyntro
- Mitgelieferte Dateien (Logo, Icon): neben dem Programm bzw. im PyInstaller-Paket.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

WINDOWS = sys.platform.startswith("win")
MAC = sys.platform == "darwin"
GEPACKT = bool(getattr(sys, "frozen", False))  # als .exe / .app gebaut

# Anzeige von Tastenkürzeln: ⌘K auf dem Mac, Strg+K unter Windows
TASTE = "⌘" if MAC else "Strg+"
SCHRIFT = "SF Pro Text" if MAC else "Segoe UI"
BEENDEN_TIPP = ("Ganz beenden: ⌘Q oder über das Symbol in der Menüleiste." if MAC else
                "Ganz beenden: Rechtsklick auf das Vyntro-Symbol unten rechts in der "
                "Taskleiste → Beenden.")


def _datenordner() -> Path:
    if WINDOWS:
        basis = Path(os.environ.get("APPDATA") or Path.home()) / "Vyntro"
    elif GEPACKT:
        basis = Path.home() / "Library" / "Application Support" / "Vyntro"
    else:
        basis = Path(__file__).resolve().parent
    basis.mkdir(parents=True, exist_ok=True)
    return basis


DATEN = _datenordner()


def ressource(name: str) -> Path:
    """Mitgelieferte Datei finden (im PyInstaller-Paket, neben app.py oder in branding/)."""
    basis = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    for p in (basis / name, basis / "branding" / name):
        if p.exists():
            return p
    return basis / name
