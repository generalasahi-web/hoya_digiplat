#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/.claude/project.config.yaml"
SKIP_SURVEY=0
SKIP_GIT=0

usage() {
  cat <<'EOF'
Usage:
  bash .scripts/bootstrap.sh [options]

Options:
  --config <path>   Use a different project config file
  --skip-survey     Skip survey execution
  --skip-git        Skip git/hook setup
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config)
      CONFIG_FILE="${2:-}"
      shift 2
      ;;
    --skip-survey)
      SKIP_SURVEY=1
      shift
      ;;
    --skip-git)
      SKIP_GIT=1
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

configure_git_hooks() {
  local protected_branches=""

  if [ -f ".githooks/commit-msg" ]; then
    chmod +x .githooks/commit-msg
  fi
  if [ -f ".githooks/pre-commit" ]; then
    chmod +x .githooks/pre-commit
  fi
  if [ -f ".githooks/pre-push" ]; then
    chmod +x .githooks/pre-push
  fi

  if [ -d ".githooks" ]; then
    git config core.hooksPath .githooks
  fi

  if [ -n "${DEFAULT_BRANCH:-}" ]; then
    protected_branches="$DEFAULT_BRANCH"
  fi
  if [ -n "${INTEGRATION_BRANCH:-}" ] && [ "${INTEGRATION_BRANCH}" != "${DEFAULT_BRANCH:-}" ]; then
    protected_branches="${protected_branches} ${INTEGRATION_BRANCH}"
  fi
  protected_branches="${protected_branches#"${protected_branches%%[![:space:]]*}"}"
  git config hooks.protectedBranches "$protected_branches"
}

create_integration_branch_if_missing() {
  if [ -z "${INTEGRATION_BRANCH:-}" ] || [ "${INTEGRATION_BRANCH}" = "${DEFAULT_BRANCH:-}" ]; then
    return
  fi

  if git show-ref --verify --quiet "refs/heads/${INTEGRATION_BRANCH}"; then
    return
  fi

  if [ -z "${DEFAULT_BRANCH:-}" ] || ! git show-ref --verify --quiet "refs/heads/${DEFAULT_BRANCH}"; then
    return
  fi

  git branch "${INTEGRATION_BRANCH}" "${DEFAULT_BRANCH}"
  echo "Created local integration branch: ${INTEGRATION_BRANCH}"

  if git remote get-url origin >/dev/null 2>&1 && [ "${PUSH_AFTER_INIT:-false}" = "true" ]; then
    ALLOW_PROTECTED_PUSH=1 git push -u origin "${INTEGRATION_BRANCH}"
    echo "Pushed integration branch: ${INTEGRATION_BRANCH}"
  fi
}

if [ "$SKIP_SURVEY" -eq 0 ]; then
  config_arg="$CONFIG_FILE"
  case "$CONFIG_FILE" in
    "$ROOT_DIR"/*)
      config_arg="${CONFIG_FILE#$ROOT_DIR/}"
      ;;
  esac
  python3 "${SCRIPT_DIR}/project_survey.py" --config "$config_arg"
fi

python3 "${SCRIPT_DIR}/generate_deployment_helpers.py" --config "$CONFIG_FILE"

if [ "$SKIP_GIT" -eq 1 ]; then
  echo "Skipped git setup."
  exit 0
fi

ENSURE_REMOTE_REPO="$(get_config repository.ensure_remote_repo)"
REMOTE_URL="$(get_config repository.remote_url)"
if [ -z "$REMOTE_URL" ]; then
  REMOTE_URL="$(build_remote_url)"
fi
DEFAULT_BRANCH="$(get_config repository.default_branch)"
INTEGRATION_BRANCH="$(get_config repository.integration_branch)"
CREATE_INITIAL_COMMIT="$(get_config repository.create_initial_commit)"
INITIAL_COMMIT_MESSAGE="$(get_config repository.initial_commit_message)"
PUSH_AFTER_INIT="$(get_config repository.push_after_init)"

if [ "${ENSURE_REMOTE_REPO:-false}" = "true" ]; then
  bash "${SCRIPT_DIR}/create-github-repo.sh" --config "$CONFIG_FILE"
fi

if git rev-parse --show-toplevel >/dev/null 2>&1 && [ "$(git rev-parse --show-toplevel)" = "$ROOT_DIR" ]; then
  configure_git_hooks

  if [ -n "$REMOTE_URL" ] && ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "$REMOTE_URL"
  fi

  create_integration_branch_if_missing

  echo "Existing git repository detected. Hooks were synchronized."
  exit 0
fi

cmd=(bash "${SCRIPT_DIR}/init-repo.sh" --branch "${DEFAULT_BRANCH:-main}")
if [ -n "${INTEGRATION_BRANCH:-}" ] && [ "${INTEGRATION_BRANCH}" != "${DEFAULT_BRANCH:-main}" ]; then
  cmd+=(--integration-branch "$INTEGRATION_BRANCH")
fi
if [ -n "$REMOTE_URL" ]; then
  cmd+=(--remote "$REMOTE_URL")
fi
if [ "$CREATE_INITIAL_COMMIT" = "true" ]; then
  cmd+=(--initial-commit --commit-message "$INITIAL_COMMIT_MESSAGE")
fi
if [ "$PUSH_AFTER_INIT" = "true" ]; then
  cmd+=(--push)
fi

"${cmd[@]}"
