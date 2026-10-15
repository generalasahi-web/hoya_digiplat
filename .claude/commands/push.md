# /push - 現在ブランチを共有

現在の作業ブランチを、安全性を確認しながら origin へ push する。

## 手順

1. `git status --short --branch` で現在のブランチと未コミット差分を確認する。
2. `bash .scripts/check-branch-sync.sh --branch <current-branch> --fetch` を使い、current branch が remote に対して遅れていないか確認する。
3. `main` または `develop` にいる場合は、共有ブランチへの直接 push かを確認し、通常作業なら止める。
4. 未コミット差分がある場合は、そのまま push せず commit / stash / cleanup を案内する。
5. `origin` の有無と upstream の有無を確認する。
6. upstream がなければ `git push -u origin <current-branch>`、ある場合は `git push` を使う。
7. push 後は、必要なら `/pre-merge-check` やチーム確認へ進む。

## 自然文の例

- `pushして`
- `プッシュして`
- `共有して`

## 出力

- 現在のブランチ
- 未コミット差分の有無
- 実行する push コマンド
- push 後の次アクション
