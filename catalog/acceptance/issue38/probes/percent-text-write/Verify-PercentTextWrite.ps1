[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$OutputPath,
    [Parameter(Mandatory = $true)][string]$EvidencePath,
    [Parameter(Mandatory = $true)][string]$RunLabel
)

$ErrorActionPreference = 'Stop'
$probeRoot = [IO.Path]::GetFullPath($PSScriptRoot)
$sourcePath = (Resolve-Path -LiteralPath (Join-Path $probeRoot 'source.xlsx')).Path
$templatePath = (Resolve-Path -LiteralPath (Join-Path $probeRoot 'template.xlsx')).Path
$output = (Resolve-Path -LiteralPath $OutputPath).Path
$evidence = [IO.Path]::GetFullPath($EvidencePath)
foreach ($path in @($sourcePath, $templatePath, $output, $evidence)) {
    if (-not $path.StartsWith($probeRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Probe paths only'
    }
}
if (Test-Path -LiteralPath $evidence) { throw 'Evidence exists' }
if ([IO.Path]::GetExtension($output) -cne '.xlsx') { throw 'Output must be xlsx' }

function Get-Sha256([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-ValueKind($Value) {
    if ($null -eq $Value) { return 'blank' }
    if ($Value -is [string]) { return 'text' }
    if ($Value -is [byte] -or $Value -is [sbyte] -or $Value -is [int16] -or $Value -is [uint16] -or
        $Value -is [int32] -or $Value -is [uint32] -or $Value -is [int64] -or $Value -is [uint64] -or
        $Value -is [single] -or $Value -is [double] -or $Value -is [decimal]) { return 'number' }
    if ($Value -is [bool]) { return 'boolean' }
    return $Value.GetType().FullName
}

function Get-WorkbookCells($Excel, [string]$Path, [string]$SheetName, [string[]]$Addresses) {
    $workbook = $null
    $worksheet = $null
    try {
        $workbook = $Excel.Workbooks.Open($Path, 0, $true)
        $worksheet = $workbook.Worksheets.Item($SheetName)
        $record = [ordered]@{}
        foreach ($address in $Addresses) {
            $cell = $null
            $style = $null
            try {
                $cell = $worksheet.Range($address)
                $style = $cell.Style
                $value = $cell.Value2
                $record[$address] = [ordered]@{
                    value = $value
                    value_kind = Get-ValueKind $value
                    clr_type = if ($null -eq $value) { $null } else { $value.GetType().FullName }
                    formula = $cell.Formula
                    has_formula = [bool]$cell.HasFormula
                    number_format = [string]$cell.NumberFormat
                    number_format_local = [string]$cell.NumberFormatLocal
                    prefix_character = [string]$cell.PrefixCharacter
                    style_name = [string]$style.Name
                }
            }
            finally {
                if ($style) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($style) }
                if ($cell) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
            }
        }
        return $record
    }
    finally {
        if ($workbook) { $workbook.Close($false) }
        if ($worksheet) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet) }
        if ($workbook) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) }
    }
}

$hashBefore = [ordered]@{
    source = Get-Sha256 $sourcePath
    template = Get-Sha256 $templatePath
    output = Get-Sha256 $output
}
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $source = Get-WorkbookCells $excel $sourcePath 'Source' @('A2', 'B2')
    $template = Get-WorkbookCells $excel $templatePath 'Target' @('A2', 'B2')
    $actual = Get-WorkbookCells $excel $output 'Target' @('A2', 'B2')
}
finally {
    $excel.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
$hashAfter = [ordered]@{
    source = Get-Sha256 $sourcePath
    template = Get-Sha256 $templatePath
    output = Get-Sha256 $output
}

$checks = [ordered]@{
    hashes_unchanged_by_verifier = (($hashBefore | ConvertTo-Json -Compress) -ceq ($hashAfter | ConvertTo-Json -Compress))
    source_text_fixed = ($source.A2.value_kind -ceq 'text' -and $source.A2.value -ceq '100%')
    source_number_fixed = ($source.B2.value_kind -ceq 'number' -and [double]$source.B2.value -eq 42.5)
    target_text_value_and_type = ($actual.A2.value_kind -ceq 'text' -and $actual.A2.value -ceq '100%')
    target_number_value_and_type = ($actual.B2.value_kind -ceq 'number' -and [double]$actual.B2.value -eq 42.5)
    text_number_format_preserved = ($actual.A2.number_format -ceq $template.A2.number_format -and $actual.A2.number_format_local -ceq $template.A2.number_format_local)
    number_number_format_preserved = ($actual.B2.number_format -ceq $template.B2.number_format -and $actual.B2.number_format_local -ceq $template.B2.number_format_local)
    text_prefix_character_preserved = ($actual.A2.prefix_character -ceq $template.A2.prefix_character -and [string]::IsNullOrEmpty($actual.A2.prefix_character))
    number_prefix_character_preserved = ($actual.B2.prefix_character -ceq $template.B2.prefix_character)
    no_formula_substitution = (-not $actual.A2.has_formula -and -not $actual.B2.has_formula)
    no_residual_extra_character = ($actual.A2.value -ceq '100%' -and [string]::IsNullOrEmpty($actual.A2.prefix_character))
}
$passed = @($checks.Values | Where-Object { -not $_ }).Count -eq 0
$record = [ordered]@{
    schema_version = 1
    kind = 'ISSUE38_PERCENT_TEXT_WRITE_VERIFICATION'
    observed_at = [DateTime]::UtcNow.ToString('o')
    run_label = $RunLabel
    status = if ($passed) { 'PASS' } else { 'FAIL' }
    paths = [ordered]@{ source = $sourcePath; template = $templatePath; output = $output }
    sha256_before = $hashBefore
    sha256_after = $hashAfter
    source = $source
    template_before = $template
    output_after_reopen = $actual
    checks = $checks
    limits = @('Fixed Source!A2:B2 and Target!A2:B2 only', 'Text 100% and numeric 42.5 only')
}
$stream = [IO.File]::Open($evidence, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try {
    $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes(($record | ConvertTo-Json -Depth 12))
    $stream.Write($bytes, 0, $bytes.Length)
}
finally { $stream.Dispose() }
$record | ConvertTo-Json -Depth 12
if (-not $passed) { exit 2 }
