---
name: sync-from-server
description: Use when the user says「取り込んで」「サーバーから同期して」「ダウンロードして」or asks to sync/download the latest files from DEV, STG, or PROD.
---

# sync-from-server

既存案件のサーバー同期を支援する。

## 手順

1. 発話から対象環境を読む。不明なら質問する。
2. `.claude/project.config.yaml` の `deployment.sync_script` を確認する。
3. 未設定なら、設定不足として止める。
4. 必要なら上書き対象を確認する。
5. `bash .scripts/sync-from-server.sh --target <target>` を実行する。
