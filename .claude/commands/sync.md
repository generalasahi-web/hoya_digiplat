# /sync - サーバー同期

サーバーからの取り込み依頼を受けた時に、必要な確認をしながら `.scripts/sync-from-server.sh` を実行する。

## 手順

1. 依頼文から対象環境を読む。`DEV / STG / PROD` が不明なら質問する。
2. `.claude/project.config.yaml` の `deployment.sync_script` を確認する。
3. 未設定なら、不足項目を質問する。
4. 破壊的な上書きがありうる場合は、対象ディレクトリとバックアップ方針を確認する。
5. `bash .scripts/sync-from-server.sh --target <target>` を実行する。

## 自然文の例

- `DEVから同期して`
- `サーバーから最新を取り込んで`
- `STGの内容を落として`
