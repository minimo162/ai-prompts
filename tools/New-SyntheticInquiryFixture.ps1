# Assistant-authored draft, not human-reviewed ground truth. No provider calls.
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$destination=Get-AgentFullPath $OutputDirectory;Assert-AgentNoReparse $destination
if(Test-Path -LiteralPath $destination){throw 'FIXTURE_EXISTS: Use a new directory.'}
$groups=[ordered]@{
 '支払'=@('請求書の振込予定日を確認したいです。','取引先から入金がまだないと連絡がありました。送金状況を調べてください。','支払先の銀行口座を変更する手順を教えてください。','請求書を二重に支払っていないか確認したいです。','立替経費の精算がいつ振り込まれるか教えてください。','未払の請求書が支払一覧に載っているか確認をお願いします。','海外送金の手数料をどちらが負担するか確認したいです。','請求書の支払期限を延長できるか担当者に相談したいです。','振込依頼書の承認状況を確認したいです。','支払通知書を受け取る方法を教えてください。');
 '決算'=@('月次決算の締め日を教えてください。','決算仕訳の提出期限を確認したいです。','決算用の残高明細を提出する場所を教えてください。','決算時の前払費用の振替仕訳を確認したいです。','固定資産の減価償却額を決算資料と照合したいです。','期末の未払計上に使う資料の様式を教えてください。','四半期決算の連結パッケージ提出期限を確認したいです。','棚卸結果を決算へ反映する担当者を教えてください。','月末の試算表と補助簿の差異を確認したいです。','決算後の修正仕訳の申請手順を教えてください。');
 'システム'=@('経理システムにログインできません。','パスワード再設定の画面が表示されません。','会計アプリを開くとエラーメッセージが出て終了します。','承認画面のボタンが反応しない不具合を調べてください。','CSV取込時に文字化けするので設定を確認したいです。','帳票をダウンロードするとファイルが空になる不具合があります。','新しい端末に業務アプリを設定する手順を教えてください。','システムの操作権限が付与されているか確認したいです。','ネットワーク接続後も会計アプリの通信が失敗します。','取込ファイル名に引用符とカンマを含むとアプリでエラーになります。');
 'その他'=@('会議室の予約方法を教えてください。','来客用の入館申請の窓口を教えてください。','社内便で荷物を送る手順を確認したいです。','事務用品を注文する担当部署を教えてください。','研修会の開催場所を確認したいです。','社員食堂の利用時間を教えてください。','電話番号の内線一覧はどこにありますか。','貸出備品の返却場所を教えてください。','社内イベントの申込み期限を確認したいです。','休憩室の忘れ物について問い合わせたいです。')
}
$ambiguous=@('処理が進みません。何の手続かはまだ確認できていません。','例の件について担当者を教えてください。','支払承認の遅れなのか、画面の不具合なのか判断できません。','決算資料の数値かシステム表示の問題か切り分けできていません。','請求書の計上時期と送金日を同時に相談したいです。','エラーの詳細は不明ですが、決算処理も支払処理も進みません。','前回の依頼を取り消したいですが、依頼内容が手元にありません。','この一覧が何のためのものか説明がなく、担当が分かりません。','資料に食い違いがありますが、資料名と対象期間が分かりません。','急ぎで確認をお願いします。対象となる業務は未記載です。')
$csv=@([pscustomobject]@{values=@('id','本文','任意列')});$expected=@();$index=0
foreach($category in $groups.Keys){foreach($body in $groups[$category]){$index++;$id=$index.ToString('00000');$optional=if($index%4 -eq 0){'=1+1'}elseif($index%3 -eq 0){"引用`"とカンマ,を含む`r`n任意列"}else{''};$csv+=[pscustomobject]@{values=@($id,$body,$optional)};$expected+=[pscustomobject]@{id=$id;text=$body;category=$category;needs_review=$false}}}
foreach($body in $ambiguous){$index++;$id=$index.ToString('00000');$csv+=[pscustomobject]@{values=@($id,$body,'要確認用の合成例')};$expected+=[pscustomobject]@{id=$id;text=$body;category=$null;needs_review=$true}}
[void][IO.Directory]::CreateDirectory($destination)
$csvPath=Join-Path $destination 'inquiries-50.csv';[IO.File]::WriteAllText($csvPath,(ConvertTo-AgentCsv $csv),(New-Object Text.UTF8Encoding($true)))
Write-AgentJson (Join-Path $destination 'expected-draft.json') @{schema_version=1;author='assistant draft';human_reviewed=$false;reviewer_id='';reviewed_utc='';input_sha256=Get-AgentHash $csvPath;categories=@($groups.Keys);rows=$expected;notes='人が全例と基準を確認するまで正解データとして受入に使用しない。'}
Write-Output $destination
