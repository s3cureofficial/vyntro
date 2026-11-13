"""Prüft auf GitHub, ob es eine neuere Vyntro-Version gibt, und installiert sie.

- Windows (installiertes Programm): lädt den Installer aus dem Release und startet ihn
  still; Vyntro beendet sich dafür und startet danach von selbst neu.
- macOS (installiert über install.sh): lädt den Quellcode des Releases und ersetzt die
  Programmdateien in ~/Library/Application Support/Trading-Signale; danach Neustart.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import requests

import pfade
from version import VERSION

REPO = "s3cureofficial/vyntro"
KOPF = {"Accept": "application/vnd.github+json", "User-Agent": "Vyntro-Update"}


def _teile(v: str) -> tuple[int, ...]:
    out = []
    for teil in v.strip().lstrip("vV").split("."):
        ziffern = "".join(c for c in teil if c.isdigit())
        out.append(int(ziffern or 0))
    return tuple(out + [0] * (3 - len(out)))


def ist_neuer(andere: str, aktuell: str = VERSION) -> bool:
    return _teile(andere) > _teile(aktuell)


def art() -> str | None:
    """Wie sich diese Installation aktualisieren lässt – oder None (z. B. Entwicklerversion)."""
    if pfade.WINDOWS and pfade.GEPACKT:
        return "windows"
    if pfade.MAC and not pfade.GEPACKT and "Application Support" in str(pfade.DATEN):
        return "mac"
    return None


def neueste() -> dict | None:
    """Neuestes Release auf GitHub oder None (offline, Limit erreicht …)."""
    r = requests.get(f"https://api.github.com/repos/{REPO}/releases/latest", headers=KOPF,
                     timeout=10)
    if r.status_code != 200:
        return None
    d = r.json()
    installer = next((a["browser_download_url"] for a in d.get("assets", [])
                      if a.get("name", "").lower().endswith(".exe")), None)
    return {"version": (d.get("tag_name") or "").lstrip("vV"), "notizen": d.get("body") or "",
            "seite": d.get("html_url"), "installer": installer,
            "quelle": d.get("zipball_url")}


def herunterladen(url: str, ziel: Path, fortschritt) -> Path:
    """Datei laden; fortschritt(anteil 0..1, text) wird laufend aufgerufen."""
    with requests.get(url, stream=True, timeout=30, headers={"User-Agent": "Vyntro-Update"}) as r:
        r.raise_for_status()
        gesamt = int(r.headers.get("content-length") or 0)
        geladen = 0
        with open(ziel, "wb") as f:
            for stueck in r.iter_content(chunk_size=256 * 1024):
                f.write(stueck)
                geladen += len(stueck)
                mb = geladen / 1_048_576
                if gesamt:
                    fortschritt(geladen / gesamt, f"Lade herunter … {mb:.1f} von "
                                                  f"{gesamt / 1_048_576:.1f} MB")
                else:
                    fortschritt(0.5, f"Lade herunter … {mb:.1f} MB")
    return ziel


MAC_DATEIEN = ("*.py", "watchlist.txt", "requirements.txt", "branding/vyntro-emblem.png",
               "branding/vyntro-icon-1024.png")


def mac_installieren(zip_datei: Path, fortschritt) -> None:
    """Programmdateien aus dem Quellcode-Archiv in den Programmordner kopieren."""
    ziel = pfade.DATEN
    tmp = Path(tempfile.mkdtemp(prefix="vyntro-update-"))
    with zipfile.ZipFile(zip_datei) as z:
        z.extractall(tmp)
    wurzel = next(p for p in tmp.iterdir() if p.is_dir())
    dateien = [p for muster in MAC_DATEIEN for p in wurzel.glob(muster) if p.is_file()]
    if not any(p.name == "app.py" for p in dateien):
        raise RuntimeError("Das Update-Archiv ist unvollständig.")
    alte_req = (ziel / "requirements.txt").read_text() if (ziel / "requirements.txt").exists() \
        else ""
    for i, p in enumerate(dateien):
        shutil.copy2(p, ziel / p.name)
        fortschritt(0.9 + 0.05 * (i + 1) / len(dateien), f"Kopiere {p.name} …")
    neue_req = (ziel / "requirements.txt").read_text()
    pip = ziel / ".venv" / "bin" / "pip"
    if neue_req != alte_req and pip.exists():
        fortschritt(0.96, "Aktualisiere Python-Pakete …")
        subprocess.run([str(pip), "install", "-q", "-r", str(ziel / "requirements.txt")],
                       check=False, timeout=900)
    shutil.rmtree(tmp, ignore_errors=True)


def neu_starten_mac() -> None:
    app = Path.home() / "Applications" / "Vyntro.app"
    subprocess.Popen(["/bin/sh", "-c", f'sleep 1.5; open "{app}"'], start_new_session=True)


def installer_starten(exe: Path) -> None:
    """Windows: Installer still ausführen; er schließt Vyntro und startet es danach neu."""
    subprocess.Popen([str(exe), "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                      "/CLOSEAPPLICATIONS"], close_fds=True,
                     creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))


def temp_ordner() -> Path:
    p = Path(tempfile.gettempdir()) / "vyntro-update"
    p.mkdir(exist_ok=True)
    return p

