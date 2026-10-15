#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/.claude/project.config.yaml"
TARGET=""
BACKUP_ID="latest"
DRY_RUN=0
YES=0

usage() {
  cat <<'EOF'
Usage:
  bash .scripts/rollback.sh --target <dev|stg|prod> [--backup-id <latest|release-id>] [--dry-run] [--yes]
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --backup-id)
      BACKUP_ID="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --yes)
      YES=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

get_config() {
  python3 "${SCRIPT_DIR}/project_config.py" "$1" --config "$CONFIG_FILE"
}

if [ -z "$TARGET" ]; then
  TARGET="$(get_config deployment.default_target)"
fi

if [ -z "$TARGET" ]; then
  echo "Rollback target is required. Set deployment.default_target or pass --target." >&2
  exit 1
fi

if [ -z "$BACKUP_ID" ]; then
  BACKUP_ID="latest"
fi

ROLLBACK_SCRIPT="$(get_config deployment.rollback_script)"
DEPLOY_METHOD="$(get_config deployment.method)"
BACKUP_DIR="$(get_config deployment.backup_dir)"

if [ -z "$ROLLBACK_SCRIPT" ]; then
  echo "deployment.rollback_script is not set in .claude/project.config.yaml" >&2
  exit 1
fi

case "$ROLLBACK_SCRIPT" in
  /*) ;;
  *) ROLLBACK_SCRIPT="${ROOT_DIR}/${ROLLBACK_SCRIPT}" ;;
esac

if [ ! -f "$ROLLBACK_SCRIPT" ]; then
  echo "Rollback script not found: $ROLLBACK_SCRIPT" >&2
  exit 1
fi

if [ "$TARGET" = "prod" ] && [ "$YES" -ne 1 ] && [ "$DRY_RUN" -ne 1 ]; then
  echo "Production rollback requires explicit confirmation. Re-run with --yes after approval." >&2
  exit 1
fi

echo "Method: ${DEPLOY_METHOD:-unset}"
echo "Target: $TARGET"
echo "Script: $ROLLBACK_SCRIPT"
echo "Backup id: $BACKUP_ID"
echo "Backup dir: ${BACKUP_DIR:-unset}"

export ROLLBACK_TARGET="$TARGET"
export ROLLBACK_BACKUP_ID="$BACKUP_ID"
export ROLLBACK_DRY_RUN="$DRY_RUN"
export ROLLBACK_BACKUP_DIR="${BACKUP_DIR:-}"
export ROLLBACK_ROOT_DIR="$ROOT_DIR"

cmd=(bash "$ROLLBACK_SCRIPT" --target "$TARGET" --backup-id "$BACKUP_ID")
if [ "$DRY_RUN" -eq 1 ]; then
  cmd+=(--dry-run)
fi

"${cmd[@]}"
