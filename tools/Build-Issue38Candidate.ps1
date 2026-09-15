[CmdletBinding()]
param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$destination = Join-Path $Root 'copilot/versions/20260915-excel-r1'
if (Test-Path -LiteralPath $destination) { throw 'Candidate already exists. Do not overwrite a sealed candidate; create a new version.' }
$utf8 = [Text.UTF8Encoding]::new($false)
New-Item -ItemType Directory -Path (Join-Path $destination 'knowledge') | Out-Null
$sources = Get-ChildItem (Join-Path $Root 'copilot/knowledge/PAD-Robin-0*.txt')
if ($sources.Count -ne 7) { throw 'Expected seven sources' }
foreach ($file in $sources) { Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $destination ('knowledge/' + $file.Name)) }
$instruction = [IO.File]::ReadAllText((Join-Path $Root 'copilot/agent-instructions-copyable.txt'))
$instruction += @'

【Excel値転記・20260915-excel-r1候補】
標準入力はこの指示全文と同版bundleの実添付です。20260913eの受入やコピーr2の静的結果をこの新版の実機PASSへ継承しません。
命令名・引数名・モード・列挙値・型・引用規則・依存構造は採取原文で固定します。パス、存在するシート名、固定矩形、転記先開始セル、出力名はデータの置換箇所です。定義と参照を一貫して変える変数名も含め、サンプルと異なるだけで未採取とはしません。ただし変更条件の実測有無を明示し、未検証の型・モードや任意の値へ一般化しません。
シート名は読取り命令に引数を発明せず、採取済みExcel.SetActiveWorksheet.ActivateWorksheetByNameを先に使います。入力原本を手動でシート選択・保存する前提にしません。
値転記の目的に数式・書式・コメント・画像の完全コピー、行削除、テーブル拡張を必須化しません。CSV文字列の1セル書込みは矩形転記ではありません。入力は読取り専用、テンプレートは原本からの作業コピー、出力は入力・原本・作業コピーと異なる新規xlsxです。
既知工程、不足工程、必要な確認を分けます。新版のExcel追補で明記した矩形書込み/型付きセル転記の不足を推測で埋めません。安全な部分フローは全体未完了と表示します。保存後に閉じて再読取りし、全対象セルの値・型・位置、対象外セル・数式・代表書式、原本SHA-256を照合して初めて完了とします。
シート存在、範囲の上下左右・件数・型、転記範囲、入力と出力の非同一、既存出力を事前確認します。欠落・無効・衝突なら依存する書込み・保存を停止し、無断補正/上書きしません。Excel SaveAs自体は衝突を安全停止しない実測があるため、未確認の安全引数を発明しません。未実測の検査を実装済みとせず、検証者による事前確認が必要なら明示します。専用出力は単独利用とし同時書込み競合は未対応です。
'@
[IO.File]::WriteAllText((Join-Path $destination 'agent-instructions.txt'), $instruction, $utf8)
$probe = [IO.File]::ReadAllText((Join-Path $Root 'catalog/evidence/p3-excel-sheet-probe-20260910.robin'))
$hash = (Get-FileHash (Join-Path $Root 'catalog/evidence/p3-excel-sheet-probe-20260910.robin')).Hash.ToLowerInvariant()
if ($hash -ne 'c7f3fa0408463de8ee36bf5b865720c64799f4a92cbf2a3b7efee4cfa1907c29') { throw 'Sheet probe changed' }
$sheetLine = ($probe -split '\r?\n' | Where-Object { $_.StartsWith('Excel.SetActiveWorksheet.') })
if (@($sheetLine).Count -ne 1) { throw 'Expected one full sheet switch action' }
$appendix = @'

Issue #38 Excel追補 / 20260915-excel-r1（候補、通常Copilot生成・PAD実行NOT_RUN）
本追補の現在の能力と過去のT04/P3履歴を分離する。過去の「読取りにシート名指定引数は未採取」は、別アクションのシート切替が未採取という意味ではない。
採取済み完全原文（入力インスタンスExcelInstance、存在するシート名Sheet1）:
'@
$appendix += "`n$sheetLine`n"
$appendix += @'
原文根拠: catalog/evidence/p3-excel-sheet-probe-20260910.robin、SHA-256 c7f3fa0408463de8ee36bf5b865720c64799f4a92cbf2a3b7efee4cfa1907c29。対応JSONおよびrun1/run2はPAD 2.71.115.26224、日本語、Power Fx OFF、編集可能で開いたexcel-catalog.xlsxのSheet1選択を保存・2回実行した別probe。JSONのpass_probe_not_bundledは当時の記録であり、本候補では上記全文を収録した。
前提: 先にExcel起動で取得したインスタンス、既存ワークシート。原本の初期選択を変えて保存する準備は不要。ReadCellsの直前にこの独立アクションを配置する。
未確認境界: 読取り専用＋別シート初期表示、日本語別名、今回の複数ブック転記全体はEX01〜EX03で未実施。旧probeのPASSをこの条件へ転記しない。以下の変更可能箇所は候補のパラメーター契約であり一般化済み実測ではない。
固定構造: Excel.SetActiveWorksheet.ActivateWorksheetByName / Instance / Name、文字列リテラルの引用規則。変更可能データ: 先に定義したインスタンスと既存シート名。未知モード・未採取引数を追加しない。
Excel.ReadFromExcel.ReadCellsのStartColumn/EndColumnは文字列、StartRow/EndRowは正の整数。TypedValues、FirstLineIsHeader: FalseとRangeValueのDataTable型を維持する。範囲は上下左右順・Excel限界内・有限件数、転記先も矩形が収まることを確認する。
入出力パスはローカル合成xlsxのみ、引用符・パーセント・エスケープを含む新しい特殊条件、結合セル、保護シート、マクロ、日付・空白・真偽値の転記は本fixture外で未確認。EX02/03の値は日本語を含むテキストと数値（0、負数、小数）。数式の計算結果取得も今回の入力fixtureには含めない。
原本は入力2ブックとテンプレート。作業用コピーを先に新規作成し、パスをフローへ渡す。作業コピーへ値のみ転記し、別の未存在xlsxへ保存後、閉じて読取り専用で再開し対象シートを再選択して照合する。
不足工程: 既存のExcel.WriteToExcel.WriteCellは文字列リテラルの単一セルだけを実測。DataTableをValueへ渡す矩形展開、数値/テキストを保つ変数書込み、有限行列反復の添字・型・座標は未採取/未実測。単一セル原文を根拠に矩形転記済みとは扱わない。
追加採取: 新規専用PADフローで「Excelワークシートに書き込む」のValueへ取得DataTable、指定シートと開始セルを設定し、コピー原文・設定・保存再コピー・全対象セル/型を実測する。範囲展開が使えない場合だけ有限行列反復と型付きセル書込みを採取・2回検証する。未採取のWriteRange等を捏造しない。
値転記と完全コピーを区別し、元数式・書式・コメント・画像を運ぶ操作は対象外。転記先の書式や対象外セル/数式の保全検査は必要であり、完全コピー機能とは別。
SaveAsは既存ファイルを無警告で上書きした過去実測がある。未存在の専用出力、原本/作業コピーとの非同一、既存衝突時停止を事前確認し、未確認のDoNotOverwrite引数を追加しない。原本SHA、作業コピーの由来、Run別成果物を検証者が照合する。
'@
foreach ($name in @('PAD-Robin-00-Index.txt','PAD-Robin-04-Office-PDF.txt','PAD-Robin-06-Examples.txt')) {
    $p=Join-Path $destination ('knowledge/'+$name)
    $old=[IO.File]::ReadAllText($p)
    # Keep old evidence text as historical scope; distinguish current appended capabilities.
    [IO.File]::WriteAllText($p, $old + "`n" + $appendix + "`n", $utf8)
}
$example=@'

例9: 指定シートからの読取り→値転記→別名保存（組合せ設計、実行未確認）
既知の読取り原文と採取済みシート切替を組み合わせる。各行は00/04の型・前提を参照し、ブックごとにインスタンスを区別する。次は採取済み切替行のNameだけを入力に存在するDataへ置換した候補部分列（この組合せのPAD実行未確認）。
Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''C:\\Users\\yuuki\\ai-prompts\\catalog\\fixtures\\excel\\t04-filter-input.xlsx''' Visible: True ReadOnly: True UseMachineLocale: False Instance=> ExcelInstance
Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: ExcelInstance Name: $'''Data'''
Excel.ReadFromExcel.ReadCells Instance: ExcelInstance StartColumn: $'''A''' StartRow: 1 EndColumn: $'''C''' EndRow: 6 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> ExcelData
Excel.CloseExcel.Close Instance: ExcelInstance
これはデータ値を置換した参照用部分列であり完成フローではない。切替の採取原文Sheet1は上の追補に完全収録済み。この列を実測済みの組合せとしない。実依頼では存在するシート名・パス・固定矩形を一貫して指定する。
全体の依存順: 安全事前確認→テンプレート作業コピー準備→入力A読取り専用起動/シート選択/矩形読取り→入力Bも同様→作業コピー編集可能起動/転記先シート選択→型を保持した矩形値転記（追加採取待ち）→新規xlsx SaveAs→全インスタンスを保存せず閉じる→出力読取り専用再開/両シート再選択/全対象セル照合→終了→原本SHAと対象外部分の独立照合。
転記原文・比較手順のPAD実測が欠ける現時点では、この部分列を依頼全体の完了として返さない。安全確認も生成停止と実行時停止を区別する。照合器だけのPASSはCopilot生成やPAD RunのPASSではない。
'@
$p=Join-Path $destination 'knowledge/PAD-Robin-06-Examples.txt'
[IO.File]::AppendAllText($p,$example+"`n",$utf8)
& (Join-Path $PSScriptRoot 'Build-KnowledgeBundle.ps1') -Root $destination -KnowledgeDirectory knowledge -OutputPath 'knowledge/PAD-Robin-Knowledge-Bundle.txt'
$records=@(Get-ChildItem (Join-Path $destination 'knowledge/PAD-Robin-0*.txt') | Sort-Object Name | ForEach-Object {
    @{path='knowledge/'+$_.Name;sha256=(Get-FileHash $_.FullName).Hash.ToLowerInvariant();bytes=$_.Length}
})
$manifest=[ordered]@{
    schema_version=1;version='20260915-excel-r1';status='CANDIDATE_PARTIAL_LIVE_NOT_RUN';inherits_live_acceptance=$false
    base_commit='c60251d65afe30160bcb33b08a988a46028b783c';base_version='20260913e';copy_rule_version='20260915-copyable-r2'
    instruction_path='agent-instructions.txt';instruction_sha256=(Get-FileHash (Join-Path $destination 'agent-instructions.txt')).Hash.ToLowerInvariant();instruction_utf16=$instruction.Length
    bundle_path='knowledge/PAD-Robin-Knowledge-Bundle.txt';bundle_sha256=(Get-FileHash (Join-Path $destination 'knowledge/PAD-Robin-Knowledge-Bundle.txt')).Hash.ToLowerInvariant()
    source_files=$records;acceptance_freeze_sha256=(Get-FileHash (Join-Path $Root 'catalog/acceptance/issue38/freeze.json')).Hash.ToLowerInvariant()
    evidence=@{sheet_probe_sha256=$hash;sheet_probe_scope='Historical editable Sheet1 only';matrix_write='NOT_CAPTURED';copilot='NOT_RUN';pad='NOT_RUN'}
}
[IO.File]::WriteAllText((Join-Path $destination 'manifest.json'),($manifest|ConvertTo-Json -Depth 8)+"`n",$utf8)
Write-Output "Candidate $destination; instruction UTF16 $($instruction.Length)"
