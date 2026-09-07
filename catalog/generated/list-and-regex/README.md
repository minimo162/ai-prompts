# 採取実例からCopilot生成、PAD実行まで

実M365 Copilotへ現在の生成プロンプトと6つの採取例を渡し、次の別タスクを依頼しました。

- 空の`StatusList`へ固定文字列`checked`を追加する。
- `Ticket 742 ready`の連続した数字を正規表現で`ID`へ置換し、`CleanText`へ保存する。

Copilotは4アクションを生成しました。実例と異なる変数名と入力値を使っています。助手が4つのリスト/テキスト操作だけで外部操作がないことを確認してから、空の専用フロー`RobinGenerated_20260907_01`へ貼り付けました。生成コードの手直しはしていません。

再コピーした`pasted.robin`は`generated.robin`と314文字・SHA256まで一致しました。保存・実行後、実PADの変数パネルで`StatusList = [checked]`、`InputText = Ticket 742 ready`、`CleanText = Ticket ID ready`を確認し、期待値と照合しました。

|記録|内容|
|---|---|
|`prompt.txt`|Copilotへ渡したタスク、生成ガイド、採取例の入力本文|
|`generated.robin`|Copilotが返したRobin原文|
|`pasted.robin`|PADへ貼り付けた後に再コピーした原文|
|`variables.json`|実行後の専用フローの変数パネルを読んだUIA記録|
|`result.png`|実行結果の実PAD画面|
|`verification.json`|出所、期待値/観測値、ファイルハッシュ、検証範囲|

最初の生成試行は専用Edgeが終了していたため送信前に停止しました。送信予約なしを確認し、同じ専用プロファイルを開き直して新しい試行を行いました。過去の不明要求は再送していません。詳細なローカル記録は`.work/catalog-copilot-generation-01`と`02`です。

このケースでは生成プロンプトが実際に役立つことを確認できましたが、アプリのRunループによる自動実行ではありません。貼付け・保存・実行は助手がUIAで行いました。他のアクション、再計画・復旧、汎用UI、社内受入の完了を意味しません。
