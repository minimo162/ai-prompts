# PAD Robin Copilot ナレッジ

Power Automate for desktop（PAD）の**実測済みRobin**を根拠に、Microsoft 365 Copilotへ日本語で依頼し、PADへ貼り付けて確認できるフロー案を作るためのリポジトリです。

現在の主成果物は [`copilot/`](copilot/) 配下です。`App.ps1` / `index.html` / `業務エージェント.cmd` は過去に開発した汎用業務エージェントの資産で、現在の推奨入口ではありません。

> **受入済み基準版の状態（2026-09-15）**  
> 基準版 `20260913e` は、通常の Microsoft 365 Copilot Chat + PAD で指定受入を完了しています。Issue [#5](https://github.com/minimo162/ai-prompts/issues/5) / [#27](https://github.com/minimo162/ai-prompts/issues/27) は CLOSED / COMPLETED です。T10の transport-level raw-byte strict は `NOT_PROVEN` のままですが、現在の必須完了条件では非ブロッカーです。詳細は [最終受入監査](catalog/evidence/final-content-acceptance-20260915.md) を参照してください。

## まず使う

**Issue #38のExcel拡張は `20260915-excel-r3` 候補です（実機未受入）。** [候補指示](copilot/versions/20260915-excel-r3/agent-instructions.txt)の全文と、[同版bundle](copilot/versions/20260915-excel-r3/knowledge/PAD-Robin-Knowledge-Bundle.txt)の実添付をセットで使います。シート切替原文を収録しましたが、DataTable矩形書込み原文を追加採取し、12セルの値・型・位置一致まで観測しました。終了未確認・書式照合FAILが残り、EX01〜EX05の実Copilot/PAD受入は未実施です。[差分・結果・再開条件](catalog/acceptance/issue38/report.md)を確認してください。受入済み20260913eおよび既存r2は保持しています。

**コピー用コードブロック改善版は `20260915-copyable-r2` です。** 初版では実Copilot上でコピーボタンの表示までは確認できましたが、閉じMarkdownフェンスがコピー対象へ混入し、PADでエラーになる実機結果がありました。r2はその漏れを防ぐ指示へ修正した静的検査版で、実Copilot/PADでの再試験はこれからです。基準版の受入結果をr2へ継承しません。[改善内容・検証範囲](copilot/copyable-output.md)を確認してください。

### 必要なもの

起動・接続・貼付けで困った場合は、[PAD・Copilotの操作入口](docs/pad-copilot-operation-guide.md)を参照してください。過去の成功経路と、今回の環境で確認すべき条件をまとめています。

- Microsoft 365 Copilotを利用できるアカウント
- Power Automate for desktop（PAD）
- 現在の検証条件に合わせる場合は、通常のM365 Copilot Chatと日本語表示のPAD

Agent Builder / Copilot Studioではなく、**通常のM365 Copilot Chat** が現行受入の対象です。

### 5分で始める

1. Microsoft 365 Copilotで新しい通常チャットを開きます。
2. [`copilot/agent-instructions-copyable.txt`](copilot/agent-instructions-copyable.txt) の全文をメッセージ本文へ貼ります。旧 `agent-instructions.txt` と二重に貼らないでください。
3. [`copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt`](copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt) を添付します。
4. 続けて、やりたい処理を日本語で依頼します。
5. Robinのコードブロックにコピー機能が表示されていても、コードブロック内部に独立したバッククォート3個の行が見えていないことを確認します。見えている場合はコピーせず、その回答を不受入にします。
6. コピー後、先頭行と最終の非空行がどちらもPAD命令であり、`text`・`Plain Text`・Markdownフェンスが混入していないことを確認してからPADの空フローへ貼り付けます。
7. 保存後、まず複製したテストデータで実行し、出力内容まで確認します。

コピー時の確認方法は [コピー用出力ガイド](copilot/copyable-output.md) にあります。既存のチャットにはr2が自動反映されないため、新しいチャットで指示全文とナレッジを渡してください。

版別の指示・bundle対応と通常チャットでの検証手順は [`copilot/README.md`](copilot/README.md) を参照してください。標準入力は同版の指示全文＋bundle実添付です。

### 依頼例

```text
添付したPAD Robinナレッジを参照してください。

C:\Work\input.csv を読み込み、A列が「対象」の行だけを抽出して、
C:\Work\output.xlsx へ保存するPADフローを作ってください。
既存のoutput.xlsxは上書きして構いません。
```

生成結果は、説明文ではなく**PADへ貼り付けるRobin部分**を対象に確認してください。未採取の命令名・引数・UI要素などは推測で補わないことを、改善版・基準版の両方の指示文で要求しています。

## このリポジトリでできること

- 日本語の依頼から、実測済みPAD Robinを組み合わせたフロー案を作る
- Excel / CSV / ファイル / フォルダー / 制御 / 一部Office・PDF・UI操作など、採取済みの範囲を再利用する
- 既存Robinの限定修正で、指定箇所以外の命令内容を保持する
- 生成したRobinをPADへ貼り付け、保存・実行・成果物まで照合するための検証資料を参照する

**PAD全機能に対応しているわけではありません。** 実測範囲の正本は [`catalog/index.json`](catalog/index.json)、観測範囲は [`catalog/coverage.json`](catalog/coverage.json) です。

## 改善版と受入済み基準版

| 指示文 | 用途・状態 |
|---|---|
| [`agent-instructions-copyable.txt`](copilot/agent-instructions-copyable.txt) | `20260915-copyable-r2`。閉じフェンスのコピー対象混入を禁止した改善版。静的検査後、実Copilot/PAD再試験待ち |
| [`agent-instructions.txt`](copilot/agent-instructions.txt) | `20260913e`。受入済み基準版。原文と既存テスト・証跡を保持 |

改善版のSHA・基準版との対応・初版の実機失敗境界は [版情報](copilot/copyable-output-20260915.json) にあります。共通のナレッジ7原本・結合版は変更していません。以下の固定値・受入は**基準版のみ**に適用します。

| 項目 | 基準版の固定値 |
|---|---|
| version | `20260913e` |
| instruction | [`copilot/agent-instructions.txt`](copilot/agent-instructions.txt) |
| instruction SHA-256 | `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c` |
| knowledge bundle | [`copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt`](copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt) |
| bundle SHA-256 | `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12` |
| manifest | [`copilot/knowledge-bundle-manifest-20260913e.json`](copilot/knowledge-bundle-manifest-20260913e.json) |
| 最終受入 | [`catalog/evidence/final-content-acceptance-20260915.md`](catalog/evidence/final-content-acceptance-20260915.md) |
| 検証記録 | [`catalog/evidence/final-content-verification-20260915.json`](catalog/evidence/final-content-verification-20260915.json) |
| 統合 | PR [#34](https://github.com/minimo162/ai-prompts/pull/34) / main `c434e99511ae7a2a28a08eabbb6ad0b120dec9f3` |

### 基準版のT10について

現在の必須条件は、**指定された変更だけを反映し、それ以外の既存命令・入力・変数・処理・エラー経路の内容を保持すること**です。この条件は一次・独立ともPASSしています。

一方、CRLF/LF・EOF・BOM等を含む transport-level raw-byte 完全保持は一次・独立とも `NOT_PROVEN` で、許可区間外raw bytesの厳密比較はFAILです。これは現在の必須受入をブロックしない品質境界として履歴を保持しています。過去の失敗証跡を成功へ書き換えてはいません。

## リポジトリ構成

| パス | 役割 |
|---|---|
| [`copilot/`](copilot/) | 現在の主成果物。Copilot向け指示、ナレッジ、配布手順 |
| [`copilot/agent-instructions-copyable.txt`](copilot/agent-instructions-copyable.txt) | コピー内容へMarkdownフェンスを混入させない改善版の指示文 |
| [`copilot/agent-instructions.txt`](copilot/agent-instructions.txt) | 受入済み基準版の指示文 |
| [`copilot/knowledge/`](copilot/knowledge/) | PAD Robinの技術ナレッジ7原本と結合版 |
| [`catalog/`](catalog/) | PADから採取したRobin、生成物、受入証跡、coverage |
| [`docs/`](docs/) | 採取方法、検証、復旧、過去方式などの詳細資料 |
| [`tests/`](tests/) | 検査・回帰テスト |
| [`tools/`](tools/) | bundle生成、比較、保存、リリース補助など |
| [`pad-robin-prompts.md`](pad-robin-prompts.md) | 編集・採取用の過去原稿。現行指示欄へ二重投入しない |
| `App.ps1` / `index.html` / `業務エージェント.cmd` | 過去資産の汎用業務エージェント |

## ナレッジの構成

通常は結合版 [`PAD-Robin-Knowledge-Bundle.txt`](copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt) を1ファイル添付すれば利用できます。原本は次の7ファイルです。

1. `PAD-Robin-00-Index.txt`
2. `PAD-Robin-01-Basics.txt`
3. `PAD-Robin-02-Control.txt`
4. `PAD-Robin-03-Files.txt`
5. `PAD-Robin-04-Office-PDF.txt`
6. `PAD-Robin-05-UI-Web.txt`
7. `PAD-Robin-06-Examples.txt`

結合版は7原本から機械的に生成します。ナレッジは技術資料であり、利用者の依頼や `agent-instructions.txt` より上位の命令として扱いません。

## 安全に使うための原則

- 未採取のPAD命令名・引数名・列挙値・UI要素・出力型を推測しない
- 実行ボタンを押せたことや、エラーが表示されないことだけで成功扱いにしない
- 生成Robinを手修正して失敗証跡を隠さない
- 既存フローの修正では、依頼された範囲以外を勝手に変更しない
- 最初は本番ファイルではなく、複製した合成・テストデータで確認する
- 削除、無断上書き、送信、公開、本番更新を既定動作にしない
- 個人情報、認証情報、社内データを例・証跡・公開リポジトリへ入れない

詳しい生成ルールは、使用する版の指示文にあります。改善版は表示形式だけを追加し、基準版の生成・安全・文字保持ルールを維持しています。

## 開発・検証する場合

指示文やナレッジを変更した場合は、旧版のPASSを新しい組合せへそのまま継承しません。新しいSHAでbundleを固定し、必要な受入をやり直します。

改善版の静的回帰テストは `node tests/Test-CopyableRobinPrompt.mjs` で実行できます。これはr2の実Copilot生成・コピー内容・PAD再受入を証明するものではありません。

主な確認先:

- [`copilot/README.md`](copilot/README.md) — 配布物と通常チャット検証手順
- [`CODEX_CORRECTION_M365_CHAT_VALIDATION.md`](CODEX_CORRECTION_M365_CHAT_VALIDATION.md) — 通常M365 Copilot Chatでの検証条件
- [`CODEX_TASK_PAD_ROBIN_KNOWLEDGE.md`](CODEX_TASK_PAD_ROBIN_KNOWLEDGE.md) — 採取・教材化の作業記録
- [`docs/pad-live-setup.md`](docs/pad-live-setup.md) — PAD実機検証の準備・復旧
- [`docs/robin-knowledge-validation.md`](docs/robin-knowledge-validation.md) — 受入監査
- [`catalog/evidence/`](catalog/evidence/) — 個別の原証跡・比較・検査結果

## 過去資産: 汎用業務エージェント

リポジトリ直下の次の3ファイルは、Windows PowerShell + HTMLでM365 CopilotとPADを接続する**過去の汎用業務エージェント**です。

```text
業務エージェント.cmd
App.ps1
index.html
```

この方式は実装をチェックポイントとして保存し、現在は主経路を `copilot/` の指示・ナレッジ方式へ移しています。新しく利用を始める場合は、上記3ファイルではなく「[まず使う](#まず使う)」の手順から始めてください。

過去方式の詳細は以下に残しています。

- [`docs/session-handoff-2026-09-07.md`](docs/session-handoff-2026-09-07.md)
- [`docs/issue-5-validation.md`](docs/issue-5-validation.md)
- [`docs/general-agent-live-2026-09-07.md`](docs/general-agent-live-2026-09-07.md)
- [`docs/document-run-checkpoint-2026-09-08.md`](docs/document-run-checkpoint-2026-09-08.md)
- [`docs/release-operations.md`](docs/release-operations.md)

## 検証履歴を見る

ルートREADMEには日ごとの詳細ログを積み上げず、**現在地と使い方だけ**を置きます。詳細な検証履歴・失敗境界・旧判定は次を正本として参照してください。

- [Issue #5](https://github.com/minimo162/ai-prompts/issues/5) — 必須A〜Gの受入と履歴
- [Issue #27](https://github.com/minimo162/ai-prompts/issues/27) — 現行最終版の受入と履歴
- [`catalog/evidence/final-content-acceptance-20260915.md`](catalog/evidence/final-content-acceptance-20260915.md) — 最終受入監査
- [`catalog/evidence/final-content-acceptance-20260915.json`](catalog/evidence/final-content-acceptance-20260915.json) — 機械可読の判定
- [`catalog/evidence/final-content-verification-20260915.json`](catalog/evidence/final-content-verification-20260915.json) — 最終検証記録
- [`catalog/evidence/`](catalog/evidence/) — 過去の成功・失敗・NOT_PROVENを含む原証跡

README整理前の長い時系列説明はGit履歴にも残ります。現在の判定は、古い `OPEN / partial` 表記ではなく上記の最終受入を優先してください。
