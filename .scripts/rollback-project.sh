#!/usr/bin/env bash
set -euo pipefail

TARGET="${ROLLBACK_TARGET:-${1:-}}"
BACKUP_ID="${ROLLBACK_BACKUP_ID:-latest}"

cat <<EOF
[SETUP REQUIRED] rollback-project.sh
このスクリプトは案件ごとに調整してください。

- target: ${TARGET:-unset}
- backup id: ${BACKUP_ID}
- backup dir: ${ROLLBACK_BACKUP_DIR:-unset}

推奨:
- deploy 時にサーバー上に退避したバックアップから戻す
- prod は確認付きで実行する
- dry-run を先に実行する
EOF

exit 1
