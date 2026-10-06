# PADダミーCSV実機検証（公開用）

既存Claude Code CLI 2.1.286のMax認証で、実モデル `claude-opus-5-5` を開始・完了記録から確認した。専用フロー `FinanceDummy-Claude-20261007` を作成・保存し、2回実行した。

| 確認 | 結果 |
|---|---|
| 新規作成・Power Fx OFF・2アクション・保存 | PASS。保存状態とConsole検索1件を確認 |
| Run1成功観測 | 2026-10-06 20:45:56 UTC（翌日05:45:56 JST） |
| Run2成功観測 | 2026-10-06 20:46:36 UTC（翌日05:46:36 JST） |
| 全行照合 | 各6行・4列、R01～R06、全行入力と論理一致、外部検算43001円 |
| 2出力の原文バイト | 一致。各174 bytes、UTF-8 BOM付き・CRLF・末尾改行なし |
| Robin貼付け／保存後再コピー | 貼付け前に保全ガード停止。再コピーNOT_RUN、原文一致NOT_VERIFIED |
| ホストの静的テスト | コピー用Robin形式14件PASS。PS5補助2件は実行ポリシーで停止 |

## 実際に使ったGUI操作経路

CLIのPowerShellからWindows標準UI Automation（`UIAutomationClient`／`UIAutomationTypes`）を使った。PID・可視HWND・専用タイトル・同一対話セッションで対象を照合し、ValuePattern／TogglePattern／InvokePatternで設定・保存・実行した。アクション追加は既存[ダブルクリック補助](../../../tools/Invoke-PadActionDoubleClick.ps1)のuser32.dll（SetForegroundWindow／mouse_event）と可視UIA境界を使った。Console→新しいフロー→Designerの通常GUIであり、nativeUItool、Computer Use、PAD URL/API実行は使っていない。以前の環境のnativeUItool未公開が解消した証明ではなく、このCLIのシェルから可視GUIへアクセスできた観測である。

クリップボード保全付き貼付けは1回だけ試し、未対応のネイティブ形式で変更前に拒否された。内容を読んだり保全ガードを外したりせず、通常のアクション設定画面でCSV読込・CSV書込を追加した。UTF-8、ヘッダーあり、システム既定区切り、変数CSVTableを設定・読戻しし、出力に列名を含めた。既存の作成・保存・Run補助はWindows PowerShell 5.1のSTAプロセスから呼び出し、観測・設定補助はPowerShell 7.6.5で動かした。既存補助の起動引数にはプロセス限定のExecutionPolicy Bypassが含まれ、永続ポリシーは変更していない。ホストのPS5静的テスト2件は別の実行コンテキストで停止し、PASSにしていない。

## 入力・結果・境界

[入力](../../fixtures/finance-expense-dummy/input.csv)の末尾列はreceipt。Copilot判定出力のresult列とは異なる。Run1後の出力をスナップショット・照合して退避し、出力先が無いことを確認してRun2を実施した。[Run1](output/run1-output.csv)と[Run2](output/run2-output.csv)のSHA-256は `ad2f1beb0b75f4253b1c878912d1f3689204c842b5f3b573d69eb238510f4516`。各回でPAD変数表示も「6 行, 4 列」だった。

実行中状態は未捕捉。実行は新規成果物、変数値、Ready復帰と実行ボタン有効化で裏付けた。合計は外部検算であり、PADで集計した結果ではない。経費判定、承認、支払、Excel転記、保存Robin原文一致、企業用M365、別PCの受入へ成功を転用しない。

この公開版は[機械可読要約](observations.json)と原文CSVを残し、生のGUIダンプ・セッションログ・PC固有パス・他アプリ情報を省いた。個人情報・会社実データは入力していない。原文CSVのBOMや改行は公開時にも変更していない。
