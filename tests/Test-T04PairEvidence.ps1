param([string]$Root=(Get-Location).Path)
$ErrorActionPreference='Stop'
$checks=0
function Check([bool]$Value,[string]$Message){if(-not $Value){throw ('T04_PAIR: '+$Message)};$script:checks++}
function ReadJson([string]$Path){Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json}
$dir=Join-Path $Root 'catalog/evidence/t04-independent-pair-20260914w'
$a=ReadJson "$dir/acceptance.json";$p=ReadJson "$dir/plan.json"
Check ($a.status -ceq 'PASS_INDEPENDENT_T04_NEW_PAIR') 'separate pair accepted'
Check ($a.old_run1 -ceq 'NOT_CAPTURED' -and $a.old_candidate -ceq 'candidate_partial' -and $a.original_primary_t04 -ceq 'NOT_ACCEPTED_PRESERVED') 'old evidence never promoted'
Check ($a.pad_run_starts -eq 2 -and $a.copilot_sends -eq 0 -and $a.c_reruns -eq 0 -and $a.t10_reruns -eq 0 -and -not $a.third_run) 'bounded operation counts'
Check ($p.max_run_starts -eq 2 -and $a.pid -eq $p.pid -and $a.hwnd -eq $p.hwnd -and $p.hwnd -gt 0 -and $p.session_id -eq 1) 'fixed target binding'
Check ((Get-FileHash (Join-Path $Root $p.source)).Hash.ToLowerInvariant() -ceq $p.source_sha256) 'unmodified saved generation'
foreach($f in $a.files){
    $path=Join-Path $Root $f.path
    Check (Test-Path -LiteralPath $path) ('file exists '+$f.path)
    Check ((Get-FileHash $path).Hash.ToLowerInvariant() -ceq $f.sha256 -and (Get-Item $path).Length -eq $f.bytes) ('original bytes '+$f.path)
}
Check ((Get-FileHash "$dir/recopy.robin").Hash -ceq (Get-FileHash "$dir/after-run2.robin").Hash) 'recopy unchanged across runs'
$run1=ReadJson "$dir/run1/values.json";$req2=ReadJson "$dir/run2-request.json"
Check ([datetime]$run1.verified_at -lt [datetime]$req2.requested_at) 'Run1 values verified before Run2 request'
foreach($n in @(1,2)){
    $q=ReadJson "$dir/run$n-request.json";$o=ReadJson "$dir/run$n-observation.json";$v=ReadJson "$dir/run$n/values.json"
    Check ($q.outputs_absent -and $q.before.ready -and -not $q.before.running -and $q.before.errors_known -and $q.before.errors -eq 0) ('fresh stopped before run '+$n)
    Check ($q.request_count -eq 1 -and $q.run_number -eq $n -and $q.plan_sha256 -ceq (Get-FileHash "$dir/plan.json").Hash.ToLowerInvariant()) ('fixed request '+$n)
    Check ($o.running_observed -and $o.completion_observed -and -not $o.additional_run_requested -and $null -eq $o.invoke_error) ('same execution completed '+$n)
    Check ($v.status -ceq 'PASS' -and $v.run_number -eq $n -and $v.input_unchanged -and @($v.artifacts).Count -eq 2) ('both artifacts gate '+$n)
    Check (($v.observed.'.xlsx' | ConvertTo-Json -Compress) -ceq ($p.expected_cells | ConvertTo-Json -Compress)) ('xlsx cells '+$n)
    foreach($f in $v.artifacts){Check ((Get-FileHash (Join-Path $Root $f.path)).Hash.ToLowerInvariant() -ceq $f.sha256) ('snapshot SHA '+$n)}
}
Check (@((ReadJson "$dir/restoration.json") | Where-Object {-not $_.restored}).Count -eq 0) 'existing artifacts restored'
Check ($a.operational_exception -match 'initially prevented' -and $a.clipboard_recovery.text_equal -and $a.clipboard_recovery.original_formats_present -and $a.clipboard_recovery.full_format_byte_equality -eq 'NOT_ASSESSED') 'clipboard failure and bounded history recovery retained'
# Exercise duplicate/limit refusals before the runner can import App or invoke UI.
$sandbox=Join-Path $Root ('.work/test-pair-guards-'+[guid]::NewGuid().ToString('N'))
[IO.Directory]::CreateDirectory($sandbox)|Out-Null
'{"max_run_starts":2}' | Set-Content "$sandbox/plan.json" -Encoding UTF8
'{}' | Set-Content "$sandbox/run1-request.json" -Encoding UTF8
$refused=$false
try{& (Join-Path $Root 'tools/Run-PadArtifactPairLive.ps1') -PlanPath "$sandbox/plan.json" -RunNumber 1}catch{$refused=$_.Exception.Message -match 'already requested'}
Check $refused 'duplicate request refused before native import'
$refused=$false
try{& (Join-Path $Root 'tools/Run-PadArtifactPairLive.ps1') -PlanPath "$sandbox/plan.json" -RunNumber 3}catch{$refused=$true}
Check $refused 'third run rejected by parameter contract'
# Extract the actual Run2 preflight only; stubs never import App or touch UI.
$parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $Root 'tools/Run-PadArtifactPairLive.ps1'),[ref]$null,[ref]$parseErrors)
Check ($parseErrors.Count -eq 0) 'runner parses'
$guard=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.IfStatementAst] -and $n.Clauses[0].Item1.Extent.Text -eq '$RunNumber -eq 2'},$true))[0].Clauses[0].Item2.Extent.Text
$guard=$guard.Substring(1,$guard.Length-2)
$plan=ReadJson "$dir/plan.json"
$script:gateForTest=ReadJson "$dir/run1/values.json"
$root=$Root
function Get-Content { $script:gateForTest | ConvertTo-Json -Depth 12 }
. ([scriptblock]::Create($guard))
Check $true 'actual Run2 gate accepts saved distinct artifact pair'
$script:gateForTest.artifacts=@($script:gateForTest.artifacts[0],$script:gateForTest.artifacts[0])
$refused=$false
try{. ([scriptblock]::Create($guard))}catch{$refused=$_.Exception.Message -match 'identities mismatch'}
Check $refused 'Run2 refuses duplicated artifact with matching hash and count'
'PASS: '+$checks+' T04 new-pair evidence checks; no native Run or clipboard calls'
