# Copilotエージェント用PAD Robin配布物

このディレクトリは、通常のMicrosoft 365 Copilotチャットへ本文入力と実ファイル添付で渡す、PAD Robinの検証用配布物です。公式入口は `https://microsoft365.com/chat` です。Agent Builder／Copilot Studioの作成・権限調査は今回の検証対象にしません。PADやCopilotを自動実行するアプリではありません。PADの画面から得た原文、設定、型、依存、実行結果を根拠に、利用者がデザイナーへ貼り付けるRobinを生成・修正します。

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

`agent-instructions.txt` の実測は UTF-8 BOMなし、Unicodeスカラー数2,943、UTF-16コード単位数2,943（7,840バイト）です。8,000文字上限以内です。通常チャットの本文へ全文を入力した実測と、送信後の欠落有無を別証跡へ保存します。

## 通常チャット検証手順

1. ログイン済みのMicrosoft 365 Copilotで新しい通常チャットを開く。Agent Builder／Copilot Studioは開かない。
2. `agent-instructions.txt` の全文、短い添付資料参照案内、試験依頼を本文へ入力し、入力後の本文が全文であることを確認する。
3. 上記7つの `.txt` を実ファイルとして添付し、添付一覧・SHA-256・送信メッセージとの対応を記録する。ファイル名やローカルパスの記載だけでは添付済みとしない。
4. 事前確認用の別チャットで、答えを質問文に含めず、設定差分・型・依存を質問し、回答原文を実ファイルと照合する。この会話を受入試験へ流用しない。
5. T01〜T10を毎回新しい通常チャットで行う。回答全文と生成Robinを保存し、手直しせず専用PADフローへ貼り付け、保存・実行・成果物を照合する。
6. 失敗時は元回答を上書きせず、原因をナレッジ不足・参照失敗・指示不足・依存説明不足・PAD操作失敗に分類する。ナレッジや指示を変更した場合は最新版を新しいチャットへ再添付して再試験する。

7つを同時に完了確認できない場合は、`copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt` を使用してよい。これは7原本をファイル名・SHA-256付き区切りで機械的に結合したフォールバックであり、生成元と版を `catalog/generated/normal-chat-t01-20260909/knowledge-bundle-manifest.json` に記録する。最終試験では同じ結合版を使い続ける。

2026-09-10の初回添付試行では、Edgeのfile chooserが`Not allowed`となり、IABでもsetFiles後の添付数が0だった。この失敗は履歴として残す。再試行では、画面に既にマウントされた`input[type=file]`をCDPで検出し、GUIのアップロードボタンを押さずに`DOM.setFileInputFiles`で結合版を添付できた。添付状態・本文全文・送信・回答取得を記録している。

## 既存カタログとの対応

実測原文とSHA-256の正本は `../catalog/index.json` と `../catalog/actions/`、組合せフローは `../catalog/flows/`、検証証拠は `../catalog/evidence/`、既存生成例は `../catalog/generated/` にあります。`catalog/coverage.json` は左側一覧の観測範囲とA〜Gの不足を記録し、全アクション対応を表示しません。

## 状態

2026-09-10時点では、配布物の骨格、73件の観測バリアント、既存証拠、PAD左パネル観測、日時・DataTable・CSV・FilterDataTable・ファイルコピー・サブテキスト・テキスト書出し・テキスト変数書込み・For each・If・Excel/Word編集可能起動・フォルダー取得・ファイル変数読取り・PDFページ2単独抽出の追加実測を整理しました。7ファイルの逐次添付が不安定なため、元ファイル名・区切り・SHA-256を保持したフォールバック結合版を使用します。現作業版結合版のSHA-256は `2a0267d4fb42b3c27b9fab8527c63ae2f126474a936339eca0ba6ebe8c7d0f12` です。通常のM365 CopilotチャットでGPT 5.6 Think Deeperを選択し、現作業版と合成Excelを添付してT04の不足構文拒否を現作業版で新規会話により確認しました。これはPAD受入ではありません。旧結合版でのT01/T02/T03/T05/T06/T07/T08/T10実行記録は履歴として保持しますが、現作業版の最終受入には再試験が必要です。T04/T09、T04独立PAD再試験は未完了です。ナレッジ固有事前質問は現作業版で別チャットへ供給し、回答原文を照合済みです。Agent Builder／Copilot Studioの登録・権限確認は将来の別環境の確認事項であり、今回の完了条件には含めません。未確認の項目を完成扱いしません。
