#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source_dir="$repo_dir/skills"
target_dir="${CODEX_HOME:-$HOME/.codex}/skills"
backup_dir="$target_dir/.backup-before-codex-skills-link"
validator="${CODEX_SKILL_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"
commit_message="Update skills"
prune_extra_local=false
skip_push=false

usage() {
  cat <<'USAGE'
Usage:
  ./sync.sh [--message "Commit message"] [--prune-extra-local] [--no-push]

What it does:
  1. Cleans local junk files under skills/.
  2. Fast-forwards from origin when the working tree is clean.
  3. Validates every skill with quick_validate.py.
  4. Links repo skills into ~/.codex/skills via install.sh.
  5. Removes stale symlinks that point into this repo.
  6. Optionally backs up extra local skills not present in the repo.
  7. Commits changed skills and pushes main.

Options:
  --message, -m        Commit message. Default: "Update skills".
  --prune-extra-local  Back up local ~/.codex/skills entries missing from repo.
  --no-push            Commit locally but do not push.
  --help, -h           Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --message|-m)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      commit_message="$2"
      shift 2
      ;;
    --prune-extra-local)
      prune_extra_local=true
      shift
      ;;
    --no-push)
      skip_push=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

cd "$repo_dir"

if [[ ! -d "$source_dir" ]]; then
  echo "Missing skills directory: $source_dir" >&2
  exit 1
fi

if [[ ! -x "$validator" && ! -f "$validator" ]]; then
  echo "Missing validator: $validator" >&2
  echo "Set CODEX_SKILL_VALIDATOR=/path/to/quick_validate.py if needed." >&2
  exit 1
fi

echo "== Repo =="
echo "$repo_dir"

echo "== Clean junk files =="
find "$source_dir" -type f \( \
  -name '.DS_Store' -o \
  -name '*.zip' -o \
  -name '*.swp' -o \
  -name '*.pyc' \
\) -print -delete

echo "== Git status before sync =="
git status --short --branch

if [[ -z "$(git status --porcelain)" ]]; then
  echo "== Pull origin =="
  git pull --ff-only
else
  echo "Working tree has local changes; skipping pull before commit."
fi

echo "== Validate skills =="
for skill_path in "$source_dir"/*; do
  [[ -f "$skill_path/SKILL.md" ]] || continue
  skill_name="$(basename "$skill_path")"
  python3 "$validator" "$skill_path" >/tmp/codex-skill-validate-"$skill_name".out 2>&1 || {
    echo "Validation failed: $skill_name" >&2
    cat /tmp/codex-skill-validate-"$skill_name".out >&2
    exit 1
  }
done
echo "All skills validated."

echo "== Install links =="
"$repo_dir/install.sh"

mkdir -p "$backup_dir"

echo "== Prune stale repo symlinks =="
for local_path in "$target_dir"/*; do
  [[ -L "$local_path" ]] || continue
  skill_name="$(basename "$local_path")"
  link_target="$(readlink "$local_path")"
  case "$link_target" in
    "$source_dir"/*)
      if [[ ! -e "$link_target" || ! -f "$source_dir/$skill_name/SKILL.md" ]]; then
        rm "$local_path"
        echo "Removed stale symlink: $skill_name -> $link_target"
      fi
      ;;
  esac
done

repo_list="$(mktemp)"
local_list="$(mktemp)"
trap 'rm -f "$repo_list" "$local_list"' EXIT

find "$source_dir" -mindepth 1 -maxdepth 1 -type d -exec sh -c '
  for d; do
    [ -f "$d/SKILL.md" ] && printf "%s\n" "${d##*/}"
  done
' sh {} + | sort > "$repo_list"

find "$target_dir" -maxdepth 1 \( -type d -o -type l \) -exec sh -c '
  for d; do
    [ -f "$d/SKILL.md" ] && printf "%s\n" "${d##*/}"
  done
' sh {} + | sort > "$local_list"

extra_local="$(comm -13 "$repo_list" "$local_list" || true)"
missing_local="$(comm -23 "$repo_list" "$local_list" || true)"

if [[ -n "$extra_local" ]]; then
  echo "Extra local skills not in repo:"
  echo "$extra_local"
  if [[ "$prune_extra_local" == true ]]; then
    while IFS= read -r skill_name; do
      [[ -n "$skill_name" ]] || continue
      local_path="$target_dir/$skill_name"
      [[ -e "$local_path" || -L "$local_path" ]] || continue
      if [[ -L "$local_path" ]]; then
        rm "$local_path"
        echo "Removed extra local symlink: $skill_name"
      else
        stamp="$(date +%Y%m%d-%H%M%S)"
        backup_path="$backup_dir/$skill_name.$stamp"
        mv "$local_path" "$backup_path"
        echo "Backed up extra local skill: $skill_name -> $backup_path"
      fi
    done <<< "$extra_local"
    find "$target_dir" -maxdepth 1 \( -type d -o -type l \) -exec sh -c '
      for d; do
        [ -f "$d/SKILL.md" ] && printf "%s\n" "${d##*/}"
      done
    ' sh {} + | sort > "$local_list"
    missing_local="$(comm -23 "$repo_list" "$local_list" || true)"
  else
    echo "Use --prune-extra-local to back them up/remove them."
  fi
fi

if [[ -n "$missing_local" ]]; then
  echo "Missing local skills after install:" >&2
  echo "$missing_local" >&2
  exit 1
fi

echo "Repo skills:  $(wc -l < "$repo_list" | tr -d ' ')"
echo "Local skills: $(wc -l < "$local_list" | tr -d ' ')"

echo "== Git commit =="
git add -A skills install.sh sync.sh README.md
if [[ -z "$(git diff --cached --name-only)" ]]; then
  echo "No Git changes to commit."
else
  git diff --cached --stat
  git commit -m "$commit_message"
fi

if [[ "$skip_push" == true ]]; then
  echo "Skipping push because --no-push was set."
else
  echo "== Push =="
  git push origin "$(git branch --show-current)"
fi

echo "== Final status =="
git status --short --branch
echo "Done."
