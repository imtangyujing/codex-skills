#!/usr/bin/env bash
# Wrapper for launchd: runs install-kimi.sh, and sends a macOS system
# notification only when something actually changed (linked / removed /
# backed up). Silent otherwise.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
log_dir="$HOME/Library/Logs/kimi-skills-sync"
mkdir -p "$log_dir"

output="$("$repo_dir/install-kimi.sh" 2>&1)" || {
  osascript -e 'display notification "install-kimi.sh 执行失败，请查看日志" with title "Kimi Skills 同步" subtitle "出错" sound name "Basso"'
  printf '%s\n%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$output" >> "$log_dir/sync.log"
  exit 1
}

changes="$(printf '%s\n' "$output" | grep -E '^(Linked|Removed|Backed up)' || true)"

printf '%s\n%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$output" >> "$log_dir/sync.log"

if [[ -n "$changes" ]]; then
  count="$(printf '%s\n' "$changes" | wc -l | tr -d ' ')"
  detail="$(printf '%s\n' "$changes" | head -3 | sed 's/ to .*$//' | paste -sd '；' -)"
  osascript - "$count" "$detail" <<'EOF'
on run argv
  set n to item 1 of argv
  set d to item 2 of argv
  display notification d with title "Kimi Skills 同步" subtitle (n & " 项变动") sound name "Glass"
end run
EOF
fi
