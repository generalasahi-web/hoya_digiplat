#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/.claude/project.config.yaml"
TARGET=""
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage:
  bash .scripts/sync-from-server.sh --target <dev|stg|prod> [--dry-run]
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
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

load_local_env() {
  if [ -f "${ROOT_DIR}/.env.local" ]; then
    set -a
    # shellcheck disable=SC1091
    . "${ROOT_DIR}/.env.local"
    set +a
  fi
}

if [ -z "$TARGET" ]; then
  TARGET="$(get_config deployment.default_target)"
fi

if [ -z "$TARGET" ]; then
  echo "Sync target is required. Set deployment.default_target or pass --target." >&2
  exit 1
fi

SYNC_SCRIPT="$(get_config deployment.sync_script)"
DEPLOY_METHOD="$(get_config deployment.method)"

load_local_env

if [ -z "$SYNC_SCRIPT" ]; then
  echo "deployment.sync_script is not set in .claude/project.config.yaml" >&2
  exit 1
fi

case "$SYNC_SCRIPT" in
  /*) ;;
  *) SYNC_SCRIPT="${ROOT_DIR}/${SYNC_SCRIPT}" ;;
esac

if [ ! -f "$SYNC_SCRIPT" ]; then
  echo "Sync script not found: $SYNC_SCRIPT" >&2
  exit 1
fi

echo "Method: ${DEPLOY_METHOD:-unset}"
echo "Target: $TARGET"
echo "Script: $SYNC_SCRIPT"

cmd=(bash "$SYNC_SCRIPT" --target "$TARGET")
if [ "$DRY_RUN" -eq 1 ]; then
  cmd+=(--dry-run)
fi

"${cmd[@]}"
