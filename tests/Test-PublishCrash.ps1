$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
. (Join-Path $PSScriptRoot 'ReleaseFixture.ps1')
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\publish-crash-'+[guid]::NewGuid().ToString('N'))));[void][IO.Directory]::CreateDirectory($root)
$source=Join-Path $root 'source';$target=Join-Path $root 'target';$evidence=Join-Path $root 'publication';$marker=Join-Path $root 'after-first-write'
$names=@('App.ps1','index.html','業務エージェント.cmd');$checks=0
function Check($Condition,[string]$Name){if(-not $Condition){throw ('FAIL: '+$Name)};$script:checks++}
foreach($entry in @(@($source,'0.2.0'),@($target,'0.1.0'))){
 [void][IO.Directory]::CreateDirectory($entry[0])
 [IO.File]::WriteAllText((Join-Path $entry[0] 'App.ps1'),('# App-Version: '+$entry[1]+"`r`n# Inert fixture`r`n"),$script:AgentEncoding)
 [IO.File]::WriteAllText((Join-Path $entry[0] 'index.html'),('<meta name="app-version" content="'+$entry[1]+'">'),$script:AgentEncoding)
 [IO.File]::WriteAllText((Join-Path $entry[0] '業務エージェント.cmd'),('@rem '+$entry[1]),[Text.Encoding]::ASCII)
 Set-TestReleaseBinding $entry[0]
}
$old=Get-AgentRelease $target;$new=Get-AgentRelease $source
$oldAcls=@{};foreach($name in $names){$oldAcls[$name]=(Get-Acl -LiteralPath (Join-Path $target $name)).Sddl}
$publisher=Join-Path $PSScriptRoot '..\tools\Publish-AgentSource.ps1'
$code=[IO.File]::ReadAllText($publisher,[Text.Encoding]::UTF8)
$code=$code.Replace(". (Join-Path `$PSScriptRoot '..\App.ps1') -Mode Library",(". '"+$script:AgentAppPath.Replace("'","''")+"' -Mode Library"))
$needle='Write-PublishStream $streams[$name] $payloads[$name]'
Check (($code.Split(@($needle),[StringSplitOptions]::None)).Count -eq 2) 'One exact write boundary'
$injected=$needle+"`r`n        [IO.File]::WriteAllText('"+$marker.Replace("'","''")+"','ready'); while (`$true) { Start-Sleep -Milliseconds 100 }"
$code=$code.Replace($needle,$injected);$fault=Join-Path $root 'crash-publisher.ps1';[IO.File]::WriteAllText($fault,$code,(New-Object Text.UTF8Encoding($true)))
$argsText='-NoProfile -ExecutionPolicy Bypass -File "'+$fault+'" -SourceDirectory "'+$source+'" -DestinationDirectory "'+$target+'" -EvidenceDirectory "'+$evidence+'" -ExpectedSourceRelease '+$new.release+' -ExpectedDestinationRelease '+$old.release
$process=Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList $argsText -WindowStyle Hidden -PassThru
try{
 $deadline=[DateTime]::UtcNow.AddSeconds(15)
 while(-not [IO.File]::Exists($marker) -and -not $process.HasExited -and [DateTime]::UtcNow -lt $deadline){Start-Sleep -Milliseconds 100}
 Check ([IO.File]::Exists($marker) -and -not $process.HasExited) 'Publisher confirmed live after exactly first destination write'
 $process.Kill();Check ($process.WaitForExit(5000)) 'Owned publisher force-terminated, releasing its locks'
}finally{if(-not $process.HasExited){$process.Kill()};$process.Dispose()}
$errorText='';try{Get-AgentRelease $target|Out-Null}catch{$errorText=$_.Exception.Message}
Check ($errorText -like 'INVALID_RELEASE:*') 'Crashed mixed package is not accepted'
Check ((Get-AgentRelease (Join-Path $evidence 'backup')).release -ceq $old.release) 'Original complete backup survives process crash'
foreach($name in $names){Check ((Get-Acl -LiteralPath (Join-Path $target $name)).Sddl -ceq $oldAcls[$name]) 'Crash preserved file ACL and owner'}
$hashes=@{};foreach($name in $names){$hashes[$name]=Get-AgentHash (Join-Path $target $name)}
$recovery=Join-Path $root 'recovery'
& (Join-Path $PSScriptRoot '..\tools\Restore-AgentPublishedBackup.ps1') -PublicationEvidenceDirectory $evidence -DestinationDirectory $target -EvidenceDirectory $recovery -ExpectedBackupRelease $old.release -ExpectedAppHash $hashes.'App.ps1' -ExpectedHtmlHash $hashes.'index.html' -ExpectedCmdHash $hashes.'業務エージェント.cmd' | Out-Null
Check ((Get-AgentRelease $target).release -ceq $old.release) 'Explicit recovery restores exactly the previous complete set'
$result=Read-AgentJson (Join-Path $recovery 'result.json')
Check ($result.status -ceq 'restored' -and $result.metadata_preserved) 'Recovery confirms bytes and metadata'
foreach($name in $names){Check ((Get-Acl -LiteralPath (Join-Path $target $name)).Sddl -ceq $oldAcls[$name]) 'Recovery preserved owner/ACL'}
Write-Output "PASS: $checks native process-crash and recovery checks. Local synthetic files only. Evidence: $root"
