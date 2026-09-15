# PAD・通常M365 Copilotの操作入口

過去の操作手順は残っている。最初にこのページで経路を確認し、詳しい設定・証跡は[PAD実機手順](pad-live-setup.md)を参照する。
以下は既存ファイルと過去の成功証跡を照合して整理したもの。今回、起動・ログイン・貼付け・Runを再実測した結果ではない。

## 最初に区別すること

| 確認対象 | 過去に成功した経路 | それだけで否定できない観測 |
|---|---|---|
| PAD | Consoleから専用空フローを作り、対象Designerを特定してWindows UIA補助ツールで操作 | Computer Useの起動エラー、アプリ一覧に出ない、プロセスだけ存在する |
| 通常M365 Copilot | 通常Google Chrome＋Claude in Chrome拡張。実添付・本文一致確認・送信・回答取得 | in-app browserの未ログイン、拡張経路のツールが現在のタスクにない |

**Computer Use失敗をPAD本体の故障と同一視しない。in-app browser未ログインを通常Chromeの未ログインと同一視しない。**
逆に、過去に成功したという理由だけで、現在その経路が操作可能・ログイン済みとも扱わない。

今回のIssue #38ではComputer UseのConsole起動が`GetCursorPos / 0x80070005`で2回失敗し、in-app browserはサインイン前だった。過去のChrome拡張・UIA経路を十分に調べず、実機環境全体の利用可否へ広げて説明した点を訂正する。直接UIAと通常Chrome拡張による今回の起動・接続は未確認。

## 再開時の確認順

1. 対象worktree、版別manifest、合成入力・依頼・出力先を確定する。既存のPID、会話URL、専用フロー名、Run計画を新しい試行へ流用しない。
2. 現在使用可能な操作ツールを確認する。過去の`file_upload`や`get_page_text`はClaude in ChromeのAPI名であり、別のブラウザーツールへ同名で呼べるとは限らない。現在のツール一覧とその仕様を使う。
3. PADのプロセスと実ウィンドウ、Chromeの対象プロフィールと通常M365タブを別々に確認する。エラーは経路名とセットで記録する。
4. 選んだ経路の利用条件・適用スキルを確認する。Computer Useスキルは同じターンで直接PowerShell UIAと併用しないため、混ぜて再試行しない。過去手順は現在の制約を上書きしない。
5. 既に処理中なら、その同じ処理を観測する。観測タイムアウトだけで再送・再貼付け・再Runしない。起動の失敗でも実プロセス/窓を確認してから次の判断をする。

## PAD：Console → 専用空フロー → 保存・再コピー

1. PADが起動済みか確認する。未起動なら、その時点でインストールされている**Console**を選んだ操作経路で開く。`PAD.Designer.exe`を直接起動して代用しない。
2. Consoleの「新しいフロー」が一意に表示され、有効であることを確認する。新規ダイアログも1個だけであることを確認し、今回専用の未使用名で作成する。既存フローは編集しない。
3. `PAD.Designer`のPID・SessionId・非ゼロHWND・タイトル`Power Automate | <専用名>`の完全一致で対象を1つに絞る。プロセスがあるだけ、HWND=0、窓が複数は操作開始条件を満たさない。
4. Power Fx OFF、日本語UI、空の対象サブフロー、エラーなしを実画面で確認する。行数とアクション数を混同しない。
5. 保存した生成原文ファイルを無修正で1回貼り付ける。クリップボードの保全に失敗したら重複貼付けしない。
6. 保存→再コピー→原文との照合を行う。アクション一覧は仮想化されるため、見えるListItem数が少ないだけで貼付け失敗としない。集計表示と保存後の全原文を確認する。
7. エラー・未確認条件がなければ実行へ進む。Run1の成果物を閉じた状態で保存・照合してからRun2へ進む。

ConsoleのUIA識別子は `CreateNewFlowButton` → `NewFlowNameTextBox` → `OKNewFlowButton`。詳細は[作成権限と復旧手順](pad-live-setup.md)にある。識別子は対象画面で再確認し、記載だけを根拠に未知状態の窓を操作しない。

### 既存の補助ツール

引数は現行ファイルのparam定義で確認した。以下の名前・数値を昔の値で埋めない。実行前に対象を確認する。

| 工程 | ファイル | 必須引数・注意 |
|---|---|---|
| 状態診断 | [Diagnose-PadWindowVisibility.ps1](../tools/Diagnose-PadWindowVisibility.ps1) | `TargetProcessIds`, `OutputPath`。非操作の診断。PIDを先に取得する |
| 空フローへ貼付け | [Paste-PadRobinLiveByStatus.ps1](../tools/Paste-PadRobinLiveByStatus.ps1) | `TargetProcessId`, `FlowName`, `InputPath`, `EvidencePath`, `ExpectedActionCount`。空フロー照合・クリップボードleaseあり |
| 保存 | [Save-PadFlowLive.ps1](../tools/Save-PadFlowLive.ps1) | `TargetProcessId`, `FlowName`。対象タイトル完全一致が必要 |
| 全原文再コピー | [Copy-PadFlowLiveByStatus.ps1](../tools/Copy-PadFlowLiveByStatus.ps1) | `TargetProcessId`, `FlowName`, `OutputPath`, `ExpectedActionCount`。出力既存なら拒否 |
| 単発Run | [Run-PadFlowLive.ps1](../tools/Run-PadFlowLive.ps1) | `TargetProcessId`, `FlowName`, `EvidencePath`。`TimeoutSeconds`既定30。これ単独ではRun間成果物ゲートにならない |
| T04専用ペア | [Run-PadArtifactPairLive.ps1](../tools/Run-PadArtifactPairLive.ps1) | `PlanPath`, `RunNumber`。CSV+xlsxの2出力とT04用条件を要求。**EX01〜EX03へそのまま流用しない** |

PowerShell版も過去記録と各ツールの依存を確認する。直近記録にはPS7のUIA補助と、PS5.1で日本語を読むためBOMを付けた貼付け補助がある。「すべてPS5.1」「すべてPS7」と一括で決めない。補助の構文や静的テストが通ることは現在のUI操作成功ではない。

## Copilot：接続 → 実添付 → 送信前確認 → コピー

1. 過去に使った通常Chrome経路が現在の操作ツールに接続されているか確認する。in-app browserとは別のセッション。通常M365 Copilotの新規チャットを使い、Agent Builderや個人向けCopilotへ置き換えない。
2. 添付するのは同版bundle。指示全文は本文へ入れる。[版の入口](../copilot/README.md)で組合せを確認する。過去の7添付手順は必須ではない。
3. 指示全文＋固定依頼の本文を用意し、実際に入力された本文と照合する。採点用expected.jsonや完成Robinは混ぜない。
4. bundleを実ファイルとして添付し、アップロード完了と添付一覧を確認する。パスやファイル名を書いただけでは添付済みにならない。
5. 本文・添付・選択モデルを確認してから1回だけ送信する。モデル名やUIの位置は現在の画面で確認する。過去はThink Deeperで成功した。
6. 完了した回答全文とコード専用コピー内容を別々に保存する。DOMの`pre.textContent`採取は補助証拠であり、コピーボタン取得内容そのものを保証しない。
7. コピー本文の先頭・末尾がPAD命令であり、フェンス・説明・行番号がないことを確認する。手編集・自動unescapeで合格にしない。表示されたコピーボタンだけでPAD成功としない。

過去記録の「可視タブを前面化して貼る」「composer内の`p`を照合する」は当時のUI依存手順。現在のツールに本文直接入力/読取りがあれば、実DOMとAPI仕様に基づき実施する。履歴の`document.title`変更や無条件`Set-Clipboard`を一般的な必須手順としてコピーしない。

## 同じつまずきの防止

| 観測 | 次の判断 |
|---|---|
| `sky`の`GetCursorPos`アクセス拒否 | 操作経路の失敗として記録。ロック状態・PAD故障・UIA経路不可を未確認のまま断定しない |
| in-appが未ログイン | 通常Chrome接続とは分ける。接続済みChromeがなければ、その不足を具体的に報告 |
| Designerプロセスはあるが窓なし | 既存状態を保全し読取り診断。直接Designerの多重起動をしない |
| ListItem数が期待より少ない | 集計表示・保存後再コピーを確認。結果不明の再貼付けは禁止 |
| Run観測がタイムアウト | 同じRunの状態を再観測。停止/成功/失敗が確定するまで次Runなし |
| 準備完了なのに実行・停止とも無効 | OutputGuardで観測。診断メニューを閉じ、既存アクションを1件選択してフォーカスを戻すと実行が有効化した（再Run・再起動なし）。この後の準備完了・実行有効・期待値・原本SHAを記録してから次Runを判断する。メニュー閉鎖と選択変更のどちらが原因かは未分離 |
| 既存出力がある | 勝手に上書きしない。前Runの成果物照合・退避を先に確定 |
| T04専用補助がEXで拒否 | 条件を外して通さない。EX用成果物・ゲートに合わせた別対応が必要 |
| ツールの`blocked by policy` | 表示された拒否理由だけを記録する。「自動承認レビューの判断」とは、発生元が確認できない限り断定しない |
| `PAD_CLIPBOARD: unsupported native format; paste refused` | `PadClipboardLease.cs`の保全処理による貼付け前の停止。自動承認レビューとは別。形式名だけで診断し、私的内容を読み出したり、保全を外して上書きしたりしない |
| コピー直後に以前の本文が読める | コピー完了は非同期。画面を再観測し、取得内容が直前の内容から変わったことを確認して保存する。古い内容を生成コードとしない |
| 変数の値の画面を閉じたのに操作できない | 値ビューアの閉じる後、次の観測で親の変数編集ダイアログを確認しキャンセルする。変数を保存しない |
| アクションの変数名欄がread-only | 「変数の設定」の`EditableText`は表示状態では読取専用だった。専用フローの同欄をダブルクリックして編集状態へ入り、次のUIA観測で`IsReadOnly=false`を確認してから設定する |
| skyで設定ダイアログの入力が空のまま | 親ウィンドウ対象の入力は反映されない例あり。再入力を重ねず、別ターンの直接UIAで可視の`EditableTextBox`を一意に取得し、設定値の読戻し後に保存できた。skyと直接UIAを同じターンで混在させない |

## 根拠と今回の確認範囲

- [既存の操作記録](pad-live-setup.md)：Console作成、UIA、仮想化、Chrome拡張経路の記載。
- [独立T01出力照合](../catalog/evidence/t01-independent-current-output-comparison-20260914e.json)：通常チャット回答、生成Robin、PAD往復・成果物の履歴。
- [独立T10生成記録](../catalog/evidence/t10-independent-current-generation-20260914e.json)：通常Chrome M365・実添付・送信回数・本文SHAの履歴。
- [Issue #38報告](../catalog/acceptance/issue38/report.md)：候補と実機未実施範囲。上の旧成功をEX受入へ継承しない。

## 2026-09-15の実機確認で分かった回避手順

PADは直接PowerShell UIA経路で起動・操作できた。以前の`sky`アクセス拒否はこの経路の不可を意味しない。

1. ConsoleはAppxManifestの`PAD.Console`登録にあるExecutableを使う。今回の登録は`dotnet\PAD.Console.Host.exe`。パッケージ直下の同名exeはアクセス拒否だったため、パスを推測しない。
   ```powershell
   $padPackage = Get-AppxPackage Microsoft.PowerAutomateDesktop
   $padManifest = Get-AppxPackageManifest -Package $padPackage.PackageFullName
   $padConsole = @($padManifest.Package.Applications.Application | Where-Object Id -eq 'PAD.Console')
   if ($padConsole.Count -ne 1) { throw 'Console registration is not unique' }
   Start-Process -FilePath (Join-Path $padPackage.InstallLocation $padConsole[0].Executable) -WindowStyle Hidden
   ```
2. `Process.MainWindowHandle`がツールチップを指す場合があった。実ウィンドウ列挙から、PIDと専用フローの完全なタイトルが一致するHWNDを選ぶ。診断補助のJSONにはT04固定メタデータがあるため、Issue38での窓観測をT04実行証拠にしない。
3. ツリーのExcel書込み項目が画面外なら、Designerを最大化し、対象項目の`ScrollItem.ScrollIntoView`後に可視状態を確認する。項目が見えないままダブルクリックを繰り返さない。
4. 今回の貼付け補助はPS7で`Dictionary<>`のコンパイルに失敗した。これは貼付け前の失敗だったことを確認し、Windows PowerShell 5.1（`powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File ...`）で実施した。21アクションの保存・再コピーSHA一致を確認した。
5. `Flow_status_ready`だけでは終了を断定できない。今回Start無効・Stop有効の状態が残り、実行補助は120秒で終了未確認となった。成果物保存補助の`READY_FOR_NEXT_RUN`も、論理照合・実行終了の合格を保証しない。

[原文・往復・Run1証跡](../catalog/acceptance/issue38/probes/matrix-write/)を保存した。これは実装AIが組み立てたプリミティブ検証で、Copilot生成のEX受入ではない。12転記セルの値・型・位置に不一致はなかったが、openpyxlの書式等の照合はFAIL。補助のExcelネイティブ書式照合は一致したが、終了未確認のためRun2未開始。

通常M365 Copilotはin-appブラウザーで利用でき、r3の指示全文とbundle実添付による生成を確認した。EX01は無修正貼付け・保存・再コピー後に2回実行し、表示値・位置が一致した（各セルの実行時型は直接未観測）。EX02はコード生成停止、EX03は未採取の`EXIT`を含むためPAD未実行。詳細は[EX証跡](../catalog/acceptance/issue38/copilot/)を参照し、全体成功と混同しない。

クリップボード形式名のみの診断では`DataObject`、`Ole Private Data`を検出した。これらは保全補助の許可対象外であり、現在の停止条件と整合する。内容は取得・変更していない。形式の存在だけで元アプリやポリシー誤判定を断定しない。
