---
name: rollback-project
description: Use when the user says「戻して」「ロールバックして」「前の状態に戻して」or wants to restore DEV, STG, or PROD from a backup via the configured rollback script.
---

# rollback-project

既存案件のロールバックを支援する。

## 手順

1. 発話から対象環境を読む。不明なら質問する。
2. `1つ前`、`latest`、日付つき指定から戻すバックアップを解釈する。曖昧なら確認する。
3. `.claude/project.config.yaml` の `deployment.rollback_script` と `deployment.backup_*` を確認する。
4. サーバー上のバックアップから復元する。
5. `PROD` は必ず最終確認を入れる。
6. `bash .scripts/rollback.sh --target <target> --backup-id <id>` を実行する。
