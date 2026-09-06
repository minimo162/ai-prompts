# 3ファイルの凍結・公開・復旧

通常の配布物は `業務エージェント.cmd`、`App.ps1`、`index.html` の3ファイルです。以下の保守ツールと記録は配布担当者側で管理し、利用者に4つ目の必須ファイルを増やしません。実際の社内共有パス・権限・保存期間は担当者と確認する必要があり、このリポジトリには埋め込みません。

## 凍結と持込み

1. Appの`App-Version`とHTMLの`app-version`を一致させます。状態形式を変えたときは`State-Contract`も見直します。現在の契約2は、型付きCSV計画、結果引継ぎ、質問回答を含みます。単なるsemverの書換えで互換性を装わないでください。
2. 編集後に、配布予定のチャネルで3ファイルを結び付けます。

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Seal-AgentRelease.ps1 -Directory $candidateDirectory -Channel candidate
   ```

   `$candidateDirectory`は担当者が指定する候補ディレクトリの絶対パスです。App内の1行に、正規化したApp本体・HTML・CMDのSHA256とリリースIDを記録します。その1行だけをApp本体ハッシュから正規化するため循環参照はありません。同じ内容・チャネルで再実行しても同じバイト列になります。

3. この3ファイルを凍結してコミットし、必要な非ライブ・実機・業務・別PC受入を同じ候補で実行します。`.gitattributes`は配布物の改行変換を止めています。Git保存・取得時にも封入したハッシュを保つためです。凍結後に1文字でも変更した場合は再度結び付け、変更箇所に必要な受入をやり直します。チャネル変更もAppのバイト列を変えるので、受入後に無断で付け替えないでください。
4. 凍結コミットと同じ候補について、外部の新しい記録パスへ対応表を作れます。

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Seal-AgentRelease.ps1 -Directory $candidateDirectory -Channel candidate -RecordPath $newRecordPath -SourceCommit $frozenCommit
   ```

   `$frozenCommit`は対応する40桁のGitコミット、`$newRecordPath`は3ファイルのディレクトリ外にある未使用の絶対パスです。既存記録を上書きしません。この対応表は署名・出荷承認を意味せず、`acceptance_approved=false`を記録します。正式な受入結果・承認者・持込み経路はこの対応表と紐付けて管理してください。
5. 社内PCでは、まずWindows標準の`Get-FileHash -Algorithm SHA256`で3ファイルを照合します。信頼した経路で受け取った承認記録と一致することを確認してから起動・保守を行います。App内のハッシュは整合性検査であり、3ファイルと宣言を同時に改ざんされた場合の真正性を証明しません。公開元の所有者・ACL、承認済み持込み、組織の署名方針が別途必要です。

CMDはAppを実行する前に3ファイルを読取り共有で保持し、組合せを検査します。確認後・起動前の差替えも通常の公開ツールの排他と競合して止まります。欠落・混在は日本語の案内と詳細を表示して終了します。Appを直接Serveで起動した場合にも配布一式を検査します。

## 公開

公開先は配布担当者だけが更新でき、利用者は読取りのみとする運用を、共有管理者に確認してください。ツールはACLを勝手に設定・解除しません。本番権限の確認を開発端末のNTFS試験で代替しないでください。

信頼済み保守用Appを`-Mode Library`で読み、`Get-AgentRelease`で候補と現在の公開版を確認して、次を実行します。パスと期待リリースは担当者が今回の記録から指定します。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Publish-AgentSource.ps1 -SourceDirectory $candidateDirectory -DestinationDirectory $publishedDirectory -EvidenceDirectory $newPublishEvidence -ExpectedSourceRelease $candidateRelease -ExpectedDestinationRelease $currentPublishedRelease
```

- 公開先の3ファイルを全て排他で開いてから書きます。元のファイルオブジェクト・所有者・ACLを維持し、前後のバイト列・権限を記録します。
- 新しい記録領域には元の一式、対象パス、公開プロセスのPIDと開始時刻を保存します。通常の例外では元のバイト列へ戻し、戻せたかも記録します。
- プロセス/OS停止を一括トランザクションにはしません。途中の一式が残った場合はハッシュ宣言と一致せず、起動・通常更新が拒否されます。
- 公開後は再読取りと所有者/ACLの比較が成功し、`result.json`が`published`となったことを確認します。
- 承認された以前の一式を共有へ戻す場合だけ、同じ期待リリース指定と`-Rollback`を使用します。利用者側の状態互換性は次項の旧版選択で個別に確認します。

## 公開途中で停止した場合

1. PIDだけで判断せず、記録したプロセス開始時刻と実在を照合します。稼働中の元公開プロセスに復旧を重ねません。
2. 公開先の現在の3ハッシュと、今回の不変バックアップのリリースを確認します。破損した公開一式を正常なローカル版として登録しません。
3. 元の公開記録と同じ対象へ、現在の3ハッシュを明示して戻します。

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\Restore-AgentPublishedBackup.ps1 -PublicationEvidenceDirectory $originalPublishEvidence -DestinationDirectory $publishedDirectory -EvidenceDirectory $newRestoreEvidence -ExpectedBackupRelease $backupRelease -ExpectedAppHash $currentAppHash -ExpectedHtmlHash $currentHtmlHash -ExpectedCmdHash $currentCmdHash
   ```

   ハッシュ文字列は小文字です。元公開プロセスが生存中、対象が違う、現在の内容やACLが変わった、バックアップが不一致の場合は書込み前に拒否します。復旧用の記録も新規作成し、元の記録・バックアップを改変しません。検証不能なら不明のまま残し、無条件の起動や再送信はしません。

## 利用者ローカルの旧版選択

「配布版・旧版への復帰」から保存済みの版を確認し、配布担当者が承認した版のリリースID・チャネルを見て選択します。

- 実行中/状態不明の依頼がある場合は切替を拒否します。`run.claim`や履歴を消して通過させません。
- 全保存ジョブのschema、CSV action contract、引継ぎ/回答形式に必要な契約を求めます。旧版の宣言では読めない状態、未知の形式がある場合は復帰できません。
- 切替は`app/current.json`だけです。入力・設定・成果物・履歴を巻き戻しません。現在のプロセスから新規実行することを拒否し、CMDで選択した版を開き直します。
- 旧版固定中は、到達可能な共有版を検証したうえで自動更新を抑止します。到達可能だが壊れた共有を正常扱いしません。固定を解除した後は**共有側のCMD**から起動すると、検証した共有版へ戻れます。保存済みローカルCMDは現在選択中のローカル版を開く入口です。
- 以前の未封入キャッシュは、元のポインターと3ファイルのハッシュが一致するときだけ、新しい検証済み共有版へ更新するために読取り照合します。旧キャッシュ自体を実行する許可や旧版候補の登録には使いません。歴史的な配布物をその場で書き換え、同じ版として扱わないでください。

## 保存容量と未確認の受入

旧版・全履歴・成果物・Edge認証プロファイルは自動削除しません。保存期間や持出しの可否は組織の情報取扱ルールで合意してください。起動中データや最後の正常版を減らして容量を確保する処理はありません。空き容量256MiB未満では新しい依頼の開始を止めます。この最小余裕は実M365のキャッシュ容量や処理全体の必要容量を保証する値ではありません。

ローカルの混在拒否、native CMD、公開プロセス強制停止、バックアップ復旧、互換性拒否、画面の版選択は試験対象に含めました。本番共有の読取り権限、実SMBのロック/同時起動、社内PC・別利用者での起動/更新/復帰、組織の保持方針の合意は未検証です。
