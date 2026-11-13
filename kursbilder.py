"""Lehrbilder für den Chart-Kurs in der Anleitung.

Jedes Bild ist ein kleiner, künstlich erzeugter Chart, der genau ein Muster zeigt
(Kerze, Trend, Unterstützung, Schulter-Kopf-Schulter …). Die Kurse sind erfunden und
mit festem Zufallswert erzeugt, damit das Bild immer gleich aussieht. Gezeichnet wird mit
matplotlib im Stil der App (dunkel, Kerzen in Mint und Rot).

png(name) liefert das Bild als PNG-Bytes. FORMAT[name] = (Seitenverhältnis Höhe/Breite,
Anteil an der Textbreite), damit die Anleitung die Größe vorab kennt.
"""

from __future__ import annotations

import io

import numpy as np

GRUEN = "#19e6a2"
ROT = "#ff5a6a"
TEXT = "#e9ecea"
LEISE = "#858c8a"
GITTER = "#1a1e1d"
SMA_KURZ = "#b9c0be"  # wie im Chart der App
SMA_LANG = "#59625f"
MARKE = "#e6eae8"  # Hilfslinien (Trendlinien, Nackenlinie …)

BREITE = 6.8  # Breite in „Entwurfs-Zoll“; alle Maße unten beziehen sich darauf
MASS = 0.8    # tatsächliche Größe = Entwurf × MASS → Schrift wirkt in der Anleitung größer
DPI = 250     # 6,8 × 0,8 × 250 = 1360 Pixel; die App skaliert passend herunter


# --------------------------------------------------------------------- Grundlagen

def _figur(hoehe: float, spalten: int = 1, zeilen: int = 1, breite: float = BREITE, **kw):
    from matplotlib.figure import Figure
    fig = Figure(figsize=(breite * MASS, hoehe * MASS), dpi=DPI)
    fig.patch.set_alpha(0)
    achsen = fig.subplots(zeilen, spalten, squeeze=False, **kw)
    for ax in achsen.flat:
        ax.set_facecolor("none")
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
    return fig, achsen


def _gitter(ax, werte) -> None:
    for w in werte:
        ax.axhline(w, color=GITTER, lw=0.8, zorder=0)


def _pfad(punkte, n: int, rauschen: float = 0.0, seed: int = 1) -> np.ndarray:
    """Kursverlauf durch Stützpunkte (x von 0 bis 1) mit etwas geglättetem Rauschen."""
    xs = np.linspace(0, 1, n)
    px, py = zip(*punkte)
    y = np.interp(xs, px, py)
    if rauschen:
        rng = np.random.default_rng(seed)
        r = rng.normal(0, rauschen, n)
        r = np.convolve(r, [0.25, 0.5, 0.25], mode="same")
        # Stützpunkte selbst bleiben (fast) exakt, damit Hochs und Tiefs sauber sitzen
        abstand = np.min(np.abs(xs[:, None] - np.array(px)[None, :]), axis=1) * n
        r *= np.clip(abstand / 2.5, 0, 1)
        y = y + r
    return y


def _ohlc(schluss: np.ndarray, seed: int = 1, docht: float = 0.5):
    """Eröffnung, Hoch, Tief aus einer Reihe von Schlusskursen erfinden."""
    rng = np.random.default_rng(seed + 100)
    schritt = np.abs(np.diff(schluss)).mean() if len(schluss) > 1 else 1.0
    eroeff = np.r_[schluss[0] - (schluss[1] - schluss[0]), schluss[:-1]]
    eroeff = eroeff + rng.normal(0, schritt * 0.15, len(schluss))
    oben = np.maximum(eroeff, schluss) + rng.uniform(0.1, 1.0, len(schluss)) * schritt * docht
    unten = np.minimum(eroeff, schluss) - rng.uniform(0.1, 1.0, len(schluss)) * schritt * docht
    return eroeff, oben, unten, schluss


def _kerzen(ax, o, h, l, c, x0: float = 0, breite: float = 0.62, lw: float = 0.9,
            alpha: float = 1.0) -> None:
    x = np.arange(len(c)) + x0
    farben = [GRUEN if cc >= oo else ROT for oo, cc in zip(o, c)]
    ax.vlines(x, l, h, colors=farben, lw=lw, zorder=3, alpha=alpha)
    koerper = np.abs(np.asarray(c) - np.asarray(o))
    koerper = np.where(koerper > 0, koerper, (np.max(h) - np.min(l)) * 0.004)
    ax.bar(x, koerper, bottom=np.minimum(o, c), width=breite, color=farben, lw=0, zorder=4,
           alpha=alpha)


def _text(ax, x, y, s, farbe=TEXT, groesse=8.5, **kw) -> None:
    kw.setdefault("va", "center")
    kw.setdefault("ha", "left")
    ax.text(x, y, s, color=farbe, fontsize=groesse, zorder=10, **kw)


def _pfeil(ax, von, nach, farbe=MARKE, lw: float = 1.1) -> None:
    ax.annotate("", xy=nach, xytext=von, zorder=9,
                arrowprops=dict(arrowstyle="-|>", color=farbe, lw=lw, shrinkA=0, shrinkB=2,
                                mutation_scale=9))


def _linie(ax, x, y, **kw) -> None:
    kw.setdefault("color", MARKE)
    kw.setdefault("lw", 1.1)
    kw.setdefault("ls", (0, (5, 3)))
    kw.setdefault("alpha", 0.85)
    ax.plot(x, y, zorder=5, **kw)


def _titel(ax, s, unter: str = "") -> None:
    ax.set_title(s, color=TEXT, fontsize=10, fontweight="medium", loc="left", pad=14 if unter else 6)
    if unter:
        ax.text(0, 1.02, unter, transform=ax.transAxes, color=LEISE, fontsize=8, va="bottom")


def _rsi(kurs: np.ndarray, tage: int = 14) -> np.ndarray:
    diff = np.diff(kurs, prepend=kurs[0])
    gew, ver = np.clip(diff, 0, None), np.clip(-diff, 0, None)
    a = 1 / tage
    g = v = None
    out = np.full(len(kurs), np.nan)
    for i in range(len(kurs)):
        g = gew[i] if g is None else g + a * (gew[i] - g)
        v = ver[i] if v is None else v + a * (ver[i] - v)
        if i >= tage:
            out[i] = 100 - 100 / (1 + g / v) if v > 0 else 100
    return out


def _sma(kurs: np.ndarray, tage: int) -> np.ndarray:
    out = np.full(len(kurs), np.nan)
    c = np.cumsum(np.r_[0, kurs])
    out[tage - 1:] = (c[tage:] - c[:-tage]) / tage
    return out


# --------------------------------------------------------------------- Bilder

def _bild_kerze():
    fig, ax = _figur(2.9)
    ax = ax[0, 0]
    ax.set_xlim(0.1, 9.1)
    ax.set_ylim(18, 92)
    for x, o, c in ((1.6, 40, 70), (6.4, 70, 40)):
        farbe = GRUEN if c > o else ROT
        ax.vlines(x, 28, 82, colors=farbe, lw=2, zorder=3)
        ax.bar(x, abs(c - o), bottom=min(o, c), width=0.9, color=farbe, lw=0, zorder=4)
        tx = x + 0.9
        for y, s, f in ((82, "Hoch", TEXT), (28, "Tief", TEXT),
                        (c, "Schluss", TEXT), (o, "Eröffnung", TEXT)):
            ax.plot([x + 0.5 if y in (o, c) else x + 0.08, tx - 0.1], [y, y], color=LEISE,
                    lw=0.8, zorder=2)
            _text(ax, tx, y, s, f, 8.5)
        # Körper und Dochte benennen
        _text(ax, x - 0.7, (o + c) / 2, "Körper", LEISE, 8, ha="right")
        _text(ax, x - 0.25, 77, "Docht", LEISE, 8, ha="right")
        _text(ax, x - 0.25, 33, "Docht", LEISE, 8, ha="right")
        _text(ax, x - 1.4, 21, "Grüne Kerze: Schluss über Eröffnung" if c > o
              else "Rote Kerze: Schluss unter Eröffnung", farbe, 8.5, fontweight="medium")
    return fig


def _bild_kerzenmuster():
    fig, achsen = _figur(2.5, spalten=5, gridspec_kw={"wspace": 0.18})
    # (Eröffnung, Hoch, Tief, Schluss); die letzte(n) markierte(n) Kerze(n) sind das Muster
    muster = [
        ("Doji", "Unentschieden", [(40, 47, 39, 46), (46, 53, 45, 52), (52, 58, 51, 57),
                                   (57, 64, 50, 57.3)], [3]),
        ("Hammer", "nach Abwärtsphase", [(62, 63, 55, 56), (56, 57, 49, 50), (50, 51, 44, 45),
                                         (44, 46.5, 34, 46), (46, 53, 45, 52)], [3]),
        ("Shooting Star", "nach Aufwärtsphase", [(38, 45, 37, 44), (44, 51, 43, 50),
                                                 (50, 57, 49, 56), (56, 67, 55, 54.5),
                                                 (54.5, 55, 47, 48)], [3]),
        ("Engulfing ▲", "bullish", [(62, 63, 55, 56), (56, 57, 49, 50), (50, 51, 46.5, 47),
                                    (46, 56, 45, 55)], [2, 3]),
        ("Engulfing ▼", "bearish", [(38, 45, 37, 44), (44, 51, 43, 50), (50, 54, 49, 53),
                                    (54, 55, 44, 45)], [2, 3]),
    ]
    from matplotlib.patches import FancyBboxPatch
    for ax, (name, unter, kerzen, mark) in zip(achsen.flat, muster):
        o, h, l, c = (np.array(v, float) for v in zip(*kerzen))
        ax.set_xlim(-0.8, 4.8)
        ax.set_ylim(30, 70)
        _kerzen(ax, o, h, l, c, breite=0.6, lw=1.1)
        x0, x1 = min(mark) - 0.5, max(mark) + 0.5
        y0, y1 = min(l[mark]) - 2, max(h[mark]) + 2
        ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                                    boxstyle="round,pad=0,rounding_size=0.3",
                                    fc=(1, 1, 1, 0.06), ec=(1, 1, 1, 0.22), lw=0.8, zorder=1))
        ax.text(0.5, -0.04, name, transform=ax.transAxes, ha="center", va="top", color=TEXT,
                fontsize=9, fontweight="medium")
        ax.text(0.5, -0.17, unter, transform=ax.transAxes, ha="center", va="top", color=LEISE,
                fontsize=7.5)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.2)
    return fig


def _zickzack(ax, punkte, farbe, marken=None) -> None:
    x, y = zip(*punkte)
    ax.plot(x, y, color=farbe, lw=1.8, solid_joinstyle="round", zorder=4)
    for i, s in (marken or {}).items():
        nachbarn = [y[j] for j in (i - 1, i + 1) if 0 <= j < len(y)]
        oben = y[i] > max(nachbarn)
        ax.scatter([x[i]], [y[i]], s=14, color=TEXT, zorder=6, lw=0)
        _text(ax, x[i], y[i] + (5 if oben else -5), s, LEISE, 7.5, ha="center")


def _bild_trends():
    fig, achsen = _figur(2.6, spalten=3, gridspec_kw={"wspace": 0.12})
    a, b, c = achsen.flat
    auf = [(0, 20), (1, 42), (2, 34), (3, 57), (4, 48), (5, 72), (6, 62), (7, 86)]
    _zickzack(a, auf, GRUEN, {1: "HH", 2: "HT", 3: "HH", 4: "HT", 5: "HH", 6: "HT", 7: "HH"})
    _linie(a, [0, 7.4], [20, 20 + 7.4 * 7])
    _titel(a, "Aufwärtstrend", "höhere Hochs, höhere Tiefs")
    ab = [(0, 86), (1, 64), (2, 72), (3, 49), (4, 58), (5, 34), (6, 44), (7, 20)]
    _zickzack(b, ab, ROT, {1: "TT", 2: "TH", 3: "TT", 4: "TH", 5: "TT", 6: "TH", 7: "TT"})
    _linie(b, [0, 7.4], [86, 86 - 7.4 * 7])
    _titel(b, "Abwärtstrend", "tiefere Hochs, tiefere Tiefs")
    seit = [(0, 44), (1, 64), (2, 42), (3, 66), (4, 43), (5, 65), (6, 44), (7, 58)]
    _zickzack(c, seit, LEISE)
    _linie(c, [0, 7.3], [66, 66])
    _linie(c, [0, 7.3], [42, 42])
    _text(c, 7.3, 70, "Decke", LEISE, 7.5, ha="right")
    _text(c, 7.3, 37, "Boden", LEISE, 7.5, ha="right")
    _titel(c, "Seitwärtsphase", "kein Trend, Kurs pendelt")
    for ax in achsen.flat:
        ax.set_xlim(-0.4, 7.6)
        ax.set_ylim(10, 96)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.82, bottom=0.03)
    return fig


def _bild_unterstuetzung():
    fig, ax = _figur(2.9)
    ax = ax[0, 0]
    pkt = [(0, 50), (.06, 59), (.12, 42), (.2, 58.5), (.28, 41), (.37, 59.2), (.45, 41.5),
           (.53, 56), (.58, 60.5), (.62, 66.5), (.68, 71), (.75, 61.2), (.8, 64),
           (.9, 76), (1, 82)]
    c = _pfad(pkt, 72, rauschen=0.9, seed=4)
    o, h, l, c = _ohlc(c, seed=4, docht=0.6)
    h = np.minimum(h, np.where(np.arange(72) < 40, 60.4, 999))  # Decke im Seitwärtsbereich
    l = np.maximum(l, np.where(np.arange(72) < 40, 40.2, 0))
    _kerzen(ax, o, h, l, c)
    ax.axhspan(39.4, 41.2, xmax=0.62, color=MARKE, alpha=0.05, lw=0)
    ax.axhspan(59.4, 61.2, color=MARKE, alpha=0.05, lw=0)
    _linie(ax, [-1, 72], [60.3, 60.3])
    _linie(ax, [-1, 44], [40.3, 40.3])
    _text(ax, -0.5, 63, "Widerstand (Decke)", TEXT, 8.5)
    _text(ax, -0.5, 37.3, "Unterstützung (Boden)", TEXT, 8.5)
    _text(ax, 30, 67, "Ausbruch", TEXT, 8.5, ha="right")
    _pfeil(ax, (30.3, 67), (40.5, 62.5))
    _text(ax, 59, 52.5, "Rücktest: alter Widerstand\nist jetzt Unterstützung", LEISE, 8,
          ha="center")
    _pfeil(ax, (56, 56), (54, 59.5), farbe=LEISE)
    _gitter(ax, (40, 60, 80))
    ax.set_xlim(-1, 73)
    ax.set_ylim(33, 86)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    return fig


def _bild_durchschnitte():
    fig, ax = _figur(2.8)
    ax = ax[0, 0]
    n = 640
    pkt = [(0, 40), (.3, 78), (.38, 74), (.6, 46), (.66, 50), (.72, 44), (1, 92)]
    k = _pfad(pkt, n, rauschen=1.6, seed=7)
    s50, s200 = _sma(k, 50), _sma(k, 200)
    start = 200
    x = np.arange(n - start)
    ax.plot(x, k[start:], color=TEXT, lw=0.9, alpha=0.4, zorder=3)
    ax.plot(x, s50[start:], color="#d5dbd9", lw=1.8, zorder=4)
    ax.plot(x, s200[start:], color="#6d7673", lw=2.2, zorder=4)
    d = np.sign(s50[start:] - s200[start:])
    kreuz = np.where(np.diff(d) != 0)[0]
    for i in kreuz:
        gold = d[i + 1] > 0
        y = s50[start + i]
        ax.scatter([i], [y], s=60, facecolor="none", edgecolor=GRUEN if gold else ROT, lw=1.6,
                   zorder=6)
        _text(ax, i, y + (-7 if gold else 7), "Golden Cross" if gold else "Death Cross",
              GRUEN if gold else ROT, 8.5, ha="center", fontweight="medium")
    for y, farbe, lw, alpha, s in ((49, TEXT, 0.9, 0.4, "Kurs"),
                                   (42.5, "#d5dbd9", 1.8, 1, "50-Tage-Linie (hell)"),
                                   (36, "#6d7673", 2.2, 1, "200-Tage-Linie (dunkel)")):
        ax.plot([2, 16], [y, y], color=farbe, lw=lw, alpha=alpha)
        _text(ax, 19, y, s, LEISE, 8)
    _gitter(ax, (40, 60, 80))
    ax.set_xlim(-4, n - start + 4)
    ax.set_ylim(32, 98)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    return fig


def _bild_volumen():
    fig, achsen = _figur(3.0, zeilen=2, sharex=True,
                         gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05})
    ax, av = achsen[0, 0], achsen[1, 0]
    n = 60
    pkt = [(0, 46), (.1, 52), (.2, 45), (.3, 52.5), (.4, 46.5), (.5, 52), (.62, 48),
           (.68, 51), (.71, 58), (.8, 63), (.86, 61), (1, 72)]
    c = _pfad(pkt, n, rauschen=0.5, seed=11)
    o, h, l, c = _ohlc(c, seed=11, docht=0.5)
    _kerzen(ax, o, h, l, c)
    rng = np.random.default_rng(3)
    vol = np.linspace(1.0, 0.55, n) * rng.uniform(0.7, 1.2, n)
    aus = int(.7 * (n - 1))
    vol[aus - 1:aus + 2] *= [1.8, 3.2, 2.2]
    vol[aus + 2:] *= 1.35
    farben = [GRUEN if cc >= oo else ROT for oo, cc in zip(o, c)]
    av.bar(np.arange(n), vol, width=0.62, color=farben, alpha=0.55, lw=0)
    _linie(ax, [-1, aus + 1], [53, 53])
    _text(ax, aus - 3, 61, "Ausbruch mit\nhohem Volumen", TEXT, 8.5, ha="right")
    _pfeil(ax, (aus - 2.6, 61), (aus - 0.3, 56.5))
    _text(ax, 1, 56.5, "Seitwärtsphase, Volumen nimmt ab", LEISE, 8)
    _text(av, -0.5, vol.max() * 0.85, "Volumen", LEISE, 8)
    ax.set_xlim(-1, n)
    ax.set_ylim(42, 76)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    return fig


def _bild_divergenz():
    fig, achsen = _figur(3.2, zeilen=2, sharex=True,
                         gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.08})
    ax, ar = achsen[0, 0], achsen[1, 0]
    rng = np.random.default_rng(147)
    teile = [(22, 0.0, 0.8), (26, 1.0, 1.0), (14, -0.7, 0.9), (34, 0.32, 0.9), (24, -0.8, 1.0)]
    k = 45 + np.cumsum(np.concatenate([rng.normal(d, sd, m) for m, d, sd in teile]))
    n = len(k)
    r = _rsi(k)
    s = 18
    x = np.arange(n - s)
    ax.plot(x, k[s:], color=TEXT, lw=1.3, zorder=3)
    ar.plot(x, r[s:], color=SMA_KURZ, lw=1.2, zorder=3)
    for w in (30, 70):
        ar.axhline(w, color=LEISE, lw=0.7, ls=(0, (1, 2.5)))
    ar.axhspan(70, 100, color=ROT, alpha=0.035, lw=0)
    ar.axhspan(0, 30, color=GRUEN, alpha=0.035, lw=0)
    # Hochs im Kurs und im RSI suchen
    e1, e3 = 48, 96  # Enden der beiden Anstiege
    i1 = e1 - 6 + int(np.argmax(k[e1 - 6:e1 + 4])) - s
    i2 = e3 - 8 + int(np.argmax(k[e3 - 8:e3 + 4])) - s
    j1 = i1 - 6 + int(np.nanargmax(r[s + i1 - 6:s + i1 + 1]))
    j2 = i2 - 6 + int(np.nanargmax(r[s + i2 - 6:s + i2 + 1]))
    _linie(ax, [i1, i2], [k[s + i1] + 1.2, k[s + i2] + 1.2], color=GRUEN, ls="-", lw=1.4)
    _linie(ar, [j1, j2], [r[s + j1] + 3, r[s + j2] + 3], color=ROT, ls="-", lw=1.4)
    _text(ax, (i1 + i2) / 2, (k[s + i1] + k[s + i2]) / 2 + 4, "Kurs: höheres Hoch", GRUEN, 8.5,
          ha="center", fontweight="medium")
    _text(ar, (j1 + j2) / 2, 14, "RSI: tieferes Hoch → Schwung lässt nach", ROT, 8.5,
          ha="center", fontweight="medium")
    _text(ar, n - s - 1, 74, "70", LEISE, 7, ha="right", va="bottom")
    _text(ar, n - s - 1, 26, "30", LEISE, 7, ha="right", va="top")
    _text(ar, 0, 92, "RSI", LEISE, 8, va="top")
    ax.set_ylim(np.min(k[s:]) - 2, np.max(k[s:]) + 7)
    ar.set_ylim(0, 100)
    ax.set_xlim(-2, n - s + 1)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    return fig


def _bild_bollinger():
    fig, ax = _figur(2.6)
    ax = ax[0, 0]
    n = 170
    rng = np.random.default_rng(21)
    schritte = np.r_[rng.normal(0.05, 1.3, 60), rng.normal(0, 0.28, 60),
                     rng.normal(0.75, 1.0, 50)]
    k = 50 + np.cumsum(schritte)
    m = _sma(k, 20)
    sd = np.array([np.std(k[max(0, i - 19):i + 1]) for i in range(n)])
    ob, ub = m + 2 * sd, m - 2 * sd
    s = 20
    x = np.arange(n - s)
    ax.fill_between(x, ub[s:], ob[s:], color=MARKE, alpha=0.06, lw=0)
    for b in (ob, ub):
        ax.plot(x, b[s:], color="#8a9592", lw=0.9, alpha=0.8)
    ax.plot(x, m[s:], color=LEISE, lw=0.8, ls=(0, (4, 3)))
    ax.plot(x, k[s:], color=TEXT, lw=1.3, zorder=3)
    eng = 100 - s
    _text(ax, eng, ob[eng + s] + 5.5, "Squeeze: Band wird eng", TEXT, 8.5, ha="center")
    _pfeil(ax, (eng, ob[eng + s] + 4), (eng, ob[eng + s] + 0.6))
    spaet = n - s - 22
    _text(ax, spaet - 4, ob[spaet + s] + 4.5, "Band öffnet sich:\nstarke Bewegung", TEXT, 8.5,
          ha="right")
    lo, hi = np.nanmin(ub[s:]), np.nanmax(ob[s:])
    ax.set_ylim(lo - 3, hi + 9)
    ax.set_xlim(-2, n - s + 1)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    return fig


def _formation(ax, pkt, n, seed, docht=0.5, rauschen=0.7):
    c = _pfad(pkt, n, rauschen=rauschen, seed=seed)
    o, h, l, c = _ohlc(c, seed=seed, docht=docht)
    _kerzen(ax, o, h, l, c)
    return o, h, l, c


def _bild_doppelboden(beschriften: bool = True, ax=None):
    fig = None
    if ax is None:
        fig, ax = _figur(2.9)
        ax = ax[0, 0]
    n = 66
    pkt = [(0, 80), (.12, 70), (.25, 45), (.38, 60), (.52, 45.3), (.64, 57), (.7, 61.5),
           (.76, 60.5), (.88, 70), (1, 76)]
    _formation(ax, pkt, n, seed=9)
    if beschriften:
        _linie(ax, [12, n], [60.5, 60.5])
        _text(ax, 13, 63, "Nackenlinie", TEXT, 8.5)
        for x, s in ((.25, "Tief 1"), (.52, "Tief 2")):
            _text(ax, x * (n - 1), 40.5, s, TEXT, 8.5, ha="center")
        _text(ax, .7 * (n - 1) - 2, 66.5, "Ausbruch", TEXT, 8.5, ha="right")
        _pfeil(ax, (.7 * (n - 1) - 1.6, 66.5), (.7 * (n - 1) + 0.2, 62.5))
        # Höhe der Formation und Kursziel
        xm = .52 * (n - 1) + 3
        ax.annotate("", xy=(xm, 45.3), xytext=(xm, 60.5),
                    arrowprops=dict(arrowstyle="<->", color=GRUEN, lw=1.1, mutation_scale=7))
        xz = n - 0.5
        ax.annotate("", xy=(xz, 75.7), xytext=(xz, 60.5),
                    arrowprops=dict(arrowstyle="<->", color=GRUEN, lw=1.1, mutation_scale=7))
        _linie(ax, [n - 8, n + 0.5], [75.7, 75.7], color=GRUEN, lw=1.0)
        _text(ax, xz - 1, 79.5, "Kursziel ≈ Höhe der Formation", GRUEN, 8.5, ha="right",
              fontweight="medium")
        ax.set_ylim(37, 86)
    ax.set_xlim(-1, n + 1.5)
    if fig is not None:
        fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    return fig


def _bild_skf():
    fig, ax = _figur(2.9)
    ax = ax[0, 0]
    n = 76
    pkt = [(0, 45), (.15, 70), (.25, 58), (.4, 82), (.53, 58.3), (.66, 70.5), (.76, 59),
           (.8, 55), (.86, 57.5), (1, 44)]
    _formation(ax, pkt, n, seed=13)
    _linie(ax, [.2 * (n - 1), n], [58.2, 58.2])
    for x, y, s in ((.15, 75, "linke Schulter"), (.4, 87, "Kopf"), (.66, 75.5, "rechte Schulter")):
        _text(ax, x * (n - 1), y, s, TEXT, 8.5, ha="center")
    _text(ax, .4 * (n - 1), 54.5, "Nackenlinie", TEXT, 8.5, ha="center")
    _text(ax, n - 1, 63.5, "Bruch der\nNackenlinie", TEXT, 8.5, ha="right")
    _pfeil(ax, (.84 * (n - 1), 61.3), (.79 * (n - 1), 57.4))
    ax.set_xlim(-1, n + 1)
    ax.set_ylim(38, 92)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    return fig


def _bild_flagge(beschriften: bool = True, ax=None):
    fig = None
    if ax is None:
        fig, ax = _figur(2.8)
        ax = ax[0, 0]
    n = 56
    pkt = [(0, 40), (.08, 41), (.27, 70), (.33, 66), (.38, 69), (.44, 64.5), (.5, 67.5),
           (.56, 63), (.6, 65.5), (.66, 72), (.8, 82), (1, 94)]
    _formation(ax, pkt, n, seed=17, rauschen=0.6)
    if beschriften:
        x0, x1 = .27 * (n - 1), .62 * (n - 1)
        _linie(ax, [x0, x1], [71.5, 67.2])
        _linie(ax, [x0 + 2, x1], [65.5, 61.6])
        _text(ax, .17 * (n - 1) - 1.5, 57, "Fahnenstange", TEXT, 8.5, ha="right")
        _text(ax, (x0 + x1) / 2, 76, "Flagge", TEXT, 8.5, ha="center")
        _text(ax, .66 * (n - 1) + 2, 66, "Ausbruch: Trend\nläuft weiter", TEXT, 8.5)
        _pfeil(ax, (.66 * (n - 1) + 1.8, 67.5), (.645 * (n - 1) + 0.2, 70))
    ax.set_xlim(-1, n + 1)
    ax.set_ylim(34, 100)
    if fig is not None:
        fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    return fig


def _bild_dreiecke():
    fig, achsen = _figur(2.5, spalten=3, gridspec_kw={"wspace": 0.12})
    a, b, c = achsen.flat
    auf = [(0, 30), (1, 70), (2, 40), (3, 70), (4, 50), (5, 70), (6, 60), (7, 70)]
    _zickzack(a, auf, TEXT)
    _linie(a, [0, 7.6], [70, 70])
    _linie(a, [0, 7.4], [30, 30 + 7.4 * 5])
    _pfeil(a, (7, 70), (8.1, 88), farbe=GRUEN, lw=1.8)
    _titel(a, "Aufsteigendes Dreieck", "flache Decke, steigende Tiefs")
    ab = [(0, 80), (1, 40), (2, 70), (3, 40), (4, 60), (5, 40), (6, 50), (7, 40)]
    _zickzack(b, ab, TEXT)
    _linie(b, [0, 7.6], [40, 40])
    _linie(b, [0, 7.4], [80, 80 - 7.4 * 5])
    _pfeil(b, (7, 40), (8.1, 22), farbe=ROT, lw=1.8)
    _titel(b, "Absteigendes Dreieck", "flacher Boden, fallende Hochs")
    sym = [(0, 82), (1, 30), (2, 74), (3, 38), (4, 66), (5, 46), (6, 58), (7, 54)]
    _zickzack(c, sym, TEXT)
    _linie(c, [0, 7.6], [82, 82 - 7.6 * 4])
    _linie(c, [1, 7.6], [30, 30 + 6.6 * 4])
    _pfeil(c, (7.3, 56), (8.3, 68), farbe=LEISE)
    _pfeil(c, (7.3, 52), (8.3, 40), farbe=LEISE)
    _titel(c, "Symmetrisches Dreieck", "Richtung offen")
    for ax in achsen.flat:
        ax.set_xlim(-0.4, 8.6)
        ax.set_ylim(16, 94)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.82, bottom=0.03)
    return fig


def _bild_gap():
    fig, ax = _figur(2.3)
    ax = ax[0, 0]
    kerzen = [(50, 51.5, 48.5, 49), (49, 50, 47, 47.8), (47.8, 50.5, 47.3, 50), (50, 51, 48.2, 49),
              (49, 50.6, 48.5, 50.2), (50.2, 51, 49, 49.6), (49.6, 51.4, 49.2, 51),
              (57, 60.5, 56.2, 59.5), (59.5, 61.5, 58.4, 61), (61, 62, 59, 59.8),
              (59.8, 62.8, 59.3, 62.3), (62.3, 64, 61.5, 63.5), (63.5, 64.2, 61.8, 62.5),
              (62.5, 65.5, 62, 65)]
    o, h, l, c = (np.array(v, float) for v in zip(*kerzen))
    _kerzen(ax, o, h, l, c, breite=0.6, lw=1.1)
    ax.axhspan(51.4, 56.2, xmin=0.44, xmax=0.56, color=GRUEN, alpha=0.1, lw=0)
    _text(ax, 5.4, 56.5, "Kurslücke (Gap):\nkein Handel in\ndiesem Bereich", TEXT, 8.5,
          ha="right")
    _pfeil(ax, (5.5, 55.5), (6.3, 53.8))
    _text(ax, 13.4, 52.5, "z. B. nach Quartalszahlen", LEISE, 8, ha="right")
    ax.set_xlim(-1, 14)
    ax.set_ylim(45, 67)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    return fig


def _uebung(nummer: str, zeichnen):
    fig, ax = _figur(2.1, breite=3.3)
    ax = ax[0, 0]
    zeichnen(ax)
    ax.text(0.02, 0.97, nummer, transform=ax.transAxes, color=TEXT, fontsize=12,
            fontweight="bold", va="top")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.98, bottom=0.02)
    return fig


def _ueb_a(ax):  # Doppeltop
    n = 60
    pkt = [(0, 42), (.2, 72), (.36, 58), (.52, 71.6), (.66, 60), (.72, 56), (.8, 58), (1, 44)]
    _formation(ax, pkt, n, seed=31)
    ax.set_xlim(-6, n)
    ax.set_ylim(36, 80)


def _ueb_b(ax):  # Bullenflagge
    _bild_flagge(beschriften=False, ax=ax)


def _ueb_c(ax):  # inverse Schulter-Kopf-Schulter
    n = 70
    pkt = [(0, 78), (.15, 54), (.26, 66), (.4, 42), (.53, 66.3), (.66, 53.5), (.78, 65),
           (.84, 70), (1, 80)]
    _formation(ax, pkt, n, seed=37)
    ax.set_xlim(-6, n)
    ax.set_ylim(36, 86)


def _ueb_d(ax):  # aufsteigendes Dreieck mit Ausbruch
    n = 64
    pkt = [(0, 42), (.12, 66), (.24, 50), (.36, 66.2), (.48, 56), (.6, 66), (.7, 60.5),
           (.78, 66.3), (.86, 74), (1, 82)]
    _formation(ax, pkt, n, seed=41, rauschen=0.5)
    ax.set_xlim(-6, n)
    ax.set_ylim(36, 88)


BILDER = {
    "kerze": _bild_kerze,
    "kerzenmuster": _bild_kerzenmuster,
    "trends": _bild_trends,
    "unterstuetzung": _bild_unterstuetzung,
    "durchschnitte": _bild_durchschnitte,
    "volumen": _bild_volumen,
    "divergenz": _bild_divergenz,
    "bollinger": _bild_bollinger,
    "doppelboden": _bild_doppelboden,
    "skf": _bild_skf,
    "flagge": _bild_flagge,
    "dreiecke": _bild_dreiecke,
    "gap": _bild_gap,
    "uebung_a": lambda: _uebung("A", _ueb_a),
    "uebung_b": lambda: _uebung("B", _ueb_b),
    "uebung_c": lambda: _uebung("C", _ueb_c),
    "uebung_d": lambda: _uebung("D", _ueb_d),
}

# Seitenverhältnis (Höhe/Breite) und Anteil an der Textbreite
FORMAT = {name: (0.0, 1.0) for name in BILDER}
_HOEHEN = {"kerze": 2.9, "kerzenmuster": 2.5, "trends": 2.6, "unterstuetzung": 2.9,
           "durchschnitte": 2.8, "volumen": 3.0, "divergenz": 3.2, "bollinger": 2.6,
           "doppelboden": 2.9, "skf": 2.9, "flagge": 2.8, "dreiecke": 2.5, "gap": 2.3}
for _n, _h in _HOEHEN.items():
    FORMAT[_n] = (_h / BREITE, 1.0)
for _n in ("uebung_a", "uebung_b", "uebung_c", "uebung_d"):
    FORMAT[_n] = (2.1 / 3.3, 0.5)

_CACHE: dict[str, bytes] = {}


def png(name: str) -> bytes:
    """Bild als PNG (doppelte Auflösung, transparenter Hintergrund)."""
    if name not in _CACHE:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        fig = BILDER[name]()
        FigureCanvasAgg(fig)
        puffer = io.BytesIO()
        fig.savefig(puffer, format="png", dpi=DPI, transparent=True)
        _CACHE[name] = puffer.getvalue()
    return _CACHE[name]
