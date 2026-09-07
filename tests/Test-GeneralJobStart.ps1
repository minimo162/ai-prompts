$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library -OfflineTest
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\general-start-'+[guid]::NewGuid().ToString('N'))));$null=Initialize-AgentHome $root
$input=Join-Path $root 'source.txt';[IO.File]::WriteAllText($input,'synthetic')
$connection=Join-Path $root ('data\jobs\'+('a'*32)+'\copilot-conversations\'+('b'*32)+'\target.json')
Write-AgentJson $connection @{id='synthetic-target'};$before=Get-AgentHash $connection;$script:starts=0
function Start-AgentProcess {$script:starts++;return [pscustomobject]@{Id=2147483647;StartTime=[datetime]::UtcNow}}
$job=New-AgentJob $root 'synthetic request' $input
if($job.status -cne 'queued' -or $script:starts -ne 1){throw 'New general job did not start'}
if((Get-AgentHash $connection) -cne $before){throw 'Connection evidence was modified'}
if((Get-AgentJobHistory $root).Count -ne 1){throw 'Connection-only directory entered job history'}
foreach($status in @('queued','unknown')){
 $job.status=$status;Save-AgentJob (Get-AgentJobDirectory $root $job.job_id) $job
 $message='';try{$null=New-AgentJob $root 'duplicate' $input}catch{$message=$_.Exception.Message}
 if($message -notlike 'BUSY:*' -or $script:starts -ne 1){throw ('Existing job not blocked: '+$status)}
}
Write-Output 'PASS: general start tolerates connection-only state, preserves evidence, and blocks queued/unknown jobs. No provider/PAD/worker invoked.'
