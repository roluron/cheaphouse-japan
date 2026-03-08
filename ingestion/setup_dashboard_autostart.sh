#!/bin/bash
# Auto-start CheapHouse dashboard on Mac boot via launchd
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_PATH="$HOME/Library/LaunchAgents/com.cheaphouse.dashboard.plist"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cheaphouse.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_DIR/venv/bin/streamlit</string>
        <string>run</string>
        <string>$SCRIPT_DIR/dashboard.py</string>
        <string>--server.port</string>
        <string>8501</string>
        <string>--server.address</string>
        <string>localhost</string>
        <string>--browser.gatherUsageStats</string>
        <string>false</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/cheaphouse-dashboard.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/cheaphouse-dashboard.err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$SCRIPT_DIR/venv/bin</string>
    </dict>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH"

echo "Dashboard auto-start configured!"
echo "  URL: http://localhost:8501"
echo "  Starts on boot, restarts on crash"
echo ""
echo "Verify: open http://localhost:8501"
echo "Remove: launchctl unload $PLIST_PATH && rm $PLIST_PATH"
