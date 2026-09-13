[CmdletBinding()]
param([string]$Root = (Split-Path -Parent $PSScriptRoot))

$ErrorActionPreference = 'Stop'

function Read-Bytes([string]$RelativePath) {
    $path = Join-Path $Root $RelativePath
    if (-not (Test-Path -LiteralPath $path)) { throw "T10_STRICT: missing $RelativePath" }
    return [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $path))
}

function Read-LinesWithoutEndings([string]$RelativePath) {
    $path = Join-Path $Root $RelativePath
    $text = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $path), [Text.Encoding]::UTF8)
    $text = $text -replace "`r`n", "`n"
    $lines = $text -split "`n"
    if ($lines.Count -gt 0 -and $lines[-1] -eq '') { $lines = $lines[0..($lines.Count - 2)] }
    return $lines
}

function Get-FileSummary([string]$RelativePath, [byte[]]$Bytes) {
    [ordered]@{
        path = $RelativePath
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Root $RelativePath)).Hash.ToLowerInvariant()
        bytes = $Bytes.Length
        crlf_count = (@($Bytes | Where-Object { $_ -eq 13 }).Count)
        lf_count = (@($Bytes | Where-Object { $_ -eq 10 }).Count)
        final_lf = ($Bytes.Length -gt 0 -and $Bytes[-1] -eq 10)
    }
}

function Get-ChangedLines([string[]]$Left, [string[]]$Right) {
    $changed = @()
    $count = [Math]::Max($Left.Count, $Right.Count)
    for ($i = 0; $i -lt $count; $i++) {
        $a = if ($i -lt $Left.Count) { $Left[$i] } else { $null }
        $b = if ($i -lt $Right.Count) { $Right[$i] } else { $null }
        if (-not [string]::Equals($a, $b, [StringComparison]::Ordinal)) { $changed += ($i + 1) }
    }
    return $changed
}

$sourcePath = 'catalog/generated/office-three-apps/generated.robin'
$generationPath = 'catalog/evidence/t10-copilot-live-generation-20260913.robin'
$recopyPath = 'catalog/evidence/t10-copilot-live-generation-20260913-pad-recopy-after-run2.robin'
$sourceBytes = Read-Bytes $sourcePath
$generationBytes = Read-Bytes $generationPath
$recopyBytes = Read-Bytes $recopyPath
$sourceLines = Read-LinesWithoutEndings $sourcePath
$generationLines = Read-LinesWithoutEndings $generationPath
$recopyLines = Read-LinesWithoutEndings $recopyPath
$sourceToGeneration = @(Get-ChangedLines $sourceLines $generationLines)
$sourceToRecopy = @(Get-ChangedLines $sourceLines $recopyLines)
$generationToRecopy = @(Get-ChangedLines $generationLines $recopyLines)
$allowed = @(2, 4)
$outsideSourceGeneration = @($sourceToGeneration | Where-Object { $_ -notin $allowed })
$outsideSourceRecopy = @($sourceToRecopy | Where-Object { $_ -notin $allowed })

$result = [ordered]@{
    schema_version = 1
    purpose = 'Read-only T10 functional/change-scope/byte-preservation regression check; no normalization or source repair.'
    files = @(
        (Get-FileSummary $sourcePath $sourceBytes),
        (Get-FileSummary $generationPath $generationBytes),
        (Get-FileSummary $recopyPath $recopyBytes)
    )
    comparisons = [ordered]@{
        source_to_generation_normalized_content = [ordered]@{
            changed_lines = $sourceToGeneration
            allowed_change_lines = $allowed
            outside_allowed_change_lines = $outsideSourceGeneration
            status = if ($outsideSourceGeneration.Count -eq 0 -and (@($sourceToGeneration) -join ',') -ceq '2,4') { 'PROVEN_CONTENT_SCOPE_ONLY' } else { 'FAIL' }
        }
        source_to_recopy_normalized_content = [ordered]@{
            changed_lines = $sourceToRecopy
            outside_allowed_change_lines = $outsideSourceRecopy
            status = if ($outsideSourceRecopy.Count -eq 0 -and (@($sourceToRecopy) -join ',') -ceq '2,4') { 'PROVEN_CONTENT_SCOPE_ONLY' } else { 'FAIL' }
        }
        generation_to_recopy_normalized_content = [ordered]@{
            changed_lines = $generationToRecopy
            status = if ($generationToRecopy.Count -eq 0) { 'PROVEN_CONTENT_EQUAL_AFTER_CRLF_NORMALIZATION' } else { 'FAIL' }
        }
    }
    strict_byte_preservation = [ordered]@{
        source_to_generation_raw_bytes_equal = [Convert]::ToBase64String($sourceBytes) -ceq [Convert]::ToBase64String($generationBytes)
        source_to_recopy_raw_bytes_equal = [Convert]::ToBase64String($sourceBytes) -ceq [Convert]::ToBase64String($recopyBytes)
        generation_to_recopy_raw_bytes_equal = [Convert]::ToBase64String($generationBytes) -ceq [Convert]::ToBase64String($recopyBytes)
        status = 'NOT_PROVEN'
        reason = 'Source CRLF/no-final-LF differs from generated LF/final-LF; normalized content scope is separate evidence and cannot prove raw byte retention.'
    }
    regression_assertions = [ordered]@{
        source_crlf_15_no_final_lf = ((@($sourceBytes | Where-Object { $_ -eq 13 }).Count -eq 15) -and (@($sourceBytes | Where-Object { $_ -eq 10 }).Count -eq 15) -and -not ($sourceBytes[-1] -eq 10))
        generation_lf_16_final_lf = ((@($generationBytes | Where-Object { $_ -eq 13 }).Count -eq 0) -and (@($generationBytes | Where-Object { $_ -eq 10 }).Count -eq 16) -and ($generationBytes[-1] -eq 10))
        recopy_crlf_16_final_lf = ((@($recopyBytes | Where-Object { $_ -eq 13 }).Count -eq 16) -and (@($recopyBytes | Where-Object { $_ -eq 10 }).Count -eq 16) -and ($recopyBytes[-1] -eq 10))
        source_generation_outside_allowed_zero = ($outsideSourceGeneration.Count -eq 0)
        generation_recopy_normalized_equal = ($generationToRecopy.Count -eq 0)
        strict_raw_source_generation_not_equal = -not ([Convert]::ToBase64String($sourceBytes) -ceq [Convert]::ToBase64String($generationBytes))
    }
}

$allAssertions = [bool]($result.regression_assertions.source_crlf_15_no_final_lf -and
    $result.regression_assertions.generation_lf_16_final_lf -and
    $result.regression_assertions.recopy_crlf_16_final_lf -and
    $result.regression_assertions.source_generation_outside_allowed_zero -and
    $result.regression_assertions.generation_recopy_normalized_equal -and
    $result.regression_assertions.strict_raw_source_generation_not_equal)
$result.status = if ($allAssertions) { 'PASS_REGRESSION_WITH_STRICT_NOT_PROVEN' } else { 'FAIL' }
$result | ConvertTo-Json -Depth 12
if ($result.status -eq 'FAIL') { exit 1 }
