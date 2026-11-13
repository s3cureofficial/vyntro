#!/usr/bin/env python3
"""Trading-Signale: regelbasierte Kauf-/Verkaufssignale für Aktien, ETFs und Krypto.

Wendet drei klassische technische Indikatoren auf Tageskurse an
(Trend über gleitende Durchschnitte, RSI, MACD), fasst sie zu einem
Score zusammen und prüft die Regeln per Backtest gegen "einfach halten".

Keine Anlageberatung. Das Skript handelt nicht, es zeigt nur Signale an.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

warnings.filterwarnings("ignore")  # urllib3/LibreSSL-Hinweise auf macOS ausblenden

import pandas as pd

import pfade
import yfinance as yf
from tabulate import tabulate

WATCHLIST = pfade.ressource("watchlist.txt")

# Regelparameter
SMA_KURZ, SMA_LANG = 50, 200
RSI_TAGE, RSI_UNTEN, RSI_OBEN = 14, 30, 70
MACD_SCHNELL, MACD_LANGSAM, MACD_SIGNAL = 12, 26, 9
KAUF_AB, VERKAUF_AB = 2, -2  # Score-Schwellen (Score reicht von -3 bis +3)
GEBUEHR = 0.001  # 0,1 % pro Kauf bzw. Verkauf im Backtest


# ---------------------------------------------------------------- Daten


def lade_kurse(ticker: str, jahre: int) -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=f"{jahre}y", interval="1d", auto_adjust=True)
    if df.empty:
        raise ValueError(f"keine Kursdaten für {ticker} gefunden")
    df.index = df.index.tz_localize(None)
    return df[["Close"]].rename(columns={"Close": "kurs"}).dropna()


# ---------------------------------------------------------- Indikatoren


def rsi(kurs: pd.Series, tage: int) -> pd.Series:
    diff = kurs.diff()
    gewinn = diff.clip(lower=0).ewm(alpha=1 / tage, adjust=False, min_periods=tage).mean()
    verlust = (-diff.clip(upper=0)).ewm(alpha=1 / tage, adjust=False, min_periods=tage).mean()
    return 100 - 100 / (1 + gewinn / verlust)


def berechne_indikatoren(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    k = df["kurs"]
    df["sma_kurz"] = k.rolling(SMA_KURZ).mean()
    df["sma_lang"] = k.rolling(SMA_LANG).mean()
    df["rsi"] = rsi(k, RSI_TAGE)
    ema_s = k.ewm(span=MACD_SCHNELL, adjust=False).mean()
    ema_l = k.ewm(span=MACD_LANGSAM, adjust=False).mean()
    df["macd"] = ema_s - ema_l
    df["macd_signal"] = df["macd"].ewm(span=MACD_SIGNAL, adjust=False).mean()

    # Teilsignale: +1 = bullisch, -1 = bärisch, 0 = neutral
    df["s_trend"] = (df["sma_kurz"] > df["sma_lang"]).astype(int) * 2 - 1
    df["s_rsi"] = 0
    df.loc[df["rsi"] < RSI_UNTEN, "s_rsi"] = 1
    df.loc[df["rsi"] > RSI_OBEN, "s_rsi"] = -1
    df["s_macd"] = (df["macd"] > df["macd_signal"]).astype(int) * 2 - 1
    df["score"] = df["s_trend"] + df["s_rsi"] + df["s_macd"]

    # erst ab genug Historie für den langen Durchschnitt aussagekräftig
    return df.dropna(subset=["sma_lang", "rsi"])


def empfehlung(score: int) -> str:
    if score >= KAUF_AB:
        return "KAUFEN"
    if score <= VERKAUF_AB:
        return "VERKAUFEN"
    return "HALTEN"


def letzte_ereignisse(df: pd.DataFrame, tage: int = 10) -> list[str]:
    """Frische Kreuzungen der letzten Handelstage."""
    ereignisse = []
    fenster = df.tail(tage + 1)
    trend = fenster["s_trend"].diff()
    macd = fenster["s_macd"].diff()
    for datum, d in trend[trend != 0].dropna().items():
        art = "Golden Cross" if d > 0 else "Death Cross"
        ereignisse.append(f"{art} {datum:%d.%m.}")
    for datum, d in macd[macd != 0].dropna().items():
        art = "MACD ↑" if d > 0 else "MACD ↓"
        ereignisse.append(f"{art} {datum:%d.%m.}")
    return ereignisse


# -------------------------------------------------------------- Backtest


@dataclass
class Backtest:
    rendite_strategie: float
    rendite_halten: float
    max_dd_strategie: float
    max_dd_halten: float
    trades: int
    investiert_anteil: float
    trades_liste: list


def max_drawdown(wert: pd.Series) -> float:
    return float((wert / wert.cummax() - 1).min())


def backteste(df: pd.DataFrame) -> Backtest:
    # Position: einsteigen bei Score >= KAUF_AB, aussteigen bei Score <= VERKAUF_AB,
    # dazwischen bisherige Position halten.
    roh = pd.Series(pd.NA, index=df.index, dtype="Float64")
    roh[df["score"] >= KAUF_AB] = 1.0
    roh[df["score"] <= VERKAUF_AB] = 0.0
    position = roh.ffill().fillna(0.0).astype(float)
    # Signal am Tagesende -> gehandelt wird erst am nächsten Tag (kein Blick in die Zukunft)
    position = position.shift(1).fillna(0.0)

    tagesrendite = df["kurs"].pct_change().fillna(0.0)
    wechsel = position.diff().abs().fillna(position.iloc[0])
    strategie = (1 + position * tagesrendite - wechsel * GEBUEHR).cumprod()
    halten = (1 + tagesrendite).cumprod()

    trades = []
    for datum, w in position.diff().items():
        if w > 0:
            trades.append((datum, "Kauf", df["kurs"].loc[datum]))
        elif w < 0:
            trades.append((datum, "Verkauf", df["kurs"].loc[datum]))

    return Backtest(
        rendite_strategie=float(strategie.iloc[-1] - 1),
        rendite_halten=float(halten.iloc[-1] - 1),
        max_dd_strategie=max_drawdown(strategie),
        max_dd_halten=max_drawdown(halten),
        trades=int((position.diff() > 0).sum()),
        investiert_anteil=float(position.mean()),
        trades_liste=trades,
    )


# ------------------------------------------------------------------- CLI


def lies_watchlist() -> list[str]:
    if not WATCHLIST.exists():
        return []
    zeilen = (z.split("#")[0].strip() for z in WATCHLIST.read_text().splitlines())
    return [z.upper() for z in zeilen if z]


def pct(x: float) -> str:
    return f"{x * 100:+.1f} %"


def zeige_uebersicht(tickers: list[str], jahre: int) -> None:
    zeilen = []
    for t in tickers:
        try:
            df = berechne_indikatoren(lade_kurse(t, jahre))
            bt = backteste(df)
        except Exception as e:  # noqa: BLE001
            zeilen.append([t, "-", "-", "-", "-", "-", f"Fehler: {e}", "-", "-"])
            continue
        z = df.iloc[-1]
        zeilen.append([
            t,
            f"{z['kurs']:.2f}",
            "↑" if z["s_trend"] > 0 else "↓",
            f"{z['rsi']:.0f}",
            "↑" if z["s_macd"] > 0 else "↓",
            f"{int(z['score']):+d}",
            empfehlung(int(z["score"])),
            f"{pct(bt.rendite_strategie)} / {pct(bt.rendite_halten)}",
            ", ".join(letzte_ereignisse(df)) or "-",
        ])
    print(tabulate(
        zeilen,
        headers=["Ticker", "Kurs", "Trend", "RSI", "MACD", "Score", "Signal",
                 f"Backtest {jahre}J (Regel / Halten)", "Neu (10 Tage)"],
        tablefmt="simple",
    ))
    print(f"\nStand: letzte Tagesschlusskurse. Score = Trend + RSI + MACD (-3 … +3); "
          f"KAUFEN ab {KAUF_AB:+d}, VERKAUFEN ab {VERKAUF_AB:+d}.")
    print("Keine Anlageberatung – vergangene Ergebnisse sagen nichts über die Zukunft. "
          "Details: signale.py --detail TICKER")


def zeige_detail(ticker: str, jahre: int) -> None:
    df = berechne_indikatoren(lade_kurse(ticker, jahre))
    bt = backteste(df)
    z = df.iloc[-1]

    print(f"\n{ticker} – {df.index[-1]:%d.%m.%Y}, Kurs {z['kurs']:.2f}\n")
    print("Teilsignale:")
    print(f"  Trend  SMA{SMA_KURZ} {z['sma_kurz']:.2f} vs. SMA{SMA_LANG} {z['sma_lang']:.2f}"
          f"  -> {'+1 Aufwärtstrend' if z['s_trend'] > 0 else '-1 Abwärtstrend'}")
    rsi_text = {1: "+1 überverkauft", -1: "-1 überkauft", 0: " 0 neutral"}[int(z["s_rsi"])]
    print(f"  RSI    {z['rsi']:.1f}  -> {rsi_text}")
    print(f"  MACD   {z['macd']:.3f} vs. Signal {z['macd_signal']:.3f}"
          f"  -> {'+1 Schwung nach oben' if z['s_macd'] > 0 else '-1 Schwung nach unten'}")
    print(f"\n  Score {int(z['score']):+d}  =>  {empfehlung(int(z['score']))}\n")

    print("Letzte 10 Handelstage:")
    tab = df.tail(10)[["kurs", "rsi", "score"]].copy()
    tab["signal"] = tab["score"].astype(int).map(empfehlung)
    tab.index = tab.index.strftime("%d.%m.%Y")
    print(tabulate(tab, headers=["Datum", "Kurs", "RSI", "Score", "Signal"],
                   floatfmt=".2f", tablefmt="simple"))

    von = df.index[0]
    print(f"\nBacktest {von:%d.%m.%Y} – {df.index[-1]:%d.%m.%Y} "
          f"(Gebühr {GEBUEHR * 100:.1f} % pro Order, Ausführung am Folgetag):")
    print(tabulate([
        ["Regel", pct(bt.rendite_strategie), pct(bt.max_dd_strategie)],
        ["Einfach halten", pct(bt.rendite_halten), pct(bt.max_dd_halten)],
    ], headers=["", "Rendite", "Max. Verlust zwischendurch"], tablefmt="simple"))
    print(f"{bt.trades} Käufe, {bt.investiert_anteil * 100:.0f} % der Zeit investiert.")
    if bt.trades_liste:
        print("\nLetzte Orders der Regel:")
        for datum, art, kurs in bt.trades_liste[-6:]:
            print(f"  {datum:%d.%m.%Y}  {art:<8} {kurs:.2f}")
    print("\nKeine Anlageberatung – vergangene Ergebnisse sagen nichts über die Zukunft.")


def main() -> int:
    p = argparse.ArgumentParser(
        description="Regelbasierte Kauf-/Verkaufssignale (Trend, RSI, MACD) mit Backtest.")
    p.add_argument("tickers", nargs="*",
                   help="z. B. AAPL SAP.DE BTC-USD (ohne Angabe: watchlist.txt)")
    p.add_argument("--detail", metavar="TICKER", help="ausführliche Analyse für einen Ticker")
    p.add_argument("--jahre", type=int, default=5, help="Historie in Jahren (Standard: 5)")
    a = p.parse_args()

    if a.detail:
        zeige_detail(a.detail.upper(), a.jahre)
        return 0
    tickers = [t.upper() for t in a.tickers] or lies_watchlist()
    if not tickers:
        p.error("keine Ticker angegeben und watchlist.txt ist leer")
    zeige_uebersicht(tickers, a.jahre)
    return 0


if __name__ == "__main__":
    sys.exit(main())
