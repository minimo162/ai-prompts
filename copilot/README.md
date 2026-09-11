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

現作業版bundleの原本対応は [knowledge-bundle-manifest-20260911c.json](knowledge-bundle-manifest-20260911c.json) に固定しています。マニフェスト自体をナレッジへ添付する必要はありません。

2026-09-11追補として、7原本へP3の実測根拠（真偽値・数値／日時演算、Else／Else-if／EXIT／NEXT、既定エラーハンドラー、PADで採取したGet last error、サブフロー、DataTable作成、File.Exists／Folder.Create／Move／Rename、Excel範囲読取り、T09停止境界）を統合しました。失敗境界（カスタム日時書式、名前付きFileNotFoundルール、DataTable行追加、Excel For each、リスト取得、T09）は未確認として明記しています。最新bundle SHA-256は `61f040b900dfc90fe395f21426bc7a684c7dbf45c2ac82e38d1f00490ffc2f6b` です。最終bundleの知識precheckとT01/T08期待エラー受入は完了しましたが、T01〜T10全件・独立再試験が完了するまで現行packageを受入済みとは扱いません。

Final3固定版のbundle SHA-256は `2bc3f2b4c5c709e94547ccf4b75f7084c9c424605781e01414f6783a1fd026a7` です。新規通常M365 Copilot送信と実PADでT01〜T08/T10を同版受入し、T01/T04/T10は独立再試験も完了しました。T09はUI要素捕捉・6アクション貼付け・保存・再コピーまでで、実行時のUI要素未検出によりRun開始前にブロックされています。P3未確認項目を含めて `partial／OPEN` を維持します。PAD空フロー作成権限とUIA復旧の観測手順は [docs/pad-live-setup.md](../docs/pad-live-setup.md) にまとめています。

ナレッジは技術資料であり、指示欄と同じ優先順位の命令書ではありません。`pad-robin-prompts.md` は既存の編集用原稿として残し、配布版と二重に指示欄へ貼りません。

`agent-instructions.txt` の現作業版は UTF-8 BOMなし、UTF-16コード単位数3,949（10,096バイト）で、8,000文字上限以内です。結合版は `tools/Build-KnowledgeBundle.ps1` で7原本から機械的に再生成します。現作業版の指示SHA-256は `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`、T01測定済み組み合わせとT08エラー記録を含む最終bundle SHA-256は `61f040b900dfc90fe395f21426bc7a684c7dbf45c2ac82e38d1f00490ffc2f6b` です。旧bundleの生成・PAD結果を新bundleへ継承せず、新ハッシュで知識precheckとT01〜T10を再受入します。T10既存フロー修正では、元行の文字列・矢印・バックスラッシュ・アンダースコアを確認できない場合はコードを出さず、手編集で差分を隠しません。

## 通常チャット検証手順

1. ログイン済みのMicrosoft 365 Copilotで新しい通常チャットを開く。Agent Builder／Copilot Studioは開かない。
2. `agent-instructions.txt` の全文、短い添付資料参照案内、試験依頼を本文へ入力し、入力後の本文が全文であることを確認する。
3. 上記7つの `.txt` を実ファイルとして添付し、添付一覧・SHA-256・送信メッセージとの対応を記録する。ファイル名やローカルパスの記載だけでは添付済みとしない。
4. 事前確認用の別チャットで、答えを質問文に含めず、設定差分・型・依存を質問し、回答原文を実ファイルと照合する。この会話を受入試験へ流用しない。
5. T01〜T10を毎回新しい通常チャットで行う。回答全文と生成Robinを保存し、手直しせず専用PADフローへ貼り付け、保存・実行・成果物を照合する。
6. 失敗時は元回答を上書きせず、原因をナレッジ不足・参照失敗・指示不足・依存説明不足・PAD操作失敗に分類する。ナレッジや指示を変更した場合は最新版を新しいチャットへ再添付して再試験する。

7つを同時に完了確認できない場合は、`copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt` を使用してよい。これは7原本をファイル名・SHA-256付き区切りで機械的に結合したフォールバックであり、生成元と版を `copilot/knowledge-bundle-manifest-20260911c.json` に固定する。新bundleの最終試験では同じ結合版を使い続ける。

2026-09-10の添付・生成・PAD結果は旧bundleに結び付く履歴である。2026-09-11のP3追補統合版ではbundle SHAが変わったため、旧bundleの知識precheck、T04/T10、独立再試験、T01〜T07のPAD結果を新bundleへ継承しない。新bundleで同じ受入を再実行し、結果を別証跡へ保存する。ブラウザー拡張CUAの失敗は `catalog/evidence/m365-current-package-upload-block-20260910b.json` に分離する。

## 既存カタログとの対応

実測原文とSHA-256の正本は `../catalog/index.json` と `../catalog/actions/`、組合せフローは `../catalog/flows/`、検証証拠は `../catalog/evidence/`、既存生成例は `../catalog/generated/` にあります。`catalog/coverage.json` は左側一覧の観測範囲とA〜Gの不足を記録し、全アクション対応を表示しません。

## 状態

現作業版の追補判定（2026-09-10）：知識precheck、T01〜T07、T04/T10一次受入、T01/T04/T10独立再試験、未採取構文・UI依存のfail-closed負例はPASS。P3のBoolean・減算・日付減算・フォルダー作成probeも別証跡でPASSだがbundle未統合。T08は有効なRobin fenced blockを生成しない形式失敗、T09は既存専用フローのランタイムprobeのみ成功し、現行package Robin受入は未確認である。個別証跡とハッシュは `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` を正本とし、旧版結果は継承しない。

2026-09-11のP3追補統合後は、7原本・bundle・マニフェストを新SHAで固定しました。旧版の通常チャット生成・PAD結果は履歴として保持し、新bundleへ継承しません。新ハッシュでの知識precheck、T01〜T10、独立再試験が未完了のため、配布packageの受入完了とは扱いません。T04/T10の旧版差分は `catalog/evidence/normal-chat-raw-provenance-20260910.json` で発生段階を分離し、Agent Builder／Copilot Studioは今回の検証対象外です。
