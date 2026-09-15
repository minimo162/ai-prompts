# Issue #38 / EX02 Excel DataTableセル型照合probe

**判定: Excel由来DataTableセルの型照合はPASS。EX02全体は未受入のまま。** 合成Excelの同表示値について、A2の数値`1`は`{"probe":1.0}`、B2の文字列`"1"`は`{"probe":"1"}`としてPAD内で区別された。同じ保存済みフローを2回実行し、正例2件はTrue、交差する負例2件はFalseで一致した。

## 範囲とfixture

- 基点は`dd505d8c31b8788ab95a3fd39f373bbe294473d9`。前probeのスカラー値を再採取せず、そのコミットで成功した「同じキーのカスタムオブジェクトへ包んでJSON化する」方式だけを参照した。
- [synthetic.xlsx](synthetic.xlsx)の`TypeProbe!A2:B2`を使用。A2はOpen XMLの`t="n"`・値`1`・表示形式`0`、B2は`t="str"`・値`1`・表示形式`@`。[fixture型記録](workbook-source-types.json)ではArtifact Tool再読込もA2=`number`、B2=`string`だった。
- このprobeが証明するのは上記2セルを現在のPADで読み取った範囲だけ。全12セル、転記先、保存・再読込、EX02全体には一般化しない。

## 読取設定

| 項目 | 設定 |
|---|---|
| Excel起動 | `LaunchAndOpenUnderExistingProcess` |
| 読取専用 | `ReadOnly: True` |
| マシンロケール | `UseMachineLocale: False` |
| シート | `ActivateWorksheetByName` / `TypeProbe` |
| 範囲 | `A2:B2` |
| セル内容 | `Excel.GetCellContentsMode.TypedValues` |
| 先頭行をヘッダー扱い | `False` |
| DataTable抽出 | `ExcelData[0][0]`、`ExcelData[0][1]`。変換アクションなし |
| Excel終了 | 保存せず`Excel.CloseExcel.Close` |

## PADから採取した最終Robin

[captured-final.robin](captured-final.robin)は17アクション、UTF-8 BOMなし、CRLFのみ、末尾CRLFあり、1457バイト。SHA-256は`02d664b5ae246bd57e2b44d454a5cd3cb01991a78b6fff8548d208759f1b1fb6`。Run1後・Run2後の再コピーも同じSHAかつ生バイト一致だった。

```text
Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38\\probes\\datatable-type-identity\\synthetic.xlsx''' Visible: True ReadOnly: True UseMachineLocale: False Instance=> ExcelInstance
Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: ExcelInstance Name: $'''TypeProbe'''
Excel.ReadFromExcel.ReadCells Instance: ExcelInstance StartColumn: $'''A''' StartRow: 2 EndColumn: $'''B''' EndRow: 2 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> ExcelData
Excel.CloseExcel.Close Instance: ExcelInstance
SET ExcelNumber TO ExcelData[0][0]
SET ExcelText TO ExcelData[0][1]
SET KnownNumber TO 1
SET KnownText TO $'''%'1'%'''
Variables.ConvertCustomObjectToJson CustomObject: { 'probe': ExcelNumber } Json=> ExcelNumberJson
Variables.ConvertCustomObjectToJson CustomObject: { 'probe': ExcelText } Json=> ExcelTextJson
Variables.ConvertCustomObjectToJson CustomObject: { 'probe': KnownNumber } Json=> KnownNumberJson
Variables.ConvertCustomObjectToJson CustomObject: { 'probe': KnownText } Json=> KnownTextJson
SET PositiveExcelNumber TO ExcelNumberJson = KnownNumberJson
SET PositiveExcelText TO ExcelTextJson = KnownTextJson
SET NegativeExcelNumberText TO ExcelNumberJson = KnownTextJson
SET NegativeExcelTextNumber TO ExcelTextJson = KnownNumberJson
SET DataTableProbeCompleted TO $'''DATATABLE_TYPE_PROBE_FINISHED'''
```

## 2回の実行結果

| セル／PAD比較 | 事前期待 | Run1 | Run2 | 判定 |
|---|---:|---:|---:|---|
| A2 → `ExcelData[0][0]` → JSON | `{"probe":1.0}` | `{"probe":1.0}` | `{"probe":1.0}` | 数値identity保持 |
| B2 → `ExcelData[0][1]` → JSON | `{"probe":"1"}` | `{"probe":"1"}` | `{"probe":"1"}` | 文字列identity保持 |
| `PositiveExcelNumber` | True | True | True | 正例PASS |
| `PositiveExcelText` | True | True | True | 正例PASS |
| `NegativeExcelNumberText` | False | False | False | 交差負例PASS |
| `NegativeExcelTextNumber` | False | False | False | 交差負例PASS |
| 終端マーカー | `DATATABLE_TYPE_PROBE_FINISHED` | 一致 | 一致 | 最終アクション到達 |

- Run1: [実行記録](run1.json)、[名前付き全変数](run1-variables.json)、[固定期待値との照合](run1-reconciliation.json)、[終了状態](run1-terminal-state.json)。Run1証跡を保存・照合し、[Run2前状態](pre-run2-state.json)で変数プレビュー0件を確認してからRun2を開始した。
- Run2: [実行記録](run2.json)、[名前付き全変数](run2-variables.json)、[固定期待値との照合](run2-reconciliation.json)、[終了状態](run2-terminal-state.json)。両Run後にPADは準備完了へ戻り、Excelプロセスは残っていなかった。
- `Run-PadFlowLive.ps1`の即時一覧は仮想化により3変数だけだったため、各Run後に変数検索欄へ15変数名を個別指定し、`VariablePreviewTextBlock`の表示値とヘルプ値が一致することを確認して保存した。

## 組立て時の不採用状態とクリップボード

最初の保全付き貼付けは`PAD_CLIPBOARD: unsupported native format; paste refused`で、クリップボード変更・貼付け・実行前に停止した。その後、利用者からこの作業では元のクリップボード内容を残さなくてよいとの明示指示を受け、共有ガードは変更せず直接上書きした。

先に保存した2アクションの後へ残り15行を貼った際、PADが選択行の前へ挿入してシート選択を末尾へ移した。この状態は[captured-preorder-not-run.robin](captured-preorder-not-run.robin)へ保存し、**実行回数0**。専用新規flowだけを空にし、固定済み17行を正順で貼り直した。実行したのは[captured-final.robin](captured-final.robin)だけで2回。詳細は[flow-construction.json](flow-construction.json)と[capture-integrity.json](capture-integrity.json)に記録した。

クリップボード元内容の保全は、今回の明示条件に従い実施していない。これは技術的合否条件からも除外し、共有ガード自体の変更や一般化はしていない。

## 保全、限界、次の最小作業

r4と既存`type-identity`証跡は基点コミットから差分0。新版作成、EX02全体の再実行、GitHubへのpush・PR・Issue書込みは行っていない。型消失がなかったため、読取設定を変えた別probeも作っていない。

次の最小作業は、**保存・再読込後のEX02 source/target全対象セルへ、今回確認したJSON identity比較を接続し、固定期待値の正例・負例を含めて2回実行すること**。そこまで完了するまではEX02全体をPASSにしない。

機械可読の最終監査は[acceptance.json](acceptance.json)を参照。ローカルコミットSHAは、この報告を含むコミットとして最終応答で示す。
