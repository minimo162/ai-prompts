# Issue #38 EX03 r12 fixed-helper saved-flow T2 auxiliary Run

## 判定

`EX03-R12-FIXED-HELPER-P1-T2` は、T1で保存された専用フローを再貼付け・再保存せず正常系1Runした補助試験である。PAD終了、固定成功JSON、12件のPAD内値・型照合、保存xlsxの固定比較はPASSした。正式EX03-r12受入には転用しない。

## 実行対象の同一性

- 現在のPAD再コピーはT1原文SHA `da54e5f4388cd0bb896ee00e534e9d81a444f5b950ac1f1bf006f8ea788ad4aa` とバイト一致
- 既知差分はlauncher成功JSONの引用符エスケープ1 hunkと改行表現のみ
- 未知差分0、復号後launcher・他処理は固定内容と一致
- helper `08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135`
- invocation `92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6`
- launcher `1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1`
- 実行用パスはT1の固定パスのまま

## PAD観測

- 再貼付け0、再保存0、確認再コピー1、Run 1
- `PowershellOutput`: `{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}`
- `TransferState`: `SAVED_REOPENED_12_JSON_COMPARISONS_READY`
- `ValueTypeMatch`: 12 true / 0 false
- 終了状態 READY、Run有効、Stop無効、Designerエラーなし
- 保存Robinは別stderr変数を持たないため、stderr空は直接断定しない。固定スクリプトに明示stderr出力はなく、成功JSON・fail-closed gate・正常終了を観測した。

## 成果物照合

- result SHA-256 `e3f631f305389229edd5505e922263dc2d4cf1ca9325267cf7483d2ea5502ded`
- 12対象セル: 値・型・位置 mismatch 0
- 対象外468セル: 値・型・数式 mismatch 0
- Excel実効書式: 480セル、48行、30列、差分0
- F6: `100%` / `System.String` / `G/標準` / prefix空 / 数式なし
- 原本入力・ひな形SHA不変、workはひな形と同一
- 旧raw比較の558差分（style 480、row 48、column 30）は別記録として保持

## 保全と境界

- T1 FAIL・Run 0記録、正式r12、固定依頼・期待値は不変
- runtime出力とJSON handoffはT2証跡へ移動保全し、T1 runtimeをworkのみの事前状態へ戻した
- Copilot送信、正式EX03再試験、候補版作成、追加Run、GitHub書込みなし
