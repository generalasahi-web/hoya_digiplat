#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
EXAMPLE_FILE="${ROOT_DIR}/.env.local.example"
TARGET_FILE="${ROOT_DIR}/.env.local"
FORCE=0

usage() {
  cat <<'EOF'
Usage:
  bash .scripts/init-local-env.sh [--force]

Options:
  --force   Overwrite existing .env.local
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --force)
      FORCE=1
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

if [ ! -f "$EXAMPLE_FILE" ]; then
  echo ".env.local.example not found: $EXAMPLE_FILE" >&2
  exit 1
fi

if [ -f "$TARGET_FILE" ] && [ "$FORCE" -ne 1 ]; then
  echo ".env.local already exists: $TARGET_FILE"
  echo "Use --force to overwrite."
  exit 0
fi

cp "$EXAMPLE_FILE" "$TARGET_FILE"
echo "Created: $TARGET_FILE"
