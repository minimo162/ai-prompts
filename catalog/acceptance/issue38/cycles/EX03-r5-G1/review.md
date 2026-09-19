# EX03-r5-G1 実Copilot / PAD受入結果

結論は **不受入** です。固定版 `20260915-excel-r5` の本文とbundleを通常Microsoft 365 Copilot Chatへ1回だけ送信し、拒否なく87行のRobinを得ました。専用のPower Fx OFFフローへ無修正で1回貼り付け、保存後再コピーはLF正規化後に生成物と完全一致しました。

Run 1は成果物を保存して最終状態まで到達しましたが、固定12セルのうち `入力ろ.xlsx / 追加項目!D3` の文字列 `100%` が `追記先!F6` で数値 `1` へ変換されました。PAD自身も `SourceCellJson={"probe":"100%"}` と `SavedCellJson={"probe":1.0}` を比較し、`追記先_F6_ValueTypeMatch=False` と検出しています。他の11セルはTrueです。

独立比較でも同じ1件を検出しました。対象外468セルの値・型・数式は一致しています。Excel実効書式比較では `追記先!F6` の表示形式が `G/標準` から `0%` へ変わり、行高・列幅の実変更は0件でした。旧比較器の558件（style 480 / row 48 / column 30）は結果から隠さず保持し、今回の実変更1件と区別しています。

Run完了観測では120秒後も開始ボタン再有効化を確認できなかったため、同じRunを再要求していません。その後の読み取り専用変数観測で最終TransferStateと上記Falseを確定しました。利用者の停止条件に従いRun 2は開始せず、版・依頼・期待値・生成Robinは変更していません。

主要証拠:

- `live-send.json`: 送信先、本文SHA、実添付、1回送信
- `generation-result.json` / `generation-safety-audit.json`: 87行生成物と安全監査
- `pad-import-and-recopy.json`: 専用フロー、貼付け1回、保存、再コピー一致
- `run1/pad-run.json`: Run 1の完了制御観測タイムアウト
- `run1/pad-variables.json` / `run1/pad-f6-json-variables.json`: 最終状態、11 True / 1 False、JSON型差
- `run1/typed-transfer.json` / `run1/comparison.json`: 固定期待値と全セルの独立比較
- `run1/native-styles.json`: F6の実書式差、行高・列幅差0
- `run2/not-run.json`: 停止条件によるRun 2未実行

最小残件は、固定期待値を変更せず、百分率らしい文字列をExcelの自動変換から守る候補レベルの書込み方式を採取・固定することです。その変更版は、今回の生成・Run結果を継承せずに改めて実Copilot/PAD受入する必要があります。
