# Issue #5 検証記録

2026-09-06 / 状態: **partial — 実機ゲート未完了**。

[Issue #5](https://github.com/minimo162/ai-prompts/issues/5) 本文と全コメント（0件）を確認して実装した。ブランチは `codex/issue-5-business-agent`。この記録は成功条件の達成宣言ではない。

## 実装した範囲

配布本体はCMD・App.ps1・index.htmlの3ファイル。ローカル同期、版とハッシュの検査、localhost UI、ジョブ状態、停止、質問と回答、Copilot計画・AiCall、有限Robin検証、専用PADへの差し替え・保存・1回実行、成果物観測を実装した。

初版のRobinはUTF-8テキスト、変数、IF、有限WAIT、固定AiCallに限定する。任意のPC操作、Excel編集、任意のPowerShellコードは未対応。PADのUI操作とM365のDOM操作を含むため、コードがあることと実機で動作が確認できたことを分ける。

## 検証結果

| 検証 | 証拠と範囲 |
|---|---|
| Windows PowerShell 5.1 契約検証 | `tests/Test-App.ps1` **137 PASS**。Copilot/PADを模擬し、要求・結果・観測・再計画・パス境界・同期と実計画/AiCallプロンプトを検査する。実サービスの証拠ではない。 |
| Copilotアダプター | `tests/Test-Copilot.ps1` **154 PASS**。CDP応答を模擬し、全文・ID・終端・生成終了・排他・ジョブ分離・異常分類、起動タブの終了と他タブの保持、送信前busy待機、実送信本文の2行契約と入力・送信の再試行禁止を検査する。本番Robin検証器で受理したReadText/WriteTextフローと約6万文字の長文をJSON復号し、原文との完全一致も確認。隔離Edgeの `tests/Test-CopilotDom.cjs` は **219 PASS**。実M365の翻訳診断では送信1回から厳格な応答取得・再読取り一致まで成功した。固定PADの正常完走とは分けて下記に記録する。 |
| PADアダプター | `tests/Test-Pad.ps1` **302 PASS**。UI/クリップボード境界を模擬し、全文一致・所有権・失敗時の旧フロー実行拒否・結果帰属を検査する。状態別のUI構造、20種類の状態ID、保存・実行・中止、実ファイルに生成した2件のAiCallテンプレートとRobinの検証も本番関数で確認。実機の固定A/Bは下記に分けて記録する。 |
| localhost HTTP | `tests/Test-Http.ps1` PASS。実App.ps1プロセスでHTML/状態、トークン/Host/Origin拒否、不完全本文の期限、再接続、設定保持、重複回答・古い質問への回答拒否、版の引き継ぎ、停止を確認。 |
| 実ブラウザー | `tests/Test-Ui.cjs` 15 PASS。実Edgeの1280×900・390×844で入力→未接続エラー→再表示、トークン除去、同ジョブ再接続、横溢れ・JavaScriptエラーなしを確認。質問ID・Copilotジョブ分離変更を含む不変版 `a00bca7` でも再実行し、両幅のPNGを目視確認した。証跡は `.work/ui-after-question-fix-66edd1690c8a4978aae727d6e5a31807/`。隔離サーバーは専用の終了APIで停止した。 |
| 実際のCMD | リポジトリ上のCMDから実LOCALAPPDATAへ同期し、ローカルApp.ps1のHTTP応答を確認。Chromeにアプリタイトルのウィンドウが現れた。最終統合版も `Bootstrap -NoBrowser` で同期し、実LOCALAPPDATAのサーバー応答と作業コピーのApp.ps1ハッシュ一致を確認した。共有UNCからの検証は下記Gate 0記録に分ける。 |
| ランチャー回帰 | `tests/Test-Launcher.ps1` **18 PASS**。実3ファイルのBootstrapと、隔離したCMDフィクスチャの環境/終了コードを区別して検証する。 |

実CMDで、親のPowerShell 7用モジュール検索パスをWindows PowerShell 5.1が引き継ぎ `Get-FileHash` を解決できない不具合を再現した。CMDの `setlocal` 内でOS標準のPowerShellとモジュールパスに限定して修正した。`-File` ではparam既定値の `$PSScriptRoot` が空になる問題も再現し、param評価後に配布元を補うよう修正した。

初回のComputer Useによる実CMD起動後の画面撮影は、現在のブラウザーURLを十分に判定できないとの理由でツールに停止された。その検証では再試行していない。後続のPAD画面確認と専用Edgeの再起動は下記に別記する。HTTPの確認を画面表示確認へ読み替えない。

## Issueのゲート

| ゲート | 状態 | 残る実機確認 |
|---|---|---|
| 0: 配布・起動 | 実共有UNCからの初回・更新は合格 | 共有切断、利用者環境での再起動・UI停止 |
| 1: 固定PADからAiCall | 第5回PADは終端照合で停止。修正後の単独実Copilot翻訳診断は合格 | 固定PADへの正常な結果受渡し、分類分岐、2回以上の直列、拒否/空/期限/中止 |
| 2: AIなしのA/B差し替え | 正常系A/B合格、異常系は未完了 | 保存・貼り付け失敗などを意図的に起こした場合の旧フロー実行防止 |
| 3: 生成Robin全文取得 | 未検証 | 実M365で長文/日本語/引用符/改行/空白/バックスラッシュ/%、過去回答・途中停止 |
| 4: 生成AiCallフロー | 未検証 | 読取→AI→分岐→書出しを同じPADで完走 |
| 5: 2〜3往復 | 未検証 | 実結果本文に応じた次の手順、ACT/DONE/ASK_USER/BLOCKED、最終表示 |
| 6: 別利用者・別PC | 未検証 | 開発環境に依存しない導入・更新・認証・結果確認 |

2026-09-06に利用者の許可とWindowsの管理者承認を経て、専用共有 `\\localhost\AiPromptsAgentPoC$` を作成した。共有範囲は `.work/shares/AiPromptsAgentPoC` の配布3ファイル、SMB権限は利用者本人の読み取り1件で、NTFS権限・サービス・ファイアウォールは変更していない。最初の承認後試行は共有作成前のファイル名照合で失敗した。作成スクリプトがBOMなしUTF-8だったため、Windows PowerShell 5.1が日本語CMD名を誤読していた。本文を変更せずUTF-8 BOMを付け、旧版の保存と独立した構文・ファイル名照合確認後に成功した。作成・UNC読取の証拠は `.work/gate0/share-create-6a7c02fc14f34586b7c7a5cb32def3c4.json` と `share-verified-6a7c02fc14f34586b7c7a5cb32def3c4.json`。

実共有UNCのCMDを使った初回・更新の結果は `.work/gate0/sessions/ba53e2cf86914d89a514f6c5f7028b66/results/initial.json` と `update.json` に記録した。CMD子プロセスだけのLOCALAPPDATAを隔離し、`49a4535` の初回同期後に共有3ファイルを `160f130` へ更新した。再起動で更新版へ切り替わり、旧キャッシュ3ファイルのハッシュが変わらないことを確認した。各段階の隔離サーバーは所有者を照合して終了し、通常のローカル版のPID・開始時刻・版・Appハッシュは前後一致した。PAD・プロバイダーは呼び出していない。共有は最新の検証済み3ファイルを保持している。

初回・更新の独立再計算は37項目すべて一致した。切断試験の事前レビューでは、検証ハーネスがBootstrapを同じPowerShell内で呼び、未設定または古い `$LASTEXITCODE` を読む問題を修正した。別のWindows PowerShell 5.1子プロセスの終了コードと30秒の上限を使い、合成4ケース・27項目（成功、exit 7、未処理例外、タイムアウト）が通過した。これは検証用スクリプトの修正であり、実共有切断時の成功証拠ではない。

独立レビュー後、専用フォルダーだけを一時改名してUNCを利用不可にする手順を1回試みたが、Windowsの「別のプロセスが使用中」により改名前に拒否された。`results/outage-helper.json` は `status=failed`、`renamed=false`、`harness_invocations=0`、復元・UNCハッシュ確認済みを記録している。共有切断とオフライン起動は未検証のままであり、共有・初回/更新の記録・キャッシュは保持している。同手順は再実行していない。

初期調査ではPAD 2.71.115.26224のインストール済みリソースから、`StartFlowButton`、`SaveFlowButton`、`ProgramItemsListBox` 等の操作要素の候補名を得た。実UIAでの存在・一意性・操作パターンは後続の調査で確認した。初回の新規フロー画面ではComputer Useの名前入力が反映されず、作成を取り消した。その後、利用者の明示的な作成許可を得て、Power Fx無効・自動生成名「無題」の空フローを1つ作成した。`Power Automate | 無題`、Main 1個、アクション0件、準備完了の実画面を確認し、アプリ設定も「無題」に合わせた。業務フローの実行・変更は行っていない。

実画面で得たタイトル形式に合わせ、フロー特定条件を修正した。フロー名だけの形式、既知の旧形式2種類、`Power Automate | フロー名` の4種類をOrdinal完全一致で認める。似た名称や任意の接尾辞は拒否し、`PAD.Designer` プロセス条件と複数一致拒否は維持する。この純粋な判定のテスト成功は、実UIAによるフロー発見成功を証明しない。

固定A/Bのハーネスと入力用Robinを `.work/gate2/` に準備した。構文検査・実Appの許可構文検証まで実施し、PADへの貼り付け・実行は未実施、予定成果物2件とも存在しないことを確認した。メモ帳経由の手動貼り付け準備中に対象と異なる画面が返ったため、古い座標や対象情報で入力を続けていない。手動貼り付けの確認をAppドライバーのGate 2合格へ読み替えない。

後続の実ドライバー検証では、PADの画面と専用Edgeの接続が閉じられていることを確認した。PADコンソールを開き、検索が空の「自分のフロー」を更新しても0件だったため、既に許可された空フロー「無題」をPower Fx無効で1件作成した。名前はUIAのValuePatternで設定して読み戻した。空のMainで保存を要求し、一覧更新後に `MyFlowsListGrid` の「無題」を確認した。前回のデザイナーが永続保存されていたとは扱わない。

`a00bca7` の実 `Invoke-AgentPad` を固定A/Bハーネスから1回呼んだ。Aは `PAD_SELECTOR: control unavailable: StatusTextBlock` で、貼り付け・保存・実行の前に失敗し、Bは開始されなかった。開始/終了マーカー、送信用Robin、予定成果物は作成されていない。証拠は `.work/gate2/sessions/c2687af0aaa2432babb49ae6fce5c9e4/summary.json`。この結果はGate 2合格ではなく、修正すべきセレクターを実機で特定した証拠である。

実UIAで、保存・停止のIDがCustomラッパーで、その直下のButtonだけがInvokePatternを持つことを確認した。空のMainでは実行Buttonは無効、保存Buttonは有効、停止Buttonは無効だった。状態IDは `Flow_status_ready` / `Flow_status_saving_process` / `Flow_status_saved`。空フローの保存を1回だけ要求して50ミリ秒間隔で観測すると、約0.2秒で保存中、約5.3秒で保存済みとなった。証拠は `.work/gate2/save-signal-5eda148ced0947398fd65d7d88bc9a2d.json`。

インストール済みPADのBAML/IL/日本語・英語リソースも読み取り専用で調べた。保存済み表示は5秒間、エラー一覧の件数は警告を含み、実行・デバッグ中には非表示になる。根拠を `.work/pad-save-signals/findings.md` とアセンブリのハッシュに記録した。修正版は状態バーの一意性・正規構造・明示的な待機状態を確認してから、非表示のエラー件数を0と判定する。貼り付け・削除後は、固定時間ではなく中止・期限に対応した状態待ちを行う。修正後の実機診断でも、保存済みの空の「無題」を `available=true / editable=true / can_run=false / status=ready` と確認できた。貼り付けから実行までの再検証は別途必要である。

`e3d9a79` の固定Aでは貼り付けまで進んだが、`ProgramDetailsStatusBarItem` が取得できず保存・実行前に停止した。Bは未開始。証拠は `.work/gate2/sessions/e83d0a2b05d64208971e2bee64dda246/`。終了後のコピー読戻しは提出Robinと比較規則の範囲で完全一致し、開始/終了マーカー・成果物は0件だった。インストール済み処理の追跡で、コード一覧の貼り付けが `Updating` を設定し、その状態と保存中には同項目を非表示にすることが分かった（`.work/pad-save-signals/paste-status-followup.md`）。失敗瞬間の状態IDは記録されていないため、その瞬間の因果関係までは断定しない。

追加修正は、状態読取りに常設の状態欄を使い、非表示エラーを0と判断するReady/Saved時にだけProgram Detailsを要求する。状態待ちの既知セレクター欠落は期限内で再観測し、安定判定をリセットする。要素の重複や型・名前・操作パターンの不一致は即時に失敗とする。保存・貼り付け・実行の再送は行わない。

失敗Aの復旧では、セッション・run・提出コードとコピー証拠のハッシュを固定し、現在のコードとの一致と開始/終了マーカー・成果物の不在を再確認した。独立レビュー後、当該コードだけを1回削除し、専用Mainが空・待機状態へ戻ったことを確認した。保存・実行は要求していない。記録は同セッションの `reset-failed-paste.json`。元の失敗証拠は保持している。

`9893e49` の新規固定Aは、貼り付け・保存・実行まで進んだが、実行後の監視が `StartFlowButton` 不在で `unknown` となり、Bは開始されなかった。セッションは `.work/gate2/sessions/f696933d6baa419eb1471f609f80cc8e/`。再実行せずに読み取り専用で照合したところ、現在のPADがエラー0の待機状態、コードと所有記録の一致、開始/終了IDの一致、唯一の出力本文の完全一致という9項目を確認した。結果は `reconcile-0f27b78568ea473f872d9c48a72214dc/observation.json` に別記し、元の `unknown` を書き換えていない。これは固定Aの実処理が完了した証拠であり、アプリの自動結果判定やA/B一連の合格ではない。

インストール済みPADのBAML/ILから、実行中はStartを隠し、一時停止中のStartは既存実行を再開することを確認した（`.work/pad-save-signals/running-controls-followup.md`）。修正版では、実行状態と実際のStopが有効な場合にだけStart不在を許し、新規Runへは使わない。観測要素の欠落が続く場合は通常の実行期限と別に20秒で不明とし、中止要求を毎回確認する。停止は専用ウィンドウからその場で厳密に解決したStopを1回だけ要求する。

事後確認済みの固定Aは、独立レビューした手順で本文・所有記録・成果物ハッシュを再確認後に1回だけ削除した。Mainが空に戻り、成果物と開始/終了マーカーが変更されていないことを確認した（同セッションの `clear-verified-a.json`）。保存・再実行は要求していない。

`7a63f52` の固定Aも実出力まで進んだが、時間付き状態名を拒否して `unknown` となり、Bは未開始だった（セッション `8edd72c431254e3b9b10d6cb9839afed`）。別プロセスの読み取り専用ログは保存中→保存済み→解析中→実行中→準備完了を記録し、事後照合9項目はすべて一致した。元の不明判定は保持した。PADの状態名は実行時間が付くと `状態 {0} {1:N0} 秒` になるため、コロン付き表示名を一律必須にする判定を修正した。状態の識別には既知の20種類のID・一意な状態欄・Text型を用い、表示名は診断情報として保持する。

`49a4535`（App SHA-256 `6e30788593980f236807053a8177f7519c4cead2f3308f7a63e5bea8b5958844`）の固定A/Bは、実Appドライバーで両方成功した。セッション `.work/gate2/sessions/9bd4da3132e94ca78d6d63a559472220/` のAは8項目、Bは9項目の検査がすべて一致した。開始/終了ID、唯一の成果物、UTF-8本文、保存した所有記録を確認し、B後もAの出力ハッシュは変わらなかった。別プロセスの `.work/gate2/observers/b2114577ff9040a4b5712b022a0e77ec/` でも、両方の保存中→保存済み→解析中→実行中→準備完了を記録した。独立レビューは保存ファイルから全17項目を再計算して一致を確認した。以前の failed/unknown の記録は変更していない。

Gate 1の固定2回AiCallの準備中に、Windows PowerShell 5.1のJSON配列読取りが1個のObject配列となり、2件のテンプレートを正しく参照できない不具合を再現した。明示的な配列展開と6フィールド・IDの検証を共通化し、実ファイルの2件を本番生成関数→読取り→Robin検証へ通す回帰検証を追加した。`.work/gate1/` のハーネスは準備段階で、実プロバイダー呼出しは別の検証である。

Gate 1の実PAD貼り付け読戻し（`.work/gate1/sessions/7d2274ce4c8d47b6883a330f46eb5434/capture-be92b773d8294dafa32109816b0c6084/`）では、提出本文との差分が4つの同一エラーハンドラーだけだった。PADは各結果/status読取と同じインデントに `ON ERROR` / `END` を置き、本文だけを4スペース深く保持したため、生成規則と厳格バリデーターをその実観測形へ合わせた。`AgentAiReadFailed` への `ERROR` 設定、`THROW ERROR`、結果→statusの直後読取順、全文貼り付け比較は維持している。捕捉時は保存・実行0回、状態ready、エラー0、開始/終了マーカーと成果物なしであり、これは貼り付け失敗の診断であってGate 1合格ではない。

`9c6f49f` のGate 1再試行は `.work/gate1/sessions/a774f4aa434d447eacaf1ac42db4a285/summary.json` に保存した。保存・実行開始までは進んだが、最初の状態観測は `PAD_SUBFLOW: exactly one Main subflow is required.` で `status=unknown`、`accepted=false` のまま保持している。同じセッションの読み取り専用事後観測 `.work/gate1/sessions/a774f4aa434d447eacaf1ac42db4a285/posthoc-runtime-error.json` は、`Flow_status_runtime_error`、`Main, エラーあり,`、2行目 `DirectoryNotFound`（`control/started.txt`）を記録した。開始マーカー・終了マーカー・AiCall結果・成果物はいずれも0で、プロバイダー送信確認もない。これは保存→実行開始の進展と別の実行時エラー証拠であり、Gate 1成功や元の `unknown` の書換えを意味しない。

実行時エラーに限り、装飾されたMainタブ名と実機で確認した直下2要素の構造を厳密に照合する修正を加えた。修正版の読み取り専用実機確認は `posthoc-error-identity-fix.json` に記録し、`runtime_error`・エラー1件・`idle=false`・`can_run=false` を確認した。保存・実行は追加していない。125件の基本契約・119件のCopilot契約・281件のPAD契約検証が通過し、独立レビューもBLOCKER 0 / MUST FIX 0。保存先エラーは未解決であり、この修正は実行時エラーの検出改善に限る。

失敗した第2回Gate 1のフローは、提出本文・実PADからの全文読戻し・run/jobファイル・所有記録を照合した後、1回の削除・保存で空Mainへ戻した。過去の `unknown` と証拠は保持した（`sessions/a774f4aa434d447eacaf1ac42db4a285/clear-second-runtime-error.json`）。続く固定ファイル診断 `path-probes/aa72021029f64ee9b5be32fd0faeca0b` では、同じPAD実行のworkspace書込みが成功し、AppDataの書込みだけが3行目で失敗した。書込み前後とも作成元からは対象フォルダーが存在していた。

環境診断 `environment-probes/866fcb958b964966b7990dd3c17a73db` では、PADの既知フォルダー、子PowerShellの環境変数と既知フォルダーが同じAppDataを返す一方、子からは直下のAiPromptsAgent・キャッシュApp・要求ファイルが見えなかった。実行中のRobotV2と子PowerShellは同一ユーザー・同一セッションと確認した。作成元で既存ディレクトリのハンドルを解決すると、実体はCodexの `Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/AiPromptsAgent` にあった（`host-view-50e2d69420094d0abe688449a9860207/observation.json`）。現物Codex manifestの新しい仮想化宣言はLocalAppData/OpenAIだけを除外し、Windows 11ではこの宣言が旧disabled指定に優先する。[Microsoftの仕様](https://learn.microsoft.com/en-us/windows/msix/desktop/flexible-virtualization)。今回の保存先不一致は検証を起動したCodex環境に由来し、製品の既定保存先やPADの権限設定は変更しない。上記のLOCALAPPDATA検証もこの実体に対する証拠であり、通常ユーザー起動の非仮想化領域を検証したことにはしない。

環境診断の3出力と終了GUIDは生成されたが、終了観測で状態表示と停止ボタンの有効状態が一致せず、元の結果は `unknown` のまま保持した。事後観測 `posthoc-d9c4b4291c8a45a985cb775211235751` で同じフロー全文・ready・待機中・エラー0を確認した。この正確な観測不一致だけを期限内の読取り直し対象へ追加し、状態判定・操作の再送条件は変えていない。一時不一致からの復帰、持続時の期限切れ、類似文言と型違いの拒否を含むPAD契約検証は301 PASS、独立レビューもBLOCKER 0 / MUST FIX 0。実AiCall・M365送信はこの診断に含まない。
実体パスを明示した診断 `physical-probes/437c276f2d65452db102fa9c9308137d/result.json` は7アクションで成功した。PADが書いたGUIDを同じPADと子PowerShellで読み戻し、子が既存の不変Appライブラリ（b14062cf…）をハッシュ照合して読み込み、従来は見えなかった要求ファイルの存在を確認した。controllerはf0d5791、削除・貼付け・保存・実行は各1回、終了はready・エラー0、provider呼出し0。旧環境診断の12ファイルとApp所有記録は変わっていない。これは保存先の解消を示す固定診断であり、AiCallの成功証拠ではない。

同じ実体HomeでJSON更新を試すと、対象229文字・一時ファイル256文字は作成できても、265文字のバックアップを伴うFile.Replaceが失敗した。バックアップを同じ親の独立GUID名へ短縮すると257文字となり、更新と旧内容の保存が成功したため、本体のWrite-AgentJsonもこの命名へ変更した。原子的な置換と成功・失敗時の一時ファイル清掃は維持する。Windows PowerShell 5.1で長い保存先の作成・更新・ロック時の旧JSON保持を含む133項目が通過し、独立レビューもBLOCKER 0 / MUST FIX 0。実体Homeでの本体再検証も成功した（`physical-home-json-a162063d41084633b839c021e4254f11.json`）。この再検証記録のbackup_length欄だけは検証スクリプトの旧式計算が残ったため、元記録を保持して別の `.metadata-correction.json` に257文字と訂正し、検証スクリプトの計算も修正した。

アプリの正式な `/api/copilot/open` から専用Edgeを起動できた。初回の同期確認は利用者の操作対象とし、自動応答していない。その後、専用ポートと専用プロファイルのプロセスが終了したことを読み取り専用で確認した。利用者から「もう一度m365 copilotを開いて」と依頼され、同じ機能から再度開いた。M365への業務プロンプト送信、認証完了、応答取得は未検証。

再起動時に余分な `about:blank` が残るとの報告を受け、明示的な空タブ起動と別のCopilotタブ作成が原因だとソースで確認した。今後の初回起動では空タブに一意の値を付け、Copilotまたは認証タブの表示後、その値・対象ID・専用プロファイル・接続先を確認して当該タブだけを閉じる。変更済み・曖昧・終了確認不能の場合は追加操作しない。既に開いている普通の空タブや拡張機能のタブは閉じない。修正の実ブラウザー検証は未実施。

専用EdgeのChatGPT拡張機能を読み取り専用で調査した。バージョン `1.26.901.11451`、無効化理由 `[1024]` を確認した。この値は[Chromiumの定義](https://github.com/chromium/chromium/blob/main/extensions/browser/disable_reason.h)では `DISABLE_CORRUPTED` に対応する。拡張機能の `background.js` に、初回インストール時に機能フラグが有効なら `/work/extension/installed` を開く処理も存在した。案内タブが開く仕組みと破損判定の発生原因は分けて扱う。拡張機能・認証・同期・ブラウザーのセキュリティ設定は変更していない。

拡張機能の検証対象1,629ファイルは欠損がなく、4,096バイト単位のSHA-256とメタデータ内のツリールートがすべて一致した。別のmanifestとアイコン4件は[Chromiumがインストール時変換のため検証から除外する対象](https://chromium.googlesource.com/chromium/src/%2B/lkgr/extensions/browser/content_verifier/content_verifier.cc)に一致する。署名そのものは未検証であり、破損判定の発生時点・原因・復旧は確認できていない。限定した診断記録は `.work/chatgpt-extension-integrity-20260905.md` に残した。

空タブとPADタイトルの修正版を `Bootstrap -NoBrowser` で実LOCALAPPDATAへ同期し、HTTP成功、App.ps1のハッシュ一致、フロー設定「無題」、実行中ジョブなしを確認した。同期は専用Edgeの起動・終了やタブ操作を要求しない。

固定A/B成功版もLOCALAPPDATAへ同期した。そのアプリからM365を開いたところ、Copilotのタブは開き入力欄もREADYだったが、起動時に渡した一意な `about:blank#...` はCDP一覧になく、別の `edge://newtab/` があった。専用Edgeのプロセス引数には識別子が届いていた。未確認の新規タブを閉じる操作はしていない。この場合は、確認済みのCopilotタブが開いていることを成功とし、起動タブの後処理は警告として返すよう追加修正した。重複・変更・不明な所有のタブを閉じる許可には使わない。

固定ファイル診断の成功後、同じ7アクションの全文を2回照合し、1回の削除・保存で空Mainへ戻した（`physical-probes/437c276f2d65452db102fa9c9308137d/cleanup-once/result.json`）。終了は保存済み・エラー0・実行不可であり、実行要求0、診断・旧Gate 1・所有記録は保持した。

専用Edgeの入力欄を本文を保存せずに調べると、空のSPAN/P/BR構造からinnerTextだけがLFを1文字返していた。この厳密な空構造だけを空文字に正規化し、実際の空白・改行・不可視文字・未知の入力構造は保持する。実装したDOMコードを隔離Edgeで評価する51項目と既存Copilot契約119項目が通過し、独立レビューも通過した。7ページ遷移はすべてローカルfixtureで応答し、実サービスへ転送していない。実M365でも修正版を読み取りだけで確認し、入力候補1件・正規化後0文字・生成中でないことを確認した（`copilot-empty-editor-verified-6ab9ff6113284410bce44473212ebed6.json`）。入力の消去、送信、タブの再起動は行っていない。

Windows起動経路の読み取り専用診断では、単なるShell.Application呼出しはCodex側のpwshを親に持ち、同じ仮想化領域を見た。デスクトップExplorerのautomation objectを介した呼出しはexplorer.exeを親に持ち、PADと同様に通常領域のAiPromptsAgentを未作成と判定した（`launch-context-probes/3cb3c628a97a40b5ab5b1b6d34614f0d.json`）。AppData作成・PAD実行・provider送信は0。この経路での導入や固定AiCallは未実施である。[MicrosoftのExplorer起動資料](https://devblogs.microsoft.com/oldnewthing/20131118-00/?p=2643)

修正済みの `16c0761` の3ファイルを専用共有へ公開した。App.ps1を1回の原子的な置換で更新し、旧3ファイルを別のバックアップに保持した。ローカル共有とUNCの新ハッシュ、バックアップの旧ハッシュ、共有権限とNTFS ACLの不変を確認した（`gate0/publish-latest/33b62f2a328c414b884b295055572a4d/result.json`）。

Desktop Explorer経由で共有CMDを1回起動した結果、終了コード0で通常のLOCALAPPDATAへ新キャッシュとサーバーが作成された（`gate0/normal-context/4c894cdeaf154913a8d8682db29b4f5e/result.json`）。通常Homeの最終実体パスも一致したが、後続のキャッシュ・サーバー検証は失敗として保存した。起動引数には期待文字列がすべて含まれ、末尾の空白1文字を除いた場合だけ末尾比較が一致した。元の失敗記録を書き換えず、既に起動したサーバーを読み取り専用で確認する。

同じ切替の旧履歴検証は、Codex側の結合されたフォルダー表示に新キャッシュ3ファイルが加わったため全体ダイジェストが不一致となった。元の45ファイルを仮想化領域の明示した実体パスと従来の表記の両方で再計算すると、45件すべてのハッシュが一致した（`gate0/normal-switch/4c894cdeaf154913a8d8682db29b4f5e/posthoc-private-history-74f96136e82f44a393f94b5bdfd62809.json`）。元の切替結果は `unknown` のまま保持し、導入を再実行していない。

通常Explorer環境からの事後確認では、元のキャッシュ検査は成功し、起動引数の末尾比較だけで同じ失敗を再現した。Windowsの引数解析では12個すべてが期待値と一致した。通常Homeの実体、新キャッシュ3ファイル、current.json、PS5サーバーのPID・開始時刻・localhost待受所有者、HTTP 200・版0.1.0・jobなしを確認した（`normal-context/4c894cdeaf154913a8d8682db29b4f5e/posthoc/913dbf5462d34bdfb597a542269c4df1/result.json`）。この確認は読み取りだけで、導入や設定変更を再実行していない。復旧側の例外も、StrictMode下で空の関数出力へ `.Count` を参照した検証スクリプトの不具合と特定した。新サーバーが稼働しているため旧サーバーの復旧起動は不要である。

設定引継ぎは別の1回のPOSTで成功した。通常HomeのAPI・設定ファイルが `copilot_port=9223`、`pad_flow_name=無題`、`max_rounds=6` で一致し、jobなし、source・cache・旧設定が不変だった（`settings-recovery/9d1af217e38b4b1b82fc6d751b2893e4/result.json`）。旧45ファイルも再び全件一致した。

第3回の固定AiCall実機検証は、通常Explorer環境と新キャッシュから1回実行した（`gate1/sessions/e696488ae08f43e094ce27f8aadcd795/summary.json`）。今回はPADの開始マーカー、最初のAiCall claimと結果ファイルまで進み、PADと子PowerShellが同じ保存先を利用できた。翻訳AiCallは `failed / connection / input_count=1 / output_count=0`、分類は未実行だった。ジョブ専用Copilotタブは作成されたが `has_sent=false` で送信試行記録はなく、業務プロンプト送信は確認していない。PAD観測は `PAD_SUBFLOW` により `unknown` のまま保存し、通常サーバーは復旧した。

第3回の事後UIA確認では、既存の厳密条件で `Main, エラーあり,` を取得でき、Main 5行目・エラー1件・停止中・17アクションを確認した。元の11 runファイルとjob・summaryは不変だった。Copilotの事後確認も接続・空の入力欄・会話なし・生成なしで成功した（`copilot-posthoc-2d0485b26fdc4e43b1c89a7e84508726.json`）。元の接続失敗の箇所は未特定で、初期タブの表示遷移を区別する診断が必要である。いずれも事後確認を元の失敗結果の置換や再送には使っていない。

新しい診断用タブを1件だけ作成し、実関数の作成→接続→最初のsnapshotを計測した。この試行の初回接続は成功したが、入力・送信0回のまま、後続snapshotで `generating=false→true→false` と変化した（`gate1/copilot-startup-probes/9c04fc30773e4288960e4425ae8fbfe1/result.json`）。その間も入力0文字・assistant 0件で、生成中と判定された時点のdocumentはinteractiveだった。これは初期表示中の判定変化の証拠であり、元のAiCall接続失敗の原因確定ではない。既存3タブと16ファイルの不変を確認し、診断タブも未送信のまま保持した。

第3回フローの最初の復旧は、PADの前面化を確認できず、削除・保存前に停止した（同セッションの `cleanup-once/result.json`）。標準UI AutomationのWindow.SetFocusで対象を前面化できることを確認し、その後も既存の前面・workspace確認を通す手順を独立レビューした。別の1回の復旧は、本文2回の一致確認後に削除1回・保存1回で成功した（`cleanup-after-focus-4acf38684dc64e6bb656bd94d0a9a1d9/result.json`）。終了は保存済み・空Main・エラー0・実行不可で、実行要求0。現行19ファイル・旧45ファイル・前回復旧5ファイルと所有記録を保持した。

次の診断用タブでは16回のsnapshot内で、productionの生成判定と同じ評価から原因要素を記録した（`gate1/copilot-busy-probes/17f3341dbb64416883a37b0b3960c807/result.json`）。入力・送信0回、空欄・assistant 0件のまま、1回だけ可視の `DIV[role=status][aria-busy=true]` が現れた。停止ボタンとstreaming属性はなく、約0.5秒後には消えた。documentがcompleteでもこの一時状態が発生することを確認した。旧20ファイル・既存4タブを保持し、新しい診断タブは未送信のまま残した。これは読み込み中の生成判定を再現した証拠であり、元のAiCall失敗瞬間の原因を断定するものではない。

送信前のfocus確認に15秒の共有期限を設け、生成判定中だけ入力せず再観測するよう修正した。snapshot後にbusyへ変わった場合も待機し、接続・focus失敗、入力消失、所有権喪失、初回ジョブの下書きや会話の出現は停止する。生成判定、全体期限・中止、4キー・本文挿入・送信を各1回に限定する規則は維持した。従来の入力欄出現待ち15秒は別に保持する。PADはnative前面化が成功しなかった場合だけWindow.SetFocusを1回試し、既存の前面・workspace確認を必須にした。基本契約133件、Copilot契約147件、PAD契約302件と隔離Edge DOM64件が通過した。DOM検証の7ページ遷移はすべてローカル応答で、実サービスへ転送していない。

修正版 `2b8207a`（App SHA-256 `858ba1de5a36392f3656b3ed0f9c56d7a6ce2f5bac16b5a97c8b2640cc267041`）は独立レビューを通過した。専用共有を1回のApp置換でrelease `0.1.0-b539c6916b80aefe7493e85b3e748b8cb9e2509be5447b124e37e80c04db0025`へ更新し、旧3ファイル・ACLを保持した（`gate0/publish-latest/2ff3f86f239945beb39352414d65aa1e/result.json`）。

通常Explorerから実共有CMDを1回起動した更新検証も成功した（`gate0/normal-updates/e1f56d5f17cb43b889700a456ce95bb8/result.json`）。CMD終了コード0、新しい通常Homeのキャッシュとcurrent.json、PS5サーバーのPID・開始時刻・Windowsで解析した起動引数・localhost待受所有者・HTTP応答・設定を照合し、旧サーバーの終了を確認した。現行ジョブ15ファイル・所有記録・設定・旧キャッシュ3ファイルの計20件と、Codex仮想化領域の45件は不変だった。helperから直接のPAD操作・Copilot送信・再起動API要求は行わず、更新と旧サーバー終了は製品の起動処理が行った。

第4回の固定AiCallは通常環境で新規IDを作り1回実行した（`gate1/sessions/ba98d1a912f74425b3700229699e8888/summary.json`）。最初の翻訳AiCallは再び `failed / connection` だったが、今回は製品のPAD監視が `failed / AICALL_connection` と検出した。分類・成果物出力は未実行で、通常サーバーは復旧した。外側の検証結果は `unknown / accepted=false` として元のまま保持する。実行前に旧所有記録を別ファイルへ保存し、終了時も旧normal 19ファイル・private 45ファイル・旧所有記録バックアップ・既存5タブの保持を確認した（`gate1/normal-executions/5afea4b151a049f6914b45e402de60ed/result.json`）。

第4回の事後確認では、ジョブ専用Copilotタブの入力が1273文字で、入力候補1件・送信ボタン有効・生成なし・assistant 0件だった（同セッションの `copilot-posthoc-5ae1512f82a443a289740a20201d8fc0.json`）。入力先にもfocusがあり、空の入力欄から本文入力まで進んだことを確認した。ただし `has_sent=false` であり、送信は確認していない。PADはMain 5行目の実行時エラー1件・17アクション・実行不可だった（`cleanup-once/uia-observation.json`）。いずれも読み取りのみで再送・再実行していない。

元のrequest・inputと製品内のAST代入式から送信予定本文を副作用なく再構成すると、期待した1271文字が実入力の先頭から完全一致し、改行3箇所も一致した。差分は末尾のU+200B・U+200C各1文字だけだった（`input-comparison-ca78585136e6447c8d774a585a5062c1.json`）。DOMはSPAN→P→2つのSPANで、最初のSPANは `data-lexical-text=true` の本文1271文字、後ろのSPANだけは `data-lexical-text=true / aria-hidden=true` で唯一のテキストノードが当該2文字だった（`input-suffix-2a80573875d14d729df7f4873e3924e2.json`）。この構造が現在の完全一致検査を不成立にすることを確認した。失敗瞬間の例外自体は保存されていない。旧19ファイルの不変と入力・focus・送信0回を確認した。実測した本文SPANと末尾のaria-hidden SPANだけを厳密に識別し、末尾マーカーだけを比較対象から除く修正を加えた。本文中の不可視文字・改行・空白、属性違い・未知の構造は保持する。Copilot契約147件、隔離Edge DOM99件が通過し、独立レビューも通過した。実M365の同じ未送信入力を修正版で読み取るだけの検証でも1273文字から1271文字となり、送信予定本文のSHA-256と完全一致した（`draft-input-verification-7c8e857e5b03473e8a77b47c57226b0c.json`）。この確認で入力・focus・送信・タブ操作は行っていない。

第4回の失敗フローも、独立レビュー後に全文2回の照合と1回の削除・保存で空Mainへ戻した（`sessions/ba98d1a912f74425b3700229699e8888/cleanup-once/result.json`）。終了は保存済み・エラー0・実行不可で、実行・provider呼出し0回。第4回の19ファイル、旧normal 19ファイル、private 45ファイルと旧所有記録バックアップは不変だった。

末尾マーカー修正版 `928b2f6`（App SHA-256 `b738672013e90ddf5de886dba7605bf0c72a0cb8ad419e047669f48307676919`）をrelease `0.1.0-5c4ef7d98162d2c5bbe28ef50f6ba6b9d7c12190f00e931fbcba8a05a88f3adb`として専用共有へ公開した。原子的なApp置換1回、旧3ファイルのバックアップとACL保持を確認した（`gate0/publish-latest/2fed9d4c4cd349c6b1a1a9c62b1d5392/result.json`）。通常Explorerからの共有CMD更新も終了コード0で成功し、新キャッシュ・サーバー・設定・引数・HTTP応答の一致、旧サーバー終了、現行20ファイル・旧normal19・private45・旧owner archive・第4cleanup証拠の不変を確認した（`gate0/normal-updates/3d66440be9c9409e860bcebbba604b63/result.json`）。

第5回の固定AiCallは新規ジョブで1回実行し、今回は本文の完全一致、送信クリックの応答、英訳回答まで進んだ（`gate1/sessions/501899397d424602a8e399e5e53f95ff/summary.json`）。最初のAiCallは `failed / invalid_response`、PADの監視も `failed / AICALL_invalid_response` で停止し、分類と成果物出力は未実行だった。通常サーバーは復旧し、外側 `normal-executions/32286c2453214a53b09ab57e06411cb4/result.json` のunknownは元のまま保持した。旧normal19＋19、private45、旧owner archive、既存6タブは不変。今回の旧ownerは別ファイルへバックアップした。事後snapshotでは入力0文字・assistant1件・生成なしで、正しいID群と英訳を含むsuccess JSONがあったが、取得した本文に必須の `AGENT_END_<request_id>` がなかった（`copilot-posthoc-dc2bdcdb615247e8b28b2d4207f3fed4.json`）。追加の読み取り専用DOM確認では、assistant候補は `markdown-reply` の1件だけで、`lastChatMessage` を含む4段階の祖先とその直下要素もすべて同じ330文字だった（`copilot-posthoc-5b22513e45434989a890343233466b3d.json`）。この回答では取得範囲の切り捨てではなく、表示された応答自体に終端がない。「JSONだけ」と「次行に終端」の指示を必須2行形式に統一する修正を別draftで準備し、終端なしの受理や事後補完は行わない。

第5回の失敗フローも、独立レビューと本文2回の照合後、削除1回・保存1回で空Mainへ戻った（`sessions/501899397d424602a8e399e5e53f95ff/cleanup-once/result.json`）。保存済み・エラー0・実行不可、Run/provider呼出し0回。今回の20ファイル（送信済みattemptを含む）、旧normal19＋19、private45と両owner archiveは不変だった。

2行指示のdraftだけを用いた新規の翻訳診断は、実Copilot呼出し1回・再送0回・PAD操作0回で実行した（`gate1/two-line-response-probes/a786d45c23824b50957b17a9b1de7909/result.json`）。今回の回答には正しいJSONと終端があったが、本文取得値では改行が空白となり、厳格な終端照合が通らず `unknown` となった。旧112ファイルと既存タブは不変だった。読み取り専用の追加観測では、可視の `DIV[data-testid=markdown-reply] → DIV → P → 単一テキストノード` にJSON・LF・終端がそのまま存在し、`innerText` だけがLFを空白へ変換していた（`copilot-posthoc-f6b8aae1381442ecbbf58fe93f5e21ae.json`）。元のunknownは保持し、応答の補完や終端規則の緩和はせず、取得処理の修正を別draftで検証する。

指示を2行形式へ統一し、実測した可視の単一テキストノード構造だけから原文を取得する修正を実装した。未知の構造は従来の取得方法を保持し、終端や改行の補完は行わない。修正前の取得では拒否される同じ実応答を、修正版では2回とも元テキストと完全一致で取得し、既存の厳格なJSON/終端/ID検証を通過した（`copilot-two-line-draft/7f539df426734827adc35e3042d25411/readonly-reader-1b7075adb66c4591bef244426855cdf1.json`）。基本137・Copilot154・隔離Edge DOM219件が通過し、独立レビューも通過した。DOMテスト初回のflexによる表示形式変換のfixture誤設定と、その修正も `dom-validation.json` に記録した。

新しい要求IDによる翻訳診断 `bc551ffcb5844e5182e607d3cd022a10` は、通常Explorer環境で実Copilot呼出し1回から正常に返却された。JSONと実LFと終端を含む厳密な2行、要求/ジョブ/run/AiCall ID、success・入出力各1件、取得JSONと再読取り2回の完全一致がすべて合格した（`gate1/two-line-response-probes/bc551ffcb5844e5182e607d3cd022a10/result.json`）。実行は2026-09-05 20:24:38〜20:25:14 UTC、既存115ファイル・既存8タブ・通常サーバーは保持され、再送/再試行/PAD操作は0回。過去のunknownは変更していない。適用したApp SHA-256は `32958784b503b9316c5b61d68bc1008f879f527242033e95263e7c1e15d97b00`。この診断はCopilotアダプターの実経路の証拠であり、Gate 1の固定PAD完走ではない。

Gate 0の切断、Gate 1/2の異常系、Gate 3〜6の実機確認も残っている。

## 再現コマンド

リポジトリのルートで実行する。アプリ配布にテスト用ランタイムを含めない。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-App.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Copilot.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Pad.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Http.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\Test-Launcher.ps1
```

UIテストは開発用PlaywrightとEdgeを使う。Copilotへ接続していない隔離Homeを指定する。`PLAYWRIGHT_MODULE` にPlaywrightの解決先を設定し、そのHomeで `App.ps1 -Mode Serve -NoBrowser -HomePath <絶対パス>` を起動してから `node tests/Test-Ui.cjs <同じHome>` を実行する。

GitHub Actionsは未設定・未実行。PR作成・マージ・Issueの完了更新は行っていない。

PAD操作の追加修正は独立コードレビューで BLOCKER 0 / MUST FIX 0。固定A/Bの実機検証に進めるとの判断であり、Issue全体の完了・マージ可能性を示すものではない。実機ゲート不足は未解決のまま保持する。
