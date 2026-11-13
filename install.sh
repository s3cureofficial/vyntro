#!/bin/bash
# Installiert/aktualisiert die Mac-App "Vyntro" in ~/Applications und auf dem Schreibtisch.
# Die App läuft aus ~/Library/Application Support/Trading-Signale (dort liegen auch deine
# Watchlist und die Logos), weil macOS per Doppelklick gestarteten Apps den Zugriff auf
# ~/Documents verwehrt.
set -euo pipefail

QUELLE="$(cd "$(dirname "$0")" && pwd)"
ZIEL="$HOME/Library/Application Support/Trading-Signale"
APP="$HOME/Applications/Vyntro.app"

mkdir -p "$ZIEL"
cp "$QUELLE/app.py" "$QUELLE/signale.py" "$QUELLE/begruendung.py" "$QUELLE/prognose.py" \
   "$QUELLE/nachrichten.py" "$QUELLE/logos.py" "$QUELLE/konto.py" "$QUELLE/pfade.py" "$QUELLE/tr_import.py" "$QUELLE/update.py" "$QUELLE/version.py" "$QUELLE/requirements.txt" "$QUELLE/branding/vyntro-emblem.png" \
   "$QUELLE/branding/vyntro-icon-1024.png" "$ZIEL/"
# Watchlist nur beim ersten Mal kopieren, danach gehört sie der App
[ -f "$ZIEL/watchlist.txt" ] || cp "$QUELLE/watchlist.txt" "$ZIEL/"

if [ ! -x "$ZIEL/.venv/bin/python" ]; then
  echo "Richte Python-Umgebung ein (einmalig, dauert etwas) …"
  /usr/bin/python3 -m venv "$ZIEL/.venv"
  "$ZIEL/.venv/bin/pip" install -q --upgrade pip
  "$ZIEL/.venv/bin/pip" install -q pandas yfinance tabulate PySide6 matplotlib
fi

# alte Starter unter dem früheren Namen entfernen (enthalten nur das Startskript)
rm -rf "$HOME/Applications/Trading-Signale.app" "$HOME/Desktop/Trading-Signale.app" \
       "$HOME/Applications/Aurum.app" "$HOME/Desktop/Aurum.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$QUELLE/branding/Vyntro.icns" "$APP/Contents/Resources/Vyntro.icns"
cat > "$APP/Contents/MacOS/Vyntro" <<'EOF'
#!/bin/bash
DIR="$HOME/Library/Application Support/Trading-Signale"
cd "$DIR" || exit 1
exec "$DIR/.venv/bin/python" "$DIR/app.py" "$@" >"$DIR/app.log" 2>&1
EOF
chmod +x "$APP/Contents/MacOS/Vyntro"
cat > "$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Vyntro</string>
  <key>CFBundleDisplayName</key><string>Vyntro</string>
  <key>CFBundleIdentifier</key><string>local.vyntro</string>
  <key>CFBundleExecutable</key><string>Vyntro</string>
  <key>CFBundleIconFile</key><string>Vyntro</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>LSMinimumSystemVersion</key><string>12.0</string>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
EOF

# Kopie auf den Schreibtisch zum Doppelklicken
rm -rf "$HOME/Desktop/Vyntro.app"
cp -R "$APP" "$HOME/Desktop/"
# Finder/Dock das neue Icon zeigen lassen
touch "$APP" "$HOME/Desktop/Vyntro.app"

echo "Fertig: $APP und ~/Desktop/Vyntro.app"
