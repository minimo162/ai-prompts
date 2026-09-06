param([string]$AppSourcePath='')
$ErrorActionPreference='Stop'
if(-not $AppSourcePath){$AppSourcePath=Join-Path $PSScriptRoot '..\App.ps1'}
. ([IO.Path]::GetFullPath($AppSourcePath)) -Mode Library
. (Join-Path $PSScriptRoot 'ReleaseFixture.ps1')
$script:checks=0
function Check($Condition,[string]$Name){if(-not $Condition){throw ('FAIL: '+$Name)};$script:checks++}
function Rejected([scriptblock]$Action,[string]$Prefix){$errorText='';try{& $Action|Out-Null}catch{$errorText=$_.Exception.Message};Check ($errorText -like ($Prefix+':*')) $errorText}
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\binding-'+[guid]::NewGuid().ToString('N'))));[void][IO.Directory]::CreateDirectory($root)
$names=@('App.ps1','index.html','業務エージェント.cmd')
function New-Set([string]$Name,[int]$Contract=2){
    $directory=Join-Path $root $Name;[void][IO.Directory]::CreateDirectory($directory)
    $body="# App-Version: 0.1.0`r`n# State-Contract: $Contract`r`n# Variant: $Name`r`n"+'param([string]$Mode,[string]$SourcePath)' + "`r`n"+'[IO.File]::WriteAllText($env:RELEASE_TEST_MARKER,''executed'')'+"`r`n"
    [IO.File]::WriteAllText((Join-Path $directory 'App.ps1'),$body,$script:AgentEncoding)
    [IO.File]::WriteAllText((Join-Path $directory 'index.html'),('<meta name="app-version" content="0.1.0"><p>'+ $Name +'</p>'),$script:AgentEncoding)
    [IO.File]::Copy((Join-Path ([IO.Path]::GetDirectoryName($script:AgentAppPath)) '業務エージェント.cmd'),(Join-Path $directory '業務エージェント.cmd'))
    [IO.File]::AppendAllText((Join-Path $directory '業務エージェント.cmd'),("@rem "+$Name+"`r`n"),[Text.Encoding]::ASCII)
    Set-TestReleaseBinding $directory
    return $directory
}
function Invoke-CmdProbe([string]$Directory){
    $marker=Join-Path $root ([guid]::NewGuid().ToString('N')+'.marker')
    $info=New-Object Diagnostics.ProcessStartInfo
    $info.FileName=Join-Path $env:SystemRoot 'System32\cmd.exe';$info.Arguments='/d /s /c ""'+(Join-Path $Directory '業務エージェント.cmd')+'""'
    $info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardInput=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
    $info.EnvironmentVariables['RELEASE_TEST_MARKER']=$marker
    $process=New-Object Diagnostics.Process;$process.StartInfo=$info
    try {
        [void]$process.Start();$process.StandardInput.WriteLine('');$process.StandardInput.Close()
        $out=$process.StandardOutput.ReadToEndAsync();$err=$process.StandardError.ReadToEndAsync()
        if(-not $process.WaitForExit(15000)){ $process.Kill();throw 'TEST_TIMEOUT' }
        return [pscustomobject]@{exit_code=$process.ExitCode;executed=[IO.File]::Exists($marker);output=$out.Result+$err.Result}
    }finally{$process.Dispose()}
}
$a=New-Set 'same-version-A';$b=New-Set 'same-version-B';$ra=Get-AgentRelease $a;$rb=Get-AgentRelease $b
Check ($ra.version -ceq $rb.version -and $ra.release -cne $rb.release) 'Same version has different content-bound identities'
$hash=Get-AgentHash (Join-Path $a 'App.ps1');Set-TestReleaseBinding $a
Check ((Get-AgentHash (Join-Path $a 'App.ps1')) -ceq $hash) 'Sealing unchanged bytes is reproducible'
$valid=Invoke-CmdProbe $a;Check ($valid.exit_code -eq 0 -and $valid.executed) ('Bound native CMD executes inert App: '+$valid.output)
foreach($name in $names){
    $mix=Join-Path $root ([guid]::NewGuid().ToString('N'));[void][IO.Directory]::CreateDirectory($mix)
    foreach($file in $names){[IO.File]::Copy((Join-Path $a $file),(Join-Path $mix $file))}
    [IO.File]::Copy((Join-Path $b $name),(Join-Path $mix $name),$true)
    Rejected {Get-AgentRelease $mix} INVALID_RELEASE
    $probe=Invoke-CmdProbe $mix;Check ($probe.exit_code -ne 0 -and -not $probe.executed -and $probe.output.Contains('INVALID_RELEASE')) ('Native CMD rejects mixed '+$name+' before App code')
}
[IO.File]::AppendAllText((Join-Path $a 'App.ps1'),"`r`n# mutation")
Rejected {Get-AgentRelease $a} INVALID_RELEASE
$probe=Invoke-CmdProbe $a;Check (-not $probe.executed -and $probe.exit_code -ne 0) 'Changed App payload cannot execute'
Set-TestReleaseBinding $a;$ra=Get-AgentRelease $a
$testHome=Initialize-AgentHome (Join-Path $root 'home');$cachedA=Sync-AgentRelease $testHome $a;$cachedB=Sync-AgentRelease $testHome $b
$jobId=[guid]::NewGuid().ToString('N');$jobDir=Get-AgentJobDirectory $testHome $jobId
Write-AgentJson (Join-Path $jobDir 'job.json') @{schema_version=2;workflow='csv_classify';status='done';plan=@{action_contract=2};job_id=$jobId}
[IO.File]::WriteAllText((Join-Path $jobDir 'run.claim'),'keep completed execution claim')
$keep=Join-Path $testHome 'data\original.csv';[IO.File]::WriteAllText($keep,'001,original')
$dataHashes=@(Get-ChildItem (Join-Path $testHome 'data') -File -Recurse | ForEach-Object { [pscustomobject]@{path=$_.FullName;hash=Get-AgentHash $_.FullName} })
$old=New-Set 'old-state-contract' 1;$oldRelease=Get-AgentRelease $old;$oldCache=Join-Path $testHome ('app\'+$oldRelease.release);[void][IO.Directory]::CreateDirectory($oldCache)
foreach($name in $names){[IO.File]::Copy((Join-Path $old $name),(Join-Path $oldCache $name))}
Rejected {Set-AgentRollback $testHome $oldRelease.release $rb.release} ROLLBACK_SCHEMA
Check (-not @((Get-AgentLocalReleases $testHome).releases | Where-Object release -CEQ $oldRelease.release)[0].compatible) 'Incompatible state is disabled in choices'
Rejected {Set-AgentRollback $testHome $ra.release ('0.1.0-'+('0'*64))} ROLLBACK_CHANGED
$selection=Set-AgentRollback $testHome $ra.release $rb.release
Check ($selection.rollback_hold -and (Get-AgentCachedRelease $testHome) -ceq $cachedA) 'Explicit rollback selects exact old package'
Check ((Sync-AgentRelease $testHome $b -WarningAction SilentlyContinue) -ceq $cachedA) 'New shared set does not override rollback pin'
Rejected {Assert-AgentRollbackRuntime $testHome} RESTART_REQUIRED
foreach($entry in $dataHashes){Check ((Get-AgentHash $entry.path) -ceq $entry.hash) 'Rollback preserves data bytes'}
Clear-AgentRollbackHold $testHome $ra.release
Check ((Sync-AgentRelease $testHome $b) -ceq $cachedB) 'Explicit unpin permits normal update'
$job=Read-AgentJson (Join-Path $jobDir 'job.json');$job.status='unknown';Write-AgentJson (Join-Path $jobDir 'job.json') $job
Rejected {Set-AgentRollback $testHome $ra.release $rb.release} BUSY
$job.status='done';$job.schema_version=99;Write-AgentJson (Join-Path $jobDir 'job.json') $job
Rejected {Set-AgentRollback $testHome $ra.release $rb.release} ROLLBACK_SCHEMA
Check ((Get-AgentCachedRelease $testHome) -ceq $cachedB) 'Refused rollback preserves current pointer'
## An old, unsealed but pointer-verified cache is inspected only to permit a sealed upgrade.
$legacy=Join-Path $root 'legacy';[void][IO.Directory]::CreateDirectory($legacy)
[IO.File]::WriteAllText((Join-Path $legacy 'App.ps1'),"# App-Version: 0.1.0`r`n# Legacy inert payload",$script:AgentEncoding)
[IO.File]::WriteAllText((Join-Path $legacy 'index.html'),'<meta name="app-version" content="0.1.0">',$script:AgentEncoding)
[IO.File]::WriteAllText((Join-Path $legacy '業務エージェント.cmd'),'@rem legacy',[Text.Encoding]::ASCII)
$legacyId=Get-AgentReleaseFileIdentity $legacy
$legacyHome=Initialize-AgentHome (Join-Path $root 'legacy-home');$legacyCache=Join-Path $legacyHome ('app\'+$legacyId.release);[void][IO.Directory]::CreateDirectory($legacyCache)
foreach($name in $names){[IO.File]::Copy((Join-Path $legacy $name),(Join-Path $legacyCache $name))}
Write-AgentJson (Join-Path $legacyHome 'app\current.json') @{version=$legacyId.version;release=$legacyId.release;app_sha256=$legacyId.hashes.'App.ps1'}
[IO.File]::WriteAllText((Join-Path $legacyHome 'data\preserved.txt'),'legacy data')
Rejected {Get-AgentCachedRelease $legacyHome} INVALID_RELEASE
Check ((Get-AgentPreviousReleaseForUpgrade $legacyHome).release -ceq $legacyId.release) 'Legacy identity is verified without granting launch authority'
$upgraded=Sync-AgentRelease $legacyHome $b
Check ((Get-AgentRelease $upgraded).release -ceq $rb.release) 'Sealed upgrade works from previous unsealed cache'
foreach($name in $names){Check ((Get-AgentHash (Join-Path $legacyCache $name)) -ceq $legacyId.hashes.$name) 'Legacy package is retained byte-for-byte'}
Check ([IO.File]::ReadAllText((Join-Path $legacyHome 'data\preserved.txt')) -ceq 'legacy data') 'Upgrade preserves legacy data'
Check (@((Get-AgentLocalReleases $legacyHome).releases | Where-Object release -CEQ $legacyId.release).Count -eq 0) 'Unsealed old cache is not advertised as a rollback choice'
Write-AgentJson (Join-Path $legacyHome 'app\current.json') @{version=$legacyId.version;release=$legacyId.release;app_sha256=$legacyId.hashes.'App.ps1'}
[IO.File]::AppendAllText((Join-Path $legacyCache 'index.html'),'tampered')
Rejected {Sync-AgentRelease $legacyHome $b} INVALID_RELEASE
$versionDir=Join-Path $root 'version-change';[void][IO.Directory]::CreateDirectory($versionDir)
foreach($name in $names){[IO.File]::Copy((Join-Path ([IO.Path]::GetDirectoryName($script:AgentAppPath)) $name),(Join-Path $versionDir $name))}
$versionApp=Join-Path $versionDir 'App.ps1';$versionHtml=Join-Path $versionDir 'index.html'
[IO.File]::WriteAllText($versionApp,([IO.File]::ReadAllText($versionApp,[Text.Encoding]::UTF8).Replace('# App-Version: 0.1.0','# App-Version: 0.9.0')),(New-Object Text.UTF8Encoding($true)))
[IO.File]::WriteAllText($versionHtml,([IO.File]::ReadAllText($versionHtml,[Text.Encoding]::UTF8).Replace('content="0.1.0"','content="0.9.0"')),$script:AgentEncoding)
Set-TestReleaseBinding $versionDir
$versionProbe=Join-Path $root 'version-probe.ps1';$versionResult=Join-Path $root 'version-result.json'
[IO.File]::WriteAllText($versionProbe,'param($VersionAppPath,$ProbePath); . $VersionAppPath -Mode Library; Write-AgentJson $ProbePath @{runtime_version=$script:AgentVersion;declared_version=(Get-AgentRuntimeRelease).version}',(New-Object Text.UTF8Encoding($true)))
$versionProcess=Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "'+$versionProbe+'" -VersionAppPath "'+$versionApp+'" -ProbePath "'+$versionResult+'"') -WindowStyle Hidden -Wait -PassThru
$versionValue=Read-AgentJson $versionResult
Check ($versionProcess.ExitCode -eq 0 -and $versionValue.runtime_version -ceq '0.9.0' -and $versionValue.declared_version -ceq '0.9.0') 'Runtime version follows the sealed declaration in a real PS5 import'
Check (-not (Get-AgentStorageStatus $testHome).automatic_deletion) 'Storage policy never silently removes versions or user data'
function Get-AgentStorageStatus([string]$HomePath){return @{available_bytes=0;minimum_start_bytes=268435456}}
Rejected {Assert-AgentStorageCapacity $testHome} STORAGE_FULL
Check ([IO.File]::ReadAllText((Join-Path $jobDir 'run.claim')) -ceq 'keep completed execution claim' -and [IO.File]::ReadAllText($keep) -ceq '001,original') 'Low-capacity refusal preserves claim and input'
Write-Output "PASS: $script:checks binding/rollback checks; native CMD used inert Apps, no service/UI/PAD. Evidence: $root"
