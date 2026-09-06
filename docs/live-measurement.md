# 実M365の合成CSV測定

開発用Node/Playwright/Edgeがある端末で実行する測定補助です。これらを利用者向け3ファイル配布の依存にはしません。実M365へ合成文を送るため、非ライブ試験とはコマンドを分けています。

1. 候補を封入して固定します。新しい出力先を指定し、専用プロファイルを開きます。

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File tools\Prepare-CsvLiveMeasurement.ps1 -OutputDirectory $newMeasurementDirectory -Live
   ```

2. 表示された専用Edgeで必要ならサインインします。既存プロファイルのCookieをコピーしません。`context.json`は固定した3ファイルのハッシュと検証homeを記録します。
3. `context.json`を使い、1・50・100を順に測定します。

   ```powershell
   node tools\Measure-CsvLive.cjs $contextPath 1 --live
   node tools\Measure-CsvLive.cjs $contextPath 50 --live
   node tools\Measure-CsvLive.cjs $contextPath 100 --live
   node tools\Measure-CsvLive.cjs $contextPath 1 --live --long-text
   ```

   計画確認と送信開始は実画面を通ります。確認質問が出た場合は画面で回答し、その操作も介入として記録してください。要確認行を「人が承認した」と回答する必要はありません。処理完了と内容承認を区別します。

   `--long-text`は本文に改行を含む補足80行を追加します。実際の本文文字数・入力バイト数を測定記録へ保存します。上限付近の性能保証や、多様な長文の意味品質とは別の合成ケースです。

入力、未確認の正解案、画面画像、measurement.json、アプリの要求/結果/接続記録を新しい出力先に保存します。`source_commit`を指定する場合は、その3ファイルに対応する実コミットを使います。未指定時は空/未確認として扱い、候補ハッシュを基準にします。

結果不明・失敗を新しいIDだけで無条件再送しません。既存回答の照合や明示的な条件変更を使い、元の記録を残します。計測補助は稼働中の業務workerを強制終了しません。

終了コードはDONEで0、その他の終端または40分の観測期限で2、測定補助自身のエラーで1です。期限切れや状態を確認できないエラーではサーバーを残します。`home/data/server.json`と画面から稼働状態を確認してください。経過時間は補助の起動からの時間で、初回サインインや別実行の復旧時間は含みません。PlaywrightがNodeの探索先にない場合は、既存インストールのモジュールパスを`PLAYWRIGHT_MODULE`に指定します。

この補助が記録する経過時間と件数だけでは、意味精度や人時間30%削減の受入になりません。人による正解確認、直接Copilot/固定処理との同条件比較、社内PC・別利用者/初見試行は別途必要です。

成果物4点のハッシュと、生成した単一CSVの全原値の保全は次で検証できます。引数には絶対パスを指定します。既存の出力記録は上書きしません。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Verify-CsvMeasurement.ps1 -InputPath $inputPath -MeasurementPath $measurementPath -OutputPath $newIntegrityPath
```

この検証も分類理由の意味評価や人の承認を代替しません。
