# Copilotエージェント用PAD Robin配布物

> 2026-09-12 最終監査: 固定finaldの生成受入は維持。A〜Gの一部の追跡証跡不足によりPR提出準備は未完了です。[監査結果](../docs/robin-knowledge-validation.md)。指示文・知識の受入済みバイトは変更していません。

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

2026-09-12の最終版（finald）bundle SHA-256は `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`、原本対応は [knowledge-bundle-manifest-20260912d.json](knowledge-bundle-manifest-20260912d.json) です。finalcとの差分はP3-1〜P3-6の実測統合（01-Basics: `SET NewVar TO CatalogList[1]`、`Text.ConvertDateTimeToText.FromCustomDateTime`／02-Control: If内If・入れ子ループ、`ON ERROR FileNotFoundError`／03-Files: 拡張子境界／04-Office: SaveAs上書き／06: 例8／00: 索引）。この版で知識precheck・T01〜T10・独立再試験・負例v2・P3正例P3-1〜P3-6を同一版受入済み（complete_live_acceptance_finald_20260912）。

（直前版）2026-09-12のfinalc bundle SHA-256は `f42f5acf4232b132b0a5b5bde469b25bf91d04f4cdb0a6823b17806d4ff85089`、原本対応は [knowledge-bundle-manifest-20260912c.json](knowledge-bundle-manifest-20260912c.json) です。直前版 `32aea4560df7a7530cd9fe1fab996181236ee8a0c34213adfffb3f022dbfc041` との差分はT09教材の待機値のみで、`WAIT 500`（500秒。2026-09-10採取時に500ミリ秒のつもりで設定した誤り）を、PADの待機ダイアログで1秒に直して再採取した `catalog/flows/ui-t09-local-roundtrip/roundtrip-wait1-20260912.robin` の `WAIT 1` に置き換えました（00-Index／05-UI-Web／06-Examples）。この版で、指示全文＋同版bundle添付の通常M365 Copilotチャット（Google Chrome、Think Deeper）により知識precheck、T01〜T10、独立再試験T01/T04/T10、負例N1〜N3を同一版で受入済みです。正本は `../catalog/evidence/current-package-status-20260912-finalc.json` と `../catalog/evidence/issue5-completion-audit-20260912-finalc.json`。

（履歴）2026-09-11のP3統合版bundleの原本対応は [knowledge-bundle-manifest-20260911h.json](knowledge-bundle-manifest-20260911h.json) に固定しています。マニフェスト自体をナレッジへ添付する必要はありません。

2026-09-11追補として、7原本へP3の実測根拠（真偽値・数値／日時演算、Else／Else-if／EXIT／NEXT、既定エラーハンドラー、PADで採取したGet last error、サブフロー、DataTable作成・行追加・セル更新・行反復、File.Exists／Folder.Create／Move／Rename、Excel範囲読取り・行反復、T09停止境界）を統合しました。失敗境界（カスタム日時書式、名前付きFileNotFoundルール、リスト取得、T09）は未確認として明記しています。最新bundle SHA-256は `dd668166e4c04b02878a6fae65e4583b6d6c910847559161c6707ae90e6626a5` です。新bundleの指示全文＋同版bundleによる知識precheckはPASS_REFERENCE_ONLY、T01〜T10全件・独立再試験・負例は未完了です。

Final3固定版のbundle SHA-256は `2bc3f2b4c5c709e94547ccf4b75f7084c9c424605781e01414f6783a1fd026a7` です。新規通常M365 Copilot送信と実PADでT01〜T08/T10を同版受入し、T01/T04/T10は独立再試験も完了しました。T09はUI要素捕捉・6アクション貼付け・保存・再コピーまでで、実行時のUI要素未検出によりRun開始前にブロックされています。P3未確認項目を含めて `partial／OPEN` を維持します。PAD空フロー作成権限とUIA復旧の観測手順は [docs/pad-live-setup.md](../docs/pad-live-setup.md) にまとめています。

ナレッジは技術資料であり、指示欄と同じ優先順位の命令書ではありません。`pad-robin-prompts.md` は既存の編集用原稿として残し、配布版と二重に指示欄へ貼りません。

`agent-instructions.txt` の現作業版は UTF-8 BOMなし、UTF-16コード単位数3,949（10,096バイト）で、8,000文字上限以内です。結合版は `tools/Build-KnowledgeBundle.ps1` で7原本から機械的に再生成します。現作業版の指示SHA-256は `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`、P3追補を含むbundle SHA-256は `dd668166e4c04b02878a6fae65e4583b6d6c910847559161c6707ae90e6626a5` です。旧bundleの生成・PAD結果を新bundleへ継承せず、新ハッシュで知識precheckとT01〜T10を再受入します。T10既存フロー修正では、元行の文字列・矢印・バックスラッシュ・アンダースコアを確認できない場合はコードを出さず、手編集で差分を隠しません。

## 通常チャット検証手順

1. ログイン済みのMicrosoft 365 Copilotで新しい通常チャットを開く。Agent Builder／Copilot Studioは開かない。
2. `agent-instructions.txt` の全文、短い添付資料参照案内、試験依頼を本文へ入力し、入力後の本文が全文であることを確認する。
3. 上記7つの `.txt` を実ファイルとして添付し、添付一覧・SHA-256・送信メッセージとの対応を記録する。ファイル名やローカルパスの記載だけでは添付済みとしない。
4. 事前確認用の別チャットで、答えを質問文に含めず、設定差分・型・依存を質問し、回答原文を実ファイルと照合する。この会話を受入試験へ流用しない。
5. T01〜T10を毎回新しい通常チャットで行う。回答全文と生成Robinを保存し、手直しせず専用PADフローへ貼り付け、保存・実行・成果物を照合する。
6. 失敗時は元回答を上書きせず、原因をナレッジ不足・参照失敗・指示不足・依存説明不足・PAD操作失敗に分類する。ナレッジや指示を変更した場合は最新版を新しいチャットへ再添付して再試験する。

7つを同時に完了確認できない場合は、`copilot/knowledge/PAD-Robin-Knowledge-Bundle.txt` を使用してよい。これは7原本をファイル名・SHA-256付き区切りで機械的に結合したフォールバックであり、生成元と版を `copilot/knowledge-bundle-manifest-20260911h.json` に固定する。新bundleの最終試験では同じ結合版を使い続ける。

2026-09-10の添付・生成・PAD結果とFinal3固定版は履歴として保全する。2026-09-11のP3追補統合版ではbundle SHAが変わったため、旧bundleの知識precheck、T04/T10、独立再試験、T01〜T07のPAD結果を新bundleへ継承しない。新bundleで同じ受入を再実行し、結果を別証跡へ保存する。ブラウザー拡張CUAの失敗は `catalog/evidence/m365-current-package-upload-block-20260910b.json` に分離する。

## 既存カタログとの対応

実測原文とSHA-256の正本は `../catalog/index.json` と `../catalog/actions/`、組合せフローは `../catalog/flows/`、検証証拠は `../catalog/evidence/`、既存生成例は `../catalog/generated/` にあります。`catalog/coverage.json` は左側一覧の観測範囲とA〜Gの不足を記録し、全アクション対応を表示しません。

## 状態

現作業版の追補判定（2026-09-11）：Final3固定版のT01〜T08/T10、T01/T04/T10独立再試験、負例、T09停止境界は保全済み。P3のDataTable行追加・セル更新・行反復とExcel行反復は専用probeの無修正2回成功を教材へ統合した。新bundleは指示全文＋同版bundleの知識precheckとT01一次受入までPASSし、T02〜T10・独立再試験・負例は未完了である。カスタム日時書式、リスト取得、名前付きカスタムエラー一致、T09通し実行は未確認として保持する。

2026-09-11のP3追補統合後は、7原本・bundle・マニフェストを新SHAで固定しました。旧版の通常チャット生成・PAD結果は履歴として保持し、新bundleへ継承しません。新ハッシュの指示全文＋同版bundleによる知識precheckはPASS_REFERENCE_ONLYですが、T01〜T10、独立再試験、負例が未完了のため、配布packageの受入完了とは扱いません。T04/T10の旧版差分は `catalog/evidence/normal-chat-raw-provenance-20260910.json` で発生段階を分離し、Agent Builder／Copilot Studioは今回の検証対象外です。
