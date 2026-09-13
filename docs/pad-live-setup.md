# PAD実機受入の作成権限・UIA復旧手順

Issue #5 の合成データ受入で、PADの空フローを作成し、Designerを一意に特定してからRobinを貼り付けるための再開メモです。既存の業務フローは対象にせず、作成した専用フローだけを使います。これは配布bundleのナレッジではなく、検証者向けの運用記録です。

## 今回確認した環境

- Microsoft.PowerAutomateDesktop `11.2608.115.0`
- 日本語UI、Power Fx OFF（既存採取条件）
- Consoleプロセス: `PAD.Console.Host.exe`
- Designerプロセス: `PAD.Designer.exe`
- CUA Trusted RPC（`sky`）は未構成。今回の受入では、厳格なWindows UI Automation（UIA）フォールバックを使用した。

`PAD.Designer.exe` を直接起動しただけでは、プロセスが存在しても `MainWindowHandle=0` でUIAのトップレベルウィンドウが返らない状態があった。この状態を「Designerが復旧した」と扱わず、Consoleから作成操作をやり直す。

## 作成権限の確認

作成権限は設定値やプロセスのコマンドラインだけで推測しない。Consoleの実画面で、次のUIA要素が一意に表示され、かつ有効であることを確認する。

| UIA要素 | AutomationId | 確認内容 |
| --- | --- | --- |
| Console本体 | `ConsoleMainWindow` | プロセス名が `PAD.Console.Host`、タイトルが `Power Automate` |
| 新しいフロー | `CreateNewFlowButton` | 一意・有効・Invoke可能 |
| 作成ダイアログ | `DialogWindow` | 1個だけ・表示中 |
| フロー名 | `NewFlowNameTextBox` | ValuePatternで専用名を設定可能 |
| 作成 | `OKNewFlowButton` | 一意・有効・Invoke可能 |

今回の実測では、Consoleの `CreateNewFlowButton` → `NewFlowNameTextBox` → `OKNewFlowButton` が成功し、専用フロー `RobinKnowledgeT01CurrentBundleLive_20260911` が作成された。これはこのPC・このアカウントでの今回のUI操作が成功した証拠であり、組織全体のライセンスや別PCの利用権限を保証するものではない。

## UIA復旧の手順

1. `PAD.Console.Host` のトップレベルUIAウィンドウ `Power Automate` を取得し、PID・開始時刻・タイトル・HWNDを記録する。
2. `DialogWindow` が複数ある場合は、各ダイアログの `CancelNewFlowButton` をInvokeして閉じ、`DialogWindow=0` を再観測する。重複したまま作成ボタンを押さない。
3. `CreateNewFlowButton` が一意であることを再確認して一度だけInvokeする。
4. 生成した `DialogWindow` が1個だけであることを確認し、`NewFlowNameTextBox`へ衝突しない専用フロー名をValuePatternで設定する。
5. `OKNewFlowButton`をInvokeし、`PAD.Designer`のトップレベルウィンドウを再列挙する。
6. `PAD.Designer`プロセスが1個、ウィンドウタイトルが `Power Automate | <専用フロー名>` とOrdinal完全一致、HWNDが0以外、UIAウィンドウ一致数が1であることを確認する。
7. いずれかが満たされなければ、古いPID・座標・タブ・フロー内容を再利用せず停止する。

直接起動で `PAD.Designer` が隠れたままの場合、Consoleからの作成経路へ戻る。作成ダイアログの重複、DesignerのHWND=0、タイトル不一致、複数一致は、作成権限や画面状態を推測して先へ進むための根拠にはならない。

## Robin受入の順序

Designerが一意に取得できた後だけ、次の既存ヘルパーを使う。

### Main/P3Worker 別空フロー再利用の観測器

通常の `Get-AgentPadSnapshot` は、業務フローの誤入口を避けるため既定で `Main` 1個だけを受理する。`Main/P3Worker` の専用再利用試験では、対象名を固定した `tools/Run-PadSubflowReuseLive.ps1` を使う。このヘルパーは、対象PID・タイトル・HWNDを完全一致で確認し、`Main` と `P3Worker` が各1個であること、Mainが選択されていること、実行前にReadyかつエラー0であることを要求する。別名、重複、未知のサブフロー、Main以外の入口は拒否する。原文Robinへの計測アクション追加や、単一サブフローガードの削除は行わない。

サブフロー呼出し完了後はPADが`P3Worker`タブを選択したままになるため、実行中のポーリングはMain選択を再要求せず、`StopFlowButton`・状態バー・エラー状態を読み取る。完了後の最終スナップショットだけでMain/P3Worker固定契約と`ButtonPressed`プレビューを照合する。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Run-PadSubflowReuseLive.ps1 `
  -TargetProcessId <観測したPAD.Designer PID> `
  -FlowName '<画面で完全一致した専用フロー名>' `
  -ExpectationPath '<保存したBのexpectation.json>' `
  -EvidencePath '<新規run1.json>' -RunNumber 1
```

`run1-request.json`／`run1.json`（Run2も同様）は、Run要求前の準備失敗、実行要求後の実行失敗、観測失敗を別状態で保存する。Run要求後にrunningを捕捉できない場合も、未実行とみなして再Runしない。完了PASSは、running→idleの観測、エラー0、`ButtonPressed=OK` の変数プレビュー、実行前後の原文SHA不変を同時に満たす場合だけである。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Paste-PadRobinLive.ps1 `
  -TargetProcessId <観測したPAD.Designer PID> `
  -FlowName '<画面で完全一致した専用フロー名>' `
  -InputPath '<保存したRobin原文>' `
  -EvidencePath '<新規paste/save証跡>' `
  -ExpectedActionCount 3

powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Copy-PadFlowLive.ps1 `
  -TargetProcessId <同じPID> `
  -FlowName '<同じ専用フロー名>' `
  -OutputPath '<新規PAD再コピー原文>' `
  -ExpectedActionCount 3

powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Run-PadFlowLive.ps1 `
  -TargetProcessId <同じPID> `
  -FlowName '<同じ専用フロー名>' `
  -EvidencePath '<run1証跡>' `
  -TimeoutSeconds 30

powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Run-PadFlowLive.ps1 `
  -TargetProcessId <同じPID> `
  -FlowName '<同じ専用フロー名>' `
  -EvidencePath '<run2証跡>' `
  -TimeoutSeconds 30
```

貼付け前に入力RobinのSHAを固定し、貼付け後にアクション数・保存完了・PAD再コピーを確認する。実行は合成入力と専用出力だけに限定し、各回の出力バイト列・BOM・改行・ハッシュと入力不変を別々に記録する。PAD再コピーが改行をLFからCRLFへ変換しても、元のCopilot原文とPAD再コピーを上書きせず、改行を明示した正規化比較だけを行う。

## 失敗時の停止条件

- ConsoleまたはDesignerのUIAウィンドウが返らない
- プロセスはあるが `MainWindowHandle=0`
- フロー名・PID・HWNDの一致が一意でない
- 作成・保存・実行ボタンが有効でない
- 既存業務フロー、古いステージ済みタブ、失効したPIDや座標が混在する

この場合は、UIAの観測証跡だけを残し、貼付け・保存・Runを実行しない。Trusted RPCが利用可能になった場合も、UIAの成功結果へ遡って置き換えず、その経路を別の証跡として扱う。

## 2026-09-14 T04でのアクション数仮想化対策

独立T04の新規空フローでは、実際に貼り付けた9アクションに対し、UIAのListItemとして実体化されたノードは6件だけだった。これは一覧仮想化による観測不足であり、貼付け失敗や生成Robinの欠落とは扱わない。Designerの集計ラベル `9 選択されたアクション`／`9 アクション`、保存後再コピーの9行、原文とのCRLF正規化後一致を併せて正とする。

この条件を固定するため、`tools/Paste-PadRobinLiveByStatus.ps1` はローカライズされた集計ラベル（`^9\\s+.*アクション`）を待つ方式へ最小修正した。直接ListItem件数だけを根拠に再送・再貼付けしない。集計ラベルが現れない場合、フロー名・PID・HWNDが一意でない場合、または保存確認が取れない場合は停止する。今回のT04はこの補助で保存後再コピーを取得し、2回Runまで実施したが、Run1のxlsxスナップショットは未採取のため受入へ昇格せず候補partialに限定した。

## 今回のT01での実測証跡

- Copilot送信・回答・Robin原文: `catalog/evidence/t01-current-bundle-live-send-20260911.json`
- 専用フロー作成、無修正貼付け、保存: `catalog/evidence/t01-current-bundle-pad-paste-save-20260911.json`
- PAD再コピー: `catalog/generated/normal-chat-current-bundle-t01-live-20260911/pad-recopy.robin`
- 2回の実行: `catalog/evidence/t01-current-bundle-pad-run1-20260911.json`、`catalog/evidence/t01-current-bundle-pad-run2-20260911.json`
- 出力・入力の照合: `catalog/evidence/t01-current-bundle-pad-output-comparison-20260911.json`

今回のT01では、アクション数3、保存完了、2回のRun完了、出力90 bytes・UTF-8 BOM・CRLF・期待SHA一致、入力87 bytes・入力SHA不変を確認した。Copilot原文Robin（646 bytes/LF）とPAD再コピー（649 bytes/CRLF）は内容を改変せず別保存し、改行を正規化した本文一致を確認した。

## 2026-09-13e 追記: 現行版T01の貼付け・保存・再実行

現行正本（instruction SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`）の通常チャット生成Robin（646 bytes、SHA `2209d9ce9437c141345c3f01a0cfd12bd6d6ed4dd0668cf0a78ae17479c5ee47`）を、Consoleから作成した専用空フロー `RobinKnowledgeT01CurrentBundleLive_20260913e`（Designer PID 5288、HWND 461824、タイトル完全一致1件）へ無修正で貼り付けた。3アクション、保存完了、保存後再コピーを確認し、2回Runとも成功、出力90 bytesのSHA一致・入力87 bytesのSHA不変を確認した。

PAD再コピーは生成RobinのLF（646 bytes）からCRLF（649 bytes）へ変換されるため、`t01-copilot-live-generation-20260913e-pad-output-comparison.json` ではCRLF正規化後の一致を記録する。生成元からPADまでの厳密バイト一致や、T10の厳密保持をこのT01結果から推論しない。貼付け・保存・Runの原記録は `catalog/evidence/t01-copilot-live-generation-20260913e-pad-*.json`、再コピーは `catalog/generated/normal-chat-20260913e-t01/pad-recopy-after-save.robin` と `pad-recopy-after-run2.robin` に保存した。

T10の判定は同じ規則をより厳密に適用する。`catalog/evidence/t10-strict-preservation-audit-20260913.json` は機能2run、許可された2行（2・4）の内容範囲、生成→PAD再コピーの正規化後一致、生バイト不一致を別フィールドで保持し、`tests/Test-T10StrictPreservation.ps1` で回帰確認する。改行正規化や非変更行の復元で厳密保持をPASSへ変えず、現行は `NOT_PROVEN` とする。

## 2026-09-14 独立T10現行版追補

20260913e正本（instruction SHA `6ad6f742…`／bundle SHA `79245787…`）を通常M365 Copilot新規会話 `6edc277b-b005-4d56-8bb7-ba64668ea636`へ3実添付して1回送信し、単一16行の応答Robinを無修正保存した。Console UIAで専用空フロー `RobinKnowledgeT10IndependentCurrentBundleLive20260914e` を作成し（Designer PID 20008、タイトル完全一致）、`dom-robin.txt` を貼り付けた。初回の60秒ヘルパー観測ではListItem 6件でタイムアウトしたが、同じ貼付けが後続で集計`16 アクション`へ収束したため再送しなかった。集計16件、保存、再コピー、2回Runを確認し、各回の出力スナップショットでExcel A1=`T10-Changed`、Word/PPT本文=`CopilotOffice 246`を確認した。既存Office出力はバックアップから復元した。生成→PADはCRLF正規化後のみ一致し、元入力→生成および生バイトの厳密保持は`NOT_PROVEN`のまま。原記録・結果は`catalog/evidence/t10-independent-current-generation-20260914e.json`と`catalog/evidence/t10-independent-current-pad-*.json`に分離保存する。

T04の20260913e追跡では、同版指示・bundle・Think Deeper・2実添付を維持した新規通常チャットへ1回だけ送信した。応答DOMの`pre code`と保存Robinは同一SHA（1,585 bytes）で、5箇所の`=\>`がDOM段階から存在したため生成回答由来の形式不履行と判定した。生成回答の手修正、auto-unescape、PAD貼付け・保存・実行は行わず、同じ方法の追加送信を停止する（`catalog/evidence/t04-copilot-live-generation-20260913-attempt3.json`、`t04-next-hypothesis-20260913e.json`）。

## 2026-09-14 現行版T01独立再試験

同じ20260913eの指示／bundle（SHA `6ad6f742…`／`79245787…`）を通常Chrome M365 Copilotの新規会話 `f0af1bd2-f257-4ba4-9b22-c3da0cce9ef9`へ実添付し、Think Deeperで1回送信した。公式応答コピーは2321文字、DOM上の`pre`は1件・3行・646 bytes（SHA `2209d9ce…`）で、生成Robinを無修正保存した。新規PADフロー `RobinKnowledgeT01IndependentCurrentBundleLive20260914e`（PID 31848）へ貼付け・保存・再コピーし、再コピーはCRLF差のみで正規化後一致。2回Runで各出力90 bytes・期待SHA `2b030f2d…`一致、入力SHA `2866f343…`不変、既存出力の同一SHA復元まで確認した（`catalog/evidence/t01-independent-current-output-comparison-20260914e.json`）。生成元→PAD厳密バイト保持は未評価で、T04／T10厳密保持等の残件判定は変更しない。

## 2026-09-12 追記: 待機の単位、UI要素の取り込み、通常チャットの操作方法

- PADの `WAIT n` は秒単位である（待機ダイアログの説明は「指定された秒数だけフローの実行を中断します」）。`WAIT 500` は8分20秒待つ。T09教材は待機ダイアログで1へ直し、PADから再コピーした `WAIT 1` を正とする。
- 通常チャットが生成するWebAutomation行はControlRepository（UI要素）を運ばない。貼付け先フローへは、ControlRepository付きの採取原文（`catalog/flows/ui-t09-local-roundtrip/roundtrip-wait1-20260912.robin`）を `tools/Paste-PadRobinLive.ps1` でファイルから貼り付けて3要素を登録し、デザイナーでアクションを全選択（Ctrl+A）して削除してから、生成6行を同じツールで貼り付ける。
- `Paste-PadRobinLive.ps1`／`Copy-PadFlowLive.ps1` の件数確認は、Designerのアクション一覧が仮想化されるため、対象Designerを最大化・前面化してから実行する。開いているDesignerが多いと（本セッションでは36窓）貼付けが応答しないことがあり、保存済みの不要なDesignerを閉じると回復した。
- 通常M365 Copilotチャットは Google Chrome（Claude in Chrome拡張）で操作する。本文はクリップボード経由で貼り付け（Set-Clipboard→composerクリック→Ctrl+A/Delete/Ctrl+V）、送信前に composer の `<p>` textContent（aria-hidden のカーソル用spanを除く）を改行で連結したSHA-256を本文ファイルと照合する。貼付けはそのタブが可視・前面のときだけ成立するため、`document.title` に目印を付けてCtrl+Tabで前面化してから行う。添付は `file_upload`、モデルは「モデル セレクター」→Think Deeper、回答は `get_page_text` と `pre.textContent` の行長で照合する。
