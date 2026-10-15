---
name: project-setup
description: Use when the user says「セットアップして」「初期設定して」or wants initial repository setup — filling missing config, organizing deploy settings, and running bootstrap.
---

# project-setup

既存案件の初回セットアップを対話しながら進める。

## 手順

1. `.claude/project.config.yaml` と `doc/project-setup.md` を確認し、必須項目の空欄を洗い出す。
2. 最初に、基本情報が書かれたファイルの有無とパスを一問だけで確認する。
3. 指定されたファイルが自然文の `.md` や `.txt` でも読んでよい。URL、client 名、環境名、repo 名候補などを拾う。
4. 既存案件の実ファイルや必要ディレクトリが揃っているか確認する。
5. 質問は一問一答で進める。1回の返答で複数質問をまとめない。
6. ユーザーが渡した文書から埋められる値があれば先に使う。
7. 回答ごとに `.claude/project.config.yaml` を更新する。

### 必ず聞く項目

8. `project.client`（クライアント名）を聞く。リポジトリの説明文に含める。
9. `project.type`（案件種別）を聞く。
10. `environment.prod_url`（本番URL）を聞く。

### リポジトリ名の自動決定

11. 本番 URL のドメインから `www.` と TLD（`.com`、`.co.jp`、`.jp` 等）を除いてリポジトリ名にする。例: `https://www.heim-k.com/` → `heim-k`。
12. 同名リポジトリが既に存在するか確認する。重複する場合は `[ドメイン]-[案件種別]` を候補として提示し、ユーザーに尋ねる。
13. `project.name`、`project.slug`、`project.client_slug` は本番 URL とクライアント名から推定して埋める。確認は不要。

### 聞かない項目（既定値で自動設定）

14. `repository.visibility` は常に `private`。聞かない。
15. `repository.default_branch` は `main`、`repository.integration_branch` は `develop`。聞かない。
16. Git 未初期化の場合、初回コミット・GitHub リポジトリ作成・push はすべて自動で行う。聞かない。コミットメッセージは `プロジェクトの初期ファイルを追加` を使う。
17. 認証情報が見つかった場合は確認なしで `.env.local` に分離する。FTP / SSH / Basic 認証 / 管理画面の ID・パスワードは `.claude/project.config.yaml` に書き戻さない。

### 任意項目

18. STG / DEV の URL は `STG環境があれば入力してください。あとから設定、もしくはなければスキップしてください。` と案内する。
19. デプロイ設定は `デプロイの設定を今しますか？` と先に聞く。yes の場合だけ `deployment.method`、対象パス、バックアップ方針、ロールバック方針を確認する。`.env.local` に必要な接続情報と `REMOTE_PATH_*` も整理する。

### 仕上げ

20. `repository.owner_name` のデフォルトは `generalasahi-web`（GitHub Organization）。変更指示がない限りそのまま使う。
21. リポジトリの説明文は `<クライアント名> <案件名>` の形式にする。
22. `develop` を使う運用なら、初回セットアップ完了時に local / remote の両方へ `develop` が揃う状態を確認する。
23. GitHub Free の private リポジトリでは GitHub 側の branch protection / rulesets を前提にせず、local の pre-push hook を基本保護として案内する。
24. `bash .scripts/bootstrap.sh` を実行する。
25. `bash .scripts/doctor.sh` を実行する。
26. 生成・更新された文書と反映スクリプトを確認し、残タスクを短くまとめる。`SETUP REQUIRED` が残っている場合は `deployment.method` の未設定または未対応方式として案内する。
