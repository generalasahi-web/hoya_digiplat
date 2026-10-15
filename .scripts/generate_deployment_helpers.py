#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
from textwrap import dedent

from project_config import get_value, load_config

AUTO_MARKER = "AUTO-GENERATED DEPLOYMENT HELPER"
SETUP_REQUIRED_MARKER = "[SETUP REQUIRED]"


def load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.is_file():
        return data

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def infer_profile(root: Path, config: dict) -> str:
    if (root / "wp-content").is_dir() or get_value(config, "wordpress.active_theme"):
        return "wordpress"
    return "existing"


def detect_source_subdir(root: Path, profile: str) -> str:
    if profile == "wordpress":
        if (root / "wp-content").is_dir():
            return "wp-content"
        if (root / "public_html" / "wp-content").is_dir():
            return "public_html/wp-content"
        return "."

    for candidate in ("public_html", "dist", "out", "build"):
        if (root / candidate).is_dir():
            return candidate
    return "."


def rsync_excludes(profile: str, source_subdir: str) -> list[str]:
    if profile == "wordpress":
        return [
            "uploads/",
            "upgrade/",
            "cache/",
            "backup-db/",
            "ai1wm-backups/",
            ".DS_Store",
        ]

    if source_subdir == ".":
        return [
            ".git/",
            ".claude/",
            ".agents/",
            ".codex/",
            ".githooks/",
            ".vscode/",
            "config/",
            "contexts/",
            "doc/",
            "rules/",
            "_deploy_backups/",
            ".env",
            ".env.local",
            ".env.*.local",
            "MEMORY.md",
            "CLAUDE.md",
            "AGENTS.md",
            "README.md",
            "*.log",
            ".DS_Store",
        ]

    return [
        "*.log",
        ".DS_Store",
    ]


def lftp_excludes(profile: str, source_subdir: str) -> list[str]:
    if profile == "wordpress":
        return [
            "uploads",
            "upgrade",
            "cache",
            "backup-db",
            "ai1wm-backups",
            ".DS_Store",
        ]

    if source_subdir == ".":
        return [
            ".git",
            ".claude",
            ".agents",
            ".codex",
            ".githooks",
            ".vscode",
            "config",
            "contexts",
            "doc",
            "rules",
            "_deploy_backups",
            ".env",
            ".env.local",
            "MEMORY.md",
            "CLAUDE.md",
            "AGENTS.md",
            "README.md",
        ]

    return [".DS_Store"]


def normalize_method(method: str) -> str:
    value = method.strip().lower()
    compact = value.replace(" ", "")
    if not compact:
        return ""
    if "sftp" in compact:
        return "sftp"
    if compact == "ftp" or compact.startswith("ftp/") or compact.endswith("/ftp") or compact.startswith("ftp+") or compact.endswith("+ftp"):
        return "ftp"
    if "rsync" in compact or compact == "ssh" or "ssh" in compact:
        return "rsync"
    return ""


def source_expr(source_subdir: str) -> str:
    if source_subdir == ".":
        return '${ROOT_DIR}'
    return '${ROOT_DIR}/' + source_subdir


def sync_dest_expr(source_subdir: str) -> str:
    if source_subdir == ".":
        return '${ROOT_DIR}/_remote_sync/${TARGET}'
    return '${ROOT_DIR}/' + source_subdir


def array_block(items: list[str]) -> str:
    if not items:
        return '  # no excludes'
    return "\n".join(f'  "{item}"' for item in items)


def render_placeholder(kind: str, method: str) -> str:
    reason = method or "unset"
    return dedent(
        f"""\
        #!/usr/bin/env bash
        set -euo pipefail

        cat <<'EOF'
        {SETUP_REQUIRED_MARKER} {kind}
        deployment.method={reason} では自動生成できません。

        対応が必要です:
        - 対象パス
        - 接続方法
        - バックアップとロールバック手順
        EOF

        exit 1
        """
    )


def render_rsync_deploy(source_subdir: str, profile: str, project_slug: str) -> str:
    return dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail

        # AUTO-GENERATED DEPLOYMENT HELPER
        # method: rsync/ssh
        # source profile: __PROFILE__

        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
        TARGET="${DEPLOY_TARGET:-}"
        DRY_RUN="${DEPLOY_DRY_RUN:-0}"
        RELEASE_ID="${DEPLOY_RELEASE_ID:-$(date '+%Y%m%d-%H%M%S')}"
        SOURCE_PATH="${DEPLOY_SOURCE_PATH:-__SOURCE_EXPR__}"

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
            *)
              shift
              ;;
          esac
        done

        load_local_env() {
          if [ -f "${ROOT_DIR}/.env.local" ]; then
            set -a
            # shellcheck disable=SC1091
            . "${ROOT_DIR}/.env.local"
            set +a
          fi
        }

        require_cmd() {
          if ! command -v "$1" >/dev/null 2>&1; then
            echo "Required command not found: $1" >&2
            exit 1
          fi
        }

        remote_path_for_target() {
          local key="REMOTE_PATH_${TARGET_UPPER}"
          printf '%s\\n' "${!key:-}"
        }

        load_local_env
        require_cmd rsync
        require_cmd ssh

        if [ -z "$TARGET" ]; then
          echo "Target is required." >&2
          exit 1
        fi

        TARGET_UPPER="$(printf '%s' "$TARGET" | tr '[:lower:]' '[:upper:]')"

        REMOTE_PATH="$(remote_path_for_target)"
        if [ -z "$REMOTE_PATH" ]; then
          echo "Remote path is not set for target ${TARGET}. Fill REMOTE_PATH_${TARGET_UPPER} in .env.local." >&2
          exit 1
        fi

        if [ -z "${SSH_HOST:-}" ] || [ -z "${SSH_USER:-}" ]; then
          echo "SSH_HOST and SSH_USER are required in .env.local for rsync/ssh deployment." >&2
          exit 1
        fi

        if [ ! -d "$SOURCE_PATH" ]; then
          echo "Source path not found: $SOURCE_PATH" >&2
          exit 1
        fi

        REMOTE_BACKUP_ROOT="${BACKUP_REMOTE_DIR:-$(dirname "$(dirname "$REMOTE_PATH")")/_backups/__PROJECT_SLUG__}"
        REMOTE_BACKUP_PATH="${REMOTE_BACKUP_ROOT%/}/${TARGET}/${RELEASE_ID}"

        EXCLUDES=(
        __RSYNC_EXCLUDES__
        )

        ssh_cmd=(ssh -p "${SSH_PORT:-22}")
        if [ -n "${SSH_KEY_PATH:-}" ]; then
          ssh_cmd+=(-i "${SSH_KEY_PATH}")
        fi
        ssh_cmd+=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new)
        rsync_rsh="$(printf '%q ' "${ssh_cmd[@]}")"
        exclude_args=()
        for pattern in "${EXCLUDES[@]}"; do
          exclude_args+=(--exclude "$pattern")
        done

        echo "Method: rsync/ssh"
        echo "Target: $TARGET"
        echo "Source: $SOURCE_PATH"
        echo "Remote path: $REMOTE_PATH"
        echo "Server backup: $REMOTE_BACKUP_PATH"

        if [ "$DRY_RUN" -eq 1 ]; then
          rsync -azn --delete -e "$rsync_rsh" "${exclude_args[@]}" "$SOURCE_PATH"/ "${SSH_USER}@${SSH_HOST}:${REMOTE_PATH%/}/"
          exit 0
        fi

        remote_path_escaped="${REMOTE_PATH//\\'/\\'\\\\\\'\\'}"
        "${ssh_cmd[@]}" "${SSH_USER}@${SSH_HOST}" "mkdir -p '$remote_path_escaped'"

        if [ "${DEPLOY_BACKUP_BEFORE_DEPLOY:-true}" = "true" ]; then
          remote_backup_escaped="${REMOTE_BACKUP_PATH//\\'/\\'\\\\\\'\\'}"
          "${ssh_cmd[@]}" "${SSH_USER}@${SSH_HOST}" "mkdir -p '${remote_backup_escaped}'"
          rsync -az --delete --backup --backup-dir="$REMOTE_BACKUP_PATH" -e "$rsync_rsh" "${exclude_args[@]}" "$SOURCE_PATH"/ "${SSH_USER}@${SSH_HOST}:${REMOTE_PATH%/}/"
          if [ -n "${DEPLOY_BACKUP_RETENTION:-}" ]; then
            remote_target_dir="${REMOTE_BACKUP_ROOT%/}/${TARGET}"
            remote_target_escaped="${remote_target_dir//\\'/\\'\\\\\\'\\'}"
            "${ssh_cmd[@]}" "${SSH_USER}@${SSH_HOST}" "cd '${remote_target_escaped}' && ls -1d */ 2>/dev/null | sort | head -n -${DEPLOY_BACKUP_RETENTION} | xargs -r rm -rf" || true
          fi
        else
          rsync -az --delete -e "$rsync_rsh" "${exclude_args[@]}" "$SOURCE_PATH"/ "${SSH_USER}@${SSH_HOST}:${REMOTE_PATH%/}/"
        fi

        echo "Deploy completed."
        """
    ).replace("__PROFILE__", profile).replace("__SOURCE_EXPR__", source_expr(source_subdir)).replace("__RSYNC_EXCLUDES__", array_block(rsync_excludes(profile, source_subdir))).replace("__PROJECT_SLUG__", project_slug)


def render_rsync_sync(source_subdir: str, profile: str) -> str:
    return dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail

        # AUTO-GENERATED DEPLOYMENT HELPER
        # method: rsync/ssh
        # source profile: __PROFILE__

        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
        TARGET="${SYNC_TARGET:-}"
        DRY_RUN=0
        DEST_PATH="${SYNC_DEST_PATH:-__SYNC_DEST_EXPR__}"

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
            *)
              shift
              ;;
          esac
        done

        load_local_env() {
          if [ -f "${ROOT_DIR}/.env.local" ]; then
            set -a
            # shellcheck disable=SC1091
            . "${ROOT_DIR}/.env.local"
            set +a
          fi
        }

        require_cmd() {
          if ! command -v "$1" >/dev/null 2>&1; then
            echo "Required command not found: $1" >&2
            exit 1
          fi
        }

        remote_path_for_target() {
          local key="REMOTE_PATH_${TARGET_UPPER}"
          printf '%s\\n' "${!key:-}"
        }

        load_local_env
        require_cmd rsync

        if [ -z "$TARGET" ]; then
          echo "Target is required." >&2
          exit 1
        fi

        TARGET_UPPER="$(printf '%s' "$TARGET" | tr '[:lower:]' '[:upper:]')"

        REMOTE_PATH="$(remote_path_for_target)"
        if [ -z "$REMOTE_PATH" ]; then
          echo "Remote path is not set for target ${TARGET}. Fill REMOTE_PATH_${TARGET_UPPER} in .env.local." >&2
          exit 1
        fi

        if [ -z "${SSH_HOST:-}" ] || [ -z "${SSH_USER:-}" ]; then
          echo "SSH_HOST and SSH_USER are required in .env.local for rsync/ssh sync." >&2
          exit 1
        fi

        if [ "$DRY_RUN" -ne 1 ]; then
          mkdir -p "$DEST_PATH"
        fi

        EXCLUDES=(
        __RSYNC_EXCLUDES__
        )

        ssh_cmd=(ssh -p "${SSH_PORT:-22}")
        if [ -n "${SSH_KEY_PATH:-}" ]; then
          ssh_cmd+=(-i "${SSH_KEY_PATH}")
        fi
        ssh_cmd+=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new)
        rsync_rsh="$(printf '%q ' "${ssh_cmd[@]}")"
        exclude_args=()
        for pattern in "${EXCLUDES[@]}"; do
          exclude_args+=(--exclude "$pattern")
        done

        echo "Method: rsync/ssh"
        echo "Target: $TARGET"
        echo "Remote path: $REMOTE_PATH"
        echo "Destination: $DEST_PATH"

        cmd=(rsync -az --delete -e "$rsync_rsh" "${exclude_args[@]}" "${SSH_USER}@${SSH_HOST}:${REMOTE_PATH%/}/" "$DEST_PATH"/)
        if [ "$DRY_RUN" -eq 1 ]; then
          cmd=(rsync -azn --delete -e "$rsync_rsh" "${exclude_args[@]}" "${SSH_USER}@${SSH_HOST}:${REMOTE_PATH%/}/" "$DEST_PATH"/)
        fi

        "${cmd[@]}"
        """
    ).replace("__PROFILE__", profile).replace("__SYNC_DEST_EXPR__", sync_dest_expr(source_subdir)).replace("__RSYNC_EXCLUDES__", array_block(rsync_excludes(profile, source_subdir)))


def render_rsync_rollback(profile: str, project_slug: str) -> str:
    return dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail

        # AUTO-GENERATED DEPLOYMENT HELPER
        # method: rsync/ssh
        # source profile: __PROFILE__

        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
        TARGET="${ROLLBACK_TARGET:-}"
        BACKUP_ID="${ROLLBACK_BACKUP_ID:-latest}"
        DRY_RUN="${ROLLBACK_DRY_RUN:-0}"

        while [ "$#" -gt 0 ]; do
          case "$1" in
            --target)
              TARGET="${2:-}"
              shift 2
              ;;
            --backup-id)
              BACKUP_ID="${2:-latest}"
              shift 2
              ;;
            --dry-run)
              DRY_RUN=1
              shift
              ;;
            *)
              shift
              ;;
          esac
        done

        load_local_env() {
          if [ -f "${ROOT_DIR}/.env.local" ]; then
            set -a
            # shellcheck disable=SC1091
            . "${ROOT_DIR}/.env.local"
            set +a
          fi
        }

        require_cmd() {
          if ! command -v "$1" >/dev/null 2>&1; then
            echo "Required command not found: $1" >&2
            exit 1
          fi
        }

        remote_path_for_target() {
          local key="REMOTE_PATH_${TARGET_UPPER}"
          printf '%s\\n' "${!key:-}"
        }

        load_local_env
        require_cmd ssh

        if [ -z "$TARGET" ]; then
          echo "Target is required." >&2
          exit 1
        fi

        TARGET_UPPER="$(printf '%s' "$TARGET" | tr '[:lower:]' '[:upper:]')"

        REMOTE_PATH="$(remote_path_for_target)"
        if [ -z "$REMOTE_PATH" ]; then
          echo "Remote path is not set for target ${TARGET}. Fill REMOTE_PATH_${TARGET_UPPER} in .env.local." >&2
          exit 1
        fi

        if [ -z "${SSH_HOST:-}" ] || [ -z "${SSH_USER:-}" ]; then
          echo "SSH_HOST and SSH_USER are required in .env.local for rsync/ssh rollback." >&2
          exit 1
        fi

        ssh_cmd=(ssh -p "${SSH_PORT:-22}")
        if [ -n "${SSH_KEY_PATH:-}" ]; then
          ssh_cmd+=(-i "${SSH_KEY_PATH}")
        fi
        ssh_cmd+=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new)

        REMOTE_BACKUP_ROOT="${BACKUP_REMOTE_DIR:-$(dirname "$(dirname "$REMOTE_PATH")")/_backups/__PROJECT_SLUG__}"
        REMOTE_TARGET_DIR="${REMOTE_BACKUP_ROOT%/}/${TARGET}"
        remote_target_escaped="${REMOTE_TARGET_DIR//\\'/\\'\\\\\\'\\'}"

        if [ "$BACKUP_ID" = "latest" ]; then
          REMOTE_BACKUP_PATH="$("${ssh_cmd[@]}" "${SSH_USER}@${SSH_HOST}" "ls -1d '${remote_target_escaped}/'*/ 2>/dev/null | sort | tail -1" | sed 's|/$||')"
          if [ -z "$REMOTE_BACKUP_PATH" ]; then
            echo "No backup found on server: ${REMOTE_TARGET_DIR}" >&2
            exit 1
          fi
        else
          REMOTE_BACKUP_PATH="${REMOTE_TARGET_DIR}/${BACKUP_ID}"
        fi

        remote_backup_escaped="${REMOTE_BACKUP_PATH//\\'/\\'\\\\\\'\\'}"
        if ! "${ssh_cmd[@]}" "${SSH_USER}@${SSH_HOST}" "test -d '${remote_backup_escaped}'" 2>/dev/null; then
          echo "Backup not found on server: ${REMOTE_BACKUP_PATH}" >&2
          echo "Available backups:"
          "${ssh_cmd[@]}" "${SSH_USER}@${SSH_HOST}" "ls -1d '${remote_target_escaped}/'*/ 2>/dev/null | sed 's|.*/\\(.*\\)/$|  \\1|'" || echo "  (none)"
          exit 1
        fi

        echo "Method: rsync/ssh"
        echo "Target: $TARGET"
        echo "Server backup: $REMOTE_BACKUP_PATH"
        echo "Remote path: $REMOTE_PATH"

        remote_path_escaped="${REMOTE_PATH//\\'/\\'\\\\\\'\\'}"

        if [ "$DRY_RUN" -eq 1 ]; then
          "${ssh_cmd[@]}" "${SSH_USER}@${SSH_HOST}" "rsync -azn '${remote_backup_escaped}/' '${remote_path_escaped}/'"
          exit 0
        fi

        "${ssh_cmd[@]}" "${SSH_USER}@${SSH_HOST}" "rsync -a '${remote_backup_escaped}/' '${remote_path_escaped}/'"
        echo "Rollback completed."
        """
    ).replace("__PROFILE__", profile).replace("__PROJECT_SLUG__", project_slug)


def render_lftp_deploy(method: str, source_subdir: str, profile: str, project_slug: str) -> str:
    port = "21" if method == "ftp" else "22"
    var_prefix = method.upper()
    return dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail

        # AUTO-GENERATED DEPLOYMENT HELPER
        # method: __METHOD__
        # source profile: __PROFILE__

        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
        TARGET="${DEPLOY_TARGET:-}"
        DRY_RUN="${DEPLOY_DRY_RUN:-0}"
        RELEASE_ID="${DEPLOY_RELEASE_ID:-$(date '+%Y%m%d-%H%M%S')}"
        SOURCE_PATH="${DEPLOY_SOURCE_PATH:-__SOURCE_EXPR__}"

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
            *)
              shift
              ;;
          esac
        done

        load_local_env() {
          if [ -f "${ROOT_DIR}/.env.local" ]; then
            set -a
            # shellcheck disable=SC1091
            . "${ROOT_DIR}/.env.local"
            set +a
          fi
        }

        require_cmd() {
          if ! command -v "$1" >/dev/null 2>&1; then
            echo "Required command not found: $1" >&2
            exit 1
          fi
        }

        remote_path_for_target() {
          local key="REMOTE_PATH_${TARGET_UPPER}"
          printf '%s\\n' "${!key:-}"
        }

        quote_lftp() {
          local value="$1"
          value="${value//\\\\/\\\\\\\\}"
          value="${value//\\"/\\\\\\"}"
          printf '"%s"' "$value"
        }

        build_exclude_flags() {
          local flags=()
          local pattern
          for pattern in "${LFTP_EXCLUDES[@]}"; do
            flags+=(-X "$pattern")
          done
          printf '%q ' "${flags[@]}"
        }

        lftp_conn() {
          lftp -u "${USER_NAME},${PASSWORD}" -p "$PORT" "__METHOD__://${HOST}" -e "$1"
        }

        load_local_env
        require_cmd lftp

        if [ -z "$TARGET" ]; then
          echo "Target is required." >&2
          exit 1
        fi

        TARGET_UPPER="$(printf '%s' "$TARGET" | tr '[:lower:]' '[:upper:]')"

        REMOTE_PATH="$(remote_path_for_target)"
        if [ -z "$REMOTE_PATH" ]; then
          echo "Remote path is not set for target ${TARGET}. Fill REMOTE_PATH_${TARGET_UPPER} in .env.local." >&2
          exit 1
        fi

        HOST="${__VAR_PREFIX___HOST:-}"
        PORT="${__VAR_PREFIX___PORT:-__PORT__}"
        USER_NAME="${__VAR_PREFIX___USER:-}"
        PASSWORD="${__VAR_PREFIX___PASS:-}"

        if [ -z "$HOST" ] || [ -z "$USER_NAME" ] || [ -z "$PASSWORD" ]; then
          echo "__VAR_PREFIX___HOST, __VAR_PREFIX___USER, and __VAR_PREFIX___PASS are required in .env.local for __METHOD__ deployment." >&2
          exit 1
        fi

        if [ ! -d "$SOURCE_PATH" ]; then
          echo "Source path not found: $SOURCE_PATH" >&2
          exit 1
        fi

        REMOTE_BACKUP_ROOT="${BACKUP_REMOTE_DIR:-$(dirname "$(dirname "$REMOTE_PATH")")/_backups/__PROJECT_SLUG__}"
        REMOTE_BACKUP_PATH="${REMOTE_BACKUP_ROOT%/}/${TARGET}/${RELEASE_ID}"

        LFTP_EXCLUDES=(
        __LFTP_EXCLUDES__
        )
        exclude_flags="$(build_exclude_flags)"
        deploy_flags="--reverse --verbose --delete"
        if [ "$DRY_RUN" -eq 1 ]; then
          deploy_flags="${deploy_flags} --dry-run"
        fi

        echo "Method: __METHOD__"
        echo "Target: $TARGET"
        echo "Source: $SOURCE_PATH"
        echo "Remote path: $REMOTE_PATH"
        echo "Server backup: $REMOTE_BACKUP_PATH"

        if [ "${DEPLOY_BACKUP_BEFORE_DEPLOY:-true}" = "true" ] && [ "$DRY_RUN" -ne 1 ]; then
          echo "Detecting changed files..."
          dry_output="$(lftp_conn "mirror --reverse --dry-run --delete ${exclude_flags} $(quote_lftp "$SOURCE_PATH") $(quote_lftp "$REMOTE_PATH"); bye" 2>&1)" || true
          changed_files="$(echo "$dry_output" | grep -oE "'[^']+'" | tr -d "'" | sort -u)" || true
          if [ -n "$changed_files" ]; then
            echo "Moving changed files to backup on server..."
            mv_cmds="mkdir -p $(quote_lftp "$REMOTE_BACKUP_PATH");"
            while IFS= read -r remote_file; do
              rel_path="${remote_file#${REMOTE_PATH}/}"
              [ "$rel_path" = "$remote_file" ] && rel_path="${remote_file#${REMOTE_PATH}}"
              [ -z "$rel_path" ] && continue
              backup_dest="${REMOTE_BACKUP_PATH%/}/${rel_path}"
              backup_dir="$(dirname "$backup_dest")"
              mv_cmds="${mv_cmds} mkdir -p $(quote_lftp "$backup_dir"); mv $(quote_lftp "${REMOTE_PATH%/}/${rel_path}") $(quote_lftp "$backup_dest") 2>/dev/null;"
            done <<< "$changed_files"
            lftp_conn "${mv_cmds} bye" || true
          fi
          if [ -n "${DEPLOY_BACKUP_RETENTION:-}" ]; then
            remote_target_dir="${REMOTE_BACKUP_ROOT%/}/${TARGET}"
            cleanup_cmd="cls -1 $(quote_lftp "$remote_target_dir") 2>/dev/null"
            old_dirs="$(lftp_conn "${cleanup_cmd}; bye" 2>/dev/null | sort | head -n "-${DEPLOY_BACKUP_RETENTION}")" || true
            if [ -n "$old_dirs" ]; then
              rm_cmds=""
              while IFS= read -r old_dir; do
                [ -z "$old_dir" ] && continue
                rm_cmds="${rm_cmds} rm -rf $(quote_lftp "${remote_target_dir%/}/${old_dir}");"
              done <<< "$old_dirs"
              lftp_conn "${rm_cmds} bye" || true
            fi
          fi
        fi

        prepare_cmd=""
        if [ "$DRY_RUN" -ne 1 ]; then
          prepare_cmd="mkdir -p $(quote_lftp "$REMOTE_PATH");"
        fi
        deploy_cmd="${prepare_cmd} mirror ${deploy_flags} ${exclude_flags} $(quote_lftp "$SOURCE_PATH") $(quote_lftp "$REMOTE_PATH"); bye"

        lftp_conn "${deploy_cmd}"
        """
    ).replace("__METHOD__", method).replace("__PROFILE__", profile).replace("__SOURCE_EXPR__", source_expr(source_subdir)).replace("__VAR_PREFIX__", var_prefix).replace("__PORT__", port).replace("__LFTP_EXCLUDES__", array_block(lftp_excludes(profile, source_subdir))).replace("__PROJECT_SLUG__", project_slug)


def render_lftp_sync(method: str, source_subdir: str, profile: str) -> str:
    port = "21" if method == "ftp" else "22"
    var_prefix = method.upper()
    return dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail

        # AUTO-GENERATED DEPLOYMENT HELPER
        # method: __METHOD__
        # source profile: __PROFILE__

        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
        TARGET="${SYNC_TARGET:-}"
        DRY_RUN=0
        DEST_PATH="${SYNC_DEST_PATH:-__SYNC_DEST_EXPR__}"

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
            *)
              shift
              ;;
          esac
        done

        load_local_env() {
          if [ -f "${ROOT_DIR}/.env.local" ]; then
            set -a
            # shellcheck disable=SC1091
            . "${ROOT_DIR}/.env.local"
            set +a
          fi
        }

        require_cmd() {
          if ! command -v "$1" >/dev/null 2>&1; then
            echo "Required command not found: $1" >&2
            exit 1
          fi
        }

        remote_path_for_target() {
          local key="REMOTE_PATH_${TARGET_UPPER}"
          printf '%s\\n' "${!key:-}"
        }

        quote_lftp() {
          local value="$1"
          value="${value//\\\\/\\\\\\\\}"
          value="${value//\\"/\\\\\\"}"
          printf '"%s"' "$value"
        }

        build_exclude_flags() {
          local flags=()
          local pattern
          for pattern in "${LFTP_EXCLUDES[@]}"; do
            flags+=(-X "$pattern")
          done
          printf '%q ' "${flags[@]}"
        }

        load_local_env
        require_cmd lftp

        if [ -z "$TARGET" ]; then
          echo "Target is required." >&2
          exit 1
        fi

        TARGET_UPPER="$(printf '%s' "$TARGET" | tr '[:lower:]' '[:upper:]')"

        REMOTE_PATH="$(remote_path_for_target)"
        if [ -z "$REMOTE_PATH" ]; then
          echo "Remote path is not set for target ${TARGET}. Fill REMOTE_PATH_${TARGET_UPPER} in .env.local." >&2
          exit 1
        fi

        HOST="${__VAR_PREFIX___HOST:-}"
        PORT="${__VAR_PREFIX___PORT:-__PORT__}"
        USER_NAME="${__VAR_PREFIX___USER:-}"
        PASSWORD="${__VAR_PREFIX___PASS:-}"

        if [ -z "$HOST" ] || [ -z "$USER_NAME" ] || [ -z "$PASSWORD" ]; then
          echo "__VAR_PREFIX___HOST, __VAR_PREFIX___USER, and __VAR_PREFIX___PASS are required in .env.local for __METHOD__ sync." >&2
          exit 1
        fi

        if [ "$DRY_RUN" -ne 1 ]; then
          mkdir -p "$DEST_PATH"
        fi

        LFTP_EXCLUDES=(
        __LFTP_EXCLUDES__
        )
        exclude_flags="$(build_exclude_flags)"
        mirror_flags="--verbose"
        if [ "$DRY_RUN" -eq 1 ]; then
          mirror_flags="${mirror_flags} --dry-run"
        fi

        echo "Method: __METHOD__"
        echo "Target: $TARGET"
        echo "Remote path: $REMOTE_PATH"
        echo "Destination: $DEST_PATH"

        lftp -u "${USER_NAME},${PASSWORD}" -p "$PORT" "__METHOD__://${HOST}" -e "mirror ${mirror_flags} ${exclude_flags} $(quote_lftp "$REMOTE_PATH") $(quote_lftp "$DEST_PATH"); bye"
        """
    ).replace("__METHOD__", method).replace("__PROFILE__", profile).replace("__SYNC_DEST_EXPR__", sync_dest_expr(source_subdir)).replace("__VAR_PREFIX__", var_prefix).replace("__PORT__", port).replace("__LFTP_EXCLUDES__", array_block(lftp_excludes(profile, source_subdir)))


def render_lftp_rollback(method: str, profile: str, project_slug: str) -> str:
    port = "21" if method == "ftp" else "22"
    var_prefix = method.upper()
    return dedent(
        """\
        #!/usr/bin/env bash
        set -euo pipefail

        # AUTO-GENERATED DEPLOYMENT HELPER
        # method: __METHOD__
        # source profile: __PROFILE__

        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
        TARGET="${ROLLBACK_TARGET:-}"
        BACKUP_ID="${ROLLBACK_BACKUP_ID:-latest}"
        DRY_RUN="${ROLLBACK_DRY_RUN:-0}"

        while [ "$#" -gt 0 ]; do
          case "$1" in
            --target)
              TARGET="${2:-}"
              shift 2
              ;;
            --backup-id)
              BACKUP_ID="${2:-latest}"
              shift 2
              ;;
            --dry-run)
              DRY_RUN=1
              shift
              ;;
            *)
              shift
              ;;
          esac
        done

        load_local_env() {
          if [ -f "${ROOT_DIR}/.env.local" ]; then
            set -a
            # shellcheck disable=SC1091
            . "${ROOT_DIR}/.env.local"
            set +a
          fi
        }

        require_cmd() {
          if ! command -v "$1" >/dev/null 2>&1; then
            echo "Required command not found: $1" >&2
            exit 1
          fi
        }

        remote_path_for_target() {
          local key="REMOTE_PATH_${TARGET_UPPER}"
          printf '%s\\n' "${!key:-}"
        }

        quote_lftp() {
          local value="$1"
          value="${value//\\\\/\\\\\\\\}"
          value="${value//\\"/\\\\\\"}"
          printf '"%s"' "$value"
        }

        lftp_conn() {
          lftp -u "${USER_NAME},${PASSWORD}" -p "$PORT" "__METHOD__://${HOST}" -e "$1"
        }

        load_local_env
        require_cmd lftp

        if [ -z "$TARGET" ]; then
          echo "Target is required." >&2
          exit 1
        fi

        TARGET_UPPER="$(printf '%s' "$TARGET" | tr '[:lower:]' '[:upper:]')"

        REMOTE_PATH="$(remote_path_for_target)"
        if [ -z "$REMOTE_PATH" ]; then
          echo "Remote path is not set for target ${TARGET}. Fill REMOTE_PATH_${TARGET_UPPER} in .env.local." >&2
          exit 1
        fi

        HOST="${__VAR_PREFIX___HOST:-}"
        PORT="${__VAR_PREFIX___PORT:-__PORT__}"
        USER_NAME="${__VAR_PREFIX___USER:-}"
        PASSWORD="${__VAR_PREFIX___PASS:-}"

        if [ -z "$HOST" ] || [ -z "$USER_NAME" ] || [ -z "$PASSWORD" ]; then
          echo "__VAR_PREFIX___HOST, __VAR_PREFIX___USER, and __VAR_PREFIX___PASS are required in .env.local for __METHOD__ rollback." >&2
          exit 1
        fi

        REMOTE_BACKUP_ROOT="${BACKUP_REMOTE_DIR:-$(dirname "$(dirname "$REMOTE_PATH")")/_backups/__PROJECT_SLUG__}"
        REMOTE_TARGET_DIR="${REMOTE_BACKUP_ROOT%/}/${TARGET}"

        if [ "$BACKUP_ID" = "latest" ]; then
          REMOTE_BACKUP_ID="$(lftp_conn "cls -1 $(quote_lftp "$REMOTE_TARGET_DIR") 2>/dev/null; bye" 2>/dev/null | sort | tail -1 | tr -d '/')"
          if [ -z "$REMOTE_BACKUP_ID" ]; then
            echo "No backup found on server: ${REMOTE_TARGET_DIR}" >&2
            exit 1
          fi
        else
          REMOTE_BACKUP_ID="$BACKUP_ID"
        fi

        REMOTE_BACKUP_PATH="${REMOTE_TARGET_DIR%/}/${REMOTE_BACKUP_ID}"

        echo "Method: __METHOD__"
        echo "Target: $TARGET"
        echo "Server backup: $REMOTE_BACKUP_PATH"
        echo "Remote path: $REMOTE_PATH"

        echo "Listing backup files on server..."
        backup_files="$(lftp_conn "find $(quote_lftp "$REMOTE_BACKUP_PATH"); bye" 2>/dev/null | grep -v '/$' | sed 's|^\\./||')" || true

        if [ -z "$backup_files" ]; then
          echo "Backup is empty or not found: ${REMOTE_BACKUP_PATH}" >&2
          echo "Available backups:"
          lftp_conn "cls -1 $(quote_lftp "$REMOTE_TARGET_DIR") 2>/dev/null; bye" 2>/dev/null | sed 's|/$||; s|^|  |' || echo "  (none)"
          exit 1
        fi

        mv_cmds=""
        while IFS= read -r rel_path; do
          [ -z "$rel_path" ] && continue
          src="${REMOTE_BACKUP_PATH%/}/${rel_path}"
          dest="${REMOTE_PATH%/}/${rel_path}"
          dest_dir="$(dirname "$dest")"
          mv_cmds="${mv_cmds} mkdir -p $(quote_lftp "$dest_dir"); mv $(quote_lftp "$src") $(quote_lftp "$dest");"
        done <<< "$backup_files"

        if [ "$DRY_RUN" -eq 1 ]; then
          echo "[dry-run] Would restore the following files:"
          echo "$backup_files" | sed 's|^|  |'
          exit 0
        fi

        lftp_conn "${mv_cmds} bye"
        echo "Rollback completed."
        """
    ).replace("__METHOD__", method).replace("__PROFILE__", profile).replace("__VAR_PREFIX__", var_prefix).replace("__PORT__", port).replace("__PROJECT_SLUG__", project_slug)


def render_scripts(method: str, source_subdir: str, profile: str, project_slug: str) -> tuple[str, str, str]:
    normalized = normalize_method(method)
    if normalized == "rsync":
        return (
            render_rsync_deploy(source_subdir, profile, project_slug),
            render_rsync_sync(source_subdir, profile),
            render_rsync_rollback(profile, project_slug),
        )
    if normalized in {"ftp", "sftp"}:
        return (
            render_lftp_deploy(normalized, source_subdir, profile, project_slug),
            render_lftp_sync(normalized, source_subdir, profile),
            render_lftp_rollback(normalized, profile, project_slug),
        )
    placeholder = (
        render_placeholder("deploy-project.sh", method),
        render_placeholder("sync-project.sh", method),
        render_placeholder("rollback-project.sh", method),
    )
    return placeholder


def should_overwrite(path: Path) -> bool:
    if not path.exists():
        return True
    text = path.read_text(encoding="utf-8")
    return SETUP_REQUIRED_MARKER in text or AUTO_MARKER in text


def write_if_needed(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not should_overwrite(path):
        return f"skipped {path}"
    path.write_text(content, encoding="utf-8")
    os.chmod(path, 0o755)
    return f"generated {path}"


def resolve_script_path(root: Path, raw_value: str, fallback: str) -> Path:
    target = raw_value or fallback
    path = Path(target)
    if path.is_absolute():
        return path
    return root / target


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deployment helper scripts from .claude/project.config.yaml")
    parser.add_argument("--config", default=".claude/project.config.yaml")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    root_dir = config_path.parent.parent
    config = load_config(config_path)
    env_values = load_env_file(root_dir / ".env.local")
    profile = infer_profile(root_dir, config)
    source_subdir = detect_source_subdir(root_dir, profile)
    method = str(get_value(config, "deployment.method") or env_values.get("DEPLOY_METHOD", ""))
    project_slug = str(get_value(config, "project.slug") or "").strip()
    if not project_slug:
        project_slug = '$(basename "$ROOT_DIR")'

    deploy_content, sync_content, rollback_content = render_scripts(method, source_subdir, profile, project_slug)

    deploy_path = resolve_script_path(root_dir, str(get_value(config, "deployment.deploy_script") or ""), ".scripts/deploy-project.sh")
    sync_path = resolve_script_path(root_dir, str(get_value(config, "deployment.sync_script") or ""), ".scripts/sync-project.sh")
    rollback_path = resolve_script_path(root_dir, str(get_value(config, "deployment.rollback_script") or ""), ".scripts/rollback-project.sh")

    for message in (
        write_if_needed(deploy_path, deploy_content),
        write_if_needed(sync_path, sync_content),
        write_if_needed(rollback_path, rollback_content),
    ):
        print(message)


if __name__ == "__main__":
    main()
