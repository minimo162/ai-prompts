# Explicit live preparation. Opens only a newly owned Edge profile; never copies authentication.
param([Parameter(Mandatory=$true)][string]$OutputDirectory,[switch]$Live,[ValidatePattern('^$|^[a-f0-9]{40}$')][string]$SourceCommit='')
$ErrorActionPreference='Stop'
if(-not $Live){throw 'LIVE_OPT_IN: Specify -Live to open a dedicated Copilot profile.'}
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
. (Join-Path $repo 'App.ps1') -Mode Library
$root=Get-AgentFullPath $OutputDirectory;Assert-AgentNoReparse $root
if(Test-Path -LiteralPath $root){throw 'LIVE_DIRECTORY_EXISTS: Use a new output directory.'}
$package=Join-Path $root 'package';[void][IO.Directory]::CreateDirectory($package)
$release=Get-AgentRelease $repo
foreach($name in @('App.ps1','index.html','業務エージェント.cmd')){[IO.File]::Copy((Join-Path $repo $name),(Join-Path $package $name))}
if((Get-AgentRelease $package).release -cne $release.release){throw 'LIVE_PACKAGE_CHANGED'}
$runtimeHome=Initialize-AgentHome (Join-Path $root 'home')
$probe=New-Object Net.Sockets.TcpListener([Net.IPAddress]::Loopback,0);$probe.Start();$port=$probe.LocalEndpoint.Port;$probe.Stop()
$settings=Get-AgentSettings $runtimeHome;$settings.copilot_port=$port;Assert-AgentSettings $settings
Write-AgentJson (Join-Path $runtimeHome 'data\settings.json') $settings
$contextPath=Join-Path $root 'context.json'
Write-AgentJson $contextPath @{home=$runtimeHome;app=Join-Path $package 'App.ps1';release=$release;source_commit=$SourceCommit;copilot_port=$port;synthetic_only=$true;pad_required=$false}
Write-Output $contextPath
Open-AgentCopilot $runtimeHome $settings | Select-Object status,port | ConvertTo-Json
Get-AgentCopilotDiagnostic $runtimeHome $settings | ConvertTo-Json
