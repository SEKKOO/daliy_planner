#!/bin/zsh

APP_DIR="/Users/vm0/daily_planner_web"
APP_AGENT_PLIST="/Users/vm0/Library/LaunchAgents/com.vm0.dailyplanner.app.plist"
APP_AGENT_LABEL="com.vm0.dailyplanner.app"
LOG_DIR="$APP_DIR/logs"
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
