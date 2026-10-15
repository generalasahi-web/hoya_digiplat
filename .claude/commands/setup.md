# /setup - 設定見直し / 再セットアップ

既存案件 repo 作成後の設定見直しや再セットアップを対話しながら進める。`.claude/project.config.yaml` の不足項目を確認し、必要な更新を行ったうえで `.scripts/bootstrap.sh` を実行する。

## 手順

1. `.claude/project.config.yaml` と `doc/project-setup.md` を確認し、初回セットアップに必要な項目を洗い出す。
2. 最初の質問では、`基本情報が書かれたファイルはありますか。あればパスを教えてください` と聞く。
3. 指定されたファイルが `.md`、`.txt`、メモ書きのような自然文でも、その内容から候補値を抽出してよい。
4. 既存案件の実ファイルや必要ディレクトリが揃っているか確認する。
5. 質問は一問一答で進める。1回の返答で複数質問をまとめて出さない。
6. 回答を受け取るたびに `.claude/project.config.yaml` を更新し、次の未入力項目へ進む。

### 必ず聞く項目

7. `project.client`（クライアント名）を聞く。リポジトリの説明文に含める。
8. `project.type`（案件種別）を聞く。
9. `environment.prod_url`（本番URL）を聞く。

### リポジトリ名の自動決定

10. 本番 URL のドメインからリポジトリ名を導出する。`www.` とTLD（`.com`、`.co.jp`、`.jp` 等）を除いた部分を使う。例: `https://www.heim-k.com/` → `heim-k`。
11. 同名リポジトリが既に存在するか `gh repo view <owner>/<repo-name>` で確認する。重複する場合は `[ドメイン]-[案件種別]` を候補として提示し、ユーザーに尋ねる。
12. `project.name` と `project.slug` は本番 URL とクライアント名から推定して埋める。確認は不要。
13. `project.client_slug` はクライアント名から英語ケバブケースで推定して埋める。

### 聞かない項目（既定値で自動設定）

14. `repository.visibility` は常に `private`。聞かない。
15. `repository.default_branch` は `main`、`repository.integration_branch` は `develop`。聞かない。
16. Git 未初期化の場合、初回コミット・GitHub リポジトリ作成・push はすべて自動で行う。聞かない。コミットメッセージは `プロジェクトの初期ファイルを追加` を使う。
17. FTP / SSH / Basic 認証 / 管理画面の ID・パスワードは `.claude/project.config.yaml` に書き戻さない。認証情報が見つかった場合は確認なしで `.env.local` に分離する。`bash .scripts/init-local-env.sh` を実行して `.env.local` を作り、値を転記する。

### 任意項目

18. STG / DEV の URL は `STG環境があれば入力してください。あとから設定、もしくはなければスキップしてください。` と案内する。
19. デプロイ設定は `デプロイの設定を今しますか？` と先に聞く。yes の場合だけ `deployment.method`、対象パス、バックアップ方針、ロールバック方針を確認する。`bootstrap.sh` は `.scripts/deploy-project.sh`、`.scripts/sync-project.sh`、`.scripts/rollback-project.sh` を `deployment.method` に応じて自動生成するため、`.env.local` に必要な接続情報と `REMOTE_PATH_*` も整理する。

### 仕上げ

20. `repository.owner_name` のデフォルトは `generalasahi-web`（GitHub Organization）。変更指示がない限りそのまま使う。
21. リポジトリの説明文は `<クライアント名> <案件名>` の形式にする。
22. `develop` を使う運用なら、初回セットアップ完了時に local / remote の両方へ `develop` が揃う状態を確認する。
23. GitHub Free の private リポジトリでは GitHub 側の branch protection / rulesets を前提にせず、local の pre-push hook を基本保護として案内する。
24. 必須項目がそろったら `bash .scripts/bootstrap.sh` を実行する。
25. `bash .scripts/doctor.sh` を実行し、設定不足や Git / hook の不備がないか診断する。
26. 更新された文書と自動生成された反映スクリプトを確認し、要確認事項を整理する。`SETUP REQUIRED` が残っている場合は `deployment.method` が未設定または未対応なので、その理由を明示する。

## 自然文の例

- `セットアップして`
- `初期設定して`
- `GitHubの準備をして`

## 出力

- 更新した設定項目
- 実行したコマンド
- doctor の診断結果
- 残っている要確認事項
