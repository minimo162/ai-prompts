[CmdletBinding()]
param([Parameter(Mandatory)][string]$EvidenceDirectory)
# Separate synthetic control experiment: Excel open/save without any cell writes.
# It cannot demonstrate a PAD flow, and never saves the frozen template itself.
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../catalog/acceptance/issue38'))
$destination = [IO.Path]::GetFullPath($EvidenceDirectory)
if (-not $destination.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Dedicated Issue38 directory required' }
if (Test-Path -LiteralPath $destination) { throw 'New experiment directory required' }
$template = Join-Path $root 'fixtures/EX02/template.xlsx'
$originalHash = (Get-FileHash -LiteralPath $template -Algorithm SHA256).Hash
[void][IO.Directory]::CreateDirectory($destination)
$work = Join-Path $destination 'work.xlsx'
$result = Join-Path $destination 'result.xlsx'
[IO.File]::Copy($template, $work, $false)
$excel = $null
$book = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AutomationSecurity = 3
    $book = $excel.Workbooks.Open($work, 0, $false)
    if (Test-Path -LiteralPath $result) { throw 'Unexpected output collision' }
    $book.SaveAs($result, 51)
    $book.Close($false)
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)
    $book = $null
} finally {
    if ($book) { $book.Close($false); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($book) }
    if ($excel) { $excel.Quit(); [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }
}
$after = (Get-FileHash -LiteralPath $template -Algorithm SHA256).Hash
$workHash = (Get-FileHash -LiteralPath $work -Algorithm SHA256).Hash
if ($originalHash -cne $after -or $workHash -cne $originalHash) { throw 'Original/work SHA changed unexpectedly' }
$record = [ordered]@{
    case = 'EX02-NATIVE-NOOP-R4'
    kind = 'CONTROL_EXPERIMENT_EXCEL_COM_NOT_PAD_NOT_COPILOT'
    observed_at = [DateTime]::UtcNow.ToString('o')
    cell_write_calls = 0
    template_sha_before = $originalHash
    template_sha_after = $after
    work_sha = $workHash
    output_sha = (Get-FileHash -LiteralPath $result -Algorithm SHA256).Hash
    saved_closed = $true
}
[IO.File]::WriteAllText((Join-Path $destination 'experiment.json'), ($record | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
$record | ConvertTo-Json
