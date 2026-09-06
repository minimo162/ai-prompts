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
Write-Output "PASS: $checks offline/privacy checks; provider, browser and PAD operations 0."
