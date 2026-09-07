$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../App.ps1') -Mode Library -OfflineTest
$script:reads=0;$script:case='transient';$checks=0
function Get-AgentPadClipboardTextOnce {
    $script:reads++
    if($script:case -ceq 'permanent'){throw [InvalidOperationException]::new('permanent test failure')}
    if($script:case -ceq 'exhausted' -or $script:reads -le 2){throw [Runtime.InteropServices.ExternalException]::new('clipboard busy test',-2147221040)}
    return 'exact clipboard text'
}
$value=Get-AgentPadClipboardText
if($value -cne 'exact clipboard text' -or $script:reads -ne 3){throw 'Transient reads were not recovered exactly'};$checks++
foreach($case in @('permanent','exhausted')){
    $script:case=$case;$script:reads=0;$message=''
    try{$null=Get-AgentPadClipboardText}catch{$message=$_.Exception.Message}
    $expected=if($case -ceq 'permanent'){1}else{20}
    if($message -notlike 'PAD_CLIPBOARD:*' -or $script:reads -ne $expected){throw ('Unexpected read retry policy: '+$case)};$checks++
}
Write-Output "PASS: $checks bounded clipboard read cases; no OS clipboard or input operations."
