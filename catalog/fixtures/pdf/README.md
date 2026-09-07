# PDF採取用の合成入力

`source-a.pdf` は3ページ、`source-b.pdf` は2ページです。各ページに識別用の `PAGE_TOKEN_A1` 等と日本語・100%を配置しています。Aの1ページには160×80の2色画像、2ページには見出し＋2データ行の3列表を含みます。

ReportLabで作成した合成データです。作者メタデータはSyntheticで、業務資料は含みません。抽出・統合の実行時には `C:\Temp\AiPromptsPdfCatalog_20260907` に配置しました。原文のパスは試験場所の記録です。

実行前後で入力ファイルのSHA256が変わらないことを確認しています。期待するページ識別文字とハッシュは [results.json](../../evidence/pdf/results.json) にあります。
