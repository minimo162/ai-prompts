# Copilotエージェント用PAD Robin配布物

このディレクトリは、Microsoft 365 Copilotの画面内「エージェント → 新しいエージェント／エージェントの作成」から開くAgent Builderの本人限定テスト用配布物です。公式入口は `https://microsoft365.com/chat` です。PADやCopilotを自動実行するアプリではありません。PADの画面から得た原文、設定、型、依存、実行結果を根拠に、利用者がデザイナーへ貼り付けるRobinを生成・修正します。

## 登録するファイル

指示欄へは [agent-instructions.txt](agent-instructions.txt) の本文だけを貼り付けます。ナレッジには次の7ファイルを `.txt` として登録します。

- `knowledge/PAD-Robin-00-Index.txt`
- `knowledge/PAD-Robin-01-Basics.txt`
- `knowledge/PAD-Robin-02-Control.txt`
- `knowledge/PAD-Robin-03-Files.txt`
- `knowledge/PAD-Robin-04-Office-PDF.txt`
- `knowledge/PAD-Robin-05-UI-Web.txt`
- `knowledge/PAD-Robin-06-Examples.txt`

ナレッジは技術資料であり、指示欄と同じ優先順位の命令書ではありません。`pad-robin-prompts.md` は既存の編集用原稿として残し、配布版と二重に指示欄へ貼りません。

`agent-instructions.txt` の実測は UTF-8 BOMなし、Unicodeスカラー数2,045、UTF-16コード単位数2,045（5,648バイト）です。7,000文字目標と8,000文字上限の両方を満たします。実際のCopilot指示欄への入力確認は、認証とテスト用エージェント作成後に別途行います。

## 登録手順

1. ログイン済みのMicrosoft 365 Copilotで「エージェント」から新しい非公開テスト用Agent Builderエージェントを開く。既存エージェントを無断で上書きしない。Copilot Studio単体の開発ポータルへ移行しない。
2. `agent-instructions.txt` を指示欄へ貼り付け、文字数エラーがないことを確認する。
3. 上記7つの `.txt` をナレッジとして登録し、アップロードと処理完了を確認する。
4. `PAD-Robin-00-Index.txt` にある実測固有の質問（設定差分、型、PDF統合順など）を行い、一般的なPAD説明だけでなく登録情報を参照できるか確認する。
5. T01〜T10を新しい会話で行う。依頼文・期待値を先に保存し、回答原文とコードを保存してから、手直しせず専用フローへ貼り付け、保存・実行・成果物を照合する。
6. 失敗時は元回答を上書きせず、原因を構文知識・検索・指示・依存・PAD操作に分類する。ナレッジや指示を変更した場合は新しい会話で再試験する。

## 既存カタログとの対応

実測原文とSHA-256の正本は `../catalog/index.json` と `../catalog/actions/`、組合せフローは `../catalog/flows/`、検証証拠は `../catalog/evidence/`、既存生成例は `../catalog/generated/` にあります。`catalog/coverage.json` は左側一覧の観測範囲とA〜Gの不足を記録し、全アクション対応を表示しません。

## 状態

2026-09-09時点では、配布物の骨格、既存証拠、PAD左パネル観測、日時取得の1設定を整理しました。M365 Copilot内Agent Builderの登録・T01〜T10は `docs/robin-knowledge-progress.md` と `docs/robin-knowledge-validation.md` の状態を正本とします。前回Copilot Studio単体で出た保存拒否は履歴として残しますが、M365 Copilot内Agent Builderの原因や再開条件とは断定しません。未確認の項目を完成扱いしません。
