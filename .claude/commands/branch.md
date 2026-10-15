# /branch - 作業ブランチ作成

`rules/git-conventions.md` に沿って、安全な起点から作業ブランチを作成する。

## 手順

1. `git status --short --branch` で現在のブランチと未コミット差分を確認する。
2. 通常作業なら `develop` から `feature/<short-name>`、緊急の本番修正だけ `main` から `hotfix/<short-name>` を使う。
3. 起点ブランチが想定と違う場合は、そのまま branch を切らずに止める。
4. `bash .scripts/check-branch-sync.sh --branch <base-branch> --fetch` を使い、起点ブランチが remote に対して遅れていないか確認する。
5. 起点ブランチが最新化されていない場合は、先に pull を案内する。
6. 説明を英語のケバブケースへ要約する。
7. 同名ブランチがないことを確認する。
8. ユーザー承認後に `git switch -c <branch-name>` を実行する。

## type の目安

- 通常の開発・修正・文書更新: `feature/`
- 緊急の本番修正: `hotfix/`

## 自然文の例

- `ブランチ切って`
- `作業ブランチを作って`
- `〇〇の修正用にブランチ作って`

## 出力

- 提案ブランチ名
- 起点ブランチ
- 先に必要な pull の有無
- 実行コマンド
