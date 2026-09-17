#!/usr/bin/env python3
"""Build the local-only EX03 r12 successor without running Copilot, PAD, or Excel.

r12 keeps the frozen r11 package and fixed EX03 contract unchanged.  It derives
one prepared teaching Robin from the r11 full-shape Robin and the independently
reviewed R2/R3 JSON-file handoff, exact success gate, and exception-restoration
probe.  All SHA-256 and newline/provenance fields are calculated from bytes read
or written by this builder; no live result is inherited as r12 acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "copilot/versions/20260917-excel-r11"
VERSION = "20260917-excel-r12"
BASE_COMMIT = "2e5ec6b8a01adc3cd63b2ef69c0871576bba47e9"
PROBE = ROOT / "catalog/acceptance/issue38/probes/ex03-r2-r3-string-stop"
TRIAL = PROBE / "trials/EX03-R2R3-POSTFIX-20260917-T1"
CORRECTION = ROOT / "catalog/acceptance/issue38/review/20260917-r4-r11-manifest-correction.json"
R11_MARKER = "Issue #38 EX03 / 20260917-excel-r11 候補の現在の範囲"
R11_INSTRUCTION_MARKER = "【Excel値転記・20260917-excel-r11候補】"

SCRIPT_SUPPORT = Path("support/EX03-R12-JSON-File-Handoff.ps1.txt")
NORMAL_SUPPORT = Path("support/EX03-R12-Prepared-Normal.robin")
NEGATIVE_SUPPORT = Path("support/EX03-R12-Prepared-Exception-Negative.robin")
CONTRACT_SUPPORT = Path("support/EX03-R12-JSON-Handoff-Contract.txt")

INPUTS = {
    "r11_manifest": BASE / "manifest.json",
    "r11_instruction": BASE / "agent-instructions.txt",
    "r11_bundle": BASE / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "r11_robin": BASE / "support/EX03-R11-Independent-PAD-Recopy.robin",
    "r11_script": BASE / "support/EX03-R11-Independent-Minimal-FormatSandwich.ps1.txt",
    "r11_contract": BASE / "support/EX03-R11-Minimal-Structural-Contract.txt",
    "r2r3_script": PROBE / "embedded-safe.ps1.txt",
    "r2r3_normal": PROBE / "candidate-normal-postfix.robin",
    "r2r3_negative": PROBE / "candidate-negative-postfix.robin",
    "trial_normal_recopy": TRIAL / "normal/pad-recopy-before-run.robin",
    "trial_negative_recopy": TRIAL / "negative/pad-recopy-before-run.robin",
    "trial_preflight": TRIAL / "preflight.json",
    "trial_final": TRIAL / "final-verification.json",
    "r11_formal": ROOT / "catalog/acceptance/issue38/cycles/EX03-r11-G1/acceptance-status.json",
    "r11_aux": ROOT / "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/acceptance-status.json",
    "r11_guard": ROOT / "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1/acceptance-status.json",
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "fixed_expected": ROOT / "catalog/acceptance/issue38/expected.json",
}

EXPECTED = {
    "r11_manifest": "295306ea7e2e45da8cf77dec2784e94ea8ea8333da0df6a4000f83e9228b509e",
    "r11_instruction": "bceb1c7e4f47c0cd6a92ad698d08108175002bffcaaaff492a309ca74a122aa1",
    "r11_bundle": "2d95ce344ff66195061fd15010d13b75937888575fa2345fb543ae2115242f69",
    "r11_robin": "148267f09f53d74db1059cee823a4a2e159f2bbebfa249d3a25c996796fa765b",
    "r11_script": "068e676d70c373a9cf8203d19f6154e38460f609c4fdf774dbef1528f68fc7ae",
    "r11_contract": "ffbe75f9803435c55341f2d7db73e85b5ce5ec961f637734da38b6ee332a1ec9",
    "r2r3_script": "aa2091327607b9ed1496f5ebb4a8bca2968e95e56ae3337f541651141e55f571",
    "r2r3_normal": "aaac1b7c04156f8038d26f6671c692faede55c91097cbf3f5d4c575348ae3851",
    "r2r3_negative": "a1ff8f503d485402ffdbb98248a52e62eedf98ac27f95d566dbaca1800dfcd1f",
    "trial_normal_recopy": "28f1349b68125ab32e0f2139fb967b91f99377a756f9b8d9bbf1f354c9b5c0e1",
    "trial_negative_recopy": "d1459baf69c8d412674599f2fbb0dec6772b74e8fd8104c694dcb1cea438599f",
    "trial_preflight": "229c324de91f82171f99713bbc6388e800e6f995f53ceebd9e77952c85cfcb4c",
    "trial_final": "6bf5de9c8df3d8526830fa85a5f34cea6dffc724ce0961c4a359ebaa796671d9",
    "r11_formal": "87536bbc5da9347401e2e9d3982e8d77caaad1d5fb5b42bf782e71c5aca167b4",
    "r11_aux": "4b76432cf58b7182ed1284f12abaa807794bc2f0ae53e385506e0b662938d6ea",
    "r11_guard": "53bca22d6b655592e1da6a6b59f45082f8d696575b1d536d5b36b5a794937e0a",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "fixed_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}

TEACHING_ROOT = r"C:\Users\yuuki\ai-prompts-issue38\catalog\teaching\excel-r12-example"
OLD_TEACHING_ROOT = r"C:\Users\yuuki\ai-prompts-issue38\catalog\teaching\excel-r8-example"
SUCCESS_OUTPUT = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'
NORMAL_MODE = "NORMAL"
NEGATIVE_MODE = "INJECT_AFTER_FORMAT_CHANGE"

FIXED_ROOT = r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38"
FIXED_COMPLETION_TERMS = [
    FIXED_ROOT + r"\\fixtures\\EX03\\入力い.xlsx",
    FIXED_ROOT + r"\\fixtures\\EX03\\入力ろ.xlsx",
    FIXED_ROOT + r"\\runs\\EX03-attempt1\\work.xlsx",
    FIXED_ROOT + r"\\runs\\EX03-attempt1\\照合結果.xlsx",
    "受取明細",
    "追加項目",
    "集計先",
    "追記先",
]
UNIQUE_GRADER_STRINGS = ["春", "夏", "秋", "項目甲", "項目乙"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def newline_metrics_bytes(raw: bytes) -> dict[str, object]:
    crlf = raw.count(b"\r\n")
    return {
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "crlf_count": crlf,
        "lf_only_count": raw.count(b"\n") - crlf,
        "final_lf": raw.endswith(b"\n"),
        "final_crlf": raw.endswith(b"\r\n"),
    }


def file_record(path: Path) -> dict[str, object]:
    return {"path": relative(path), **newline_metrics_bytes(path.read_bytes())}


def replace_once(value: str, old: str, new: str, label: str) -> str:
    if value.count(old) != 1:
        raise ValueError(f"Expected exactly one {label}, found {value.count(old)}")
    return value.replace(old, new, 1)


def replace_between(value: str, start: str, end: str, replacement: str, label: str) -> str:
    if value.count(start) != 1 or value.count(end) != 1:
        raise ValueError(f"Unexpected boundaries for {label}")
    begin = value.index(start)
    finish = value.index(end, begin)
    return value[:begin] + replacement + value[finish:]


def robin_literal(value: str) -> str:
    return "$'''" + value.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"') + "'''"


def script_action(script: str) -> str:
    escaped = script.rstrip("\r\n").replace("\\", "\\\\").replace("'", "\\'")
    return "Scripting.RunPowershellScript.RunScript Script: $'''" + escaped + "''' ScriptOutput=> PowershellOutput"


def decode_robin_string(value: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(value):
        if value[index] == "\\" and index + 1 < len(value) and value[index + 1] in {"\\", "'", '"'}:
            result.append(value[index + 1])
            index += 2
        else:
            result.append(value[index])
            index += 1
    return "".join(result)


def embedded_script(robin: str) -> str:
    prefix = "Scripting.RunPowershellScript.RunScript Script: $'''"
    suffix = "''' ScriptOutput=> PowershellOutput"
    start = robin.index(prefix) + len(prefix)
    end = robin.index(suffix, start)
    return decode_robin_string(robin[start:end])


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def build_script(source: str) -> tuple[str, list[str]]:
    """Mechanically adapt the reviewed R2/R3 script to the 7-text teaching shape."""
    script = source.replace("\r\n", "\n")
    transforms: list[str] = []

    script = replace_once(
        script,
        r"$targetPath = 'C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r2-r3-string-stop\runtime\work.xlsx'",
        rf"$targetPath = '{TEACHING_ROOT}\work-copy.xlsx'",
        "R2/R3 target path",
    )
    transforms.append("target_path_to_independent_teaching_slot")
    script = replace_once(
        script,
        r"$jsonRoot = 'C:\Users\yuuki\ai-prompts-issue38\catalog\acceptance\issue38\probes\ex03-r2-r3-string-stop\runtime'",
        rf"$jsonRoot = '{TEACHING_ROOT}'",
        "R2/R3 JSON root",
    )
    transforms.append("json_root_to_dedicated_teaching_work_area")

    payload_block = "    $payloads = @(\n" + ",\n".join(
        f"        (Get-Content -LiteralPath (Join-Path $jsonRoot 'source-{index}.json') -Raw -Encoding UTF8 | ConvertFrom-Json)"
        for index in range(1, 8)
    ) + "\n    )\n"
    script = replace_between(
        script,
        "    $payloads = @(\n",
        "    $modePayload = ",
        payload_block,
        "payload file list",
    )
    transforms.append("payload_files_4_to_7_text_slots")

    type_block = (
        "    for ($index = 0; $index -lt 7; $index++) {\n"
        "        if ($payloads[$index].probe -isnot [string]) { throw ('TEXT_PAYLOAD_TYPE_' + ($index + 1)) }\n"
        "    }"
    )
    script = replace_between(
        script,
        "    for ($index = 0; $index -lt 3; $index++) {\n",
        "\n\n    $targetPath = [IO.Path]::GetFullPath($targetPath)",
        type_block,
        "bounded payload type gate",
    )
    transforms.append("remove_unconfirmed_numeric_json_generalization_and_validate_7_strings")

    writes = [
        ("Data1[0][0]", "教材出力一", "J4", 0),
        ("Data1[1][0]", "教材出力一", "J5", 1),
        ("Data1[2][0]", "教材出力一", "J6", 2),
        ("Data2[0][0]", "教材出力二", "B10", 3),
        ("Data2[1][0]", "教材出力二", "B11", 4),
        ("Data2[0][2]", "教材出力二", "D10", 5),
        ("Data2[1][2]", "教材出力二", "D11", 6),
    ]
    write_lines = []
    for index, (source_label, sheet, address, payload_index) in enumerate(writes):
        comma = "," if index + 1 < len(writes) else ""
        write_lines.append(
            f"        @('{source_label}', '{sheet}', '{address}', [string]$payloads[{payload_index}].probe){comma}"
        )
    write_block = "    $writes = @(\n" + "\n".join(write_lines) + "\n    )\n"
    script = replace_between(
        script,
        "    $writes = @(\n",
        "    $writesCompleted = 0",
        write_block,
        "teaching write map",
    )
    transforms.append("write_map_3_to_7_existing_r11_text_slots")

    script = replace_once(
        script,
        "            $worksheet = $workbook.Worksheets.Item('Target')\n"
        "            $cell = $worksheet.Range([string]$write[1])\n"
        "            if ([bool]$cell.HasFormula) { throw ('FORMULA_TARGET_' + $write[1]) }",
        "            $sheetName = [string]$write[1]\n"
        "            $cellAddress = [string]$write[2]\n"
        "            $worksheet = $workbook.Worksheets.Item($sheetName)\n"
        "            $cell = $worksheet.Range($cellAddress)\n"
        "            if ([bool]$cell.HasFormula) { throw ('FORMULA_TARGET_' + $sheetName + '!' + $cellAddress) }",
        "worksheet and cell slots",
    )
    script = replace_once(
        script,
        "                if ($mode -ceq 'INJECT_AFTER_FORMAT_CHANGE' -and [string]$write[1] -ceq 'A2') {",
        "                if ($mode -ceq 'INJECT_AFTER_FORMAT_CHANGE' -and $writesCompleted -eq 0) {",
        "first-write exception injection",
    )
    script = replace_once(script, "$cell.Value2 = [string]$write[2]", "$cell.Value2 = [string]$write[3]", "write value slot")
    script = replace_once(
        script,
        "            if ($cell.Value2 -isnot [string] -or [string]$cell.Value2 -cne [string]$write[2]) {\n"
        "                throw ('TEXT_VALUE_TYPE_' + $write[1])\n"
        "            }\n"
        "            if ([string]$cell.NumberFormat -cne $beforeFormat) { throw ('FORMAT_NOT_RESTORED_' + $write[1]) }\n"
        "            if ([string]$cell.PrefixCharacter -cne '') { throw ('PREFIX_CHANGED_' + $write[1]) }\n"
        "            if ([bool]$cell.HasFormula) { throw ('FORMULA_AFTER_WRITE_' + $write[1]) }",
        "            if ($cell.Value2 -isnot [string] -or [string]$cell.Value2 -cne [string]$write[3]) {\n"
        "                throw ('TEXT_VALUE_TYPE_' + $sheetName + '!' + $cellAddress)\n"
        "            }\n"
        "            if ([string]$cell.NumberFormat -cne $beforeFormat) { throw ('FORMAT_NOT_RESTORED_' + $sheetName + '!' + $cellAddress) }\n"
        "            if ([string]$cell.PrefixCharacter -cne '') { throw ('PREFIX_CHANGED_' + $sheetName + '!' + $cellAddress) }\n"
        "            if ([bool]$cell.HasFormula) { throw ('FORMULA_AFTER_WRITE_' + $sheetName + '!' + $cellAddress) }",
        "post-write checks",
    )
    script = replace_once(script, "$writesCompleted -ne 3", "$writesCompleted -ne 7", "normal write count")
    script = replace_once(script, "text_writes = 3", "text_writes = 7", "success write count")
    transforms.extend([
        "per_target_sheet_and_cell_slots",
        "forced_exception_remains_after_format_before_value",
        "normal_success_count_7",
    ])

    script = script.rstrip("\n") + "\n"
    if "%TextSource" in script or "%RunMode" in script:
        raise ValueError("Input-derived PAD values remain interpolated in PowerShell source")
    return script, transforms


def build_robin(base: str, script: str, mode: str) -> str:
    old_robin_root = OLD_TEACHING_ROOT.replace("\\", "\\\\")
    new_robin_root = TEACHING_ROOT.replace("\\", "\\\\")
    normalized = base.replace("\r\n", "\n").replace(old_robin_root, new_robin_root)
    prefix = "Scripting.RunPowershellScript.RunScript Script: $'''"
    suffix = "''' ScriptOutput=> PowershellOutput"
    start = normalized.index(prefix)
    finish = normalized.index(suffix, start) + len(suffix)
    skeleton = normalized[:start] + "__R12_SCRIPT_ACTION__" + normalized[finish:]
    lines = skeleton.splitlines()
    marker_index = next(index for index, line in enumerate(lines) if "__R12_SCRIPT_ACTION__" in line)

    work_launch = (
        "    Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: "
        + robin_literal(TEACHING_ROOT + r"\work-copy.xlsx")
        + " Visible: True ReadOnly: False UseMachineLocale: False Instance=> Work"
    )
    if lines.count(work_launch) != 1:
        raise ValueError("Expected one r11 teaching work launch")
    lines.remove(work_launch)
    marker_index = next(index for index, line in enumerate(lines) if "__R12_SCRIPT_ACTION__" in line)

    handoff = [
        f"    SET RunMode TO {robin_literal(mode)}",
        "    Variables.ConvertCustomObjectToJson CustomObject: { 'probe': RunMode } Json=> RunModeJson",
    ]
    for index in range(1, 8):
        handoff.append(
            "    File.WriteText File: "
            + robin_literal(TEACHING_ROOT + rf"\source-{index}.json")
            + f" TextToWrite: TextSource{index}Json AppendNewLine: False IfFileExists: File.IfFileExists.Overwrite Encoding: File.FileEncoding.UTF8"
        )
    handoff.append(
        "    File.WriteText File: "
        + robin_literal(TEACHING_ROOT + r"\mode.json")
        + " TextToWrite: RunModeJson AppendNewLine: False IfFileExists: File.IfFileExists.Overwrite Encoding: File.FileEncoding.UTF8"
    )
    handoff.extend([work_launch, "    " + script_action(script)])

    before = lines[:marker_index]
    after = lines[marker_index + 1 :]
    if not after or after[-1] != "END":
        raise ValueError("Unexpected r11 output guard boundary")
    body = after[:-1]
    gated_body: list[str] = []
    numeric_flag_written = False
    for line in body:
        if line.startswith("    Excel.WriteToExcel.WriteCell") and not numeric_flag_written:
            gated_body.append("            SET NumericWriteEntered TO True")
            numeric_flag_written = True
        if line.startswith("    Excel.SaveExcel.SaveAs"):
            gated_body.append("            SET SaveAsEntered TO True")
        gated_body.append("        " + line)
    if not numeric_flag_written:
        raise ValueError("Numeric write boundary missing")

    before.insert(1, "SET ScriptGatePassed TO False")
    before.insert(2, "SET NumericWriteEntered TO False")
    before.insert(3, "SET SaveAsEntered TO False")
    result = before + handoff + [
        f"    IF PowershellOutput = {robin_literal(SUCCESS_OUTPUT)} THEN",
        f"        IF RunMode = {robin_literal(NORMAL_MODE)} THEN",
        "            SET ScriptGatePassed TO True",
        *gated_body,
        "        ELSE",
        "            Excel.CloseExcel.Close Instance: Work",
        "            SET TransferState TO $'''MODE_NOT_NORMAL_NO_SAVE'''",
        "        END",
        "    ELSE",
        "        Excel.CloseExcel.Close Instance: Work",
        "        SET TransferState TO $'''SCRIPT_NOT_SUCCESS_NO_SAVE'''",
        "    END",
        "END",
    ]
    return "\r\n".join(result) + "\r\n"


R12_SCOPE = """Issue #38 EX03 / 20260917-excel-r12 候補の現在の範囲
この節だけがr11後継の追加範囲である。固定依頼・期待値、凍結r11、正式r11 delivery-contract FAIL、補助検証、既存output guard、旧558 raw差分を変更せず、どの旧PASSもr12のCopilot生成・EX03統合PASSへ継承しない。
1. R2/R3で、DataTable値をJSON primitiveへ変換し専用作業領域のUTF-8 JSONファイルへ書き、PowerShellはGet-Content -LiteralPath -Raw -Encoding UTF8とConvertFrom-Jsonだけで読む経路を確認した。入力由来のセル値をPowerShellソースへ直接補間しない。
2. 同じR2/R3で、PowerShell出力がexact success JSONかつRunModeがNORMALの場合だけ後続の数値WriteCellとSaveAsへ進む。ERROR、空出力、想定負例出力、別modeはWorkを閉じ、成功状態・後続書込み・SaveAsへ進まない。
3. 各文字列セルは非formula、元Value2型・NumberFormat・PrefixCharacter・HasFormulaを保持してから一時@へ変更する。Value2書込みまたは直後検査に例外があっても内側finallyで元NumberFormatを復元する。確認済み負例は最初のセルの書式変更直後に意図的例外を発生させ、値・型・書式・prefix・formula不変、成功ゲート不通過、後続書込み・SaveAsなしを確認した。
4. 数値JSONのDouble/Decimal許容は固定R2/R3 probeだけの観測であり、未確認の整数型や別値へ一般化しない。r12正式形では7文字列だけをファイルhandoffし、数値5位置は従来どおりPAD WriteCellと保存後JSON比較を使う。
5. r12 prepared Robinは凍結r11の12セルshapeへ上記採取済み構文を機械適用した非ライブ候補である。通常版と負例版はRunMode一行だけが異なる。support scriptは末尾LFあり、Robin内包scriptはaction表現上その末尾LFだけを除く。SHA・CRLF・LF-only件数・対応関係はbuilderが実ファイルから算出する。
6. r11 manifestのsource_recopy_lf_only_count 87は実体57への訂正記録を別追加し、r11本体は変更しない。別のsource_candidate 87は別原文の実測値として保持する。
7. r12は未送信・未貼付け・未実行である。Copilot送信0、r12 PAD/Excel Run 0、全件回帰未実施、GitHub書込み0。text/number以外、別shape、空白、真偽値、日付、error、formula result、任意object、別PC/PAD版へ一般化しない。
"""

EXAMPLE_MAPPING = """r12独立教材例のデータ対応:
- source-one.xlsx / 教材入力一 H3:I5 -> 教材出力一 J4:K6。各行はtext, number。
- source-two.xlsx / 教材入力二 C7:E8 -> 教材出力二 B10:D11。各行はtext, number, text。
- work-copy.xlsxだけを編集し、未存在のexample-result.xlsxへSaveAsする。JSON handoffファイルは同じ教材専用作業領域のsource-1.jsonからsource-7.jsonとmode.jsonである。
- text 7位置はDataTableからJSONファイルへ渡して1 RunScript内で各1回、number 5位置はexact successかつNORMALの内側で通常WriteCellにより各1回だけ書く。保存・クローズ・ReadOnly再開後に12位置を個別JSON比較する。
- 固定するもの: 命令名、引数名、mode、DataTable添字、型の役割、依存順、分岐、1 RunScript、7 JSON writes、5 numeric writes、12 JSON comparisons、失敗時no-save。
- 依頼から変更するもの: 同じ確認範囲内のpath、存在するsheet名、3x2と2x3のrectangle、target、work copy、未存在output、data slot由来label。
"""

STRUCTURAL_CONTRACT_BASE = """EX03 r12 JSON-file handoff and stop-gate structural contract
1. Use the complete same-version prepared normal Robin as the adaptation source. Change only request-derived data slots and teaching-only labels; do not reconstruct other actions.
2. Convert all seven text DataTable values and NORMAL mode to JSON in PAD, then write eight UTF-8 files in the dedicated run work area before RunScript. Never interpolate a source value or its JSON text into PowerShell source.
3. PowerShell must read seven source JSON files plus mode.json with Get-Content -LiteralPath -Raw -Encoding UTF8 and ConvertFrom-Json. It must accept only seven System.String payloads in this path.
4. For every text target, capture value/type/format/prefix/formula, set temporary @, write Value2, and restore the original NumberFormat in an inner finally. The injected exception point stays immediately after temporary format and before Value2.
5. Only the exact success JSON plus NORMAL mode may enclose five numeric WriteCell actions and SaveAs. Any other output or mode closes Work without the completion path.
6. Preserve the existing-output guard, exact workbook one-match guard, five numeric writes, twelve saved JSON comparisons, source/target shape, non-formula checks, and no-overwrite behavior.
7. The fixed R2/R3 normal and forced-exception Runs are source evidence only. r12 has no Copilot send, PAD save/re-copy, or integrated Run, and inherits no PASS.
8. Emit the formal answer in exactly one text code block. If any required structural check fails, emit no Robin and explain the failed check; never repair a generated answer after emission.
"""

R12_INSTRUCTIONS = """【Excel値転記・20260917-excel-r12候補】
標準入力は同版の指示全文＋bundle実添付です。固定依頼・期待値、旧版、正式r11のdelivery-contract FAIL、補助検証PASS、既存output guard PASS、旧558 raw差分FAILを分離して保持し、いずれも今回のr12生成・PAD受入へ継承しません。00/04/06末尾の「EX03 / 20260917-excel-r12」だけを追加範囲として参照します。
r12は06末尾の完全なprepared normal Robinから、依頼本文で列挙されたdata slotと教材専用labelだけを一貫置換して作ります。入力由来のセル値やJSON文字列をPowerShellソースへ直接補間しません。教材専用path・sheet・target・labelを残さず、固定試験のpath、sheet、target cell、grader値、完成Robinを教材から補いません。
文字列7位置は同じRunのDataTableからJSON primitive化し、固定Run作業領域内のsource-1.jsonからsource-7.jsonへUTF-8で書きます。RunModeもmode.jsonへ書きます。既存output guardはこれらの生成、Work起動、書込みより前に置きます。PowerShellは固定ファイル名をGet-Content -LiteralPath -Raw -Encoding UTF8とConvertFrom-Jsonで読み、7 payloadがSystem.String、modeがNORMALであることを先に検査します。
内包scriptは絶対FullName正規化後の`-ieq`で開いているWorkを一冊だけ選びます。各text targetで非formula、元Value2型・NumberFormat・PrefixCharacter・HasFormulaを保持し、一時`@`、Value2書込み、内側`finally`による元NumberFormat復元、直後の値・System.String・元format・prefix空・formulaなしを検査します。例外時もERROR JSONを返し、成功状態へ読み替えません。
PowerShell出力が`status=OK`、`mode=NORMAL`、`text_writes=7`、`formats_restored=true`のexact JSONで、かつPAD側RunModeがNORMALの場合だけ、数値5位置のWriteCellとSaveAsを実行します。空・ERROR・想定負例・別modeはWorkを閉じ、後続書込み・SaveAs・完成状態へ進みません。数値JSONのDouble/Decimal観測は固定probeだけなので、正式形の数値型判定へ一般化しません。
SaveAs後はcloseしてReadOnly再開し、2矩形をTypedValuesで再取得して12位置を個別JSON比較します。入力と原本はReadOnly、検証者が準備したwork copyだけ編集、既存output時はno-writeです。原本・対象外cell・formula・effective formatの独立検査と旧558 raw差分記録を維持します。
回答確定前に、1 RunScript、7 source JSON writes＋1 mode JSON write、PowerShell内7 file reads、内側finally復元、exact success＋NORMAL二重gate、5 numeric writes、1 SaveAs、12 JSON comparisons、失敗側close/no-saveを確認します。入力値の`%...Json%`直接補間、Invoke-Expression、外部ps1、network、delete、overwrite、権限・security・Excel設定変更を入れません。
回答は全工程を一つのtextコードブロックへ入れます。r12は通常M365 Copilot未送信、PAD保存・再コピー・Run1/Run2・成果物照合が未実施のローカル候補です。完成・実行済み・受入済みと表示しません。
"""


def build(destination: Path) -> dict[str, object]:
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Candidate exists; sealed versions must not be overwritten")

    actual = {name: sha256(path) for name, path in INPUTS.items()}
    if actual != EXPECTED:
        raise ValueError(f"Protected r11/R2/R3/fixed input hash mismatch: {actual}")

    manifest = json.loads(INPUTS["r11_manifest"].read_bytes())
    if manifest["version"] != "20260917-excel-r11":
        raise ValueError("Unexpected base candidate")
    for record in manifest["source_files"]:
        if sha256(BASE / record["path"]) != record["sha256"]:
            raise ValueError(f"Frozen r11 source mismatch: {record['path']}")
    for record in manifest["support_files"]:
        if sha256(BASE / record["path"]) != record["sha256"]:
            raise ValueError(f"Frozen r11 support mismatch: {record['path']}")

    formal = json.loads(INPUTS["r11_formal"].read_bytes())
    auxiliary = json.loads(INPUTS["r11_aux"].read_bytes())
    guard = json.loads(INPUTS["r11_guard"].read_bytes())
    preflight = json.loads(INPUTS["trial_preflight"].read_bytes())
    final = json.loads(INPUTS["trial_final"].read_bytes())
    correction = json.loads(CORRECTION.read_bytes())
    if formal["decision"]["failure_code"] != "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD":
        raise ValueError("Frozen r11 formal failure changed")
    if auxiliary["decision"]["formal_ex03_r11_g1_accepted"] or not auxiliary["decision"]["auxiliary_validation_passed"]:
        raise ValueError("Frozen r11 auxiliary boundary changed")
    if not guard["decision"]["existing_output_guard_passed"]:
        raise ValueError("Frozen r11 guard evidence changed")
    if preflight["result"] != "PASS_READY_FOR_NORMAL_ONE_RUN_ONLY":
        raise ValueError("R2/R3 preflight changed")
    if final["result"] != "PASS_NORMAL_AND_FORCED_EXCEPTION_ONE_RUN_EACH":
        raise ValueError("R2/R3 final evidence changed")

    r11_recopy_record = file_record(INPUTS["r11_robin"])
    corrected = correction["correction"]
    if corrected["recorded_value"] != 87 or corrected["corrected_value"] != r11_recopy_record["lf_only_count"]:
        raise ValueError("R4 r11 correction does not match actual recopy bytes")
    if corrected["source_sha256"] != r11_recopy_record["sha256"] or corrected["crlf_count"] != r11_recopy_record["crlf_count"]:
        raise ValueError("R4 correction identity mismatch")
    if correction["frozen_manifest"]["sha256"] != actual["r11_manifest"] or correction["frozen_manifest"]["modified"]:
        raise ValueError("R4 correction does not preserve frozen r11")

    fixed_runtime = str((PROBE / "runtime").resolve()).replace("\\", "\\\\")
    path_normalization: dict[str, bool] = {}
    for phase, trial_key, fixed_key in (
        ("normal", "trial_normal_recopy", "r2r3_normal"),
        ("negative", "trial_negative_recopy", "r2r3_negative"),
    ):
        trial_runtime = str((TRIAL / phase / "runtime").resolve()).replace("\\", "\\\\")
        normalized_trial = text(INPUTS[trial_key]).replace(trial_runtime, fixed_runtime)
        path_normalization[phase] = normalized_trial == text(INPUTS[fixed_key])
    if not all(path_normalization.values()):
        raise ValueError("R2/R3 PAD re-copy no longer maps to the fixed source by path only")

    source_script = text(INPUTS["r2r3_script"])
    script, script_transforms = build_script(source_script)
    base_robin = text(INPUTS["r11_robin"])
    normal_robin = build_robin(base_robin, script, NORMAL_MODE)
    negative_robin = build_robin(base_robin, script, NEGATIVE_MODE)
    if normal_robin.replace(
        "SET RunMode TO $'''NORMAL'''", "SET RunMode TO $'''INJECT_AFTER_FORMAT_CHANGE'''", 1
    ) != negative_robin:
        raise ValueError("Prepared normal/negative Robin differs beyond the fixed mode line")

    decoded_normal = embedded_script(normal_robin)
    decoded_negative = embedded_script(negative_robin)
    if decoded_normal != script.rstrip("\n") or decoded_negative != script.rstrip("\n"):
        raise ValueError("Embedded script differs from support script beyond the final LF")
    parser_module = load_module(
        "issue38_r12_powershell_parser", ROOT / "tools/Analyze-Issue38Ex03R10Generation.py"
    )
    if parser_module.parse_powershell(decoded_normal):
        raise ValueError("r12 embedded PowerShell does not parse cleanly")

    if normal_robin.count("Scripting.RunPowershellScript.RunScript") != 1:
        raise ValueError("r12 RunScript count changed")
    if normal_robin.count("File.WriteText File:") != 8:
        raise ValueError("r12 JSON file write count changed")
    if normal_robin.count("Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource") != 5:
        raise ValueError("r12 numeric write count changed")
    if normal_robin.count("_ValueTypeMatch TO SourceCellJson = SavedCellJson") != 12:
        raise ValueError("r12 saved JSON comparison count changed")
    if normal_robin.count("Excel.SaveExcel.SaveAs") != 1:
        raise ValueError("r12 SaveAs count changed")
    for forbidden in ("%TextSource", "%RunMode", "Invoke-Expression", "ScriptBlock]::Create"):
        if forbidden in decoded_normal:
            raise ValueError(f"Unsafe PowerShell handoff remains: {forbidden}")

    support_script_bytes = script.encode("utf-8")
    normal_bytes = normal_robin.encode("utf-8")
    negative_bytes = negative_robin.encode("utf-8")
    support_hashes = {
        "script": sha256_bytes(support_script_bytes),
        "normal": sha256_bytes(normal_bytes),
        "negative": sha256_bytes(negative_bytes),
    }
    structural_contract = (
        STRUCTURAL_CONTRACT_BASE
        + "\nSame-version identities calculated by the builder:\n"
        + f"- support script: {SCRIPT_SUPPORT.as_posix()} / SHA-256 {support_hashes['script']}\n"
        + f"- prepared normal Robin: {NORMAL_SUPPORT.as_posix()} / SHA-256 {support_hashes['normal']}\n"
        + f"- prepared exception-negative Robin: {NEGATIVE_SUPPORT.as_posix()} / SHA-256 {support_hashes['negative']}\n"
        + "- normal and negative Robin differ only in the one RunMode assignment; the formal adaptation uses NORMAL only.\n"
    )

    (destination / "knowledge").mkdir(parents=True)
    (destination / "support").mkdir(parents=True)
    (destination / SCRIPT_SUPPORT).write_bytes(support_script_bytes)
    (destination / NORMAL_SUPPORT).write_bytes(normal_bytes)
    (destination / NEGATIVE_SUPPORT).write_bytes(negative_bytes)
    (destination / CONTRACT_SUPPORT).write_text(structural_contract, encoding="utf-8", newline="\n")

    validation_summary = f"""r12 local source/evidence boundary
- frozen r11 formal result: {relative(INPUTS['r11_formal'])} / SHA-256 {actual['r11_formal']} / FAIL preserved
- fixed R2/R3 normal and forced-exception evidence: {relative(INPUTS['trial_final'])} / SHA-256 {actual['trial_final']} / source evidence only, not inherited
- R2/R3 normal PAD re-copy: {relative(INPUTS['trial_normal_recopy'])} / SHA-256 {actual['trial_normal_recopy']} / path-only correspondence true
- R2/R3 negative PAD re-copy: {relative(INPUTS['trial_negative_recopy'])} / SHA-256 {actual['trial_negative_recopy']} / path-only correspondence true
- r11 R4 correction: {relative(CORRECTION)} / SHA-256 {sha256(CORRECTION)} / r11 files unchanged
- r12 prepared normal/negative source: non-live builder output; normal and negative differ only by RunMode assignment
- Copilot send 0; r12 PAD save/re-copy 0; r12 integrated Run 0; full regression not run; GitHub write 0
"""

    for record in manifest["source_files"]:
        source = BASE / record["path"]
        name = Path(record["path"]).name
        content = text(source)
        if name.startswith(("PAD-Robin-00-", "PAD-Robin-04-", "PAD-Robin-06-")):
            if R11_MARKER not in content:
                raise ValueError(f"r11 replacement marker missing: {name}")
            content = content.split(R11_MARKER, 1)[0].rstrip("\r\n") + "\n\n"
            content += R12_SCOPE + EXAMPLE_MAPPING
            if name.startswith("PAD-Robin-04-"):
                content += "\n" + validation_summary + "\n" + structural_contract
            if name.startswith("PAD-Robin-06-"):
                content += "\nEX03 r12 prepared normal教材原文（別条件例・非ライブ・未受入）\n"
                content += f"source: {NORMAL_SUPPORT.as_posix()} / SHA-256 {support_hashes['normal']}\n"
                content += "この見出しより後のRobinだけを逐語使用し、依頼由来data slotと教材専用label以外を変更しない。RunModeはNORMALのまま使う。\n"
                content += normal_robin.rstrip("\r\n") + "\n"
        (destination / record["path"]).write_bytes(content.encode("utf-8"))

    base_instruction = text(INPUTS["r11_instruction"])
    if R11_INSTRUCTION_MARKER not in base_instruction:
        raise ValueError("r11 instruction replacement marker missing")
    instructions = base_instruction.split(R11_INSTRUCTION_MARKER, 1)[0] + R12_INSTRUCTIONS
    (destination / "agent-instructions.txt").write_text(instructions, encoding="utf-8", newline="\n")
    instruction_utf16 = len(instructions.encode("utf-16-le")) // 2
    if instruction_utf16 > 8000:
        raise ValueError(f"Instruction exceeds limit: {instruction_utf16}")

    subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(ROOT / "tools/Build-KnowledgeBundle.ps1"),
            "-Root",
            str(destination),
            "-KnowledgeDirectory",
            "knowledge",
            "-OutputPath",
            "knowledge/PAD-Robin-Knowledge-Bundle.txt",
        ],
        check=True,
    )
    bundle_path = destination / manifest["bundle_path"]
    bundle = text(bundle_path)
    if normal_robin.rstrip("\r\n") not in bundle:
        raise ValueError("Complete prepared normal Robin is missing from bundle")
    for required in (
        "JSON-file handoff and stop-gate structural contract",
        "Never interpolate a source value",
        "exact success JSON plus NORMAL mode",
        "exactly one text code block",
    ):
        if required not in bundle:
            raise ValueError(f"r12 contract missing from bundle: {required}")

    independent_source = instructions + R12_SCOPE + EXAMPLE_MAPPING + structural_contract + script + normal_robin + negative_robin
    for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS + ["100%"]:
        if term in independent_source:
            raise ValueError(f"Fixed EX03 answer leaked into r12 independent source: {term}")
    for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS:
        if term in bundle:
            raise ValueError(f"Fixed EX03 answer leaked into r12 bundle: {term}")

    support_files = []
    for path, runtime in (
        (SCRIPT_SUPPORT, "generation_support_and_embedded_in_prepared_robin_without_final_lf"),
        (NORMAL_SUPPORT, "prepared_non_live_adaptation_source_not_pad_saved_or_executed"),
        (NEGATIVE_SUPPORT, "prepared_non_live_structural_negative_not_pad_saved_or_executed"),
        (CONTRACT_SUPPORT, "generation_time_structural_contract_not_runtime_code"),
    ):
        full = destination / path
        support_files.append({"path": path.as_posix(), "runtime": runtime, **newline_metrics_bytes(full.read_bytes())})

    evidence_inputs = dict(manifest.get("evidence_inputs", {}))
    for path in [*INPUTS.values(), CORRECTION]:
        evidence_inputs[relative(path)] = sha256(path)

    normal_metrics = newline_metrics_bytes(normal_bytes)
    negative_metrics = newline_metrics_bytes(negative_bytes)
    script_metrics = newline_metrics_bytes(support_script_bytes)
    embedded_metrics = newline_metrics_bytes(decoded_normal.encode("utf-8"))
    r4_provenance = {
        "all_metrics_computed_from_actual_files": True,
        "r11_frozen_recopy": r11_recopy_record,
        "r11_manifest_correction": file_record(CORRECTION),
        "r2r3_fixed_script": file_record(INPUTS["r2r3_script"]),
        "r2r3_fixed_normal": file_record(INPUTS["r2r3_normal"]),
        "r2r3_fixed_negative": file_record(INPUTS["r2r3_negative"]),
        "r2r3_trial_normal_recopy": file_record(INPUTS["trial_normal_recopy"]),
        "r2r3_trial_negative_recopy": file_record(INPUTS["trial_negative_recopy"]),
        "r2r3_trial_path_only_correspondence": path_normalization,
        "script_transformations": script_transforms,
        "support_script": {"path": SCRIPT_SUPPORT.as_posix(), **script_metrics},
        "embedded_script": {"container": NORMAL_SUPPORT.as_posix(), **embedded_metrics},
        "support_script_final_lf": script_metrics["final_lf"],
        "embedded_script_final_lf": embedded_metrics["final_lf"],
        "embedded_equals_support_without_final_lf": decoded_normal == script.rstrip("\n"),
        "prepared_normal": {"path": NORMAL_SUPPORT.as_posix(), **normal_metrics},
        "prepared_negative": {"path": NEGATIVE_SUPPORT.as_posix(), **negative_metrics},
        "normal_negative_only_mode_assignment_diff": True,
    }

    manifest.update(
        version=VERSION,
        status="LOCAL_CANDIDATE_EX03_R12_JSON_FILE_HANDOFF_GATE_RESTORE_NOT_COPILOT_OR_PAD_ACCEPTED",
        inherits_live_acceptance=False,
        base_candidate="20260917-excel-r11",
        base_commit=BASE_COMMIT,
        instruction_sha256=sha256(destination / "agent-instructions.txt"),
        instruction_utf16=instruction_utf16,
        bundle_sha256=sha256(bundle_path),
        evidence_inputs=evidence_inputs,
        builder="tools/Build-Issue38Ex03CandidateR12.py",
        support_files=support_files,
        r4_file_provenance=r4_provenance,
    )
    for record in manifest["source_files"]:
        path = destination / record["path"]
        record.update(sha256=sha256(path), bytes=path.stat().st_size)

    evidence = manifest["evidence"]
    # These inherited fields described r9-r11's then-current candidate source.
    # Keeping them unqualified in r12 would look like a live r12 re-copy or PASS.
    for stale_key in (
        "source_chain",
        "actual_sent_bundle_claimed_escape_counts",
        "actual_sent_bundle_raw_token_counts",
        "prior_refusal_internal_cause",
        "confirmed_package_issue",
        "source_exact_bytes",
        "escape_failure_boundary",
        "escape_failure_hidden_model_cause",
        "generated_backslash_open_bracket_count",
        "generated_backslash_close_bracket_count",
        "teaching_backslash_open_bracket_count",
        "teaching_backslash_close_bracket_count",
        "expected_vs_generated_differing_lines",
        "generated_vs_pad_recopy_differing_lines",
        "diagnostic_normalization_explains_expected",
        "diagnostic_normalization_applied_to_evidence",
        "stale_teaching_label_count",
        "source_reused_exact_bytes",
        "source_new_pad_capture_required",
        "source_new_pad_capture_reason",
        "fidelity_contract_sha256",
        "structural_failure_boundary",
        "structural_failure_hidden_model_or_service_cause",
        "r9_response_dom_sha256",
        "r9_response_dom_equals_raw_clipboard",
        "expected_vs_generated_differing_line_numbers",
        "structural_token_expected_counts",
        "structural_token_generated_counts",
        "required_invariant_fragment_count",
        "forbidden_corruption_fragment_count",
        "structural_fidelity_contract_sha256",
        "pipeline_failure_boundary",
        "pipeline_hidden_model_or_service_cause",
        "extraction_good_parser_error_count",
        "extraction_intentional_negative_parser_error_count",
        "source_pad_action_count",
        "source_pad_variable_count",
        "synthetic_pad_run_count",
        "synthetic_pad_run_status",
        "synthetic_artifact_status",
        "synthetic_artifact_check_count",
        "embedded_script_old_lines",
        "embedded_script_new_lines",
        "embedded_script_old_utf8_bytes_without_final_newline",
        "embedded_script_new_utf8_bytes_without_final_newline",
        "retired_fragments",
        "required_fragment_count",
        "forbidden_fragment_count",
    ):
        evidence.pop(stale_key, None)

    evidence.update(
        copilot="R11_FORMAL_ONE_SEND_DELIVERY_CONTRACT_FAIL_PRESERVED_R12_NOT_SENT",
        pad="R2R3_FIXED_PROBE_NORMAL_AND_NEGATIVE_PASS_SOURCE_ONLY_R12_PAD_RUN0",
        teaching_test_independence="PASS_R12_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_INSTRUCTION_AND_NEW_SOURCE",
        candidate_adaptation="PREPARED_NON_LIVE_R11_FULL_SHAPE_WITH_R2R3_JSON_FILE_HANDOFF_GATE_AND_RESTORE",
        candidate_script_sha256=support_hashes["script"],
        candidate_robin_sha256=support_hashes["normal"],
        candidate_negative_robin_sha256=support_hashes["negative"],
        candidate_prepared_robin_sha256=support_hashes["normal"],
        source_candidate_sha256=support_hashes["normal"],
        source_pad_recopy_sha256=None,
        source_candidate_crlf_count=normal_metrics["crlf_count"],
        source_candidate_lf_only_count=normal_metrics["lf_only_count"],
        source_recopy_crlf_count=None,
        source_recopy_lf_only_count=None,
        source_recopy_status="NOT_RUN_R12_PREPARED_SOURCE_ONLY",
        source_lf_normalized_exact=None,
        source_action_decodes_to_script=True,
        source_executed=False,
        r2r3_trial_normal_run_count=1,
        r2r3_trial_negative_run_count=1,
        r2r3_trial_results_inherited=False,
        r2r3_trial_normal_status=final["normal"]["gate_result"],
        r2r3_trial_negative_status="PASS_FORCED_EXCEPTION_RESTORE_AND_NO_SAVE",
        r2r3_numeric_json_scope="FIXED_PROBE_DOUBLE_OR_DECIMAL_ONLY_NOT_APPLIED_TO_EX03_NUMERIC_MATRIX",
        input_values_directly_interpolated_into_powershell=False,
        json_file_write_count=7,
        mode_json_file_write_count=1,
        json_file_read_count=7,
        exact_success_and_normal_gate=True,
        exception_after_format_before_value=True,
        exception_format_restore_in_finally=True,
        support_script_final_lf=script_metrics["final_lf"],
        embedded_script_final_lf=embedded_metrics["final_lf"],
        embedded_script_equals_support_without_final_lf=True,
        exception_path_runtime="PASS_R2R3_FIXED_PROBE_NOT_R12_INTEGRATED",
        formal_r11_result="FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD_PRESERVED",
        r11_auxiliary_result="PASS_FIXED_SCOPE_NOT_INHERITED",
        existing_output_guard="PASS_FIXED_R11_FILE_AUX1_NOT_INHERITED_TO_R12",
        r11_manifest_correction_sha256=sha256(CORRECTION),
        r11_frozen_manifest_sha256=actual["r11_manifest"],
        fixed_request_spec_expected_hashes_preserved=True,
        formal_text_code_block_required_count=1,
        legacy_558_failure_preserved=True,
        copilot_send_count=0,
        integrated_ex03_run_count=0,
        r12_pad_save_recopy_count=0,
        full_regression="NOT_RUN_BY_SCOPE",
        github_write_count=0,
        structural_contract_sha256=sha256(destination / CONTRACT_SUPPORT),
    )

    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    result = {
        "version": VERSION,
        "status": manifest["status"],
        "instruction_utf16": instruction_utf16,
        "instruction_sha256": manifest["instruction_sha256"],
        "bundle_sha256": manifest["bundle_sha256"],
        "manifest_sha256": sha256(destination / "manifest.json"),
        "support_script_sha256": support_hashes["script"],
        "prepared_normal_sha256": support_hashes["normal"],
        "prepared_negative_sha256": support_hashes["negative"],
        "correction_sha256": sha256(CORRECTION),
        "copilot_send": 0,
        "r12_pad_run": 0,
    }
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "copilot/versions" / VERSION)
    build(parser.parse_args().output)
