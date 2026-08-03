#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$repo_dir/skills"
target_dir="${CODEX_HOME:-$HOME/.codex}/skills"

"$repo_dir/install.sh"

for target_path in "$target_dir"/*; do
  [[ -L "$target_path" ]] || continue
  link_target="$(readlink "$target_path")"

  case "$link_target" in
    "$source_dir"/*)
      if [[ ! -e "$link_target" ]]; then
        rm "$target_path"
        echo "Removed stale symlink: $(basename "$target_path") -> $link_target"
      fi
      ;;
  esac
done

echo "Codex skill links reconciled."
