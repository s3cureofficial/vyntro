"""Startpunkt für das gepackte Programm (Windows-.exe).

Ein Fensterprogramm hat unter Windows keine Konsole: sys.stdout und sys.stderr sind dann
None, und Bibliotheken, die etwas ausgeben wollen, würden abstürzen. Außerdem wird jeder
Absturz mit vollständiger Fehlermeldung in absturz.txt im Datenordner geschrieben.
"""

import os
import sys
import traceback

for _name in ("stdout", "stderr"):
    if getattr(sys, _name) is None:
        setattr(sys, _name, open(os.devnull, "w", encoding="utf-8"))


def _absturz_speichern() -> None:
    text = traceback.format_exc()
    try:
        import pfade
        (pfade.DATEN / "absturz.txt").write_text(text, encoding="utf-8")
    except Exception:  # noqa: BLE001
        basis = os.environ.get("APPDATA") or os.path.expanduser("~")
        os.makedirs(os.path.join(basis, "Vyntro"), exist_ok=True)
        with open(os.path.join(basis, "Vyntro", "absturz.txt"), "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    try:
        import app
        code = app.main()
    except SystemExit:
        raise
    except BaseException:  # noqa: BLE001
        _absturz_speichern()
        if "--selbsttest" in sys.argv:
            os._exit(5)
        raise
    sys.exit(code)
