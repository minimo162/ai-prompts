# 合成経費CSV：Copilot判定とPAD入出力の検証

2026-10-06 UTCに架空6行だけを使い、個人用表示のCopilotで2新規チャットの判定・コード専用コピーを確認した。その後、既存Claude Code CLIからPADの専用フローを作成・保存・2回実行した。2試験の入力・成功範囲を分けて記録する。承認・支払や実データ操作は行わない。

## Copilot：固定6行の判定・コピー

1. 既存の利用可能なアカウント種別を確認する。個人用表示やURLだけで企業用条件を証明しない。
2. 新規通常チャットへ[固定依頼](../copilot/finance/expense-dummy-prompt.txt)を貼り、6行・規則・列順を照合して1回送信する。expected.csvは渡さない。
3. 回答のコード専用コピーをUTF-8ファイルに保存し、フェンス・説明・行番号の混入を確認する。独立した新規チャットで同じ試験を1回繰り返す。
4. 原文を改変せず[固定CSV検査](../tools/Verify-FinanceDummyCsv.mjs)で照合する。

`node tools/Verify-FinanceDummyCsv.mjs catalog/evidence/finance-expense-20261006/run1-copy.csv catalog/evidence/finance-expense-20261006/run2-copy.csv`

| 行 | 期待する判定 | 2回答の結果 |
|---|---|---|
| R01 | 10000円ちょうど | OK |
| R02 | 10001円 | LIMIT |
| R03 | receipt=N | MISSING |
| R04・R05 | 同じinvoice_idの全行 | 両行DUPLICATE |
| R06 | 理由の規定順序 | LIMIT;MISSING |

固定6行・列順・金額43001円は2回ともPASS。モデル選択は「自動」、実モデル名は未取得。基準版bundle・r2全文を添付しておらず、Robin生成やr2受入試験ではない。[Run1原文](../catalog/evidence/finance-expense-20261006/run1-copy.csv)は末尾LFあり、[Run2原文](../catalog/evidence/finance-expense-20261006/run2-copy.csv)は無しで、原文バイト一致はFAIL。原文を揃えてPASSにしない。[観測要約](../catalog/evidence/finance-expense-20261006/observations.json)と[比較](../catalog/evidence/finance-expense-20261006/comparison.json)を参照。

## PAD：通常GUIでCSV読込・書込

既存Claude Code CLI 2.1.286のMax認証を使い、`opus`指定の実モデル `claude-opus-5-5` を記録で確認した。Store版PAD `11.2609.183.0` の通常GUIへ、CLIのPowerShellとWindows標準UI Automationでアクセスできた。以前のnativeUItool未公開という観測とは別の経路である。

1. Consoleで未使用の専用名を確認し、新規空フローを作る。Power Fx OFF・Main空・専用タイトル・PID・可視HWND・同一対話セッション・一意な対象を現観測で照合する。
2. 保全付き貼付けが未対応形式で停止したら、ガードやクリップボードを消さない。今回の試験では通常のアクション一覧・設定ダイアログからCSV読込／書込2アクションを追加し、値を読戻して保存した。
3. 入力は[架空input.csv](../catalog/fixtures/finance-expense-dummy/input.csv)の6行4列。UTF-8・ヘッダーあり・システム既定区切りを確認する。システム既定が同じとは限らないので、他環境で結果を継承しない。
4. フロー全体を保存し、保存状態とConsole検索を確認。出力先が空の専用ディレクトリであることを確認してRun1。
5. 出力をスナップショット・全行照合して保全し、次Runゲートを通す。出力先が無いことを確認してRun2。観測タイムアウトだけで再Runしない。
6. [PAD固定入出力検査](../tools/Verify-FinancePadRoundTrip.mjs)で全行論理一致と2出力の原文バイト一致を別々に照合する。

`node tools/Verify-FinancePadRoundTrip.mjs catalog/evidence/finance-expense-pad-cli-20261006/output/run1-output.csv catalog/evidence/finance-expense-pad-cli-20261006/output/run2-output.csv`

専用名は `FinanceDummy-Claude-20261007`。Run1成功観測は2026-10-06 20:45:56 UTC、Run2は20:46:36 UTC（JST翌日05:45:56、05:46:36）。作成・保存・2RunはPASS。出力は各6行4列、R01～R06、外部検算43001円で全行入力と論理一致。2出力は174 bytesで原文一致、UTF-8 BOM付き・CRLF・末尾改行なし。入力はBOMなし・LF・末尾改行ありなので、入力と出力のバイト一致とは区別する。

保存後Robin再コピーはクリップボード保全上の制約でNOT_RUN、原文一致はNOT_VERIFIED。実行中状態は未捕捉、新規出力・変数プレビュー「6 行, 4 列」・Ready復帰で実行を裏付けた。ホストのコピー用Robin静的14テストPASS、PS5補助テスト2件は実行ポリシーで停止した。CSV入出力の成功を経費判定、PADでの集計、承認・支払、Excel転記の成功へ転用しない。

[PAD公開用報告](../catalog/evidence/finance-expense-pad-cli-20261006/report.md)と[機械可読要約](../catalog/evidence/finance-expense-pad-cli-20261006/observations.json)を参照。会社実データ、新規ログイン・インストール・課金設定や権限追加は使っていない。企業テナント・DLP・ライセンス・別PC、CSVエスケープや不正入力は未検証。
