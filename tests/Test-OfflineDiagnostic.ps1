[CmdletBinding()]
param([string]$AppSourcePath = '')
$ErrorActionPreference = 'Stop'
if (-not $AppSourcePath) { $AppSourcePath = Join-Path $PSScriptRoot '..\App.ps1' }
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\offline-' + [guid]::NewGuid().ToString('N'))))
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library -HomePath $root -OfflineTest
$checks = 0
function Assert-Case($Condition, [string]$Label) { if (-not $Condition) { throw ('FAIL: ' + $Label) }; $script:checks++ }
function Assert-Blocked([scriptblock]$Action) { $message = ''; try { & $Action | Out-Null } catch { $message = $_.Exception.Message }; Assert-Case ($message -match '^(CDP|PAD)_UNAVAILABLE:') 'Offline boundary refuses operations' }
Assert-Case (-not [IO.Directory]::Exists($root)) 'Library import has no home/filesystem side effects'
Assert-Blocked { Invoke-AgentCopilot -Prompt 'synthetic' -RequestId 'test' -JobId ('a' * 32) -HomePath $root }
Assert-Blocked { Invoke-AgentCopilotHttp -Config $null -Path '/json/list' }
Assert-Blocked { Open-AgentCopilot -HomePath $root -Settings $null }
Assert-Blocked { Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $root -RunId ('b' * 32) -Job $null -Settings $null -CancelPath '' }
Assert-Case (-not [IO.Directory]::Exists($root)) 'Refused operations created no profile, attempt, or output'
$secret = 'SYNTHETIC_SECRET_81234'
$job = [pscustomobject]@{ status = 'partial'; error = $secret; goal = $secret; target = 'C:\Users\SyntheticPerson\secret.csv'; token = $secret; history = @($secret); summary = [pscustomobject]@{ total = 50; success = 20; needs_review = 3; failed = 1; unprocessed = 26; unknown = 0 }; results = @($secret) }
$diagnostic = Get-AgentSupportDiagnostic $root $job
$json = ConvertTo-Json $diagnostic -Depth 10
Assert-Case (-not $json.Contains($secret) -and -not $json.Contains('SyntheticPerson') -and -not $json.Contains('secret.csv')) 'Support allowlist excludes secret, user path, and all business data'
Assert-Case ($diagnostic.counts.total -eq 50 -and $diagnostic.phase -ceq 'partial' -and -not $diagnostic.uploaded) 'Support includes typed counters and no upload'
$job.status = $secret; $job.summary.total = $secret
$diagnostic = Get-AgentSupportDiagnostic $root $job
Assert-Case ($diagnostic.phase -ceq 'unknown' -and $diagnostic.counts.total -eq 0 -and -not (ConvertTo-Json $diagnostic).Contains($secret)) 'Malformed expected fields do not bypass allowlist'
$job|Add-Member job_id ('a'*32) -Force
$job|Add-Member release_app_sha256 ('d'*64) -Force
$job|Add-Member preservation ([pscustomobject]@{main_status='needs_recovery';clipboard_status='restore_failed';warnings=@($secret)}) -Force
$job|Add-Member recovery_required $true -Force
$trace=New-AgentConnectionTrace $root ('b'*32) ('a'*32) JsonPartsV1
$trace|Add-Member deadline_utc '2026-09-07T01:02:03.0000000Z' -Force
$trace|Add-Member prompt $secret -Force
$trace.send_reserved=$true;$trace.error_type='timeout';Set-AgentConnectionTrace $root $trace unknown 180000
$diagnostic=Get-AgentSupportDiagnostic $root $job;$json=ConvertTo-Json $diagnostic -Depth 10
Assert-Case ($diagnostic.schema_version -eq 2 -and $diagnostic.job_ref -cmatch '^[a-f0-9]{16}$' -and $diagnostic.job_ref -cne $job.job_id) 'Diagnostic has a scoped opaque reference'
Assert-Case ($diagnostic.job_app_sha256 -ceq ('d'*64) -and $diagnostic.app_sha256 -cne $diagnostic.job_app_sha256) 'Job start hash is separate from current runtime hash'
Assert-Case ($diagnostic.connection.elapsed_ms -eq 180000 -and $diagnostic.connection.error_type -ceq 'timeout' -and $diagnostic.connection.send_reserved -and $diagnostic.connection.deadline_utc -ceq '2026-09-07T01:02:03.0000000Z') 'Connection preserves bounded timing and typed send uncertainty'
Assert-Case ($diagnostic.preservation.main_status -ceq 'needs_recovery' -and $diagnostic.preservation.clipboard_status -ceq 'restore_failed' -and $diagnostic.preservation.recovery_required) 'Preservation failure is separate from job completion'
Assert-Case (-not $json.Contains($secret) -and -not $json.Contains($job.job_id) -and -not $json.Contains('b'*32)) 'Nested trace and preservation cannot expose raw data or raw IDs'
$trace.elapsed_ms=$secret;$trace.phase=$secret;$trace.error_type=$secret;$trace.send_reserved=$secret;$trace.deadline_utc=$secret
Write-AgentJson ((Get-AgentCopilotAttemptPath $root ('b'*32))+'.json') $trace
$job.preservation.main_status=$secret;$job.recovery_required=$secret
$diagnostic=Get-AgentSupportDiagnostic $root $job
Assert-Case ($null -eq $diagnostic.connection.elapsed_ms -and $null -eq $diagnostic.connection.send_reserved -and $null -eq $diagnostic.connection.deadline_utc -and $diagnostic.connection.phase -ceq 'unknown') 'Malformed telemetry cannot become typed support facts'
Assert-Case (-not (ConvertTo-Json $diagnostic -Depth 10).Contains($secret) -and $diagnostic.preservation.main_status -ceq 'unknown' -and $null -eq $diagnostic.preservation.recovery_required) 'Malformed nested values stay out of support output'
$job.job_id='c'*32
Assert-Case ($null -eq (Get-AgentSupportDiagnostic $root $job).connection) 'Other job telemetry is not selected'
Write-Output "PASS: $checks offline/privacy checks; provider, browser and PAD operations 0."
