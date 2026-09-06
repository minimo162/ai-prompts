# Real local files/locks/ACLs; no shared folder, server or provider operations.
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
. (Join-Path $repo 'App.ps1') -Mode Library
$publisher=Join-Path $repo 'tools\Publish-AgentSource.ps1'
$root=Join-Path $repo ('.work\publish-test-'+[guid]::NewGuid().ToString('N'))
$source=Join-Path $root 'source';$target=Join-Path $root 'target'
$names=@('App.ps1','index.html','業務エージェント.cmd')
foreach($dir in @($source,$target)){[IO.Directory]::CreateDirectory($dir)|Out-Null}
foreach($entry in @(@($target,'0.1.0'),@($source,'0.1.1'))){
    [IO.File]::WriteAllText((Join-Path $entry[0] 'App.ps1'),('# App-Version: '+$entry[1]+"`r`n"))
    [IO.File]::WriteAllText((Join-Path $entry[0] 'index.html'),('<meta name="app-version" content="'+$entry[1]+'">'))
    [IO.File]::WriteAllText((Join-Path $entry[0] '業務エージェント.cmd'),('@rem '+$entry[1]+"`r`n@exit /b 0`r`n"))
}
$old=Get-AgentRelease $target;$new=Get-AgentRelease $source
$before=@{};foreach($name in $names){$before[$name]=(Get-Acl (Join-Path $target $name)).Sddl}
$checks=0
function Check($Condition,[string]$Name){if(-not $Condition){throw ('FAIL: '+$Name)};$script:checks++}
$argsBase=@{SourceDirectory=$source;DestinationDirectory=$target;ExpectedSourceRelease=$new.release;ExpectedDestinationRelease=$old.release}
# Failure to open the last file must leave the first two files untouched.
$locked=[IO.File]::Open((Join-Path $target $names[2]),'Open','ReadWrite','None')
try {
    $failed=$false
    try{& $publisher @argsBase -EvidenceDirectory (Join-Path $root 'locked')|Out-Null}catch{$failed=$true}
    Check $failed 'locked last destination rejects publication'
} finally {$locked.Dispose()}
Check ((Get-AgentRelease $target).release -ceq $old.release) 'all old bytes retained after lock failure'
# Real successful publication after releasing the lock.
& $publisher @argsBase -EvidenceDirectory (Join-Path $root 'success')|Out-Null
Check ((Get-AgentRelease $target).release -ceq $new.release) 'all new bytes published'
$result=Read-AgentJson (Join-Path $root 'success\result.json')
Check ($result.status -ceq 'published' -and $result.writes -eq 3 -and $result.metadata_preserved) 'publication result verifies metadata and all writes'
foreach($name in $names){Check ((Get-Acl (Join-Path $target $name)).Sddl -ceq $before[$name]) ('ACL unchanged: '+$name)}
Check ((Get-AgentRelease (Join-Path $root 'success\backup')).release -ceq $old.release) 'immutable old package backup'
$failed=$false
try{& $publisher @argsBase -EvidenceDirectory (Join-Path $root 'wrong-pin')|Out-Null}catch{$failed=$true}
Check $failed 'stale destination release refuses publication'
Check (-not (Test-Path (Join-Path $root 'wrong-pin'))) 'pin failure occurs before evidence creation'
# Inject a single write-boundary failure into an isolated copy, preserving the
# executable publisher. This verifies recovery, not an actual disk-full event.
$faultTarget=Join-Path $root 'fault-target';[IO.Directory]::CreateDirectory($faultTarget)|Out-Null
foreach($name in $names){[IO.File]::Copy((Join-Path $root ('success\backup\'+$name)),(Join-Path $faultTarget $name))}
$faultCode=[IO.File]::ReadAllText($publisher)
$faultCode=$faultCode.Replace(". (Join-Path `$PSScriptRoot '..\App.ps1') -Mode Library",(". '"+(Join-Path $repo 'App.ps1')+"' -Mode Library"))
$needle='Write-PublishStream $streams[$name] $payloads[$name]'
if(($faultCode.Split(@($needle),[StringSplitOptions]::None)).Count -ne 2){throw 'Fault insertion must be unique'}
$faultCode=$faultCode.Replace($needle,($needle+"`n"+"        throw 'TEST_WRITE_BOUNDARY'"))
$faultScript=Join-Path $root 'fault-publisher.ps1';[IO.File]::WriteAllText($faultScript,$faultCode,(New-Object Text.UTF8Encoding($true)))
$faultArgs=@{};foreach($key in $argsBase.Keys){$faultArgs[$key]=$argsBase[$key]};$faultArgs.DestinationDirectory=$faultTarget
$failed=$false
try{& $faultScript @faultArgs -EvidenceDirectory (Join-Path $root 'fault')|Out-Null}catch{$failed=$true}
Check $failed 'write-boundary exception reported as failed'
$result=Read-AgentJson (Join-Path $root 'fault\result.json')
Check ($result.rollback_attempted -and $result.rollback_verified -and $result.writes -eq 1 -and $result.metadata_preserved) 'single write failure restores all bytes with ACLs'
Check ((Get-AgentRelease $faultTarget).release -ceq $old.release) 'restored package has exact old release'
Write-AgentJson (Join-Path $root 'validation.json') @{status='passed';checks=$checks;source_sha256=Get-AgentHash $publisher;live_share_calls=0;provider_calls=0;fault_injection='single write-boundary exception; not actual disk failure'}
"PASS: $checks publication checks; real local files/locks/ACLs, one synthetic write fault; no live share/provider. Evidence: $root"
