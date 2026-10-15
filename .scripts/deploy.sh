#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/.claude/project.config.yaml"
TARGET=""
DRY_RUN=0
YES=0

usage() {
  cat <<'EOF'
Usage:
  bash .scripts/deploy.sh --target <dev|stg|prod> [--dry-run] [--yes]
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
  echo "Deployment target is required. Set deployment.default_target or pass --target." >&2
  exit 1
fi

DEPLOY_SCRIPT="$(get_config deployment.deploy_script)"
DEPLOY_METHOD="$(get_config deployment.method)"
BACKUP_BEFORE_DEPLOY="$(get_config deployment.backup_before_deploy)"
BACKUP_DIR="$(get_config deployment.backup_dir)"
BACKUP_RETENTION="$(get_config deployment.backup_retention)"
RELEASE_ID="$(date '+%Y%m%d-%H%M%S')"

load_local_env

if [ -z "$DEPLOY_SCRIPT" ]; then
  echo "deployment.deploy_script is not set in .claude/project.config.yaml" >&2
  exit 1
fi

if [ "${BACKUP_BEFORE_DEPLOY:-true}" = "true" ] && [ -z "$BACKUP_DIR" ]; then
  echo "deployment.backup_dir is not set in .claude/project.config.yaml" >&2
  exit 1
fi

case "$DEPLOY_SCRIPT" in
  /*) ;;
  *) DEPLOY_SCRIPT="${ROOT_DIR}/${DEPLOY_SCRIPT}" ;;
esac

if [ ! -f "$DEPLOY_SCRIPT" ]; then
  echo "Deploy script not found: $DEPLOY_SCRIPT" >&2
  exit 1
fi

if [ "$TARGET" = "prod" ] && [ "$YES" -ne 1 ] && [ "$DRY_RUN" -ne 1 ]; then
  echo "Production deploy requires explicit confirmation. Re-run with --yes after approval." >&2
  exit 1
fi

echo "Method: ${DEPLOY_METHOD:-unset}"
echo "Target: $TARGET"
echo "Script: $DEPLOY_SCRIPT"
echo "Backup before deploy: ${BACKUP_BEFORE_DEPLOY:-true}"
echo "Backup dir: ${BACKUP_DIR:-unset}"
echo "Backup retention: ${BACKUP_RETENTION:-unset}"
echo "Release id: $RELEASE_ID"

export DEPLOY_TARGET="$TARGET"
export DEPLOY_DRY_RUN="$DRY_RUN"
export DEPLOY_RELEASE_ID="$RELEASE_ID"
export DEPLOY_BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"
export DEPLOY_BACKUP_DIR="${BACKUP_DIR:-}"
export DEPLOY_BACKUP_RETENTION="${BACKUP_RETENTION:-}"
export DEPLOY_ROOT_DIR="$ROOT_DIR"

cmd=(bash "$DEPLOY_SCRIPT" --target "$TARGET")
if [ "$DRY_RUN" -eq 1 ]; then
  cmd+=(--dry-run)
fi

"${cmd[@]}"
