"""Logos für Aktien, ETFs und Kryptowährungen – geladen aus öffentlichen Bildquellen
und auf der Festplatte zwischengespeichert (auch "kein Logo vorhanden")."""

from __future__ import annotations

import re
from pathlib import Path

import requests

import pfade

ORDNER = pfade.DATEN / "logos"
KRYPTO = re.compile(r"^([A-Z0-9]+)-(USD|EUR|USDT|USDC|GBP|CHF|JPY|BTC|ETH)$")
KOPF = {"User-Agent": "Mozilla/5.0"}


def _quellen(ticker: str, krypto: bool) -> list[str]:
    m = KRYPTO.match(ticker.upper())
    if krypto or m:
        sym = (m.group(1) if m else ticker.split("-")[0]).lower()
        return [f"https://assets.coincap.io/assets/icons/{sym}@2x.png",
                f"https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/128/color/"
                f"{sym}.png"]
    basis = ticker.split(".")[0]
    urls = [f"https://financialmodelingprep.com/image-stock/{ticker}.png"]
    if basis != ticker:
        urls.append(f"https://financialmodelingprep.com/image-stock/{basis}.png")
    return urls


def _ist_bild(daten: bytes) -> bool:
    return len(daten) > 200 and (daten[:8] == b"\x89PNG\r\n\x1a\n" or daten[:3] == b"\xff\xd8\xff"
                                 or daten[:4] == b"RIFF")


def hole(ticker: str, krypto: bool = False) -> bytes | None:
    """Logo als Bilddaten oder None. Ergebnisse (auch Fehlanzeigen) werden gespeichert."""
    ORDNER.mkdir(exist_ok=True)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", ticker.upper())
    datei, leer = ORDNER / f"{name}.img", ORDNER / f"{name}.none"
    if datei.exists():
        return datei.read_bytes()
    if leer.exists():
        return None
    for url in _quellen(ticker, krypto):
        try:
            r = requests.get(url, timeout=8, headers=KOPF)
        except requests.RequestException:
            return None  # Netzproblem: nicht als "kein Logo" merken
        if r.status_code == 200 and _ist_bild(r.content):
            datei.write_bytes(r.content)
            return r.content
    leer.touch()
    return None
