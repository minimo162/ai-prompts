[CmdletBinding()]
param([string]$Root = (Split-Path -Parent $PSScriptRoot))

$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath($Root)
$probe = Join-Path $repo 'catalog/acceptance/issue38/probes/ex03-r11-minimal-powershell'
$recordPath = Join-Path $probe 'synthetic-pad-run-preflight.json'
if (Test-Path -LiteralPath $recordPath) { throw 'Preflight record exists' }

function Get-Sha([string]$Path) {
    (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Read-Json([string]$Name) {
    Get-Content -LiteralPath (Join-Path $probe $Name) -Raw | ConvertFrom-Json
}

$source = Join-Path $probe 'source.xlsx'
$template = Join-Path $probe 'template.xlsx'
$work = Join-Path $probe 'runtime/work.xlsx'
$output = Join-Path $probe 'runtime/result.xlsx'
$analysis = Read-Json 'analysis.json'
$sourceCapture = Read-Json 'independent-pad-capture.json'
$syntheticCapture = Read-Json 'synthetic-pad-capture.json'
$checks = [ordered]@{
    head_is_r10_checkpoint = ((git -C $repo rev-parse HEAD) -ceq 'ac90b0943d2ff4e1172c23712ef49fe93787b7b2')
    source_sha_fixed = ((Get-Sha $source) -ceq 'dda07aac129a7f2f55bbd40067eda426b4b8f4f997254e7e9f69059803ac5874')
    template_sha_fixed = ((Get-Sha $template) -ceq '13855dcaf2fa8a9dd8d282197fd74c2f138d9ebc5552debbedbc5886296d2bde')
    work_is_exact_template_copy = ((Get-Sha $work) -ceq (Get-Sha $template))
    output_absent = (-not (Test-Path -LiteralPath $output))
    source_pad_recopy_pass = ($sourceCapture.result -ceq 'PASS_PAD_DESIGNER_SAVE_RECOPY_NO_EXECUTION' -and $sourceCapture.comparison.lf_normalized_exact)
    synthetic_pad_recopy_pass = ($syntheticCapture.result -ceq 'PASS_PAD_DESIGNER_SAVE_RECOPY_NO_EXECUTION' -and $syntheticCapture.comparison.lf_normalized_exact)
    good_decode_parser_zero = ($analysis.extraction_decode_tests.good.parser_error_count -eq 0)
    negative_decode_detected = ($analysis.extraction_decode_tests.intentional_negative.parser_error_count -gt 0)
    local_script_parser_zero = ($analysis.local_successor.parser_error_count -eq 0)
    fragile_static_member_fragments_avoided = (@($analysis.local_successor.avoided_fragments).Count -eq 3)
    no_excel_process_before_run = (@(Get-Process -Name EXCEL -ErrorAction SilentlyContinue).Count -eq 0)
    r9_generated_preserved = ((Get-Sha (Join-Path $repo 'catalog/acceptance/issue38/cycles/EX03-r9-G1/generated.robin')) -ceq '7a02ea0d073adde698578b8fa578f5701c728114ee55fbf20aa0ecdaaa32cb14')
    r10_generated_preserved = ((Get-Sha (Join-Path $repo 'catalog/acceptance/issue38/cycles/EX03-r10-G1/generated.robin')) -ceq '4946431c9ce47f986b841115fbfd328036356c4e12ae7cbe912c2bf06e2b1ed3')
}
$passed = @($checks.Values | Where-Object { -not $_ }).Count -eq 0
$record = [ordered]@{
    schema_version = 1
    prepared_at = [DateTime]::UtcNow.ToString('o')
    status = if ($passed) { 'PASS_READY_FOR_ONE_DEDICATED_SYNTHETIC_PAD_RUN' } else { 'FAIL_STOP' }
    probe = 'EX03-R11-MINIMAL-POWERSHELL'
    flow_name = '無題 (9)'
    paths = [ordered]@{ source = $source; template = $template; work = $work; output = $output }
    checks = $checks
    authorization_boundary = [ordered]@{
        dedicated_synthetic_pad_run_max = 1
        copilot_send = 0
        integrated_ex03_run = 0
        github_write = 0
    }
}
$bytes = (New-Object Text.UTF8Encoding($false)).GetBytes((($record | ConvertTo-Json -Depth 8) + "`n"))
$stream = [IO.File]::Open($recordPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
$record | ConvertTo-Json -Depth 8
if (-not $passed) { exit 2 }
