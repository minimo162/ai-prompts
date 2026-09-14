# 最終受入監査：明示的なT10完了条件変更（2026-09-15）

開始mainは `f4fa9a2e61bfd2a2be0414eccd9e42b2d4a5e35e`。現行版20260913eのinstruction／bundle／7教材を変更しない。機械可読の判定・個別証跡・原文ハッシュは [監査JSON](final-content-acceptance-20260915.json) に固定する。検査結果は [今回の検証記録](final-content-verification-20260915.json) に記録する。

## 判断の根拠と限界

[provenance audit](t10-final-provenance-audit-20260915.md) のCASE Bは履歴として維持する。元依頼・固定ケースの内容保持と、後続で明示的に必須とされたraw-byte監査は区別できるが、後者を無断で任意へ下げられなかった。その後、ユーザーは2026-09-15に次を正式な必須完了条件として明示した。

> 指定された変更だけを反映し、それ以外の既存命令・入力・変数・処理・エラー経路の内容を保持すること

同じ判断により、CRLF/LF・EOF・BOM等を含むtransport-level raw-byte完全保持はclose条件から外し、非ブロッカーの品質境界とした。従って今回の分類は **CASE Bの明示的なユーザー判断による解消**。過去の判断をCASE Aへ書き換えたものではない。

| T10の判定対象 | 一次 | 独立 |
|---|---|---|
| 機能実行（既存2回のPAD Run） | PASS | PASS |
| 指定変更のみ（2行目の値、4行目の保存先） | PASS | PASS |
| 変更しない14命令の内容保持 | PASS | PASS |
| transport raw-byte strict | NOT_PROVEN | NOT_PROVEN |
| 許可区間外raw bytes | FAIL | FAIL |
| 取得要求／完了／残枠 | 1／1／0 | 1／1／0 |

入力は16命令、CRLF15・最終LFなし。保存済みDOM回答はCR0/LF16・最終LFあり。内容比較は区切りと命令文字列を分離し、固定された2つのリテラル変更以外の文字列一致を確認する。trim、unescape、ファイル書換え、改行正規化によるstrict合格は行わない。既存のstrict comparator／recapture regressionはFAILとNOT_PROVENを維持する。

## Issue #5：必須A〜G

元依頼 §4–5 → PAD採取原文 → 別空フローへのファイル再利用 → 実行・固定実値 → 保存後再コピー → 現行教材の対応を追跡した。下表は主要な確認先であり、用途別の全参照は監査JSONの `issue5.a_g` と既存 [A〜G trace](issue5-a-g-trace-20260914g.json) にある。

| 必須範囲 | 採取・再利用・実値・再コピーの根拠 | 教材／必要なCopilot受入 | 判定 |
|---|---|---|---|
| A 基礎 | Boolean／Subtractの別空フロー受入、List index1、substring日本語、文字列・数値・日時の保存原文と再利用記録 | Basics、T01/T02、P3-1/P3-5 | 実測必須範囲を満たす |
| B 制御 | nested IF/LOOP、エラー経路。Main/P3Workerは後続の2 RunでOK、別run ID、原文不変、両subflowの保存・再open・再コピー | Control、T03修正版、T08、P3-2/P3-6 | 実測必須範囲を満たす |
| C データ | DataTable作成・行追加・繰返し、CSV。`c-cell-read-20260914v/acceptance.json` はscalar `CRead-20260914v` を2回確認し、再open再コピーも一致 | Basics／Files、T02、独立T04新pair | 実測必須範囲を満たす |
| D ファイル | folder/create、exists、text、copy、move／renameは固定合成入力を再作成し2回、原文・保存・再利用記録 | Files、T01/T03修正版、P3-3 | 実測必須範囲を満たす |
| E Excel | 新規／既存、cell/range/sheet、foreach、SaveAs。独立T04新pairはRun1確認後Run2、CSV/xlsx各回3×3固定値を照合 | Basics／Examples、T05、P3-4、独立T04新pair | 実測必須範囲を満たす |
| F Word/PPT/PDF | `office/verification.json`、Office成果物、T06本文置換、T07ページ内容、一次／独立T10のExcel変更とWord/PPT内容保持 | OfficePDF、T06/T07/T10 | 内容契約を満たす。transportはNOT_PROVEN |
| G UI/browser | T09安全なローカル画面。捕捉UI repositoryを別途importした新フローで生成6命令・WAIT 1・2 RunのT09-clicked・ブラウザー終了 | UIWeb、現行T09 | 観測経路を満たす |

古いB observerの `NOT_RUN_TARGET_UNAVAILABLE` は削除しない。採用した後続証跡は `p3-subflow-reuse-20260913-run1.json`、`run2.json`、`reopen-recopy.json`。C補完・独立T04新pair・PR #33のPAD補助は再実行・変更しない。

## Issue #27：現行20260913e

監査JSONの `issue27.cases` は、知識precheck、T01/T02/T03/T05/T06/T07/T08/T09、独立T01、独立T04新pair、一次・独立T10、P3-1〜P3-6、負例v2の20項目を個別参照する。

- T03は修正版依頼限定。元依頼への無条件PASSではない。
- 元T04生成失敗、旧独立候補のRun1 NOT_CAPTURED／candidate_partialは維持。新pairの証跡だけを現在の独立T04受入に採用し、元T04成功として二重計上しない。
- T08/P3-6は観測済みaction-levelエラー経路。未確認のblock-level FileNotFoundまで拡張しない。
- 負例v2は現行instruction/bundle、1送信、非実行の記録を採用し、旧版PASSを継承しない。

T06の原JSONのbundle SHAには `cadadb` / `dacadb` の転記不整合がある。明示された20260913e manifest、同一instruction・会話・Robin・Runの参照を照合して現在のpackage対応を整理した。原JSONを修正せず、アップロード内容を新たにバイト観測したとは主張しない。P3-4〜6の63桁instruction SHAは、既存の [転記訂正記録](p3-current-sha-correction-20260914e.json) を採用する。

## 完了範囲と公開条件

#5の必須A〜G、#27の指定された現行受入に、変更後のT10契約以外の必須残件は見つからなかった。技術的受入完了の範囲は通常M365 Copilot Chat＋PADの実測範囲に限定する。Agent Builder、全PAD機能、組織展開、一般的なbyte-preserving transport、未実行のDOM/Playwrightを完了とはしない。

Copilot新規送信・DOM再取得・Copilot export/API・PAD Run・clipboard変更は今回すべて0。必要な非ライブ検査、原文保全、差分確認を終え、変更をmainへ統合してから、完全main SHAを付して両Issueにコメントしcloseする。統合前のtechnical PASSはGitHub上のclose済みを意味しない。
