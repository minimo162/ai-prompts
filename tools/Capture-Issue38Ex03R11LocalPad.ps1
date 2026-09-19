[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('Source', 'Synthetic')][string]$Mode,
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][int]$ObservedActionCount,
    [Parameter(Mandatory = $true)][int]$ObservedVariableCount,
    [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$rootPath = [IO.Path]::GetFullPath($Root)
$evidenceDirectory = Join-Path $rootPath 'catalog/acceptance/issue38/probes/ex03-r11-minimal-powershell'
$candidateName = if ($Mode -ceq 'Source') { 'independent-candidate.robin' } else { 'synthetic-candidate.robin' }
$recopyName = if ($Mode -ceq 'Source') { 'independent-pad-recopy.robin' } else { 'synthetic-pad-recopy-before-run.robin' }
$recordName = if ($Mode -ceq 'Source') { 'independent-pad-capture.json' } else { 'synthetic-pad-capture.json' }
$candidatePath = Join-Path $evidenceDirectory $candidateName
$recopyPath = Join-Path $evidenceDirectory $recopyName
$recordPath = Join-Path $evidenceDirectory $recordName

if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) { throw 'Candidate missing' }
if (Test-Path -LiteralPath $recordPath) { throw 'Refusing to overwrite PAD capture record' }
$utf8 = [Text.UTF8Encoding]::new($false)
$candidate = [IO.File]::ReadAllText($candidatePath, $utf8)
$recopy = Get-Clipboard -Raw
if ([string]::IsNullOrEmpty($recopy)) { throw 'PAD re-copy clipboard is empty' }
$normalizedCandidate = $candidate.Replace("`r`n", "`n").TrimEnd("`r", "`n")
$normalizedRecopy = $recopy.Replace("`r`n", "`n").TrimEnd("`r", "`n")
if ($normalizedCandidate -cne $normalizedRecopy) { throw 'PAD re-copy differs outside newline serialization' }

if ($Mode -ceq 'Source') {
    $required = @(
        'excel-r8-example', 'work-copy.xlsx',
        '教材出力一', '教材出力二',
        "[IO.Path]::GetFullPath([string]`$candidate.FullName) -ieq `$targetPath",
        "PrefixCharacter -cne",
        "finally { `$cell.NumberFormat = `$beforeNumberFormat }"
    )
    $forbidden = @(
        'fixtures\EX03\入力い.xlsx', 'fixtures\EX03\入力ろ.xlsx',
        'runs\EX03-attempt1\work.xlsx', 'runs\EX03-attempt1\照合結果.xlsx',
        "[string]::Equals(", "[StringComparison]::OrdinalIgnoreCase", "[string]::IsNullOrEmpty("
    )
}
else {
    $required = @(
        'ex03-r11-minimal-powershell', 'source.xlsx', 'runtime', 'work.xlsx', 'result.xlsx',
        "SET ProbeState TO `$'''R11_MINIMAL_FINISHED'''",
        "[IO.Path]::GetFullPath([string]`$candidate.FullName) -ieq `$targetPath",
        "finally { `$cell.NumberFormat = `$beforeNumberFormat }"
    )
    $forbidden = @("[string]::Equals(", "[StringComparison]::OrdinalIgnoreCase", "[string]::IsNullOrEmpty(")
}
$missing = @($required | Where-Object { -not $recopy.Contains($_) })
$presentForbidden = @($forbidden | Where-Object { $recopy.Contains($_) })
if ($missing.Count -ne 0) { throw ('Required fragment missing: ' + ($missing -join ', ')) }
if ($presentForbidden.Count -ne 0) { throw ('Forbidden fragment present: ' + ($presentForbidden -join ', ')) }

function Get-Sha256Text([string]$Value) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($utf8.GetBytes($Value)))).Replace('-', '').ToLowerInvariant() }
    finally { $algorithm.Dispose() }
}

[IO.File]::WriteAllText($recopyPath, $recopy, $utf8)
$record = [ordered]@{
    schema_version = 1
    capture_id = 'EX03-R11-' + $Mode.ToUpperInvariant() + '-PAD-RECOPY'
    captured_utc = [DateTime]::UtcNow.ToString('o')
    environment = [ordered]@{
        pad_file_version = '2.71.115.26224'
        language = 'ja-JP'
        power_fx = 'OFF'
        flow_name = $FlowName
        subflow = 'Main'
    }
    scope = [ordered]@{
        mode = $Mode
        executed_before_capture = $false
        copilot_send = $false
        integrated_ex03_run = $false
        github_write = $false
    }
    observation = [ordered]@{
        initial_actions = 0
        paste_invocations = 1
        selected_actions_after_paste = $ObservedActionCount
        actions_after_paste = $ObservedActionCount
        variables_after_paste = $ObservedVariableCount
        save_invocations = 1
        recopy_invocations = 1
        designer_status_after_save = 'READY'
        designer_error_observed = $false
    }
    comparison = [ordered]@{
        candidate_path = [IO.Path]::GetRelativePath($rootPath, $candidatePath).Replace('\', '/')
        candidate_sha256 = Get-Sha256Text $candidate
        candidate_chars = $candidate.Length
        recopy_path = [IO.Path]::GetRelativePath($rootPath, $recopyPath).Replace('\', '/')
        recopy_sha256 = Get-Sha256Text $recopy
        recopy_chars = $recopy.Length
        exact_bytes = $candidate -ceq $recopy
        lf_normalized_exact = $true
        candidate_crlf_count = [regex]::Matches($candidate, "`r`n").Count
        candidate_lf_only_count = [regex]::Matches($candidate, "(?<!`r)`n").Count
        recopy_crlf_count = [regex]::Matches($recopy, "`r`n").Count
        recopy_lf_only_count = [regex]::Matches($recopy, "(?<!`r)`n").Count
        required_fragments_present = $true
        forbidden_fragments_absent = $true
    }
    result = 'PASS_PAD_DESIGNER_SAVE_RECOPY_NO_EXECUTION'
}
[IO.File]::WriteAllText($recordPath, (($record | ConvertTo-Json -Depth 8) + "`n"), $utf8)
$record | ConvertTo-Json -Depth 8
