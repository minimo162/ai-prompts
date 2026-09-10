# 通常M365 Copilotチャット受入試験 T01〜T10（継続中）

このフォルダーは、通常のMicrosoft 365 Copilotチャットへ最新版の指示文とナレッジ結合版を添付して行う受入試験の依頼文・期待値を固定する場所です。ここにある期待値は、生成回答に合わせて後から変更してはいけません。

## 実行前提

- 対象: ログイン済み通常M365 Copilotチャット。モデルは `GPT 5.6 Think Deeper` を明示選択する。Agent Builder／Copilot Studioは使わない。
- 入力: 各ケースで指定する合成データ、専用フォルダー、専用PADフロー。
- 手順: 新しい会話へ依頼 → 回答原文と生成コードを保存 → 手直しせずPADへ貼付け → 設定 → 保存・実行 → 成果物と期待値を照合。
- 失敗時: 元回答を上書きせず、原因分類と失敗位置を保存。指示・ナレッジを変更したら新しい会話で再試験。
- 以下の表は、指示文 `e467855137a1eec8655cfb6086f274e6a8e996412b3d07068f32c6912d9482c1`／bundle `431cdaa9c2ba34e217d848a0df0191d960608e04940674bca33f151cb1f62bc3` の履歴受入を保全したものです。原文保持規則を強化した現作業版は、指示文 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`／bundle `4282e4ece4f2d79ce26e85143fcab201091b185d9ee5d9defe4d8f49a4a7b2cd` で、T04は現作業版の通常チャット生成・無修正PAD受入までPASSしました。旧版のT01〜T03/T05〜T10生成・PAD結果を現作業版へ継承しません。T04/T10の差分発生段階は `catalog/evidence/normal-chat-raw-provenance-20260910.json`、結合版の再生成は `tools/Build-KnowledgeBundle.ps1` です。

## 固定ケース

| ID | 依頼の要点 | 固定した期待値 | 状態 |
|---|---|---|---|
| T01 | 日本語・引用符・`100%`・バックスラッシュを含む文字列を置換し、新しいUTF-8テキストへ保存 | 指定語だけ置換。特殊文字・改行・対象外文字を保持し、新規出力を確認 | PASS（最終版PAD 2回） |
| T02 | 日本語と引用符を含む合成CSVを読み、条件一致行だけ別CSVへ保存 | 条件一致行と列・引用符を保持。入力CSVは不変 | PASS（最終版PAD 2回） |
| T03 | 複数の合成ファイルをFor eachで処理し、名前または拡張子で分岐 | 各ファイルを一度ずつ処理。条件外は対象外経路。未採取のFor each構文を捏造しない | PASS（最終版PAD 2回） |
| T04 | Excel範囲を読み、条件一致行または集計結果を別ブックへ保存 | 指定範囲だけを読み、別ブックの期待セルと値を照合 | PARTIAL（最終生成の引用符差分、先行有効版はPASS） |
| T05 | 既存の合成Excelで指定セル／範囲だけ修正し、別名保存 | 指定セルだけ変更。無関係なセルと元ブックのハッシュを保持 | PASS（最終版PAD 2回） |
| T06 | 合成Wordの指定文字列を置換して別名保存（または採取済みPowerPoint生成例） | 指定箇所だけ置換し、本文・保存形式を照合 | PASS（最終版PAD 2回） |
| T07 | 合成PDFの指定ページのテキストを抽出して保存 | 指定ページ識別文字とページ対応を照合。ページ境界を推測で整形しない | PASS（最終版PAD 2回） |
| T08 | 存在しない入力ファイルを意図的に処理 | 期待したエラー経路・記録だけを確認し、依存する後続処理を実行しない | PASS（最終版の期待エラー） |
| T09 | 安全なローカル画面で文字入力→クリック→待機→文字取得 | 対象UI要素の登録手順と取得文字を明示。未確認セレクターを出さない | PARTIAL（UI要素捕捉・貼付けPASS、WebAutomation実行タイムアウト） |
| T10 | 動作確認済み既存フローを渡し、条件1つと出力名だけ変更 | 指定変更のみ反映し、既存の入力・変数・別処理・エラー経路を保持 | PARTIAL（最終版Word SaveAsで停止、独立再試験待ち） |

上表は履歴版の判定です。現作業版ではT04をPASS_CURRENT_REVISIONとし、同じT01〜T10の残りを新規通常チャットから再生成して無修正PAD貼付け・保存・実行・成果物照合まで行う必要があります。

現作業版の固定サマリは `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` です。

現作業版の追補：T01〜T07、T04/T10一次受入、T01/T04/T10独立再試験はPASS_CURRENT_REVISION。T08は生成形式失敗、T09はランタイムBLOCKED、負例は未実行です。

現作業版bundleのみを添付した知識precheckは `catalog/evidence/normal-chat-current-revision-knowledge-precheck-20260910.json` に保存し、ナレッジ固有の設定・型・依存を回答原文と照合しました。これは受入ケースの代用ではありません。

現作業版T10一次受入は `catalog/evidence/t10-current-revision-acceptance-20260910.json`、別チャット／別PADフローの独立再試験は `catalog/evidence/t10-current-revision-independent-acceptance-20260910.json` に保存しています。T01独立再試験は `catalog/evidence/t01-current-revision-independent-acceptance-20260910.json`、T04独立再試験は `catalog/evidence/t04-current-revision-independent-acceptance-20260910.json` に保存しています。

現作業版T10の生成・無修正PAD貼付け・保存・実行・Office成果物照合は `catalog/evidence/t10-current-revision-acceptance-20260910.json` に保存しています。独立再試験も別チャット／別PADフローでPASSしています。

現作業版T04の生成・貼付け・保存・2回実行・成果物照合は `catalog/evidence/t04-current-revision-acceptance-20260910.json` と `catalog/evidence/t04-current-revision-pad-paste-20260910.json` に記録しています。貼付けヘルパーの可視6件は仮想化による偽陰性であり、Designerの「9 アクション」表示を確認しました。

## 独立再試験

最終版を固定した後、T01・T04・T10をそれぞれ別の新しい会話で1回ずつ実施する。旧指示版でのT01独立正例は履歴として保持するが、現行版のT01独立受入は未完了。T04/T10独立再試験は現行版でPASS済み。初回結果と最終版結果を混ぜない。

現作業版では `catalog/evidence/pad-native-ui-blocked-20260910.json` のとおり、PADプロセスは起動したがnative Computer Use Trusted RPCが未構成である。T04はUIAフォールバックで正例の2回実行まで確認した。T09は `catalog/evidence/t09-runtime-block-20260910.json` のとおりUIA捕捉・貼付け・保存は確認したが、WebAutomation実行完了は未確認である。
