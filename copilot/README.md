# PAD Robin配布物

Issue #38の固定EX03向け推奨入口は[機械ビルダー利用案内](../catalog/acceptance/issue38/probes/ex03-r12-fixed-helper-mechanical-builder/README.md)です。検証者管理の固定WIRING SPEC・固定helper・固定launcherを使用し、LIVE2正常1Run、LIVE3正常1Run・既存出力ガードPASSを根拠に限定受入しています。自然言語→WIRING SPECの自動生成・受入は未検証です。

固定EX03での通常M365 CopilotによるRobin直接生成は非推奨の実験経路です。A1〜A3は拒否、A4は比較欠落・固定launcher不一致と構文破損で停止しました。正式r12はFAILのままで、機械ビルダーとの間でPASSを転用していません。[現行受入報告](../catalog/acceptance/issue38/report.md)と[case matrix](../catalog/acceptance/issue38/case-matrix.json)を参照してください。

## 既存Copilot版の配布・履歴

操作方法は[PAD・Copilotの操作入口](../docs/pad-copilot-operation-guide.md)へ。起動・接続確認から送信・貼付け・保存・再コピーまでを整理しています。

通常M365 Copilot Chatの新規チャットへ、選んだ版の**指示全文＋同版bundleの実添付**を渡します。7分割への切替えや比較は必須ではありません。

| 用途・状態 | 指示 | bundle・版対応 |
|---|---|---|
| 旧EX02候補 `20260915-excel-r4`：実生成は型照合不足で拒否、PAD未実施という履歴 | [候補指示](versions/20260915-excel-r4/agent-instructions.txt) | [bundle](versions/20260915-excel-r4/knowledge/PAD-Robin-Knowledge-Bundle.txt) / [manifest](versions/20260915-excel-r4/manifest.json) |
| 旧Excel候補 `20260915-excel-r3`：EX01等の部分結果を保持、EX02/03未達 | [旧指示](versions/20260915-excel-r3/agent-instructions.txt) | [旧bundle](versions/20260915-excel-r3/knowledge/PAD-Robin-Knowledge-Bundle.txt) / [manifest](versions/20260915-excel-r3/manifest.json) |
| コピーr2：静的検査、再実機検証待ち | [r2指示](agent-instructions-copyable.txt) | [基準bundle](knowledge/PAD-Robin-Knowledge-Bundle.txt) / [対応](copyable-output-20260915.json) |
| 受入済み基準版 `20260913e`：原証跡を保持 | [基準指示](agent-instructions.txt) | [基準bundle](knowledge/PAD-Robin-Knowledge-Bundle.txt) / [manifest](knowledge-bundle-manifest-20260913e.json) |

指示を二重に貼らず、新旧のbundleを混在させません。候補の7原本は版別knowledgeディレクトリに保存しています。

EX02向けr4は、r3に未収録だった出力存在分岐・セル比較と、矩形転記から保存/再読取りまでの完全原文を統合しました。固定EX02を同版指示＋実添付bundleで1回生成し、既知工程は認識されましたが、厳密な型照合不足でコードなしとなりました。等価比較を型検証と呼びません。r4のPAD貼付け・Run1/2は未実施で、r4時点のEX02は未受入でした。[EX02 r4レビュー資料](../catalog/acceptance/issue38/cycles/EX02-r4/review.md)は当時の記録です。後続r5-G2の固定範囲機能PASSと書式分類は[既存レビュー](../catalog/acceptance/issue38/review/20260917-b73e0b5/README.md)に保持しています。

r3ではEX01のPAD2Run表示値・位置一致、EX04の4条件生成停止、EX05の範囲区別を確認済みでした。EX02は生成拒否、EX03は未採取EXITでPAD未実行です。この履歴をr4の受入へ継承しません。矩形probeのXML書式558差分FAILとExcelネイティブ限定一致は保持しています。

[固定受入・検査結果・再開条件](../catalog/acceptance/issue38/report.md)を参照してください。コピー機能の表示・Robinだけのコピー本文・無修正PAD貼付け/保存/実行は別判定です。[コピー規則](copyable-output.md)を維持します。

旧r4パッケージの再現検査（履歴参照用。現行入口への切替えや再実施を要求するものではありません）:

```powershell
node ./tests/Test-Issue38Package.mjs 20260915-excel-r4
python ./tests/Test-Issue38Ex02.py
```

後者は新しい一時ディレクトリで候補一式を再生成し、凍結版と全ファイルのバイト一致を確認します。ビルダー単体は `python tools/Build-Issue38Ex02Candidate.py --output <未存在ディレクトリ>`。既存候補の上書きは拒否します。生成後のSHAがmanifestと異なる場合は同版として使わず、新版候補を作ります。旧版固定ハッシュ検査を候補ハッシュで書き換えません。

基準版の最終状態は[最終受入監査](../catalog/evidence/final-content-acceptance-20260915.md)。以前の逐次記録は[履歴](README-history-before-issue38.md)へ分離しました。履歴内のOPEN/未完了は当時の記録です。#5/#27の完了を取り消さず追加範囲は#38で扱います。

旧Excel候補r1は保持。Excel候補r2は改行変換によるmanifest文字数不一致で使用不可（未送信・未実行）。r3はこれを修正した別版です。コピー規則のr2とは別の版番号です。
