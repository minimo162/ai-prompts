# EX03 r6 refusal / r7 source investigation

## 結論

r6拒否文が挙げた説明用エスケープは、実送信bundleのバイト列には存在しなかった。したがって、拒否理由だけを根拠に「bundleのRobinがエスケープ破損していた」とは分類しない。

教材側で確認できた不足は、r6の完全な統合Robinが「実装者候補・未受入」とされ、その完全原文自体のPAD Designer保存・再コピー証跡がなかったこと、および「未実行なので成功を主張しない」と「固定原文を出力してよい」の区別が明示されていなかったことである。この不足は実データに基づく教材上の弱点だが、Copilot内部の拒否原因を断定するものではない。

後継 `20260916-excel-r7` では、同じ固定EX03完全Robinを専用PADへ一度だけ貼り付け、保存・再コピーした原文を生成の権威ソースとして収録した。実行はしておらず、Copilot生成・EX03 Run・受入へは読み替えない。

## 三者照合

| 対象 | SHA-256 | 結果 |
|---|---|---|
| r6拒否原文 `response-rendered.txt` | `7c6f30590b3ee7905038f142c1974d7639c4579c44a6f445ae0a9ea22f58b342` | `=\>`、`\_`、角括弧のバックスラッシュを拒否理由として記載 |
| 実送信r6 bundle | `9c566e7f85a431f1869302c6a40985e2f81237f17ac4fbbdc9a73e62a646b580` | `=\>` / `\_` / `\[` は各0件。raw `=>` 184件、`_ValueTypeMatch` 60件、`Data1[0][0]` 12件 |
| PAD保存・再コピー原文 | `529d66dd598c395c6313a6f6d6b44c80049effb79de96b675a37f7dc99596d89` | 候補とLF正規化後完全一致。内包RunScriptはsupportと最終LFを除き完全一致 |

## 専用PAD確認

- 環境: PAD `2.71.115.26224`、日本語UI、Power Fx OFF、専用の空Main
- 候補: 197行、SHA `1f6ea14ea59242d7351d01ef75cd9571eb90676ab3845ffd2a842f01d84c771b`
- 操作: native clipboardから貼付け1回、保存1回、再コピー1回
- 観測: 110アクション、45変数、Designerエラーなし、保存後READY
- 差分: 候補はLF-only 197件。PAD再コピーはトップレベル区切りCRLF 110件、内包PowerShellのLF-only 87件。LF正規化後の文字列は完全一致
- 非実施: Run、Copilot送信、EX03統合実行、GitHub書込み

## 修正前後

| 箇所 | r6 | r7 |
|---|---|---|
| 指示末尾 | 完全例を「実装者候補・未受入」とだけ区分 | PAD保存・再コピー原文を固定EX03の逐語生成ソースとし、未実行は受入主張の禁止であって固定原文の出力禁止ではないと明記 |
| knowledge 00 | r6の範囲・固定mapping | r6拒否を保持しつつ、実bundle token監査、PAD再コピー範囲、未実施境界を追加 |
| knowledge 04 | probe・候補scriptを掲載 | 拒否原文／実送信bundle／PAD再コピーの三者照合と、再コピーRunScript↔supportの機械一致を掲載 |
| knowledge 06 | builder由来の統合候補 | PADから保存・再コピーした完全Robin原文を混在改行のまま掲載 |
| support | 内包PowerShell 1件 | 同じPowerShellをバイト保持し、PAD再コピー完全Robinを別supportとして追加 |

01/02/03/05はr6からバイト一致。固定依頼、spec、期待値、fixture、work template、旧版、旧証跡、原本・対象外セル・数式・実効書式・558差分FAILの検査、安全ガードは変更していない。

## 新版固定値

- version: `20260916-excel-r7`
- instruction SHA-256: `b888b7497c2c5a7fb79860c22da6be4b62f013731ab920e87dbb503ef1f0d7fa`
- bundle SHA-256: `228329f60f17192f87878fb6393abf22520d051a1225d9905f2f71354216f1ed`
- manifest SHA-256: `38517f37be934b1bcf37c0e12f9f33c9e803fa174af15e41579ccdd612dc4e3f`
- PAD再コピーsupport SHA-256: `529d66dd598c395c6313a6f6d6b44c80049effb79de96b675a37f7dc99596d89`
- 内包PowerShell support SHA-256: `d0a5df36516fcf4e27f6d789300ee5a03789aba8176571b1ab86fe84f15fba1a`
- status: `FROZEN_CANDIDATE_EX03_PAD_RECOPIED_SOURCE_NOT_COPILOT_OR_RUNTIME_ACCEPTED`

## 判定と残件

r7は非ライブpackageと固定Robin sourceの準備までPASS。通常M365 Copilot生成、無修正生成物のPAD Run1/Run2、保存成果物照合、負例、既存出力ガード実機経路は未実施であり、EX03受入は未達のまま。今回の許可範囲に従い、それらは実行していない。

## 検査結果

- r7 package: PASS（指示6,350 UTF-16 units、7教材、bundle再構成・SHA一致）
- EX03回帰: 8/8 PASS。三者照合、PAD再コピー↔候補、RunScript↔内包script、順序・件数、数値を文字列へ変えた既存負例、r7再buildのバイト一致を含む
- Excel oracle: 13/13 PASS
- EX02回帰: 18/18 PASS（旧558件FAILを保持する検査を含む）
- EX04既存出力負例: 4/4 PASS
- package回帰: r1、r3、r4、r5、r6、r7 PASS
- r2 package検査は既存のままFAIL。未変更r2指示はCRLF 67件を含み実長5,911だがmanifestは5,844を記録している。ファイルSHAはmanifestと一致し、HEADとの差分はないため、今回の修正で旧版を書換えて隠していない
- `git diff --check`、Python AST、PowerShell parser、Node構文検査: PASS
