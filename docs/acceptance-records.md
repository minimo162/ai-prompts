# 候補別の受入記録

出荷候補の3ファイルを封入して固定し、同じハッシュの証拠だけを集めます。`Test-AgentAcceptance.ps1`は不足・不一致を検出する保守用ツールで、公開や承認を実行しません。全条件が揃っても結果は`READY_FOR_REVIEW`、`release_approved=false`です。証拠の実施内容と正しさは担当者が確認します。

## 記録を用意する

候補を3ファイル専用のディレクトリへコピーし、外部の新しい証拠ディレクトリにひな形を作ります。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\New-AgentAcceptanceTemplate.ps1 -CandidateDirectory $packageDirectory -Kind business_e2e -OutputPath $newAcceptanceRecord
```

`$newAcceptanceRecord`は未使用の絶対パスで、名前を`.acceptance.json`で終えます。初期状態は`NOT_RUN`です。実験/観測なしにPASSや非模擬を設定しないでください。

- `candidate_hashes`: 自動で記録したApp/HTML/CMDの3ハッシュを維持。
- `kind`: nonlive、native_pad、live_m365、business_e2e、corporate_pc、usability、quality、comparison、documentationを区別。mock/障害注入境界を`simulated`とnotesへ明記。
- `requirements`: 実際に確認した項目だけを`8.1`等で記録。全51項目は`issues-8-14-acceptance.json`を参照。
- `host_id` / `participant_id`: PC/参加者ごとの一意な32桁の不透明ID。氏名、端末名、個人パスを入れない。同じ人/PCに別IDを発行して人数を増やさない。
- `attachments`: 証拠ディレクトリからの`relative_path`とそのファイルの`sha256`。絶対パス・範囲外・変更済みの添付は拒否する。業務本文や認証情報の公開を求めるものではなく、合成データの検証結果を使う。
- `metrics`: 件数、原本保全、実画面操作、品質、人時間等を実測から記録。時間比較は準備・操作・確認・復旧、総経過、PC占有を分ける。数値を見積りで埋めない。

## 評価する

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Test-AgentAcceptance.ps1 -CandidateDirectory $packageDirectory -EvidenceDirectory $evidenceDirectory -OutputPath $newGateReport
```

未準備は終了コード2です。出力は上書きせず、過去の記録を保持します。次のいずれかが欠けると`NOT_READY`になります。

- 同じ候補、添付ハッシュ、要求項目と検証層の対応
- 実画面での1/50/100件、件数一致・重複0・原本保全
- 社内PCを含む2台2利用者、管理者権限なしの社内受入
- 初見5人、うち4人以上の口頭介入なし完了
- 人が確認した正解に対する明確例90%以上、意図的な要確認例を全件レビューへ
- 同じ50行・品質基準で人時間30%以上の削減
- native PADのSave失敗/貼付け遅延/前面変更/clipboard保全、実M365の認証切れ/送信後timeout/長文/複数ターン

層が足りない項目を別の層のPASSで埋めません。Appだけの変更でも旧候補の記録は不一致になります。判定器のテストに使う架空記録は実受入に使いません。

人時間の削減率は、直接Copilotと固定処理のうち人時間が短い方を基準に再計算し、記録した率と一致することも検査します。項目ごとの`EVIDENCE_PRESENT`は必要な種類の証拠が揃ったという意味で、添付内容を人が確認したことの代わりにはしません。

現在の全非ライブ試験の成功は、実M365・native復元・意味品質・別PC/別利用者の成功ではありません。これらの記録は未実施のまま残しています。
