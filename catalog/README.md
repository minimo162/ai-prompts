# PAD実アクションのRobinカタログ

`index.json`は実際の左パネルから追加・設定・コピーした例の索引です。`.robin`はクリップボードから得た原文をUTF-8 BOMなしで保存し、改行を変換しません。Gitでもバイトを保持します。

現在は「新しいリストの作成」「項目をリストに追加」の2件です。専用フロー`RobinCatalog_20260907`で保存・実行し、変数`CatalogList`のプレビュー`[CatalogItem]`を確認しました。コピー前のクリップボードはメモリーに保持して復元し、その内容をファイルへ記録していません。

```text
Variables.CreateNewList List=> CatalogList
Variables.AddItemToList Item: $'''CatalogItem''' List: CatalogList
```

これは説明用表示です。コピー原文の正本は`flows/list-create-add/default.robin`です。

今回の設定画面では追加先リストに`%CatalogList%`を指定しましたが、コピーしたRobinでは`List: CatalogList`になりました。任意の文字列・選択肢・式までこの例から一般化しません。

空の`Roundtrip`サブフローへコピー原文を貼り付け、再コピーした`roundtrip.robin`が112文字・SHA256まで元と一致することも確認しました。実行結果を観測したのは元のMainです。

Copilotによる生成、アプリのRobin検証器/実行経路との接続はまだ未確認です。実アクションがPADで動くことと、このアプリがその構文を実行できることは別です。採取・拡張の方針は[採取ガイド](../docs/robin-action-catalog.md)を参照してください。
