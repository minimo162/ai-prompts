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

## 今回のT01での実測証跡

- Copilot送信・回答・Robin原文: `catalog/evidence/t01-current-bundle-live-send-20260911.json`
- 専用フロー作成、無修正貼付け、保存: `catalog/evidence/t01-current-bundle-pad-paste-save-20260911.json`
- PAD再コピー: `catalog/generated/normal-chat-current-bundle-t01-live-20260911/pad-recopy.robin`
- 2回の実行: `catalog/evidence/t01-current-bundle-pad-run1-20260911.json`、`catalog/evidence/t01-current-bundle-pad-run2-20260911.json`
- 出力・入力の照合: `catalog/evidence/t01-current-bundle-pad-output-comparison-20260911.json`

今回のT01では、アクション数3、保存完了、2回のRun完了、出力90 bytes・UTF-8 BOM・CRLF・期待SHA一致、入力87 bytes・入力SHA不変を確認した。Copilot原文Robin（646 bytes/LF）とPAD再コピー（649 bytes/CRLF）は内容を改変せず別保存し、改行を正規化した本文一致を確認した。
