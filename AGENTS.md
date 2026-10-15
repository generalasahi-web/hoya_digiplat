# AGENTS.md
<!-- PROJECT: プロジェクト名を記入 -->
<!-- STACK: 未調査 -->

> GitHub運用導入用の配布テンプレート
> 対応ツール: OpenAI Codex CLI / Claude Code

## Response language & style

- 返答は日本語。
- 既存ルールがあればそれを優先する。
- 明示されていない大規模刷新は提案止まりにする。
- 推定に自信がない項目は `要確認` と明記する。

## Reference order

1. 既存案件の README / CONTRIBUTING / 運用ドキュメント
2. チームの Git / GitHub 運用資料
3. 設定ファイル（`.editorconfig`, lint, formatter, build 設定, CI 設定）
4. 変更対象周辺の既存実装
5. `CLAUDE.md` とこの `AGENTS.md` の調査結果
6. このテンプレートの規約ファイル

## Working rules

- 既存プロジェクトの構造を壊さない。
- FLOCSS や特定フレームワーク前提の判断を持ち込まない。
- Git 運用は `rules/git-conventions.md` を正本とする。
- 自然文の依頼が既存 skill に対応する場合は、その workflow を優先する。
  例: 「セットアップして」=`$project-setup`、「ブランチ切って」=`$branch-with-rules`、「コミットして」=`$commit-with-rules`、「pushして」=`$push-current-branch`、「merge前確認して」=`$pre-merge-check`、「反映して」「アップロードして」=`$deploy-project`、「取り込んで」=`$sync-from-server`、「戻して」=`$rollback-project`
- 通常作業は `develop` から `feature/xxx`、緊急修正だけ `main` から `hotfix/xxx` を標準にする。
- ブランチ作成前に、起点ブランチが正しいことと最新化済みであることを確認する。
- コミットは 1 目的ごとに区切り、曖昧なメッセージを避ける。
- `main` / `develop` への直接コミット、直接 push、強制 push、広範囲削除は承認なしで行わない。
- `--no-verify`（`-n`）で hook をスキップしない。hook エラーは原因を調べて正しく対処する。
- `bash .scripts/check-branch-sync.sh --branch <base-branch> --fetch` を使い、作業開始前に base branch が remote に対して遅れていないか確認する。
- `main` / `develop` への commit は pre-commit hook で既定拒否する。承認済みの最終反映だけ一時解除する。
- `main` / `develop` への push は pre-push hook で既定拒否する。承認済みの最終反映だけ一時解除する。
- GitHub Free の private リポジトリでは GitHub 側の branch protection / rulesets を前提にしない。
- 作業中の発見は `MEMORY.md` に一時記録し、確定後に正本へ移す。
- 差分レビューでは correctness、security、behavior regression、missing tests を優先する。

## Auto survey summary

`.scripts/project_survey.py` はこのセクション内だけを更新する。

### Project overview
<!-- survey:start:project-overview -->
未調査
<!-- survey:end:project-overview -->

### Tech stack
<!-- survey:start:tech-stack -->
未調査
<!-- survey:end:tech-stack -->

### Directory structure
<!-- survey:start:directory-structure -->
未調査
<!-- survey:end:directory-structure -->

### Detected conventions
<!-- survey:start:detected-conventions -->
未調査
<!-- survey:end:detected-conventions -->

### Available verification
<!-- survey:start:available-verification -->
未調査
<!-- survey:end:available-verification -->

### Environment summary
<!-- survey:start:environment-summary -->
未調査
<!-- survey:end:environment-summary -->

### Deployment summary
<!-- survey:start:deployment-summary -->
未調査
<!-- survey:end:deployment-summary -->

### Open questions
<!-- survey:start:open-questions -->
未調査
<!-- survey:end:open-questions -->

## Codex workflow

- built-in は `/plan`、`/review`、`/diff`、`/permissions`、`/status`、`/skills` を優先する。
- repo skill は `.agents/skills/` に置く。確実に使いたい操作は `$skill-name` で明示起動する。
- `README.md` にある自然文の依頼例は、そのまま該当 skill の入口として扱ってよい。
- GitHub 基本運用では `$branch-with-rules`、`$commit-with-rules`、`$push-current-branch`、`$pre-merge-check` を優先する。
- Claude command / Codex skill の対応正本は `README.md`。追加・改名時は `.claude/commands/` と `.agents/skills/` を同時更新する。

## Available skills

- `$project-setup`
- `$branch-with-rules`
- `$commit-with-rules`
- `$push-current-branch`
- `$pre-merge-check`
- `$sync-from-server`
- `$deploy-project`
- `$rollback-project`
