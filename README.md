# 業務エージェント PoC — Issue #5

CMDからローカルへ同期して起動する、Windows PowerShell + HTML の業務エージェントです。M365 Copilotが作業を計画し、Power Automate Desktop (PAD) が実行し、必要な箇所で同じ `App.ps1` の `AiCall` を呼びます。

**開発中です。Issue #5 の実機ゲートは未完了です。** ローカルの契約検証と、実際のCopilot/PAD/共有フォルダー/別PCでの検証を区別します。[検証記録](docs/issue-5-validation.md)を参照してください。

## 配布と起動

共有フォルダーへ配置するアプリ本体は次の3ファイルです。

```text
業務エージェント.cmd
App.ps1
index.html
```

`業務エージェント.cmd` をダブルクリックします。通常の処理は `%LOCALAPPDATA%\AiPromptsAgent` で行います。利用者のデータやログを共有フォルダーへ書き戻しません。

必要な環境は Windows、Windows PowerShell 5.1、Microsoft Edge、PAD、M365 Copilotを利用できるアカウントです。Node、Python、独自EXE、常駐サービスは配布に不要です。認証は利用者が行います。組織で禁止されている接続・実行をアプリが解除することはありません。ランチャーは自分のPowerShellプロセスだけに実行ポリシー引数を指定し、永続設定やグループポリシーを変更しません。

初回の準備:

1. HTML画面の「設定・接続確認」で「Copilot を開く」を押し、アプリ専用のEdgeでM365 Copilotへサインインします。既存の個人ブラウザープロファイルは流用しません。
2. PADで、Power Fxを無効にした空の「業務エージェント専用」フローを作成して保存し、Mainデザイナーを開いたままにします。別の名前を付けた場合は、画面の設定も同じフロー名にします。既存業務フローを指定しないでください。アプリは専用フローに自分で反映したアクションだけを次回以降置き換えます。
3. 「自己診断する」で接続状態を確認します。操作対象が見つからない場合、PADの反映や実行へ進みません。
4. やりたいことと対象を入力して開始します。質問があれば画面で回答します。画面を閉じても処理は停止しません。CMDで開き直すと同じ状態へ接続します。停止には画面の「停止する」を使います。

初版の自動実行は、UTF-8テキストの読み取り、新しい成果物ファイルへの書き出し、変数、IF分岐、有限待機、固定AiCallテンプレートに限定しています。翻訳、要約、分類、抽出、判断を呼び出せます。Excel/ブラウザー/任意アプリ操作は、この版の検証済みアクション集合に含まれません。未対応の目的を完了扱いにはしません。元の業務ファイルの削除・上書き、送信、公開、本番更新は実行しません。

## 更新の扱い

アプリは `app/<版>-<内容のSHA256>/` に保存します。初回・内容変更時だけ一時ディレクトリへコピーし、3ファイルと版・ハッシュを検査してから `app/current.json` を切り替えます。起動中の版を上書きせず、ジョブは開始時のPS1を使い続けます。状態、設定、認証プロファイル、履歴、成果物は `data/` です。

配布時はAppの `# App-Version` とHTMLの `app-version` を同じ新しい版にして、3ファイルの置換完了後に利用可能にしてください。共有側が更新中で版が異なる場合やファイルが欠けた場合はエラーにします。共有パスが利用不可で、検証できるローカル版がある場合だけ、その旨を表示して継続します。共有フォルダー自体が開けない場合、そこにあるCMDもダブルクリックできないため、既に同期したローカル版のCMDから起動してください。

以前の版を自動削除しません。更新に伴って利用者データを消さないためです。保存済みの古いCMDを開いても、検証した現在のローカル版を起動します。共有版がローカル版より古い場合は更新を拒否します。実行中のジョブがある場合は既存サーバーへ再接続し、その版を使い続けます。ジョブが終了した後にCMDから開き直すと、新しい版へ切り替わります。

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

AI応答からコードフェンスや正当なバックスラッシュを削除せず、不完全なJSONやRobinを修復して実行しません。要求ごとのID、終端マーカー、今回の回答、生成終了を確認します。ファイル本文やAIの業務結果はデータとして扱います。

確定した失敗は次の判断へ返します。同じ失敗手順を新しい実行IDに置き換えただけのACTは拒否します。比較時にだけアプリ発行のパス・IDを置き換え、実行するRobin本文は変更しません。結果不明・中止はそのまま終了します。

Copilotへ送信するタブはジョブごとに新規作成し、同じジョブの計画とAiCallで使います。サインイン用や以前のジョブのタブは送信先に流用しません。最初の送信前に過去の回答や下書きが見つかれば停止します。この分離の実M365での確認は残っています。

ローカルHTTP APIは `127.0.0.1` に限定します。ページの起動トークン、Host、Originを検査し、任意ファイル配信APIは設けません。画面の表示文字列はDOMのテキストとして描画します。

## 開発と検証

Appのロジックは1つのPS1内の関数です。`-Mode Library` は関数を読み込むだけで、サービス起動やCopilot/PAD操作は行いません。テスト・説明書は配布ファイルには含めません。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-App.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Copilot.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Pad.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Http.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Launcher.ps1
```

開発用の状態領域を分ける場合:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File .\App.ps1 -Mode Serve -HomePath "$PWD\.local"
```

テスト結果を他PC対応の証明として使わないでください。PAD 2.71の日本語デザイナーで固定A/Bの貼り付け・保存・置換・実行・結果判定が通りました。失敗条件の実機検証、実Copilotを含む通し検証、他PCでの確認は残っています。

仕様: [Issue #5](https://github.com/minimo162/ai-prompts/issues/5)。Robinの元プロンプト: [pad-robin-prompts.md](pad-robin-prompts.md)。

一般仕様の確認先: [PADデザイナーのコピー・保存](https://learn.microsoft.com/en-us/power-automate/desktop-flows/designer-workspace)、[スクリプト実行アクション](https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/scripting)、[Edge DevTools Protocol](https://learn.microsoft.com/en-us/microsoft-edge/devtools/protocol/)。これらは本アプリの実機合格証拠ではありません。
