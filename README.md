# PAD Robin Copilotエージェント用 指示文・ナレッジ

このリポジトリの今回の成果物は、PADの実測Robinを根拠にMicrosoft 365 Copilotエージェントがフロー案を生成・修正するための配布物です。入口は [copilot/README.md](copilot/README.md) です。指示欄へ貼る文章は [copilot/agent-instructions.txt](copilot/agent-instructions.txt)、登録用ナレッジと手順は `copilot/knowledge/` にあります。PAD・Copilotを自動実行する新しいアプリは作りません。

通常チャットでの検証条件と禁止事項は [CODEX_CORRECTION_M365_CHAT_VALIDATION.md](CODEX_CORRECTION_M365_CHAT_VALIDATION.md) を先に確認してください。Agent Builder／Copilot Studioの登録は今回の検証先ではありません。

2026-09-10の現作業版は、原文保持の再発防止を反映した指示文SHA-256 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e` と、7原本から再生成したbundle SHA-256 `4282e4ece4f2d79ce26e85143fcab201091b185d9ee5d9defe4d8f49a4a7b2cd` です。知識precheck、T01〜T07、T04/T10一次受入、T01/T04/T10独立再試験、未採取構文・UI依存のfail-closed負例を確認しました。T08は有効なRobin fenced blockを生成しない形式失敗、T09は既存専用フローのランタイムprobeは成功したものの現行package Robinが未確認です。P3ではBoolean、減算、日時加算・減算、フォルダー作成を別の合成専用probeで採取・実行しましたが、bundleには未統合です。旧版生成・PAD結果は現作業版へ継承していません。T04/T10の発生段階の比較は [raw provenance](catalog/evidence/normal-chat-raw-provenance-20260910.json)、結合版の再生成は [Build-KnowledgeBundle.ps1](tools/Build-KnowledgeBundle.ps1) を参照してください。

実測原文の正本は [catalog/index.json](catalog/index.json)、観測範囲は [catalog/coverage.json](catalog/coverage.json)、途中経過は [docs/robin-knowledge-progress.md](docs/robin-knowledge-progress.md) です。既存の採取原文・検証証拠は保全し、未観測のアクションを全機能対応とは表示しません。

P3追補：Boolean、数値減算、日時加算・減算、DateAndTime取得、フォルダー作成、Excelシート選択は別の合成専用probeで採取・実行済みですが、現行7ファイルbundleには未統合です。カスタム日時書式化は未確認、T08は形式失敗、T09は現行package Robin未確認です。

ファイル存在確認の`IF ... THEN`／`END`と、ファイル移動の1回probeも別証跡で固定しています。false分岐・名前変更・移動の再実行は未確認です。
ファイル名前変更も成功1回とDoNothing衝突no-op 1回を別probeで固定しました。false分岐・移動の再実行は未確認です。
列付きDataTableの行追加は、値数不一致のnative runtime errorを再現し、正しいRowToAdd型を推測せず失敗証跡として保持しています。
別試行ではビジュアライザー保存後の0列への戻りも確認し、成功構文を推測していません。
If/Else/ENDとIf/Else-if/ENDの構造は別probeで実行まで確認していますが、入れ子・分岐内処理は未確認です。
有限Loopの`EXIT LOOP`も別probeでLoopIndex=1、`NEXT LOOP`も2回実行してLoopIndex=4を確認していますが、入れ子とloop内副作用は未確認です。
（Loop Continue probeは現行bundleへ未統合です。）
エラー処理の`BLOCK / ON BLOCK ERROR / THROW ERROR / END`骨格、欠損ファイル子アクションのruntime error、P3Worker作成＋Mainからの`CALL P3Worker`も別probeで確認していますが、カスタムハンドラーは未確認です。

P3ではファイル存在確認の`IF ... THEN`／`END`も別probeで2回実行しました。各probeは現行bundle未統合で、残るfalse分岐・移動・名前変更・データ反復等は未確認です。

P3追補：Boolean、数値減算、日時加算・減算、DateAndTime取得、フォルダー作成は別の合成専用probeで採取・実行済みですが、現行7ファイルbundleには未統合です。カスタム日時書式化は未確認、T08は形式失敗、T09は現行package Robin未確認です。

M365 Copilot内Agent Builderを利用先とする継続方針の訂正は [CODEX_CORRECTION_M365_AGENT_BUILDER.md](CODEX_CORRECTION_M365_AGENT_BUILDER.md) に記録しています。

## 過去資産: 汎用業務エージェント（開発中）

現在は実装をチェックポイントとして保存し、方式を見直す段階です。[次セッションへの引き継ぎ・社内条件・比較対象](docs/session-handoff-2026-09-07.md)を参照してください。

CMDからローカルへ同期して起動する、Windows PowerShell + HTML の業務エージェントです。M365 Copilotが作業を計画し、Power Automate Desktop (PAD) が実行し、必要な箇所で同じ `App.ps1` の `AiCall` を呼びます。

**開発中です。Issue #5 の実機ゲートは未完了です。** ローカルの契約検証と、実際のCopilot/PAD/共有フォルダー/別PCでの検証を区別します。[検証記録](docs/issue-5-validation.md)を参照してください。

画面は「やりたいこと」と「作業対象」から依頼する構成です。PAD左パネルから採取した[Robinカタログ](catalog/README.md)を根拠に、プロンプトと検証器を広げています。現在の追加対応はリスト作成・文字列項目追加、テキスト置換・分割・結合、数値変換・書式化・有限ループです。未定義変数や分岐後の不確かな型は実行前に拒否します。正規表現置換を含む1ケースでは、新UI→実M365→PAD実行1回→入力/出力を比較する完了判断→DONEまで約80秒で確認しました。[実機記録と未完了範囲](docs/general-agent-live-2026-09-07.md)を参照してください。他の操作や複数業務全般の受入は継続中です。

Office用の[Robin生成プロンプト](pad-robin-prompts.md)には、PAD左欄から採取したExcel・Word・PowerPointの17種類・22設定例を収録しました。採取形式をアプリの検証器・成果物観測へ接続し、新規3形式の作成は画面から開始してDONEまで確認しています。[現在の接続範囲と実機結果](docs/document-run-checkpoint-2026-09-08.md)を参照してください。

PDFの5種類・11設定例も同じプロンプトに収録しました。テキスト・表・画像の抽出とページ抽出・統合を実機で検査しています。この環境では2ファイルの統合が入力リストと逆順になる挙動があり、[PDF採取記録](docs/pdf-action-capture.md)に条件と結果を記載しています。

CSV分類は「CSVの定型分類」を開いて使う補助機能です。対象・列・文字コード・分類条件・送信範囲を確認して開始します。CSV処理にはPADは不要です。過去の実装と未完了の受入は[実装状況](docs/issues-8-14-progress.md)、新しい汎用化の範囲は[採取・接続の方針](docs/robin-action-catalog.md)を参照してください。Office・PDFは限定した形式で自動Runへ接続しました。ブラウザー等と、既存文書・他環境での受入は継続中です。

## 配布と起動

共有フォルダーへ配置するアプリ本体は次の3ファイルです。

```text
業務エージェント.cmd
App.ps1
index.html
```

`業務エージェント.cmd` をダブルクリックします。通常の処理は `%LOCALAPPDATA%\AiPromptsAgent` で行います。利用者のデータやログを共有フォルダーへ書き戻しません。

必要な環境は Windows、Windows PowerShell 5.1、Microsoft Edge、PAD、M365 Copilotを利用できるアカウントです。Node、Python、独自EXE、常駐サービスは配布に不要です。認証は利用者が行います。組織で禁止されている接続・実行をアプリが解除することはありません。ランチャーは自分のPowerShellプロセスだけに実行ポリシー引数を指定し、永続設定やグループポリシーを変更しません。

配布の想定経路は **GitHub → 社内PC → 社内の共有フォルダー → 利用者ローカル** です。社内PCで受け取った同じ版の上記3ファイルを、配布担当者が実際の共有フォルダーへ配置します。リポジトリのテスト・開発用補助・`.work` は利用者への配布に含めません。更新中は起動を控え、3ファイルの配置完了後に利用を再開してください。開発PC上の `\\localhost\AiPromptsAgentPoC$` は作り替え可能な検証用共有で、実際の配布先ではありません。社内PCからの導入・更新・実行は別途確認が必要です。

現在はPADとM365 Copilotを日本語表示で使用してください。他言語の画面は未検証です。ChatGPTのブラウザー拡張機能は不要です。

PADを使う汎用依頼の準備:

1. HTML画面の「設定・接続確認」で「Copilot を開く」を押し、アプリ専用のEdgeでM365 Copilotへサインインします。既存の個人ブラウザープロファイルは流用しません。
2. PADで、Power Fxを無効にした空の「業務エージェント専用」フローを作成して保存し、Mainデザイナーを開いたままにします。別の名前を付けた場合は、画面の設定も同じフロー名にします。既存業務フローを指定しないでください。アプリは専用フローに自分で反映したアクションだけを次回以降置き換えます。
3. 「自己診断する」で接続状態を確認します。操作対象が見つからない場合、PADの反映や実行へ進みません。
4. やりたいことと対象を入力して開始します。質問があれば画面で回答します。画面を閉じても処理は停止しません。CMDで開き直すと同じ状態へ接続します。停止には画面の「停止する」を使います。

PAD経路の自動実行は、UTF-8テキストの読み取り、新しい成果物ファイルへの書き出し、文字列・リスト・数値変換、変数、IF分岐、有限ループ・待機、固定AiCallテンプレートなど、検証済みの構文に限定しています。翻訳、要約、分類、抽出、判断を呼び出せます。Excel/ブラウザー/任意アプリ操作は、この版の検証済みアクション集合に含まれません。未対応の目的を完了扱いにはしません。元の業務ファイルの削除・上書き、送信、公開、本番更新は実行しません。

PADのMain編集が途中で止まった場合は、元Mainと所有記録を保全し、新しい依頼を止めます。「保全・復旧」から、停止・同じ対象・内容の一致を確認した場合だけ元Mainを戻して保存できます。元処理のRunは行いません。クリップボードの復元失敗と未確認の途中ファイルも表示します。[復旧条件と未検証範囲](docs/pad-recovery.md)を参照してください。

CSVの送信後に結果不明となった場合は、「送信済みの既存回答を照合する」で同じ要求IDの完全な回答だけを読み取れます。再送信はしません。照合済みの結果を保って未送信分を新しい候補へ引き継ぐ場合は、改めて送信範囲を確認します。形式や終端が欠けた回答は補完しません。[実Copilot測定の経過](docs/live-benchmark-2026-09-07.md)を参照してください。

## 更新の扱い

新しい汎用依頼の成果物は、画面からID検証付きで開く要求を送れます。「実行時に確認した内容」で観測時のテキストも表示できます。関連付けのない端末や古い履歴の扱いは[成果物の確認方法](docs/general-artifacts.md)を参照してください。

アプリは `app/<版>-<内容のSHA256>/` に保存します。初回・内容変更時だけ一時ディレクトリへコピーし、3ファイルと版・ハッシュを検査してから `app/current.json` を切り替えます。起動中の版を上書きせず、ジョブは開始時のPS1を使い続けます。状態、設定、認証プロファイル、履歴、成果物は `data/` です。

配布時はAppの `# App-Version` とHTMLの `app-version` を合わせ、`tools/Seal-AgentRelease.ps1`でApp・HTML・CMDの組合せを封入してから検証・公開します。版番号が同じでも、対応するハッシュが異なる組合せはCMD起動前に拒否します。Appを編集すると封入は無効になるため、検証前に再封入が必要です。App.ps1のUTF-8 BOMありを維持してください。[凍結・持込み・公開・復旧の手順](docs/release-operations.md)を参照してください。共有パスが利用不可で、検証できるローカル版がある場合だけ、その旨を表示して継続します。共有フォルダー自体が開けない場合、そこにあるCMDもダブルクリックできないため、既に同期したローカル版のCMDから起動してください。

以前の版を自動削除しません。保存済みの古いCMDも現在のローカル版を開く入口です。通常は低い共有版への更新を拒否しますが、「配布版・旧版への復帰」から互換性を確認した保存済みの版を明示選択できます。入力・成果物・履歴を保ったまま旧版に固定し、CMDから開き直します。固定解除後は共有側のCMDで更新できます。未封入の従来キャッシュは、元のハッシュが一致するときだけ新しい共有版への更新用に読取り照合し、旧版候補にはしません。実行中のジョブは開始版を使い続けます。CSVの続行も記録した開始版のPS1とハッシュを照合します。

## 実行の契約

- `Run`: `ACT` / `DONE` / `ASK_USER` / `BLOCKED` をJSONで判定します。通常文章の「完了」では判定しません。最大往復数・回答待ち・Copilot・PADの各待機には期限があります。
- `ACT`: Robinを有限の許可構文と対象範囲で検証し、PADへ反映、全文コピー戻し、保存状態、保存後の全文一致を確認してから一度だけ実行します。今回固有の開始・終了記録と成果物を照合します。結果不明なら再実行しません。
- `AiCall`: `job_id/run_id/ai_call_id` で要求と結果を対応付けます。要求は実行中ジョブ配下の `calls/<ID>/request.json`、結果は同じ場所の `result.json` だけです。任意パスの結果書き込みや全体Runの再帰起動はしません。
- AiCallはUTF-8入力256KB以内、メタデータを含むJSON化後のプロンプト180,000文字以内、待機5〜240秒です。容量・文字数の上限超過は切り詰めず、送信前に `input_too_large` として失敗させます。
- AiCallの `success/needs_review/failed/cancelled` は全体のDONEとは別です。入力件数・出力件数も照合します。成功した本文は `result.txt`、状態は `status.txt` に返します。Robinは直後にこの順で読みます。失敗時に結果本文を用意して後続を続けることはありません。
- 初版では1つのPAD実行中に最大3回のAiCallを直列実行できます。外側RunはPAD待機中にCopilotの排他を保持しません。
- 宣言したAiCallはすべて実行する必要があります。IFの条件によりAiCall自体をスキップする構成は未対応です。AI結果を読んだ後の分類・状態による分岐は利用できます。
- `DONE`: そのジョブで実際に観測した成果物が存在し、観測時のハッシュと一致することを確認します。入力ファイルを成果物として流用しません。

次の計画には成果物の実際のUTF-8本文、ハッシュ、件数、切り詰め状態を渡します。本文全体を確認できていない成果物を根拠にDONEにはしません。前の実行の成果物を再利用する場合も、同じジョブで観測した正確なパスと現在のハッシュを照合します。質問ごとのIDと回答の一度だけの受付により、複数画面から回答を上書きしたり、古い質問への回答を次の質問へ流用したりしません。

計画の応答は、1つのコードブロック内にメタデータJSONとRobin本文を明示的な目印で区切って受け取ります（Planner V2）。従来の2ブロック形式の読取りも維持しています。Robinは最大64000 UTF-16文字・250行で、コードの引用符、バックスラッシュ、空白をそのまま保持します。画面上で空行と特殊な空白を混同しないよう、空行だけは今回の要求IDを含む専用の目印で送り、完全一致した目印を空行へ復号します。メタデータと復元後の最終JSONは、それぞれ最大1048576文字です。PAD内のAiCallは従来の番号付きJSON断片（1断片最大8192文字、最大256ブロック、連結後最大1048576文字）を使います。

どちらも要求ID・順序・欠落・重複・終端を検査し、応答IDとブロック境界を含む全文が3回連続で一致し、生成が終了したことを確認します。折りたたみ表示でも、既知の構造に全行が存在し、この検査を通った応答だけを取得します。不完全なJSONやRobinの修復、正当なバックスラッシュの削除は行いません。ファイル本文やAIの業務結果はデータとして扱います。Planner V2の実機での通し確認は進行中です。

確定した失敗は次の判断へ返します。同じ失敗手順を新しい実行IDに置き換えただけのACTは拒否します。比較時にだけアプリ発行のパス・IDを置き換え、実行するRobin本文は変更しません。結果不明・中止はそのまま終了します。

Copilotへ送信するタブはジョブごとに新規作成し、同じジョブの計画とAiCallで使います。サインイン用や以前のジョブのタブは送信先に流用しません。最初の送信前に過去の回答や下書きが見つかれば停止します。ジョブごとのタブ分離は実M365で確認済みです。

ローカルHTTP APIは `127.0.0.1` に限定します。ページの起動トークン、Host、Originを検査し、任意ファイル配信APIは設けません。画面の表示文字列はDOMのテキストとして描画します。

## 開発と検証

Appのロジックは1つのPS1内の関数です。`-Mode Library` は関数を読み込むだけで、サービス起動やCopilot/PAD操作は行いません。テスト・説明書は配布ファイルには含めません。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Seal-AgentRelease.ps1 -Directory "$PWD" -Channel candidate
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-App.ps1 -AppSourcePath "$PWD\App.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Copilot.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File tests\Test-CopilotPlannerV2.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File tests\Test-PlannerV2Transport.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Pad.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Http.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Launcher.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-PublishAgentSource.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-AiCallProcess.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-AiCallProviderFailure.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File tests\Test-ClipboardSnapshot.ps1
```

`Test-AiCallProviderFailure.ps1` は、実AiCall子プロセスのプロバイダー関数だけを差し替え、拒否・空回答・期限・応答時中止の受信処理を検査します。実M365の応答やPADフローの異常系検証とは区別します。

開発用の状態領域を分ける場合:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File .\App.ps1 -Mode Serve -HomePath "$PWD\.local"
```

テスト結果を他PC対応の証明として使わないでください。PAD 2.71の日本語デザイナーで固定A/Bの貼り付け・保存・置換・実行・結果判定と、実Copilotによる分類からPAD2回、最終ファイル保存、完了表示までの通し検証が通りました。長文生成の安定性、失敗条件の実機検証、他PCでの確認は残っています。

仕様: [Issue #5](https://github.com/minimo162/ai-prompts/issues/5)。Robinの元プロンプト: [pad-robin-prompts.md](pad-robin-prompts.md)。

一般仕様の確認先: [PADデザイナーのコピー・保存](https://learn.microsoft.com/en-us/power-automate/desktop-flows/designer-workspace)、[スクリプト実行アクション](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/scripting)、[Edge DevTools Protocol](https://learn.microsoft.com/en-us/microsoft-edge/devtools/protocol/)。これらは本アプリの実機合格証拠ではありません。


## アプリ接続の追記（2026-09-08）

上記の採取時点の「自動Run未接続／未検証」は、その後の実装で更新しました。Office/PDFの採取形式を検証器・出力観測・完了判定へ接続し、Office3ファイル作成とPDF各操作の2ケースをアプリ開始からDONEまで確認しました。PDF表は追加採取したCSV書出しで保存します。既存51例に今回の18例（日時取得、空テーブル、行追加失敗、CSV読取り、CSV書出し、ファイルコピー、サブテキスト取得、テキスト書出し、テキスト変数書込み2設定、For each、If2、Excel/Word編集可能起動2設定、フォルダー取得2設定、ファイル変数読取り）を加え、現在のカタログは69設定です。

検証範囲・制約・先行失敗・未完了事項は [自動Run接続チェックポイント](docs/document-run-checkpoint-2026-09-08.md) を参照してください。既存Office文書の自動Run、書式・レイアウト、別PC・社内受入は未確認です。
現在の観測カタログは `catalog/index.json` の73設定です。追加のFilterDataTable、CSVヘッダー付き読取り・書出し、PDFページ2単独抽出を含みます。
