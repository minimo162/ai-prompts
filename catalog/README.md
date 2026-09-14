# PAD実アクションのRobinカタログ

## 2026-09-15 T10既存応答の限定再取得

T10-STRICT-20260914Xの残枠を使い、固定一次・独立会話の既存応答を各1回要求・1回完了しました。ブラウザー前提確認は1回成功。UTF-16LE／UTF-8のSHAを取得時に固定し、既存保存補助で新規保存した1752／1771 bytesは取得文字列と一致しました。許可2か所の内容も依頼一致ですが、どちらもLF16個・末尾LFありで、固定入力のCRLF・末尾改行なしと区間外bytesが異なるため、両strictは `NOT_PROVEN`です。[取得原文・区間比較・回数](evidence/t10-strict-20260914x-recapture-results.json)。

これはDOM文字列から保存ファイルまでの観測であり、モデル内部や通信上の元バイトの証明ではありません。保存器の追加改行を直しても今回の差は解消していません。PAD Run・新規送信・クリップボード変更は0回。元の各1回枠は消化済みで、新IDによる再取得はしません。再開には、未観測の上流を区別する別仮説と新たな明示的上限が必要です。C・独立T04新pair受入と旧原証跡を保ち、#5全体と#27最終版は別判定でOPEN / partialです。

## 2026-09-14 T10厳密比較と保存経路の限定検証（20260914x）

許可された2/4行目の値・保存先の内容区間だけを除外し、その前後すべての生バイトを位置ずれ付きで比較する判定器を追加しました。合成正例2件・負例12件と元SHA拒否、保存器4検査は非ライブPASSです。過去のNOT_PROVEN回帰は保持しています。

過去に使ったファイル追加パッチと同じ処理へ既知の18 bytesを1回通すと、末尾LFが追加され19 bytesになりました。文字列を直接UTF-8保存する補助では18 bytesのままです。この局所対照は通常チャット全経路の証明ではありません。ブラウザー一覧取得がタイムアウトし、実応答の追加取得は一次0・独立0。既存保存回答は依頼内容一致、許可区間外のバイト不一致で、両方strict `NOT_PROVEN`です。PAD Run・Copilot送信・クリップボード変更はいずれも0回。クリップボード全形式の生バイト同一は未評価のままです。

[比較器・対照・取得境界・再開条件](evidence/t10-strict-20260914x-audit.json)。次はブラウザーの読み取りが利用可能な時に、固定した既存2会話の応答を各最大1回、文字列段階のSHAと新保存ファイルへ対応付けます。新規送信は不要・未許可とし、不一致なら保持します。C・独立T04新pairの受入を保ち、#5全体追跡と#27最終版受入はともにOPEN / partialです。

## 2026-09-14 独立T04の新Runペア（20260914w）

保存済み20260913e独立生成を無修正で専用空フローへ配置し、9アクションを保存・再コピーして最大2 Runを実施しました。Run1のCSV/xlsxを独立保存し、3行3列（対象/A/10、対象/C/25、対象/D/5）と入力SHA不変を検証してからRun2を開始し、Run2も一致しました。[新pair原証跡](evidence/t04-independent-pair-20260914w/acceptance.json)。旧Run1 `NOT_CAPTURED`・旧候補 `candidate_partial`・元T04不成立は保全し、同じ独立生成を一次T04へ二重計上しません。

今回PAD 2 Run・Copilot送信0・C/T10再Run0。20260913eと保護409ファイルは不変です。必須技術残件はT10 strict raw-byte保持 `NOT_PROVEN`。同経路対照がないため再送・機能Runは行わず、[保存証跡の比較](evidence/t10-saved-evidence-review-20260914w.json)を分離しました。貼付け観測失敗で未復元となったクリップボードは、貼付け直前のWindows履歴項目を復元し、Text一致と元形式の存在を確認しました。全形式の生バイト同一は未評価です。補助の失敗時復元とPS5文字コードも修正しました。Issue #5/#27はOPEN / partial。

## 2026-09-14 Cセル値読取りの補完（20260914v）

実アクションから採取した `SET CellReadValue TO DataTable[0][0]` を、別空フローへ無修正貼付け・保存・再オープン後に2回実行し、Text値 `CRead-20260914v` と一致しました。前段は1行2列の合成DataTableです。4回の原文コピーは174 bytesで一致し、Run2前には値をクリアしています。Run2の観測補助例外は、追加Runせず同一実行を読み取り直して確認しました。

[原証跡・期待値・段階別判定](evidence/c-cell-read-20260914v/acceptance.json)。Copilot送信0回、PAD Run 2回。数値添字0/0のネイティブ再利用証跡であり、新しいCopilot生成合格や列名構文の保証ではありません。20260913e instruction/bundleは変更していません。必須残件は独立T04 Run1成果物とT10 strict raw-byte保持の2件で、Issue #5/#27はOPEN / partialを維持します。過去の不成立・未採取記録は以下に保存しています。

## 2026-09-14 現行版集約訂正・負例v2受入

集約状態を現行個別証跡へ整合させた。P3-1〜P3-6はすべて20260913eの同版指示・bundleで生成、無修正貼付け、保存・再コピー、2回Runまで確認済みで、P3-4〜P3-6の旧「未受入」表示は派生表示の残りとして訂正した。63桁のinstruction SHAは原送信・回答記録を変更せず、`evidence/p3-current-sha-correction-20260914e.json`へ訂正根拠と参照を記録した。負例v2は固定依頼を通常M365 Copilotへ1回送信し、N1〜N3を項目別に未確認受入（理由・必要証拠・禁止後続処理あり）とした。回答は無修正保存し、コードフェンス・Robin命令・疑似コード・未採取引数の推測はなく、PAD貼付け／Run／未登録Web操作は行っていない。旧finald負例PASSは履歴として保持し現行版へ継承していない。残件はT04形式不受入・独立T04候補partial、T10厳密保持NOT_PROVEN、最終A〜G監査であり、Issue #5/#27はOPEN / partialを維持する。

### 2026-09-14 現行版P3-1追跡

現行正本20260913e（instruction SHA `6ad6f742…`／bundle SHA `79245787…`）を通常M365 Copilot新規会話へ2実添付して1回送信し、4行Robinを無修正で採取した。専用空フロー `RobinKnowledgeP31CurrentBundleLive20260914e`（Designer PID 11016）で貼付け・保存・再コピー・2回Runを行い、`CatalogList=[CatalogItem, SecondItem]`、`NewVar=SecondItem`を確認した。証跡は `evidence/p31-current-bundle-live-20260914e.json`。旧20260912 P3-1 PASSを現行版へ移していない。P3-4〜P3-6・負例v2・T10厳密保持・A〜G監査は未完了で、Issue #5/#27はOPEN / partial。

### 2026-09-14 現行版P3-2追跡

同版指示全文＋bundleを通常M365 Copilot新規会話 `cc53abdf-077f-40eb-873e-f0ef92056be4`へThink Deeperで1回送信し、23行の入れ子If／EXIT LOOP Robinを無修正で採取した。専用空フロー `RobinKnowledgeP32CurrentBundleLive20260914e`（Designer PID 39172→23188）へ貼付け・保存・再コピーし、Designerの権威サマリー`23 アクション`を確認した（ListItem 6件表示は仮想化による偽陰性）。2回Runとも`CatalogList=[CatalogItem, SecondItem, ThirdItem]`、`OuterCount=2`、`InnerNo=1`、`InnerYes=1`、`LastSeen=SecondItem`、出力`SecondItem`を確認した。生成Robin SHA `3189a4c7…`、再コピーSHA `b2c65f7e…`はCRLF差のみで正規化一致。証跡は`evidence/p32-current-bundle-live-20260914e.json`と同参照のpaste/run記録。旧版P3-2 PASSは現行版へ移していない。P3-4〜P3-6・負例v2・T10厳密保持・A〜G監査は未完了で、Issue #5/#27はOPEN / partial。

### 2026-09-14 独立T04の現行版候補

窓の可視性を壊さない読取専用診断として、対象PIDの`Refresh()`後に全トップレベル窓をWin32 `EnumWindows`で列挙し、前景窓・所有PID・SessionId・UIA・Computer Useを比較した。過去の全窓0／CASE_Aは`evidence/t04-independent-current-pad-window-diagnostic-20260914r.json`として保全し、最新再確認では通常の`Power Automate`窓のみ可視、PAD DesignerはHWND 0・タイトル空・UIA 0のCASE_Bとなった。PAD実行失敗とは判定せず、T04のcandidate_partial、Run1 `NOT_CAPTURED`、新規pair未開始を維持する。最新証跡は`evidence/t04-independent-current-pad-window-observation-20260914t.json`。
追加の`quser`読取ではSession 1が`console / Active`で、PowerShellとPAD両PIDもSession 1だったため、Windowsセッション不一致は未成立とした。`Win32_ComputerSystem`は`ACCESS_DENIED`として未確認のまま補足証跡`evidence/t04-independent-current-pad-session-diagnostic-20260914s.json`へ記録した。

### 2026-09-14 現行版P3-3追跡

同版指示全文＋bundleを通常M365 Copilot新規会話 `8e3e9a69-098f-41ce-82df-47b581c6bbad`へThink Deeperで1回送信し、評価者用件数・期待値を渡さず13行の拡張子境界Robinを無修正で採取した。専用空フロー `RobinKnowledgeP33CurrentBundleLive20260914e`（Designer PID 38136）へ貼付け・保存・再コピーし、Designerの権威サマリー`13 アクション`を確認した（ListItem 7件表示は仮想化による偽陰性）。2回Runとも`TxtCount=3`、`OtherCount=2`、対象5ファイルのSHA不変を確認した。生成Robin SHA `2b3494e4…`、PAD再コピーはCRLF SHA `e909a165…`で正規化後一致、生バイト一致は主張しない。証跡は`evidence/p33-current-bundle-live-20260914e.json`と同参照のpaste/run記録。旧版P3-3 PASSは現行版へ移していない。P3-4〜P3-6、負例v2、T10厳密保持・A〜G監査は未完了で、Issue #5/#27はOPEN / partial。

### 2026-09-14 現行版P3-4追跡

同版指示全文＋bundleを通常M365 Copilot新規会話 `b9376b28-b208-4f56-a79d-05758849de9f`へThink Deeperで1回送信し、評価者用件数・期待値を渡さず4行のExcel SaveAs Robinを無修正で採取した。専用空フロー `RobinKnowledgeP34CurrentBundleLive20260914e`（Designer PID 30620）へ貼付け・保存・再コピーし、Designerの権威サマリー`4 選択されたアクション`を確認した。2回Runとも成功し、Run1/Run2のxlsxスナップショットでB2=`T05-Changed`を確認した。Run2はRun1出力が存在する状態から実行し出力SHAが変化、入力Excel SHAは不変だった。生成SHA `d67dba35…`、PAD再コピーSHA `f10a2518…`はCRLF差のみで正規化後一致し、生バイト一致は主張しない。詳細は `evidence/p34-current-bundle-live-20260914e.json` と同参照のpaste/run記録。P3-5/P3-6、負例v2、T10厳密保持・A〜G監査は残り、Issue #5/#27はOPEN / partial。

### 2026-09-14 現行版P3-5追跡

現行正本20260913e（instruction SHA `6ad6f742…`／bundle SHA `79245787…`）を通常M365 Copilot新規会話 `a505b6cc-1517-4959-8978-63f495d900c6`へThink Deeperで1回送信し、評価者用件数・期待値を渡さず2行の日時書式Robinを無修正で採取した。専用空フロー `RobinKnowledgeP35CurrentBundleLive20260914e`（Designer PID 34916）へ貼付け・保存・再コピーし、Designerの権威サマリー`2 アクション`を確認した。2回Runとも成功し、`FormattedDateTime2=2026-09-14`を確認した。生成SHA `004ef2f3…`、PAD再コピーSHA `19cf8878…`はCRLF差のみで正規化後一致し、生バイト一致は主張しない。`yyyy-MM-dd`以外の書式トークンと既存変換アクション編集経路は未証明のまま。証跡は`evidence/p35-current-bundle-live-20260914e.json`およびpaste/run各JSON。P3-6、T04形式、T10厳密保持、負例v2、A〜G監査は残り、Issue #5/#27はOPEN / partial。

### 2026-09-14 現行版P3-6追跡

現行正本20260913e（instruction SHA `6ad6f742…`／bundle SHA `79245787…`）の全文を本文へ置き、同版bundleと指示ファイルを通常M365 Copilot新規会話 `724624ae-3f2d-4c82-92a6-f4e40a51f64d`へThink Deeperで1回送信した。評価者用件数・期待値は渡さず、12行のエラー処理Robinを無修正で採取した。専用空フロー `RobinKnowledgeP36CurrentBundleLive20260914e`（Designer PID 19332）へ貼付け・保存・再コピーし、権威サマリー`4 アクション`を確認した。初回paste helperは12行をアクション数として渡した入力ミスでタイムアウトしたが、同一貼付け後の4アクション状態をUIAで確認し、再貼付けはしていない。2回Runとも成功し、`NewVar=named`、`LastError`に`見つかりません`を確認した。生成SHA `a1544f08…`、PAD再コピーSHA `ae5bcb55…`は`BLOCK`末尾空白とCRLF差があり、生バイト一致は主張しない。ブロック側利用者定義`FileNotFound`一致と厳密保持は未証明のまま。証跡は`evidence/p36-current-bundle-live-20260914e.json`およびpaste/run各JSON。独立T04候補の実行別照合と新規補完ペアの準備／未実行境界は `evidence/t04-independent-current-evidence-reconciliation-20260914e.json` に記録した。P3-6以外の残件（T04形式、T10厳密保持、負例v2、A〜G監査）は継続し、Issue #5/#27はOPEN / partial。

### 2026-09-14 独立T10の現行版機能受入（厳密保持は未証明）

現行正本20260913e（instruction SHA `6ad6f742…`／bundle SHA `79245787…`）を新規通常M365 Copilot会話 `6edc277b-b005-4d56-8bb7-ba64668ea636`へThink Deeper・3実添付で1回送信した。応答DOMは単一16行Robin（SHA `2bcb5512…`）で、元入力との差は許可したExcel A1値とSaveAs先の2行だけ（正規化後の範囲外差分0）。専用空フロー `RobinKnowledgeT10IndependentCurrentBundleLive20260914e`（Designer PID 20008）へ無修正で貼付け・保存・再コピーし、集計16アクション（ListItemは仮想化で5〜6件）を確認した。2回Runとも成功し、独立Excel A1=`T10-Changed`、Word/PPT本文=`CopilotOffice 246`を各回の新規スナップショットで確認した。既存のExcel/Word/PPT出力はバックアップから復元した。初回貼付けヘルパーは60秒時点で6件のためタイムアウトしたが、同じ貼付けの後続状態で集計16件が現れたため再送せず、失敗原記録を残した。生成→PADはCRLF正規化後のみ一致し、生バイトと元入力→生成の厳密保持は`NOT_PROVEN`のまま。詳細は`evidence/t10-independent-current-generation-20260914e.json`。Issue #5/#27はOPEN / partialを維持する。

現行正本20260913e（instruction SHA `6ad6f742…`／bundle SHA `79245787…`）を同版指示＋bundle実添付の新規Think Deeper通常チャットへ送信した。評価者用の件数・期待値を本文へ渡さない補正版依頼で、公式応答（SHA `a932e7e7…`）とDOM単一`pre`のRobin（SHA `dd4f39f0…43569d`、9行、`=>` 5箇所、`\\=>` 0箇所）を無修正保存した。`RobinKnowledgeT04IndependentCurrentBundleLive20260914eD`へ貼付け・保存・再コピーし、再コピーはCRLF正規化後のみ一致（生バイト一致は主張しない）。2回Runは成功し、Run2のxlsxは3行3列（対象/A/10、対象/C/25、対象/D/5）、入力fixture SHAは不変、既存出力と中間CSVは復元した。Run1のxlsxスナップショットはRun2前に採取できなかったため候補`partial`であり、追加3回目は行わず、元T04の応答由来形式不受入を上書き・昇格していない。詳細は`evidence/t04-independent-current-output-comparison-20260914e.json`。Issue #5/#27はOPEN / partialを維持する。

> 2026-09-14追補: 20260913e正本（instruction `6ad6f742…`／bundle `79245787…`）でT06/T07/T08を新規通常M365 Copilot会話へ送信し、Think Deeper・同版指示＋bundle実添付を確認。T06は4行Robinを無修正で新規専用空フローへ貼付け・保存・再コピー・2回Runし、Word本文置換・入力SHA不変を照合。T07は2行Robin（SHA `47a33ef2…`）を`RobinKnowledgeT07CurrentBundleLive20260914e`へ無修正貼付け・保存・再コピー、2回Runを完了し、合成PDF出力は両回とも`PAGE_TOKEN_A2`のみ、入力PDF SHA不変、既存出力復元を確認した（`evidence/t07-current-bundle-live-acceptance-20260914e.json`、`evidence/t07-current-bundle-output-comparison-20260914e.json`）。T08は12行Robin（SHA `d4a6b697…`）を`RobinKnowledgeT08CurrentBundleLive20260914e`へ無修正貼付け・保存・再コピー、2回Runし、アクション単位`FileNotFoundError`で`NewVar=named`、欠損LastError、ブロック側`FileNotFound`一致NOT_PROVEN、入力不在・後続書込み／マーカー／公開なしを確認した（`evidence/t08-current-bundle-live-acceptance-20260914e.json`、`evidence/t08-current-bundle-output-comparison-20260914e.json`）。独立T01も新規通常チャット／新規空フローへ無修正3行を貼付け・保存・再コピーし、2回Runで出力SHA `2b030f2d…`・入力SHA不変を確認した（`evidence/t01-independent-current-output-comparison-20260914e.json`）。厳密バイト保持は各再コピーの正規化一致を超えて主張しない。現行版受入済みはT01/T02/T03（修正版依頼）/T05/T06/T07/T08/T09と独立T01、T04形式・T10厳密保持・独立T04/T10・P3・負例・A〜G監査は残り、Issue #5/#27はOPEN / partial。

> 2026-09-12 最終監査: 固定finaldの生成受入は維持。A〜Gの一部の別空フロー再利用等の保存証跡が未特定で、PR提出準備は未完了です。[原証跡の対応表と不足](../docs/robin-knowledge-validation.md)を確認してください。

> 2026-09-13e追跡: T03は固定カウンター要件を依頼本文へ明示した候補限定の再生成を無修正PADへ貼付け、2回実行（2 txt／2 other）まで確認しました。指示・bundleの現行正本SHAと一致するため、元依頼なしの「明示カウンター付き修正版依頼」に限る現行版追跡を追加しました（`evidence/t03-copilot-live-generation-20260913e-pad-acceptance.json`）。元の3試行と、カウンター要件が見えない元依頼は不受入のままです。T04は同版・同添付の新規会話へ追加1回だけ送信し、`=>`前バックスラッシュがDOMと保存Robinに一致して再現したため生成回答由来の形式不受入として停止しました（`evidence/t04-copilot-live-generation-20260913-attempt3.json`）。T09指示の`WAIT 500`を、知識原文と一致する`WAIT 1`へ修正して20260913e正本（SHA `6ad6f742…`）へ固定し、同版の通常チャット知識precheckを`PASS_REFERENCE_ONLY`で追跡しました。同版T01は通常チャット生成→専用空フローへ無修正3行貼付け・保存・再コピー→2回Run、出力／入力不変まで受入しました（`evidence/t01-copilot-live-generation-20260913e-pad-acceptance.json`）。T02も同版通常チャット生成→専用空フローへ3行を無修正貼付け・保存・再コピー→2回Run、CSV出力一致・入力不変まで確認し、既存候補原記録を現行版追跡へ昇格しました（`evidence/t02-copilot-live-generation-20260913e-pad-acceptance.json`）。T09も同版通常チャット生成→専用空フローで要素登録・削除→無修正6行貼付け・保存・再コピー→2回Run（`T09-clicked`）まで受入しました（`evidence/t09-20260913e-pad-acceptance.json`）。T07の現行版受入（2行Robin、専用空フロー2回Run、`PAGE_TOKEN_A2`のみ、入力PDF不変、既存出力復元）は`evidence/t07-current-bundle-live-acceptance-20260914e.json`へ追加しました。T10は機能実行と許可2行の内容範囲を`evidence/t10-strict-preservation-audit-20260913.json`で分離し、厳密バイト保持はNOT_PROVENです。T04/T08、独立再試験、P3正例、負例v2は新版本未受入で、旧finald PASSを移していません。現在の判定はOPEN / partialです（`evidence/current-package-status-20260913.json`）。

`index.json`は実際の左パネルから追加・設定・コピーした例の索引です。`.robin`はクリップボードから得た原文をUTF-8 BOMなしで保存し、改行を変換しません。Gitでもバイトを保持します。

既存の変数・テキスト・ループ・ファイル読取り・Office・PDF操作に、2026-09-09/10の日時取得、空データテーブル、行追加失敗、CSV読取り・書出し、FilterDataTable、ファイルコピー、サブテキスト取得、テキスト書出し、テキスト変数書込み2設定、For each、If2、Excel/Word編集可能起動2設定、フォルダー取得2設定、ファイル変数読取り、PDFページ2単独抽出を加え、`catalog/index.json` は86観測バリアントです。既存51例と追加例を、採取・再貼付け・実行・失敗の証拠範囲ごとに分けています。初期の専用フローは`RobinCatalog_20260907`、Officeの採取先はユーザーが用意した`test`です。コピー前のクリップボードはメモリーに保持して復元し、その内容をファイルへ記録していません。

2026-09-10の現作業版では、左パネル全体の完全対応を主張せず、`coverage.json` の `observed_variant_count=86` と `complete=false` を正本とします。T04/T10のCopilot生成時の原文変化は `evidence/normal-chat-raw-provenance-20260910.json` に保存し、現作業版T01〜T07、T04/T10一次受入、T01/T04/T10独立再試験、未採取構文・UI依存のfail-closed負例は各受入証拠へ記録しています。P3のBoolean・減算・日付減算・フォルダー作成probeは別証跡でPASSまたは境界確認ですが、現行bundle未統合です。T08は形式失敗、T09は現行package生成未確認です。現作業版の指示・bundleハッシュは `README.md` と `copilot/README.md` に記録しています。過去の73・61等の値は履歴であり、現行値へ読み替えません。

## 履歴（現行値へ読み替えない）

P3追補：Boolean、数値減算、日時加算・減算、DateAndTime取得、フォルダー作成、Excelシート選択は別probeで採取・実行済みですが、現行bundle未統合です。カスタム日時書式化は未確認、T08は生成形式失敗、T09は現行package生成未確認です。

ファイル存在確認とファイル移動（成功＋DoNothing衝突再実行）のprobeも別証跡で保持しています。欠損パスのfalse分岐はrawコピー・実行完了まで確認しましたが、branch bodyのside effectは未確認です。
ファイル名前変更の成功／衝突no-opも別証跡で保持しています。false分岐のbranch-body実行は未確認です。
3列1行（A/10/対象）のDataTable作成は別probeで2回実行確認しています。列付き行追加は値数不一致のnative runtime errorを再現し、成功構文を推測せず未確認として保持しています。
ビジュアライザー保存後に0列へ戻る別失敗も記録し、成功構文を推測していません。
If/Else/ENDとIf/Else-if/ENDの構造も別probeで確認しています。入れ子・分岐内処理は未確認です。
有限Loopの`EXIT LOOP`と`NEXT LOOP`は別probeで確認しています。入れ子とloop内副作用は未確認です。
（Loop Continue probeは現行bundleへ未統合です。）
エラー処理ブロックの骨格、欠損ファイル子アクションのruntime error、P3Worker作成＋MainからのCALLも別probeで確認しています。カスタムハンドラーは未確認です。

ファイル存在確認の`IF ... THEN`／`END`も別probeでtrue条件を2回、欠損パス条件を1回実行し、欠損パスのrawも取得しました。branch bodyのside effectとデータ反復等は未確認です。

P3追補：Boolean、数値減算、日時加算・減算、DateAndTime取得、フォルダー作成は別probeで採取・実行済みですが、現行bundle未統合です。カスタム日時書式化は未確認、T08は生成形式失敗、T09は現行package生成未確認です。

```text
Variables.CreateNewList List=> CatalogList
Variables.AddItemToList Item: $'''CatalogItem''' List: CatalogList
```

これは説明用表示です。コピー原文の正本は`flows/list-create-add/default.robin`です。

今回の設定画面では追加先リストに`%CatalogList%`を指定しましたが、コピーしたRobinでは`List: CatalogList`になりました。任意の文字列・選択肢・式までこの例から一般化しません。

「変数の設定」は通常文字列と特殊文字の2例を採取しました。特殊文字の例を含む3アクションのMainを保存・実行し、変数パネルで `日本語 100% '引用' "二重引用" C:\sample` を確認しています。設定画面の入力は`100%%`で、Robinの引用符とバックスラッシュにもPADがエスケープを付けています。原文は`actions/variables-set/special-text.robin`です。通常文字列の例はコピーのみ、特殊文字の例は保存・実行までで、いずれも再貼付けは未確認です。

左パネルの全一覧は未完了です。UIAに一度に現れるノードが仮想化されており、一部だけを全一覧として保存しないよう、不完全な試行結果はカタログから除外しています。

「テキストを置換する」は通常置換と正規表現置換を採取・保存・実行しました。通常置換は`ReplaceText`、正規表現は`ReplaceTextWithRegex`で、前者には`ComparisonType`も含まれます。日本語→English、数字の連続→NUMBERの結果を、他の特殊文字が残ることと合わせて検証しました。変数パネルの実UIA記録を`evidence/text-replace-*-variables.json`に保存しています。再貼付けはまだ未確認です。

アクションを追加した位置が変数定義より前だったため、実行前にPADの「下に移動」で順序を直しました。採取補助も行番号とアクション名を照合するようにし、位置だけで別の行を採用しないようにしています。

空の`Roundtrip`サブフローへコピー原文を貼り付け、再コピーした`roundtrip.robin`が112文字・SHA256まで元と一致することも確認しました。実行結果を観測したのは元のMainです。

Copilotによる生成は[リストと正規表現の組合せ1ケース](generated/list-and-regex/README.md)で確認しました。別の変数名・入力値を使った生成コードを手直しせずPADへ貼り付け、再コピーのバイト一致、保存・実行、期待値一致まで確認しています。

アプリのRobin検証器/Runループとの接続はまだ未確認です。実アクションがPADで動くことと、このアプリがその構文を実行できることは別です。採取・拡張の方針は[採取ガイド](../docs/robin-action-catalog.md)を参照してください。

分割・結合は、カスタムのカンマ区切りから alpha | beta | gamma を得る例と、既存文字列の標準スペース分割から再結合する例を保存・実行しました。カスタムの空白1文字は入力欄の長さ1を確認しても設計時エラーになり、標準スペースへ切り替えました。新しい3設定は再貼付け未確認です。

数値SET、変数の加算（固定値/ループ変数）、Loopの1〜3を追加しました。LoopSamplesサブフローを先頭から実行し、固定値1の加算は3、ループ変数の合計は6、終了後のLoopIndexは4を確認しています。Main実行や再貼付けとは区別します。

テキスト読取り・数値変換・小数2桁の書式化を追加しました。1234.5から1234.50を得ることをNumberSamplesで確認し、not-a-numberはランタイムエラーとして停止しました。数値12.5を入力したコピー例は、PADが引用符なしの数値として出力しているため、ファイルから読んだ文字列の例と区別しています。

## Officeの採取とCopilot生成

Excel・Word・PowerPointの17種類・22設定例を追加しました。新規作成・読み書き・別名保存・終了、既存ファイルの起動、Excel範囲読取り、Word全件置換を含みます。各例の依存と検証範囲は `index.json` に記録しています。

基本16操作の再貼付けはバイト一致し、3種類の成果物を検査しました。既存文書の再読取り・置換の組合せ11操作も確認済みです。[実Copilot生成の検証](generated/office-three-apps/README.md)では新しい本文・保存名の16操作を手直しせず実行できました。詳細は[Office採取記録](../docs/office-action-capture.md)を参照してください。今回のOffice操作はアプリの自動Run検証器には追加していません。

## PDFの採取

PDFカテゴリの5種類・11設定例を追加しました。テキスト・表・画像抽出、ページ抽出、統合を実行確認しています。この環境の2ファイル統合は入力と逆順になる挙動があり、[PDF採取記録](../docs/pdf-action-capture.md)と生成プロンプトに明記しました。カタログ全体は33種類・50設定例です。アプリの自動RunとCopilotによるPDF生成は未検証です。


## アプリ接続の追記（2026-09-08）

上記の採取時点の「自動Run未接続／未検証」は、その後の実装で更新しました。Office/PDFの採取形式を検証器・出力観測・完了判定へ接続し、Office3ファイル作成とPDF各操作の2ケースをアプリ開始からDONEまで確認しました。PDF表は追加採取したCSV書出しで保存します。既存51例に今回の10例を加え、現在のカタログは61設定です。

検証範囲・制約・先行失敗・未完了事項は [自動Run接続チェックポイント](../docs/document-run-checkpoint-2026-09-08.md) を参照してください。既存Office文書の自動Run、書式・レイアウト、別PC・社内受入は未確認です。

## 2026-09-11 P3統合・T09別フロー境界

Final3固定版の成果を保全したうえで、DataTable行追加・セル更新・行反復とExcel行反復の専用probe成功を7原本へ統合した。新bundle SHA-256は `dd668166e4c04b02878a6fae65e4583b6d6c910847559161c6707ae90e6626a5`、マニフェストは `../copilot/knowledge-bundle-manifest-20260911h.json`。指示全文＋同版bundleの通常チャット知識precheckはPASS_REFERENCE_ONLY、T01〜T10のPAD受入は未実行で、旧版PASSは継承しない。

T09別空フロー `RobinKnowledgeT09Separate_20260911` は6アクションの貼付け・保存まで成功したが、UI要素ピッカーはEdge Window/Paneしか列挙せず、入力・実行ボタン・結果段落を登録できなかった。エラー3件・Start無効・Run未開始で、LaunchEdge単独フローの完了はT09通し成功へ拡張していない。詳細は `evidence/t09-separate-ui-registration-20260911.json`。

## 2026-09-12 最終版（finalc）受入とT09待機値の修正

T09の採取原文 `flows/ui-t09-local-roundtrip/roundtrip.robin` の `WAIT 500` は、PADの待機アクションが秒単位のため500秒待っていた（2026-09-10採取時の500ミリ秒のつもりの誤設定。利用者の指摘で判明）。PADへ貼り付けた同原文の待機ダイアログで期間を1へ変更・保存・再コピーした `roundtrip-wait1-20260912.robin`（4行目のみ `WAIT 1`、他5行は同一）を新しい空フロー `RobinKnowledgeT09Wait1_20260912` で2回実行し、いずれも数秒で `AttributeValue=T09-clicked` とブラウザー終了を確認した（`evidence/t09-wait1-acceptance-20260912.json`、`actions/wait/t09-1s.robin`）。原本の `roundtrip.robin` と `actions/wait/t09-500ms.robin` は履歴として保全している。

この修正を含む最終版bundle `f42f5acf4232b132b0a5b5bde469b25bf91d04f4cdb0a6823b17806d4ff85089`（`../copilot/knowledge-bundle-manifest-20260912c.json`）で、通常M365 Copilotチャット（Google Chrome、Think Deeper、指示全文＋同版bundle添付）の知識precheck、T01〜T10、独立再試験T01/T04/T10、負例N1〜N3を同一版で受入した。T09は生成6行が `WAIT 1` となり、要素取り込み後の無修正貼付け・2回実行で `T09-clicked` を確認（`evidence/t09-finalc-20260912-live-acceptance-20260912.json`）。T08は名前付きFileNotFound＋既定ハンドラーの9行が生成され、既定経路で期待エラーを確認（名前付き一致は未確認のまま）。正本は `evidence/current-package-status-20260912-finalc.json`、`evidence/issue5-completion-audit-20260912-finalc.json`。直前版 `32aea4560df7a7530cd9fe1fab996181236ee8a0c34213adfffb3f022dbfc041` の受入（T09は500秒待機で2回完了）は `evidence/current-package-status-20260912-final.json` に superseded として保全した。

## 2026-09-12 P3-1〜P3-6の実測とfinald作業版

Issue #5のP3残課題を専用合成フローで採取した。P3-1 `SET NewVar TO CatalogList[1]`（ダイアログ入力→再コピー→別空フロー再利用、各2回で`SecondItem`）、P3-2 If内If＋ファイル書込み＋`EXIT LOOP`（23行）と`LOOP…STEP`内For each＋`NEXT LOOP`（15行、期待値は`flows/p3-nested-control/expectations-20260912.json`で事前固定）、P3-3 `fixtures/files-boundary`（`.TXT`はElse＝等価比較は大文字小文字を区別、`.txt.bak`はElse、親フォルダー名`sub.txt`は影響なし、`IncludeSubfolders`で再帰制御。固定T03は不変）、P3-4 Excel／Word SaveAsは既存出力を無警告で上書き、P3-5 `FromCustomDateTime yyyy-MM-dd`（新規追加経路で採取。2026-09-11の内部例外は既存アクション編集経路）、P3-6 アクション単位 `ON ERROR FileNotFoundError` が一致し`NewVar=named`のみ設定（ブロック既定ルール非発火。ブロック側利用者定義名`FileNotFound`は不一致のまま）。証拠: `evidence/p3-list-idx1-acceptance-20260912.json`、`p3-nested-control-…`、`p3-file-boundary-…`、`p3-saveas-collision-…`、`p3-date-format-…`、`p3-named-error-…`。

統合後のbundle `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`（`../copilot/knowledge-bundle-manifest-20260912d.json`）で、知識precheck、T01〜T10（T03は2回目生成）、独立再試験T01/T04/T10、負例v2、P3正例P3-1〜P3-6を同一版で受入した（`generated/normal-chat-finald-20260912-*/`、PADフロー `RobinKnowledge*FinalD2_20260912`、証跡 `evidence/*-finald-20260912-*-acceptance-20260912.json`）。P3正例の生成Robinはいずれも実測原文と同一（P3-4は出力名、P3-5はShortDate行の有無のみ差）。`evidence/current-package-status-20260912-finald.json` は complete_live_acceptance_finald_20260912。
