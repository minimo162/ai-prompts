# T10最終受入条件の出所監査

監査日: 2026-09-15 JST。開始main/origin/main: `f4fa9a2e61bfd2a2be0414eccd9e42b2d4a5e35e`（fetch後も一致）。専用ブランチ: `codex/t10-final-provenance-audit-20260915`。

## 結論: CASE B

**原依頼のT10は動作・内容の保持を要求しており、CRLF/BOM/EOFを含むraw-byte完全保持を明文化してはいない。しかし、後続の固定requestで空白・改行の逐語保持が要求され、さらにIssueの明示的な必須完了条件としてraw-byte保持が採用されている。現在の必須条件から外す変更は未承認である。**

したがって「元の表の内容保持」と「後続のraw-byte保持」が最初から同一だったとは判断しない。一方、後続条件を単なる任意の診断と認定して無断で非ブロッカーへ変更することもできない。今回の分岐条件にある「明示された必須完了条件」に該当するためCASE Bとする。最初期に存在しなかったことだけを理由に、後から明示された完了条件を無効化しない。

一次・独立ともfunctional/authorized content scopeの既存PASSは維持する。区間外raw bytesはFAIL、strictはNOT_PROVEN、取得要求1／完了1／残枠0。#5全体と#27最終版受入はそれぞれOPEN / partial、close不可。CASE A限定のA〜G・現行版全受入再監査と派生complete化は実施しない。

## A. 原依頼に存在した必須条件

- [元依頼書](../../CODEX_TASK_PAD_ROBIN_KNOWLEDGE.md) §8 T10（261行）: 「動作確認済みの既存フローを提示し、条件1つと出力名の変更を依頼する。既存の別の動作が保持されることを確認する。」
- 同§7項8（227行）: 「利用者が変えてほしい範囲と既存の入出力・変数・サブフロー・UI要素の関係を保つ。無関係な部分を作り直さない。」
- 同§5（162–165行）は採取原文を勝手に整形しないことと再コピー比較を要求するが、「完全一致は強い証拠だが、差分があるだけで即座に失敗とはしない」と明記する。**採取・証拠保存での改変禁止と、モデル出力transportのbyte一致保証は別の契約である。**
- [通常M365 Chat優先訂正](../../CODEX_CORRECTION_M365_CHAT_VALIDATION.md) §4–5は元A〜G/T01〜T10/独立再試験を維持し、無修正PAD実行・成果物照合を要求する。raw-byte/CRLF/EOF完全一致を独立の必須条件として追加する文言はない。
- 元依頼の初回Git収録は `45275ed18c47cd91d3a8ff5ac556d2b9fdec6a19`（2026-09-09）、通常チャット訂正の収録は `c6d1e8daa25c7c0b72ebf51a26911e1318937807`（2026-09-10）。Git収録日は依頼が初めて発せられた時刻そのものとは扱わない。

## B. 固定受入ケース・requestによる具体化

- [固定ケース表](../generated/acceptance-t01-t10/README.md) T10（181行）: 「指定変更のみ反映し、既存の入力・変数・別処理・エラー経路を保持」。初回収録 `45275ed…` の表も同じ期待文言であり、CRLF/EOFの明記はない。
- [20260910固定request](../generated/normal-chat-current-revision-t10-20260910/request.txt): 「添付原文の変更しない行を文字・記号・空白・改行まで逐語複写してください」「変更範囲外を逐語一致できない場合はコードブロックを出さず」。[独立v2 request](../generated/normal-chat-current-revision-t10-20260910/request-independent-v2.txt)も「空白、改行をMarkdown用に変換しない」「原文と1文字でも違う場合はRobinコードブロックを返さず」と指定する。Git収録は `725718e3689be25c049952e81003428015c806e2`（2026-09-11）。この条件は元の概要表より強いが、それだけでBOM/EOFを含む一般的transport保証までは推論しない。
- 現行[独立request](../generated/normal-chat-20260914e-t10-independent-live/request.txt)はExcel値とSaveAs先だけを指定し、16命令・既存処理・raw二重バックスラッシュ等を保持する。現行[共通指示](../../copilot/agent-instructions.txt)48行には「原文の引用符、バックスラッシュ、パーセント、改行、インデントは、置換対象として明示されない限り変更しません」がある。これも元の概要表と後続の具体化を区別して読む。
- 一次の固定送信本文はローカル `.work/finale-20260912/t10-independent/sent-body.txt`、SHA `f426277d018eecf0df3a838f3a9a8089309e2d3a35b0f5d661cc9c78029a126c`。独立request SHA `b36fc9925aabec165c10732c7890d076ba07798f9a012fa447c0b64fda414a03`。両者の具体的許可区間は[既存auditのactual.contract](t10-strict-20260914x-audit.json)の2/4行の値部分で固定済み。依頼書・期待値を新しく作り直していない。
- 一次の固定expectation `.work/finale-20260912/t10-independent/expectation.json`（固定日時2026-09-12T07:32:57.945Z、SHA `8d715ee03b724dacca85e049184259ad35cbc57f0de6190891ee9080cd767a09`）は `allowed_changed_lines:[2,4]`、`unchanged_other_lines:14`、Excel/Word/PPT実値、2 Run、手修正禁止を定める。CRLF/EOF必須の明記はない。この期待値だけからraw-byte契約を導出しない。

## C. 後続監査・明示的完了条件

- 保持されたIssueコメントで、T10のCRLF/末尾改行を明示する最古の具体的指示として確認できたのは[#27 2026-09-12T12:35:53Z](https://github.com/minimo162/ai-prompts/issues/27#issuecomment-5645919342)。原文は「T10は機能成功と許可差分外の厳密保持を別判定する。原文CRLF／末尾改行なしと、DOM保存・公式コピーの差を…限定切り分けする」「期待値や保持要件の緩和でPASSを作らない」。同コメント末尾は残件があればOPEN / partialを維持するよう指示する。
- [#5 2026-09-12T12:36:28Z](https://github.com/minimo162/ai-prompts/issues/5#issuecomment-5645922155)も「T10の機能成功と改行等を含む厳密保持を別判定」「期待値緩和・正規化・非変更行の後付け復元でPASSを作らない」と指示する。
- 現在の[#5本文](https://github.com/minimo162/ai-prompts/issues/5)には「必須技術残件はT10 strictのみ」「生バイト保持要件の変更・例外受入は未承認」「行末・BOM・EOFを除外せず」と明記されている。[#27本文](https://github.com/minimo162/ai-prompts/issues/27)にも「必須技術残件 | T10 strictのみ」とある。**CASE Bの直接根拠はこの明示された必須完了条件であり、派生JSONだけを権威にしていない。**
- Issue本文の過去編集履歴を完全復元できたわけではない。上記コメントをraw-byte条件の「史上最初の発言」と断定しない。保存コメントで確認できる最古の明示指示と、現在の必須化を分離する。元依頼や最初期ケースへ遡及してraw-byte文言があったとは記録しない。
- [current-package-status](current-package-status-20260913.json)、[issue5-completion-audit](issue5-completion-audit-20260911.json)、[coverage](../coverage.json)、[index](../index.json)、[validation](../../docs/robin-knowledge-validation.md)、[progress](../../docs/robin-knowledge-progress.md)、[README](../../README.md)は、この後続条件によるNOT_PROVEN/partialを伝える派生記録として確認した。原依頼そのものの証拠には格上げしない。新たなcomplete判定へ変更しない。

## 未達と必要な判断

[限定再取得結果](t10-strict-20260914x-recapture-results.json)と[検証](t10-strict-20260914x-recapture-verification.json)では、固定入力はCRLF15・末尾改行なし、両DOM応答はCR0・LF16・末尾LFあり。保存器は取得文字列と一致したが、許可区間外bytesは不一致。この観測は保持し、モデル・通信・描画の原因を特定したとはしない。既存[公式別表現判断](t10-official-representation-decision-20260915.md)も再開しない。

closeへ進むにはユーザーが次のどちらかを正式に判断する必要がある。

1. raw-byte要件を元契約として維持する。この場合は既存ブロッカーを維持し、取得枠追加なしでは再取得しない。
2. content-preservationを正式なT10必須条件とし、transport byte preservationを非ブロッカーへ変更する。この変更承認後もstrict NOT_PROVENと区間外FAILは残し、#5/#27の残る必須受入を別々に監査してからcloseを判断する。

今回はどちらも新たに選択していない。close権限が与えられたことを要件変更の選択と解釈しない。

## 固定・保全と検査

現行20260913e: instruction SHA `6ad6f742f0eea335aeb523aba36c4f32cb9207fb418680b7d87f508124c1e79c`、bundle SHA `79245787fd34885592c2d1059297ccd215f046fa529dacadb7d3b7963e036e12` を実ファイルで確認。C/独立T04/PR33補助を変更・再実行していない。

開始working treeは追跡変更なし、保護対象の未追跡 `docs/agent-approach-comparison-2026-09-07.md` と `%SystemDrive%/`、ignored `.work/` を保持。ignored一覧取得は一部の長いパスに警告があり、全ignored列挙の完全性は主張しない。保護対象の個別ハッシュ検証とは分離する。

本監査の認証済みUI・ブラウザー・Copilot送信・DOM取得・export・対象サービスAPI・PAD Run・clipboard変更はすべて0。GitHub Issueの読取り・監査報告は別。コード/配布物変更なし、PR/main統合・Issue closeは行わない。

原ファイル・過去の失敗JSON・raw証跡は変更しない。保護409件と基準`3ef2a9c3d7483db055e60078d2923a2ddbeb146d`の原本807件、固定パッケージの不変を個別比較で確認した（2026-09-14T21:47:58.460Z）。

補助コードの履歴SHAには別の観測境界がある。旧一括保全スクリプトは4コードファイルのcheckout SHA差で失敗した。Compare-T10Bytes.mjs、Save-T10Capture.mjs、Test-T10ByteComparator.mjs/.ps1は、main内Git blobのSHAが旧manifestと一致し、現在checkoutはそのLFをCRLFへ展開した内容と一致する。これはコードのGit展開差の診断であり、Robin原文を正規化して保全PASSへ変換したものではない。旧manifestを書き換えていない。

個別検査: CurrentStatus57、Issue5 A-G trace316、RobinCatalog107、RawContracts、Copilot package（3947 UTF-16／7知識／87アクション）、T10 strict regression、T10 recapture regression（2証拠＋4負例）がPASS。最初のCurrentStatus起動は非対応の`-Root`引数で実行前拒否となり、正しい引数で実行し直した。原失敗ログは保持する。JSON1801件のparse、当記録のローカル参照18件、manifestの7原本/bundle SHA、差分・機密混入点検も実施した。

今回新規実行した非ライブAllは38/38 PASS（`.work/nonlive-08d81f026ff445d794af6894f6e9a122/verification.json`）。対象App/index/launcherの検査前後ハッシュ一致、live_m365/native_padはNOT_RUN。過去のAll結果を今回へ付け替えず、追加回帰検査を38件へ合算しない。検査がPASSでも、raw-byteの受入判定はNOT_PROVENのままであり、CASE Bは解消しない。
