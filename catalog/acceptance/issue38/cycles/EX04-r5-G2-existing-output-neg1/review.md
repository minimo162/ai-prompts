# EX04 existing-output guard live negative

## 結論

`EX04-R5-G2-EXISTING-OUTPUT-NEG1` は固定範囲で合格した。G2正例2Runとは別IDで、無修正の87アクションを追加1回だけ実行した。合成`result.xlsx`が既に存在する条件で、PADは`TransferState=OUTPUT_EXISTS_NO_WRITE`を直接表示して`Ready`へ戻り、ELSE内のExcel転記・SaveAs・再読込へ進まなかった。

EX02の機能面PASSおよびa6662d8の558差分裁定は変更していない。558差分の再調査は行っていない。今回の結果はEX04の既存出力衝突だけの部分結果であり、Issue #38全体の完了を示さない。

## 使用した固定フロー

- PAD: `Power Automate | 無題 (4)` / `Main` / Power Fx OFF
- Robin: `catalog/acceptance/issue38/cycles/EX02-r5-G2/generated.robin`
- Robin SHA-256: `0829526420158a61146e5d3fde7c4a5cc035228e2ab98be96d9697aa64d457bd`
- アクション数: 87
- 貼り直し・編集・保存: なし
- 追加PAD Run: 1/1、再実行なし

Robinの1～4行目は`NOT_STARTED`、既存出力IF、`OUTPUT_EXISTS_NO_WRITE`、ELSEであり、全Excel起動・読取り・転記・SaveAs・再読込はELSE内にある。

## 直接観測

- Run直後のPAD概要: `pad-after-run-overview.jpg`
  - 87 actions
  - ステータス`Ready`
  - Run有効、Stop無効
  - `TransferState`の`OUTPUT_EXISTS_...`接頭辞
- PAD変数詳細: `pad-after-run-transferstate.jpg`
  - 完全値`OUTPUT_EXISTS_NO_WRITE`
  - ダイアログは保存せずキャンセルで閉じた
- 実行時エラー・設計エラー: 観測なし
- Excelプロセス: 実行前0、実行後0

## 前後SHA

| 対象 | 実行前 | 実行後 | 判定 |
|---|---|---|---|
| 既存出力 | `826d09ab3b5818326fa0dedac0af8a87f74057f4431e29e8a59c72ca7e08fda9` | 同左 | 不変 |
| input-a | `f655b62c82750fc07f4e54bcfd098e8e7c0b771c9422c4321cc413a4d6d07fa9` | 同左 | 不変 |
| input-b | `69627e161747fedad0f7c3b410c1d625b29a553786be0c145e83aaf43d1b105a` | 同左 | 不変 |
| template | `0e3cf3b1c9e6e73e835c324b71602b50f708df689944a3760e4b411959f3b457` | 同左 | 不変 |
| work | `0e3cf3b1c9e6e73e835c324b71602b50f708df689944a3760e4b411959f3b457` | 同左 | 不変 |

合成既存出力は実行前後コピーを専用サイクルへ保存した。両方とも上記SHAでバイト一致する。検証後、実行用`result.xlsx`は削除せず`existing-output-after.xlsx`へ移動し、実行前の不在状態を復元した。

## 境界

- Copilot再生成なし
- Robin・PADフロー修正なし
- 候補版変更なし
- GitHub書込みなし
- EX04のmissing sheet、invalid range、same-output等へ今回のPASSを一般化しない
- Issue #38全体の完了は宣言しない
