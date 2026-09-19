# Issue #38 / EX02 型保持照合probe

**判定: 今回の型照合probeは成功。EX02全体は引き続き未受入。** 数値1と文字列`"1"`を同じキーのカスタムオブジェクトに包んでJSON化し、その結果をPAD内で比較した。正例2件・負例2件は、同じ保存済みフローのRun1/Run2で固定期待値に一致した。外部Pythonによる入力比較は実施していない。

## 前回記録と今回の範囲

- 基点はローカルr4コミット`02e33b4702ed88c3ff7138f5cf59f429f48138a0`。作業先は`C:\Users\yuuki\ai-prompts-issue38`、ブランチは`codex/issue38-type-probe-20260915`。
- [前回r4報告](../../cycles/EX02-r4/review.md)と[旧scalar-compare原文](../scalar-compare/captured-full.robin)を確認した。旧probeは数値-3と同表示文字列でもMATCHとなっており、数値1の今回実測として再利用していない。
- [plan.json](plan.json)で合成入力・正負の組合せを固定した。追加貼付けが停止したため、実行前に[ui-only-plan.json](ui-only-plan.json)へ実装手順を変更した。MATCH/DIFFERENTをTrue/Falseで直接記録する対応を明示し、入力と一致・不一致の期待は維持した。両計画を保存し、実行後の期待値変更はしていない。
- 新規専用フロー`RobinIssue38TypeIdentity20260915C`をConsoleから1回作成。Power Fx OFF、日本語UI、PADファイル版`2.71.115.26224`。開始時0アクションを確認した。既存の`RobinIssue38TypeCapture20260915B`と各EX/probeフローは編集・実行していない。
- r4の指示・bundle・7原本・manifestと既存証跡を保持した。新版作成、EX02全体の再試験、Copilot送信、GitHubへのpush/PR/Issue書込みは0件。

## PAD由来のRobin原文

不足していたJSON変換はPADのアクション設定画面で`%{ 'probe': NumberOne }%`を指定して保存し、[単独アクション原文](captured-json-action.robin)をコピーした。残りのJSON変換・比較式もPADの設定画面で入力値を読戻して保存した。入力4行は既存SET構文の合成パラメーター置換から開始し、PAD保存後に[原文](captured-inputs.robin)を採取した。

以下は[保存後の全14アクション原文](captured-full.robin)。表示用コードブロックであり、原ファイルはUTF-8 BOMなし、CRLF、末尾CRLFあり、869バイト。SHA-256は`27a89c538916ac083be0c39864a617521646a27f83993837519eddde96197798`。

```text
SET NumberOne TO 1
SET TextOne TO $'''%'1'%'''
SET NumberOneCopy TO 1
SET TextOneCopy TO $'''%'1'%'''
Variables.ConvertCustomObjectToJson CustomObject: { 'probe': NumberOne } Json=> CustomObjectAsJson
Variables.ConvertCustomObjectToJson CustomObject: { 'probe': TextOne } Json=> CustomObjectAsJson2
Variables.ConvertCustomObjectToJson CustomObject: { 'probe': NumberOneCopy } Json=> CustomObjectAsJson3
Variables.ConvertCustomObjectToJson CustomObject: { 'probe': TextOneCopy } Json=> CustomObjectAsJson4
SET PositiveNumber TO CustomObjectAsJson = CustomObjectAsJson3
SET PositiveText TO CustomObjectAsJson2 = CustomObjectAsJson4
SET NegativeNumberText TO CustomObjectAsJson = CustomObjectAsJson2
SET NegativeTextNumber TO CustomObjectAsJson2 = CustomObjectAsJson
SET ScalarEquality TO NumberOne = TextOne
SET ProbeCompleted TO $'''TYPE_PROBE_FINISHED'''
```

`CustomObjectAsJson`/`3`は数値、`2`/`4`は文字列を包んだ結果。PADが実行した`SET ... TO 左辺 = 右辺`の真偽値を採取しており、外部言語で入力を比較してPAD成功へ転記していない。

## 実行結果

| PAD内の比較 | 事前期待 | Run1 | Run2 | 判定 |
|---|---|---|---|---|
| 数値1と数値1のJSON (`PositiveNumber`) | True | True | True | 正例成功 |
| 文字列1と文字列1のJSON (`PositiveText`) | True | True | True | 正例成功 |
| 数値1と文字列1のJSON (`NegativeNumberText`) | False | False | False | 負例で不一致を検出 |
| 文字列1と数値1のJSON (`NegativeTextNumber`) | False | False | False | 負例で不一致を検出 |
| 通常の数値1 = 文字列1 (`ScalarEquality`) | 観測のみ | True | True | 厳密な型照合として不適合 |
| 終端マーカー (`ProbeCompleted`) | TYPE_PROBE_FINISHED | 一致 | 一致 | 最終アクション到達 |

PADが生成したJSONは両Runで次の通りだった。

```text
CustomObjectAsJson  = {"probe":1.0}
CustomObjectAsJson2 = {"probe":"1"}
CustomObjectAsJson3 = {"probe":1.0}
CustomObjectAsJson4 = {"probe":"1"}
```

- Run1終了観測: 2026-09-15 20:25:27 JST。[実行記録](run1.json)、[終了状態](run1-terminal-state.json)、[名前付き変数原記録](run1-variables-visible.json)、[追加表示](run1-variables-additional.json)、[固定期待値との照合](run1-reconciliation.json)。
- Run1の[入力型画面](run1-input-types.png)は4変数すべての表示値1と、数値の`#`アイコン／テキストの`T`アイコンを同時に示す。[フローと結果画面](run1-pad-window.png)も保存した。
- Run1の原文・結果保存と期待値照合後、結果プレビューを1回クリアした。[Run2開始前](pre-run2-state.json)ではプレビュー0件、エラー0、実行可能を確認。残留値をRun2成功としていない。
- Run2終了観測: 2026-09-15 20:28:46 JST。[実行記録](run2.json)、[終了状態](run2-terminal-state.json)、[名前付き変数原記録](run2-variables.json)、[固定期待値との照合](run2-reconciliation.json)、[4比較結果画面](run2-cases.png)。
- 両Runとも`ready`、`running=false`、既知のエラー数0、終端マーカーと全4比較結果を確認した。`ready`だけを合格根拠にしていない。
- [Run1後再コピー](recopy-after-run1.robin)と[Run2後再コピー](recopy-after-run2.robin)は実行前の869バイト原文とSHA一致。最初の5アクションのバイトも全原文の先頭で保持している。
- `run*-reconciliation.json`はPADが計算した表示結果と事前期待値の照合記録であり、外部の数値／文字列比較器ではない。

## 失敗・方式変更の記録

| 工程 | 観測 | 処理 |
|---|---|---|
| 前ターンのComputer Use | `accessibility=null`、PAD対象取得中の別アプリ前面表示、前面化1回で`failed to activate captured window` | 新規フロー作成・実行前で停止。次ターンで現在状態を確認して直接UIAを利用。同ターン内にskyと直接UIAを混在させていない |
| PowerShell 7の貼付け補助 | `PadClipboardLease.cs`のコンパイルで`CS0246 Dictionary<,>` | クリップボード操作前・0アクションのまま。BOM付き既存補助をWindows PowerShell 5.1で実行し、入力4行の貼付けを1回確認 |
| IF構成の追加貼付け | [append-tail.json](append-tail.json)は`pasteRequested=false`、`not_changed`。`PAD_CLIPBOARD: unsupported native format; paste refused` | `DataObject`/`Ole Private Data`という内部形式名だけを確認。保全チェックを外さず、以後の追加はPAD設定画面で行った |
| 旧組立て案 | [assembled-tail.robin](assembled-tail.robin) | Robinは**NOT_PASTED / NOT_RUN**。[補助](Append-TypeProbeTail.ps1)は実行し、上記の保全ガードで貼付け前に停止。成功した14アクション原文とは別物として保存 |

入力4行の貼付け記録のclipboard状態は`newer_clipboard_preserved`、全形式の生バイト同一性は`NOT_ASSESSED`のまま。各原文コピー補助の復元成功と区別する。最初の入力ファイルはLF 102バイト、PADコピーはCRLF 106バイトで、入力時からのバイト一致とはしていない。

## 保全・限界・次の最小作業

[最終保全確認](final-preservation.json)で、開始時の既存233ファイル、r4全10ファイル、前回が保護した192ファイル（Git ignore対象の準備済みrunファイルを含む）は、それぞれ保存済みSHAとすべて一致した。今回の変更は本probeディレクトリ内への追加だけで、旧等価比較の結果、558差分FAIL、r4の生成拒否・EX02未受入状態は変更していない。

今回証明したのは、**数値1と同じ表示の文字列1を保持して区別する値照合**。JSON全体の文字列比較は値も比較するため、任意値について型だけを返す汎用GetType相当ではない。数値内部の整数/小数型区別、任意の複合型、空値・日時・特殊文字などへ一般化しない。

未証明は、Excel/DataTableから取り出したセルへのこの方式の接続、全12セルの照合、安全分岐と保存／再読取りの統合、EX02全体の受入。これらは今回実行していない。

次に必要な最小作業は、**合成Excelから取り出した数値1・文字列1の各セルへ、今回のオブジェクト化とJSON比較を接続する小規模probe**。それが確認できてから、別途許可された範囲で次候補への統合を検討する。

方式検討では[Microsoftのカスタムオブジェクト仕様](https://learn.microsoft.com/en-us/power-automate/desktop-flows/variable-data-types#custom-object)と[JSON変換アクション](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/variables#convert-custom-object-to-json)を参照した。公式資料は構文・機能の参考であり、本件の型保持成功の根拠は上記PAD実測である。
