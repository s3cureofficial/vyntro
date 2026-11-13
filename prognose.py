"""Prognosen: Prognose-Linie (fortgeschriebener 12-Monats-Trend), statistische Kursspannen, Analysten-Kursziele und was nach früheren
Signalen passiert ist.

Wichtig: Nichts davon sagt die Richtung des Kurses sicher voraus. Die Spannen
beschreiben nur, wie weit sich der Kurs bei gleichbleibender Schwankung
typischerweise bewegt. Keine Anlageberatung.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

import signale as s

# Standardnormal-Quantile für 10 %, 25 %, 75 %, 90 %
Z10, Z25 = -1.2816, -0.6745
HORIZONTE = [(1, "1 Monat"), (3, "3 Monate"), (6, "6 Monate"), (12, "12 Monate")]
TREND_DAEMPFUNG = 0.5  # nur der halbe Trend wird fortgeschrieben – Trends lassen meist nach
TREND_GRENZE = 0.25    # und höchstens ±25 % pro Jahr (log)
SIGNAL_HORIZONTE = [(20, "ca. 1 Monat"), (60, "ca. 3 Monate")]
EMPFEHLUNG = {"strong_buy": "Stark kaufen", "buy": "Kaufen", "hold": "Halten",
              "underperform": "Untergewichten", "sell": "Verkaufen", "none": ""}


@dataclass
class Spanne:
    name: str
    monate: int
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float


@dataclass
class SignalVerlauf:
    name: str
    tage: int
    n: int
    anteil_hoch: float
    median: float
    alle_anteil_hoch: float
    alle_median: float


@dataclass
class Prognose:
    kurs: float
    sigma_tag: float      # Standardabweichung der täglichen Log-Renditen (12 Monate)
    tage_pro_jahr: float  # Handelstage pro Jahr (Aktien ~252, Krypto 365)
    spannen: list[Spanne]
    signal: str
    verlauf: list[SignalVerlauf]
    analysten: dict | None
    trend_jahr: float = 0.0   # fortgeschriebener Trend (Log-Rendite pro Jahr, begrenzt)
    trend_roh: float = 0.0    # gemessener Trend der letzten 12 Monate (unbegrenzt)

    @property
    def vola_jahr(self) -> float:
        return self.sigma_tag * math.sqrt(self.tage_pro_jahr)

    def band(self, kalendertage: float, z: float) -> float:
        """Kurs nach kalendertage für das Normal-Quantil z, um die Trendlinie herum.
        z = 0 ist die Prognose-Linie selbst."""
        n = self.tage_pro_jahr * kalendertage / 365
        return self.kurs * math.exp(self.trend_jahr * kalendertage / 365
                                    + z * self.sigma_tag * math.sqrt(max(n, 0)))

    def linie(self, kalendertage: float) -> float:
        return self.band(kalendertage, 0.0)


def _spannen(pr: "Prognose") -> list[Spanne]:
    out = []
    for monate, name in HORIZONTE:
        t = monate * 365 / 12
        out.append(Spanne(name, monate, pr.band(t, Z10), pr.band(t, Z25), pr.linie(t),
                          pr.band(t, -Z25), pr.band(t, -Z10)))
    return out


def trend(kurse: pd.Series) -> float:
    """Steigung einer Geraden durch die logarithmierten Kurse (pro Jahr)."""
    tage = (kurse.index - kurse.index[0]).days.to_numpy(dtype=float)
    y = kurse.map(math.log).to_numpy()
    if len(tage) < 20 or tage[-1] <= 0:
        return 0.0
    mt, my = tage.mean(), y.mean()
    steigung = ((tage - mt) * (y - my)).sum() / ((tage - mt) ** 2).sum()
    return float(steigung * 365)


def _verlauf(df: pd.DataFrame, signal: str) -> list[SignalVerlauf]:
    sig = df["score"].map(lambda x: s.empfehlung(int(x)))
    out = []
    for tage, name in SIGNAL_HORIZONTE:
        zukunft = df["kurs"].shift(-tage) / df["kurs"] - 1
        gueltig = zukunft.notna()
        auswahl = zukunft[gueltig & (sig == signal)]
        alle = zukunft[gueltig]
        if len(auswahl) < 10 or len(alle) < 10:
            continue
        out.append(SignalVerlauf(
            name, tage, len(auswahl), float((auswahl > 0).mean()), float(auswahl.median()),
            float((alle > 0).mean()), float(alle.median())))
    return out


def analysten(info: dict) -> dict | None:
    ziel = info.get("targetMeanPrice")
    if not ziel:
        return None
    return {
        "mittel": float(ziel),
        "median": info.get("targetMedianPrice"),
        "tief": info.get("targetLowPrice"),
        "hoch": info.get("targetHighPrice"),
        "anzahl": info.get("numberOfAnalystOpinions") or 0,
        "konsens": EMPFEHLUNG.get(info.get("recommendationKey") or "none", ""),
    }


def erstelle(df: pd.DataFrame, info: dict | None = None) -> Prognose:
    kurs = float(df["kurs"].iloc[-1])
    jahr = df[df.index >= df.index[-1] - pd.DateOffset(months=12)]["kurs"]
    log = (jahr / jahr.shift(1)).dropna().map(math.log)
    sigma = float(log.std())
    tage_pro_jahr = float(len(jahr)) * 365 / max((jahr.index[-1] - jahr.index[0]).days, 1)
    signal = s.empfehlung(int(df["score"].iloc[-1]))
    roh = trend(jahr)
    pr = Prognose(
        kurs=kurs, sigma_tag=sigma, tage_pro_jahr=tage_pro_jahr, spannen=[], signal=signal,
        verlauf=_verlauf(df, signal), analysten=analysten(info or {}),
        trend_jahr=max(-TREND_GRENZE, min(TREND_GRENZE, roh * TREND_DAEMPFUNG)), trend_roh=roh,
    )
    pr.spannen = _spannen(pr)
    return pr
