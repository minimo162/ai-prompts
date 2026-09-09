# Robinナレッジ検証報告（途中）

更新日: 2026-09-09
ブランチ: `codex/robin-knowledge-2026-09-09`
基準: `7613e999661ceeb4e025dbfad11dfc21bd42b376`
状態: partial

## 利用先の訂正

検証対象は、ログイン済みの `https://microsoft365.com/chat` から「エージェント → 新しいエージェント／エージェントの作成」で開くMicrosoft 365 Copilot内Agent Builderです。Copilot Studio単体ポータルを利用先にしません。前回のStudio単体保存拒否は履歴として保持しますが、M365 Copilot内Agent Builderの原因や再開条件とは断定しません。詳細は `CODEX_CORRECTION_M365_AGENT_BUILDER.md` を参照します。

2026-09-09の実測では、`https://microsoft365.com/chat` は `https://m365.cloud.microsoft/chat` のMicrosoft Copilot画面へ到達した。ナビゲーションと「アプリなど」を確認したが、表示された項目はチャット、検索、ライブラリ、ノートブック、詳細等で、「エージェント」項目は画面上に現れなかった。「アプリなど」→「作成」は `/create` の画像作成画面へ遷移した。画面には「個人用」のアカウント表示があり、別テナントへの切替は行っていない。この観測だけからライセンスや管理者設定の原因は推測しない。Agent Builderの正規入口が表示される組織・アカウント条件の確認が必要である。最小限の観測値は `catalog/generated/agent-builder-m365-entry-20260909.json` に保存した。

## 静的・ファイル検証

- `copilot/agent-instructions.txt` を作成。UTF-8 BOMなし、5,648バイト、Unicodeスカラー数2,045、UTF-16コード単位数2,045、36行。7,000文字目標および8,000文字上限以内。
- ナレッジ配布版は7つの `.txt`。指示欄と技術資料を分離し、合計9ファイル（READMEを含む）で20ファイル上限を超えない。
- `catalog/coverage.json` は `catalog/index.json` から生成し、観測バリアント57件（既存51＋日時取得1＋空データテーブル1＋行追加失敗1＋CSV読取り1＋CSV書出し1＋ファイルコピー1）と必須範囲A〜Gの16チェックを記録。左側一覧は `complete=false`、未観測の名称は推測していない。
- `README.md` 冒頭をCopilotエージェント用配布物の入口へ変更。旧アプリ説明は過去資産として区別した。
- `pad-robin-prompts.md` 冒頭に編集用原稿であることと配布正本への対応を追記した。
- `catalog/generated/acceptance-t01-t10/README.md` にT01〜T10の依頼要点・期待値・状態を固定した。

## 既存PAD証拠の再利用（今回の再実測ではない）

- 変数・テキスト・有限Loop・数値変換、Office17種類22設定、PDF5種類11設定は既存の採取原文・証拠を参照可能。
- `catalog/generated/list-and-regex/` は実Copilot生成→PAD貼付け→実行→期待値照合の既存1ケース。
- `catalog/generated/office-three-apps/` は実Copilot生成16操作の既存ケース。新しいエージェントへ今回作成した7ファイルを登録した結果ではない。
- 既存証拠には再貼付け未確認のアクションや、アプリ自動Runとは別経路のものがあるため、coverageとナレッジで状態を分離した。

## PAD実機（今回のセッション）

|項目|結果|証拠・理由|
|---|---|---|
|ネイティブPADウィンドウ|PASS（観測のみ）|専用フロー `RobinKnowledgeLive_20260909` を作成し、Designer PID 27436をUI Automationで観測した|
|PAD版・言語・Power Fx|PASS（条件確認）|Designer file version `2.71.115.26224`、日本語UI、作成ダイアログのPower Fx=Offを確認した|
|左側アクション一覧|PASS（観測範囲）|ActionsTreeViewを展開して上端から下端までスクロールし、412ノード（グループ72、アクション340）を保存。全機能一覧とは表示していない|
|A〜Gの追加・コピー・別フロー再貼付け・保存・実行|部分PASS|日時取得の1設定を今回の全工程で実測。残りの未採取項目は未完了|

### 日時取得の1設定

「現在の日時を取得」を左パネルから追加し、取得=現在の日付のみ、タイム ゾーン=システム タイム ゾーン、出力=CurrentDateTimeを設定した。原文を `catalog/actions/datetime-get-current-date/date-only.robin` へ保存し、空の `RobinKnowledgeRoundtrip_20260909` へファイルから貼り付け、保存、再コピーした。原文と再コピーはSHA-256 `df0a911a7c9185a6f7127c442d6973929fb26a3dd1a527779c0fe61844c241f5` で一致した。2回実行し、両方で `CurrentDateTime=2026/09/09 0:00:00` を期待値と照合した。詳細は `catalog/evidence/datetime-current-date-validation.json`。

### 空データテーブルの1設定

「新しいデータ テーブルを作成する」を左パネルから追加し、入力テーブル0行0列、生成変数DataTable、エラー発生時=既定を確認した。原文 `Variables.CreateNewDatatable InputTable: { } DataTable=> DataTable` を保存し、別の空フローへファイルから貼り付け、保存、再コピーした。原文と再コピーはSHA-256 `f3eef9ad3585b35d39c8f90d9202629d63907414e1f7601270e9d0fff7af9256` で一致した。2回実行し、変数プレビュー「0 行, 0 列」を期待値と照合した。行追加・セル参照は別設定として未確認。詳細は `catalog/evidence/datatable-create-validation.json`。

行追加の失敗境界として、0行0列のDataTableへ `[]` を追加する設定を採取した。Robinは `Variables.AddRowToDataTable.AppendRowToDataTable DataTable: $'''DataTable''' RowToAdd: $'''[]'''`。PADデザイナーは「エラーあり」と表示し実行ボタンを無効化したため、実行成功・再貼付け成功とは扱わず、失敗原文を `catalog/actions/datatable-add-row/empty-table-failed.robin` と `catalog/evidence/datatable-add-row-empty-failed.robin` に分離保存した。列を持つテーブルの行追加は未採取。

### CSV読取り・DataTable書出しの組合せ

日本語と引用符を含む合成CSVを「CSV ファイルから読み取る」でUTF-8、TrimFields=True、FirstLineContainsColumnNames=False、SystemDefault区切りとして読み、3行3列のDataTableを確認した。別の空フローへファイルから貼付け、保存、再コピーし、DataTable変数参照を使う「CSV ファイルに書き込む」を追加した。2回実行後の出力CSVはUTF-8 BOM付きだが、論理3行（`ID,Name,Status`、日本語と二重引用符を含む行、`2,alpha,除外`）が入力と一致した。初回の誤設定（変数欄へ文字列リテラルを入力）は型エラーとして別記録し、正しい `%CSVTable%` 設定と混同していない。詳細は `catalog/evidence/csv-read-validation.json`。

### ファイルコピーの1設定

「ファイルのコピー」を左パネルから追加し、合成入力 `copy-input-20260909.txt` を専用出力フォルダーへコピーする設定（衝突時=何もしない、出力変数=CopiedFiles）を採取した。別の空フローへファイルから貼付け、保存、再コピーし、1回目はCopiedFilesに出力ファイルが入り、入力・出力のSHA-256 `c9b143da9a441652db51c7d921cbe46fa5df2bca8cc69e7ff7718f5fd300ffa5` が一致した。2回目は衝突時の「何もしない」によりCopiedFilesが空、既存出力が不変だった。詳細は `catalog/evidence/file-copy-validation.json`。移動・名前変更・上書きは未採取。

## Copilotエージェント（M365入口の実測と過去のStudio単体経路）

### M365 Copilot内Agent Builder（今回）

|項目|状態|証拠・再開条件|
|---|---|---|
|正規入口 `microsoft365.com/chat`|PASS（到達）|Microsoft Copilotのチャット画面へ到達した|
|「エージェント → 新しいエージェント／エージェントの作成」|NOT_FOUND|現在の画面にはエージェント項目が表示されず、`/create` は画像作成画面だった。表示される組織・アカウント条件を確認する|
|指示欄・ナレッジ登録|NOT_RUN|Agent Builder画面が見つからないため入力・アップロードしていない|
|登録後の質問・T01〜T10|NOT_RUN|上記画面での登録完了後に実施|

前回、Copilot Studio単体ポータルの作成フォームへ指示文を入力したが、保存時に「You don't have permission to create agents」「Ask your admin to grant you the right role, then try again.」「ユーザーの管理者ライセンスが無効です。」と表示され、作成は拒否された。これは失敗履歴として保持し、M365 Copilot内Agent Builderの再開条件にはしない。M365 Copilot内Agent Builderの登録・生成試験は未実施。

|項目|状態|再開条件|
|---|---|---|
|M365 Copilot内Agent Builder指示欄|NOT_RUN|正規入口でエージェント項目が表示されなかった|
|M365 Copilot内Agent Builder作成・ナレッジ登録|NOT_RUN|Agent Builder画面、登録先、共有範囲を確認していない|
|実測固有質問|NOT_RUN|登録完了後に新しい会話で実施|
|T01〜T10|NOT_RUN|登録完了、PAD専用フロー、合成データ、実行観測がそろう|
|T01/T04/T10独立再試験|NOT_RUN|T01〜T10最終版合格後に実施|

## 未対応・未確認

- A〜Gの必須チェックには未観測項目が残る（coverage.json参照）。必須項目のBLOCKED／未確認が残るため、目標は未完了。
- Copilotの認証・エージェント登録・生成・PAD実行の外部依存が未解消。
- push、PR、merge、公開、旧アプリの機能拡張は実施していない。

## 次の再開手順

1. ログイン済みM365 Copilotの `https://microsoft365.com/chat` から「エージェント」を開き、Agent Builderの画面構成・接続先を確認する。
2. `copilot/README.md` に従って指示欄・7つの `.txt` を登録し、処理完了を確認する。
3. PAD専用フローでcoverageの未採取から1アクション×1設定を選び、依頼書第5節の全工程を通す。
4. T01〜T10を固定期待値のまま実施し、結果をこの報告へ追記する。
