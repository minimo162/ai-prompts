$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library -OfflineTest
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\robin-catalog-'+[guid]::NewGuid().ToString('N'))));[void][IO.Directory]::CreateDirectory($root)
$job=[pscustomobject]@{target=$root};$checks=0
function Accept([string]$Text){$null=Test-AgentRobin $Text $root $job;$script:checks++}
function Reject([string]$Text,[string]$Code){$message='';try{$null=Test-AgentRobin $Text $root $job}catch{$message=$_.Exception.Message};if($message -notlike ($Code+':*')){throw ('Unexpected result: '+$message)};$script:checks++}
$catalog=Read-AgentJson (Join-Path $PSScriptRoot '..\catalog\index.json')
foreach($flow in $catalog.flows){Accept ([IO.File]::ReadAllText((Join-Path $PSScriptRoot ('..\catalog\'+$flow.robin_path))))}
$generated=[IO.File]::ReadAllText((Join-Path $PSScriptRoot '..\catalog\generated\list-and-regex\generated.robin'))
Accept $generated
$list='Variables.CreateNewList List=> Items'
# Literal construction is explicit so test source quoting does not transform Robin.
$q='$'+"'''";$end="'''";$add='Variables.AddItemToList Item: '+$q+'checked'+$end+' List: Items'
$set='SET TextValue TO '+$q+'Ticket 742 ready'+$end
$replace='Text.Replace.ReplaceTextWithRegex Text: TextValue TextToFind: '+$q+'\\d+'+$end+' IgnoreCase: False ReplaceWith: '+$q+'ID'+$end+' ActivateEscapeSequences: False Result=> CleanText'
Accept ($list+"`n"+$add+"`n"+$set+"`n"+$replace)
Reject $add ROBIN_VARIABLE
Reject ('SET Items TO '+$q+'text'+$end+"`n"+$add) ROBIN_TYPE
Reject ('Variables.CreateNewList List=> TextValue'+"`n"+$replace) ROBIN_TYPE
Reject $replace ROBIN_VARIABLE
Reject ($set+"`n"+$replace.Replace('TextValue TextToFind','Missing TextToFind')) ROBIN_VARIABLE
Reject ($set+"`n"+$replace.Replace('WithRegex','')) ROBIN_ACTION
Reject ($set+"`n"+$replace.Replace(' Result=>',' ComparisonType: Text.TextComparisonType.CultureSensitive Result=>')) ROBIN_ACTION
Reject ($set+"`n"+$replace.Replace('ActivateEscapeSequences: False','ActivateEscapeSequences: True')) ROBIN_ACTION
Reject ($set+"`n"+$replace.Replace('ID'+$end,'%Missing%'+$end)) ROBIN_VARIABLE
Reject ($set+"`n"+$replace.Replace('ID'+$end,'%TextValue.Length%'+$end)) ROBIN_EXPRESSION
Accept ('SET Escaped TO '+$q+'100%% %%Missing%%'+$end)
Reject ('SET Escaped TO '+$q+'100%'+$end) ROBIN_EXPRESSION
$condition='IF TextValue = '+$q+'yes'+$end+' THEN'
Reject ($set+"`n"+$condition+"`n    "+$list+"`nEND`n"+$add) ROBIN_VARIABLE
Reject ($set+"`n"+$list+"`n"+$condition+"`n    SET Items TO "+$q+'text'+$end+"`nEND`n"+$add) ROBIN_TYPE
Accept ($set+"`n"+$condition+"`n    "+$list+"`nELSE`n    "+$list+"`nEND`n"+$add)
Reject ($set+"`n"+$condition+"`n    "+$list+"`nELSE`n    SET Items TO "+$q+'text'+$end+"`nEND`n"+$add) ROBIN_TYPE
$split=[IO.File]::ReadAllText((Join-Path $PSScriptRoot '..\catalog\actions\text-split\custom-comma.robin'))
$join=[IO.File]::ReadAllText((Join-Path $PSScriptRoot '..\catalog\actions\text-join\custom-pipe.robin'))
$spaceSplit=[IO.File]::ReadAllText((Join-Path $PSScriptRoot '..\catalog\actions\text-split\standard-space.robin'))
Accept ($split+$join)
Accept ($split+$join+$replace.Replace('Text: TextValue','Text: JoinedText'))
Reject $join ROBIN_VARIABLE
Reject ('SET TextList TO '+$q+'text'+$end+"`n"+$join) ROBIN_TYPE
Reject ($list+"`n"+$split.Replace('Text: '+$q+'alpha,beta,gamma'+$end,'Text: Items')) ROBIN_TYPE
Reject ($split.Replace('CustomDelimiter: '+$q+','+$end,'CustomDelimiter: '+$q+' '+$end)) ROBIN_ARGUMENT
Reject ($split.Replace('IsRegEx: False','IsRegEx: True')) ROBIN_ACTION
Reject ('SET Replaced TO '+$q+'a b'+$end+"`n"+$spaceSplit.Replace('DelimiterTimes: 1','DelimiterTimes: 2')) ROBIN_ACTION
Reject ($split+$join.Replace('CustomDelimiter: '+$q+' | '+$end,'CustomDelimiter: '+$q+$end)) ROBIN_ARGUMENT
Write-Output "PASS: $checks Robin catalog checks; no PAD/Copilot invoked."
