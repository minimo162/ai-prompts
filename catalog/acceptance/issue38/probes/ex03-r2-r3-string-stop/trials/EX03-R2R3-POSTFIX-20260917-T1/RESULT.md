# Issue #38 EX03 R2/R3 postfix 実機試行結果

## 判定

試行 `EX03-R2R3-POSTFIX-20260917-T1` は、承認された正常系1Runと、その正常系PASS・成果物保全後の強制例外系1Runを各1回だけ実行し、`PASS_NORMAL_AND_FORCED_EXCEPTION_ONE_RUN_EACH` となった。

このPASSは、固定3文字列、固定数値 `42.5`、固定セル `A2:D2`、今回のPAD・Excel・Windows PowerShell環境に限る。Copilot送信、EX03統合再試験、候補版作成、全件回帰、GitHub書込みは実施していない。

## 固定SHA-256

| 対象 | SHA-256 |
|---|---|
| 基点コミット | `1f929d6c4e1ba5bc4d963374e3e322c7a52649c1` |
| `source.xlsx` | `74d2f493e8e687859badcb9c0b13ddff54d466c7394c3212e512a050113a2dc4` |
| `template.xlsx` | `108d25e5cfb86cd34422e738f7590d6050933c4f5429c672df65907fb2f31a36` |
| `embedded-safe.ps1.txt` | `aa2091327607b9ed1496f5ebb4a8bca2968e95e56ae3337f541651141e55f571` |
| 固定正常系Robin | `aaac1b7c04156f8038d26f6671c692faede55c91097cbf3f5d4c575348ae3851` |
| 固定負例Robin | `a1ff8f503d485402ffdbb98248a52e62eedf98ac27f95d566dbaca1800dfcd1f` |
| パス分離した正常系Robin | `28f1349b68125ab32e0f2139fb967b91f99377a756f9b8d9bbf1f354c9b5c0e1` |
| パス分離した正常系script | `7e0baed476cd9c2d63264d3ae66af273217c471860a526cb3d855c71dd270ade` |
| パス分離した負例Robin | `d1459baf69c8d412674599f2fbb0dec6772b74e8fd8104c694dcb1cea438599f` |
| パス分離した負例script | `184e03cc6c43ad007c210de85e72adeb185c7bce0c6582f10aa2a4b4950c7087` |
| 正常系 `result.xlsx` / 保全コピー | `a712dffdc1f9d41f0b5e034c1e8366ef4001631f3eb139d5dc8dcbe060464af3` |

各パス分離版は、専用runtime絶対パス11箇所以外を固定版へ戻すとRobin・内包scriptともバイト同一になる。両scriptのPowerShell ASTエラーは0で、禁止トークン検査もPASSした。

## 非ライブ型確認

PADが使用するWindows PowerShell `5.1.26100.9444` (`Desktop`) で、既存実JSON `source-4.json`（SHA-256 `0300d9078e3fc280b8b7f946191afaebf0d3c7f70c9005dbb645e83bb708724a`）を読んだ。値は `42.5`、型は `System.Decimal`、`Double` 判定はfalse、`Decimal` 判定はtrueで、修正済み `Double or Decimal` ゲートはtrueだった。

## PAD保存・再コピー

両専用フローともPower FxはOFF、アクション数は63。貼付け、保存、再コピー、実行は各1回。実行前再コピーは候補とバイト同一だった。

| Run | PADフロー | 再コピーSHA-256 | Run数 |
|---|---|---|---|
| 正常系 | `Power Automate | 無題 (12)` | `28f1349b68125ab32e0f2139fb967b91f99377a756f9b8d9bbf1f354c9b5c0e1` | 1 |
| 強制例外系 | `Power Automate | 無題 (13)` | `d1459baf69c8d412674599f2fbb0dec6772b74e8fd8104c694dcb1cea438599f` | 1 |

## 正常系1Run

- PAD終端: `READY`
- script出力: `{"status":"OK","mode":"NORMAL","text_writes":3,"formats_restored":true}`
- `ProbeState`: `SUCCESS_GATE_PASSED_SAVED_READBACK_READY`
- 成功ゲート、数値書込み、SaveAs: すべて通過
- 再読込: 1行4列、4 sourceとも保存値との比較true

| セル | 保存・再読込値 | COM型 | 元書式との一致 | prefix | 数式 |
|---|---|---|---|---|---|
| A2 | `O'Brien` | `System.String` | `G/標準` = template | 空 | なし |
| B2 | `He said "Go"` + 改行 + `Second line 'quoted'` | `System.String` | `0.00` = template | 空 | なし |
| C2 | `100%` | `System.String` | `G/標準` = template | 空 | なし |
| D2 | `42.5` | `System.Double` | `0.00` = template | 空 | なし |

COM検査は読み取り専用で、検査前後の成果物SHAは同一。別読取りによるxlsx inspectionでも値、空数式、JavaScript型 `string/string/string/number` を確認し、プレビュー画像を目視確認した。最初の読取り専用検査はローカライズ済み表示形式名のコンソール文字化けを検出して受入に使わず、UTF-8 Base64搬送と同一COMによるtemplate/result直接比較へ切り替えた。PADの追加Runはしていない。

## 強制例外系1Run

- 正常系の成果物と同一SHAの保全コピーを確認してから実行した。
- PAD終端: `READY`
- script出力: `{"status":"EXPECTED_ERROR","mode":"INJECT_AFTER_FORMAT_CHANGE","format_restored":true,"value_unchanged":true}`
- `ProbeState`: `SCRIPT_NOT_SUCCESS_NO_SAVE`
- 成功ゲート、後続数値書込み、SaveAs: すべて不通過
- Readback: 0行0列
- `negative/runtime/result.xlsx`: 不在
- `negative/runtime/work.xlsx`: templateと同一SHA `108d25e5cfb86cd34422e738f7590d6050933c4f5429c672df65907fb2f31a36`

例外はA2の一時書式変更直後に意図的に発生させた。scriptはcatch後、元書式、元値と型、prefix、数式有無を直接再検査し、いずれかが変化していれば別のエラーで停止する。PAD実機で上記EXPECTED_ERROR出力を先頭から末尾まで確認したため、事前型チェック停止を途中例外成功へ読み替えていない。

## 保全・残件

- 基点で記録した既存probe 27ファイルのGit blobは全件不変。
- 元試行の失敗、旧版、固定期待値、既存証跡は変更していない。
- 適用範囲は固定データ・固定セル・今回環境のみ。任意文字列や未確認型へ一般化しない。
- Copilot生成フロー、EX03統合、全件回帰、候補版、manifest訂正、GitHub書込みは未実施のまま残す。

## 局所自動検査

- `Test-Issue38Ex03R2R3PostfixTrial.py`: 7/7 PASS
- 既存 `Test-Issue38Ex03R2R3Probe.py`: 13/13 PASS
- 既存 `Test-Issue38Ex03R11FileAuxFinalizer.py`: 9/9 PASS
- Python構文、Node構文、再コピー用PowerShell AST: PASS
