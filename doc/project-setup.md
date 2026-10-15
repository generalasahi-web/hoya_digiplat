# 案件セットアップ手順

配布用テンプレートを既存案件へ後付け導入する時の標準手順です。

## 1. ファイルを配置する

1. 既存案件のルートへ、このテンプレートのファイルを追加またはマージする。
2. 既存の `.gitignore` や設定ファイルは、上書きではなく必要差分だけ取り込む。
3. 案件メモがあれば `基本情報.md` または `doc/基本情報.md` に置く。

## 2. 設定見直しを実行する

- Claude なら「セットアップして」または `/setup`
- Codex なら「セットアップして」または `$project-setup`

確実に command / skill を使いたい場合は、上記の明示名を使う。

セットアップでは次を一問一答で整理する。

- `.claude/project.config.yaml` の不足項目
- GitHub owner / repo 名 / 公開範囲
- `repository.default_branch` と `repository.integration_branch`
- Git 未初期化なら、初回コミットと `develop` ブランチ作成をその場で行うか
- GitHub remote が未作成なら、その場でリポジトリ作成と初回 push を行うか
- PROD / STG URL
- deploy / sync / rollback の対象パス
- バックアップ方針とロールバック方針
- 機密情報を `.env.local` へ分離するか

自然文の `.md` や `.txt` メモでも読める。
FTP / SSH / Basic 認証 / 管理画面の ID・パスワードは Git 管理ファイルへ転記しない。
必要なら `bash .scripts/init-local-env.sh` で `.env.local` を作る。

GitHub を使う場合の標準:

- 通常作業は `develop` から `feature/xxx`
- 緊急修正だけ `main` から `hotfix/xxx`
- `main` / `develop` への反映は、チームの確認手順と承認に従う
- 初回セットアップで Git 未初期化なら、`main` の初回コミット後に `develop` を作成し、必要なら remote へも push する
- ブランチ作成前は `bash .scripts/check-branch-sync.sh --branch develop --fetch` で `develop` が古くないか確認する
- GitHub Free の private リポジトリでは GitHub 側の branch protection / rulesets を使えない前提で、local の pre-push hook を基本の保護にする

## 3. bootstrap と doctor を実行する

```bash
bash .scripts/bootstrap.sh
bash .scripts/doctor.sh
```

- `bootstrap.sh` は survey、hook 同期、必要なら Git 初期化、deploy / sync / rollback スクリプト生成までまとめて行う。
- `doctor.sh` は設定不足、Git 状態、ブランチ運用、反映スクリプトの未生成や未対応方式を確認する。
- まずは GitHub 基本運用を整え、deploy 系は必要時に有効化する。

## 4. survey 結果を確認する

確認対象:

- `CLAUDE.md`
- `AGENTS.md`
- `doc/repo-survey.md`

特に以下を人間が補完する。

- 相談先
- merge / release の承認者
- クライアント固有ルール
- deploy 時の注意
- 既存コード上の地雷

## 5. 運用開始

- 状態確認は `bash .scripts/doctor.sh`
- ブランチ作成は `/branch` または `$branch-with-rules`
- レビューや検証整理は自然文で依頼する
- コミットは `/commit` または `$commit-with-rules`
- push は `/push` または `$push-current-branch`
- merge 前確認は `/pre-merge-check` または `$pre-merge-check`
- サーバーからの取り込みは `/sync` または `$sync-from-server`
- 反映は `/deploy` または `$deploy-project`
- 戻しは `/rollback` または `$rollback-project`

反映時は、意図した配置先かを確認し、既存ファイルをバックアップへ退避してからアップロードする。
`main` / `develop` への commit / push は pre-commit / pre-push hook が既定で止めるため、承認済みの最終反映だけ一時解除する。公開リポジトリや有料プランでは、GitHub 側の保護設定も追加してよい。
