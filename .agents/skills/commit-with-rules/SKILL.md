---
name: commit-with-rules
description: Use when the user says「コミットして」「規約どおりにコミットして」or wants help creating a commit that follows the repository's convention and git rules.
---

# commit-with-rules

既存案件の慣習と `rules/git-conventions.md` に沿ってコミットを支援する。

## 手順

1. `git status` と差分を確認する。
2. 1コミット1目的になっているかを見る。
3. 履歴に既存ルールがあるか確認する。
4. 既存ルールがなければ、prefix なしで「何をどう変えたか」が分かる具体的な日本語メッセージを提案する。
5. 秘密情報や意図しないファイルが混ざっていないか確認する。
6. ユーザー承認後にコミットする。

## 注意

- `修正` や `fix` のような曖昧なメッセージを避ける。
- force push 前提の運用を勝手に選ばない。
