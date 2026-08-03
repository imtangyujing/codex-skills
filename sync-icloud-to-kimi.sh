#!/bin/bash
#
# sync-icloud-to-kimi.sh
# 单向同步：iCloud Skills → Kimi Skills
# 以 iCloud 为 master，覆盖 Kimi 中同名的 skill
# Kimi 独有的内置 managed skills 不受影响
#

set -euo pipefail

# ── 路径配置 ──────────────────────────────
ICLOUD_SKILLS="${ICLOUD_SKILLS:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Skills/skills}"
KIMI_SKILLS="${KIMI_SKILLS:-$HOME/Library/Application Support/kimi-desktop/daimon-share/daimon/skills}"
LOG_DIR="${LOG_DIR:-$HOME/Documents/kimi/workspace}"
LOG_FILE="$LOG_DIR/sync-icloud-to-kimi.log"

# ── 参数解析 ──────────────────────────────
DRY_RUN=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run|-n)
      DRY_RUN=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      cat << 'EOF'
用法: ./sync-icloud-to-kimi.sh [选项]

选项:
  --dry-run, -n    预览变更，不实际执行
  --verbose, -v    显示详细 rsync 输出
  --help, -h       显示帮助

环境变量:
  ICLOUD_SKILLS    iCloud skills 目录路径
  KIMI_SKILLS      Kimi skills 目录路径
  LOG_DIR          日志目录

说明:
  以 iCloud 为 master，单向同步到 Kimi。
  只同步 iCloud 中存在的 skill，Kimi 独有的内置 skill 不受影响。
  运行前请确认没有 Agent 正在修改 skill 文件。
EOF
      exit 0
      ;;
    *)
      echo "未知选项: $1" >&2
      echo "用 --help 查看用法" >&2
      exit 1
      ;;
  esac
done

# ── 前置检查 ──────────────────────────────
if [[ ! -d "$ICLOUD_SKILLS" ]]; then
  echo "❌ iCloud skills 目录不存在: $ICLOUD_SKILLS" >&2
  exit 1
fi

if [[ ! -d "$KIMI_SKILLS" ]]; then
  echo "❌ Kimi skills 目录不存在: $KIMI_SKILLS" >&2
  exit 1
fi

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# ── 标题 ──────────────────────────────────
echo "=========================================="
echo "  iCloud → Kimi Skills 同步"
echo "=========================================="
echo ""
echo "源 (iCloud):  $ICLOUD_SKILLS"
echo "目标 (Kimi):  $KIMI_SKILLS"
echo "模式:         $(if $DRY_RUN; then echo '预览 (--dry-run)'; else echo '实际执行'; fi)"
echo ""

# ── 安全检查 ──────────────────────────────
echo "⚠️  安全检查: 请确认当前没有 Agent 正在修改 skill 文件"
echo "   （如果有 Agent 在跑，等它结束再执行此脚本）"
echo ""

if ! $DRY_RUN; then
  read -r -p "确认继续? (y/N) " CONFIRM
  if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "已取消"
    exit 0
  fi
fi

# ── 统计 ──────────────────────────────────
ICLOUD_COUNT=$(find "$ICLOUD_SKILLS" -maxdepth 1 -mindepth 1 -type d | wc -l | tr -d ' ')
KIMI_COUNT=$(find "$KIMI_SKILLS" -maxdepth 1 -mindepth 1 -type d | grep -v '^\.' | wc -l | tr -d ' ')

echo "iCloud 中的 skills: $ICLOUD_COUNT 个"
echo "Kimi 中的 skills:   $KIMI_COUNT 个"
echo ""

# ── 构建同步列表 ──────────────────────────
# 找出两边都有的 + iCloud 独有的
SKILLS_TO_SYNC=()
while IFS= read -r -d '' SKILL_DIR; do
  SKILL_NAME=$(basename "$SKILL_DIR")
  # 跳过隐藏文件
  [[ "$SKILL_NAME" == .* ]] && continue
  SKILLS_TO_SYNC+=("$SKILL_NAME")
done < <(find "$ICLOUD_SKILLS" -maxdepth 1 -mindepth 1 -type d -print0 | sort -z)

# ── 预览变更 ──────────────────────────────
echo "将要同步的 skills (${#SKILLS_TO_SYNC[@]} 个):"
echo ""

SYNCED=0
CHANGED=0
NEW=0

for SKILL_NAME in "${SKILLS_TO_SYNC[@]}"; do
  SRC="$ICLOUD_SKILLS/$SKILL_NAME"
  DST="$KIMI_SKILLS/$SKILL_NAME"

  if [[ -d "$DST" ]]; then
    # 已存在，检查是否有差异
    DIFF=$(diff -qr "$SRC" "$DST" 2>/dev/null || true)
    if [[ -n "$DIFF" ]]; then
      echo "  🔄  $SKILL_NAME  (有变更)"
      ((CHANGED++)) || true
    else
      echo "  ✅  $SKILL_NAME  (无变化)"
    fi
  else
    echo "  ➕  $SKILL_NAME  (新增)"
    ((NEW++)) || true
  fi
  ((SYNCED++)) || true
done

echo ""
echo "摘要: $CHANGED 个有变更, $NEW 个新增, $(($SYNCED - $CHANGED - $NEW)) 个无变化"
echo ""

# ── 执行同步 ──────────────────────────────
RSYNC_OPTS="-a --delete"
if $VERBOSE; then
  RSYNC_OPTS="$RSYNC_OPTS -v"
else
  RSYNC_OPTS="$RSYNC_OPTS --stats"
fi
if $DRY_RUN; then
  RSYNC_OPTS="$RSYNC_OPTS --dry-run"
fi

# 排除项
EXCLUDES=(
  --exclude='.DS_Store'
  --exclude='.git'
  --exclude='node_modules'
  --exclude='__pycache__'
)

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] 开始同步" >> "$LOG_FILE"

for SKILL_NAME in "${SKILLS_TO_SYNC[@]}"; do
  SRC="$ICLOUD_SKILLS/$SKILL_NAME"
  DST="$KIMI_SKILLS/$SKILL_NAME"

  echo "→ 同步: $SKILL_NAME"

  # 确保目标父目录存在
  mkdir -p "$KIMI_SKILLS"

  # rsync 同步（带尾部斜杠表示同步目录内容）
  rsync $RSYNC_OPTS "${EXCLUDES[@]}" "$SRC/" "$DST/" 2>&1 | tee -a "$LOG_FILE" || {
    echo "❌ 同步失败: $SKILL_NAME" >&2
    echo "[$TIMESTAMP] 失败: $SKILL_NAME" >> "$LOG_FILE"
    continue
  }

  echo "[$TIMESTAMP] 成功: $SKILL_NAME" >> "$LOG_FILE"
done

# ── 完成 ──────────────────────────────────
echo ""
if $DRY_RUN; then
  echo "✅ 预览完成。实际文件未被修改。"
  echo "   去掉 --dry-run 参数执行真正的同步。"
else
  echo "✅ 同步完成。Kimi 的 watcher 会自动重新加载变更的 skills。"
fi

echo ""
echo "日志: $LOG_FILE"
