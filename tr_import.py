"""Import der Transaktions-CSV von Trade Republic (Export „Transaktionen“).

Übernommen werden Käufe und Verkäufe (auch Sparplan-Ausführungen). Einzahlungen, Zinsen,
Dividenden und technische Umbuchungen („MIGRATION“) werden übersprungen. Die
Wertpapiere stehen in der Datei als ISIN; der passende Yahoo-Ticker wird über die
Yahoo-Suche ermittelt und kann im Import-Dialog korrigiert werden.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pfade

ZUORDNUNG = pfade.DATEN / "isin_ticker.json"  # gemerkte ISIN → Ticker (auch Korrekturen)

# Börsen-Kürzel bei Yahoo: US-Hauptbörsen und Xetra
US_BOERSEN = {"NMS", "NYQ", "NGM", "NCM", "ASE", "PCX", "BTS", "NAS", "NYS"}


def _zahl(text: str) -> float:
    try:
        return float(text) if text not in ("", None) else 0.0
    except ValueError:
        return float(text.replace(".", "").replace(",", "."))


def lesen(datei: Path) -> list[dict]:
    """Käufe/Verkäufe aus der CSV. Jede Buchung behält die Transaktions-ID von Trade
    Republic, damit ein erneuter Import nichts doppelt einträgt."""
    with open(datei, newline="", encoding="utf-8-sig") as f:
        probe = f.read(4096)
        f.seek(0)
        trenner = ";" if probe.count(";") > probe.count(",") else ","
        zeilen = list(csv.DictReader(f, delimiter=trenner))
    if not zeilen or "transaction_id" not in zeilen[0] or "shares" not in zeilen[0]:
        raise ValueError("Das sieht nicht wie ein Transaktions-Export von Trade Republic aus "
                         "(Spalten wie „shares“, „price“, „transaction_id“ fehlen).")
    out = []
    for z in zeilen:
        if (z.get("category") or "").upper() != "TRADING":
            continue  # Einzahlungen, Dividenden, Zinsen, Umbuchungen
        stueck = _zahl(z.get("shares", ""))
        kurs = abs(_zahl(z.get("price", "")))
        if not stueck or not kurs:
            continue
        typ = (z.get("type") or "").upper()
        verkauf = stueck < 0 or "SELL" in typ
        if (z.get("currency") or "EUR").upper() != "EUR":
            continue  # Vyntro rechnet das Depot in Euro
        out.append({
            "tr_id": z.get("transaction_id") or "",
            "datum": (z.get("date") or z.get("datetime", ""))[:10],
            "art": "verkauf" if verkauf else "kauf",
            "name": z.get("name") or "",
            "isin": z.get("symbol") or "",
            "krypto": (z.get("asset_class") or "").upper() == "CRYPTO",
            "stueck": abs(stueck),
            "kurs_eur": kurs,
            # Gebühr und einbehaltene Steuer mindern bzw. erhöhen den Betrag
            "gebuehr_eur": abs(_zahl(z.get("fee", ""))) + abs(_zahl(z.get("tax", ""))),
        })
    return sorted(out, key=lambda b: b["datum"])


def gemerkte_zuordnung() -> dict[str, str]:
    try:
        d = json.loads(ZUORDNUNG.read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def zuordnung_merken(neu: dict[str, str]) -> None:
    d = gemerkte_zuordnung()
    d.update({k: v for k, v in neu.items() if k and v})
    ZUORDNUNG.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def ticker_finden(isin: str, name: str, krypto: bool) -> str | None:
    """Yahoo-Ticker zu einer ISIN (bzw. einem Krypto-Kürzel wie BTC)."""
    if krypto:
        return f"{isin.upper()}-USD" if isin else None
    gemerkt = gemerkte_zuordnung().get(isin)
    if gemerkt:
        return gemerkt
    import yfinance as yf

    def suche(begriff: str) -> list[dict]:
        try:
            q = yf.Search(begriff, max_results=15, news_count=0).quotes or []
        except Exception:  # noqa: BLE001
            return []
        return [x for x in q if x.get("symbol") and x.get("quoteType") in
                ("EQUITY", "ETF", "MUTUALFUND", None)]

    treffer = suche(isin) if isin else []
    if isin.startswith("US"):  # US-Aktie: Hauptlisting ohne Börsen-Endung
        for q in treffer + (suche(name) if name else []):
            if q.get("exchange") in US_BOERSEN and "." not in q["symbol"]:
                return q["symbol"]
    # sonst bevorzugt Xetra (Kurs in Euro) – notfalls über den Namen suchen
    for q in treffer:
        if q["symbol"].endswith(".DE"):
            return q["symbol"]
    if name:
        namen_treffer = suche(name)
        lang = (treffer[0].get("longname") or treffer[0].get("shortname") or "") if treffer else ""
        for begriff in ([lang] if lang else []):
            namen_treffer += suche(begriff)
        for q in namen_treffer:
            if q["symbol"].endswith(".DE"):
                return q["symbol"]
        treffer = treffer or namen_treffer
    return treffer[0]["symbol"] if treffer else None
