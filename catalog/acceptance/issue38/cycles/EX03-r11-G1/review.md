# EX03-r11-G1 live-generation review

## 結論

EX03-r11-G1は**不受入**です。固定版`20260917-excel-r11`の本文と同版bundleを通常Microsoft 365 Copilotへ1回だけ送信し、拒否なしで応答と12,487-byteの`ex03.robin`を得ました。無修正ファイルは教材からの許可置換と167行すべて一致し、埋込みPowerShellのASTエラー0、固定token・対象ブック特定・副作用検査もPASSです。

一方、固定契約は全工程を1つの`text`コードブロックに出すことを要求していましたが、完成応答のコードブロックは0件で、Copilot自身が切り詰めを理由にblob-downloadへ置き換えました。失敗コードは`FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD`です。固定の不一致停止条件に従い、専用PADへの貼付け・保存・再コピー・Run1・Run2はすべて未実施です。再送、生成物修正、追加Run、次版試行は行っていません。

## 固定版と送信

- version: `20260917-excel-r11`
- base/action-time HEAD: `659ae9db649d33226d4bf9220965e263e34ee323`
- instruction SHA-256: `bceb1c7e4f47c0cd6a92ad698d08108175002bffcaaaff492a309ca74a122aa1`
- bundle SHA-256: `2d95ce344ff66195061fd15010d13b75937888575fa2345fb543ae2115242f69`
- manifest SHA-256: `295306ea7e2e45da8cf77dec2784e94ea8ea8333da0df6a4000f83e9228b509e`
- teaching Robin SHA-256: `148267f09f53d74db1059cee823a4a2e159f2bbebfa249d3a25c996796fa765b`
- embedded script SHA-256: `068e676d70c373a9cf8203d19f6154e38460f609c4fdf774dbef1528f68fc7ae`
- structural contract SHA-256: `ffbe75f9803435c55341f2d7db73e85b5ce5ec961f637734da38b6ee332a1ec9`
- submitted body SHA-256: `4bd51be17353634c8b38cabbee91a9235a1dd1af87243675f5d42500f40c5984`
- conversation: <https://m365.cloud.microsoft/chat/conversation/5019b961-47f4-4ca9-8602-30b6fb83512c?es=SSR>
- normal M365 send: 1 / resend: 0 / model: Think Deeper

送信直前には通常M365、Think Deeper、同版bundleの添付chip、固定本文を確認しました。生のエディタシリアライズにだけ現れた末尾U+200B/U+200Cを除く可視本文は固定本文とSHA一致しています。送信クリックは1回です。

## r11生成物の静的検査

- generated Robin SHA-256: `a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875`
- 12,487 UTF-8 bytes / 167行 / LF / 最終改行なし
- 独立教材からの許可置換との差: 0行
- PowerShell ASTエラー: 0
- `[string]` 12 / `[bool]` 2 / `[void]` 6
- `[Runtime.InteropServices.Marshal]` 7 / `[IO.Path]` 2 / `::GetFullPath(` 2
- `-ieq` 1 / `$matches[0]` 1 / `$beforeNumberFormat` 3
- 禁止旧表現・破損断片: すべて0
- RunScript 1 / numeric WriteCell 5 / source JSON 7 / saved JSON 12 / ValueTypeMatch 12
- normalized FullNameによる一冊選択: 1
- delete/network/external-process断片: 0

このPASSは**ダウンロードされた生成ファイルの静的検査だけ**です。コードブロック契約違反を相殺せず、PAD保存・再コピー・実行成功・EX03受入へ読み替えていません。

## 工程判定

- 送信先・固定本文・同版bundle・SHA・独立性: PASS
- 通常M365送信: PASS（1回、拒否なし、再送0）
- 無修正ダウンロード原文の構文・構造・対象ブック・副作用検査: PASS
- 応答の固定delivery契約: FAIL（要求1 code block / 実際0）
- PAD貼付け・保存: NOT_RUN
- PAD再コピー一致: NOT_RUN
- Run1: NOT_RUN
- Run1の12セル・F6・対象外・数式・実効書式・原本SHA照合: NOT_RUN
- Run2: NOT_RUN（Run1前提未達）
- 出力`照合結果.xlsx`: 未作成
- `work.xlsx`とテンプレート: SHA一致
- 保護対象312ファイル: 不一致0
- 固定依頼・fixture・期待値: 変更なし
- 旧558差分FAIL: 保持
- 既存output guard実機経路: 未確認のまま
- GitHub書込み: 0

詳細は`generation-safety-audit.json`、`generation-result.json`、`live-send.json`、`acceptance-status.json`、`protected-files-after.json`に記録しています。Copilot可視応答は`copilot-response.visible.txt`、無修正生成ファイルは`generated.robin`です。
