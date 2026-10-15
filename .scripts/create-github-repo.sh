#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/.claude/project.config.yaml"
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage:
  bash .scripts/create-github-repo.sh [options]

Options:
  --config <path>   Use a different project config file
  --dry-run         Print commands without executing
EOF
}

run_cmd() {
  echo "+ $*"
  if [ "$DRY_RUN" -eq 0 ]; then
    "$@"
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config)
      CONFIG_FILE="${2:-}"
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

cd "$ROOT_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Config file not found: $CONFIG_FILE" >&2
  exit 1
fi

get_config() {
  python3 "${SCRIPT_DIR}/project_config.py" "$1" --config "$CONFIG_FILE"
}

build_remote_url() {
  python3 "${SCRIPT_DIR}/repository_meta.py" remote-url --config "$CONFIG_FILE"
}

build_repo_description() {
  python3 "${SCRIPT_DIR}/repository_meta.py" repo-description --config "$CONFIG_FILE"
}

provider="$(get_config repository.provider)"
owner_name="$(get_config repository.owner_name)"
repo_name="$(get_config repository.repo_name)"
visibility="$(get_config repository.visibility)"
remote_url="$(get_config repository.remote_url)"
repo_description="$(get_config repository.description)"

if [ -z "$remote_url" ]; then
  remote_url="$(build_remote_url)"
fi
if [ -z "$repo_description" ]; then
  repo_description="$(build_repo_description)"
fi

if [ "${provider:-github}" != "github" ]; then
  echo "Only repository.provider=github is supported." >&2
  exit 1
fi

if [ -z "$owner_name" ] || [ -z "$repo_name" ]; then
  echo "repository.owner_name and repository.repo_name must be set." >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "gh command not found. Install GitHub CLI first." >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated. Run 'gh auth login' first." >&2
  exit 1
fi

repo_full_name="${owner_name}/${repo_name}"

case "${visibility:-private}" in
  private)
    visibility_flag="--private"
    ;;
  public)
    visibility_flag="--public"
    ;;
  internal)
    visibility_flag="--internal"
    ;;
  *)
    echo "Unsupported repository.visibility: ${visibility}" >&2
    exit 1
    ;;
esac

if gh repo view "$repo_full_name" >/dev/null 2>&1; then
  echo "GitHub repository already exists: ${repo_full_name}"
  if [ -n "$repo_description" ]; then
    run_cmd gh repo edit "$repo_full_name" --description "$repo_description"
  fi
else
  if [ -n "$repo_description" ]; then
    run_cmd gh repo create "$repo_full_name" "$visibility_flag" --description "$repo_description"
  else
    run_cmd gh repo create "$repo_full_name" "$visibility_flag"
  fi
fi

if git rev-parse --show-toplevel >/dev/null 2>&1 && [ "$(git rev-parse --show-toplevel)" = "$ROOT_DIR" ]; then
  if [ -n "$remote_url" ] && ! git remote get-url origin >/dev/null 2>&1; then
    run_cmd git remote add origin "$remote_url"
  fi
fi

echo "GitHub repository is ready: ${repo_full_name}"
