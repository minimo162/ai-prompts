# EX03-r10-G1 live-generation review

## 結論

EX03-r10-G1は**不受入**です。通常Microsoft 365 Copilotへ固定本文と同版bundleを1回だけ送信し、拒否なしで197行のRobinを得ました。しかし、コードコピーで取得した無修正生成物は、r10で明示した構造忠実性ゲートに反して50行目と90行目の型修飾子を欠落させています。埋込みPowerShellは非実行AST解析で19件の構文エラーとなりました。固定停止条件に従い、専用PADへの貼付け・保存・再コピー・Run1・Run2はすべて未実施です。再送・手修正・次版試行は行っていません。

## 固定版と送信

- version: `20260917-excel-r10`
- candidate commit: `06aa0a572c58a09357ac1ac27a0a04eeaa4d680d`
- frozen checkpoint commit: `d510252b481a9ec4aa93b8db23961ab6da3e7771`
- action-time starting HEAD: `9935d88ea282611e91ab50d3acda3af0f4bea435`
- instruction SHA-256: `9434c976457b2fec14ad24d8ee57a3400e7eb092ba38259e3f8f728139c20681`
- bundle SHA-256: `0c53d6ce82fc5e23363332420b59c34470decbb123f804b2e628d26d58928ec6`
- manifest SHA-256: `7807e31e8177b05dc89d235496ee1b5978502f7406586dff2621d769981d6cbe`
- submitted body SHA-256: `751252c0ca263be62c01dce3dc83b10d733579bc395bc4bea01903d543be6247`
- conversation: <https://m365.cloud.microsoft/chat/conversation/b0df40da-e1a7-4a85-a107-ff963d94d307?es=SSR>
- normal M365 send: 1 / resend: 0 / model: Think Deeper

送信直前の可視エディタ内容は固定本文と一致しました。生のエディタコピーに現れた末尾のU+200B/U+200Cは`aria-hidden`のCopilot UI制御ノードで、これら2文字だけを除く可視シリアライズは固定本文とSHA一致しています。最初にシステムclipboard由来の古い長文が下書きへ入った時点では送信せず、全消去後に固定本文をplain textで入れ直して一致確認してから送信しました。

## 未共有だったr9結果とr10への変更

r9は`20260917-excel-r9`（instruction `a699dd910a4b0529fc71c9b8045b845bf49b8a407df9da88027a0ca0ab0f51fa`、bundle `b402a6c78fb39cb68dd4111590122b9f9be3364609358fd58a9ad3880d29b993`）を通常M365へ1回送信し、拒否なしで197行を生成しました。しかし50行目・90行目に構造破損があり、埋込みPowerShellは22件のASTエラーでした。PAD貼付け・Runは0回で、停止証跡はcommit `e8fc12c2a916df7a708536b652017d12c81f2714`に固定済みです。

r10では、r9の独立教材Robin SHA `6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb`と内包script SHA `65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9`をbyte同一で保持し、指示・bundle側だけに次を追加しました。

- source由来12 tokenの正確な件数
- 必須不変断片2件を各1件
- r9で観測した禁止破損断片3件を各0件
- 適応後error label 2件の正確な値
- 1件でも不一致ならRobinを出さない停止条件

固定EX03依頼・grader期待値・fixture・教材と試験の独立性は変更していません。

## r10生成物と停止理由

コードコピー原文は`generated.robin`にbyte同一で保存しました。

- raw/code-copy SHA-256: `4946431c9ce47f986b841115fbfd328036356c4e12ae7cbe912c2bf06e2b1ed3`
- 14,275 UTF-8 bytes / 14,073 UTF-16 units / 197行 / LF / 最終改行なし
- Copilotが応答内で主張したSHA-256: `e14b1ae8dd2652eccc6d0537705c01de977f4657536c338580c8b681e020356c`
- 主張SHAとコードコピーSHA: **不一致**

期待適応との内容差は2行だけです。

```text
50 expected: if ([string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)) {
50 actual:   if (:Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, :OrdinalIgnoreCase)) {
90 expected: ... -not [string]::IsNullOrEmpty($afterPrefixCharacter)) {
90 actual:   ... -not :IsNullOrEmpty($afterPrefixCharacter)) {
```

固定tokenのうち`[string]`は期待14件に対して12件、`[StringComparison]`、`::OrdinalIgnoreCase`、`::IsNullOrEmpty(`は各期待1件に対して0件でした。必須不変断片2件は各0件、禁止断片`, :OrdinalIgnoreCase`と`-not :IsNullOrEmpty(`は各1件です。角括弧直前backslashは各0件、適応後labelは各1件ですが、部分的な一致を全体PASSへ読み替えていません。

r9生成物との差は内容上50行目だけです。r10はr9の壊れた`GetFulling]`を`GetFullPath([string]...`へ戻した一方、先頭の`[string]`を落とし、`[StringComparison]`欠落を残しました。90行目の欠落は同一です。したがってr10追加ゲートは応答文では「通過」と主張されましたが、実出力には適用されていません。

## 工程判定と保全

- 送信先・固定本文・同版bundle・SHA・独立性: PASS
- 通常M365送信: PASS（1回、拒否なし、再送0）
- 無修正生成物の安全確認: FAIL
- PAD貼付け・保存: NOT_RUN
- PAD再コピー一致: NOT_RUN
- Run1: NOT_RUN
- Run1成果物照合・保全: NOT_RUN
- Run2: NOT_RUN（Run1前提未達）
- 出力`照合結果.xlsx`: 未作成
- `work.xlsx`とテンプレート: SHA一致
- 保護対象264ファイル: 不一致0
- 固定依頼・期待値: 変更なし
- 旧558差分FAIL: 保持
- 既存output guard実機経路: 未確認のまま
- GitHub書込み: 0

機械照合の全token・断片・変更前後・ASTエラーは`generation-safety-audit.json`、送信実績は`live-send.json`、工程判定は`acceptance-status.json`に記録しています。原文は`generated-robin.clipboard.utf8.b64`、応答全文は`copilot-response.clipboard.utf8.b64`から再現できます。
