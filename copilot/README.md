# PAD Robin配布物

操作方法は[PAD・Copilotの操作入口](../docs/pad-copilot-operation-guide.md)へ。起動・接続確認から送信・貼付け・保存・再コピーまでを整理しています。

通常M365 Copilot Chatの新規チャットへ、選んだ版の**指示全文＋同版bundleの実添付**を渡します。7分割への切替えや比較は必須ではありません。

| 用途・状態 | 指示 | bundle・版対応 |
|---|---|---|
| Issue #38 Excel候補 `20260915-excel-r3`：非ライブ検査済み、実機未受入 | [候補指示](versions/20260915-excel-r3/agent-instructions.txt) | [bundle](versions/20260915-excel-r3/knowledge/PAD-Robin-Knowledge-Bundle.txt) / [manifest](versions/20260915-excel-r3/manifest.json) |
| コピーr2：静的検査、再実機検証待ち | [r2指示](agent-instructions-copyable.txt) | [基準bundle](knowledge/PAD-Robin-Knowledge-Bundle.txt) / [対応](copyable-output-20260915.json) |
| 受入済み基準版 `20260913e`：原証跡を保持 | [基準指示](agent-instructions.txt) | [基準bundle](knowledge/PAD-Robin-Knowledge-Bundle.txt) / [manifest](knowledge-bundle-manifest-20260913e.json) |

指示を二重に貼らず、新旧のbundleを混在させません。候補の7原本は版別knowledgeディレクトリに保存しています。

Excel候補はシート切替原文を索引・Excel教材・組合せ例へ収録しました。DataTable矩形書込み原文を追加採取し、12セルの値・型・位置一致まで観測しました。通常Copilotでr3全ケースを生成検証し、EX01はPADで2回の表示値・位置一致、EX04は4条件の生成停止、EX05は値転記と完全コピーの区別を確認しました。EX02は生成停止、EX03は未採取構文を含みPAD未実行です。補助probeは各2回の終了を確認しましたが、XML書式照合FAILと全体フローの未達が残るため、候補を受入済みとは扱いません。

[固定受入・検査結果・再開条件](../catalog/acceptance/issue38/report.md)を参照してください。コピー機能の表示・Robinだけのコピー本文・無修正PAD貼付け/保存/実行は別判定です。[コピー規則](copyable-output.md)を維持します。

候補bundle再生成（リポジトリ直下、PowerShell 7）:

```powershell
./tools/Build-KnowledgeBundle.ps1 -Root ./copilot/versions/20260915-excel-r3 -KnowledgeDirectory knowledge -OutputPath knowledge/PAD-Robin-Knowledge-Bundle.txt
node ./tests/Test-Issue38Package.mjs 20260915-excel-r3
```

生成後のSHAがmanifestと異なる場合は同版として使わず、新版候補を作ります。旧版固定ハッシュ検査を候補ハッシュで書き換えません。

基準版の最終状態は[最終受入監査](../catalog/evidence/final-content-acceptance-20260915.md)。以前の逐次記録は[履歴](README-history-before-issue38.md)へ分離しました。履歴内のOPEN/未完了は当時の記録です。#5/#27の完了を取り消さず追加範囲は#38で扱います。

旧Excel候補r1は保持。Excel候補r2は改行変換によるmanifest文字数不一致で使用不可（未送信・未実行）。r3はこれを修正した別版です。コピー規則のr2とは別の版番号です。
