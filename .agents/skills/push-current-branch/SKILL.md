---
name: push-current-branch
description: Use when the user says「pushして」「プッシュして」「共有して」or wants to push the current working branch to origin after checking branch safety and upstream status.
---

# push-current-branch

現在の作業ブランチを安全に push する。

## 手順

1. 現在のブランチ、未コミット差分、upstream 設定の有無を確認する。
2. `bash .scripts/check-branch-sync.sh --branch <current-branch> --fetch` を使い、current branch が remote に対して遅れていないか確認する。
3. `main` または `develop` 上にいる場合は、共有ブランチへの直接 push かを確認する。通常作業なら止める。
4. 未コミット差分がある場合は、そのまま push せず commit / stash / cleanup を案内する。
5. `origin` が未設定なら push しない。
6. upstream がない場合は `git push -u origin <current-branch>`、ある場合は `git push` を使う。
7. push 後は、必要なら merge 前確認やチーム確認へ進む。

## 注意

- feature / hotfix ブランチの共有を優先する。
- 不明な状態で `main` / `develop` を push しない。
