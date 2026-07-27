#!/usr/bin/env bash
# Link every folder in skills/ into Kimi Work's local skills directory.
# Mirrors install.sh (which targets ~/.codex/skills), but for Kimi.
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$repo_dir/skills"
target_dir="${KIMI_SKILLS_HOME:-$HOME/Library/Application Support/kimi-desktop/daimon-share/daimon}/skills"
backup_dir="$target_dir/.backup-before-kimi-skills-link"

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

# Prune dangling links that point into this repo's skills/ but whose source
# folder no longer exists (i.e. the skill was deleted from the repo).
# Only links pointing into $source_dir are touched; Kimi-managed and other
# third-party skills are never removed.
for target_path in "$target_dir"/*; do
  [[ -L "$target_path" ]] || continue

  current_target="$(readlink "$target_path")"
  case "$current_target" in
    "$source_dir"/*) ;;
    *) continue ;;
  esac

  if [[ ! -d "$current_target" ]]; then
    skill_name="$(basename "$target_path")"
    rm "$target_path"
    echo "Removed: $skill_name (source folder deleted)"
  fi
done

echo "Done. Restart Kimi if the new or updated skills do not appear immediately."
