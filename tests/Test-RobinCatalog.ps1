$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\App.ps1') -Mode Library -OfflineTest
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot ('..\.work\robin-catalog-'+[guid]::NewGuid().ToString('N'))));[void][IO.Directory]::CreateDirectory($root)
$job=[pscustomobject]@{target=$root};$checks=0
function Accept([string]$Text){$null=Test-AgentRobin $Text $root $job;$script:checks++}
function Reject([string]$Text,[string]$Code){$message='';try{$null=Test-AgentRobin $Text $root $job}catch{$message=$_.Exception.Message};if($message -notlike ($Code+':*')){throw ('Unexpected result: '+$message)};$script:checks++}
$catalog=Read-AgentJson (Join-Path $PSScriptRoot '..\catalog\index.json')
foreach($flow in $catalog.flows){
    $code=[IO.File]::ReadAllText((Join-Path $PSScriptRoot ('..\catalog\'+$flow.robin_path)));$job.target=$root
    if ((Get-AgentProperty $flow 'catalog_only' $false)) {
        if ([string]::IsNullOrWhiteSpace($code)) { throw ('Catalog-only flow is empty: ' + $flow.id) }
        $checks++
        continue
    }
    if ((Get-AgentProperty $flow 'controller_support' '') -eq 'validated_subset') {
        # Scope/lifecycle contract only. Native document contents are tested separately.
        $inputs=Join-Path $root 'document-inputs';$outputs=Join-Path $root 'artifacts'
        [void][IO.Directory]::CreateDirectory($inputs);[void][IO.Directory]::CreateDirectory($outputs)
        foreach($name in @('excel-catalog.xlsx','word-catalog.docx','powerpoint-catalog.pptx','source-a.pdf','source-b.pdf')){
            $fixture=Join-Path $inputs $name;if(-not [IO.File]::Exists($fixture)){[IO.File]::WriteAllText($fixture,'contract fixture, not a live document')}
        }
        $literal='\$\x27{3}(?:[^\x27\\\r\n]|\\[\\\x27\x22])*\x27{3}'
        $code=[regex]::Replace($code,'(DocumentPath|ExtractedPDFPath|MergedPDFPath|ImagesFolder|CSVFile): ('+$literal+')',[Text.RegularExpressions.MatchEvaluator]{param($m)
            $path=ConvertFrom-AgentRobinLiteral $m.Groups[2].Value
            return $m.Groups[1].Value+': '+(ConvertTo-AgentRobinLiteral (Join-Path $outputs ([IO.Path]::GetFileName($path))))
        })
        foreach($sourceRoot in @('C:\\Temp\\AiPromptsOfficeCatalog_20260907\\','C:\\Temp\\AiPromptsPdfCatalog_20260907\\')){$code=$code.Replace($sourceRoot,($inputs+'\').Replace('\','\\'))}
    }
    # Native PAD captures are syntax evidence, not automatic controller permission.
    if ((Get-AgentProperty $flow 'controller_support' '') -eq 'not_implemented') {
        Reject $code ROBIN_ACTION
        continue
    }
    if(Get-AgentProperty $flow 'input_scope' ''){
        # Substitute only the captured file-path literal for this local contract test.
        # The copied Robin evidence itself remains byte-identical.
        $fixture=Join-Path $root ($flow.id+'-input.txt');[IO.File]::Copy((Join-Path $PSScriptRoot ('..\catalog\'+$flow.input_fixture)),$fixture)
        $code=$code.Replace((ConvertTo-AgentRobinLiteral $flow.input_scope),(ConvertTo-AgentRobinLiteral $fixture));$job.target=$fixture
    }
    Accept $code
}
$job.target=$root
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
