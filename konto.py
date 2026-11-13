"""Eigenes Depot (eingetragene Käufe) und Kurs-/Signal-Alarme.

Beides wird als JSON neben der App gespeichert. Alle Depot-Beträge sind in Euro, damit
Gewinn/Verlust auch Wechselkursschwankungen enthält (so wie beim Broker).
"""

from __future__ import annotations

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

import pfade

DEPOT = pfade.DATEN / "depot.json"
ALARME = pfade.DATEN / "alarme.json"


def _lesen(datei: Path) -> list[dict]:
    try:
        daten = json.loads(datei.read_text())
        return daten if isinstance(daten, list) else []
    except (OSError, ValueError):
        return []


def _schreiben(datei: Path, daten: list[dict]) -> None:
    tmp = datei.with_suffix(".tmp")
    tmp.write_text(json.dumps(daten, indent=2, ensure_ascii=False))
    tmp.replace(datei)


def neue_id() -> str:
    return uuid.uuid4().hex[:10]


# ------------------------------------------------------------------ Depot

def lade_kaeufe() -> list[dict]:
    return _lesen(DEPOT)


def speichere_kaeufe(kaeufe: list[dict]) -> None:
    _schreiben(DEPOT, kaeufe)


def kauf(ticker: str, stueck: float, kurs_eur: float, gebuehr_eur: float, datum: str,
         art: str = "kauf") -> dict:
    return {"id": neue_id(), "ticker": ticker, "art": art, "stueck": stueck,
            "kurs_eur": kurs_eur, "gebuehr_eur": gebuehr_eur, "datum": datum}


def ist_verkauf(k: dict) -> bool:
    return k.get("art") == "verkauf"


def alle_werte(kaeufe: list[dict]) -> dict[str, dict]:
    """Je Wert: aktuelle Stückzahl, Einstand der noch gehaltenen Stücke (Durchschnittskosten,
    inkl. Kaufgebühren) und realisierter Gewinn/Verlust aus Verkäufen."""
    out: dict[str, dict] = {}
    for k in sorted(kaeufe, key=lambda k: (k["datum"], not ist_verkauf(k))):
        p = out.setdefault(k["ticker"], {"stueck": 0.0, "einstand": 0.0, "realisiert": 0.0,
                                          "kaeufe": []})
        p["kaeufe"].append(k)
        geb = k.get("gebuehr_eur", 0.0)
        if ist_verkauf(k):
            menge = min(k["stueck"], p["stueck"])
            if p["stueck"] <= 0:
                continue
            anteil = p["einstand"] * menge / p["stueck"]
            p["realisiert"] += menge * k["kurs_eur"] - geb - anteil
            p["einstand"] -= anteil
            p["stueck"] -= menge
            if p["stueck"] < 1e-9:
                p["stueck"], p["einstand"] = 0.0, 0.0
        else:
            p["stueck"] += k["stueck"]
            p["einstand"] += k["stueck"] * k["kurs_eur"] + geb
    return out


def realisiert_je_jahr(kaeufe: list[dict]) -> dict[int, float]:
    """Realisierter Gewinn/Verlust (Durchschnittskosten) je Kalenderjahr des Verkaufs."""
    jahre: dict[int, float] = {}
    bestand: dict[str, list[float]] = {}  # Ticker -> [Stück, Einstand]
    for k in sorted(kaeufe, key=lambda k: (k["datum"], not ist_verkauf(k))):
        st, ein = bestand.setdefault(k["ticker"], [0.0, 0.0])
        geb = k.get("gebuehr_eur", 0.0)
        if ist_verkauf(k):
            if st <= 0:
                continue
            menge = min(k["stueck"], st)
            anteil = ein * menge / st
            jahr = int(k["datum"][:4])
            jahre[jahr] = jahre.get(jahr, 0.0) + menge * k["kurs_eur"] - geb - anteil
            bestand[k["ticker"]] = [st - menge, ein - anteil]
        else:
            bestand[k["ticker"]] = [st + k["stueck"], ein + k["stueck"] * k["kurs_eur"] + geb]
    return jahre


STEUERSATZ = 0.26375  # Abgeltungssteuer 25 % + Solidaritätszuschlag, ohne Kirchensteuer


def steuer_schaetzung(gewinn: float, freibetrag: float) -> dict:
    steuerpflichtig = max(0.0, gewinn - freibetrag)
    return {"gewinn": gewinn, "freibetrag_genutzt": min(max(gewinn, 0.0), freibetrag),
            "steuerpflichtig": steuerpflichtig, "steuer": steuerpflichtig * STEUERSATZ}


# ------------------------------------------------------------------ Notizen

NOTIZEN = pfade.DATEN / "notizen.json"


def lade_notizen() -> dict[str, str]:
    try:
        d = json.loads(NOTIZEN.read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def speichere_notizen(notizen: dict[str, str]) -> None:
    tmp = NOTIZEN.with_suffix(".tmp")
    tmp.write_text(json.dumps({k: v for k, v in notizen.items() if v.strip()}, indent=2,
                              ensure_ascii=False))
    tmp.replace(NOTIZEN)


# ------------------------------------------------------------------ Export

def csv_export(datei: Path, kaeufe: list[dict], namen: dict[str, str],
               bewertung: dict[str, dict]) -> None:
    """Käufe/Verkäufe und aktuelle Positionen als CSV (Semikolon, deutsches Zahlenformat –
    öffnet sich so direkt richtig in Excel und Numbers)."""
    import csv

    def z(x, n=2):
        return "" if x is None else f"{x:.{n}f}".replace(".", ",")
    with open(datei, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Buchungen"])
        w.writerow(["Datum", "Art", "Ticker", "Name", "Stück", "Kurs €", "Gebühr €",
                    "Betrag €"])
        for k in sorted(kaeufe, key=lambda k: k["datum"]):
            betrag = k["stueck"] * k["kurs_eur"]
            betrag = betrag - k.get("gebuehr_eur", 0) if ist_verkauf(k) else betrag + k.get(
                "gebuehr_eur", 0)
            w.writerow([k["datum"], "Verkauf" if ist_verkauf(k) else "Kauf", k["ticker"],
                        namen.get(k["ticker"], ""), z(k["stueck"], 6), z(k["kurs_eur"], 4),
                        z(k.get("gebuehr_eur", 0)), z(betrag)])
        w.writerow([])
        w.writerow(["Positionen"])
        w.writerow(["Ticker", "Name", "Stück", "Einstand €", "Wert €", "Gewinn/Verlust €",
                    "Gewinn/Verlust %"])
        for t, p in sorted(positionen(kaeufe).items()):
            b = bewertung.get(t, {})
            pct = b.get("gv_pct")
            w.writerow([t, namen.get(t, ""), z(p["stueck"], 6), z(p["einstand"]),
                        z(b.get("wert")), z(b.get("gv")), z(pct * 100 if pct is not None
                                                            else None)])


def positionen(kaeufe: list[dict]) -> dict[str, dict]:
    """Nur Werte, von denen noch Stücke im Depot liegen."""
    return {t: p for t, p in alle_werte(kaeufe).items() if p["stueck"] > 0}


def realisiert(kaeufe: list[dict]) -> float:
    return sum(p["realisiert"] for p in alle_werte(kaeufe).values())


def bestand_am(kaeufe: list[dict], ticker: str, datum: str) -> float:
    """Stückzahl, die am Ende des Tages `datum` (JJJJ-MM-TT) im Depot lag."""
    menge = 0.0
    for k in kaeufe:
        if k["ticker"] == ticker and k["datum"] <= datum:
            menge += -k["stueck"] if ist_verkauf(k) else k["stueck"]
    return max(menge, 0.0)


def depot_verlauf(kaeufe: list[dict], kurse_eur: dict, vergleich_eur=None):
    """Täglicher Depotwert, eingezahltes Geld (netto) und – falls angegeben – derselbe
    Geldfluss in einem Vergleichswert (z. B. MSCI-World-ETF).

    kurse_eur: Ticker -> pandas.Series mit Tagesschlusskursen in Euro.
    Rückgabe: DataFrame mit Spalten wert, eingezahlt (und vergleich) oder None.
    """
    import pandas as pd
    if not kaeufe:
        return None
    start = pd.Timestamp(min(k["datum"] for k in kaeufe))
    reihen = {t: s[s.index >= start - pd.Timedelta(days=10)] for t, s in kurse_eur.items()
              if s is not None and len(s)}
    if not reihen:
        return None
    tage = sorted(set().union(*[set(s.index) for s in reihen.values()]))
    tage = pd.DatetimeIndex([d for d in tage if d >= start] or [start])
    wert = pd.Series(0.0, index=tage)
    for t, s in reihen.items():
        kurs = s.reindex(tage, method="ffill")
        menge = pd.Series([bestand_am(kaeufe, t, f"{d:%Y-%m-%d}") for d in tage], index=tage)
        wert += (menge * kurs).fillna(0)
    fluss = pd.Series(0.0, index=tage)  # Ein- (+) und Auszahlungen (−) je Tag
    for k in kaeufe:
        d = tage[tage.searchsorted(pd.Timestamp(k["datum"]))] if pd.Timestamp(
            k["datum"]) <= tage[-1] else tage[-1]
        betrag = k["stueck"] * k["kurs_eur"]
        fluss[d] += -(betrag - k.get("gebuehr_eur", 0)) if ist_verkauf(k) else betrag + k.get(
            "gebuehr_eur", 0)
    out = pd.DataFrame({"wert": wert, "eingezahlt": fluss.cumsum()})
    if vergleich_eur is not None and len(vergleich_eur):
        v = vergleich_eur.reindex(tage, method="ffill").bfill()
        anteile = (fluss / v).cumsum()
        out["vergleich"] = anteile * v
    return out


def sparplan(kurse_eur, monatlich: float, jahre: int):
    """Historischer Sparplan: am ersten Handelstag jedes Monats `monatlich` Euro investiert
    (ohne Gebühren). Rückgabe: DataFrame (wert, eingezahlt) oder None, wenn zu wenig
    Historie da ist."""
    import pandas as pd
    if kurse_eur is None or not len(kurse_eur):
        return None
    ende = kurse_eur.index[-1]
    start = ende - pd.DateOffset(years=jahre)
    k = kurse_eur[kurse_eur.index >= start]
    if len(k) < 20 or k.index[0] - start > pd.Timedelta(days=45):
        return None
    monat = k.index.to_period("M")
    erster = ~monat.duplicated()
    stueck = (erster * (monatlich / k)).cumsum()
    eingezahlt = (erster * monatlich).cumsum()
    return pd.DataFrame({"wert": stueck * k, "eingezahlt": eingezahlt.astype(float)})


def bewerte(pos: dict, preis_eur: float | None) -> dict:
    """Wert und Gewinn/Verlust einer Position beim aktuellen Euro-Kurs."""
    if preis_eur is None:
        return {"wert": None, "gv": None, "gv_pct": None}
    wert = pos["stueck"] * preis_eur
    gv = wert - pos["einstand"]
    return {"wert": wert, "gv": gv, "gv_pct": gv / pos["einstand"] if pos["einstand"] else 0.0}


# ----------------------------------------------------------------- Alarme

ARTEN = {"ueber": "Kurs steigt über", "unter": "Kurs fällt unter",
         "tag_plus": "Steigt heute um mehr als", "tag_minus": "Fällt heute um mehr als",
         "rsi_unter": "RSI fällt unter", "rsi_ueber": "RSI steigt über",
         "hoch52": "Neues 52-Wochen-Hoch", "tief52": "Neues 52-Wochen-Tief",
         "signal": "Signal ändert sich"}

LAUNCH_AGENT = Path.home() / "Library" / "LaunchAgents" / "local.vyntro.plist"


ALTER_AGENT = Path.home() / "Library" / "LaunchAgents" / "local.aurum.plist"


RUN_SCHLUESSEL = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _start_befehl() -> str:
    """Befehl, mit dem Windows Vyntro beim Anmelden im Hintergrund startet."""
    import sys
    if pfade.GEPACKT:
        return f'"{sys.executable}" --hintergrund'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    return f'"{pythonw}" "{Path(__file__).with_name("app.py")}" --hintergrund'


def autostart_an() -> bool:
    if pfade.WINDOWS:
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_SCHLUESSEL) as k:
                winreg.QueryValueEx(k, "Vyntro")
            return True
        except OSError:
            return False
    return LAUNCH_AGENT.exists()


def autostart_setzen(an: bool) -> None:
    """Vyntro beim Anmelden im Hintergrund starten (macOS: LaunchAgent,
    Windows: Eintrag unter „Autostart“ in der Registrierung des Benutzers)."""
    if pfade.WINDOWS:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_SCHLUESSEL, 0,
                            winreg.KEY_SET_VALUE) as k:
            if an:
                winreg.SetValueEx(k, "Vyntro", 0, winreg.REG_SZ, _start_befehl())
            else:
                try:
                    winreg.DeleteValue(k, "Vyntro")
                except OSError:
                    pass
        return
    ALTER_AGENT.unlink(missing_ok=True)  # Eintrag unter dem früheren Namen
    if not an:
        LAUNCH_AGENT.unlink(missing_ok=True)
        return
    app = Path.home() / "Applications" / "Vyntro.app"
    LAUNCH_AGENT.parent.mkdir(parents=True, exist_ok=True)
    LAUNCH_AGENT.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>local.vyntro</string>
  <key>ProgramArguments</key>
  <array><string>/usr/bin/open</string><string>-g</string><string>{app}</string>
         <string>--args</string><string>--hintergrund</string></array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
""")


def lade_alarme() -> list[dict]:
    return _lesen(ALARME)


def speichere_alarme(alarme: list[dict]) -> None:
    _schreiben(ALARME, alarme)


def alarm(ticker: str, art: str, wert: float | None = None, signal: str | None = None) -> dict:
    return {"id": neue_id(), "ticker": ticker, "art": art, "wert": wert, "aktiv": True,
            "erstellt": datetime.now().isoformat(timespec="seconds"), "ausgeloest": None,
            "signal": signal}


def kurs_erreicht(a: dict, preis: float) -> bool:
    if not a["aktiv"] or a["art"] not in ("ueber", "unter"):
        return False
    return preis >= a["wert"] if a["art"] == "ueber" else preis <= a["wert"]


MELDER = None  # unter Windows: Funktion der App, die eine Systembenachrichtigung zeigt


def melden(titel: str, text: str) -> None:
    """Mitteilung im macOS-Mitteilungszentrum (mit Ton) bzw. als Windows-Benachrichtigung."""
    if not pfade.MAC:
        if MELDER:
            MELDER(titel, text)
        return

    def esc(x: str) -> str:
        return x.replace("\\", "\\\\").replace('"', '\\"')
    skript = (f'display notification "{esc(text)}" with title "Vyntro" '
              f'subtitle "{esc(titel)}" sound name "Glass"')
    try:
        subprocess.Popen(["osascript", "-e", skript], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
    except OSError:
        pass
