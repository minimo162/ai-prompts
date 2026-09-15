# EX02 r4 ローカルレビュー資料

**判定: 部分実装・実生成を実施したがEX02未受入。** r3で不足していた教材本文を統合し、通常M365 Copilotへ固定依頼を再送した結果、拒否理由は「フロー自身の厳密な型照合原文が未採取」に絞られました。型照合・無修正PAD 2Run受入は未達です。Issue #38全体やEX03以降を完了にしていません。

## 開始状態と保全

- 元作業先: `main` / `d0bd39699fcc92773ef0238f29701f9e310a7693`。fetch後のorigin/mainも同じ。元mainの未追跡 `%SystemDrive%/` と `docs/agent-approach-comparison-2026-09-07.md` を保持。
- 証跡worktree: `C:\Users\yuuki\ai-prompts-issue38` は同じSHAのdetached、追跡変更・未追跡なし。ignore対象の `runs/EX02-attempt1`、`EX03-attempt1`、`probe-matrix-A` は存在し保全。
- 未使用ブランチ `codex/issue38-ex02-r4-20260915` をこのworktreeで作成。reset/clean/worktree削除なし。終了HEADとpatchは同梱のレビュー用エクスポートのmetadataで特定する。
- 祖先・repo内のファイル版AGENTS.mdなし。利用者添付のGlobal working agreementsとObsidian手順を適用。
- GitHub: IssueはOPEN、最新コメントはPR #39の部分結果（2026-09-15 09:30:51Z）。GitHubのr3拒否/558差分FAILとローカル基点は一致。r4変更はローカルのみでGitHubには未反映。
- `protected-files.json`の192ファイル（旧候補、基準版、fixture、固定依頼・期待値、原回答・probe・既存run成果物）は全SHA一致。旧status全文は`prior-status.json`へ保全。凍結r4一式10ファイルのSHAは`candidate-files-sha256.json`。

## 拒否原文と不足の分類

| 分類 | r3の拒否に対応する不足 | 今回の変更・境界 |
|---|---|---|
| 採取・測定済みだがbundle未収録 | `File.IfFile.Exists + ELSE/END`の既存/未存在分岐。`SET ... TO ExcelData[0][0]` / `[1][1]`とIF比較 | output-guard、scalar-compareの完全原文とSHAを02-Control・06-Examplesに収録。過去の各2Run証跡を再利用。新たな成功として再計上しない |
| 命令はあるが組合せ例・説明が不足 | 入力2冊→シート→矩形WriteCell→SaveAs→Close→読取り専用再開→2矩形再取得の全体と安全分岐の配置 | 実測21アクション全文を04-Officeへ収録。06-ExamplesへELSE内に全Excel処理を置く構成例と、12セルの定数添字比較候補を追加。統合例は未実行と明示 |
| 実際に未採取・未検証 | フロー内の厳密な型識別、全12セルの型比較、統合された生成フローの実機受入 | 未証明のまま保持。数値/文字列の等価一致で型PASSにしない。追加採取を試みる前段の専用フロー名入力が反映されず、画面をキャンセル |

r3の拒否は「安全停止まで含む完成例」「保存・再読取りの完全原文」「DataTable同士の値・型・位置照合」の不足でした。r4の実回答では前二者を既知として認識し、次を明記しています。

> 値と位置の転記・保存・再読取りまでは根拠がありますが、必須の「フロー自身による型照合」に必要なPAD原文が未採取だからです。

原回答は`response-full.txt`（2555 UTF-16単位、SHA `2738b7e25c50be63e5f2fc57268c08b8e9a7293f61a8708ab3fd6e07bd8196b5`）。回答が提案した「既存出力で再実行」は補助負例であり、要求された別成果物の正常Run2の代用には採用しない。

## 重要な差分

- 新規 `tools/Build-Issue38Ex02Candidate.py`: r3の指示・7原本・bundle・採取原文SHAを照合してからr4を作成。既存出力ディレクトリは拒否。一時ディレクトリへの再生成と全10ファイルのバイト一致を検査可能。
- 新規 `copilot/versions/20260915-excel-r4/`: 7原本＋指示＋bundle＋manifest。r3を変更せず、r4内の旧Excel追補を現在の説明へ統合。01-Basics、03-Files、05-UI-Webはr3とバイト同一。
- 新規 `tools/Compare-Issue38Ex02.py`: 既存Verify-Issue38Excel.pyを変更せずそのFAILを継承。対象12/対象外468の各セル座標・期待/実際の値と型タグ、数式、書式属性別・行列寸法差分、出力読取り前後SHAと原本SHAを分けて出力。
- 新規 `tools/Measure-Issue38NativeRoundtrip.ps1`: テンプレートの新コピーだけを専用Excel COMで開き、新規出力へSaveAsする対照実験。セル書込み0、原本/作業コピーSHA不変。既存Excelへのattachや一括終了なし。
- `tests/Test-Issue38Package.mjs`: r4を追加し、原文全文のbundle収録・証跡SHA・型未証明表記を検査。r1/r3や基準版の固定期待ハッシュは維持。
- 新規 `tests/Test-Issue38Ex02.py`: 値違い、数値を文字列化、位置ずれ、対象外数式、書式・行高差分の負例、旧558 FAIL保持、再生成一致など9テスト。
- README、copilot/README、操作ガイド、report/status: r4入口と実際の未達へ更新。旧r3の実施済み項目を「全て未実施」としていたREADMEを訂正。EX01/03/04/05の旧結果には版を明示。

構造差分の要点（説明用抜粋、実測済み完成コードではない）:

```text
IF (File.IfFile.Exists File: <今回の出力パス>) THEN
    SET TransferState TO $'''OUTPUT_EXISTS_NO_WRITE'''
ELSE
    <入力読取り→矩形転記→別名保存→クローズ→再開・再読取り>
    <全12セルの取得値と再読取り値を定数添字で等価比較>
    SET TypeState TO $'''NOT_PROVEN'''
END
```

単独EXITを作らず、存在分岐の外へ書込みが漏れない構成。等価比較のMATCHは値比較の結果であり、型の完成判定ではない。原依頼を変更したり、読取り専用フローへ縮小したりしていない。

## 凍結版と非ライブ検査

| 項目 | r4 |
|---|---|
| 版ID | `20260915-excel-r4` |
| 指示UTF-16単位 | 5867（8000以下、目安7000以下） |
| 指示SHA-256 | `eb23d43327d4c5f81987e53d3f3d3bdf59ba9699d8dcf8bf4a5cc836276add72` |
| bundle SHA-256 | `aa1fb5aff28c1cbb5ffc51d78459a51af846823a2ab168d6f32ed8bbef2096dd` |
| manifest SHA-256 | `0b81b0ac29bb3eddb53b5a9e6427fbe71769b41491b26243b31b3a6f126a8925` |
| 符号化 | 指示・7原本・bundle・manifestすべてUTF-8、BOMなし |
| 再生成 | 新規一時ディレクトリで全10ファイルのバイト一致 |

リポジトリ直下で再現（詳細出力はchecks/とnon-live-results.json）:

```powershell
node tests/Test-Issue38Package.mjs 20260915-excel-r4
node tests/Test-Issue38Package.mjs 20260915-excel-r3
node tests/Test-CopyableRobinPrompt.mjs
python tests/Test-Issue38Excel.py
python tests/Test-Issue38Ex02.py
pwsh -NoProfile -File tests/Test-CopilotRobinPackage.ps1
pwsh -NoProfile -File tests/Test-RobinRawContracts.ps1
pwsh -NoProfile -File tests/Test-RobinCatalog.ps1
node tests/Test-FinalContentAcceptance.mjs
```

9コマンドすべてexit 0。コピー14件、既存Excel13件、新EX02 9件、catalog107件、基準版500ハッシュ・34記録の静的保全を検査。EX03の既存oracleの非ライブ正例は含むが、EX03以降の実Copilot/PAD再試験は行っていない。T10の新規採取・raw-byte調査は行わず、既存静的回帰のみ。

別途 `git diff --cached --check` は **exit 1**。凍結r4の00-Index末尾に空行1件があり `new blank line at EOF` を報告します。実送信済み版のSHAを変えないため末尾を整形していません。凍結版を除いたソース・文書のdiff-checkはexit 0。検査結果を全件PASSと一括表示せず、この空行は次の新候補でのみ整理可能です。

新規テストの初回は位置ずれ負例のXMLがJ4を重複させ、後続の空セルで上書き解釈されたため1件失敗。意図した単一セル移動になるよう注入側を修正し、位置違い・対象外違いの両検出を確認した。assertionや固定fixtureは緩めていない。

独立比較（新しいevidenceファイル名を指定する。旧FAIL維持が正しい結果なのでexit 1）:

```powershell
python tools/Compare-Issue38Ex02.py --output catalog/acceptance/issue38/probes/matrix-write/run2/result.xlsx --evidence <未存在JSON>
```

## 558差分の切り分け

| 観測 | 旧矩形probe Run2を今回再検査 | 新規対照実験 EX02-NATIVE-NOOP-R4 |
|---|---:|---:|
| Excelへのセル書込み | 旧probeにあり（今回再Runなし） | 0 |
| 対象12セルの値・型・位置不一致 | 0 | 12（未転記の対照なので期待どおり不一致） |
| 対象外468セルの値・型・数式不一致 | 0 | 0 |
| 書式差分のセル | 480 | 480 |
| 行寸法差分 | 48 | 48 |
| 列寸法差分 | 30 | 30 |
| 旧oracleの全体結果 | FAIL 558 | FAIL 570 |
| Excelネイティブ指定属性 | 旧限定MATCHを保持 | 480セル/指定寸法でMATCH_WITHIN_RECORDED_SCOPE |

両出力の558差分の箇所の多重集合、行列寸法のbefore/afterが一致。旧比較器は寸法キーの集合を反復するため列挙順は一致せず、原リストは両方保存した。比較対象の並びだけを整えて箇所を照合し、保存ファイル・FAIL・期待値は変更していない。

fontではcharset/familyの補完、borderではNoneと空Side表現の違いが各480セル。列ではA:Jの定義の集約を含む。行高はXMLの22→14.65で実際の保存値が違う一方、既存のExcel読取り専用観測ではテンプレートを開いた時点から14.7と認識されていた。今回の書込み0対照でも同じ差分が出るため、矩形WriteCell固有の破損とは断定できない。ただしExcelがそう解釈する内部理由や任意テンプレートの保存保証は未証明であり、行高差を単なる表記差として合格にしていない。

検証器の変更は結果の分解・根拠追加のみ。旧oracleの検査削除・期待値変更・許容差追加はない。新旧の限定的な一致を合わせても、生成フロー内の型工程やEX02全体の受入を証明しない。

## 実試験の工程別判定

| 工程 | EX02-R4-G1 | 根拠 |
|---|---|---|
| 指示・bundle凍結/事前検査 | PASS | 指示5867、7原本、BOM、機械結合、再生成一致、旧版保全 |
| 通常M365 Copilot実添付・送信 | 実施・成功 | in-app通常chat、Think Deeper、添付1、送信1。本文62非空行を照合（rich editorの空段落・末尾マーカーはraw同一とはしない） |
| Copilot生成 | 実施・未達 | 完了回答2555単位。厳密型照合不足でコードブロック0 |
| コード専用コピー | 非該当 | コードなし。架空のcode-copyファイルは作らない |
| 未採取命令/フェンス混入検査 | 非該当 | 実行コードなし。回答を手編集してコード化しない |
| PAD追加採取の準備 | 実施・失敗 | Console画面は確認。新規フロー名入力1回が反映されずキャンセル。フロー作成0 |
| PAD貼付け・保存・再コピー | 未実施 | コードなし |
| Run1終了・別名保存・クローズ・再読取り | 未実施 | コードなし。probeやCOM実験をRun1へ転用しない |
| Run2 | 未実施 | Run1受入未達。Run間の準備操作なし |
| 生成物の独立照合 | 未実施 | 生成成果物なし。既存probe再比較と新COM対照は別ID |

元の固定EX02依頼・パスをそのまま使用。以前準備済みのwork.xlsxはテンプレートSHAと一致、result.xlsxは未存在と再確認した。既存workを再作成・上書きしていない。

## 残件と次の最小作業

- 成功: 新版教材の実装/凍結/再生成検査、旧証跡保全、比較器と負例、通常Copilot実添付・回答採取、書込み0対照による558差分の切り分け。
- 実施したが未達: EX02の生成（型原文不足）、Computer Useの新規フロー名入力。
- 未実施: 型識別の追加原文採取、生成物のPAD貼付け/保存/再コピー、Run1/2と成果物比較、EX03以降の実再試験。
- 未証明: フロー内の厳密型照合、統合フローの安全分岐と全セル比較、書式保全の全体受入。旧数値比較の実測値は-3であり、数値1/文字列1の今回PAD実測とは言わない。

次の最小1作業は、**許可済みPAD操作経路で、数値と同じ表示の文字列を区別できる型識別/型保持比較の原文を1つ採取し、正負例を検証すること**。UI上の「カスタム オブジェクトを JSON に変換」は過去inventoryに表示名のみが存在するが、DataTableで利用できるか・型が保たれるかの原文/実測はなく、候補仮説にすぎない。未知のGetType等を教材へ入れていない。

今回使用したcomputer-useスキルのguidanceは `Do not mix direct PowerShell UI Automation code in the same turn as Computer Use.` と規定するため、このターンで直接UIAへ切り替えて入力を反復していない。既存UIA経路は別ターンで現在画面を再確認してから利用可能性を判断する。ポリシー拒否の回避や認証/権限変更は不要・未実施。

型方式が確認できた場合はr4を変更せず別版・別試験IDにし、固定EX02の全工程を再生成→無修正PAD 2Runへ進める。既存出力負例を正常Run2の代わりにしない。

push、PR作成、merge、Issue更新/close、release、ブランチ削除は0件。レビュー用ローカルコミットと添付可能なbinary patchをエクスポートする。
