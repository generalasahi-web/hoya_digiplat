#  <br> ⚠️  <br>こちらデプロイやバックアップ関連の処理に不具合があったため、現在修正中です。<br>利用は控えてください。<br>  


# GitHub運用導入テンプレート

既存の `public_html` など実ファイルを置いた案件へ、Git / GitHub の基本運用を後付け導入するためのテンプレートです。

## 最初の入口

- Codex には「セットアップして」または `$project-setup`
- Claude には「セットアップして」または `/setup`

自然文でもよいですが、確実に同じ workflow を使いたい時は明示名を使います。

## セットアップでやること

1. `.claude/project.config.yaml` の不足項目を埋める
2. 必要なら `.env.local` を作り、機密情報を Git 管理外へ逃がす
3. Git 未初期化なら初回コミットを作る
4. GitHub remote が未作成ならリポジトリを作る
5. `main` と `develop` の運用をそろえる
6. `bash .scripts/bootstrap.sh`
7. `bash .scripts/doctor.sh`

## 標準ルール

- 通常作業は `develop` から `feature/<short-name>`
- 緊急修正だけ `main` から `hotfix/<short-name>`
- `main` / `develop` へ直接コミットしない
- 作業前に `develop` が remote に対して遅れていないか確認する
- コミットは 1 目的ごとに分ける
- コミットメッセージは具体的な日本語 1 行で書く
- `feature -> develop`、`develop -> main` は承認手順に従う

詳しくは `rules/git-conventions.md` と `doc/project-setup.md` を参照します。

## よく使う依頼

- 「セットアップして」: 初回設定、GitHub repo 作成、hook 同期、doctor 実行
- 「作業ブランチを切って」: `$branch-with-rules` / `/branch`
- 「規約どおりにコミットして」: `$commit-with-rules` / `/commit`
- 「pushして」: `$push-current-branch` / `/push`
- 「merge前確認して」: `$pre-merge-check` / `/pre-merge-check`

## 保護ブランチの commit / push

GitHub Free の private リポジトリでは、GitHub 側の branch protection / rulesets を使えないため、`main` / `develop` への commit / push は local hook で止めます。
承認済みの最終反映だけ、一時的に解除します。

```bash
ALLOW_PROTECTED_COMMIT=1 git commit ...
```

または merge 時:

```bash
ALLOW_PROTECTED_BRANCH_OPS=1 git merge ...
```

```bash
ALLOW_PROTECTED_PUSH=1 git push ...
```

または

```bash
git config hooks.allowProtectedPush true
git push ...
git config --unset hooks.allowProtectedPush
```

公開リポジトリや有料プランで GitHub 側の保護が使える場合は、そちらも追加して二重で守る運用にしてよいです。

## 配布時の最低確認

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `doc/project-setup.md`
- `.claude/project.config.yaml`
- `.githooks/commit-msg`
- `.githooks/pre-commit`
- `.githooks/pre-push`
- `.scripts/check-branch-sync.sh`
