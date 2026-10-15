# /deploy - 反映実行

アップロードやデプロイの依頼を受けた時に、必要な確認をしながら `.scripts/deploy.sh` を実行する。

## 手順

1. 依頼文から対象環境を読む。`DEV / STG / PROD` が不明なら質問する。
2. `.claude/project.config.yaml` の `deployment.*` を確認する。
3. `deployment.deploy_script`、対象パス、接続方法が未設定なら、不足項目を質問する。
4. 意図した配置先かを確認する。
5. `deployment.backup_before_deploy` が `true` なら、変更対象のファイルだけがサーバー内のバックアップフォルダに退避される前提であることを確認する。
6. `PROD` の場合は必ず最終確認を入れる。必要なら先に `--dry-run` を提案する。
7. 未コミット変更や反映対象の意図を確認する。
8. `bash .scripts/deploy.sh --target <target>` を実行する。

## 自然文の例

- `DEVにアップロードして`
- `STGへ反映して`
- `デプロイして`
- `本番にアップロードして`
