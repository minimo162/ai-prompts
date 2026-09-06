# Managed clipboard data only: this test never reads or writes the OS clipboard.
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library
$checks=0
function Assert-Snapshot([bool]$Condition,[string]$Name){if(-not $Condition){throw ('FAIL: '+$Name)};$script:checks++}

$source=New-Object Windows.Forms.DataObject
$text="  日本語 %Value% C:\literal\n`n"
$bytes=[byte[]]@(1,2,3)
$stream=New-Object IO.MemoryStream -ArgumentList (,[byte[]]@(4,5,6))
$stream.Position=1
$bitmap=New-Object Drawing.Bitmap(1,1)
$bitmap.SetPixel(0,0,[Drawing.Color]::Red)
$snapshot=$null
try{
    $source.SetData('UnicodeText',$false,$text)
    $source.SetData('HTML Format',$false,'<b>Sample</b>')
    $source.SetData('Agent.Bytes',$false,$bytes)
    $source.SetData('Agent.Stream',$false,$stream)
    $source.SetData('Bitmap',$false,$bitmap)
    $snapshot=Copy-AgentPadClipboardSnapshot $source
    Assert-Snapshot (@(Compare-Object @($source.GetFormats($false)) @($snapshot.GetFormats($false))).Count -eq 0) 'All native formats are retained'
    $source.SetData('UnicodeText',$false,'replacement')
    $source.SetData('HTML Format',$false,'replacement')
    $bytes[0]=99
    $stream.Position=0;$stream.WriteByte(99)
    $bitmap.SetPixel(0,0,[Drawing.Color]::Blue)
    Assert-Snapshot ([string]$snapshot.GetData('UnicodeText',$false) -ceq $text) 'Text remains exact after its source changes'
    Assert-Snapshot ([string]$snapshot.GetData('HTML Format',$false) -ceq '<b>Sample</b>') 'HTML is retained as data'
    Assert-Snapshot (([byte[]]$snapshot.GetData('Agent.Bytes',$false))[0] -eq 1) 'Byte arrays are detached from mutable source data'
    $savedStream=$snapshot.GetData('Agent.Stream',$false)
    Assert-Snapshot ($savedStream.ToArray()[0] -eq 4 -and $savedStream.Position -eq 1) 'Stream bytes and position are captured independently'
    Assert-Snapshot ($snapshot.GetData('Bitmap',$false).GetPixel(0,0).ToArgb() -eq [Drawing.Color]::Red.ToArgb()) 'Bitmap data is detached from the source image'
    Assert-Snapshot (@((Copy-AgentPadClipboardSnapshot $null).GetFormats($false)).Count -eq 0) 'An empty clipboard has an explicit empty snapshot'
    $unreadable=New-Object Windows.Forms.DataObject
    $unreadable.SetData('Agent.Unreadable',$false,$null)
    $errorCode=''
    try{$null=Copy-AgentPadClipboardSnapshot $unreadable}catch{$errorCode=$_.Exception.Message}
    Assert-Snapshot ($errorCode -like 'PAD_CLIPBOARD:*') 'Unreadable data is rejected instead of silently dropped'
}finally{
    $stream.Dispose();$bitmap.Dispose()
    if($snapshot){$snapshot.GetData('Agent.Stream',$false).Dispose();$snapshot.GetData('Bitmap',$false).Dispose()}
}
"PASS: $checks managed clipboard snapshot checks; no OS clipboard or PAD operations."
