#!/usr/bin/env bash
set -euo pipefail

TARGET="${SYNC_TARGET:-${1:-}}"

cat <<EOF
[SETUP REQUIRED] sync-project.sh
このスクリプトは案件ごとに調整してください。

- target: ${TARGET:-unset}
- method: \${DEPLOY_METHOD:-.claude/project.config.yaml を参照}

推奨:
- SSH / rsync または SFTP でサーバーから取得する
- 一時ファイルや生成物は除外する
- dry-run を先に実行する
EOF

exit 1
