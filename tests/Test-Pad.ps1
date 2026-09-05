param([string]$SourcePath=(Join-Path $PSScriptRoot '..\App.ps1'))
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0

# Contract tests only: AST-load production definitions, never the launcher/server,
# never initialize UI Automation, and never open or execute a PAD flow.
$sourceFiles=@([IO.Path]::GetFullPath($SourcePath))
$fragmentRoot=Join-Path ([IO.Path]::GetDirectoryName($sourceFiles[0])) '.work'
foreach($fragment in @('pad-adapter.ps1','aicall-templates.ps1')) {
    $candidate=Join-Path $fragmentRoot $fragment
    if(Test-Path -LiteralPath $candidate){$sourceFiles+=$candidate}
}
$definitions=@{}
foreach($sourceFile in $sourceFiles) {
    $parseErrors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile($sourceFile,[ref]$null,[ref]$parseErrors)
    if($parseErrors.Count){throw ('PowerShell parse errors in '+$sourceFile+': '+$parseErrors.Count)}
    foreach($definition in @($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$false))) {
        # The assembled app is authoritative; fragments support development only.
        if(-not $definitions.ContainsKey($definition.Name)){$definitions[$definition.Name]=$definition}
    }
}
$wanted=@('Test-AgentId','Assert-AgentId','Read-AgentJson','Write-AgentJson','Get-AgentProperty','Get-AgentFullPath','Assert-AgentPathUnder','Assert-AgentNoReparse','Get-AgentHash','Get-AgentVerifiedPriorArtifacts','Get-AgentTextHash','ConvertTo-AgentRobinLiteral','ConvertFrom-AgentRobinLiteral','Assert-AgentPadPath','Test-AgentRobin','ConvertTo-AgentComparableRobin','Get-AgentAiCallTemplate','New-AgentAiCallTemplates','Get-AgentPadAiResults','Test-AgentPadWindowTitle','Get-AgentPadElement','Get-AgentPadInvokableButton','Get-AgentPadStatusBar','Get-AgentPadStatus','Get-AgentPadErrorState','New-AgentPadSnapshotState','Get-AgentPadSnapshot','Wait-AgentPadEditable','Invoke-AgentPad')
foreach($name in $wanted) {
    if(-not $definitions.ContainsKey($name)){throw ('Missing production function: '+$name)}
    . ([scriptblock]::Create($definitions[$name].Extent.Text))
}
$script:AgentEncoding=New-Object Text.UTF8Encoding($false)
$script:checks=0
function Assert-Case([bool]$Actual,[string]$Name) {
    if(-not $Actual){throw ('FAIL: '+$Name)}
    $script:checks++
}
function Assert-Rejected([scriptblock]$Action,[string]$Prefix,[string]$Name) {
    $caught=$false
    try {& $Action | Out-Null} catch {
        if($_.Exception.Message -notlike ($Prefix+':*')){throw ('FAIL: '+$Name+'; unexpected error: '+$_.Exception.Message)}
        $caught=$true
    }
    Assert-Case $caught $Name
}

# Load UIA type metadata only.  The mock never references RootElement, a
# process, or an actual AutomationElement, so these tests cannot inspect PAD.
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes
if(-not ('PadResolverMockElement' -as [type])) {
    $uiaReferences=@([Windows.Automation.AutomationElement].Assembly.Location,[Windows.Automation.ControlType].Assembly.Location)
    Add-Type -ReferencedAssemblies $uiaReferences -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Windows.Automation;
public sealed class PadResolverMockCurrent {
    public string AutomationId { get; set; }
    public string Name { get; set; }
    public ControlType ControlType { get; set; }
    public bool IsEnabled { get; set; }
}
public sealed class PadResolverMockPatternCurrent { public bool IsSelected { get; set; } }
public sealed class PadResolverMockPattern { public PadResolverMockPatternCurrent Current { get; private set; } public PadResolverMockPattern(bool selected) { Current=new PadResolverMockPatternCurrent { IsSelected=selected }; } }
public sealed class PadResolverMockElement {
    public PadResolverMockCurrent Current { get; private set; }
    private readonly List<PadResolverMockElement> children = new List<PadResolverMockElement>();
    private readonly bool invokeAvailable;
    private readonly bool selected;
    public PadResolverMockElement(string id, string name, ControlType controlType, bool enabled, bool invoke, bool isSelected) {
        Current=new PadResolverMockCurrent { AutomationId=id, Name=name, ControlType=controlType, IsEnabled=enabled };
        invokeAvailable=invoke; selected=isSelected;
    }
    public void AddChild(PadResolverMockElement child) { children.Add(child); }
    private void AddDescendants(List<PadResolverMockElement> result) { foreach(var child in children) { result.Add(child); child.AddDescendants(result); } }
    public object[] FindAll(TreeScope scope, Condition condition) {
        var candidates=new List<PadResolverMockElement>();
        if(scope==TreeScope.Children) candidates.AddRange(children); else AddDescendants(candidates);
        var property=condition as PropertyCondition;
        if(property==null) return new object[0];
        var matches=new List<object>();
        foreach(var candidate in candidates) {
            bool match=false;
            if(property.Property.Id==AutomationElement.AutomationIdProperty.Id) match=Object.Equals(candidate.Current.AutomationId,property.Value);
            else if(property.Property.Id==AutomationElement.ControlTypeProperty.Id) match=candidate.Current.ControlType.Id==Convert.ToInt32(property.Value);
            if(match) matches.Add(candidate);
        }
        return matches.ToArray();
    }
    public object GetCurrentPattern(AutomationPattern pattern) {
        if(pattern==InvokePattern.Pattern && invokeAvailable) return new PadResolverMockPattern(false);
        if(pattern==SelectionItemPattern.Pattern) return new PadResolverMockPattern(selected);
        throw new InvalidOperationException("Pattern unavailable in resolver mock.");
    }
}
'@
}
function New-PadResolverElement([string]$Id,[string]$Name,[Windows.Automation.ControlType]$ControlType,[bool]$Enabled=$true,[bool]$Invoke=$true,[bool]$Selected=$false) {
    return New-Object PadResolverMockElement($Id,$Name,$ControlType,$Enabled,$Invoke,$Selected)
}
function New-PadResolverLayout([string]$StatusId='Flow_status_ready',[bool]$StartEnabled=$false,[bool]$StopEnabled=$false,[bool]$SaveEnabled=$true,[object]$ErrorText=$null,[bool]$SelectedMain=$true,[bool]$WorkspaceIsList=$true) {
    $root=New-PadResolverElement 'Root' 'mock root' ([Windows.Automation.ControlType]::Window)
    $start=New-PadResolverElement 'StartFlowButton' 'Run' ([Windows.Automation.ControlType]::Button) $StartEnabled $true
    $stopWrapper=New-PadResolverElement 'StopFlowButton' 'stop wrapper' ([Windows.Automation.ControlType]::Custom) $true $false
    $stop=New-PadResolverElement 'Button' '停止' ([Windows.Automation.ControlType]::Button) $StopEnabled $true
    $saveWrapper=New-PadResolverElement 'SaveFlowButton' 'save wrapper' ([Windows.Automation.ControlType]::Custom) $true $false
    $save=New-PadResolverElement 'Button' '保存' ([Windows.Automation.ControlType]::Button) $SaveEnabled $true
    $workspaceType=if($WorkspaceIsList){[Windows.Automation.ControlType]::List}else{[Windows.Automation.ControlType]::Pane}
    $workspace=New-PadResolverElement 'ProgramItemsListBoxActions' 'workspace' $workspaceType
    $tabs=New-PadResolverElement 'SubflowTabControl' 'tabs' ([Windows.Automation.ControlType]::Tab)
    $main=New-PadResolverElement 'MainTab' 'Main' ([Windows.Automation.ControlType]::TabItem) $true $true $SelectedMain
    $statusBar=New-PadResolverElement 'DesignerStatusBar' 'status bar' ([Windows.Automation.ControlType]::StatusBar)
    $normalStatus=New-PadResolverElement 'NormalStatusBarItem' 'normal status' ([Windows.Automation.ControlType]::Pane)
    $programDetails=New-PadResolverElement 'ProgramDetailsStatusBarItem' 'program details' ([Windows.Automation.ControlType]::Pane)
    $status=New-PadResolverElement $StatusId '状態: mock' ([Windows.Automation.ControlType]::Text) $true $false
    $stopWrapper.AddChild($stop); $saveWrapper.AddChild($save); $tabs.AddChild($main); $normalStatus.AddChild($status); $statusBar.AddChild($normalStatus); $statusBar.AddChild($programDetails)
    foreach($element in @($start,$stopWrapper,$saveWrapper,$workspace,$tabs,$statusBar)) {$root.AddChild($element)}
    if($null -ne $ErrorText) {
        $errors=New-PadResolverElement 'ErrorsStatusBarItem' 'errors' ([Windows.Automation.ControlType]::Pane)
        $count=New-PadResolverElement 'ErrorCountTextBlock' ([string]$ErrorText) ([Windows.Automation.ControlType]::Text) $true $false
        $errors.AddChild($count); $statusBar.AddChild($errors)
    }
    return [pscustomobject]@{root=$root;start=$start;stop_wrapper=$stopWrapper;stop=$stop;save_wrapper=$saveWrapper;save=$save;workspace=$workspace;tabs=$tabs;status_bar=$statusBar;normal_status=$normalStatus;program_details=$programDetails;status=$status;main=$main}
}
function New-ReadAction([string]$Path,[string]$Variable='InputText') {
    'File.ReadTextFromFile.ReadText File: '+(ConvertTo-AgentRobinLiteral $Path)+' Encoding: File.TextFileEncoding.UTF8 Content=> '+$Variable
}
function New-WriteAction([string]$Path,[string]$Value='InputText') {
    'File.WriteText File: '+(ConvertTo-AgentRobinLiteral $Path)+' TextToWrite: '+$Value+' AppendNewLine: False IfFileExists: File.IfFileExists.Append Encoding: File.FileEncoding.UTF8'
}
function Test-Flow([string]$Robin) {Test-AgentRobin -Robin $Robin -RunDirectory $script:run -Job $script:job}

# Exercise the production UIA resolvers against a closed mock tree.  The mock
# models only controls documented by the real PAD inspection; no selector is
# monkey-patched for these checks.
$resolverLayout=New-PadResolverLayout
$statusBarCondition=New-Object Windows.Automation.PropertyCondition([Windows.Automation.AutomationElement]::ControlTypeProperty,[Windows.Automation.ControlType]::StatusBar)
Assert-Case ($resolverLayout.root.FindAll([Windows.Automation.TreeScope]::Descendants,$statusBarCondition).Count -eq 1) 'Resolver mock exposes exactly one StatusBar control'
$resolvedSave=Get-AgentPadInvokableButton $resolverLayout.root 'SaveFlowButton' '保存' -Wrapped
Assert-Case ([object]::ReferenceEquals($resolvedSave,$resolverLayout.save) -and $resolverLayout.save_wrapper.Current.IsEnabled -and $resolvedSave.Current.IsEnabled) 'Save resolver returns the direct observed Button rather than its Custom wrapper'
$resolverLayout.save.Current.IsEnabled=$false
$resolvedDisabledSave=Get-AgentPadInvokableButton $resolverLayout.root 'SaveFlowButton' '保存' -Wrapped
Assert-Case (-not $resolvedDisabledSave.Current.IsEnabled -and $resolverLayout.save_wrapper.Current.IsEnabled) 'Wrapped Save enabled state comes from the child, not the always-enabled wrapper'
$resolvedStop=Get-AgentPadInvokableButton $resolverLayout.root 'StopFlowButton' '停止' -Wrapped
Assert-Case ([object]::ReferenceEquals($resolvedStop,$resolverLayout.stop)) 'Stop resolver returns the direct observed 停止 button'
$resolvedStart=Get-AgentPadInvokableButton $resolverLayout.root 'StartFlowButton'
Assert-Case ([object]::ReferenceEquals($resolvedStart,$resolverLayout.start)) 'Start resolver accepts the observed direct invokable button'
$badName=New-PadResolverLayout; $badName.save.Current.Name='別の保存'
Assert-Rejected {Get-AgentPadInvokableButton $badName.root 'SaveFlowButton' '保存' -Wrapped} 'PAD_SELECTOR' 'Wrapped Save rejects an unrelated direct child name'
$badId=New-PadResolverLayout; $badId.save.Current.AutomationId='UnexpectedButton'
Assert-Rejected {Get-AgentPadInvokableButton $badId.root 'SaveFlowButton' '保存' -Wrapped} 'PAD_SELECTOR' 'Wrapped Save rejects an unrelated direct child id'
$missingChildRoot=New-PadResolverElement 'Root' 'mock root' ([Windows.Automation.ControlType]::Window)
$missingChildWrapper=New-PadResolverElement 'SaveFlowButton' 'save wrapper' ([Windows.Automation.ControlType]::Custom) $true $false
$missingChildRoot.AddChild($missingChildWrapper)
Assert-Rejected {Get-AgentPadInvokableButton $missingChildRoot 'SaveFlowButton' '保存' -Wrapped} 'PAD_SELECTOR' 'Wrapped Save rejects a missing direct button'
$multipleChild=New-PadResolverLayout; $multipleChild.save_wrapper.AddChild((New-PadResolverElement 'Button' '保存' ([Windows.Automation.ControlType]::Button) $true $true))
Assert-Rejected {Get-AgentPadInvokableButton $multipleChild.root 'SaveFlowButton' '保存' -Wrapped} 'PAD_SELECTOR' 'Wrapped Save rejects multiple direct buttons'
$noInvokeRoot=New-PadResolverElement 'Root' 'mock root' ([Windows.Automation.ControlType]::Window)
$noInvokeRoot.AddChild((New-PadResolverElement 'StartFlowButton' 'Run' ([Windows.Automation.ControlType]::Button) $true $false))
Assert-Rejected {Get-AgentPadInvokableButton $noInvokeRoot 'StartFlowButton'} 'PAD_SELECTOR' 'Start resolver rejects a button without InvokePattern'

$status=Get-AgentPadStatus $resolverLayout.root
Assert-Case ($status.id -ceq 'Flow_status_ready' -and $status.state -ceq 'ready') 'Status resolver accepts exactly one observed ready status'
$knownStatuses=@{
    Flow_status_errors='errors'; Flow_status_runtime_error='runtime_error'; Flow_status_parsing='parsing'; Flow_status_running='running'; Flow_status_stepping='stepping'; Flow_status_stepping_over='stepping_over'; Flow_status_stepping_out='stepping_out'; Flow_status_pausing='pausing'; Flow_status_paused='paused'; Flow_status_stopping='stopping'; Flow_status_checking='checking'; Flow_status_resuming='resuming'; Flow_status_saving_process='saving'; Flow_status_saved='saved'; Flow_status_running_flow='running_flow'; Flow_status_updating='updating'; Flow_status_publishing='publishing'; Flow_status_repairing='repairing'; Flow_status_runningCUA='running_cua'
}
foreach($id in $knownStatuses.Keys) {
    $knownStatus=Get-AgentPadStatus (New-PadResolverLayout -StatusId $id).root
    Assert-Case ($knownStatus.state -ceq $knownStatuses[$id]) ('Status resolver classifies verified transient: '+$id)
}
$ambiguousStatus=New-PadResolverLayout; $ambiguousStatus.normal_status.AddChild((New-PadResolverElement 'Flow_status_saved' '状態: saved' ([Windows.Automation.ControlType]::Text) $true $false))
Assert-Rejected {Get-AgentPadStatus $ambiguousStatus.root} 'PAD_SELECTOR' 'Status resolver rejects multiple known status descendants'
$missingStatus=New-PadResolverLayout -StatusId 'Flow_status_unobserved'
Assert-Rejected {Get-AgentPadStatus $missingStatus.root} 'PAD_SELECTOR' 'Status resolver rejects an unknown or missing status id'
$badStatusName=New-PadResolverLayout; $badStatusName.status.Current.Name='Status: ready'
Assert-Rejected {Get-AgentPadStatus $badStatusName.root} 'PAD_SELECTOR' 'Status resolver requires the observed Japanese accessible-name prefix'

foreach($case in @(@{text='エラー リスト (12)';count=12;name='Japanese'},@{text='Errors list (7)';count=7;name='English'},@{text='3';count=3;name='legacy numeric'})) {
    $errorLayout=New-PadResolverLayout -ErrorText $case.text
    $errorState=Get-AgentPadErrorState $errorLayout.root $false $true
    Assert-Case ($errorState.known -and $errorState.count -eq $case.count) ('Error resolver reads '+$case.name+' BAML count format')
}
$idleNoError=Get-AgentPadErrorState $resolverLayout.root $false $true
Assert-Case ($idleNoError.known -and $idleNoError.count -eq 0) 'Absent error status is zero only for observed idle state'
$partialStatusRoot=New-PadResolverElement 'Root' 'mock root' ([Windows.Automation.ControlType]::Window)
$partialStatusBar=New-PadResolverElement 'DesignerStatusBar' 'status bar' ([Windows.Automation.ControlType]::StatusBar)
$partialStatusBar.AddChild((New-PadResolverElement 'NormalStatusBarItem' 'normal status' ([Windows.Automation.ControlType]::Pane)))
$partialStatusRoot.AddChild($partialStatusBar)
Assert-Rejected {Get-AgentPadErrorState $partialStatusRoot $false $true} 'PAD_SELECTOR' 'Absent errors cannot infer zero without the exact supported status-bar layout'
foreach($stateName in @('running','paused','stopping')) {
    $unknownError=Get-AgentPadErrorState $resolverLayout.root ($stateName -eq 'running') $false
    Assert-Case (-not $unknownError.known -and $unknownError.count -eq -1) ('Absent error status remains unknown while '+$stateName)
}

$snapshotLayout=New-PadResolverLayout
$snapshot=Get-AgentPadSnapshot $snapshotLayout.root
Assert-Case ($snapshot.idle -and $snapshot.editable -and -not $snapshot.can_run -and $snapshot.errors_known -and $snapshot.errors -eq 0 -and $snapshot.status -ceq 'ready') 'Full production snapshot accepts exact empty Main layout as idle and editable'
Assert-Case ((Wait-AgentPadEditable $snapshotLayout.root ([IO.Path]::Combine([IO.Path]::GetTempPath(),'missing-pad-cancel')) -TimeoutSeconds 1).status -ceq 'ready') 'Editable wait accepts two settled supported ready samples'
$badMain=New-PadResolverLayout -SelectedMain:$false
Assert-Rejected {Get-AgentPadSnapshot $badMain.root} 'PAD_SUBFLOW' 'Full snapshot requires the only Main subflow to be selected'
$twoMain=New-PadResolverLayout; $twoMain.tabs.AddChild((New-PadResolverElement 'OtherMainTab' 'Main' ([Windows.Automation.ControlType]::TabItem) $true $true $true))
Assert-Rejected {Get-AgentPadSnapshot $twoMain.root} 'PAD_SUBFLOW' 'Full snapshot rejects multiple Main subflow tabs'
$wrongWorkspace=New-PadResolverLayout -WorkspaceIsList:$false
Assert-Rejected {Get-AgentPadSnapshot $wrongWorkspace.root} 'PAD_SELECTOR' 'Full snapshot rejects a workspace outside the observed List control type'

# The modern title was independently observed on the real PAD designer. These
# are pure title-contract checks, not live window/process discovery evidence.
foreach($title in @('無題','無題 - Power Automate','無題* - Power Automate','Power Automate | 無題')) {
    Assert-Case (Test-AgentPadWindowTitle $title '無題') ('Dedicated PAD title form accepted: '+$title)
}
foreach($title in @('Power Automate | 別フロー','Power Automate | 無題2','Power Automate | 無題 コピー','Power Automate |  無題','Power Automate | 無題 ','prefix Power Automate | 無題','Power Automate | 無題 | suffix','Power Automate|無題','power automate | 無題','別の無題','無題2 - Power Automate','')) {
    Assert-Case (-not (Test-AgentPadWindowTitle $title '無題')) ('Different or partial PAD flow title rejected: '+$title)
}
Assert-Case (-not (Test-AgentPadWindowTitle 'Power Automate | Untitled' 'untitled')) 'Observed modern title requires exact flow-name case'
Assert-Case (-not (Test-AgentPadWindowTitle 'Power Automate | ' '')) 'Empty dedicated flow name rejected by pure title guard'
foreach($title in @('無題 - 別フロー','無題* - 別フロー','無題 - Power Automate suffix','無題* - Power Automate suffix')) {
    Assert-Case (-not (Test-AgentPadWindowTitle $title '無題')) ('Legacy title cannot adopt arbitrary suffix or another flow: '+$title)
}
foreach($title in @('Untitled','Untitled - Power Automate','Untitled* - Power Automate')) {
    Assert-Case (-not (Test-AgentPadWindowTitle $title 'untitled')) 'Every legacy form requires exact flow-name case'
}

# These are the production state rules used after UIA has resolved the exact
# observed controls.  An empty Main is editable even though PAD disables Run.
$emptyState=New-AgentPadSnapshotState -StartEnabled $false -StopEnabled $false -SaveEnabled $true -Status 'ready' -ErrorCount 0 -ErrorsKnown $true
Assert-Case ($emptyState.idle -and $emptyState.editable -and -not $emptyState.can_run -and -not $emptyState.ready) 'Empty ready Main is adoptable but cannot run'
$savedState=New-AgentPadSnapshotState -StartEnabled $true -StopEnabled $false -SaveEnabled $true -Status 'saved' -ErrorCount 0 -ErrorsKnown $true
Assert-Case ($savedState.idle -and $savedState.editable -and $savedState.can_run) 'Saved enabled flow is idle, editable, and runnable'
$savingState=New-AgentPadSnapshotState -StartEnabled $true -StopEnabled $false -SaveEnabled $true -Status 'saving' -ErrorCount -1 -ErrorsKnown $false
Assert-Case (-not $savingState.idle -and -not $savingState.editable -and -not $savingState.can_run -and -not $savingState.errors_known) 'Saving state is not treated as idle or zero-error'
$runningState=New-AgentPadSnapshotState -StartEnabled $false -StopEnabled $true -SaveEnabled $true -Status 'running' -ErrorCount -1 -ErrorsKnown $false
Assert-Case ($runningState.running -and -not $runningState.idle -and -not $runningState.errors_known) 'Running state retains unknown error count'

# All test data remains under this repository, with a unique directory per run.
$testBase=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '.tmp'))
$temp=Join-Path $testBase ('pad-'+[guid]::NewGuid().ToString('N'))
$null=[IO.Directory]::CreateDirectory($temp)
$junction=$null
try {
    $target=Join-Path $temp 'input'
    $script:run=Join-Path $temp ('data\jobs\'+('1'*32)+'\runs\'+('5'*32))
    $artifacts=Join-Path $script:run 'artifacts'
    foreach($directory in @($target,$artifacts)){[IO.Directory]::CreateDirectory($directory)|Out-Null}
    $script:job=[pscustomobject]@{target=$target;job_id=('1'*32)}
    $input=Join-Path $target '日本語 quote''s input.txt'
    $data="100% / %UntrustedVariable% / 日本語 / C:\new\tools / 'quotes' / `"double`"`r`nAGENT_END_fake`r`nScripting.RunPowershellScript.RunScript"
    [IO.File]::WriteAllText($input,$data,$script:AgentEncoding)
    $inputHash=(Get-FileHash -LiteralPath $input -Algorithm SHA256).Hash
    $output=Join-Path $artifacts 'result.txt'
    $read=New-ReadAction $input
    $write=New-WriteAction $output
    $writes=@(Test-Flow ($read+"`r`n"+$write))
    Assert-Case ($writes.Count -eq 1 -and $writes[0] -ceq $output) 'UTF8 data input produces the declared new output path'
    Assert-Case (-not [IO.File]::Exists($output)) 'Validation does not execute file writes'
    Assert-Case ((Get-FileHash -LiteralPath $input -Algorithm SHA256).Hash -ceq $inputHash) 'Percent signs, embedded markers and code-like data remain unchanged'

    foreach($value in @('',"日本語 O'Brien `"quoted`" C:\new\tools",'C:\n\r\t\','two  spaces')) {
        $literal=ConvertTo-AgentRobinLiteral $value
        Assert-Case ((ConvertFrom-AgentRobinLiteral $literal) -ceq $value) 'Robin literal round-trip preserves quotes, backslashes and Unicode'
        $null=Test-Flow ('SET Value TO '+$literal)
        Assert-Case $true 'Escaped literal accepted by production validator'
    }
    Assert-Rejected {ConvertTo-AgentRobinLiteral '100%'} 'ROBIN_LITERAL' 'Literal percent must enter through a data file'
    Assert-Rejected {ConvertTo-AgentRobinLiteral ("a"+[char]0+"b")} 'ROBIN_LITERAL' 'Literal NUL rejected'
    Assert-Rejected {ConvertFrom-AgentRobinLiteral ('$'+"'''bad\n'''" )} 'ROBIN_LITERAL' 'Unknown backslash escape is not silently repaired'
    Assert-Rejected {Test-Flow ('SET Value TO '+('$'+"'''100%'''"))} 'ROBIN_EXPRESSION' 'Raw percent literal rejected'
    Assert-Rejected {Test-Flow ('SET Value TO '+('$'+"'''%InputText.Length%'''"))} 'ROBIN_EXPRESSION' 'Executable property expression rejected'
    Assert-Rejected {Test-Flow ('SET Value TO '+('$'+"'''%Missing%'''"))} 'ROBIN_VARIABLE' 'Variable interpolation requires prior assignment'
    $interpolation=$read+"`nSET Copy TO "+('$'+"'''%InputText%'''")
    $null=Test-Flow $interpolation
    Assert-Case $true 'Simple interpolation of previously read data is accepted'

    $yes=ConvertTo-AgentRobinLiteral 'yes'
    $no=ConvertTo-AgentRobinLiteral 'no'
    $branch=$read+"`nIF InputText = "+$yes+" THEN`n    SET Choice TO "+$yes+"`nELSE`n    SET Choice TO "+$no+"`nEND`n"+(New-WriteAction $output 'Choice')
    Assert-Case (@(Test-Flow $branch).Count -eq 1) 'IF/ELSE assignments are definite after both branches'
    $thenOnly=$read+"`nIF InputText = "+$yes+" THEN`n    SET Choice TO "+$yes+"`nEND`n"+(New-WriteAction $output 'Choice')
    Assert-Rejected {Test-Flow $thenOnly} 'ROBIN_VARIABLE' 'Then-only assignment cannot escape an IF'
    $elseOnly=$read+"`nIF InputText = "+$yes+" THEN`n    SET Other TO "+$yes+"`nELSE`n    SET Choice TO "+$no+"`nEND`n"+(New-WriteAction $output 'Choice')
    Assert-Rejected {Test-Flow $elseOnly} 'ROBIN_VARIABLE' 'Else-only assignment cannot escape an IF'
    $crossBranch=$read+"`nIF InputText = "+$yes+" THEN`n    SET Choice TO "+$yes+"`nELSE`n    SET Other TO "+('$'+"'''%Choice%'''")+"`nEND"
    Assert-Rejected {Test-Flow $crossBranch} 'ROBIN_VARIABLE' 'ELSE cannot reference a variable defined only in THEN'
    Assert-Rejected {Test-Flow $write} 'ROBIN_VARIABLE' 'Write variable requires assignment'
    Assert-Rejected {Test-Flow ($read+"`nIF Missing = "+$yes+" THEN`nEND")} 'ROBIN_VARIABLE' 'IF condition requires assignment'
    foreach($code in @('END','ELSE',($read+"`nIF InputText = "+$yes+' THEN'),($read+"`nIF InputText = "+$yes+" THEN`n  WAIT 0`nEND"),($read+"`nIF InputText = "+$yes+" THEN`nELSE`nELSE`nEND"))) {
        Assert-Rejected {Test-Flow $code} 'ROBIN_BLOCK' 'Malformed or incomplete block rejected'
    }

    foreach($code in @('Unknown.Action Value: 1','Scripting.RunPowershellScript.RunScript Script: $'+"'''Get-Process''' ScriptOutput=> Output",'LOOP FOREVER','File.Delete Files: '+(ConvertTo-AgentRobinLiteral $input),$read.Replace('UTF8','Unicode'),$write.Replace('Append','Overwrite'))) {
        Assert-Rejected {Test-Flow $code} 'ROBIN_ACTION' 'Unknown action or parameter combination rejected'
    }
    Assert-Rejected {Test-Flow ($read+"`n"+$write+"`n"+$write)} 'ROBIN_WRITE' 'Repeated write to an output path rejected'
    [IO.File]::WriteAllText($output,'existing',$script:AgentEncoding)
    Assert-Rejected {Test-Flow ($read+"`n"+$write)} 'ROBIN_WRITE' 'Existing artifact cannot be appended or overwritten'
    [IO.File]::Delete($output)
    $pathCases=@(
        (Join-Path $target '..\outside.txt'),
        (Join-Path $artifacts '..\control\finished.txt'),
        (Join-Path $target 'input.txt:alternate'),
        (Join-Path $target '%DynamicPath%'),
        (Join-Path $temp 'input-other\escape.txt'),
        '\\server\share\input.txt',
        'relative.txt'
    )
    foreach($path in $pathCases){Assert-Rejected {Assert-AgentPadPath $path @($target,$artifacts)} 'ROBIN_PATH' 'Traversal, alternate stream, dynamic, sibling, UNC or relative path rejected'}
    Assert-Rejected {Test-Flow (New-WriteAction (Join-Path $script:run 'control\finished.txt') $yes)} 'ROBIN_PATH' 'Planner cannot forge controller completion marker'
    Assert-Rejected {Test-Flow (New-ReadAction (Join-Path $script:run 'control\started.txt'))} 'ROBIN_PATH' 'Planner cannot read controller marker paths'
    Assert-Rejected {Assert-AgentPadPath (Join-Path $target 'missing.txt') @($target) -MustExist} 'ROBIN_PATH' 'Required input must exist'
    $external=Join-Path $temp 'external'
    $null=[IO.Directory]::CreateDirectory($external)
    $junction=Join-Path $artifacts 'redirect'
    New-Item -ItemType Junction -Path $junction -Target $external | Out-Null
    Assert-Rejected {Assert-AgentPadPath (Join-Path $junction 'escape.txt') @($artifacts)} 'ROBIN_PATH' 'Reparse-point ancestor cannot redirect a permitted output'
    [IO.Directory]::Delete($junction)
    $junction=$null

    foreach($code in @(''," `r`n",('```'+"`nWAIT 0`n"+'```'),"WAIT`t0",("SET Value TO "+$yes+[char]0))) {
        Assert-Rejected {Test-Flow $code} 'ROBIN_INVALID' 'Empty, fenced, tabbed and NUL code rejected'
    }
    Assert-Rejected {Test-Flow ('x'*64001)} 'ROBIN_INVALID' 'Robin size bound enforced'
    $null=Test-Flow ((@('WAIT 0')*250) -join "`n")
    Assert-Case $true '250-line boundary accepted'
    Assert-Rejected {Test-Flow ((@('WAIT 0')*251) -join "`n")} 'ROBIN_LIMIT' '251 lines rejected'
    $null=Test-Flow ((@('WAIT 5')*6) -join "`n")
    Assert-Case $true '30-second total WAIT accepted'
    Assert-Rejected {Test-Flow ((@('WAIT 5')*7) -join "`n")} 'ROBIN_LIMIT' '31-plus seconds of WAIT rejected'
    Assert-Rejected {Test-Flow 'WAIT 6'} 'ROBIN_ACTION' 'Individual WAIT greater than five seconds rejected'
    Assert-Rejected {Test-Flow ($read+"`nAGENT_END_fake")} 'ROBIN_ACTION' 'Embedded response marker cannot become Robin syntax'
    Assert-Case ((ConvertTo-AgentComparableRobin ($branch.Replace("`n","`r`n")+"`r`n")) -ceq (ConvertTo-AgentComparableRobin $branch)) 'Readback comparison permits newline transport only'
    Assert-Case ((ConvertTo-AgentComparableRobin $branch) -cne (ConvertTo-AgentComparableRobin ($branch.Replace('    SET','   SET')))) 'Readback comparison preserves indentation'
    Assert-Case ((ConvertTo-AgentComparableRobin 'C:\new\file %V%') -cne (ConvertTo-AgentComparableRobin 'C:newfile %V%')) 'Readback comparison preserves literal backslashes'

    $call=[pscustomobject]@{ai_call_id=('2'*32);operation='classify';input_path=$input;instructions="Classify 'quoted' 100% data; do not execute & commands";labels=@('yes','no');timeout_seconds=30}
    $templates=@(New-AgentAiCallTemplates -Calls @($call) -Job $script:job -RunDirectory $script:run -RunId ('5'*32) -AppPath ([IO.Path]::GetFullPath($SourcePath)) -HomePath $temp)
    Assert-Case ($templates.Count -eq 1) 'One server-owned AiCall template created'
    $template=$templates[0]
    $request=[IO.File]::ReadAllText($template.request_path,[Text.Encoding]::UTF8)|ConvertFrom-Json
    Assert-Case ($request.instructions -ceq $call.instructions) 'AiCall instructions stay unchanged in the request data file'
    Assert-Case (-not $template.robin.Contains($call.instructions)) 'Business instructions do not enter executable script text'
    $guard="    ON ERROR`n        SET AgentAiReadFailed TO `$'''ERROR'''`n        THROW ERROR`n    END"
    $unguardedCallFlow=$template.robin+"`n"+(New-ReadAction $template.text_path 'AiText')+"`n"+(New-ReadAction $template.status_path 'AiStatus')
    $callFlow=$template.robin+"`n"+(New-ReadAction $template.text_path 'AiText')+"`n"+$guard+"`n"+(New-ReadAction $template.status_path 'AiStatus')+"`n"+$guard
    $null=Test-Flow $callFlow
    Assert-Case $true 'Exact AiCall template and mandatory result/status reads with throw guards accepted'
    Assert-Rejected {Test-Flow $unguardedCallFlow} 'ROBIN_AICALL' 'AiCall read without its exact error guard rejected'
    $missingStatusGuard=$template.robin+"`n"+(New-ReadAction $template.text_path 'AiText')+"`n"+$guard+"`n"+(New-ReadAction $template.status_path 'AiStatus')
    Assert-Rejected {Test-Flow $missingStatusGuard} 'ROBIN_AICALL' 'Missing final status-read error guard rejected'
    foreach($alteredFlow in @($callFlow.Replace('        THROW ERROR','        WAIT 0'),$callFlow.Replace('AgentAiReadFailed','OtherName'),$callFlow.Replace('    ON ERROR','   ON ERROR'),$callFlow.Replace("'''ERROR'''","'''OK'''"))) {
        Assert-Rejected {Test-Flow $alteredFlow} 'ROBIN_AICALL' 'Altered throw, assignment, guard indentation or error literal rejected'
    }
    $nestedCall='SET Condition TO '+$yes+"`nIF Condition = "+$yes+" THEN`n"+(($callFlow -split "`n" | ForEach-Object {'    '+$_}) -join "`n")+"`nEND"
    $null=Test-Flow $nestedCall
    Assert-Case $true 'Mandatory AiCall guards preserve relative indentation inside IF'
    Assert-Rejected {Test-Flow ($callFlow+"`n"+(New-WriteAction $output 'AgentAiReadFailed'))} 'ROBIN_VARIABLE' 'Failure-only guard assignment is not definite on normal execution'
    Assert-Rejected {Test-Flow $template.robin} 'ROBIN_AICALL' 'AiCall without mandatory result/status reads rejected'
    Assert-Rejected {Test-Flow ($template.robin+"`nWAIT 0")} 'ROBIN_AICALL' 'AiCall result reads cannot be deferred'
    Assert-Rejected {Test-Flow ($template.robin+"`n"+(New-ReadAction $template.status_path))} 'ROBIN_AICALL' 'AiCall must read result text before status'
    Assert-Rejected {Test-Flow $template.robin.Replace('-NoProfile','-NoProfile -Command evil')} 'ROBIN_ACTION' 'Mutated AiCall command rejected'
    Assert-Rejected {Test-Flow ($template.robin+' ')} 'ROBIN_ACTION' 'Template exact match does not trim a modified action'
    Assert-Rejected {Test-Flow ($callFlow+"`n"+$callFlow)} 'ROBIN_AICALL' 'One AiCall ID cannot execute twice'
    $null=Test-Flow (New-ReadAction $template.text_path 'AiText')
    Assert-Case $true 'Prepared AiCall result text is an allowed data input'
    $null=Test-Flow (New-ReadAction $template.status_path 'AiStatus')
    Assert-Case $true 'Prepared AiCall status is an allowed data input'
    Assert-Rejected {Test-Flow (New-ReadAction $template.request_path)} 'ROBIN_PATH' 'AiCall request JSON is outside planner data inputs'
    Assert-Rejected {Test-Flow (New-ReadAction (Join-Path $script:run ('calls\'+('4'*32)+'\result.txt')))} 'ROBIN_PATH' 'Unreserved AiCall result path rejected'
    Assert-Rejected {New-AgentAiCallTemplates -Calls @($call,$call,$call,$call) -Job $script:job -RunDirectory $script:run -RunId ('5'*32) -AppPath $SourcePath -HomePath $temp} 'AICALL_LIMIT' 'More than three serial AiCalls rejected'

    # Pure observation of local result JSON; no AI provider or flow is called.
    $ai=Get-AgentPadAiResults -RunDirectory $script:run -RunId ('5'*32) -Job $script:job
    Assert-Case ($ai.status -ceq 'failed' -and $ai.error -like 'PAD_AI_RESULT_MISSING:*') 'Missing AI result cannot prove successful completion'
    $aiRecord=[ordered]@{job_id=$script:job.job_id;run_id=('5'*32);ai_call_id=$template.ai_call_id;status='success';result='synthetic result';error_type='';input_count=1;output_count=1}
    foreach($case in @(@{status='success';error_type='';overall='success'},@{status='needs_review';error_type='';overall='success'},@{status='failed';error_type='RESPONSE_TIMEOUT';overall='failed'},@{status='cancelled';error_type='CANCELLED';overall='cancelled'})) {
        $aiRecord.status=$case.status;$aiRecord.error_type=$case.error_type
        Write-AgentJson $template.result_path $aiRecord
        $ai=Get-AgentPadAiResults -RunDirectory $script:run -RunId ('5'*32) -Job $script:job
        Assert-Case ($ai.status -ceq $case.overall -and $ai.ai_calls.Count -eq 1 -and $ai.ai_calls[0].status -ceq $case.status -and $ai.ai_calls[0].error_type -ceq $case.error_type) ('AI result classification preserves '+$case.status+' and error type')
        if($case.status -in @('failed','cancelled')) {Assert-Case ($ai.error -ceq ('AICALL_'+$case.error_type)) ('Failure diagnostic preserved: '+$case.status)}
    }
    $aiRecord.status='success';$aiRecord.error_type=''
    foreach($field in @('job_id','run_id','ai_call_id')) {
        $original=$aiRecord[$field];$aiRecord[$field]='9'*32
        Write-AgentJson $template.result_path $aiRecord
        $ai=Get-AgentPadAiResults -RunDirectory $script:run -RunId ('5'*32) -Job $script:job
        Assert-Case ($ai.status -ceq 'unknown' -and $ai.error -like 'PAD_AI_RESULT_ID:*' -and $ai.ai_calls.Count -eq 0) ('Mismatched AI '+$field+' cannot be attributed to this run')
        $aiRecord[$field]=$original
    }
    $aiRecord.status='unexpected'
    Write-AgentJson $template.result_path $aiRecord
    $ai=Get-AgentPadAiResults -RunDirectory $script:run -RunId ('5'*32) -Job $script:job
    Assert-Case ($ai.status -ceq 'unknown' -and $ai.error -like 'PAD_AI_RESULT_STATUS:*') 'Invalid AI result status remains unknown'
    $aiRecord.status='success'
    Write-AgentJson $template.result_path $aiRecord

    # Mock ONLY application UI boundary functions. Native clipboard, keyboard,
    # UIA assembly, and real control invocation are never loaded or called.
    function Reset-PadMock([string]$Scenario) {
        $script:padScenario=$Scenario
        $script:padWindowReads=0;$script:padSnapshotReads=0;$script:padRunInvocations=0
        $script:padSaveInvocations=0;$script:padStopInvocations=0;$script:padReadbacks=0
        $script:padClipboard='original clipboard';$script:padClipboardRestores=0
        $script:padKeys=New-Object 'Collections.Generic.List[string]'
        $script:padMockSnapshot=$null
        $script:padStatusSequence=@()
        $script:padCancelDuringSettle=$null
    }
    function Get-AgentPadWindow($Settings){$script:padWindowReads++;return [pscustomobject]@{Mock=$true}}
    function Get-AgentPadSnapshot($Window,[switch]$AllowErrors) {
        $script:padSnapshotReads++
        $status='ready';$idle=$true;$editable=$true;$canRun=$true;$errors=0;$errorsKnown=$true
        if($script:padStatusSequence.Count -gt 0) {
            $index=[Math]::Min($script:padSnapshotReads-1,$script:padStatusSequence.Count-1)
            $status=[string]$script:padStatusSequence[$index]
            if($status -in @('saving','parsing','checking','updating','publishing','repairing')) {$idle=$false;$editable=$false;$canRun=$false;$errors=-1;$errorsKnown=$false}
            if($status -eq 'saved') {$idle=$true;$editable=$true;$canRun=$true}
        }
        if($script:padScenario -eq 'idle-false' -or ($script:padScenario -eq 'before-paste-busy' -and $script:padSnapshotReads -eq 2) -or ($script:padScenario -eq 'before-run-busy' -and $script:padSnapshotReads -eq 3)){$idle=$false;$editable=$false;$canRun=$false}
        if($script:padScenario -eq 'run-disabled' -and $script:padSnapshotReads -eq 3){$canRun=$false}
        if($script:padScenario -eq 'runtime-error' -and $script:padRunInvocations -gt 0){$errors=1}
        if($script:padScenario -eq 'cancel-while-settling' -and $script:padSnapshotReads -eq 1 -and $script:padCancelDuringSettle){[IO.File]::WriteAllText($script:padCancelDuringSettle,'cancel',$script:AgentEncoding)}
        $script:padMockSnapshot=[pscustomobject]@{ready=$canRun;idle=$idle;editable=$editable;can_run=$canRun;running=$false;errors=$errors;errors_known=$errorsKnown;window=$Window;workspace='mock-workspace';start='mock-start';stop='mock-stop';save='mock-save';status=$status}
        return $script:padMockSnapshot
    }
    function Set-AgentPadFocus($Window,$Workspace) {
        if($script:padScenario -eq 'focus-failure'){throw 'PAD_FOCUS: mocked focus uncertainty.'}
    }
    function Test-AgentPadEmpty($Workspace) {return $script:padScenario -notin @('unowned','owner-missing','user-edited','replace-failure')}
    function Get-AgentPadClipboard {return 'original clipboard'}
    function Get-AgentPadClipboardText {return $script:padClipboard}
    function Set-AgentPadClipboardText([string]$Text) {$script:padClipboard=$Text}
    function Restore-AgentPadClipboard($Clipboard) {$script:padClipboardRestores++;$script:padClipboard=$Clipboard}
    function Send-AgentPadKeys([string]$Keys) {
        $script:padKeys.Add($Keys)
        if($script:padScenario -eq 'copy-result' -and $Keys -ceq '^c'){$script:padClipboard=$script:mockCopiedCode}
    }
    function Get-AgentPadCode($Snapshot) {
        $script:padReadbacks++
        if($script:padScenario -eq 'unowned'){return 'WAIT 0'}
        if($script:padScenario -in @('replace-failure','owner-missing')){return $script:mockOwnedCode}
        if($script:padScenario -eq 'user-edited'){return $script:mockOwnedCode+"`nWAIT 1"}
        if($script:padScenario -eq 'clipboard-user-changed'){$script:padClipboard='new user clipboard';return 'WAIT 1'}
        if($script:padScenario -eq 'paste-mismatch' -or ($script:padScenario -eq 'save-mismatch' -and $script:padReadbacks -eq 2)){return $script:padClipboard+"`nWAIT 1"}
        return $script:padClipboard
    }
    function Wait-AgentPadSaved($Window,[string]$CancelPath) {
        if($script:padScenario -eq 'save-unknown'){throw 'PAD_SAVE_UNKNOWN: mocked unconfirmed save.'}
        if($script:padScenario -eq 'cancel-during-save'){throw 'CANCELLED: mocked stop during save.'}
        return $script:padMockSnapshot
    }
    function Wait-AgentPadEditable($Window,[string]$CancelPath) {
        if($script:padScenario -eq 'settle-unknown'){throw 'PAD_SETUP: mocked state did not settle.'}
        return $script:padMockSnapshot
    }
    function Wait-AgentPadSaveBaseline($Window,[string]$CancelPath) {
        if($script:padScenario -eq 'save-stale'){throw 'PAD_SAVE_UNKNOWN: mocked stale saved state.'}
        return $script:padMockSnapshot
    }
    function Invoke-AgentPadControl($Element) {
        switch -Exact ($Element) {
            'mock-save' {$script:padSaveInvocations++;return}
            'mock-stop' {$script:padStopInvocations++;return}
            'mock-start' {
                $script:padRunInvocations++
                if($script:padScenario -in @('conditional-complete','finish-marker-mismatch')) {
                    # Synthetic observer inputs only; this is not a PAD execution.
                    [IO.File]::WriteAllText((Join-Path $script:mockRunDirectory 'control\started.txt'),$script:mockRunId,$script:AgentEncoding)
                    $endValue=if($script:padScenario -eq 'finish-marker-mismatch'){'wrong-run-id'}else{$script:mockRunId}
                    [IO.File]::WriteAllText((Join-Path $script:mockRunDirectory 'control\finished.txt'),$endValue,$script:AgentEncoding)
                    if($script:mockObservedArtifact){[IO.File]::WriteAllText($script:mockObservedArtifact,'synthetic branch result',$script:AgentEncoding)}
                    return
                }
                if($script:padScenario -ne 'runtime-error'){throw 'TEST_UI_INVOCATION_UNKNOWN: single mocked Run returned an uncertain failure.'}
                return
            }
            default {throw 'Unexpected mock control.'}
        }
    }
    Reset-PadMock 'idle-false'
    $settings=[pscustomobject]@{pad_flow_name='TEST ONLY'}
    $script:mockOwnedCode='SET AgentOwnedFlow TO $'+"'''AiPromptsAgent'''`nWAIT 0"
    $padOwnerPath=Join-Path (Join-Path $temp 'data') ('pad-owned-'+(Get-AgentTextHash $settings.pad_flow_name)+'.json')
    $cancel=Join-Path $temp 'cancel'
    $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:run -RunId ('5'*32) -Job $script:job -Settings $settings -CancelPath $cancel
    Assert-Case ($result.status -ceq 'failed' -and $result.error -like 'PAD_BUSY:*') 'Mock busy designer fails closed before UI mutation'
    Assert-Case ($script:padWindowReads -eq 1 -and $script:padSnapshotReads -eq 1 -and $script:padRunInvocations -eq 0) 'Busy path stops at the idle gate'
    [IO.File]::WriteAllText($cancel,'cancel',$script:AgentEncoding)
    $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:run -RunId ('5'*32) -Job $script:job -Settings $settings -CancelPath $cancel
    Assert-Case ($result.status -ceq 'cancelled' -and $script:padWindowReads -eq 1) 'Pre-cancellation performs no UI inspection'
    [IO.File]::Delete($cancel)
    $mockCases=@(
        @{scenario='before-paste-busy';prefix='PAD_BUSY';saves=0},
        @{scenario='focus-failure';prefix='PAD_FOCUS';saves=0},
        @{scenario='unowned';prefix='PAD_OWNERSHIP';saves=0},
        @{scenario='owner-missing';prefix='PAD_OWNERSHIP';saves=0},
        @{scenario='user-edited';prefix='PAD_OWNERSHIP';saves=0},
        @{scenario='replace-failure';prefix='PAD_REPLACE';saves=0},
        @{scenario='paste-mismatch';prefix='PAD_PASTE_MISMATCH';saves=0},
        @{scenario='save-stale';prefix='PAD_SAVE_UNKNOWN';saves=0},
        @{scenario='save-unknown';prefix='PAD_SAVE_UNKNOWN';saves=1},
        @{scenario='save-mismatch';prefix='PAD_SAVE_MISMATCH';saves=1},
        @{scenario='before-run-busy';prefix='PAD_SETUP';saves=1},
        @{scenario='run-disabled';prefix='PAD_SETUP';saves=1}
    )
    foreach($case in $mockCases) {
        Reset-PadMock $case.scenario
        if($case.scenario -eq 'owner-missing') {[IO.File]::Delete($padOwnerPath)}
        if($case.scenario -in @('user-edited','replace-failure')) {Write-AgentJson $padOwnerPath @{flow_name=$settings.pad_flow_name;hash=(Get-AgentTextHash (ConvertTo-AgentComparableRobin $script:mockOwnedCode))}}
        $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:run -RunId ('5'*32) -Job $script:job -Settings $settings -CancelPath $cancel
        Assert-Case ($result.status -ceq 'failed' -and $result.error -like ($case.prefix+':*')) ('Mock failure classified: '+$case.scenario+'; '+$result.error)
        Assert-Case ($script:padRunInvocations -eq 0 -and $script:padSaveInvocations -eq $case.saves) ('No Run after '+$case.scenario)
        if($case.scenario -in @('unowned','owner-missing','user-edited')) {Assert-Case ($script:padKeys.Count -eq 0) ('Unowned or externally edited actions cannot be deleted: '+$case.scenario)}
        if($case.scenario -eq 'paste-mismatch') {
            Assert-Case (@($script:padKeys | Where-Object {$_ -ceq '^v'}).Count -eq 1) 'Uncertain paste is attempted once'
            Assert-Case ($script:padClipboardRestores -eq 1 -and $script:padClipboard -ceq 'original clipboard') 'Controller restores its mock clipboard on paste failure'
        }
    }
    Reset-PadMock 'cancel-during-save'
    $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:run -RunId ('5'*32) -Job $script:job -Settings $settings -CancelPath $cancel
    Assert-Case ($result.status -ceq 'cancelled' -and $script:padRunInvocations -eq 0) 'Mock cancellation during save prevents Run'
    Reset-PadMock 'run-unknown'
    $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:run -RunId ('5'*32) -Job $script:job -Settings $settings -CancelPath $cancel
    Assert-Case ($result.status -ceq 'unknown' -and $result.error -like 'TEST_UI_INVOCATION_UNKNOWN:*') 'Exception at Run boundary is an unknown result'
    Assert-Case ($script:padRunInvocations -eq 1 -and $script:padSaveInvocations -eq 1) 'Unknown Run invocation is never retried'
    Reset-PadMock 'runtime-error'
    $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:run -RunId ('5'*32) -Job $script:job -Settings $settings -CancelPath $cancel
    Assert-Case ($result.status -ceq 'failed' -and $result.error -like 'PAD_RUNTIME_ERROR:*' -and $script:padRunInvocations -eq 1) 'Mock runtime error cannot be reported as completion'
    foreach($aiStatus in @('failed','cancelled')) {
        $aiRecord.status=$aiStatus;$aiRecord.error_type=if($aiStatus -eq 'failed'){'RESPONSE_TIMEOUT'}else{'CANCELLED'}
        Write-AgentJson $template.result_path $aiRecord
        Reset-PadMock 'runtime-error'
        $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:run -RunId ('5'*32) -Job $script:job -Settings $settings -CancelPath $cancel
        Assert-Case ($result.status -ceq $aiStatus -and $result.error -ceq ('AICALL_'+$aiRecord.error_type) -and $result.artifacts.Count -eq 0 -and $script:padRunInvocations -eq 1) ('Stopped mock runtime preserves AI '+$aiStatus+' diagnostic without retry')
    }
    $aiRecord.status='success';$aiRecord.error_type=''
    Write-AgentJson $template.result_path $aiRecord
    Reset-PadMock 'clipboard-user-changed'
    $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:run -RunId ('5'*32) -Job $script:job -Settings $settings -CancelPath $cancel
    Assert-Case ($result.error -like 'PAD_PASTE_MISMATCH:*' -and $script:padRunInvocations -eq 0) 'Clipboard change cannot authorize a mismatched paste'
    Assert-Case ($script:padClipboardRestores -eq 0 -and $script:padClipboard -ceq 'new user clipboard') 'Cleanup preserves a clipboard change made by another actor'

    $script:mockRunId='6'*32
    $script:mockRunDirectory=Join-Path ([IO.Path]::GetDirectoryName($script:run)) $script:mockRunId
    $branchArtifacts=Join-Path $script:mockRunDirectory 'artifacts'
    $null=[IO.Directory]::CreateDirectory($branchArtifacts)
    $script:mockObservedArtifact=Join-Path $branchArtifacts 'selected.txt'
    $unselected=Join-Path $branchArtifacts 'unselected.txt'
    $conditional='SET Condition TO '+$yes+"`nIF Condition = "+$yes+" THEN`n    "+(New-WriteAction $script:mockObservedArtifact $yes)+"`nELSE`n    "+(New-WriteAction $unselected $no)+"`nEND"
    Reset-PadMock 'conditional-complete'
    $result=Invoke-AgentPad -Robin $conditional -RunDirectory $script:mockRunDirectory -RunId $script:mockRunId -Job $script:job -Settings $settings -CancelPath $cancel
    Assert-Case ($result.status -ceq 'success' -and $result.artifacts.Count -eq 1 -and $result.artifacts[0] -ceq $script:mockObservedArtifact) 'Synthetic completion reports only the observed conditional branch output'
    Assert-Case (-not [IO.File]::Exists($unselected) -and $script:padRunInvocations -eq 1) 'Unselected branch output is not fabricated'
    Reset-PadMock 'run-unknown'
    $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:mockRunDirectory -RunId $script:mockRunId -Job $script:job -Settings $settings -CancelPath $cancel
    Assert-Case ($result.error -like 'PAD_REPLAY:*' -and $script:padRunInvocations -eq 0 -and $script:padKeys.Count -eq 0) 'Existing control markers prevent another paste or Run'
    $script:mockRunId='7'*32
    $script:mockRunDirectory=Join-Path ([IO.Path]::GetDirectoryName($script:run)) $script:mockRunId
    $null=[IO.Directory]::CreateDirectory((Join-Path $script:mockRunDirectory 'artifacts'))
    $script:mockObservedArtifact=$null
    Reset-PadMock 'finish-marker-mismatch'
    $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:mockRunDirectory -RunId $script:mockRunId -Job $script:job -Settings $settings -CancelPath $cancel
    Assert-Case ($result.status -ceq 'unknown' -and $result.error -like 'PAD_RUN_ID:*' -and $result.artifacts.Count -eq 0 -and $script:padRunInvocations -eq 1) 'Mismatched synthetic finish marker cannot prove completion or trigger retry'

    # A real OS mutex on a helper thread verifies contention and abandonment.
    # This helper contains no PAD/UI code and does not emulate the controller.
    if(-not ('PadTestMutexHolder' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Threading;
public sealed class PadTestMutexHolder : IDisposable {
    private readonly Mutex mutex;
    private readonly ManualResetEvent acquired = new ManualResetEvent(false);
    private readonly ManualResetEvent release = new ManualResetEvent(false);
    private readonly Thread thread;
    private Exception error;
    public PadTestMutexHolder(string name, bool abandon) {
        mutex = new Mutex(false, name);
        thread = new Thread(() => {
            try {
                if (!mutex.WaitOne(5000)) throw new Exception("Test mutex acquisition timed out.");
                acquired.Set();
                if (!abandon) { release.WaitOne(); mutex.ReleaseMutex(); }
            } catch(Exception ex) { error=ex; acquired.Set(); }
        });
        thread.IsBackground=true;
        thread.Start();
        if (!acquired.WaitOne(10000)) throw new Exception("Test mutex helper did not start.");
        if (error != null) throw error;
        if (abandon) thread.Join();
    }
    public void Dispose() {
        release.Set(); thread.Join(10000); mutex.Dispose(); acquired.Dispose(); release.Dispose();
    }
}
'@
    }
    foreach($abandon in @($false,$true)) {
        Reset-PadMock 'idle-false'
        $holder=New-Object PadTestMutexHolder('Local\AiPromptsAgent-PAD',$abandon)
        try {
            $result=Invoke-AgentPad -Robin 'WAIT 0' -RunDirectory $script:run -RunId ('5'*32) -Job $script:job -Settings $settings -CancelPath $cancel
            $prefix=if($abandon){'PAD_UNKNOWN:'}else{'PAD_BUSY:'}
            $expectedStatus=if($abandon){'unknown'}else{'failed'}
            Assert-Case ($result.error.StartsWith($prefix) -and $result.status -ceq $expectedStatus) ('OS mutex state remains unknown after abandonment, abandoned='+$abandon+'; '+$result.error)
            Assert-Case ($script:padWindowReads -eq 0 -and $script:padRunInvocations -eq 0) 'Contended or abandoned controller lock never reaches UI'
        } finally {$holder.Dispose()}
    }

    # Exercise real readback/save helpers against the same narrow mock boundary.
    foreach($name in @('Get-AgentPadCode','Wait-AgentPadEditable','Wait-AgentPadSaveBaseline','Wait-AgentPadSaved')) {
        if(-not $definitions.ContainsKey($name)){throw ('Missing production function: '+$name)}
        . ([scriptblock]::Create($definitions[$name].Extent.Text))
    }
    Reset-PadMock 'copy-sentinel'
    $snapshot=Get-AgentPadSnapshot ([pscustomobject]@{Mock=$true})
    Assert-Rejected {Get-AgentPadCode $snapshot} 'PAD_COPY' 'Unchanged clipboard sentinel rejects an unconfirmed copy'
    Reset-PadMock 'copy-result'
    $script:mockCopiedCode=$branch
    $snapshot=Get-AgentPadSnapshot ([pscustomobject]@{Mock=$true})
    Assert-Case ((Get-AgentPadCode $snapshot) -ceq $branch) 'Readback helper preserves copied Robin exactly through mocked clipboard'
    Assert-Case (($script:padKeys -join ',') -ceq '^a,^c') 'Readback helper selects and copies exactly once'
    Assert-Case ($script:AgentPadClipboardValue -ceq $branch) 'Readback helper records its own clipboard value for conditional restoration'
    Reset-PadMock 'settle-after-paste'
    $script:padStatusSequence=@('parsing','checking','ready')
    Assert-Case ((Wait-AgentPadEditable ([pscustomobject]@{Mock=$true}) $cancel).status -ceq 'ready') 'Editable wait observes parse/check transient states until ready'
    Assert-Case ($script:padSnapshotReads -eq 4) 'Editable wait requires two consecutive ready samples after parse/check transients'
    Reset-PadMock 'settle-after-paste'
    $script:padStatusSequence=@('ready','parsing','checking','ready')
    Assert-Case ((Wait-AgentPadEditable ([pscustomobject]@{Mock=$true}) $cancel).status -ceq 'ready') 'Editable wait does not accept an early Ready before parsing resumes'
    Assert-Case ($script:padSnapshotReads -eq 5) 'Early Ready is reset by parsing and cannot authorize readback'
    Reset-PadMock 'settle-after-paste'
    $script:padStatusSequence=@('parsing')
    Assert-Rejected {Wait-AgentPadEditable ([pscustomobject]@{Mock=$true}) $cancel -TimeoutSeconds 0} 'PAD_SETUP' 'Editable wait fails closed when parsing cannot settle'
    Reset-PadMock 'cancel-while-settling'
    $script:padStatusSequence=@('parsing')
    $script:padCancelDuringSettle=$cancel
    Assert-Rejected {Wait-AgentPadEditable ([pscustomobject]@{Mock=$true}) $cancel} 'CANCELLED' 'Editable wait observes cancellation while settling'
    [IO.File]::Delete($cancel)
    Reset-PadMock 'save-observed'
    $script:padStatusSequence=@('ready')
    Assert-Case ((Wait-AgentPadSaveBaseline ([pscustomobject]@{Mock=$true}) $cancel).status -ceq 'ready') 'Save helper requires a fresh ready baseline before Invoke'
    Reset-PadMock 'save-observed'
    $script:padStatusSequence=@('saving','saved')
    Assert-Case ((Wait-AgentPadSaved ([pscustomobject]@{Mock=$true}) $cancel).status -ceq 'saved') 'Save helper accepts only an observed saving-to-saved transition'
    Reset-PadMock 'save-observed'
    $script:padStatusSequence=@('saved')
    Assert-Rejected {Wait-AgentPadSaveBaseline ([pscustomobject]@{Mock=$true}) $cancel -TimeoutSeconds 0} 'PAD_SAVE_UNKNOWN' 'Stale Saved state cannot authorize this save'
    Reset-PadMock 'save-observed'
    $script:padStatusSequence=@('saved')
    Assert-Rejected {Wait-AgentPadSaved ([pscustomobject]@{Mock=$true}) $cancel -TimeoutSeconds 0} 'PAD_SAVE_UNKNOWN' 'Saved without a fresh saving state cannot authorize this save'
    [IO.File]::WriteAllText($cancel,'cancel',$script:AgentEncoding)
    $readsBeforeCancel=$script:padSnapshotReads
    Assert-Rejected {Wait-AgentPadSaved ([pscustomobject]@{Mock=$true}) $cancel} 'CANCELLED' 'Save helper observes cancellation before polling UI'
    Assert-Case ($script:padSnapshotReads -eq $readsBeforeCancel) 'Cancelled save helper performs no further UI inspection'
    [IO.File]::Delete($cancel)
} finally {
    # Remove the junction itself first; never recursively traverse a test link.
    if($junction -and [IO.Directory]::Exists($junction)){[IO.Directory]::Delete($junction)}
    $resolved=[IO.Path]::GetFullPath($temp)
    if(-not $resolved.StartsWith($testBase+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Unsafe test cleanup path.'}
    if(Test-Path -LiteralPath $resolved){Remove-Item -LiteralPath $resolved -Recurse -Force}
}
Write-Output ('PASS: '+$script:checks+' PAD contract/local mock checks. No live PAD/UIA/clipboard/flow execution was exercised.')
