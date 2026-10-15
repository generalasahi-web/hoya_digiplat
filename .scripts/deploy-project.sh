#!/usr/bin/env bash
set -euo pipefail

TARGET="${DEPLOY_TARGET:-${1:-}}"

cat <<EOF
[SETUP REQUIRED] deploy-project.sh
このスクリプトは案件ごとに調整してください。

- target: ${TARGET:-unset}
- method: \${DEPLOY_METHOD:-.claude/project.config.yaml を参照}
- backup dir: ${DEPLOY_BACKUP_DIR:-unset}

推奨:
- SSH / rsync の場合は .env.local の接続情報を読む
- 反映前に変更対象のファイルだけをサーバー内のバックアップフォルダに退避する
- dry-run を先に実行する
EOF

exit 1
