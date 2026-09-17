# EX03 r11 FILE-AUX1 existing-output guard live negative

## 結論

`EX03-R11-FILE-AUX1-EXISTING-OUTPUT-NEG1` は固定範囲でPASS。無修正の`Power Automate | 無題 (10)` / Main / 110 actionsを、正例2Runとは別IDで追加1回だけ実行した。固定出力へ書込み可能な合成xlsxを事前配置し、PADで`TransferState=OUTPUT_EXISTS_NO_WRITE`、`Work=<空白>`、12個の`ValueTypeMatch=False`、`Ready`、Run有効、Stop無効を直接観測した。既存出力・入力2冊・テンプレート・workのSHAは前後不変で、既存出力の最終更新時刻も変化していない。

## 分離した判定

- Formal `EX03-r11-G1`: **FAILを保持**。`FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD`、formal PAD 0のまま。
- `EX03-R11-FILE-AUX1`: **機能2Run PASSを保持**。今回再実行していない。
- `EX03-R11-FILE-AUX1-EXISTING-OUTPUT-NEG1`: **既存出力ガード1Run PASS**。
- 書式: 旧raw比較の558件FAILは履歴として保持。固定範囲のExcel実効書式・寸法差は0件という既存裁定を保持し、558件を未解決の実破損とは扱わない。今回は再調査していない。

## 使用した固定フロー

- 版: `20260917-excel-r11`
- Robin SHA-256: `a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875`
- PAD: `Power Automate | 無題 (10)` / `Main` / Power Fx OFF
- actions / variables: `110 / 45`
- Fresh re-copy: LF正規化一致
- Robin編集・貼り直し: なし
- 今回のPAD Run: `1/1`、再実行なし

Robin先頭は`NOT_STARTED`、既存出力IF、`OUTPUT_EXISTS_NO_WRITE`、`ELSE`で、全Excel処理と唯一のSaveAsはELSE内にある。

## 直接観測と前後不変

- `TransferState`: `OUTPUT_EXISTS_NO_WRITE`（変数ダイアログで完全値を開き、保存せずCancel）
- `Work`: `<空白>`
- `ValueTypeMatch`: 12件すべて`False`（書込み側へ入らないRunの初期値）
- 終端: `Ready`、Run有効、Stop無効、設計/実行エラーなし
- Excelプロセス: 実行前後0
- 既存出力 SHA-256: `dc5c158d93ec322e29181fc34c961a396964c22c39c4f23d00d3ce215ee71af9`（前後同一、最終更新時刻も同一）
- input A: `c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9`
- input B: `01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725`
- template/work: `881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21`

合成既存出力は`existing-output-before.xlsx`と`existing-output-after.xlsx`へ保全した。検証後は固定出力パスを不在へ戻した。

## 境界

Copilot送信、正例2Run再実行、原因調査、全回帰、Robin/版/比較器変更、追加Run、GitHub書込みは行っていない。このPASSを未確認の型・形状・他環境・他ガードへ一般化しない。Issue #38全体の完了は宣言しない。
