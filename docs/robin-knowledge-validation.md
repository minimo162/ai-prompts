# Robinナレッジ検証報告（途中）

更新日: 2026-09-10
ブランチ: `codex/issue-5-acceptance-20260910b`
基準main: `69fe344`
固定コミット: `2731e0e`（最新P3 probe・metadata反映コミット）
状態: partial

## 利用先の訂正

検証対象は、ログイン済みの `https://microsoft365.com/chat` の通常M365 Copilotチャットです。Agent Builder／Copilot Studioは今回の検証先から外し、別環境での確認事項として扱います。前回のStudio単体保存拒否と入口観測は履歴として保持します。最新仕様は `CODEX_CORRECTION_M365_CHAT_VALIDATION.md` を参照します。

2026-09-09の再実測では、ログイン済みEdgeの `https://microsoft365.com/chat` は `https://m365.cloud.microsoft/chat` のMicrosoft Copilot画面へ到達した。ナビゲーションと「アプリなど」を確認したが、表示された項目はチャット、検索、ライブラリ、ノートブック、詳細等で、「エージェント」項目は画面上に現れなかった。「アプリなど」→「作成」は `/create` の作成画面へ遷移し、別タイルの「Office Agent」は `https://officeagent.microsoft.com/?srcref=officehome` のOffice Agent画面へ遷移した。後者は画面構成が指定のM365 Copilot内Agent Builderと異なるため、Agent Builderとして扱っていない。画面には「個人用アカウント」と表示され、別テナントへの切替は行っていない。この観測だけからライセンスや管理者設定の原因は推測しない。Agent Builderの正規入口が表示される組織・アカウント条件の確認が必要である。再実測値は `catalog/generated/agent-builder-m365-entry-rerun-20260909.json` に保存した。

## 静的・ファイル検証

- 履歴版の `copilot/agent-instructions.txt` はUTF-8 BOMなし、9,214バイト、Unicodeスカラー数3,585、47行。SHA-256は `e467855137a1eec8655cfb6086f274e6a8e996412b3d07068f32c6912d9482c1`。現作業版はUTF-8 BOMなし、10,096バイト、UTF-16 3,949、SHA-256 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`。
- 現作業版の結合bundle SHA-256は `4282e4ece4f2d79ce26e85143fcab201091b185d9ee5d9defe4d8f49a4a7b2cd`。旧bundle `431c...` の生成・PAD結果は履歴であり、現作業版の受入には継承しない。
- ナレッジ配布版は7つの `.txt`。指示欄と技術資料を分離し、合計9ファイル（READMEを含む）で20ファイル上限を超えない。
- `catalog/coverage.json` は `catalog/index.json` と既存証拠を突合し、観測バリアント86件（既存51＋追加35件）と必須範囲A〜Gの16チェックを記録。別probeでBoolean／減算／日時加算・減算／Else／Loop脱出・継続／ファイル操作／Excelシート／エラー骨格／サブフロー作成・呼出しを確認したが、現行bundleへは未統合。左側一覧は `complete=false`、未観測の名称は推測していない。
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
|A〜Gの追加・コピー・別フロー再貼付け・保存・実行|部分PASS|日時取得、空DataTable、CSV、ファイルコピー、サブテキスト取得を今回の全工程で実測。残りの未採取項目は未完了|

### 2026-09-10 継続ターンの実機状態

- Microsoft.PowerAutomateDesktop `11.2608.115.0` のPAD.Console.HostとDesignerプロセス、`RobinKnowledgeT04ExcelFilter_20260910` を起動・列挙できた。
- native Computer UseでDesignerへ接続しようとしたが、Trusted RPCが未構成（`Trusted RPC service is not configured: sky`）で、現在のPAD画面のアクセシビリティ状態を取得できなかった。
- native CUAはTrusted RPC未構成だったが、リポジトリ既存の厳格なUIAヘルパーへ切り替え、T04のクリップボード取得、別空フロー貼付け、保存、実行、成果物照合を実施した。T09はUI要素捕捉・貼付け・保存まで実施し、WebAutomationタイムアウトを分離記録した。native CUAの未接続証拠は `catalog/evidence/pad-native-ui-blocked-20260910.json`、UIA復旧とT04正例は `catalog/evidence/pad-uia-recovered-20260910.json` と `catalog/evidence/t04-positive-acceptance-20260910.json`、T09は `catalog/evidence/t09-runtime-block-20260910.json`。

### 日時取得の1設定

「現在の日時を取得」を左パネルから追加し、取得=現在の日付のみ、タイム ゾーン=システム タイム ゾーン、出力=CurrentDateTimeを設定した。原文を `catalog/actions/datetime-get-current-date/date-only.robin` へ保存し、空の `RobinKnowledgeRoundtrip_20260909` へファイルから貼り付け、保存、再コピーした。原文と再コピーはSHA-256 `df0a911a7c9185a6f7127c442d6973929fb26a3dd1a527779c0fe61844c241f5` で一致した。2回実行し、両方で `CurrentDateTime=2026/09/09 0:00:00` を期待値と照合した。詳細は `catalog/evidence/datetime-current-date-validation.json`。

### 空データテーブルの1設定

「新しいデータ テーブルを作成する」を左パネルから追加し、入力テーブル0行0列、生成変数DataTable、エラー発生時=既定を確認した。原文 `Variables.CreateNewDatatable InputTable: { } DataTable=> DataTable` を保存し、別の空フローへファイルから貼り付け、保存、再コピーした。原文と再コピーはSHA-256 `f3eef9ad3585b35d39c8f90d9202629d63907414e1f7601270e9d0fff7af9256` で一致した。2回実行し、変数プレビュー「0 行, 0 列」を期待値と照合した。行追加・セル参照は別設定として未確認。詳細は `catalog/evidence/datatable-create-validation.json`。

行追加の失敗境界として、0行0列のDataTableへ `[]` を追加する設定を採取した。Robinは `Variables.AddRowToDataTable.AppendRowToDataTable DataTable: $'''DataTable''' RowToAdd: $'''[]'''`。PADデザイナーは「エラーあり」と表示し実行ボタンを無効化したため、実行成功・再貼付け成功とは扱わず、失敗原文を `catalog/actions/datatable-add-row/empty-table-failed.robin` と `catalog/evidence/datatable-add-row-empty-failed.robin` に分離保存した。列を持つテーブルの行追加は未採取。

### CSV読取り・DataTable書出しの組合せ

日本語と引用符を含む合成CSVを「CSV ファイルから読み取る」でUTF-8、TrimFields=True、FirstLineContainsColumnNames=False、SystemDefault区切りとして読み、3行3列のDataTableを確認した。別の空フローへファイルから貼付け、保存、再コピーし、DataTable変数参照を使う「CSV ファイルに書き込む」を追加した。2回実行後の出力CSVはUTF-8 BOM付きだが、論理3行（`ID,Name,Status`、日本語と二重引用符を含む行、`2,alpha,除外`）が入力と一致した。初回の誤設定（変数欄へ文字列リテラルを入力）は型エラーとして別記録し、正しい `%CSVTable%` 設定と混同していない。詳細は `catalog/evidence/csv-read-validation.json`。

### ファイルコピーの1設定

「ファイルのコピー」を左パネルから追加し、合成入力 `copy-input-20260909.txt` を専用出力フォルダーへコピーする設定（衝突時=何もしない、出力変数=CopiedFiles）を採取した。別の空フローへファイルから貼付け、保存、再コピーし、1回目はCopiedFilesに出力ファイルが入り、入力・出力のSHA-256 `c9b143da9a441652db51c7d921cbe46fa5df2bca8cc69e7ff7718f5fd300ffa5` が一致した。2回目は衝突時の「何もしない」によりCopiedFilesが空、既存出力が不変だった。詳細は `catalog/evidence/file-copy-validation.json`。移動・名前変更・上書きは未採取。

### サブテキスト取得の1設定

「サブテキストの取得」を左パネルから追加し、元のテキスト=`A日本語BC`、開始インデックス=1、長さ=3、生成変数=`Subtext`を設定した。原文 `Text.GetSubtext.GetSubtext Text: $'''A日本語BC''' CharacterPosition: 1 NumberOfChars: 3 Subtext=> Subtext` を保存し、別の空フローへ貼付け・保存・再コピーした。原文と再コピーのSHA-256は `4f1021aafc353edba483e83ea61c6dd93d3c7944ad7b4566049c50fe81e4f70c` で一致した。元フローとRoundtripフローを各2回実行し、両方で `Subtext=日本語` を照合した。別の開始位置、末尾まで取得、範囲外入力は未確認。詳細は `catalog/evidence/text-substring-validation.json`。

### テキスト書出しの1設定

「テキストをファイルに書き込む」を左パネルから追加し、UI入力では`100%%`、エンコード=UTF-8、既存内容を上書き、末尾改行=Trueを設定した。原文を保存し、別の空フローへ貼付け・保存・再コピー、元フローとRoundtrip各2回実行まで確認した。出力はUTF-8 BOM付き73 bytesで、正規化した4行に日本語、100%、引用符、バックスラッシュ、対象語を保持した。`100%`をそのまま入力した失敗試行は設計エラーとして別証拠に分離した。詳細は `catalog/evidence/text-write-validation.json` と `catalog/evidence/text-write-invalid-percent.json`。

### テキスト変数書込みと末尾改行なし設定

「書き込むテキスト」へ既存テキスト変数`Replaced`を指定した原文`File.WriteText ... TextToWrite: Replaced AppendNewLine: True ...`を採取し、別空フローへの貼付け・保存・再コピーでSHA-256 `7d73b162b4b298a547b7c45f98eab0f116a0abf047e6ec1e65de3d426063adac`の一致を確認した。さらに同じ変数参照で`AppendNewLine=False`へ変更した原文`catalog/actions/file-write-text/variable-reference-no-append.robin`（SHA-256 `ca6006e287fdd4050f277f4965d6c2e8c3e1aa724dfbcbd4f3300cd3e7d2abe6`）を採取し、別空フローへの貼付け・保存・再コピーを確認した。

### 通常M365チャットのT01初回修正版

通常のMicrosoft 365 Copilotチャットでモデルメニューから`GPT OpenAI`→`GPT 5.6 Think Deeper`を選び、表示が`GPT 5.6 Think`になることを確認した。7原本の機械的結合版（現行SHA-256 `dd6091bbea9c05eee84f59d5c1105a178ba8b4c76b0cb6c74fe9038d97ce433a`）をCDPで既存`input[type=file]`へ直接設定し、アップロードメニュー操作なしで添付チップ1件を確認した。本文はcontenteditable正規化後に全文一致し、送信・回答取得を確認した。

回答のRobinを編集せず`catalog/generated/normal-chat-t01-20260909-gpt56-noappend-clean2/robin.txt`から新規PADフローへ貼付け、3アクション・保存・2回実行を確認した。出力`catalog/evidence/normal-chat-t01-output-20260909.txt`はUTF-8 BOM付き85 bytesで、期待する5行（日本語、対象語だけ置換、100%、引用符、バックスラッシュ、対象外語、末尾改行）と完全一致した。証拠は`catalog/evidence/normal-chat-t01-noappend-paste.json`、`normal-chat-t01-noappend-run-1.json`、`normal-chat-t01-noappend-run-2.json`。AppendNewLine=Trueの初回生成は末尾に追加改行が生じたため失敗として残し、最新版ではFalseへ修正した。

## 通常のM365 Copilotチャット検証

今回の検証先は、ログイン済み `https://microsoft365.com/chat` の通常チャットである。Agent Builder／Copilot Studioの作成・権限調査は行わない。通常チャットの成功は「通常のM365 Copilotチャット＋PADで検証済み」と記録できるが、Agent Builderの登録・検索・指示遵守・実行環境差は未検証として併記する。

|項目|状態|証拠・再開条件|
|---|---|---|
|通常チャット到達|PASS|専用EdgeのCDPでログイン済みM365 Copilot通常チャットと本文入力欄を確認した|
|本文全文入力|PASS|2,307文字を挿入し、contenteditable境界を正規化した全文一致を確認した|
|7つの実ファイル添付|PARTIAL（結合版へ切替）|7件逐次添付は4件目以降の一対一保持を確認できず、7原本を機械的に結合した1ファイルを添付する方式へ切り替えた。元ファイルのSHAと区切りはmanifestへ保存した|
|ナレッジ固有質問|PASS_REFERENCE_ONLY（現行bundle 431c版）|現行bundleを別の新規通常チャットへ添付し、UTF-8書込み差分・T04 9行原文・T09捕捉と実行未完了・確認状態の分離を回答原文と照合。`catalog/evidence/normal-chat-knowledge-precheck-current-20260910.json`|
|T01生成回答|PASS（初回修正版）|GPT 5.6 Think Deeperの新規チャットで結合版を添付し、本文3,128文字・回答全文・3行Robinを保存。`gpt56-noappend-clean2`の`robin.txt`は3アクション|
|T01 PAD実行・成果物照合|PASS（初回修正版）|回答Robinを無修正で新規フローへ貼付け、保存、2回実行。出力UTF-8 BOM付き85 bytes、期待内容と完全一致。`normal-chat-t01-noappend-*`|
|T01〜T07、T10|PASS_CURRENT_REVISION|現行版の新規通常チャット生成、無修正貼付け・保存・2回実行・期待値照合を個別証跡へ記録|
|T08|FAILED_CURRENT_REVISION_FORMAT|現行版は有効なRobin fenced blockを返さず、拒否／inline／未出力。期待エラー合格へ読み替えない|
|T04|PASS_CURRENT_REVISION|現行版でFilterParameters原文保持、無修正貼付け・保存・2回実行・期待行照合を確認|
|T09|BLOCKED_CURRENT_PACKAGE_GENERATION|既存runtime probeは別証跡でPASSだが、現行packageの無修正Robin生成・受入は未確認|
|T10|PASS_CURRENT_REVISION_PRIMARY|現行版で変更範囲外行の逐語一致、無修正貼付け・保存・実行・成果物照合を確認|
|T01/T04/T10独立再試験|PASS_CURRENT_REVISION_INDEPENDENT|別チャット・別PADフローで現行版T01/T04/T10を再試験済み|

前回のCopilot Studio単体保存拒否と、M365 Copilot画面でAgent Builder項目が見えなかった事実は履歴として保持するが、今回の通常チャット検証の再開条件やBLOCKED理由にはしない。

### 受入マトリクス更新（2026-09-10）

上表は最終版指示ハッシュ `e467855137a1eec8655cfb6086f274e6a8e996412b3d07068f32c6912d9482c1` とbundle `431cdaa9c2ba34e217d848a0df0191d960608e04940674bca33f151cb1f62bc3` の状態を示す。T01〜T03、T05〜T08は最終版PAD実行を確認した。T04は最終生成の引用符差分、T09はWebAutomationタイムアウト、T10はWord SaveAsエラーを未完了として記録する。旧bundle／旧指示版の結果は履歴であり、最終版へ自動継承しない。

なお、T02/T03/T07向けの追加採取と索引更新後の旧結合版SHA-256は `660ae01fd6d7636711ec6efc68417d8d97dafb064b09405df25a6127d79393ca` である。T01/T02/T03/T05/T06/T07/T08/T10の旧版生成・実行結果は履歴として保持する。現作業版SHA-256は `431cdaa9c2ba34e217d848a0df0191d960608e04940674bca33f151cb1f62bc3`。

- T05: 編集可能Excelを開き、B2だけを変更して別名保存。元ブックA1/B2不変、出力B2=`T05-Changed`。
- T06: 編集可能Wordを開き、`OfficeCatalog`だけを`T06Replaced`へ置換して別名保存。元ファイルSHA不変。
- T07: PDF 2ページ範囲抽出→UTF-8保存を2回実行。`PAGE_TOKEN_A2`あり、`PAGE_TOKEN_A1`なし。
- T08: 存在しないファイルでErrorsGridに「ファイルが見つかりません」。後続アクションと出力はなし。
- T03: 全ファイル列挙→For each→`.txt`判定→UTF-8読取りを無修正貼付け・実行。最終対象が`.md`でもFileContentsは直前の`.txt`値のままで、対象外を読み取らないことを確認。
- T10: 既存16アクションのExcel書込み値とExcel出力名だけを変更。Excel A1=`T10-Changed`、Word/PowerPointは`CopilotOffice 246`保持。独立再試験も同結果。
- T02: 現行bundleのFilterDataTable条件付きRobinを無修正で新規PADフローへ貼り付け、保存・実行。ヘッダーとStatus=対象の2行を含むUTF-8 BOM CSVを確認し、入力fixture内容を保持した。

### 現行bundleの再生成照合（2026-09-10）

旧bundleの生成・実行記録は履歴として保持する。最終版の同一bundle再生成（知識プレチェック、T01〜T10）は `catalog/generated/normal-chat-*-final-*` と `catalog/evidence/normal-chat-final-package-acceptance-20260910.json` に保存した。T01〜T03、T05〜T08は最終版PAD実行、T04は引用符差分／完全一致拒否、T10はWord SaveAsエラーまでを記録した。T09は未完了である。

T04の拒否境界はbundle `2a0267d4…` 添付時に確認した。その後、PAD専用フローでExcel A1:C6→FilterDataTable→中間CSV→別xlsx保存の正例を2回実測した。正例証拠は `catalog/evidence/t04-positive-acceptance-20260910.json`、失敗出力保全は `catalog/evidence/normal-chat-t04-output-x000D-failure.xlsx`。ナレッジ正例を含む現作業版bundle `431cdaa9c2ba34e217d848a0df0191d960608e04940674bca33f151cb1f62bc3` でのT04通常チャット再生成・無修正PAD貼付け・2回実行を確認。

T09は `catalog/fixtures/ui/t09-local-test.html` を起動し、PAD UI要素ピッカーから入力・実行ボタン・結果段落を捕捉した。無修正6アクションを空フローへ貼付け・保存し、再コピーのアクション行一致を確認したが、元フロー・貼付けフローのWebAutomation実行は完了せず停止した。`AttributeValue=T09-clicked` は未観測である。現行貼付け先を90秒再probeしたところ、112秒時点でも実行中で、入力・クリック・結果取得・終了のエラー表示と`未実行`プレースホルダーが残ったため、停止ボタンを一度だけ押して準備完了へ戻した。これは既存のWAIT=1秒成功probeとは別の失敗境界である（`catalog/evidence/t09-capture-source-20260910.json`、`t09-final-paste-acceptance-20260910.json`、`t09-runtime-block-20260910.json`、`catalog/evidence/p3-t09-current-runtime-reprobe-20260911.json`）。

T02ではPADのFilter DataTable設定画面で列／インデックス=`2`、演算子=`と等しい (=)`、値=`対象`を入力し、先行CSV読取りとCSV書出しを含む新規フローで保存・2回実行した。条件付きRobin原文と成果物は `catalog/actions/datatable-filter/status-equals-index2.robin`、`catalog/flows/datatable-filter/roundtrip.robin`、`catalog/evidence/normal-chat-t02-final-pad-run.json` に記録した。先行アクションなしの未解決入力試行は `catalog/evidence/filter-t02-condition-config-attempt.json` に失敗境界として分離している。

## 未対応・未確認

- A〜Gの必須チェックには未観測項目が残る（coverage.json参照）。必須項目のBLOCKED／未確認が残るため、目標は未完了。
- 通常チャットの7原本個別添付は一対一完了を確認できず、結合版へ切り替えた。最終版結合版の直接添付・本文送信・知識プレチェック・T01〜T10生成と、T01〜T03/T05〜T08のPAD受入を完了した。T04/T09/T10と独立最終版受入は未完了。
- Agent Builderの登録・検索・指示遵守・実行環境差は今回の別環境確認事項。
- PR #19は既にsquashマージ済み。今回の再開確認では新規push・PR・merge・公開・旧アプリの機能拡張は実施していない。

## 次の再開手順

1. T04について、生成モデルが引用符を含む9行原文を完全一致で返せるか再試験する。保証できない場合はコードを出さない現在のfail-closedを維持する。
2. T09のブラウザー拡張／WebAutomation実行環境を復旧し、UI要素3件の通し実行を確認する。
3. T10は既存16行のパス・エスケープを文字単位で保持する独立生成を行い、Excel/Word/PowerPointを実行・照合する。
4. T01・T04・T10の独立再試験を最終指示ハッシュで行い、負例とともに受入証拠へ追記する。

### 現作業版の原文保持是正（2026-09-10）

開始時のmainは `69fe344`、作業ブランチは `codex/issue-5-acceptance-20260910b`。PAD 2.71.115.26224、Edge 152.0.4191.66、Office 16.0.20326.20132、日本語UI、Power Fx OFF（既存採取条件）を現物／記録で突合した。Trusted RPCは `sky` 未構成のままで、UIAによる既存成功と混同していない。保護資料のSHA-256は開始前後一致。

最初にT04/T10の原文を比較し、差分の段階を `catalog/evidence/normal-chat-raw-provenance-20260910.json` へ保存した。T04先行成功は測定済みFilterParametersの6引用符を保持し、最終v5だけが生成時に7引用符へ変化した。T10は入力原文から許可変更の2行以外にWord/PowerPoint保存パスが変化し、PAD再コピーは`_`を除いた別段階の正規化だった。`tests/Test-RobinRawContracts.ps1` の6 assertionsはPASSであり、生成Robinを正解へ書き換えていない。

指示文へT04構造化引数の逐語複写、T10添付原文の変更範囲外逐語保持を追加し、T04/T10の技術資料へ正本行と失敗段階を追記した。7原本を `tools/Build-KnowledgeBundle.ps1` で再結合し、原本対応は `copilot/knowledge-bundle-manifest-20260910b.json` に固定した。現作業版は指示SHA-256 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`、bundle SHA-256 `4282e4ece4f2d79ce26e85143fcab201091b185d9ee5d9defe4d8f49a4a7b2cd`、UTF-16 3,949。パッケージ検査86 observed actions、カタログ77 checks、差分検査はPASS。

現作業版は別CDPセッションでbundleと合成Excelを実添付し、T04生成・無修正PAD貼付け・保存・2回実行まで確認した（`catalog/evidence/t04-current-revision-acceptance-20260910.json`）。T10も現行bundleと機械的コンテキスト添付で生成し、変更範囲外行の逐語一致、無修正PAD貼付け・保存・実行、3成果物の照合まで確認した（`catalog/evidence/t10-current-revision-acceptance-20260910.json`）。別の新規チャット・新規PADフローによるT10独立再試験もPASSした（`catalog/evidence/t10-current-revision-independent-acceptance-20260910.json`）。ブラウザー拡張CUAのfile chooser失敗は `catalog/evidence/m365-current-package-upload-block-20260910b.json` に履歴として残す。T09ローカル画面の要素と結果文字は到達性として再確認したが、PAD WebAutomation実行の証拠ではない（`catalog/evidence/t09-current-environment-20260910b.json`）。旧版 `431c...` の生成・PAD結果は履歴として保持し、現作業版T01〜T03/T05〜T09・独立T01/T04・負例へ継承しない。Issue #5は `partial` を維持する。
T10の一括2ファイル添付はbundleのみが添付され生成前に停止した。失敗証拠は `catalog/evidence/normal-chat-current-revision-t10-batch-attachment-failure-20260910.json` に保全し、単一コンテキスト添付でのT10一次受入と混同しない。

P3残課題は `catalog/coverage.json` の `p3_blocked_items` に11件を追加し、真の外部依存（PAD Designerの追加・コピー、WebAutomation拡張ハンドシェイク、Trusted RPC）を項目ごとにBLOCKEDとしている。既存のCSV／Office／PDF等の証跡を未採取用途へ拡張せず、候補名・静的確認・手動DOM観測を実行成功に読み替えていない。

現作業版の追補判定は、T01〜T07、T04/T10一次、T01/T04/T10独立、知識precheck、fail-closed負例を確認済み、T08を生成形式失敗、T09を現行package生成未確認とする。既存専用フローのT09ランタイムprobe（待機値1秒の一時変更・復元）は `catalog/evidence/t09-runtime-probe-20260910.json` に分離した。詳細は `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` に固定した。

未採取構文・UI依存の負例（Else／ループ脱出、非空DataTable行・セル、未登録Webセレクター／WebDriver）を現行bundleの新規通常チャットで実施し、3件ともRobinコードを出さず、不足するPAD原文・設定・実行証拠と禁止すべき後続処理を回答した。証跡は `catalog/evidence/normal-chat-current-revision-negative-suite-20260910.json`。これはT08の形式失敗やT09の通し実行を合格へ変えるものではない。

現作業版のケース別判定は `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` に固定し、T04/T10一次受入・T04/T10独立再試験PASS、知識precheckは参照確認PASS、その他は未実行またはBLOCKEDとして旧版成功を継承しない。

P0〜P5の要件監査表は `catalog/evidence/issue5-completion-audit-20260910.json`。P4はT04/T10一次受入、T04/T10独立再試験、知識precheckを現作業版で確認済みで、残りは未実行である。T04/T10貼付け時の可視6件は仮想化による偽陰性で、Designerの総アクション数（9／16）を確認して保存・実行した。

### 最新P3実測追補（2026-09-10）

日時加算は `DateTime.Add ... TimeUnit.Days` を新規専用フローへ追加し、原文コピー・保存・2回実行、`2026/09/11 0:00:00` を確認した（`catalog/evidence/p3-date-add-probe-20260910.json`）。

サブフローは `P3Worker` を作成し、Mainから `CALL P3Worker` で呼び出した。Workerのタイムアウト付きメッセージは2回とも `ButtonPressed=OK` で完了した（`catalog/evidence/p3-subflow-probe-20260910.json`）。Error blockでは欠損ファイル子アクションを1回実行し、Main line 2のruntime errorと後続非実行を確認した（`catalog/evidence/p3-error-trigger-probe-20260910.json`）。これらのprobeは現行bundle未統合である。カスタムエラーハンドラー、入れ子、DataTable成功構文、Excel反復などは未確認のまま保持する。

DataTableは3列1行（`A/10/対象`）の作成を新規専用フローでコピー・保存・2回実行し、`1 行, 3 列`を確認した。行追加・行反復・セル参照の成功構文は未確認であり、5列に1値を渡すnative runtime errorとビジュアライザー復帰失敗は別の失敗証跡として保持する。現行失敗フローのUIではDataTable `0 行, 0 列`、RowValues `[A, B]`、2値対0列エラーを読み取り、直後の失敗Robin原文をコピーしてSHA `e0088169fdbe6490453ff926a488b9ca21c912f5632c00e47a5fc09be30db7d0`で固定した（`catalog/evidence/p3-datatable-create-success-20260911.json`、`catalog/evidence/p3-datatable-row-failure-20260910.json`、`catalog/evidence/p3-datatable-row-list-failure-20260910.json`、`catalog/evidence/p3-datatable-row-error-state-20260911.json`）。

リスト項目取得は、削除アクションが取得値を返さないことを再確認した。現行の専用フローでActionsTreeViewの読取りインベントリを実行したが、仮想化スクロールが終端で揺れ続け、401ノード以上を観測した時点で停止した。検索語「項目」では追加・削除・重複削除・共通項目検索・DataTable項目更新だけが表示され、専用取得アクションは観測されなかった。ただし式参照等の別方式までは否定せず、原文・実行証拠は未確認として維持する（`catalog/evidence/p3-list-remove-probe-20260910.json`、`catalog/evidence/p3-list-get-inventory-boundary-20260911.json`、`catalog/evidence/p3-list-get-search-boundary-20260911.json`）。

Excelの専用probeでは、合成`excel-catalog.xlsx`の`Sheet1`を選択し、A1:C6をTypedValuesで読み取り、Designer上で`ExcelData=6行, 3列`・エラー0を確認した。Run監視ヘルパーの完了表示は45秒以内に観測できなかったため、範囲読取りはUIプレビュー成功・完了通知未確認として分離し、Excelデータ反復は未確認のまま保持する（`catalog/evidence/p3-excel-read-range-probe-20260911.json`、`p3-excel-read-range-probe-20260911.robin`）。

DateTimeカスタム書式化の専用probeでは「現在の日時／システム タイム ゾーン」選択をUIで確認したが、保存更新時にPAD内部例外 `System.InvalidOperationException: Sequence contains no matching element`（`FunctionModel.GetProgramItem`）が発生した。ダイアログ選択や例外画面は成功Robin・実行値の証拠ではないため、カスタム書式化は未確認のまま保持する（`catalog/evidence/p3-date-format-dialog-crash-20260911.json`）。

エラー処理専用probeでは、名前付きカスタムエラー`FileNotFound`に変数設定ルール（`ErrorHandled=true`）を追加し、続行ON／スローOFFへ設定したが、欠損ファイル実行はなおruntime errorとなった。既定の「すべてのエラー」へ`ErrorHandledDefault=true`を設定し、続行ON／スローOFFとした別probeは2回ともtrueプレビューで完了した。名前付きルールの一致条件や他のエラーへの一般化、現行bundle統合は未確認として分離する（`catalog/evidence/p3-error-custom-handler-20260911.json`、`p3-error-custom-handler-flow-20260911.robin`、`p3-error-default-handler-20260911.json`、`p3-error-default-handler-flow-20260911.robin`）。
Excelの専用probeでは、合成`excel-catalog.xlsx`の`Sheet1`を選択し、A1:C6をTypedValuesで読み取り、Designer上で`ExcelData=6行, 3列`・エラー0を確認した。Run監視ヘルパーの完了表示は45秒以内に観測できなかったため、範囲読取りはUIプレビュー成功・完了通知未確認として分離した。For eachの設定は保存後に消える試行と、読み取り前にループが置かれる失敗原文を別証跡へ保存し、Excelデータ反復は未確認のまま保持する（`catalog/evidence/p3-excel-read-range-probe-20260911.json`、`p3-excel-read-range-probe-20260911.robin`、`p3-excel-foreach-configuration-boundary-20260911.json`）。

### 静的ゲート追補（2026-09-11）

HEAD `b411a7c`でRaw契約6 assertions、Copilot package（指示3,949 UTF-16／7原本／86 observed actions）、Robin catalog 84 checks、bundled DOM 898 checks、`git diff --check`を再実行してPASSした。`tests/Test-Copilot.ps1`は30秒タイムアウト履歴のため未完了扱いとし、T08/T09の現行パッケージ受入やP3統合をPASSへ読み替えていない（`catalog/evidence/current-package-static-check-20260911.json`）。

最新HEAD `1cd329c`でも同じ静的ゲートを再実行してPASSした。対象ハッシュは不変で、`tests/Test-Copilot.ps1`のタイムアウトとT08/T09・P3の未完了判定も維持する（`catalog/evidence/current-package-static-check-20260911b.json`）。

最新HEAD `f308d90`でも同じ静的ゲートを再実行してPASSした。既定エラーハンドラーprobeは別証跡で成功したがbundle未統合であり、T08/T09と残るP3は未完了のままとする（`catalog/evidence/current-package-static-check-20260911c.json`）。

### P3追補統合版（2026-09-11）

7原本へ、既定エラーハンドラーの2回成功、DataTable作成、ファイル／制御／Excel範囲読取りの実測根拠と、未確認・失敗境界を統合した。bundle SHA-256は `0c89e53ce84671fd4bf1da4287563bf79f5164674f22907c8a420758310b36e6`、マニフェストは `copilot/knowledge-bundle-manifest-20260911.json`。統合後の通常チャット知識precheck、T01〜T10、T01/T04/T10独立再試験は未実行で、旧bundle証跡を新bundleのPASSへ付け替えない（`catalog/evidence/current-package-status-20260911-p3-integration.json`）。

T09の90秒再probe（112秒時点で実行中、WebAutomationエラーと`未実行`表示後に停止）をP3統合版へ追加し、bundle SHA-256を `513fe84b8bc1fe3acb9d9092f057bace4d47215fe2cb30945b23d3ff77685831`、マニフェストを `copilot/knowledge-bundle-manifest-20260911b.json` に更新した。新bundleの知識precheck、T01〜T10、独立再試験は未実行である（`catalog/evidence/current-package-status-20260911-p3b-integration.json`、`catalog/evidence/p3-t09-current-runtime-reprobe-20260911.json`）。

Indexの旧版「未確認」記述をP3現行判定へ揃え、Office範囲読取りとT09再probe境界を反映したbundle SHA-256を `e35fa2f4a960841603cc876ad2e1e8af254ff66afc97b297224ffb3c44d08644`、マニフェストを `copilot/knowledge-bundle-manifest-20260911c.json` に更新した。新bundleの知識precheck、T01〜T10、独立再試験は未実行である（`catalog/evidence/current-package-status-20260911-p3c-integration.json`）。

P3統合版をHEAD `7b06805`で静的検査し、Raw 6、Package 3949/7/86、Catalog 84、DOM 898、`git diff --check`をPASSした。新bundleのCopilot/PAD受入はまだ未実行である（`catalog/evidence/current-package-static-check-20260911-p3.json`）。

最新HEAD `2da9610`でもP3統合版の同じ静的ゲートを再実行してPASSした。新bundleのCopilot送信とT01〜T10受入は未実行である（`catalog/evidence/current-package-static-check-20260911-p3b.json`）。

最新HEAD `0ce051b`でもT09停止境界を含むbundleの同じ静的ゲートを再実行してPASSした。新bundleのCopilot送信とT01〜T10受入は未実行である（`catalog/evidence/current-package-static-check-20260911-t09.json`）。

同じ現行版で`tests/Test-Copilot.ps1`も完走し、304件のオフライン／モック契約検査をPASSした。ライブM365 Copilot／Edge統合ではないため、新bundleの知識precheck・T01〜T10・T08/T09受入は未完了のままとする（`catalog/evidence/current-package-static-check-20260911-t09b.json`）。
