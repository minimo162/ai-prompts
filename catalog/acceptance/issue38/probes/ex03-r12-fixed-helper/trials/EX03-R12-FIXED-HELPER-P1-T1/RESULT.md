# Issue #38 EX03 r12 fixed-helper one-run trial

## 判定

`EX03-R12-FIXED-HELPER-P1-T1` は、専用PADフロー `Power Automate | 無題 (14)` へ1回貼付けて保存し、実行前再コピーを1回取得した。再コピーは候補とバイト完全一致しなかったため、既定の停止条件どおりRun前に停止した。PAD Run、launcher/helper実行、Excel操作、数値書込み、SaveAs、成果物照合は0回である。

## 固定SHA-256

| 対象 | SHA-256 |
|---|---|
| helper | `08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135` |
| invocation | `92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6` |
| launcher | `1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1` |
| PAD貼付け候補 | `0a84679b0b9875780aa70c975602a7404af0dd82fcf9b13978fe9c1e036f5b94` |
| PAD保存後再コピー | `da54e5f4388cd0bb896ee00e534e9d81a444f5b950ac1f1bf006f8ea788ad4aa` |
| 原本 / 専用work | `881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21` |

## 返却経路の事前照合

既存stub証拠を再実行せず、実helperの `Write-Output -NoEnumerate`、launcherの `(& $helperPath ... | Out-String).Trim()`、最終 `[Console]::Out.Write($helperOutput)` を照合した。既存正常stubは単一の成功JSONを返す。ただし今回の実経路はRun前停止のため、実helperでの成功JSON・stderr・正常終了は未観測である。

## PAD保存・再コピー

- PAD: `2.71.115.26224`、Power Fx OFF、Main、保存後ステータス READY
- 貼付け1回、保存1回、再コピー1回、Run 0回
- 候補: LF-only 194、最終改行なし
- 再コピー: CRLF 136 + LF-only 59、最終改行あり
- 内容差分: 1 hunk。候補line 48のlauncher `$expectedSuccess` 内のJSON二重引用符8個へ、PADがRobinエスケープ `\"` を付加
- Robinを復号したlauncher本文は一致するが、意味同値をバイト完全一致PASSへ読み替えていない

## 停止時保全

- 専用workは原本と同一SHAのまま
- JSON handoff 8ファイルは不在
- 出力xlsxは不在
- launcher/helper、数値書込み、SaveAsは未進入
- 正式r12、固定依頼・spec・期待値、既存prototype証跡は不変
- GitHub書込みなし

## 未実施・残件

12対象セル、対象外セル、数式、Excel実効書式、F6の `100%` 文字列・元書式・空prefix・数式なしは、成果物がないためすべてNOT_RUN。別途承認された後継試行では、実行前にPAD正規化後とバイト一致する候補表現を固定する必要がある。
