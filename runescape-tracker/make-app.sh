#!/bin/bash
# Builds "RS Tracker.app" in your Applications folder, so you can open the
# widget from Launchpad, Spotlight or the Dock without using the terminal.
#
# Run it with:   bash make-app.sh
# Run it again if you move this folder, so the app knows where to find widget.py.

APP="$HOME/Applications/RS Tracker.app"
WIDGET="$(cd "$(dirname "$0")" && pwd)/widget.py"
PYTHON="$(command -v python3)"

# A Mac app is just a folder with a special layout.
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

# Download the Old School RuneScape icon from the OSRS Wiki and turn it into a
# Mac app icon. A copy goes in the icons folder so the widget can show it in
# the Dock too. (The icons folder isn't uploaded to GitHub.)
ICONS="$(dirname "$WIDGET")/icons"
mkdir -p "$ICONS"
curl -s -A "my-first-ghr-runescape-tracker" -o "$ICONS/app.png" \
    "https://oldschool.runescape.wiki/images/Old_School_RuneScape_Mobile_icon.png"
sips -s format icns "$ICONS/app.png" --out "$APP/Contents/Resources/AppIcon.icns" >/dev/null

# The file the Mac runs when you open the app: it starts the widget with Python.
cat > "$APP/Contents/MacOS/RS Tracker" <<EOF
#!/bin/bash
exec "$PYTHON" "$WIDGET"
EOF
chmod +x "$APP/Contents/MacOS/RS Tracker"

# Tells the Mac the app's name and which file to run.
cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>RS Tracker</string>
    <key>CFBundleExecutable</key>
    <string>RS Tracker</string>
    <key>CFBundleIdentifier</key>
    <string>com.my-first-ghr.rs-tracker</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
</dict>
</plist>
EOF

# Tell Finder and the Dock to notice the new icon.
touch "$APP"

echo "Made $APP"
echo "Open it from Launchpad or Spotlight (Command + Space, then type RS Tracker)."
