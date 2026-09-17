# Issue #38 EX03 R2/R3 局所probe結果

## 結論

正常系1Runは、文字列受渡しではなく数値JSONのPowerShell型判定で停止した。停止ゲートは意図どおり働き、後続数値書込みとSaveAsは未進入、完成出力は不在、`runtime/work.xlsx` はテンプレートと同一SHAのままだった。固定停止条件に従い、負例Runと修正後のライブ再実行は行っていない。そのため、この局所probeの実機受入は未完了である。

原因は、PADが生成した `{"probe":42.5}` をWindows PowerShell 5.1の `ConvertFrom-Json` が `System.Decimal` に復元する一方、ライブ実行に使ったscriptが `System.Double` だけを許していたことである。局所修正では、実測済みの `System.Decimal` と既存の `System.Double` のみを許可した。任意の数値型へ一般化していない。

## 固定境界

- 起点: `f8765ea42e71e43d4924a6f8101b5950db31868c`
- r11、固定依頼、固定期待値、既存証跡は変更していない。
- Copilot送信、EX03統合再試験、候補版作成、全件回帰、manifest訂正、GitHub書込みは実施していない。
- 専用PAD: `Power Automate | 無題 (11)`、window id `105976394`、Power Fx無効、63アクション。

## 非ライブ安全検査

- r11方式へ `O'Brien`、引用符・改行を含む文字列、`100%` を補間した未実行scriptはASTエラー7件で拒否した。
- 修正方式はPADの `ConvertCustomObjectToJson` からUTF-8固定ファイルへ書き、PowerShellが `Get-Content -Raw | ConvertFrom-Json` で読む。データ値はPowerShellソースへ補間しない。
- 安全scriptはASTエラー0、PADデータplaceholder 0、固定JSON読取り5件。
- `PowershellOutput` の完全一致と `RunMode=NORMAL` の二重ゲート内にだけ、数値書込み1件とSaveAs 1件がある。欠落、空文字、`ERROR`、負例modeはいずれもゲートを通らない。
- 初回貼付け元RobinのSHA-256は `d59787268539d20318190caa9309a4ee50221502f222433cd6fff986f96ec0c3`。PAD再コピーは、63アクション境界のLFをCRLFへ変え、成功JSONリテラルの引用符12個を `\"` へ直列化したため、最初のbyte比較は不一致だった。処理ロジックは不変であることを機械確認し、ローカル候補をPAD正規形へ再生成した。実行前の再比較はbyte一致し、ライブ使用・保存後再コピー・現行 `candidate-normal.robin` のSHA-256はいずれも `a9ba6694b40840a7583c5c61cf2f46a5cc7a279a337b69bfcfa23523430d2e9d`。

## PADが実際に生成したJSON

全5ファイルはUTF-8 BOM付きで、改行追記なしだった。

```json
{"probe":"O'Brien"}
{"probe":"He said \"Go\"\nSecond line 'quoted'"}
{"probe":"100%"}
{"probe":42.5}
{"probe":"NORMAL"}
```

JSONとしての引用符、改行、アポストロフィ、`%`、数値表現は保持された。これらはコードとして評価されず、固定ファイルからJSONとして復元された。

## 正常系1Run

- 実行前: `runtime/work.xlsx` と `template.xlsx` は同一SHA `108d25e5cfb86cd34422e738f7590d6050933c4f5429c672df65907fb2f31a36`。完成出力とJSONファイルは不在。
- 実行回数: 1。
- 終了: PADはREADYへ戻った。
- `PowershellOutput`: `{"status":"ERROR","mode":"NORMAL","error_code":"NUMBER_PAYLOAD_TYPE"}`
- `ProbeState`: `SCRIPT_NOT_SUCCESS_NO_SAVE`
- `ScriptGatePassed=False`、`NumericWriteEntered=False`、`SaveAsEntered=False`。
- `runtime/result.xlsx`: 不在。
- 実行後 `runtime/work.xlsx`: SHAは実行前・テンプレートと同一。

したがって、「エラー・成功結果欠落時に保存前停止する」ことはこの実Runで確認できた。一方、正常系の値・型・元書式保持は書込み前停止のため未確認である。

## 原因と局所修正

修正前:

```powershell
if ($payloads[3].probe -isnot [double]) { throw 'NUMBER_PAYLOAD_TYPE' }
```

修正後:

```powershell
$numberPayload = $payloads[3].probe
if ($numberPayload -isnot [double] -and $numberPayload -isnot [decimal]) {
    throw 'NUMBER_PAYLOAD_TYPE'
}
```

実ファイル `runtime/source-4.json` は、PowerShell 7では `System.Double`、Windows PowerShell 5.1では `System.Decimal` になった。後者がライブ停止と一致する。修正後script SHAは `aa2091327607b9ed1496f5ebb4a8bca2968e95e56ae3337f541651141e55f571`、正常系Robin SHAは `aaac1b7c04156f8038d26f6671c692faede55c91097cbf3f5d4c575348ae3851`、負例Robin SHAは `a1ff8f503d485402ffdbb98248a52e62eedf98ac27f95d566dbaca1800dfcd1f`。修正後Robinはライブ未実行である。

## 負例

正常系が失敗した時点で停止したため、承認済みの負例1Runは `NOT_RUN`。従って、一時書式変更直後の意図的例外について、元書式復元・後続書込み未進入・完成出力不在を実機で直接確認したとは扱わない。静的には `finally` の書式復元、`EXPECTED_ERROR` が成功ゲートを通らない構造、負例modeでSaveAsへ進まない構造を確認しただけである。

## テスト

- R2/R3 probe: 13/13 PASS。
- R1受入集約器: 9/9 PASS。既存2Run正例、4つの独立レビュー負例、必須キー欠落、case/Run/source/座標結合、two-run artifact結合、既存記録不変を含む。
- 合計: 22/22 PASS。

R1 `f8765ea` の主要diffは、`validate_run()` の状態文字列確認から、固定specの12座標、成果物SHA、参照元、case/Run、typed mapping、native bounds/件数、必須キーを強制する検証へ置換した点である。テストは `tests/Test-Issue38Ex03R11FileAuxFinalizer.py` に保持されている。

## 適用限界・残件

- 修正後正常系をライブで再実行していないため、修正後の値・型・元書式保持は未確認。
- 負例は未実行。書式復元の実機確認も未完了。
- 固定3文字列と固定数値 `42.5` だけを対象とし、任意文字列・任意数値・他型へ一般化しない。
- PADの実JSONは確認したが、PAD製品一般のJSON型規則を証明したものではない。
- manifestのLF-only旧記録訂正は既存残件のまま。
