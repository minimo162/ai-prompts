[CmdletBinding()]
param(
    [string]$Root = (Split-Path -Parent $PSScriptRoot),
    [string]$FlowName = '無題 (5)',
    [int]$ObservedActionCount = 110,
    [int]$ObservedVariableCount = 45
)

$ErrorActionPreference = 'Stop'
$rootPath = [IO.Path]::GetFullPath($Root)
$evidenceDirectory = Join-Path $rootPath 'catalog/acceptance/issue38/probes/ex03-r7-robin-source'
$sourcePath = Join-Path $evidenceDirectory 'candidate-full.robin'
$recopyPath = Join-Path $evidenceDirectory 'pad-recopy-full.robin'
$recordPath = Join-Path $evidenceDirectory 'pad-capture.json'

if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
    throw "Candidate source is missing: $sourcePath"
}
if (Test-Path -LiteralPath $recordPath) {
    throw 'Refusing to overwrite existing PAD capture record.'
}

$utf8 = [Text.UTF8Encoding]::new($false)
$source = [IO.File]::ReadAllText($sourcePath, $utf8)
$recopy = Get-Clipboard -Raw
if ([string]::IsNullOrEmpty($recopy)) {
    throw 'PAD re-copy clipboard is empty.'
}

$normalizedSource = $source.Replace("`r`n", "`n").TrimEnd("`r", "`n")
$normalizedRecopy = $recopy.Replace("`r`n", "`n").TrimEnd("`r", "`n")
if ($normalizedSource -cne $normalizedRecopy) {
    throw 'PAD re-copy differs from the candidate outside permitted line-ending normalization.'
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
    $existingRecopy = [IO.File]::ReadAllText($recopyPath, $utf8)
    if ($existingRecopy -cne $recopy) {
        throw 'Existing PAD re-copy file does not match the current clipboard; refusing overwrite.'
    }
}
else {
    [IO.File]::WriteAllText($recopyPath, $recopy, $utf8)
}

$record = [ordered]@{
    schema_version = 1
    capture_id = 'EX03-R7-ROBIN-SOURCE'
    captured_utc = [DateTime]::UtcNow.ToString('o')
    environment = [ordered]@{
        pad_file_version = '2.71.115.26224'
        language = 'ja-JP'
        power_fx = 'OFF'
        flow_name = $FlowName
        subflow = 'Main'
    }
    scope = [ordered]@{
        purpose = 'Dedicated PAD Designer paste, save, and re-copy of the exact r6 integrated Robin source'
        executed = $false
        copilot_send = $false
        integrated_ex03_run = $false
        github_write = $false
    }
    observation = [ordered]@{
        initial_actions = 0
        browser_session_clipboard_paste_actions_after = 0
        native_clipboard_paste_invocations = 1
        selected_actions_after_paste = $ObservedActionCount
        actions_after_paste = $ObservedActionCount
        variables_after_paste = $ObservedVariableCount
        save_invocations = 1
        recopy_invocations = 1
        designer_status_after_save = 'READY'
        designer_error_observed = $false
    }
    comparison = [ordered]@{
        candidate_path = 'catalog/acceptance/issue38/probes/ex03-r7-robin-source/candidate-full.robin'
        candidate_sha256 = Get-Sha256Text $source
        candidate_chars = $source.Length
        recopy_path = 'catalog/acceptance/issue38/probes/ex03-r7-robin-source/pad-recopy-full.robin'
        recopy_sha256 = Get-Sha256Text $recopy
        recopy_chars = $recopy.Length
        exact_bytes = $source -ceq $recopy
        lf_normalized_exact = $true
        candidate_crlf_count = [regex]::Matches($source, "`r`n").Count
        candidate_lf_only_count = [regex]::Matches($source, "(?<!`r)`n").Count
        recopy_crlf_count = [regex]::Matches($recopy, "`r`n").Count
        recopy_lf_only_count = [regex]::Matches($recopy, "(?<!`r)`n").Count
        permitted_difference = 'PAD changed the 110 top-level action separators from LF to CRLF; embedded script line feeds and all normalized text remained unchanged.'
    }
    result = 'PASS_PAD_DESIGNER_SAVE_RECOPY_NO_EXECUTION'
}

[IO.File]::WriteAllText(
    $recordPath,
    (($record | ConvertTo-Json -Depth 8) + "`n"),
    $utf8
)

$record | ConvertTo-Json -Depth 8
