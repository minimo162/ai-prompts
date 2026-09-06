# 業務エージェント PoC — Issue #5

CMDからローカルへ同期して起動する、Windows PowerShell + HTML の業務エージェントです。M365 Copilotが作業を計画し、Power Automate Desktop (PAD) が実行し、必要な箇所で同じ `App.ps1` の `AiCall` を呼びます。

**開発中です。Issue #5 の実機ゲートは未完了です。** ローカルの契約検証と、実際のCopilot/PAD/共有フォルダー/別PCでの検証を区別します。[検証記録](docs/issue-5-validation.md)を参照してください。

Issue #8〜#14の実装を進めています。画面上部のCSV分類では、列・文字コード・分類条件を指定し、送信範囲を確認してから開始します。Copilotが型付き操作を選び、ホストが対象・件数・結果を照合します。CSV処理にはPADの準備は不要です。要確認行への追加指示、未送信分の続行、過去の結果との比較を実装しましたが、実M365の50件業務・別PC受入は未完了です。[実装状況と残作業](docs/issues-8-14-progress.md)を参照してください。

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

従来のPAD検証用依頼の準備:

1. HTML画面の「設定・接続確認」で「Copilot を開く」を押し、アプリ専用のEdgeでM365 Copilotへサインインします。既存の個人ブラウザープロファイルは流用しません。
2. PADで、Power Fxを無効にした空の「業務エージェント専用」フローを作成して保存し、Mainデザイナーを開いたままにします。別の名前を付けた場合は、画面の設定も同じフロー名にします。既存業務フローを指定しないでください。アプリは専用フローに自分で反映したアクションだけを次回以降置き換えます。
3. 「自己診断する」で接続状態を確認します。操作対象が見つからない場合、PADの反映や実行へ進みません。
4. やりたいことと対象を入力して開始します。質問があれば画面で回答します。画面を閉じても処理は停止しません。CMDで開き直すと同じ状態へ接続します。停止には画面の「停止する」を使います。

従来のPAD互換経路の自動実行は、UTF-8テキストの読み取り、新しい成果物ファイルへの書き出し、変数、IF分岐、有限待機、固定AiCallテンプレートに限定しています。翻訳、要約、分類、抽出、判断を呼び出せます。Excel/ブラウザー/任意アプリ操作は、この版の検証済みアクション集合に含まれません。未対応の目的を完了扱いにはしません。元の業務ファイルの削除・上書き、送信、公開、本番更新は実行しません。

PADのMain編集が途中で止まった場合は、元Mainと所有記録を保全し、新しい依頼を止めます。「保全・復旧」から、停止・同じ対象・内容の一致を確認した場合だけ元Mainを戻して保存できます。元処理のRunは行いません。クリップボードの復元失敗と未確認の途中ファイルも表示します。[復旧条件と未検証範囲](docs/pad-recovery.md)を参照してください。

## 更新の扱い

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
