"""Freeze the EX03 percent-like-text successor without modifying r5.

The measured PAD probe remains evidence for one fixed text value and one
numeric control.  This builder carries its captured Robin and complete script
into a new candidate, then composes a fixed-EX03-only adaptation that must earn
its own normal-Copilot/PAD acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'copilot/versions/20260915-excel-r5'
VERSION = '20260916-excel-r6'
BASE_COMMIT = '1701d8dd3ca88c2c60de443205e54a764e578fc9'
PROBE = ROOT / 'catalog/acceptance/issue38/probes/percent-text-write'
CAPTURED_FLOW = PROBE / 'captured-final.robin'
CAPTURED_ACTION = PROBE / 'captured-powershell-format-action-v2.robin'
CAPTURED_SCRIPT = PROBE / 'active-excel-format-sandwich.ps1.txt'
PROBE_EVIDENCE = [
    PROBE / 'acceptance.json',
    PROBE / 'two-run-result.json',
    PROBE / 'verification.json',
    PROBE / 'report.md',
]
SUPPORT_PATH = Path('support/EX03-TextWrite-FormatSandwich.ps1.txt')
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()


TEXT_MAPPINGS = [
    (1, 0, 0, 'TextSource1', '集計先', 'F7'),
    (1, 1, 0, 'TextSource2', '集計先', 'F8'),
    (1, 2, 0, 'TextSource3', '集計先', 'F9'),
    (2, 0, 0, 'TextSource4', '追記先', 'D5'),
    (2, 1, 0, 'TextSource5', '追記先', 'D6'),
    (2, 0, 2, 'TextSource6', '追記先', 'F5'),
    (2, 1, 2, 'TextSource7', '追記先', 'F6'),
]
NUMBER_MAPPINGS = [
    (1, 0, 1, 'NumberSource1', '集計先', 'G7'),
    (1, 1, 1, 'NumberSource2', '集計先', 'G8'),
    (1, 2, 1, 'NumberSource3', '集計先', 'G9'),
    (2, 0, 1, 'NumberSource4', '追記先', 'E5'),
    (2, 1, 1, 'NumberSource5', '追記先', 'E6'),
]
ALL_MAPPINGS = [
    (1, 0, 0, '集計先_F7', '集計先', 'F7'),
    (1, 0, 1, '集計先_G7', '集計先', 'G7'),
    (1, 1, 0, '集計先_F8', '集計先', 'F8'),
    (1, 1, 1, '集計先_G8', '集計先', 'G8'),
    (1, 2, 0, '集計先_F9', '集計先', 'F9'),
    (1, 2, 1, '集計先_G9', '集計先', 'G9'),
    (2, 0, 0, '追記先_D5', '追記先', 'D5'),
    (2, 0, 1, '追記先_E5', '追記先', 'E5'),
    (2, 0, 2, '追記先_F5', '追記先', 'F5'),
    (2, 1, 0, '追記先_D6', '追記先', 'D6'),
    (2, 1, 1, '追記先_E6', '追記先', 'E6'),
    (2, 1, 2, '追記先_F6', '追記先', 'F6'),
]


TEXT_WRITE_SCRIPT = r"""$ErrorActionPreference = 'Stop'
$targetPath = 'C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\runs\EX03-attempt1\work.xlsx'
$writes = @(
    [ordered]@{ Source = 'Data1[0][0]'; Sheet = '集計先'; Cell = 'F7'; Json = '%TextSource1Json%' },
    [ordered]@{ Source = 'Data1[1][0]'; Sheet = '集計先'; Cell = 'F8'; Json = '%TextSource2Json%' },
    [ordered]@{ Source = 'Data1[2][0]'; Sheet = '集計先'; Cell = 'F9'; Json = '%TextSource3Json%' },
    [ordered]@{ Source = 'Data2[0][0]'; Sheet = '追記先'; Cell = 'D5'; Json = '%TextSource4Json%' },
    [ordered]@{ Source = 'Data2[1][0]'; Sheet = '追記先'; Cell = 'D6'; Json = '%TextSource5Json%' },
    [ordered]@{ Source = 'Data2[0][2]'; Sheet = '追記先'; Cell = 'F5'; Json = '%TextSource6Json%' },
    [ordered]@{ Source = 'Data2[1][2]'; Sheet = '追記先'; Cell = 'F6'; Json = '%TextSource7Json%' }
)
$allowedTargets = @{
    '集計先' = @('F7', 'F8', 'F9')
    '追記先' = @('D5', 'D6', 'F5', 'F6')
}
$excel = [Runtime.InteropServices.Marshal]::GetActiveObject('Excel.Application')
$workbook = $null
$audit = @()
try {
    $matches = @()
    for ($index = 1; $index -le $excel.Workbooks.Count; $index++) {
        $candidate = $excel.Workbooks.Item($index)
        if ([string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)) {
            $matches += $candidate
        }
        else {
            [void][Runtime.InteropServices.Marshal]::ReleaseComObject($candidate)
        }
    }
    if ($matches.Count -ne 1) { throw ('Expected one exact target workbook, found ' + $matches.Count) }
    $workbook = $matches[0]
    foreach ($write in $writes) {
        $sheetName = [string]$write.Sheet
        $cellAddress = [string]$write.Cell
        if (-not $allowedTargets.ContainsKey($sheetName) -or $allowedTargets[$sheetName] -cnotcontains $cellAddress) {
            throw ('Target is outside the fixed EX03 text mapping: ' + $sheetName + '!' + $cellAddress)
        }
        $payload = [string]$write.Json | ConvertFrom-Json
        if ($payload.probe -isnot [string]) { throw ('Fixed text source is not a string: ' + $write.Source) }
        $worksheet = $null
        $cell = $null
        try {
            $worksheet = $workbook.Worksheets.Item($sheetName)
            $cell = $worksheet.Range($cellAddress)
            if ([bool]$cell.HasFormula) { throw ('Refusing to replace a formula cell: ' + $sheetName + '!' + $cellAddress) }
            $beforeValue = $cell.Value2
            $beforeValueType = if ($null -eq $beforeValue) { 'null' } else { $beforeValue.GetType().FullName }
            $beforeNumberFormat = [string]$cell.NumberFormat
            $beforePrefixCharacter = [string]$cell.PrefixCharacter
            try {
                $cell.NumberFormat = '@'
                $cell.Value2 = [string]$payload.probe
            }
            finally {
                $cell.NumberFormat = $beforeNumberFormat
            }
            $afterValue = $cell.Value2
            $afterValueType = if ($null -eq $afterValue) { 'null' } else { $afterValue.GetType().FullName }
            $afterNumberFormat = [string]$cell.NumberFormat
            $afterPrefixCharacter = [string]$cell.PrefixCharacter
            if ($afterValue -isnot [string] -or $afterValue -cne [string]$payload.probe) { throw ('Text value/type was not preserved: ' + $sheetName + '!' + $cellAddress) }
            if ($afterNumberFormat -cne $beforeNumberFormat) { throw ('Original number format was not restored: ' + $sheetName + '!' + $cellAddress) }
            if ($afterPrefixCharacter -cne $beforePrefixCharacter -or -not [string]::IsNullOrEmpty($afterPrefixCharacter)) { throw ('Prefix character changed or remained: ' + $sheetName + '!' + $cellAddress) }
            if ([bool]$cell.HasFormula) { throw ('A formula remained after text write: ' + $sheetName + '!' + $cellAddress) }
            $audit += [ordered]@{
                source = $write.Source
                target = $sheetName + '!' + $cellAddress
                before = $beforeValue
                beforeType = $beforeValueType
                beforeFormat = $beforeNumberFormat
                beforePrefix = $beforePrefixCharacter
                after = $afterValue
                afterType = $afterValueType
                afterFormat = $afterNumberFormat
                afterPrefix = $afterPrefixCharacter
            }
        }
        finally {
            if ($null -ne $cell) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell) }
            if ($null -ne $worksheet) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($worksheet) }
        }
    }
    $audit | ConvertTo-Json -Compress
}
finally {
    if ($null -ne $workbook) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($workbook) }
    if ($null -ne $excel) { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) }
}
"""


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def robin_script_action(script):
    escaped = script.rstrip('\r\n').replace('\\', '\\\\').replace("'", "\\'")
    return "Scripting.RunPowershellScript.RunScript Script: $'''" + escaped + "''' ScriptOutput=> PowershellOutput"


def fixed_mapping_section():
    lines = [
        '固定EX03の書込み前型区分（値は固定せず、DataTableから同じRunで取得する）:',
        '文字列7セルは採取済みJSON primitiveで文字列型を確認してから、内包スクリプトの一時@→Value2→元NumberFormat復元で一度だけ書く。',
    ]
    for data, row, col, variable, sheet, cell in TEXT_MAPPINGS:
        lines.append(f'- Data{data}[{row}][{col}] -> {variable}Json -> {sheet}!{cell} (text write)')
    lines.append('数値5セルは文字列化せず、採取済み通常WriteCellで一度だけ書く。')
    for data, row, col, variable, sheet, cell in NUMBER_MAPPINGS:
        lines.append(f'- Data{data}[{row}][{col}] -> {variable} -> {sheet}!{cell} (numeric WriteCell)')
    lines += [
        'この区分はSHA固定されたEX03 fixtureの文字列/数値だけに限定する。値自体をコードへ埋めず、空白、真偽値、日付、エラー、数式結果、任意オブジェクト、別fixtureへ一般化しない。',
        '全12セルは保存・クローズ・読取り専用再開後、同じsource/readbackを同じprobeキーでJSON化し、定数位置ごとに比較する。検証者の固定期待値はbundleへ入れない。',
    ]
    return '\n'.join(lines) + '\n'


CURRENT = '''Issue #38 EX03 / 20260916-excel-r6 候補の現在の範囲
この節だけがr5後継の追加範囲である。r5、EX03-r5-G1の不受入証跡、固定依頼、fixture、期待値、成功済みprobeは変更も再採取もしない。旧版の生成・Run結果を現版へ継承しない。
1. 固定EX03の入力2矩形、対象12セル、出力存在ガード、保存→クローズ→読取り専用再開、12個のJSON型照合を保持する。入力とひな形原本を編集せず、検証者が準備した作業コピーから未存在出力へだけSaveAsする。
2. 1701d8dで固定した文字列保持probeは、文字列100%と数値42.5の専用synthetic範囲、同一環境の2RunだけがPASSである。採取Robin、採取アクション、内包PowerShell全文、SHA、実行条件を04へ収録する。これはr6完成フローの成功ではない。
3. r6候補ではF6や特定値の事後修正を行わない。固定fixtureで文字列と確定した7 source位置をDataTableから書込み前に取得し、同じprobeキーでJSON化する。1つの内包スクリプトがJSONを文字列型と確認し、対応する7 destinationセルを各1回だけ書く。数値5セルは通常WriteCellのまま各1回だけ書く。
4. 内包スクリプトはアクティブExcel内で作業コピーの絶対FullNameが一致するブックをちょうど1冊だけ要求し、固定7組以外のsheet/cellを拒否する。対象セルが数式なら拒否する。各セルの元NumberFormatを取得し、一時的に@へ変更してValue2へ文字列を書き、finallyで元NumberFormatへ戻す。直後の値、System.String、元書式、prefix空、数式なしが一致しなければSaveAs前に失敗する。
5. 例外時もfinallyで元書式復元を試みる。復元自体を含むいずれかの検査が失敗した場合、PowerShellアクションを失敗させ、後続の数値書込み・SaveAs・完了状態へ進めない。権限、セキュリティ設定、Excelアプリ設定、安全ガードを変更しない。外部ファイル実行、ネットワーク、削除、上書きを行わない。
6. 確認範囲は固定EX03の文字列/数値だけ。PowerShell文字列への受渡しは固定fixtureのJSONに限定し、引用符・改行等を含む任意文字列へ一般化しない。例外復元構造は静的点検対象であり、例外注入の実機成功とは表示しない。
7. 回答は固定依頼の全工程を一つのRobinコードブロックへ入れる。06のr6統合構成は実装者候補であり、Copilot生成・無修正PAD保存・再コピー・Run1保全後Run2・独立照合を同版で完了するまでは受入済みと書かない。
'''


def measured_section(support_sha, support_text):
    captured_flow = CAPTURED_FLOW.read_bytes().decode('utf-8').rstrip('\r\n')
    captured_action = CAPTURED_ACTION.read_bytes().decode('utf-8').rstrip('\r\n')
    captured_script = CAPTURED_SCRIPT.read_bytes().decode('utf-8').rstrip('\r\n')
    return f'''1701d8dで固定した文字列保持probe（r6完成フローの受入ではない）
採取フロー完全原文: {relative(CAPTURED_FLOW)} / SHA-256 {sha(CAPTURED_FLOW)}
{captured_flow}

採取PowerShellアクション完全原文: {relative(CAPTURED_ACTION)} / SHA-256 {sha(CAPTURED_ACTION)}
{captured_action}

採取アクション内スクリプト完全原文: {relative(CAPTURED_SCRIPT)} / SHA-256 {sha(CAPTURED_SCRIPT)}
{captured_script}

採取済み実行条件: Power Fx OFF、Excel desktop、厳密な作業ブックFullName、Target!A2、source文字列100%と数値42.5、保存・クローズ・再読込を2Run。文字列はSystem.String、元書式G/標準、prefix空、数式なしを保持し、数値は通常WriteCellを使用した。未確認型・別文字列・別ブック・別PC/PAD版へ一般化しない。

r6の例外復元付き内包スクリプト候補（probe原文からの派生であり、r6ライブ受入前は未受入）
配置: {SUPPORT_PATH.as_posix()} / SHA-256 {support_sha}
実行条件: 固定EX03 fixture SHA一致、runs\\EX03-attempt1\\work.xlsxだけが書込み可能で開かれていること、出力が未存在、Excel desktop/PAD Power Fx OFF、source JSON 7件が文字列、許可targetが集計先!F7/F8/F9および追記先!D5/D6/F5/F6だけであること。スクリプトはRobinへ内包し、外部ファイルとして実行しない。
{support_text}
'''


def full_robin_example():
    lines = [
        "SET TransferState TO $'''NOT_STARTED'''",
        "IF (File.IfFile.Exists File: $'''C:\\\\Users\\\\yuuki\\\\ai-prompts-issue38\\\\catalog\\\\acceptance\\\\issue38\\\\runs\\\\EX03-attempt1\\\\照合結果.xlsx''') THEN",
        "    SET TransferState TO $'''OUTPUT_EXISTS_NO_WRITE'''",
        'ELSE',
        "    Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''C:\\\\Users\\\\yuuki\\\\ai-prompts-issue38\\\\catalog\\\\acceptance\\\\issue38\\\\fixtures\\\\EX03\\\\入力い.xlsx''' Visible: True ReadOnly: True UseMachineLocale: False Instance=> Input1",
        "    Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Input1 Name: $'''受取明細'''",
        "    Excel.ReadFromExcel.ReadCells Instance: Input1 StartColumn: $'''D''' StartRow: 4 EndColumn: $'''E''' EndRow: 6 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> Data1",
        '    Excel.CloseExcel.Close Instance: Input1',
        "    Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''C:\\\\Users\\\\yuuki\\\\ai-prompts-issue38\\\\catalog\\\\acceptance\\\\issue38\\\\fixtures\\\\EX03\\\\入力ろ.xlsx''' Visible: True ReadOnly: True UseMachineLocale: False Instance=> Input2",
        "    Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Input2 Name: $'''追加項目'''",
        "    Excel.ReadFromExcel.ReadCells Instance: Input2 StartColumn: $'''B''' StartRow: 2 EndColumn: $'''D''' EndRow: 3 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> Data2",
        '    Excel.CloseExcel.Close Instance: Input2',
        "    Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''C:\\\\Users\\\\yuuki\\\\ai-prompts-issue38\\\\catalog\\\\acceptance\\\\issue38\\\\runs\\\\EX03-attempt1\\\\work.xlsx''' Visible: True ReadOnly: False UseMachineLocale: False Instance=> Work",
    ]
    for data, row, col, variable, _, _ in TEXT_MAPPINGS:
        lines += [
            f'    SET {variable} TO Data{data}[{row}][{col}]',
            f"    Variables.ConvertCustomObjectToJson CustomObject: {{ 'probe': {variable} }} Json=> {variable}Json",
        ]
    lines.append('    ' + robin_script_action(TEXT_WRITE_SCRIPT).replace('\n', '\n    '))
    for data, row, col, variable, _, _ in NUMBER_MAPPINGS:
        lines.append(f'    SET {variable} TO Data{data}[{row}][{col}]')
    lines += [
        "    Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Work Name: $'''集計先'''",
        "    Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource1 Column: $'''G''' Row: 7",
        "    Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource2 Column: $'''G''' Row: 8",
        "    Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource3 Column: $'''G''' Row: 9",
        "    Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Work Name: $'''追記先'''",
        "    Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource4 Column: $'''E''' Row: 5",
        "    Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource5 Column: $'''E''' Row: 6",
        "    Excel.SaveExcel.SaveAs Instance: Work DocumentFormat: Excel.ExcelFormat.OpenXmlWorkbook DocumentPath: $'''C:\\\\Users\\\\yuuki\\\\ai-prompts-issue38\\\\catalog\\\\acceptance\\\\issue38\\\\runs\\\\EX03-attempt1\\\\照合結果.xlsx'''",
        '    Excel.CloseExcel.Close Instance: Work',
        "    Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''C:\\\\Users\\\\yuuki\\\\ai-prompts-issue38\\\\catalog\\\\acceptance\\\\issue38\\\\runs\\\\EX03-attempt1\\\\照合結果.xlsx''' Visible: True ReadOnly: True UseMachineLocale: False Instance=> Reopened",
        "    Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Reopened Name: $'''集計先'''",
        "    Excel.ReadFromExcel.ReadCells Instance: Reopened StartColumn: $'''F''' StartRow: 7 EndColumn: $'''G''' EndRow: 9 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> Readback1",
        "    Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Reopened Name: $'''追記先'''",
        "    Excel.ReadFromExcel.ReadCells Instance: Reopened StartColumn: $'''D''' StartRow: 5 EndColumn: $'''F''' EndRow: 6 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> Readback2",
        '    Excel.CloseExcel.Close Instance: Reopened',
    ]
    for data, row, col, name, _, _ in ALL_MAPPINGS:
        lines += [
            f'    SET SourceCell TO Data{data}[{row}][{col}]',
            f'    SET SavedCell TO Readback{data}[{row}][{col}]',
            "    Variables.ConvertCustomObjectToJson CustomObject: { 'probe': SourceCell } Json=> SourceCellJson",
            "    Variables.ConvertCustomObjectToJson CustomObject: { 'probe': SavedCell } Json=> SavedCellJson",
            f'    SET {name}_ValueTypeMatch TO SourceCellJson = SavedCellJson',
        ]
    lines += ["    SET TransferState TO $'''SAVED_REOPENED_12_JSON_COMPARISONS_READY'''", 'END']
    return '\n'.join(lines) + '\n'


def build(destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Candidate exists; sealed versions must not be overwritten')
    manifest = json.loads((BASE / 'manifest.json').read_bytes())
    for record in manifest['source_files']:
        assert sha(BASE / record['path']) == record['sha256']
    assert sha(BASE / manifest['instruction_path']) == manifest['instruction_sha256']
    assert sha(BASE / manifest['bundle_path']) == manifest['bundle_sha256']
    probe_acceptance = json.loads((PROBE / 'acceptance.json').read_bytes())
    assert probe_acceptance['status'] == 'PASS_LOCAL_PROBE_ONLY'
    assert probe_acceptance['baseline_commit'] == 'f134afe1958d3acc1601e2861cec4139d2b13310'

    (destination / 'knowledge').mkdir(parents=True)
    (destination / SUPPORT_PATH.parent).mkdir(parents=True)
    support_bytes = TEXT_WRITE_SCRIPT.encode('utf-8')
    (destination / SUPPORT_PATH).write_bytes(support_bytes)
    support_sha = sha(destination / SUPPORT_PATH)
    mapping = fixed_mapping_section()
    measured = measured_section(support_sha, TEXT_WRITE_SCRIPT.rstrip('\r\n'))
    for record in manifest['source_files']:
        source = BASE / record['path']
        content = source.read_bytes().decode('utf-8')
        name = Path(record['path']).name
        if name.startswith('PAD-Robin-00-'):
            content = content.rstrip('\r\n') + '\n\n' + CURRENT + mapping
        elif name.startswith('PAD-Robin-04-'):
            content = content.rstrip('\r\n') + '\n\n' + CURRENT + mapping + '\n' + measured
        elif name.startswith('PAD-Robin-06-'):
            content = content.rstrip('\r\n') + '\n\n' + CURRENT + mapping
            content += '\nEX03 r6統合構成例（実装者候補。Copilot生成・PAD実行前は未受入）\n'
            content += '固定fixtureの値は埋めず、DataTableから同じRunで取得する。文字列7セルを先に一度だけ安全書込みし、数値5セルを通常WriteCellで一度だけ書く。F6または特定値だけの事後修正ではない。\n'
            content += full_robin_example()
        (destination / record['path']).write_bytes(content.encode('utf-8'))

    original = (BASE / 'agent-instructions.txt').read_bytes().decode('utf-8')
    prefix = original.split('【Excel値転記・20260915-excel-r5候補】', 1)[0]
    instructions = prefix + '''【Excel値転記・20260916-excel-r6候補】
標準入力は同版の指示全文＋bundle実添付です。r5、EX03-r5-G1、成功済みprobeを現版の受入へ継承しません。00/04/06末尾の「EX03 / 20260916-excel-r6」だけを後継追加範囲として参照します。
固定EX03の入力・ひな形・作業コピー・未存在出力、2矩形、12対象位置、出力存在ガード、保存→閉じる→読取り専用再開、12個のJSON型比較を保持します。入力と原本はReadOnlyで開き、作業コピーだけを編集します。既存出力時は書込み経路へ入らず、ELSE内に全Excel処理を置きます。
1701d8dの文字列保持probeは、固定文字列100%と数値42.5、固定セル、同一PAD/Excel環境の2Runだけが確認済みです。04にある採取Robin・採取PowerShellアクション・内包スクリプト全文を根拠にしますが、probe成功をr6生成フローの成功へ転用しません。
r6ではF6や100%だけを後から修正しません。SHA固定されたEX03 fixtureで文字列の7 source位置をDataTableから書込み前に取得し、同じprobeキーのJSONで文字列型を確認します。04/06の内包スクリプトを一度実行し、集計先F7/F8/F9、追記先D5/D6/F5/F6を各1回だけ書きます。値はDataTableから取得し、コードへ固定値を埋めません。数値の5 source位置は文字列化せず、集計先G7/G8/G9、追記先E5/E6へ通常WriteCellで各1回だけ書きます。
内包スクリプトはruns\\EX03-attempt1\\work.xlsxの絶対FullNameに一致するアクティブブックが1冊だけであること、sheet/cellが上記7組だけであること、source JSONが文字列であること、対象セルが数式でないことを検査します。各セルの元NumberFormatを保存し、一時的に@へ変更してValue2へ文字列を書き、finallyで元NumberFormatへ復元します。直後のSystem.String、値、元書式、prefix空、数式なしを検査し、失敗時はSaveAsや完了状態へ進みません。
PowerShellはRobinの採取済みRunScriptアクションへ全文を内包します。外部ps1、ネットワーク、削除、権限変更、セキュリティ・Excel設定変更を要求しません。必要条件はWindows上のPAD Power Fx OFF、Excel desktop、固定fixture SHA一致、検証者が準備した未保存作業コピー、未存在出力です。例外復元構造は静的点検対象であり、例外注入を実行済みとは書きません。
固定EX03の文字列/数値以外、引用符や改行等を含む任意文字列、空白、真偽値、日付、エラー、数式結果、オブジェクト、別fixture、他PC/PAD版へ一般化しません。未知の型や条件が必要ならコードを出さず追加採取を示します。
SaveAs後に閉じ、出力をReadOnlyで再開し、2矩形をTypedValuesで再取得します。source/readbackの12対応位置を同じprobeキーで個別JSON化し、12個のValueTypeMatchを残します。検証者専用の固定期待値を回答へ推測・埋込みしません。対象外全セル、数式、実効書式、原本SHAは独立検査を維持します。
回答は部分フローにせず、固定依頼の全工程を一つのRobinコードブロックへ入れます。06の統合構成は候補であり、同版の通常M365 Copilot生成、無修正PAD貼付け・保存・再コピー、Run1成果物保全後のRun2、独立照合が終わるまでは完成・実行済みと表示しません。
'''
    (destination / 'agent-instructions.txt').write_text(instructions, encoding='utf-8', newline='\n')
    subprocess.run([
        'pwsh', '-NoProfile', '-File', str(ROOT / 'tools/Build-KnowledgeBundle.ps1'),
        '-Root', str(destination), '-KnowledgeDirectory', 'knowledge',
        '-OutputPath', 'knowledge/PAD-Robin-Knowledge-Bundle.txt'
    ], check=True)

    evidence_inputs = dict(manifest.get('evidence_inputs', {}))
    for path in [CAPTURED_FLOW, CAPTURED_ACTION, CAPTURED_SCRIPT, *PROBE_EVIDENCE]:
        evidence_inputs[relative(path)] = sha(path)
    manifest.update(
        version=VERSION,
        status='FROZEN_CANDIDATE_EX03_PERCENT_TEXT_INTEGRATED_NOT_LIVE_ACCEPTED',
        inherits_live_acceptance=False,
        base_candidate='20260915-excel-r5',
        base_commit=BASE_COMMIT,
        instruction_sha256=sha(destination / 'agent-instructions.txt'),
        instruction_utf16=len(instructions.encode('utf-16-le')) // 2,
        bundle_sha256=sha(destination / manifest['bundle_path']),
        evidence_inputs=evidence_inputs,
        builder='tools/Build-Issue38Ex03CandidateR6.py',
        support_files=[{
            'path': SUPPORT_PATH.as_posix(),
            'sha256': support_sha,
            'bytes': (destination / SUPPORT_PATH).stat().st_size,
            'runtime': 'embedded_in_robin_not_loaded_from_disk',
        }],
    )
    assert manifest['instruction_utf16'] <= 8000
    for record in manifest['source_files']:
        record.update(
            sha256=sha(destination / record['path']),
            bytes=(destination / record['path']).stat().st_size,
        )
    manifest['evidence'].update(
        copilot='NOT_RUN_AT_FREEZE',
        pad='R6_CANDIDATE_NOT_RUN_PROBE_NOT_INHERITED',
        percent_text_write='PAD_TWO_RUN_FIXED_100_PERCENT_TEXT_AND_NUMERIC_SCOPE',
        percent_text_flow_sha256=sha(CAPTURED_FLOW),
        percent_text_action_sha256=sha(CAPTURED_ACTION),
        percent_text_script_sha256=sha(CAPTURED_SCRIPT),
        percent_text_scope='Synthetic text 100% and numeric 42.5 only; r6 seven-cell adaptation requires same-version live acceptance',
        candidate_adaptation='EXCEPTION_SAFE_FIXED_EX03_SEVEN_TEXT_POSITIONS_NOT_LIVE_ACCEPTED',
        candidate_script_sha256=support_sha,
    )
    (destination / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8', newline='\n'
    )
    print(json.dumps({
        key: manifest[key]
        for key in ['version', 'instruction_utf16', 'instruction_sha256', 'bundle_sha256']
    }, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT / 'copilot/versions' / VERSION)
    build(parser.parse_args().output)
