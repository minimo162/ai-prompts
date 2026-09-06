# Maintainer tool; never a fourth required application file. Not a signature or approval.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Directory,[ValidateSet('development','candidate','production')][string]$Channel='candidate',[string]$RecordPath='',[ValidatePattern('^$|^[a-f0-9]{40}$')][string]$SourceCommit='')
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$directoryPath=Get-AgentFullPath $Directory; Assert-AgentNoReparse $directoryPath
foreach($name in @('App.ps1','index.html','業務エージェント.cmd')) { Assert-AgentNoReparse (Join-Path $directoryPath $name) }
if($RecordPath){$RecordPath=Get-AgentFullPath $RecordPath;Assert-AgentNoReparse $RecordPath;if(Test-Path -LiteralPath $RecordPath){throw 'SEAL_RECORD: Use a new record path.'};if($RecordPath.StartsWith($directoryPath+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'SEAL_RECORD: Keep maintainer records outside the three-file package.'}}
$appPath=Join-Path $directoryPath 'App.ps1'
$raw=(New-Object Text.UTF8Encoding($false,$true)).GetString([IO.File]::ReadAllBytes($appPath))
$pattern='(?m)^# Release-Binding: [^\r\n]*'
if([regex]::Matches($raw,$pattern).Count -ne 1){throw 'SEAL_DECLARATION: Add exactly one Release-Binding declaration before sealing.'}
$state=[regex]::Matches($raw,'(?m)^# State-Contract: ([12])\r?$')
if($state.Count -ne 1){throw 'SEAL_DECLARATION: Declare the supported state contract.'}
$appHash=Get-AgentReleasePayloadHash $appPath
$htmlHash=Get-AgentHash (Join-Path $directoryPath 'index.html'); $cmdHash=Get-AgentHash (Join-Path $directoryPath '業務エージェント.cmd')
$id=(Get-AgentTextHash ($appHash+'|'+$htmlHash+'|'+$cmdHash+'|'+$Channel+'|'+$state[0].Groups[1].Value)).Substring(0,32)
$binding=[ordered]@{schema_version=1;release_id=$id;channel=$Channel;state_contract=[int]$state[0].Groups[1].Value;app_payload_sha256=$appHash;html_sha256=$htmlHash;cmd_sha256=$cmdHash}
$encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes((ConvertTo-Json $binding -Compress)))
$sealed=[regex]::Replace($raw,$pattern,('# Release-Binding: '+$encoded))
[IO.File]::WriteAllText($appPath,$sealed,(New-Object Text.UTF8Encoding($false)))
$release=Get-AgentRelease $directoryPath
if($RecordPath){Write-AgentJson $RecordPath @{schema_version=1;source_commit=$SourceCommit;release=$release;created_utc=[DateTime]::UtcNow.ToString('o');signature=$false;acceptance_approved=$false}}
$release | ConvertTo-Json -Depth 10
