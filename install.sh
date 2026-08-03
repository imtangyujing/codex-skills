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

linked=0
updated=0
skipped=0
backed_up=0
pruned=0

for skill_path in "$source_dir"/*; do
  [[ -d "$skill_path" ]] || continue
  [[ -f "$skill_path/SKILL.md" ]] || continue

  skill_name="$(basename "$skill_path")"
  target_path="$target_dir/$skill_name"

  if [[ -L "$target_path" ]]; then
    current_target="$(readlink "$target_path")"
    if [[ "$current_target" == "$skill_path" ]]; then
      ((skipped++)) || true
      continue
    fi
    rm "$target_path"
    ((updated++)) || true
  elif [[ -e "$target_path" ]]; then
    stamp="$(date +%Y%m%d-%H%M%S)"
    backup_path="$backup_dir/$skill_name.$stamp"
    mv "$target_path" "$backup_path"
    ((backed_up++)) || true
  fi

  ln -s "$skill_path" "$target_path"
  ((linked++)) || true
done

# Prune dangling symlinks that point into this repo's skills/ but whose source
# folder no longer exists (i.e. the skill was deleted from the repo).
# Only links pointing into $source_dir are touched; Codex-managed and other
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
    ((pruned++)) || true
  fi
done

echo ""
echo "== 摘要 =="
echo "  新增链接: $linked"
echo "  更新链接: $updated"
echo "  备份现有: $backed_up"
echo "  已存在跳过: $skipped"
echo "  清理失效: $pruned"
echo ""
echo "Done. Restart Codex if the new or updated skills do not appear immediately."
