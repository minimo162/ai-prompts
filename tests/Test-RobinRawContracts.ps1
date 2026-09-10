[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'

function Read-Utf8Lines([string]$RelativePath) {
    $path = Join-Path $Root $RelativePath
    if (-not (Test-Path -LiteralPath $path)) { throw "RAW_CONTRACT: Missing $RelativePath" }
    return [IO.File]::ReadAllLines((Resolve-Path -LiteralPath $path), [Text.Encoding]::UTF8)
}

function Get-FileSummary([string]$RelativePath) {
    $path = Join-Path $Root $RelativePath
    $text = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $path), [Text.Encoding]::UTF8)
    [ordered]@{
        path = $RelativePath
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
        utf16_code_units = $text.Length
        utf8_bytes = [Text.Encoding]::UTF8.GetByteCount($text)
        line_count = ([regex]::Matches($text, "`n")).Count + 1
        single_quote_count = ([regex]::Matches($text, "'")).Count
        backslash_count = ([regex]::Matches($text, '\\')).Count
        underscore_count = ([regex]::Matches($text, '_')).Count
        arrow_count = ([regex]::Matches($text, '=>')).Count
        nbsp_count = ([regex]::Matches($text, [char]0x00a0)).Count
    }
}

function Get-LineDiff([string[]]$A, [string[]]$B) {
    $rows = @()
    $count = [Math]::Max($A.Count, $B.Count)
    for ($i = 0; $i -lt $count; $i++) {
        $left = if ($i -lt $A.Count) { $A[$i] } else { $null }
        $right = if ($i -lt $B.Count) { $B[$i] } else { $null }
        if (-not [string]::Equals($left, $right, [StringComparison]::Ordinal)) {
            $rows += [ordered]@{
                line = $i + 1
                left = $left
                right = $right
                left_utf16 = if ($null -eq $left) { $null } else { $left.Length }
                right_utf16 = if ($null -eq $right) { $null } else { $right.Length }
            }
        }
    }
    return $rows
}

$t04SourcePath = 'catalog/flows/excel-t04-filter-to-workbook/roundtrip.robin'
$t04EarlyPath = 'catalog/generated/normal-chat-t04-20260910-current-v4/robin.txt'
$t04FinalPath = 'catalog/generated/normal-chat-t04-20260910-final-v5/robin.txt'
$t10SourcePath = 'catalog/generated/office-three-apps/generated.robin'
$t10GeneratedPath = 'catalog/generated/normal-chat-t10-20260910-final-v8/robin.txt'
$t10RecopyPath = 'catalog/evidence/normal-chat-final-pad-20260910/t10-recopy.txt'

$t04Source = Read-Utf8Lines $t04SourcePath
$t04Early = Read-Utf8Lines $t04EarlyPath
$t04Final = Read-Utf8Lines $t04FinalPath
$t10Source = Read-Utf8Lines $t10SourcePath
$t10Generated = Read-Utf8Lines $t10GeneratedPath
$t10Recopy = Read-Utf8Lines $t10RecopyPath

$result = [ordered]@{
    schema_version = 1
    captured_at = [DateTime]::UtcNow.ToString('o')
    purpose = 'Read-only raw Robin provenance comparison; no normalization or code repair.'
    files = @(
        (Get-FileSummary $t04SourcePath),
        (Get-FileSummary $t04EarlyPath),
        (Get-FileSummary $t04FinalPath),
        (Get-FileSummary $t10SourcePath),
        (Get-FileSummary $t10GeneratedPath),
        (Get-FileSummary $t10RecopyPath)
    )
    comparisons = [ordered]@{
        t04_source_to_early = [ordered]@{
            differing_lines = @(Get-LineDiff $t04Source $t04Early)
            interpretation = 'Early success kept the measured FilterParameters literal; only requested output-path substitutions differ.'
        }
        t04_source_to_final = [ordered]@{
            differing_lines = @(Get-LineDiff $t04Source $t04Final)
            interpretation = 'The final-v5 generated response changed the FilterParameters empty-literal quote count during Copilot generation; PAD paste was not confirmed. Output-path substitutions are a separate requested-path change.'
        }
        t10_source_to_generated = [ordered]@{
            differing_lines = @(Get-LineDiff $t10Source $t10Generated)
            interpretation = 'Lines 2 and 4 are the requested changes. Lines 9 and 15 are outside the change scope and were mutated in the generated response (extra backslashes and escaped underscore).'
        }
        t10_generated_to_recopy = [ordered]@{
            differing_lines = @(Get-LineDiff $t10Generated $t10Recopy)
            interpretation = 'PAD recopy changed only the rendering of the same two path lines by removing the backslash before underscore; this is downstream of generation and is not byte-identity proof.'
        }
    }
    assertions = [ordered]@{
        t04_early_filter_line_matches_source = [string]::Equals($t04Source[2], $t04Early[2], [StringComparison]::Ordinal)
        t04_final_filter_line_differs_from_source = -not [string]::Equals($t04Source[2], $t04Final[2], [StringComparison]::Ordinal)
        t10_expected_changed_lines = ((@((Get-LineDiff $t10Source $t10Generated).line) -join ',') -ceq '2,4,9,15')
        t10_recopy_only_path_lines_differ = ((@((Get-LineDiff $t10Generated $t10Recopy).line) -join ',') -ceq '9,15')
    }
}

$result | ConvertTo-Json -Depth 12
