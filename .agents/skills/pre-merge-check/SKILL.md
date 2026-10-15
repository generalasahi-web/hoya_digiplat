---
name: pre-merge-check
description: Use when the user says「merge前確認して」「マージ前チェックして」or wants a final self-check before merging a feature or hotfix branch.
---

# pre-merge-check

`feature` または `hotfix` を取り込む前の最終確認を行う。

## 手順

1. 現在ブランチと未コミット差分を確認する。
2. 現在ブランチが `feature/` なら取り込み先を `develop`、`hotfix/` なら取り込み先を `main` とみなす。判定できない場合は取り込み先を確認する。
3. `main` / `develop` 上で作業している場合は止める。
4. `git diff <target>...HEAD` と `git log --oneline <target>..HEAD` で変更範囲を把握する。
5. 既存規約、既存実装パターン、挙動退行、セキュリティ、検証不足を優先して確認する。
6. 利用可能な検証手段を使って確認し、未確認事項を残す。
7. `WIP` コミット、複数目的のコミット、未 push のままの作業、秘密情報混入があれば blocker として扱う。
8. `feature -> develop`、`develop -> main` の反映手順がチームルールに沿っているか確認する。
9. blocker と手動確認項目を分けて、merge 可否を判定する。

## 出力

- 取り込み先ブランチ
- 判定: Ready / Needs fixes / Manual check
- blocker
- 手動確認項目
- 実施した確認
- merge 前にやること
