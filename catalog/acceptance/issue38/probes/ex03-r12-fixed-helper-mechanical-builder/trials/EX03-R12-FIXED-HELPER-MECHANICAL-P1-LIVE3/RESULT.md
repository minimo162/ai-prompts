# EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE3

`PASS_LIVE3_NORMAL1_THEN_EXISTING_OUTPUT_GUARD1`。別IDの正常系1Runが固定範囲で完全PASSした後にだけ、別IDの既存出力ガード1Runを実行した。

- 正常系: 12対象、対象外468、数式、実効書式、原本SHA、F6契約、LIVE2との値・型・位置・書式比較PASS
- 負例: `OUTPUT_EXISTS_NO_RUN`、成功gate・数値書込み・SaveAs未進入、8 JSON・既存出力・入力・template・work不変、READY正常終了
- 負例の型比較: 未実行のためNOT_EVALUATED
- Copilot送信、候補版、全件回帰、追加Run、GitHub書込み: 0

本判定は固定EX03の機械ビルダー経路に限定する。
