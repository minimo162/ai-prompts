[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$InvocationPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$excel = $null
$workbook = $null
$result = $null
$mode = 'UNREAD'

try {
    $invocationFullPath = [IO.Path]::GetFullPath($InvocationPath)
    if (-not (Test-Path -LiteralPath $invocationFullPath -PathType Leaf)) {
        throw 'INVOCATION_NOT_FOUND'
    }
    $invocation = Get-Content -LiteralPath $invocationFullPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ([int]$invocation.schema_version -ne 1) { throw 'INVOCATION_SCHEMA' }

    $targetPath = [IO.Path]::GetFullPath([string]$invocation.target_workbook)
    $jsonRoot = [IO.Path]::GetFullPath([string]$invocation.json_root)
    if (-not (Test-Path -LiteralPath $targetPath -PathType Leaf)) { throw 'TARGET_FILE_NOT_FOUND' }
    if (-not (Test-Path -LiteralPath $jsonRoot -PathType Container)) { throw 'JSON_ROOT_NOT_FOUND' }

    $mappings = @($invocation.text_writes)
    if ($mappings.Count -ne 7) { throw ('TEXT_MAPPING_COUNT_' + $mappings.Count) }
    $seenIndexes = @{}
    foreach ($mapping in $mappings) {
        $sourceIndex = [int]$mapping.source_index
        if ($sourceIndex -lt 1 -or $sourceIndex -gt 7) { throw ('SOURCE_INDEX_' + $sourceIndex) }
        if ($seenIndexes.ContainsKey($sourceIndex)) { throw ('SOURCE_INDEX_DUPLICATE_' + $sourceIndex) }
        $seenIndexes[$sourceIndex] = $true
        if ([string]::IsNullOrWhiteSpace([string]$mapping.source_label)) { throw 'SOURCE_LABEL_EMPTY' }
        if ([string]::IsNullOrWhiteSpace([string]$mapping.sheet)) { throw 'TARGET_SHEET_EMPTY' }
        if ([string]::IsNullOrWhiteSpace([string]$mapping.cell)) { throw 'TARGET_CELL_EMPTY' }
    }
    for ($index = 1; $index -le 7; $index++) {
        if (-not $seenIndexes.ContainsKey($index)) { throw ('SOURCE_INDEX_MISSING_' + $index) }
    }

    $payloads = @(
        (Get-Content -LiteralPath (Join-Path $jsonRoot 'source-1.json') -Raw -Encoding UTF8 | ConvertFrom-Json),
        (Get-Content -LiteralPath (Join-Path $jsonRoot 'source-2.json') -Raw -Encoding UTF8 | ConvertFrom-Json),
        (Get-Content -LiteralPath (Join-Path $jsonRoot 'source-3.json') -Raw -Encoding UTF8 | ConvertFrom-Json),
        (Get-Content -LiteralPath (Join-Path $jsonRoot 'source-4.json') -Raw -Encoding UTF8 | ConvertFrom-Json),
        (Get-Content -LiteralPath (Join-Path $jsonRoot 'source-5.json') -Raw -Encoding UTF8 | ConvertFrom-Json),
        (Get-Content -LiteralPath (Join-Path $jsonRoot 'source-6.json') -Raw -Encoding UTF8 | ConvertFrom-Json),
        (Get-Content -LiteralPath (Join-Path $jsonRoot 'source-7.json') -Raw -Encoding UTF8 | ConvertFrom-Json)
    )
    $modePayload = Get-Content -LiteralPath (Join-Path $jsonRoot 'mode.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $mode = [string]$modePayload.probe
    if ($mode -cne 'NORMAL' -and $mode -cne 'INJECT_AFTER_FORMAT_CHANGE') {
        throw 'MODE_NOT_ALLOWED'
    }
    for ($index = 0; $index -lt 7; $index++) {
        if ($payloads[$index].probe -isnot [string]) { throw ('TEXT_PAYLOAD_TYPE_' + ($index + 1)) }
    }

    $writes = @()
    foreach ($mapping in $mappings) {
        $sourceIndex = [int]$mapping.source_index
        $writes += ,@(
            [string]$mapping.source_label,
            [string]$mapping.sheet,
            [string]$mapping.cell,
            [string]$payloads[$sourceIndex - 1].probe
        )
    }

    $excel = [Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application')
    $matches = @()
    for ($index = 1; $index -le $excel.Workbooks.Count; $index++) {
        $candidate = $excel.Workbooks.Item($index)
        if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath) {
            $matches += $candidate
        }
        else {
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($candidate)
        }
    }
    if ($matches.Count -ne 1) {
        foreach ($match in $matches) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($match) }
        throw ('TARGET_WORKBOOK_COUNT_' + $matches.Count)
    }
    $workbook = $matches[0]

    $writesCompleted = 0
    foreach ($write in $writes) {
        $worksheet = $null
        $cell = $null
        try {
            $sheetName = [string]$write[1]
            $cellAddress = [string]$write[2]
            $worksheet = $workbook.Worksheets.Item($sheetName)
            $cell = $worksheet.Range($cellAddress)
            if ([bool]$cell.HasFormula) { throw ('FORMULA_TARGET_' + $sheetName + '!' + $cellAddress) }
            $beforeValue = $cell.Value2
            $beforeType = if ($null -eq $beforeValue) { 'null' } else { $beforeValue.GetType().FullName }
            $beforeFormat = [string]$cell.NumberFormat
            $beforePrefix = [string]$cell.PrefixCharacter
            $beforeFormula = [bool]$cell.HasFormula
            $writeError = $null
            try {
                $cell.NumberFormat = '@'
                if ($mode -ceq 'INJECT_AFTER_FORMAT_CHANGE' -and $writesCompleted -eq 0) {
                    throw 'ISSUE38_INTENTIONAL_AFTER_FORMAT_CHANGE'
                }
                $cell.Value2 = [string]$write[3]
            }
            catch {
                $writeError = $_
            }
            finally {
                $cell.NumberFormat = $beforeFormat
            }

            if ($null -ne $writeError) {
                if ($mode -ceq 'INJECT_AFTER_FORMAT_CHANGE' -and $writeError.Exception.Message -ceq 'ISSUE38_INTENTIONAL_AFTER_FORMAT_CHANGE') {
                    $afterValue = $cell.Value2
                    $afterType = if ($null -eq $afterValue) { 'null' } else { $afterValue.GetType().FullName }
                    if ([string]$cell.NumberFormat -cne $beforeFormat) { throw 'NEGATIVE_FORMAT_NOT_RESTORED' }
                    if ($afterType -cne $beforeType -or [string]$afterValue -cne [string]$beforeValue) { throw 'NEGATIVE_VALUE_CHANGED' }
                    if ([string]$cell.PrefixCharacter -cne $beforePrefix) { throw 'NEGATIVE_PREFIX_CHANGED' }
                    if ([bool]$cell.HasFormula -ne $beforeFormula) { throw 'NEGATIVE_FORMULA_CHANGED' }
                    $result = [ordered]@{
                        status = 'EXPECTED_ERROR'
                        mode = 'INJECT_AFTER_FORMAT_CHANGE'
                        format_restored = $true
                        value_unchanged = $true
                    }
                    break
                }
                throw $writeError
            }

            if ($cell.Value2 -isnot [string] -or [string]$cell.Value2 -cne [string]$write[3]) {
                throw ('TEXT_VALUE_TYPE_' + $sheetName + '!' + $cellAddress)
            }
            if ([string]$cell.NumberFormat -cne $beforeFormat) { throw ('FORMAT_NOT_RESTORED_' + $sheetName + '!' + $cellAddress) }
            if ([string]$cell.PrefixCharacter -cne '') { throw ('PREFIX_CHANGED_' + $sheetName + '!' + $cellAddress) }
            if ([bool]$cell.HasFormula) { throw ('FORMULA_AFTER_WRITE_' + $sheetName + '!' + $cellAddress) }
            $writesCompleted++
        }
        finally {
            if ($null -ne $cell) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
            if ($null -ne $worksheet) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet) }
        }
    }

    if ($mode -ceq 'NORMAL') {
        if ($writesCompleted -ne 7) { throw ('NORMAL_WRITE_COUNT_' + $writesCompleted) }
        $result = [ordered]@{
            status = 'OK'
            mode = 'NORMAL'
            text_writes = 7
            formats_restored = $true
        }
    }
    elseif ($null -eq $result -or $result.status -cne 'EXPECTED_ERROR') {
        throw 'EXPECTED_ERROR_NOT_OBSERVED'
    }
}
catch {
    $result = [ordered]@{
        status = 'ERROR'
        mode = $mode
        error_code = [string]$_.Exception.Message
    }
}
finally {
    if ($null -ne $workbook) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) }
    if ($null -ne $excel) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }
}

Write-Output -NoEnumerate ([string]($result | ConvertTo-Json -Compress))
