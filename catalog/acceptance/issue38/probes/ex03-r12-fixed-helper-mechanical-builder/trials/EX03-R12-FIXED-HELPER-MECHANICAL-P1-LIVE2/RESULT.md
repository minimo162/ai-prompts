# Issue #38 EX03 mechanical-builder LIVE2

## 判定

`PASS_MECHANICAL_BUILDER_PATH_LIVE2_NORMAL_RUN1`。LIVE1のSTOP証跡を変更せず、固定invocationとWIRINGが一致する合成検証用`json_root`を事前配置し、保存済み専用フローを再貼付け・再保存せず正常系1Runだけ実行した。

## 事前配置・実行同一性

- json_root: `C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\runs\EX03-attempt1\a4-helper-json`
- invocation/WIRING一致、8保存先の親一致、合成検証用領域内
- 一時書込み・読戻し・削除PASS、既存ファイル削除0、権限変更0
- 保存済みフロー再コピー SHA-256 `570b26c57abeca0e9b8e19368c6542a529b44994bac518f2e70cb69baec52c0f`、LIVE1再コピーとbyte一致
- 再貼付け0、再保存0、Run 1

## PAD・成果物

- READY、Designerエラーなし
- `PowershellOutput`: `{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}`
- `ProbeState`: `SUCCESS_GATE_PASSED_SAVED_READBACK_READY`
- `Position1ValueTypeMatch`〜`Position12ValueTypeMatch`: 12 true / 0 false
- result SHA-256 `49e4ad48e711ecbde7a0b6ec625dad8d2c74247e54eec69fe230aaf5366da5f8`
- 12対象セル: 値・型・位置 mismatch 0
- 対象外468セル: 値・型・数式 mismatch 0
- Excel実効書式: 480セル、48行、30列、差分0
- F6: `100%` / `System.String` / 元書式 / prefix空 / 数式なし
- 入力2冊・template・work不変
- 旧raw 558差分は診断記録として保持

## 境界

成功済み生成検査・全件回帰、Copilot送信、Run2、候補版作成、追加Run、GitHub書込みは行っていない。本PASSは機械ビルダー経路の今回1Runだけに限定し、Copilot生成経路やIssue #38全体へ転用しない。
