[CmdletBinding()]
param(
    [string]$IndexPath = (Join-Path $PSScriptRoot '..\catalog\index.json'),
    [string]$OutputPath = (Join-Path $PSScriptRoot '..\catalog\coverage.json')
)

$ErrorActionPreference = 'Stop'
$index = Get-Content -LiteralPath (Resolve-Path -LiteralPath $IndexPath) -Raw | ConvertFrom-Json

$observed = @(
    foreach ($a in $index.actions) {
        [ordered]@{
            category = $a.category
            ui_name = $a.ui_name
            action_id = $a.id
            variant = $a.variant
            settings = $a.settings
            status = if ($a.verification.re_pasted -and $a.verification.executed_in_flow) { 'verified_roundtrip_and_run' } elseif ($a.verification.copied) { 'captured_partial_verification' } else { 'not_verified' }
            reference = $a.robin_path
            evidence = [ordered]@{
                sha256 = $a.sha256
                added_from_left_panel = [bool]$a.verification.added_from_left_panel
                copied = [bool]$a.verification.copied
                saved = [bool]$a.verification.saved
                re_pasted = [bool]$a.verification.re_pasted
                executed_in_flow = $a.verification.executed_in_flow
            }
        }
    }
)

$required = @(
    [ordered]@{ id='A-text-number-boolean-set'; area='A'; purpose='文字列・数値・真偽値の設定'; status='partial'; observed_action_ids=@('variables-set-text','variables-set-zero','variables-set-special-text'); reason='文字列と数値は観測済み。真偽値の独立採取は未確認。'; reference='catalog/index.json' },
    [ordered]@{ id='A-arithmetic-add-subtract'; area='A'; purpose='数値の加減算'; status='partial'; observed_action_ids=@('variables-increase-one','variables-increase-index'); reason='増加（加算）例は観測済み。減算は未確認。'; reference='catalog/index.json' },
    [ordered]@{ id='A-list-create-add-get'; area='A'; purpose='リスト作成・項目追加・取出し'; status='partial'; observed_action_ids=@('variables-create-new-list','variables-add-item-to-list'); reason='作成と追加は観測済み。項目取出しは未確認。'; reference='catalog/index.json' },
    [ordered]@{ id='A-text-replace-split-join'; area='A'; purpose='文字列の置換・分割・結合'; status='observed_partial'; observed_action_ids=@('text-replace-literal','text-replace-regex','text-split-comma','text-split-space','text-join-pipe'); reason='主要モードを観測済み。切出しは別チェック。'; reference='catalog/index.json' },
    [ordered]@{ id='A-text-substring'; area='A'; purpose='文字列の切出し'; status='observed_partial'; observed_action_ids=@('text-get-subtext-mixed-index-length'); reason='サブテキストの取得で開始インデックス1・長さ3のUnicode混在リテラルを実測済み。別の開始位置・末尾まで取得する長さ設定は未確認。'; reference='catalog/index.json; catalog/evidence/text-substring-validation.json' },
    [ordered]@{ id='A-number-conversion'; area='A'; purpose='数値変換'; status='observed_partial'; observed_action_ids=@('text-to-number-variable','text-to-number-decimal','number-to-text-two-decimals'); reason='変換と小数2桁書式は観測済み。別地域・桁区切りは未確認。'; reference='catalog/index.json' },
    [ordered]@{ id='A-datetime'; area='A'; purpose='日時取得・書式化'; status='partial'; observed_action_ids=@('datetime-get-current-date'); reason='現在の日時を取得（取得=現在の日付のみ）は今回の左パネル採取・再貼付け・実行まで確認済み。日時加算・減算と日時書式化は未確認。'; reference='catalog/index.json; catalog/evidence/datetime-current-date-validation.json' },
    [ordered]@{ id='B-if-else'; area='B'; purpose='If／Else'; status='not_observed'; observed_action_ids=@(); reason='現在の実測カタログにブロック原文なし。'; reference=$null },
    [ordered]@{ id='B-loop-fixed-foreach-exit'; area='B'; purpose='回数指定ループ・For each・ループ脱出'; status='partial'; observed_action_ids=@('loop-one-to-three'); reason='定数範囲Loopのみ観測済み。For eachと脱出は未確認。'; reference='catalog/index.json' },
    [ordered]@{ id='B-error-subflow'; area='B'; purpose='エラー処理・サブフロー作成／呼出し'; status='not_observed'; observed_action_ids=@(); reason='今回のindexに対応する左欄原文がない。'; reference=$null },
    [ordered]@{ id='C-datatable'; area='C'; purpose='データテーブル作成・行追加・行反復・セル参照'; status='partial'; observed_action_ids=@('datatable-create-empty','datatable-filter-status-equals-index2'); failed_action_ids=@('datatable-add-row-empty-failed'); reason='空のデータテーブル作成と、列インデックス2のFilterDataTable条件は実測済み。0行0列への空行追加は設計エラーとなったため失敗例として保存。列を持つテーブルの行追加・行反復・セル参照は未採取。'; reference='catalog/index.json; catalog/evidence/datatable-create-validation.json; catalog/evidence/filter-t02-roundtrip2-run-2.json' },
    [ordered]@{ id='C-csv-read-write'; area='C'; purpose='CSV読取り／書出し'; status='partial'; observed_action_ids=@('file-write-csv-pdf-table-headers','csv-read-utf8-system-default-no-header','csv-read-utf8-system-default-header','csv-write-variable-reference'); reason='UTF-8 CSV読取り（ヘッダーなし／ヘッダーあり）と、DataTable変数参照でのCSV書出しは実測済み。別区切り・引用符境界の追加モードは未確認。'; reference='catalog/index.json; catalog/evidence/csv-read-validation.json; catalog/evidence/filter-t02-roundtrip2-run-2.json' },
    [ordered]@{ id='D-files-folders'; area='D'; purpose='ファイル取得・存在確認・フォルダー作成・テキスト読書き・コピー・移動・名前変更'; status='partial'; observed_action_ids=@('file-read-text-utf8','file-write-text-utf8-overwrite','file-copy-single-no-overwrite'); reason='UTF-8読取り、UTF-8書出し、単一ファイルのコピー（衝突時は何もしない）は実測済み。フォルダー内取得、存在確認、作成、移動・名前変更は未確認または別設定が必要。'; reference='catalog/index.json; catalog/evidence/text-write-validation.json; catalog/evidence/file-copy-validation.json' },
    [ordered]@{ id='E-excel'; area='E'; purpose='Excel起動・セル／範囲読書き・シート・反復・別名保存・終了'; status='partial'; observed_action_ids=@('excel-launch-new-visible','excel-launch-open-readonly','excel-write-cell-a1-text','excel-read-cell-a1-typed','excel-read-range-a1-b2','excel-read-used-range','excel-save-as-xlsx','excel-close-no-save'); reason='起動・セル／範囲・保存・終了は観測済み。シート選択とデータ反復の独立例は未確認。'; reference='catalog/index.json' },
    [ordered]@{ id='F-office-pdf'; area='F'; purpose='Word・PowerPoint・PDFの主要操作'; status='observed_partial'; observed_action_ids=@('word-launch-new-visible','word-launch-open-readonly','word-write-end-text','word-read-all-text','word-replace-all-literal','word-save-as-docx-extension','word-close-no-save','powerpoint-launch-new','powerpoint-launch-open','powerpoint-add-slide-end','powerpoint-write-slide-index','powerpoint-read-all-text','powerpoint-save-as-pptx','powerpoint-close-no-save','pdf-extract-text-all-pages','pdf-extract-text-pages-2-3','pdf-extract-text-page-2','pdf-extract-text-page-2-layout','pdf-extract-tables-with-headers','pdf-extract-tables-without-headers','pdf-extract-images-all-pages','pdf-extract-images-page-1','pdf-extract-pages-pages-2-3-no-overwrite','pdf-merge-two-files-no-overwrite','pdf-merge-two-files-b-a-no-overwrite'); reason='既存採取と証跡を再利用する。新規エージェント登録での再利用は未確認。'; reference='docs/office-action-capture.md; docs/pdf-action-capture.md' },
    [ordered]@{ id='G-ui-browser'; area='G'; purpose='起動／接続・文字入力・クリック・待機・文字取得・終了'; status='blocked_pending_live_ui'; observed_action_ids=@(); reason='過去のEdge起動はWeb拡張機能通信エラー。現在セッションでもPADウィンドウが観測できず、通し採取は未実施。'; reference='docs/robin-action-catalog.md; pad-robin-prompts.md' }
)

$inventoryPath = Join-Path $PSScriptRoot '..\catalog\evidence\pad-action-inventory-20260909.json'
$liveInventory = $null
if (Test-Path -LiteralPath $inventoryPath) {
    $liveInventory = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $inventoryPath), (New-Object Text.UTF8Encoding($false))) | ConvertFrom-Json
}
$liveMap = @{
    'A-text-number-boolean-set' = @('LanguageConstructs.Assign')
    'A-arithmetic-add-subtract' = @('Variables.IncreaseVariable','Variables.DecreaseVariable')
    'A-list-create-add-get' = @('Variables.CreateNewList','Variables.AddItemToList','Variables.RemoveItemFromList')
    'A-text-replace-split-join' = @('Text.Replace','Text.SplitText','Text.JoinText')
    'A-text-substring' = @('Text.GetSubtext')
    'A-number-conversion' = @('Text.ToNumber','Text.FromNumber')
    'A-datetime' = @('DateTime.GetCurrentDateTime','DateTime.Add','DateTime.Subtract')
    'B-if-else' = @('LanguageConstructs.If','LanguageConstructs.Else','LanguageConstructs.ElseIf')
    'B-loop-fixed-foreach-exit' = @('LanguageConstructs.Loop','LanguageConstructs.Foreach','LanguageConstructs.Break','LanguageConstructs.Continue')
    'B-error-subflow' = @('LanguageConstructs.Block','LanguageConstructs.CallFunction','LanguageConstructs.ExitFunction')
    'C-datatable' = @('Variables.CreateNewDatatable','Variables.AddRowToDataTable','Variables.ModifyDataTableItem')
    'C-csv-read-write' = @('File.ReadFromCSVFile','File.WriteToCSVFile','Variables.GenerateDataTableFromCSV')
    'D-files-folders' = @('File.ReadTextFromFile','File.WriteText','File.Copy','File.Move','File.RenameFiles','Folder.GetFiles','Folder.Create','If.File.IfFile','If.Folder.IfFolderExists')
    'E-excel' = @('Excel.SelectCellsFromExcel','Excel.ReadCellFormula','Excel.AddWorksheet','Excel.AppendCells')
    'F-office-pdf' = @('Word.LaunchWord','PowerPoint.LaunchPowerPoint','Pdf.ExtractTextFromPDF','Pdf.ExtractTablesFromPDF')
    'G-ui-browser' = @('WebAutomation.LaunchEdge','WebAutomation.GoToWebPage','WebAutomation.Click','WebAutomation.ExecuteJavascript','WebAutomation.CloseWebBrowser','UIAutomation.PopulateTextField','UIAutomation.Click')
}
if ($null -ne $liveInventory) {
    foreach ($check in $required) {
        $candidates = @($liveMap[[string]$check.id])
        $check['live_ui_candidates'] = @($liveInventory.nodes | Where-Object { $candidates -contains $_.automation_id } | ForEach-Object {
            [ordered]@{ ui_name = $_.ui_name; automation_id = $_.automation_id; parent_id = $_.parent_id }
        })
    }
}

$result = [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToString('o')
    environment = $index.environment
    left_panel_scope = [ordered]@{
        complete = $false
        current_tree_inventory_complete = [bool]($null -ne $liveInventory -and $liveInventory.reached_bottom)
        status = if ($null -ne $liveInventory) { 'observed_current_designer_tree' } else { 'not_reobserved_in_current_session' }
        observed_categories = if ($null -ne $liveInventory) { @($liveInventory.nodes | Where-Object kind -eq 'group' | Select-Object -ExpandProperty ui_name -Unique | Sort-Object) } else { @($index.actions | Select-Object -ExpandProperty category -Unique | Sort-Object) }
        observed_variant_count = $index.actions.Count
        live_node_count = if ($null -ne $liveInventory) { $liveInventory.nodes.Count } else { 0 }
        live_action_count = if ($null -ne $liveInventory) { @($liveInventory.nodes | Where-Object kind -eq 'action').Count } else { 0 }
        live_inventory_path = if ($null -ne $liveInventory) { 'catalog/evidence/pad-action-inventory-20260909.json' } else { $null }
        note = 'complete=false means this is not a complete PAD feature reference or execution allowlist. The current_tree inventory covers the expanded ActionsTreeView only; unobserved names are not inferred.'
        current_session_reason = if ($null -ne $liveInventory) { 'PAD Designer ActionsTreeView groups were expanded and scrolled from top to bottom in a dedicated empty flow; actions_executed=0.' } else { 'PAD native window was not returned by initial observation.' }
    }
    observed_actions = $observed
    required_checks = $required
}

$json = $result | ConvertTo-Json -Depth 20
$encoding = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText((Resolve-Path -LiteralPath (Split-Path -Parent $OutputPath)).Path + '\' + (Split-Path -Leaf $OutputPath), $json, $encoding)
Write-Output "WROTE=$OutputPath"
Write-Output "OBSERVED_ACTIONS=$($observed.Count)"
Write-Output "REQUIRED_CHECKS=$($required.Count)"
