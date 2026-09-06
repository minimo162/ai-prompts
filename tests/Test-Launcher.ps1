param([string]$SourceDirectory)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0
if([string]::IsNullOrWhiteSpace($SourceDirectory)){$SourceDirectory=Join-Path $PSScriptRoot '..'}
$SourceDirectory=[IO.Path]::GetFullPath($SourceDirectory)
$script:checks=0
function Assert-Case([bool]$Actual,[string]$Name) {
    if(-not $Actual){throw ('FAIL: '+$Name)}
    $script:checks++
}
function Invoke-TestChild([string]$Executable,[string]$Arguments,[string]$Directory,[hashtable]$Environment) {
    $info=New-Object Diagnostics.ProcessStartInfo
    $info.FileName=$Executable;$info.Arguments=$Arguments;$info.WorkingDirectory=$Directory
    $info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden
    $info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true;$info.RedirectStandardInput=$true
    foreach($key in $Environment.Keys){$info.EnvironmentVariables[$key]=[string]$Environment[$key]}
    $process=New-Object Diagnostics.Process
    $process.StartInfo=$info
    try {
        $null=$process.Start()
        $stdout=$process.StandardOutput.ReadToEndAsync();$stderr=$process.StandardError.ReadToEndAsync()
        # The shipped CMD pauses on failure; redirected input completes it without UI.
        $process.StandardInput.WriteLine('');$process.StandardInput.Close()
        if(-not $process.WaitForExit(30000)){$process.Kill();$process.WaitForExit();throw 'Test child process timed out.'}
        return [pscustomobject]@{exit_code=$process.ExitCode;stdout=$stdout.Result;stderr=$stderr.Result}
    } finally {$process.Dispose()}
}

$workRoot=[IO.Path]::GetFullPath((Join-Path $SourceDirectory '.work'))
$temp=Join-Path $workRoot ('launcher-tests-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory($temp)
$encoding=New-Object Text.UTF8Encoding($true)
$nativePs=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$nativeModules=Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\Modules'
$runtimePath=$null;$serverStopped=$true
$originalModulePath=$env:PSModulePath
try {
    $releaseSource=Join-Path $temp 'real release with spaces'
    $otherDirectory=Join-Path $temp 'unrelated working directory'
    $realLocal=Join-Path $temp 'real-localappdata'
    foreach($directory in @($releaseSource,$otherDirectory,$realLocal)){[IO.Directory]::CreateDirectory($directory)|Out-Null}
    # Freeze the real three-file distribution. No functions are replaced or mocked.
    foreach($file in @('App.ps1','index.html','業務エージェント.cmd')) {
        [IO.File]::Copy((Join-Path $SourceDirectory $file),(Join-Path $releaseSource $file),$false)
    }
    $realHome=Join-Path $realLocal 'AiPromptsAgent'
    $runtimePath=Join-Path $realHome 'data\server.json'
    $arguments='-NoProfile -NonInteractive -ExecutionPolicy Bypass -STA -File "'+(Join-Path $releaseSource 'App.ps1')+'" -Mode Bootstrap -NoBrowser'
    $serverStopped=$false
    $child=Invoke-TestChild $nativePs $arguments $otherDirectory @{LOCALAPPDATA=$realLocal;PSModulePath=$nativeModules}
    Assert-Case ($child.exit_code -eq 0) ('Real PS5 -File Bootstrap succeeds without SourcePath: '+$child.stderr+$child.stdout)
    $pointerPath=Join-Path $realHome 'app\current.json'
    Assert-Case ([IO.File]::Exists($pointerPath) -and [IO.File]::Exists($runtimePath)) 'Real Bootstrap creates a local release pointer and running server metadata'
    $pointer=[IO.File]::ReadAllText($pointerPath,[Text.Encoding]::UTF8)|ConvertFrom-Json
    $runtime=[IO.File]::ReadAllText($runtimePath,[Text.Encoding]::UTF8)|ConvertFrom-Json
    $cachedDirectory=Join-Path $realHome ('app\'+$pointer.release)
    Assert-Case ($runtime.app_path -ceq (Join-Path $cachedDirectory 'App.ps1')) 'Real server runs the immutable local release'
    foreach($file in @('App.ps1','index.html','業務エージェント.cmd')) {
        Assert-Case ((Get-FileHash -LiteralPath (Join-Path $cachedDirectory $file) -Algorithm SHA256).Hash -ceq (Get-FileHash -LiteralPath (Join-Path $releaseSource $file) -Algorithm SHA256).Hash) ('Real cached release preserves '+$file)
    }
    $state=Invoke-RestMethod -Uri ('http://127.0.0.1:'+$runtime.port+'/api/state') -Headers @{'X-App-Token'=$runtime.token} -TimeoutSec 5
    Assert-Case ($state.ok -eq $true -and $null -eq $state.job) 'Real loopback server returns authenticated idle state without opening a browser'

    # These next cases run the shipped CMD unchanged, with an INERT App fixture.
    # They verify its shell/runtime environment and exit behavior, not app startup.
    $fixture=Join-Path $temp 'cmd fixture with spaces'
    $fakeBin=Join-Path $temp 'fake-path-bin'
    $poisonModules=Join-Path $temp 'inherited-non-native-modules'
    $fixtureLocal=Join-Path $temp 'fixture-localappdata'
    foreach($directory in @($fixture,$fakeBin,$poisonModules,$fixtureLocal)){[IO.Directory]::CreateDirectory($directory)|Out-Null}
    [IO.File]::Copy((Join-Path $SourceDirectory '業務エージェント.cmd'),(Join-Path $fixture '業務エージェント.cmd'),$false)
    $fixtureScript=@'
param([string]$Mode,[string]$SourcePath)
$ErrorActionPreference='Stop'
$hash=Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256
$probe=[ordered]@{mode=$Mode;source=$SourcePath;major=$PSVersionTable.PSVersion.Major;minor=$PSVersionTable.PSVersion.Minor;edition=$PSVersionTable.PSEdition;ps_home=$PSHOME;module_path=$env:PSModulePath;local_app_data=$env:LOCALAPPDATA;hash=$hash.Hash}
[IO.File]::WriteAllText($env:LAUNCHER_TEST_PROBE,($probe|ConvertTo-Json -Compress),(New-Object Text.UTF8Encoding($false)))
if($env:LAUNCHER_TEST_FAILURE -eq '1'){throw 'CONTROLLED_INERT_APP_FAILURE'}
'@
    [IO.File]::WriteAllText((Join-Path $fixture 'App.ps1'),$fixtureScript,$encoding)
    [IO.File]::WriteAllText((Join-Path $fixture 'App.ps1'),("# App-Version: 0.1.0`r`n"+$fixtureScript),$encoding)
    [IO.File]::WriteAllText((Join-Path $fixture 'index.html'),'<meta name="app-version" content="0.1.0">',$encoding)
    . (Join-Path $PSScriptRoot 'ReleaseFixture.ps1')
    Set-TestReleaseBinding $fixture
    [IO.File]::WriteAllText((Join-Path $fakeBin 'powershell.cmd'),"@echo off`r`necho wrongly-resolved>%LAUNCHER_TEST_SPY_FILE%`r`nexit /b 99`r`n",[Text.Encoding]::ASCII)
    $spy=Join-Path $temp 'wrong-powershell-used.txt'
    $probePath=Join-Path $temp 'cmd-probe.json'
    foreach($fail in @('0','1')) {
        [IO.File]::Delete($probePath)
        $childEnvironment=@{LOCALAPPDATA=$fixtureLocal;PSModulePath=$poisonModules;PATH=($fakeBin+';'+$env:PATH);LAUNCHER_TEST_PROBE=$probePath;LAUNCHER_TEST_FAILURE=$fail;LAUNCHER_TEST_SPY_FILE=$spy}
        $cmdArguments='/d /s /c ""'+(Join-Path $fixture '業務エージェント.cmd')+'""'
        $cmdResult=Invoke-TestChild (Join-Path $env:SystemRoot 'System32\cmd.exe') $cmdArguments $otherDirectory $childEnvironment
        $expected=if($fail -eq '1'){1}else{0}
        Assert-Case ($cmdResult.exit_code -eq $expected) ('Shipped CMD preserves inert App exit after pause; failure='+$fail+'; '+$cmdResult.stdout+$cmdResult.stderr)
        Assert-Case ([IO.File]::Exists($probePath) -and -not [IO.File]::Exists($spy)) 'Shipped CMD invokes the explicit native PowerShell executable'
        $probe=[IO.File]::ReadAllText($probePath,[Text.Encoding]::UTF8)|ConvertFrom-Json
        Assert-Case ($probe.major -eq 5 -and $probe.minor -eq 1 -and $probe.edition -ceq 'Desktop') 'Inert CMD fixture executes on Windows PowerShell 5.1'
        Assert-Case ($probe.module_path -cnotmatch [regex]::Escape($poisonModules) -and $probe.module_path -match [regex]::Escape($nativeModules) -and $probe.hash -match '^[A-Fa-f0-9]{64}$') 'Shipped CMD resets inherited module pollution and Get-FileHash is available'
        Assert-Case ($probe.mode -ceq 'Bootstrap' -and $probe.source.TrimEnd('\') -ceq $fixture -and $probe.local_app_data -ceq $fixtureLocal) 'Shipped CMD passes its own source directory and preserves isolated LOCALAPPDATA'
    }
    Assert-Case ($env:PSModulePath -ceq $originalModulePath) 'Launcher tests do not change the calling process module environment'
} finally {
    # Shut down only the authenticated server whose identity belongs to this test.
    if($runtimePath -and [IO.File]::Exists($runtimePath)) {
        $ownedRuntime=[IO.File]::ReadAllText($runtimePath,[Text.Encoding]::UTF8)|ConvertFrom-Json
        $ownedApp=[IO.Path]::GetFullPath([string]$ownedRuntime.app_path)
        if(-not $ownedApp.StartsWith($temp+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Test cleanup refused a server outside its own directory.'}
        $ownedProcess=Get-Process -Id $ownedRuntime.pid -ErrorAction SilentlyContinue
        if($ownedProcess) {
            if($ownedProcess.StartTime.ToUniversalTime().ToString('o') -cne $ownedRuntime.started -or $ownedProcess.Path -ine $nativePs){throw 'Test cleanup refused a server with a changed process identity.'}
            try {$null=Invoke-RestMethod -Uri ('http://127.0.0.1:'+$ownedRuntime.port+'/api/restart') -Method Post -ContentType 'application/json' -Body '{}' -Headers @{'X-App-Token'=$ownedRuntime.token} -TimeoutSec 5} catch {}
            if(-not $ownedProcess.WaitForExit(5000)){Stop-Process -InputObject $ownedProcess -Force;$ownedProcess.WaitForExit()}
            $ownedProcess.Dispose()
        }
        $serverStopped=$true
    } elseif(-not [IO.File]::Exists((Join-Path $temp 'real-localappdata\AiPromptsAgent\app\current.json'))) {$serverStopped=$true}
    $resolved=[IO.Path]::GetFullPath($temp)
    if(-not $resolved.StartsWith($workRoot+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Unsafe launcher test cleanup path.'}
    if($serverStopped -and (Test-Path -LiteralPath $resolved)){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
Write-Output ('PASS: '+$script:checks+' launcher checks. Real PS5 Bootstrap/loopback exercised with -NoBrowser; CMD environment/exit checks used an inert App fixture. No browser, PAD or M365 was opened.')
