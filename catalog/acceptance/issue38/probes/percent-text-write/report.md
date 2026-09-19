# Issue #38 / EX03 text `100%` write probe

## 結論

ローカル専用probeは `PASS_LOCAL_PROBE_ONLY`。固定文字列 `100%` が数値 `1`・表示形式 `0%` になる原因は、保存・再読込ではなく、PADの通常の「Excelへ書き込み」(`Excel.WriteToExcel.WriteCell`) が宛先セルへ値を渡した時点でExcelの入力解釈を受けることだった。

採用した最小方式は、検証対象の文字列セルだけについて、厳密に一致するアクティブブック・シート・セルへ接続し、元の `NumberFormat` を保存して一時的に `@` とし、`Value2` に文字列を書き、直ちに元の `NumberFormat` へ戻すもの。直後に値、CLR型、表示形式、`PrefixCharacter` を検査している。数値セルは通常の数値書き込みのまま変更していない。

これはEX03/r5への組込みではなく、固定fixture `Source!A2:B2`（文字列 `100%`、数値 `42.5`）だけの実機probe結果である。

## 原因分離

| 候補 | 書込み直後 | 保存・再読込後 | 判定 |
|---|---|---|---|
| 通常のscalar `WriteCell` | A2が `{"probe":1.0}`、sourceとのJSON型照合は `False` | A2の表示形式が `G/標準` から `0%` に変化 | FAIL。変換は保存前に発生 |
| 先頭アポストロフィ | 値・文字列型・表示形式は一致 | `PrefixCharacter="'"` が残る | FAIL。残留文字禁止条件に抵触 |
| 表示形式サンドイッチ | `100%` / `System.String` / `G/標準` / prefix空 | 同じ値・型・表示形式・prefix空 | 採用 |

通常書込みの実測は [candidate-scalar-direct-variables.json](candidate-scalar-direct-variables.json) と [candidate-scalar-direct-style.json](candidate-scalar-direct-style.json)、アポストロフィ候補の拒否根拠は [candidate-prefix-text/verification.json](candidate-prefix-text/verification.json) に保存した。

## 採用Robin

- 実PADから再取得した最終Robin: [captured-final.robin](captured-final.robin)
- SHA-256: `0b86dd150dac532e2c73f5a407a7c396b4153bbc3052e03a65a8c84c6dab6f46`
- 実PADから再取得した採用アクション: [captured-powershell-format-action-v2.robin](captured-powershell-format-action-v2.robin)
- アクションSHA-256: `aae8f3d12b458e7bba0bf7759ad0f2c15720bbc803f032e5c86e3621edc16538`
- Run1/Run2終了後の再コピーRobinはいずれも最終Robinとbyte同一。

採用アクションの直後監査値は両Runとも次のとおり。

```json
{"m":"fmt","b":"BEFORE_TEXT","bt":"System.String","bf":"G/標準","bp":"","a":"100%","at":"System.String","af":"G/標準","ap":""}
```

## 2Run結果

| 項目 | Run1 | Run2 |
|---|---|---|
| source文字列JSON | `{"probe":"100%"}` | 同左 |
| 書込み直後文字列JSON | `{"probe":"100%"}` | 同左 |
| 再読込後文字列JSON | `{"probe":"100%"}` | 同左 |
| source数値JSON | `{"probe":42.5}` | 同左 |
| 書込み直後・再読込後数値JSON | `{"probe":42.5}` | 同左 |
| A2表示形式 / prefix / 数式 | `G/標準` / 空 / なし | 同左 |
| B2表示形式 / 数式 | `0.00` / なし | 同左 |
| Target範囲の実効書式差 | 0 | 0 |
| PAD終了状態 | `TERMINAL_CONFIRMED` | `TERMINAL_CONFIRMED` |
| 成果物SHA-256 | `b980e1060896dcbc78c0cf10f2e1738a8ebc5c6658d98f045a17b306e828b1a3` | `2c9d138133d4f999f4e7d96486995bb1e8726032379feadba5f76f4186e8d39c` |

機械可読の集約は [two-run-result.json](two-run-result.json) と [acceptance.json](acceptance.json)。個別証拠は [run1/verification.json](run1/verification.json)、[run1/style.json](run1/style.json)、[run1/terminal.json](run1/terminal.json)、[run2/verification.json](run2/verification.json)、[run2/style.json](run2/style.json)、[run2/terminal.json](run2/terminal.json) に保存した。Run1は汎用runnerが180秒でタイムアウトしたが、その同一Runについて後続観測で開始ボタン再有効・実行中/エラー表示なし・最終marker・Excel終了・成果物存在を満たしたため、[run1/pad-run-timeout.json](run1/pad-run-timeout.json) を消さず [run1/terminal.json](run1/terminal.json) に別記した。

## 非代替・保全確認

- 全セルの文字列化なし。A2だけが採用方式、B2は通常の数値書込み。
- 数式置換なし。A2/B2とも `has_formula=false`。
- 先頭アポストロフィ等の残留文字なし。
- F6だけの後処理ではなく、専用synthetic source/templateの固定2セルを対象にした独立probe。
- source DataTableと固定期待値は変更していない。
- Robin貼付時のクリップボード復元は、利用者の明示指示に従いこの操作だけ省略した。既定ガード自体は変更していない。記録は [final-paste.json](final-paste.json)。
- r5、既存EX03-r5-G1証跡、候補版は変更していない。
- Copilot再送、EX03全体再実行、GitHub書込みは行っていない。

## 適用限界と残件

- 確認済みは文字列 `100%` と数値 `42.5`、このPAD/Excel環境、この固定セルだけ。空白、真偽値、日付、エラー、数式結果、オブジェクト、別文字列、別PAD版・別PCへ一般化しない。
- 採用PowerShellはprobeの厳密なブックパス、`Target!A2` に固定されており、EX03/r5へは未統合。
- `%SourceText%` の埋込み安全性も固定値 `100%` でのみ確認済み。任意文字列の一般解ではない。
- 以前のEX03-r5-G1 Run終了観測不確実性は別残件のまま。このprobeのRun1後続確認を過去Runへ転用しない。
- よってEX03全体の受入判定は変更しない。本記録が確定したのは原因と、限定された最小書込み方式の2Run成功のみ。
