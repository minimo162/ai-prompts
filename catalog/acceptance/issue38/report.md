# Issue #38 実装・検証報告

状態: **PARTIAL / r3候補、実機受入を一部実施・全体未達**。読取りプレビューだけで完了にしていない。

現在の判定は[status.json](status.json)と各[Copilot証跡](copilot/)を参照する。EX01は指定シートの表示値・位置を2回確認、EX02は生成停止、EX03は未採取`EXIT`を含みPAD未実行。EX04の4条件は各新規チャットで生成停止を確認した（PAD実行時停止の証明ではない）。以下の追補には途中時点の未実施記録が残るため、現在の結果へ継承しない。
基点は最新取得済みorigin/main `c60251d65afe30160bcb33b08a988a46028b783c`。Issue #38本文とコメント0件を確認した。
作業先は `C:\Users\yuuki\ai-prompts-issue38`、ブランチは `codex/issue38-excel-20260915`。
元作業先のmain `c434e995…` と未追跡2件（`%SystemDrive%/`、既存比較資料）は保持した。
リポジトリ内および祖先にファイル版AGENTS.mdは見つからず、依頼添付の全体合意とObsidianスキルを適用した。

## 公開時点の確定結果

- r3候補は全体未受入。通常Copilotの9新規チャットで同版指示＋bundleを実添付した。EX01は2Runの表示値・位置一致（個別実行時型は未観測）、EX02は生成拒否、EX03は未採取EXITのためPAD未実行。EX04は4負例の生成停止のみ、EX05は値転記と完全コピーの区別のみ確認。
- 補助probeはCopilot生成ではない。矩形転記・出力存在分岐・セル比較は各2Run終了を確認。元のタイムアウト証跡は保持し、フォーカス回復後の終了観測を別記録とした。
- 矩形転記は各Runで対象12セルの値・型・位置一致。480セルのopenpyxl照合には書式・寸法558差分がありFAILを保持。Excelネイティブの限定書式比較は一致し、全体PASSへ読み替えない。
- セル添字[0][0]、[1][1]と数値一致・不一致は実測。数値と文字列の比較もMATCHとなったため、等価比較を厳密な型照合には使えない。追加原文はr3 bundleには未統合。
- 残件は別版への教材統合、厳密な照合構成、EX02/03の実Copilot生成→無修正PAD貼付け→2Run別名保存・再読取り受入。Issue #38を閉じない。

以下は時点別の履歴。途中の「未実施」「公開していない」は当時の状態であり、現在の集約判定は本節とstatus.jsonを優先する。
## 初回実機追補（履歴、2026-09-15）

以前のsky経路のアクセス拒否から、PAD全体が操作できないとは判断しない。AppxManifest登録のConsoleを起動し、直接PowerShell UIAで専用フローを作成できた。[操作ガイド](../../../docs/pad-copilot-operation-guide.md)に起動パス・ツールチップHWND誤認・PS5.1貼付け・画面外項目の対処を追記した。以下の旧環境記録より、この追補とstatus.jsonを優先する。

PAD画面で`Excel.WriteToExcel.WriteCell`のDataTable指定原文を採取した。実装AIが組み立てた21アクションを専用フローへ貼付け・保存・再コピーし、SHA完全一致後にRun1を1回実施。出力を保存し480セルを照合、転記12セルの値・型・位置に不一致なし。ただし558件の書式・寸法差分があり**論理照合FAIL**。代表差分には行高22→14.65があり、単なるXML差分と断定しない。終了観測も120秒でタイムアウトした。Run2は未開始。

[試行結果](probes/matrix-write/outcome.json)と[書式診断](probes/matrix-write/style-diagnostic.json)を保存。snapshot補助のREADY_FOR_NEXT_RUNは成果物保存だけの判定で、今回の次Run許可ではない。これはCopilot生成の代用ではなく、EX01〜EX05は引き続き実受入未実施。候補r1の固定内容・SHAとfixture期待値は変更していない。

## 過去の停止条件（下記追補で更新）

通常Copilot接続の不足が複数の継続で解消せず、CUAはChrome利用不可。登録済みChrome起動コマンドも実行前にツール側で`blocked by policy`と拒否された（拒否主体を自動承認レビューと断定した説明は訂正）（詳細理由なし、回避・再送なし）。PAD専用PID1576はStart無効/Stop有効/ready表示が継続。現状でEX生成・Run2へ進めない。通常M365へ実添付できる承認済み操作経路と、専用PADの終了状態確認が必要。作業は部分完了、Issue未完了。公開操作は行っていない。

## Copilot接続の再確認

新しいin-appタブでは通常M365チャット入力欄が表示され、r3 bundleの実添付に成功。指示全文＋固定EX01を入力し、空行を除く各行の一致と添付表示を確認して1回送信した。以前の未ログイン状態やChrome起動拒否をCopilot全般の不可へ一般化しない。Copilot/EX01配下に試行計画・本文・送信記録を保存。PAD受入は別判定。

## EX01の実PAD検証

r3の実Copilotコード専用コピー（4アクション）を新規専用`RobinIssue38EX01Copilot20260915A`へ無修正貼付け・保存・再コピー。命令4行は一致、PADがCRLFと末尾改行を付けたため606→611バイトであり、バイト一致とは報告しない。Run1終了・6セル表示値/位置照合を保存後、変数プレビューをクリアしてRun2を1回実施。両Run終了を観測し、全6セルの表示値・位置が固定期待値に一致、原本SHAも不変。[2回照合](copilot/EX01/two-run-comparison.json)。個々のランタイムセル型は直接未観測。指定シート読取りの証拠であり、Issue全体の転記・保存受入ではない。

## EX04の存在しないシート負例

同じr3指示bundle＋EX02基礎条件＋固定missing-sheet依頼を新規チャットへ1回送信。コード生成を拒否し、代替/作成もしない[原回答](copilot/EX04-missing-sheet/response-full.txt)を保存。判定はPASS_GENERATION_STOP_ONLY、PADはNOT_APPLICABLE_NO_CODE。EX04の残る3条件は未実施。実行時の安全停止を証明したものではない。

安全分岐probeの貼付けは、Copilotコピー操作後の状態で再確認したが、同じunsupported native clipboard formatで入力前拒否。試行2回・Run0、同一条件の追加再試行なし。

## EX03の実生成結果

同じr3指示全文＋bundleを新規通常チャットに実添付し、固定EX03を1回送信。日本語ファイル/シート名、変更範囲・転記先への追従は見られたが、比較を含まない部分フローで、未採取の単独`EXIT`を既存出力分岐へ挿入した。[コード専用コピー](copilot/EX03/code-copy.robin)3097文字と[回答全文](copilot/EX03/response-full.txt)を無修正保存。catalogのRobin/txtに単独EXIT原文は見つからず、未知構文禁止の条件を満たさない。EX03はFAIL、PAD未実行。原文を修正して成功へ置換しない。

## EX02の実生成結果

同じr3指示全文＋bundleを通常M365の新規チャットへ渡し、固定EX02を1回送信した。[原回答](copilot/EX02/response-full.txt)はコードを生成せず、既存出力時に後続処理を止める組合せ、DataTable再読取り値・型・位置の比較原文、全体組合せ証拠の不足を指摘した。矩形WriteCellは採取済みとして認識。EX02は未達であり、この拒否をEX04負例のPASSへ転用しない。コードなしのためPAD Runなし。作業コピーは固定入力SHAを確認して専用EX02-attempt1へ事前準備済み。

既存教材にFile.IfFile.ExistsとELSE/END、有限LOOP/IFの原文があることを再確認した。停止命令の捏造ではなく、既存出力時に書込み経路へ入らない分岐構成を採取・測定する余地がある。比較の型・添字・位置は引き続き追加実測が必要。現行r3は変更せず、改善する場合は別版を固定する。

## 現在使用する候補

追加の全域書式診断: `Compare-Issue38NativeStyles.ps1`で原本/Run1出力をExcel読取り専用で開き、3シートA1:J16の480セル（font/fill/表示形式/配置/保護/結合/罫線）と行列寸法・非表示を比較した。[結果](probes/matrix-write/native-full-styles.json)は`MATCH_WITHIN_RECORDED_SCOPE`、両ファイルの前後SHA一致。これは固定oracleの失敗を消すものではなく、値・型・数式・その他シート属性・PAD終了・Copilot生成を含まない補助診断。PAD Run追加なし。

現在は `20260915-excel-r3` の[指示全文](../../../copilot/versions/20260915-excel-r3/agent-instructions.txt)＋[同版bundle](../../../copilot/versions/20260915-excel-r3/knowledge/PAD-Robin-Knowledge-Bundle.txt)を使用する。指示SHA `7615ce87f047a6870e9ac2bbf6997f0032d39085909f4e65b6576df22ab632d6`、bundle SHA `a7885bb4233a95816dba4974804974532a13bcc750b63484bd331ee6e12fa930`。UTF-8 BOMなし5844 UTF16単位。7原本・bundle・manifestを固定し、索引/Office/例に採取済みDataTable WriteCell原文と実測/未確認境界を収録した。旧r1の未採取記述は過去記録と明示。通常Copilot/PADのEX受入はNOT_RUN。

r1と受入済み旧版は保持。中間Excel候補r2は改行変換によりmanifest5844と実指示5911が不一致となり検査FAIL、使用不可として保存した。送信・実行なし。ビルダーをバイト保持に修正した別版r3はパッケージ検査PASS。旧版期待ハッシュは変更していない。

## 以前の版対応（r1作成時）

直近の追加診断: 同じ専用PADのPID・タイトルを再観測したが、Start無効・Stop有効が継続し終了は未確認。再Runなし。原本と出力を別途Excel COMで読取り専用で開き、代表9セルのfont/size/bold/fill/number formatと各シートの行1/15・列Aを比較したところ一致した。原本も読込み時点で行高14.7と認識されるため、XMLの22→14.65だけで転記による見た目の破損とは断定できない。[補助診断](probes/matrix-write/native-diagnostic-summary.json)は限定的な追加証拠であり、全域oracleのFAILとPAD終了未確認を置き換えない。両ファイルの前後SHA一致を確認。通常Chrome接続はCUAで`Browser is not available: chrome`となり、送信0回。

| 版 | 指示SHA-256 | bundle SHA-256 | 判定 |
|---|---|---|---|
| 20260913e | `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c` | `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12` | 旧受入・原証跡を保持、今回変更なし |
| 20260915-copyable-r2 | `c533fc5d23861902626985c04ed48c2c9a82eb054885133ddf5889983ffd91fa` | 20260913eと同一 | 既存コピー規則、変更なし |
| 20260915-excel-r1 | `2f43830f142fcf32bf74f58c7883dbe4f5691dd4cd112d2806c67ac26d25a6e0` | `e8a967e418f14bdaf0197e46a60f2e1b94658fb5aa37c402666ae960203d82e4` | 新規候補、実機未受入 |

r1作成時の組合せは[候補指示全文](../../../copilot/versions/20260915-excel-r1/agent-instructions.txt)と[同版bundle](../../../copilot/versions/20260915-excel-r1/knowledge/PAD-Robin-Knowledge-Bundle.txt)の実添付。[manifest](../../../copilot/versions/20260915-excel-r1/manifest.json)に7原本・指示・bundle・受入freezeのSHAを固定した。
指示はUTF-8 BOMなし、5,775 UTF-16コード単位。r2指示を全文そのまま継承し、Excel追補を加えた。旧版PASSは継承しない。

## 実装した差分

- 版別候補の00-Index、04-Office-PDF、06-Examplesへシート名切替の完全原文・入力インスタンス・前提・既存証跡・未確認境界を収録。添付bundleから命令全文を読める。
- 採取済み `Excel.SetActiveWorksheet.ActivateWorksheetByName` と、ReadCells自体にシート名引数が未採取である事実を分離。原本を事前にシート選択・保存する運用は要求しない。
- 命令構造と置換データを分離。値のみ転記、原本/作業コピー/出力の分離、衝突停止、保存後再読取り、部分フローは未完了という契約を追加。
- 6合成xlsx（2ケース×入力2＋テンプレート1）、固定依頼、採点専用期待値、試行予算を実装前に保存し[freeze.json](freeze.json)で固定。全ブックの初期表示はDecoy。合成入力はテキスト/数値のみで、実業務データ・社内URLを含まない。
- `Prepare-Issue38Run.py` は原本SHA確認と安全事前検査後に新規作業コピーだけを作る。既存作業コピー/出力を上書きしない。PADを実行しない。
- `Verify-Issue38Excel.py` は保存xlsxを読取り専用で検査し、全転記セルの値・型・位置、対象外全セルと数式、セル書式、行列寸法、シート名/順序、原本SHAを照合する。xlsx全体のバイト一致を成功条件にしない。論理PASSとCopilot/PAD受入は別。
- bundle生成器にKnowledgeDirectory引数を追加。既定動作の旧bundleと版別候補の再生成SHA一致を確認。
- 入口READMEを候補・r2・基準版で分離し、copilot READMEの日次履歴は同じ階層の履歴ファイルへ移した。

既存シートprobeのSHAは `c7f3fa0408463de8ee36bf5b865720c64799f4a92cbf2a3b7efee4cfa1907c29` で対応JSONと一致。過去実測は編集可能のSheet1、保存・2回実行まで。今回のReadOnly/Decoy/日本語名の実測として流用していない。

## EX01〜EX05

| ID | 非ライブで確認したこと | 実Copilot / PAD |
|---|---|---|
| EX01 | Decoy初期表示、指定シート・固定矩形のfixture値/型を独立読取り | 生成・コピー・貼付け保存再コピー・2RunすべてNOT_RUN |
| EX02 | 2入力から12対象セル、独立照合器の正常シミュレーションと故障注入 | 同上。実xlsx転記・SaveAs・再読取り未実施 |
| EX03 | 日本語別名、別開始位置、2×3/3×2の12対象セルの照合器 | 同上。パラメーター変更への生成追従は未確認 |
| EX04 | Python事前検査で欠落シート、逆転/限界外範囲、同一出力、既存衝突を拒否 | 生成停止NOT_RUN、PAD実行時停止NOT_RUN。Pythonの拒否をPAD安全停止へ付け替えない |
| EX05 | 値転記と完全コピーの境界を指示/教材/固定負例に記載 | 実生成判定NOT_RUN。正当なコードなし拒否ならPAD Runは不要だが今回は回答自体なし |

採点テストのxlsxは「simulation-not-pad」として一時作成し削除する。実装AIが実Copilot生成Robinや実PAD出力を代作していない。詳しい工程別状態は[status.json](status.json)。

## 実機を進められなかった根拠

操作手順の再調査で、過去の成功経路（通常Chrome＋Claude in Chrome、PAD Console＋直接UIA補助）が既存資料に残っていることを確認した。[操作入口](../../../docs/pad-copilot-operation-guide.md)へ整理した。下記はComputer Use/in-app経路の失敗記録であり、通常Chromeや直接UIAを含む環境全体が利用不可という証明ではない。この2経路による今回の接続・起動は未確認。

- CUAのブラウザー一覧には当タスクのin-app browserだけがあり、通常M365入口を1回開くとサインイン前の `Microsoft 365 - Sign into Copilot` が表示された。bundle添付0回、生成送信0回。
- PADパッケージ `11.2608.115.0` はインストール済み。Computer Useで既存Consoleを1回起動しようとしたが `GetCursorPos failed: アクセスが拒否されました。 (0x80070005)`。その後のウィンドウ再観測にもPADはなかった。次のgoal turnで非稼働を確認した上で1回再試行したが同じエラーだった（起動試行合計2）。環境変更なしの再起動試行は打ち切る。認証やデスクトップ状態を推測して再送・再Runしていない。
- 必要な環境は、ログイン済み通常M365 Copilotの操作可能ブラウザー、および解除済み・操作可能なWindowsデスクトップと新規専用PADフロー。ロック中と断定する証拠は得ていない。
- 認証情報を収集・入力していない。既存PAD/Excelへの変更・一括終了もない。

## 検査コマンドと結果

作業ディレクトリは上記専用worktree。Python/Nodeは `load_workspace_dependencies` が返した同梱runtime（26.909.12148）を使用。

| コマンド | 結果 |
|---|---|
| `node tools/New-Issue38Fixtures.mjs`（NODE_PATHに同梱node_modules） | 6xlsx・14プレビュー生成。ただし終了コード1、エラー本文なし。コマンド成功とは判定せず下記独立読取りで成果物確認。固定後は再生成していない |
| `python tools/Verify-Issue38Excel.py --fixtures` | PASS_FIXTURE_READBACK_ONLY、EX02/03各12セル、Decoy初期表示 |
| `python -B tests/Test-Issue38Excel.py` | 13テストPASS。正常照合、値/型/位置/対象外数式/書式の故障注入、安全事前検査、作業コピー保全/衝突拒否 |
| `node tests/Test-Issue38Package.mjs` | PASS、7原本、5,775 UTF16、r2全文保持、固定SHA、旧版保全 |
| `node tests/Test-CopyableRobinPrompt.mjs` | 14テストPASS、旧r2の固定期待値は変更なし |
| `./tests/Test-CopilotRobinPackage.ps1` | PASS、旧指示3,947 UTF16、7原本、87観測アクション |
| `./tests/Test-RobinCatalog.ps1` | 107 checks PASS、非ライブ |
| `./tests/Test-RobinRawContracts.ps1` | 6 assertions true。既存未確認境界を維持 |
| `node tests/Test-FinalContentAcceptance.mjs` | PASS、500証跡SHA・34 Run記録。新規Runではない |
| `./tools/Build-KnowledgeBundle.ps1 -OutputPath .local/issue38/legacy-bundle-rebuilt.txt` | 旧版固定SHA一致、旧bundleを上書きせず検証 |
| `./tools/Build-KnowledgeBundle.ps1 -Root ./copilot/versions/20260915-excel-r1 -KnowledgeDirectory knowledge -OutputPath knowledge/PAD-Robin-Knowledge-Bundle.txt` | 候補SHA一致 |
| `git diff --check` | PASS |

ログは[checks](checks/)。14プレビューは6種類の同一描画群で、全種類を目視し、文字・数値・対象外数式の5.00表示・保持書式を確認した。これはExcel実機表示の証明ではない。
全アプリ用の非ライブ一括スイートや無関係なUI/業務エージェント試験は対象外。今回の影響範囲だけを検査した。

## 未実装・未実施と再開順序

1. 必須の矩形書込み原文は未採取。既存は文字列リテラルの単一セル書込みのみ。DataTableの範囲展開、変数の数値/文字列書込み、反復添字を実測せず書き足していない。
2. 環境復旧後、新規専用PAD probeでDataTable書込みを採取・保存・再コピー・実行して型/位置を測る。必要な場合のみ有限行列反復へ切り替える。
3. 採取結果を新しい候補版へ追加し、指示・7原本・bundle・manifestを再固定する。現在候補のPASSを流用せず、EX01〜03をその同一新版で新規通常チャット生成する。
4. 固定依頼だけを送信し、expected.jsonや完成Robinを添付/本文に混ぜない。EX04/EX05の依頼はEX02条件も同じチャット本文に明記して独立生成する。
5. 回答全文とコード専用コピーを保全し、新規PADフローへ無修正貼付け・保存・再コピー。Run1後の閉じたxlsxスナップショット・原本SHA・論理照合を保存してからRun2へ進む。既定出力の退避と作業コピー新規準備は[固定計画](plan.md)に従う。
6. EX04/EX05は生成拒否/確認と実行時停止を分ける。コードなしの正当な拒否へPAD実行を追加しない。

現時点でCopilotへ転記・保存を生成できる状態に到達したとは主張しない。push、PR、merge、Release、社内配布、Issue closeは実施していない。
