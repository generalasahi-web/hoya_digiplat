---
name: branch-with-rules
description: Use when the user says「ブランチ切って」「作業ブランチを作って」or wants a safe working branch that follows the repository's branch convention and base-branch policy.
---

# branch-with-rules

`rules/git-conventions.md` に沿って、安全な起点からブランチ作成を支援する。

## 手順

1. 現在のブランチと未コミット差分を確認する。
2. 通常作業なら `develop` から `feature/<short-name>`、緊急の本番修正だけ `main` から `hotfix/<short-name>` を使う。
3. 起点ブランチが想定と違う場合は、そのまま作成せずに止める。
4. `bash .scripts/check-branch-sync.sh --branch <base-branch> --fetch` を使い、起点ブランチが remote に対して遅れていないか確認する。
5. 起点ブランチが最新化されていない場合は、先に pull を案内する。
6. 説明を英語のケバブケースに要約する。
7. `<type>/<short-name>` の形式でブランチ名を提案する。
8. 同名ブランチの有無を確認する。
9. ユーザー承認後に `git switch -c <branch-name>` を実行する。
