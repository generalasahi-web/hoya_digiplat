#!/usr/bin/env bash
set -euo pipefail

branch="main"
integration_branch=""
remote_url=""
commit_message=""
initial_commit=0
push_after_commit=0
dry_run=0

sync_hooks() {
  local protected_branches=""

  if [ -f ".githooks/commit-msg" ]; then
    run_cmd chmod +x .githooks/commit-msg
  fi
  if [ -f ".githooks/pre-commit" ]; then
    run_cmd chmod +x .githooks/pre-commit
  fi
  if [ -f ".githooks/pre-push" ]; then
    run_cmd chmod +x .githooks/pre-push
  fi

  if [ -d ".githooks" ]; then
    run_cmd git config core.hooksPath .githooks
  fi

  if [ -n "$branch" ]; then
    protected_branches="$branch"
  fi
  if [ -n "$integration_branch" ] && [ "$integration_branch" != "$branch" ]; then
    protected_branches="${protected_branches} ${integration_branch}"
  fi
  protected_branches="${protected_branches#"${protected_branches%%[![:space:]]*}"}"
  run_cmd git config hooks.protectedBranches "$protected_branches"
}

usage() {
  cat <<'EOF'
Usage:
  bash .scripts/init-repo.sh [options]

Options:
  --remote <url>            Set remote origin URL
  --branch <name>           Branch name (default: main)
  --integration-branch <n>  Additional integration branch to create after initial commit
  --initial-commit          Create initial commit after init
  --commit-message <msg>    Commit message for --initial-commit
  --push                    Push after initial commit
  --dry-run                 Print commands without executing
EOF
}

run_cmd() {
  echo "+ $*"
  if [ "$dry_run" -eq 0 ]; then
    "$@"
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --remote)
      remote_url="${2:-}"
      shift 2
      ;;
    --branch)
      branch="${2:-}"
      shift 2
      ;;
    --integration-branch)
      integration_branch="${2:-}"
      shift 2
      ;;
    --initial-commit)
      initial_commit=1
      shift
      ;;
    --commit-message)
      commit_message="${2:-}"
      shift 2
      ;;
    --push)
      push_after_commit=1
      shift
      ;;
    --dry-run)
      dry_run=1
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

if [ -d ".git" ]; then
  echo ".git already exists in $(pwd). Nothing to initialize."
  exit 0
fi

if git rev-parse --show-toplevel >/dev/null 2>&1; then
  top="$(git rev-parse --show-toplevel)"
  if [ "$top" != "$(pwd)" ]; then
    echo "Current directory is inside another Git repository: $top" >&2
    echo "Run this script in a standalone project root." >&2
    exit 1
  fi
fi

run_cmd git init
run_cmd git branch -M "$branch"

sync_hooks

if [ -n "$remote_url" ]; then
  run_cmd git remote add origin "$remote_url"
fi

if [ "$initial_commit" -eq 1 ]; then
  if [ -z "$commit_message" ]; then
    commit_message="プロジェクトの初期ファイルを追加"
  fi
  run_cmd git add .
  run_cmd env ALLOW_PROTECTED_COMMIT=1 git commit -m "$commit_message"
  if [ -n "$integration_branch" ] && [ "$integration_branch" != "$branch" ]; then
    run_cmd git branch "$integration_branch"
  fi
fi

if [ "$push_after_commit" -eq 1 ]; then
  if [ -z "$remote_url" ]; then
    echo "--push requires --remote" >&2
    exit 1
  fi
  if [ "$initial_commit" -eq 0 ]; then
    echo "--push requires --initial-commit" >&2
    exit 1
  fi
  run_cmd env ALLOW_PROTECTED_PUSH=1 git push -u origin "$branch"
  if [ -n "$integration_branch" ] && [ "$integration_branch" != "$branch" ]; then
    run_cmd env ALLOW_PROTECTED_PUSH=1 git push -u origin "$integration_branch"
  fi
fi

if [ "$initial_commit" -eq 1 ] && [ -n "$integration_branch" ] && [ "$integration_branch" != "$branch" ]; then
  run_cmd git switch "$integration_branch"
fi

echo
echo "Git initialization finished."
if [ -f ".githooks/commit-msg" ]; then
  echo "commit-msg hook is enabled via .githooks/commit-msg"
fi
if [ -f ".githooks/pre-commit" ]; then
  echo "pre-commit hook is enabled via .githooks/pre-commit"
fi
if [ -f ".githooks/pre-push" ]; then
  echo "pre-push hook is enabled via .githooks/pre-push"
fi
if [ -n "$integration_branch" ] && [ "$integration_branch" != "$branch" ]; then
  if [ "$initial_commit" -eq 1 ]; then
    echo "integration branch prepared: ${integration_branch}"
    echo "current branch: ${integration_branch}"
  else
    echo "integration branch was not created yet. Create ${integration_branch} after the first commit."
  fi
fi
