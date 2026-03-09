#!/bin/bash
#
# Set up Ollama to auto-start on Mac boot via LaunchAgent.
# Run once: bash setup_ollama_autostart.sh
#

set -e

# Find Ollama binary
OLLAMA_BIN="$(which ollama 2>/dev/null || echo '/usr/local/bin/ollama')"
if [ ! -f "$OLLAMA_BIN" ]; then
    echo "ERROR: Ollama not found. Install from https://ollama.com"
    exit 1
fi

PLIST_PATH="$HOME/Library/LaunchAgents/com.cheaphouse.ollama.plist"
mkdir -p "$HOME/Library/LaunchAgents"

# Unload if already exists
launchctl unload "$PLIST_PATH" 2>/dev/null || true

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cheaphouse.ollama</string>
    <key>ProgramArguments</key>
    <array>
        <string>${OLLAMA_BIN}</string>
        <string>serve</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/ollama.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/ollama.stderr.log</string>
</dict>
</plist>
EOF

# Load it
launchctl load "$PLIST_PATH"

echo "Ollama auto-start configured."
echo ""
echo "  Starts on boot:     yes"
echo "  Restarts on crash:  yes (KeepAlive)"
echo "  Binary:             $OLLAMA_BIN"
echo "  Logs:               /tmp/ollama.stdout.log"
echo ""
echo "Verify:   launchctl list | grep ollama"
echo "Remove:   launchctl unload $PLIST_PATH && rm $PLIST_PATH"
