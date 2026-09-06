param([Parameter(Mandatory=$true)][string]$ContextPath,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
$context=Get-Content -LiteralPath $ContextPath -Raw | ConvertFrom-Json
if($context.synthetic_only -ne $true -or $context.pad_required -ne $false -or $context.copilot_port -isnot [int] -or $context.copilot_port -lt 1024 -or $context.copilot_port -gt 65535){throw 'RESOURCE_CONTEXT_INVALID'}
$profile=[IO.Path]::GetFullPath((Join-Path $context.home 'data\edge-profile'))
$processes=@(Get-CimInstance Win32_Process -Filter "name='msedge.exe'")
$roots=@($processes|Where-Object { $_.CommandLine -and $_.CommandLine.Contains($profile) -and $_.CommandLine -notmatch '--type=' })
if($roots.Count -ne 1){throw 'RESOURCE_ROOT_NOT_UNIQUE'}
$owned=New-Object 'Collections.Generic.HashSet[uint32]';[void]$owned.Add([uint32]$roots[0].ProcessId)
do{$added=$false;foreach($p in $processes){if($owned.Contains([uint32]$p.ParentProcessId) -and $owned.Add([uint32]$p.ProcessId)){$added=$true}}}while($added)
$live=@(Get-Process -Id @($owned) -ErrorAction SilentlyContinue)
$targets=Invoke-RestMethod -Uri ('http://127.0.0.1:'+$context.copilot_port+'/json/list')
$tabs=@($targets|Where-Object type -CEQ 'page')
$record=[ordered]@{kind='owned_edge_resource_snapshot';captured_utc=[DateTime]::UtcNow.ToString('o');root_pid=[int]$roots[0].ProcessId;process_count=$live.Count;page_target_count=$tabs.Count;working_set_sum_bytes=($live|Measure-Object WorkingSet64 -Sum).Sum;private_memory_sum_bytes=($live|Measure-Object PrivateMemorySize64 -Sum).Sum;note='Point-in-time aggregate of the dedicated profile process tree. Includes retained historical tabs; not peak or capacity acceptance.'}
$full=[IO.Path]::GetFullPath($OutputPath);if(Test-Path -LiteralPath $full){throw 'EVIDENCE_EXISTS'}
[IO.File]::WriteAllText($full,($record|ConvertTo-Json),(New-Object Text.UTF8Encoding($false)))
$record|ConvertTo-Json
