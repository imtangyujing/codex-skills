#!/bin/bash
# sync-all-skills.sh — 一键同步 Codex + Kimi Skills
# 以 iCloud Skills 为 master，修复 Codex 软链接 + rsync 同步 Kimi

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="$REPO_DIR/skills"

# ── 路径 ──────────────────────────────────
CODEX_SKILLS="${CODEX_HOME:-$HOME/.codex}/skills"
KIMI_SKILLS="${KIMI_SKILLS_HOME:-$HOME/Library/Application Support/kimi-desktop/daimon-share/daimon}/skills"

# ── 检查 ──────────────────────────────────
if [[ ! -d "$SKILLS_DIR" ]]; then
  echo "❌ iCloud skills 目录不存在: $SKILLS_DIR" >&2
  exit 1
fi

# ── Codex: 修复软链接 ─────────────────────
fix_codex_links() {
  local linked=0 updated=0 skipped=0 backed_up=0 pruned=0

  mkdir -p "$CODEX_SKILLS"

  for skill_path in "$SKILLS_DIR"/*; do
    [[ -d "$skill_path" ]] || continue
    [[ -f "$skill_path/SKILL.md" ]] || continue

    local skill_name target_path
    skill_name="$(basename "$skill_path")"
    target_path="$CODEX_SKILLS/$skill_name"

    if [[ -L "$target_path" ]]; then
      local current_target
      current_target="$(readlink "$target_path")"
      if [[ "$current_target" == "$skill_path" ]]; then
        ((skipped++)) || true
        continue
      fi
      rm "$target_path"
      ((updated++)) || true
    elif [[ -e "$target_path" ]]; then
      local stamp backup_path
      stamp="$(date +%Y%m%d-%H%M%S)"
      backup_path="$CODEX_SKILLS/.backup-before-codex-skills-link/$skill_name.$stamp"
      mkdir -p "$CODEX_SKILLS/.backup-before-codex-skills-link"
      mv "$target_path" "$backup_path"
      ((backed_up++)) || true
    fi

    ln -s "$skill_path" "$target_path"
    ((linked++)) || true
  done

  # 清理 dangling links
  for target_path in "$CODEX_SKILLS"/*; do
    [[ -L "$target_path" ]] || continue
    local current_target
    current_target="$(readlink "$target_path")"
    case "$current_target" in
      "$SKILLS_DIR"/*) ;;
      *) continue ;;
    esac
    if [[ ! -d "$current_target" ]]; then
      rm "$target_path"
      ((pruned++)) || true
    fi
  done

  echo "codex_linked=$linked"
  echo "codex_updated=$updated"
  echo "codex_backed_up=$backed_up"
  echo "codex_skipped=$skipped"
  echo "codex_pruned=$pruned"
}

# ── Kimi: rsync 同步 ──────────────────────
sync_kimi() {
  local synced=0 changed=0 new=0 unchanged=0

  if [[ ! -d "$KIMI_SKILLS" ]]; then
    echo "kimi_error="目录不存在: $KIMI_SKILLS""
    return 1
  fi

  for skill_path in "$SKILLS_DIR"/*; do
    [[ -d "$skill_path" ]] || continue
    [[ -f "$skill_path/SKILL.md" ]] || continue

    local skill_name src dst
    skill_name="$(basename "$skill_path")"
    src="$skill_path"
    dst="$KIMI_SKILLS/$skill_name"

    if [[ -d "$dst" ]]; then
      if diff -qr "$src" "$dst" > /dev/null 2>&1; then
        ((unchanged++)) || true
      else
        ((changed++)) || true
      fi
    else
      ((new++)) || true
    fi
    ((synced++)) || true
  done

  # 执行实际同步（只同步有变化的）
  for skill_path in "$SKILLS_DIR"/*; do
    [[ -d "$skill_path" ]] || continue
    [[ -f "$skill_path/SKILL.md" ]] || continue

    local skill_name
    skill_name="$(basename "$skill_path")"
    rsync -a --delete \
      --exclude='.DS_Store' \
      --exclude='.git' \
      --exclude='node_modules' \
      "$skill_path/" "$KIMI_SKILLS/$skill_name/" 2>/dev/null || true
  done

  echo "kimi_synced=$synced"
  echo "kimi_changed=$changed"
  echo "kimi_new=$new"
  echo "kimi_unchanged=$unchanged"
}

# ── 主流程 ────────────────────────────────
echo "=========================================="
echo "  Skills 同步: iCloud → Codex + Kimi"
echo "=========================================="
echo ""

# Codex
echo "→ 修复 Codex 软链接..."
fix_codex_links
echo ""

# Kimi
echo "→ 同步 Kimi..."
sync_kimi
echo ""

echo "✅ 全部完成。"
