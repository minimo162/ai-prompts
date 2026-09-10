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

現作業版bundleの原本対応は [knowledge-bundle-manifest-20260910b.json](knowledge-bundle-manifest-20260910b.json) に固定しています。マニフェスト自体をナレッジへ添付する必要はありません。

ナレッジは技術資料であり、指示欄と同じ優先順位の命令書ではありません。`pad-robin-prompts.md` は既存の編集用原稿として残し、配布版と二重に指示欄へ貼りません。

`agent-instructions.txt` の現作業版は UTF-8 BOMなし、UTF-16コード単位数3,949（10,096バイト）で、8,000文字上限以内です。結合版は `tools/Build-KnowledgeBundle.ps1` で7原本から機械的に再生成します。現作業版の指示SHA-256は `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`、bundle SHA-256は `4282e4ece4f2d79ce26e85143fcab201091b185d9ee5d9defe4d8f49a4a7b2cd` です。T04は現作業版で通常チャット添付・生成・無修正PAD貼付け・保存・2回実行まで確認済みです。T01〜T03/T05〜T10については旧版の生成・PAD結果を現作業版へ継承しません。T10既存フロー修正では、元行の文字列・矢印・バックスラッシュ・アンダースコアを確認できない場合はコードを出さず、手編集で差分を隠しません。

## 通常チャット検証手順

1. ログイン済みのMicrosoft 365 Copilotで新しい通常チャットを開く。Agent Builder／Copilot Studioは開かない。
2. `agent-instructions.txt` の全文、短い添付資料参照案内、試験依頼を本文へ入力し、入力後の本文が全文であることを確認する。
3. 上記7つの `.txt` を実ファイルとして添付し、添付一覧・SHA-256・送信メッセージとの対応を記録する。ファイル名やローカルパスの記載だけでは添付済みとしない。
4. 事前確認用の別チャットで、答えを質問文に含めず、設定差分・型・依存を質問し、回答原文を実ファイルと照合する。この会話を受入試験へ流用しない。
5. T01〜T10を毎回新しい通常チャットで行う。回答全文と生成Robinを保存し、手直しせず専用PADフローへ貼り付け、保存・実行・成果物を照合する。
6. 失敗時は元回答を上書きせず、原因をナレッジ不足・参照失敗・指示不足・依存説明不足・PAD操作失敗に分類する。ナレッジや指示を変更した場合は最新版を新しいチャットへ再添付して再試験する。

7つを同時に完了確認できない場合は、`copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt` を使用してよい。これは7原本をファイル名・SHA-256付き区切りで機械的に結合したフォールバックであり、生成元と版を `catalog/generated/normal-chat-t01-20260909/knowledge-bundle-manifest.json` に記録する。最終試験では同じ結合版を使い続ける。

2026-09-10の初回添付試行では、Edgeのfile chooserが`Not allowed`となり、IABでもsetFiles後の添付数が0だった。この失敗は履歴として残す。今回の現作業版は、別CDPセッションで画面に既にマウントされた`input[type=file]`からbundleと合成Excelを添付し、知識precheck、T04、T10一次受入、T10独立再試験まで完了した。ブラウザー拡張CUAの失敗は `catalog/evidence/m365-current-package-upload-block-20260910b.json` に分離し、T01〜T03/T05〜T09の現作業版受入は未実行である。

## 既存カタログとの対応

実測原文とSHA-256の正本は `../catalog/index.json` と `../catalog/actions/`、組合せフローは `../catalog/flows/`、検証証拠は `../catalog/evidence/`、既存生成例は `../catalog/generated/` にあります。`catalog/coverage.json` は左側一覧の観測範囲とA〜Gの不足を記録し、全アクション対応を表示しません。

## 状態

現作業版の追補判定（2026-09-10）：知識precheck、T01〜T07、T04/T10一次受入、T01/T04/T10独立再試験はPASS。T08は有効なRobin fenced blockを生成しない形式失敗、T09はWebAutomation実行BLOCKED、負例は未実行である。個別証跡とハッシュは `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` を正本とし、旧版結果は継承しない。

2026-09-10時点では、配布物の骨格、86件の観測バリアント、既存証拠、PAD左パネル観測、日時・DataTable・CSV・FilterDataTable・ファイルコピー・サブテキスト・テキスト書出し・テキスト変数書込み・For each・If・Excel/Word編集可能起動・フォルダー取得・ファイル変数読取り・PDFページ2単独抽出・T04 Excel条件抽出→別xlsx・T09ローカルUI要素捕捉の追加実測を整理しました。7ファイルの逐次添付が不安定なため、元ファイル名・区切り・SHA-256を保持したフォールバック結合版を使用します。旧版の通常チャット生成・PAD結果は `catalog/evidence/normal-chat-final-package-acceptance-20260910.json` に履歴として保持します。現作業版の正本判定は上記追補と `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` です。T04/T10の旧版差分は `catalog/evidence/normal-chat-raw-provenance-20260910.json` で発生段階を分離しています。Agent Builder／Copilot Studioの登録・権限確認は将来の別環境の確認事項であり、今回の完了条件には含めません。未確認の項目を完成扱いしません。
