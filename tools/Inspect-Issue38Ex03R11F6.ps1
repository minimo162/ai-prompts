[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$TemplatePath,
    [Parameter(Mandatory)][string]$SheetName,
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$EvidencePath
)

$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$issueRoot = Join-Path $root 'catalog/acceptance/issue38'
$template = (Resolve-Path -LiteralPath $TemplatePath).Path
$output = (Resolve-Path -LiteralPath $OutputPath).Path
$evidence = [IO.Path]::GetFullPath($EvidencePath)
$expectedWorkSha = '881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21'

foreach ($path in @($template, $output, $evidence)) {
    if (-not ([IO.Path]::GetFullPath($path)).StartsWith($issueRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Dedicated Issue38 paths only'
    }
}
if (Test-Path -LiteralPath $evidence) { throw 'Evidence exists; refusing overwrite' }
if ((Get-FileHash -LiteralPath $template -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expectedWorkSha) {
    throw 'Frozen template SHA mismatch'
}

function Get-CellState {
    param($Book, [string]$SheetName, [string]$Address)
    $sheet = $null
    $cell = $null
    try {
        $sheet = $Book.Worksheets.Item($SheetName)
        $cell = $sheet.Range($Address)
        $value = $cell.Value2
        return [ordered]@{
            sheet = $SheetName
            address = $Address
            value2 = $value
            value2_dotnet_type = if ($null -eq $value) { $null } else { $value.GetType().FullName }
            text = [string]$cell.Text
            has_formula = [bool]$cell.HasFormula
            formula = if ([bool]$cell.HasFormula) { [string]$cell.Formula } else { $null }
            number_format_invariant = [string]$cell.NumberFormat
            number_format_local = [string]$cell.NumberFormatLocal
            prefix_character = [string]$cell.PrefixCharacter
        }
    } finally {
        if ($cell) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
        if ($sheet) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet) }
    }
}

$hashBefore = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant()
$excel = $null
$templateBook = $null
$outputBook = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.AutomationSecurity = 3
    $templateBook = $excel.Workbooks.Open($template, 0, $true)
    $outputBook = $excel.Workbooks.Open($output, 0, $true)
    $before = Get-CellState $templateBook $SheetName 'F6'
    $after = Get-CellState $outputBook $SheetName 'F6'
} finally {
    if ($outputBook) {
        $outputBook.Close($false)
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($outputBook)
    }
    if ($templateBook) {
        $templateBook.Close($false)
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($templateBook)
    }
    if ($excel) {
        $excel.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    }
}
$hashAfter = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant()
$checks = [ordered]@{
    output_unchanged_by_read = $hashBefore -ceq $hashAfter
    value_is_exact_text_100_percent = ($after.value2_dotnet_type -ceq 'System.String') -and ($after.value2 -ceq '100%')
    displayed_text_is_100_percent = $after.text -ceq '100%'
    number_format_invariant_preserved = $after.number_format_invariant -ceq $before.number_format_invariant
    number_format_local_preserved = $after.number_format_local -ceq $before.number_format_local
    prefix_character_preserved_empty = ($before.prefix_character -ceq '') -and ($after.prefix_character -ceq '')
    no_formula = -not $after.has_formula
}
$allPass = @($checks.Values | Where-Object { -not $_ }).Count -eq 0
$record = [ordered]@{
    schema_version = 1
    kind = 'EX03_R11_F6_EXCEL_NATIVE_READ_ONLY_INSPECTION'
    observed_at = [DateTime]::UtcNow.ToString('o')
    output_path = $output
    output_sha256_before = $hashBefore
    output_sha256_after = $hashAfter
    template_f6 = $before
    saved_f6 = $after
    checks = $checks
    status = if ($allPass) { 'PASS_F6_SYSTEM_STRING_100_PERCENT_ORIGINAL_FORMAT_EMPTY_PREFIX_NO_FORMULA' } else { 'FAIL' }
    scope = 'Fixed EX03 F6 target only; no type generalization.'
}
$parent = Split-Path -Parent $evidence
if (-not (Test-Path -LiteralPath $parent)) { [void][IO.Directory]::CreateDirectory($parent) }
[IO.File]::WriteAllText($evidence, (($record | ConvertTo-Json -Depth 10) + "`n"), [Text.UTF8Encoding]::new($false))
[pscustomobject]$record | ConvertTo-Json -Depth 10
if (-not $allPass) { exit 1 }
