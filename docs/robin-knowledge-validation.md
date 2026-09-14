# Robinナレッジ検証報告
## 2026-09-14 集約訂正・現行負例v2受入

P3-1〜P3-6の現行版個別証跡はすべて同版指示・bundleに結び付き、派生集約のP3-4〜P3-6未受入表示を訂正した。63桁SHAの原記録は変更せず、訂正根拠と参照を`catalog/evidence/p3-current-sha-correction-20260914e.json`へ残した。固定負例v2（N1〜N3）は通常M365 Copilot新規会話へ1回送信し、回答原文を無修正保存した。三項目とも未確認受入で、理由・必要証拠・禁止後続処理を満たし、コードフェンス・Robin命令・疑似コード・未採取アクション名／引数の推測はない。PAD貼付け・Run・未登録Web操作は行っていない。旧finald負例PASSは履歴のまま現行版へ移していない。残件はT04形式不受入・独立T04候補partial、T10厳密保持NOT_PROVEN、A〜G監査であり、Issue #5/#27はOPEN / partialを維持する。

## 2026-09-14 独立T04候補の実行別証跡追跡補完

独立T04候補の既存ファイルを上書きせず、生成・貼付け保存・再コピー・Run1/Run2・Run2 xlsxの各SHAと参照を`catalog/evidence/t04-independent-current-evidence-reconciliation-20260914e.json`へ集約した。現行指示／bundle／manifestへの結び付き、生成Robin `dd4f39f0…43569d`（plain `=>` 5、escaped `\\=>` 0）、PAD権威9アクション（ListItem 6件は仮想化表示）、入力SHA不変を機械テスト `tests/Test-T04IndependentEvidence.ps1`（61 checks）で確認した。

Run1/Run2はともに成功したが、Run1のxlsxは`NOT_CAPTURED`であり、Run2の3行（対象/A/10、対象/C/25、対象/D/5）をRun1の結果へ付け替えていない。最大2回を事前固定した新規空フロー `RobinKnowledgeT04IndependentCurrentOutputComparison20260914eR1` は作成できたものの、Designer PID 44316はHWND 0・完全一致タイトル未観測でUIA rootを取得できなかったため、貼付け・実行を開始していない。保存済みRobinの再送・手修正・第3回Run・空フロー削除は行わず、候補は`candidate_partial`、Issue #5/#27はOPEN / partialのままとする。次回は正確な非0 HWND／タイトルを観測した場合のみ、無修正Robinを使って各Run前にxlsxを捕捉する。

その後の再確認（`2026-09-14T14:07:13+09:00`）も、同じPID 44316が応答中ながらHWND 0・タイトル空、UIAトップレベル0件であることを確認した。Designerログ（SHA `3435c1aeb5c0441620c259eea4775d81175d8c110c1480d31c49298e843a4a34`、165328 bytes）には`flowId`／`scriptId`がall-zero、`isHiddenInstance=true`、`canCreateFlow=false`が記録されている。これは `catalog/evidence/t04-independent-current-pad-window-observation-20260914f.json` に原ログ参照とともに保存し、不可視・未バインドDesignerに対して貼付け・保存・Runを呼び出していないことを検証テストへ追加した（70 checks）。

## 2026-09-14 現行版P3-1の送信・実機PAD受入

現行正本20260913e（instruction SHA `6ad6f742…`、bundle SHA `79245787…`、manifest `copilot/knowledge-bundle-manifest-20260913e.json`）を、通常M365 Copilotの新規会話 `https://m365.cloud.microsoft/chat/conversation/2167fd22-b6fb-4101-9379-8f4e760a518a`へ同版指示全文とbundleを実添付してThink Deeperで1回送信した。評価者用正解コード・期待値・Issue本文は送っていない。回答DOMの単一コードブロックから4行Robinを無修正保存した。

生成Robin `catalog/generated/normal-chat-20260914e-p31-current-live/generated-robin.txt`（205 bytes、SHA `fdaa3eea…`）を、Console UIAで作成した専用空フロー `RobinKnowledgeP31CurrentBundleLive20260914e`（Designer PID 11016）へ無修正貼付け・保存・再コピーした。PAD再コピーは209 bytes／CRLF（SHA `36a8179b…`）で、改行正規化後のみ一致し、生バイト差を隠していない。2回Runとも成功し、各回の変数プレビューで`CatalogList=[CatalogItem, SecondItem]`、`NewVar=SecondItem`を確認した。原回答・依頼・PAD貼付け保存・Run記録は `catalog/evidence/p31-current-bundle-live-20260914e.json` と同参照ファイルへ分離保存した。

これは現行版P3-1だけの受入記録であり、旧版P3-1 PASSを現行版へ移していない。続くP3-2、P3-3は別節で現行版受入を記録する。P3-4〜P3-6、負例v2、T10厳密保持、最終A〜G監査は未完了のため、Issue #5/#27をOPEN / partialのまま維持する。

## 2026-09-14 現行版P3-2の送信・実機PAD受入

現行正本20260913e（instruction SHA `6ad6f742…`、bundle SHA `79245787…`）を通常M365 Copilot新規会話 `https://m365.cloud.microsoft/chat/conversation/cc53abdf-077f-40eb-873e-f0ef92056be4`へ同版指示全文＋bundleを実添付し、Think Deeperで1回送信した。評価者用正解コード・固定期待値・Issue本文は渡していない。応答DOMの単一`pre`から23行Robinを無修正保存した。

生成Robin `catalog/generated/normal-chat-20260914e-p32-current-live/generated-robin.txt`（1057 bytes、SHA `3189a4c7…`）を専用空フロー `RobinKnowledgeP32CurrentBundleLive20260914e`へ貼付け・保存した。貼付け直後のListItem 6件は仮想化表示で、Designerの権威サマリー`23 アクション`を確認した。再コピー `pad-recopy.robin`（1080 bytes、CRLF、SHA `b2c65f7e…`）は生成原文と生バイトは異なるが、改行正規化後は一致する。生成コードの手直し・unescape・後付け期待値は行っていない。

PADを2回Runし、両回とも変数プレビュー`[CatalogItem, SecondItem, ThirdItem]`、`SecondItem`、`1`、`1`、`SecondItem`、`2`を確認した。指定出力は13 bytesのUTF-8 BOM付き`SecondItem`（SHA `e9b8ede4…`）で、`OuterCount=2`、`InnerNo=1`、`InnerYes=1`、`LastSeen=SecondItem`、ThirdItem未訪問の期待と一致する。run1はDesigner PID 39172、run2は再オープン後PID 23188で、各Runの原JSONを保存した。

この受入は現行版P3-2だけを対象とし、旧20260912 P3-2 PASSを移していない。P3-4〜P3-6、負例v2、T10厳密保持、最終A〜G監査は残件で、Issue #5/#27はOPEN / partialを維持する。詳細は`catalog/evidence/p32-current-bundle-live-20260914e.json`および同参照のpaste/run証跡を参照する。P3-3は次節で別途現行版受入を記録する。

## 2026-09-14 現行版P3-3の送信・実機PAD受入

現行正本20260913e（instruction SHA `6ad6f742…`、bundle SHA `79245787…`、manifest `copilot/knowledge-bundle-manifest-20260913e.json`）を通常M365 Copilotの新規会話 `https://m365.cloud.microsoft/chat/conversation/8e3e9a69-098f-41ce-82df-47b581c6bbad`へ同版指示全文とbundleを実添付してThink Deeperで1回送信した。評価者用正解コード・固定件数・期待値・Issue本文は渡していない。応答DOM単一`pre`から13行Robinを無修正で保存し、生成SHAは`2b3494e4e8ceffd33e8ef242b19387205b8159d2307ad8a56f93aeb789e3454a`である。

生成Robin `catalog/generated/normal-chat-20260914e-p33-current-live/generated-robin.txt`（808 bytes）を、Console UIAで作成した専用空フロー `RobinKnowledgeP33CurrentBundleLive20260914e`（Designer PID 38136）へ無修正貼付け・保存・再コピーした。貼付け後のListItem 7件は仮想化表示で、Designerの権威サマリー`13 選択されたアクション`を正とした。PAD再コピー `pad-recopy.robin` は821 bytes・CRLF（SHA `e909a165…`）で、生成原文とは生バイトが異なるが改行正規化後は一致する。貼付けヘルパーの初回JSONはプロセス終了までに出力されなかったが、同じ1回の貼付け状態を独立UIAで確認し、重複貼付けは行っていない。

PADを2回Runし、両回とも`TxtCount=3`、`OtherCount=2`、`CurrentFile=...\\sub.txt\\inner.txt`、`OtherSeen=...\\x.txt.bak`、`FileContents=inner`を確認した。5入力fixture（plain.txt、upper.TXT、x.txt.bak、sub.txt/inner.txt、nested/deep.txt）の各SHAは両Run後も不変で、`.TXT`は厳密な`.txt`比較のElse、`.txt.bak`もElse、親フォルダー名`sub.txt`は拡張子判定へ影響しないことを実測した。これは現行版P3-3の生成・無修正PAD貼付け・保存・2回機能受入であり、厳密な生成→PAD生バイト保持、NoSort順序、閉じて再オープン後の再コピーまでは証明していない。旧P3-3 PASSは移転せず、P3-4〜P3-6、負例v2、T10厳密保持、最終A〜G監査は残件で、Issue #5/#27はOPEN / partialを維持する。詳細は `catalog/evidence/p33-current-bundle-live-20260914e.json` とpaste/run証跡。

## 2026-09-14 現行版P3-4の送信・実機PAD受入

現行正本20260913e（instruction SHA `6ad6f742…`／bundle SHA `79245787…`）を通常M365 Copilot新規会話 `b9376b28-b208-4f56-a79d-05758849de9f`へThink Deeper・2実添付で1回送信した。評価者用件数・期待値は渡さず、DOM単一`pre`から4行のExcel SaveAs Robinを無修正保存した。専用空フロー `RobinKnowledgeP34CurrentBundleLive20260914e`（Designer PID 30620）へ貼付け・保存・再コピーし、権威サマリー`4 選択されたアクション`を確認した。再コピーはCRLF正規化後のみ一致し、生バイト一致は主張しない。

Run1/Run2とも成功し、各xlsxスナップショットのB2=`T05-Changed`を確認した。Run1前の出力は不在、Run2前にはRun1出力が存在し、Run2後に出力SHAが`5342fa57…`から`4b41bd36…`へ変化したため既存ターゲットの無警告上書きを実測した。入力`excel-catalog.xlsx`のSHA `e94bd14c…`は前後不変。生成・貼付け・2回実行の原記録は `catalog/evidence/p34-current-bundle-live-20260914e.json`、paste/run各JSON、`catalog/generated/normal-chat-20260914e-p34-current-live/`に保全した。P3-4は現行版受入へ追加するが、P3-5/P3-6、T04形式、T10厳密保持、負例v2、A〜G監査は未完了で、Issue #5/#27はOPEN / partialを維持する。

## 2026-09-14 独立T10現行版の機能受入

現行正本20260913e（instruction SHA `6ad6f742…`、bundle SHA `79245787…`、manifest `copilot/knowledge-bundle-manifest-20260913e.json`）を通常M365 Copilotの新規会話 `https://m365.cloud.microsoft/chat/conversation/6edc277b-b005-4d56-8bb7-ba64668ea636`へ、同版指示全文とbundle・生成元Robinの3実添付でThink Deeper送信した。送信は1回で、評価者用正解コード／期待値／Issue本文は渡していない。応答DOMは単一16行Robin（`catalog/generated/normal-chat-20260914e-t10-independent-live/dom-robin.txt`、SHA `2bcb5512…`）で、生成元との差は許可したExcel A1値とSaveAs先の2行だけ（改行を除く範囲外差分0）。

Console UIAの新規フロー経路で `RobinKnowledgeT10IndependentCurrentBundleLive20260914e`（Designer PID 20008、タイトル完全一致）を作成し、DOM Robinを無修正で貼付け・保存・再コピーした。初回貼付けヘルパーは60秒時点でListItem 6件のためタイムアウトしたが、同じ貼付けの後続状態でDesigner集計 `16 アクション` が現れたため再送しなかった。保存後／Run2後の再コピーは同一SHA（CRLF・末尾LF）で、生成Robinとは正規化後のみ一致する。

2回Runとも成功し、各Run前に出力を専用`.work`へスナップショットした。Run1/2ともExcel A1=`T10-Changed`、Word本文=`CopilotOffice 246`、PowerPoint本文=`CopilotOffice 246`を確認し、元のExcel/Word/PowerPoint出力はバックアップSHAへ復元した。これはT10の機能実行と許可内容範囲の受入である。入力元（CRLF・末尾LFなし）→生成（LF・末尾LFあり）→PAD再コピー（CRLF・末尾LFあり）の生バイト一致は成立せず、改行正規化や復元による厳密PASS化は行わない。厳密保持は`NOT_PROVEN`として残し、詳細は`catalog/evidence/t10-independent-current-generation-20260914e.json`、`catalog/evidence/t10-independent-current-pad-*.json`、`.work/t10-independent-20260914e/run1`／`run2`。Issue #5/#27はOPEN / partial。

## 2026-09-14 独立T04の生成形式補正候補

T04の元試行3でDOMと保存Robinに`=>`前literalバックスラッシュが現れた原因を生成回答由来として保持したまま、同版の別仮説を検証した。現行正本20260913e（instruction SHA `6ad6f742…`、bundle SHA `79245787…`）を新規Think Deeper通常チャットへ同版指示＋bundle実添付し、評価者用の件数・期待値を依頼本文へ渡さない補正版依頼を1回だけ送信した。公式応答（SHA `a932e7e7…`）とDOM単一`pre`（Robin SHA `dd4f39f0…43569d`、9行、plain `=>` 5、escaped `\\=>` 0）を無修正で保存した。

新規空フロー `RobinKnowledgeT04IndependentCurrentBundleLive20260914eD`（PID 29660）へ貼付け・保存・再コピーした。アクション一覧は仮想化で表示6件だったが、Designer集計 `9 選択されたアクション` と再コピー9行を正としたため、`tools/Paste-PadRobinLiveByStatus.ps1` をローカライズされた集計ラベルと60秒待機へ最小修正した。無修正貼付け・保存後再コピー（CRLF正規化後一致）を確認し、2回Runとも成功。Run2 xlsxは3行3列（対象/A/10、対象/C/25、対象/D/5）で、入力fixture SHAは不変、元のT04 CSV/xlsxは復元した。

Run1のxlsxスナップショットはRun2前に取得できず、追加3回目は行わなかった。したがって本件は `PASS_CURRENT_20260914E_INDEPENDENT_T04_GENERATION_PAD_TWO_RUNS_PARTIAL`／`candidate_partial` に限定し、独立T04の完全受入や元T04の昇格とはしない。厳密な入力→生成バイト保持も`NOT_ASSESSED`。詳細証跡は `catalog/generated/normal-chat-20260914e-t04-independent-live/`、`catalog/evidence/t04-independent-current-output-comparison-20260914e.json`、paste/save、recopy、run1/run2各JSON。

## 2026-09-14 T08現行版生成・PAD受入

現行正本20260913e（instruction SHA `6ad6f742…`、bundle SHA `79245787…`、manifest `copilot/knowledge-bundle-manifest-20260913e.json`）を新規通常M365 Copilotチャット（Think Deeper、同版指示＋bundle実添付、会話 `https://m365.cloud.microsoft/chat/conversation/4b3b4dfc-8fb9-4d0c-a5de-3427be8a00eb`）へ送信した。固定依頼SHAは `79070940…`、送信本文SHAは `72b55f32…`。回答原文2,635文字（SHA `60191af3…`）と単一12行Robin（末尾LF除外SHA `d4a6b697…`）を無修正で保存した。生成回答の形式はT04の矢印エスケープとは異なり、DOM `pre.textContent` と一致した。

Robinを新規専用空フロー `RobinKnowledgeT08CurrentBundleLive20260914e`（Designer PID 35772、4アクション）へ無修正貼付け・保存・再コピーし、2回Runとも成功した。両回ともアクション単位 `ON ERROR FileNotFoundError` で `NewVar=named`、`LastError` に欠損メッセージ、ブロック側 `ErrorHandled`／`ErrorHandledDefault` は未設定。欠損入力は前後とも不在で、書込み・完了マーカー・公開処理は発生しなかった。再コピーのBLOCK末尾空白差は原記録のまま保持し、正規化後一致だけを確認した。ブロック側利用者定義 `FileNotFound` の一致はNOT_PROVENであり、アクション単位の実測から一般化していない。証跡は `catalog/evidence/t08-current-bundle-live-acceptance-20260914e.json`、`catalog/evidence/t08-current-bundle-output-comparison-20260914e.json`。

旧finald PASSは現行版へ付け替えていない。現行版受入済みはT01/T02/T03（修正版依頼）/T05/T06/T07/T08/T09、P3-1/P3-2/P3-3、独立T01、独立T10の機能／許可範囲。T04形式不受入、T10厳密バイト保持 `NOT_PROVEN`、独立T04、P3-4〜P3-6、負例v2、A〜G全体監査は残り、Issue #5/#27はOPEN / partialとする。

## 2026-09-14 T06現行版生成・PAD受入

20260913e正本（instruction SHA `6ad6f742…`、bundle SHA `79245787…`、manifest `copilot/knowledge-bundle-manifest-20260913e.json`）をThink Deeperの通常M365 Copilot新規会話 `https://m365.cloud.microsoft/chat/conversation/efc8983a-0075-4040-833a-8f06183823b4`へ、指示全文とbundleの実添付で送信した。生成された4行Robin（SHA `c0940cb3e3ddbd82880d274692858ce3e2335f623acb11abe521926e642f9fd9`、593 bytes）は無修正で新規専用空フロー `RobinKnowledgeT06CurrentBundleLive20260914e`（Designer PID 34264、HWND 397164）へ貼付け・保存・再コピーした。PAD再コピーはCRLF（597 bytes）だが、生成原文との改行正規化後一致を確認した。

同フローを2回Runし、両回ともReady復帰・Start有効・エラーなし・`Word インスタンス`プレビューを確認した。合成Word本文は入力 `OfficeCatalog 日本語 100%` から出力 `T06Replaced 日本語 100%` となり、`OfficeCatalog` 0件、`T06Replaced` 1件、指定置換以外の本文一致、入力SHA `2753855b…` 不変、Wordプロセス0を直接照合した。Run 1/2のdocxパッケージSHAは異なるため、本文結果の受入であり厳密な入力→生成→PADバイト保持は主張しない。既存の同名出力は各Run前に退避し、Run後に元SHAで復元した。証跡は`catalog/evidence/t06-copilot-live-generation-20260914e.json`、`catalog/evidence/t06-copilot-live-generation-20260914e-pad-acceptance.json`、`catalog/evidence/t06-20260914e-output-comparison.json`。

旧finaldのT06 PASSは履歴として保持し、今回の現行版受入へ移していない。T04の生成形式不受入、T10厳密バイト保持、独立再試験、P3正例、負例v2、A〜G全体監査は残り、Issue #5/#27はOPEN / partialとする。

## 2026-09-14 T05現行版追跡昇格（新規自動名フロー）

20260913e正本（instruction SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`）でT05生成を追跡した。初回回答の矢印前literalバックスラッシュは原記録として不受入保存し、同じ会話の許可済み1回リトライで取得した4行Robin（SHA `be40e6b337620f1c76ba650b202f316d4b80b339de1c859fe1cb55a9f2714911`）だけを無修正で使用した。指示・bundle実添付、依頼SHA、失敗原文は `catalog/evidence/t05-copilot-live-generation-20260913.json` から追跡できる。

PADでは新規空フローへ貼付け・保存・再コピーし、2回Runとも成功。合成ExcelのB2=`T05-Changed`、A1不変、入力SHA `e94bd14c919375c76e7114f63031a18a7317a1ce15b55ce99e487fac9ddbbad6` 不変、出力比較PASSを確認した（`catalog/evidence/t05-copilot-live-generation-20260913e-pad-acceptance.json`）。作成ダイアログの名前入力が利用可能UI経路で設定できず、フロー名は自動名 `無題 (2)` となった。新規作成・既存フロー非再利用は記録したが、明示的な人手命名を受入条件とする場合は、同じ生成Robinを編集せず、新しい一意名の空フローでPAD貼付け・2runだけを再実施する。

旧finald PASSは移していない。T04生成形式不受入、T10厳密保持`NOT_PROVEN`、P3、負例、A〜G全体監査は残し、独立T10の機能／許可範囲のみ現行版へ追加した。Issue #5/#27はOPEN / partialとする。

## 2026-09-14 T03現行版追跡昇格（修正版依頼のみ）

20260913e正本（instruction SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`、manifest `copilot/knowledge-bundle-manifest-20260913e.json`）と一致するT03候補証跡を、現行版の修正版依頼受入として追跡した。依頼本文へ固定期待の`TxtCount`／`OtherCount`要件を明示しただけで、指示・知識・fixture・期待値・既存3試行原記録は変更していない。Copilotへ期待数値は渡していない。

生成Robin（13行、SHA `63fe35ec8619387f08c5dd270eb226bbd944457b410e09cc2425023ff9396572`）は無修正で専用空フロー `RobinKnowledgeT03Revised20260913` へ貼付け・保存し、2回Runとも成功。`TxtCount=2`／`OtherCount=2`、`FileContents=alpha 日本語`、4入力fixture不変、PAD再コピーのCRLF正規化後一致を確認した。閉じて再オープン後の再コピーは未実施として残す。派生証跡は `catalog/evidence/t03-copilot-live-generation-20260913e-pad-acceptance.json`。

これは修正版依頼に限る現行版追跡であり、元依頼（カウンター要件が本文から観測できない）や元3試行のPASSではない。T03の旧finald PASSは移していない。T04の応答由来literalバックスラッシュ不受入、T10厳密保持`NOT_PROVEN`、P3、負例、A〜G全体監査は維持し、独立T10の機能／許可範囲は別証跡で受入した。Issue #5/#27はOPEN / partialとする。

## 2026-09-13e T01生成追跡

現行正本の保存済み固定本文（`.work/finale-20260912/t01/sent-body.txt`、4,393文字／11,022 bytes、WAIT 1=1、WAIT 500=0）を新規通常M365 Copilotチャット`https://m365.cloud.microsoft/chat/conversation/f5106564-f9a6-4665-9b09-bd0eca6e6d01`へ送信し、回答全文2,309文字と1つのRobinコードブロック（646 bytes）を無修正で採取した。生成Robinを専用空フロー `RobinKnowledgeT01CurrentBundleLive_20260913e` へ無修正貼付け・保存・再コピーし、2回Run（成功、出力SHA一致、入力SHA不変）まで現行版で受入した。証跡は`catalog/evidence/t01-copilot-live-generation-20260913e.json`、`catalog/evidence/t01-copilot-live-generation-20260913e-pad-acceptance.json`、`catalog/evidence/t01-copilot-live-generation-20260913e-pad-output-comparison.json`。PAD再コピーはLF→CRLFの正規化一致として記録し、生成元からPADまでの厳密バイト一致は主張していない。

## 2026-09-13 T10機能実行・厳密保持の派生監査

既存のT10原記録（入力 `catalog/generated/office-three-apps/generated.robin`、生成DOM Robin、PAD再コピー、2回Run）を変更せず、`catalog/evidence/t10-strict-preservation-audit-20260913.json` と `tests/Test-T10StrictPreservation.ps1` で判定を分離した。機能実行は既存の2回RunとOffice成果物照合により `PROVEN_SEPARATELY`、命令内容の差分は許可された2行目（Excel A1）と4行目（SaveAs先）だけで、変更範囲外の14行は正規化後の内容として一致した。

一方、入力はCRLF・末尾改行なし、生成RobinはLF・末尾改行あり、PAD再コピーはCRLF・末尾改行ありで、source→generation、source→recopy、generation→recopyの生バイトSHAは一致しない。generation→recopyはCRLF正規化後の内容一致に限定して `PROVEN_NORMALIZED_CONTENT_ONLY` と記録し、入力から生成への厳密バイト保持は `NOT_PROVEN` のまま昇格していない。回帰テストは `PASS_REGRESSION_WITH_STRICT_NOT_PROVEN`（ソース修正・自動unescape・期待値変更なし）である。従来の受入JSONにある`strict_reproduction=PROVEN`はこの正規化後再コピーの意味を超えて解釈しない。

## 2026-09-12 進捗成果のmain反映

利用者の別途明示指示により、ここまでのコミット済み成果を進捗PRとして提出・squashマージする。対象は `7c26038a4daf0907c9692b788c780674cc618373` までの成果と本追記、基準mainは `de5efc1a525db0d49b4af9aa6cd6ec674ef9b4e8`。以下の「未push／PR未準備」は各時点の履歴であり、完全受入の不足判定は維持する。マージ結果はPRとIssue #5/#27に記録する。

これはfinald最終監査の完全合格やfinale配布版への昇格を意味しない。配布正本・旧版PASSは据え置き、T10厳密保持、B/C/D/Eの限定追跡不足、finale独立T10・P3正例・負例v2・最終統合監査は未完了。両Issueはクローズしない。

`.work/finale-20260912/`の候補・回答・実行原記録はローカル限定で保全し、今回のPRには含めない。本文中の同パス参照はリモートレビュー可能な原証跡ではなく、候補の受入昇格には必要な原記録の選別・ハッシュ照合・追跡追加が必要。次の単一作業はMain/P3Workerの別空フロー再利用。貼付け・各1アクションの再コピーまで取得したが、単一Main専用観測器が2サブフローを拒否し実行要求前に停止。run記録はなく、PASSには数えない。PAD全体の故障とは扱わない。

## 2026-09-13e 正本固定と実機precheck

T09の配布指示行39に残っていた`WAIT 500`（秒）を、実測知識と`docs/pad-live-setup.md`の単位に合わせて`WAIT 1`へ最小修正した。変更後の正本は指示SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`、manifest `copilot/knowledge-bundle-manifest-20260913e.json`である。旧finaldの指示SHA `b4a3c24f…`に対する生成・PAD受入は履歴として保持し、新版本へ移していない。

同版の通常M365 Copilotチャット（Google Chrome、Think Deeper、指示全文＋bundle実添付）を新規会話`https://m365.cloud.microsoft/chat/conversation/f1efa8e2-0c54-4797-81d5-fcb45e1c0302`で送信した。回答は参照要約のみ（Robinコード0ブロック、回答DOM 4,460文字、SHA `8cc646cce609a3b4fcdffc317b2c4a908c783ecf3948b595c56c4cda4a43b420`）で、リスト添字1、EXIT/NEXTの最近接ループ、拡張子境界、SaveAs上書き、`yyyy-MM-dd`、アクション単位`FileNotFoundError`と未確認境界を引用した。証跡は`catalog/evidence/current-bundle-20260913e-precheck.json`。これは`PASS_REFERENCE_ONLY`であり、生成Robin／PAD貼付け／実行の受入ではない。

指示バイトが変わったため、20260913eのT03〜T08／T10、独立T01/T04/T10、P3正例、負例v2は未実施として残す。T01は同版通常チャット生成後、専用空フロー`RobinKnowledgeT01CurrentBundleLive_20260913e`へ無修正3行貼付け・保存・再コピー→2回Runを実施し、出力SHA一致・入力SHA不変まで確認した（`catalog/evidence/t01-copilot-live-generation-20260913e-pad-acceptance.json`）。T02は同版通常チャット生成後、専用空フロー`RobinKnowledgeT02CurrentBundle_20260913`へ3行を無修正貼付け・保存・再コピー→2回Runを実施し、CSV出力一致・入力SHA不変を確認した。これは9/13に取得済みの候補原記録を現行版へ追跡昇格した派生証跡であり、再送・再Run・期待値変更は行っていない（`catalog/evidence/t02-copilot-live-generation-20260913e-pad-acceptance.json`）。T09は同版の通常チャット生成後、専用空フロー`RobinKnowledgeT09CurrentBundleLive20260913e`でControlRepository登録→登録6アクション削除→生成6行の無修正貼付け・保存→再コピー→2回Runを実施し、両回`T09-clicked`、Ready、エラーなし、PAD起動Edge残存なしを確認した（`catalog/evidence/t09-20260913e-pad-acceptance.json`）。初回30秒ヘルパー試行は実行中のまま証跡を出さず、完了後も受入回へ数えず、状態確定後に2回を取り直した。T03補正依頼の2run成功は同一SHAの候補追跡として保持し元依頼の受入へ付け替えず、T04の応答由来エスケープ不受入、T10厳密保持`NOT_PROVEN`も維持する。Issue #5/#27はOPEN／partialのままとする。

今回の提出前確認：CurrentStatus46項目PASS。検査コード不変の直前非ライブAll36/36 PASSを再利用し、今回の再実行とはしない。監査修正差分のdiff --checkはPASS、基準mainからの全差分では原証跡2行の末尾空白を保全する。DOMはNOT_RUN、GitHub CIはPRの実際の状態を別途確認する。保護未追跡資料はSHA e0ea487e66b2f62303097cd580c9caeeffd80a3da08954ce35608b6a043e2699のまま保持する。

## 2026-09-13 PAD別空フロー再利用（B/C/D/E）

PADを実機で起動し、固定した別空フローへ既存のraw Robinを無修正で貼付け、保存、2回実行、保存後再コピーまで進めた。Bは`RobinKnowledgeSubflowReuse_20260913_1534`でMain／P3Workerを再配置し、両runとも`ButtonPressed=OK`、Ready、errors=0を確認した。終了後にConsoleから再オープンした新PIDでMain／P3Workerの各1アクションを再観測し、再コピーを取得した（`catalog/evidence/p3-subflow-reuse-20260913-reopen-recopy.json`）。観測器はP3Worker選択後もRun状態を読むよう補完し、1回目・2回目ともPAD DataCollectionの`robin.execution.success`と`OK`プレビューを別々に記録した。実行結果JSONは`catalog/evidence/p3-subflow-reuse-20260913-run1.json`／`run2.json`に固定している。

Cは行追加・セル更新・行反復、Dは存在確認・移動・名前変更、EはExcel行反復をそれぞれ専用別空フローで実行した。C行は2行3列と最終`B / 20 / 対象2`、Cセルは列2／行0の`CellChanged`とDataTable=1行3列、C反復は2行3列の最終行を両runで確認した。D移動・名前変更は初回成功後にsourceを復元し、2回目の`DoNothing`で出力リスト`[]`、source／destination（またはtarget）同一ハッシュを確認した。Dの合成入力は各run後に元の存在状態へ復元した。Eは`ExcelData=6行, 3列`、最終行`対象外 / E / 40`、Excelインスタンス終了を両runで確認した。各raw再コピーはPADのCRLF化のみで、LF原文との差を内容一致として正規化していない。

対応するpaste/save、run1／run2、recopy、衝突状態の証跡は`catalog/evidence/p3-*-reuse-20260913-*`に固定し、`catalog/index.json`と`catalog/coverage.json`から追跡できる。これは別空フローprobeの前進であり、現行bundleの同一版Copilot/T01-T10再受入、T10厳密改行保持、Bの名前付きFileNotFoundルール一般化、G/T09の残件を完了扱いにはしない。D File.Existsでは初回にアクション数期待値を1とした試行が2項目（IF＋END）で停止したため、再試行フローで正しい2項目を貼付けて採取し、失敗試行を成功証跡へ付け替えていない。

## 2026-09-12 finald保存証跡の最終監査

### 監査後の継続: finale候補（未受入・未昇格）

**A真偽値・Dフォルダー作成の不足補完:** 既存採取原文をそれぞれ新しい空フローへ無修正で貼付け、2回の固定期待照合と保存後再オープン再コピーを確認した。`a-boolean-reuse-20260912/acceptance.json`はP3Bool=Trueを08:06:15Z／08:06:57Zの2runで確認。両回のstatus ambiguousは同じ実行の観測継続でready/errors0へ到達し、再実行要求なし。短いrunning表示は未捕捉として残す。

`d-folder-create-reuse-20260912/acceptance.json`は08:13:17Z／08:17:49Zの2runで対象不在からの新規作成、実行要求後の作成時刻、NewFolderの指定パス、ready/errors0を確認した。元の合成空フォルダーは各回前に退避し、各回後に元の作成時刻を保持して復元。2回目の最初の準備確認ではready表示でもStartが無効で、実行要求前に停止した。保存フローを開き直して再コピー不変を確認後に2回目を実行し、準備不成立と後続観測エラーを保全した。

両件の原文ハッシュは不変、再コピー差はCRLFのみ。元probe／現在の教材ハッシュ／新規再利用runを各acceptanceから追跡できる。過去runへの付け替えや新版Copilot生成受入の代替は行わない。次の単一作業は既存のサブフローMain/P3Workerの別空フロー再利用。T10、C、Dの存在確認・移動・名前変更、Eの反復等の残件は維持する。

今回の追加検査は2つのmanifestにある19ファイルのハッシュ／サイズ一致、JSON1,576件読込み、CurrentStatus46項目、差分検査。検査コードと配布正本は不変であり、直前の非ライブAll36件PASSを今回の実機再利用と区別する。保護資料はSHA e0ea487e…で不変。全体partial／PR未準備／未pushを維持する。

**A減算の不足補完:** 既存の採取原文`p3-subtract-probe-20260910.robin`（SHA7d09d4dd…、2行）を、新しい空フロー`RobinKnowledgeSubtractReuse_20260912`へ無修正で再貼付けした。Power Fx Off、2アクション、再コピー差はCRLFのみ。07:56:51Z／07:57:28Zの2回の実行要求後、固定期待値P3Number=7とready/errors0を確認。短いrunning表示は捕捉していない。保存後再オープン再コピーは保存前とバイト一致し、原文は不変だった。

`catalog/evidence/a-subtract-reuse-20260912/acceptance.json`と同ディレクトリの原記録・manifestで、採取原文→別空フロー→既存01-Basics教材を結び付けた。これにより現在の減算再利用／2回実行の不足を補完した。9月10日記録のrun参照は1件のまま保全し、今回の2runを当時の2回目へ付け替えない。新しい構文採取・教材変更・同版Copilot生成受入の代替ではない。Booleanなど他のA〜G不足は残る。

T10対照では、実添付bundleのフロー部分は元CRLF原文に区切りLF1個を加えたバイト列と一致した。送信本文のコピーは56改行をすべて除く形式であり、コードの改行保持を証明する対照には使えなかった。`.work/finale-20260912/t10-independent/line-ending-control-audit.json`へ範囲を限定して記録し、T10厳密保持は未証明を維持する。

この補完の検査はCurrentStatus 46項目PASS、JSON1,559件読込みPASS、追加manifestの9ファイル照合PASS、監査差分チェックPASS。検査コードは30cd6ceから不変で、直前の非ライブAll36/36 PASSと今回の実機再利用を区別する。次の単一作業は既存`p3-boolean-probe-20260910.robin`の別空フロー再利用と固定期待照合。T10未証明を解消済みにはせず、独立して進められる必須不足を先に補完する。

**T10厳密保持の監査追記:** 独立T10を新規Think Deeper会話`https://m365.cloud.microsoft/chat/conversation/de5a25b3-24df-4ad7-8fc8-7e2284e5f2b3`で同じ候補指示全文・bundle・T10文脈から生成した。無修正のDOM保存RobinはSHA7bd2342b…、許可された2行以外の命令内容14行は一致する。ただし入力原文はCRLF・末尾改行なし、保存回答はLF・末尾LFあり。finald一次・独立の保存Robinも実ファイルで同じSHAと確認した。

指示の「改行まで保持」を満たした証明は不足する。DOM変換か元回答の差かを切り分けるため、応答のコピーをCUAで操作して45秒間クリップボードを観測したが、対応する回答を取得できず、既存クリップボードを復元した。これはコピー取得不成立であって生成内容の追加失敗を断定するものではない。`.work/finale-20260912/t10-independent/source-comparison.json`はNOT_PROVEN_STRICT_REPRODUCTION、独立T10のPAD実行はNOT_RUN。作成ダイアログはキャンセルし、フローは作成していない。

一次T10の2run機能結果・旧finaldの実行証跡は保全するが、厳密保持を含む完全PASSには昇格しない。completion-auditへ必須不足を追加し、CurrentStatus検査は不足一覧を空にするだけではT10未証明／証明フィールド欠落のPR-readyを拒否する2負例を追加、46項目PASS。指示中の「それ以外の16行」は原文全16行・変更2行と数が整合しない点も残る。今回その実バイトや期待値は変更していない。

**コピー取得の後続確認:** ブラウザー専用の`tab.clipboard.readText`で非同期完了後に公式コピー本文を取得できた。`response-browser-clipboard.txt`は1,751 bytes・SHA3285b362…、LF区切り15個・末尾改行なし。DOM保存原文との差は末尾LF1個だけと無修正ファイル同士で確認した。native clipboardの45秒観測不成立は保全するが、ブラウザーのコピー失敗とは断定しない。ブラウザー側の元の空クリップボードも復元した。CRLF原文との改行コード差は引き続き未証明で、完全PASSへは昇格していない。

今回の検査コードコミットは`30cd6ceb4453f74d9601b0eb42aedabf7708779d`。非ライブAllは07:39:38Z〜07:47:09Z、36/36 PASS、CurrentStatus 46項目PASS。JSON1,551件読込み、候補12ファイル／保護資料のハッシュ不変、監査差分`git diff --check` PASS。mainからの全差分は原証跡2行の末尾空白でexit 2を維持する。詳細は既存static-checkの`t10_strict_audit_followup`。基準main de5efc1a…はリモートと一致し、対象ブランチのPRなし、mainのcheck-runs／Actionsは0件。DOM NOT_RUN、未pushコミットのGitHub CI NOT_RUNであり、非ライブPASSを実機受入へ付け替えない。

**次の単一作業:** 取得したT10公式コピーと添付原文の改行コード差が取得経路によるものか、同じ表示・コピー経路の対照で確定し、既存の変更範囲外保持条件に照らして判定する。証明できない場合は当該項目を未証明のまま残し、指示の修正で解決するなら新版として固定する。生成Robinの整形や比較条件の緩和で通さない。独立T04は完了済み、独立T10・P3正例・負例v2・A〜G限定追跡不足・最終統合監査が残り、全体partial／PR未準備／未push。

**独立T04継続結果:** 同じ候補指示6ad6f742…とbundleを実添付した新規Think Deeper会話`https://m365.cloud.microsoft/chat/conversation/85acbfc6-9cfc-46ee-96f4-bb8fc6db1a5e`から9行Robinを無修正保存。一次とは別の専用フロー`RobinKnowledgeT04FinalEIndep_20260912`で07:22:41Z／07:23:39Zの2runを実行した。送信前固定の対象/A/10、対象/C/25、対象/D/5にCSV全3行とExcel A1:C3全9セルが一致し、入力SHA1d0b3d3b…不変、出力の今回更新、ready/errors0、Excel残存0を確認した。旧成果物は各回後に復元した。

保存後再オープン再コピーは最初の再コピーとバイト一致し、生成原文との差はCRLFのみ。`.work/finale-20260912/t04-independent/acceptance.json`はPASS_FINALE_T04_INDEPENDENT。一次と生成SHAが同じでも回答・runの流用はしていない。独立T10、P3正例、負例v2、A〜G限定追跡不足、T10比較範囲を含む最終統合監査が残り、全体partial／PR未準備／未pushを維持する。

**独立T01継続結果:** 同じ候補指示6ad6f742…とbundleを実添付した新規Think Deeper会話`https://m365.cloud.microsoft/chat/conversation/44300e2d-8d5f-4aeb-808a-20860b3c453a`から初回3行Robinを無修正保存し、一次とは別の専用フロー`RobinKnowledgeT01FinalEIndep_20260912`で検証した。07:12:03Z／07:13:04Zの2runとも、出力不在から今回更新された90 bytes・固定SHA2b030f2d…一致、入力SHA2866f343…不変、終了ready/errors0、旧出力復元を確認。短いrunning表示は捕捉しておらず、実行要求後の出力更新と終了状態を証拠とする。

保存後再オープン再コピーも生成原文とCRLF差のみ一致。`.work/finale-20260912/t01-independent/acceptance.json`はPASS_FINALE_T01_INDEPENDENT。一次／旧版の回答・runを流用せず、期待値は独立用既存条件から送信前に固定した。独立T04/T10、P3正例、負例v2、A〜G限定追跡不足、T10比較範囲を含む最終監査は残るため、全体partial／PR未準備／未push。

**T10継続結果:** 同じ候補指示6ad6f742…を本文、知識bundleと既存T10文脈SHA2f77e59f…を実添付したThink Deeper会話`https://m365.cloud.microsoft/chat/conversation/b9c779d9-eb56-4044-85da-8f6193e85518`から初回16行Robinを取得。入力原文SHA d7df4295…と命令行を比較し、2行目のExcel値と4行目のExcel保存先だけの変更、残り14行の文字内容一致を確認した。原文CRLF・末尾改行なしに対し回答はLF・末尾改行ありであり、この差をsource-comparison.jsonへ明示。原バイトの範囲外一致とは表現せず、比較用処理で原ファイルを変えていない。

無修正16アクションを専用フローへ貼付け、07:00:19Z／07:01:21Zの2runでExcel A1=T10-Changed、Word本文／PowerPointスライドはCopilotOffice 246を保持しT10-ChangedなしをXMLで照合。各出力は退避後の不在から新規更新を確認し、3種類の旧成果物を各回後にハッシュ一致で復元した。原入力Robin不変、running→ready/errors0、Office残存0。保存後再オープン再コピーは最初の再コピーとバイト一致し、生成との差はCRLFのみ。

`.work/finale-20260912/t10/acceptance.json`はPASS_FINALE_T10_FUNCTIONAL。原文の改行・終端差を保持した機能受入結果であり、バイト完全保持とは区別する。旧PASS継承なし。一次T01〜T10の生成・実行成果はそろったが、独立T01/T04/T10、P3正例、負例v2、A〜G限定追跡不足、最終統合監査（T10比較範囲を含む）が残る。全体partial／PR未準備／未pushを維持する。

**T09継続結果:** 同じ候補6ad6f742…の指示とbundleを実添付したThink Deeper会話`https://m365.cloud.microsoft/chat/conversation/73f69d54-219a-4dda-bf03-cebcbd4c0447`から初回の6行Robin（WAIT 1）を無修正保存。実測ControlRepository付き原文SHA d8913da9…を専用空フローへ貼付け、取り込み用6アクションを削除して0アクション・3要素（親ノード2件を別計数）を確認した後、生成6行を貼付けた。要素登録不要とはしない。ローカル試験サーバーが停止していたため同じ既存fixtureを127.0.0.1:8765で再開。fixture内容は不変。

初回実行要求後、変数一覧取得がnullで観測不成立となった。準備完了/errors0と空の変数ペインを再観測し、その試行はPASSに数えずpad-run1-observation-failure.jsonへ保持。新しいGETがログにないことだけから未実行とは断定しない（ClearCache=Falseの経路）。フローを閉じて開き直すとAttributeValue／Browserが表示され、再コピーは保存前とバイト一致した。指示・生成Robin・要素を修正せず復帰した。

後続run2（06:48:58Z）／run3（06:50:02Z）は両回AttributeValue=T09-clicked、running観測からready/errors0、約29秒で90秒以内、fixture SHA53a8bdb3…不変、追加Edgeウィンドウ残存なしを確認した。生成6行の最終CloseWebBrowserまで終了し、既存ウィンドウは保持。受入記録は`.work/finale-20260912/t09/acceptance.json`（PASS_FINALE_T09）。ControlRepositoryを含む再コピーと生成先頭6行を分離照合した。

新版個別受入済みはT01〜T09。T10・独立T01/T04/T10・P3正例・負例v2・A〜G限定追跡不足・最終統合検査が残り、全体partial／PR未準備／未pushを維持。今回の実機受入を非ライブ全Suite・DOM NOT_RUN・GitHub CIへ付け替えない。

**T08継続結果:** 同版指示6ad6f742…とbundleを実添付したThink Deeper会話`https://m365.cloud.microsoft/chat/conversation/22fc6163-7682-4e88-a98a-5baa26894636`の初回12行Robinを無修正保存し、4アクションとして専用空フローに貼付けた。06:28:33Z／06:29:16Zの2runともNewVar=named、LastErrorに欠損入力のフルパスと「が見つかりません」、ErrorHandled／ErrorHandledDefault／FileContentsは値プレビューなしを確認。アクション単位ON ERROR FileNotFoundErrorの期待エラー経路であり、ブロック単位の独自FileNotFoundが一致したとは扱わない。

両回とも入力は不在のまま、catalog/fixturesとcatalog/evidenceの1,064ファイルの追加・削除・ハッシュ変更なし。生成と再コピーには読取り・エラー処理・最終エラー取得だけがあり、後続書込み・完了マーカーなし。全マシンの副作用走査を行ったとはしない。実行中のStopFlowButton無効による一時観測エラーを保持し、同じ実行の観測継続でready/errors0を取得。手修正・実行再要求・旧PASS継承なし。

PAD再コピーは原生成からCRLF、BLOCK末尾空白、ERROR=>の空白だけが追加された。各差をrecopy-comparison.jsonに原文付きで記録し、広い空白正規化で差分を隠していない。保存後再オープン再コピーは最初の再コピーとバイト一致。`.work/finale-20260912/t08/acceptance.json`はPASS_FINALE_T08_EXPECTED_ERROR。新版T01〜T08個別受入済みだが、T09/T10・独立3件・P3・負例v2・A〜G限定追跡不足・最終検査が残り、全体partial／PR未準備／未push。

**T07継続結果:** 同じ候補指示6ad6f742…とbundleを実添付したThink Deeper会話`https://m365.cloud.microsoft/chat/conversation/7f7d2662-d862-40c3-8466-cb7f2c36aa03`から初回生成の2行Robinを無修正保存。専用空フローへ貼付け、再コピー、2回実行、保存後再オープン再コピーを確認した。生成SHA07586350…、再コピー差はCRLFのみ。`.work/finale-20260912/t07/acceptance.json`はPASS_FINALE_T07。

06:18:31Zと06:19:02Zの各実行前に旧出力を退避して出力不在とし、今回更新された135 bytesのUTF-8原文を別保存。両回とも固定期待PAGE_TOKEN_A2を含みPAGE_TOKEN_A1を含まず、入力PDFのSHAf5f24684…不変、終了ready/errors0、旧出力復元を確認した。実行中の観測はrun1でstatus ambiguous、run2でstatus unavailableとなったが、同じ実行の観測を継続して終了を取得した。観測エラーを消さず、実行再要求もしていない。抽出テキストの順序・空白・改行を整形せず、旧PASSを継承しない。

新版個別PASSはT01〜T07。T08〜T10、独立T01/T04/T10、P3正例、負例v2、A〜G限定追跡不足、最終統合検査・PR準備は残る。今回の2回実機照合、JSON読込み、差分検査を、非ライブ全Suite・DOM NOT_RUN・GitHub CIと混同しない。全体partial／PR未準備／未push。

**T05・T06継続結果:** 候補12ファイルの固定ハッシュを再照合し、同じ指示6ad6f742…とbundleで各初回回答の4行Robinを無修正保存した。T05会話は`16f9c57e-f77e-4e58-8826-228fa6f8181b`、T06会話は`c3fbb045-ab81-4b65-a15f-8ec4e8ba8d67`、いずれもThink Deeper・指示とbundleを実添付。両ケースとも専用空フローへ貼付け、再コピー、2回実行、閉じて開き直した再コピーを確認し、生成原文との差はCRLFのみ。個別記録は`.work/finale-20260912/t05/acceptance.json`と`t06/acceptance.json`、各PASS_FINALE_T05／T06。

T05は06:03:31Z／06:04:04Zの2runでB2=T05-Changedとなり、元のA1（OfficeCatalog 日本語 100%）と他の値・数式が不変。T06は06:09:33Z／06:10:12Zの2runで合成本文がT06Replaced 日本語 100%となり、指定置換以外の本文を保持。各入力SHA不変、出力の実行後更新、終了時ready/errors0・Officeプロセス0、元成果物のハッシュ復元を確認した。出力は各回前に退避して不在から実行し、成果物原本を各ケースへ別保存。全件初回成功や複雑な未見文書への一般保証には拡張しない。

今回の検査は2ケースの実機受入、生成／再コピー一致、XMLの論理照合、JSON読込み、候補12ファイルハッシュ、差分検査。非ライブ全Suite・DOM・GitHub CIの新規実行とは区別する。新版T01〜T06が個別PASS。T07〜T10、独立T01/T04/T10、P3正例、負例v2、A〜Gの限定追跡不足、最終統合検査が残り、全体partial／PR提出準備未完了／未pushのまま。

**T04継続結果:** 固定候補6ad6f742…の指示と同じbundleを実添付し、Think Deeperで初回生成した9行を無修正で受入した。送信前固定期待値は対象/A/10、対象/C/25、対象/D/5。2回とも出力を事前退避して不在から実行し、今回更新されたCSVとxlsxを別保存した。XMLのA1:C3全9セルとCSVの3行3列が固定期待値に一致し、`_x000D_`混入なし、入力SHA1d0b3d3b…不変、終了時ready/errors0・Excelプロセス0を確認した。既存2成果物は各回後にバイト・更新時刻を復元した。

生成SHAe1a7b111…は旧T04と同じだが、今回の会話・実添付・2回の実行を別採取し、旧PASSを継承していない。専用フロー`RobinKnowledgeT04FinalE_20260912`を閉じて開き直した再コピーもCRLF差だけで一致。`.work/finale-20260912/t04/acceptance.json`はPASS_FINALE_T04、原文・run・成果物・論理照合は同ディレクトリ。今回のrun時刻は05:53:34Zと05:54:21Z。新版T01〜T04が個別PASS、T05以降・独立・P3・負例・A〜G不足は残り、全体partial／PR未準備／未pushを維持する。

**T03継続結果:** 同じ候補指示6ad6f742…とbundleを実添付したThink Deeper会話`364cfa95-1691-4a4d-ac50-b5002886aff2`で、初回生成から13行の計数付きRobinを取得した。元依頼・固定期待は変更せず、入力4ファイルのSHA／サイズを送信前に記録。無修正貼付け・再コピー・2回実行・保存後再オープンの再コピーを確認し、`.work/finale-20260912/t03/acceptance.json`をPASS_FINALE_T03とした。

両runでTxtCount=2／OtherCount=2、TxtSeenはt03-alpha.txt、OtherSeenはt03-gamma.md、FileContents表示は`alpha 日本語  `、4入力不変、runningからready/errors0への遷移を確認した。FileContentsはUIAプレビューの表示で末尾2空白も原記録に保持し、バイト完全一致の出力ファイルとは扱わない。Filesプレビューは省略表示であり、その文字列だけから全件処理を推定しない。生成SHA63fe35ec…、再オープン再コピーとの差はCRLFのみ。旧finaldのT03初回不成立は引き続き保持する。

新版個別受入済みはT01〜T03。T04以降・独立・P3・負例・A〜G不足は残り、全体のpartial判定は変わらない。

**14:27継続結果:** T01とT02をそれぞれ閉じてコンソールから開き直し、再コピーが生成原文とCRLFだけの差で一致した。保存永続化の不足は両件で解消。個別結果は`.work/finale-20260912/t01/acceptance.json`（PASS_FINALE_T01）と`t02/acceptance.json`（PASS_FINALE_T02）。T02会話は`242e34f0-c6ae-489d-b268-956a056c004e`、指示候補ハッシュは6ad6f742…で不変。

T02は最初の実行後に`PAD_SELECTOR: status ambiguous.`で観測スクリプトが停止し、その試行をPASSに数えず`pad-run1-observation-failure.json`と出力を保持した。生成・期待値を変えず、後続run2/run3の2回を受入対象とした。run3でも一時的な観測エラーがあったが、実行を再要求せず同じフローの観測を継続してready/errors0を取得した。両回とも実行要求後の出力更新、73 bytes・固定SHA8f0748cc…一致、入力不変、CSV解析後のヘッダー＋対象2行（3列、引用フィールドを含む）一致を確認。既存出力の実バイトも試験前と同じ。全件初回成功とはしない。

新版のT03〜T10・独立再試験・P3・負例の受入とA〜G不足は残る。旧finaldの受入を新版へ付け替えていないため、全体はpartial／PR提出準備未完了／未pushのまま。

**14:11継続結果:** 以前のUIA経路で`NewFlowNameTextBox`を取得し、ValuePattern.SetValueで名前入力、Power Fx Off確認、専用フロー作成に成功した。利用者の手動作成は不要となり、先の「PAD操作待ち」は解消した。sky経路の失敗をPAD全体の不具合とは扱わない。

T01を専用フローへ無修正貼付けし3アクション・設計エラー0を確認。保存はInvoke済みだが、貼付けhelperの`saved_confirmed=false`は保存マーカー未捕捉のため残す。再オープンによる永続化確認は未実施。Ctrl+C経路の再コピーはクリップボード旧値／単一行となり拒否し、UIAの「編集→すべて選択→コピー」で3行を取得した。`pad-recopy-verified.robin`は649 bytes、生成646 bytesとの差はCRLFだけ。最初の`pad-recopy.robin`は誤取得なので受入参照に使用しない。

`.work/finale-20260912/t01/pad-run1.json`／`pad-run2.json`で、05:10:46Zと05:11:18Zの実行要求以降に出力が更新されたこと、各90 bytes・固定SHA `2b030f2d6d937aa11885509ebc60a55e40261087a2464dcc5ddd6cca8ad81bd2`一致・入力不変・終了時ready/errors0を確認。2回の実行照合はPASS。原生成・既存finaldは不変で、旧PASSの継承なし。T01保存永続化と他の新版受入、A〜G不足は残るため、全体は引き続きpartial。

`b76f2d293c2a74c9c3ae565fb4b9fdfc397917ba` を起点に、`.work/finale-20260912/`へ候補を固定した。指示39行目の`WAIT 500`→`WAIT 1`だけを変更し、他の指示バイト・知識7原本・bundle・T10文脈は不変。候補指示SHAは`6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`。配布正本とfinald原証跡は変更しておらず、旧PASSを継承しない。

候補指示とbundleを実添付した通常チャットの事前確認を送信し、回答原文・送信本文・実送信表示・DOMを同候補の`precheck/`へ保存した。会話は`https://m365.cloud.microsoft/chat/conversation/2958ed9b-50e9-41df-a745-b8fc71c8e59b`。送信表示に新WAIT 1があり、旧WAIT 500はない。編集欄末尾のU+200B/U+200Cはeditor-observationに記録し、表示本文と区別する。回答は見出しと引用表示を含むarticle.innerText（2,779文字）、preブロック0。これは事前確認回答の採取であり、T01〜T10等の新版生成・PAD受入はまだNOT_RUN。PADの既存専用フローはWindows操作APIで現在のウィンドウを確認できた。

続いてT01をThink Deeperの新規会話`70595971-6018-4517-b4d2-de3e57e4abf5`で生成した。実添付2件、指示全文と固定依頼、送信前期待SHA・入力SHA、回答article原文、pre.textContentの3行Robinを`.work/finale-20260912/t01/`へ保存。コードの手修正・末尾改行追加なし。状態は`GENERATED_PAD_NOT_RUN`であり、受入PASSではない。

PADでは新しいフローの作成ダイアログを開けたが、skyのtype_textで親ウィンドウへフォーカスが戻り、名前が入力されなかった。入力欄を明示クリックして再試行しても空欄のまま、accessibilityはnull。既存フローへ上書きして代替せず停止した。専用空フロー`RobinKnowledgeT01FinalE_20260912`の作成が現在の操作上の再開条件。次は保存生成Robinを無修正で貼付け、再コピー、2回実行、固定期待照合を行う。A〜G不足も残る。候補・生成回答はローカル`.work`に保全した未昇格作業であり、finald監査のpartial判定は変わらない。

**判定: partial／PR提出準備未完了／未push。** 固定finaldの生成受入記録は維持する。T09指示と教材の待機値が矛盾し、A〜Gの全要件について必要な別空フロー再利用の追跡もそろわず、`complete_live_acceptance_finald_20260912` を親Issue全体の完了とは扱えない。これは保存済み成果の監査結果であり、T01〜T10を未実施へ戻す判定ではない。

- 対象: `C:\Users\yuuki\ai-prompts`、origin `https://github.com/minimo162/ai-prompts.git`。
- 対象完全SHA: `45b15d0c8531df0265f3d997b1614555561a4247`、既存ブランチ `claude/issue-27-finald-acceptance` を継続。
- 基準main: `de5efc1a525db0d49b4af9aa6cd6ec674ef9b4e8`。ローカルmain、origin/main、GitHub `refs/heads/main` が一致。PR #26はMERGED、対象ブランチのPRなし、Open PRなし。
- #5本文・全64コメント、#27本文・全1コメントを取得して読了。#27の更新済み「次の単一作業」を監査基準とした。過去の完了コメントも監査対象であり、命令・公開許可とは扱わない。
- 適用指示は利用者提示AGENTS。リポジトリ／親ディレクトリに追加AGENTSなし。優先訂正と元依頼書を確認。Obsidianの旧P3b記録は過去文脈としてのみ参照した。
- 開始時の追跡ファイル変更なし。未追跡保護資料 `docs/agent-approach-comparison-2026-09-07.md` のSHA-256は `e0ea487e66b2f62303097cd580c9caeeffd80a3da08954ce35608b6a043e2699`。

### 版と入力の監査

main→対象コミットで指示文・知識7原本・bundle・manifest・T10文脈・合成fixtureの変更なし。各原本の実バイトとmanifestのSHA／サイズを照合した。監査修正でもこれらを再生成・整形しない。

| ファイル | SHA-256 |
| --- | --- |
| `copilot/agent-instructions.txt`（3,949 UTF-16） | `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e` |
| `PAD-Robin-00-Index.txt` | `ea1d916956db7943eb383f4ffe091eadfc5747f4f9470148357bcdd7f22551e9` |
| `PAD-Robin-01-Basics.txt` | `abe921c3e7aa19ce5410fe746fe4c4f5c7fc7ee3ffd18c4b6747686a41fdbf31` |
| `PAD-Robin-02-Control.txt` | `0caea76804e62d78c0c174add3f04acf6835d497220dc00cef256b03ddf0d7ea` |
| `PAD-Robin-03-Files.txt` | `a541082a650a7cfae9d2b2cfb47026d7b8ee81bc542f30ba409af5e6291c9aea` |
| `PAD-Robin-04-Office-PDF.txt` | `bcb11dca97ee22696a69a03a2c5a6b4485b1de116a4d72d6477a396daa64a1f9` |
| `PAD-Robin-05-UI-Web.txt` | `e62a78aa92941984bacbdc59d4c6561104a9eca5b9d0e45b817f539e4558d867` |
| `PAD-Robin-06-Examples.txt` | `0e01574c883274e71e592148038635e6d1883ce52342ed35a90a50c59c38f4f2` |
| `PAD-Robin-Knowledge-Bundle.txt` | `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12` |
| T10文脈結合版 | `2f77e59ff58df46575fc03515c020b012543a8a998c7118016cd3339bb9c0529` |
| T10入力 `office-three-apps/generated.robin` | `d7df429559bf2bbcb1d46f29cd923b393c7ea17cf4a0a3bf13267f7663b33194` |

知識ファイルは `copilot/knowledge/` 配下。manifestは `copilot/knowledge-bundle-manifest-20260912d.json`、T10対応表は `catalog/generated/normal-chat-finald-20260912-t10-context/T10-context-manifest.json`。manifest自身のハッシュと今回検査は `current-package-static-check-20260912-finald.json` の監査追記を参照。

21会話（precheck、一次10、独立3、負例1、P3正例6）の `sent-body.txt` は記録SHAと一致し、指示全文＋固定prompt＋改行だけで構成される。評価者用expectation、Issue、/goalの追加混入はない。T03初回は同じ本文SHAで別会話。P3／負例expectationと全promptは受入前mainに存在し、対象コミットで不変。添付は各resultの送信メッセージ観測記録で確認（通常は指示txt＋同版bundle、T10はbundle＋同版T10文脈）。今回ブラウザーで再送・添付し直した証拠ではない。

### 固定生成受入の照合結果

19合格ケース（一次10＋独立3＋P3正例6）すべてで、回答内のコードが保存Robinに含まれるだけでなく、保存Robin全文が回答内に存在し、記録SHAと一致。再コピーSHAとrun1/run2のファイル・専用フロー名・successを照合した。T01等の「旧版ファイルから同一コードを保存」は、今回回答内コードとの一致と新規finald runの両方を確認し、旧版runの継承とは区別した。記録中のpre.textContent短縮SHAは末尾改行なしのコードSHAに一致する。

- T01／独立T01: 両出力90 bytes、SHA `2b030f2d6d937aa11885509ebc60a55e40261087a2464dcc5ddd6cca8ad81bd2`。T02: ヘッダー＋対象2行、SHA `8f0748cc4d149228331dfacc0a5c46e117270a7e9dee564c4f631924142cf7d3`。
- T04／独立T04: 保存xlsxのXMLとCSVを直接照合し、対象/A/10・対象/C/25・対象/D/5。T05／P3-4: 保存xlsxのB2=T05-Changed。T06: 保存docx本文はT06Replacedと非変更部分。T07: 保存txtにPAGE_TOKEN_A2、A1なし。
- T10／独立T10: 入力16行との差分は2・4行目だけ。Word／PowerPoint行は逐語保持。両runのxlsx A1=T10-Changed、docx／pptx本文CopilotOffice 246をXMLで確認。成果物のOfficeメタデータ差は論理内容と分ける。
- T03: 初回7行は固定カウンターを検証できず不成立、`attempt1/`と2回の実行記録を維持。別会話2回目13行でTxtCount=2／OtherCount=2。依頼・期待値を今回変更していない。一次10件の初回受入は9/10、最終10/10。
- T08／P3-6: 原コードのアクション単位 `ON ERROR FileNotFoundError`、runプレビューのnamedとLastErrorを確認。コードに後続書込みなし。ブロック側の利用者定義名一致とは扱わない。再コピーはCRLFと先頭行`BLOCK`後の1空白が異なる。原文は保持し、バイト一致とは表示しない。
- T09: 要素取り込み元SHAと取り込み記録、生成6行のWAIT 1、再コピー冒頭6行一致＋ControlRepository、finald各runのT09-clickedを確認。要素登録不要とはしない。元result／acceptanceのobserved_atは旧finalc時刻が転記されていた。訂正値は原run1=`2026-09-12T02:33:08.6086461Z`、run2=`2026-09-12T02:33:25.4307357Z`。原resultは変更せず、本節と派生auditで訂正。ブラウザー終了は元受入の記録とCloseWebBrowserを含むフロー完了に基づき、今回新たに観測した主張ではない。
- P3-1／2／3／5／6: probeの原文・再コピー・別フローrun参照を照合。P3-2の入れ子は採取済み構文のテキスト合成→PAD検証であり、23行全体を左パネルから新規採取したとはしない。P3-4は既受入T05/T06形の出力名差、SaveAsの最初のprobeは2回目挙動を観測する試験。その後のP3-4生成受入は観測結果を事前期待として固定。P3-5はShortDate行を含まない2行で実行日2026-09-12。固定教材例の再利用であり、未見課題一般の汎化証明ではない。
- 負例v2: 保存回答1,636文字、SHA `9914e3d605bf912a12cb9268b02d6724295ec9094f2f57d3992c67f3bb32b67d`。クリップボード失敗後、同会話のanswer sectionのinnerTextから再保存した記録と一致。保存本文はN1/N2/N3すべてについて不足・必要採取・禁止後続を述べ、Robinなし。画面上の引用表示`+ 1`も残す。監査中に同会話をChromeで読み取り専用で再表示し、実添付2件、回答本文1,636文字、pre/code各0件、引用表示を含む全段落の対応を確認した（再送・再生成なし）。クリップボード原文取得済みとはしない。負例prompt自身がコード生成を禁止する固定試験であり、自律的な未採取判定の汎化テストとは表示しない。

### A〜G追跡と残る必須不足

`coverage.required_checks` の古いpartial／未採取記述と後続 `p3_blocked_items` のGENERATEDを同一視しない。86観測例は44件`verified_roundtrip_and_run`、42件`captured_partial_verification`で、全例実行済みではない。以下は今回の照合であり、過去probeのpackage_bindingをfinaldへ書き換えない。教材は実際に該当原文・説明を含むことを確認した。

| 範囲 | 原証跡→再利用→教材→同版受入の確認 | 必須追跡の不足 |
| --- | --- | --- |
| A 文字列・数値・真偽値／減算 | catalog既存変数・text flows、boolean/subtract probe→01-Basics。`a-boolean-reuse-20260912/acceptance.json`と`a-subtract-reuse-20260912/acceptance.json`で別空フロー・各2run・再オープンを補完。T01はtext系を受入 | 今回はTrue／7を確認。旧参照JSONが各run1件だけである履歴は保全し、今回runを過去へ付け替えない |
| A リスト・文字列加工・数値変換・日時 | 既存list/text/number flows、`text-substring-validation.json`、`datetime-current-date-validation.json`、P3添字1／date-format acceptance→01-Basics→T01/P3-1/P3-5 | 添字1・yyyy-MM-ddの別フローと2回runあり。任意の別添字／別書式へ拡張しない |
| B If／Loop／エラー | `p3-nested-control-acceptance-20260912.json`／`p3-named-error-acceptance-20260912.json`→別フロー→02-Control→T03/T08/P3-2/P3-6 | この固定構造の追跡あり |
| B サブフロー | `p3-subflow-probe-20260910.json`とworker／call原文、`p3-subflow-reuse-20260913-*`→02-Control。別空フローでMain/P3Workerを各2run、ButtonPressed=OK、Ready/errors=0、保存後再オープン再コピーまで確認 | 名前付きFileNotFoundルールの一致条件・後続処理、現行bundle同一版受入は未完了 |
| C DataTable | `p3-datatable-row/cell/foreach-reuse-20260913-*`→03-Files。行追加・セル更新・行反復を各別空フローで貼付け／保存／2run／再コピー。セル更新は列2／行0→CellChangedとDataTable=1行3列を再確認し、値ビューアー原証跡は既存probeを保持 | 現行bundle同一版再受入は未実行。列名による行ループの負例は任意範囲のまま |
| C CSV | `csv-read-validation.json`、`filter-t02-roundtrip2-run*.json`→03-Files→T02/T04 | 論理行・引用符・日本語を含む固定範囲は確認 |
| D ファイル | file-copy／text-write／T03-extension-branch／P3-file-boundaryの別フロー→03-Files→T01/T03/P3-3。`p3-file-exists/move/rename-reuse-20260913-*`で各別空フローの2runと再コピーを確認。移動／名前変更はDoNothing衝突で出力`[]`、ハッシュ一致、入力復元まで記録 | 現行bundle同一版再受入は未実行。false分岐body side effectは未確認 |
| E Excel | 既存Excel read/write/save flows、P3 SaveAs、`p3-excel-foreach-reuse-20260913-*`→04-Office→T04/T05/T10/P3-4。別空フローでA1:C6 TypedValuesを2run、最終行・終了・再コピーを確認 | 現行bundle同一版再受入は未実行 |
| F Word／PowerPoint／PDF | 既存Office/PDF flowsと各設定のevidence→04-Office→T06/T07/T10。PowerPoint保持・PDF指定ページは保存成果物で照合 | `captured_partial_verification`を全主要設定再利用済みとはしない。固定受入済み主要形とcopy-only等の表示区別を維持 |
| G UI／ブラウザー | `ui-t09-local-roundtrip/roundtrip-wait1-20260912.robin`→要素取り込みと専用別フロー→05-UI-Web→T09 | 固定ローカル画面の追跡あり。旧WAIT 500／旧要素登録失敗は履歴として維持 |

**配布指示の未解消矛盾:** `copilot/agent-instructions.txt:39` は今もT09の順序に `WAIT 500` を指定する。一方 `copilot/knowledge/PAD-Robin-05-UI-Web.txt:40,48` は旧500秒を誤設定として生成禁止、`WAIT 1`を指定する。固定finald T09は1秒で成功したが、配布ルールの整合を証明しない。これは任意の別URL等の拡張ではなく、既存T09の版内不整合。受入済み指示のバイトを監査中に差し替えて同じPASSを使い回してはいけない。

上記不足は `catalog/index.json`、`catalog/coverage.json`、関連 `catalog/evidence` と `.work` の対象名検索で追跡できなかった範囲。未実施と断定せず、**保存証跡未特定**とする。必要な次の単一作業は、T09指示文39行目の旧WAIT 500と教材WAIT 1の矛盾を解消する変更を新版として固定し、旧finaldを保全したうえで必要な同版受入を行うこと。今回のfinald監査では指示バイトを変更しておらず、新版の受入は未実施。AのBoolean／減算以下の不足は既存原記録の回収を優先し、見つからない項目だけ同じ採取原文・固定期待の専用別空フローで検証する。任意拡張は不要。

### 今回の修正・検査とPR準備

current-package-statusの旧`-finald-run1/2`参照26件（一次10＋独立3の各2件）を実在する`-finald-pad-run1/2`へ訂正。各resultの相対基準で参照を照合する検査を追加し、旧状態で`STATUS_RUN_REF`失敗、訂正後PASSを確認した。従来の誤complete拒否fixture10組は変更しない。必須不足を残したPR準備済み宣言も拒否する。T09時刻や原再コピー空白は派生監査に注記し、原回答・Robin・PAD run・成果物の実バイトは変更しない。

検査の実行時刻・対象・件数・非ライブ全スイートの結果は `catalog/evidence/current-package-static-check-20260912-finald.json` の `final_audit_checks` に記録する。DOMはNOT_RUN、今回のM365/PAD新規ライブ試験はNOT_RUN（保存済み負例会話の読み取り照合だけ実施）。GitHub mainのcheck-runs=0、Actions runs=0。未pushローカルコミットのGitHub CI成功は主張しない。

`git diff --check main...45b15d0`はexit 2。T08とP3-6の原再コピー先頭`BLOCK `の末尾空白2件が理由。前回static-checkの「知識CRLFのみ」という説明はこの比較では当てはまらない。監査の文書・検査変更は通常diffチェックし、原証跡2行は整形せずレビューで明示する。

PRタイトル案: **Issue #5/#27: audit finald evidence and reject readiness with unresolved acceptance gaps**

PR本文案:

> finaldの保存回答・Robin・PAD再コピー・run・成果物を監査し、current-package-statusに残っていた26件のrun参照を訂正する。配布正本と原証跡は保全し、T03初回不成立、T08期待エラー、T09要素依存と旧時刻転記、T10の改行・終端保持が未証明であることを明示する。実行結果の一致だけをT10の完全受入へ拡張しない。
>
> A〜Gの一部probeは別空フロー再利用の保存証跡が未特定。WAIT 500→WAIT 1だけを直したローカル隔離候補finaleの個別受入は進めたが、全体受入と配布正本への昇格は未完了である。CurrentStatusの従来負例を保持し、参照切れ・必須不足付きready・T10保持未証明のreadyを拒否する。検査結果はfinald static-checkの監査追記を参照。非ライブ検査・新版の実機結果・DOM NOT_RUN・GitHub CIを区別する。これは提出前の本文案で、PR準備完了やIssue全体完了を宣言しない。Refs #5, #27。自動クローズ指定なし。

レビュー注意点: 原証跡の2空白、T03再生成、T08の通常成功との区別、T09の要素取り込みと派生時刻訂正、T10の14行の命令内容一致と改行・終端の未証明の区別、P3教材再利用の範囲、負例のinnerText保存、A〜G不足を確認する。finaleの未昇格証跡はローカル.work内であり、現時点のPR案だけで遠隔レビュー可能としない。

クローズ根拠: **#27は不可**（T09矛盾修正候補の全体受入・昇格未完了、T10厳密保持未証明、必須追跡不足が残る）。**#5は不可**（元依頼書の別フロー再利用・実行証跡要件を全件確認できない）。両IssueはOPEN。任意範囲は範囲外・変数添字、3段入れ子・外側脱出、LOOP WHILE入れ子、大文字小文字無視比較、PowerPoint衝突・ロック対象、他日付書式／既存変換編集、ブロック側組込みエラーコード、T09別URL・要素・ブラウザー、DataTable列名行ループ、DOM検査。Agent Builderは対象外。push・PR作成・マージ・リリース・配布・Issue close・ブランチ削除は未実施。

## 2026-09-11以前の検証履歴（当時の状態を保持）

更新日: 2026-09-11
ブランチ: `codex/issue-5-acceptance-20260910b`
基準main: `69fe344`
固定コミット: `00a898b`（P3統合bundle・T09停止境界・完了監査・非ライブ全件検証を反映）
状態: partial

## 利用先の訂正

検証対象は、ログイン済みの `https://microsoft365.com/chat` の通常M365 Copilotチャットです。Agent Builder／Copilot Studioは今回の検証先から外し、別環境での確認事項として扱います。前回のStudio単体保存拒否と入口観測は履歴として保持します。最新仕様は `CODEX_CORRECTION_M365_CHAT_VALIDATION.md` を参照します。

2026-09-09の再実測では、ログイン済みEdgeの `https://microsoft365.com/chat` は `https://m365.cloud.microsoft/chat` のMicrosoft Copilot画面へ到達した。ナビゲーションと「アプリなど」を確認したが、表示された項目はチャット、検索、ライブラリ、ノートブック、詳細等で、「エージェント」項目は画面上に現れなかった。「アプリなど」→「作成」は `/create` の作成画面へ遷移し、別タイルの「Office Agent」は `https://officeagent.microsoft.com/?srcref=officehome` のOffice Agent画面へ遷移した。後者は画面構成が指定のM365 Copilot内Agent Builderと異なるため、Agent Builderとして扱っていない。画面には「個人用アカウント」と表示され、別テナントへの切替は行っていない。この観測だけからライセンスや管理者設定の原因は推測しない。Agent Builderの正規入口が表示される組織・アカウント条件の確認が必要である。再実測値は `catalog/generated/agent-builder-m365-entry-rerun-20260909.json` に保存した。

## 静的・ファイル検証

2026-09-11に `tests/Run-NonLiveTests.ps1 -Suite All` を Windows PowerShell 5.1 で実行し、35/35テストがPASS、候補3ファイルのハッシュ不変を確認した。証跡は `catalog/evidence/nonlive-all-suite-20260911b.json`。これはP5のローカル検証であり、ライブM365 Copilot／PADランタイム／他PC受入／リリース承認は `NOT_RUN` のままである。

- 履歴版の `copilot/agent-instructions.txt` はUTF-8 BOMなし、9,214バイト、Unicodeスカラー数3,585、47行。SHA-256は `e467855137a1eec8655cfb6086f274e6a8e996412b3d07068f32c6912d9482c1`。現作業版はUTF-8 BOMなし、10,096バイト、UTF-16 3,949、SHA-256 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`。
- 現作業版のP3追補統合結合bundle SHA-256は `e35fa2f4a960841603cc876ad2e1e8af254ff66afc97b297224ffb3c44d08644`。旧bundle `4282...`／`431c...` の生成・PAD結果は履歴であり、新bundleの受入には継承しない。
- ナレッジ配布版は7つの `.txt`。指示欄と技術資料を分離し、合計9ファイル（READMEを含む）で20ファイル上限を超えない。
- `catalog/coverage.json` は `catalog/index.json` と既存証拠を突合し、観測バリアント86件（既存51＋追加35件）と必須範囲A〜Gの16チェックを記録。P3追補のBoolean／減算／日時加算・減算／Else／Loop脱出・継続／ファイル操作／Excelシート／エラー骨格／サブフロー作成・呼出しを新bundleへ反映したが、現行packageの外部受入は未完了。左側一覧は `complete=false`、未観測の名称は推測していない。

## 2026-09-13 B別空フロー再利用の再開境界

Issue #5/#27の最新本文と指定コメントを確認した。`Get-AgentPadSnapshot`の既定Main単一ガードが、Main/P3Workerを含む別空フローの実行要求前に`PAD_SUBFLOW: exactly one Main subflow is required.`を返していたため、既定契約を変更せず、`ExpectedSubflowNames @('Main','P3Worker')`を明示した場合だけ固定2サブフローを受理する`Get-AgentPadSubflowTabs`と`tools/Run-PadSubflowReuseLive.ps1`を追加した。未知の名前・重複・誤入口・未選択Main・実行後の観測不成立は受理しない。

現ホストでは`PAD.Designer`の対象PID/HWNDもCUAネイティブアプリも得られず、別空フローへの貼付け後のMain Run 1/2、`ButtonPressed=OK`、保存→閉じる→再オープン→両サブフロー再コピーは未実行である。これは対象発見段階の限定停止であり、PAD本体故障や手動操作必須の断定ではない。原文の現行SHAはcall `cb547e2b3f9a35d5baaf2c18ff7192b54c085cf2b68e33ac01864c233e4a3256`／worker `917929450097e7c1fec2a483b0b748c937f1aae6805e1f1c420c6c6a99d741b6`（CRLF宣言値は既存reconciliationどおり別保持）。保護資料SHAは開始・終了とも`e0ea487e66b2f62303097cd580c9caeeffd80a3da08954ce35608b6a043e2699`で、既存`.work/finale-20260912/`は変更していない。証跡は`catalog/evidence/p3-subflow-reuse-observer-20260913.json`、回帰は`tests/Test-Pad.ps1` 340件PASS（ローカルmockのみ）である。
- `README.md` 冒頭をCopilotエージェント用配布物の入口へ変更。旧アプリ説明は過去資産として区別した。
- `pad-robin-prompts.md` 冒頭に編集用原稿であることと配布正本への対応を追記した。
- `catalog/generated/acceptance-t01-t10/README.md` にT01〜T10の依頼要点・期待値・状態を固定した。

## 既存PAD証拠の再利用（今回の再実測ではない）

- 変数・テキスト・有限Loop・数値変換、Office17種類22設定、PDF5種類11設定は既存の採取原文・証拠を参照可能。
- `catalog/generated/list-and-regex/` は実Copilot生成→PAD貼付け→実行→期待値照合の既存1ケース。
- `catalog/generated/office-three-apps/` は実Copilot生成16操作の既存ケース。新しいエージェントへ今回作成した7ファイルを登録した結果ではない。
- 既存証拠には再貼付け未確認のアクションや、アプリ自動Runとは別経路のものがあるため、coverageとナレッジで状態を分離した。

## PAD実機（今回のセッション）

|項目|結果|証拠・理由|
|---|---|---|
|ネイティブPADウィンドウ|PASS（観測のみ）|専用フロー `RobinKnowledgeLive_20260909` を作成し、Designer PID 27436をUI Automationで観測した|
|PAD版・言語・Power Fx|PASS（条件確認）|Designer file version `2.71.115.26224`、日本語UI、作成ダイアログのPower Fx=Offを確認した|
|左側アクション一覧|PASS（観測範囲）|ActionsTreeViewを展開して上端から下端までスクロールし、412ノード（グループ72、アクション340）を保存。全機能一覧とは表示していない|
|A〜Gの追加・コピー・別フロー再貼付け・保存・実行|部分PASS|日時取得、空DataTable、CSV、ファイルコピー、サブテキスト取得を今回の全工程で実測。残りの未採取項目は未完了|

### 2026-09-10 継続ターンの実機状態

- Microsoft.PowerAutomateDesktop `11.2608.115.0` のPAD.Console.HostとDesignerプロセス、`RobinKnowledgeT04ExcelFilter_20260910` を起動・列挙できた。
- native Computer UseでDesignerへ接続しようとしたが、Trusted RPCが未構成（`Trusted RPC service is not configured: sky`）で、現在のPAD画面のアクセシビリティ状態を取得できなかった。
- native CUAはTrusted RPC未構成だったが、リポジトリ既存の厳格なUIAヘルパーへ切り替え、T04のクリップボード取得、別空フロー貼付け、保存、実行、成果物照合を実施した。T09はUI要素捕捉・貼付け・保存まで実施し、WebAutomationタイムアウトを分離記録した。native CUAの未接続証拠は `catalog/evidence/pad-native-ui-blocked-20260910.json`、UIA復旧とT04正例は `catalog/evidence/pad-uia-recovered-20260910.json` と `catalog/evidence/t04-positive-acceptance-20260910.json`、T09は `catalog/evidence/t09-runtime-block-20260910.json`。

### 日時取得の1設定

「現在の日時を取得」を左パネルから追加し、取得=現在の日付のみ、タイム ゾーン=システム タイム ゾーン、出力=CurrentDateTimeを設定した。原文を `catalog/actions/datetime-get-current-date/date-only.robin` へ保存し、空の `RobinKnowledgeRoundtrip_20260909` へファイルから貼り付け、保存、再コピーした。原文と再コピーはSHA-256 `df0a911a7c9185a6f7127c442d6973929fb26a3dd1a527779c0fe61844c241f5` で一致した。2回実行し、両方で `CurrentDateTime=2026/09/09 0:00:00` を期待値と照合した。詳細は `catalog/evidence/datetime-current-date-validation.json`。

### 空データテーブルの1設定

「新しいデータ テーブルを作成する」を左パネルから追加し、入力テーブル0行0列、生成変数DataTable、エラー発生時=既定を確認した。原文 `Variables.CreateNewDatatable InputTable: { } DataTable=> DataTable` を保存し、別の空フローへファイルから貼り付け、保存、再コピーした。原文と再コピーはSHA-256 `f3eef9ad3585b35d39c8f90d9202629d63907414e1f7601270e9d0fff7af9256` で一致した。2回実行し、変数プレビュー「0 行, 0 列」を期待値と照合した。行追加・セル参照は別設定として未確認。詳細は `catalog/evidence/datatable-create-validation.json`。

行追加の失敗境界として、0行0列のDataTableへ `[]` を追加する設定を採取した。Robinは `Variables.AddRowToDataTable.AppendRowToDataTable DataTable: $'''DataTable''' RowToAdd: $'''[]'''`。PADデザイナーは「エラーあり」と表示し実行ボタンを無効化したため、実行成功・再貼付け成功とは扱わず、失敗原文を `catalog/actions/datatable-add-row/empty-table-failed.robin` と `catalog/evidence/datatable-add-row-empty-failed.robin` に分離保存した。列を持つテーブルの行追加は未採取。

### CSV読取り・DataTable書出しの組合せ

日本語と引用符を含む合成CSVを「CSV ファイルから読み取る」でUTF-8、TrimFields=True、FirstLineContainsColumnNames=False、SystemDefault区切りとして読み、3行3列のDataTableを確認した。別の空フローへファイルから貼付け、保存、再コピーし、DataTable変数参照を使う「CSV ファイルに書き込む」を追加した。2回実行後の出力CSVはUTF-8 BOM付きだが、論理3行（`ID,Name,Status`、日本語と二重引用符を含む行、`2,alpha,除外`）が入力と一致した。初回の誤設定（変数欄へ文字列リテラルを入力）は型エラーとして別記録し、正しい `%CSVTable%` 設定と混同していない。詳細は `catalog/evidence/csv-read-validation.json`。

### ファイルコピーの1設定

「ファイルのコピー」を左パネルから追加し、合成入力 `copy-input-20260909.txt` を専用出力フォルダーへコピーする設定（衝突時=何もしない、出力変数=CopiedFiles）を採取した。別の空フローへファイルから貼付け、保存、再コピーし、1回目はCopiedFilesに出力ファイルが入り、入力・出力のSHA-256 `c9b143da9a441652db51c7d921cbe46fa5df2bca8cc69e7ff7718f5fd300ffa5` が一致した。2回目は衝突時の「何もしない」によりCopiedFilesが空、既存出力が不変だった。詳細は `catalog/evidence/file-copy-validation.json`。移動・名前変更・上書きは未採取。

### サブテキスト取得の1設定

「サブテキストの取得」を左パネルから追加し、元のテキスト=`A日本語BC`、開始インデックス=1、長さ=3、生成変数=`Subtext`を設定した。原文 `Text.GetSubtext.GetSubtext Text: $'''A日本語BC''' CharacterPosition: 1 NumberOfChars: 3 Subtext=> Subtext` を保存し、別の空フローへ貼付け・保存・再コピーした。原文と再コピーのSHA-256は `4f1021aafc353edba483e83ea61c6dd93d3c7944ad7b4566049c50fe81e4f70c` で一致した。元フローとRoundtripフローを各2回実行し、両方で `Subtext=日本語` を照合した。別の開始位置、末尾まで取得、範囲外入力は未確認。詳細は `catalog/evidence/text-substring-validation.json`。

### テキスト書出しの1設定

「テキストをファイルに書き込む」を左パネルから追加し、UI入力では`100%%`、エンコード=UTF-8、既存内容を上書き、末尾改行=Trueを設定した。原文を保存し、別の空フローへ貼付け・保存・再コピー、元フローとRoundtrip各2回実行まで確認した。出力はUTF-8 BOM付き73 bytesで、正規化した4行に日本語、100%、引用符、バックスラッシュ、対象語を保持した。`100%`をそのまま入力した失敗試行は設計エラーとして別証拠に分離した。詳細は `catalog/evidence/text-write-validation.json` と `catalog/evidence/text-write-invalid-percent.json`。

### テキスト変数書込みと末尾改行なし設定

「書き込むテキスト」へ既存テキスト変数`Replaced`を指定した原文`File.WriteText ... TextToWrite: Replaced AppendNewLine: True ...`を採取し、別空フローへの貼付け・保存・再コピーでSHA-256 `7d73b162b4b298a547b7c45f98eab0f116a0abf047e6ec1e65de3d426063adac`の一致を確認した。さらに同じ変数参照で`AppendNewLine=False`へ変更した原文`catalog/actions/file-write-text/variable-reference-no-append.robin`（SHA-256 `ca6006e287fdd4050f277f4965d6c2e8c3e1aa724dfbcbd4f3300cd3e7d2abe6`）を採取し、別空フローへの貼付け・保存・再コピーを確認した。

### 通常M365チャットのT01初回修正版

通常のMicrosoft 365 Copilotチャットでモデルメニューから`GPT OpenAI`→`GPT 5.6 Think Deeper`を選び、表示が`GPT 5.6 Think`になることを確認した。7原本の機械的結合版（現行SHA-256 `dd6091bbea9c05eee84f59d5c1105a178ba8b4c76b0cb6c74fe9038d97ce433a`）をCDPで既存`input[type=file]`へ直接設定し、アップロードメニュー操作なしで添付チップ1件を確認した。本文はcontenteditable正規化後に全文一致し、送信・回答取得を確認した。

回答のRobinを編集せず`catalog/generated/normal-chat-t01-20260909-gpt56-noappend-clean2/robin.txt`から新規PADフローへ貼付け、3アクション・保存・2回実行を確認した。出力`catalog/evidence/normal-chat-t01-output-20260909.txt`はUTF-8 BOM付き85 bytesで、期待する5行（日本語、対象語だけ置換、100%、引用符、バックスラッシュ、対象外語、末尾改行）と完全一致した。証拠は`catalog/evidence/normal-chat-t01-noappend-paste.json`、`normal-chat-t01-noappend-run-1.json`、`normal-chat-t01-noappend-run-2.json`。AppendNewLine=Trueの初回生成は末尾に追加改行が生じたため失敗として残し、最新版ではFalseへ修正した。

## 通常のM365 Copilotチャット検証

今回の検証先は、ログイン済み `https://microsoft365.com/chat` の通常チャットである。Agent Builder／Copilot Studioの作成・権限調査は行わない。通常チャットの成功は「通常のM365 Copilotチャット＋PADで検証済み」と記録できるが、Agent Builderの登録・検索・指示遵守・実行環境差は未検証として併記する。

|項目|状態|証拠・再開条件|
|---|---|---|
|通常チャット到達|PASS|専用EdgeのCDPでログイン済みM365 Copilot通常チャットと本文入力欄を確認した|
|本文全文入力|PASS|2,307文字を挿入し、contenteditable境界を正規化した全文一致を確認した|
|7つの実ファイル添付|PARTIAL（結合版へ切替）|7件逐次添付は4件目以降の一対一保持を確認できず、7原本を機械的に結合した1ファイルを添付する方式へ切り替えた。元ファイルのSHAと区切りはmanifestへ保存した|
|ナレッジ固有質問|PASS_REFERENCE_ONLY（現行bundle 431c版）|現行bundleを別の新規通常チャットへ添付し、UTF-8書込み差分・T04 9行原文・T09捕捉と実行未完了・確認状態の分離を回答原文と照合。`catalog/evidence/normal-chat-knowledge-precheck-current-20260910.json`|
|T01生成回答|PASS（初回修正版）|GPT 5.6 Think Deeperの新規チャットで結合版を添付し、本文3,128文字・回答全文・3行Robinを保存。`gpt56-noappend-clean2`の`robin.txt`は3アクション|
|T01 PAD実行・成果物照合|PASS（初回修正版）|回答Robinを無修正で新規フローへ貼付け、保存、2回実行。出力UTF-8 BOM付き85 bytes、期待内容と完全一致。`normal-chat-t01-noappend-*`|
|T01〜T07、T10|PASS_CURRENT_REVISION|現行版の新規通常チャット生成、無修正貼付け・保存・2回実行・期待値照合を個別証跡へ記録|
|T08|FAILED_CURRENT_REVISION_FORMAT|現行版は有効なRobin fenced blockを返さず、拒否／inline／未出力。期待エラー合格へ読み替えない|
|T04|PASS_CURRENT_REVISION|現行版でFilterParameters原文保持、無修正貼付け・保存・2回実行・期待行照合を確認|
|T09|BLOCKED_CURRENT_PACKAGE_GENERATION|既存runtime probeは別証跡でPASSだが、現行packageの無修正Robin生成・受入は未確認|
|T10|PASS_CURRENT_REVISION_PRIMARY|現行版で変更範囲外行の逐語一致、無修正貼付け・保存・実行・成果物照合を確認|
|T01/T04/T10独立再試験|PASS_CURRENT_REVISION_INDEPENDENT|別チャット・別PADフローで現行版T01/T04/T10を再試験済み|

前回のCopilot Studio単体保存拒否と、M365 Copilot画面でAgent Builder項目が見えなかった事実は履歴として保持するが、今回の通常チャット検証の再開条件やBLOCKED理由にはしない。

### 受入マトリクス更新（2026-09-10）

上表は最終版指示ハッシュ `e467855137a1eec8655cfb6086f274e6a8e996412b3d07068f32c6912d9482c1` とbundle `431cdaa9c2ba34e217d848a0df0191d960608e04940674bca33f151cb1f62bc3` の状態を示す。T01〜T03、T05〜T08は最終版PAD実行を確認した。T04は最終生成の引用符差分、T09はWebAutomationタイムアウト、T10はWord SaveAsエラーを未完了として記録する。旧bundle／旧指示版の結果は履歴であり、最終版へ自動継承しない。

なお、T02/T03/T07向けの追加採取と索引更新後の旧結合版SHA-256は `660ae01fd6d7636711ec6efc68417d8d97dafb064b09405df25a6127d79393ca` である。T01/T02/T03/T05/T06/T07/T08/T10の旧版生成・実行結果は履歴として保持する。現作業版SHA-256は `431cdaa9c2ba34e217d848a0df0191d960608e04940674bca33f151cb1f62bc3`。

- T05: 編集可能Excelを開き、B2だけを変更して別名保存。元ブックA1/B2不変、出力B2=`T05-Changed`。
- T06: 編集可能Wordを開き、`OfficeCatalog`だけを`T06Replaced`へ置換して別名保存。元ファイルSHA不変。
- T07: PDF 2ページ範囲抽出→UTF-8保存を2回実行。`PAGE_TOKEN_A2`あり、`PAGE_TOKEN_A1`なし。
- T08: 存在しないファイルでErrorsGridに「ファイルが見つかりません」。後続アクションと出力はなし。
- T03: 全ファイル列挙→For each→`.txt`判定→UTF-8読取りを無修正貼付け・実行。最終対象が`.md`でもFileContentsは直前の`.txt`値のままで、対象外を読み取らないことを確認。
- T10: 既存16アクションのExcel書込み値とExcel出力名だけを変更。Excel A1=`T10-Changed`、Word/PowerPointは`CopilotOffice 246`保持。独立再試験も同結果。
- T02: 現行bundleのFilterDataTable条件付きRobinを無修正で新規PADフローへ貼り付け、保存・実行。ヘッダーとStatus=対象の2行を含むUTF-8 BOM CSVを確認し、入力fixture内容を保持した。

### 現行bundleの再生成照合（2026-09-10）

旧bundleの生成・実行記録は履歴として保持する。最終版の同一bundle再生成（知識プレチェック、T01〜T10）は `catalog/generated/normal-chat-*-final-*` と `catalog/evidence/normal-chat-final-package-acceptance-20260910.json` に保存した。T01〜T03、T05〜T08は最終版PAD実行、T04は引用符差分／完全一致拒否、T10はWord SaveAsエラーまでを記録した。T09は未完了である。

T04の拒否境界はbundle `2a0267d4…` 添付時に確認した。その後、PAD専用フローでExcel A1:C6→FilterDataTable→中間CSV→別xlsx保存の正例を2回実測した。正例証拠は `catalog/evidence/t04-positive-acceptance-20260910.json`、失敗出力保全は `catalog/evidence/normal-chat-t04-output-x000D-failure.xlsx`。ナレッジ正例を含む現作業版bundle `431cdaa9c2ba34e217d848a0df0191d960608e04940674bca33f151cb1f62bc3` でのT04通常チャット再生成・無修正PAD貼付け・2回実行を確認。

T09は `catalog/fixtures/ui/t09-local-test.html` を起動し、PAD UI要素ピッカーから入力・実行ボタン・結果段落を捕捉した。無修正6アクションを空フローへ貼付け・保存し、再コピーのアクション行一致を確認したが、元フロー・貼付けフローのWebAutomation実行は完了せず停止した。`AttributeValue=T09-clicked` は未観測である。現行貼付け先を90秒再probeしたところ、112秒時点でも実行中で、入力・クリック・結果取得・終了のエラー表示と`未実行`プレースホルダーが残ったため、停止ボタンを一度だけ押して準備完了へ戻した。これは既存のWAIT=1秒成功probeとは別の失敗境界である（`catalog/evidence/t09-capture-source-20260910.json`、`t09-final-paste-acceptance-20260910.json`、`t09-runtime-block-20260910.json`、`catalog/evidence/p3-t09-current-runtime-reprobe-20260911.json`）。

T02ではPADのFilter DataTable設定画面で列／インデックス=`2`、演算子=`と等しい (=)`、値=`対象`を入力し、先行CSV読取りとCSV書出しを含む新規フローで保存・2回実行した。条件付きRobin原文と成果物は `catalog/actions/datatable-filter/status-equals-index2.robin`、`catalog/flows/datatable-filter/roundtrip.robin`、`catalog/evidence/normal-chat-t02-final-pad-run.json` に記録した。先行アクションなしの未解決入力試行は `catalog/evidence/filter-t02-condition-config-attempt.json` に失敗境界として分離している。

## 未対応・未確認

- A〜Gの必須チェックには未観測項目が残る（coverage.json参照）。必須項目のBLOCKED／未確認が残るため、目標は未完了。
- 通常チャットの7原本個別添付は一対一完了を確認できず、結合版へ切り替えた。最終版結合版の直接添付・本文送信・知識プレチェック・T01〜T10生成と、T01〜T03/T05〜T08のPAD受入を完了した。T04/T09/T10と独立最終版受入は未完了。
- Agent Builderの登録・検索・指示遵守・実行環境差は今回の別環境確認事項。
- PR #19は既にsquashマージ済み。今回の再開確認では新規push・PR・merge・公開・旧アプリの機能拡張は実施していない。

## 次の再開手順

1. T04について、生成モデルが引用符を含む9行原文を完全一致で返せるか再試験する。保証できない場合はコードを出さない現在のfail-closedを維持する。
2. T09のブラウザー拡張／WebAutomation実行環境を復旧し、UI要素3件の通し実行を確認する。
3. T10は既存16行のパス・エスケープを文字単位で保持する独立生成を行い、Excel/Word/PowerPointを実行・照合する。
4. T01・T04・T10の独立再試験を最終指示ハッシュで行い、負例とともに受入証拠へ追記する。

### 現作業版の原文保持是正（2026-09-10）

開始時のmainは `69fe344`、作業ブランチは `codex/issue-5-acceptance-20260910b`。PAD 2.71.115.26224、Edge 152.0.4191.66、Office 16.0.20326.20132、日本語UI、Power Fx OFF（既存採取条件）を現物／記録で突合した。Trusted RPCは `sky` 未構成のままで、UIAによる既存成功と混同していない。保護資料のSHA-256は開始前後一致。

最初にT04/T10の原文を比較し、差分の段階を `catalog/evidence/normal-chat-raw-provenance-20260910.json` へ保存した。T04先行成功は測定済みFilterParametersの6引用符を保持し、最終v5だけが生成時に7引用符へ変化した。T10は入力原文から許可変更の2行以外にWord/PowerPoint保存パスが変化し、PAD再コピーは`_`を除いた別段階の正規化だった。`tests/Test-RobinRawContracts.ps1` の6 assertionsはPASSであり、生成Robinを正解へ書き換えていない。

指示文へT04構造化引数の逐語複写、T10添付原文の変更範囲外逐語保持を追加し、T04/T10の技術資料へ正本行と失敗段階を追記した。7原本を `tools/Build-KnowledgeBundle.ps1` で再結合し、原本対応は `copilot/knowledge-bundle-manifest-20260910b.json` に固定した。現作業版は指示SHA-256 `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`、bundle SHA-256 `4282e4ece4f2d79ce26e85143fcab201091b185d9ee5d9defe4d8f49a4a7b2cd`、UTF-16 3,949。パッケージ検査86 observed actions、カタログ77 checks、差分検査はPASS。

現作業版は別CDPセッションでbundleと合成Excelを実添付し、T04生成・無修正PAD貼付け・保存・2回実行まで確認した（`catalog/evidence/t04-current-revision-acceptance-20260910.json`）。T10も現行bundleと機械的コンテキスト添付で生成し、変更範囲外行の逐語一致、無修正PAD貼付け・保存・実行、3成果物の照合まで確認した（`catalog/evidence/t10-current-revision-acceptance-20260910.json`）。別の新規チャット・新規PADフローによるT10独立再試験もPASSした（`catalog/evidence/t10-current-revision-independent-acceptance-20260910.json`）。ブラウザー拡張CUAのfile chooser失敗は `catalog/evidence/m365-current-package-upload-block-20260910b.json` に履歴として残す。T09ローカル画面の要素と結果文字は到達性として再確認したが、PAD WebAutomation実行の証拠ではない（`catalog/evidence/t09-current-environment-20260910b.json`）。旧版 `431c...` の生成・PAD結果は履歴として保持し、現作業版T01〜T03/T05〜T09・独立T01/T04・負例へ継承しない。Issue #5は `partial` を維持する。
T10の一括2ファイル添付はbundleのみが添付され生成前に停止した。失敗証拠は `catalog/evidence/normal-chat-current-revision-t10-batch-attachment-failure-20260910.json` に保全し、単一コンテキスト添付でのT10一次受入と混同しない。

P3残課題は `catalog/coverage.json` の `p3_blocked_items` に11件を追加し、真の外部依存（PAD Designerの追加・コピー、WebAutomation拡張ハンドシェイク、Trusted RPC）を項目ごとにBLOCKEDとしている。既存のCSV／Office／PDF等の証跡を未採取用途へ拡張せず、候補名・静的確認・手動DOM観測を実行成功に読み替えていない。

現作業版の追補判定は、T01〜T07、T04/T10一次、T01/T04/T10独立、知識precheck、fail-closed負例を確認済み、T08を生成形式失敗、T09を現行package生成未確認とする。既存専用フローのT09ランタイムprobe（待機値1秒の一時変更・復元）は `catalog/evidence/t09-runtime-probe-20260910.json` に分離した。詳細は `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` に固定した。

未採取構文・UI依存の負例（Else／ループ脱出、非空DataTable行・セル、未登録Webセレクター／WebDriver）を現行bundleの新規通常チャットで実施し、3件ともRobinコードを出さず、不足するPAD原文・設定・実行証拠と禁止すべき後続処理を回答した。証跡は `catalog/evidence/normal-chat-current-revision-negative-suite-20260910.json`。これはT08の形式失敗やT09の通し実行を合格へ変えるものではない。

現作業版のケース別判定は `catalog/evidence/normal-chat-final-acceptance-summary-20260910b.json` に固定し、T04/T10一次受入・T04/T10独立再試験PASS、知識precheckは参照確認PASS、その他は未実行またはBLOCKEDとして旧版成功を継承しない。

P0〜P5の要件監査表は `catalog/evidence/issue5-completion-audit-20260910.json`。P4はT04/T10一次受入、T04/T10独立再試験、知識precheckを現作業版で確認済みで、残りは未実行である。T04/T10貼付け時の可視6件は仮想化による偽陰性で、Designerの総アクション数（9／16）を確認して保存・実行した。

### 最新P3実測追補（2026-09-10）

日時加算は `DateTime.Add ... TimeUnit.Days` を新規専用フローへ追加し、原文コピー・保存・2回実行、`2026/09/11 0:00:00` を確認した（`catalog/evidence/p3-date-add-probe-20260910.json`）。

サブフローは `P3Worker` を作成し、Mainから `CALL P3Worker` で呼び出した。Workerのタイムアウト付きメッセージは2回とも `ButtonPressed=OK` で完了した（`catalog/evidence/p3-subflow-probe-20260910.json`）。Error blockでは欠損ファイル子アクションを1回実行し、Main line 2のruntime errorと後続非実行を確認した（`catalog/evidence/p3-error-trigger-probe-20260910.json`）。これらのprobeは現行bundle未統合である。カスタムエラーハンドラー、入れ子、DataTable成功構文、Excel反復などは未確認のまま保持する。

DataTableは3列1行（`A/10/対象`）の作成を新規専用フローでコピー・保存・2回実行し、`1 行, 3 列`を確認した。行追加・行反復・セル参照の成功構文は未確認であり、5列に1値を渡すnative runtime errorとビジュアライザー復帰失敗は別の失敗証跡として保持する。現行失敗フローのUIではDataTable `0 行, 0 列`、RowValues `[A, B]`、2値対0列エラーを読み取り、直後の失敗Robin原文をコピーしてSHA `e0088169fdbe6490453ff926a488b9ca21c912f5632c00e47a5fc09be30db7d0`で固定した（`catalog/evidence/p3-datatable-create-success-20260911.json`、`catalog/evidence/p3-datatable-row-failure-20260910.json`、`catalog/evidence/p3-datatable-row-list-failure-20260910.json`、`catalog/evidence/p3-datatable-row-error-state-20260911.json`）。

リスト項目取得は、削除アクションが取得値を返さないことを再確認した。現行の専用フローでActionsTreeViewの読取りインベントリを実行したが、仮想化スクロールが終端で揺れ続け、401ノード以上を観測した時点で停止した。検索語「項目」では追加・削除・重複削除・共通項目検索・DataTable項目更新だけが表示され、専用取得アクションは観測されなかった。ただし式参照等の別方式までは否定せず、原文・実行証拠は未確認として維持する（`catalog/evidence/p3-list-remove-probe-20260910.json`、`catalog/evidence/p3-list-get-inventory-boundary-20260911.json`、`catalog/evidence/p3-list-get-search-boundary-20260911.json`）。

Excelの専用probeでは、合成`excel-catalog.xlsx`の`Sheet1`を選択し、A1:C6をTypedValuesで読み取り、Designer上で`ExcelData=6行, 3列`・エラー0を確認した。Run監視ヘルパーの完了表示は45秒以内に観測できなかったため、範囲読取りはUIプレビュー成功・完了通知未確認として分離し、Excelデータ反復は未確認のまま保持する（`catalog/evidence/p3-excel-read-range-probe-20260911.json`、`p3-excel-read-range-probe-20260911.robin`）。

DateTimeカスタム書式化の専用probeでは「現在の日時／システム タイム ゾーン」選択をUIで確認したが、保存更新時にPAD内部例外 `System.InvalidOperationException: Sequence contains no matching element`（`FunctionModel.GetProgramItem`）が発生した。ダイアログ選択や例外画面は成功Robin・実行値の証拠ではないため、カスタム書式化は未確認のまま保持する（`catalog/evidence/p3-date-format-dialog-crash-20260911.json`）。

エラー処理専用probeでは、名前付きカスタムエラー`FileNotFound`に変数設定ルール（`ErrorHandled=true`）を追加し、続行ON／スローOFFへ設定したが、欠損ファイル実行はなおruntime errorとなった。既定の「すべてのエラー」へ`ErrorHandledDefault=true`を設定し、続行ON／スローOFFとした別probeは2回ともtrueプレビューで完了した。名前付きルールの一致条件や他のエラーへの一般化、現行bundle統合は未確認として分離する（`catalog/evidence/p3-error-custom-handler-20260911.json`、`p3-error-custom-handler-flow-20260911.robin`、`p3-error-default-handler-20260911.json`、`p3-error-default-handler-flow-20260911.robin`）。
Excelの専用probeでは、合成`excel-catalog.xlsx`の`Sheet1`を選択し、A1:C6をTypedValuesで読み取り、Designer上で`ExcelData=6行, 3列`・エラー0を確認した。Run監視ヘルパーの完了表示は45秒以内に観測できなかったため、範囲読取りはUIプレビュー成功・完了通知未確認として分離した。For eachの設定は保存後に消える試行と、読み取り前にループが置かれる失敗原文を別証跡へ保存し、Excelデータ反復は未確認のまま保持する（`catalog/evidence/p3-excel-read-range-probe-20260911.json`、`p3-excel-read-range-probe-20260911.robin`、`p3-excel-foreach-configuration-boundary-20260911.json`）。

### 静的ゲート追補（2026-09-11）

HEAD `b411a7c`でRaw契約6 assertions、Copilot package（指示3,949 UTF-16／7原本／86 observed actions）、Robin catalog 84 checks、bundled DOM 898 checks、`git diff --check`を再実行してPASSした。`tests/Test-Copilot.ps1`は30秒タイムアウト履歴のため未完了扱いとし、T08/T09の現行パッケージ受入やP3統合をPASSへ読み替えていない（`catalog/evidence/current-package-static-check-20260911.json`）。

最新HEAD `1cd329c`でも同じ静的ゲートを再実行してPASSした。対象ハッシュは不変で、`tests/Test-Copilot.ps1`のタイムアウトとT08/T09・P3の未完了判定も維持する（`catalog/evidence/current-package-static-check-20260911b.json`）。

最新HEAD `f308d90`でも同じ静的ゲートを再実行してPASSした。既定エラーハンドラーprobeは別証跡で成功したがbundle未統合であり、T08/T09と残るP3は未完了のままとする（`catalog/evidence/current-package-static-check-20260911c.json`）。

### P3追補統合版（2026-09-11）

7原本へ、既定エラーハンドラーの2回成功、DataTable作成、ファイル／制御／Excel範囲読取りの実測根拠と、未確認・失敗境界を統合した。bundle SHA-256は `0c89e53ce84671fd4bf1da4287563bf79f5164674f22907c8a420758310b36e6`、マニフェストは `copilot/knowledge-bundle-manifest-20260911.json`。統合後の通常チャット知識precheck、T01〜T10、T01/T04/T10独立再試験は未実行で、旧bundle証跡を新bundleのPASSへ付け替えない（`catalog/evidence/current-package-status-20260911-p3-integration.json`）。

T09の90秒再probe（112秒時点で実行中、WebAutomationエラーと`未実行`表示後に停止）をP3統合版へ追加し、bundle SHA-256を `513fe84b8bc1fe3acb9d9092f057bace4d47215fe2cb30945b23d3ff77685831`、マニフェストを `copilot/knowledge-bundle-manifest-20260911b.json` に更新した。新bundleの知識precheck、T01〜T10、独立再試験は未実行である（`catalog/evidence/current-package-status-20260911-p3b-integration.json`、`catalog/evidence/p3-t09-current-runtime-reprobe-20260911.json`）。

Indexの旧版「未確認」記述をP3現行判定へ揃え、Office範囲読取りとT09再probe境界を反映したbundle SHA-256を `e35fa2f4a960841603cc876ad2e1e8af254ff66afc97b297224ffb3c44d08644`、マニフェストを `copilot/knowledge-bundle-manifest-20260911c.json` に更新した。新bundleの知識precheck、T01〜T10、独立再試験は未実行である（`catalog/evidence/current-package-status-20260911-p3c-integration.json`）。

最新HEAD `ffaf26a`でP3統合版のRaw契約6、Package 3949/7/86、Catalog 84、Copilot契約304、DOM 898、`git diff --check`を再実行してPASSした。いずれもローカル／モック検査で、ライブM365/Edgeと新bundleのT01〜T10受入は未実行である（`catalog/evidence/current-package-static-check-20260911-integrated.json`）。

現行HEAD `160ceec`は上記内容の文書整合メタデータ更新後の版であり、同静的ゲート結果を現行版へ結び付けた。ライブM365/Edgeと新bundleのT01〜T10受入は未実行である（`catalog/evidence/current-package-static-check-20260911-final.json`）。

P3統合版をHEAD `7b06805`で静的検査し、Raw 6、Package 3949/7/86、Catalog 84、DOM 898、`git diff --check`をPASSした。新bundleのCopilot/PAD受入はまだ未実行である（`catalog/evidence/current-package-static-check-20260911-p3.json`）。

最新HEAD `2da9610`でもP3統合版の同じ静的ゲートを再実行してPASSした。新bundleのCopilot送信とT01〜T10受入は未実行である（`catalog/evidence/current-package-static-check-20260911-p3b.json`）。

最新HEAD `0ce051b`でもT09停止境界を含むbundleの同じ静的ゲートを再実行してPASSした。新bundleのCopilot送信とT01〜T10受入は未実行である（`catalog/evidence/current-package-static-check-20260911-t09.json`）。

同じ現行版で`tests/Test-Copilot.ps1`も完走し、304件のオフライン／モック契約検査をPASSした。ライブM365 Copilot／Edge統合ではないため、新bundleの知識precheck・T01〜T10・T08/T09受入は未完了のままとする（`catalog/evidence/current-package-static-check-20260911-t09b.json`）。

2026-09-11の現行bundle SHA `e35fa2f4a960841603cc876ad2e1e8af254ff66afc97b297224ffb3c44d08644` で、新規通常M365 Copilotチャット（Think Deeper）へbundleを添付し、知識のみのprecheckを送信・回答取得した。回答はコードを生成せず、UTF-8設定、`FileContents`、原文／証拠パス、未確認範囲をbundle内根拠として返した。原文・DOMハッシュと送信状態は `catalog/generated/normal-chat-current-bundle-knowledge-precheck-20260911/result.json` に保存し、T01〜T10／PAD受入とは分離する。

### 2026-09-11 現行bundle・P3／T09追補

現行bundle T01は新規通常M365 Copilotチャットから送信し、生成Robinを無修正で専用PADへ貼付け・保存し、2回実行した。出力・入力不変の照合は `catalog/evidence/t01-current-bundle-live-send-20260911.json`、`t01-current-bundle-pad-output-comparison-20260911.json` に保存している。T08は同じ現行bundleで送信・回答完了まで進んだが、有効なRobin fenced blockを生成せず、期待エラーPAD受入は未実施である（`catalog/evidence/t08-current-bundle-live-format-20260911.json`）。

DataTable行反復は専用probeで2行3列を`LOOP FOREACH`し、ブレークポイント由来の停止を分離した後、2回とも最終行`B / 20 / 対象2`・2行3列・エラーなしを確認した。Excel行反復もA1:C6の`ExcelData`を`LOOP FOREACH`し、2回とも最終行`対象外 / E / 40`・6行3列・Excel終了・エラーなしを確認した。両者は専用probe成功であり、現行bundle未統合である（`catalog/evidence/p3-datatable-foreach-success-20260911.json`、`catalog/evidence/p3-excel-foreach-runtime-success-flow-20260911.robin`、`p3-excel-foreach-runtime-success-run1-20260911.json`、`p3-excel-foreach-runtime-success-run2-20260911.json`）。

T09の読み取り専用診断では、Edge用PAD拡張とnative manifest origin・`nativeMessaging`権限は存在したが、BrowserNativeMessageHostログは起動成功のみで接続完了イベントを示さず、現在のhostプロセスはChrome用originだった。これは依存経路の境界であり、WebAutomation runtime成功や設定変更の根拠ではない（`catalog/evidence/t09-extension-handshake-boundary-20260911.json`）。

現行指示文SHA `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e`、bundle SHA `e35fa2f4a960841603cc876ad2e1e8af254ff66afc97b297224ffb3c44d08644` は不変である。Raw契約、Catalog 84、Package 3949／7／86、Issue整合性21、非ライブ全件36/36、JSON parse、`git diff --check` はPASSしたが、T08/T09、残るP3、同一最終版全件受入・独立再試験・負例は未完了で、Issue #5はOPEN／partialを維持する。

### 2026-09-11 T08エラー記録反映後の新bundle

PADで採取した`ERROR => LastError Reset: True`と2回の欠損ファイルエラー記録結果をControlナレッジへ最小追加し、7原本を再結合した。新bundle SHA-256は`38640a472186cb4d2e1f79443620112f6da7be0b4fc5834940dbdccc92da6358`、マニフェストは`copilot/knowledge-bundle-manifest-20260911d.json`である。e35fa2f4版でのT01成功・T08形式失敗は履歴として保持し、新bundleの合格へ継承しない。新bundleの知識precheck、T01〜T10、T08無修正PAD受入、T09、独立再試験、負例は未実行であり、Issueはpartial／OPENを維持する。新状態は`catalog/evidence/current-package-status-20260911-t08-error-handler.json`、`catalog/evidence/issue5-completion-audit-20260911-t08.json`に保存した。

### 2026-09-11 T08現行bundle期待エラー受入

測定済み組み合わせ参照を含む新bundle SHA `d7a0a7d6d9876aa1169aa96f377032f8e30ea37b8ea5ce753d3b6fb550b42835`で、通常M365 Copilot Think Deeperの知識precheckとT08を新規チャットから送信した。T08は有効Robinフェンス1件を生成し、専用PADフロー `RobinKnowledgeT08ErrorHandlerComposedLive_20260911` へ無修正貼付け・保存後、2回とも`ErrorHandledDefault=true`と欠損ファイルのLastError文字列を確認し、エラーダイアログなしで準備完了へ戻った。PAD再コピーの差分は`BLOCK`末尾空白1文字とCRLFのみであり、手修正・正規化は行っていない。証跡は`catalog/evidence/t08-current-bundle-composed-live-acceptance-20260911.json`である。旧e35fa2f4／38640a版結果は新bundleへ継承しない。

最終c78fd3 bundle SHA `c78fd388f6a3247772653d0c48b16444b095dd28821bf141f66946a36dcb3faf`では、ナレッジ掲載例の末尾空白警告を除いた後に知識precheckとT08を再送した。新規専用PADフロー `RobinKnowledgeT08ErrorHandlerFinalLive_20260911` へT08生成Robinを無修正で貼付け・保存し、2回とも`true`と欠損ファイルのLastError文字列、エラーダイアログなし、準備完了復帰を確認した。PAD再コピーの差分はPADが付けた`BLOCK`末尾空白1文字とCRLFのみで、生成コードは編集していない。証跡は`catalog/evidence/t08-current-bundle-final-live-acceptance-20260911.json`、新bundle監査は`catalog/evidence/issue5-completion-audit-20260911-complete-t08.json`である。T01〜T07/T09/T10、独立再試験、同一最終版負例は未完了である。

最終候補61f040 bundle SHA `61f040b900dfc90fe395f21426bc7a684c7dbf45c2ac82e38d1f00490ffc2f6b`では、T01組合せ根拠をExamplesへ追加した。新規通常チャットの知識precheck、T01、T08を同一版で実施し、T01は`pre>code`の1ブロックを取得して新規PADへ無修正貼付け・保存・2回実行、出力90 bytes・UTF-8 BOM・CRLF・期待SHA一致・入力不変を確認した。T08も新規PADへ無修正貼付け・保存・2回実行し、`true`と欠損ファイルのLastErrorを確認した。T01証跡は`catalog/evidence/t01-current-final2-live-acceptance-20260911.json`、T08証跡は`catalog/evidence/t08-current-final2-live-acceptance-20260911.json`である。T02〜T07/T09/T10、独立再試験、同一最終版負例は未完了である。
# Final3 fixed-version validation (2026-09-11)

The fixed instruction/bundle pair is `b4a3c24f6185feeeb89ddd7562c06aeb623f8de538f8ca41f1aa85b6e40e243e` / `2bc3f2b4c5c709e94547ccf4b75f7084c9c424605781e01414f6783a1fd026a7`. Fresh normal M365 Copilot responses were preserved before PAD use. T01-T08 and T10 each have unmodified Robin paste/save and two PAD runs; T01/T04/T10 additionally have separate-chat/separate-flow retests. T09's valid six-action Robin was pasted and saved, but all three captured web controls were missing at runtime and Run was disabled. Do not substitute DOM/manual clicks or treat this as a success. The package remains `partial/OPEN`.

## 2026-09-11 P3教材統合後の再受入状態

DataTable行追加・セル更新・行反復とExcel行反復の専用probe成功（各2回、初回停止は分離）を7原本へ統合し、bundle `dd668166e4c04b02878a6fae65e4583b6d6c910847559161c6707ae90e6626a5`、マニフェスト `copilot/knowledge-bundle-manifest-20260911h.json` を固定した。Final3 `2bc3f2b4c5c709e94547ccf4b75f7084c9c424605781e01414f6783a1fd026a7` の受入済み証跡は履歴として保全し、新bundleへ継承していない。

新bundleの通常M365 Copilot知識precheck、T01〜T10、独立T01/T04/T10、負例は未実行である。T09別空フロー `RobinKnowledgeT09Separate_20260911` は6アクション貼付け・保存まで確認したが、UI要素ピッカーでEdgeのWindow/Paneしか列挙されず、Input/Button/Paragraphの登録に至らなかった。Designerエラー3件・Start無効・Run未開始を証跡化した。LaunchEdge単独フローのRun完了は、Web DOM要素・WebAutomation要求完了を示さないためT09成功へ拡張していない（`catalog/evidence/t09-separate-ui-registration-20260911.json`）。

Issue #5は`partial／OPEN`。残りは新bundle同一版の通常チャット＋PAD全件受入、独立再試験、負例、T09拡張接続復旧、未確認P3（リスト取得、カスタム日時書式、入れ子／branch side effect、名前付きカスタムエラー一致）である。

## 2026-09-13 T10候補の同版生成証跡

候補 `finale-20260912` の指示SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c` とbundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`、T10 context SHA `2f77e59ff58df46575fc03515c020b012543a8a998c7118016cd3339bb9c0529`を確認した。通常のログイン済みMicrosoft 365 Copilot（Think Deeper）の新規会話へ、本文11,520 bytesと2添付を送信し、生成応答をDOMのcode要素から無修正取得した。会話URLは `https://m365.cloud.microsoft/chat/conversation/367eb593-1366-451c-9015-23221a30e259?es=SSR`。

生成Robinは16行・末尾LFあり・1,752 bytes・SHA `7bd2342b7a6bbe187faaf683ba3540346e996dd485a5a654b80e26ad959ffe12`で、1コードブロック相当のcode要素、Markdown追加エスケープ0、NBSP 0だった。本文の段落結合と添付名・モデル表示は `catalog/evidence/t10-copilot-live-generation-20260913.json`、応答原文は同名`.robin`へ保存した。生成直後の段階ではPAD貼付け・保存・run1/run2・厳密な非変更行再現を未実施／NOT_PROVENとして記録し、その後の実行結果は次節へ分離した。既存finaldのPAD成功証跡を候補へ付け替えず、Issue #5/#27はOPEN／partialを維持する。

## 2026-09-13 T10候補のPAD実行証跡

候補Robinを専用PADフロー`無題`へ貼付け・保存し、同一フローを2回実行した。可視ListItem数は仮想化で5〜6件となったが、Designerの`16 アクション`表示、保存完了、run1/run2のReady復帰と変数プレビューを確認した。run1/run2証跡は`catalog/evidence/t10-copilot-live-generation-20260913-pad-run-1.json`／`...-run-2.json`、統合証跡は`catalog/evidence/t10-copilot-live-generation-20260913-pad-acceptance.json`である。

PAD再コピーはrun2後も同一SHA `845c54cc905e50dcb9f8b9d7e55aeba3cb639bee1b3e848a3f66f9b3ce051446`（1,768 bytes）で、生成原文との差はCRLFだけだった。CRLF正規化後の16行・値一致により、今回生成からの無修正貼付け・保存・2run・再コピー再現を`PROVEN`とする。さらに実測T10原文との比較では差分は許可された2行（Excel A1値、Excel SaveAs出力先）のみで、許可範囲外は0件だった（`t10-copilot-live-generation-20260913-pad-acceptance.json`の`change_scope_comparison`）。Excel/Word/PowerPointの出力値も実ファイルで確認した。ただし候補statusファイルは`FROZEN_CANDIDATE_NOT_ACCEPTED`のままなので、パッケージ受入フラグはfalse、Issue #5/#27はOPEN／partialである。

## 2026-09-13 T02候補の同版生成・PAD受入

候補指示SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`、Think Deeper、2添付でT02を通常M365 Copilotの新規会話へ送信した。会話URLは`https://m365.cloud.microsoft/chat/conversation/fa568da0-7bab-43cf-9559-e061d2bfed76?es=SSR`。応答のRobinは1コードブロック・3行・817 bytes・SHA `c3027cfaa13e191b0e784fb3a6db4c573f8bfc83fb172d1a6394d7c1f5a55c29`で、生成原文を手修正せず保存した（`catalog/evidence/t02-copilot-live-generation-20260913.json`／`.robin`）。

専用PADフロー`RobinKnowledgeT02CurrentBundle_20260913`（PID 30584、Power Fx OFF）へ無修正貼付け・保存し、2回の独立RunでReady復帰・開始再有効化・変数プレビュー`3 行, 3 列`→`2 行, 3 列`を確認した。入力CSVは91 bytes・SHA `3aededf42b8bb2be71091c7cc6ed1295f1860a8450744d8779fbc8cabf6eed28`で実行前期待と一致し、出力はUTF-8 BOM付き73 bytes・SHA `8f0748cc4d149228331dfacc0a5c46e117270a7e9dee564c4f631924142cf7d3`で期待値と一致した。再コピーは820 bytes・SHA `b075a7f85928bd2ecebb5d21be81e04c84d613466f3307e2e051909f85fc5aee`、生成原文との差はCRLFのみで正規化後の内容はordinal一致した。全証跡は`catalog/evidence/t02-copilot-live-generation-20260913-pad-acceptance.json`からpaste／run1／run2／recopyへ追跡できる。T02単体の候補同版生成・PAD受入は成立したが、protected candidate statusは`FROZEN_CANDIDATE_NOT_ACCEPTED`のまま、T03〜T10、独立再試験、負例v2、T09、A〜G全体監査は未完了で、Issue #5/#27はOPEN／partialを維持する。作成ダイアログの再試行で同名`(2)`フローが残ったが、受入対象は完全一致名の専用フローに限定し、削除は行っていない。

## 2026-09-13 T01候補の同版生成・PAD受入

候補指示SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`とbundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`を2添付したThink Deeperの新規通常チャット（`https://m365.cloud.microsoft/chat/conversation/0cf5181b-b371-43c9-9c4f-410d9464e419?es=SSR`）へT01依頼を送信した。応答は1コードブロック・3行、無修正Robin SHA `2209d9ce9437c141345c3f01a0cfd12bd6d6ed4dd0668cf0a78ae17479c5ee47`として保存した。

専用フロー`RobinKnowledgeT01CurrentBundle_20260913`へ貼付け・保存し、2回ともReady復帰・エラーなし、置換前後の変数プレビューを確認した。入力SHAは実行前後で不変、出力90 bytes・SHA `2b030f2d6d937aa11885509ebc60a55e40261087a2464dcc5ddd6cca8ad81bd2`が固定期待と一致した。再コピーは649 bytes・SHA `d2a7f74e6b5038557a5b0eeca1bde4468f4d4fc402a9baaf95ba7fe5e91a317b`で、原文との差はPADのCRLFのみだった。証跡は`catalog/evidence/t01-copilot-live-generation-20260913-pad-acceptance.json`。T01単体の候補同版受入は成立したが、全T01-T10の同版受入、T09、独立再試験、負例v2、候補statusの昇格は未完了である。

## 2026-09-13 T03候補の同版生成・不受入

候補と同じ指示SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`、Think Deeper、2添付でT03を通常M365 Copilotから生成した。初回の新規会話（`https://m365.cloud.microsoft/chat/conversation/2ec1cac1-7c3f-4b29-85f8-ec80c8f53637?es=SSR`）は1コードブロック・7行・550 bytes・SHA `33302fc08266b3c698e18f1086ffc2db1dfd1e6037d10afb4ff524fad6a33a9c`だった。`Folder.GetFiles`→`LOOP FOREACH`→`.Extension = .txt`→UTF-8読取り→空の`ELSE`の最小構成で、期待する`TxtCount`／`OtherCount`集計アクションを含まないため、貼付け・保存・実行は行わず不受入として保全した。

同版・同添付で別の新規会話（`https://m365.cloud.microsoft/chat/conversation/dc9a9979-7203-41dc-94fb-3183f06760eb?es=SSR`）を再生成し、初回表示は literal な `\\*`／`=\\>` を含む7行・538 bytes・SHA `b86a9a9fd18d64a47c40b991b434d99ae5a49afa5c758d504bdce7b89f8ee26a`として原文保存した。その後の同会話「再試行」も、7行・550 bytes・SHA `33302fc08266b3c698e18f1086ffc2db1dfd1e6037d10afb4ff524fad6a33a9c`で集計アクションを含まなかった。生成結果は手修正せず、3試行すべて`generated_minimal_not_accepted`、PAD貼付け・保存・実行なしと判定した（`catalog/evidence/t03-copilot-live-generation-20260913-attempt1.json`、`attempt2.json`、`attempt3.json`）。既存finaldの10行T03成功は今回候補へ付け替えない。候補statusは`FROZEN_CANDIDATE_NOT_ACCEPTED`、Issue #5/#27はOPEN／partialを維持する。
## 2026-09-13 T04候補の同版生成・不受入

候補と同じ指示SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`、Think Deeper、2添付でT04を通常M365 Copilotから生成した。新規会話（`https://m365.cloud.microsoft/chat/conversation/7fc929a2-2d3f-4988-9d84-7b91e34809dd?es=SSR`）の初回応答は1コードブロック・9行・UTF-8 1,589 bytes・SHA `0356955358d35bdaabc31475332ebd03328323a890a4da072b0c3da967fb9f1c`だった。T04の実測9命令系列と同じアクション順ですが、`=>`矢印と`FilterParameters`括弧へ literal なバックスラッシュが残る原文のため、無修正貼付け候補として不受入にした。

同一会話の「再試行」も1コードブロック・9行・1,585 bytes・SHA `feea538a6dd9018554d162400f50d4cd07abe90ed43ef6cca864812ac626be1e`で、矢印の literal バックスラッシュを保持した。生成結果は手修正せず、2試行とも `generated_format_not_accepted`、PAD貼付け・保存・実行なしと判定した（`catalog/evidence/t04-copilot-live-generation-20260913-attempt1.json`、`attempt2.json`）。既存finaldのT04成功を今回候補へ付け替えず、候補statusは`FROZEN_CANDIDATE_NOT_ACCEPTED`、Issue #5/#27はOPEN／partialを維持する。

追加仮説として、同じ指示SHA・bundle SHA・Think Deeper・2添付を維持した新規会話（`https://m365.cloud.microsoft/chat/conversation/fd0a3c67-b305-46a4-92f9-80109bd11611`）へ1回だけ送信した。応答は1コードブロック・9行・1,585 bytes・SHA `feea538a6dd9018554d162400f50d4cd07abe90ed43ef6cca864812ac626be1e`で、DOMの`pre code`文字列にも5箇所の`=\>`が現れ、保存RobinとDOM SHAが一致した。新規会話でも同じ矢印エスケープが再現したため、既存会話・ローカル保存経路に限定された現象ではなく、生成回答由来の形式不履行と切り分けた。入力／出力パスの変更は依頼本文で明示した範囲のみであり、生成Robinは無修正保全、PAD貼付け・保存・実行は行っていない。証跡は`catalog/evidence/t04-copilot-live-generation-20260913-attempt3.json`、`.robin`、`.response.txt`、`.sent-body.txt`、`catalog/evidence/t04-next-hypothesis-20260913e.json`。

## 2026-09-13 T05候補の同版生成・再試行

候補と同じ指示SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`、Think Deeper、2添付でT05（合成ExcelのB2単一セル書込み→別名保存）を通常M365 Copilotへ送信した。会話URLは`https://m365.cloud.microsoft/chat/conversation/e360f2ad-f623-4290-8e92-7f68e999c9e2?es=SSR`。初回応答は1コードブロック・4行・564 bytes・SHA `299628c3cb205aa8219d23f005b4a7fe99ac76518ce688f497368ccfd87524ca`で、`Instance=\> ExcelInstance`のliteralバックスラッシュを含んだため、原文をそのまま不受入保存した。

同一会話の再試行は1コードブロック・4行・563 bytes・SHA `be40e6b337620f1c76ba650b202f316d4b80b339de1c859fe1cb55a9f2714911`で、`Instance=> ExcelInstance`の矢印、4アクション、入力・出力パス、B2／T05-Changed指定が確認できるクリーンな候補となった。生成原文は手修正せず`catalog/evidence/t05-copilot-live-generation-20260913.robin`へ保存したが、物理EscapeでComputer Useが停止されたため、専用PADへの貼付け・保存・2回実行・再コピーは未実施である。初回原文は`...-attempt1.robin`、両メタデータは`...-attempt1.json`／`...json`に固定し、既存finaldのT05成功を今回候補へ付け替えない。候補statusは`FROZEN_CANDIDATE_NOT_ACCEPTED`、Issue #5/#27はOPEN／partialを維持する。

## 2026-09-13 T05候補のPAD実機受入

クリーンな再試行Robin（指示SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`、生成SHA `be40e6b337620f1c76ba650b202f316d4b80b339de1c859fe1cb55a9f2714911`）を、PADコンソールで新規作成した空フロー`無題 (2)`へ無修正貼付け・保存した。Designer表示は4アクションで、Excel編集可能起動（ReadOnly=False）→B2書込み→別名保存→終了の順序と`ExcelInstance`参照を確認した。作成ダイアログの名前欄はComputer Useの入力APIで設定できず自動名となったが、既存フローの再利用・Robin手修正はしていない。

2回のRunはともに準備完了復帰・開始再有効化を確認した。出力`catalog/evidence/normal-chat-t05-final.xlsx`は両回でB2=`T05-Changed`、A1は入力と同値、入力SHA `e94bd14c919375c76e7114f63031a18a7317a1ce15b55ce99e487fac9ddbbad6`は不変だった。Excelが保存時に更新するOOXMLメタデータのため出力SHAはrun1 `44940c8d1a940a5ead0494a533a4461a97b2522d935e90c9ec66ee23fe08c6e9`（9005 bytes）からrun2 `2d7f921b1bafb1dd36d5de691cf37d2016ed3a6ceb47b50e01f3ac7a2c285358`（9006 bytes）へ変化したが、セル値と「B2だけを変更」の照合は一致した。詳細は`catalog/evidence/t05-copilot-live-generation-20260913-pad-run-1.json`、`...-run-2.json`、`catalog/evidence/normal-chat-t05-output-comparison-20260913.json`。

run2後のPAD再コピー`catalog/evidence/t05-copilot-live-generation-20260913-pad-recopy-after-run2.robin`（および初回再コピー）は、生成原文とbyte一致（4行563 bytes、SHA `be40e6b337620f1c76ba650b202f316d4b80b339de1c859fe1cb55a9f2714911`）した。統合証跡は`catalog/evidence/t05-copilot-live-generation-20260913-pad-acceptance.json`。T05候補単体は生成・無修正貼付け・保存・2run・期待値照合・再コピーまで`PROVEN`とするが、保護候補statusは更新せず、T03/T04/T06〜T09、独立・負例・全体監査は未完了である。従って候補statusは`FROZEN_CANDIDATE_NOT_ACCEPTED`、Issue #5/#27は`OPEN／partial`を維持する。

## 2026-09-14 現行版P3-5生成・PAD受入

現行正本20260913e（instruction `6ad6f742…`／bundle `79245787…`）を通常M365 Copilot新規会話 `https://m365.cloud.microsoft/chat/conversation/a505b6cc-1517-4959-8978-63f495d900c6`へThink Deeper・同版2実添付で1回送信した。評価者用期待値は渡さず、応答DOMの単一preから2行Robinを無修正で保存した。専用空フロー `RobinKnowledgeP35CurrentBundleLive20260914e`（Designer PID 34916）へ貼付け・保存・再コピーし、権威サマリー`2 選択されたアクション`を確認した。2回Runとも成功し、変数プレビューで`FormattedDateTime2=2026-09-14`を確認した。生成SHA `004ef2f3…`、PAD再コピーSHA `19cf8878…`はCRLFシリアライズ差のみで正規化一致し、生バイト一致は主張しない。要求本文は実行日の日付を検証する同版入力であり、`yyyy-MM-dd`以外の書式トークン、既存変換アクション編集経路、元入力から生成への厳密保持は未証明である。paste helperはタイムアウトしたが、同じ1回貼付けのDesigner状態をUIAで独立確認し、再貼付けはしていない。証跡は`catalog/evidence/p35-current-bundle-live-20260914e.json`、`p35-current-pad-paste-save-20260914e.json`、`p35-current-pad-run1-20260914e.json`、`p35-current-pad-run2-20260914e.json`。旧P3-5 PASSは現行版へ移していない。P3-6、T04形式、T10厳密保持、負例v2、A〜G監査は残件で、Issue #5/#27はOPEN / partialを維持する。

## 2026-09-14 現行版P3-6の送信・実機PAD受入

現行正本20260913e（instruction SHA `6ad6f742…`／bundle SHA `79245787…`）を、通常M365 Copilot新規会話 `https://m365.cloud.microsoft/chat/conversation/724624ae-3f2d-4c82-92a6-f4e40a51f64d`へThink Deeperで1回送信した。指示全文は本文へ含め、同版bundleを実添付した。評価者用正解コード・期待値・Issue本文は渡していない。固定P3-6依頼（依頼SHA `b328ce94…`、末尾LFを除く意味SHA `972c80a0…`）を全文で含むcomposer本文の意味SHAは `bd47ec51…`、送信回数は1回だった。

応答DOMの単一`pre`から12行のエラー処理Robinを無修正で保存した（生成SHA `a1544f08…`、458 bytes）。`ON ERROR FileNotFoundError`のアクション単位処理で`NewVar=named`と欠損LastErrorを得る構造を含み、ブロック側利用者定義`FileNotFound`の一致や`ErrorHandled`／`ErrorHandledDefault`設定は実測で成立していない。生成回答・DOM・依頼・添付ハッシュは `catalog/evidence/p36-current-bundle-live-20260914e.json` と `catalog/generated/normal-chat-20260914e-p36-current-live/` に原記録を保全した。

専用空フロー `RobinKnowledgeP36CurrentBundleLive20260914e`（Designer PID 19332）へ生成Robinを無修正で1回貼付け・保存・再コピーした。Designer権威集計は`4 アクション`で、再コピーは先頭`BLOCK`末尾空白とCRLFの差を含む471 bytes（SHA `ae5bcb55…`）だった。最初のpaste helperには12行をアクション数として渡してタイムアウトしたが、これは入力パラメータの不整合であり生成失敗ではない。空フロー確認後の同一1回貼付けをUIAで確認して保存し、重複貼付け・自動unescape・手修正は行っていない。

PADを2回Runし、両回とも成功、`NewVar=named`、`LastError`に`見つかりません`を確認した。欠損fixtureはRun前後とも不在で、ブロック側ルール一致・生成からPADまでの生バイト厳密一致は`NOT_PROVEN`のまま残す。P3-6は現行版の生成・無修正貼付け・保存・2回機能受入へ追加するが、T04形式、T10厳密保持、負例v2、最終A〜G監査は未完了で、Issue #5/#27はOPEN / partialを維持する。

## 2026-09-14 T01現行版独立再試験

現行正本20260913e（instruction SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12`、manifest `copilot/knowledge-bundle-manifest-20260913e.json`）を、通常M365 Copilotの新規会話 `f0af1bd2-f257-4ba4-9b22-c3da0cce9ef9`（Think Deeper、指示＋bundle実添付）で独立T01依頼へ適用した。公式「応答のコピー」で得た応答は2321文字、DOM上の`pre`は1件・3行・646 bytes（SHA `2209d9ce9437c141345c3f01a0cfd12bd6d6ed4dd0668cf0a78ae17479c5ee47`）で、生成Robinは無修正で保存した。公式コピー本文SHA（末尾LFなし）は`3e50575fc8bb7406e248140b1d7f47639faa185ceec0f21a3ef04cfb576659cc`として、DOM原文・ローカル保存の末尾LF差と分離記録している。

生成Robinを新規専用空フロー `RobinKnowledgeT01IndependentCurrentBundleLive20260914e`（Designer PID 31848）へ無修正貼付け・保存・再コピーし、3アクションを確認した。PAD再コピーは649 bytes・CRLF（SHA `d2a7f74e6b5038557a5b0eeca1bde4468f4d4fc402a9baaf95ba7fe5e91a317b`）で、生成原文との差はCRLFのみ（正規化後一致）だった。2回Runとも準備完了復帰し、出力は各90 bytes・SHA `2b030f2d6d937aa11885509ebc60a55e40261087a2464dcc5ddd6cca8ad81bd2`、入力SHA `2866f343e2cc6997d936914c2dfd1baa070eea5b813e14bdd4cde9d70cfbe47f`は不変。既存出力はRun前後に退避・同一SHAで復元した。証跡は `catalog/evidence/t01-independent-current-output-comparison-20260914e.json`、paste/save、recopy、run1/run2、生成ディレクトリ `catalog/generated/normal-chat-20260914e-t01-independent-live/`。

この独立T01は現行版で`PASS_CURRENT_20260914E_INDEPENDENT_PAD_ACCEPTED`とするが、生成元→PADの厳密バイト保持は評価していない（CRLF正規化後一致のみ）。T04形式不受入、T10厳密バイト保持、独立T04/T10、P3正例、負例v2、A〜G全体監査は残り、Issue #5/#27はOPEN / partialを維持する。

## 2026-09-14 A〜G必須要件の原証跡対応付け

Issue #5/#27の必須A〜Gを、教材正本・原probe／別空フロー再利用・現行版live evidenceへ対応付けた機械可読台帳を追加した。台帳は各チェックの証跡ファイル存在、測定範囲、未証明境界を分離し、過去版のPASSを20260913eへ付け替えない。A〜G全体のstatusは`PARTIAL_REQUIRED_TRACEABILITY_GAPS`、`a_to_g_complete=false`、IssueはOPENのままである。独立T04は比較・再調整・PAD窓観測をリンクしたが、Run1 xlsxは`NOT_CAPTURED`、新しい2-run pairは不可視DesignerかつComputer Useネイティブアプリバインディングなしのため未開始である。T10は機能／許可範囲と厳密生バイト保持を分離し、後者は`NOT_PROVEN`を維持する。

対応付けの正本: `catalog/evidence/issue5-a-g-trace-20260914g.json`。`catalog/index.json` と `catalog/coverage.json` の `final_a_g_trace` から辿れる。検査は `tests/Test-Issue5AGTrace.ps1` で、A〜Gの全リンク、現行版ハッシュ、T04候補partial、Run1未取得、最新PAD窓観測、T10厳密未証明、Issue OPEN／PR #31 MERGEDを固定する。

## 2026-09-14 T04 Designerプロトコル起動の追加観測

`ms-powerautomatedesigner:` の登録プロトコルを1回だけ起動観測したが、`ACCESS_DENIED`で新規プロセス・可視窓は生成されなかった。既存のPAD.Console.Host／PAD.Designerは応答中でもHWND 0・タイトル空のままで、Computer Useのネイティブアプリ一覧も空だった。貼付け・保存・Run・Copilot再送・Robin編集・第3回Runは行わず、現行T04の`candidate_partial`、Run1 `NOT_CAPTURED`、新規pair未開始を維持する。原証跡は `catalog/evidence/t04-independent-current-pad-window-observation-20260914i.json` で、A〜G台帳と各集約の`latest_window_observation`から参照できる。

その後、既存`explorer.exe`経由でPAD ConsoleのAppsFolder起動を15秒観測したが、新しいPADプロセス・可視窓は発生しなかった（`catalog/evidence/t04-independent-current-pad-window-observation-20260914j.json`）。したがってDesignerの一意なPID／タイトル／HWND／UIAは依然取得できず、実行ペアは開始していない。
