# Robinナレッジ作成 進捗

更新日: 2026-09-09

## 全体目標

アプリではなく、PADの実測Robinに基づくCopilotエージェント用の指示文とナレッジを完成する。

## 作業ブランチ／基準コミット

- ブランチ: `codex/robin-knowledge-2026-09-09`
- 基準コミット: `7613e999661ceeb4e025dbfad11dfc21bd42b376`（main）
- origin: `https://github.com/minimo162/ai-prompts.git`
- push、PR、merge、公開: 実施しない

## 実機の条件

- 既存記録で確認済みの条件: PAD `2.71.115.26224`、日本語UI、Power Fx OFF、合成データ・専用フロー。
- これは過去の記録であり、この再開ターンでのPAD画面・版・Power Fxの再確認ではない。
- 現在のDesigner PID 27436でファイルバージョン `2.71.115.26224`、日本語UI、作成ダイアログのPower Fx=Offを確認した。専用フロー `RobinKnowledgeLive_20260909` と空の `RobinKnowledgeRoundtrip_20260909` を使用している。
- Computer Useはブラウザー操作に限定されるため、PADは既存のUI Automation補助を読み取り・専用フローに限定して再利用した。既存業務フローは操作していない。

## 既存資産の再集計

- `catalog/index.json` の実測エントリ: 51件。
- 今回の日時取得・空データテーブル・空テーブルへの行追加失敗・CSV読取り・CSV書出し・ファイルコピーを追加後の `catalog/index.json`: 57件（既存51＋新規6）。
- 既存カテゴリ別: 変数7、テキスト8、ループ1、ファイル2、Excel8、Word7、PowerPoint7、PDF11。今回、日時1・変数2（成功1、失敗1）・ファイル3（CSV読取り／書出し／コピー）を追加。
- 索引のscopeは「Observed PAD action variants」であり、全アクション一覧でも実行許可集合でもない。
- 既存の生成・実行証拠は `catalog/generated/list-and-regex/` と `catalog/generated/office-three-apps/` にあるが、新しいエージェントへの登録試験とは区別する。

## 固定した必須採取チェックリスト

- A 基礎: 既存の変数・文字列・数値・リスト・置換・分割・結合・数値変換に加え、日時取得のdate-only設定を実測済み。日時加算・減算・書式化、一般の数値減算、リスト取出しは未確認。
- B 制御: 定数範囲Loopは観測済み。If/Else、For each、ループ脱出、エラー処理、サブフロー作成・呼出しは今回の必須チェックとして未確認。
- C データ処理: 空データテーブル作成、CSV読取り、DataTable変数参照でのCSV書出しは実測済み。0行0列への空行追加は設計エラーとして記録。列を持つテーブルの行追加・行反復・セル参照は未確認。
- D ファイル: UTF-8テキスト読取り、CSV読取り、CSV書出しは観測済み。フォルダー内ファイル取得、存在確認、フォルダー作成、テキスト書出し、コピー・移動・名前変更は未確認または既存記録との対応整理が必要。
- E Excel: 起動・セル/範囲読取り・書込み・保存・終了は観測済み。シート選択・データ反復の独立例は未確認。
- F Word・PowerPoint・PDF: 既存採取・証跡を引き継ぐ教材化と再利用確認が必要。未採取モードを完成例へ混ぜない。
- G UI・ブラウザー: 既存記録ではEdge起動が拡張機能通信エラー。起動・入力・クリック・待機・文字取得・終了の通し実測は未確認。

## 現在の段階

採取／教材化（左パネル全体観測と日時取得1設定のRoundtrip・2回実行を完了。M365 Copilot内Agent Builder試験待ち）。

## 直前に完了した項目

- 依頼書を読み直した。
- 既存索引を再集計し、51件・8カテゴリであることを確認した。
- 作業ブランチを作成した。
- `copilot/agent-instructions.txt` と7つの登録用 `.txt`、`copilot/README.md` を作成した。
- `catalog/coverage.json` を生成し、観測済み56件と必須範囲A〜Gの16チェックを明示した。
- T01〜T10の依頼・期待値を `catalog/generated/acceptance-t01-t10/README.md` に固定した。
- `docs/robin-knowledge-validation.md` に静的検証、実機・CopilotのBLOCKED状態、再開手順を保存した。
- `tests/Test-CopilotRobinPackage.ps1` がPASS（指示欄UTF-16 2,045、ナレッジ7、観測51）。
- 左パネルをActionsTreeViewで再観測し、412ノード（グループ72、アクション340）を `catalog/evidence/pad-action-inventory-20260909.json` に保存した。
- 「現在の日時を取得」を「現在の日付のみ」で採取し、保存テキストを別の空フローへ貼付け・保存・再コピー・SHA-256一致・2回実行・期待値照合した。
- 「新しいデータ テーブルを作成する」を0行0列設定で採取し、別の空フローへ貼付け・保存・再コピー・SHA-256一致・2回実行・0行0列期待値照合した。行追加・セル参照は未採取。
- 0行0列DataTableへの空リスト行追加を試し、設計エラーを観測。失敗原文を保存し、成功件数へ含めていない。
- 日本語・引用符を含む合成CSVをUTF-8で読み、3行3列を確認。DataTable変数参照で別CSVへ書き戻し、内容一致と2回の実行を確認した。
- 合成ファイルのコピーを専用フォルダーへ実行し、1回目の入力・出力ハッシュ一致と、2回目のDoNothingによる出力不変を確認した。

## その証拠ファイル

- `CODEX_TASK_PAD_ROBIN_KNOWLEDGE.md`
- `CODEX_CORRECTION_M365_AGENT_BUILDER.md`
- `catalog/index.json`
- `docs/robin-action-catalog.md`
- `docs/office-action-capture.md`
- `docs/pdf-action-capture.md`
- `catalog/generated/list-and-regex/`
- `catalog/generated/office-three-apps/`
- `copilot/agent-instructions.txt`
- `copilot/knowledge/`
- `catalog/coverage.json`
- `catalog/generated/acceptance-t01-t10/README.md`
- `docs/robin-knowledge-validation.md`
- `catalog/evidence/pad-action-inventory-20260909.json`
- `catalog/actions/datetime-get-current-date/date-only.robin`
- `catalog/evidence/datetime-current-date-roundtrip.json`
- `catalog/evidence/datetime-current-date-roundtrip-recopy.robin`
- `catalog/evidence/datetime-current-date-validation.json`
- `catalog/generated/agent-builder-m365-entry-20260909.json`
- `catalog/actions/datatable-create/empty.robin`
- `catalog/flows/datatable-create/roundtrip.robin`
- `catalog/evidence/datatable-create-roundtrip.json`
- `catalog/evidence/datatable-create-roundtrip-recopy.robin`
- `catalog/evidence/datatable-create-run-1.json`
- `catalog/evidence/datatable-create-run-2.json`
- `catalog/evidence/datatable-create-validation.json`
- `catalog/actions/datatable-add-row/empty-table-failed.robin`
- `catalog/evidence/datatable-add-row-empty-failed.robin`
- `catalog/fixtures/csv/input-20260909.csv`
- `catalog/actions/csv-read/utf8.robin`
- `catalog/actions/csv-write/variable-reference-utf8.robin`
- `catalog/flows/csv-read-write2/roundtrip.robin`
- `catalog/evidence/csv-read-validation.json`
- `catalog/evidence/csv-read-write-output2-20260909.csv`
- `catalog/fixtures/files/copy-input-20260909.txt`
- `catalog/actions/file-copy/single-no-overwrite.robin`
- `catalog/flows/file-copy/roundtrip.robin`
- `catalog/evidence/file-copy-roundtrip.json`
- `catalog/evidence/file-copy-roundtrip-recopy.robin`
- `catalog/evidence/file-copy-run-1.json`
- `catalog/evidence/file-copy-run-2.json`
- `catalog/evidence/file-copy-validation.json`

## 残っている必須項目

- A〜Gの残り未採取チェック項目の1アクション×1設定採取・再貼付け・保存・実行・結果照合。
- M365 Copilot内Agent Builderでの指示欄・7つの `.txt` 登録、処理完了、ナレッジ参照質問。
- T01〜T10、T01/T04/T10独立再試験、生成回答・PAD貼付け・実行結果の証拠。

## 失敗した方法と分かったこと

- 過去記録ではPAD左パネルのUI Automationが仮想化され、一度に表示された部分を全件と扱えなかった。
- 過去のEdge起動はWeb拡張機能との通信エラーで、ブラウザインスタンスが空白になった。UI・ブラウザー通し成功の根拠にはしない。
- 既存のOffice/PDF生成証拠は実Copilot/PADの別ケースを含むが、新規エージェントへファイル登録した試験ではない。
- `Run-NonLiveTests.ps1 -Suite All` は既存契約テストの途中までPASSしたが、`Test-Copilot.ps1` で長時間無出力となったためプロセスを停止した。全体PASSの証拠にはしない。
- 左パネル全件収集の初版はスクロール値が1.936...で停滞したため停止。SetScrollPercentで段階的に移動する方式へ変え、上端から下端までの412ノードを取得した。
- 列を持たないDataTableへ空行を追加するとデザイナーエラーとなった。列定義や行値を推測せず、失敗例として分離した。

## 人の操作が必要な項目・具体的な理由

- PADは現在UI Automationで専用フローを観測・操作できる。実機採取を続けるため、専用フロー名と対象Designer PIDを毎回再確認する。
- M365 Copilotの正規入口 `https://microsoft365.com/chat` はチャット画面へ到達したが、画面内に「エージェント」項目は表示されず、「アプリなど」→「作成」は画像作成 `/create` へ遷移した。画面のアカウント表示は「個人用」。別テナントへ切り替えていない。
- M365 Copilot内Agent Builderの画面・登録先・共有範囲は未確認。前回のCopilot Studio単体エラーは履歴として保持し、原因や再開条件を推測しない。

## 次に行う1作業

ログイン済みM365 Copilotの `https://microsoft365.com/chat` から「エージェント → 新しいエージェント／エージェントの作成」を開き、Agent Builderの画面構成・接続先を記録する。並行してPADのA〜G未採取から次の1設定を選ぶ。
