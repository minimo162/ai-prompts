# Real PS5 persistence/process identity, mocked PAD/clipboard. No native PAD/clipboard operations.
param([string]$AppSourcePath='')
$ErrorActionPreference='Stop'
if(-not $AppSourcePath){$AppSourcePath=Join-Path $PSScriptRoot '..\App.ps1'}
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library
$script:checks=0
function Check($Value,[string]$Name){if(-not $Value){throw ('FAIL: '+$Name)};$script:checks++}
$dead=Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList '-NoProfile -Command "Start-Sleep -Milliseconds 300"' -WindowStyle Hidden -PassThru
$deadPid=$dead.Id;$deadStarted=$dead.StartTime.ToUniversalTime().ToString('o');[void]$dead.WaitForExit(5000);Check $dead.HasExited 'Synthetic prior controller has actually exited';$dead.Dispose()
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\pad-recovery-'+[guid]::NewGuid().ToString('N'))))
$script:windowIdentity=[pscustomobject]@{pid=$PID;handle=1;started=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o')}
function Get-AgentPadWindow($Settings){$script:windowReads++;return [pscustomobject]@{mock=$true}}
function Get-AgentPadWindowIdentity($Window){if($script:scenario -ceq 'other_window'){return [pscustomobject]@{pid=$PID;handle=2;started=$script:windowIdentity.started}};return $script:windowIdentity}
function Get-AgentPadSnapshot($Window,[switch]$AllowErrors){return [pscustomobject]@{window=$Window;workspace='main';save='save';start='run';idle=($script:scenario -cne 'running');editable=($script:scenario -cne 'running');running=($script:scenario -ceq 'running');errors_known=$true;errors=0;status=$(if($script:saved){'saved'}else{'ready'})}}
function Test-AgentPadEmpty($Workspace){return $script:main -ceq ''}
function Set-AgentPadFocus($Window,$Workspace){}
function Get-AgentPadClipboardSequence{return $script:sequence}
function Get-AgentPadClipboard{return $script:clipboard}
function Get-AgentPadClipboardText{return $script:clipboard}
function Set-AgentPadClipboardText([string]$Text){Assert-AgentPadClipboardUnchanged;$script:clipboard=$Text;$script:sequence++;$script:AgentPadClipboardSequence=$script:sequence;$script:AgentPadClipboardValue=$Text}
function Restore-AgentPadClipboard($Value){$script:restores++;if($script:scenario -ceq 'clipboard_failure'){throw 'Synthetic clipboard failure'};$script:clipboard=$Value;$script:sequence++}
function Get-AgentPadCode($Snapshot,[string]$CancelPath=''){Set-AgentPadClipboardText $script:main;return $script:main}
function Send-AgentPadKeys([string]$Keys){if($Keys -ceq '{DELETE}'){$script:main='';$script:saved=$false;$script:edits++};if($Keys -ceq '^v'){$script:main=$script:clipboard;$script:saved=$false;$script:edits++;if($script:scenario -ceq 'restore_paste_mismatch'){$script:main+=' changed'}}}
function Wait-AgentPadEditable($Window,[string]$CancelPath,[switch]$RequireActions){if($RequireActions -and -not $script:main){throw 'Empty mock paste'};return Get-AgentPadSnapshot $Window}
function Wait-AgentPadSaveBaseline($Window,[string]$CancelPath){return Get-AgentPadSnapshot $Window}
function Wait-AgentPadSaved($Window,[string]$CancelPath){return Get-AgentPadSnapshot $Window}
function Invoke-AgentPadControl($Element){if($Element -ceq 'run'){$script:runs++;throw 'UNEXPECTED_RUN'};if($Element -ceq 'save'){$script:saves++;if($script:scenario -ceq 'save_failure'){throw 'Synthetic native Save boundary failure'};$script:saved=$true;if($script:scenario -ceq 'user_same_text'){$script:sequence++;$script:flavor='user RTF'}}}
function New-Fixture([string]$Scenario,[string]$Phase='saving',[switch]$EmptyOriginal){
 $script:scenario=$Scenario;$script:sequence=1;$script:clipboard='original user clipboard';$script:flavor='original';$script:edits=0;$script:runs=0;$script:saves=0;$script:restores=0;$script:windowReads=0;$script:saved=$false
 $fixtureHome=Initialize-AgentHome (Join-Path $root ([guid]::NewGuid().ToString('N')));$jobId=[guid]::NewGuid().ToString('N');$runId=[guid]::NewGuid().ToString('N');$jobDir=Get-AgentJobDirectory $fixtureHome $jobId;$run=Join-Path $jobDir ('runs\'+$runId);[void][IO.Directory]::CreateDirectory($run)
 $old=if($EmptyOriginal){''}else{'SET AgentOwnedFlow TO $'+"'''AiPromptsAgent'''`r`nWAIT 0"};$new='SET AgentOwnedFlow TO $'+"'''AiPromptsAgent'''`r`nWAIT 1"
 $job=[pscustomobject]@{job_id=$jobId;status='blocked';last_pad_run_id=$runId;recovery_required=$true;history=@();error='synthetic editing failure'}
 Write-AgentJson (Join-Path $jobDir 'job.json') $job
 $settings=[pscustomobject]@{pad_flow_name='TEST ONLY'};$owner=Get-AgentPadOwnerPath $run $jobId $settings.pad_flow_name;$ownerBytes=@()
 if(-not $EmptyOriginal){$ownerText=' { "flow_name": "TEST ONLY", "hash": "'+(Get-AgentTextHash (ConvertTo-AgentComparableRobin $old))+'" }'+"`r`n";$ownerBytes=(New-Object Text.UTF8Encoding($true)).GetPreamble()+[Text.Encoding]::UTF8.GetBytes($ownerText);[IO.File]::WriteAllBytes($owner,[byte[]]$ownerBytes)}
 $script:scenario='capture';$state=New-AgentPadRecoveryBackup $run $runId $job $settings ([pscustomobject]@{mock=$true}) $old $new;$script:scenario=$Scenario
 # A post-exit fixture uses a real terminated PID/start identity; no desktop state is claimed.
 $backupPath=Join-Path $run 'pad-backup.json';$backup=Read-AgentJson $backupPath;$backup.controller_pid=$deadPid;$backup.controller_started=$deadStarted;Write-AgentJson $backupPath $backup
 $state.backup_sha256=Get-AgentHash $backupPath;$state.phase=$Phase;$state.paste_settled=$Phase -cne 'paste_requested';Write-AgentJson (Join-Path $run 'pad-recovery-state.json') $state
 $script:main=if($Phase -ceq 'deleted'){''}else{$new}
 if($Scenario -ceq 'user_edited'){$script:main+=' user edit'}
 if($Scenario -ceq 'new_owner'){Write-AgentJson $owner ([ordered]@{flow_name='TEST ONLY';hash=Get-AgentTextHash (ConvertTo-AgentComparableRobin $new)})}
 return [pscustomobject]@{home=$fixtureHome;job=$job;run_id=$runId;directory=$run;backup=$backup;state=$state;backup_path=$backupPath;owner=$owner;owner_bytes=[byte[]]$ownerBytes;old=$old;new=$new}
}
function Recover($Fixture){return Restore-AgentPadMain $Fixture.home $Fixture.job.job_id $Fixture.run_id $Fixture.state.backup_sha256}
foreach($phase in @('deleted','pasted','saving','ready')){
 $f=New-Fixture 'normal' $phase;$hash=Get-AgentHash $f.backup_path;$result=Recover $f
 Check ($result.status -ceq 'restored' -and $script:main -ceq $f.old -and $script:saves -eq 1 -and $script:runs -eq 0) ('Restore known '+$phase+' with Save and zero Run')
 Check (([Convert]::ToBase64String([IO.File]::ReadAllBytes($f.owner))) -ceq ([Convert]::ToBase64String($f.owner_bytes))) 'Original owner bytes including BOM and whitespace preserved'
 Check ((Get-AgentHash $f.backup_path) -ceq $hash -and $script:clipboard -ceq 'original user clipboard') 'Backup unchanged and clipboard restored'
 $beforeEdits=$script:edits;$again=Recover $f;Check ($again.status -ceq 'restored' -and $script:edits -eq $beforeEdits) 'Repeated recovery does not repeat UI edits'
}
$f=New-Fixture 'new_owner' 'owner_writing';$result=Recover $f;Check ($result.owner_restored -and (Get-AgentHash $f.owner) -ceq $f.backup.owner_sha256) 'App-written new owner rolls back to original bytes'
$f=New-Fixture 'normal' 'saving' -EmptyOriginal;$result=Recover $f;Check ($script:main -ceq '' -and -not [IO.File]::Exists($f.owner) -and $script:runs -eq 0) 'Empty original restored without adding an owner record'
foreach($scenario in @('user_edited','other_window','running','owner_changed','started','pending_paste','live_controller','bad_owner_backup','bad_state_type')){
 $phase=if($scenario -ceq 'pending_paste'){'paste_requested'}else{'saving'};$f=New-Fixture $scenario $phase
 if($scenario -ceq 'owner_changed'){[IO.File]::WriteAllText($f.owner,'user owner edit')}
 if($scenario -ceq 'started'){$f.state.execution_reserved=$true}
 if($scenario -ceq 'bad_state_type'){$f.state.execution_reserved='false'}
 if($scenario -ceq 'live_controller'){$f.backup.controller_pid=$PID;$f.backup.controller_started=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o')}
 if($scenario -ceq 'bad_owner_backup'){$f.backup.owner_base64='invalid!'}
 if($scenario -cin @('live_controller','bad_owner_backup')){Write-AgentJson $f.backup_path $f.backup;$f.state.backup_sha256=Get-AgentHash $f.backup_path}
 Write-AgentJson (Join-Path $f.directory 'pad-recovery-state.json') $f.state
 $originalMain=$script:main;$ownerHash=Get-AgentHash $f.owner;$message='';try{Recover $f|Out-Null}catch{$message=$_.Exception.Message}
 Check ($message -like 'PAD_RECOVERY*' -and $script:edits -eq 0 -and $script:saves -eq 0 -and $script:runs -eq 0) ('Reject '+$scenario+' without UI writes')
 Check ($script:main -ceq $originalMain -and (Get-AgentHash $f.owner) -ceq $ownerHash) 'Refusal preserves Main and owner'
}
$f=New-Fixture 'save_failure';$message='';try{Recover $f|Out-Null}catch{$message=$_.Exception.Message};Check ($message -like 'PAD_RECOVERY_FAILED:*' -and -not (Read-AgentJson (Join-Path $f.directory 'pad-recovery-state.json')).restored -and $script:runs -eq 0) 'Failed Save cannot report restoration complete'
$f=New-Fixture 'clipboard_failure';$result=Recover $f;Check ($result.status -ceq 'restored' -and $result.clipboard_status -ceq 'restore_failed' -and $script:runs -eq 0) 'Clipboard failure is reported independently from restored Main'
$f=New-Fixture 'user_same_text';$message='';try{Recover $f|Out-Null}catch{$message=$_.Exception.Message};Check ($script:flavor -ceq 'user RTF' -and $script:restores -eq 0 -and $message -like 'PAD_RECOVERY_FAILED:*') 'Same-text foreign clipboard sequence is not overwritten'
$f=New-Fixture 'normal';$view=Get-AgentPadRecoveryView $f.home $f.job;Check ($view.required -and $view.can_attempt -and $view.run_id -ceq $f.run_id) 'Recovery view is attached to the latest run'
$f.job | Add-Member preservation ([pscustomobject]@{warnings=@('元処理でクリップボードを復元できませんでした。')})
Write-AgentJson (Join-Path (Get-AgentJobDirectory $f.home $f.job.job_id) 'job.json') $f.job
$result=Invoke-AgentPadRecoveryRequest $f.home $f.job.job_id $f.run_id $f.state.backup_sha256;$job=Get-AgentJob $f.home $f.job.job_id
Check (-not $job.recovery_required -and $job.preservation.main_status -ceq 'restored' -and $job.status -ceq 'blocked') 'Server clears the recovery gate without rerunning the original job'
Check ([IO.File]::Exists($f.backup_path) -and $script:runs -eq 0) 'Recovery retains evidence and performs no Run'
Check ($job.preservation.warnings -contains '元処理でクリップボードを復元できませんでした。') 'Later Main recovery never erases an earlier clipboard preservation warning'
$f=New-Fixture 'partial_output';$script:partialOutput=Join-Path $f.directory 'artifacts\partial.txt';[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($script:partialOutput))
$script:outsideOutput=Join-Path $root 'outside.txt';[IO.File]::WriteAllText($script:outsideOutput,'outside input')
function Invoke-AgentPadCore($Robin,$RunDirectory,$RunId,$Job,$Settings,$CancelPath,$Preservation){[IO.File]::WriteAllText($script:partialOutput,'partial output');$Preservation.declared_outputs=@($script:partialOutput,$script:outsideOutput);return @{status='failed';error='Synthetic runtime failure';artifacts=@()}}
$partial=Invoke-AgentPad 'WAIT 0' $f.directory $f.run_id $f.job ([pscustomobject]@{pad_flow_name='TEST ONLY'}) ''
Check ($partial.partial_artifacts.Count -eq 1 -and $partial.partial_artifacts[0].path -ceq $script:partialOutput -and $partial.partial_artifacts[0].state -ceq 'unverified') 'Failed execution lists only in-scope partial files as unverified'
Check ($partial.status -ceq 'failed' -and $partial.artifacts.Count -eq 0 -and [IO.File]::ReadAllText($script:outsideOutput) -ceq 'outside input') 'Partial file listing never promotes failure or changes input'
Write-Output "PASS: $script:checks PAD recovery policy/file checks; mocked UI/clipboard, no native PAD actions. Evidence: $root"
