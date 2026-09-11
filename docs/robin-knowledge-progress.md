# Robinナレッジ作成 進捗

更新日: 2026-09-11

## 全体目標

アプリではなく、PADの実測Robinに基づくCopilotエージェント用の指示文とナレッジを完成する。

## 作業ブランチ／基準コミット

- ブランチ: `codex/issue-5-acceptance-20260910b`（2026-09-10継続作業）
- 基準main: `69fe344`（origin/mainと一致）
- 現在の固定コミット: `00a898b`（P3統合bundle・T09停止境界・完了監査・非ライブ全件検証を反映）
- origin: `https://github.com/minimo162/ai-prompts.git`
- PR #19: squashマージ済み。今回の再開確認では新規push・PR・merge・公開を行わない。

## 実機の条件

- 既存記録で確認済みの条件: PAD `2.71.115.26224`、日本語UI、Power Fx OFF、合成データ・専用フロー。
- 既存記録ではPAD `2.71.115.26224`、日本語UI、Power Fx OFFを確認済み。今回の起動確認ではMicrosoft.PowerAutomateDesktop `11.2608.115.0` のPAD.Console.HostとDesignerプロセス、専用Designerウィンドウ群を列挙できた。
- 現セッションのnative Computer UseをPADへバインドしようとしたが、Trusted RPC未構成（`Trusted RPC service is not configured: sky`）だったため、既存の厳格なUIAヘルパーへ切り替えた。T04のクリップボード・保存・実行とT09のUI要素捕捉・貼付け・保存・実行試行は、このフォールバックで新規証跡化した。native CUA経路の成功とは扱わない。詳細は `catalog/evidence/pad-native-ui-blocked-20260910.json` と `catalog/evidence/pad-uia-recovered-20260910.json`。

## 既存資産の再集計

- 追加前の既存 `catalog/index.json` 実測エントリ: 51件。
- 今回の日時取得・空データテーブル・空テーブルへの行追加失敗・CSV読取り2・CSV書出し2・FilterDataTable・ファイルコピー・サブテキスト取得・テキスト書出し・テキスト変数書込み2設定・For each・If2・Excel/Word編集可能起動2設定・フォルダー取得2設定・ファイル変数読取り・PDFページ2単独抽出を追加後の `catalog/index.json`: 86件（既存51＋追加35）。T04のExcel読取り・FilterDataTable・CSV変換・中間CSV・別xlsx保存の7実測バリアントと、T09ブラウザー6バリアントを追加。
- 既存カテゴリ別: 変数7、テキスト8、ループ1、ファイル2、Excel8、Word7、PowerPoint7、PDF11。今回、日時1・テキスト1・変数2（成功1、失敗1）・ファイル9（CSV読取り／書出し／コピー／テキスト書出し／テキスト変数書込み2設定／フォルダー取得2／ファイル変数読取り）・ループ1・条件2・Excel起動1・Word起動1を追加。
- 索引のscopeは「Observed PAD action variants」であり、全アクション一覧でも実行許可集合でもない。
- 既存の生成・実行証拠は `catalog/generated/list-and-regex/` と `catalog/generated/office-three-apps/` にあるが、新しいエージェントへの登録試験とは区別する。

## 固定した必須採取チェックリスト

- A 基礎: 既存の変数・文字列・数値・リスト・置換・分割・結合・数値変換に加え、日時取得のdate-only設定とサブテキスト取得のUnicode混在1設定を実測済み。別probeで日時加算・減算、一般の数値減算を実行確認したが、カスタム日時書式化とリスト取出しは未確認。
- B 制御: 定数範囲LoopとFor each／Ifの原文を観測し、For each＋If＋ファイル読取りのT03組合せを実行済み。別probeでElse、Else-if、EXIT LOOP、NEXT LOOP、エラー処理ブロック骨格、欠損ファイル子アクションのruntime error、P3Worker作成＋MainからのCALLを確認したが、入れ子とカスタムハンドラーは未確認。
- C データ処理: 空データテーブル作成、3列1行DataTable作成、CSV読取り、DataTable変数参照でのCSV書出しは実測済み。0行0列・列数不一致の行追加は失敗として記録。列付き行追加・行反復・セル参照の成功は未確認。
- D ファイル: UTF-8テキスト読取り・書出し、CSV読取り・書出し、単一ファイルのコピー、フォルダー内ファイル取得2設定、変数パス読取りは原文・別フロー貼付け・実行へ対応づけた。別probeで存在確認、フォルダー作成、移動（成功＋DoNothing衝突再実行）、名前変更を確認した。欠損パスのfalse分岐はrawコピー・実行完了まで確認したが、branch bodyのside effectは未確認。
- E Excel: 起動・セル/範囲読取り・書込み・保存・終了、Sheet1選択、A1:C6読取り（6行3列プレビュー）は確認済み。データ反復の独立例は未確認。
- F Word・PowerPoint・PDF: 既存採取・証跡を引き継ぐ教材化と再利用確認が必要。未採取モードを完成例へ混ぜない。
- G UI・ブラウザー: T09でローカルEdgeの入力・ボタン・結果段落をUI要素ピッカーから捕捉し、6アクションを空フローへ貼付け・保存した。WebAutomation通し実行はブラウザー拡張経路のタイムアウトで未完了。

## 現在の段階

前回版の採取／教材化（指示SHA `e467855137a1eec8655cfb6086f274e6a8e996412b3d07068f32c6912d9482c1` とbundle SHA `431cdaa9c2ba34e217d848a0df0191d960608e04940674bca33f151cb1f62bc3`）の履歴。知識プレチェックとT01〜T10の通常チャット生成を保存し、T01〜T03/T05〜T08は前回版PAD貼付け・保存・2回実行まで完了。T04は引用符差分、T09はWebAutomationタイムアウト、T10はWord SaveAsエラーをpartialとして記録した。現作業版は末尾の「現作業版の再開記録」で別管理する。

T02のFilter DataTableは、PAD UIで列／インデックス=`2`・等価演算子・値=`対象`を設定し、先行CSV読取り・CSV書出しを含む新規フローへ無修正Robinを貼付け、保存・2回実行・CSV照合まで完了した。先行CSVTable生成がない専用フローの未解決入力試行は失敗例として分離した。

2026-09-11の非ライブ全件検証では、Windows PowerShell 5.1の35テストが35/35 PASSし、候補3ファイルのハッシュ不変を確認した（`catalog/evidence/nonlive-all-suite-20260911b.json`）。この結果はP5のローカル証拠であり、ライブM365 Copilot／PAD実行／他PC／業務品質の受入を示さない。

旧bundle SHA-256は履歴として保持する。P3追補統合後の現作業版は instruction SHA `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e` と bundle SHA `e35fa2f4a960841603cc876ad2e1e8af254ff66afc97b297224ffb3c44d08644` で、旧版のT01〜T10実行証拠は新bundleの最終受入へ継承しない。T09はUI要素捕捉・空フロー貼付け・保存まで完了したが、現行6アクションのWebAutomation実行は112秒時点で停止し、未完了である。

## 直前に完了した項目

- 依頼書を読み直した。
- 既存索引を再集計し、51件・8カテゴリであることを確認した。
- 作業ブランチを作成した。
- `copilot/agent-instructions.txt` と7つの登録用 `.txt`、`copilot/README.md` を作成した。
- `catalog/coverage.json` を生成し、観測済み86件と必須範囲A〜Gの16チェックを明示した。
- T01〜T10の依頼・期待値を `catalog/generated/acceptance-t01-t10/README.md` に固定した。
- `docs/robin-knowledge-validation.md` に静的検証、実機・CopilotのBLOCKED状態、再開手順を保存した。
- `tests/Test-CopilotRobinPackage.ps1` がPASS（指示欄UTF-16 3,585、ナレッジ7、観測86）。
- `tests/Test-RobinCatalog.ps1` がPASS（55 checks、PAD/Copilotを呼び出さない静的契約検査）。
- 左パネルをActionsTreeViewで再観測し、412ノード（グループ72、アクション340）を `catalog/evidence/pad-action-inventory-20260909.json` に保存した。
- 「現在の日時を取得」を「現在の日付のみ」で採取し、保存テキストを別の空フローへ貼付け・保存・再コピー・SHA-256一致・2回実行・期待値照合した。
- 「新しいデータ テーブルを作成する」を0行0列設定で採取し、別の空フローへ貼付け・保存・再コピー・SHA-256一致・2回実行・0行0列期待値照合した。行追加・セル参照は未採取。
- 0行0列DataTableへの空リスト行追加を試し、設計エラーを観測。失敗原文を保存し、成功件数へ含めていない。
- 日本語・引用符を含む合成CSVをUTF-8で読み、3行3列を確認。DataTable変数参照で別CSVへ書き戻し、内容一致と2回の実行を確認した。
- 合成ファイルのコピーを専用フォルダーへ実行し、1回目の入力・出力ハッシュ一致と、2回目のDoNothingによる出力不変を確認した。
- 「サブテキストの取得」を左パネルから追加し、Unicode混在テキストを開始インデックス1・長さ3で切り出した。原文保存、別フローへの貼付け・保存・再コピー、元フローとRoundtripの各2回実行、`Subtext=日本語`照合まで完了した。
- 「テキストをファイルに書き込む」をUTF-8・上書き・末尾改行で追加採取し、原文保存、別フロー貼付け・保存・再コピー、元フローとRoundtrip各2回実行、BOM付き出力の内容照合まで完了した。`100%`をそのまま入力した失敗フローも分離保存した。
- 「テキストをファイルに書き込む」の既存テキスト変数参照（`TextToWrite: Replaced`）と`AppendNewLine=False`を追加採取し、各原文の再コピー一致を確認した。結合版を最新版へ再生成した。
- 通常M365 Copilotチャットでモデルを`GPT 5.6 Think Deeper`へ切り替え、結合版をCDPの既存file inputへ直接添付し、本文3,128文字を全文一致で送信した。回答の3行Robinを無修正で新規PADフローへ貼付け、保存、2回実行した。出力はUTF-8 BOM付き85 bytes、期待5行と完全一致した。詳細は`catalog/generated/normal-chat-t01-20260909-gpt56-noappend-clean2/`、`catalog/evidence/normal-chat-t01-noappend-paste.json`、`normal-chat-t01-noappend-run-1.json`、`normal-chat-t01-noappend-run-2.json`。
- T03は全ファイル取得、For each、`.txt`判定、ファイルパス変数のUTF-8読取りを通常チャットから生成し、PAD実行で`.txt`だけ読み取り、`.csv`/`.md`を読み取らないことを確認した。T05は編集可能Excel起動原文を追加採取後、B2だけを変更するRobinを通常チャットから生成し、元ブックA1/B2不変、出力B2=`T05-Changed`を照合した。T06は編集可能Word起動・置換・別名保存・終了を通常チャットから生成し、元文書SHA不変・出力置換を確認した。T07はPDF2ページ抽出を2回実行し、T08は存在しないファイルのErrorsGrid期待エラーを記録した。
- T10は既存16アクションをT10-Knowledge-Flow-Bundleへ機械的に供給し、Excelの1書込み値と1保存名だけをASCII変更したRobinを生成した。PADでExcel A1=`T10-Changed`、Word/PowerPoint本文保持、独立再試験同結果まで確認した。複数ファイル添付は後続ファイルを落としたため、結合版へ切り替えた。

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
- `catalog/generated/agent-builder-m365-entry-rerun-20260909.json`
- `catalog/evidence/m365-chat-attachment-attempt-20260910.json`
- `catalog/evidence/text-substring-validation.json`
- `catalog/actions/text-substring/mixed-index-length.robin`
- `catalog/flows/text-substring/roundtrip.robin`
- `catalog/actions/file-write-text/utf8-overwrite.robin`
- `catalog/flows/file-write-text/roundtrip.robin`
- `catalog/evidence/text-write-validation.json`
- `catalog/evidence/text-write-invalid-percent.json`
- `catalog/actions/file-write-text/variable-reference.robin`
- `catalog/actions/file-write-text/variable-reference-no-append.robin`
- `catalog/evidence/text-write-variable-recopy.robin`
- `catalog/evidence/text-write-variable-noappend-recopy.robin`
- `catalog/evidence/text-write-variable-paste.json`
- `catalog/evidence/text-write-variable-noappend-paste.json`
- `catalog/generated/normal-chat-t01-20260909-gpt56-variable/`
- `catalog/generated/normal-chat-t01-20260909-gpt56-noappend-clean2/`
- `catalog/evidence/normal-chat-t01-pad-paste.json`
- `catalog/evidence/normal-chat-t01-pad-run-1.json`
- `catalog/evidence/normal-chat-t01-pad-run-2.json`
- `catalog/evidence/normal-chat-t01-noappend-paste.json`
- `catalog/evidence/normal-chat-t01-noappend-run-1.json`
- `catalog/evidence/normal-chat-t01-noappend-run-2.json`
- `catalog/fixtures/excel/excel-catalog.xlsx`
- `catalog/fixtures/word/word-catalog.docx`
- `catalog/generated/normal-chat-t05-20260910-gpt56/`
- `catalog/generated/normal-chat-t05-20260910-final-v3/`
- `catalog/evidence/normal-chat-t05-paste.json`
- `catalog/evidence/normal-chat-t05-run-1.json`
- `catalog/generated/normal-chat-t06-20260910-gpt56-v2/`
- `catalog/generated/normal-chat-t06-20260910-final/`
- `catalog/evidence/normal-chat-t06-paste.json`
- `catalog/evidence/normal-chat-t06-run-1.json`
- `catalog/generated/normal-chat-t07-20260910-gpt56/`
- `catalog/generated/normal-chat-t07-20260910-final/`
- `catalog/evidence/normal-chat-t07-paste.json`
- `catalog/evidence/normal-chat-t07-run-1.json`
- `catalog/evidence/normal-chat-t07-run-2.json`
- `catalog/generated/normal-chat-t08-20260910-gpt56/`
- `catalog/generated/normal-chat-t08-20260910-final/`
- `catalog/evidence/normal-chat-t08-paste.json`
- `catalog/evidence/normal-chat-t08-run.json`
- `catalog/generated/normal-chat-t10-20260910-gpt56-v6/`
- `catalog/generated/normal-chat-t10-20260910-final-v2/`
- `catalog/generated/normal-chat-t10-20260910-final-independent-v2/`
- `catalog/evidence/normal-chat-t10-v6-paste.json`
- `catalog/evidence/normal-chat-t10-v6-run.json`
- `catalog/generated/normal-chat-t10-20260910-gpt56-independent/`
- `catalog/evidence/normal-chat-t10-independent-paste.json`
- `catalog/evidence/normal-chat-t10-independent-run.json`
- `catalog/evidence/normal-chat-t10-independent-output.json`
- `catalog/actions/foreach/items-variable.robin`
- `catalog/actions/if/current-item-status-equals.robin`
- `catalog/actions/folder-get-files/txt-files.robin`
- `catalog/actions/excel-launch/open-editable.robin`
- `catalog/actions/word-launch/open-editable.robin`
- `catalog/evidence/filter-t02-copy-failure.json`
- `catalog/generated/normal-chat-t02-20260910-gpt56/`
- `catalog/generated/normal-chat-t03-20260910-gpt56/`
- `catalog/generated/normal-chat-t03-20260910-final3/`
- `catalog/evidence/normal-chat-t03-final-run.json`
- `catalog/generated/normal-chat-t04-20260910-gpt56/`
- `catalog/generated/normal-chat-t06-20260910-gpt56-v2/`
- `catalog/generated/normal-chat-t10-20260910-final/`
- `catalog/evidence/normal-chat-t10-final-save.json`
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

- A〜Gの残り未採取チェック項目の1アクション×1設定採取・再貼付け・保存・実行・結果照合。coverageの対応表は既存証拠に合わせて更新したが、未採取項目は残る。
- 通常チャットの7原本個別添付は不安定で、結合版へ切替済み。ナレッジ固有の事前確認質問は現行bundleで別チャットへ添付・送信し、回答原文を保存した（`catalog/evidence/normal-chat-knowledge-precheck-current-20260910.json`）。
- 最終版bundleのknowledge precheckとT01〜T10通常チャット生成を完了した。T01〜T03/T05〜T08は最終版Robinを専用PADへ貼付け・保存・2回実行した。T04は最終生成RobinのFilterParameters引用符差分で貼付け未成立、完全一致要求の再試験はコードを出さず拒否。T09はUI要素3件の捕捉・6アクション貼付け・保存まででWebAutomation実行未完了。T10は最終生成16アクションを保存したがWord SaveAs（9行目）で停止。旧版の通常チャット証拠を最終版の合格へ付け替えない。

## 失敗した方法と分かったこと

- 過去記録ではPAD左パネルのUI Automationが仮想化され、一度に表示された部分を全件と扱えなかった。
- 過去のEdge起動はWeb拡張機能との通信エラーで、ブラウザインスタンスが空白になった。UI・ブラウザー通し成功の根拠にはしない。
- 既存のOffice/PDF生成証拠は実Copilot/PADの別ケースを含むが、新規エージェントへファイル登録した試験ではない。
- `Run-NonLiveTests.ps1 -Suite All` は既存契約テストの途中までPASSしたが、`Test-Copilot.ps1` で長時間無出力となったためプロセスを停止した。全体PASSの証拠にはしない。
- 左パネル全件収集の初版はスクロール値が1.936...で停滞したため停止。SetScrollPercentで段階的に移動する方式へ変え、上端から下端までの412ノードを取得した。
- 列を持たないDataTableへ空行を追加するとデザイナーエラーとなった。列定義や行値を推測せず、失敗例として分離した。

## 人の操作が必要な項目・具体的な理由

- native Computer Use Trusted RPCは未構成だが、リポジトリ既存の厳格なUIAヘルパーで専用PADフローを一意に操作でき、T04の現作業版生成Robinの貼付け→保存→2回実行を実測した。T09は同じ方式でUI要素を捕捉・貼付けし、WebAutomationタイムアウトを記録した。
- 前回のM365 Copilot入口確認では個人用アカウントにAgent Builder項目がなく、`/create` とOffice Agentは指定入口ではなかった。この履歴は将来の別環境確認用に保持するが、今回の通常チャット検証をBLOCKEDにはしない。
- 通常チャットの本文入力・添付一覧・回答原文・T01〜T10はAgent Builderの検証結果と混同しない。初回のfile chooser失敗（`Not allowed`）は履歴として保持し、再試行では既存file inputへのCDP直接添付を確認した。

## 最終版受入の記録（2026-09-10）

最終版のケース別状態とPAD証拠は `catalog/evidence/normal-chat-final-package-acceptance-20260910.json`、PAD貼付け・実行の個別証拠は `catalog/evidence/normal-chat-final-pad-20260910/` に保存した。T04の先行有効版正例は `catalog/evidence/normal-chat-t04-current-v4-acceptance.json`、T04完全一致拒否は `catalog/generated/normal-chat-t04-20260910-final-exact-v1/`、T10のパスエスケープ差分とWord SaveAsエラーは同PAD証拠フォルダーに分離している。状態はpartialであり、未確認を完了扱いにしない。

## 次に行う1作業

T04の先行PAD正例と最終版チャット生成を保存した。残作業はT04の正確な原文受入、T09 WebAutomation環境復旧、T10のパス保持と独立再試験、最終指示ハッシュでの独立T01/T04/T10、負例と公開ゲートである。native CUAの再開条件はTrusted RPC構成であり、現状はUIAフォールバック証拠を使用する。Agent Builder／Copilot Studioは開かない。

## 現作業版の再開記録（2026-09-10）

PR #21後のmain `69fe344` から作業ブランチ `codex/issue-5-acceptance-20260910b` を作成し、未追跡の保護資料 `docs/agent-approach-comparison-2026-09-07.md` はSHA-256 `e0ea487e66b2f62303097cd580c9caeeffd80a3da08954ce35608b6a043e2699` のまま保持した。現物確認ではPAD 2.71.115.26224、Edge 152.0.4191.66、Office 16.0.20326.20132、日本語UI、既存ローカルfixture `http://127.0.0.1:8765/t09-local-test.html` を確認した。Power Fxは既存の2026-09-09採取条件（OFF）を継承記録として扱い、今回のUI再変更は行っていない。

T04先行成功・最終失敗、T10入力原文・生成・PAD再コピーの差分を `catalog/evidence/normal-chat-raw-provenance-20260910.json` に固定した。T04の6個→7個の引用符変化とT10の変更範囲外パス変化はいずれもCopilot生成時に発生し、PAD再コピーは別の下流正規化である。検出専用の `tests/Test-RobinRawContracts.ps1` は6 assertions PASSで、コードの自動修復は行わない。

原文保持規則を指示文とT04/T10技術資料へ最小追加し、`tools/Build-KnowledgeBundle.ps1` で7原本を再結合した。原本とbundleの対応は `copilot/knowledge-bundle-manifest-20260910b.json` に固定した。現作業版は指示SHA-256 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`、bundle SHA-256 `4282e4ece4f2d79ce26e85143fcab201091b185d9ee5d9defe4d8f49a4a7b2cd`、指示UTF-16 3,949である。`Test-CopilotRobinPackage.ps1` 86 observed actions、`Test-RobinCatalog.ps1` 77 checks、`git diff --check` はPASSした。

現作業版は別CDPセッションの既存file inputからbundleと合成Excelを添付し、T04生成・無修正貼付け・保存・2回実行まで確認した。T04の別チャット・別PADフロー独立再試験も成功した（`catalog/evidence/t04-current-revision-independent-acceptance-20260910.json`）。T10も現行bundle＋機械的コンテキスト添付から生成し、変更範囲外行の逐語一致、無修正貼付け・保存・実行、Excel/Word/PowerPoint成果物照合まで確認した（`catalog/evidence/t10-current-revision-acceptance-20260910.json`）。別の新規チャットと新規PADフローによるT10独立再試験も同じ結果を確認した（`catalog/evidence/t10-current-revision-independent-acceptance-20260910.json`）。ブラウザー拡張CUAのfile chooser失敗は履歴として `catalog/evidence/m365-current-package-upload-block-20260910b.json` に残す。T09はローカル画面の3要素と `T09-clicked` の到達性を再確認したが、これは手動DOM状態でありPAD WebAutomation実行ではない（`catalog/evidence/t09-current-environment-20260910b.json`）。旧版の成功を現作業版へ継承せず、現作業版T01〜T03/T05〜T09、独立T01、負例は未完了のまま保持する。必要な人の操作は、同じCDP/file-input経路で残りの現作業版ケースを送信すること、またはPADのTrusted RPCを構成してT09の無修正貼付け・実行を再観測することである。次の1作業は、T08を生成形式修正なしで期待エラーとして扱わず、未採取の形式境界を検査証跡へ固定し、T09以外の残りケースを受入すること。
T10の一括2ファイル添付はbundleのみ表示され生成前に停止したが、失敗原文は `catalog/evidence/normal-chat-current-revision-t10-batch-attachment-failure-20260910.json` に保全し、単一コンテキスト添付へ切り替えた。これは期待エラーではなく、添付方式の失敗として記録する。

P3の未採取項目は、coverageの `p3_blocked_items` に11件を項目単位で記録した。候補名だけの構文推測はせず、既存証跡で満たせる用途と、PAD Designer／WebAutomationの実測が必要な用途を分離している。

### 現作業版受入の追補（2026-09-10）

現作業版ではT01〜T07の一次受入、T04/T10の一次受入、T01/T04/T10の独立再試験、知識precheck、未採取構文・UI依存のfail-closed負例を確認済みである。T08は有効なRobin fenced blockを生成しない形式失敗、T09はWebAutomation実行未完了、P3の未観測項目は未実行のままとする。これらの判定は `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` と個別受入証跡を正本とし、旧版の成功を継承しない。
T09については、既存専用フローの待機値を一時的に1秒へ束ねたランタイムprobeで入力→クリック→`T09-clicked`取得→PAD完了を確認し、元の`WAIT 500`へ復元した。ただし現行packageの新規通常チャット生成Robinを無修正で貼付けた受入ではないため、P4のT09は未確認として保持する。現行6アクション貼付け先の90秒再probeは112秒時点でも実行中で、WebAutomationエラーと`未実行`結果要素が残ったため停止した（`catalog/evidence/t09-runtime-probe-20260910.json`、`catalog/evidence/p3-t09-current-runtime-reprobe-20260911.json`）。
P3ではBoolean（`SET P3Bool TO True`、preview=True）と減算（10−3→7）を新規専用フローで採取・保存・実行した。いずれも現行bundleへ統合すると再ハッシュ・T01〜T10再受入が必要なため、別probeとして保持する（`catalog/evidence/p3-boolean-probe-20260910.json`、`p3-subtract-probe-20260910.json`）。
日時の「日付の減算」は、合成2日付・単位Daysの新規専用フローで原文コピー・保存・2回実行（出力1）を確認した。別probeの「加算する日時」は1日加算を2回実行し、`2026/09/11 0:00:00`を確認した。カスタム書式化は専用probeで「現在の日時／システム タイム ゾーン」選択まで到達したが、保存更新時にPAD内部例外 `Sequence contains no matching element` が発生し、成功原文・実行値は未採取である。各probeは現行bundleへ未統合である（`catalog/evidence/p3-date-subtract-probe-20260910.json`、`catalog/evidence/p3-date-add-probe-20260910.json`、`catalog/evidence/p3-date-format-dialog-crash-20260911.json`）。
「現在の日時を取得」のDateAndTime設定も、システムタイムゾーンの新規専用フローで原文コピー・保存・2回実行し、`2026/09/10 19:01:11`形式の出力を確認した。カスタム書式化は未採取で、DateAndTime／加算probeは現行bundleへ未統合である（`catalog/evidence/p3-date-format-probe-20260910.json`、`catalog/evidence/p3-date-add-probe-20260910.json`）。
Excelでは合成`excel-catalog.xlsx`を開き、`Sheet1`を名前指定でアクティブ化する2アクションを新規専用フローからコピー・保存・2回実行した。別の専用probeでA1:C6をTypedValuesとして読み取り、`ExcelData=6行, 3列`・エラー0を確認し、3アクション原文を保存した。Run監視ヘルパーの完了表示は45秒以内に観測できなかったため、実行証跡はUIプレビュー境界として扱う。For eachの初期設定境界は保存後に入力・変数が消えるケースと読み取り前にループが置かれる失敗原文として保存したが、後続の専用probeではデータ反復の成功を再採取した（probeは現行bundleへ未統合）。初期境界の証跡は`catalog/evidence/p3-excel-sheet-probe-20260910.json`、`p3-excel-read-range-probe-20260911.json`、`p3-excel-read-range-probe-20260911.robin`、`p3-excel-foreach-configuration-boundary-20260911.json`に保存した。
Dの「ファイルが存在する場合」は、既存の合成fixtureを対象にtrue条件を2回、欠損パス条件を1回実行し、欠損パスのrawも取得した。branch bodyのside effectは未採取、probeは現行bundleへ未統合である（`catalog/evidence/p3-file-exists-probe-20260910.json`、`p3-file-exists-false-probe-20260910.json`、`p3-file-exists-false-20260910.robin`）。
Dの「ファイルの移動」は、合成sourceを専用destinationへ移動する1アクションをコピー・保存し、1回目の移動とsource再作成後のDoNothing衝突再実行を確認した。`MovedFiles=[]`、source／destinationハッシュ一致、false分岐は未採取である（`catalog/evidence/p3-file-move-probe-20260910.json`）。
Dの「ファイルの名前を変更する」は、拡張子保持・DoNothing設定で合成ファイルを1回改名し、2回目は衝突no-opを確認した。false分岐は未採取、probeは現行bundleへ未統合である（`catalog/evidence/p3-file-rename-probe-20260910.json`）。
Cの列付きDataTableは5列の作成を試したが、1値だけを渡す行追加でPAD native runtime error（指定値1件／列5件の不一致）となった。行値の正しい型・行反復・セル参照を推測せず、失敗原文を別証跡へ固定した（`catalog/evidence/p3-datatable-row-failure-20260910.json`）。
3列1行（A/10/対象）のDataTable作成を別の新規専用probeでコピー・保存・2回実行し、1行3列のpreviewを確認した。行追加の成功構文は未確認である。2回目の行追加試行では、ビジュアライザー上の1行3列が親ダイアログ保存後に実行時0行0列へ戻り、2値の`%RowValues%`も値数不一致で失敗した。現行失敗フローのUIでも同じ0行0列／`[A,B]`／2値対0列エラーを確認し、失敗Robin原文をSHA付きで保存した。成功構文を推測していない（`catalog/evidence/p3-datatable-create-success-20260911.json`、`catalog/evidence/p3-datatable-row-list-failure-20260910.json`、`catalog/evidence/p3-datatable-row-error-state-20260911.json`、`catalog/evidence/p3-datatable-row-error-state-20260911.robin`）。
If/Else/ENDとIf/Else-if/ENDは新規専用probeで正しいリテラル比較を採取し、各構造を2回実行した。branch side effectを追加していないため、入れ子・分岐内アクションは未採取で、probeは現行bundleへ未統合である（`catalog/evidence/p3-else-probe-20260910.json`、`catalog/evidence/p3-else-if-probe-20260910.json`）。
有限Loop 1..3へ`EXIT LOOP`を追加したprobeも、LoopIndex=1で終了することを確認した。別probeの`NEXT LOOP`は2回ともLoopIndex=4で終了した。入れ子・分岐内処理・loop side effectは未採取、probeは現行bundle未統合である（`catalog/evidence/p3-break-probe-20260910.json`、`catalog/evidence/p3-continue-probe-20260910.json`）。
同じ有限Loopへ`NEXT LOOP`を追加したprobeでは、LoopIndex=4で終了することを2回確認した。入れ子・loop side effectは未採取、probeは現行bundle未統合である（`catalog/evidence/p3-continue-probe-20260910.json`）。
`BLOCK / ON BLOCK ERROR / THROW ERROR / END`のエラー処理骨格、欠損ファイル子アクションによるruntime error、P3Worker作成＋Mainからの`CALL P3Worker`を新規専用probeでコピー・保存・実行した。追加のカスタムエラー`FileNotFound`へ`SET ErrorHandled TO $'''true'''`、続行ON／スローOFFを設定した名前付きルールはruntime errorのままだった。一方、既定の「すべてのエラー」へ`SET ErrorHandledDefault TO $'''true'''`、続行ON／スローOFFを設定したprobeは、欠損ファイル実行を2回とも完了し、trueプレビューを確認した。名前付きルールの一致条件や後続処理の一般化、現行bundle統合は未確認である（`catalog/evidence/p3-error-block-probe-20260910.json`、`p3-error-trigger-probe-20260910.json`、`p3-subflow-probe-20260910.json`、`p3-error-custom-handler-20260911.json`、`p3-error-default-handler-20260911.json`、`p3-error-default-handler-flow-20260911.robin`）。
リスト項目取得は、表示された「リストから項目を削除」を作成→追加→削除の最小probeで確認したが、削除後に項目値を返す出力変数がなく、取得構文の代用にはならなかった。現行の専用フローで左パネルの読取りインベントリは仮想化スクロールの終端が安定せず、401ノード以上を観測した時点で停止した。追加の検索語「項目」でも追加・削除・重複削除・共通項目検索・DataTable項目更新だけが実表示され、専用のリスト項目取得アクションは観測されなかった。ただし式参照等の別方式までは否定せず、推測で追加せず未確認として保持する（`catalog/evidence/p3-list-remove-probe-20260910.json`、`catalog/evidence/p3-list-get-inventory-boundary-20260911.json`、`catalog/evidence/p3-list-get-search-boundary-20260911.json`）。
Dの「フォルダーの作成」は合成fixture配下の新規専用フローで、原文コピー・保存・2回実行・`NewFolder`出力を確認した。存在確認・移動（衝突再実行）・名前変更も別probeで確認済みだが、各probeは現行bundleへ未統合で、false分岐のbranch body side effectは未採取のままとする（`catalog/evidence/p3-folder-create-probe-20260910.json`、`p3-file-exists-probe-20260910.json`、`p3-file-exists-false-probe-20260910.json`、`p3-file-move-probe-20260910.json`、`p3-file-rename-probe-20260910.json`）。

現作業版のT01〜T10／独立再試験／負例の判定表は `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` に固定した。T01〜T07、T04/T10一次受入、T04/T10独立再試験はPASS_CURRENT_REVISION、知識precheckはPASS_REFERENCE_ONLY、T08は生成形式失敗、T09はBLOCKEDとして扱う。知識precheckの回答原文は `catalog/generated/normal-chat-current-revision-knowledge-precheck-20260910/response.txt` に保存した。

P0〜P5の要件ごとの完了監査は `catalog/evidence/issue5-completion-audit-20260910.json` に固定した。P1と静的P5は完了、P2/P3は項目別BLOCKED、P4はT01〜T07・T04/T10一次・独立受入・知識precheckを確認済みで、T08形式失敗とT09実行依存を残すため全体完了とは扱わない。T04/T10のPAD貼付けヘルパー可視6件は仮想化による偽陰性で、Designerの9／16アクション表示と実行成功を優先した。

2026-09-11の現HEAD `b411a7c`で静的ゲートを再実行した。Raw契約6 assertions、Copilot package（3,949 UTF-16／7原本／86 observed actions）、Robin catalog 84 checks、bundled DOM 898 checks、`git diff --check`はPASS。`tests/Test-Copilot.ps1`はタイムアウト履歴のため未完了扱いとし、現行パッケージのT08/T09やP3統合成功とは扱わない（`catalog/evidence/current-package-static-check-20260911.json`）。

最新HEAD `1cd329c`でも同じ静的ゲートを再実行してPASSした。指示文・bundle・保護資料のSHAは不変で、`tests/Test-Copilot.ps1`のタイムアウトと現行パッケージの未完了判定を維持する（`catalog/evidence/current-package-static-check-20260911b.json`）。

最新HEAD `f308d90`でも同じ静的ゲートを再実行してPASSした。既定エラーハンドラーprobeは別証跡で成功したがbundle未統合で、T08/T09と残るP3の未完了判定を維持する（`catalog/evidence/current-package-static-check-20260911c.json`）。

2026-09-11 P3追補統合版では、7原本へ実測済みP3成功と失敗境界を反映し、bundle SHA-256を `0c89e53ce84671fd4bf1da4287563bf79f5164674f22907c8a420758310b36e6`、マニフェストを `copilot/knowledge-bundle-manifest-20260911.json` に更新した。新bundleでの知識precheck、T01〜T10、独立再試験は未実行で、旧bundleの成功証跡を継承しない。現行coverageは `catalog/evidence/current-package-status-20260911-p3-integration.json` を正本とする。

T09停止境界をP3統合版へ追補し、bundle SHA-256を `513fe84b8bc1fe3acb9d9092f057bace4d47215fe2cb30945b23d3ff77685831`、マニフェストを `copilot/knowledge-bundle-manifest-20260911b.json` に更新した。90秒再probeは112秒時点で実行中のまま停止したため、T09成功とは扱わない。新bundleの知識precheckとT01〜T10は未実行である（`catalog/evidence/current-package-status-20260911-p3b-integration.json`）。

Indexの旧版「未確認」記述をP3現行判定へ揃え、Office範囲読取りとT09再probe境界を反映したbundle SHA-256を `e35fa2f4a960841603cc876ad2e1e8af254ff66afc97b297224ffb3c44d08644`、マニフェストを `copilot/knowledge-bundle-manifest-20260911c.json` に更新した。新bundleの知識precheckとT01〜T10は未実行である（`catalog/evidence/current-package-status-20260911-p3c-integration.json`）。

最新HEAD `ffaf26a`でP3統合版のRaw契約6、Package 3949/7/86、Catalog 84、Copilot契約304、DOM 898、`git diff --check`を再実行してPASSした。いずれもローカル／モック検査で、ライブM365/Edgeと新bundleのT01〜T10受入は未実行である（`catalog/evidence/current-package-static-check-20260911-integrated.json`）。

現行HEAD `160ceec`は上記内容の文書整合メタデータ更新後の版であり、同静的ゲート結果を現行版へ結び付けた。ライブM365/Edgeと新bundleのT01〜T10受入は未実行である（`catalog/evidence/current-package-static-check-20260911-final.json`）。

P3統合版をHEAD `7b06805`で静的検査し、Raw 6、Package 3949/7/86、Catalog 84、DOM 898、`git diff --check`をPASSした。新bundleのCopilot/PAD受入は未実行である（`catalog/evidence/current-package-static-check-20260911-p3.json`）。

最新HEAD `2da9610`でもP3統合版の同じ静的ゲートを再実行してPASSした。新bundleのCopilot送信とT01〜T10受入は未実行である（`catalog/evidence/current-package-static-check-20260911-p3b.json`）。

最新HEAD `0ce051b`でもT09停止境界を含むbundleの同じ静的ゲートを再実行してPASSした。新bundleのCopilot送信とT01〜T10受入は未実行である（`catalog/evidence/current-package-static-check-20260911-t09.json`）。

同じ現行版で`tests/Test-Copilot.ps1`も完走し、304件のオフライン／モック契約検査をPASSした。ライブM365 Copilot／Edge統合ではないため、新bundleの知識precheck・T01〜T10・T08/T09受入は未完了のままとする（`catalog/evidence/current-package-static-check-20260911-t09b.json`）。

2026-09-11の現行bundle SHA `e35fa2f4a960841603cc876ad2e1e8af254ff66afc97b297224ffb3c44d08644` で、通常M365 Copilotの知識precheckをThink Deeperで送信し、回答原文・DOMハッシュを保存した（`catalog/generated/normal-chat-current-bundle-knowledge-precheck-20260911/result.json`）。これは参照確認のみで、Robin生成・T01〜T10・PAD受入を含まない。T01の後続ライブ受入は下記追補へ記録する。

## PAD作成権限・UIA復旧メモ（2026-09-11）

Consoleの `CreateNewFlowButton` → `NewFlowNameTextBox` → `OKNewFlowButton` をUIAで一意に操作し、`RobinKnowledgeT01CurrentBundleLive_20260911` のDesigner（タイトル `Power Automate | RobinKnowledgeT01CurrentBundleLive_20260911`）を取得できた。直接起動したDesignerが `MainWindowHandle=0`／UIAトップレベルなしになる境界、重複した作成ダイアログをCancelで0件へ戻す手順、作成後のPID・タイトル・HWND完全一致を `docs/pad-live-setup.md` に整理した。CUA Trusted RPCの成功とは混同せず、UIAフォールバックの実測として扱う。

この復旧経路で現行bundle T01を新規通常チャットから送信し、無修正Robinを専用PADへ貼付け・保存・2回実行した。出力・入力照合は `catalog/evidence/t01-current-bundle-pad-output-comparison-20260911.json`、全体対応は `catalog/evidence/t01-current-bundle-live-send-20260911.json` に保存した。現行P0〜P5の追補監査は `catalog/evidence/issue5-completion-audit-20260911-t01.json` に分離している。T01はPASSだが、T08/T09、残りP3、同一最終版の全件受入は未完了である。

## P3 DataTable行追加probe（2026-09-11）

専用フロー `RobinKnowledgeP3DataTableRow_20260911` で、3列1行のDataTable、3値の`RowValues`リスト、`AddRowToDataTable`（挿入場所=末尾）をPAD画面から設定した。DataTable欄を文字列ではなく`%DataTable%`変数参照へ直した後、無修正の6アクションを保存・再コピーし、2回実行とも`DataTable=2 行, 3 列`／`RowValues=[A, 10, 対象]`／エラーなしを確認した。成功構文は `catalog/evidence/p3-datatable-row-success-20260911.json` と原文証跡へ保存したが、現行bundleには未統合である。行反復・セル参照は未確認のまま保持する。

別の専用フロー `RobinKnowledgeP3DataTableCell_20260911` では、`ModifyDataTableItem` の `DataTable: DataTable`、列インデックス2、行インデックス0、値`CellChanged`を実測した。2回実行後の値ビューアーで列表示インデックス1=`A`、2=`10`、3=`CellChanged`を確認した。セル更新の成功は `catalog/evidence/p3-datatable-cell-success-20260911.json` に保存したが、現行bundle未統合で、行反復は未確認である。

## 2026-09-11 現行bundle T08ライブ形式境界

現行bundle SHA `e35fa2f4a960841603cc876ad2e1e8af254ff66afc97b297224ffb3c44d08644` を添付した新規通常M365 Copilotチャット（Think Deeper）へ、T08欠損ファイル負例の全文を送信した。回答は完了し、指定された欠損パス、UTF-8読取り、後続処理を置かない最小構成を説明したが、エラー捕捉・記録を含む完全な実測Robin原文がbundleにないとして、コードブロックを出さなかった。これはT08の期待エラーPAD受入ではなく、現行bundle生成形式失敗として扱う。

回答原文は `catalog/generated/normal-chat-current-revision-t08-20260911/response.txt`（DOM innerText観測2046文字を可視本文として保存し、段落区切りを保持したファイル2080文字、SHA `2AD70F32D73F6DC213B3D267A562FC994240798BA13242097EEAEF89BF7B1838`）に保存し、送信・完了・Robinブロック数0を `catalog/generated/normal-chat-current-revision-t08-20260911/result.json` に固定した。会話URLは `https://m365.cloud.microsoft/chat/conversation/e4b2343e-ddff-48f8-bf3e-80d62280c780` である。現行T08は有効Robinの無修正貼付け・保存・PAD期待エラー実行を行っていないため、P4とIssue全体はpartial/OPENのまま維持する。

DataTable行反復は専用フロー `RobinKnowledgeP3DataTableForeach_20260911` で2行3列（A/10/対象、B/20/対象2）を用いて実測した。`LOOP FOREACH CurrentItem IN DataTable` の本体へ `SET ForeachValue TO CurrentItem` を追加し、無修正4アクションを保存・再コピーした。ブレークポイント残留による初回タイムアウトは `catalog/evidence/p3-datatable-foreach-timeout-breakpoint-20260911.json` に分離し、解除後の2回は`ForeachValue=3列 { Column1: B, Column2: 20, Column3: 対象2 }`、`DataTable=2行, 3列`、エラーなしで完了した。成功証跡は `catalog/evidence/p3-datatable-foreach-success-20260911.json` と関連raw/runファイルに保存した。現行bundle未統合のため、同一最終版の再受入は未完了である。
Excel行反復は専用フロー `RobinKnowledgeP3ExcelForeachRuntime_20260911` で合成fixtureのA1:C6をTypedValuesとして読み取り、`LOOP FOREACH CurrentItem IN ExcelData` の本体へ `SET ExcelRowSeen TO CurrentItem` を追加した。無修正5アクションを保存・2回実行し、いずれも`ExcelData=6行, 3列`、最終行`対象外 / E / 40`、エラーなしで完了した。原文SHA-256は`db98d5bfa837ea65e0e92f2412b02f3847e3541fff653078c2645ae427939166`で、成功証跡は`catalog/evidence/p3-excel-foreach-runtime-success-flow-20260911.robin`、`p3-excel-foreach-runtime-success-run1-20260911.json`、`p3-excel-foreach-runtime-success-run2-20260911.json`に保存した。専用probe成功であり現行bundle未統合のため、同一最終版の再受入は未完了である。

T09の追加読み取り専用診断では、Edge用PAD拡張（ID `kagpabjoboikccfdghpdlaaopmgpgfdc`、version `2.70.0.35`）の有効状態、`nativeMessaging`権限、native manifestの許可originを確認した。しかし利用可能なBrowserNativeMessageHostログは`application.start.success`までで接続／要求完了イベントを含まず、現在のhostプロセスはChrome用origin・parent window 0でEdge実行に一致しなかった。これは拡張・native host接続経路の境界を狭める読み取り証拠であり、T09 WebAutomation成功や設定変更の根拠ではない（`catalog/evidence/t09-extension-handshake-boundary-20260911.json`）。

T08のエラー記録は、専用PADフローで`最後のエラーを取得`を保存先`LastError`、エラー消去`On`として設定し、無修正再コピーから`ERROR => LastError Reset: True`（SHA `816d164003f259523451cdd53af2832e82562f236562563775f2ae3a8a3a4213`）を取得した。欠損ファイルを含むブロックとの組合せは、ブロック原文とこのアクション原文を別々にPADから採取したうえで、PADのアクション順に組み合わせた参照例として保存している（単一のPAD clipboard rawではない）。クリーンな2回の実行は`true`と「ファイルが見つかりません」のLastErrorプレビューで完了し、エラーダイアログは出なかった（`catalog/evidence/p3-error-handler-measured-20260911.json`）。初回のDesigner内部例外は別失敗証跡へ分離した。

## 2026-09-11 T08エラー記録反映後の新bundle

PADで採取した`ERROR => LastError Reset: True`と2回の欠損ファイルエラー記録結果をControlナレッジへ最小追加し、7原本を再結合した。新bundle SHA-256は`38640a472186cb4d2e1f79443620112f6da7be0b4fc5834940dbdccc92da6358`、マニフェストは`copilot/knowledge-bundle-manifest-20260911d.json`である。e35fa2f4版でのT01成功・T08形式失敗は履歴として保持し、新bundleの合格へ継承しない。新bundleの知識precheck、T01〜T10、T08無修正PAD受入、T09、独立再試験、負例は未実行であり、Issueはpartial／OPENを維持する。新状態は`catalog/evidence/current-package-status-20260911-t08-error-handler.json`、`catalog/evidence/issue5-completion-audit-20260911-t08.json`に保存した。

## 2026-09-11 T08現行bundle期待エラー受入

測定済み組み合わせ参照を含む新bundle SHA `d7a0a7d6d9876aa1169aa96f377032f8e30ea37b8ea5ce753d3b6fb550b42835`で、通常M365 Copilot Think Deeperの知識precheckとT08を新規チャットから送信した。T08は有効Robinフェンス1件を生成し、専用PADフロー `RobinKnowledgeT08ErrorHandlerComposedLive_20260911` へ無修正貼付け・保存後、2回とも`ErrorHandledDefault=true`と欠損ファイルのLastError文字列を確認し、エラーダイアログなしで準備完了へ戻った。PAD再コピーの差分は`BLOCK`末尾空白1文字とCRLFのみであり、手修正・正規化は行っていない。証跡は`catalog/evidence/t08-current-bundle-composed-live-acceptance-20260911.json`である。旧e35fa2f4／38640a版結果は新bundleへ継承しない。

最終c78fd3 bundle SHA `c78fd388f6a3247772653d0c48b16444b095dd28821bf141f66946a36dcb3faf`では、ナレッジ掲載例の末尾空白警告を除いた後に知識precheckとT08を再送した。新規専用PADフロー `RobinKnowledgeT08ErrorHandlerFinalLive_20260911` へT08生成Robinを無修正で貼付け・保存し、2回とも`true`と欠損ファイルのLastError文字列、エラーダイアログなし、準備完了復帰を確認した。PAD再コピーの差分はPADが付けた`BLOCK`末尾空白1文字とCRLFのみで、生成コードは編集していない。証跡は`catalog/evidence/t08-current-bundle-final-live-acceptance-20260911.json`、新bundle監査は`catalog/evidence/issue5-completion-audit-20260911-complete-t08.json`である。T01〜T07/T09/T10、独立再試験、同一最終版負例は未完了である。

最終候補61f040 bundle SHA `61f040b900dfc90fe395f21426bc7a684c7dbf45c2ac82e38d1f00490ffc2f6b`では、T01組合せ根拠をExamplesへ追加した。新規通常チャットの知識precheck、T01、T08を同一版で実施し、T01は`pre>code`の1ブロックを取得して新規PADへ無修正貼付け・保存・2回実行、出力90 bytes・UTF-8 BOM・CRLF・期待SHA一致・入力不変を確認した。T08も新規PADへ無修正貼付け・保存・2回実行し、`true`と欠損ファイルのLastErrorを確認した。T01証跡は`catalog/evidence/t01-current-final2-live-acceptance-20260911.json`、T08証跡は`catalog/evidence/t08-current-final2-live-acceptance-20260911.json`である。T02〜T07/T09/T10、独立再試験、同一最終版負例は未完了である。
# Final3 fixed bundle update (2026-09-11)

Final3 bundle SHA-256: `2bc3f2b4c5c709e94547ccf4b75f7084c9c424605781e01414f6783a1fd026a7`. The normal M365 Copilot + PAD acceptance set now covers T01-T08 and T10 on this exact hash, with independent T01/T04/T10 retests and a current fail-closed negative suite. T09 remains blocked before Run because PAD cannot resolve the previously captured web UI elements in the new flow. P3 gaps (list retrieval, custom date formatting, nested/side-effect branch behavior, named custom error matching, and related unbundled probes) remain explicitly open.

## 2026-09-11 P3教材統合とT09別空フロー再確認

Final3固定版（bundle `2bc3f2b4c5c709e94547ccf4b75f7084c9c424605781e01414f6783a1fd026a7`）の受入済み成果・初回失敗・T09停止境界は保全した。P3専用probeで実測済みだったDataTable行追加・セル更新・行反復とExcel行反復を7原本へ統合し、現行bundleを `dd668166e4c04b02878a6fae65e4583b6d6c910847559161c6707ae90e6626a5`、マニフェストを `copilot/knowledge-bundle-manifest-20260911h.json` へ更新した。

DataTable行追加は3列の`DataTable`へ3値`RowValues`を渡し2回とも2行3列、セル更新は列2・行0を`CellChanged`へ更新、行反復は最終行`B / 20 / 対象2`を確認した。Excel行反復はA1:C6の`ExcelData`を反復し、最終行`対象外 / E / 40`、6行3列、Excel終了を2回確認した。初回ブレークポイント停止・0列復帰・値数不一致は成功例と分離した。

P3統合後は指示文SHA `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`、bundle SHA `dd668166e4c04b02878a6fae65e4583b6d6c910847559161c6707ae90e6626a5`である。新bundleの通常M365 Copilot知識precheckは、指示全文の本文逐語一致（末尾UIマーカーのみ除外）とbundle／指示ファイル2添付を確認し、RobinなしのP3要約を取得してPASS_REFERENCE_ONLYとした。T01〜T10、T01/T04/T10独立再試験、負例は未実行で、旧版PASSを継承しない（`catalog/generated/normal-chat-current-bundle-p3b-full-precheck-20260911/`、`current-package-status-20260911-p3b.json`、`issue5-completion-audit-20260911-p3b.json`）。

T09は別空フロー`RobinKnowledgeT09Separate_20260911`を作成し、Final3 T09 Robinの6アクション貼付け・保存・再確認を実施した。UI要素ピッカーの実測ではEdgeのWindow/Paneまでしか列挙されず、`Input text 't09-input'`、`Button '実行'`、`Paragraph '未実行'`は登録できなかった。Designerエラー3件、Start無効、Run未開始を確認した。別のLaunchEdge単独フローは貼付け・保存・Run完了（Browser変数preview）まで確認したが、対象ページのWeb DOM要素やWebAutomation要求完了を示さず、T09通し成功へ拡張していない（`catalog/evidence/t09-separate-ui-registration-20260911.json`、`t09-edge-launch-paste-20260911.json`、`t09-edge-launch-run-20260911b.json`）。

現状は`partial／OPEN`。新bundleのT01は全文指示＋同版bundle、無修正Robin、PAD 2回実行、成果物照合までPASSした。残りはT02〜T10→独立T01/T04/T10→負例を同一版で再受入し、T09はEdge拡張/native-hostがWeb DOM要素を返す条件で無修正6アクションを2回通し実行すること。未確認のP3はリスト項目取得、カスタム日時書式、入れ子／branch side effect、名前付きカスタムエラー一致である。
