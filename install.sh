#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$repo_dir/skills"
target_dir="${CODEX_HOME:-$HOME/.codex}/skills"
backup_dir="$target_dir/.backup-before-codex-skills-link"

if [[ ! -d "$source_dir" ]]; then
  echo "Missing skills directory: $source_dir" >&2
  exit 1
fi

mkdir -p "$target_dir" "$backup_dir"

for skill_path in "$source_dir"/*; do
  [[ -d "$skill_path" ]] || continue

  skill_name="$(basename "$skill_path")"
  target_path="$target_dir/$skill_name"

  if [[ -L "$target_path" ]]; then
    current_target="$(readlink "$target_path")"
    if [[ "$current_target" == "$skill_path" ]]; then
      echo "Already linked: $skill_name"
      continue
    fi
    rm "$target_path"
  elif [[ -e "$target_path" ]]; then
    stamp="$(date +%Y%m%d-%H%M%S)"
    backup_path="$backup_dir/$skill_name.$stamp"
    mv "$target_path" "$backup_path"
    echo "Backed up existing $skill_name to $backup_path"
  fi

  ln -s "$skill_path" "$target_path"
  echo "Linked: $skill_name"
done

echo "Done. Restart Codex if the new or updated skills do not appear immediately."

