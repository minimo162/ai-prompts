[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$FlowName,
    [Parameter(Mandatory = $true)][int]$FlowWindowId
)

$ErrorActionPreference = 'Stop'
$probe = $PSScriptRoot
$trial1 = Join-Path $probe 'trials/EX03-R12-FIXED-HELPER-P1-T1'
$trial2 = Join-Path $probe 'trials/EX03-R12-FIXED-HELPER-P1-T2'
$runtime = Join-Path $trial1 'runtime'
$baselineRecopy = Join-Path $trial1 'pad-recopy-mismatch.robin'
$capturedRecopy = Join-Path $trial2 'pad-recopy-before-run.robin'
$recordPath = Join-Path $trial2 'pad-recopy.json'
$helperPath = Join-Path $probe 'EX03-R12-Fixed-StringTransfer.ps1'
$invocationPath = Join-Path $trial1 'invocation.json'
$launcherPath = Join-Path $trial1 'launcher.ps1'
$workPath = Join-Path $runtime 'work.xlsx'
$outputPath = Join-Path $runtime '照合結果.xlsx'
$expected = [ordered]@{
    helper = '08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135'
    invocation = '92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6'
    launcher = '1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1'
    pad_recopy = 'da54e5f4388cd0bb896ee00e534e9d81a444f5b950ac1f1bf006f8ea788ad4aa'
    template = '881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21'
}

if (Test-Path -LiteralPath $trial2) { throw 'Refusing to overwrite T2 evidence' }
foreach ($path in @($baselineRecopy, $helperPath, $invocationPath, $launcherPath, $workPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required file missing: $path" }
}
if (Test-Path -LiteralPath $outputPath) { throw 'Output exists before T2 Run' }

$jsonPaths = @(1..7 | ForEach-Object { Join-Path $runtime "source-$_.json" })
$jsonPaths += Join-Path $runtime 'mode.json'
if (@($jsonPaths | Where-Object { Test-Path -LiteralPath $_ }).Count) {
    throw 'JSON handoff exists before T2 Run'
}

function Get-FileSha([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$utf8 = [Text.UTF8Encoding]::new($false)
$current = Get-Clipboard -Raw
if ([string]::IsNullOrEmpty($current)) { throw 'Current PAD re-copy clipboard is empty' }
if ($current -ceq 'ISSUE38_FIXED_HELPER_T2_RECOPY_SENTINEL_20260918') {
    throw 'PAD copy did not replace the T2 sentinel'
}
$algorithm = [Security.Cryptography.SHA256]::Create()
try {
    $currentSha = ([BitConverter]::ToString($algorithm.ComputeHash($utf8.GetBytes($current)))).Replace('-', '').ToLowerInvariant()
} finally {
    $algorithm.Dispose()
}

$observed = [ordered]@{
    helper = Get-FileSha $helperPath
    invocation = Get-FileSha $invocationPath
    launcher = Get-FileSha $launcherPath
    t1_baseline_recopy = Get-FileSha $baselineRecopy
    current_saved_flow_recopy = $currentSha
    work = Get-FileSha $workPath
}
foreach ($name in $expected.Keys) {
    $observedName = if ($name -eq 'pad_recopy') { 't1_baseline_recopy' } elseif ($name -eq 'template') { 'work' } else { $name }
    if ($observed[$observedName] -cne $expected[$name]) {
        throw "Fixed SHA mismatch for $name"
    }
}
if ($currentSha -cne $expected.pad_recopy) { throw 'Current saved flow differs from T1 re-copy baseline' }

[void][IO.Directory]::CreateDirectory($trial2)
[IO.File]::WriteAllText($capturedRecopy, $current, $utf8)
if ((Get-FileSha $capturedRecopy) -cne $expected.pad_recopy) {
    throw 'Captured T2 re-copy SHA mismatch'
}

$record = [ordered]@{
    schema_version = 1
    trial_id = 'EX03-R12-FIXED-HELPER-P1-T2'
    captured_utc = [DateTime]::UtcNow.ToString('o')
    execution_baseline = [ordered]@{
        source_trial = 'EX03-R12-FIXED-HELPER-P1-T1'
        source_path = 'catalog/acceptance/issue38/probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T1/pad-recopy-mismatch.robin'
        required_sha256 = $expected.pad_recopy
    }
    flow = [ordered]@{
        name = $FlowName
        window_id = $FlowWindowId
        subflow = 'Main'
        power_fx = 'OFF'
        status_before_run = 'READY'
    }
    observation = [ordered]@{
        repaste_count = 0
        resave_count = 0
        verification_recopy_count = 1
        pad_run_count = 0
    }
    comparison = [ordered]@{
        t1_baseline_sha256 = $observed.t1_baseline_recopy
        current_saved_flow_sha256 = $currentSha
        captured_sha256 = Get-FileSha $capturedRecopy
        byte_exact_to_t1_baseline = $true
        characters = $current.Length
        utf8_bytes = $utf8.GetByteCount($current)
        crlf_count = [regex]::Matches($current, "`r`n").Count
        lf_only_count = [regex]::Matches($current, "(?<!`r)`n").Count
        final_newline = $current.EndsWith("`n") -or $current.EndsWith("`r")
    }
    fixed_sha256 = $observed
    pre_run = [ordered]@{
        work_matches_template = $true
        output_absent = $true
        json_handoff_absent = $true
    }
    result = 'PASS_CURRENT_SAVED_FLOW_EXACT_T1_RECOPY_BASELINE'
}
[IO.File]::WriteAllText($recordPath, (($record | ConvertTo-Json -Depth 10) + "`n"), $utf8)
$record | ConvertTo-Json -Depth 10
