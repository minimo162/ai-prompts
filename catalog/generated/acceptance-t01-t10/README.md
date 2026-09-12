# 通常M365 Copilotチャット受入試験 T01〜T10（継続中）

## 作業版（2026-09-12、finald-20260912、P3統合・同一版受入は未実施）

指示文 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`（不変）／bundle `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`（マニフェスト `copilot/knowledge-bundle-manifest-20260912d.json`）。直前版 finalc `f42f5acf4232b132b0a5b5bde469b25bf91d04f4cdb0a6823b17806d4ff85089` との差分は、P3-1〜P3-6の実測結果（リスト添字1、If内If／入れ子ループとEXIT LOOP／NEXT LOOPの作用範囲、`.TXT`／`.txt.bak`／親フォルダー名／サブフォルダー境界、Excel／Word SaveAsの無警告上書き、カスタム日付書式 `yyyy-MM-dd`、アクション単位の名前付きエラー `ON ERROR FileNotFoundError`）を7原本へ統合したことです。各probeは専用合成フローで2回実行し、リスト・入れ子・日付・エラーは別空フローへの再利用まで確認済み（`catalog/evidence/p3-*-acceptance-20260912.json`）。

この版で完了しているのは知識precheck（`catalog/evidence/current-bundle-finald-precheck-20260912.json`、Robinなし）だけです。T01〜T10、独立再試験T01/T04/T10、負例v2（N1をIf内If＋副作用＋脱出から3段入れ子・外側脱出へ差し替え。旧N1は正例P3-2へ）、P3正例P3-1〜P3-6（`catalog/generated/acceptance-p3-20260912/cases.json`）は、送信本文と専用PADフロー（`RobinKnowledge*FinalD_20260912`）を用意した段階で**未送信・未受入**です。finalcの合格はこの版へ継承しません。状態の正本は `catalog/evidence/current-package-status-20260912-finald.json`（partial）と `issue5-completion-audit-20260912-finald.json`。

| 区分 | finald判定 | 証跡 |
| --- | --- | --- |
| 知識precheck | PASS_REFERENCE_ONLY | `catalog/generated/normal-chat-finald-20260912-precheck/` |
| T01〜T10 | NOT_RUN（本文・フロー準備済み） | `catalog/generated/normal-chat-finald-20260912-t01`〜`t10/` |
| 独立再試験 T01/T04/T10 | PENDING | 同上 `-independent/` |
| 負例 v2 N1〜N3 | PENDING（期待を事前固定） | `catalog/generated/normal-chat-finald-20260912-negative-suite/expectation.json` |
| P3正例 P3-1〜P3-6 | PENDING（期待を事前固定） | `catalog/generated/normal-chat-finald-20260912-p31`〜`p36/expectation.json` |

## 直前の受入済み版（2026-09-12、finalc-20260912）

指示文 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`／bundle `f42f5acf4232b132b0a5b5bde469b25bf91d04f4cdb0a6823b17806d4ff85089`（マニフェスト `copilot/knowledge-bundle-manifest-20260912c.json`）を同一版として固定しました。直前版 `32aea4560df7a7530cd9fe1fab996181236ee8a0c34213adfffb3f022dbfc041` との差分はT09教材の待機値のみです（`WAIT 500`＝500秒は2026-09-10採取時の500ミリ秒のつもりの誤設定。待機ダイアログで1秒へ直した再採取原文 `WAIT 1` を教材にし、2回実行で数秒完了を確認）。

受入はすべて、通常のM365 Copilotチャット（Google Chrome、Claude in Chrome拡張で操作、モデル表示 Think Deeper）で新規会話ごとに指示全文を本文へ入力し、同版bundleと`agent-instructions.txt`（T10はbundleとT10文脈結合版 `b1330a10…`）を実添付して行いました。本文は送信前にSHA-256で全文一致を確認しています。生成Robinは無修正で専用PADフロー（`RobinKnowledge*FinalC_20260912`）へ貼付け・保存・再コピーし、2回実行して固定期待値と照合しました。T09の依頼文だけは `WAIT 500` を指定する文言を「ナレッジで確認済みの待機（`WAIT`、単位は秒）」へ改め、期待値（`AttributeValue=T09-clicked`、ブラウザー終了）は変えていません。

| ケース | 最終版判定 | 生成回数 | 証跡 |
| --- | --- | --- | --- |
| 知識プレチェック | PASS_REFERENCE_ONLY（Robinなし。T03拡張子、T09の待機1秒再採取と要素取り込み、リスト添字を正しく参照） | 1 | `catalog/generated/normal-chat-finalc-20260912-precheck/`、`catalog/evidence/current-bundle-finalc-precheck-20260912.json` |
| T01 | PASS（出力90 bytes SHA `2b030f2d…`、入力不変） | 1 | `catalog/evidence/t01-finalc-20260912-live-acceptance-20260912.json` |
| T02 | PASS（ヘッダー＋Status=対象2行、SHA `8f0748cc…`、入力不変） | 1 | `catalog/evidence/t02-finalc-20260912-live-acceptance-20260912.json` |
| T03 | PASS（13行、`.Extension = '.txt'`、TxtCount=2／OtherCount=2、入力4件不変） | 1 | `catalog/evidence/t03-finalc-20260912-live-acceptance-20260912.json` |
| T04 | PASS（初回生成で形式契約を満たし、3行3列・入力SHA不変） | 1 | `catalog/evidence/t04-finalc-20260912-live-acceptance-20260912.json` |
| T05 | PASS（B2=T05-Changed、A1他不変、入力不変） | 1 | `catalog/evidence/t05-finalc-20260912-live-acceptance-20260912.json` |
| T06 | PASS（OfficeCatalog→T06Replaced、本文他不変、入力不変） | 1 | `catalog/evidence/t06-finalc-20260912-live-acceptance-20260912.json` |
| T07 | PASS（PAGE_TOKEN_A2あり／A1なし、入力不変） | 1 | `catalog/evidence/t07-finalc-20260912-live-acceptance-20260912.json` |
| T08 | PASS（期待エラー：名前付きFileNotFound＋既定ハンドラーの9行。既定経路でtrue、LastError=ファイルが見つかりません。名前付き一致は未確認のまま） | 1 | `catalog/evidence/t08-finalc-20260912-live-acceptance-20260912.json` |
| T09 | PASS（生成6行の待機は `WAIT 1`。要素取り込み後の無修正貼付け・2回実行で `T09-clicked`、ブラウザー終了） | 1 | `catalog/evidence/t09-finalc-20260912-live-acceptance-20260912.json` |
| T10 | PASS（16行中2行のみ変更、Excel A1=T10-Changed、Word/PowerPointは`CopilotOffice 246`保持） | 1 | `catalog/evidence/t10-finalc-20260912-live-acceptance-20260912.json` |
| 独立再試験 T01/T04/T10 | PASS（別チャット・別PADフロー） | 各1 | `catalog/evidence/t01-finalc-20260912-independent-acceptance-20260912.json`、`t04-…`、`t10-…` |
| 負例 N1〜N3 | PASS_NEGATIVE_FAIL_CLOSED（コードフェンス0、Robin命令0、回答全文を保存） | 1 | `catalog/evidence/negative-suite-finalc-20260912-acceptance-20260912.json` |

状態の正本は `catalog/evidence/current-package-status-20260912-finalc.json` と `catalog/evidence/issue5-completion-audit-20260912-finalc.json` です。以下の節は旧版（final-20260912 `32aea4560df7a7530cd9fe1fab996181236ee8a0c34213adfffb3f022dbfc041`、P3b `dd668166…`、Final3 `2bc3f2b4…`、それ以前）の履歴であり、この最終版へ継承していません。


このフォルダーは、通常のMicrosoft 365 Copilotチャットへ最新版の指示文とナレッジ結合版を添付して行う受入試験の依頼文・期待値を固定する場所です。ここにある期待値は、生成回答に合わせて後から変更してはいけません。

## 実行前提

- 対象: ログイン済み通常M365 Copilotチャット。モデルは `GPT 5.6 Think Deeper` を明示選択する。Agent Builder／Copilot Studioは使わない。
- 入力: 各ケースで指定する合成データ、専用フォルダー、専用PADフロー。
- 手順: 新しい会話へ依頼 → 回答原文と生成コードを保存 → 手直しせずPADへ貼付け → 設定 → 保存・実行 → 成果物と期待値を照合。
- 失敗時: 元回答を上書きせず、原因分類と失敗位置を保存。指示・ナレッジを変更したら新しい会話で再試験。
- 以下の表は、指示文 `e467855137a1eec8655cfb6086f274e6a8e996412b3d07068f32c6912d9482c1`／bundle `431cdaa9c2ba34e217d848a0df0191d960608e04940674bca33f151cb1f62bc3` の履歴受入を保全したものです。原文保持規則を強化した現作業版は、指示文 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`／bundle `4282e4ece4f2d79ce26e85143fcab201091b185d9ee5d9defe4d8f49a4a7b2cd` で、T04は現作業版の通常チャット生成・無修正PAD受入までPASSしました。旧版のT01〜T03/T05〜T10生成・PAD結果を現作業版へ継承しません。T04/T10の差分発生段階は `catalog/evidence/normal-chat-raw-provenance-20260910.json`、結合版の再生成は `tools/Build-KnowledgeBundle.ps1` です。

## 固定ケース

| ID | 依頼の要点 | 固定した期待値 | 状態 |
|---|---|---|---|
| T01 | 日本語・引用符・`100%`・バックスラッシュを含む文字列を置換し、新しいUTF-8テキストへ保存 | 指定語だけ置換。特殊文字・改行・対象外文字を保持し、新規出力を確認 | PASS（最終版PAD 2回） |
| T02 | 日本語と引用符を含む合成CSVを読み、条件一致行だけ別CSVへ保存 | 条件一致行と列・引用符を保持。入力CSVは不変 | PASS（最終版PAD 2回） |
| T03 | 複数の合成ファイルをFor eachで処理し、名前または拡張子で分岐 | 各ファイルを一度ずつ処理。条件外は対象外経路。未採取のFor each構文を捏造しない | PASS（最終版PAD 2回） |
| T04 | Excel範囲を読み、条件一致行または集計結果を別ブックへ保存 | 指定範囲だけを読み、別ブックの期待セルと値を照合 | PARTIAL（最終生成の引用符差分、先行有効版はPASS） |
| T05 | 既存の合成Excelで指定セル／範囲だけ修正し、別名保存 | 指定セルだけ変更。無関係なセルと元ブックのハッシュを保持 | PASS（最終版PAD 2回） |
| T06 | 合成Wordの指定文字列を置換して別名保存（または採取済みPowerPoint生成例） | 指定箇所だけ置換し、本文・保存形式を照合 | PASS（最終版PAD 2回） |
| T07 | 合成PDFの指定ページのテキストを抽出して保存 | 指定ページ識別文字とページ対応を照合。ページ境界を推測で整形しない | PASS（最終版PAD 2回） |
| T08 | 存在しない入力ファイルを意図的に処理 | 期待したエラー経路・記録だけを確認し、依存する後続処理を実行しない | PASS（最終版の期待エラー） |
| T09 | 安全なローカル画面で文字入力→クリック→待機→文字取得 | 対象UI要素の登録手順と取得文字を明示。未確認セレクターを出さない | PARTIAL（UI要素捕捉・貼付けPASS、WebAutomation実行タイムアウト） |
| T10 | 動作確認済み既存フローを渡し、条件1つと出力名だけ変更 | 指定変更のみ反映し、既存の入力・変数・別処理・エラー経路を保持 | PARTIAL（最終版Word SaveAsで停止、独立再試験待ち） |

上表は履歴版の判定です。現行P3b bundleではknowledge precheck、T01、T02、T04〜T08、T10を`PASS_CURRENT_BUNDLE`（T08は期待エラー）として記録し、T01/T04/T10の独立再試験と負例スイートも完了しています。T03は厳密な拡張子／名前取得の原文が未採取でRobinなし、T09はUI要素登録・WebAutomation通し実行が外部依存でブロック中です。

2026-09-11現在の新しい最終配布候補は、指示文 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`／bundle `61f040b900dfc90fe395f21426bc7a684c7dbf45c2ac82e38d1f00490ffc2f6b` です。T08エラー記録のPAD採取結果とT01測定済み組み合わせ参照を反映し、末尾空白の差分警告を除いた最終候補を再構築しました。前版c78fd3のT08受入は履歴として保持し、最終2版の知識precheck、T08、T01受入はこれから実施します。旧e35fa2f4／38640a／d7a0a7／c78fd3版の結果をこの候補へ継承しません。新候補の状態は `catalog/evidence/current-package-status-20260911-final2.json` と `catalog/evidence/issue5-completion-audit-20260911-final2.json` で管理します。

## 現行Final3固定版（2026-09-11）

指示文 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`／bundle `2bc3f2b4c5c709e94547ccf4b75f7084c9c424605781e01414f6783a1fd026a7` を同一版として固定しました。知識precheckはPASS_REFERENCE_ONLY、T01〜T08とT10は通常M365 Copilot送信→有効Robin無修正貼付け→保存→2回PAD実行→成果物照合まで受入済みです。T01/T04/T10は別チャット・別PADフローの独立再試験も受入済みです。T09は6アクションの送信・貼付け・保存・再コピーまでは確認しましたが、捕捉済みUI要素が新規PAD実行時に見つからずRun開始前に停止したため未受入です。P3の未統合・未確認項目も残るため、状態は `partial／OPEN` を維持します。詳細は `catalog/evidence/current-package-status-20260911-final4.json` と `catalog/evidence/issue5-completion-audit-20260911-final4.json` を参照してください。

## 現行bundleのライブ進捗（2026-09-11）

| ケース | 現行bundle判定 | 証跡 |
| --- | --- | --- |
| T01 | PASS_CURRENT_BUNDLE（Copilot送信、Robin原文保存、専用PAD貼付け・保存、2回実行、出力／入力照合） | `catalog/evidence/t01-current-bundle-live-send-20260911.json`、`catalog/evidence/t01-current-bundle-pad-output-comparison-20260911.json` |
| T02〜T10 | NOT_RUN／PARTIAL（旧版結果を継承しない） | `catalog/evidence/issue5-completion-audit-20260911.json` |

T01のRobin原文、PAD再コピー、run1/run2は `catalog/generated/normal-chat-current-bundle-t01-live-20260911/` と `catalog/evidence/t01-current-bundle-pad-*.json` に保存しています。Copilot原文Robin（LF）とPAD再コピー（CRLF）は別ファイルとして保持し、改行を正規化した本文一致だけを確認しました。

P3追補：DataTableの列数一致RowToAdd入力は `RobinKnowledgeP3DataTableRow_20260911` で実測し、2回とも2行3列のプレビューとエラーなしを確認しました。`catalog/evidence/p3-datatable-row-success-20260911.json` に保存し、原文・型・変数参照を新bundleへ統合しました。新bundleの通常チャット／PAD受入は別途必要です。

P3追補：`RobinKnowledgeP3DataTableCell_20260911` で `ModifyDataTableItem` の列2・行0更新を2回実行し、値ビューアーで `CellChanged` を確認しました。`catalog/evidence/p3-datatable-cell-success-20260911.json` に保存し、新bundleへ統合しました。新bundleの通常チャット／PAD受入は別途必要です。

P3追補：DataTable行反復は `RobinKnowledgeP3DataTableForeach_20260911` で2行3列を`LOOP FOREACH`し、ブレークポイント由来の初回停止を分離した後、2回とも最終行`B / 20 / 対象2`・2行3列・エラーなしを確認しました。Excel行反復も `RobinKnowledgeP3ExcelForeachRuntime_20260911` でA1:C6を`ExcelData`へ読み取り、`CurrentItem`を`ExcelRowSeen`へ設定する5アクションを2回実行し、最終行`対象外 / E / 40`・6行3列・Excel終了・エラーなしを確認しました。原文・境界・成功条件を新bundleへ統合し、新bundleの通常チャット／PAD受入は別途必要です。

## 2026-09-11 P3教材統合後の新bundle（再受入待ち）

P3で測定済みだったDataTable行追加・セル更新・行反復とExcel行反復の原文・設定・境界を7原本へ統合し、bundle SHA-256を `dd668166e4c04b02878a6fae65e4583b6d6c910847559161c6707ae90e6626a5`、マニフェストを `copilot/knowledge-bundle-manifest-20260911h.json` に固定しました。Final3固定版 `2bc3f2b4c5c709e94547ccf4b75f7084c9c424605781e01414f6783a1fd026a7` のT01〜T08/T10、独立T01/T04/T10、負例、T09停止証跡は履歴として保全し、新bundleへ継承しません。

新bundleの知識precheck、T01〜T10、独立再試験、負例は `NOT_RUN_NEW_BUNDLE` です。P3のカスタム日時書式、リスト項目取得、入れ子／branch side effect、名前付きカスタムエラー一致は未確認です。T09は別空フロー `RobinKnowledgeT09Separate_20260911` で6アクション貼付け・保存まで確認しましたが、UI要素ピッカーはEdge Window/Paneのみを返し、`Input text 't09-input'`、`Button '実行'`、`Paragraph '未実行'`を登録できず、エラー3件・Start無効のため実行開始前に停止しました（`catalog/evidence/t09-separate-ui-registration-20260911.json`）。

T09追補：Edge用PAD拡張・native manifest origin・`nativeMessaging`権限は読み取りで存在を確認しましたが、BrowserNativeMessageHostログは起動成功だけで接続完了を示さず、現在のhostプロセスはChrome用originでした。T09 WebAutomation成功の根拠ではなく、拡張接続境界の診断証跡として `catalog/evidence/t09-extension-handshake-boundary-20260911.json` に保存しています。

T08 P3追補：PADの「最後のエラーを取得」を保存先`LastError`・エラー消去`On`で設定し、原文`ERROR => LastError Reset: True`を無修正再コピーした。欠損ファイルを含むエラー処理probeは2回とも`true`と「ファイルが見つかりません」のプレビューで完了した。ブロック原文とLastError原文は別々のPAD採取であり、組合せ参照は単一clipboard rawではない。現行bundle未統合のため、T08の通常Copilot生成・無修正PAD受入はまだ未完了です（`catalog/evidence/p3-error-handler-measured-20260911.json`）。

現作業版の固定サマリは `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` です。

現作業版の追補：T01〜T07、T04/T10一次受入、T01/T04/T10独立再試験はPASS_CURRENT_REVISION。fail-closed負例はPASS_NEGATIVE_FAIL_CLOSED。T08は生成形式失敗、T09は既存専用フローのランタイムprobeのみPASSで、現行package Robin受入は未確認です。

P3追補：日時加算とサブフロー作成／呼出しは別の合成専用probeで原文コピー・保存・2回実行まで確認しましたが、カスタム日時書式化、エラー発生子アクション、カスタムハンドラー、未採取の構文は未確認として保持します。DataTable行追加・セル更新・行反復とExcel行反復はP3教材へ統合済みです。

現作業版bundleのみを添付した知識precheckは `catalog/evidence/normal-chat-current-revision-knowledge-precheck-20260910.json` に保存し、ナレッジ固有の設定・型・依存を回答原文と照合しました。これは受入ケースの代用ではありません。

現作業版T10一次受入は `catalog/evidence/t10-current-revision-acceptance-20260910.json`、別チャット／別PADフローの独立再試験は `catalog/evidence/t10-current-revision-independent-acceptance-20260910.json` に保存しています。T01独立再試験は `catalog/evidence/t01-current-revision-independent-acceptance-20260910.json`、T04独立再試験は `catalog/evidence/t04-current-revision-independent-acceptance-20260910.json` に保存しています。

現作業版T10の生成・無修正PAD貼付け・保存・実行・Office成果物照合は `catalog/evidence/t10-current-revision-acceptance-20260910.json` に保存しています。独立再試験も別チャット／別PADフローでPASSしています。

現作業版T04の生成・貼付け・保存・2回実行・成果物照合は `catalog/evidence/t04-current-revision-acceptance-20260910.json` と `catalog/evidence/t04-current-revision-pad-paste-20260910.json` に記録しています。貼付けヘルパーの可視6件は仮想化による偽陰性であり、Designerの「9 アクション」表示を確認しました。

## 2026-09-11 P3b同版T01受入

指示文全文（本文3949文字、末尾U+200B/U+200CのみUI付加）と同版bundle `dd668166e4c04b02878a6fae65e4583b6d6c910847559161c6707ae90e6626a5`を通常M365 Copilotへ添付し、T01の3アクションRobinを生成した。Robin SHA `2209d9ce9437c141345c3f01a0cfd12bd6d6ed4dd0668cf0a78ae17479c5ee47`は無修正で専用PADフローへ貼付け・保存・再コピーし、2回実行した。入力SHA不変、出力UTF-8 BOM・90 bytes・期待SHA `2b030f2d6d937aa11885509ebc60a55e40261087a2464dcc5ddd6cca8ad81bd2`一致を確認し、T01を`PASS_CURRENT_BUNDLE`とした。証拠は `catalog/evidence/t01-current-p3b-live-acceptance-20260911.json` と `t01-current-p3b-pad-output-comparison-20260911.json`。

T02も同一bundle・全文指示・2添付で新規通常チャット生成を行った。Robin SHA `c3027cfaa13e191b0e784fb3a6db4c573f8bfc83fb172d1a6394d7c1f5a55c29`を無修正で専用PADフローへ貼付け・保存・再コピーし、2回実行。出力はヘッダー＋Status=対象の2論理行、UTF-8 BOM・CRLF・末尾改行なし、入力SHA不変を確認し、T02を`PASS_CURRENT_BUNDLE`とした。証拠は `catalog/evidence/t02-current-p3b-live-acceptance-20260911.json` と `t02-current-p3b-pad-output-comparison-20260911.json`。
T03は同一bundle・全文指示・2添付で通常チャット送信したが、厳密な拡張子／ファイル名取得と末尾`.txt`一致を未確認としてRobinコードブロックを返さなかったため、`NOT_ACCEPTED_CURRENT_BUNDLE_NO_ROBIN`とした。生成物は`catalog/generated/normal-chat-current-bundle-p3b-t03-live-20260911/`に保存し、PADフローは作成・実行していない。

T04は同一bundle・全文指示・2添付で9アクションRobinを生成し、無修正で専用PADフローへ貼付け・保存・再コピー、2回実行した。Designerは9アクション（ListItem可視6件は仮想化）を示し、両回ともExcelData 6行3列、FilteredDataTable 3行3列、対象/A/10・対象/C/25・対象/D/5、入力SHA不変を確認した。出力xlsxはExcelメタデータによりSHAが変動するため論理行で照合し、直接パーサーの日本語表示は未正規化として注記した。証拠は`catalog/evidence/t04-current-p3b-live-acceptance-20260911.json`と`catalog/evidence/t04-current-p3b-pad-output-comparison-20260911.json`。
T05は同一bundle・全文指示・2添付で4アクションRobinを生成し、無修正で専用PADフローへ貼付け・保存・2回実行した。`ReadOnly=False`で既存xlsxを開き、B2だけを`T05-Changed`へ変更して別名保存し、出力B2・入力A1一致と元入力SHA不変を直接確認した。証拠は`catalog/evidence/t05-current-p3b-live-acceptance-20260911.json`と`catalog/evidence/t05-current-p3b-output-comparison-20260911.json`。

T06は同一bundle・全文指示・2添付で4アクションRobinを生成し、無修正で専用PADフローへ貼付け・保存・2回実行した。編集可能なWordで`OfficeCatalog`だけを`T06Replaced`へ置換して別名保存し、出力文書の置換結果と元入力SHA不変を直接確認した。証拠は`catalog/evidence/t06-current-p3b-live-acceptance-20260911.json`と`catalog/evidence/t06-current-p3b-output-comparison-20260911.json`。
T07は同一bundle・全文指示・2添付で2アクションRobinを生成し、無修正で専用PADフローへ貼付け・保存・2回実行した。ページ2のみを抽出し、`PAGE_TOKEN_A2`を含み`PAGE_TOKEN_A1`を含まないUTF-8テキストと入力PDF SHA不変を確認した。証拠は`catalog/evidence/t07-current-p3b-live-acceptance-20260911.json`と`catalog/evidence/t07-current-p3b-output-comparison-20260911.json`。
T08は同一bundle・全文指示・2添付で欠損ファイルのエラー処理Robinを生成し、無修正で専用PADフローへ貼付け・保存・2回実行した。両回とも`ErrorHandledDefault=true`と`LastError`のファイル不存在内容を確認し、書込み・公開処理は含めなかった。名前付き`FileNotFound`一致は未確認として保持した。証拠は`catalog/evidence/t08-current-p3b-live-acceptance-20260911.json`と`catalog/evidence/t08-current-p3b-output-comparison-20260911.json`。
T10は同一bundle・全文指示・現行T10コンテキスト添付で16命令Robinを生成し、無修正で専用PADフローへ貼付け・保存・2回実行した。Excelの書込み値とSaveAs先だけが変更され、Word／PowerPointの`CopilotOffice 246`と既存処理を保持した。Excel A1、Word本文、PowerPointスライドを直接照合し、Designer 16アクション（ListItem可視6件は仮想化）を確認した。証拠は`catalog/evidence/t10-current-p3b-live-acceptance-20260911.json`と`catalog/evidence/t10-current-p3b-output-comparison-20260911.json`。

## 独立再試験

最終版を固定した後、T01・T04・T10をそれぞれ別の新しい会話で1回ずつ実施した。T01/T04/T10独立再試験は現行版でPASS済み。初回結果と最終版結果を混ぜない。

現作業版では `catalog/evidence/pad-native-ui-blocked-20260910.json` のとおり、PADプロセスは起動したがnative Computer Use Trusted RPCが未構成である。T04はUIAフォールバックで正例の2回実行まで確認した。T09は `catalog/evidence/t09-runtime-block-20260910.json` のとおりUIA捕捉・貼付け・保存は確認したが、WebAutomation実行完了は未確認である。
