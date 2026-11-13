"""Begründung in Klartext, warum die Regel KAUFEN, HALTEN oder VERKAUFEN zeigt.

Alles hier beschreibt nur, was die Indikatoren und die Kurshistorie sagen –
keine Anlageberatung.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

import signale as s

HORIZONT = 20  # Handelstage, nach denen die Trefferquote früherer Signale gemessen wird


@dataclass
class Punkt:
    text: str
    richtung: int  # +1 spricht für steigende Kurse, -1 für fallende, 0 neutral


@dataclass
class Begruendung:
    signal: str
    score: int
    kurz: str                      # ein Satz Zusammenfassung
    gruende: list[Punkt]           # was das Signal trägt
    dagegen: list[Punkt]           # was dagegen spricht
    kontext: list[Punkt] = field(default_factory=list)  # Kursentwicklung, nicht im Score
    trefferquote: str = ""
    wechsel: str = ""


def _zahl(x: float, n: int = 1) -> str:
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _proz(x: float) -> str:
    return ("+" if x > 0 else "−" if x < 0 else "±") + _zahl(abs(x) * 100) + " %"


def _seit(df: pd.DataFrame, spalte: str) -> str:
    """Datum, an dem die Spalte zuletzt ihren aktuellen Wert angenommen hat."""
    wechsel = df.index[df[spalte].diff().fillna(0) != 0]
    return f"{wechsel[-1]:%d.%m.%Y}" if len(wechsel) else f"vor {df.index[0]:%d.%m.%Y}"


def _kurs_vor(df: pd.DataFrame, monate: int) -> float | None:
    ziel = df.index[-1] - pd.DateOffset(months=monate)
    vorher = df[df.index <= ziel]
    return float(vorher["kurs"].iloc[-1]) if len(vorher) else None


def indikator_punkte(df: pd.DataFrame) -> list[Punkt]:
    z = df.iloc[-1]
    punkte = []

    abstand = z["sma_kurz"] / z["sma_lang"] - 1
    if z["s_trend"] > 0:
        punkte.append(Punkt(
            f"Aufwärtstrend: Der 50-Tage-Durchschnitt liegt {_zahl(abs(abstand) * 100)} % über "
            f"dem 200-Tage-Durchschnitt (seit {_seit(df, 's_trend')}, „Golden Cross“).", 1))
    else:
        punkte.append(Punkt(
            f"Abwärtstrend: Der 50-Tage-Durchschnitt liegt {_zahl(abs(abstand) * 100)} % unter "
            f"dem 200-Tage-Durchschnitt (seit {_seit(df, 's_trend')}, „Death Cross“). "
            f"Mittelfristig fällt der Kurs also eher, als dass er steigt.", -1))

    rsi = z["rsi"]
    if z["s_rsi"] < 0:
        punkte.append(Punkt(
            f"Überkauft: Der RSI steht bei {_zahl(rsi, 0)} (über {s.RSI_OBEN}). Der Kurs ist "
            f"in kurzer Zeit stark gestiegen – danach kommt es häufig zu Rücksetzern.", -1))
    elif z["s_rsi"] > 0:
        punkte.append(Punkt(
            f"Überverkauft: Der RSI steht bei {_zahl(rsi, 0)} (unter {s.RSI_UNTEN}). Der Kurs "
            f"ist in kurzer Zeit stark gefallen – danach folgt oft eine Gegenbewegung.", 1))
    else:
        punkte.append(Punkt(
            f"RSI neutral bei {_zahl(rsi, 0)}: weder überkauft (über {s.RSI_OBEN}) noch "
            f"überverkauft (unter {s.RSI_UNTEN}).", 0))

    if z["s_macd"] > 0:
        punkte.append(Punkt(
            f"Schwung nimmt zu: Der MACD liegt über seiner Signallinie "
            f"(seit {_seit(df, 's_macd')}).", 1))
    else:
        punkte.append(Punkt(
            f"Schwung lässt nach: Der MACD liegt unter seiner Signallinie "
            f"(seit {_seit(df, 's_macd')}). Die Kursbewegung verliert an Kraft "
            f"bzw. die Abwärtsbewegung beschleunigt sich.", -1))
    return punkte


def kontext_punkte(df: pd.DataFrame) -> list[Punkt]:
    z = df.iloc[-1]
    k = float(z["kurs"])
    punkte = []
    zu200 = k / z["sma_lang"] - 1
    punkte.append(Punkt(
        f"Der Kurs liegt {_zahl(abs(zu200) * 100)} % {'über' if zu200 >= 0 else 'unter'} "
        f"dem 200-Tage-Durchschnitt.", 1 if zu200 >= 0 else -1))
    teile = []
    for monate, name in ((1, "1 Monat"), (3, "3 Monaten"), (12, "12 Monaten")):
        vorher = _kurs_vor(df, monate)
        if vorher:
            teile.append(f"{_proz(k / vorher - 1)} in {name}")
    if teile:
        m1 = _kurs_vor(df, 1)
        punkte.append(Punkt("Entwicklung: " + ", ".join(teile) + ".",
                            0 if not m1 else (1 if k >= m1 else -1)))
    jahr = df[df.index >= df.index[-1] - pd.DateOffset(months=12)]["kurs"]
    vom_hoch = k / jahr.max() - 1
    if vom_hoch < -0.005:
        punkte.append(Punkt(
            f"{_zahl(abs(vom_hoch) * 100)} % unter dem 52-Wochen-Hoch "
            f"({_zahl(jahr.max(), 2)} am {jahr.idxmax():%d.%m.%Y}).", -1 if vom_hoch < -0.2 else 0))
    else:
        punkte.append(Punkt("Der Kurs notiert nahe seinem 52-Wochen-Hoch.", 1))
    return punkte


def trefferquote(df: pd.DataFrame, signal: str, ticker: str) -> str:
    """Wie entwickelte sich der Kurs nach früheren Signalen derselben Art?"""
    if signal == "HALTEN":
        return ""
    sig = df["score"].map(lambda x: s.empfehlung(int(x)))
    beginn = (sig == signal) & (sig.shift(1) != signal)
    renditen = []
    pos = {d: i for i, d in enumerate(df.index)}
    for d in df.index[beginn]:
        i = pos[d]
        if i + HORIZONT < len(df) and i > 0:
            renditen.append(df["kurs"].iloc[i + HORIZONT] / df["kurs"].iloc[i] - 1)
    if not renditen:
        return (f"Für {ticker} gab es im Zeitraum noch kein früheres {signal}-Signal, "
                "an dem man die Regel messen könnte.")
    n = len(renditen)
    if signal == "VERKAUFEN":
        treffer = sum(r < 0 for r in renditen)
        richtig = "niedriger"
    else:
        treffer = sum(r > 0 for r in renditen)
        richtig = "höher"
    schnitt = sum(renditen) / n
    text = (f"Nach den bisherigen {n} {signal}-Signalen bei {ticker} lag der Kurs "
            f"{HORIZONT} Handelstage später in {treffer} von {n} Fällen {richtig} "
            f"(im Schnitt {_proz(schnitt)}).")
    if n < 5:
        text += " Das sind wenige Fälle – die Quote ist kaum aussagekräftig."
    elif treffer / n < 0.5:
        text += " Bei diesem Wert lag die Regel also öfter falsch als richtig."
    return text


def _wechsel(df: pd.DataFrame, signal: str) -> str:
    z = df.iloc[-1]
    score = int(z["score"])
    # mögliche Änderungen: (Beschreibung, Score-Änderung)
    hoch, runter = [], []
    if z["s_trend"] < 0:
        hoch.append(("der 50-Tage-Durchschnitt über den 200-Tage-Durchschnitt steigt", 2))
    else:
        runter.append(("der 50-Tage-Durchschnitt unter den 200-Tage-Durchschnitt fällt", -2))
    if z["s_macd"] < 0:
        hoch.append(("der MACD seine Signallinie nach oben kreuzt", 2))
    else:
        runter.append(("der MACD seine Signallinie nach unten kreuzt", -2))
    if z["s_rsi"] < 0:
        hoch.append((f"der RSI unter {s.RSI_OBEN} fällt", 1))
    elif z["s_rsi"] > 0:
        runter.append((f"der RSI über {s.RSI_UNTEN} steigt", -1))
    else:
        hoch.append((f"der RSI unter {s.RSI_UNTEN} fällt (überverkauft)", 1))
        runter.append((f"der RSI über {s.RSI_OBEN} steigt (überkauft)", -1))

    def satz(optionen, ziel, bedingung):
        allein = [t for t, d in optionen if bedingung(score + d)]
        if allein:
            return f"Das Signal wechselt zu {ziel}, sobald " + " oder ".join(allein) + "."
        if optionen:
            return (f"Für {ziel} müsste sich mehreres ändern: "
                    + ", ".join(t for t, _ in optionen) + ".")
        return ""

    if signal == "VERKAUFEN":
        return satz(hoch, "HALTEN", lambda x: x > s.VERKAUF_AB)
    if signal == "KAUFEN":
        return satz(runter, "HALTEN", lambda x: x < s.KAUF_AB)
    teile = [satz(hoch, "KAUFEN", lambda x: x >= s.KAUF_AB),
             satz(runter, "VERKAUFEN", lambda x: x <= s.VERKAUF_AB)]
    return " ".join(t for t in teile if t)


def erklaere(df: pd.DataFrame, ticker: str) -> Begruendung:
    z = df.iloc[-1]
    score = int(z["score"])
    signal = s.empfehlung(score)
    punkte = indikator_punkte(df)
    runter = [p for p in punkte if p.richtung < 0]
    hoch = [p for p in punkte if p.richtung > 0]

    if signal == "VERKAUFEN":
        gruende, dagegen = runter, hoch + [p for p in punkte if p.richtung == 0]
        kurz = (f"Die Regel zeigt VERKAUFEN, weil {len(runter)} von 3 Indikatoren nach unten "
                f"zeigen (Score {score:+d}). Ein Verkaufssignal heißt: Nach diesen Regeln "
                f"überwiegt gerade das Risiko weiter fallender Kurse.")
    elif signal == "KAUFEN":
        gruende, dagegen = hoch, runter + [p for p in punkte if p.richtung == 0]
        kurz = (f"Die Regel zeigt KAUFEN, weil {len(hoch)} von 3 Indikatoren nach oben zeigen "
                f"(Score {score:+d}).")
    else:
        gruende, dagegen = hoch, runter
        kurz = (f"Die Regel zeigt HALTEN (Score {score:+d}): Die Indikatoren sind sich nicht "
                f"einig – {len(hoch)} zeigen nach oben, {len(runter)} nach unten.")

    return Begruendung(
        signal=signal, score=score, kurz=kurz, gruende=gruende, dagegen=dagegen,
        kontext=kontext_punkte(df), trefferquote=trefferquote(df, signal, ticker),
        wechsel=_wechsel(df, signal),
    )
