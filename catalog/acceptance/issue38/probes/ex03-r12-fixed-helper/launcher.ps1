$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$helperPath = 'C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper\EX03-R12-Fixed-StringTransfer.ps1'
$invocationPath = 'C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r12-fixed-helper\invocation.json'
$expectedHelperSha256 = '08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135'
$expectedInvocationSha256 = '9ff979598a0383099aec88ca3aace330f29ed519cc66d9cf6ca63e31d962227a'
$expectedSuccess = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'

function Stop-Launcher {
    param([string]$Code, [int]$ExitCode)
    $failure = [ordered]@{ status = 'ERROR'; error_code = $Code }
    [Console]::Out.Write([string]($failure | ConvertTo-Json -Compress))
    exit $ExitCode
}

function Get-Sha256 {
    param([string]$Path)
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    }
    finally {
        $algorithm.Dispose()
        $stream.Dispose()
    }
}

if (-not (Test-Path -LiteralPath $helperPath -PathType Leaf)) {
    Stop-Launcher 'HELPER_NOT_FOUND' 41
}
if (-not (Test-Path -LiteralPath $invocationPath -PathType Leaf)) {
    Stop-Launcher 'INVOCATION_NOT_FOUND' 42
}

$actualHelperSha256 = Get-Sha256 $helperPath
if ($actualHelperSha256 -cne $expectedHelperSha256) {
    Stop-Launcher 'HELPER_SHA256_MISMATCH' 43
}
$actualInvocationSha256 = Get-Sha256 $invocationPath
if ($actualInvocationSha256 -cne $expectedInvocationSha256) {
    Stop-Launcher 'INVOCATION_SHA256_MISMATCH' 44
}

try {
    $helperOutput = (& $helperPath -InvocationPath $invocationPath | Out-String).Trim()
}
catch {
    Stop-Launcher 'HELPER_INVOCATION_FAILED' 45
}

if ([string]::IsNullOrWhiteSpace($helperOutput)) {
    Stop-Launcher 'HELPER_SUCCESS_OUTPUT_MISSING' 46
}
if ($helperOutput -cne $expectedSuccess) {
    Stop-Launcher 'HELPER_UNEXPECTED_OUTPUT' 47
}

[Console]::Out.Write($helperOutput)
