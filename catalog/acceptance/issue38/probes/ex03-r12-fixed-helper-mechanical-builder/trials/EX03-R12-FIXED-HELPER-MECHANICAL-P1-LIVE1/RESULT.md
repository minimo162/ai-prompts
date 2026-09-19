# Issue #38 EX03 mechanical-builder LIVE1

## 判定

`STOP_MECHANICAL_BUILDER_PATH_RUN1_RUNTIME_DIRECTORY_MISSING`。固定Robin `3d9c1671a5debc6f0247cef8c5e0d414dc07246a7cb7ce0ac6245fb860967e47` は専用PADへの無修正貼付け・保存・再コピーを通過したが、正常系Run1はMain 32行目で停止した。再Runは行っていない。

## 実行前・再コピー

- Build.py --check: PASS / CHECK_BYTE_IDENTICAL
- PAD再コピー SHA-256: `570b26c57abeca0e9b8e19368c6542a529b44994bac518f2e70cb69baec52c0f`
- 改行・末尾改行の正規化後は固定Robinと全文一致
- 未知差分0、命令欠落0、構文破損0
- 8 JSON保存、5数値書込み、2矩形readback、12比較、guard、成功gate、SaveAs、失敗分岐の再監査PASS
- 復号launcher SHA-256: `a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5`

## Run1停止

- PAD Run: 通算1回
- PAD表示: `無効なディレクトリ (パス 'C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\runs\EX03-attempt1\a4-helper-json\source-1.json' の一部が見つかりませんでした...`
- 場所: Main 32行目、最初の `source-1.json` File.WriteText
- `a4-helper-json` 親ディレクトリは停止後も不在
- helper成功JSON、保存出力、12比較はいずれも未到達
- `照合結果.xlsx` なし、JSON handoffなし、Excelプロセス0
- 入力2冊・template・workのSHAは不変

## 比較・境界

出力がないため、12対象セル、対象外468セル、数式、実効書式・行高・列幅、F6の比較はNOT_RUN。Run2、負例、Copilot送信、A5、ビルダー修正、全件回帰、追加Run、GitHub書込みは行っていない。本結果は機械ビルダー経路の停止証跡であり、Copilot生成経路やIssue #38全体の判定へ転用しない。
