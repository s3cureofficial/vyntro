# Vyntro

Regelbasierte Kauf-, Halte- und Verkaufssignale für Aktien, ETFs und Krypto – als Desktop-App
für **Windows** und **macOS**. Kursdaten von Yahoo Finance.

> **Keine Anlageberatung.** Vyntro handelt nicht und gibt keine Empfehlungen. Die Signale
> folgen festen Regeln aus Kursdaten (Trend, RSI, MACD); vergangene Ergebnisse sagen nichts
> über die Zukunft.

## Download

**Windows:** Den neuesten Installer `Vyntro-Setup-….exe` unter
[**Releases**](../../releases/latest) herunterladen und ausführen.

Der Installer ist nicht signiert. Windows zeigt deshalb beim ersten Start eventuell
„Der Computer wurde durch Windows geschützt“ – dann auf **Weitere Informationen →
Trotzdem ausführen** klicken. Installiert wird ohne Administratorrechte; Vyntro erscheint im
Startmenü und optional auf dem Desktop.

**macOS:** siehe [Mac-Installation](#mac-installation) weiter unten.

## Funktionen

- **Home:** Markt auf einen Blick (DAX, S&P 500, Nasdaq, Bitcoin, Gold, EUR/USD), Depot,
  Gewinner und Verlierer, Kaufsignale, Termine, Alarme
- **Watchlist** mit Mini-Charts, mehreren Listen, Sortieren und Ziehen mit der Maus
- **Detailansicht:** Kerzen-Chart (1 Tag bis Max) mit Fadenkreuz, Bollinger, Volumen,
  52-Wochen-Linien, Vergleich mit anderen Werten, Begründung des Signals, Prognose-Spanne,
  Backtest, Infos, Termine und Nachrichten
- **Depot:** Käufe und Verkäufe eintragen, Gewinn/Verlust in Euro, Verlauf im Vergleich zum
  MSCI World, Aufteilung, Dividenden, Steuer-Schätzung, CSV-Export
- **Markt:** Heatmap und Filter (Signal, RSI, Dividende, Kurs …) über DAX 40, große
  US-Werte und Krypto
- **Alarme:** Kursmarken, Tagesbewegung, RSI, 52-Wochen-Hoch/-Tief, Signalwechsel –
  als Systemmitteilung, auch im Hintergrund
- **Schnellsuche** (Strg+K / ⌘K), Notizen pro Wert, Autostart, Symbol in Taskleiste/Menüleiste
- **Trade Republic importieren:** Transaktions-Export (CSV) einlesen, Käufe und Verkäufe
  werden übernommen
- **Automatische Updates:** Vyntro meldet neue Versionen und aktualisiert sich auf Knopfdruck
- **Anleitung mit Chart-Kurs:** Trading-Grundlagen, ein Mini-Kurs in elf Lektionen (Kerzen,
  Trends, Unterstützung/Widerstand, Indikatoren, Chartformationen – mit Bildern und Übung),
  Fachbegriffe A–Z und eine Erklärung jeder Funktion

Deine Daten (Listen, Depot, Alarme, Notizen) bleiben auf deinem Rechner:
Windows `%APPDATA%\Vyntro`, macOS `~/Library/Application Support/Trading-Signale`.

## Mac-Installation

```bash
git clone https://github.com/s3cureofficial/vyntro.git
cd vyntro
./install.sh
```

Legt **Vyntro.app** in `~/Applications` und auf dem Schreibtisch an.

## Selbst bauen (Windows)

Der Installer entsteht automatisch über GitHub Actions
([`.github/workflows/windows.yml`](.github/workflows/windows.yml)), sobald ein Tag wie
`v1.1.1` gepusht wird. Die Versionsnummer in `version.py` muss zum Tag passen; was neu ist,
steht in `NEU.md` und erscheint im Release und im Update-Fenster der App. Lokal:

```bat
pip install -r requirements.txt pyinstaller
pyinstaller --windowed --name Vyntro --icon branding\vyntro.ico ^
  --add-data "branding\vyntro-emblem.png;." --add-data "branding\vyntro-icon-1024.png;." ^
  --add-data "watchlist.txt;." --collect-all yfinance --collect-all curl_cffi --hidden-import app vyntro.py
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" windows\vyntro.iss
```

## Kommandozeile

```bash
python signale.py                  # alle Ticker aus watchlist.txt
python signale.py AAPL BTC-USD     # bestimmte Ticker
python signale.py --detail SAP.DE  # ausführliche Analyse + Backtest-Orders
```

Ticker in Yahoo-Schreibweise: `SAP.DE` (Xetra), `EUNL.DE` (ETF), `BTC-USD` (Krypto).

## Regeln

Score aus drei Indikatoren (je −1, 0 oder +1): Trend (Ø 50 vs. Ø 200 Tage), RSI (unter 30 /
über 70), MACD (über/unter Signallinie). **KAUFEN** ab +2, **VERKAUFEN** ab −2, sonst HALTEN.
