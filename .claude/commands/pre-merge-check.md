# /pre-merge-check - merge 前の最終確認

`feature` または `hotfix` ブランチを取り込む前のセルフチェックを行う。

## 手順

1. `git status --short --branch` で現在ブランチと未コミット差分を確認する。
2. 現在ブランチが `feature/` なら取り込み先を `develop`、`hotfix/` なら取り込み先を `main` とみなす。判定できない場合は取り込み先を確認する。
3. `main` / `develop` 上で作業している場合はそこで止める。
4. `git diff <target>...HEAD` と `git log --oneline <target>..HEAD` で変更範囲を把握する。
5. `/review` 相当で、既存規約、既存実装パターン、挙動退行、セキュリティ、検証不足を確認する。
6. `/verify` 相当で、利用可能な検証手段を使って確認し、未確認事項を残す。
7. `WIP` コミット、複数目的のコミット、未 push のままの作業、秘密情報混入があれば merge blocker として扱う。
8. `feature -> develop` や `develop -> main` の反映が、チームの確認手順に沿っているか確認する。
9. blocker と手動確認項目を分けて整理し、merge 可否を判定する。

## 自然文の例

- `merge前確認して`
- `マージ前チェックして`
- `取り込み前の確認をして`

## 出力

- 取り込み先ブランチ
- 判定: Ready / Needs fixes / Manual check
- blocker
- 手動確認項目
- 実施した review / verify
- merge 前にやること
