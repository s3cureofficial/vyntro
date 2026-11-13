#!/usr/bin/env python3
"""Vyntro – Signale. Klar erklärt. Fenster-App für macOS (Qt).

Watchlist links, Detailansicht rechts: Signal, Indikatoren, Chart und Backtest.
Die Regeln stammen aus signale.py. Keine Anlageberatung – die App handelt nicht.
"""

from __future__ import annotations

import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

import matplotlib

matplotlib.use("QtAgg")
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import pandas as pd
import yfinance as yf
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import json
import os
import math
import pickle
import re

import numpy as np
import threading
import time

from PySide6.QtCore import (
    QByteArray, QDate, QEasingCurve, QEvent, QObject, QPointF, QRectF, QRunnable, QSettings, QSize, Qt, QThreadPool, QTimer,
    QUrl, QVariantAnimation, Signal,
)
from PySide6.QtGui import (
    QAction, QBrush, QDesktopServices, QFont, QIcon, QImage, QLinearGradient, QPainter, QRadialGradient, QPainterPath, QPen, QPalette, QPixmap, QRadialGradient, QColor, QFontMetrics, QKeySequence, QShortcut, QStandardItem, QStandardItemModel,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QCompleter, QDateEdit, QDialog, QDialogButtonBox,
    QAbstractItemView, QComboBox, QHeaderView, QTableWidget, QTableWidgetItem, QDoubleSpinBox, QFileDialog, QTextBrowser, QInputDialog, QMessageBox, QPlainTextEdit, QRadioButton, QSystemTrayIcon, QSpinBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

import anleitung
import begruendung
import update
import tr_import
import pfade
import konto
import logos
import nachrichten
import prognose
import signale as s

JAHRE = 5  # Historie für Backtest und Chart

# Eigene, markierte Werte
MEINE = pfade.DATEN / "meine.txt"
LISTEN = pfade.DATEN / "listen.json"  # weitere eigene Listen
# Beliebte Werte, die als Vorschläge erscheinen (sofern nicht schon markiert)
VORSCHLAEGE = ["AAPL", "MSFT", "NVDA", "AMZN", "TSLA", "SAP.DE", "EUNL.DE",
               "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD"]
# Diese Beispiele standen früher vorgegeben in watchlist.txt – sie sind jetzt Vorschläge
ALTE_BEISPIELE = ["AAPL", "SAP.DE", "EUNL.DE", "BTC-USD", "ETH-USD"]
GOLD = "#19e6a2"  # Mint aus dem Logo – nur für einzelne Akzente
SILBER = "#e6eae8"  # Bedienelemente, Auswahl, Sterne
# Werte, die für die Kategorie "Kaufsignale" im Hintergrund geprüft werden
SCAN = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "JPM", "V",
        "COST", "NFLX", "AMD", "PLTR", "SAP.DE", "SIE.DE", "ALV.DE", "DTE.DE", "AIR.DE",
        "RHM.DE", "MBG.DE", "BMW.DE", "IFX.DE", "EUNL.DE", "VWCE.DE",
        # restlicher DAX 40
        "ADS.DE", "BEI.DE", "BNR.DE", "CON.DE", "1COV.DE", "DHL.DE", "DTG.DE", "ENR.DE",
        "FME.DE", "FRE.DE", "HNR1.DE", "HEI.DE", "HEN3.DE", "MRK.DE", "MTX.DE", "MUV2.DE",
        "P911.DE", "QIA.DE", "SHL.DE", "SY1.DE", "VOW3.DE", "ZAL.DE", "SRT3.DE", "G1A.DE",
        "DB1.DE",
        # weitere große US-Werte
        "BRK-B", "LLY", "UNH", "XOM", "WMT", "MA", "PG", "JNJ", "HD", "KO", "PEP", "ORCL",
        "CRM", "ADBE", "DIS", "MCD", "CSCO", "UBER", "PYPL", "COIN",
        # günstigere Aktien (Kurs meist unter 50 €)
        "CBK.DE", "EOAN.DE", "LHA.DE", "VNA.DE", "DBK.DE", "PAH3.DE", "BAS.DE", "BAYN.DE",
        "F", "PFE", "T", "NOK", "VZ", "BAC", "SNAP", "RIVN", "NIO", "KHC", "INTC",
        # Krypto
        "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD", "DOGE-USD", "BNB-USD", "ADA-USD",
        "AVAX-USD", "LINK-USD", "DOT-USD", "LTC-USD", "TRX-USD", "XLM-USD", "BCH-USD"]
# Krypto-Ticker bei Yahoo enden auf "-Währung" (z. B. BTC-USD, ETH-EUR)
PREISGRENZE = 50.0  # Kategorie "Kaufsignal unter 50 €" (in den Einstellungen änderbar)
SORTIERUNGEN = {"eigene": "Eigene Reihenfolge", "name": "Name", "aenderung": "Tagesänderung",
                "signal": "Signal"}
KRYPTO_MUSTER = re.compile(r"-(USD|EUR|USDT|USDC|GBP|CHF|JPY|BTC|ETH)$")

matplotlib.rcParams["font.family"] = (["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
                                      if sys.platform == "darwin" else
                                      ["Segoe UI", "Arial", "DejaVu Sans"])

# ------------------------------------------------------------------ Theme

# Glasmorphismus: halbtransparente Flächen (QSS-Werte als rgba) über einem farbigen
# Verlaufs-Hintergrund. "chart", "gitter" und "markerrand" sind die Farben für matplotlib.
HELL = dict(
    bg="#e7eaf6",
    seite="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,255,255,175), "
          "stop:1 rgba(255,255,255,120))",
    karte="qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(255,255,255,175), "
          "stop:1 rgba(255,255,255,120))",
    rand="rgba(255,255,255,230)", glanz="rgba(255,255,255,255)", auswahl="rgba(255,255,255,200)",
    feld="rgba(255,255,255,140)", feldhover="rgba(255,255,255,180)",
    solid="#f7f8fc", text="#0f1222", leise="#5c6178", akzent="#0f1222",
    gruen="#0f9f4a", rot="#e0303c", grau="#6b7088", orange="#d9860b", lila="#7c5cff",
    chart="none", gitter="#d4d8e8", markerrand="#ffffff",
    blobs=[("#a78bfa", .15, .10, .55), ("#60a5fa", .90, .20, .50), ("#5eead4", .70, .95, .55),
           ("#f9a8d4", .30, .80, .45)],
)
DUNKEL = dict(
    # Fast schwarz, Silber für Bedienelemente, Mint (Logo) nur als einzelner Akzent
    bg="#010101",
    seite="qlineargradient(x1:0, y1:0, x2:0.35, y2:1, stop:0 rgba(235,245,242,13), "
          "stop:0.5 rgba(235,245,242,5), stop:1 rgba(235,245,242,2))",
    karte="qlineargradient(x1:0, y1:0, x2:0.35, y2:1, stop:0 rgba(235,245,242,13), "
          "stop:0.5 rgba(235,245,242,5), stop:1 rgba(235,245,242,2))",
    rand="rgba(230,240,236,14)", glanz="rgba(230,240,236,34)",
    auswahl="rgba(235,245,242,13)", feld="rgba(235,245,242,7)", feldhover="rgba(235,245,242,13)",
    solid="#0a0b0b", text="#e9ecea", leise="#858c8a", akzent="#e6eae8",
    gruen="#19e6a2", rot="#ff5a6a", grau="#7c8381", orange="#9c9277", lila="#5e6765",
    chart="none", gitter="#141716", markerrand="#030303",
    # sehr dunkle, kühle Licht-Inseln, nur ganz unten rechts ein Hauch Mint
    blobs=[("#151817", .05, .00, .55), ("#111413", .98, .10, .50), ("#06261c", .92, 1.08, .45),
           ("#0d1110", .20, .95, .40)],
)
T = dict(HELL)

QSS = """
* { font-family: "SF Pro Text", "Segoe UI", "Helvetica Neue"; color: @text; }
QMainWindow { background: @bg; }
#seite, #karte {
  background: @karte; border: 1px solid @rand; border-top-color: @glanz; border-radius: 14px;
}
#topbar { background: @bg; }
QLabel { background: transparent; border: none; }
QLabel[rolle="h1"] { font-size: 18px; font-weight: 500; }
QLabel[rolle="h2"] { font-size: 13px; font-weight: 500; letter-spacing: 0.2px; }
QLabel[rolle="kartentitel"] { font-size: 16px; font-weight: 500; letter-spacing: 0.2px; }
QLabel[rolle="kartenname"] { font-size: 11px; font-weight: 500; color: @leise; letter-spacing: 0.6px; }
QLabel[rolle="sektion"] { font-size: 12px; font-weight: 400; color: @leise; }
QLabel[rolle="leise"] { font-size: 13px; color: @leise; }
QLabel[rolle="klein"] { font-size: 11px; color: @leise; }
QLabel[rolle="preis"] { font-size: 30px; font-weight: 400; letter-spacing: -0.3px; }
QLabel[rolle="wert"] { font-size: 20px; font-weight: 400; }
QLabel[rolle="zticker"] { font-size: 13px; font-weight: 500; }
QLabel[rolle="zkurs"] { font-size: 13px; font-weight: 400; }
QLineEdit#suche {
  background: @feld; border: 1px solid @rand; border-radius: 8px;
  padding: 8px 12px; font-size: 13px; selection-background-color: @leise;
}
QLineEdit#suche:focus { border: 1px solid rgba(235,245,242,70); background: @feldhover; }
QListWidget#liste { background: transparent; border: none; outline: 0; }
QListWidget#liste::item { border-radius: 8px; margin: 1px 0; border: 1px solid transparent; }
QListWidget#liste::item:hover { background: @feld; }
QListWidget#liste::item:selected { background: @auswahl; border: 1px solid rgba(235,245,242,34); }
QWidget#zeile { background: transparent; }
QSpinBox {
  background: @feld; border: 1px solid @rand; border-radius: 6px; padding: 3px 6px;
  font-size: 12px;
}
QDoubleSpinBox, QDateEdit {
  background: @feld; border: 1px solid @rand; border-radius: 8px; padding: 7px 10px;
  font-size: 14px;
}
QPlainTextEdit#notiz {
  background: @feld; border: 1px solid @rand; border-radius: 8px; padding: 6px 8px;
  font-size: 13px; selection-background-color: @leise;
}
QPlainTextEdit#notiz:focus { border: 1px solid rgba(235,245,242,70); }
QDoubleSpinBox:focus, QDateEdit:focus { border: 1px solid rgba(235,245,242,70); }
QDialog { background: @solid; }
QRadioButton { font-size: 13px; spacing: 10px; }
QRadioButton::indicator {
  width: 14px; height: 14px; border-radius: 8px; border: 1px solid @leise; background: @feld;
}
QRadioButton::indicator:checked { border: 4px solid @akzent; background: @solid; width: 8px; height: 8px; }
QDialogButtonBox QPushButton {
  background: @feld; border: 1px solid @rand; border-radius: 8px; padding: 7px 16px;
  font-size: 13px; font-weight: 500;
}
QDialogButtonBox QPushButton:hover { background: @feldhover; }
QDialogButtonBox QPushButton:default { background: @akzent; color: #050505; border: none; }
QDialogButtonBox QPushButton:disabled { color: @leise; background: @feld; }
QFrame#depotzeile { background: transparent; border-radius: 8px; }
QTextBrowser#anleitung { background: transparent; border: none; selection-background-color: @leise; }
QPushButton#update {
  background: rgba(25,230,162,22); color: #19e6a2; border: 1px solid rgba(25,230,162,90);
  border-radius: 8px; padding: 6px 12px; font-size: 12px; font-weight: 600;
}
QPushButton#update:hover { background: rgba(25,230,162,40); }
QPushButton#updatejetzt {
  background: #19e6a2; color: #050505; border: none; border-radius: 8px; padding: 8px 16px;
  font-size: 13px; font-weight: 600;
}
QPushButton#updatejetzt:disabled { background: @feld; color: @leise; }
QProgressBar#updatebalken { background: @feld; border: none; border-radius: 3px; max-height: 6px; }
QProgressBar#updatebalken::chunk {
  border-radius: 3px;
  background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(25,230,162,120), stop:1 #19e6a2);
}
QFrame#homekachel {
  background: @karte; border: 1px solid @rand; border-top-color: @glanz; border-radius: 12px;
}
QFrame#homekachel:hover { border-color: rgba(235,245,242,40); }
QFrame#palettenrahmen { background: @solid; border: 1px solid @glanz; border-radius: 12px; }
QLineEdit#paletteneingabe {
  background: transparent; border: none; font-size: 16px; padding: 8px 4px;
  selection-background-color: @leise;
}
QListWidget#palettenliste { background: transparent; border: none; outline: 0; font-size: 13px; }
QListWidget#palettenliste::item { border-radius: 7px; padding: 0 8px; }
QListWidget#palettenliste::item:selected { background: @auswahl; color: @text; }
QListWidget#palettenliste::item:hover { background: @feld; }
QTableWidget#tabelle {
  background: transparent; border: none; font-size: 13px; outline: 0;
  selection-background-color: @auswahl; selection-color: @text;
}
QTableWidget#tabelle::item { padding: 0 10px; border-bottom: 1px solid @rand; }
QTableWidget#tabelle::item:hover { background: @feld; }
QHeaderView { background: transparent; border: none; }
QTableCornerButton::section { background: transparent; border: none; }
QHeaderView::section {
  background: transparent; color: @leise; border: none; border-bottom: 1px solid @rand;
  padding: 6px 10px; font-size: 11px; font-weight: 500;
}
QFrame#depotzeile:hover { background: @feld; }
QSpinBox#betrag { font-size: 26px; font-weight: 500; padding: 10px 14px; border-radius: 10px; }
QSpinBox:focus { border: 1px solid @leise; }
QCheckBox { font-size: 13px; spacing: 10px; }
QCheckBox::indicator {
  width: 14px; height: 14px; border-radius: 4px; border: 1px solid @leise; background: @feld;
}
QCheckBox::indicator:checked { background: @akzent; border: 1px solid @akzent; }
QComboBox {
  background: @feld; border: 1px solid @rand; border-radius: 8px; padding: 6px 10px;
  font-size: 13px; color: @text;
}
QComboBox:hover { background: @feldhover; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
  background: @solid; border: 1px solid @rand; border-radius: 8px; padding: 4px;
  selection-background-color: @auswahl; outline: 0;
}
QPushButton#aktion {
  background: @auswahl; color: @text; border: none; border-radius: 8px;
  padding: 8px 14px; font-size: 13px; font-weight: 500;
}
QPushButton#aktion:hover { background: @rand; }
QPushButton#chip {
  background: @feld; color: @text; border: 1px solid @rand; border-top-color: @glanz;
  border-radius: 8px; padding: 6px 12px; font-size: 12px; font-weight: 500;
}
QPushButton#chip:hover { background: @feldhover; }
QPushButton#chip:checked { background: @auswahl; color: @akzent; border-color: rgba(235,245,242,44); }
QLabel#statuschip {
  background: @feld; border: 1px solid @rand; border-top-color: @glanz; border-radius: 8px;
  padding: 6px 12px; font-size: 12px; font-weight: 500;
}
QPushButton#icon {
  background: transparent; border: none; border-radius: 6px; font-size: 15px;
  color: @leise; padding: 3px 7px;
}
QPushButton#icon:hover { background: @feld; color: @text; }
QFrame#tabs { background: @feld; border: 1px solid @rand; border-radius: 9px; }
QPushButton#tab {
  background: transparent; border: none; border-radius: 6px; padding: 6px 12px;
  font-size: 13px; font-weight: 500; color: @leise;
}
QPushButton#tab:hover { color: @text; }
QPushButton#tab:checked { background: @auswahl; color: @akzent; }
QPushButton#seg {
  background: transparent; border: none; border-radius: 6px; padding: 4px 9px;
  font-size: 12px; font-weight: 500; color: @leise;
}
QPushButton#seg:hover { color: @text; background: @feld; }
QPushButton#listenwahl {
  background: transparent; border: none; border-radius: 6px; padding: 3px 6px;
  font-size: 13px; font-weight: 500; color: @text;
}
QPushButton#listenwahl:hover { background: @feld; }
QPushButton#seg:checked { color: @akzent; background: @auswahl; }
QProgressBar { background: @feld; border: none; border-radius: 2px; max-height: 4px; }
QProgressBar::chunk { border-radius: 2px; background: @text; }
QAbstractItemView#popup {
  background: @solid; border: 1px solid @rand; border-radius: 10px; padding: 4px;
  font-size: 13px; outline: 0;
}
QAbstractItemView#popup::item { padding: 7px 8px; border-radius: 6px; }
QAbstractItemView#popup::item:selected { background: @auswahl; color: @text; }
QMenu { background: @solid; border: 1px solid @rand; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 16px; border-radius: 5px; }
QMenu::item:selected { background: @auswahl; }
QScrollArea#detailscroll, QScrollArea#detailscroll > QWidget, QWidget#detail,
QStackedWidget { background: transparent; border: none; }
QToolTip { background: @solid; color: @text; border: 1px solid @rand; border-radius: 6px; padding: 6px; }
QScrollBar:vertical { background: transparent; width: 6px; }
QListWidget#liste QScrollBar:vertical { width: 10px; margin: 2px 0 2px 4px; }
QScrollBar::handle:vertical { background: rgba(255,250,240,32); border-radius: 3px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: rgba(255,250,240,60); }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""


def qss() -> str:
    out = QSS
    for k in sorted(T, key=len, reverse=True):
        if isinstance(T[k], str):
            out = out.replace("@" + k, T[k])
    return out


def signal_farbe(signal: str) -> str:
    return {"KAUFEN": T["gruen"], "VERKAUFEN": T["rot"]}.get(signal, T["grau"])


def wert_farbe(x: float) -> str:
    return T["gruen"] if x > 0 else T["rot"] if x < 0 else T["grau"]


def pill_stil(farbe: str, gross: bool = False) -> str:
    c = QColor(farbe)
    pad, size = ("5px 14px", 12) if gross else ("2px 0px", 10)
    return (f"background: rgba({c.red()},{c.green()},{c.blue()},12); color: {farbe};"
            f"border: 1px solid rgba({c.red()},{c.green()},{c.blue()},38);"
            f"border-radius: {7 if gross else 5}px; padding: {pad};"
            f"font-size: {size}px; font-weight: 600; letter-spacing: 0.4px;")


# ------------------------------------------------------- Zahlenformat (DE)


def zahl(x: float, n: int = 2) -> str:
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def kurs_text(x: float) -> str:
    return zahl(x, 2 if abs(x) >= 1 else 4)


def differenz_text(x: float, bezug: float) -> str:
    """Kursdifferenz mit so vielen Nachkommastellen wie der Kurs selbst."""
    return zahl(abs(x), 2 if abs(bezug) >= 1 else 4)


def prozent(x: float, n: int = 1) -> str:
    return ("+" if x > 0 else "−" if x < 0 else "±") + zahl(abs(x) * 100, n) + " %"


def pfeil(x: float, n: int = 2, einheit: str = " %", faktor: float = 100) -> str:
    """Veränderung im Stil ▲ 1,42 % / ▼ 0,80 %."""
    zeichen = "▲" if x > 0 else "▼" if x < 0 else "■"
    return f"{zeichen} {zahl(abs(x) * faktor, n)}{einheit}"


def male_hintergrund(widget: QWidget) -> None:
    """Farbiger, weich verlaufender Hintergrund, auf dem die Glas-Panels liegen."""
    p = QPainter(widget)
    p.setRenderHint(QPainter.Antialiasing)
    r = widget.rect()
    p.fillRect(r, QColor(T["bg"]))
    groesse = max(r.width(), r.height())
    for farbe, fx, fy, radius in T["blobs"]:
        mitte = QPointF(r.width() * fx, r.height() * fy)
        g = QRadialGradient(mitte, groesse * radius)
        c = QColor(farbe)
        c.setAlpha(150 if T["bg"] == DUNKEL["bg"] else 170)
        g.setColorAt(0, c)
        c2 = QColor(farbe)
        c2.setAlpha(0)
        g.setColorAt(1, c2)
        p.fillRect(r, g)
    p.end()


def durchsichtig(canvas: FigureCanvasQTAgg) -> None:
    """matplotlib-Fläche ohne eigenen Hintergrund, damit das Glas-Panel durchscheint."""
    canvas.setAttribute(Qt.WA_OpaquePaintEvent, False)
    canvas.setAutoFillBackground(False)
    pal = canvas.palette()
    pal.setColor(QPalette.Window, QColor(0, 0, 0, 0))
    canvas.setPalette(pal)
    canvas.setStyleSheet("background: transparent;")


class GlasFlaeche(QWidget):
    """Fenster-Hintergrund mit Farbverlauf."""

    def paintEvent(self, _):
        male_hintergrund(self)


def blinken(widget: QLabel, farbe: str) -> None:
    """Färbt einen geänderten Kurs kurz grün/rot und blendet sanft zur Textfarbe zurück.
    Pro Feld gibt es genau eine Animation, die bei jedem neuen Kurs neu startet."""
    anim = getattr(widget, "_blink", None)
    if anim is None:
        anim = QVariantAnimation(widget)  # gehört zum Feld und verschwindet mit ihm
        anim.setDuration(900)
        anim.setEasingCurve(QEasingCurve.InQuad)
        anim.valueChanged.connect(lambda c: widget.setStyleSheet(f"color: {c.name()};"))
        anim.finished.connect(lambda: widget.setStyleSheet(""))
        widget._blink = anim
    anim.stop()
    anim.setStartValue(QColor(farbe))
    anim.setEndValue(QColor(T["text"]))
    anim.start()


def punkt(farbe: str, groesse: int = 10) -> QLabel:
    p = QLabel()
    p.setFixedSize(groesse, groesse)
    p.setStyleSheet(f"background: {farbe}; border-radius: {groesse // 2}px;")
    return p


class KuerzLabel(QLabel):
    """Einzeiliges Label, das zu lange Texte passend zur Breite mit … kürzt."""

    def __init__(self, rolle: str = ""):
        super().__init__()
        if rolle:
            self.setProperty("rolle", rolle)
        self._voll = ""
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    def setze(self, text: str) -> None:
        self._voll = text
        self._kuerzen()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._kuerzen()

    def _kuerzen(self) -> None:
        self.ensurePolished()
        super().setText(QFontMetrics(self.font()).elidedText(
            self._voll, Qt.ElideRight, max(40, self.width())))

    def minimumSizeHint(self):
        return QSize(80, super().minimumSizeHint().height())

    def sizeHint(self):
        h = super().sizeHint()
        return QSize(QFontMetrics(self.font()).horizontalAdvance(self._voll) + 4, h.height())


def kurzer_name(name: str) -> str:
    return nachrichten.ZUSAETZE.sub("", name).strip(" ,") or name


def kartenkopf(layout, titel: str, name: bool = True) -> QLabel:
    """Kopf eines Panels: ● Name (oben, klein) und darunter ein großer Titel."""
    if name:
        zeile = QHBoxLayout()
        zeile.setSpacing(8)
        p = punkt(T["grau"])
        p.setProperty("rolle", "kartenpunkt")
        n = label("", "kartenname")
        n.setProperty("kartenname", True)
        zeile.addWidget(p)
        zeile.addWidget(n)
        zeile.addStretch()
        layout.addLayout(zeile)
    t = label(titel, "kartentitel")
    layout.addWidget(t)
    return t


def label(text: str = "", rolle: str = "") -> QLabel:
    lbl = QLabel(text)
    if rolle:
        lbl.setProperty("rolle", rolle)
    return lbl


def karte() -> QFrame:
    f = QFrame()
    f.setObjectName("karte")
    return f


# ------------------------------------------------------ Hintergrund-Jobs

TYPEN = {"EQUITY": "Aktie", "ETF": "ETF", "CRYPTOCURRENCY": "Krypto", "INDEX": "Index",
         "FUTURE": "Future", "MUTUALFUND": "Fonds", "CURRENCY": "Währung"}
BOERSEN = {"NMS": "NASDAQ", "NYQ": "NYSE", "GER": "Xetra", "CCC": "Krypto", "PCX": "NYSE Arca"}


class _SucheSignale(QObject):
    fertig = Signal(str, list)


class Suche(QRunnable):
    """Fragt Yahoo Finance nach passenden Tickern zu einem Suchbegriff."""

    def __init__(self, begriff: str):
        super().__init__()
        self.begriff = begriff
        self.signale = _SucheSignale()

    def run(self) -> None:
        try:
            treffer = yf.Search(self.begriff, max_results=10, news_count=0).quotes
        except Exception:  # noqa: BLE001
            treffer = []
        vorschlaege = []
        for q in treffer:
            sym = q.get("symbol")
            if not sym:
                continue
            name = " ".join((q.get("shortname") or q.get("longname") or "").split())
            typ = TYPEN.get(q.get("quoteType", ""), q.get("quoteType", "").title())
            zusatz = " · ".join(x for x in (typ, q.get("exchDisp", "")) if x)
            vorschlaege.append((sym, f"{sym}   {name}   ·  {zusatz}"))
        self.signale.fertig.emit(self.begriff, vorschlaege)


def kurs_jetzt(d: dict) -> tuple[float, float, "pd.Timestamp | None"]:
    """Aktueller Kurs (live, falls vorhanden), Änderung zum Vortag, Zeit des Live-Kurses."""
    df = d["df"]
    live = d.get("live")
    if live:
        preis, zeit = live[0], live[1]
        if len(live) > 2 and live[2] is not None:  # Änderung direkt aus dem Live-Stream
            return preis, live[2], zeit
        tag = zeit.tz_convert(None).normalize()
        vorher = df["kurs"][df.index.normalize() < tag]
        vortag = float(vorher.iloc[-1]) if len(vorher) else float(df["kurs"].iloc[-2])
        return preis, preis / vortag - 1, zeit
    return float(df["kurs"].iloc[-1]), float(df["kurs"].iloc[-1] / df["kurs"].iloc[-2] - 1), None


class LiveStream:
    """Empfängt Kurse in Echtzeit über Yahoos WebSocket-Stream (läuft in einem eigenen
    Thread und verbindet sich bei Abbruch neu). Die Oberfläche holt sich die neuesten
    Kurse jede Sekunde mit abholen()."""

    def __init__(self):
        self._lock = threading.Lock()
        self._neu: dict[str, tuple] = {}
        self._tickers: set[str] = set()
        self._ws = None
        self.verbunden = False
        self.updates = 0
        threading.Thread(target=self._laufen, daemon=True).start()

    def abonnieren(self, tickers) -> None:
        neu = set(tickers) - self._tickers
        if not neu:
            return
        self._tickers |= neu
        ws = self._ws
        if ws is not None:
            try:
                ws.subscribe(sorted(neu))
            except Exception:  # noqa: BLE001
                pass

    def abholen(self) -> dict[str, tuple]:
        with self._lock:
            neu, self._neu = self._neu, {}
        return neu

    def _nachricht(self, m: dict) -> None:
        try:
            t, preis = m["id"], float(m["price"])
            zeit = pd.Timestamp(int(m["time"]), unit="ms", tz="UTC")
            ch = m.get("change_percent")
            ch = float(ch) / 100 if ch is not None else None
        except (KeyError, TypeError, ValueError):
            return
        with self._lock:
            self._neu[t] = (preis, zeit, ch)
            self.updates += 1

    def _laufen(self) -> None:
        while True:
            if not self._tickers:
                time.sleep(1)
                continue
            try:
                self._ws = yf.WebSocket(verbose=False)
                self._ws.subscribe(sorted(self._tickers))
                self.verbunden = True
                self._ws.listen(self._nachricht)
            except Exception:  # noqa: BLE001
                pass
            self.verbunden = False
            self._ws = None
            time.sleep(5)  # kurz warten, dann neu verbinden


class _LiveSignale(QObject):
    fertig = Signal(dict, dict)


class LiveJob(QRunnable):
    """Holt für alle Ticker auf einmal den letzten Minutenkurs."""

    def __init__(self, tickers: list[str]):
        super().__init__()
        self.tickers = tickers
        self.signale = _LiveSignale()

    def run(self) -> None:
        kurse, verlauf = {}, {}
        try:
            roh = yf.download(self.tickers, period="2d", interval="1m", progress=False,
                              auto_adjust=True, threads=True)
            close = roh["Close"]
            if isinstance(close, pd.Series):
                close = close.to_frame(self.tickers[0])
            for t in close.columns:
                spalte = close[t].dropna()
                if len(spalte):
                    kurse[str(t)] = (float(spalte.iloc[-1]), spalte.index[-1])
                    # Tagesverlauf des letzten Handelstags für die Mini-Charts
                    tag = spalte.index[-1].normalize()
                    heute = spalte[spalte.index >= tag]
                    if len(heute) >= 5:
                        schritt = max(1, len(heute) // 60)
                        verlauf[str(t)] = heute.iloc[::schritt].to_numpy(dtype=float).tolist()
        except Exception:  # noqa: BLE001
            pass
        try:
            self.signale.fertig.emit(kurse, verlauf)
        except RuntimeError:
            pass


class _NewsSignale(QObject):
    fertig = Signal(str, list)


class NewsJob(QRunnable):
    def __init__(self, ticker: str, name: str, typ: str):
        super().__init__()
        self.ticker, self.name, self.typ = ticker, name, typ
        self.signale = _NewsSignale()

    def run(self) -> None:
        artikel = nachrichten.hole(self.ticker, self.name, self.typ)
        try:
            self.signale.fertig.emit(self.ticker, artikel)
        except RuntimeError:
            pass


_WECHSELKURSE: dict[str, float] = {"EUR": 1.0}
_WECHSEL_LOCK = threading.Lock()


def eur_faktor(waehrung: str) -> float | None:
    """Faktor, um einen Kurs in Euro umzurechnen (z. B. USD -> EUR). Wird zwischengespeichert."""
    if not waehrung:
        return None
    teiler = 1.0
    if waehrung in ("GBp", "GBX", "ILA", "ZAc"):  # Kurse in Pence/Agorot/Cent
        waehrung, teiler = {"GBp": "GBP", "GBX": "GBP", "ILA": "ILS", "ZAc": "ZAR"}[waehrung], 100.0
    with _WECHSEL_LOCK:
        if waehrung in _WECHSELKURSE:
            return _WECHSELKURSE[waehrung] / teiler
    try:
        kurs = float(yf.Ticker(f"{waehrung}EUR=X").history(period="5d")["Close"].dropna().iloc[-1])
    except Exception:  # noqa: BLE001
        return None
    with _WECHSEL_LOCK:
        _WECHSELKURSE[waehrung] = kurs
    return kurs / teiler


LOGO_DATEI = pfade.ressource("vyntro-emblem.png")


def logo_pixmap(groesse: int) -> QPixmap:
    """Das Vyntro-Logo als scharfes Bild in der gewünschten Größe."""
    dpr = 2
    bild = QPixmap(str(LOGO_DATEI)).scaledToHeight(groesse * dpr, Qt.SmoothTransformation)
    bild.setDevicePixelRatio(dpr)
    return bild


class _LaderSignale(QObject):
    fertig = Signal(str, object)
    fehler = Signal(str, str)


CACHE = pfade.DATEN / "cache"


def cache_datei(ticker: str) -> "s.Path":
    return CACHE / (re.sub(r"[^A-Za-z0-9._-]", "_", ticker.upper()) + ".pkl")


def auswerten(ticker: str, roh: pd.DataFrame, info: dict, meta: dict, fx) -> dict:
    """Aus Rohkursen und Stammdaten alles berechnen, was die App anzeigt."""
    df = s.berechne_indikatoren(roh[["Close"]].rename(columns={"Close": "kurs"}).dropna())
    if df.empty:
        raise ValueError("zu wenig Historie für die Analyse")
    boerse = meta.get("exchangeName", "")
    return {
        "df": df,
        "bt": s.backteste(df),
        "begruendung": begruendung.erklaere(df, ticker),
        "kurse_voll": roh["Close"].dropna(),  # ohne 200-Tage-Anlaufzeit
        "ohlc": roh[["Open", "High", "Low", "Close"]].dropna(),
        "volumen": roh["Volume"].fillna(0) if "Volume" in roh else None,
        "verzoegerung": int(info.get("exchangeDataDelayedBy") or 0),
        "prognose": prognose.erstelle(df, info),
        "info": info,
        "name": " ".join((meta.get("longName") or meta.get("shortName") or ticker).split()),
        "waehrung": meta.get("currency", ""),
        "eur_faktor": fx,
        "typ": TYPEN.get(meta.get("instrumentType", ""), ""),
        "boerse": BOERSEN.get(boerse, boerse),
    }


class Lader(QRunnable):
    """Lädt Kurse + Stammdaten, berechnet Indikatoren und Backtest. Mit nur_cache=True
    werden nur die zuletzt gespeicherten Daten von der Festplatte gelesen (schneller Start,
    funktioniert auch ohne Internet)."""

    def __init__(self, ticker: str, nur_cache: bool = False):
        super().__init__()
        self.ticker = ticker
        self.nur_cache = nur_cache
        self.signale = _LaderSignale()

    def run(self) -> None:
        if self.nur_cache:
            try:
                with open(cache_datei(self.ticker), "rb") as f:
                    c = pickle.load(f)
                d = auswerten(self.ticker, c["roh"], c["info"], c["meta"], c["fx"])
                d["aus_cache"] = c["zeit"]
                self.signale.fertig.emit(self.ticker, d)
            except Exception:  # noqa: BLE001 – kein oder kaputter Zwischenspeicher
                pass
            return
        try:
            tk = yf.Ticker(self.ticker)
            roh = tk.history(period=f"{JAHRE}y", interval="1d", auto_adjust=True)
            if roh.empty:
                raise ValueError("keine Kursdaten gefunden")
            roh.index = roh.index.tz_localize(None)
            meta = tk.history_metadata or {}
            try:  # Stammdaten, Kennzahlen und (bei Aktien) Analystenziele
                info = tk.info or {}
            except Exception:  # noqa: BLE001
                info = {}
            fx = eur_faktor(meta.get("currency", ""))
            d = auswerten(self.ticker, roh, info, meta, fx)
            try:
                CACHE.mkdir(exist_ok=True)
                tmp = cache_datei(self.ticker).with_suffix(".tmp")
                with open(tmp, "wb") as f:
                    pickle.dump({"roh": roh, "info": info, "meta": dict(meta), "fx": fx,
                                 "zeit": time.time()}, f)
                tmp.replace(cache_datei(self.ticker))
            except Exception:  # noqa: BLE001
                pass
            self.signale.fertig.emit(self.ticker, d)
        except RuntimeError:
            pass  # App wurde während des Ladens geschlossen
        except Exception as e:  # noqa: BLE001
            try:
                self.signale.fehler.emit(self.ticker, str(e))
            except RuntimeError:
                pass


# ---------------------------------------------------------- Watchlist-Zeile


# ----------------------------------------------------------------- Icons
# Eigene, schlichte Linien-Icons (24er-Raster), statt Emojis und Sonderzeichen.

ICON_FORMEN = {
    "stern": '<path d="M12 3.6l2.55 5.2 5.75.84-4.16 4.05.98 5.72L12 16.7l-5.12 2.7.98-5.72'
             '-4.16-4.05 5.75-.84z"/>',
    "glocke": '<path d="M6.5 16.5V11a5.5 5.5 0 0 1 11 0v5.5l1.6 1.6H4.9z"/>'
              '<path d="M10 20.6a2.3 2.3 0 0 0 4 0"/>',
    "regler": '<path d="M4 7h9M17.5 7H20M4 17h2.5M11 17h9"/>'
              '<circle cx="15.2" cy="7" r="2.2"/><circle cx="8.8" cy="17" r="2.2"/>',
    "neu": '<path d="M19.6 12.2a7.6 7.6 0 1 1-2.3-5.6"/><path d="M19.6 4.4v4.2h-4.2"/>',
    "plus": '<path d="M12 5.5v13M5.5 12h13"/>',
    "x": '<path d="M7 7l10 10M17 7L7 17"/>',
    "runter": '<path d="M7.5 10l4.5 4.5 4.5-4.5"/>',
    "depot": '<rect x="3.5" y="6.5" width="17" height="12.5" rx="2.6"/>'
             '<path d="M7 6.5V5.6A1.6 1.6 0 0 1 8.6 4h8.2"/><path d="M15.5 12.8h2"/>',
    "trend": '<path d="M3.5 16.5l5.4-5.4 4 4 7.3-7.3"/><path d="M15 7.8h5.2V13"/>',
    "preis": '<path d="M3.8 12.4V4.8a1 1 0 0 1 1-1h7.6l8 8-8.6 8.6z"/>'
             '<circle cx="8.3" cy="8.3" r="1.3"/>',
    "export": '<path d="M12 4v11"/><path d="M7.5 8.5L12 4l4.5 4.5"/>'
              '<path d="M5 14.5v3.3A2.2 2.2 0 0 0 7.2 20h9.6a2.2 2.2 0 0 0 2.2-2.2v-3.3"/>',
    "raster": '<rect x="4" y="4" width="7" height="7" rx="1.6"/><rect x="13" y="4" width="7" '
              'height="7" rx="1.6"/><rect x="4" y="13" width="7" height="7" rx="1.6"/>'
              '<rect x="13" y="13" width="7" height="7" rx="1.6"/>',
    "suche": '<circle cx="10.8" cy="10.8" r="6.3"/><path d="M15.5 15.5L20 20"/>',
    "haus": '<path d="M4 10.8L12 4.5l8 6.3V19a1.2 1.2 0 0 1-1.2 1.2H15v-5.4h-6v5.4H5.2A1.2 1.2 0 0 1 4 19z"/>',
    "import": '<path d="M12 4v11"/><path d="M7.5 10.5L12 15l4.5-4.5"/>'
              '<path d="M5 14.5v3.3A2.2 2.2 0 0 0 7.2 20h9.6a2.2 2.2 0 0 0 2.2-2.2v-3.3"/>',
    "buch": '<path d="M4.5 5.5A1.5 1.5 0 0 1 6 4h5v15H6a1.5 1.5 0 0 0-1.5 1.5z"/>'
            '<path d="M19.5 5.5A1.5 1.5 0 0 0 18 4h-5v15h5a1.5 1.5 0 0 1 1.5 1.5z"/>'
            '<path d="M4.5 20.5V5.5M19.5 20.5V5.5"/>',
    "funke": '<path d="M12 3.5c.6 4.3 2.2 5.9 6.5 6.5-4.3.6-5.9 2.2-6.5 6.5-.6-4.3-2.2-5.9'
             '-6.5-6.5 4.3-.6 5.9-2.2 6.5-6.5z"/><path d="M18.5 15.5v4M16.5 17.5h4"/>',
}


def icon_bild(name: str, farbe: str, groesse: int = 16, gefuellt: bool = False,
              strich: float = 1.7) -> QPixmap:
    form = ICON_FORMEN[name]
    fuellung = farbe if gefuellt else "none"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{fuellung}" '
           f'stroke="{farbe}" stroke-width="{strich}" stroke-linecap="round" '
           f'stroke-linejoin="round">{form}</svg>')
    dpr = 2
    bild = QPixmap(groesse * dpr, groesse * dpr)
    bild.fill(Qt.transparent)
    p = QPainter(bild)
    p.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(QByteArray(svg.encode())).render(p)
    p.end()
    bild.setDevicePixelRatio(dpr)
    return bild


def icon(name: str, farbe: str | None = None, groesse: int = 16, gefuellt: bool = False,
         aktiv_farbe: str | None = None) -> QIcon:
    """QIcon in Textfarbe; optional andere Farbe im gedrückten/aktiven Zustand."""
    farbe = farbe or T["text"]
    ic = QIcon()
    ic.addPixmap(icon_bild(name, farbe, groesse, gefuellt), QIcon.Normal, QIcon.Off)
    if aktiv_farbe:
        ic.addPixmap(icon_bild(name, aktiv_farbe, groesse, gefuellt), QIcon.Normal, QIcon.On)
    ic.addPixmap(icon_bild(name, T["leise"], groesse, gefuellt), QIcon.Disabled, QIcon.Off)
    return ic


def icon_label(name: str, farbe: str | None = None, groesse: int = 16,
               gefuellt: bool = False) -> QLabel:
    l_ = QLabel()
    l_.setPixmap(icon_bild(name, farbe or T["text"], groesse, gefuellt))
    l_.setFixedSize(groesse, groesse)
    return l_


def icon_knopf(name: str, tooltip: str = "", groesse: int = 16,
               objekt: str = "icon") -> QPushButton:
    b = QPushButton(objectName=objekt)
    b.setIcon(icon(name, T["leise"] if objekt == "icon" else None, groesse))
    b.setIconSize(QSize(groesse, groesse))
    b.setCursor(Qt.PointingHandCursor)
    if tooltip:
        b.setToolTip(tooltip)
    return b


def mit_pfeil(knopf: QPushButton) -> QPushButton:
    """Kleiner Pfeil nach unten rechts neben dem Text (für Auswahlmenüs)."""
    knopf.setIcon(icon("runter", T["leise"], 14))
    knopf.setIconSize(QSize(13, 13))
    knopf.setLayoutDirection(Qt.RightToLeft)
    return knopf


def stern_stil(gemerkt: bool, gross: bool = False) -> str:
    farbe = SILBER if gemerkt else T["leise"]
    return (f"QPushButton {{ background: transparent; border: none; color: {farbe};"
            f" font-size: {20 if gross else 17}px; padding: 0; }}"
            f"QPushButton:hover {{ color: {SILBER}; }}")


class Abschnitt(QWidget):
    """Überschrift in der Watchlist (nicht auswählbar)."""

    def __init__(self, titel: str, hinweis: str = "", farbe: str = "", symbol: str = "",
                 symbol_farbe: str = ""):
        super().__init__()
        self.setObjectName("zeile")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 12, 6, 2)
        lay.setSpacing(8)
        if symbol:
            lay.addWidget(icon_label(symbol, symbol_farbe or T["text"], 15,
                                     gefuellt=symbol == "stern"))
        kopf = label(titel, "h2")
        if farbe:
            kopf.setStyleSheet(f"color: {farbe};")
        lay.addWidget(kopf)
        lay.addStretch()
        if hinweis:
            lay.addWidget(label(hinweis, "klein"))


# ----------------------------------------------------------------- Logos

LOGOS: dict[str, "QPixmap | None"] = {}  # None = es gibt kein Logo


def rund(logo: QPixmap, groesse: int) -> QPixmap:
    """Logo zentriert auf einem weißen Kreis (wie App-Icons in Broker-Apps)."""
    dpr = 2
    bild = QPixmap(groesse * dpr, groesse * dpr)
    bild.fill(Qt.transparent)
    p = QPainter(bild)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#ffffff"))
    p.drawEllipse(0, 0, groesse * dpr, groesse * dpr)
    innen = int(groesse * dpr * 0.68)
    skaliert = logo.scaled(innen, innen, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    p.drawPixmap((groesse * dpr - skaliert.width()) // 2,
                 (groesse * dpr - skaliert.height()) // 2, skaliert)
    p.end()
    bild.setDevicePixelRatio(dpr)
    return bild


class _LogoSignale(QObject):
    fertig = Signal(str, object)


class LogoJob(QRunnable):
    def __init__(self, ticker: str):
        super().__init__()
        self.ticker = ticker
        self.signale = _LogoSignale()

    def run(self) -> None:
        try:
            daten = logos.hole(self.ticker)
        except Exception:  # noqa: BLE001
            daten = None
        try:
            self.signale.fertig.emit(self.ticker, daten)
        except RuntimeError:
            pass


class LogoDienst(QObject):
    """Lädt Logos im Hintergrund und meldet, wenn eines da ist."""
    geladen = Signal(str)

    def __init__(self):
        super().__init__()
        self.ladend: set[str] = set()

    def anfordern(self, ticker: str) -> None:
        if not ticker or ticker in LOGOS or ticker in self.ladend:
            return
        self.ladend.add(ticker)
        job = LogoJob(ticker)
        job.signale.fertig.connect(self._da)
        QThreadPool.globalInstance().start(job)

    def _da(self, ticker: str, daten) -> None:
        self.ladend.discard(ticker)
        pix = QPixmap()
        LOGOS[ticker] = pix if daten and pix.loadFromData(daten) else None
        self.geladen.emit(ticker)


LOGO_DIENST: "LogoDienst | None" = None


def avatar_fuellen(a: QLabel) -> None:
    """Zeigt das Logo, sonst einen runden Platzhalter mit Kürzel."""
    ticker, groesse = a.property("avatar_ticker") or "", a.property("avatar_groesse") or 36
    logo = LOGOS.get(ticker)
    if logo is not None:
        a.setText("")
        a.setStyleSheet("background: transparent;")
        a.setPixmap(rund(logo, groesse))
        return
    if ticker not in LOGOS and LOGO_DIENST is not None:
        LOGO_DIENST.anfordern(ticker)
    kuerzel = re.sub(r"[-.].*$", "", ticker)[:3]
    farbton = sum(ord(c) * (i + 1) for i, c in enumerate(ticker)) % 360
    c = QColor.fromHsl(farbton, 110, 78)
    a.setPixmap(QPixmap())
    a.setText(kuerzel)
    a.setStyleSheet(f"background: {c.name()}; border-radius: {groesse // 2}px; color: white;"
                    f" font-size: {max(9, groesse // 3 - 1)}px; font-weight: 600;")


def logo_icon(ticker: str, groesse: int = 28) -> QIcon:
    """Icon für Listen: Logo, sonst Kreis mit Kürzel."""
    logo = LOGOS.get(ticker)
    if logo is not None:
        return QIcon(rund(logo, groesse))
    dpr = 2
    bild = QPixmap(groesse * dpr, groesse * dpr)
    bild.fill(Qt.transparent)
    p = QPainter(bild)
    p.setRenderHint(QPainter.Antialiasing)
    farbton = sum(ord(c) * (i + 1) for i, c in enumerate(ticker)) % 360
    p.setPen(Qt.NoPen)
    p.setBrush(QColor.fromHsl(farbton, 110, 78))
    p.drawEllipse(0, 0, groesse * dpr, groesse * dpr)
    p.setPen(QColor("white"))
    schrift = p.font()
    schrift.setBold(True)
    schrift.setPixelSize(int(groesse * dpr * 0.32))
    p.setFont(schrift)
    p.drawText(bild.rect(), Qt.AlignCenter, re.sub(r"[-.].*$", "", ticker)[:3])
    p.end()
    bild.setDevicePixelRatio(dpr)
    return QIcon(bild)


def avatar(ticker: str, groesse: int = 36) -> QLabel:
    a = QLabel()
    a.setFixedSize(groesse, groesse)
    a.setAlignment(Qt.AlignCenter)
    a.setProperty("avatar_ticker", ticker)
    a.setProperty("avatar_groesse", groesse)
    avatar_fuellen(a)
    return a


class Sparkline(QWidget):
    """Kleiner Kursverlauf (heute, sonst letzter Monat) in einer Watchlist-Zeile."""

    def __init__(self, breite: int = 54, hoehe: int = 26):
        super().__init__()
        self.setFixedSize(breite, hoehe)
        self.werte: list[float] = []
        self.farbe = T["leise"]
        self.bezug: float | None = None

    def setze(self, werte, farbe: str, bezug: float | None = None, tipp: str = "") -> None:
        self.werte, self.farbe, self.bezug = list(werte or []), farbe, bezug
        self.setToolTip(tipp)
        self.update()

    def paintEvent(self, _e):
        w = self.werte
        if len(w) < 2:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        unten, oben = min(w), max(w)
        if self.bezug is not None:
            unten, oben = min(unten, self.bezug), max(oben, self.bezug)
        spanne = (oben - unten) or 1
        rand = 2
        b, h = self.width() - 2 * rand, self.height() - 2 * rand

        def punkt_(i, v):
            return QPointF(rand + b * i / (len(w) - 1), rand + h * (1 - (v - unten) / spanne))
        if self.bezug is not None:  # gepunktete Linie: Schlusskurs Vortag
            y = punkt_(0, self.bezug).y()
            stift = QPen(QColor(T["leise"]), 0.8, Qt.DotLine)
            p.setPen(stift)
            p.drawLine(QPointF(rand, y), QPointF(rand + b, y))
        pfad = QPainterPath()
        pfad.moveTo(punkt_(0, w[0]))
        for i, v in enumerate(w[1:], start=1):
            pfad.lineTo(punkt_(i, v))
        flaeche = QPainterPath(pfad)
        flaeche.lineTo(QPointF(rand + b, rand + h))
        flaeche.lineTo(QPointF(rand, rand + h))
        flaeche.closeSubpath()
        c = QColor(self.farbe)
        verlauf = QLinearGradient(0, rand, 0, rand + h)
        c.setAlpha(55)
        verlauf.setColorAt(0, c)
        c.setAlpha(0)
        verlauf.setColorAt(1, c)
        p.fillPath(flaeche, verlauf)
        p.setPen(QPen(QColor(self.farbe), 1.3))
        p.drawPath(pfad)
        p.end()


class Zeile(QWidget):
    stern_geklickt = Signal(str)

    def __init__(self, ticker: str, gemerkt: bool, in_euro: bool = False):
        super().__init__()
        self.setObjectName("zeile")
        self.ticker = ticker
        self.gemerkt = gemerkt
        self.in_euro = in_euro
        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 8, 10, 8)
        lay.setSpacing(10)

        self.stern = QPushButton()
        self.stern.setIcon(icon("stern", SILBER if gemerkt else T["leise"], 17, gefuellt=gemerkt))
        self.stern.setIconSize(QSize(17, 17))
        self.stern.setFixedSize(26, 28)
        self.stern.setCursor(Qt.PointingHandCursor)
        self.stern.setToolTip("Nicht mehr merken" if gemerkt else "Zu „Meine“ hinzufügen")
        self.stern.clicked.connect(lambda: self.stern_geklickt.emit(self.ticker))
        lay.addWidget(avatar(ticker))

        links = QVBoxLayout()
        links.setSpacing(1)
        self.l_ticker = label(ticker, "zticker")
        self.l_name = label("lädt …", "klein")
        links.addWidget(self.l_ticker)
        links.addWidget(self.l_name)

        self.spark = Sparkline()
        mitte = QVBoxLayout()
        mitte.setSpacing(1)
        self.l_kurs = label("", "zkurs")
        self.l_change = label("", "klein")
        for w in (self.l_kurs, self.l_change):
            w.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            mitte.addWidget(w)

        self.pill = QLabel()
        self.pill.setFixedSize(68, 22)
        self.pill.setAlignment(Qt.AlignCenter)

        lay.addLayout(links, 1)
        lay.addWidget(self.spark)
        lay.addLayout(mitte)
        lay.addWidget(self.pill)
        lay.addWidget(self.stern)
        self.daten = None
        self.fehler = ""

    def setze(self, daten=None, fehler: str = "") -> None:
        self.daten, self.fehler = daten, fehler
        self.aktualisiere()

    def aktualisiere(self) -> None:
        self.stern.setStyleSheet("QPushButton { background: transparent; border: none; }"
                                 f"QPushButton:hover {{ background: {T['feld']}; "
                                 "border-radius: 6px; }")
        fm = QFontMetrics(self.l_name.font())
        if self.fehler:
            self.l_name.setText("nicht gefunden")
            self.l_name.setToolTip(self.fehler)
            self.l_kurs.setText("")
            self.l_change.setText("")
            self.pill.setText("FEHLER")
            self.pill.setStyleSheet(pill_stil(T["grau"]))
            return
        if not self.daten:
            self.pill.setText("…")
            self.pill.setStyleSheet(pill_stil(T["grau"]))
            return
        df = self.daten["df"]
        self.l_name.setText(fm.elidedText(self.daten["name"], Qt.ElideRight, 104))
        self.l_name.setToolTip(self.daten["name"])
        preis, ch, _ = kurs_jetzt(self.daten)
        alt = getattr(self, "_letzter_preis", None)
        self._letzter_preis = preis
        if self.in_euro and self.daten.get("eur_faktor"):
            self.l_kurs.setText(f"{kurs_text(preis * self.daten['eur_faktor'])} €")
            self.l_kurs.setToolTip(f"{kurs_text(preis)} {self.daten['waehrung']}, "
                                   "in Euro umgerechnet")
        else:
            self.l_kurs.setText(kurs_text(preis))
        if alt is not None and preis != alt:
            blinken(self.l_kurs, T["gruen"] if preis > alt else T["rot"])
        self.l_change.setText(pfeil(ch))
        self.l_change.setStyleSheet(f"color: {wert_farbe(ch)}; font-weight: 500;")
        heute = self.daten.get("spark")
        if heute:
            werte = heute + [preis]
            self.spark.setze(werte, wert_farbe(ch), preis / (1 + ch), "Verlauf heute")
        else:
            monat = df["kurs"].iloc[-22:].tolist()
            self.spark.setze(monat, wert_farbe(monat[-1] - monat[0]), None,
                             "Verlauf letzter Monat")
        sig = s.empfehlung(int(df["score"].iloc[-1]))
        self.pill.setText(sig)
        self.pill.setStyleSheet(pill_stil(signal_farbe(sig)))
        b = self.daten["begruendung"]
        self.pill.setToolTip(b.kurz + "".join(f"\n• {p.text}" for p in b.gruende))


# ------------------------------------------------------------------ Chart

ZEITRAEUME = [("1T", "T"), ("1W", "W"), ("1M", 1), ("3M", 3), ("6M", 6), ("1J", 12),
              ("3J", 36), ("Max", None)]
INTRADAY = {"T": ("1d", "2m"), "W": ("5d", "15m")}  # Zeitraum, Kerzenabstand bei Yahoo


class _IntradaySignale(QObject):
    fertig = Signal(str, str, object)


class IntradayJob(QRunnable):
    """Kursverlauf des letzten Handelstags (1T) bzw. der letzten fünf Handelstage (1W)."""

    def __init__(self, ticker: str, art: str):
        super().__init__()
        self.ticker, self.art = ticker, art
        self.signale = _IntradaySignale()

    def run(self) -> None:
        ergebnis = None
        try:
            tk = yf.Ticker(self.ticker)
            zeitraum, abstand = INTRADAY[self.art]
            roh = tk.history(period=zeitraum, interval=abstand, auto_adjust=True)
            kurse = roh["Close"].dropna()
            if len(kurse) >= 2:
                lokal = datetime.now().astimezone().tzinfo
                kurse.index = kurse.index.tz_convert(lokal).tz_localize(None)
                meta = tk.history_metadata or {}
                if self.art == "T":
                    referenz = meta.get("chartPreviousClose") or meta.get("previousClose")
                else:
                    referenz = None
                ergebnis = {"kurse": kurse, "referenz": float(referenz or kurse.iloc[0]),
                            "zeit": time.time()}
        except Exception:  # noqa: BLE001
            ergebnis = None
        try:
            self.signale.fertig.emit(self.ticker, self.art, ergebnis)
        except RuntimeError:
            pass


class Chart(FigureCanvasQTAgg):
    def __init__(self):
        self.fig = Figure(figsize=(7, 4))
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(430)
        durchsichtig(self)
        self._fk = None  # Fadenkreuz: Daten und Zeichenobjekte
        self._hintergrund = None
        self.mpl_connect("draw_event", self._gezeichnet)
        self.mpl_connect("motion_notify_event", self._maus)
        self.mpl_connect("figure_leave_event", lambda _: self._fk_aus())

    # --- Fadenkreuz (folgt der Maus, zeigt Datum und Kurs am nächsten Punkt)

    def _fk_einrichten(self, ax, achsen, xs, ys, texte, erster, waehrung, zukunft=None,
                       nur_text: bool = False) -> None:
        stil = dict(color=T["leise"], lw=0.8, ls=(0, (3, 3)), animated=True, visible=False)
        linien = [a.axvline(xs[0], **stil) for a in achsen]
        quer = ax.axhline(ys[0], **stil)
        punkt_ = ax.plot([xs[0]], [ys[0]], "o", ms=7, color=GOLD, mec=T["markerrand"], mew=1.5,
                         animated=True, visible=False, zorder=12)[0]
        schild = ax.text(xs[0], 1.0, "", transform=ax.get_xaxis_transform(), fontsize=9,
                         color=T["text"], va="bottom", ha="center", animated=True,
                         visible=False, zorder=13, fontweight="medium",
                         bbox=dict(boxstyle="round,pad=0.45,rounding_size=0.25", fc=T["solid"],
                                   ec=T["gitter"], lw=1))
        # Wert an der Mausposition rechts an der Kursachse
        y_schild = ax.text(1.0, ys[0], "", transform=ax.get_yaxis_transform(), fontsize=8.5,
                           color="#050505", va="center", ha="left", animated=True,
                           visible=False, zorder=14, fontweight="medium", clip_on=False,
                           bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.2", fc=T["text"],
                                     ec="none"))
        self._fk = dict(ax=ax, achsen=achsen, xs=np.asarray(xs, dtype=float),
                        ys=list(ys), texte=list(texte), erster=erster, waehrung=waehrung,
                        zukunft=zukunft, nur_text=nur_text,
                        artists=linien + [quer, punkt_, schild, y_schild],
                        linien=linien, quer=quer, punkt=punkt_, schild=schild,
                        y_schild=y_schild)

    def _gezeichnet(self, _event) -> None:
        self._hintergrund = self.copy_from_bbox(self.fig.bbox)

    def _fk_aus(self) -> None:
        if not self._fk or not self._fk["schild"].get_visible():
            return
        for a in self._fk["artists"]:
            a.set_visible(False)
        if self._hintergrund is not None:
            self.restore_region(self._hintergrund)
            self.blit(self.fig.bbox)

    def _maus(self, e) -> None:
        fk = self._fk
        if not fk or e.inaxes not in fk["achsen"] or e.xdata is None:
            self._fk_aus()
            return
        xs = fk["xs"]
        ax = fk["ax"]
        # Mausposition in Koordinaten des Kurs-Charts (auch über RSI- oder Volumen-Achse)
        maus_x, maus_y = ax.transData.inverted().transform((e.x, e.y))
        im_kurs = ax.bbox.contains(e.x, e.y)
        if fk["zukunft"] and e.xdata > xs[-1]:
            x, y, txt = fk["zukunft"](e.xdata)
            if y is None:
                self._fk_aus()
                return
        else:
            i = int(np.clip(np.searchsorted(xs, e.xdata), 1, len(xs) - 1))
            i = i - 1 if e.xdata - xs[i - 1] < xs[i] - e.xdata else i
            x, y = xs[i], fk["ys"][i]
            txt = fk["texte"][i] if fk["nur_text"] else (
                f"{fk['texte'][i]}   {kurs_text(y)} {fk['waehrung']}   "
                f"{prozent(y / fk['erster'] - 1, 2)}")
        # Kreuz genau an der Maus; der Punkt markiert den nächsten Kurs auf der Linie
        for l in fk["linien"]:
            l.set_xdata([maus_x, maus_x])
        fk["quer"].set_ydata([maus_y, maus_y])
        fk["y_schild"].set_position((1.0, maus_y))
        fk["y_schild"].set_text(" " + ax.yaxis.get_major_formatter()(maus_y))
        fk["punkt"].set_data([x], [y])
        links, rechts = ax.get_xlim()
        anteil = (maus_x - links) / (rechts - links)
        fk["schild"].set_position((maus_x, 1.0))
        fk["schild"].set_ha("left" if anteil < 0.15 else "right" if anteil > 0.85 else "center")
        fk["schild"].set_text(txt)
        if self._hintergrund is None:
            return
        self.restore_region(self._hintergrund)
        for a in fk["artists"]:
            a.set_visible(im_kurs or a not in (fk["quer"], fk["y_schild"]))
            if a.get_visible():
                a.axes.draw_artist(a)
        self.blit(self.fig.bbox)

    def leer(self, text: str) -> None:
        self._fk = None
        self.fig.clear()
        self.fig.text(0.5, 0.5, text, ha="center", va="center", color=T["leise"], fontsize=11)
        self.draw_idle()

    def zeichne_intraday(self, daten, iv: dict, art: str) -> None:
        """Linienchart für 1T/1W. Die x-Achse zählt Messpunkte, damit Nächte und
        Wochenenden keine Lücken erzeugen."""
        kurse = iv["kurse"]
        preis, _, _ = kurs_jetzt(daten)
        referenz = iv["referenz"]
        ys = kurse.to_numpy(dtype=float)
        xs = np.arange(len(ys), dtype=float)
        letzter = float(ys[-1])
        farbe = wert_farbe(letzter - referenz)
        self._fk = None
        self.fig.clear()
        self.fig.set_facecolor(T["chart"])
        ax = self.fig.subplots()
        self.fig.subplots_adjust(left=0.005, right=0.90, top=0.93, bottom=0.07)
        ax.set_facecolor(T["chart"])
        ax.tick_params(colors=T["leise"], labelsize=9, length=0, pad=8)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.yaxis.tick_right()
        ax.grid(color=T["gitter"], lw=0.8)

        ax.plot(xs, ys, color=farbe, lw=1.8, zorder=4, solid_joinstyle="round")
        unten, oben = min(ys.min(), referenz), max(ys.max(), referenz)
        spiel = (oben - unten) * 0.08 or abs(oben) * 0.01
        boden = unten - spiel
        ax.fill_between(xs, ys, boden, color=farbe, alpha=0.08, lw=0, zorder=2)
        ax.axhline(referenz, color=T["leise"], lw=1, ls=(0, (1, 2.5)), zorder=3)
        ax.text(0, referenz, ("Vortag " if art == "T" else "Start ") + kurs_text(referenz),
                color=T["leise"], fontsize=7.5, va="bottom", ha="left")
        ax.set_ylim(boden, oben + spiel)
        ax.set_xlim(0, len(xs) - 1 + max(1, len(xs) * 0.02))
        nk = 0 if oben >= 1000 else 2 if oben >= 1 else 4
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: zahl(v, nk)))
        ax.annotate(kurs_text(letzter), xy=(1, letzter), xycoords=("axes fraction", "data"),
                    xytext=(6, 0), textcoords="offset points", va="center", ha="left",
                    fontsize=9, fontweight="medium",
                    color="#0a0a0a" if farbe == T["gruen"] else "white",
                    bbox=dict(boxstyle="round,pad=0.35,rounding_size=0.2", fc=farbe, ec="none"),
                    annotation_clip=False, zorder=10)
        ax.text(0.01, 0.97, f"{'+' if letzter >= referenz else '−'}"
                f"{differenz_text(letzter - referenz, referenz)} ({prozent(letzter / referenz - 1, 2)})"
                f"  {'seit Vortag' if art == 'T' else 'in 5 Handelstagen'}",
                transform=ax.transAxes, color=farbe, fontsize=9.5, fontweight="medium",
                va="top")

        zeiten = kurse.index
        if art == "T":
            marken = [i for i in range(len(zeiten))
                      if i > 0 and zeiten[i].hour != zeiten[i - 1].hour]
            schritt = max(1, len(marken) // 7)
            marken = marken[::schritt]
            ax.set_xticks(marken, [f"{zeiten[i]:%H:%M}" for i in marken])
            texte = [f"{z:%H:%M}" for z in zeiten]
        else:
            tage = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
            marken = [i for i in range(len(zeiten))
                      if i > 0 and zeiten[i].date() != zeiten[i - 1].date()]
            ax.set_xticks(marken, [f"{tage[zeiten[i].weekday()]} {zeiten[i]:%d.%m.}"
                                   for i in marken])
            for m in marken:
                ax.axvline(m, color=T["gitter"], lw=0.8, zorder=1)
            texte = [f"{tage[z.weekday()]} {z:%d.%m. %H:%M}" for z in zeiten]
        self._fk_einrichten(ax, [ax], xs, ys, texte, referenz, daten["waehrung"])
        self.draw_idle()

    @staticmethod
    def _kerzen(ohlc: pd.DataFrame) -> pd.DataFrame:
        """Bei vielen Tagen zu Wochenkerzen zusammenfassen, damit sie lesbar bleiben."""
        if len(ohlc) <= 300:
            return ohlc
        return ohlc.resample("W-FRI").agg(
            {"Open": "first", "High": "max", "Low": "min", "Close": "last"}).dropna()

    def zeichne_vergleich(self, daten, andere: list, monate, ticker: str) -> None:
        """Mehrere Werte prozentual vom selben Startpunkt aus (Tagesschlusskurse)."""
        reihen = [(ticker, daten)] + andere
        ende = daten["df"].index[-1]
        grenze = ende - pd.DateOffset(months=monate) if monate else None
        self._fk = None
        self.fig.clear()
        self.fig.set_facecolor(T["chart"])
        ax = self.fig.subplots()
        self.fig.subplots_adjust(left=0.005, right=0.90, top=0.93, bottom=0.07)
        ax.set_facecolor(T["chart"])
        ax.tick_params(colors=T["leise"], labelsize=9, length=0, pad=8)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.yaxis.tick_right()
        ax.grid(color=T["gitter"], lw=0.8)
        farben = [GOLD, SILBER, "#8a9592", "#5d7f95"]
        kurven = [(t, d["kurse_voll"]) for t, d in reihen if d.get("kurse_voll") is not None]
        start = max(k.index[0] for _, k in kurven)
        if grenze is not None:
            start = max(start, grenze)
        haupt = None
        etiketten = []
        for i, (t, k) in enumerate(kurven):
            k = k[k.index >= start]
            if len(k) < 2:
                continue
            p = (k / float(k.iloc[0]) - 1) * 100
            ax.plot(p.index, p.values, color=farben[i % 4], lw=2.0 if i == 0 else 1.5, zorder=5 - i)
            etiketten.append((float(p.iloc[-1]), t, farben[i % 4]))
            if i == 0:
                haupt = p
        unten_, oben_ = ax.get_ylim()
        abstand = (oben_ - unten_) * 0.07
        etiketten.sort()
        letzte = None
        for wert, t, farbe in etiketten:
            y = wert if letzte is None else max(wert, letzte + abstand)
            letzte = y
            ax.annotate(f"{t}  {prozent(wert / 100, 1)}", xy=(1, y),
                        xycoords=("axes fraction", "data"), xytext=(6, 0),
                        textcoords="offset points", va="center", fontsize=8.5,
                        fontweight="medium", color="#0a0a0a",
                        bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.2",
                                  fc=farbe, ec="none"), annotation_clip=False)
        ax.axhline(0, color=T["leise"], lw=0.9, ls=(0, (1, 2.5)))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{zahl(v, 0)} %"))
        ax.text(0.01, 0.97, f"Vergleich seit {start:%d.%m.%Y} · Veränderung in %",
                transform=ax.transAxes, color=T["leise"], fontsize=9.5, va="top")
        loc = mdates.AutoDateLocator(minticks=4, maxticks=8)
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(
            loc, show_offset=False, formats=["%Y", "%b", "%d.%m.", "%H:%M", "%H:%M", "%S"]))
        if haupt is not None:
            werte = {t: (k[k.index >= start] / float(k[k.index >= start].iloc[0]) - 1)
                     for t, k in kurven if len(k[k.index >= start]) >= 2}
            texte = []
            for d in haupt.index:
                teile = [f"{d:%d.%m.%Y}"]
                for t, w in werte.items():
                    v = w.asof(d)
                    if v == v:
                        teile.append(f"{t} {prozent(v, 1)}")
                texte.append("   ".join(teile))
            self._fk_einrichten(ax, [ax], mdates.date2num(haupt.index.to_pydatetime()),
                                haupt.to_numpy(dtype=float), texte, 1, "", nur_text=True)
        self.draw_idle()

    def zeichne(self, daten, monate, extras: set | None = None) -> None:
        extras = extras or set()
        df, bt = daten["df"], daten["bt"]
        ohlc = daten.get("ohlc")
        if monate:
            grenze = df.index[-1] - pd.DateOffset(months=monate)
            df = df[df.index >= grenze]
            if ohlc is not None:
                ohlc = ohlc[ohlc.index >= grenze]
        else:
            ohlc = ohlc[ohlc.index >= df.index[0]] if ohlc is not None else None
        start = df.index[0]
        preis, _, _ = kurs_jetzt(daten)

        fg, leise, rand = T["text"], T["leise"], T["gitter"]
        gruen, rot = T["gruen"], T["rot"]
        self._fk = None
        self.fig.clear()
        self.fig.set_facecolor(T["chart"])
        ax, ax_rsi = self.fig.subplots(
            2, 1, sharex=True, gridspec_kw={"height_ratios": [5, 1], "hspace": 0.06})
        self.fig.subplots_adjust(left=0.005, right=0.90, top=0.93, bottom=0.07)
        for a in (ax, ax_rsi):
            a.set_facecolor(T["chart"])
            a.tick_params(colors=leise, labelsize=9, length=0, pad=8)
            for sp in a.spines.values():
                sp.set_visible(False)
            a.yaxis.tick_right()
            a.grid(color=rand, lw=0.8)

        # Kerzen
        if ohlc is not None and len(ohlc):
            kerzen = self._kerzen(ohlc)
            x = mdates.date2num(kerzen.index.to_pydatetime())
            breite = (x[1] - x[0]) * 0.62 if len(x) > 1 else 0.6
            hoch = kerzen["Close"] >= kerzen["Open"]
            farben = [gruen if h else rot for h in hoch]
            ax.vlines(x, kerzen["Low"], kerzen["High"], colors=farben, lw=0.9, zorder=3)
            koerper = (kerzen["Close"] - kerzen["Open"]).abs()
            koerper = koerper.where(koerper > 0, kerzen["Close"] * 0.0008)
            ax.bar(x, koerper, bottom=kerzen[["Open", "Close"]].min(axis=1), width=breite,
                   color=farben, lw=0, zorder=4)
            unten, oben = float(kerzen["Low"].min()), float(kerzen["High"].max())
            erster = float(kerzen["Open"].iloc[0])
        else:
            ax.plot(df.index, df["kurs"], color=fg, lw=1.6, zorder=3)
            unten, oben = float(df["kurs"].min()), float(df["kurs"].max())
            erster = float(df["kurs"].iloc[0])

        ax.plot(df.index, df["sma_kurz"], color="#b9c0be", lw=1, alpha=0.75)
        ax.plot(df.index, df["sma_lang"], color="#59625f", lw=1.1, alpha=0.9)
        if "bollinger" in extras:
            voll = daten["kurse_voll"]
            mitte_b = voll.rolling(20).mean()
            sd = voll.rolling(20).std()
            ob, ub = (mitte_b + 2 * sd)[voll.index >= start], (mitte_b - 2 * sd)[voll.index >= start]
            ax.fill_between(ob.index, ub.values, ob.values, color=SILBER, alpha=0.04, lw=0)
            for b in (ob, ub):
                ax.plot(b.index, b.values, color="#8a9592", lw=0.8, alpha=0.6)
            unten, oben = min(unten, float(ub.min())), max(oben, float(ob.max()))
        if "52w" in extras:
            jahr = daten["kurse_voll"].iloc[-252:]
            for wert, txt in ((float(jahr.max()), "52W-Hoch"), (float(jahr.min()), "52W-Tief")):
                ax.axhline(wert, color=T["orange"], lw=0.9, ls=(0, (6, 3)), alpha=0.7)
                ax.text(df.index[0], wert, f" {txt} {kurs_text(wert)}", color=T["orange"],
                        fontsize=7.5, va="bottom", alpha=0.9)
                unten, oben = min(unten, wert), max(oben, wert)
        kaeufe = [(d, p) for d, a, p in bt.trades_liste if a == "Kauf" and d >= start]
        verk = [(d, p) for d, a, p in bt.trades_liste if a == "Verkauf" and d >= start]
        if kaeufe:
            ax.scatter(*zip(*kaeufe), marker="^", s=70, color=gruen, zorder=6,
                       edgecolor=T["markerrand"], lw=1.2)
        if verk:
            ax.scatter(*zip(*verk), marker="v", s=70, color=rot, zorder=6,
                       edgecolor=T["markerrand"], lw=1.2)

        # Prognose: Linie (gedämpfter Trend) mit 50 %- und 80 %-Spanne als feine Linien
        pr = daten.get("prognose")
        if pr:
            fenster_tage = (df.index[-1] - df.index[0]).days
            tage = min(365, max(30, fenster_tage * 0.3))
            xs = pd.date_range(df.index[-1], df.index[-1] + pd.Timedelta(days=tage), periods=60)
            t = [(d - xs[0]).total_seconds() / 86400 for d in xs]
            mitte = [pr.linie(v) for v in t]
            lo80 = [pr.band(v, prognose.Z10) for v in t]
            hi80 = [pr.band(v, -prognose.Z10) for v in t]
            lo50 = [pr.band(v, prognose.Z25) for v in t]
            hi50 = [pr.band(v, -prognose.Z25) for v in t]
            ax.fill_between(xs, lo80, hi80, color=fg, alpha=0.035, lw=0)
            ax.fill_between(xs, lo50, hi50, color=fg, alpha=0.05, lw=0)
            for werte, stil, alpha in ((lo80, (0, (1, 3)), 0.55), (hi80, (0, (1, 3)), 0.55),
                                       (lo50, (0, (4, 3)), 0.6), (hi50, (0, (4, 3)), 0.6)):
                ax.plot(xs, werte, color=leise, lw=0.9, ls=stil, alpha=alpha)
            ax.plot(xs, mitte, color=GOLD, lw=2.2, solid_capstyle="round", zorder=7)
            ax.scatter([xs[-1]], [mitte[-1]], s=36, color=GOLD, zorder=8,
                       edgecolor=T["markerrand"], lw=1.5)
            ziel_ende = None
            if pr.analysten:
                ziel_ende = preis + (pr.analysten["mittel"] - preis) * min(1, tage / 365)
            unten_drunter = ziel_ende is not None and ziel_ende > mitte[-1]
            ax.annotate(f"Prognose {xs[-1]:%d.%m.%y}\n{kurs_text(mitte[-1])}",
                        xy=(xs[-1], mitte[-1]), xytext=(-8, -12 if unten_drunter else 10),
                        textcoords="offset points", ha="right",
                        va="top" if unten_drunter else "bottom", fontsize=8.5,
                        fontweight="medium", color=GOLD, zorder=9)
            for werte, txt in ((hi80, "80 %"), (hi50, "50 %"), (lo50, ""), (lo80, "")):
                if txt:
                    ax.text(xs[-1], werte[-1], f" {txt}", color=leise, fontsize=7.5,
                            va="center")
            unten, oben = min(unten, min(lo80)), max(oben, max(hi80))
            if pr.analysten:
                ziel = pr.analysten["mittel"]
                ende = df.index[-1] + pd.Timedelta(days=365)
                xa = pd.date_range(df.index[-1], ende, periods=60)
                ya = [preis + (ziel - preis) * i / 59 for i in range(60)]
                sichtbar = [(x, y) for x, y in zip(xa, ya) if x <= xs[-1]]
                if sichtbar:
                    ax.plot(*zip(*sichtbar), color=fg, lw=1.2, ls="--", alpha=0.6)
                    xe, ye = sichtbar[-1]
                    ax.text(xe, ye, " Analysten", color=leise, fontsize=7.5, va="center")
                    unten, oben = min(unten, ye), max(oben, ye)
            ax.set_xlim(right=mdates.date2num(xs[-1].to_pydatetime()) + tage * 0.12)
            xs_ende = mdates.date2num(xs[-1].to_pydatetime())

        # aktueller Kurs: gepunktete Linie + Preismarke an der Achse
        aenderung = preis - erster
        farbe = wert_farbe(aenderung)
        ax.axhline(preis, color=farbe, lw=1, ls=(0, (1, 2.5)), zorder=2)
        spiel = (oben - unten) * 0.05
        ax.set_ylim(unten - spiel, oben + spiel)
        nk = 0 if oben >= 1000 else 2 if oben >= 1 else 4
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: zahl(v, nk)))
        ax.annotate(zahl(preis, nk if nk else 0) if preis >= 1000 else kurs_text(preis),
                    xy=(1, preis), xycoords=("axes fraction", "data"), xytext=(6, 0),
                    textcoords="offset points", va="center", ha="left", fontsize=9,
                    fontweight="medium", color="#0a0a0a" if farbe == gruen else "white",
                    bbox=dict(boxstyle="round,pad=0.35,rounding_size=0.2", fc=farbe, ec="none"),
                    annotation_clip=False, zorder=10)
        ax.text(0.01, 0.97, f"{'+' if aenderung >= 0 else '−'}{differenz_text(aenderung, preis)} "
                f"({prozent(preis / erster - 1, 2)})", transform=ax.transAxes, color=farbe,
                fontsize=9.5, fontweight="medium", va="top")

        ax_rsi.axhspan(s.RSI_OBEN, 100, color=rot, alpha=0.07, lw=0)
        ax_rsi.axhspan(0, s.RSI_UNTEN, color=gruen, alpha=0.07, lw=0)
        ax_rsi.plot(df.index, df["rsi"], color=leise, lw=1)
        ax_rsi.set_ylim(0, 100)
        ax_rsi.set_yticks([s.RSI_UNTEN, s.RSI_OBEN])
        ax_rsi.text(0.01, 0.85, "RSI", transform=ax_rsi.transAxes, fontsize=8,
                    color=leise, va="top")
        loc = mdates.AutoDateLocator(minticks=4, maxticks=8)
        ax_rsi.xaxis.set_major_locator(loc)
        ax_rsi.xaxis.set_major_formatter(mdates.ConciseDateFormatter(
            loc, show_offset=False,
            formats=["%Y", "%b", "%d.%m.", "%H:%M", "%H:%M", "%S"]))

        xs = mdates.date2num(df.index.to_pydatetime())
        zukunft = None
        if pr:
            letzter_tag = df.index[-1]

            def zukunft(xv, pr=pr, letzter_tag=letzter_tag, ende=xs_ende):
                xv = min(xv, ende)
                tag = mdates.num2date(xv).replace(tzinfo=None)
                tage = (pd.Timestamp(tag) - letzter_tag).total_seconds() / 86400
                y = pr.linie(tage)
                return xv, y, (f"Prognose {tag:%d.%m.%Y}   {kurs_text(y)} {daten['waehrung']}"
                               f"   {prozent(y / preis - 1, 1)} ab heute")
        achsen = [ax, ax_rsi]
        vol = daten.get("volumen")
        if "volumen" in extras and vol is not None and len(vol):
            vol = vol[vol.index >= start]
            if ohlc is not None and len(ohlc) > 300:
                vol = vol.resample("W-FRI").sum()
            ax_v = ax.twinx()
            ax_v.set_zorder(ax.get_zorder() - 1)
            ax.patch.set_visible(False)
            xv = mdates.date2num(vol.index.to_pydatetime())
            bv = (xv[1] - xv[0]) * 0.62 if len(xv) > 1 else 0.6
            ax_v.bar(xv, vol.values, width=bv, color=T["leise"], alpha=0.22, lw=0)
            ax_v.set_ylim(0, float(vol.max() or 1) * 5)
            ax_v.set_yticks([])
            for sp in ax_v.spines.values():
                sp.set_visible(False)
        self._fk_einrichten(ax, achsen, xs, df["kurs"].to_numpy(dtype=float),
                            [f"{d:%d.%m.%Y}" for d in df.index], erster, daten["waehrung"],
                            zukunft)
        self.draw_idle()


# ------------------------------------------------------- Detail-Bausteine


class IndikatorKarte(QFrame):
    def __init__(self, titel: str, erklaerung: str):
        super().__init__()
        self.setObjectName("karte")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 16)
        lay.setSpacing(4)
        kopf = QHBoxLayout()
        kopf.addWidget(label(titel, "h2"))
        kopf.addStretch()
        self.chip = QLabel()
        self.chip.setFixedWidth(34)
        self.chip.setAlignment(Qt.AlignCenter)
        kopf.addWidget(self.chip)
        lay.addLayout(kopf)
        self.wert = label("", "wert")
        self.urteil = label("")
        self.urteil.setStyleSheet("font-size: 13px; font-weight: 500;")
        self.balken = QProgressBar(maximum=100, textVisible=False)
        self.balken.hide()
        self.info = label("", "klein")
        self.info.setWordWrap(True)
        self.setToolTip(erklaerung)
        for w in (self.wert, self.urteil, self.balken, self.info):
            lay.addWidget(w)
        lay.addStretch()

    def setze(self, wert: str, urteil: str, punkte: int, info: str) -> None:
        farbe = wert_farbe(punkte)
        self.wert.setText(wert)
        self.urteil.setText(urteil)
        self.urteil.setStyleSheet(f"font-size: 13px; font-weight: 500; color: {farbe};")
        self.chip.setText(f"{punkte:+d}" if punkte else "0")
        self.chip.setStyleSheet(pill_stil(farbe))
        self.info.setText(info)


class BegruendungKarte(QFrame):
    """Erklärt in Klartext, warum die Regel das aktuelle Signal zeigt."""

    TITEL = {
        "VERKAUFEN": ("Warum verkaufen?", "Gründe für das Verkaufssignal", "Was dagegen spricht"),
        "KAUFEN": ("Warum kaufen?", "Gründe für das Kaufsignal", "Was dagegen spricht"),
        "HALTEN": ("Warum halten?", "Spricht für steigende Kurse", "Spricht für fallende Kurse"),
    }

    def __init__(self):
        super().__init__()
        self.setObjectName("karte")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 18)
        lay.setSpacing(10)
        self.titel = kartenkopf(lay, "")
        self.kurz = label("")
        self.kurz.setWordWrap(True)
        lay.addWidget(self.kurz)

        spalten = QHBoxLayout()
        spalten.setSpacing(28)
        self.links_titel, self.links = label("", "h2"), label("")
        self.rechts_titel, self.rechts = label("", "h2"), label("")
        for t, inhalt in ((self.links_titel, self.links), (self.rechts_titel, self.rechts)):
            box = QVBoxLayout()
            box.setSpacing(4)
            inhalt.setWordWrap(True)
            inhalt.setTextFormat(Qt.RichText)
            box.addWidget(t)
            box.addWidget(inhalt)
            box.addStretch()
            spalten.addLayout(box, 1)
        lay.addLayout(spalten)

        self.trenner = QFrame()
        self.trenner.setFixedHeight(1)
        lay.addWidget(self.trenner)

        unten = QGridLayout()
        unten.setHorizontalSpacing(16)
        unten.setVerticalSpacing(8)
        self.felder = {}
        for r, (key, name) in enumerate((("kontext", "Kursentwicklung"),
                                         ("treffer", "Bisherige Trefferquote"),
                                         ("wechsel", "Was das Signal ändern würde"))):
            kopf = label(name, "klein")
            kopf.setStyleSheet("font-weight: 500;")
            kopf.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            inhalt = label("")
            inhalt.setWordWrap(True)
            inhalt.setTextFormat(Qt.RichText)
            unten.addWidget(kopf, r, 0)
            unten.addWidget(inhalt, r, 1)
            self.felder[key] = (kopf, inhalt)
        unten.setColumnStretch(1, 1)
        lay.addLayout(unten)
        lay.addWidget(label("Die Begründung beschreibt, was die Regel sieht – sie ist keine "
                            "Anlageberatung und keine Garantie.", "klein"))

    @staticmethod
    def _liste(punkte, leer: str) -> str:
        if not punkte:
            return f"<span style='color:{T['leise']}'>{leer}</span>"
        zeilen = []
        for p in punkte:
            farbe = wert_farbe(p.richtung)
            icon = "▲" if p.richtung > 0 else "▼" if p.richtung < 0 else "●"
            zeilen.append(f"<tr><td valign='top' style='color:{farbe}; padding-right:8px'>"
                          f"{icon}</td><td style='padding-bottom:6px'>{p.text}</td></tr>")
        return ("<table cellspacing='0' cellpadding='0' style='font-size:13px'>"
                + "".join(zeilen) + "</table>")

    def setze(self, b, ticker: str) -> None:
        farbe = signal_farbe(b.signal)
        titel, links, rechts = self.TITEL[b.signal]

        self.titel.setText(titel)

        self.kurz.setText(b.kurz)
        self.kurz.setStyleSheet("font-size: 14px; font-weight: 400;")
        self.links_titel.setText(links)
        self.rechts_titel.setText(rechts)
        self.links.setText(self._liste(b.gruende, "keine"))
        self.rechts.setText(self._liste(b.dagegen, "Nichts – alle Indikatoren sind sich einig."))
        self.trenner.setStyleSheet(f"background: {T['gitter']};")

        kontext = "<br>".join(
            f"<span style='color:{wert_farbe(p.richtung)}'>"
            f"{'▲' if p.richtung > 0 else '▼' if p.richtung < 0 else '●'}</span>&nbsp;{p.text}"
            for p in b.kontext)
        werte = {"kontext": kontext, "treffer": b.trefferquote, "wechsel": b.wechsel}
        for key, (kopf, inhalt) in self.felder.items():
            sichtbar = bool(werte[key])
            kopf.setVisible(sichtbar)
            inhalt.setVisible(sichtbar)
            inhalt.setText(f"<span style='font-size:13px'>{werte[key]}</span>")


def termine(info: dict) -> list[tuple[str, datetime, str]]:
    """Kommende Termine aus den Stammdaten: Quartalszahlen, Ex-Dividende, Auszahlung."""
    i = info or {}
    jetzt = datetime.now()
    out = []
    for schluessel, name in (("earningsTimestampStart", "Quartalszahlen"),
                             ("earningsTimestamp", "Quartalszahlen"),
                             ("exDividendDate", "Ex-Dividende"),
                             ("dividendDate", "Dividenden-Zahltag")):
        ts = i.get(schluessel)
        if not ts or any(n == name for n, _, _ in out):
            continue
        try:
            zeit = datetime.fromtimestamp(int(ts))
        except (TypeError, ValueError, OSError):
            continue
        if zeit.date() >= jetzt.date():
            tage = (zeit.date() - jetzt.date()).days
            wann = "heute" if tage == 0 else "morgen" if tage == 1 else f"in {tage} Tagen"
            out.append((name, zeit, wann))
    return sorted(out, key=lambda x: x[1])


def dividende_je_stueck(info: dict) -> float | None:
    """Jährliche Dividende je Stück in der Kurswährung (falls bekannt)."""
    i = info or {}
    return i.get("dividendRate") or i.get("trailingAnnualDividendRate") or None


class SparplanKarte(QFrame):
    """Rückblick: Was wäre aus einem monatlichen Sparplan in diesem Wert geworden?"""

    def __init__(self):
        super().__init__(objectName="karte")
        self.daten = None
        lay = QHBoxLayout(self)
        lay.setContentsMargins(22, 16, 22, 16)
        lay.setSpacing(28)
        links = QVBoxLayout()
        links.setSpacing(8)
        kartenkopf(links, "Was wäre wenn")
        zeile = QHBoxLayout()
        zeile.setSpacing(8)
        zeile.addWidget(label("Monatlich", "leise"))
        self.rate = QSpinBox()
        self.rate.setRange(5, 10_000)
        self.rate.setSingleStep(25)
        self.rate.setValue(50)
        self.rate.setSuffix(" €")
        self.rate.setButtonSymbols(QSpinBox.NoButtons)
        self.rate.setFixedWidth(90)
        zeile.addWidget(self.rate)
        zeile.addSpacing(10)
        zeile.addWidget(label("seit", "leise"))
        self.jahre = QButtonGroup(self)
        for i, j in enumerate((1, 3, 5)):
            b = QPushButton(f"{j} {'Jahr' if j == 1 else 'Jahren'}", objectName="seg",
                            checkable=True)
            b.setCursor(Qt.PointingHandCursor)
            b.setProperty("jahre", j)
            self.jahre.addButton(b, i)
            zeile.addWidget(b)
        self.jahre.button(1).setChecked(True)
        zeile.addStretch()
        links.addLayout(zeile)
        self.ergebnis = label("")
        self.ergebnis.setTextFormat(Qt.RichText)
        self.ergebnis.setWordWrap(True)
        links.addWidget(self.ergebnis)
        hinweis = label("Rückblick mit echten Kursen der Vergangenheit, Kauf am ersten "
                        "Handelstag jedes Monats, ohne Gebühren und Steuern, Fremdwährung zum "
                        "heutigen Wechselkurs. Sagt nichts über die Zukunft.", "klein")
        hinweis.setWordWrap(True)
        links.addWidget(hinweis)
        links.addStretch()
        lay.addLayout(links, 1)
        self.fig = Figure(figsize=(4, 1.8))
        self.canvas = FigureCanvasQTAgg(self.fig)
        durchsichtig(self.canvas)
        self.canvas.setFixedHeight(170)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        lay.addWidget(self.canvas, 1)
        self.rate.valueChanged.connect(lambda _: self.rechnen())
        self.jahre.idClicked.connect(lambda _: self.rechnen())

    def setze(self, d: dict) -> None:
        self.daten = d
        self.rechnen()

    def rechnen(self) -> None:
        d = self.daten
        if not d:
            return
        jahre = self.jahre.checkedButton().property("jahre")
        faktor = d.get("eur_faktor")
        sp = konto.sparplan(d["kurse_voll"] * faktor if faktor else None,
                            self.rate.value(), jahre) if faktor else None
        self.fig.clear()
        if sp is None:
            self.ergebnis.setText(f"<span style='color:{T['leise']}'>Für {jahre} "
                                  f"{'Jahr' if jahre == 1 else 'Jahre'} gibt es zu wenig "
                                  "Kursdaten.</span>")
            self.canvas.draw_idle()
            return
        wert, ein = float(sp["wert"].iloc[-1]), float(sp["eingezahlt"].iloc[-1])
        f = wert_farbe(wert - ein)
        self.ergebnis.setText(
            f"<span style='font-size:13px; color:{T['leise']}'>Eingezahlt</span> "
            f"<span style='font-size:13px'>{euro(ein)}</span>&nbsp;&nbsp;&nbsp;"
            f"<span style='font-size:13px; color:{T['leise']}'>Wert heute</span> "
            f"<span style='font-size:17px'>{euro(wert)}</span><br>"
            f"<span style='color:{f}; font-size:13px; font-weight:500'>{euro_vz(wert - ein)}"
            f"&nbsp;&nbsp;{prozent(wert / ein - 1, 1)}</span>")
        self.fig.set_facecolor("none")
        ax = self.fig.add_axes([0.0, 0.08, 0.86, 0.9])
        ax.set_facecolor("none")
        ax.fill_between(sp.index, sp["wert"], color=f, alpha=0.10, lw=0)
        ax.plot(sp.index, sp["wert"], color=f, lw=1.6)
        ax.plot(sp.index, sp["eingezahlt"], color=T["leise"], lw=1, ls=(0, (3, 3)))
        ax.text(sp.index[-1], float(sp["eingezahlt"].iloc[-1]), " eingezahlt",
                color=T["leise"], fontsize=7.5, va="center")
        ax.text(sp.index[-1], wert, " Wert", color=f, fontsize=7.5, va="center")
        for sp_ in ax.spines.values():
            sp_.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_ylim(0, max(wert, ein) * 1.08)
        self.canvas.draw_idle()


class PrognoseKarte(QFrame):
    """Statistische Kursspannen, Analysten-Kursziele und Verlauf nach früheren Signalen."""

    def __init__(self):
        super().__init__()
        self.setObjectName("karte")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 18)
        lay.setSpacing(10)
        kartenkopf(lay, "Prognose")
        self.einleitung = label("", "leise")
        self.einleitung.setWordWrap(True)
        lay.addWidget(self.einleitung)

        # Tabelle über die volle Breite, darunter Analysten | frühere Signale
        lay.addWidget(label("Mögliche Kursspanne", "h2"))
        self.tabelle = label("")
        self.tabelle.setTextFormat(Qt.RichText)
        lay.addWidget(self.tabelle)
        lay.addSpacing(6)

        unten = QHBoxLayout()
        unten.setSpacing(28)
        links = QVBoxLayout()
        links.setSpacing(6)
        self.analyst_titel = label("Analysten-Kursziele (12 Monate)", "h2")
        self.analyst = label("")
        self.analyst.setTextFormat(Qt.RichText)
        self.analyst.setWordWrap(True)
        links.addWidget(self.analyst_titel)
        links.addWidget(self.analyst)
        links.addStretch()
        unten.addLayout(links, 1)
        rechts = QVBoxLayout()
        rechts.setSpacing(6)
        self.verlauf_titel = label("", "h2")
        self.verlauf = label("")
        self.verlauf.setTextFormat(Qt.RichText)
        self.verlauf.setWordWrap(True)
        rechts.addWidget(self.verlauf_titel)
        rechts.addWidget(self.verlauf)
        rechts.addStretch()
        unten.addLayout(rechts, 1)
        lay.addLayout(unten)

        hinweis = label("Prognosen sind unsicher: Die Spannen zeigen, wie weit sich der Kurs "
                        "bei gleicher Schwankung typischerweise bewegt. Die Linie ist eine "
                        "Fortschreibung, keine Vorhersage. Keine Anlageberatung.", "klein")
        hinweis.setWordWrap(True)
        lay.addWidget(hinweis)

    def setze(self, pr, waehrung: str, ticker: str) -> None:
        roh = math.expm1(pr.trend_roh)
        genutzt = math.expm1(pr.trend_jahr)
        self.einleitung.setText(
            f"<span style='font-weight:500'>Prognose-Linie:</span> In den letzten 12 Monaten lag der Trend bei "
            f"<span style='color:{wert_farbe(roh)}'>{prozent(roh, 0)}</span> pro Jahr. "
            f"Fortgeschrieben wird davon nur die Hälfte ({prozent(genutzt, 0)} pro Jahr, "
            f"begrenzt auf ±28 %), weil Trends meist nachlassen. Um die Linie herum zeigen "
            f"die Spannen, wo der Kurs bei der bisherigen Schwankung "
            f"({zahl(pr.vola_jahr * 100, 0)} % pro Jahr) wahrscheinlich liegt.")
        self.einleitung.setTextFormat(Qt.RichText)

        def bereich(lo, hi):
            return (f"{kurs_text(lo)}&nbsp;–&nbsp;{kurs_text(hi)}<br>"
                    f"<span style='color:{T['leise']}; font-size:11px'>"
                    f"{prozent(lo / pr.kurs - 1, 0)} bis {prozent(hi / pr.kurs - 1, 0)}</span>")

        def mitte(wert):
            d = wert / pr.kurs - 1
            return (f"<span style='font-weight:500'>{kurs_text(wert)}</span><br><span style='color:{wert_farbe(d)};"
                    f" font-size:11px'>{pfeil(d, 0)}</span>")

        kopf = (f"<tr style='color:{T['leise']}; font-size:11px'>"
                f"<td>Zeitraum&nbsp;&nbsp;</td><td>Prognose-Linie&nbsp;&nbsp;&nbsp;</td>"
                f"<td>wahrscheinlich (50 %)&nbsp;&nbsp;&nbsp;</td>"
                f"<td>sehr wahrscheinlich (80 %)</td></tr>")
        zeilen = [f"<tr><td style='padding:5px 14px 5px 0'><span style='font-weight:500'>{sp.name}</span></td>"
                  f"<td style='padding:5px 18px 5px 0'>{mitte(sp.p50)}</td>"
                  f"<td style='padding:5px 18px 5px 0'>{bereich(sp.p25, sp.p75)}</td>"
                  f"<td style='padding:5px 0'>{bereich(sp.p10, sp.p90)}</td></tr>"
                  for sp in pr.spannen]
        self.tabelle.setText("<table cellspacing='0' style='font-size:13px'>"
                             + kopf + "".join(zeilen) + "</table>")

        a = pr.analysten
        self.analyst_titel.setVisible(True)
        if a:
            diff = a["mittel"] / pr.kurs - 1
            spanne = (f"<br>Spanne {kurs_text(a['tief'])} – {kurs_text(a['hoch'])}"
                      if a["tief"] and a["hoch"] else "")
            konsens = f" · Konsens: <span style='font-weight:500'>{a['konsens']}</span>" if a["konsens"] else ""
            self.analyst.setText(
                f"<span style='font-size:13px'>Ø Kursziel <span style='font-weight:500'>{kurs_text(a['mittel'])} {waehrung}"
                f"</span> (<span style='color:{wert_farbe(diff)}'>{prozent(diff)}</span>)"
                f"{spanne}<br><span style='color:{T['leise']}'>{a['anzahl']} Analysten"
                f"{konsens}</span></span>")
        else:
            self.analyst.setText(f"<span style='color:{T['leise']}; font-size:13px'>Für {ticker} "
                                 "gibt es keine Analysten-Kursziele (nur bei Einzelaktien).</span>")

        self.verlauf_titel.setText(f"Nach früheren {pr.signal}-Signalen")
        if pr.verlauf:
            zeilen = []
            for v in pr.verlauf:
                besser = v.anteil_hoch - v.alle_anteil_hoch
                zeilen.append(
                    f"<span style='font-weight:500'>{v.name}</span> später lag der Kurs in "
                    f"<span style='font-weight:500'>{zahl(v.anteil_hoch * 100, 0)} %</span> der Fälle höher "
                    f"(Median <span style='color:{wert_farbe(v.median)}'>"
                    f"{prozent(v.median)}</span>)<br><span style='color:{T['leise']}'>"
                    f"an allen Tagen: {zahl(v.alle_anteil_hoch * 100, 0)} % höher, Median "
                    f"{prozent(v.alle_median)} · {v.n} Tage mit diesem Signal</span>")
            self.verlauf.setText("<span style='font-size:13px'>"
                                 + "<br><br>".join(zeilen) + "</span>")
        else:
            self.verlauf.setText(f"<span style='color:{T['leise']}; font-size:13px'>"
                                 "Zu wenige frühere Tage mit diesem Signal.</span>")


def gross_zahl(x) -> str:
    if not x:
        return ""
    x = float(x)
    for grenze, wort in ((1e12, "Bio."), (1e9, "Mrd."), (1e6, "Mio.")):
        if abs(x) >= grenze:
            return f"{zahl(x / grenze, 2)} {wort}"
    return zahl(x, 0)


def fakten(info: dict, typ: str, waehrung: str) -> list[tuple[str, str]]:
    i = info or {}
    w = f" {waehrung}" if waehrung else ""
    out = []
    if typ == "Krypto":
        out += [("Marktkapitalisierung", gross_zahl(i.get("marketCap")) + w),
                ("Umlaufmenge", gross_zahl(i.get("circulatingSupply"))),
                ("Handelsvolumen 24 h", gross_zahl(i.get("volume24Hr")) + w)]
    elif typ == "ETF":
        kosten = i.get("netExpenseRatio")
        out += [("Kategorie", i.get("category") or ""),
                ("Anbieter", i.get("fundFamily") or ""),
                ("Fondsvolumen", gross_zahl(i.get("totalAssets")) + w),
                ("Laufende Kosten", f"{zahl(kosten, 2)} % pro Jahr" if kosten else "")]
    else:
        branche = " · ".join(x for x in (i.get("sector"), i.get("industry")) if x)
        kgv = i.get("trailingPE")
        div = i.get("dividendYield")
        mitarb = i.get("fullTimeEmployees")
        out += [("Branche", branche), ("Land", i.get("country") or ""),
                ("Marktkapitalisierung", gross_zahl(i.get("marketCap")) + w),
                ("KGV", zahl(kgv, 1) if kgv else ""),
                ("Dividendenrendite", f"{zahl(div, 2)} %" if div else "keine"),
                ("Mitarbeiter", zahl(mitarb, 0) if mitarb else "")]
    hoch, tief = i.get("fiftyTwoWeekHigh"), i.get("fiftyTwoWeekLow")
    if hoch and tief:
        out.append(("52-Wochen-Spanne", f"{kurs_text(tief)} – {kurs_text(hoch)}"))
    return [(k, v.strip()) for k, v in out if v and v.strip()]


class InfoNachrichtenKarte(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("karte")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 16, 20, 18)
        lay.setSpacing(32)

        links = QVBoxLayout()
        links.setSpacing(8)
        kartenkopf(links, "Infos")
        self.fakten = label("")
        self.fakten.setWordWrap(True)
        self.fakten.setTextFormat(Qt.RichText)
        links.addWidget(self.fakten)
        self.beschreibung = label("", "klein")
        self.beschreibung.setWordWrap(True)
        links.addWidget(self.beschreibung)
        links.addStretch()
        lay.addLayout(links, 2)

        rechts = QVBoxLayout()
        rechts.setSpacing(8)
        kartenkopf(rechts, "Nachrichten")
        self.news_info = label("", "klein")
        rechts.addWidget(self.news_info)
        self.news = label("")
        self.news.setTextFormat(Qt.RichText)
        self.news.setWordWrap(True)
        self.news.setOpenExternalLinks(True)
        self.news.setTextInteractionFlags(Qt.TextBrowserInteraction)
        rechts.addWidget(self.news)
        rechts.addStretch()
        lay.addLayout(rechts, 3)

    def setze_infos(self, d: dict) -> None:
        zeilen = "".join(
            f"<tr><td style='color:{T['leise']}; padding:3px 16px 3px 0'>{k}</td>"
            f"<td style='padding:3px 0'>{v}</td></tr>"
            for k, v in fakten(d.get("info", {}), d["typ"], d["waehrung"]))
        for name, zeit, wann in termine(d.get("info", {})):
            zeilen += (f"<tr><td style='color:{T['leise']}; padding:3px 16px 3px 0'>{name}</td>"
                       f"<td style='padding:3px 0'><span style='color:{SILBER}'>{zeit:%d.%m.%Y}"
                       f"</span> · {wann}</td></tr>")
        div = dividende_je_stueck(d.get("info", {}))
        if div and d["typ"] != "Krypto":
            zeilen += (f"<tr><td style='color:{T['leise']}; padding:3px 16px 3px 0'>Dividende "
                       f"je Stück</td><td style='padding:3px 0'>{kurs_text(div)} "
                       f"{d['waehrung']} pro Jahr</td></tr>")
        self.fakten.setText(f"<table cellspacing='0' style='font-size:13px'>{zeilen}</table>"
                            if zeilen else "Keine Stammdaten verfügbar.")
        text = (d.get("info") or {}).get("longBusinessSummary") or ""
        if len(text) > 420:
            text = text[:420].rsplit(" ", 1)[0] + " …"
        self.beschreibung.setText(text)
        self.beschreibung.setVisible(bool(text))

    def setze_news(self, artikel: list | None) -> None:
        if artikel is None:
            self.news_info.setText("")
            self.news.setText(f"<span style='color:{T['leise']}'>Lade Nachrichten …</span>")
            return
        self.news_info.setText("Google News (DE) · Yahoo Finance (EN)")
        if not artikel:
            self.news.setText(f"<span style='color:{T['leise']}'>Keine aktuellen Nachrichten "
                              "gefunden.</span>")
            return
        zeilen = []
        for a in artikel:
            titel = a["titel"].replace("<", "&lt;")
            zeilen.append(
                f"<p style='margin:0 0 9px 0'><a href='{a['link']}' style='color:{T['text']};"
                f" text-decoration:none; font-weight:500'>{titel}</a><br>"
                f"<span style='color:{T['leise']}; font-size:11px'>{a['quelle']} · "
                f"{nachrichten.vor_wann(a['zeit'])} · {a['sprache']}</span></p>")
        self.news.setText("<div style='font-size:13px'>" + "".join(zeilen) + "</div>")


# ------------------------------------------------------- Depot & Alarme


def euro(x: float) -> str:
    return f"{zahl(x, 2)} €"


def euro_vz(x: float) -> str:
    """Betrag mit Vorzeichen, z. B. +12,40 € / −3,10 €."""
    return ("+" if x > 0 else "−" if x < 0 else "±") + euro(abs(x))


def leeren(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.hide()
            w.setParent(None)
            w.deleteLater()
        elif item.layout():
            leeren(item.layout())


def listenzeile(text: str, tooltip: str, entfernen, extra: "QPushButton | None" = None) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 2, 0, 2)
    lay.setSpacing(6)
    lbl = label(text, "")
    lbl.setTextFormat(Qt.RichText)
    lbl.setStyleSheet("font-size: 13px;")
    lbl.setToolTip(tooltip)
    lbl.setWordWrap(True)
    lay.addWidget(lbl, 1)
    if extra is not None:
        lay.addWidget(extra)
    weg = icon_knopf("x", "Löschen", 14)
    weg.clicked.connect(entfernen)
    lay.addWidget(weg)
    return w


def alarm_text(a: dict, waehrung: str = "") -> str:
    art, w = a["art"], a.get("wert")
    if art == "signal":
        return "Signal ändert sich" + (f" (zuletzt {a['signal']})" if a.get("signal") else "")
    if art in ("tag_minus", "tag_plus"):
        return f"{konto.ARTEN[art]} {zahl(w, 1)} %"
    if art in ("rsi_unter", "rsi_ueber"):
        return f"{konto.ARTEN[art]} {zahl(w, 0)}"
    if art in ("hoch52", "tief52"):
        return konto.ARTEN[art]
    return f"{konto.ARTEN[art]} {kurs_text(w)} {waehrung}".rstrip()


def alarm_pruefen(a: dict, d: dict) -> tuple[str, str] | None:
    """Ist die Bedingung eines (aktiven) Alarms erfüllt? Dann (Titel, Text), sonst None."""
    if not a.get("aktiv") or a["art"] == "signal":
        return None
    preis, ch, _ = kurs_jetzt(d)
    name, w, cur = kurzer_name(d["name"]), a.get("wert"), d["waehrung"]
    t = a["ticker"]
    kurs = f"{kurs_text(preis)} {cur} ({pfeil(ch)} heute)"
    art = a["art"]
    if art == "ueber" and preis >= w:
        return f"{t} über {kurs_text(w)} {cur}", f"{name} steht bei {kurs}."
    if art == "unter" and preis <= w:
        return f"{t} unter {kurs_text(w)} {cur}", f"{name} steht bei {kurs}."
    if art == "tag_minus" and ch <= -w / 100:
        return f"{t} heute {prozent(ch, 1)}", f"{name} ist heute um mehr als {zahl(w, 1)} % " \
                                               f"gefallen und steht bei {kurs}."
    if art == "tag_plus" and ch >= w / 100:
        return f"{t} heute {prozent(ch, 1)}", f"{name} ist heute um mehr als {zahl(w, 1)} % " \
                                               f"gestiegen und steht bei {kurs}."
    rsi = float(d["df"]["rsi"].iloc[-1])
    if art == "rsi_unter" and rsi < w:
        return f"{t}: RSI {zahl(rsi, 0)}", f"{name} gilt mit RSI {zahl(rsi, 0)} als " \
                                            f"überverkauft. Kurs {kurs}."
    if art == "rsi_ueber" and rsi > w:
        return f"{t}: RSI {zahl(rsi, 0)}", f"{name} gilt mit RSI {zahl(rsi, 0)} als " \
                                            f"überkauft. Kurs {kurs}."
    jahr = d["kurse_voll"].iloc[-253:-1]
    if len(jahr):
        if art == "hoch52" and preis > float(jahr.max()):
            return f"{t}: neues 52-Wochen-Hoch", f"{name} steht bei {kurs} – höher als in den " \
                                                 "letzten 12 Monaten."
        if art == "tief52" and preis < float(jahr.min()):
            return f"{t}: neues 52-Wochen-Tief", f"{name} steht bei {kurs} – tiefer als in den " \
                                                 "letzten 12 Monaten."
    return None


def alarm_status(a: dict) -> str:
    if a["aktiv"]:
        return f"<span style='color:{GOLD}'>● aktiv</span>"
    zeit = datetime.fromisoformat(a["ausgeloest"]) if a.get("ausgeloest") else None
    return (f"<span style='color:{T['leise']}'>ausgelöst "
            f"{zeit:%d.%m. %H:%M}</span>" if zeit else f"<span style='color:{T['leise']}'>aus</span>")


class KaufDialog(QDialog):
    """Kauf eintragen: Betrag oder Stückzahl, Kurs in Euro, Gebühr, Datum."""

    def __init__(self, parent, ticker: str, name: str, preis_eur: float | None,
                 bestand: float = 0.0):
        super().__init__(parent)
        self.setWindowTitle(f"Kauf / Verkauf eintragen · {ticker}")
        self.setMinimumWidth(420)
        self.bestand = bestand
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(label(name, "kartentitel"))
        umschalter = QFrame(objectName="tabs")
        ul = QHBoxLayout(umschalter)
        ul.setContentsMargins(3, 3, 3, 3)
        ul.setSpacing(3)
        self.art_knoepfe = QButtonGroup(self)
        for i, txt in enumerate(("Kauf", "Verkauf")):
            b = QPushButton(txt, objectName="tab", checkable=True)
            b.setCursor(Qt.PointingHandCursor)
            b.setEnabled(i == 0 or bestand > 0)
            if i == 1 and bestand <= 0:
                b.setToolTip("Du hast von diesem Wert noch nichts im Depot.")
            self.art_knoepfe.addButton(b, i)
            ul.addWidget(b, 1)
        self.art_knoepfe.button(0).setChecked(True)
        self.art_knoepfe.idClicked.connect(lambda _: self._rechne("betrag"))
        lay.addWidget(umschalter)
        hinweis = label("Trag ein, was du beim Broker tatsächlich bezahlt hast. Alle Beträge "
                        "in Euro – so enthält Gewinn/Verlust auch den Wechselkurs.", "klein")
        hinweis.setWordWrap(True)
        lay.addWidget(hinweis)
        g = QGridLayout()
        g.setHorizontalSpacing(14)
        g.setVerticalSpacing(10)

        def feld(dezimal: int, maximum: float, suffix: str) -> QDoubleSpinBox:
            f = QDoubleSpinBox()
            f.setDecimals(dezimal)
            f.setRange(0, maximum)
            f.setSuffix(suffix)
            f.setGroupSeparatorShown(True)
            f.setButtonSymbols(QDoubleSpinBox.NoButtons)
            return f

        self.kurs = feld(4, 10_000_000, " €")
        self.stueck = feld(6, 1_000_000_000, " Stück")
        self.betrag = feld(2, 1_000_000_000, " €")
        self.gebuehr = feld(2, 10_000, " €")
        self.datum = QDateEdit(QDate.currentDate())
        self.datum.setCalendarPopup(True)
        self.datum.setDisplayFormat("dd.MM.yyyy")
        self.datum.setMaximumDate(QDate.currentDate())
        self.l_datum = label("Kaufdatum", "leise")
        for r, (txt, w) in enumerate((("Kurs je Stück", self.kurs), ("Betrag", self.betrag),
                                      ("Stück", self.stueck), ("Gebühr", self.gebuehr),
                                      ("Kaufdatum", self.datum))):
            g.addWidget(self.l_datum if txt == "Kaufdatum" else label(txt, "leise"), r, 0)
            g.addWidget(w, r, 1)
        lay.addLayout(g)
        self.summe = label("", "leise")
        self.summe.setTextFormat(Qt.RichText)
        lay.addWidget(self.summe)

        if preis_eur is not None and preis_eur >= 1:
            self.kurs.setDecimals(2)
        self.kurs.setValue(preis_eur or 0)
        self.gebuehr.setValue(1.0)
        self.betrag.setValue(100.0)
        self._sperre = False
        self.betrag.valueChanged.connect(lambda _: self._rechne("betrag"))
        self.stueck.valueChanged.connect(lambda _: self._rechne("stueck"))
        self.kurs.valueChanged.connect(lambda _: self._rechne("kurs"))
        self.gebuehr.valueChanged.connect(lambda _: self._rechne("kurs"))
        self._rechne("betrag")

        knoepfe = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        knoepfe.button(QDialogButtonBox.Save).setText("Speichern")
        knoepfe.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        knoepfe.accepted.connect(self.accept)
        knoepfe.rejected.connect(self.reject)
        self.ok = knoepfe.button(QDialogButtonBox.Save)
        lay.addWidget(knoepfe)
        self.betrag.setFocus()
        self.betrag.selectAll()

    def _rechne(self, quelle: str) -> None:
        if self._sperre:
            return
        self._sperre = True
        kurs = self.kurs.value()
        if quelle == "stueck" and kurs:
            self.betrag.setValue(self.stueck.value() * kurs)
        elif kurs:
            self.stueck.setValue(self.betrag.value() / kurs)
        self._sperre = False
        verkauf = self.ist_verkauf()
        self.l_datum.setText("Verkaufsdatum" if verkauf else "Kaufdatum")
        if verkauf:
            erloes = self.stueck.value() * kurs - self.gebuehr.value()
            zu_viel = self.stueck.value() > self.bestand + 1e-9
            self.summe.setText(
                f"<span style='color:{T['rot']}'>Du hast nur "
                f"{zahl(self.bestand, 6).rstrip('0').rstrip(',')} Stück.</span>" if zu_viel
                else f"Erlös nach Gebühr: {euro(erloes)} · im Depot: "
                     f"{zahl(self.bestand, 6).rstrip('0').rstrip(',')} Stück")
        else:
            zu_viel = False
            gesamt = self.stueck.value() * kurs + self.gebuehr.value()
            self.summe.setText(f"Einstand gesamt: {euro(gesamt)}")
        if hasattr(self, "ok"):
            self.ok.setEnabled(self.stueck.value() > 0 and kurs > 0 and not zu_viel)

    def ist_verkauf(self) -> bool:
        return self.art_knoepfe.checkedId() == 1

    def ergebnis(self, ticker: str) -> dict:
        return konto.kauf(ticker, self.stueck.value(), self.kurs.value(), self.gebuehr.value(),
                          self.datum.date().toString("yyyy-MM-dd"),
                          "verkauf" if self.ist_verkauf() else "kauf")


class AlarmDialog(QDialog):
    def __init__(self, parent, ticker: str, name: str, preis: float, waehrung: str,
                 rsi: float = 50.0):
        super().__init__(parent)
        self.setWindowTitle(f"Alarm · {ticker}")
        self.setMinimumWidth(520)
        self.preis = preis
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(label(name, "kartentitel"))
        lay.addWidget(label(f"Aktueller Kurs: {kurs_text(preis)} {waehrung}", "leise"))
        self.arten = QButtonGroup(self)
        self.waehrung = waehrung
        self.rsi = rsi
        raster = QGridLayout()
        raster.setHorizontalSpacing(18)
        raster.setVerticalSpacing(8)
        for i, (art, txt) in enumerate((("ueber", "Kurs steigt über …"),
                                        ("unter", "Kurs fällt unter …"),
                                        ("tag_plus", "Steigt heute um mehr als … %"),
                                        ("tag_minus", "Fällt heute um mehr als … %"),
                                        ("rsi_unter", "RSI fällt unter … (überverkauft)"),
                                        ("rsi_ueber", "RSI steigt über … (überkauft)"),
                                        ("hoch52", "Neues 52-Wochen-Hoch"),
                                        ("tief52", "Neues 52-Wochen-Tief"),
                                        ("signal", "Signal der Regel ändert sich"))):
            r = QRadioButton(txt)
            r.setProperty("art", art)
            self.arten.addButton(r, i)
            raster.addWidget(r, i // 2, i % 2)
        lay.addLayout(raster)
        self.arten.button(0).setChecked(True)
        self.wert = QDoubleSpinBox()
        self.wert.setDecimals(2 if preis >= 1 else 6)
        self.wert.setRange(0, 1e9)
        self.wert.setSuffix(f" {waehrung}")
        self.wert.setGroupSeparatorShown(True)
        self.wert.setButtonSymbols(QDoubleSpinBox.NoButtons)
        lay.addWidget(self.wert)
        self.abstand = label("", "klein")
        lay.addWidget(self.abstand)
        hinweis = label("Du bekommst eine Mitteilung mit Ton, solange Vyntro läuft (auch im "
                        "Hintergrund). Alarme melden sich einmal und schalten sich dann ab – "
                        "außer dem Signal-Alarm.", "klein")
        hinweis.setWordWrap(True)
        lay.addWidget(hinweis)
        knoepfe = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        knoepfe.button(QDialogButtonBox.Save).setText("Alarm anlegen")
        knoepfe.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        knoepfe.accepted.connect(self.accept)
        knoepfe.rejected.connect(self.reject)
        self.ok = knoepfe.button(QDialogButtonBox.Save)
        lay.addWidget(knoepfe)
        self.arten.idClicked.connect(self._art_gewaehlt)
        self.wert.valueChanged.connect(lambda _: self._pruefen())
        self._art_gewaehlt(0)

    def art(self) -> str:
        return self.arten.checkedButton().property("art")

    def _art_gewaehlt(self, _id) -> None:
        art = self.art()
        ohne_wert = art in ("signal", "hoch52", "tief52")
        self.wert.setVisible(not ohne_wert)
        if not ohne_wert:
            if art in ("ueber", "unter"):
                self.wert.setDecimals(2 if self.preis >= 1 else 6)
                self.wert.setSuffix(f" {self.waehrung}")
                self.wert.setValue(self.preis * (1.05 if art == "ueber" else 0.95))
            elif art in ("tag_plus", "tag_minus"):
                self.wert.setDecimals(1)
                self.wert.setSuffix(" %")
                self.wert.setValue(5.0)
            else:
                self.wert.setDecimals(0)
                self.wert.setSuffix("")
                self.wert.setValue(30 if art == "rsi_unter" else 70)
            self.wert.setFocus()
            self.wert.selectAll()
        self._pruefen()

    def _pruefen(self) -> None:
        art, w = self.art(), self.wert.value()
        if art in ("signal", "hoch52", "tief52"):
            self.abstand.setText("")
            self.abstand.setStyleSheet("")
            self.ok.setEnabled(True)
            return
        if art in ("tag_plus", "tag_minus"):
            self.ok.setEnabled(0 < w < 100)
            self.abstand.setText("Gilt gegenüber dem Schlusskurs vom Vortag.")
            self.abstand.setStyleSheet("")
            return
        if art in ("rsi_unter", "rsi_ueber"):
            ok = (0 < w < self.rsi) if art == "rsi_unter" else (self.rsi < w < 100)
            self.ok.setEnabled(ok)
            self.abstand.setText(f"RSI aktuell {zahl(self.rsi, 0)}" + (
                "" if ok else " – der Wert muss " + ("darunter" if art == "rsi_unter"
                                                     else "darüber") + " liegen."))
            self.abstand.setStyleSheet("" if ok else f"color: {T['rot']};")
            return
        ok = w > self.preis if art == "ueber" else 0 < w < self.preis
        self.ok.setEnabled(ok)
        if ok:
            self.abstand.setText(f"{prozent(w / self.preis - 1, 1)} vom aktuellen Kurs")
            self.abstand.setStyleSheet("")
        else:
            self.abstand.setText("Der Wert muss " + ("über" if art == "ueber" else "unter")
                                 + " dem aktuellen Kurs liegen.")
            self.abstand.setStyleSheet(f"color: {T['rot']};")


class NotizKarte(QFrame):
    """Eigene Notizen zu einem Wert, z. B. warum gekauft. Speichert automatisch."""
    geaendert = Signal(str, str)

    def __init__(self):
        super().__init__(objectName="karte")
        self.ticker = ""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 16, 22, 16)
        lay.setSpacing(8)
        kopf = QHBoxLayout()
        kopf.addWidget(label("Notizen", "h2"))
        kopf.addStretch()
        self.stand = label("", "klein")
        kopf.addWidget(self.stand)
        lay.addLayout(kopf)
        self.feld = QPlainTextEdit(objectName="notiz")
        self.feld.setPlaceholderText("Warum beobachte oder besitze ich das? Ziele, Gedanken, "
                                     "Termine … (wird automatisch gespeichert)")
        self.feld.setFixedHeight(96)
        lay.addWidget(self.feld)
        self.timer = QTimer(self, singleShot=True, interval=700)
        self.timer.timeout.connect(self._speichern)
        self.feld.textChanged.connect(self._getippt)
        self._laden = False

    def setze(self, ticker: str, text: str) -> None:
        if ticker == self.ticker and self.feld.hasFocus():
            return  # nicht beim Tippen überschreiben
        self._laden = True
        self.ticker = ticker
        self.feld.setPlainText(text)
        self.stand.setText("")
        self._laden = False

    def _getippt(self) -> None:
        if not self._laden:
            self.stand.setText("…")
            self.timer.start()

    def _speichern(self) -> None:
        self.geaendert.emit(self.ticker, self.feld.toPlainText())
        self.stand.setText("gespeichert")


class KontoKarte(QFrame):
    """In der Detailansicht: eigene Position in diesem Wert und Alarme dazu."""
    kauf_neu = Signal(str)
    kauf_weg = Signal(str)
    alarm_neu = Signal(str)
    alarm_weg = Signal(str)
    alarm_wieder = Signal(str)

    def __init__(self):
        super().__init__(objectName="karte")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(22, 16, 22, 16)
        lay.setSpacing(34)
        self.ticker = ""
        self.pos = None

        links = QVBoxLayout()
        links.setSpacing(4)
        kopf = QHBoxLayout()
        kopf.addWidget(label("Mein Depot", "h2"))
        kopf.addStretch()
        b = QPushButton(" Kauf / Verkauf", objectName="chip")
        b.setIcon(icon("plus", None, 14))
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(lambda: self.kauf_neu.emit(self.ticker))
        kopf.addWidget(b)
        links.addLayout(kopf)
        self.d_wert = label("", "wert")
        self.d_gv = label("")
        self.d_gv.setTextFormat(Qt.RichText)
        self.d_info = label("", "klein")
        self.d_info.setWordWrap(True)
        for w in (self.d_wert, self.d_gv, self.d_info):
            links.addWidget(w)
        self.d_liste = QVBoxLayout()
        self.d_liste.setSpacing(0)
        links.addLayout(self.d_liste)
        links.addStretch()
        lay.addLayout(links, 1)

        trenner = QFrame()
        trenner.setFixedWidth(1)
        trenner.setStyleSheet(f"background: {T['rand']};")
        lay.addWidget(trenner)

        rechts = QVBoxLayout()
        rechts.setSpacing(4)
        kopf = QHBoxLayout()
        kopf.addWidget(label("Alarme", "h2"))
        kopf.addStretch()
        b = QPushButton(" Alarm", objectName="chip")
        b.setIcon(icon("glocke", None, 14))
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(lambda: self.alarm_neu.emit(self.ticker))
        kopf.addWidget(b)
        rechts.addLayout(kopf)
        self.a_liste = QVBoxLayout()
        self.a_liste.setSpacing(0)
        rechts.addLayout(self.a_liste)
        rechts.addStretch()
        lay.addLayout(rechts, 1)

    def setze(self, ticker: str, d: dict, pos: dict | None, alarme: list[dict],
              eintraege: list[dict] | None = None, realisiert: float = 0.0) -> None:
        self.ticker, self.pos, self.realisiert = ticker, pos, realisiert
        leeren(self.d_liste)
        if eintraege:
            for k in sorted(eintraege, key=lambda k: k["datum"], reverse=True):
                datum = datetime.strptime(k["datum"], "%Y-%m-%d")
                vk = konto.ist_verkauf(k)
                art = (f"<span style='color:{T['rot']}'>Verkauf</span>" if vk
                       else f"<span style='color:{T['gruen']}'>Kauf</span>")
                text = (f"<span style='color:{T['leise']}'>{datum:%d.%m.%Y}</span>&nbsp;&nbsp;"
                        f"{art}&nbsp;&nbsp;{zahl(k['stueck'], 4).rstrip('0').rstrip(',')} Stück à "
                        f"{euro(k['kurs_eur'])}")
                self.d_liste.addWidget(listenzeile(
                    text, f"Gebühr {euro(k.get('gebuehr_eur', 0))}",
                    lambda _=False, i=k["id"]: self.kauf_weg.emit(i)))
        leeren(self.a_liste)
        if not alarme:
            hinweis = label("Noch keine Alarme. Lass dich benachrichtigen, wenn der Kurs eine "
                            "Marke erreicht oder das Signal wechselt.", "klein")
            hinweis.setWordWrap(True)
            self.a_liste.addWidget(hinweis)
        for a in alarme:
            extra = None
            if not a["aktiv"] and a["art"] != "signal":
                extra = QPushButton("Wieder an", objectName="icon")
                extra.setStyleSheet("font-size: 12px;")
                extra.setCursor(Qt.PointingHandCursor)
                extra.clicked.connect(lambda _=False, i=a["id"]: self.alarm_wieder.emit(i))
            self.a_liste.addWidget(listenzeile(
                f"{alarm_text(a, d['waehrung'])}&nbsp;&nbsp;{alarm_status(a)}", "",
                lambda _=False, i=a["id"]: self.alarm_weg.emit(i), extra))
        self.kurs(d)

    def kurs(self, d: dict) -> None:
        """Wert und Gewinn/Verlust mit dem aktuellen Kurs (auch bei Live-Updates)."""
        pos = self.pos
        real = getattr(self, "realisiert", 0.0)
        real_text = (f" · aus Verkäufen {euro_vz(real)}" if abs(real) >= 0.005 else "")
        if not pos:
            self.d_wert.setText("–")
            self.d_gv.setText("")
            self.d_info.setText(("Aktuell nicht im Depot" + real_text + ".") if real_text else
                                "Noch nicht im Depot. Trag deine Käufe ein, dann siehst du "
                                "hier Wert und Gewinn/Verlust.")
            return
        faktor = d.get("eur_faktor")
        preis = kurs_jetzt(d)[0] * faktor if faktor else None
        b = konto.bewerte(pos, preis)
        stueck = zahl(pos["stueck"], 6).rstrip("0").rstrip(",")
        if b["wert"] is None:
            self.d_wert.setText("–")
            self.d_gv.setText("Kein Wechselkurs verfügbar")
            return
        self.d_wert.setText(euro(b["wert"]))
        f = wert_farbe(b["gv"])
        self.d_gv.setText(f"<span style='color:{f}; font-weight:500'>{euro_vz(b['gv'])}"
                          f"&nbsp;&nbsp;{prozent(b['gv_pct'], 2)}</span>"
                          f"<span style='color:{T['leise']}'>&nbsp;&nbsp;gesamt</span>")
        self.d_info.setText(f"{stueck} Stück · Einstand {euro(pos['einstand'])} "
                            f"(inkl. Gebühren) · Ø {euro(pos['einstand'] / pos['stueck'])} je Stück"
                            + real_text)


class DepotZeile(QFrame):
    geklickt = Signal(str)

    def __init__(self, ticker: str):
        super().__init__(objectName="depotzeile")
        self.ticker = ticker
        self.setCursor(Qt.PointingHandCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 12, 8)
        lay.setSpacing(12)
        lay.addWidget(avatar(ticker, 34))
        links = QVBoxLayout()
        links.setSpacing(1)
        self.l_name = KuerzLabel("zticker")
        self.l_info = label("", "klein")
        links.addWidget(self.l_name)
        links.addWidget(self.l_info)
        lay.addLayout(links, 1)
        self.l_kurs = label("", "zkurs")
        self.l_kurs.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.l_kurs.setMinimumWidth(110)
        lay.addWidget(self.l_kurs)
        rechts = QVBoxLayout()
        rechts.setSpacing(1)
        self.l_wert = label("", "zkurs")
        self.l_gv = label("", "klein")
        for w in (self.l_wert, self.l_gv):
            w.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            w.setMinimumWidth(150)
            rechts.addWidget(w)
        lay.addLayout(rechts)

    def mousePressEvent(self, e):
        self.geklickt.emit(self.ticker)


class DepotSeite(QWidget):
    """Übersicht über alle eingetragenen Positionen, in Euro: Verlauf, Aufteilung,
    Positionen und Dividenden."""
    oeffnen = Signal(str)
    export_gewuenscht = Signal()
    import_gewuenscht = Signal()
    VERGLEICH = "EUNL.DE"  # iShares Core MSCI World

    def __init__(self):
        super().__init__(objectName="detail")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 16)
        lay.setSpacing(14)
        kopf = karte()
        kl = QVBoxLayout(kopf)
        kl.setContentsMargins(24, 20, 24, 20)
        kl.setSpacing(4)
        titel = QHBoxLayout()
        titel.addWidget(label("Mein Depot", "kartentitel"))
        titel.addStretch()
        importieren = QPushButton(" Trade Republic importieren", objectName="chip")
        importieren.setIcon(icon("import", None, 14))
        importieren.setCursor(Qt.PointingHandCursor)
        importieren.setToolTip("Käufe und Verkäufe aus dem CSV-Export von Trade Republic "
                               "übernehmen (Profil → Transaktionen exportieren)")
        importieren.clicked.connect(self.import_gewuenscht)
        titel.addWidget(importieren)
        export = QPushButton(" Als CSV exportieren", objectName="chip")
        export.setIcon(icon("export", None, 14))
        export.setCursor(Qt.PointingHandCursor)
        export.setToolTip("Buchungen und Positionen als Tabelle für Excel/Numbers speichern")
        export.clicked.connect(self.export_gewuenscht)
        titel.addWidget(export)
        kl.addLayout(titel)
        self.gesamt = label("", "preis")
        self.gesamt.setTextFormat(Qt.RichText)
        kl.addWidget(self.gesamt)
        self.gv = label("")
        self.gv.setTextFormat(Qt.RichText)
        kl.addWidget(self.gv)
        self.info = label("", "klein")
        self.info.setWordWrap(True)
        kl.addWidget(self.info)
        lay.addWidget(kopf)

        # Verlauf | Aufteilung
        reihe = QHBoxLayout()
        reihe.setSpacing(14)
        vk = karte()
        vl = QVBoxLayout(vk)
        vl.setContentsMargins(20, 16, 20, 14)
        vl.setSpacing(4)
        vl.addWidget(label("Verlauf", "h2"))
        self.verlauf_info = label("", "klein")
        self.verlauf_info.setTextFormat(Qt.RichText)
        self.verlauf_info.setWordWrap(True)
        vl.addWidget(self.verlauf_info)
        self.v_fig = Figure(figsize=(6, 2.4))
        self.v_canvas = FigureCanvasQTAgg(self.v_fig)
        durchsichtig(self.v_canvas)
        self.v_canvas.setFixedHeight(230)
        vl.addWidget(self.v_canvas)
        reihe.addWidget(vk, 3)

        ak = karte()
        al = QVBoxLayout(ak)
        al.setContentsMargins(20, 16, 20, 14)
        al.setSpacing(6)
        al.addWidget(label("Aufteilung", "h2"))
        seg = QHBoxLayout()
        seg.setSpacing(2)
        self.auft_knoepfe = QButtonGroup(self)
        for i, (key, txt) in enumerate((("wert", "Werte"), ("branche", "Branche"),
                                        ("land", "Land"), ("art", "Art"))):
            b = QPushButton(txt, objectName="seg", checkable=True)
            b.setCursor(Qt.PointingHandCursor)
            b.setProperty("key", key)
            self.auft_knoepfe.addButton(b, i)
            seg.addWidget(b)
        seg.addStretch()
        self.auft_knoepfe.button(0).setChecked(True)
        self.auft_knoepfe.idClicked.connect(lambda _: self._aufteilung_zeichnen())
        al.addLayout(seg)
        self.a_fig = Figure(figsize=(3.2, 2.4))
        self.a_canvas = FigureCanvasQTAgg(self.a_fig)
        durchsichtig(self.a_canvas)
        self.a_canvas.setFixedHeight(230)
        al.addWidget(self.a_canvas)
        reihe.addWidget(ak, 2)
        lay.addLayout(reihe)

        liste = karte()
        self.ll = QVBoxLayout(liste)
        self.ll.setContentsMargins(14, 14, 14, 14)
        self.ll.setSpacing(2)
        lay.addWidget(liste)

        dk = karte()
        dl = QVBoxLayout(dk)
        dl.setContentsMargins(20, 16, 20, 16)
        dl.setSpacing(6)
        dl.addWidget(label("Dividenden", "h2"))
        self.dividenden = label("")
        self.dividenden.setTextFormat(Qt.RichText)
        self.dividenden.setWordWrap(True)
        dl.addWidget(self.dividenden)
        lay.addWidget(dk)

        sk = karte()
        stl = QVBoxLayout(sk)
        stl.setContentsMargins(20, 16, 20, 16)
        stl.setSpacing(6)
        stl.addWidget(label("Steuer-Schätzung", "h2"))
        self.steuer = label("")
        self.steuer.setTextFormat(Qt.RichText)
        self.steuer.setWordWrap(True)
        stl.addWidget(self.steuer)
        hinweis = label("Grobe Überschlagsrechnung: 25 % Abgeltungssteuer + Soli auf realisierte "
                        "Gewinne nach Sparerpauschbetrag, ohne Kirchensteuer, Teilfreistellung "
                        "bei Fonds, Verlusttöpfe und Dividenden. Deutsche Broker führen die "
                        "Steuer meist selbst ab. Keine Steuerberatung.", "klein")
        hinweis.setWordWrap(True)
        stl.addWidget(hinweis)
        lay.addWidget(sk)
        self.freibetrag = 1000.0

        fuss = label("Werte in Euro zum aktuellen Kurs und Wechselkurs. Nur deine eigenen "
                     "Eintragungen – Vyntro ist nicht mit deinem Broker verbunden.", "klein")
        fuss.setWordWrap(True)
        fuss.setAlignment(Qt.AlignCenter)
        lay.addWidget(fuss)
        lay.addStretch()
        self.zeilen: dict[str, DepotZeile] = {}
        self._tickers: list[str] = []
        self._verlauf_schluessel = None
        self._verlauf_zeit = 0.0
        self._auft = ({}, {})

    def setze(self, kaeufe: list[dict], daten: dict[str, dict]) -> None:
        positionen = konto.positionen(kaeufe)
        tickers = sorted(positionen)
        if tickers != self._tickers:
            self._tickers = tickers
            leeren(self.ll)
            self.zeilen.clear()
            self.ll.addWidget(label("Positionen", "h2"))
            if not tickers:
                hinweis = label("Noch keine Käufe eingetragen. Öffne einen Wert und klicke auf "
                                "„+ Kauf / Verkauf“.", "leise")
                hinweis.setWordWrap(True)
                hinweis.setContentsMargins(10, 10, 10, 10)
                self.ll.addWidget(hinweis)
            for t in tickers:
                z = DepotZeile(t)
                z.geklickt.connect(self.oeffnen)
                self.ll.addWidget(z)
                self.zeilen[t] = z
        wert_summe = einstand_summe = heute = 0.0
        fehlend = 0
        werte: dict[str, float] = {}
        for t, pos in positionen.items():
            z, d = self.zeilen[t], daten.get(t)
            stueck = zahl(pos["stueck"], 6).rstrip("0").rstrip(",")
            z.l_name.setze(d["name"] if d else t)
            z.l_info.setText(f"{t} · {stueck} Stück · Ø {euro(pos['einstand'] / pos['stueck'])}")
            if not d or not d.get("eur_faktor"):
                z.l_kurs.setText("lädt …")
                z.l_wert.setText("")
                z.l_gv.setText("")
                fehlend += 1
                continue
            preis, ch, _ = kurs_jetzt(d)
            p_eur = preis * d["eur_faktor"]
            b = konto.bewerte(pos, p_eur)
            z.l_kurs.setText(f"{kurs_text(p_eur)} €")
            z.l_kurs.setToolTip(f"{kurs_text(preis)} {d['waehrung']} · heute {pfeil(ch)}")
            z.l_wert.setText(euro(b["wert"]))
            z.l_gv.setText(f"{euro_vz(b['gv'])}  {prozent(b['gv_pct'], 2)}")
            z.l_gv.setStyleSheet(f"color: {wert_farbe(b['gv'])}; font-weight: 500;")
            wert_summe += b["wert"]
            einstand_summe += pos["einstand"]
            heute += b["wert"] - b["wert"] / (1 + ch)
            werte[t] = b["wert"]
        real = konto.realisiert(kaeufe)
        self.gesamt.setText(f"{zahl(wert_summe, 2)}&nbsp;<span style='font-size:18px'>€</span>")
        if einstand_summe:
            gv = wert_summe - einstand_summe
            f, fh = wert_farbe(gv), wert_farbe(heute)
            self.gv.setText(
                f"<span style='color:{f}; font-weight:500; font-size:14px'>{euro_vz(gv)}"
                f"&nbsp;&nbsp;{prozent(gv / einstand_summe, 2)}</span>"
                f"<span style='color:{T['leise']}; font-size:13px'>&nbsp;&nbsp;gesamt</span>"
                f"&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:{fh}; font-weight:500; "
                f"font-size:14px'>{euro_vz(heute)}</span><span style='color:{T['leise']};"
                f" font-size:13px'>&nbsp;&nbsp;heute</span>")
        else:
            self.gv.setText("")
        teile = []
        if positionen:
            teile.append(f"{len(positionen)} Positionen · Einstand {euro(einstand_summe)} "
                         "inkl. Gebühren")
        if abs(real) >= 0.005:
            teile.append(f"aus Verkäufen realisiert {euro_vz(real)}")
        if fehlend:
            teile.append(f"{fehlend} noch ohne Kurs")
        self.info.setText(" · ".join(teile))

        # Aufteilung (nur neu zeichnen, wenn sich die Anteile spürbar ändern)
        if werte:
            gerundet = {t: round(w / max(wert_summe, 1) * 200) for t, w in werte.items()}
            if gerundet != self._auft[1]:
                self._auft = (dict(werte), gerundet)
                self._daten = daten
                self._aufteilung_zeichnen()
        elif self._auft[0]:
            self._auft = ({}, {})
            self._aufteilung_zeichnen()

        self._dividenden(positionen, daten)
        self._steuer(kaeufe)

        # Verlauf: höchstens jede Minute oder bei geänderten Käufen neu berechnen
        schluessel = (tuple(sorted(k["id"] for k in kaeufe)),
                      tuple(sorted(t for t in {k["ticker"] for k in kaeufe} if t in daten)),
                      self.VERGLEICH in daten)
        if schluessel != self._verlauf_schluessel or time.time() - self._verlauf_zeit > 60:
            self._verlauf_schluessel, self._verlauf_zeit = schluessel, time.time()
            self._verlauf_zeichnen(kaeufe, daten)

    def _verlauf_zeichnen(self, kaeufe: list[dict], daten: dict) -> None:
        kurse = {}
        for t in {k["ticker"] for k in kaeufe}:
            d = daten.get(t)
            if d and d.get("eur_faktor"):
                kurse[t] = d["kurse_voll"] * d["eur_faktor"]
        v = daten.get(self.VERGLEICH)
        vergleich = v["kurse_voll"] * v["eur_faktor"] if v and v.get("eur_faktor") else None
        df = konto.depot_verlauf(kaeufe, kurse, vergleich) if kurse else None
        self.v_fig.clear()
        self.v_fig.set_facecolor("none")
        if df is None or len(df) < 2:
            self.verlauf_info.setText("Der Verlauf erscheint, sobald Käufe eingetragen und die "
                                      "Kurse geladen sind.")
            self.v_canvas.draw_idle()
            return
        ax = self.v_fig.add_axes([0.0, 0.12, 0.88, 0.86])
        ax.set_facecolor("none")
        ax.tick_params(colors=T["leise"], labelsize=8, length=0, pad=6)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.yaxis.tick_right()
        ax.grid(color=T["gitter"], lw=0.7)
        ax.fill_between(df.index, df["wert"], color=GOLD, alpha=0.08, lw=0)
        ax.plot(df.index, df["wert"], color=GOLD, lw=1.8, label="Depot")
        ax.plot(df.index, df["eingezahlt"], color=T["leise"], lw=1, ls=(0, (3, 3)),
                label="eingezahlt")
        if "vergleich" in df:
            ax.plot(df.index, df["vergleich"], color=SILBER, lw=1.1, alpha=0.6,
                    label="MSCI World")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{zahl(x, 0)} €"))
        loc = mdates.AutoDateLocator(minticks=3, maxticks=6)
        ax.xaxis.set_major_locator(loc)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(
            loc, show_offset=False, formats=["%Y", "%b", "%d.%m.", "%H:%M", "%H:%M", "%S"]))
        ende = df.iloc[-1]
        teile = [f"<span style='color:{GOLD}'>━</span> Depot {euro(ende['wert'])}",
                 f"<span style='color:{T['leise']}'>┅</span> eingezahlt (netto) "
                 f"{euro(ende['eingezahlt'])}"]
        if "vergleich" in df:
            teile.append(f"<span style='color:{SILBER}'>━</span> dasselbe Geld im MSCI World "
                         f"{euro(ende['vergleich'])}")
        self.verlauf_info.setText("&nbsp;&nbsp;&nbsp;".join(teile))
        self.verlauf_info.setToolTip("Tagesschlusskurse, Fremdwährungen zum heutigen Kurs "
                                     "umgerechnet. Der MSCI-World-Vergleich kauft und verkauft "
                                     "an denselben Tagen mit denselben Beträgen.")
        self.v_canvas.draw_idle()

    def _aufteilung_zeichnen(self) -> None:
        werte = self._auft[0]
        daten = getattr(self, "_daten", {})
        key = self.auft_knoepfe.checkedButton().property("key")
        gruppen: dict[str, float] = {}
        for t, w in werte.items():
            d = daten.get(t) or {}
            info, typ = d.get("info") or {}, d.get("typ") or ""
            if key == "wert":
                g = t
            elif key == "branche":
                g = info.get("sector") or ({"ETF": "ETF (gemischt)", "Krypto": "Krypto"}
                                           .get(typ, "unbekannt"))
            elif key == "land":
                g = info.get("country") or ({"ETF": "ETF (gemischt)", "Krypto": "Krypto"}
                                            .get(typ, "unbekannt"))
            else:
                g = typ or "unbekannt"
            gruppen[g] = gruppen.get(g, 0.0) + w
        self.a_fig.clear()
        self.a_fig.set_facecolor("none")
        summe = sum(gruppen.values())
        if not summe:
            self.a_canvas.draw_idle()
            return
        teile = sorted(gruppen.items(), key=lambda x: -x[1])
        if len(teile) > 6:
            teile = teile[:5] + [("Sonstige", sum(w for _, w in teile[5:]))]
        farben = [GOLD, "#d5dad8", "#9aa3a0", "#6b7471", "#454c4a", "#2c3130"]
        ax = self.a_fig.add_axes([0.0, 0.02, 0.5, 0.96])
        ax.pie([w for _, w in teile], colors=farben[:len(teile)], startangle=90,
               counterclock=False, wedgeprops=dict(width=0.32, edgecolor=T["bg"], linewidth=1.5))
        ax.text(0, 0, f"{len(werte)}\nWerte" if key == "wert" else f"{len(teile)}\nGruppen",
                ha="center", va="center", color=T["leise"], fontsize=8.5)
        ax.set_aspect("equal")
        for i, (name, w) in enumerate(teile):
            y = 0.86 - i * 0.15
            self.a_fig.text(0.54, y, "●", color=farben[i], fontsize=10, va="center")
            self.a_fig.text(0.60, y, name if len(name) <= 18 else name[:17] + "…",
                            color=T["text"], fontsize=8.5, va="center")
            self.a_fig.text(0.99, y, f"{zahl(w / summe * 100, 0)} %", color=T["leise"],
                            fontsize=8.5, va="center", ha="right")
        self.a_canvas.draw_idle()

    def _steuer(self, kaeufe: list[dict]) -> None:
        je_jahr = konto.realisiert_je_jahr(kaeufe)
        jahr = datetime.now().year
        st = konto.steuer_schaetzung(je_jahr.get(jahr, 0.0), self.freibetrag)
        zeilen = [f"<div style='font-size:13px'>Realisiert {jahr}: <b>{euro_vz(st['gewinn'])}"
                  f"</b>&nbsp;&nbsp;<span style='color:{T['leise']}'>Sparerpauschbetrag genutzt "
                  f"{euro(st['freibetrag_genutzt'])} von {euro(self.freibetrag)}</span></div>",
                  f"<div style='font-size:13px; margin-top:4px'>Geschätzte Steuer: "
                  f"<b>{euro(st['steuer'])}</b>"
                  f"<span style='color:{T['leise']}'>&nbsp;&nbsp;auf "
                  f"{euro(st['steuerpflichtig'])} steuerpflichtigen Gewinn</span></div>"]
        frueher = {j: g for j, g in je_jahr.items() if j != jahr}
        if frueher:
            zeilen.append(f"<div style='font-size:12px; color:{T['leise']}; margin-top:4px'>"
                          "Frühere Jahre: " + " · ".join(f"{j}: {euro_vz(g)}" for j, g in
                                                        sorted(frueher.items())) + "</div>")
        self.steuer.setText("".join(zeilen))

    def _dividenden(self, positionen: dict, daten: dict) -> None:
        zeilen, summe = [], 0.0
        for t, pos in sorted(positionen.items()):
            d = daten.get(t)
            if not d:
                continue
            je = dividende_je_stueck(d.get("info"))
            naechste = next((f"{z:%d.%m.%Y}" for n, z, _ in termine(d.get("info"))
                             if n == "Ex-Dividende"), "")
            if je and d.get("eur_faktor") and d["typ"] != "Krypto":
                jahr = je * d["eur_faktor"] * pos["stueck"]
                summe += jahr
                betrag = euro(jahr)
            else:
                betrag = (f"<span style='color:{T['leise']}'>"
                          + ("keine (Krypto)" if d["typ"] == "Krypto" else
                             "keine / thesaurierend") + "</span>")
            zeilen.append(
                f"<tr><td style='padding:3px 18px 3px 0'>{t}</td>"
                f"<td style='padding:3px 18px 3px 0; color:{T['leise']}'>"
                f"{kurzer_name(d['name'])}</td>"
                f"<td align='right' style='padding:3px 18px 3px 0'>{betrag}</td>"
                f"<td style='padding:3px 0; color:{T['leise']}'>"
                f"{'Ex-Tag ' + naechste if naechste else ''}</td></tr>")
        if not zeilen:
            self.dividenden.setText(f"<span style='color:{T['leise']}'>Noch keine Positionen."
                                    "</span>")
            return
        self.dividenden.setText(
            f"<div style='font-size:13px'>Erwartet pro Jahr: <b>{euro(summe)}</b> "
            f"<span style='color:{T['leise']}'>(≈ {euro(summe / 12)} im Monat, vor Steuern, "
            f"nach der letzten bekannten Dividende)</span></div>"
            f"<table cellspacing='0' style='font-size:13px; margin-top:6px'>{''.join(zeilen)}"
            "</table>")


class AlarmSeite(QWidget):
    """Alle Alarme auf einen Blick."""
    oeffnen = Signal(str)
    alarm_weg = Signal(str)
    alarm_wieder = Signal(str)

    def __init__(self):
        super().__init__(objectName="detail")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 16)
        lay.setSpacing(14)
        k = karte()
        self.kl = QVBoxLayout(k)
        self.kl.setContentsMargins(24, 20, 24, 20)
        self.kl.setSpacing(6)
        lay.addWidget(k)
        hinweis = label("Alarme werden geprüft, solange Vyntro geöffnet ist: Kursalarme jede "
                        "Sekunde, Signal-Alarme alle 15 Minuten. Du bekommst dann eine "
                        "Mitteilung mit Ton.", "klein")
        hinweis.setWordWrap(True)
        hinweis.setAlignment(Qt.AlignCenter)
        lay.addWidget(hinweis)
        lay.addStretch()

    def setze(self, alarme: list[dict], daten: dict[str, dict]) -> None:
        leeren(self.kl)
        self.kl.addWidget(label("Alarme", "kartentitel"))
        if not alarme:
            h = label("Noch keine Alarme. Öffne einen Wert und klicke auf „+ Alarm“.", "leise")
            h.setWordWrap(True)
            self.kl.addWidget(h)
            return
        for a in sorted(alarme, key=lambda a: (not a["aktiv"], a["ticker"])):
            d = daten.get(a["ticker"])
            zeile = QHBoxLayout()
            zeile.setSpacing(12)
            av = avatar(a["ticker"], 30)
            zeile.addWidget(av)
            name = d["name"] if d else a["ticker"]
            kurs = (f" · jetzt {kurs_text(kurs_jetzt(d)[0])} {d['waehrung']}"
                    if d and a["art"] != "signal" else "")
            tx = label(f"<b>{a['ticker']}</b>&nbsp;&nbsp;<span style='color:{T['leise']}'>"
                       f"{name}</span><br>{alarm_text(a, d['waehrung'] if d else '')}"
                       f"<span style='color:{T['leise']}'>{kurs}</span>"
                       f"&nbsp;&nbsp;{alarm_status(a)}")
            tx.setTextFormat(Qt.RichText)
            tx.setStyleSheet("font-size: 13px;")
            tx.setCursor(Qt.PointingHandCursor)
            tx.mousePressEvent = lambda _e, t=a["ticker"]: self.oeffnen.emit(t)
            zeile.addWidget(tx, 1)
            if not a["aktiv"] and a["art"] != "signal":
                w = QPushButton("Wieder an", objectName="chip")
                w.setCursor(Qt.PointingHandCursor)
                w.clicked.connect(lambda _=False, i=a["id"]: self.alarm_wieder.emit(i))
                zeile.addWidget(w)
            weg = icon_knopf("x", "Löschen", 14)
            weg.clicked.connect(lambda _=False, i=a["id"]: self.alarm_weg.emit(i))
            zeile.addWidget(weg)
            self.kl.addLayout(zeile)


class Meldung(QFrame):
    """Kurz eingeblendeter Hinweis oben im Fenster (zusätzlich zur Mitteilung)."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("meldung")
        self.setStyleSheet(f"QFrame#meldung {{ background: {T['solid']}; border: 1px solid "
                           f"rgba(25,230,162,90); border-radius: 10px; }}")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 12, 18, 12)
        lay.setSpacing(12)
        symbol = icon_label("glocke", GOLD, 18)
        lay.addWidget(symbol, 0, Qt.AlignTop)
        self.text = QLabel()
        self.text.setTextFormat(Qt.RichText)
        self.text.setWordWrap(True)
        self.text.setStyleSheet("font-size: 13px;")
        lay.addWidget(self.text, 1)
        self.hide()
        self.timer = QTimer(self, singleShot=True, interval=9000)
        self.timer.timeout.connect(self.hide)

    def zeige(self, titel: str, text: str) -> None:
        self.text.setText(f"<span style='font-weight:600'>{titel}</span><br>"
                          f"<span style='color:{T['leise']}'>{text}</span>")
        breite = min(520, self.parent().width() - 40)
        self.setFixedWidth(breite)
        self.adjustSize()
        self.move((self.parent().width() - breite) // 2, 64)
        self.raise_()
        self.show()
        self.timer.start()

    def mousePressEvent(self, _e):
        self.hide()


class Detail(QWidget):
    merken_geklickt = Signal(str)

    def __init__(self):
        super().__init__()
        self.setObjectName("detail")
        self.daten = None
        self.ticker = ""
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 16)
        lay.setSpacing(14)

        # Kurs-Panel mit Kopf, Preis und Kerzen-Chart
        chart_karte = karte()
        cl = QVBoxLayout(chart_karte)
        cl.setContentsMargins(22, 18, 18, 12)
        cl.setSpacing(6)
        namenszeile = QHBoxLayout()
        namenszeile.setSpacing(8)
        self.kopf_punkt = punkt(T["grau"])
        namenszeile.addWidget(self.kopf_punkt)
        self.unter = label("", "kartenname")
        namenszeile.addWidget(self.unter)
        namenszeile.addStretch()
        self.stand = label("", "leise")
        namenszeile.addWidget(self.stand)
        cl.addLayout(namenszeile)

        titelzeile = QHBoxLayout()
        titelzeile.setSpacing(14)
        self.name = KuerzLabel("kartentitel")
        self.merken = QPushButton()
        self.merken.setCursor(Qt.PointingHandCursor)
        self.merken.clicked.connect(lambda: self.merken_geklickt.emit(self.ticker))
        self.logo = avatar("", 44)
        titelzeile.addWidget(self.logo)
        titelzeile.addWidget(self.name)
        titelzeile.addWidget(self.merken)
        titelzeile.addStretch()
        self.badge = QLabel()
        self.badge.setAlignment(Qt.AlignCenter)
        titelzeile.addWidget(self.badge)
        cl.addLayout(titelzeile)

        preiszeile = QHBoxLayout()
        preisbox = QVBoxLayout()
        preisbox.setSpacing(0)
        self.preis = label("", "preis")
        self.change = label("")
        preisbox.addWidget(self.preis)
        preisbox.addWidget(self.change)
        preiszeile.addLayout(preisbox)
        preiszeile.addStretch()
        self.badge_info = label("", "leise")
        self.badge_info.setWordWrap(True)
        self.badge_info.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        preiszeile.addWidget(self.badge_info)
        cl.addLayout(preiszeile)

        self.chart = Chart()
        cl.addWidget(self.chart)

        fusszeile = QHBoxLayout()
        fusszeile.setSpacing(2)
        self.zeitraum = QButtonGroup(self)
        for i, (txt, monate) in enumerate(ZEITRAEUME):
            b = QPushButton(txt, objectName="seg", checkable=True)
            b.setCursor(Qt.PointingHandCursor)
            b.setProperty("monate", monate)
            self.zeitraum.addButton(b, i)
            fusszeile.addWidget(b)
        self.zeitraum.button(5).setChecked(True)
        self.zeitraum.idClicked.connect(lambda _: self.zeichne_chart())
        self.intraday: dict[tuple[str, str], dict] = {}
        self.intraday_ladend: set[tuple[str, str]] = set()
        fusszeile.addStretch()
        einst = QSettings("trading-signale", "app")
        self.extras = set(einst.value("chart_extras", [], type=list) or [])
        self.extra_knoepfe = {}
        for key, txt, tipp in (("bollinger", "Bollinger", "Bollinger-Bänder: 20-Tage-Schnitt "
                                "± 2 Standardabweichungen – zeigt, wie stark der Kurs schwankt"),
                               ("volumen", "Volumen", "Handelsvolumen pro Tag (bzw. Woche)"),
                               ("52w", "52W", "52-Wochen-Hoch und -Tief")):
            b = QPushButton(txt, objectName="seg", checkable=True)
            b.setToolTip(tipp)
            b.setCursor(Qt.PointingHandCursor)
            b.setChecked(key in self.extras)
            b.toggled.connect(lambda an, k=key: self.extra_umschalten(k, an))
            self.extra_knoepfe[key] = b
            fusszeile.addWidget(b)
        fusszeile.addSpacing(14)
        self.vergleich: list[str] = []
        self.alle_daten: dict = {}
        self.vergleich_knopf = mit_pfeil(QPushButton("Vergleichen", objectName="seg"))
        self.vergleich_knopf.setCursor(Qt.PointingHandCursor)
        self.vergleich_knopf.setToolTip("Bis zu drei andere Werte prozentual im selben Chart")
        self.vergleich_knopf.clicked.connect(self.vergleich_menue)
        fusszeile.addWidget(self.vergleich_knopf)
        self.chart.setToolTip("")
        cl.addLayout(fusszeile)
        lay.addWidget(chart_karte, 1)

        # Mein Depot + Alarme
        self.k_konto = KontoKarte()
        lay.addWidget(self.k_konto)
        self.k_notiz = NotizKarte()
        lay.addWidget(self.k_notiz)

        # Indikatoren
        reihe = QHBoxLayout()
        reihe.setSpacing(14)
        self.k_trend = IndikatorKarte(
            "Trend", "Vergleicht den 50-Tage- mit dem 200-Tage-Durchschnitt.")
        self.k_rsi = IndikatorKarte(
            "RSI", "Relative Stärke (0–100): unter 30 überverkauft, über 70 überkauft.")
        self.k_macd = IndikatorKarte(
            "MACD", "Misst, ob der Kursschwung zu- oder abnimmt.")
        for k in (self.k_trend, self.k_rsi, self.k_macd):
            reihe.addWidget(k, 1)
        lay.addLayout(reihe)

        # Begründung
        self.k_begruendung = BegruendungKarte()
        lay.addWidget(self.k_begruendung)

        # Prognose
        self.k_prognose = PrognoseKarte()
        lay.addWidget(self.k_prognose)

        # Was wäre wenn (Sparplan-Rückblick)
        self.k_sparplan = SparplanKarte()
        lay.addWidget(self.k_sparplan)

        # Infos & Nachrichten
        self.k_info = InfoNachrichtenKarte()
        lay.addWidget(self.k_info)

        # Backtest + Orders
        unten = QHBoxLayout()
        unten.setSpacing(14)
        bt_karte = karte()
        bl = QVBoxLayout(bt_karte)
        bl.setContentsMargins(18, 14, 18, 16)
        bl.setSpacing(8)
        kartenkopf(bl, "Backtest")
        self.bt_titel = label("", "sektion")
        bl.addWidget(self.bt_titel)
        g = QGridLayout()
        g.setHorizontalSpacing(28)
        g.setVerticalSpacing(4)
        for c, t in enumerate(["", "Rendite", "Max. Verlust", ""]):
            g.addWidget(label(t, "klein"), 0, c)
        g.addWidget(label("Regel", "h2"), 1, 0)
        g.addWidget(label("Einfach halten", "h2"), 2, 0)
        self.bt = {}
        for r, key in ((1, "regel"), (2, "halten")):
            self.bt[key] = (label("", "h2"), label("", "leise"), label("", "klein"))
            for c, w in enumerate(self.bt[key], start=1):
                g.addWidget(w, r, c)
        g.setColumnStretch(3, 1)
        bl.addLayout(g)
        self.bt_fazit = label("", "leise")
        self.bt_fazit.setWordWrap(True)
        bl.addWidget(self.bt_fazit)
        unten.addWidget(bt_karte, 3)

        or_karte = karte()
        ol = QVBoxLayout(or_karte)
        ol.setContentsMargins(18, 14, 18, 16)
        ol.setSpacing(6)
        kartenkopf(ol, "Signale der Regel")
        self.orders = label("", "")
        self.orders.setWordWrap(True)
        self.orders.setTextFormat(Qt.RichText)
        self.orders.setStyleSheet("font-size: 13px;")
        ol.addWidget(self.orders)
        self.neu = label("", "klein")
        self.neu.setWordWrap(True)
        ol.addWidget(self.neu)
        ol.addStretch()
        unten.addWidget(or_karte, 2)
        lay.addLayout(unten)

        for lbl in self.findChildren(QLabel):
            if lbl.property("rolle") in ("klein", "leise") and not lbl.wordWrap():
                lbl.setWordWrap(True)
        for w_r, w_dd, _ in self.bt.values():  # Zahlen im Backtest nicht umbrechen
            w_r.setWordWrap(False)
            w_dd.setWordWrap(False)
        fuss = label("Keine Anlageberatung. Die Signale folgen festen Regeln; vergangene "
                     "Ergebnisse sagen nichts über die Zukunft. Daten: Yahoo Finance.", "klein")
        fuss.setAlignment(Qt.AlignCenter)
        fuss.setWordWrap(True)
        lay.addWidget(fuss)

    vergleich_laden = Signal(str)

    def extra_umschalten(self, key: str, an: bool) -> None:
        (self.extras.add if an else self.extras.discard)(key)
        QSettings("trading-signale", "app").setValue("chart_extras", sorted(self.extras))
        self.zeichne_chart()

    def vergleich_menue(self) -> None:
        menue = QMenu(self)
        kandidaten = [t for t in dict.fromkeys(
            getattr(self, "vergleich_kandidaten", []) + ["EUNL.DE", "VWCE.DE", "^GDAXI",
                                                         "^GSPC", "BTC-USD", "GC=F"])
            if t != self.ticker]
        namen = {"^GDAXI": "DAX", "^GSPC": "S&P 500", "GC=F": "Gold", "EUNL.DE": "MSCI World ETF",
                 "VWCE.DE": "FTSE All-World ETF"}
        for t in kandidaten[:24]:
            d = self.alle_daten.get(t)
            name = namen.get(t) or (kurzer_name(d["name"]) if d else "")
            a = QAction(f"{t}   {name}".replace("&", "&&"), menue, checkable=True)
            a.setChecked(t in self.vergleich)
            a.setEnabled(t in self.vergleich or len(self.vergleich) < 3)
            a.toggled.connect(lambda an, t=t: self.vergleich_setzen(t, an))
            menue.addAction(a)
        if self.vergleich:
            menue.addSeparator()
            aus = QAction("Vergleich beenden", menue)
            aus.triggered.connect(lambda: self.vergleich_setzen(None, False))
            menue.addAction(aus)
        menue.exec(self.vergleich_knopf.mapToGlobal(self.vergleich_knopf.rect().bottomLeft()))

    def vergleich_setzen(self, ticker, an: bool) -> None:
        if ticker is None:
            self.vergleich = []
        elif an and ticker not in self.vergleich:
            self.vergleich.append(ticker)
            if ticker not in self.alle_daten:
                self.vergleich_laden.emit(ticker)
        elif not an and ticker in self.vergleich:
            self.vergleich.remove(ticker)
        self.vergleich_knopf.setText(f"Vergleich · {len(self.vergleich)}" if self.vergleich
                                     else "Vergleichen")
        if self.vergleich and self.zeitraum_art() in INTRADAY:
            self.zeitraum.button(5).setChecked(True)
        self.zeichne_chart()

    def zeitraum_art(self):
        return self.zeitraum.checkedButton().property("monate")

    def zeichne_chart(self) -> None:
        if not self.daten:
            return
        art = self.zeitraum_art()
        if self.vergleich and art not in INTRADAY:
            andere = [(t, self.alle_daten[t]) for t in self.vergleich if t in self.alle_daten]
            self.chart.zeichne_vergleich(self.daten, andere, art, self.ticker)
            return
        if art not in INTRADAY:
            self.chart.zeichne(self.daten, art, self.extras)
            return
        iv = self.intraday.get((self.ticker, art))
        if iv:
            self.chart.zeichne_intraday(self.daten, iv, art)
        else:
            self.chart.leer("Lade Kursverlauf …")
        if not iv or time.time() - iv["zeit"] > 60:
            self.intraday_laden(self.ticker, art)

    def intraday_laden(self, ticker: str, art: str) -> None:
        if (ticker, art) in self.intraday_ladend:
            return
        self.intraday_ladend.add((ticker, art))
        job = IntradayJob(ticker, art)
        job.signale.fertig.connect(self._intraday_da)
        QThreadPool.globalInstance().start(job)

    def _intraday_da(self, ticker: str, art: str, iv) -> None:
        self.intraday_ladend.discard((ticker, art))
        if iv:
            self.intraday[(ticker, art)] = iv
        if ticker == self.ticker and self.daten and self.zeitraum_art() == art:
            if iv:
                self.chart.zeichne_intraday(self.daten, iv, art)
            elif (ticker, art) not in self.intraday:
                self.chart.leer("Für diesen Zeitraum liefert Yahoo gerade keine Kurse.")

    def intraday_auffrischen(self) -> None:
        """Wird jede Sekunde aufgerufen: 1T/1W-Verlauf höchstens jede Minute neu laden."""
        art = self.zeitraum_art()
        if self.daten and art in INTRADAY:
            iv = self.intraday.get((self.ticker, art))
            if iv and time.time() - iv["zeit"] > 60:
                self.intraday_laden(self.ticker, art)

    def setze_gemerkt(self, gemerkt: bool) -> None:
        if gemerkt:
            self.merken.setText(" Gemerkt")
            self.merken.setIcon(icon("stern", SILBER, 14, gefuellt=True))
            self.merken.setToolTip("Klicken, um nicht mehr zu merken")
            hinter, farbe, rand = "rgba(235,245,242,14)", SILBER, "rgba(235,245,242,60)"
        else:
            self.merken.setText(" Merken")
            self.merken.setIcon(icon("stern", T["leise"], 14))
            self.merken.setToolTip("Zu „Meine“ hinzufügen")
            hinter, farbe, rand = "transparent", T["leise"], T["rand"]
        self.merken.setStyleSheet(
            f"QPushButton {{ background: {hinter}; color: {farbe}; border: 1px solid {rand};"
            f" border-radius: 7px; padding: 3px 10px; font-size: 12px; font-weight: 500; }}"
            f"QPushButton:hover {{ border-color: {SILBER}; color: {SILBER}; }}")

    def kopf_kurs(self, ticker: str, d: dict) -> None:
        """Kurs, Änderung und Stand im Kopf – wird auch bei Live-Updates aufgerufen."""
        preis, ch, zeit = kurs_jetzt(d)
        if zeit is not None:
            lokal = zeit.tz_convert(datetime.now().astimezone().tzinfo)
            alter = (pd.Timestamp.now(tz=lokal.tz) - lokal).total_seconds()
            verz = d.get("verzoegerung") or 0
            if alter >= 1800:
                stand = f"Letzter Kurs {lokal:%d.%m. %H:%M}"
            elif verz:
                stand = (f"<span style='color:{T['orange']}'>●</span>&nbsp;ca. {verz} Min. "
                         f"verzögert · {lokal:%H:%M:%S}")
            else:
                stand = f"<span style='color:{T['gruen']}'>●</span>&nbsp;Live · {lokal:%H:%M:%S}"
        else:
            stand = f"Schlusskurs {d['df'].index[-1]:%d.%m.%Y}"
        self.stand.setText(stand)
        teile = [ticker, d["typ"], d["boerse"] if d["boerse"] != d["typ"] else ""]
        self.unter.setText("  ·  ".join(x for x in teile if x))
        alt = getattr(self, "_letzter_preis", None)
        if getattr(self, "_letzter_ticker", None) != ticker:
            alt = None
        self._letzter_preis, self._letzter_ticker = preis, ticker
        if alt is not None and preis != alt:
            blinken(self.preis, T["gruen"] if preis > alt else T["rot"])
        self.preis.setText(f"{kurs_text(preis)}&nbsp;<span style='font-size:18px'>"
                           f"{d['waehrung']}</span>")
        absolut = preis - preis / (1 + ch)
        f = wert_farbe(ch)
        self.change.setText(
            f"<span style='color:{f}; font-weight:500; font-size:13px'>{pfeil(ch)}"
            f"&nbsp;&nbsp;&nbsp;{pfeil(absolut, 2, ' ' + d['waehrung'], 1)}</span>"
            f"&nbsp;&nbsp;<span style='color:{T['leise']}; font-size:13px'>heute</span>")

    def zeige(self, ticker: str, d: dict, gemerkt: bool = False) -> None:
        self.ticker = ticker
        self.setze_gemerkt(gemerkt)
        self.daten = d
        df, bt = d["df"], d["bt"]
        z = df.iloc[-1]
        score = int(z["score"])
        sig = s.empfehlung(score)

        self.name.setze(d["name"])
        self.name.setToolTip(d["name"])
        self.kopf_kurs(ticker, d)
        self.logo.setProperty("avatar_ticker", ticker)
        avatar_fuellen(self.logo)
        farbe = signal_farbe(sig)
        self.kopf_punkt.setStyleSheet(f"background: {farbe}; border-radius: 5px;")
        kurzname = kurzer_name(d["name"])
        for lbl in self.findChildren(QLabel):
            if lbl.property("kartenname"):
                lbl.setText(kurzname)
            elif lbl.property("rolle") == "kartenpunkt":
                lbl.setStyleSheet(f"background: {farbe}; border-radius: 5px;")
        self.badge.setText(sig)
        self.badge.setStyleSheet(pill_stil(farbe, gross=True))
        self.badge_info.setText(f"Signal laut Regel · Score {score:+d} von ±3")
        self.k_begruendung.setze(d["begruendung"], ticker)
        self.k_prognose.setze(d["prognose"], d["waehrung"], ticker)
        self.k_info.setze_infos(d)
        self.k_sparplan.setze(d)

        # Indikatoren
        tr = int(z["s_trend"])
        self.k_trend.setze(
            "Aufwärts" if tr > 0 else "Abwärts",
            "Ø 50 über Ø 200" if tr > 0 else "Ø 50 unter Ø 200", tr,
            f"Ø 50 Tage {kurs_text(z['sma_kurz'])} · Ø 200 Tage {kurs_text(z['sma_lang'])}")
        rs = int(z["s_rsi"])
        self.k_rsi.setze(
            zahl(z["rsi"], 0), {1: "überverkauft", -1: "überkauft", 0: "neutral"}[rs], rs,
            f"unter {s.RSI_UNTEN} überverkauft · über {s.RSI_OBEN} überkauft")
        self.k_rsi.balken.setValue(int(z["rsi"]))
        self.k_rsi.balken.setStyleSheet(
            f"QProgressBar::chunk {{ background: {wert_farbe(rs) if rs else T['akzent']}; }}")
        self.k_rsi.balken.show()
        mc = int(z["s_macd"])
        self.k_macd.setze(
            "Steigend" if mc > 0 else "Fallend",
            "MACD über Signallinie" if mc > 0 else "MACD unter Signallinie", mc,
            f"MACD {zahl(z['macd'], 3)} · Signal {zahl(z['macd_signal'], 3)}")

        self.zeichne_chart()

        # Backtest
        self.bt_titel.setText(f"Seit {df.index[0]:%d.%m.%Y} · "
                              f"{zahl(s.GEBUEHR * 100, 1)} % Gebühr pro Order")
        for key, r, dd in (("regel", bt.rendite_strategie, bt.max_dd_strategie),
                           ("halten", bt.rendite_halten, bt.max_dd_halten)):
            w_r, w_dd, w_x = self.bt[key]
            w_r.setText(prozent(r))
            w_r.setStyleSheet(f"color: {wert_farbe(r)};")
            w_dd.setText(prozent(dd))
        self.bt["regel"][2].setText(f"{bt.trades} Käufe · {bt.investiert_anteil * 100:.0f} % "
                                    f"der Zeit investiert")
        diff = (bt.rendite_strategie - bt.rendite_halten) * 100
        if abs(diff) < 1:
            fazit = "Regel und einfaches Halten lagen etwa gleichauf."
        elif diff > 0:
            fazit = f"Die Regel lag {zahl(diff, 0)} Prozentpunkte vor einfachem Halten."
        else:
            fazit = f"Einfaches Halten lag {zahl(-diff, 0)} Prozentpunkte vor der Regel."
        self.bt_fazit.setText(fazit)

        zeilen = []
        for datum, art, kurs in reversed(bt.trades_liste[-5:]):
            f = T["gruen"] if art == "Kauf" else T["rot"]
            pfeil = "▲" if art == "Kauf" else "▼"
            zeilen.append(
                f"<tr><td style='color:{f}'>{pfeil}&nbsp;</td>"
                f"<td style='color:{T['leise']}'>{datum:%d.%m.%Y}&nbsp;&nbsp;</td>"
                f"<td><span style='font-weight:500'>{art}</span>&nbsp;&nbsp;</td>"
                f"<td align='right'>{kurs_text(kurs)}</td></tr>")
        self.orders.setText(f"<table cellspacing='0' cellpadding='3'>{''.join(zeilen)}</table>"
                            if zeilen else "Keine Orders im Zeitraum.")
        ereignisse = s.letzte_ereignisse(df)
        self.neu.setText("Neu in den letzten 10 Tagen: " + (", ".join(ereignisse) or "nichts"))


# ---------------------------------------------------------------- Fenster


class EinstellungenDialog(QDialog):
    def __init__(self, parent, werte: dict, menue_optionen: list[tuple[str, str]]):
        super().__init__(parent)
        self.setWindowTitle("Einstellungen")
        self.setMinimumWidth(460)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(10)
        lay.addWidget(label("Einstellungen", "kartentitel"))

        def abschnitt(txt):
            l_ = label(txt, "h2")
            l_.setContentsMargins(0, 8, 0, 0)
            lay.addWidget(l_)

        abschnitt("Hintergrund")
        self.autostart = QCheckBox("Beim Anmelden am Mac automatisch starten (ohne Fenster)")
        self.hintergrund = QCheckBox("Beim Schließen des Fensters im Hintergrund weiterlaufen")
        self.autostart.setChecked(werte["autostart"])
        self.hintergrund.setChecked(werte["hintergrund"])
        lay.addWidget(self.autostart)
        lay.addWidget(self.hintergrund)
        h = label("Nur so kommen Alarme auch, wenn das Fenster zu ist. " + pfade.BEENDEN_TIPP,
                  "klein")
        h.setWordWrap(True)
        lay.addWidget(h)

        abschnitt("Menüleiste" if pfade.MAC else "Taskleisten-Symbol")
        zeile = QHBoxLayout()
        zeile.addWidget(label("Oben in der Menüleiste zeigen" if pfade.MAC else
                              "Im Symbol unten rechts anzeigen (Tooltip)", "leise"))
        self.menueleiste = QComboBox()
        for key, txt in menue_optionen:
            self.menueleiste.addItem(txt, key)
        i = self.menueleiste.findData(werte["menueleiste"])
        self.menueleiste.setCurrentIndex(max(i, 0))
        zeile.addWidget(self.menueleiste, 1)
        lay.addLayout(zeile)

        abschnitt("Mitteilungen")
        self.termine = QCheckBox("Tag vor Quartalszahlen melden (Depot und „Meine“)")
        self.termine.setChecked(werte["termine"])
        lay.addWidget(self.termine)

        abschnitt("Depot")
        zeile = QHBoxLayout()
        zeile.addWidget(label("Sparerpauschbetrag für die Steuer-Schätzung", "leise"))
        self.freibetrag = QComboBox()
        self.freibetrag.addItem("1.000 € (allein)", 1000.0)
        self.freibetrag.addItem("2.000 € (zusammen veranlagt)", 2000.0)
        self.freibetrag.addItem("0 € (schon anderweitig genutzt)", 0.0)
        self.freibetrag.setCurrentIndex(max(0, self.freibetrag.findData(werte["freibetrag"])))
        zeile.addWidget(self.freibetrag, 1)
        lay.addLayout(zeile)

        abschnitt("Watchlist")
        zeile = QHBoxLayout()
        zeile.addWidget(label("Kategorie „Unter … €“: Preisgrenze", "leise"))
        self.grenze = QSpinBox()
        self.grenze.setRange(1, 100_000)
        self.grenze.setSuffix(" €")
        self.grenze.setValue(int(werte["preisgrenze"]))
        self.grenze.setButtonSymbols(QSpinBox.NoButtons)
        self.grenze.setFixedWidth(90)
        zeile.addWidget(self.grenze)
        zeile.addStretch()
        lay.addLayout(zeile)

        lay.addSpacing(6)
        lay.addWidget(label(f"Vyntro {update.VERSION}", "klein"))
        knoepfe = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        knoepfe.button(QDialogButtonBox.Save).setText("Speichern")
        knoepfe.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        knoepfe.accepted.connect(self.accept)
        knoepfe.rejected.connect(self.reject)
        lay.addSpacing(6)
        lay.addWidget(knoepfe)

    def werte(self) -> dict:
        return {"autostart": self.autostart.isChecked(),
                "hintergrund": self.hintergrund.isChecked(),
                "menueleiste": self.menueleiste.currentData(),
                "termine": self.termine.isChecked(),
                "freibetrag": self.freibetrag.currentData(),
                "preisgrenze": float(self.grenze.value())}


def menueleisten_icon(text: str) -> QIcon:
    """Text als Bild für die Menüleiste (macOS färbt es passend hell/dunkel ein)."""
    schrift = QFont(pfade.SCHRIFT)
    schrift.setPixelSize(26)
    schrift.setWeight(QFont.Medium)
    breite = QFontMetrics(schrift).horizontalAdvance(text) + 8
    bild = QPixmap(breite, 36)
    bild.fill(Qt.transparent)
    p = QPainter(bild)
    p.setRenderHint(QPainter.TextAntialiasing)
    p.setFont(schrift)
    p.setPen(QColor("black"))
    p.drawText(bild.rect(), Qt.AlignCenter, text)
    p.end()
    icon = QIcon(bild)
    icon.setIsMask(True)
    return icon


class Menueleiste(QObject):
    """Symbol mit Kurs oder Depotwert oben in der Mac-Menüleiste, mit kleinem Menü."""

    def __init__(self, fenster: "Fenster"):
        super().__init__(fenster)
        self.f = fenster
        self.tray = QSystemTrayIcon(fenster)
        self.menue = QMenu()
        self.menue.aboutToShow.connect(self.menue_bauen)
        self.tray.setContextMenu(self.menue)
        if not pfade.MAC:  # Windows: Klick aufs Symbol öffnet das Fenster
            self.tray.activated.connect(
                lambda grund: self.f.zeigen() if grund in (
                    QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) else None)
        self._text = None
        self.aktualisieren()
        self.tray.show()

    def text(self) -> str:
        wahl = self.f.einstellungen.value("menueleiste", "depot", type=str)
        if wahl == "aus":
            return "V"
        if wahl == "depot":
            pos = konto.positionen(self.f.kaeufe)
            if not pos:
                return "V"
            wert = einstand = heute = 0.0
            for t, p in pos.items():
                d = self.f.daten.get(t)
                if not d or not d.get("eur_faktor"):
                    return "V …"
                preis, ch, _ = kurs_jetzt(d)
                w = p["stueck"] * preis * d["eur_faktor"]
                wert += w
                heute += w - w / (1 + ch)
                einstand += p["einstand"]
            vorher = wert - heute
            pct = heute / vorher if vorher else 0
            return f"{zahl(wert, 0)} € {'▲' if pct > 0 else '▼' if pct < 0 else '■'}" \
                   f"{zahl(abs(pct) * 100, 1)}%"
        d = self.f.daten.get(wahl)
        if not d:
            return f"{wahl} …"
        preis, ch, _ = kurs_jetzt(d)
        kurz = re.sub(r"[-.].*$", "", wahl)
        return f"{kurz} {kurs_text(preis)} {'▲' if ch > 0 else '▼' if ch < 0 else '■'}" \
               f"{zahl(abs(ch) * 100, 1)}%"

    def aktualisieren(self) -> None:
        text = self.text()
        if text != self._text:
            self._text = text
            if pfade.MAC:  # Text direkt in der Menüleiste
                self.tray.setIcon(menueleisten_icon(text))
                self.tray.setToolTip("Vyntro")
            else:  # Windows: Logo im Infobereich, Kurs im Tooltip
                if self.tray.icon().isNull():
                    self.tray.setIcon(QApplication.windowIcon())
                self.tray.setToolTip(f"Vyntro · {text}")

    def menue_bauen(self) -> None:
        m = self.menue
        m.clear()
        oeffnen = m.addAction("Vyntro öffnen")
        oeffnen.triggered.connect(self.f.zeigen)
        m.addSeparator()
        for t in self.f.meine[:12]:
            d = self.f.daten.get(t)
            if not d:
                continue
            preis, ch, _ = kurs_jetzt(d)
            sig = s.empfehlung(int(d["df"]["score"].iloc[-1]))
            a = m.addAction(f"{t}   {kurs_text(preis)} {d['waehrung']}   {pfeil(ch)}   · {sig}")
            a.triggered.connect(lambda _=False, t=t: (self.f.zeigen(), self.f.oeffnen(t)))
        m.addSeparator()
        zeigen = m.addMenu("In der Menüleiste zeigen" if pfade.MAC else "Im Symbol anzeigen")
        wahl = self.f.einstellungen.value("menueleiste", "depot", type=str)
        for key, txt in self.f.menueleisten_optionen():
            a = zeigen.addAction(txt)
            a.setCheckable(True)
            a.setChecked(key == wahl)
            a.triggered.connect(lambda _=False, k=key: self.waehlen(k))
        m.addAction("Einstellungen …").triggered.connect(
            lambda: (self.f.zeigen(), self.f.einstellungen_oeffnen()))
        m.addSeparator()
        m.addAction("Vyntro beenden").triggered.connect(self.f.beenden)

    def waehlen(self, key: str) -> None:
        self.f.einstellungen.setValue("menueleiste", key)
        self.aktualisieren()


class QuitWaechter(QObject):
    """Merkt sich, wenn die App wirklich beendet werden soll (⌘Q), damit das Schließen
    des Fensters dann nicht nur in den Hintergrund führt."""

    def __init__(self, fenster):
        super().__init__(fenster)
        self.f = fenster

    def eventFilter(self, obj, e):
        if e.type() == QEvent.Quit:
            self.f.wirklich_beenden = True
        return False


class Heatmap(QWidget):
    """Kacheln je Wert: Farbe = Tagesänderung, Größe = Gewicht (z. B. Depotanteil)."""
    geklickt = Signal(str)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(300)
        self.setMouseTracking(True)
        self.eintraege: list[tuple[str, float, float, str]] = []
        self.kacheln: list[tuple[QRectF, tuple]] = []

    def setze(self, eintraege) -> None:
        self.eintraege = [e for e in eintraege if e[1] > 0]
        self.update()

    @staticmethod
    def _teilen(items, r: QRectF, out) -> None:
        if not items:
            return
        if len(items) == 1:
            out.append((r, items[0]))
            return
        gesamt = sum(i[1] for i in items)
        links, summe = [], 0.0
        for i in items:  # in zwei etwa gleich schwere Gruppen teilen
            if summe and summe + i[1] / 2 > gesamt / 2:
                break
            links.append(i)
            summe += i[1]
        rechts = items[len(links):]
        anteil = summe / gesamt
        if r.width() >= r.height():
            a = QRectF(r.x(), r.y(), r.width() * anteil, r.height())
            b = QRectF(r.x() + a.width(), r.y(), r.width() - a.width(), r.height())
        else:
            a = QRectF(r.x(), r.y(), r.width(), r.height() * anteil)
            b = QRectF(r.x(), r.y() + a.height(), r.width(), r.height() - a.height())
        Heatmap._teilen(links, a, out)
        Heatmap._teilen(rechts, b, out)

    @staticmethod
    def farbe(ch: float) -> QColor:
        staerke = max(-1.0, min(1.0, ch / 0.03))  # ±3 % = volle Farbe
        basis = QColor(T["gruen"] if staerke >= 0 else T["rot"])
        neutral = QColor("#161918")
        f = abs(staerke) * 0.75
        return QColor(int(neutral.red() + (basis.red() - neutral.red()) * f),
                      int(neutral.green() + (basis.green() - neutral.green()) * f),
                      int(neutral.blue() + (basis.blue() - neutral.blue()) * f))

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        self.kacheln = []
        if not self.eintraege:
            p.setPen(QColor(T["leise"]))
            p.drawText(self.rect(), Qt.AlignCenter, "Noch keine Werte geladen.")
            p.end()
            return
        items = sorted(self.eintraege, key=lambda e: -e[1])
        if len({round(e[1], 6) for e in items}) == 1:  # alle gleich groß: Raster
            items = sorted(items, key=lambda e: -e[2])  # von stark im Plus bis stark im Minus
            n = len(items)
            spalten = max(1, round(math.sqrt(n * self.width() / max(1, self.height()))))
            zeilen_ = math.ceil(n / spalten)
            bw, bh = self.width() / spalten, self.height() / zeilen_
            for i, e in enumerate(items):
                self.kacheln.append((QRectF((i % spalten) * bw, (i // spalten) * bh, bw, bh), e))
        else:
            self._teilen(items, QRectF(self.rect()), self.kacheln)
        for r, (ticker, _g, ch, _name) in self.kacheln:
            k = r.adjusted(1.5, 1.5, -1.5, -1.5)
            pfad = QPainterPath()
            pfad.addRoundedRect(k, 6, 6)
            p.fillPath(pfad, self.farbe(ch))
            if k.width() < 38 or k.height() < 26:
                continue
            gross = max(10, min(20, int(min(k.width() / 5.5, k.height() / 3))))
            schrift = QFont(pfade.SCHRIFT)
            schrift.setPixelSize(gross)
            schrift.setWeight(QFont.DemiBold)
            p.setFont(schrift)
            p.setPen(QColor("#f4f6f5"))
            kurz = re.sub(r"[-.].*$", "", ticker)
            p.drawText(k.adjusted(0, -gross * 0.45, 0, 0), Qt.AlignCenter, kurz)
            schrift.setPixelSize(max(9, int(gross * 0.72)))
            schrift.setWeight(QFont.Normal)
            p.setFont(schrift)
            p.setPen(QColor(235, 245, 242, 200))
            p.drawText(k.adjusted(0, gross * 1.0, 0, 0), Qt.AlignCenter, prozent(ch, 2))
        p.end()

    def _kachel_bei(self, pos):
        for r, e in self.kacheln:
            if r.contains(QPointF(pos)):
                return e
        return None

    def mouseMoveEvent(self, e):
        k = self._kachel_bei(e.position() if hasattr(e, "position") else e.pos())
        self.setToolTip(f"{k[0]} · {k[3]}\nheute {prozent(k[2], 2)}" if k else "")
        self.setCursor(Qt.PointingHandCursor if k else Qt.ArrowCursor)

    def mousePressEvent(self, e):
        k = self._kachel_bei(e.position() if hasattr(e, "position") else e.pos())
        if k:
            self.geklickt.emit(k[0])


class ZahlItem(QTableWidgetItem):
    """Tabellenzelle, die nach Zahl (nicht nach Text) sortiert."""

    def __init__(self, text: str, wert: float):
        super().__init__(text)
        self.wert = wert
        self.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def __lt__(self, other):
        return self.wert < getattr(other, "wert", 0)


class MarktSeite(QWidget):
    """Heatmap und Filter über alle geprüften Werte."""
    oeffnen = Signal(str)

    def __init__(self):
        super().__init__(objectName="detail")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 16)
        lay.setSpacing(14)

        hk = karte()
        hl = QVBoxLayout(hk)
        hl.setContentsMargins(20, 16, 20, 16)
        hl.setSpacing(10)
        kopf = QHBoxLayout()
        kopf.addWidget(label("Heatmap", "kartentitel"))
        kopf.addSpacing(10)
        self.auswahl = QButtonGroup(self)
        for i, (key, txt) in enumerate((("liste", "Meine Liste"), ("depot", "Depot"),
                                        ("alle", "Alle geprüften"))):
            b = QPushButton(txt, objectName="seg", checkable=True)
            b.setCursor(Qt.PointingHandCursor)
            b.setProperty("key", key)
            self.auswahl.addButton(b, i)
            kopf.addWidget(b)
        self.auswahl.button(2).setChecked(True)
        self.auswahl.idClicked.connect(lambda _: self.heatmap_setzen())
        kopf.addStretch()
        kopf.addWidget(label("Farbe: Veränderung heute · Größe im Depot: Anteil", "klein"))
        hl.addLayout(kopf)
        self.heatmap = Heatmap()
        self.heatmap.geklickt.connect(self.oeffnen)
        hl.addWidget(self.heatmap)
        lay.addWidget(hk)

        fk = karte()
        fl = QVBoxLayout(fk)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(10)
        fl.addWidget(label("Filter", "kartentitel"))
        reihe = QHBoxLayout()
        reihe.setSpacing(10)
        self.filter: dict[str, QComboBox] = {}
        for key, txt, optionen in (
                ("art", "Art", [("alle", "Alle"), ("Aktie", "Aktien"), ("ETF", "ETFs"),
                                ("Krypto", "Krypto")]),
                ("signal", "Signal", [("alle", "Alle"), ("KAUFEN", "Kaufen"),
                                      ("HALTEN", "Halten"), ("VERKAUFEN", "Verkaufen")]),
                ("rsi", "RSI", [("alle", "Alle"), ("unter30", "unter 30"),
                                ("mitte", "30 – 70"), ("ueber70", "über 70")]),
                ("dividende", "Dividende", [(0.0, "egal"), (2.0, "ab 2 %"), (3.0, "ab 3 %"),
                                            (4.0, "ab 4 %"), (5.0, "ab 5 %")]),
                ("preis", "Kurs", [(0.0, "egal"), (10.0, "bis 10 €"), (50.0, "bis 50 €"),
                                   (100.0, "bis 100 €"), (500.0, "bis 500 €")]),
                ("tag", "Heute", [("alle", "egal"), ("plus", "im Plus"),
                                  ("minus", "im Minus"), ("stark", "über ±3 %")])):
            box = QVBoxLayout()
            box.setSpacing(3)
            box.addWidget(label(txt, "klein"))
            c = QComboBox()
            for wert, name in optionen:
                c.addItem(name, wert)
            c.currentIndexChanged.connect(lambda _: self.tabelle_setzen())
            box.addWidget(c)
            reihe.addLayout(box, 1)
            self.filter[key] = c
        fl.addLayout(reihe)
        self.treffer = label("", "klein")
        fl.addWidget(self.treffer)
        self.tabelle = QTableWidget(0, 8, objectName="tabelle")
        self.tabelle.setHorizontalHeaderLabels(["Ticker", "Name", "Kurs €", "Heute", "RSI",
                                                "Dividende", "Signal", "Score"])
        self.tabelle.verticalHeader().setVisible(False)
        self.tabelle.setShowGrid(False)
        self.tabelle.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabelle.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabelle.setSortingEnabled(True)
        self.tabelle.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        kopfzeile = self.tabelle.horizontalHeader()
        kopfzeile.setSectionResizeMode(QHeaderView.ResizeToContents)
        kopfzeile.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabelle.cellDoubleClicked.connect(
            lambda r, _c: self.oeffnen.emit(self.tabelle.item(r, 0).text()))
        self.tabelle.cellClicked.connect(
            lambda r, _c: self.oeffnen.emit(self.tabelle.item(r, 0).text()))
        fl.addWidget(self.tabelle)
        hinweis = label("Gefiltert werden alle Werte, die Vyntro prüft (deine Listen, Depot, "
                        "DAX 40, große US-Werte, Krypto). Ein Filter ist keine Empfehlung.",
                        "klein")
        hinweis.setWordWrap(True)
        fl.addWidget(hinweis)
        lay.addWidget(fk)
        lay.addStretch()
        self.daten: dict = {}
        self.liste: list[str] = []
        self.depot: dict = {}

    def setze(self, daten: dict, liste: list[str], depot: dict, tabelle: bool = True) -> None:
        self.daten, self.liste, self.depot = daten, liste, depot
        self.heatmap_setzen()
        if tabelle:
            self.tabelle_setzen()

    def heatmap_setzen(self) -> None:
        key = self.auswahl.checkedButton().property("key")
        if key == "liste":
            tickers = self.liste
        elif key == "depot":
            tickers = list(self.depot)
        else:
            tickers = [t for t in self.daten if t not in HOME_TICKER]
        eintraege = []
        for t in tickers:
            d = self.daten.get(t)
            if not d or d.get("typ") == "Index":
                continue
            preis, ch, _ = kurs_jetzt(d)
            gewicht = 1.0
            if key == "depot" and d.get("eur_faktor"):
                gewicht = self.depot[t]["stueck"] * preis * d["eur_faktor"]
            eintraege.append((t, gewicht, ch, d["name"]))
        self.heatmap.setze(eintraege)
        self.heatmap.setMinimumHeight(260 if len(eintraege) < 20 else 420)

    def tabelle_setzen(self) -> None:
        f = {k: c.currentData() for k, c in self.filter.items()}
        zeilen = []
        for t, d in self.daten.items():
            if d.get("typ") == "Index" or not d.get("eur_faktor") or t in HOME_TICKER:
                continue
            preis, ch, _ = kurs_jetzt(d)
            p_eur = preis * d["eur_faktor"]
            z = d["df"].iloc[-1]
            score = int(z["score"])
            sig = s.empfehlung(score)
            rsi = float(z["rsi"])
            div = float((d.get("info") or {}).get("dividendYield") or 0)
            if f["art"] != "alle" and d["typ"] != f["art"]:
                continue
            if f["signal"] != "alle" and sig != f["signal"]:
                continue
            if f["rsi"] == "unter30" and rsi >= 30 or f["rsi"] == "ueber70" and rsi <= 70:
                continue
            if f["rsi"] == "mitte" and not 30 <= rsi <= 70:
                continue
            if f["dividende"] and div < f["dividende"]:
                continue
            if f["preis"] and p_eur > f["preis"]:
                continue
            if (f["tag"] == "plus" and ch <= 0 or f["tag"] == "minus" and ch >= 0
                    or f["tag"] == "stark" and abs(ch) < 0.03):
                continue
            zeilen.append((t, d, p_eur, ch, rsi, div, sig, score))
        self.tabelle.setSortingEnabled(False)
        self.tabelle.setRowCount(len(zeilen))
        for r, (t, d, p_eur, ch, rsi, div, sig, score) in enumerate(zeilen):
            it = QTableWidgetItem(t)
            it.setIcon(logo_icon(t, 22))
            self.tabelle.setItem(r, 0, it)
            self.tabelle.setItem(r, 1, QTableWidgetItem(kurzer_name(d["name"])))
            self.tabelle.setItem(r, 2, ZahlItem(kurs_text(p_eur), p_eur))
            c = ZahlItem(prozent(ch, 2), ch)
            c.setForeground(QColor(wert_farbe(ch)))
            self.tabelle.setItem(r, 3, c)
            self.tabelle.setItem(r, 4, ZahlItem(zahl(rsi, 0), rsi))
            self.tabelle.setItem(r, 5, ZahlItem(f"{zahl(div, 2)} %" if div else "–", div))
            g = QTableWidgetItem(sig)
            g.setForeground(QColor(signal_farbe(sig)))
            self.tabelle.setItem(r, 6, g)
            self.tabelle.setItem(r, 7, ZahlItem(f"{score:+d}", score))
        self.tabelle.setSortingEnabled(True)
        self.tabelle.setFixedHeight(34 + 34 * max(1, len(zeilen)))
        for r in range(len(zeilen)):
            self.tabelle.setRowHeight(r, 34)
        self.treffer.setText(f"{len(zeilen)} Treffer von {len(self.daten)} geprüften Werten")


class Schnellsuche(QDialog):
    """⌘K: Wert oder Befehl tippen, Enter – fertig."""

    def __init__(self, fenster: "Fenster"):
        super().__init__(fenster, Qt.FramelessWindowHint | Qt.Popup)
        self.f = fenster
        self.setObjectName("palette")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(620)
        aussen = QVBoxLayout(self)
        aussen.setContentsMargins(0, 0, 0, 0)
        rahmen = QFrame(objectName="palettenrahmen")
        aussen.addWidget(rahmen)
        lay = QVBoxLayout(rahmen)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)
        zeile = QHBoxLayout()
        zeile.setContentsMargins(8, 0, 4, 0)
        zeile.addWidget(icon_label("suche", T["leise"], 17))
        self.eingabe = QLineEdit(objectName="paletteneingabe",
                                 placeholderText="Wert suchen oder Befehl … (z. B. Apple, BTC, "
                                                 "Depot, Alarm)")
        self.eingabe.textChanged.connect(self.filtern)
        self.eingabe.installEventFilter(self)
        zeile.addWidget(self.eingabe, 1)
        zeile.addWidget(label("esc", "klein"))
        lay.addLayout(zeile)
        self.liste = QListWidget(objectName="palettenliste")
        self.liste.setIconSize(QSize(24, 24))
        self.liste.setFixedHeight(380)
        self.liste.itemActivated.connect(self.ausfuehren)
        self.liste.itemClicked.connect(self.ausfuehren)
        lay.addWidget(self.liste)
        self.such_timer = QTimer(self, singleShot=True, interval=280)
        self.such_timer.timeout.connect(self._yahoo)
        self._yahoo_treffer: list = []
        self.filtern("")

    def befehle(self) -> list[tuple[str, str, object]]:
        f = self.f
        b = [("raster", "Markt: Heatmap und Filter", lambda: f.ansicht_setzen("markt")),
             ("depot", "Mein Depot", lambda: f.ansicht_setzen("depot")),
             ("glocke", "Alle Alarme", lambda: f.ansicht_setzen("alarme")),
             ("regler", "Einstellungen", f.einstellungen_oeffnen),
             ("neu", "Alle Kurse neu laden", f.alle_laden),
             ("funke", "Neue Liste anlegen", f.liste_neu),
             ("import", "Trade Republic importieren", f.depot_importieren),
             ("buch", "Anleitung", lambda: f.ansicht_setzen("anleitung"))]
        b += [("buch", f"Anleitung: {titel}", lambda k=kid: f.anleitung_oeffnen(k))
              for kid, titel, _g, _h in anleitung.KAPITEL]
        t = f.detail.ticker
        if t and f.ansicht == "detail":
            b += [("plus", f"Kauf / Verkauf eintragen: {t}", lambda: f.kauf_eintragen(t)),
                  ("glocke", f"Alarm anlegen: {t}", lambda: f.alarm_anlegen(t))]
        return b

    def filtern(self, text: str) -> None:
        text = text.strip().lower()
        self.liste.clear()
        for sym, name, aktion in self.befehle():
            if not text or text in name.lower():
                self._eintrag(icon(sym, T["text"], 18), name, "Befehl", aktion)
        treffer = []
        for t, d in self.f.daten.items():
            if not text or text in t.lower() or text in d["name"].lower():
                rang = (0 if t.lower().startswith(text) else 1 if text in t.lower() else 2,
                        t not in self.f.meine, t)
                treffer.append((rang, t, d))
        for _, t, d in sorted(treffer)[:12 if text else 6]:
            preis, ch, _ = kurs_jetzt(d)
            self._eintrag(logo_icon(t, 24), f"{t}   {kurzer_name(d['name'])}",
                          f"{kurs_text(preis)} {d['waehrung']}  {pfeil(ch)}",
                          lambda t=t: self.f.oeffnen(t))
        bekannt = set(self.f.daten)
        for sym, anzeige in self._yahoo_treffer:
            if sym not in bekannt:
                self._eintrag(logo_icon(sym, 24), anzeige, "Yahoo Finance",
                              lambda s_=sym: self.f.oeffnen(s_))
        if self.liste.count():
            self.liste.setCurrentRow(0)
        if len(text) >= 2:
            self.such_timer.start()

    def _eintrag(self, ic: QIcon, text: str, rechts: str, aktion) -> None:
        item = QListWidgetItem(ic, f"{text}")
        item.setToolTip(rechts)
        item.setData(Qt.UserRole, aktion)
        item.setData(Qt.UserRole + 1, rechts)
        item.setSizeHint(QSize(0, 38))
        self.liste.addItem(item)

    def _yahoo(self) -> None:
        begriff = self.eingabe.text().strip()
        if len(begriff) < 2:
            return
        job = Suche(begriff)
        job.signale.fertig.connect(self._yahoo_da)
        QThreadPool.globalInstance().start(job)

    def _yahoo_da(self, begriff: str, vorschlaege: list) -> None:
        if begriff != self.eingabe.text().strip():
            return
        self._yahoo_treffer = vorschlaege[:8]
        zeile = self.liste.currentRow()
        self.eingabe.blockSignals(True)
        self.filtern(begriff)
        self.eingabe.blockSignals(False)
        self.such_timer.stop()
        self.liste.setCurrentRow(max(0, zeile))

    def ausfuehren(self, item=None) -> None:
        item = item or self.liste.currentItem()
        if not item:
            return
        aktion = item.data(Qt.UserRole)
        self.accept()
        QTimer.singleShot(0, aktion)

    def eventFilter(self, obj, e):
        if obj is self.eingabe and e.type() == QEvent.KeyPress:
            if e.key() in (Qt.Key_Down, Qt.Key_Up):
                schritt = 1 if e.key() == Qt.Key_Down else -1
                self.liste.setCurrentRow(max(0, min(self.liste.count() - 1,
                                                    self.liste.currentRow() + schritt)))
                return True
            if e.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.ausfuehren()
                return True
        return super().eventFilter(obj, e)

    def zeigen(self) -> None:
        mitte = self.f.geometry().center()
        self.adjustSize()
        self.move(mitte.x() - self.width() // 2, self.f.geometry().top() + 110)
        self.eingabe.clear()
        self.filtern("")
        self.show()
        self.eingabe.setFocus()


HOME_INDIZES = [("^GDAXI", "DAX"), ("^GSPC", "S&P 500"), ("^IXIC", "Nasdaq"),
                ("BTC-USD", "Bitcoin"), ("GC=F", "Gold"), ("EURUSD=X", "EUR / USD")]


HOME_TICKER = {t for t, _ in HOME_INDIZES} - {"BTC-USD"}


class Klickflaeche(QFrame):
    geklickt = Signal()

    def __init__(self, objekt: str = "homekachel"):
        super().__init__(objectName=objekt)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, _e):
        self.geklickt.emit()


class HomeSeite(QWidget):
    """Startseite: Markt auf einen Blick, Depot, Bewegungen, Signale, Termine, Alarme."""
    oeffnen = Signal(str)
    ansicht = Signal(str)

    def __init__(self):
        super().__init__(objectName="detail")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 16)
        lay.setSpacing(14)
        kopf = QVBoxLayout()
        kopf.setContentsMargins(6, 6, 0, 2)
        kopf.setSpacing(2)
        self.gruss = label("", "h1")
        self.gruss.setStyleSheet("font-size: 24px; font-weight: 500;")
        self.untertitel = label("", "leise")
        kopf.addWidget(self.gruss)
        kopf.addWidget(self.untertitel)
        oben = QHBoxLayout()
        oben.addLayout(kopf, 1)
        hilfe = QPushButton("  Neu hier? Anleitung öffnen", objectName="chip")
        hilfe.setIcon(icon("buch", None, 15))
        hilfe.setCursor(Qt.PointingHandCursor)
        hilfe.clicked.connect(lambda: self.ansicht.emit("anleitung"))
        oben.addWidget(hilfe, 0, Qt.AlignBottom)
        lay.addLayout(oben)

        self.indizes = QGridLayout()
        self.indizes.setSpacing(12)
        self.index_kacheln = {}
        for i, (t, name) in enumerate(HOME_INDIZES):
            k = Klickflaeche()
            kl = QVBoxLayout(k)
            kl.setContentsMargins(14, 12, 14, 12)
            kl.setSpacing(2)
            n = label(name, "klein")
            wert = label("–", "zkurs")
            wert.setStyleSheet("font-size: 16px;")
            ch = label("", "klein")
            sp = Sparkline(150, 30)
            sp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            sp.setMinimumWidth(60)
            sp.setMaximumWidth(16777215)
            for w in (n, wert, ch, sp):
                kl.addWidget(w)
            k.geklickt.connect(lambda t=t: self.oeffnen.emit(t))
            self.indizes.addWidget(k, 0, i)
            self.index_kacheln[t] = (wert, ch, sp)
        lay.addLayout(self.indizes)

        def zwei(links: str, rechts: str):
            reihe = QHBoxLayout()
            reihe.setSpacing(14)
            boxen = []
            for titel in (links, rechts):
                k = karte()
                kl = QVBoxLayout(k)
                kl.setContentsMargins(20, 16, 20, 16)
                kl.setSpacing(6)
                kopfzeile = QHBoxLayout()
                kopfzeile.addWidget(label(titel, "h2"))
                kopfzeile.addStretch()
                kl.addLayout(kopfzeile)
                inhalt = QVBoxLayout()
                inhalt.setSpacing(2)
                kl.addLayout(inhalt)
                kl.addStretch()
                reihe.addWidget(k, 1)
                boxen.append((kopfzeile, inhalt))
            lay.addLayout(reihe)
            return boxen

        (dk, self.depot_box), (ak, self.alarm_box) = zwei("Mein Depot", "Alarme")
        for kopfzeile, ziel, txt in ((dk, "depot", "Zum Depot"), (ak, "alarme", "Alle Alarme")):
            b = QPushButton(txt, objectName="seg")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, z=ziel: self.ansicht.emit(z))
            kopfzeile.addWidget(b)
        (_, self.gewinner_box), (_, self.verlierer_box) = zwei("Gewinner heute",
                                                               "Verlierer heute")
        (sk, self.signal_box), (tk, self.termin_box) = zwei("Kaufsignale jetzt",
                                                            "Termine (14 Tage)")
        b = QPushButton("Im Markt filtern", objectName="seg")
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(lambda: self.ansicht.emit("markt"))
        sk.addWidget(b)
        fuss = label(f"Vyntro {update.VERSION} · Signale folgen festen Regeln aus Kursdaten · "
                     "keine Anlageberatung · Daten: Yahoo Finance", "klein")
        fuss.setAlignment(Qt.AlignCenter)
        lay.addWidget(fuss)
        lay.addStretch()

    # --- Bausteine

    def _zeile(self, ziel, t: str, d: dict, rechts: str = "", rechts_farbe: str = "") -> None:
        z = Klickflaeche("depotzeile")
        zl = QHBoxLayout(z)
        zl.setContentsMargins(6, 5, 8, 5)
        zl.setSpacing(10)
        zl.addWidget(avatar(t, 28))
        tx = QVBoxLayout()
        tx.setSpacing(0)
        n = KuerzLabel("zticker")
        n.setze(kurzer_name(d["name"]))
        tx.addWidget(n)
        tx.addWidget(label(t, "klein"))
        zl.addLayout(tx, 1)
        preis, ch, _ = kurs_jetzt(d)
        sp = Sparkline(60, 24)
        if d.get("spark"):
            sp.setze(d["spark"] + [preis], wert_farbe(ch), preis / (1 + ch))
        else:
            m = d["df"]["kurs"].iloc[-22:].tolist()
            sp.setze(m, wert_farbe(m[-1] - m[0]))
        zl.addWidget(sp)
        rb = QVBoxLayout()
        rb.setSpacing(0)
        k = label(f"{kurs_text(preis)} {d['waehrung']}", "zkurs")
        k.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        c = label(rechts or pfeil(ch), "klein")
        c.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        c.setStyleSheet(f"color: {rechts_farbe or wert_farbe(ch)}; font-weight: 500;")
        rb.addWidget(k)
        rb.addWidget(c)
        zl.addLayout(rb)
        z.geklickt.connect(lambda t=t: self.oeffnen.emit(t))
        ziel.addWidget(z)

    @staticmethod
    def _leer(ziel, text: str) -> None:
        h = label(text, "leise")
        h.setWordWrap(True)
        h.setContentsMargins(4, 6, 4, 6)
        ziel.addWidget(h)

    # --- Inhalt

    def setze(self, f: "Fenster") -> None:
        jetzt = datetime.now()
        stunde = jetzt.hour
        gruss = ("Guten Morgen" if 5 <= stunde < 11 else "Guten Tag" if stunde < 18
                 else "Guten Abend")
        self.gruss.setText(gruss)
        tage = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        monate = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
                  "September", "Oktober", "November", "Dezember"]
        wochenende = jetzt.weekday() >= 5
        xetra = (not wochenende) and (9 <= stunde < 17 or (stunde == 17 and jetzt.minute < 30))
        status = ("Wochenende – Börsen geschlossen, Krypto handelt weiter" if wochenende else
                  "Xetra ist geöffnet" if xetra else "Xetra ist geschlossen")
        self.untertitel.setText(f"{tage[jetzt.weekday()]}, {jetzt.day}. {monate[jetzt.month - 1]}"
                                f" {jetzt.year}  ·  {status}")

        for t, (wert, ch_l, sp) in self.index_kacheln.items():
            d = f.daten.get(t)
            if not d:
                continue
            preis, ch, _ = kurs_jetzt(d)
            nk = 4 if t.endswith("=X") else 0 if preis >= 1000 else 2
            wert.setText(zahl(preis, nk))
            ch_l.setText(pfeil(ch))
            ch_l.setStyleSheet(f"color: {wert_farbe(ch)}; font-weight: 500;")
            if d.get("spark"):
                sp.setze(d["spark"] + [preis], wert_farbe(ch), preis / (1 + ch))
            else:
                m = d["df"]["kurs"].iloc[-22:].tolist()
                sp.setze(m, wert_farbe(m[-1] - m[0]))

        # Depot
        leeren(self.depot_box)
        pos = konto.positionen(f.kaeufe)
        if not pos:
            self._leer(self.depot_box, "Noch keine Käufe eingetragen. Öffne einen Wert und "
                                       "klicke auf „Kauf / Verkauf“.")
        else:
            wert = einstand = heute = 0.0
            for t, p in pos.items():
                d = f.daten.get(t)
                if not d or not d.get("eur_faktor"):
                    continue
                pr, ch, _ = kurs_jetzt(d)
                w = p["stueck"] * pr * d["eur_faktor"]
                wert += w
                heute += w - w / (1 + ch)
                einstand += p["einstand"]
            gv = wert - einstand
            gross = label(f"{zahl(wert, 2)}&nbsp;<span style='font-size:16px'>€</span>", "preis")
            gross.setTextFormat(Qt.RichText)
            gross.setStyleSheet("font-size: 28px;")
            self.depot_box.addWidget(gross)
            zeile = label(
                f"<span style='color:{wert_farbe(heute)}; font-weight:500'>{euro_vz(heute)}"
                f"</span><span style='color:{T['leise']}'>&nbsp;heute</span>&nbsp;&nbsp;&nbsp;"
                f"<span style='color:{wert_farbe(gv)}; font-weight:500'>{euro_vz(gv)}&nbsp;"
                f"{prozent(gv / einstand, 2) if einstand else ''}</span>"
                f"<span style='color:{T['leise']}'>&nbsp;gesamt</span>")
            zeile.setTextFormat(Qt.RichText)
            self.depot_box.addWidget(zeile)
            self.depot_box.addWidget(label(f"{len(pos)} Positionen", "klein"))

        # Alarme
        leeren(self.alarm_box)
        aktiv = [a for a in f.alarme if a["aktiv"]]
        ausgeloest = sorted([a for a in f.alarme if a.get("ausgeloest")],
                            key=lambda a: a["ausgeloest"], reverse=True)[:3]
        if not f.alarme:
            self._leer(self.alarm_box, "Keine Alarme. In jeder Detailansicht kannst du mit "
                                       "„Alarm“ einen anlegen.")
        else:
            self.alarm_box.addWidget(label(f"{len(aktiv)} aktiv", "leise"))
            for a in ausgeloest:
                d = f.daten.get(a["ticker"])
                zeit = datetime.fromisoformat(a["ausgeloest"])
                l_ = label(f"<b>{a['ticker']}</b>&nbsp;&nbsp;{alarm_text(a, d['waehrung'] if d else '')}"
                           f"<span style='color:{T['leise']}'>&nbsp;&nbsp;ausgelöst "
                           f"{zeit:%d.%m. %H:%M}</span>")
                l_.setTextFormat(Qt.RichText)
                l_.setStyleSheet("font-size: 13px;")
                self.alarm_box.addWidget(l_)

        # Gewinner / Verlierer aus Listen und Depot
        eigene = [t for t in dict.fromkeys(f.alle_listen_tickers() + list(pos))
                  if t in f.daten]
        bewegt = sorted(eigene, key=lambda t: kurs_jetzt(f.daten[t])[1], reverse=True)
        for box, auswahl, leer in ((self.gewinner_box,
                                    [t for t in bewegt if kurs_jetzt(f.daten[t])[1] > 0][:4],
                                    "Heute ist keiner deiner Werte im Plus."),
                                   (self.verlierer_box,
                                    [t for t in reversed(bewegt)
                                     if kurs_jetzt(f.daten[t])[1] < 0][:4],
                                    "Heute ist keiner deiner Werte im Minus.")):
            leeren(box)
            if not eigene:
                self._leer(box, "Merke dir Werte mit dem Stern, dann siehst du hier ihre "
                                "Bewegungen.")
            elif not auswahl:
                self._leer(box, leer)
            for t in auswahl:
                self._zeile(box, t, f.daten[t])

        # Kaufsignale
        leeren(self.signal_box)
        kauf = [t for t in f.kaufsignale() if t in f.daten][:5]
        if not kauf:
            self._leer(self.signal_box, "Gerade zeigt die Regel bei keinem geprüften Wert "
                                        "KAUFEN.")
        for t in kauf:
            self._zeile(self.signal_box, t, f.daten[t],
                        f"Score {int(f.daten[t]['df']['score'].iloc[-1]):+d}", T["gruen"])

        # Termine
        leeren(self.termin_box)
        liste = []
        for t in eigene:
            for name, zeit, wann in termine(f.daten[t].get("info")):
                if (zeit.date() - jetzt.date()).days <= 14:
                    liste.append((zeit, t, name, wann))
        if not liste:
            self._leer(self.termin_box, "Keine Quartalszahlen oder Dividendentermine deiner "
                                        "Werte in den nächsten zwei Wochen.")
        for zeit, t, name, wann in sorted(liste)[:6]:
            z = Klickflaeche("depotzeile")
            zl = QHBoxLayout(z)
            zl.setContentsMargins(6, 5, 8, 5)
            zl.setSpacing(10)
            zl.addWidget(avatar(t, 24))
            l_ = label(f"<b>{t}</b>&nbsp;&nbsp;{name}")
            l_.setTextFormat(Qt.RichText)
            l_.setStyleSheet("font-size: 13px;")
            zl.addWidget(l_, 1)
            w = label(f"{zeit:%d.%m.} · {wann}", "klein")
            zl.addWidget(w)
            z.geklickt.connect(lambda t=t: self.oeffnen.emit(t))
            self.termin_box.addWidget(z)


class _TickerSignale(QObject):
    gefunden = Signal(str, str)
    fertig = Signal()


class TickerSuche(QRunnable):
    """Sucht im Hintergrund die Yahoo-Ticker zu allen ISINs eines Imports."""

    def __init__(self, werte: list[tuple[str, str, bool]]):
        super().__init__()
        self.werte = werte
        self.signale = _TickerSignale()

    def run(self) -> None:
        for isin, name, krypto in self.werte:
            try:
                t = tr_import.ticker_finden(isin, name, krypto) or ""
            except Exception:  # noqa: BLE001
                t = ""
            try:
                self.signale.gefunden.emit(isin, t)
            except RuntimeError:
                return
        try:
            self.signale.fertig.emit()
        except RuntimeError:
            pass


class ImportDialog(QDialog):
    """Vorschau der Käufe/Verkäufe aus der Trade-Republic-CSV, Ticker korrigierbar."""

    def __init__(self, parent, buchungen: list[dict], vorhanden: set[str]):
        super().__init__(parent)
        self.setWindowTitle("Trade Republic importieren")
        self.setMinimumSize(900, 600)
        self.buchungen = buchungen
        self.vorhanden = vorhanden
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(10)
        lay.addWidget(label("Trade Republic importieren", "kartentitel"))
        neu = sum(1 for b in buchungen if b["tr_id"] not in vorhanden)
        info = label(f"{len(buchungen)} Käufe und Verkäufe gefunden, davon {neu} neu. "
                     "Schon importierte Buchungen werden übersprungen. Einzahlungen, Zinsen und "
                     "Dividenden werden nicht übernommen.", "leise")
        info.setWordWrap(True)
        lay.addWidget(info)
        self.status = label("Suche passende Ticker bei Yahoo Finance …", "klein")
        lay.addWidget(self.status)

        self.isins = list(dict.fromkeys(b["isin"] for b in buchungen))
        self.werte_tabelle = QTableWidget(len(self.isins), 4, objectName="tabelle")
        self.werte_tabelle.setHorizontalHeaderLabels(["Wertpapier", "ISIN", "Ticker (änderbar)",
                                                      "Buchungen"])
        self.werte_tabelle.verticalHeader().setVisible(False)
        self.werte_tabelle.setShowGrid(False)
        kopf = self.werte_tabelle.horizontalHeader()
        kopf.setSectionResizeMode(QHeaderView.ResizeToContents)
        kopf.setSectionResizeMode(0, QHeaderView.Stretch)
        for r, isin in enumerate(self.isins):
            b = next(x for x in buchungen if x["isin"] == isin)
            n = sum(1 for x in buchungen if x["isin"] == isin)
            for c, text in enumerate((b["name"], isin, "…", f"{n}")):
                it = QTableWidgetItem(text)
                if c != 2:
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                self.werte_tabelle.setItem(r, c, it)
            self.werte_tabelle.setRowHeight(r, 32)
        lay.addWidget(label("Wertpapiere", "h2"))
        lay.addWidget(self.werte_tabelle, 2)

        lay.addWidget(label("Buchungen", "h2"))
        self.tabelle = QTableWidget(len(buchungen), 6, objectName="tabelle")
        self.tabelle.setHorizontalHeaderLabels(["Datum", "Art", "Wertpapier", "Stück",
                                                "Kurs €", "Gebühr €"])
        self.tabelle.verticalHeader().setVisible(False)
        self.tabelle.setShowGrid(False)
        self.tabelle.setEditTriggers(QAbstractItemView.NoEditTriggers)
        kopf = self.tabelle.horizontalHeader()
        kopf.setSectionResizeMode(QHeaderView.ResizeToContents)
        kopf.setSectionResizeMode(2, QHeaderView.Stretch)
        for r, b in enumerate(buchungen):
            alt = b["tr_id"] in vorhanden
            vk = b["art"] == "verkauf"
            zellen = [datetime.strptime(b["datum"], "%Y-%m-%d").strftime("%d.%m.%Y"),
                      "Verkauf" if vk else "Kauf", b["name"],
                      zahl(b["stueck"], 6).rstrip("0").rstrip(","), kurs_text(b["kurs_eur"]),
                      zahl(b["gebuehr_eur"], 2)]
            for c, text in enumerate(zellen):
                it = QTableWidgetItem(text + ("  · schon importiert" if alt and c == 2 else ""))
                if c >= 3:
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if alt:
                    it.setForeground(QColor(T["leise"]))
                elif c == 1:
                    it.setForeground(QColor(T["rot"] if vk else T["gruen"]))
                self.tabelle.setItem(r, c, it)
            self.tabelle.setRowHeight(r, 30)
        lay.addWidget(self.tabelle, 3)

        knoepfe = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.ok = knoepfe.button(QDialogButtonBox.Ok)
        self.ok.setText(f"{neu} Buchungen übernehmen")
        self.ok.setEnabled(False)
        knoepfe.button(QDialogButtonBox.Cancel).setText("Abbrechen")
        knoepfe.accepted.connect(self.accept)
        knoepfe.rejected.connect(self.reject)
        lay.addWidget(knoepfe)
        if not neu:
            self.ok.setText("Nichts Neues")

        werte = [(isin, next(x["name"] for x in buchungen if x["isin"] == isin),
                  next(x["krypto"] for x in buchungen if x["isin"] == isin))
                 for isin in self.isins]
        self.suche = TickerSuche(werte)
        self.suche.signale.gefunden.connect(self._gefunden)
        self.suche.signale.fertig.connect(self._fertig)
        QThreadPool.globalInstance().start(self.suche)

    def _gefunden(self, isin: str, ticker: str) -> None:
        r = self.isins.index(isin)
        it = self.werte_tabelle.item(r, 2)
        it.setText(ticker)
        if not ticker:
            it.setText("")
            it.setToolTip("Nicht gefunden – bitte den Yahoo-Ticker eintragen, z. B. SAP.DE")

    def _fertig(self) -> None:
        offen = sum(1 for r in range(len(self.isins))
                    if not self.werte_tabelle.item(r, 2).text().strip())
        self.status.setText("Ticker gefunden. Du kannst sie in der Tabelle noch ändern."
                            if not offen else f"{offen} Ticker nicht gefunden – bitte eintragen "
                                              "(Yahoo-Schreibweise, z. B. SAP.DE).")
        neu = sum(1 for b in self.buchungen if b["tr_id"] not in self.vorhanden)
        self.ok.setEnabled(neu > 0)

    def ergebnis(self) -> tuple[list[dict], dict[str, str]]:
        zuordnung = {isin: self.werte_tabelle.item(r, 2).text().strip().upper()
                     for r, isin in enumerate(self.isins)}
        neu = []
        for b in self.buchungen:
            t = zuordnung.get(b["isin"])
            if b["tr_id"] in self.vorhanden or not t:
                continue
            k = konto.kauf(t, b["stueck"], b["kurs_eur"], b["gebuehr_eur"], b["datum"], b["art"])
            k["tr_id"] = b["tr_id"]
            neu.append(k)
        return neu, zuordnung


class _UpdateSignale(QObject):
    gefunden = Signal(object)
    fortschritt = Signal(float, str)
    fertig = Signal(str)
    fehler = Signal(str)


class UpdatePruefung(QRunnable):
    """Fragt GitHub nach der neuesten Version (im Hintergrund)."""

    def __init__(self):
        super().__init__()
        self.signale = _UpdateSignale()

    def run(self) -> None:
        try:
            info = update.neueste()
        except Exception:  # noqa: BLE001 – offline o. Ä.: einfach nichts anzeigen
            info = None
        try:
            self.signale.gefunden.emit(info)
        except RuntimeError:
            pass


class UpdateJob(QRunnable):
    """Lädt das Update herunter und bereitet die Installation vor."""

    def __init__(self, info: dict):
        super().__init__()
        self.info = info
        self.signale = _UpdateSignale()

    def run(self) -> None:
        def melden(anteil: float, text: str) -> None:
            try:
                self.signale.fortschritt.emit(anteil, text)
            except RuntimeError:
                pass
        try:
            ordner = update.temp_ordner()
            if update.art() == "windows":
                ziel = ordner / f"Vyntro-Setup-{self.info['version']}.exe"
                update.herunterladen(self.info["installer"], ziel,
                                     lambda a, t: melden(a * 0.95, t))
                melden(0.97, "Starte Installation …")
            else:
                ziel = ordner / f"vyntro-{self.info['version']}.zip"
                update.herunterladen(self.info["quelle"], ziel, lambda a, t: melden(a * 0.88, t))
                melden(0.9, "Installiere …")
                update.mac_installieren(ziel, melden)
                melden(1.0, "Fertig – Vyntro startet neu …")
            self.signale.fertig.emit(str(ziel))
        except Exception as e:  # noqa: BLE001
            try:
                self.signale.fehler.emit(str(e) or e.__class__.__name__)
            except RuntimeError:
                pass


class UpdateDialog(QDialog):
    """Kleines Fenster: was ist neu, Knopf zum Aktualisieren, Fortschritt."""

    def __init__(self, parent: "Fenster", info: dict):
        super().__init__(parent)
        self.f = parent
        self.info = info
        self.setWindowTitle("Vyntro aktualisieren")
        self.setFixedWidth(500)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(26, 24, 26, 22)
        lay.setSpacing(10)
        kopf = QHBoxLayout()
        kopf.setSpacing(14)
        if LOGO_DATEI.exists():
            logo = QLabel()
            logo.setPixmap(logo_pixmap(30))
            kopf.addWidget(logo)
        titel = QVBoxLayout()
        titel.setSpacing(0)
        titel.addWidget(label(f"Vyntro {info['version']} ist da", "kartentitel"))
        titel.addWidget(label(f"Du nutzt Version {update.VERSION}", "klein"))
        kopf.addLayout(titel, 1)
        lay.addLayout(kopf)
        notizen = info.get("notizen", "").split("---")[0].strip()  # nur „Was ist neu“
        self.notizen = QLabel(notizen[:900] or "Verbesserungen und Fehlerbehebungen.")
        self.notizen.setTextFormat(Qt.MarkdownText)
        self.notizen.setWordWrap(True)
        self.notizen.setStyleSheet(f"color: {T['leise']}; font-size: 12px;")
        lay.addWidget(self.notizen)
        lay.addSpacing(6)
        self.balken = QProgressBar(objectName="updatebalken")
        self.balken.setRange(0, 1000)
        self.balken.setTextVisible(False)
        self.balken.hide()
        lay.addWidget(self.balken)
        self.status = label("", "klein")
        self.status.hide()
        lay.addWidget(self.status)
        knoepfe = QHBoxLayout()
        knoepfe.addStretch()
        self.spaeter = QPushButton("Später", objectName="chip")
        self.spaeter.clicked.connect(self.reject)
        self.los = QPushButton("  Jetzt aktualisieren", objectName="updatejetzt")
        self.los.setIcon(icon("import", "#050505", 15))
        self.los.setCursor(Qt.PointingHandCursor)
        self.los.clicked.connect(self.starten)
        knoepfe.addWidget(self.spaeter)
        knoepfe.addWidget(self.los)
        lay.addLayout(knoepfe)
        if not update.art():
            self.los.setEnabled(False)
            self.status.setText("Diese Installation kann sich nicht selbst aktualisieren "
                                "(Entwicklerversion). Bitte mit „git pull“ und install.sh.")
            self.status.show()

    def starten(self) -> None:
        self.los.setEnabled(False)
        self.spaeter.setEnabled(False)
        self.balken.show()
        self.status.show()
        self.status.setText("Verbinde …")
        job = UpdateJob(self.info)
        job.signale.fortschritt.connect(self._fortschritt)
        job.signale.fertig.connect(self._fertig)
        job.signale.fehler.connect(self._fehler)
        QThreadPool.globalInstance().start(job)

    def _fortschritt(self, anteil: float, text: str) -> None:
        self.balken.setValue(int(anteil * 1000))
        self.status.setText(f"{text}   {int(anteil * 100)} %")

    def _fertig(self, pfad: str) -> None:
        self.balken.setValue(1000)
        if update.art() == "windows":
            self.status.setText("Installiere … Vyntro schließt sich kurz und startet neu.")
            update.installer_starten(s.Path(pfad))
        else:
            self.status.setText("Fertig – Vyntro startet neu …")
            update.neu_starten_mac()
        QTimer.singleShot(1200, self.f.beenden)

    def _fehler(self, text: str) -> None:
        self.status.setText(f"Update fehlgeschlagen: {text}")
        self.status.setStyleSheet(f"color: {T['rot']};")
        self.los.setEnabled(True)
        self.los.setText("  Erneut versuchen")
        self.spaeter.setEnabled(True)


class AnleitungText(QTextBrowser):
    """Textfeld der Anleitung, das die Lehrbilder des Chart-Kurses selbst zeichnet.

    Bilder stehen im HTML als kurs:NAME?b=BREITE und werden von kursbilder.py (matplotlib)
    erzeugt, einmal pro Name zwischengespeichert und passend zur Breite und
    Bildschirmauflösung verkleinert.
    """

    def __init__(self):
        super().__init__(objectName="anleitung")
        self._roh: dict[str, QImage] = {}

    def loadResource(self, typ, url):
        if url.scheme() == "kurs":
            name = url.path()
            try:
                breite = int(url.query().partition("b=")[2] or 600)
                if name not in self._roh:
                    import kursbilder
                    self._roh[name] = QImage.fromData(kursbilder.png(name))
                roh = self._roh[name]
                dpr = max(1.0, self.devicePixelRatioF())
                bild = roh.scaledToWidth(min(roh.width(), round(breite * dpr)),
                                         Qt.SmoothTransformation)
                bild.setDevicePixelRatio(dpr)
                return bild
            except Exception:  # noqa: BLE001 – ein fehlendes Bild soll die Anleitung nicht stören
                return QImage()
        return super().loadResource(typ, url)


class AnleitungSeite(QWidget):
    """Eingebaute Anleitung: Inhaltsverzeichnis mit Suche links, Kapitel rechts."""

    def __init__(self):
        super().__init__(objectName="detail")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 16)
        lay.setSpacing(14)

        links = karte()
        links.setFixedWidth(260)
        ll = QVBoxLayout(links)
        ll.setContentsMargins(14, 16, 14, 14)
        ll.setSpacing(10)
        kopf = QHBoxLayout()
        kopf.setSpacing(8)
        kopf.addWidget(icon_label("buch", T["text"], 17))
        kopf.addWidget(label("Anleitung", "kartentitel"))
        kopf.addStretch()
        ll.addLayout(kopf)
        self.suche = QLineEdit(objectName="suche", placeholderText="Suchen, z. B. RSI …")
        self.suche.setClearButtonEnabled(True)
        self.suche.textChanged.connect(self._filtern)
        ll.addWidget(self.suche)
        self.inhalt = QListWidget(objectName="palettenliste")
        self.inhalt.currentItemChanged.connect(lambda item, _alt: self._zeigen(item))
        ll.addWidget(self.inhalt, 1)
        lay.addWidget(links)

        rechts = karte()
        rl = QVBoxLayout(rechts)
        rl.setContentsMargins(34, 26, 34, 18)
        rl.setSpacing(10)
        self.text = AnleitungText()
        self.text.setOpenLinks(False)
        self.text.anchorClicked.connect(self._link)
        self.text.document().setDocumentMargin(0)
        self.text.document().setDefaultStyleSheet(
            f"h1 {{ font-size: 24px; font-weight: 500; margin-top: 2px; margin-bottom: 10px; }}"
            f"h3 {{ font-size: 15px; font-weight: 600; margin-top: 18px; margin-bottom: 4px; }}"
            f"p, li, td {{ font-size: 14px; line-height: 150%; color: {T['text']}; }}"
            f"b {{ color: {GOLD}; font-weight: 600; }}"
            f"i {{ color: {T['leise']}; }}"
            f"a {{ color: {GOLD}; }}"
            f".kicker {{ font-size: 11px; font-weight: 700; letter-spacing: 1.6px; "
            f"color: {GOLD}; margin-bottom: 0px; }}"
            f".lead {{ font-size: 15px; color: {T['leise']}; margin-bottom: 8px; }}"
            f".bild {{ font-size: 12px; color: {T['leise']}; margin-top: 2px; }}"
            f".bildzeile {{ line-height: 100%; margin-top: 10px; margin-bottom: 0px; }}"
            f".kastentitel {{ font-size: 10px; font-weight: 700; letter-spacing: 1.6px; "
            f"margin-bottom: 4px; }}"
            f".weiter {{ font-size: 14px; color: {T['leise']}; }}")
        rl.addWidget(self.text, 1)
        unten = QHBoxLayout()
        self.zurueck = QPushButton("←  Zurück", objectName="chip")
        self.weiter = QPushButton("Weiter  →", objectName="chip")
        for b in (self.zurueck, self.weiter):
            b.setCursor(Qt.PointingHandCursor)
        self.zurueck.clicked.connect(lambda: self._blaettern(-1))
        self.weiter.clicked.connect(lambda: self._blaettern(1))
        self.position = label("", "klein")
        unten.addWidget(self.zurueck)
        unten.addStretch()
        unten.addWidget(self.position)
        unten.addStretch()
        unten.addWidget(self.weiter)
        rl.addLayout(unten)
        lay.addWidget(rechts, 1)
        self._ids = [k[0] for k in anleitung.KAPITEL]
        self._kapitel: str | None = None
        self._loesung = False  # Auflösung der Übung sichtbar?
        self._breite = 0  # Bildbreite, mit der das aktuelle Kapitel gezeichnet wurde
        # Bilder an neue Fensterbreite anpassen, aber nicht bei jedem Pixel neu zeichnen
        self._groesse_timer = QTimer(self, singleShot=True, interval=150)
        self._groesse_timer.timeout.connect(self._breite_pruefen)
        self.text.viewport().installEventFilter(self)
        self._filtern("")

    def eventFilter(self, obj, ev):
        if obj is self.text.viewport() and ev.type() == QEvent.Resize:
            self._groesse_timer.start()
        return super().eventFilter(obj, ev)

    def _bildbreite(self) -> int:
        # in 40er-Schritten, damit eine erscheinende Bildlaufleiste kein Neuzeichnen auslöst
        return max(240, (self.text.viewport().width() - 24) // 40 * 40)

    def _breite_pruefen(self) -> None:
        if self._kapitel and anleitung.hat_bilder(self._kapitel) \
                and self._bildbreite() != self._breite:
            self._rendern(scroll_behalten=True)

    def _rendern(self, scroll_behalten: bool = False) -> None:
        leiste = self.text.verticalScrollBar()
        anteil = leiste.value() / leiste.maximum() if scroll_behalten and leiste.maximum() else 0
        farben = {"gruen": T["gruen"], "rot": T["rot"], "grau": T["grau"],
                  "kasten": "#0f1513"}
        self._breite = self._bildbreite()
        self.text.setHtml(anleitung.kapitel_html(self._kapitel, pfade.TASTE, farben,
                                                 breite=self._breite, loesung=self._loesung))
        if anteil:  # erst nach dem Layout ist die neue Länge bekannt
            QTimer.singleShot(0, lambda: leiste.setValue(round(anteil * leiste.maximum())))
        else:
            leiste.setValue(0)

    def _link(self, url: QUrl) -> None:
        if url.scheme() == "anleitung":
            self.suche.clear()
            self.oeffnen(url.path())
        elif url.scheme() == "loesung":
            self._loesung = True
            self._rendern(scroll_behalten=True)
        elif url.scheme() in ("http", "https"):
            QDesktopServices.openUrl(url)

    def _filtern(self, text: str) -> None:
        treffer = set(anleitung.suchen(text))
        aktuell = self.inhalt.currentItem().data(Qt.UserRole) if self.inhalt.currentItem() \
            else None
        self.inhalt.blockSignals(True)
        self.inhalt.clear()
        gruppe = None
        erstes = None
        for kid, titel, grp, _ in anleitung.KAPITEL:
            if kid not in treffer:
                continue
            if grp != gruppe:
                gruppe = grp
                kopf = QListWidgetItem(grp.upper())
                kopf.setFlags(Qt.NoItemFlags)
                kopf.setForeground(QColor(T["leise"]))
                f = kopf.font()
                f.setPixelSize(10)
                f.setLetterSpacing(QFont.AbsoluteSpacing, 1.2)
                kopf.setFont(f)
                kopf.setSizeHint(QSize(0, 30))
                self.inhalt.addItem(kopf)
            item = QListWidgetItem(titel)
            item.setData(Qt.UserRole, kid)
            item.setSizeHint(QSize(0, 32))
            self.inhalt.addItem(item)
            if kid == aktuell or erstes is None:
                erstes = item if (erstes is None or kid == aktuell) else erstes
        self.inhalt.blockSignals(False)
        if erstes is not None:
            self.inhalt.setCurrentItem(erstes)
            self._zeigen(erstes)
        else:
            self._kapitel = None
            self.text.setHtml(f"<p style='color:{T['leise']}'>Nichts gefunden.</p>")

    def _zeigen(self, item) -> None:
        if not item or not item.data(Qt.UserRole):
            return
        kid = item.data(Qt.UserRole)
        if kid != self._kapitel:
            self._loesung = False
        self._kapitel = kid
        self._rendern()
        self.text.verticalScrollBar().setValue(0)
        i = self._ids.index(kid)
        self.zurueck.setEnabled(i > 0)
        self.weiter.setEnabled(i < len(self._ids) - 1)
        self.position.setText(f"Kapitel {i + 1} von {len(self._ids)}")

    def _blaettern(self, schritt: int) -> None:
        item = self.inhalt.currentItem()
        kid = item.data(Qt.UserRole) if item else self._ids[0]
        ziel = self._ids[max(0, min(len(self._ids) - 1, self._ids.index(kid) + schritt))]
        self.suche.clear()
        self.oeffnen(ziel)

    def oeffnen(self, kid: str) -> None:
        for r in range(self.inhalt.count()):
            if self.inhalt.item(r).data(Qt.UserRole) == kid:
                self.inhalt.setCurrentRow(r)
                return


class Watchliste(QListWidget):
    """Watchlist, in der sich die eigenen Werte per Ziehen mit der Maus umsortieren lassen."""
    umsortiert = Signal(list)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)

    def dropEvent(self, e):
        super().dropEvent(e)
        reihenfolge = []
        for i in range(self.count()):
            key = self.item(i).data(Qt.UserRole + 1) or ""
            if key.startswith("meine:"):
                reihenfolge.append(key.split(":", 1)[1])
        self.umsortiert.emit(reihenfolge)


class Fenster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Vyntro")
        self.resize(1360, 900)
        self.setMinimumSize(1100, 720)
        self.daten: dict[str, dict] = {}
        self.fehler: dict[str, str] = {}
        # Schlüssel "bereich:ticker" -> (Listeneintrag, Zeile); ein Ticker kann in
        # mehreren Bereichen stehen (z. B. in "Meine" und bei den Kaufsignalen)
        self.items: dict[str, tuple[QListWidgetItem, Zeile]] = {}
        self.ladend: set[str] = set()
        self.pool = QThreadPool.globalInstance()
        self.listen: dict[str, list[str]] = {"Meine": self.lade_meine()}
        self.listen.update(self.lade_weitere_listen())
        self.aktive_liste = QSettings("trading-signale", "app").value("liste", "Meine", type=str)
        if self.aktive_liste not in self.listen:
            self.aktive_liste = "Meine"
        self.kauf_angezeigt: list[str] = []
        self.news_cache: dict[str, tuple[datetime, list]] = {}
        self.news_ladend: set[str] = set()
        self.live_laeuft = False
        self.live_zeit: datetime | None = None
        self.kaeufe = konto.lade_kaeufe()
        self.notizen = konto.lade_notizen()
        self.alarme = konto.lade_alarme()
        self.ansicht = "detail"  # oder "depot" / "alarme"
        self.signal_timer = QTimer(self, interval=15 * 60_000)  # Signale neu berechnen
        self.signal_timer.timeout.connect(self.eigene_neu_laden)
        self.signal_timer.start()
        global LOGO_DIENST
        LOGO_DIENST = LogoDienst()
        LOGO_DIENST.geladen.connect(self.logo_da)
        self.stream = LiveStream()
        self.sekunden_timer = QTimer(self, interval=1000)  # Anzeige jede Sekunde
        self.sekunden_timer.timeout.connect(self.sekunde)
        self.sekunden_timer.start()
        self.live_timer = QTimer(self, interval=60_000)  # Absicherung: jede Minute
        self.live_timer.timeout.connect(self.live_laden)
        self.live_timer.start()
        QTimer.singleShot(6000, self.live_laden)
        self.markt_timer = QTimer(self, singleShot=True, interval=700)
        self.markt_timer.timeout.connect(self.seite_auffrischen)
        self.umbau_timer = QTimer(self, singleShot=True, interval=400)
        self.umbau_timer.timeout.connect(lambda: self.aufbauen())

        zentral = GlasFlaeche(objectName="haupt")
        aussen = QVBoxLayout(zentral)
        aussen.setContentsMargins(18, 10, 12, 0)
        aussen.setSpacing(12)
        self.setCentralWidget(zentral)

        # --- Kopfleiste
        topbar = QHBoxLayout()
        topbar.setSpacing(10)
        # Logo + Schriftzug
        marke = QLabel()
        marke.setCursor(Qt.PointingHandCursor)
        marke.setToolTip("Home")
        marke.mousePressEvent = lambda _e: self.ansicht_setzen("home")
        if LOGO_DATEI.exists():
            marke.setPixmap(logo_pixmap(22))
        topbar.addWidget(marke)
        schriftzug = QLabel("VYNTRO")
        schriftzug.setStyleSheet(
            "font-size: 16px; font-weight: 600; letter-spacing: 6px; color: qlineargradient("
            "x1:0, y1:0, x2:0, y2:1, stop:0 #f2f4f3, stop:1 #a9afad);")
        topbar.addSpacing(4)
        topbar.addWidget(schriftzug)
        topbar.addStretch()
        self.k_depot = QPushButton("Depot", objectName="chip", checkable=True)
        self.k_alarme = QPushButton("Alarme", objectName="chip", checkable=True)
        self.k_home = QPushButton(" Home", objectName="chip", checkable=True)
        self.k_home.setToolTip(f"Startseite ({pfade.TASTE}1)")
        self.k_markt = QPushButton(" Markt", objectName="chip", checkable=True)
        self.k_markt.setToolTip(f"Heatmap und Filter über alle Werte ({pfade.TASTE}J)")
        for b, name, sym in ((self.k_home, "home", "haus"), (self.k_markt, "markt", "raster"),
                             (self.k_depot, "depot", "depot"),
                             (self.k_alarme, "alarme", "glocke")):
            b.setIcon(icon(sym, None, 15))
            b.setIconSize(QSize(15, 15))
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, n=name: self.ansicht_setzen(
                "detail" if self.ansicht == n else n))
            topbar.addWidget(b)
        self.k_depot.setToolTip(f"Deine eingetragenen Käufe mit Gewinn/Verlust ({pfade.TASTE}D)")
        self.k_alarme.setToolTip(f"Kurs- und Signal-Alarme ({pfade.TASTE}L)")
        topbar.addSpacing(6)
        self.update_knopf = QPushButton(objectName="update")
        self.update_knopf.setCursor(Qt.PointingHandCursor)
        self.update_knopf.hide()
        self.update_knopf.clicked.connect(self.update_zeigen)
        topbar.addWidget(self.update_knopf)
        self.update_info: dict | None = None
        self.status = QLabel(objectName="statuschip")
        topbar.addWidget(self.status)
        suche_k = QPushButton(f"  Suchen   {pfade.TASTE}K", objectName="chip")
        suche_k.setIcon(icon("suche", None, 15))
        suche_k.setCursor(Qt.PointingHandCursor)
        suche_k.setToolTip("Schnellsuche: Werte und Befehle")
        suche_k.clicked.connect(self.schnellsuche)
        topbar.addWidget(suche_k)
        buch = QPushButton(objectName="chip")
        buch.setIcon(icon("buch", None, 16))
        buch.setIconSize(QSize(16, 16))
        buch.setToolTip("Anleitung")
        buch.setCursor(Qt.PointingHandCursor)
        buch.clicked.connect(lambda: self.ansicht_setzen(
            "detail" if self.ansicht == "anleitung" else "anleitung"))
        topbar.addWidget(buch)
        zahnrad = QPushButton(objectName="chip")
        zahnrad.setIcon(icon("regler", None, 16))
        zahnrad.setIconSize(QSize(16, 16))
        zahnrad.setToolTip(f"Einstellungen ({pfade.TASTE},)")
        zahnrad.setCursor(Qt.PointingHandCursor)
        zahnrad.clicked.connect(self.einstellungen_oeffnen)
        topbar.addWidget(zahnrad)
        QShortcut(QKeySequence("Ctrl+,"), self, activated=self.einstellungen_oeffnen)
        neu = QPushButton(objectName="chip")
        neu.setIcon(icon("neu", None, 16))
        neu.setIconSize(QSize(16, 16))
        neu.setToolTip(f"Alle Kurse neu laden ({pfade.TASTE}R)")
        neu.setCursor(Qt.PointingHandCursor)
        neu.clicked.connect(self.alle_laden)
        topbar.addWidget(neu)
        aussen.addLayout(topbar)
        hl = QHBoxLayout()
        hl.setSpacing(14)
        aussen.addLayout(hl, 1)

        # --- Seitenleiste
        seite = QFrame(objectName="seite")
        seite.setFixedWidth(430)
        sl = QVBoxLayout(seite)
        sl.setContentsMargins(16, 18, 14, 12)
        sl.setSpacing(10)
        kartenkopf(sl, "Watchlist", name=False)

        # Umschalter Aktien & ETFs | Krypto
        self.einstellungen = QSettings("trading-signale", "app")
        self.krypto_modus = self.einstellungen.value("krypto", False, type=bool)
        self.preisgrenze = self.einstellungen.value("preisgrenze", PREISGRENZE, type=float)
        self.sortierung = self.einstellungen.value("sortierung", "eigene", type=str)
        tabs = QFrame(objectName="tabs")
        tl = QHBoxLayout(tabs)
        tl.setContentsMargins(3, 3, 3, 3)
        tl.setSpacing(3)
        self.bereich_knoepfe = QButtonGroup(self)
        for i, (name, krypto) in enumerate((("Aktien & ETFs", False), ("Krypto", True))):
            b = QPushButton(name, objectName="tab", checkable=True)
            b.setCursor(Qt.PointingHandCursor)
            b.setProperty("name", name)
            b.setProperty("krypto", krypto)
            b.setChecked(krypto == self.krypto_modus)
            self.bereich_knoepfe.addButton(b, i)
            tl.addWidget(b, 1)
        self.bereich_knoepfe.idClicked.connect(lambda i: self.bereich_setzen(i == 1))
        sl.addWidget(tabs)

        self.eingabe = QLineEdit(objectName="suche",
                                 placeholderText="Suchen: Dogecoin, Apple, SAP …")
        self.eingabe.setClearButtonEnabled(True)
        self.eingabe.returnPressed.connect(self.hinzufuegen)
        sl.addWidget(self.eingabe)

        self.vorschlag_modell = QStandardItemModel(self)
        self.completer = QCompleter(self.vorschlag_modell, self)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.setCompletionRole(Qt.UserRole)
        self.completer.setMaxVisibleItems(10)
        self.completer.activated[str].connect(self.vorschlag_gewaehlt)
        self.completer.popup().setObjectName("popup")
        self.completer.popup().setIconSize(QSize(28, 28))
        self.eingabe.setCompleter(self.completer)
        self.such_timer = QTimer(self, singleShot=True, interval=250)
        self.such_timer.timeout.connect(self.suche_starten)
        self.eingabe.textEdited.connect(lambda _: self.such_timer.start())

        self.liste = Watchliste(objectName="liste")
        self.liste.umsortiert.connect(self.umsortiert)
        self.liste.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.liste.setContextMenuPolicy(Qt.CustomContextMenu)
        self.liste.customContextMenuRequested.connect(self.kontextmenue)
        self.extra_ticker: str | None = None
        self.liste.currentItemChanged.connect(lambda *_: self._listenwahl())
        self.liste.itemClicked.connect(lambda *_: self._listenwahl())
        sl.addWidget(self.liste, 1)

        hl.addWidget(seite)

        # --- Hauptbereich
        self.stapel = QStackedWidget()
        self.leer = label("", "leise")
        self.leer.setAlignment(Qt.AlignCenter)
        self.leer.setWordWrap(True)
        self.detail = Detail()
        self.detail.merken_geklickt.connect(self.markieren)
        self.stapel.addWidget(self.leer)
        self.detail_scroll = QScrollArea(objectName="detailscroll")
        self.detail_scroll.setWidgetResizable(True)
        self.detail_scroll.setFrameShape(QFrame.NoFrame)
        self.detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.detail_scroll.setWidget(self.detail)
        self.detail.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.stapel.addWidget(self.detail_scroll)
        self.detail.alle_daten = self.daten
        self.detail.vergleich_laden.connect(self.laden)
        self.detail.k_notiz.geaendert.connect(self.notiz_speichern)
        k = self.detail.k_konto
        k.kauf_neu.connect(self.kauf_eintragen)
        k.kauf_weg.connect(self.kauf_loeschen)
        k.alarm_neu.connect(self.alarm_anlegen)
        k.alarm_weg.connect(self.alarm_loeschen)
        k.alarm_wieder.connect(self.alarm_wieder_an)

        self.depot = DepotSeite()
        self.depot.oeffnen.connect(self.oeffnen)
        self.depot.export_gewuenscht.connect(self.depot_exportieren)
        self.depot.import_gewuenscht.connect(self.depot_importieren)
        self.depot.freibetrag = self.einstellungen.value("freibetrag", 1000.0, type=float)
        self.alarm_seite = AlarmSeite()
        self.alarm_seite.oeffnen.connect(self.oeffnen)
        self.alarm_seite.alarm_weg.connect(self.alarm_loeschen)
        self.alarm_seite.alarm_wieder.connect(self.alarm_wieder_an)
        self.markt = MarktSeite()
        self.markt.oeffnen.connect(self.oeffnen)
        self.anleitung = AnleitungSeite()
        self.home = HomeSeite()
        self.home.oeffnen.connect(self.oeffnen)
        self.home.ansicht.connect(self.ansicht_setzen)
        self._home_zeit = 0.0
        self.seiten = {}
        self.stapel.addWidget(self.anleitung)
        for name, w in (("depot", self.depot), ("alarme", self.alarm_seite),
                        ("markt", self.markt), ("home", self.home)):
            sc = QScrollArea(objectName="detailscroll")
            sc.setWidgetResizable(True)
            sc.setFrameShape(QFrame.NoFrame)
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            sc.setWidget(w)
            w.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            self.stapel.addWidget(sc)
            self.seiten[name] = sc
        self.seiten["anleitung"] = self.anleitung
        hl.addWidget(self.stapel, 1)
        self.meldung = Meldung(zentral)
        QShortcut(QKeySequence("Ctrl+D"), self, activated=lambda: self.ansicht_setzen(
            "detail" if self.ansicht == "depot" else "depot"))
        QShortcut(QKeySequence("Ctrl+K"), self, activated=self.schnellsuche)
        QShortcut(QKeySequence.HelpContents, self,
                  activated=lambda: self.ansicht_setzen("anleitung"))
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self.ansicht_setzen("home"))
        QShortcut(QKeySequence("Ctrl+J"), self, activated=lambda: self.ansicht_setzen(
            "detail" if self.ansicht == "markt" else "markt"))
        QShortcut(QKeySequence("Ctrl+L"), self, activated=lambda: self.ansicht_setzen(
            "detail" if self.ansicht == "alarme" else "alarme"))
        self.knoepfe_beschriften()
        self.wirklich_beenden = False
        self.offline = False
        QTimer.singleShot(5000, self.update_pruefen)  # beim Start nach neuer Version schauen
        self.update_timer = QTimer(self, interval=6 * 3600 * 1000)
        self.update_timer.timeout.connect(self.update_pruefen)
        self.update_timer.start()
        QApplication.instance().installEventFilter(QuitWaechter(self))
        QApplication.instance().setQuitOnLastWindowClosed(False)
        QApplication.instance().applicationStateChanged.connect(self._app_zustand)
        self.leiste = Menueleiste(self) if QSystemTrayIcon.isSystemTrayAvailable() else None
        if not pfade.MAC and self.leiste:  # Windows-Benachrichtigungen über das Taskleisten-Symbol
            konto.MELDER = lambda titel, text: self.leiste.tray.showMessage(
                titel, text, QApplication.windowIcon(), 9000)
        if not pfade.MAC:
            QShortcut(QKeySequence("Ctrl+Q"), self, activated=self.beenden)

        for seq in (QKeySequence.Delete, QKeySequence(Qt.Key_Backspace)):
            QShortcut(seq, self.liste, activated=self.entfernen)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.alle_laden)
        QShortcut(QKeySequence.Find, self, activated=self.eingabe.setFocus)

        self.aufbauen()
        self.aus_cache_laden()
        self.ansicht_setzen("home")  # Start auf der Home-Seite
        QTimer.singleShot(0, self.alle_laden)

    # --- Speichern / Laden der eigenen Liste

    def lade_meine(self) -> list[str]:
        if MEINE.exists():
            zeilen = (z.split("#")[0].strip().upper() for z in MEINE.read_text().splitlines())
            return [z for z in zeilen if z]
        # einmalige Übernahme aus der alten watchlist.txt, ohne die früheren Beispiele
        alt = s.lies_watchlist()
        if alt[:len(ALTE_BEISPIELE)] == ALTE_BEISPIELE:
            alt = alt[len(ALTE_BEISPIELE):]
        MEINE.write_text("".join(t + "\n" for t in alt))
        return alt

    @staticmethod
    def lade_weitere_listen() -> dict[str, list[str]]:
        try:
            daten = json.loads(LISTEN.read_text())
            return {str(k): [str(x) for x in v] for k, v in daten.items() if k != "Meine"}
        except (OSError, ValueError, AttributeError):
            return {}

    @property
    def meine(self) -> list[str]:
        """Die gerade gewählte Liste (Standard: „Meine“)."""
        return self.listen[self.aktive_liste]

    @meine.setter
    def meine(self, werte: list[str]) -> None:
        self.listen[self.aktive_liste] = werte

    def alle_listen_tickers(self) -> list[str]:
        return list(dict.fromkeys(t for l_ in self.listen.values() for t in l_))

    def speichern(self) -> None:
        MEINE.write_text("# Meine gemerkten Werte (Yahoo-Finance-Ticker), einer pro Zeile.\n"
                         + "".join(t + "\n" for t in self.listen["Meine"]))
        weitere = {k: v for k, v in self.listen.items() if k != "Meine"}
        tmp = LISTEN.with_suffix(".tmp")
        tmp.write_text(json.dumps(weitere, indent=2, ensure_ascii=False))
        tmp.replace(LISTEN)

    # --- Mehrere Listen

    def liste_menue(self, knopf: QPushButton) -> None:
        menue = QMenu(self)
        for name, werte in self.listen.items():
            a = QAction(f"{name}  ·  {len(werte)}", menue, checkable=True)
            a.setChecked(name == self.aktive_liste)
            a.triggered.connect(lambda _=False, n=name: self.liste_waehlen(n))
            menue.addAction(a)
        menue.addSeparator()
        menue.addAction("Neue Liste …").triggered.connect(self.liste_neu)
        if self.aktive_liste != "Meine":
            menue.addAction(f"„{self.aktive_liste}“ umbenennen …").triggered.connect(
                self.liste_umbenennen)
            menue.addAction(f"„{self.aktive_liste}“ löschen").triggered.connect(
                self.liste_loeschen)
        menue.exec(knopf.mapToGlobal(knopf.rect().bottomLeft()))

    def liste_waehlen(self, name: str) -> None:
        self.aktive_liste = name
        self.einstellungen.setValue("liste", name)
        self.aufbauen()

    def liste_neu(self) -> None:
        name, ok = QInputDialog.getText(self, "Neue Liste", "Name der Liste (z. B. Dividenden, "
                                        "Tech, Beobachten):")
        name = name.strip()
        if ok and name and name not in self.listen:
            self.listen[name] = []
            self.speichern()
            self.liste_waehlen(name)

    def liste_umbenennen(self) -> None:
        alt = self.aktive_liste
        name, ok = QInputDialog.getText(self, "Liste umbenennen", "Neuer Name:", text=alt)
        name = name.strip()
        if ok and name and name not in self.listen and alt != "Meine":
            self.listen = {(name if k == alt else k): v for k, v in self.listen.items()}
            self.speichern()
            self.liste_waehlen(name)

    def liste_loeschen(self) -> None:
        name = self.aktive_liste
        if name == "Meine":
            return
        antwort = QMessageBox.question(
            self, "Liste löschen", f"Die Liste „{name}“ mit {len(self.listen[name])} Werten "
            "löschen? Die Werte selbst bleiben in anderen Listen und im Depot erhalten.")
        if antwort == QMessageBox.Yes:
            del self.listen[name]
            self.speichern()
            self.liste_waehlen("Meine")

    def in_liste_umschalten(self, liste: str, ticker: str) -> None:
        werte = self.listen[liste]
        if ticker in werte:
            werte.remove(ticker)
        else:
            werte.append(ticker)
        self.speichern()
        self.aufbauen()
        if ticker not in self.daten:
            self.laden(ticker)

    def umsortiert(self, reihenfolge: list[str]) -> None:
        """Nach Ziehen mit der Maus: neue Reihenfolge der Werte im aktuellen Bereich."""
        bereich = [t for t in reihenfolge if t in self.meine]
        if len(bereich) != len(self.im_bereich(self.meine)):
            QTimer.singleShot(0, self.aufbauen)
            return
        andere = iter(bereich)
        self.meine = [next(andere) if self.ist_krypto(t) == self.krypto_modus else t
                      for t in self.meine]
        self.speichern()
        aktuell = self.aktueller_ticker()
        QTimer.singleShot(0, lambda: self.aufbauen(auswahl=f"meine:{aktuell}" if aktuell
                                                   else None))

    def alle_tickers(self) -> list[str]:
        return list(dict.fromkeys(self.alle_listen_tickers() + [k["ticker"] for k in self.kaeufe]
                                  + [a["ticker"] for a in self.alarme] + SCAN + VORSCHLAEGE))

    def ist_krypto(self, ticker: str) -> bool:
        d = self.daten.get(ticker)
        if d and d.get("typ"):
            return d["typ"] == "Krypto"
        return bool(KRYPTO_MUSTER.search(ticker))

    def im_bereich(self, tickers: list[str]) -> list[str]:
        """Nur die Ticker des gewählten Bereichs (Aktien & ETFs oder Krypto)."""
        return [t for t in tickers if self.ist_krypto(t) == self.krypto_modus]

    def kaufsignale(self) -> list[str]:
        """Werte des aktuellen Bereichs, bei denen die Regel gerade KAUFEN anzeigt."""
        treffer = []
        for t in self.im_bereich(self.alle_tickers()):
            d = self.daten.get(t)
            if d and s.empfehlung(int(d["df"]["score"].iloc[-1])) == "KAUFEN":
                z = d["df"].iloc[-1]
                treffer.append((-int(z["score"]), float(z["rsi"]), t))
        return [t for *_, t in sorted(treffer)]

    def vorschlaege(self) -> list[str]:
        kauf = set(self.kaufsignale())
        return [t for t in self.im_bereich(VORSCHLAEGE) if t not in self.meine and t not in kauf]

    # --- Liste aufbauen

    def _sonderzeile(self, widget: QWidget, hoehe: int) -> None:
        item = QListWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        item.setSizeHint(QSize(0, hoehe))
        self.liste.addItem(item)
        self.liste.setItemWidget(item, widget)

    def _hinweis(self, text: str) -> None:
        hinweis = label(text, "klein")
        hinweis.setWordWrap(True)
        hinweis.setContentsMargins(8, 4, 8, 4)
        self._sonderzeile(hinweis, 52)

    def preis_eur(self, t: str) -> float | None:
        d = self.daten.get(t)
        if not d or not d.get("eur_faktor"):
            return None
        return kurs_jetzt(d)[0] * d["eur_faktor"]

    def guenstige_kaufsignale(self) -> list[str]:
        """Werte mit Kaufsignal (laut Regel), deren Kurs unter PREISGRENZE Euro liegt."""
        return [t for t in self.kaufsignale()
                if (e := self.preis_eur(t)) is not None and e < self.preisgrenze]

    def _zeile(self, ticker: str, bereich: str) -> None:
        key = f"{bereich}:{ticker}"
        item = QListWidgetItem()
        item.setData(Qt.UserRole, ticker)
        item.setData(Qt.UserRole + 1, key)
        item.setSizeHint(QSize(0, 62))
        flaggen = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if bereich == "meine" and self.sortierung == "eigene":
            flaggen |= Qt.ItemIsDragEnabled
        item.setFlags(flaggen)
        zeile = Zeile(ticker, ticker in self.meine, in_euro=bereich == "guenstig")
        zeile.stern_geklickt.connect(self.markieren)
        self.liste.addItem(item)
        self.liste.setItemWidget(item, zeile)
        self.items[key] = (item, zeile)
        zeile.setze(self.daten.get(ticker), self.fehler.get(ticker, ""))

    def zeilen_von(self, ticker: str) -> list[Zeile]:
        return [z for k, (_, z) in self.items.items() if k.split(":", 1)[1] == ticker]

    def aktueller_ticker(self) -> str | None:
        if getattr(self, "extra_ticker", None):
            return self.extra_ticker
        item = self.liste.currentItem()
        return item.data(Qt.UserRole) if item else None

    def aufbauen(self, auswahl: str | None = None) -> None:
        """Baut die Liste neu auf. auswahl = Ticker oder "bereich:ticker"."""
        item = self.liste.currentItem()
        aktuell = item.data(Qt.UserRole + 1) if item else None
        scroll = self.liste.verticalScrollBar().value()
        self.liste.blockSignals(True)
        self.liste.clear()
        self.items.clear()

        bereich = "Kryptowährungen" if self.krypto_modus else "Aktien & ETFs"
        for b in self.bereich_knoepfe.buttons():
            n = len([t for t in self.meine if self.ist_krypto(t) == b.property("krypto")])
            b.setText(f"{b.property('name')}  ·  {n}".replace("&", "&&"))  # & ist sonst Kürzel

        meine = self.sortiert(self.im_bereich(self.meine))
        kopf_m = Abschnitt("", symbol="stern")
        listen_knopf = mit_pfeil(QPushButton(f"{self.aktive_liste}  ·  {len(meine)}",
                                             objectName="listenwahl"))
        listen_knopf.setCursor(Qt.PointingHandCursor)
        listen_knopf.setToolTip("Liste wechseln, neue Liste anlegen …")
        listen_knopf.clicked.connect(lambda: self.liste_menue(listen_knopf))
        kopf_m.layout().insertWidget(1, listen_knopf)
        sortier = mit_pfeil(QPushButton(SORTIERUNGEN[self.sortierung], objectName="seg"))
        sortier.setCursor(Qt.PointingHandCursor)
        sortier.setToolTip("Sortierung von „Meine“")
        sortier.clicked.connect(lambda: self.sortier_menue(sortier))
        kopf_m.layout().addWidget(sortier)
        self._sonderzeile(kopf_m, 44)
        if not meine:
            self._hinweis(f"Noch keine {bereich} gemerkt. Such oben einen Wert "
                          "und klicke dort auf „Merken“.")
        for t in meine:
            self._zeile(t, "meine")

        guenstig = self.guenstige_kaufsignale()
        kopf_g = Abschnitt(f"Unter {zahl(self.preisgrenze, 0)} €  ·  {len(guenstig)}",
                           "Kaufsignal laut Regel · keine Empfehlung", symbol="preis")
        kopf_g.setToolTip(f"Werte mit Kaufsignal laut Regel, deren aktueller Kurs unter "
                          f"{zahl(self.preisgrenze, 0)} € liegt (Fremdwährungen umgerechnet). "
                          "Ein niedriger Stückpreis heißt nicht, dass ein Wert günstig "
                          "bewertet ist.")
        self._sonderzeile(kopf_g, 48)
        if not guenstig:
            self._hinweis(f"Gerade kein Wert unter {zahl(self.preisgrenze, 0)} € mit Kaufsignal."
                          if not self.ladend else "Prüfe Markt …")
        for t in guenstig:
            self._zeile(t, "guenstig")

        kauf = self.kaufsignale()
        self.kauf_angezeigt = kauf
        alle = self.im_bereich(self.alle_tickers())
        geprueft = sum(1 for t in alle if t in self.daten or t in self.fehler)
        gesamt = len(alle)
        kopf = Abschnitt(f"Kaufsignale jetzt  ·  {len(kauf)}",
                         "laut Regel · keine Empfehlung", symbol="trend", symbol_farbe=GOLD)
        kopf.setToolTip(f"Von {gesamt} geprüften {bereich} (deine + bekannte Werte) zeigt "
                        "die Regel bei diesen gerade KAUFEN (Score ≥ +2). "
                        "Sortiert nach Score, dann niedrigster RSI.")
        self._sonderzeile(kopf, 48)
        if geprueft < gesamt:
            self._hinweis(f"Prüfe Markt … {geprueft} von {gesamt} Werten")
        elif not kauf:
            self._hinweis("Bei keinem der geprüften Werte zeigt die Regel gerade KAUFEN.")
        for t in kauf:
            self._zeile(t, "kauf")

        vs = self.vorschlaege()
        if vs:
            self._sonderzeile(Abschnitt("Vorschläge", "Stern klicken zum Merken",
                                        symbol="funke"), 48)
            for t in vs:
                self._zeile(t, "vorschlag")

        ziel = None
        for wunsch in (auswahl, aktuell):
            if not wunsch:
                continue
            if wunsch in self.items:
                ziel = wunsch
            else:
                ziel = next((k for k in self.items if k.split(":", 1)[1] == wunsch), None)
            if ziel:
                break
        if not ziel and not self.extra_ticker:
            ziel = next(iter(self.items), None)
        if ziel:
            self.liste.setCurrentItem(self.items[ziel][0])
        self.liste.blockSignals(False)
        if not auswahl:
            self.liste.verticalScrollBar().setValue(scroll)
        else:
            self.liste.scrollToItem(self.items[ziel][0]) if ziel else None
        self.auswahl_geaendert()

    def bereich_setzen(self, krypto: bool, auswahl: str | None = None) -> None:
        if krypto != self.krypto_modus:
            self.krypto_modus = krypto
            self.einstellungen.setValue("krypto", krypto)
            self.bereich_knoepfe.button(1 if krypto else 0).setChecked(True)
            self.liste.setCurrentItem(None)  # Auswahl gehört zum alten Bereich
            self.aufbauen(auswahl=auswahl)
            self.liste.scrollToTop() if not auswahl else None
        else:
            self.aufbauen(auswahl=auswahl)

    # --- Merken / Entfernen

    def markieren(self, ticker: str) -> None:
        if ticker in self.meine:
            self.meine.remove(ticker)
        else:
            self.meine.append(ticker)
        self.speichern()
        self.aufbauen(auswahl=f"meine:{ticker}" if ticker in self.meine else ticker)
        if ticker not in self.daten:
            self.laden(ticker)

    def hinzufuegen(self) -> None:
        """Gesuchten Wert öffnen – gemerkt wird er erst mit Klick auf den Stern."""
        t = self.eingabe.text().strip().upper()
        if not t:
            return
        self.eingabe.clear()
        self.oeffnen(t)

    def entfernen(self) -> None:
        t = self.aktueller_ticker()
        if t and t in self.meine:
            self.markieren(t)

    def kontextmenue(self, pos) -> None:
        item = self.liste.itemAt(pos)
        t = item.data(Qt.UserRole) if item else None
        if not t:
            return
        menue = QMenu(self)
        a_merk = QAction("Nicht mehr merken" if t in self.meine else "Merken", menue)
        a_merk.triggered.connect(lambda: self.markieren(t))
        a_neu = QAction("Neu laden", menue)
        a_neu.triggered.connect(lambda: self.laden(t))
        menue.addAction(a_merk)
        if len(self.listen) > 1:
            unter = menue.addMenu("In Listen")
            for name, werte in self.listen.items():
                a = QAction(name, unter, checkable=True)
                a.setChecked(t in werte)
                a.triggered.connect(lambda _=False, n=name: self.in_liste_umschalten(n, t))
                unter.addAction(a)
        if t in self.meine and self.sortierung == "eigene":
            for txt, schritt in (("Nach oben", -1), ("Nach unten", 1),
                                 ("Ganz nach oben", -999)):
                a = QAction(txt, menue)
                a.triggered.connect(lambda _=False, s_=schritt: self.verschieben(t, s_))
                menue.addAction(a)
        menue.addAction(a_neu)
        menue.exec(self.liste.mapToGlobal(pos))

    # --- Sortieren / Verschieben

    def sortiert(self, tickers: list[str]) -> list[str]:
        art = self.sortierung
        if art == "eigene":
            return tickers

        def schluessel(t):
            d = self.daten.get(t)
            if not d:
                return (1, 0, t)
            if art == "name":
                return (0, 0, d["name"].lower())
            if art == "aenderung":
                return (0, -kurs_jetzt(d)[1], t)
            score = int(d["df"]["score"].iloc[-1])
            return (0, -score, t)
        return sorted(tickers, key=schluessel)

    def sortier_menue(self, knopf: QPushButton) -> None:
        menue = QMenu(self)
        for key, txt in SORTIERUNGEN.items():
            a = QAction(txt, menue, checkable=True)
            a.setChecked(key == self.sortierung)
            a.triggered.connect(lambda _=False, k=key: self.sortierung_setzen(k))
            menue.addAction(a)
        menue.addSeparator()
        hinweis = QAction("Eigene Reihenfolge: Rechtsklick → Nach oben/unten", menue)
        hinweis.setEnabled(False)
        menue.addAction(hinweis)
        menue.exec(knopf.mapToGlobal(knopf.rect().bottomLeft()))

    def sortierung_setzen(self, art: str) -> None:
        self.sortierung = art
        self.einstellungen.setValue("sortierung", art)
        self.aufbauen()

    def verschieben(self, ticker: str, schritt: int) -> None:
        """Verschiebt einen Wert innerhalb von „Meine“ (nur im aktuellen Bereich)."""
        bereich = self.im_bereich(self.meine)
        i = bereich.index(ticker)
        ziel = max(0, min(len(bereich) - 1, i + schritt))
        if ziel == i:
            return
        bereich.insert(ziel, bereich.pop(i))
        andere = iter(bereich)
        self.meine = [next(andere) if self.ist_krypto(t) == self.krypto_modus else t
                      for t in self.meine]
        self.speichern()
        self.aufbauen(auswahl=f"meine:{ticker}")

    # --- Suche

    def suche_starten(self) -> None:
        begriff = self.eingabe.text().strip()
        if not begriff:
            self.vorschlag_modell.clear()
            return
        job = Suche(begriff)
        job.signale.fertig.connect(self.vorschlaege_da)
        self.pool.start(job)

    def logo_da(self, ticker: str) -> None:
        """Ein Logo ist angekommen: überall eintragen, wo der Wert angezeigt wird."""
        for a in self.findChildren(QLabel):
            if a.property("avatar_ticker") == ticker:
                avatar_fuellen(a)
        logo = LOGOS.get(ticker)
        if logo is not None:
            for r in range(self.vorschlag_modell.rowCount()):
                item = self.vorschlag_modell.item(r)
                if item.data(Qt.UserRole) == ticker:
                    item.setIcon(logo_icon(ticker))

    def vorschlaege_da(self, begriff: str, vorschlaege: list) -> None:
        if begriff != self.eingabe.text().strip():
            return
        self.vorschlag_modell.clear()
        for sym, anzeige in vorschlaege:
            item = QStandardItem(anzeige)
            item.setIcon(logo_icon(sym))
            if sym not in LOGOS:
                LOGO_DIENST.anfordern(sym)
            item.setData(sym, Qt.UserRole)
            self.vorschlag_modell.appendRow(item)
        if vorschlaege and self.eingabe.hasFocus():
            self.completer.complete()
            self.completer.popup().setMinimumWidth(max(self.eingabe.width(), 560))

    def vorschlag_gewaehlt(self, symbol: str) -> None:
        self.eingabe.setText(symbol)
        self.hinzufuegen()
        QTimer.singleShot(0, self.eingabe.clear)
        self.vorschlag_modell.clear()

    # --- Kurse laden

    def alle_laden(self) -> None:
        for t, _ in HOME_INDIZES:
            self.laden(t)
        for t in self.alle_tickers():
            self.laden(t)

    def aus_cache_laden(self) -> None:
        """Beim Start: zuletzt gespeicherte Kurse sofort anzeigen, bis die neuen da sind."""
        for t in [t for t, _ in HOME_INDIZES] + self.alle_tickers():
            job = Lader(t, nur_cache=True)
            job.signale.fertig.connect(self.geladen)
            self.pool.start(job)

    def laden(self, ticker: str) -> None:
        if ticker in self.ladend:
            return
        self.ladend.add(ticker)
        self.status_setzen()
        job = Lader(ticker)
        job.signale.fertig.connect(self.geladen)
        job.signale.fehler.connect(self.fehlgeschlagen)
        self.pool.start(job)

    # --- Hintergrund, Menüleiste, Einstellungen

    def closeEvent(self, e):
        if not self.wirklich_beenden and self.einstellungen.value("hintergrund", True, type=bool):
            e.ignore()
            self.hide()
            if not self.einstellungen.value("hinweis_hintergrund", False, type=bool):
                self.einstellungen.setValue("hinweis_hintergrund", True)
                konto.melden("Vyntro läuft im Hintergrund weiter",
                             "Alarme bleiben aktiv. " + pfade.BEENDEN_TIPP)
            return
        super().closeEvent(e)
        QApplication.instance().quit()

    def zeigen(self) -> None:
        if not self.isVisible():  # aus dem Hintergrund geholt: wieder auf Home
            self.ansicht_setzen("home")
        self.show()
        self.raise_()
        self.activateWindow()

    def beenden(self) -> None:
        self.wirklich_beenden = True
        QApplication.instance().quit()

    def _app_zustand(self, zustand) -> None:
        # Klick aufs Dock-Symbol, während das Fenster versteckt ist: wieder zeigen
        if zustand == Qt.ApplicationActive and not self.isVisible():
            self.zeigen()

    def menueleisten_optionen(self) -> list[tuple[str, str]]:
        return ([("depot", "Depotwert"), ("aus", "Nur Symbol")]
                + [(t, t) for t in self.meine])

    def einstellungen_oeffnen(self) -> None:
        e = self.einstellungen
        werte = {"autostart": konto.autostart_an(),
                 "hintergrund": e.value("hintergrund", True, type=bool),
                 "menueleiste": e.value("menueleiste", "depot", type=str),
                 "termine": e.value("termine", True, type=bool),
                 "freibetrag": e.value("freibetrag", 1000.0, type=float),
                 "preisgrenze": self.preisgrenze}
        dlg = EinstellungenDialog(self, werte, self.menueleisten_optionen())
        if dlg.exec() != QDialog.Accepted:
            return
        neu = dlg.werte()
        if neu["autostart"] != werte["autostart"]:
            try:
                konto.autostart_setzen(neu["autostart"])
            except OSError as fehler:
                self.meldung.zeige("Autostart nicht möglich", str(fehler))
        for k in ("hintergrund", "menueleiste", "termine", "preisgrenze", "freibetrag"):
            e.setValue(k, neu[k])
        self.depot.freibetrag = neu["freibetrag"]
        self.seite_auffrischen()
        if neu["preisgrenze"] != self.preisgrenze:
            self.preisgrenze = neu["preisgrenze"]
            self.aufbauen()
        if self.leiste:
            self.leiste.aktualisieren()

    def termine_pruefen(self, ticker: str) -> None:
        """Einmalige Mitteilung, wenn morgen (oder heute) Quartalszahlen kommen."""
        if not self.einstellungen.value("termine", True, type=bool):
            return
        if ticker not in self.meine and ticker not in konto.positionen(self.kaeufe):
            return
        d = self.daten.get(ticker)
        if not d:
            return
        gemeldet = set(self.einstellungen.value("gemeldete_termine", [], type=list) or [])
        for name, zeit, wann in termine(d.get("info")):
            if name != "Quartalszahlen" or wann not in ("heute", "morgen"):
                continue
            key = f"{ticker}:{zeit:%Y-%m-%d}"
            if key in gemeldet:
                continue
            gemeldet.add(key)
            self.einstellungen.setValue("gemeldete_termine", sorted(gemeldet)[-200:])
            self.ausloesen(f"{ticker}: Quartalszahlen {wann}",
                           f"{kurzer_name(d['name'])} legt am {zeit:%d.%m.%Y} Zahlen vor. "
                           "Rund um solche Termine schwankt der Kurs oft stärker.")

    def status_setzen(self) -> None:
        if getattr(self, "leiste", None):
            self.leiste.aktualisieren()
        if self.ladend:
            self.status.setText(f"Lade Kurse … ({len(self.ladend)})")
        elif self.stream.verbunden:
            self.status.setText(f"<span style='color:{T['gruen']}'>●</span>&nbsp;Live · "
                                f"{datetime.now():%H:%M:%S}")
            letzte = f"{self.live_zeit:%H:%M:%S}" if self.live_zeit else "–"
            self.status.setToolTip(
                f"Echtzeit-Stream verbunden · {self.stream.updates} Kurs-Updates empfangen · "
                f"letztes um {letzte}. Kurse kommen, sobald gehandelt wird – bei geschlossener "
                "Börse bleibt der Kurs stehen. Die Signale werden aus Tagesschlusskursen "
                "berechnet.")
        elif getattr(self, "offline", False):
            self.status.setText(f"<span style='color:{T['rot']}'>●</span>&nbsp;Keine Verbindung")
            self.status.setToolTip("Yahoo Finance ist gerade nicht erreichbar. Angezeigt werden "
                                   "die zuletzt geladenen Kurse.")
        elif self.live_zeit:
            self.status.setText(f"<span style='color:{T['orange']}'>●</span>&nbsp;Minütlich · "
                                f"{self.live_zeit:%H:%M:%S}")
            self.status.setToolTip("Echtzeit-Stream gerade nicht verbunden – Kurse werden "
                                   "jede Minute abgefragt.")
        else:
            self.status.setText(f"Aktualisiert {datetime.now():%H:%M}")

    def geladen(self, ticker: str, d: dict) -> None:
        if d.get("aus_cache"):
            if ticker in self.daten:  # frische Daten sind schon da
                return
        else:
            self.ladend.discard(ticker)
        self.status_setzen()
        alt = self.daten.get(ticker)
        if alt and alt.get("live") and "live" not in d:
            d["live"] = alt["live"]  # Live-Kurs beim Neuberechnen behalten
        self.daten[ticker] = d
        self.fehler.pop(ticker, None)
        self.nach_laden(ticker)
        if not d.get("aus_cache"):  # Alarme nur mit frischen Kursen prüfen
            self.signal_alarme_pruefen(ticker)
            self.kurs_alarme_pruefen([ticker])
            self.termine_pruefen(ticker)
        if ticker in self.detail.vergleich and self.ansicht == "detail":
            self.detail.zeichne_chart()
        if self.ansicht in ("markt", "home"):
            self.markt_timer.start()  # gesammelt neu aufbauen
        elif self.ansicht != "detail":
            self.seite_auffrischen()

    def fehlgeschlagen(self, ticker: str, meldung: str) -> None:
        self.ladend.discard(ticker)
        if ticker in self.daten:  # z. B. offline: gespeicherte Kurse weiter anzeigen
            self.offline = True
            self.status_setzen()
            return
        self.status_setzen()
        self.fehler[ticker] = meldung
        self.nach_laden(ticker)

    def nach_laden(self, ticker: str) -> None:
        for z in self.zeilen_von(ticker):
            z.setze(self.daten.get(ticker), self.fehler.get(ticker, ""))
        if self.aktueller_ticker() == ticker:
            self.auswahl_geaendert()
        # Kaufsignal-Bereich (und Fortschritt) gesammelt neu aufbauen, höchstens alle 400 ms
        if not self.umbau_timer.isActive():
            self.umbau_timer.start()

    # --- Anzeige

    def theme_anwenden(self) -> None:
        QApplication.instance().setStyleSheet(qss())
        self.aufbauen()

    def zeige_leer(self, text: str) -> None:
        self.leer.setText(text)
        if self.ansicht == "detail":  # Home, Markt usw. nicht überdecken
            self.stapel.setCurrentWidget(self.leer)

    def auswahl_geaendert(self) -> None:
        if self.ansicht != "detail":
            self.seite_auffrischen()
            return
        t = self.aktueller_ticker()
        if not t:
            self.zeige_leer("Suche oben links nach einer Aktie, einem ETF oder einer "
                            "Kryptowährung.")
        elif t in self.fehler:
            self.zeige_leer(f"Für {t} wurden keine Kursdaten gefunden.")
        elif t not in self.daten:
            self.zeige_leer(f"{t} wird geladen …")
        else:
            neu_gewaehlt = t != self.detail.ticker
            self.detail.vergleich_kandidaten = list(dict.fromkeys(
                self.meine + [k["ticker"] for k in self.kaeufe]))
            self.detail.zeige(t, self.daten[t], gemerkt=t in self.meine)
            self.konto_karte_setzen()
            self.stapel.setCurrentWidget(self.detail_scroll)
            if neu_gewaehlt:
                self.detail_scroll.verticalScrollBar().setValue(0)
            self.news_zeigen(t)

    # --- Nachrichten

    def news_zeigen(self, t: str) -> None:
        cache = self.news_cache.get(t)
        if cache and (datetime.now() - cache[0]).total_seconds() < 600:
            self.detail.k_info.setze_news(cache[1])
            return
        self.detail.k_info.setze_news(cache[1] if cache else None)
        if t in self.news_ladend:
            return
        self.news_ladend.add(t)
        d = self.daten[t]
        job = NewsJob(t, d["name"], d["typ"])
        job.signale.fertig.connect(self.news_da)
        self.pool.start(job)

    def news_da(self, t: str, artikel: list) -> None:
        self.news_ladend.discard(t)
        self.news_cache[t] = (datetime.now(), artikel)
        if self.aktueller_ticker() == t and self.detail.ticker == t:
            self.detail.k_info.setze_news(artikel)

    # --- Live-Kurse

    def live_laden(self) -> None:
        if self.live_laeuft:
            return
        tickers = [t for t in [t for t, _ in HOME_INDIZES] + self.alle_tickers()
                   if t in self.daten]
        if not tickers:
            return
        self.live_laeuft = True
        job = LiveJob(tickers)
        job.signale.fertig.connect(self.live_da)
        self.pool.start(job)

    def live_da(self, kurse: dict, verlauf: dict | None = None) -> None:
        self.live_laeuft = False
        for t, werte in (verlauf or {}).items():
            if t in self.daten:
                self.daten[t]["spark"] = werte
        self.offline = not kurse and not self.stream.verbunden
        if not kurse:
            self.status_setzen()
            return
        self.live_zeit = datetime.now()
        for t, wert in kurse.items():
            if t in self.daten:
                alt = self.daten[t].get("live")
                if alt is not None and alt[1] >= wert[1]:
                    continue  # Stream-Kurs ist neuer
                self.daten[t]["live"] = wert
                for z in self.zeilen_von(t):
                    z.aktualisiere()
        t = self.aktueller_ticker()
        if t in self.daten and self.detail.ticker == t:
            self.detail.kopf_kurs(t, self.daten[t])
            self.detail.k_konto.kurs(self.daten[t])
        self.kurs_alarme_pruefen(kurse.keys())
        if self.ansicht == "depot":
            self.seite_auffrischen()
        elif self.ansicht == "markt":
            self.seite_auffrischen(tabelle=False)
        self.status_setzen()

    def sekunde(self) -> None:
        """Jede Sekunde: neue Kurse aus dem Live-Stream übernehmen und anzeigen."""
        self.stream.abonnieren(t for t in [t for t, _ in HOME_INDIZES] + self.alle_tickers()
                               if t in self.daten)
        neu = self.stream.abholen()
        for t, wert in neu.items():
            if t in self.daten:
                self.daten[t]["live"] = wert
                for z in self.zeilen_von(t):
                    z.aktualisiere()
        t = self.aktueller_ticker()
        if t in neu and t in self.daten and self.detail.ticker == t:
            self.detail.kopf_kurs(t, self.daten[t])
            self.detail.k_konto.kurs(self.daten[t])
        if neu:
            self.live_zeit = datetime.now()
            self.kurs_alarme_pruefen(neu.keys())
            if self.ansicht == "depot":
                self.seite_auffrischen()
            elif self.ansicht == "markt":
                self.seite_auffrischen(tabelle=False)
        if self.ansicht == "detail":
            self.detail.intraday_auffrischen()
        elif self.ansicht == "home" and time.time() - self._home_zeit > 3:
            self.seite_auffrischen()
        self.status_setzen()

    # --- Ansichten: Detail / Depot / Alarme

    def _listenwahl(self) -> None:
        self.extra_ticker = None
        self.ansicht_setzen("detail")

    def ansicht_setzen(self, ansicht: str) -> None:
        self.ansicht = ansicht
        self.k_depot.setChecked(ansicht == "depot")
        self.k_alarme.setChecked(ansicht == "alarme")
        self.k_markt.setChecked(ansicht == "markt")
        self.k_home.setChecked(ansicht == "home")
        if ansicht == "detail":
            self.auswahl_geaendert()
        else:
            self.seite_auffrischen()
            self.stapel.setCurrentWidget(self.seiten[ansicht])

    def seite_auffrischen(self, tabelle: bool = True) -> None:
        if self.ansicht == "home":
            self._home_zeit = time.time()
            self.home.setze(self)
        elif self.ansicht == "markt":
            self.markt.setze(self.daten, self.meine, konto.positionen(self.kaeufe), tabelle)
        elif self.ansicht == "depot":
            self.depot.setze(self.kaeufe, self.daten)
        elif self.ansicht == "alarme":
            self.alarm_seite.setze(self.alarme, self.daten)

    def oeffnen(self, ticker: str) -> None:
        """Wert (aus Übersichten, Heatmap, Schnellsuche …) in der Detailansicht öffnen."""
        self.ansicht = "detail"
        self.k_depot.setChecked(False)
        self.k_alarme.setChecked(False)
        self.k_markt.setChecked(False)
        self.k_home.setChecked(False)
        self.extra_ticker = None
        self.bereich_setzen(self.ist_krypto(ticker), auswahl=ticker)
        item = self.liste.currentItem()
        if not item or item.data(Qt.UserRole) != ticker:  # steht in keiner Liste
            self.extra_ticker = ticker
            self.liste.blockSignals(True)
            self.liste.setCurrentItem(None)
            self.liste.clearSelection()
            self.liste.blockSignals(False)
            if ticker not in self.daten:
                self.laden(ticker)
            self.auswahl_geaendert()

    def update_pruefen(self) -> None:
        job = UpdatePruefung()
        job.signale.gefunden.connect(self._update_gefunden)
        self.pool.start(job)

    def _update_gefunden(self, info) -> None:
        if not info or not info.get("version") or not update.ist_neuer(info["version"]):
            return
        if update.art() == "windows" and not info.get("installer"):
            return  # Release ohne Installer (wird gerade noch gebaut)
        neu = self.update_info is None or self.update_info["version"] != info["version"]
        self.update_info = info
        self.update_knopf.setText(f"  Neue Version {info['version']}")
        self.update_knopf.setIcon(icon("import", "#19e6a2", 14))
        self.update_knopf.setToolTip("Jetzt aktualisieren")
        self.update_knopf.show()
        if neu:
            self.meldung.zeige(f"Vyntro {info['version']} ist verfügbar",
                               "Klick oben auf „Neue Version“, um zu aktualisieren.")

    def update_zeigen(self) -> None:
        if self.update_info:
            UpdateDialog(self, self.update_info).exec()

    def anleitung_oeffnen(self, kapitel: str = "start") -> None:
        self.ansicht_setzen("anleitung")
        self.anleitung.suche.clear()
        self.anleitung.oeffnen(kapitel)

    def schnellsuche(self) -> None:
        if not hasattr(self, "_palette"):
            self._palette = Schnellsuche(self)
        self._palette.zeigen()

    def knoepfe_beschriften(self) -> None:
        n_pos = len(konto.positionen(self.kaeufe))
        n_al = sum(1 for a in self.alarme if a["aktiv"])
        self.k_depot.setText(f" Depot  ·  {n_pos}" if n_pos else " Depot")
        self.k_alarme.setText(f" Alarme  ·  {n_al}" if n_al else " Alarme")

    def notiz_speichern(self, ticker: str, text: str) -> None:
        self.notizen[ticker] = text
        konto.speichere_notizen(self.notizen)

    def depot_importieren(self, datei: str | None = None) -> None:
        if not datei:
            datei, _ = QFileDialog.getOpenFileName(
                self, "Trade-Republic-Export wählen", str(s.Path.home() / "Downloads"),
                "CSV-Dateien (*.csv)")
        if not datei:
            return
        try:
            buchungen = tr_import.lesen(s.Path(datei))
        except (OSError, ValueError, UnicodeDecodeError) as fehler:
            self.meldung.zeige("Import nicht möglich", str(fehler))
            return
        if not buchungen:
            self.meldung.zeige("Nichts zu importieren",
                               "In der Datei stehen keine Käufe oder Verkäufe.")
            return
        vorhanden = {k.get("tr_id") for k in self.kaeufe if k.get("tr_id")}
        dlg = ImportDialog(self, buchungen, vorhanden)
        self._import_dialog = dlg
        if dlg.exec() != QDialog.Accepted:
            return
        neu, zuordnung = dlg.ergebnis()
        tr_import.zuordnung_merken(zuordnung)
        self.kaeufe.extend(neu)
        self.konto_geaendert()
        for t in {k["ticker"] for k in neu}:
            if t not in self.daten:
                self.laden(t)
        self.meldung.zeige("Import fertig", f"{len(neu)} Buchungen aus Trade Republic "
                                            "übernommen.")
        self.ansicht_setzen("depot")

    def depot_exportieren(self) -> None:
        vorschlag = str(s.Path.home() / "Downloads" / f"Vyntro-Depot-{datetime.now():%Y-%m-%d}.csv")
        datei, _ = QFileDialog.getSaveFileName(self, "Depot exportieren", vorschlag,
                                               "CSV-Tabelle (*.csv)")
        if not datei:
            return
        namen = {t: d["name"] for t, d in self.daten.items()}
        bewertung = {t: konto.bewerte(p, self.preis_eur(t))
                     for t, p in konto.positionen(self.kaeufe).items()}
        try:
            konto.csv_export(s.Path(datei), self.kaeufe, namen, bewertung)
            self.meldung.zeige("Depot exportiert", s.Path(datei).name)
        except OSError as fehler:
            self.meldung.zeige("Export fehlgeschlagen", str(fehler))

    def konto_karte_setzen(self) -> None:
        t = self.detail.ticker
        if t:
            self.detail.k_notiz.setze(t, self.notizen.get(t, ""))
        if t and t in self.daten:
            werte = konto.alle_werte(self.kaeufe).get(t)
            self.detail.k_konto.setze(t, self.daten[t], konto.positionen(self.kaeufe).get(t),
                                      [a for a in self.alarme if a["ticker"] == t],
                                      werte["kaeufe"] if werte else [],
                                      werte["realisiert"] if werte else 0.0)

    def konto_geaendert(self) -> None:
        konto.speichere_kaeufe(self.kaeufe)
        konto.speichere_alarme(self.alarme)
        self.knoepfe_beschriften()
        self.konto_karte_setzen()
        self.seite_auffrischen()

    # --- Depot

    def kauf_eintragen(self, ticker: str) -> None:
        d = self.daten.get(ticker)
        if not d:
            return
        pos = konto.positionen(self.kaeufe).get(ticker)
        dlg = KaufDialog(self, ticker, d["name"], self.preis_eur(ticker),
                         pos["stueck"] if pos else 0.0)
        if dlg.exec() != QDialog.Accepted:
            return
        self.kaeufe.append(dlg.ergebnis(ticker))
        if ticker not in self.meine:  # was man besitzt, will man auch beobachten
            self.meine.append(ticker)
            self.speichern()
            self.detail.setze_gemerkt(True)
            self.umbau_timer.start()
        self.konto_geaendert()

    def kauf_loeschen(self, kauf_id: str) -> None:
        self.kaeufe = [k for k in self.kaeufe if k["id"] != kauf_id]
        self.konto_geaendert()

    # --- Alarme

    def alarm_anlegen(self, ticker: str) -> None:
        d = self.daten.get(ticker)
        if not d:
            return
        dlg = AlarmDialog(self, ticker, d["name"], kurs_jetzt(d)[0], d["waehrung"],
                          float(d["df"]["rsi"].iloc[-1]))
        if dlg.exec() != QDialog.Accepted:
            return
        art = dlg.art()
        signal = s.empfehlung(int(d["df"]["score"].iloc[-1]))
        ohne_wert = art in ("signal", "hoch52", "tief52")
        self.alarme.append(konto.alarm(ticker, art, None if ohne_wert else dlg.wert.value(),
                                       signal))
        self.konto_geaendert()

    def alarm_loeschen(self, alarm_id: str) -> None:
        self.alarme = [a for a in self.alarme if a["id"] != alarm_id]
        self.konto_geaendert()

    def alarm_wieder_an(self, alarm_id: str) -> None:
        for a in self.alarme:
            if a["id"] == alarm_id:
                d = self.daten.get(a["ticker"])
                if d and alarm_pruefen({**a, "aktiv": True}, d) and a["art"] in ("ueber",
                                                                                 "unter"):
                    self.meldung.zeige("Alarm nicht aktiviert",
                                       f"{a['ticker']} steht schon jenseits von "
                                       f"{kurs_text(a['wert'])} {d['waehrung']}. Lege einen "
                                       "neuen Alarm mit einer anderen Marke an.")
                    return
                a["aktiv"], a["ausgeloest"] = True, None
        self.konto_geaendert()

    def ausloesen(self, titel: str, text: str) -> None:
        konto.melden(titel, text)
        self.meldung.zeige(titel, text)
        QApplication.alert(self)  # Dock-Symbol hüpft, falls Vyntro im Hintergrund ist

    def kurs_alarme_pruefen(self, tickers) -> None:
        tickers = set(tickers)
        geaendert = False
        for a in self.alarme:
            if a["ticker"] not in tickers or a["ticker"] not in self.daten:
                continue
            d = self.daten[a["ticker"]]
            if d.get("aus_cache"):
                continue
            treffer = alarm_pruefen(a, d)
            if treffer:
                a["aktiv"] = False
                a["ausgeloest"] = datetime.now().isoformat(timespec="seconds")
                self.ausloesen(*treffer)
                geaendert = True
        if geaendert:
            self.konto_geaendert()

    def signal_alarme_pruefen(self, ticker: str) -> None:
        d = self.daten.get(ticker)
        if not d:
            return
        jetzt = s.empfehlung(int(d["df"]["score"].iloc[-1]))
        geaendert = False
        for a in self.alarme:
            if a["ticker"] != ticker or a["art"] != "signal" or not a["aktiv"]:
                continue
            if a.get("signal") and a["signal"] != jetzt:
                a["ausgeloest"] = datetime.now().isoformat(timespec="seconds")
                self.ausloesen(f"{ticker}: Signal jetzt {jetzt}",
                               f"{kurzer_name(d['name'])}: Die Regel zeigt jetzt {jetzt} "
                               f"(vorher {a['signal']}). {d['begruendung'].kurz}")
            if a.get("signal") != jetzt:
                a["signal"] = jetzt
                geaendert = True
        if geaendert:
            self.konto_geaendert()

    def eigene_neu_laden(self) -> None:
        """Alle 15 Minuten: eigene Werte, Depot und Alarm-Werte neu berechnen."""
        for t in dict.fromkeys(self.meine + [k["ticker"] for k in self.kaeufe]
                               + [a["ticker"] for a in self.alarme]):
            self.laden(t)



class Startbild(QWidget):
    """Startbildschirm: Logo, Schriftzug und ein feiner Ladebalken, während die Kurse
    aus dem Zwischenspeicher und dem Netz kommen."""

    BREITE, HOEHE = 560, 400

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                         | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(self.BREITE, self.HOEHE)
        self.fortschritt = 0.0
        self.text = "Starte …"
        self.phase = 0.0
        self.logo = QPixmap(str(LOGO_DATEI)) if LOGO_DATEI.exists() else QPixmap()
        # Kursverlauf, der sich beim Laden zeichnet: Zufallsweg mit Aufwärtstrend,
        # immer gleich (fester Startwert), damit er jedes Mal schön aussieht
        import random
        zufall = random.Random(7)
        roh, v = [], 0.0
        for i in range(72):
            v += 0.35 + i * 0.022 + zufall.gauss(0, 0.9)  # Trend wird nach rechts steiler
            if i in (20, 21, 44, 45):  # ein paar Rücksetzer, damit es echt wirkt
                v -= 2.6
            roh.append(v)
        werte = [sum(roh[max(0, i - 1):i + 2]) / len(roh[max(0, i - 1):i + 2])
                 for i in range(len(roh))]  # leicht geglättet
        unten, oben = min(werte), max(werte)
        self.kurve = [(w - unten) / (oben - unten) for w in werte]
        bildschirm = QApplication.primaryScreen().availableGeometry()
        self.move(bildschirm.center().x() - self.BREITE // 2,
                  bildschirm.center().y() - self.HOEHE // 2 - 40)
        self.setWindowOpacity(0.0)
        self._takt = QTimer(self, interval=16)
        self._takt.timeout.connect(self._weiter)
        self._takt.start()

    def zeigen(self) -> None:
        self.show()
        self._blende(0.0, 1.0, 380)

    def _blende(self, von: float, bis: float, ms: int, fertig=None) -> None:
        anim = QVariantAnimation(self, startValue=von, endValue=bis, duration=ms)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.valueChanged.connect(self.setWindowOpacity)
        if fertig:
            anim.finished.connect(fertig)
        anim.start()
        self._anim = anim

    def setze(self, anteil: float, text: str) -> None:
        self.fortschritt = max(self.fortschritt, min(1.0, anteil))
        self.text = text

    def schliessen(self, danach=None) -> None:
        self.fortschritt = 1.0

        def weg():
            self._takt.stop()
            self.close()
            if danach:
                danach()
        self._blende(self.windowOpacity(), 0.0, 320, weg)

    def _weiter(self) -> None:
        self.phase = (self.phase + 0.012) % 1.0
        self._anzeige = getattr(self, "_anzeige", 0.0)
        self._anzeige += (self.fortschritt - self._anzeige) * 0.08  # weich nachziehen
        self.update()

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        pfad = QPainterPath()
        pfad.addRoundedRect(r, 18, 18)
        grund = QLinearGradient(r.topLeft(), r.bottomRight())
        grund.setColorAt(0, QColor("#0d0f0f"))
        grund.setColorAt(1, QColor("#020202"))
        p.fillPath(pfad, grund)
        # ganz schwacher Mint-Schein hinter dem Logo
        schein = QRadialGradient(QPointF(r.center().x(), r.top() + 135), 210)
        schein.setColorAt(0, QColor(25, 230, 162, 26))
        schein.setColorAt(1, QColor(25, 230, 162, 0))
        p.save()
        p.setClipPath(pfad)
        p.fillRect(r, schein)
        p.restore()
        p.setPen(QPen(QColor(230, 240, 236, 26), 1))
        p.drawPath(pfad)
        p.setPen(QPen(QColor(230, 240, 236, 50), 1))
        p.drawLine(QPointF(r.left() + 18, r.top() + 0.5), QPointF(r.right() - 18, r.top() + 0.5))

        # Logo
        if not self.logo.isNull():
            hoehe = 92
            breite = hoehe * self.logo.width() / self.logo.height()
            p.drawPixmap(QRectF(r.center().x() - breite / 2, r.top() + 72, breite, hoehe),
                         self.logo, QRectF(self.logo.rect()))
        # Schriftzug
        schrift = QFont(pfade.SCHRIFT)
        schrift.setPixelSize(24)
        schrift.setWeight(QFont.DemiBold)
        schrift.setLetterSpacing(QFont.AbsoluteSpacing, 11)
        p.setFont(schrift)
        verlauf = QLinearGradient(0, r.top() + 196, 0, r.top() + 226)
        verlauf.setColorAt(0, QColor("#f2f4f3"))
        verlauf.setColorAt(1, QColor("#9ea5a3"))
        p.setPen(QPen(verlauf, 1))
        p.drawText(QRectF(r.left() + 11, r.top() + 192, r.width(), 36), Qt.AlignCenter,
                   "VYNTRO")
        schrift.setPixelSize(10)
        schrift.setWeight(QFont.Normal)
        schrift.setLetterSpacing(QFont.AbsoluteSpacing, 4)
        p.setFont(schrift)
        p.setPen(QColor("#7d8582"))
        p.drawText(QRectF(r.left() + 4, r.top() + 230, r.width(), 18), Qt.AlignCenter,
                   "SIGNALE  ·  DEPOT  ·  MARKT")

        # Kurslinie, die mit dem Ladefortschritt nach rechts wächst und steigt
        cx, cy, cb, ch_ = r.left() + 70, r.top() + 268, r.width() - 140, 68
        p.setPen(QPen(QColor(230, 240, 236, 18), 1, Qt.DotLine))
        for i in range(3):
            y = cy + ch_ * i / 2
            p.drawLine(QPointF(cx, y), QPointF(cx + cb, y))
        anteil = getattr(self, "_anzeige", 0.0)
        n = len(self.kurve)
        bis = max(1.0, anteil * (n - 1))

        def pkt(i: float) -> QPointF:
            a, b_ = int(i), min(int(i) + 1, n - 1)
            w = self.kurve[a] + (self.kurve[b_] - self.kurve[a]) * (i - a)
            return QPointF(cx + cb * i / (n - 1), cy + ch_ * (1 - w))
        linie = QPainterPath()
        linie.moveTo(pkt(0))
        i = 1
        while i < bis:
            linie.lineTo(pkt(i))
            i += 1
        spitze = pkt(bis)
        linie.lineTo(spitze)
        flaeche = QPainterPath(linie)
        flaeche.lineTo(QPointF(spitze.x(), cy + ch_))
        flaeche.lineTo(QPointF(cx, cy + ch_))
        flaeche.closeSubpath()
        unter = QLinearGradient(0, cy, 0, cy + ch_)
        unter.setColorAt(0, QColor(25, 230, 162, 60))
        unter.setColorAt(1, QColor(25, 230, 162, 0))
        p.fillPath(flaeche, unter)
        stift = QLinearGradient(cx, 0, spitze.x() + 1, 0)
        stift.setColorAt(0, QColor(25, 230, 162, 40))
        stift.setColorAt(1, QColor(25, 230, 162, 255))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QBrush(stift), 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setOpacity(0.18)
        p.drawPath(linie)  # weicher Schein
        p.setOpacity(1.0)
        p.setPen(QPen(QBrush(stift), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(linie)
        # leuchtende, pulsierende Spitze
        puls = 0.5 + 0.5 * math.sin(self.phase * 2 * math.pi * 2)
        glanz = QRadialGradient(spitze, 16 + 6 * puls)
        glanz.setColorAt(0, QColor(25, 230, 162, int(150 + 70 * puls)))
        glanz.setColorAt(1, QColor(25, 230, 162, 0))
        p.setPen(Qt.NoPen)
        p.setBrush(glanz)
        p.drawEllipse(spitze, 22, 22)
        p.setBrush(QColor("#eafff7"))
        p.drawEllipse(spitze, 3.2, 3.2)
        # Prozent an der Spitze
        schrift.setPixelSize(10)
        schrift.setLetterSpacing(QFont.AbsoluteSpacing, 0.5)
        p.setFont(schrift)
        p.setPen(QColor(25, 230, 162, 230))
        p.drawText(QRectF(spitze.x() - 30, spitze.y() - 26, 60, 14), Qt.AlignCenter,
                   f"{int(round(anteil * 100))} %")
        by = cy + ch_ + 4
        schrift.setPixelSize(11)
        schrift.setLetterSpacing(QFont.AbsoluteSpacing, 0.3)
        p.setFont(schrift)
        p.setPen(QColor("#858c8a"))
        p.drawText(QRectF(r.left(), by + 12, r.width(), 18), Qt.AlignCenter, self.text)
        p.end()


def ist_dunkel(app: QApplication) -> bool:
    try:
        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except AttributeError:
        return app.palette().window().color().lightness() < 128


def main() -> int:
    if pfade.WINDOWS:  # eigenes Taskleisten-Symbol und Name in Benachrichtigungen
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Vyntro.App")
        except Exception:  # noqa: BLE001
            pass
    app = QApplication(sys.argv)
    app.setApplicationName("Vyntro")
    if LOGO_DATEI.exists():
        icon = pfade.ressource("vyntro-icon-1024.png")
        app.setWindowIcon(QIcon(str(icon if icon.exists() else LOGO_DATEI)))  # Dock-Symbol
    app.setStyle("Fusion")

    # immer dunkel – unabhängig von der macOS-Einstellung
    T.clear()
    T.update(DUNKEL)
    app.setStyleSheet(qss())
    if "--selbsttest" in sys.argv:  # für den automatischen Build: startet, lädt, beendet
        protokoll = pfade.DATEN / "selbsttest.txt"
        protokoll.write_text("gestartet\n")
        fenster = Fenster()
        fenster.show()
        protokoll.write_text("Fenster gebaut\n")

        def ende():
            protokoll.write_text(f"ok {len(fenster.daten)} Werte geladen\n")
            # hart beenden: nicht auf laufende Downloads im Hintergrund warten
            os._exit(0)
        QTimer.singleShot(25_000, ende)
        return app.exec()

    if "--hintergrund" in sys.argv:  # beim Autostart ohne Fenster und Startbild
        Fenster()
        return app.exec()

    start = Startbild()
    start.zeigen()
    for _ in range(25):  # Startbild einblenden, bevor das Hauptfenster gebaut wird
        app.processEvents()
        time.sleep(0.012)
    start.setze(0.08, "Baue Oberfläche auf …")
    app.processEvents()
    fenster = Fenster()
    beginn = time.time()

    def pruefen():
        tickers = [t for t, _ in HOME_INDIZES] + fenster.alle_tickers()
        da = sum(1 for t in tickers if t in fenster.daten)
        anteil = 0.1 + 0.9 * da / max(1, len(tickers))
        start.setze(anteil, f"Lade Kurse · {da} von {len(tickers)}")
        vergangen = time.time() - beginn
        # alles, was Home zeigt: Indizes, eigene Listen, Depot
        wichtig = ([t for t, _ in HOME_INDIZES] + fenster.alle_listen_tickers()
                   + [k["ticker"] for k in fenster.kaeufe])
        home_fertig = all(t in fenster.daten or t in fenster.fehler for t in wichtig)
        # mindestens kurz zeigen, höchstens 6 Sekunden warten
        if vergangen > 1.3 and ((home_fertig and anteil > 0.85) or vergangen > 6.0):
            uhr.stop()
            start.setze(1.0, "Fertig")
            fenster.ansicht_setzen("home")  # Home mit allen Daten frisch aufbauen
            QTimer.singleShot(260, lambda: start.schliessen())
            QTimer.singleShot(330, lambda: (fenster.setWindowOpacity(0.0), fenster.show(),
                                            fenster.raise_(), fenster.activateWindow(),
                                            einblenden()))

    def einblenden():
        anim = QVariantAnimation(fenster, startValue=0.0, endValue=1.0, duration=300)
        anim.valueChanged.connect(fenster.setWindowOpacity)
        anim.start()
        fenster._einblenden = anim

    uhr = QTimer(interval=80)
    uhr.timeout.connect(pruefen)
    uhr.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
