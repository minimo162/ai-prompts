[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ProbeRoot,
    [Parameter(Mandatory = $true)][string]$EvidencePath
)

$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($ProbeRoot)
$sourcePath = (Resolve-Path -LiteralPath (Join-Path $root 'source.xlsx')).Path
$templatePath = (Resolve-Path -LiteralPath (Join-Path $root 'template.xlsx')).Path
$workPath = (Resolve-Path -LiteralPath (Join-Path $root 'runtime\work.xlsx')).Path
$outputPath = (Resolve-Path -LiteralPath (Join-Path $root 'runtime\result.xlsx')).Path
$evidence = [IO.Path]::GetFullPath($EvidencePath)
foreach ($path in @($sourcePath, $templatePath, $workPath, $outputPath, $evidence)) {
    if (-not $path.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'R11 probe paths only'
    }
}
if (Test-Path -LiteralPath $evidence) { throw 'Evidence exists' }

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

function Get-Cells($Excel, [string]$Path, [string]$SheetName) {
    $workbook = $null
    $worksheet = $null
    try {
        $workbook = $Excel.Workbooks.Open($Path, 0, $true)
        $worksheet = $workbook.Worksheets.Item($SheetName)
        $record = [ordered]@{}
        foreach ($address in @('A2', 'B2')) {
            $cell = $null
            try {
                $cell = $worksheet.Range($address)
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
                }
            }
            finally {
                if ($null -ne $cell) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
            }
        }
        return $record
    }
    finally {
        if ($null -ne $workbook) { $workbook.Close($false) }
        if ($null -ne $worksheet) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet) }
        if ($null -ne $workbook) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) }
    }
}

$hashBefore = [ordered]@{
    source = Get-Sha256 $sourcePath
    template = Get-Sha256 $templatePath
    work = Get-Sha256 $workPath
    output = Get-Sha256 $outputPath
}
$excel = New-Object -ComObject Excel.Application
$excel.Visible = $false
$excel.DisplayAlerts = $false
try {
    $source = Get-Cells $excel $sourcePath 'Source'
    $template = Get-Cells $excel $templatePath 'Target'
    $work = Get-Cells $excel $workPath 'Target'
    $output = Get-Cells $excel $outputPath 'Target'
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
    work = Get-Sha256 $workPath
    output = Get-Sha256 $outputPath
}

$checks = [ordered]@{
    verifier_is_read_only = (($hashBefore | ConvertTo-Json -Compress) -ceq ($hashAfter | ConvertTo-Json -Compress))
    source_fixture_sha_fixed = ($hashBefore.source -ceq 'dda07aac129a7f2f55bbd40067eda426b4b8f4f997254e7e9f69059803ac5874')
    template_fixture_sha_fixed = ($hashBefore.template -ceq '13855dcaf2fa8a9dd8d282197fd74c2f138d9ebc5552debbedbc5886296d2bde')
    work_copy_stayed_original = ($hashBefore.work -ceq $hashBefore.template)
    source_text_fixed = ($source.A2.value_kind -ceq 'text' -and $source.A2.value -ceq '100%')
    source_number_fixed = ($source.B2.value_kind -ceq 'number' -and [double]$source.B2.value -eq 42.5)
    output_text_value_and_type = ($output.A2.value_kind -ceq 'text' -and $output.A2.clr_type -ceq 'System.String' -and $output.A2.value -ceq '100%')
    output_number_value_and_type = ($output.B2.value_kind -ceq 'number' -and [double]$output.B2.value -eq 42.5)
    output_text_format_preserved = ($output.A2.number_format -ceq $template.A2.number_format -and $output.A2.number_format_local -ceq $template.A2.number_format_local)
    output_number_format_preserved = ($output.B2.number_format -ceq $template.B2.number_format -and $output.B2.number_format_local -ceq $template.B2.number_format_local)
    output_prefix_empty = ([string]::IsNullOrEmpty($output.A2.prefix_character) -and $output.A2.prefix_character -ceq $template.A2.prefix_character)
    no_formula_substitution = (-not $output.A2.has_formula -and -not $output.B2.has_formula)
    source_workbook_not_modified = ($hashBefore.source -ceq $hashAfter.source)
}
$passed = @($checks.Values | Where-Object { -not $_ }).Count -eq 0
$record = [ordered]@{
    schema_version = 1
    kind = 'ISSUE38_EX03_R11_MINIMAL_POWERSHELL_SYNTHETIC_VERIFICATION'
    observed_at = [DateTime]::UtcNow.ToString('o')
    status = if ($passed) { 'PASS_EXTERNAL_ARTIFACT_CHECK_FOR_DEDICATED_PAD_PROBE' } else { 'FAIL' }
    paths = [ordered]@{
        source = $sourcePath
        template = $templatePath
        work = $workPath
        output = $outputPath
    }
    sha256_before = $hashBefore
    sha256_after = $hashAfter
    source = $source
    template = $template
    work = $work
    output = $output
    checks = $checks
    limits = @(
        'This verifies the dedicated synthetic output artifact, not EX03 integrated acceptance.',
        'The fixed scope is text 100% and number 42.5 at Source/Target A2:B2 only.',
        'PAD terminal state and PAD variables require separate UI evidence.'
    )
}
$stream = [IO.File]::Open($evidence, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try {
    $bytes = (New-Object Text.UTF8Encoding($false)).GetBytes(($record | ConvertTo-Json -Depth 12))
    $stream.Write($bytes, 0, $bytes.Length)
}
finally { $stream.Dispose() }
$record | ConvertTo-Json -Depth 12
if (-not $passed) { exit 2 }
