#!/usr/bin/env bash
set -euo pipefail

branch=""
remote="origin"
fetch=0

usage() {
  cat <<'EOF'
Usage:
  bash .scripts/check-branch-sync.sh [options]

Options:
  --branch <name>   Branch to inspect (default: current branch)
  --remote <name>   Remote name (default: origin)
  --fetch           Fetch remote refs before checking
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --branch)
      branch="${2:-}"
      shift 2
      ;;
    --remote)
      remote="${2:-origin}"
      shift 2
      ;;
    --fetch)
      fetch=1
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

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "[ERROR] Git リポジトリではありません。" >&2
  exit 1
fi

if [ -z "$branch" ]; then
  branch="$(git branch --show-current 2>/dev/null || true)"
fi

if [ -z "$branch" ]; then
  echo "[ERROR] 対象ブランチを特定できません。" >&2
  exit 1
fi

if ! git show-ref --verify --quiet "refs/heads/${branch}"; then
  echo "[ERROR] ローカルブランチが見つかりません: ${branch}" >&2
  exit 1
fi

if [ "$fetch" -eq 1 ] && git remote get-url "$remote" >/dev/null 2>&1; then
  git fetch "$remote" --prune >/dev/null 2>&1 || {
    echo "[WARN] ${remote} の fetch に失敗しました。手元の remote 情報で判定します。"
  }
fi

upstream="$(git for-each-ref --format='%(upstream:short)' "refs/heads/${branch}")"
if [ -z "$upstream" ] && git show-ref --verify --quiet "refs/remotes/${remote}/${branch}"; then
  upstream="${remote}/${branch}"
fi

if [ -z "$upstream" ]; then
  echo "[WARN] ${branch} の upstream が未設定です。"
  exit 0
fi

counts="$(git rev-list --left-right --count "${branch}...${upstream}")"
ahead="$(printf '%s\n' "$counts" | awk '{print $1}')"
behind="$(printf '%s\n' "$counts" | awk '{print $2}')"

if [ "${behind}" -gt 0 ] && [ "${ahead}" -gt 0 ]; then
  echo "[WARN] ${branch} は ${upstream} と分岐しています（ahead ${ahead} / behind ${behind}）。先に pull / rebase 方針を整理してください。"
  exit 2
fi

if [ "${behind}" -gt 0 ]; then
  echo "[WARN] ${branch} は ${upstream} より ${behind} commit 遅れています。先に pull してください。"
  exit 2
fi

if [ "${ahead}" -gt 0 ]; then
  echo "[OK] ${branch} は ${upstream} より ${ahead} commit 進んでいます。"
  exit 0
fi

echo "[OK] ${branch} は ${upstream} と同期しています。"
exit 0
