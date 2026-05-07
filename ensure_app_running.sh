#!/bin/zsh

APP_DIR="$(CDPATH='' cd -- "$(dirname "$0")" && pwd)"
CONFIG_LINES=("${(@f)$(python3 - "$APP_DIR" <<'PY'
import sys
from pathlib import Path

app_dir = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(app_dir))

from project_config import load_app_config

config = load_app_config(app_dir)
print(config["launchd"]["agent_label"])
print(config["launchd"]["agent_plist_path"])
print(config["paths"]["log_dir"])
PY
)}")
APP_AGENT_LABEL="${CONFIG_LINES[1]}"
APP_AGENT_PLIST="${CONFIG_LINES[2]}"
LOG_DIR="${CONFIG_LINES[3]}"
MONITOR_LOG="$LOG_DIR/monitor.log"
LAUNCHCTL_BIN="/bin/launchctl"
USER_ID="$(/usr/bin/id -u)"

mkdir -p "$LOG_DIR"

timestamp() {
  /bin/date "+%Y-%m-%d %H:%M:%S"
}

if "$LAUNCHCTL_BIN" print "gui/$USER_ID/$APP_AGENT_LABEL" 2>/dev/null | /usr/bin/grep -q "state = running"; then
  exit 0
fi

{
  echo "[$(timestamp)] app.py not running, starting via launchctl..."
} >> "$MONITOR_LOG"

if ! "$LAUNCHCTL_BIN" print "gui/$USER_ID/$APP_AGENT_LABEL" >/dev/null 2>&1; then
  "$LAUNCHCTL_BIN" bootstrap "gui/$USER_ID" "$APP_AGENT_PLIST" >> "$MONITOR_LOG" 2>&1
fi

"$LAUNCHCTL_BIN" kickstart -k "gui/$USER_ID/$APP_AGENT_LABEL" >> "$MONITOR_LOG" 2>&1
exit 0
