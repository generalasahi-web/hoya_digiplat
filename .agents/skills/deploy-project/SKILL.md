---
name: deploy-project
description: Use when the user says「反映して」「デプロイして」「アップロードして」or asks to upload/deploy changes to DEV, STG, or PROD via the configured deployment script.
---

# deploy-project

既存案件のアップロードやデプロイを支援する。

## 手順

1. 発話から対象環境を読む。不明なら質問する。
2. `.claude/project.config.yaml` の `deployment.*` を確認する。
3. `deployment.deploy_script`、対象パス、接続方法が未設定なら、設定不足として止める。
4. 意図した配置先かを確認する。
5. `deployment.backup_before_deploy` が有効なら、変更対象のファイルだけをサーバー内のバックアップフォルダに退避する前提で進める。
6. `PROD` は必ず最終確認を入れる。
7. `bash .scripts/deploy.sh --target <target>` を実行する。
