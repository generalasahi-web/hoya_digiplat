# CLAUDE.md
<!-- PROJECT: プロジェクト名を記入 -->
<!-- STACK: 未調査 -->

## Response language & style

- 返答は日本語。
- 既存のコーディング規約、命名規則、ディレクトリ構成を尊重する。
- 仕様にない改善は提案してよいが、勝手に大規模変更しない。
- 明示ルールがない場合のみ、既存実装からパターンを推定する。

## Operating rules

- 既存案件の正本は、その案件の README、運用ドキュメント、設定ファイル、既存実装。
- CSS、JS、テンプレート、PHP の設計流儀を新しく持ち込まない。
- Git 運用の fallback は `rules/git-conventions.md` を参照する。
- 自然文の依頼が既存 command に対応する場合は、その workflow を優先する。
  例: 「セットアップして」=`/setup`、「ブランチ切って」=`/branch`、「コミットして」=`/commit`、「pushして」=`/push`、「merge前確認して」=`/pre-merge-check`、「反映して」「アップロードして」=`/deploy`、「取り込んで」=`/sync`、「戻して」=`/rollback`
- 大規模なリネーム、CSS 再編、フォルダ移動、ビルド更新は承認なしに行わない。
- 作業中の発見や暗黙知は一時的に `MEMORY.md` へ記録し、確定後に正本へ移す。

## Git workflow

- `main`: 公開中または安定版。通常作業を直接入れない。
- `develop`: 日常の作業を集約するブランチ。通常の作業開始地点にする。
- 通常の開発・修正・文書更新は `develop` から `feature/xxx` を切る。
- 緊急の本番修正だけ `main` から `hotfix/xxx` を切る。
- ブランチ作成前に、現在ブランチと pull 済みかを確認する。
- `bash .scripts/check-branch-sync.sh --branch <base-branch> --fetch` を使い、作業開始前に base branch が remote に対して遅れていないか確認する。
- コミットは 1 目的ごとに区切り、曖昧なメッセージを避ける。
- コミット後は作業ブランチを push して共有する。
- `feature -> develop`、`develop -> main` の merge は、チームで決めた確認手順と承認に従う。
- `reset`、`force push`、共有ブランチ削除、`main` / `develop` への直接 push は承認必須とする。
- `--no-verify`（`-n`）で hook をスキップしない。hook エラーは原因を調べて正しく対処する。
- `main` / `develop` への commit は pre-commit hook で既定拒否する。承認済みの最終反映だけ一時解除する。
- `main` / `develop` への push は pre-push hook で既定拒否する。承認済みの最終反映だけ一時解除する。
- GitHub Free の private リポジトリでは GitHub 側の branch protection / rulesets を前提にしない。

## 自動更新セクション

`.scripts/project_survey.py` はこのセクション内だけを更新する。人間の追記は他セクションへ書くこと。

### プロジェクト概要
<!-- survey:start:project-overview -->
未調査
<!-- survey:end:project-overview -->

### 技術スタック
<!-- survey:start:tech-stack -->
未調査
<!-- survey:end:tech-stack -->

### ディレクトリ構成
<!-- survey:start:directory-structure -->
未調査
<!-- survey:end:directory-structure -->

### 検出した規約
<!-- survey:start:detected-conventions -->
未調査
<!-- survey:end:detected-conventions -->

### 利用可能な検証手段
<!-- survey:start:available-verification -->
未調査
<!-- survey:end:available-verification -->

### 環境情報
<!-- survey:start:environment-summary -->
未調査
<!-- survey:end:environment-summary -->

### デプロイ情報
<!-- survey:start:deployment-summary -->
未調査
<!-- survey:end:deployment-summary -->

### 要確認事項
<!-- survey:start:open-questions -->
未調査
<!-- survey:end:open-questions -->

## 人間メモ

### 注意事項

- プロジェクト固有の地雷や運用上の注意を書く。

### 相談先

- Git / GitHub の承認者、相談先、merge 担当者を書く。

### 承認必須の操作

- `main` / `develop` への直接 push
- `feature -> develop`、`develop -> main` の最終反映
- 本番反映
- 強制 push、リセット、ブランチ削除
- 大量リネーム
- 依存関係の追加や更新

## 利用可能なコマンド

- `/setup`
- `/branch`
- `/commit`
- `/push`
- `/pre-merge-check`
- `/sync`
- `/deploy`
- `/rollback`
