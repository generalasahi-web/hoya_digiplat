# /rollback - バックアップから戻す

反映後の不具合や事故時に、バックアップから戻すための確認と実行を行う。

## 手順

1. 依頼文から対象環境を読む。`DEV / STG / PROD` が不明なら質問する。
2. `1つ前`、`latest`、`2026-04-05 のバックアップ` のような指定から戻し先を解釈する。
3. `.claude/project.config.yaml` の `deployment.rollback_script` と `deployment.backup_*` を確認する。
4. サーバー上のバックアップから復元する。
5. `PROD` の場合は必ず最終確認を入れる。必要なら先に `--dry-run` を提案する。
6. `bash .scripts/rollback.sh --target <target> --backup-id <id>` を実行する。

## 自然文の例

- `STGを1つ前に戻して`
- `本番をロールバックして`
- `DEVを latest バックアップへ戻して`
- `DEV を 2026-04-05 のバックアップまで戻して`
