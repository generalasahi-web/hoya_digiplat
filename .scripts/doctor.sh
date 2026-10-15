#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/.claude/project.config.yaml"
STRICT=0

OK_COUNT=0
WARN_COUNT=0
ERROR_COUNT=0

usage() {
  cat <<'EOF'
Usage:
  bash .scripts/doctor.sh [--config <path>] [--strict]

Options:
  --config <path>   Use a different project config file
  --strict          Exit with status 1 when warnings exist
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --config)
      CONFIG_FILE="${2:-}"
      shift 2
      ;;
    --strict)
      STRICT=1
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

rel_path() {
  local path="$1"
  case "$path" in
    "$ROOT_DIR"/*) printf '%s\n' "${path#$ROOT_DIR/}" ;;
    *) printf '%s\n' "$path" ;;
  esac
}

resolve_path() {
  local raw="$1"
  case "$raw" in
    /*) printf '%s\n' "$raw" ;;
    *) printf '%s\n' "${ROOT_DIR}/${raw}" ;;
  esac
}

ok() {
  printf '[OK] %s\n' "$1"
  OK_COUNT=$((OK_COUNT + 1))
}

warn() {
  printf '[WARN] %s\n' "$1"
  WARN_COUNT=$((WARN_COUNT + 1))
}

error() {
  printf '[ERROR] %s\n' "$1"
  ERROR_COUNT=$((ERROR_COUNT + 1))
}

section() {
  printf '\n## %s\n' "$1"
}

is_placeholder() {
  case "$1" in
    ""|"案件名"|"クライアント名"|"要入力"|"任意")
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

get_config() {
  if [ ! -f "$CONFIG_FILE" ]; then
    return 0
  fi
  python3 "${SCRIPT_DIR}/project_config.py" "$1" --config "$CONFIG_FILE" 2>/dev/null || true
}

build_repo_name() {
  python3 "${SCRIPT_DIR}/repository_meta.py" repo-name --config "$CONFIG_FILE" 2>/dev/null || true
}

build_remote_url() {
  python3 "${SCRIPT_DIR}/repository_meta.py" remote-url --config "$CONFIG_FILE" 2>/dev/null || true
}

build_repo_description() {
  python3 "${SCRIPT_DIR}/repository_meta.py" repo-description --config "$CONFIG_FILE" 2>/dev/null || true
}

check_config_field() {
  local key="$1"
  local label="$2"
  local value
  value="$(get_config "$key")"
  if is_placeholder "$value"; then
    warn "${label}: 未設定"
  else
    ok "${label}: ${value}"
  fi
}

check_script_field() {
  local key="$1"
  local label="$2"
  local raw
  raw="$(get_config "$key")"
  if is_placeholder "$raw"; then
    warn "${label}: 未設定"
    return
  fi

  local resolved
  resolved="$(resolve_path "$raw")"
  if [ -f "$resolved" ]; then
    if grep -q "\[SETUP REQUIRED\]" "$resolved" 2>/dev/null; then
      warn "${label}: $(rel_path "$resolved") （未生成です。deployment.method を設定して bootstrap.sh を再実行してください）"
    else
      ok "${label}: $(rel_path "$resolved")"
    fi
  else
    error "${label}: $(rel_path "$resolved") が見つかりません"
  fi
}

check_command() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    ok "コマンド ${name}: 利用可能"
  else
    case "$name" in
      rg)
        warn "コマンド rg: 見つかりません（ripgrep。macOS は brew install ripgrep）"
        ;;
      *)
        warn "コマンド ${name}: 見つかりません"
        ;;
    esac
  fi
}

cd "$ROOT_DIR"

section "Files"
for path in "CLAUDE.md" "AGENTS.md" "MEMORY.md" "README.md" "doc/project-setup.md"; do
  if [ -f "$ROOT_DIR/$path" ]; then
    ok "ファイル: $path"
  else
    warn "ファイル: $path がありません"
  fi
done

if [ -f "$ROOT_DIR/.env.local.example" ]; then
  ok "ファイル: .env.local.example"
else
  warn "ファイル: .env.local.example がありません"
fi

if [ -f "$CONFIG_FILE" ]; then
  ok "設定ファイル: $(rel_path "$CONFIG_FILE")"
else
  error "設定ファイルがありません: $(rel_path "$CONFIG_FILE")"
fi

section "Config"
check_config_field "project.name" "案件名"
check_config_field "project.slug" "案件スラッグ"
check_config_field "project.client" "クライアント"
check_config_field "project.client_slug" "クライアントスラッグ"
check_config_field "project.type" "案件種別"
check_config_field "environment.prod_url" "PROD URL"
check_config_field "environment.stg_url" "STG URL"

local_url="$(get_config environment.local_url)"
if is_placeholder "$local_url"; then
  warn "Local URL: 未設定"
else
  ok "Local URL: ${local_url}"
fi

check_config_field "deployment.method" "配備方法"
default_target="$(get_config deployment.default_target)"
if is_placeholder "$default_target"; then
  warn "既定ターゲット: 未設定"
elif [ "$default_target" = "dev" ] || [ "$default_target" = "stg" ] || [ "$default_target" = "prod" ]; then
  ok "既定ターゲット: ${default_target}"
else
  warn "既定ターゲット: ${default_target} (dev/stg/prod 以外)"
fi

check_script_field "deployment.deploy_script" "配備スクリプト"
check_script_field "deployment.sync_script" "同期スクリプト"
check_script_field "deployment.rollback_script" "ロールバックスクリプト"

backup_before="$(get_config deployment.backup_before_deploy)"
if [ "${backup_before:-true}" = "true" ]; then
  ok "反映前バックアップ: true"
  backup_dir="$(get_config deployment.backup_dir)"
  if is_placeholder "$backup_dir"; then
    error "バックアップ先: 未設定"
  else
    ok "バックアップ先: ${backup_dir}"
  fi
  backup_retention="$(get_config deployment.backup_retention)"
  if is_placeholder "$backup_retention"; then
    warn "バックアップ保持世代: 未設定"
  else
    ok "バックアップ保持世代: ${backup_retention}"
  fi
else
  warn "反映前バックアップ: false"
fi

visibility="$(get_config repository.visibility)"
if [ "$visibility" = "private" ] || [ "$visibility" = "public" ] || [ "$visibility" = "internal" ]; then
  ok "GitHub 公開範囲: ${visibility}"
else
  warn "GitHub 公開範囲: ${visibility:-未設定}"
fi

ensure_remote_repo="$(get_config repository.ensure_remote_repo)"
if [ "${ensure_remote_repo:-false}" = "true" ]; then
  ok "GitHub リポジトリ自動作成: true"
  if command -v gh >/dev/null 2>&1; then
    ok "GitHub CLI gh: 利用可能"
    if gh auth status >/dev/null 2>&1; then
      ok "GitHub CLI 認証: 有効"
    else
      warn "GitHub CLI 認証: 未ログイン"
    fi
  else
    error "GitHub CLI gh: 見つかりません"
  fi
else
  ok "GitHub リポジトリ自動作成: false"
fi

owner_type="$(get_config repository.owner_type)"
if is_placeholder "$owner_type"; then
  warn "GitHub 所有者種別: 未設定"
elif [ "$owner_type" = "personal" ] || [ "$owner_type" = "organization" ]; then
  ok "GitHub 所有者種別: ${owner_type}"
else
  warn "GitHub 所有者種別: ${owner_type} (personal/organization を推奨)"
fi

owner_name="$(get_config repository.owner_name)"
if is_placeholder "$owner_name"; then
  warn "GitHub 所有者名: 未設定"
else
  ok "GitHub 所有者名: ${owner_name}"
fi

repo_name="$(get_config repository.repo_name)"
suggested_repo_name="$(build_repo_name)"
if is_placeholder "$repo_name"; then
  if [ -n "$suggested_repo_name" ]; then
    warn "GitHub リポジトリ名: 未設定（候補: ${suggested_repo_name}）"
  else
    warn "GitHub リポジトリ名: 未設定"
  fi
else
  ok "GitHub リポジトリ名: ${repo_name}"
  if [ -n "$suggested_repo_name" ] && [ "$repo_name" != "$suggested_repo_name" ]; then
    warn "命名候補との差分: 推奨は ${suggested_repo_name}"
  fi
fi

repo_description="$(get_config repository.description)"
suggested_repo_description="$(build_repo_description)"
if is_placeholder "$repo_description"; then
  if [ -n "$suggested_repo_description" ]; then
    warn "GitHub 説明文: 未設定（候補: ${suggested_repo_description}）"
  else
    warn "GitHub 説明文: 未設定"
  fi
else
  ok "GitHub 説明文: ${repo_description}"
fi

remote_url="$(get_config repository.remote_url)"
derived_remote_url="$(build_remote_url)"
if is_placeholder "$remote_url"; then
  if [ -n "$derived_remote_url" ]; then
    warn "GitHub remote: 未設定（候補: ${derived_remote_url}）"
  else
    warn "GitHub remote: 未設定"
  fi
else
  ok "GitHub remote: ${remote_url}"
  if [ -n "$derived_remote_url" ] && [ "$remote_url" != "$derived_remote_url" ]; then
    warn "GitHub remote の候補との差分: ${derived_remote_url}"
  fi
fi

stable_branch="$(get_config repository.default_branch)"
if is_placeholder "$stable_branch"; then
  warn "安定ブランチ: 未設定"
else
  ok "安定ブランチ: ${stable_branch}"
fi

integration_branch="$(get_config repository.integration_branch)"
if is_placeholder "$integration_branch"; then
  warn "統合ブランチ: 未設定"
else
  ok "統合ブランチ: ${integration_branch}"
fi

if ! is_placeholder "$stable_branch" && ! is_placeholder "$integration_branch" && [ "$stable_branch" = "$integration_branch" ]; then
  warn "安定ブランチと統合ブランチが同じです: ${stable_branch}"
fi

section "Git"
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  git_root="$(git rev-parse --show-toplevel)"
  if [ "$git_root" = "$ROOT_DIR" ]; then
    ok "Git ルート: 現在のディレクトリ"
  else
    warn "Git ルート: $(rel_path "$git_root") (このディレクトリは子階層)"
  fi

  current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  if [ -n "$current_branch" ]; then
    if [ -n "$stable_branch" ] && [ "$current_branch" = "$stable_branch" ]; then
      warn "現在のブランチ: ${current_branch} （通常作業は feature ブランチを推奨）"
    elif [ -n "$integration_branch" ] && [ "$current_branch" = "$integration_branch" ]; then
      ok "現在のブランチ: ${current_branch}"
    else
      ok "現在のブランチ: ${current_branch}"
    fi
  else
    warn "現在のブランチ: 取得できません"
  fi

  if ! is_placeholder "$stable_branch"; then
    if git show-ref --verify --quiet "refs/heads/${stable_branch}"; then
      ok "ローカル安定ブランチ: ${stable_branch}"
    else
      warn "ローカル安定ブランチ: ${stable_branch} がありません"
    fi
  fi

  if ! is_placeholder "$integration_branch"; then
    if git show-ref --verify --quiet "refs/heads/${integration_branch}"; then
      ok "ローカル統合ブランチ: ${integration_branch}"
    else
      warn "ローカル統合ブランチ: ${integration_branch} がありません"
    fi
  fi

  if git remote get-url origin >/dev/null 2>&1; then
    ok "origin: $(git remote get-url origin)"
  else
    warn "origin: 未設定"
  fi

  hooks_path="$(git config --get core.hooksPath || true)"
  if [ "$hooks_path" = ".githooks" ]; then
    ok "core.hooksPath: .githooks"
  elif [ -n "$hooks_path" ]; then
    warn "core.hooksPath: ${hooks_path}"
  else
    warn "core.hooksPath: 未設定"
  fi

  expected_protected_branches=""
  if ! is_placeholder "$stable_branch"; then
    expected_protected_branches="$stable_branch"
  fi
  if ! is_placeholder "$integration_branch" && [ "$integration_branch" != "$stable_branch" ]; then
    expected_protected_branches="${expected_protected_branches} ${integration_branch}"
  fi
  expected_protected_branches="${expected_protected_branches#"${expected_protected_branches%%[![:space:]]*}"}"

  protected_branches="$(git config --get hooks.protectedBranches || true)"
  if [ -z "$protected_branches" ]; then
    warn "hooks.protectedBranches: 未設定"
  elif [ -n "$expected_protected_branches" ] && [ "$protected_branches" = "$expected_protected_branches" ]; then
    ok "hooks.protectedBranches: ${protected_branches}"
  else
    warn "hooks.protectedBranches: ${protected_branches}"
  fi

  dirty_count="$(git status --porcelain | wc -l | tr -d ' ')"
  if [ "${dirty_count:-0}" = "0" ]; then
    ok "未コミット差分: なし"
  else
    warn "未コミット差分: ${dirty_count} 件"
  fi
else
  warn "Git: 未初期化"
fi

if [ -f ".githooks/commit-msg" ]; then
  if [ -x ".githooks/commit-msg" ]; then
    ok "commit-msg hook: 有効"
  else
    warn "commit-msg hook: 実行権限なし"
  fi
else
  warn "commit-msg hook: .githooks/commit-msg がありません"
fi

if [ -f ".githooks/pre-commit" ]; then
  if [ -x ".githooks/pre-commit" ]; then
    ok "pre-commit hook: 有効"
  else
    warn "pre-commit hook: 実行権限なし"
  fi
else
  warn "pre-commit hook: .githooks/pre-commit がありません"
fi

if [ -f ".githooks/pre-push" ]; then
  if [ -x ".githooks/pre-push" ]; then
    ok "pre-push hook: 有効"
  else
    warn "pre-push hook: 実行権限なし"
  fi
else
  warn "pre-push hook: .githooks/pre-push がありません"
fi

section "Runtime"
check_command "bash"
check_command "python3"
check_command "git"
check_command "rg"

if [ -f "${SCRIPT_DIR}/check-branch-sync.sh" ]; then
  ok "スクリプト check-branch-sync.sh: 利用可能"
else
  warn "スクリプト check-branch-sync.sh: 見つかりません"
fi

if [ -d "$ROOT_DIR/wp-content" ] || ! is_placeholder "$(get_config wordpress.active_theme)"; then
  section "WordPress"
  if [ -d "$ROOT_DIR/wp-content/themes" ]; then
    ok "テーマディレクトリ: wp-content/themes/"
  else
    warn "テーマディレクトリ: wp-content/themes/ がありません"
  fi

  active_theme="$(get_config wordpress.active_theme)"
  if is_placeholder "$active_theme"; then
    warn "運用テーマ: 未設定"
  elif [ -d "$ROOT_DIR/wp-content/themes/$active_theme" ]; then
    ok "運用テーマ: ${active_theme}"
  else
    warn "運用テーマ: ${active_theme} が見つかりません"
  fi

  child_theme="$(get_config wordpress.child_theme)"
  if ! is_placeholder "$child_theme"; then
    if [ -d "$ROOT_DIR/wp-content/themes/$child_theme" ]; then
      ok "子テーマ: ${child_theme}"
    else
      warn "子テーマ: ${child_theme} が見つかりません"
    fi
  fi

  parent_theme="$(get_config wordpress.parent_theme)"
  if ! is_placeholder "$parent_theme"; then
    if [ -d "$ROOT_DIR/wp-content/themes/$parent_theme" ]; then
      ok "親テーマ: ${parent_theme}"
    else
      warn "親テーマ: ${parent_theme} が見つかりません"
    fi
  fi
fi

printf '\nSummary: %s OK / %s WARN / %s ERROR\n' "$OK_COUNT" "$WARN_COUNT" "$ERROR_COUNT"

if [ "$ERROR_COUNT" -gt 0 ] || { [ "$STRICT" -eq 1 ] && [ "$WARN_COUNT" -gt 0 ]; }; then
  exit 1
fi
