# Issue #5 検証記録

2026-09-05 / 状態: **partial — 実機ゲート未完了**。

[Issue #5](https://github.com/minimo162/ai-prompts/issues/5) 本文と全コメント（0件）を確認して実装した。ブランチは `codex/issue-5-business-agent`。この記録は成功条件の達成宣言ではない。

## 実装した範囲

配布本体はCMD・App.ps1・index.htmlの3ファイル。ローカル同期、版とハッシュの検査、localhost UI、ジョブ状態、停止、質問と回答、Copilot計画・AiCall、有限Robin検証、専用PADへの差し替え・保存・1回実行、成果物観測を実装した。

初版のRobinはUTF-8テキスト、変数、IF、有限WAIT、固定AiCallに限定する。任意のPC操作、Excel編集、任意のPowerShellコードは未対応。PADのUI操作とM365のDOM操作を含むため、コードがあることと実機で動作が確認できたことを分ける。

## 検証結果

| 検証 | 証拠と範囲 |
|---|---|
| Windows PowerShell 5.1 契約検証 | `tests/Test-App.ps1` **125 PASS**。Copilot/PADを模擬し、要求・結果・観測・再計画・パス境界・同期を検査する。実サービスの証拠ではない。 |
| Copilotアダプター | `tests/Test-Copilot.ps1` **108 PASS**。CDP応答を模擬し、全文・ID・終端・生成終了・排他・ジョブ分離・異常分類、実際の起動関数の呼出順、今回だけの起動タブの終了と他タブの保持を検査する。M365での送信と起動タブ修正後の実ブラウザー確認は未実施。 |
| PADアダプター | `tests/Test-Pad.ps1` **175 PASS**。UI/クリップボード境界を模擬し、全文一致・所有権・失敗時の旧フロー実行拒否・結果帰属を検査する。実機で観測したタイトル形式の厳密一致検証を含む。実PAD貼り付けではない。 |
| localhost HTTP | `tests/Test-Http.ps1` PASS。実App.ps1プロセスでHTML/状態、トークン/Host/Origin拒否、不完全本文の期限、再接続、設定保持、重複回答・古い質問への回答拒否、版の引き継ぎ、停止を確認。 |
| 実ブラウザー | `tests/Test-Ui.cjs` 15 PASS。実Edgeの1280×900・390×844で入力→未接続エラー→再表示、トークン除去、同ジョブ再接続、横溢れ・JavaScriptエラーなしを確認。後の質問ID変更・Copilotジョブ分離変更後の再実行は未実施。 |
| 実際のCMD | リポジトリ上のCMDから実LOCALAPPDATAへ同期し、ローカルApp.ps1のHTTP応答を確認。Chromeにアプリタイトルのウィンドウが現れた。最終統合版も `Bootstrap -NoBrowser` で同期し、実LOCALAPPDATAのサーバー応答と作業コピーのApp.ps1ハッシュ一致を確認した。共有UNC起動ではない。 |
| ランチャー回帰 | `tests/Test-Launcher.ps1` **18 PASS**。実3ファイルのBootstrapと、隔離したCMDフィクスチャの環境/終了コードを区別して検証する。 |

実CMDで、親のPowerShell 7用モジュール検索パスをWindows PowerShell 5.1が引き継ぎ `Get-FileHash` を解決できない不具合を再現した。CMDの `setlocal` 内でOS標準のPowerShellとモジュールパスに限定して修正した。`-File` ではparam既定値の `$PSScriptRoot` が空になる問題も再現し、param評価後に配布元を補うよう修正した。

初回のComputer Useによる実CMD起動後の画面撮影は、現在のブラウザーURLを十分に判定できないとの理由でツールに停止された。その検証では再試行していない。後続のPAD画面確認と専用Edgeの再起動は下記に別記する。HTTPの確認を画面表示確認へ読み替えない。

## Issueのゲート

| ゲート | 状態 | 残る実機確認 |
|---|---|---|
| 0: 配布・起動 | 部分確認 | 実共有UNCからの初回・更新、共有切断、利用者環境での再起動・UI停止 |
| 1: 固定PADからAiCall | 未検証 | 実M365翻訳、分類分岐、2回以上の直列、拒否/空/期限/中止 |
| 2: AIなしのA/B差し替え | 未検証 | 実デザイナーで貼り付け・保存・実行・開始終了観測、失敗で旧フローを走らせない |
| 3: 生成Robin全文取得 | 未検証 | 実M365で長文/日本語/引用符/改行/空白/バックスラッシュ/%、過去回答・途中停止 |
| 4: 生成AiCallフロー | 未検証 | 読取→AI→分岐→書出しを同じPADで完走 |
| 5: 2〜3往復 | 未検証 | 実結果本文に応じた次の手順、ACT/DONE/ASK_USER/BLOCKED、最終表示 |
| 6: 別利用者・別PC | 未検証 | 開発環境に依存しない導入・更新・認証・結果確認 |

PAD 2.71.115.26224のインストール済みリソースを確認し、操作要素の候補名を得た。候補は `StartFlowButton`、`SaveFlowButton`、`ProgramItemsListBox` 等だが、リソース上の名前が実UIAのAutomationIdとして存在すること、一意性、操作パターンは未確認。初回の新規フロー画面ではComputer Useの名前入力が反映されず、作成を取り消した。その後、利用者の明示的な作成許可を得て、Power Fx無効・自動生成名「無題」の空フローを1つ作成した。`Power Automate | 無題`、Main 1個、アクション0件、準備完了の実画面を確認し、アプリ設定も「無題」に合わせた。業務フローの実行・変更は行っていない。

実画面で得たタイトル形式に合わせ、フロー特定条件を修正した。フロー名だけの形式、既知の旧形式2種類、`Power Automate | フロー名` の4種類をOrdinal完全一致で認める。似た名称や任意の接尾辞は拒否し、`PAD.Designer` プロセス条件と複数一致拒否は維持する。この純粋な判定のテスト成功は、実UIAによるフロー発見成功を証明しない。

固定A/Bのハーネスと入力用Robinを `.work/gate2/` に準備した。構文検査・実Appの許可構文検証まで実施し、PADへの貼り付け・実行は未実施、予定成果物2件とも存在しないことを確認した。メモ帳経由の手動貼り付け準備中に対象と異なる画面が返ったため、古い座標や対象情報で入力を続けていない。手動貼り付けの確認をAppドライバーのGate 2合格へ読み替えない。

アプリの正式な `/api/copilot/open` から専用Edgeを起動できた。初回の同期確認は利用者の操作対象とし、自動応答していない。その後、専用ポートと専用プロファイルのプロセスが終了したことを読み取り専用で確認した。利用者から「もう一度m365 copilotを開いて」と依頼され、同じ機能から再度開いた。M365への業務プロンプト送信、認証完了、応答取得は未検証。

再起動時に余分な `about:blank` が残るとの報告を受け、明示的な空タブ起動と別のCopilotタブ作成が原因だとソースで確認した。今後の初回起動では空タブに一意の値を付け、Copilotまたは認証タブの表示後、その値・対象ID・専用プロファイル・接続先を確認して当該タブだけを閉じる。変更済み・曖昧・終了確認不能の場合は追加操作しない。既に開いている普通の空タブや拡張機能のタブは閉じない。修正の実ブラウザー検証は未実施。

専用EdgeのChatGPT拡張機能を読み取り専用で調査した。バージョン `1.26.901.11451`、無効化理由 `[1024]` を確認した。この値は[Chromiumの定義](https://github.com/chromium/chromium/blob/main/extensions/browser/disable_reason.h)では `DISABLE_CORRUPTED` に対応する。拡張機能の `background.js` に、初回インストール時に機能フラグが有効なら `/work/extension/installed` を開く処理も存在した。案内タブが開く仕組みと破損判定の発生原因は分けて扱う。拡張機能・認証・同期・ブラウザーのセキュリティ設定は変更していない。

拡張機能の検証対象1,629ファイルは欠損がなく、4,096バイト単位のSHA-256とメタデータ内のツリールートがすべて一致した。別のmanifestとアイコン4件は[Chromiumがインストール時変換のため検証から除外する対象](https://chromium.googlesource.com/chromium/src/%2B/lkgr/extensions/browser/content_verifier/content_verifier.cc)に一致する。署名そのものは未検証であり、破損判定の発生時点・原因・復旧は確認できていない。限定した診断記録は `.work/chatgpt-extension-integrity-20260905.md` に残した。

空タブとPADタイトルの修正版を `Bootstrap -NoBrowser` で実LOCALAPPDATAへ同期し、HTTP成功、App.ps1のハッシュ一致、フロー設定「無題」、実行中ジョブなしを確認した。同期は専用Edgeの起動・終了やタブ操作を要求しない。

次は作成済みの空の「無題」でGate 1/2を固定コードにより実施し、セレクターやRobin構文を確定してからGate 3〜5へ進む。Copilotには利用者の初回確認・必要な認証が残る。実共有パスと別PCはその後の検証対象とする。

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

最終の独立コードレビューは MUST FIX 0。実機ゲート不足は未解決のまま保持する。
