# 汎用Run経路の実機確認

新UIから、合成テキスト`Ticket 742 ready`の連続した数字を正規表現で`ID`へ置換し、新規UTF-8ファイルに保存する依頼を実行しました。CSV経路や手動生成コードの貼付けではなく、アプリのRunから実M365 CopilotとPADを呼び出しています。

## 開始処理の修正

最初の候補は、接続記録だけのジョブディレクトリーにも`job.json`が存在する前提の古い走査で開始を拒否しました。新ジョブ生成・Copilot送信・PAD実行はありません。`New-AgentJob`の重複した走査を共通の`Assert-AgentNoActiveJob`へそろえました。

回帰試験は、接続記録だけのディレクトリーを保持して開始できること、queued/unknownの登録ジョブは引き続き拒否することを確認します。`Test-GeneralJobStart.ps1`、基本契約149項目、HTTP試験がPASSしました。修正コミットは`cca1550`です。

## 修正版の結果

- App SHA256: `c22753f33b8823d53ff547b531e91ceb175d5dc4453df25a4bcba50a0459bded`。
- HTML SHA256: `cbab45bb02d86882f7b1642c0e57e391905ed1335a3ee09f762dcfed0f9799e8`。
- 新しい空の専用PADフロー`AgentRuntime_20260907`、Power Fx OFFで開始しました。既存の無題・採取・生成フローは上書きしていません。
- アプリが計画、検証、Main反映、保存、PAD実行、成果物読取りまで進みました。6回のPAD実行はすべてsuccessで、クリップボード復元も記録されています。
- 各出力はUTF-8 BOM付き18バイト、内容は正確に`Ticket ID ready`でした。入力ハッシュは不変、出力の保存ハッシュも一致しました。
- しかしCopilotはDONEを選ばず、成功した同等の処理を新しい出力先で繰り返しました。最大6往復に達してblockedで停止しています。**エージェントとしての通し完了ではありません。**

保存された観測には実際の内容、`text_status=complete`、`truncated=false`がありました。成果物が読めなかったという説明ではありません。今後は完了判断と次のコード生成の分離、成功済み処理の反復の扱いを検証します。出力があるだけで自動的にDONEへ変更しません。

ローカル証拠は`.work/general-live-01/start-failure.json`、`.work/general-live-02/run-1788740621492/measurement.json`、`.work/general-live-02/verification.json`、検証Homeのジョブ`04d57e2304754217941e19af9b891ace`です。元の記録と6つの出力は保持しています。
