[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$FlowName = '無題 (6)',
    [int]$ObservedActionCount = 110,
    [int]$ObservedVariableCount = 45
)

$ErrorActionPreference = 'Stop'
$rootPath = [IO.Path]::GetFullPath($Root)
$evidenceDirectory = Join-Path $rootPath 'catalog/acceptance/issue38/probes/ex03-r8-independent-source'
$candidatePath = Join-Path $evidenceDirectory 'candidate-full.robin'
$recopyPath = Join-Path $evidenceDirectory 'pad-recopy-full.robin'
$recordPath = Join-Path $evidenceDirectory 'pad-capture.json'

if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) {
    throw "Candidate source is missing: $candidatePath"
}
if (Test-Path -LiteralPath $recordPath) {
    throw 'Refusing to overwrite existing PAD capture record.'
}

$utf8 = [Text.UTF8Encoding]::new($false)
$candidate = [IO.File]::ReadAllText($candidatePath, $utf8)
$recopy = Get-Clipboard -Raw
if ([string]::IsNullOrEmpty($recopy)) {
    throw 'PAD re-copy clipboard is empty.'
}

$normalizedCandidate = $candidate.Replace("`r`n", "`n").TrimEnd("`r", "`n")
$normalizedRecopy = $recopy.Replace("`r`n", "`n").TrimEnd("`r", "`n")
if ($normalizedCandidate -cne $normalizedRecopy) {
    throw 'PAD re-copy differs from the independent candidate outside line-ending normalization.'
}

$forbidden = @(
    'fixtures\\EX03\\入力い.xlsx',
    'fixtures\\EX03\\入力ろ.xlsx',
    'runs\\EX03-attempt1\\work.xlsx',
    'runs\\EX03-attempt1\\照合結果.xlsx',
    '受取明細', '追加項目', '集計先', '追記先'
)
$leaks = @($forbidden | Where-Object { $recopy.Contains($_) })
if ($leaks.Count -ne 0) {
    throw ('Fixed EX03 identifiers leaked into PAD re-copy: ' + ($leaks -join ', '))
}

$requiredExample = @(
    'catalog\\teaching\\excel-r8-example\\source-one.xlsx',
    'catalog\\teaching\\excel-r8-example\\source-two.xlsx',
    'catalog\\teaching\\excel-r8-example\\work-copy.xlsx',
    'catalog\\teaching\\excel-r8-example\\example-result.xlsx',
    '教材入力一', '教材入力二', '教材出力一', '教材出力二'
)
$missingExample = @($requiredExample | Where-Object { -not $recopy.Contains($_) })
if ($missingExample.Count -ne 0) {
    throw ('Independent example identifiers missing from PAD re-copy: ' + ($missingExample -join ', '))
}

function Get-Sha256Text([string]$Value) {
    $bytes = $utf8.GetBytes($Value)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($algorithm.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $algorithm.Dispose()
    }
}

if (Test-Path -LiteralPath $recopyPath) {
    $existing = [IO.File]::ReadAllText($recopyPath, $utf8)
    if ($existing -cne $recopy) {
        throw 'Existing PAD re-copy file differs; refusing overwrite.'
    }
}
else {
    [IO.File]::WriteAllText($recopyPath, $recopy, $utf8)
}

$record = [ordered]@{
    schema_version = 1
    capture_id = 'EX03-R8-INDEPENDENT-SOURCE'
    captured_utc = [DateTime]::UtcNow.ToString('o')
    environment = [ordered]@{
        pad_file_version = '2.71.115.26224'
        language = 'ja-JP'
        power_fx = 'OFF'
        flow_name = $FlowName
        subflow = 'Main'
    }
    scope = [ordered]@{
        purpose = 'Dedicated PAD Designer paste, save, and re-copy of the independent r8 teaching example'
        executed = $false
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
        candidate_path = 'catalog/acceptance/issue38/probes/ex03-r8-independent-source/candidate-full.robin'
        candidate_sha256 = Get-Sha256Text $candidate
        candidate_chars = $candidate.Length
        recopy_path = 'catalog/acceptance/issue38/probes/ex03-r8-independent-source/pad-recopy-full.robin'
        recopy_sha256 = Get-Sha256Text $recopy
        recopy_chars = $recopy.Length
        exact_bytes = $candidate -ceq $recopy
        lf_normalized_exact = $true
        candidate_crlf_count = [regex]::Matches($candidate, "`r`n").Count
        candidate_lf_only_count = [regex]::Matches($candidate, "(?<!`r)`n").Count
        recopy_crlf_count = [regex]::Matches($recopy, "`r`n").Count
        recopy_lf_only_count = [regex]::Matches($recopy, "(?<!`r)`n").Count
        fixed_ex03_identifiers_absent = $true
        independent_example_identifiers_present = $true
    }
    result = 'PASS_PAD_DESIGNER_SAVE_RECOPY_INDEPENDENT_SOURCE_NO_EXECUTION'
}

[IO.File]::WriteAllText(
    $recordPath,
    (($record | ConvertTo-Json -Depth 8) + "`n"),
    $utf8
)

$record | ConvertTo-Json -Depth 8
