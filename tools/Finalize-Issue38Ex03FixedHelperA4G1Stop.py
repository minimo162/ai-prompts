#!/usr/bin/env python3
"""Finalize the one-send A4-G1 stop before PAD without altering captured evidence."""

from __future__ import annotations

import difflib
import hashlib
import importlib.util
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CANDIDATE = ROOT / "copilot/versions/20260918-excel-r12-fixed-helper-a4"
CYCLE = BASE / "cycles/EX03-R12-FIXED-HELPER-A4-G1"
PROBE = BASE / "probes/ex03-r12-fixed-helper"
A4_PROBE = BASE / "probes/ex03-r12-fixed-helper-a4"
RUNTIME = BASE / "runs/EX03-attempt1"

GENERATED = CYCLE / "generated.robin"
RESPONSE = CYCLE / "copilot-response.txt"
BROWSER_CAPTURE = CYCLE / "browser-capture.json"
PROTECTED_BEFORE = CYCLE / "protected-before.json"

HELPER = PROBE / "EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = A4_PROBE / "invocation.json"
LAUNCHER = A4_PROBE / "launcher.ps1"
TEMPLATE = BASE / "fixtures/EX03/ひな形.xlsx"
INPUT1 = BASE / "fixtures/EX03/入力い.xlsx"
INPUT2 = BASE / "fixtures/EX03/入力ろ.xlsx"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
JSON_ROOT = RUNTIME / "a4-helper-json"
WIRING = CANDIDATE / "wiring-spec.json"

CYCLE_ID = "EX03-R12-FIXED-HELPER-A4-G1"
ROUTE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A4"
CANDIDATE_ID = "20260918-excel-r12-fixed-helper-a4"
BASE_COMMIT = "4a1e890fa95bc55cbe981578a2694548bb310c94"

EXPECTED_SHA256 = {
    "instruction": "93cfd7aa5d0f1c380e1a5c50f764794a7bab2e676f1d064c9fe9b349788f3829",
    "submitted_body": "8924f824256a161f035f686b221ea58bf2033a66e0ef359c8968506c338f9647",
    "bundle": "62695ca3c007ab291732657ddaeca66723a57115d151efc7b1730ef5341c514c",
    "wiring": "c62ec6951bdd36e895acfc937d7a1f390e75e8d984b26a9531cc2c88d970f58c",
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "5c5a2008f55296a48f63fa65178aab971e4212455bb2af58e33149bdcaec40d8",
    "launcher": "a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
    "generated": "eb5648631466da3431a21cf8df98fb06e5fece8876c3705b6483b4d74b58e290",
    "response": "3a241e5fab1ad0055266d162309ee26defc4ffa8959b9fb5bb2caeb5634e5451",
}
EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'

OUTPUTS = {
    "live_send": CYCLE / "live-send.json",
    "assessment": CYCLE / "generation-assessment.json",
    "integrity": CYCLE / "post-stop-integrity.json",
    "result": CYCLE / "RESULT.md",
}

FORBIDDEN_RUNTIME = [
    "File.Delete",
    "Folder.Delete",
    "WebAutomation.",
    "HTTP.",
    "System.RunDOSCommand",
    "System.RunApplication",
    "Start-Process",
    "Remove-Item",
    "Invoke-WebRequest",
    "Invoke-RestMethod",
    "Invoke-Expression",
    "ScriptBlock]::Create",
    "Add-Type",
    "Set-ExecutionPolicy",
    "Unblock-File",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text_new(path: Path, value: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def control_balance(lines: list[str]) -> dict[str, Any]:
    stack: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    counts = {"if": 0, "else": 0, "end": 0}
    for line_number, raw in enumerate(lines, 1):
        value = raw.strip()
        if value.startswith("IF ") and value.endswith(" THEN"):
            counts["if"] += 1
            stack.append({"line": line_number, "else_seen": False})
        elif value == "ELSE":
            counts["else"] += 1
            if not stack:
                errors.append({"line": line_number, "error": "ELSE_WITHOUT_IF"})
            elif stack[-1]["else_seen"]:
                errors.append({"line": line_number, "error": "DUPLICATE_ELSE"})
            else:
                stack[-1]["else_seen"] = True
        elif value == "END":
            counts["end"] += 1
            if not stack:
                errors.append({"line": line_number, "error": "END_WITHOUT_IF"})
            else:
                stack.pop()
    errors.extend({"line": item["line"], "error": "IF_WITHOUT_END"} for item in stack)
    return {"counts": counts, "errors": errors, "balanced": not errors}


def escaped_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\")


def build_assessment() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != BASE_COMMIT:
        raise ValueError("A4-G1 finalization must still be based on commit 4a1e890")
    for output in OUTPUTS.values():
        if output.exists():
            raise FileExistsError(f"Refusing to overwrite A4-G1 evidence: {output}")

    fixed_paths = {
        "instruction": CANDIDATE / "agent-instructions.txt",
        "submitted_body": CANDIDATE / "submitted-body.txt",
        "bundle": CANDIDATE / "knowledge/PAD-Robin-Fixed-Helper-A4-Bundle.txt",
        "wiring": WIRING,
        "helper": HELPER,
        "invocation": INVOCATION,
        "launcher": LAUNCHER,
        "template": TEMPLATE,
        "generated": GENERATED,
        "response": RESPONSE,
    }
    actual_sha = {name: sha256(path) for name, path in fixed_paths.items()}
    if actual_sha != EXPECTED_SHA256:
        raise ValueError(f"Fixed or captured SHA mismatch: {actual_sha}")

    capture = json.loads(BROWSER_CAPTURE.read_text(encoding="utf-8"))
    if capture["cycle_id"] != CYCLE_ID:
        raise ValueError("Browser capture cycle mismatch")
    if capture["pre_send"]["submitted_body_sha256"] != EXPECTED_SHA256["submitted_body"]:
        raise ValueError("Browser-captured submitted body SHA mismatch")
    if capture["pre_send"]["bundle_sha256"] != EXPECTED_SHA256["bundle"]:
        raise ValueError("Browser-captured bundle SHA mismatch")
    if capture["response"]["assistant_inner_text_sha256"] != EXPECTED_SHA256["response"]:
        raise ValueError("Browser-captured response SHA mismatch")
    if capture["generated_copy"]["sha256"] != EXPECTED_SHA256["generated"]:
        raise ValueError("Browser-captured generated Robin SHA mismatch")
    if capture["send"]["button_click_count"] != 1 or capture["send"]["limit_total"] != 1:
        raise ValueError("A4-G1 send count is not exactly 1/1")
    if capture["send"]["resend_performed"]:
        raise ValueError("Unexpected A4-G1 resend")

    raw = GENERATED.read_bytes()
    if b"\r" in raw:
        raise ValueError("Generated Robin is not the browser-observed LF-only payload")
    generated = raw.decode("utf-8")
    lines = generated.split("\n")
    nonempty = [line for line in lines if line.strip()]
    a2 = load_module(
        "issue38_a4_stop_a2",
        ROOT / "tools/Build-Issue38Ex03FixedHelperCopilotCandidateA2.py",
    )
    parser = load_module(
        "issue38_a4_stop_parser",
        ROOT / "tools/Analyze-Issue38Ex03R10Generation.py",
    )
    decoded_launcher = a2.embedded_script(generated)
    decoded_restored = decoded_launcher.encode("utf-8") + b"\n"
    expected_launcher = LAUNCHER.read_bytes()
    if not expected_launcher.endswith(b"\n") or b"\r" in expected_launcher:
        raise ValueError("Fixed A4 launcher LF contract changed")
    parser_errors = parser.parse_powershell(decoded_launcher)
    launcher_diff = list(
        difflib.unified_diff(
            expected_launcher.decode("utf-8").splitlines(),
            decoded_launcher.splitlines(),
            fromfile="fixed-launcher.ps1",
            tofile="generated-decoded-launcher.ps1",
            lineterm="",
        )
    )

    balance = control_balance(lines)
    forbidden_counts = {fragment: generated.count(fragment) for fragment in FORBIDDEN_RUNTIME}
    output_encoded = escaped_path(OUTPUT)
    json_root_encoded = escaped_path(JSON_ROOT)

    source_json_writes = re.findall(
        r"File\.WriteText File: \$'''([^']*source-(\d)\.json)''' TextToWrite: (Source\dJson)",
        generated,
    )
    mode_json_writes = re.findall(
        r"File\.WriteText File: \$'''([^']*mode\.json)''' TextToWrite: (RunModeJson)",
        generated,
    )
    source_sets = re.findall(r"^\s*SET Source(\d+) TO (Data[12]\[\d\]\[\d\])$", generated, re.MULTILINE)
    source_jsons = re.findall(
        r"Variables\.ConvertCustomObjectToJson CustomObject: \{ 'probe': Source(\d+) \} Json=> Source(\d+)Json",
        generated,
    )
    numeric_sets = re.findall(r"^\s*SET Num(\d+) TO (Data[12]\[\d\]\[\d\])$", generated, re.MULTILINE)
    numeric_writes = re.findall(
        r"Excel\.WriteToExcel\.WriteCell Instance: Work Value: (Num\d+) Column: \$'''([A-Z]+)''' Row: (\d+)",
        generated,
    )
    saved_sets = re.findall(r"^\s*SET Saved(\d+) TO (Readback[12]\[\d\]\[\d\])$", generated, re.MULTILINE)
    saved_jsons = re.findall(
        r"Variables\.ConvertCustomObjectToJson CustomObject: \{ 'probe': Saved(\d+) \} Json=> Saved(\d+)Json",
        generated,
    )
    comparison_lines = [
        {"line": index, "text": line.strip()}
        for index, line in enumerate(lines, 1)
        if re.match(r"\s*SET \S+VsSaved TO .+ = Saved\d+Json$", line)
    ]
    compared_saved_indexes = [
        int(re.search(r"Saved(\d+)Json$", item["text"]).group(1))
        for item in comparison_lines
    ]
    inline_action_expressions = [
        {"line": index, "text": line.strip()}
        for index, line in enumerate(lines, 1)
        if " TO Variables.ConvertCustomObjectToJson(" in line
    ]
    expected_observed_comparison_texts = [
        "SET Source1VsSaved TO Source1Json = Saved1Json",
        "SET Source2VsSaved TO Variables.ConvertCustomObjectToJson({ 'probe': Data1[0][1] }) = Saved2Json",
        "SET Source3VsSaved TO Source2Json = Saved3Json",
        "SET Source4VsSaved TO Variables.ConvertCustomObjectToJson({ 'probe': Data1[1][1] }) = Saved4Json",
        "SET Source5VsSaved TO Source3Json = Saved5Json",
        "SET Source6VsSaved TO Variables.ConvertCustomObjectToJson({ 'probe': Data1[2][1] }) = Saved6Json",
        "SET Source7VsSaved TO Source4Json = Saved7Json",
    ]
    observed_comparison_texts = [item["text"] for item in comparison_lines]

    wiring = json.loads(WIRING.read_text(encoding="utf-8"))
    positions = wiring["comparison_contract"]["positions"]
    missing_indexes = [index for index in range(1, 13) if index not in compared_saved_indexes]
    missing_positions = [
        {
            "order": item["order"],
            "source": f'{item["source_workbook"]}!{item["source_sheet"]}!{item["source_cell"]}',
            "source_reference": item["source_reference"],
            "saved": f'{item["saved_sheet"]}!{item["saved_cell"]}',
            "saved_reference": item["saved_reference"],
            "kind": item["kind"],
        }
        for item in positions
        if item["order"] in missing_indexes
    ]

    expected_numeric_sets = [
        ("1", "Data1[0][1]"),
        ("2", "Data1[1][1]"),
        ("3", "Data1[2][1]"),
        ("4", "Data2[0][1]"),
        ("5", "Data2[1][1]"),
    ]
    expected_source_sets = [
        ("1", "Data1[0][0]"),
        ("2", "Data1[1][0]"),
        ("3", "Data1[2][0]"),
        ("4", "Data2[0][0]"),
        ("5", "Data2[1][0]"),
        ("6", "Data2[0][2]"),
        ("7", "Data2[1][2]"),
    ]
    expected_numeric_writes = [
        ("Num1", "G", "7"),
        ("Num2", "G", "8"),
        ("Num3", "G", "9"),
        ("Num4", "E", "5"),
        ("Num5", "E", "6"),
    ]
    expected_saved_sets = [
        (str(index), f"Readback1[{row}][{column}]")
        for index, (row, column) in enumerate(
            [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)], 1
        )
    ] + [
        (str(index), f"Readback2[{row}][{column}]")
        for index, (row, column) in enumerate(
            [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)], 7
        )
    ]

    input1_open = f"Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''{escaped_path(INPUT1)}''' Visible: True ReadOnly: True UseMachineLocale: False Instance=> SourceBook1"
    input2_open = f"Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''{escaped_path(INPUT2)}''' Visible: True ReadOnly: True UseMachineLocale: False Instance=> SourceBook2"
    input1_read = "Excel.ReadFromExcel.ReadCells Instance: SourceBook1 StartColumn: $'''D''' StartRow: 4 EndColumn: $'''E''' EndRow: 6 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> Data1"
    input2_read = "Excel.ReadFromExcel.ReadCells Instance: SourceBook2 StartColumn: $'''B''' StartRow: 2 EndColumn: $'''D''' EndRow: 3 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> Data2"
    ordered_markers = [
        f"IF (File.IfFile.Exists File: $'''{output_encoded}''') THEN",
        input1_open,
        "Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: SourceBook1 Name: $'''受取明細'''",
        input1_read,
        "Excel.CloseExcel.Close Instance: SourceBook1",
        input2_open,
        "Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: SourceBook2 Name: $'''追加項目'''",
        input2_read,
        "Excel.CloseExcel.Close Instance: SourceBook2",
        "SET Source1 TO Data1[0][0]",
        "File.WriteText File:",
        f"Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''{escaped_path(WORK)}'''",
        "Scripting.RunPowershellScript.RunScript",
        "IF PowershellOutput =",
        "IF RunMode = $'''NORMAL''' THEN",
        "SET Num1 TO Data1[0][1]",
        "Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Work Name: $'''集計先'''",
        "Excel.WriteToExcel.WriteCell Instance: Work Value: Num1",
        "Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Work Name: $'''追記先'''",
        "Excel.WriteToExcel.WriteCell Instance: Work Value: Num4",
        "Excel.SaveExcel.SaveAs Instance: Work",
        f"Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: $'''{output_encoded}''' Visible: True ReadOnly: True",
        "RangeValue=> Readback1",
        "RangeValue=> Readback2",
        "SET Saved1 TO Readback1[0][0]",
        "Variables.ConvertCustomObjectToJson CustomObject: { 'probe': Saved1 } Json=> Saved1Json",
        "SET Source1VsSaved TO Source1Json = Saved1Json",
    ]
    ordered_positions: list[int] = []
    search_start = 0
    for marker in ordered_markers:
        found = generated.find(marker, search_start)
        ordered_positions.append(found)
        if found >= 0:
            search_start = found + len(marker)

    structure = {
        "control_balance": balance,
        "first_nonempty_line": nonempty[0],
        "last_nonempty_line": nonempty[-1],
        "first_and_last_are_pad_instructions": nonempty[0].startswith("SET ") and nonempty[-1] == "END",
        "output_guard_count": generated.count(f"IF (File.IfFile.Exists File: $'''{output_encoded}''') THEN"),
        "readonly_input_open_count": len(re.findall(r"Instance=> SourceBook[12]$", generated, re.MULTILINE)),
        "typed_input_range_read_count": len(re.findall(r"RangeValue=> Data[12]$", generated, re.MULTILINE)),
        "fixed_input1_open_count": generated.count(input1_open),
        "fixed_input2_open_count": generated.count(input2_open),
        "fixed_input1_sheet_count": generated.count("Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: SourceBook1 Name: $'''受取明細'''"),
        "fixed_input2_sheet_count": generated.count("Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: SourceBook2 Name: $'''追加項目'''"),
        "fixed_input1_typed_range_count": generated.count(input1_read),
        "fixed_input2_typed_range_count": generated.count(input2_read),
        "source_sets": [list(item) for item in source_sets],
        "source_sets_match_wiring": source_sets == expected_source_sets,
        "source_json_conversion_count": len(source_jsons),
        "source_json_conversions_pair_indexes": [left == right for left, right in source_jsons],
        "source_json_write_count": len(source_json_writes),
        "source_json_write_indexes": [int(item[1]) for item in source_json_writes],
        "source_json_write_variable_indexes": [int(re.search(r"(\d+)", item[2]).group(1)) for item in source_json_writes],
        "source_json_writes_match_indexes": all(int(item[1]) == int(re.search(r"(\d+)", item[2]).group(1)) for item in source_json_writes),
        "source_json_write_all_under_fixed_root": all(item[0].startswith(json_root_encoded) for item in source_json_writes),
        "mode_json_write_count": len(mode_json_writes),
        "mode_json_write_under_fixed_root": len(mode_json_writes) == 1 and mode_json_writes[0][0].startswith(json_root_encoded),
        "editable_work_open_count": generated.count(f"Path: $'''{escaped_path(WORK)}''' Visible: True ReadOnly: False"),
        "run_script_count": generated.count("Scripting.RunPowershellScript.RunScript"),
        "exact_success_gate_count": generated.count(
            "IF PowershellOutput = $'''{\\\"status\\\":\\\"OK\\\",\\\"mode\\\":\\\"NORMAL\\\",\\\"text_writes\\\":7,\\\"formats_restored\\\":true}''' THEN"
        ),
        "normal_gate_count": generated.count("IF RunMode = $'''NORMAL''' THEN"),
        "numeric_sets": [list(item) for item in numeric_sets],
        "numeric_sets_match_wiring": numeric_sets == expected_numeric_sets,
        "numeric_writes": [list(item) for item in numeric_writes],
        "numeric_writes_match_wiring": numeric_writes == expected_numeric_writes,
        "target_collect_sheet_activation_count": generated.count("Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Work Name: $'''集計先'''"),
        "target_append_sheet_activation_count": generated.count("Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Work Name: $'''追記先'''"),
        "save_as_count": generated.count("Excel.SaveExcel.SaveAs Instance: Work"),
        "save_as_fixed_output_count": generated.count(f"DocumentPath: $'''{output_encoded}'''"),
        "readonly_output_reopen_count": generated.count(f"Path: $'''{output_encoded}''' Visible: True ReadOnly: True"),
        "typed_readback_rectangle_count": generated.count("GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> Readback"),
        "fixed_readback1_count": generated.count("StartColumn: $'''F''' StartRow: 7 EndColumn: $'''G''' EndRow: 9 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> Readback1"),
        "fixed_readback2_count": generated.count("StartColumn: $'''D''' StartRow: 5 EndColumn: $'''F''' EndRow: 6 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> Readback2"),
        "saved_sets": [list(item) for item in saved_sets],
        "saved_sets_match_wiring": saved_sets == expected_saved_sets,
        "saved_json_conversion_count": len(saved_jsons),
        "saved_json_conversions_pair_indexes": [left == right for left, right in saved_jsons],
        "json_value_type_comparison_count": len(comparison_lines),
        "comparison_saved_indexes": compared_saved_indexes,
        "observed_comparison_texts_match_fixed_positions_1_through_7": observed_comparison_texts == expected_observed_comparison_texts,
        "comparison_required_indexes": list(range(1, 13)),
        "comparison_missing_indexes": missing_indexes,
        "inline_uncaptured_action_expression_count": len(inline_action_expressions),
        "inline_uncaptured_action_expressions": inline_action_expressions,
        "failure_close_no_save_else_count": len(re.findall(r"ELSE\n\s+Excel\.CloseExcel\.Close Instance: Work\n\s+SET ProbeState TO \$'''(?:MODE_NOT_NORMAL_NO_SAVE|SCRIPT_NOT_SUCCESS_NO_SAVE)'''", generated)),
        "major_execution_order_marker_count": len(ordered_markers),
        "major_execution_order_positions": ordered_positions,
        "major_execution_order_valid": all(value >= 0 for value in ordered_positions) and ordered_positions == sorted(ordered_positions),
    }
    pre_comparison_structure_pass = all(
        [
            balance["balanced"],
            structure["first_and_last_are_pad_instructions"],
            structure["output_guard_count"] == 1,
            structure["readonly_input_open_count"] == 2,
            structure["typed_input_range_read_count"] == 2,
            structure["fixed_input1_open_count"] == 1,
            structure["fixed_input2_open_count"] == 1,
            structure["fixed_input1_sheet_count"] == 1,
            structure["fixed_input2_sheet_count"] == 1,
            structure["fixed_input1_typed_range_count"] == 1,
            structure["fixed_input2_typed_range_count"] == 1,
            structure["source_sets_match_wiring"],
            structure["source_json_conversion_count"] == 7,
            all(structure["source_json_conversions_pair_indexes"]),
            structure["source_json_write_count"] == 7,
            structure["source_json_write_indexes"] == list(range(1, 8)),
            structure["source_json_write_variable_indexes"] == list(range(1, 8)),
            structure["source_json_writes_match_indexes"],
            structure["source_json_write_all_under_fixed_root"],
            structure["mode_json_write_count"] == 1,
            structure["mode_json_write_under_fixed_root"],
            structure["editable_work_open_count"] == 1,
            structure["run_script_count"] == 1,
            structure["exact_success_gate_count"] == 1,
            structure["normal_gate_count"] == 1,
            structure["numeric_sets_match_wiring"],
            structure["numeric_writes_match_wiring"],
            structure["target_collect_sheet_activation_count"] == 1,
            structure["target_append_sheet_activation_count"] == 1,
            structure["save_as_count"] == 1,
            structure["save_as_fixed_output_count"] == 1,
            structure["readonly_output_reopen_count"] == 1,
            structure["typed_readback_rectangle_count"] == 2,
            structure["fixed_readback1_count"] == 1,
            structure["fixed_readback2_count"] == 1,
            structure["saved_sets_match_wiring"],
            structure["saved_json_conversion_count"] == 12,
            all(structure["saved_json_conversions_pair_indexes"]),
            structure["failure_close_no_save_else_count"] == 2,
            structure["major_execution_order_valid"],
        ]
    )
    comparison_structure_pass = all(
        [
            structure["json_value_type_comparison_count"] == 12,
            not structure["comparison_missing_indexes"],
            structure["inline_uncaptured_action_expression_count"] == 0,
        ]
    )
    structure["pre_comparison_structure_pass"] = pre_comparison_structure_pass
    structure["comparison_structure_pass"] = comparison_structure_pass
    structure_pass = pre_comparison_structure_pass and comparison_structure_pass
    structure["pass"] = structure_pass

    launcher = {
        "expected_path": relative(LAUNCHER),
        "expected_sha256": EXPECTED_SHA256["launcher"],
        "decoded_terminal_lf_restored_sha256": sha256_bytes(decoded_restored),
        "exact_match": decoded_restored == expected_launcher,
        "expected_line_count": len(expected_launcher.decode("utf-8").splitlines()),
        "decoded_line_count": len(decoded_launcher.splitlines()),
        "powershell_parser_error_count": len(parser_errors),
        "powershell_parser_errors": parser_errors,
        "helper_invocation_count": decoded_launcher.count("& $helperPath -InvocationPath $invocationPath"),
        "helper_sha_check_count": decoded_launcher.count("$actualHelperSha256 = Get-Sha256 $helperPath"),
        "invocation_sha_check_count": decoded_launcher.count("$actualInvocationSha256 = Get-Sha256 $invocationPath"),
        "expected_stdout_literal_count": decoded_launcher.count(EXPECTED_SUCCESS),
        "unified_diff": launcher_diff,
        "pass": decoded_restored == expected_launcher and not parser_errors,
    }

    component_assessment = {
        "C01_STATE_INIT": "PASS_PRESENT",
        "C02_OUTPUT_GUARD": "PASS_PRESENT",
        "C03_READONLY_TYPED_RANGE": "PASS_TWO_FIXED_PATH_SHEET_RANGE_READS",
        "C04_JSON_FILE_HANDOFF": "PASS_SEVEN_FIXED_SOURCE_MAPPINGS_PLUS_ONE_MODE_WRITE",
        "C05_EDITABLE_WORK_OPEN": "PASS_FIXED_WORK",
        "C06_FIXED_LAUNCHER_RUNSCRIPT": "FAIL_DECODED_LAUNCHER_NOT_FIXED_SHA_AND_POWERSHELL_PARSE_ERROR",
        "C07_EXACT_SUCCESS_MODE_GATE": "PASS_PRESENT",
        "C08_TARGET_SHEET_ACTIVATION": "PASS_TWO_FIXED_TARGET_ACTIVATIONS",
        "C09_NUMERIC_WRITE": "PASS_FIVE_FIXED_WRITES",
        "C10_SAVE_CLOSE_REOPEN_READBACK": "PASS_FIXED_OUTPUT_AND_TWO_RECTANGLES",
        "C11_JSON_VALUE_TYPE_COMPARE": "FAIL_SEVEN_OF_TWELVE_AND_THREE_UNCAPTURED_INLINE_EXPRESSIONS",
        "C12_FAILURE_CLOSE_NO_SAVE": "PASS_TWO_FAILURE_BRANCHES",
    }

    safety_pass = all(count == 0 for count in forbidden_counts.values()) and all(
        [
            structure["output_guard_count"] == 1,
            structure["source_json_write_count"] == 7,
            structure["source_json_write_all_under_fixed_root"],
            structure["mode_json_write_count"] == 1,
            structure["mode_json_write_under_fixed_root"],
            structure["save_as_count"] == 1,
            structure["save_as_fixed_output_count"] == 1,
            generated.count(str(HELPER.resolve()).replace("\\", "\\\\")) == 1,
            generated.count(str(INVOCATION.resolve()).replace("\\", "\\\\")) == 1,
        ]
    )
    safety = {
        "kind": "STATIC_TOKEN_AND_FIXED_PATH_AUDIT_ONLY_NOT_EXECUTION",
        "forbidden_runtime_fragments": forbidden_counts,
        "file_writes": {
            "source_json_count": len(source_json_writes),
            "mode_json_count": len(mode_json_writes),
            "all_under_fixed_a4_json_root": structure["source_json_write_all_under_fixed_root"] and structure["mode_json_write_under_fixed_root"],
        },
        "save_as_only_fixed_output": structure["save_as_count"] == 1 and structure["save_as_fixed_output_count"] == 1,
        "helper_invocation_or_launcher_creation_or_modification": False,
        "network_or_delete_or_security_setting_token_count": sum(forbidden_counts.values()),
        "pass": safety_pass,
    }

    delivery_pass = all(
        [
            capture["pre_send"]["normal_m365_chat_confirmed"],
            capture["pre_send"]["new_chat_without_observed_message_history"],
            capture["pre_send"]["submitted_body_dom_reconstruction_exact"],
            capture["pre_send"]["visible_attachment_count"] == 1,
            capture["response"]["complete"],
            capture["response"]["code_copy_button_count"] == 1,
            capture["response"]["plain_text_badge_count"] == 1,
            not capture["generated_copy"]["contains_markdown_fence"],
            not capture["generated_copy"]["contains_visual_line_number_prefix"],
            not capture["generated_copy"]["manual_edit"],
            structure["first_and_last_are_pad_instructions"],
        ]
    )

    stop_reasons = [
        "Decoded C06 launcher does not equal the fixed A4 launcher SHA, has a PowerShell parser error, and omits helper execution and SHA-validation logic.",
        "C11 contains 7 of the required 12 source/saved JSON comparisons; positions 8 through 12 are absent.",
        "Three numeric comparisons use an uncaptured inline Variables.ConvertCustomObjectToJson(...) expression instead of an observed PAD action/output shape.",
    ]
    final_status = "STOPPED_FAIL_GENERATED_ROBIN_WIRING_AND_FIXED_LAUNCHER_MISMATCH"

    live_send = {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "recorded_at": datetime.now().astimezone().isoformat(),
        "status": "SENT_ONCE_RESPONSE_COMPLETE_ONE_PLAIN_TEXT_CODE_PREVIEW_GENERATED",
        "resumed_from_commit": BASE_COMMIT,
        "target": capture["target"],
        "conversation_url": capture["conversation_url"],
        "pre_send": capture["pre_send"],
        "send_button_clicked": True,
        "send_count": 1,
        "send_limit_total": 1,
        "send_limit_consumed": True,
        "response_observed_complete": True,
        "response_ui_inner_text_sha256": EXPECTED_SHA256["response"],
        "generated_robin_sha256": EXPECTED_SHA256["generated"],
        "generated_copy": capture["generated_copy"],
        "resend_performed": False,
    }

    assessment = {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "candidate_id": CANDIDATE_ID,
        "route_id": ROUTE_ID,
        "recorded_at": datetime.now().astimezone().isoformat(),
        "generation_status": "GENERATED_ONE_UNMODIFIED_ROBIN_BUT_REJECTED_BEFORE_PAD",
        "fixed_identity": {
            "instruction_sha256": EXPECTED_SHA256["instruction"],
            "submitted_body_sha256": EXPECTED_SHA256["submitted_body"],
            "bundle_sha256": EXPECTED_SHA256["bundle"],
            "wiring_sha256": EXPECTED_SHA256["wiring"],
            "helper_sha256": EXPECTED_SHA256["helper"],
            "invocation_sha256": EXPECTED_SHA256["invocation"],
            "launcher_sha256": EXPECTED_SHA256["launcher"],
        },
        "delivery": {
            "send_count": 1,
            "send_limit": 1,
            "ui_plain_text_code_preview_count": 1,
            "dom_pre_element_count": capture["response"]["pre_element_count"],
            "dom_code_element_count": capture["response"]["code_element_count"],
            "generated_robin_unmodified": True,
            "generated_robin_sha256": EXPECTED_SHA256["generated"],
            "generated_robin_utf8_bytes": len(raw),
            "generated_robin_line_count": len(lines),
            "generated_robin_final_newline": raw.endswith(b"\n"),
            "pass": delivery_pass,
        },
        "syntax_and_structure": structure,
        "fixed_launcher": launcher,
        "wiring_conformance": {
            "required_text_mappings": 7,
            "observed_text_source_sets": len(source_sets),
            "text_source_sets_match_wiring": source_sets == expected_source_sets,
            "observed_text_source_json_conversions": len(source_jsons),
            "observed_text_source_json_writes": len(source_json_writes),
            "required_numeric_mappings": 5,
            "observed_numeric_writes": len(numeric_writes),
            "required_readbacks": 2,
            "observed_readbacks": structure["typed_readback_rectangle_count"],
            "required_comparisons": 12,
            "observed_comparisons": len(comparison_lines),
            "comparison_lines": comparison_lines,
            "observed_comparison_texts_match_fixed_positions_1_through_7": observed_comparison_texts == expected_observed_comparison_texts,
            "missing_positions": missing_positions,
            "source_and_saved_position_coverage": f"{len(compared_saved_indexes)}/12",
            "component_assessment": component_assessment,
            "pass": False,
        },
        "safety": safety,
        "acceptance": {
            "pass": False,
            "final_status": final_status,
            "stop_reasons": stop_reasons,
            "pad_save": "NOT_RUN_STOPPED_ON_GENERATED_ROBIN_MISMATCH",
            "pad_recopy": "NOT_RUN_STOPPED_ON_GENERATED_ROBIN_MISMATCH",
            "run1": "NOT_RUN_STOPPED_BEFORE_PAD",
            "run2": "NOT_RUN_STOPPED_BEFORE_PAD",
            "pad_run_count": 0,
            "resend": "NOT_RUN_LIMIT_CONSUMED_AND_STOP_CONDITION",
            "manual_generated_robin_edit": False,
            "next_candidate_created": False,
            "github_write": False,
        },
        "preserved_boundaries": {
            "formal_r12_status": "UNCHANGED_FAIL",
            "past_t2_auxiliary_status": "UNCHANGED_PASS_NOT_INHERITED",
            "a3_status": "UNCHANGED_REFUSAL_NOT_REUSED",
            "legacy_558_difference_record": "PRESERVED_NOT_RECLASSIFIED",
        },
    }

    protected_before = json.loads(PROTECTED_BEFORE.read_text(encoding="utf-8"))
    mismatches = []
    for item in protected_before["files"]:
        path = ROOT / item["path"]
        observed = sha256(path) if path.is_file() else None
        if observed != item["sha256"]:
            mismatches.append({"path": item["path"], "expected": item["sha256"], "actual": observed})
    work_sha = sha256(WORK) if WORK.is_file() else None
    template_sha = sha256(TEMPLATE)
    integrity = {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "recorded_at": datetime.now().astimezone().isoformat(),
        "status": "PASS_STOPPED_WITHOUT_PAD_OR_RUNTIME_MUTATION" if not mismatches and work_sha == template_sha and not OUTPUT.exists() and not JSON_ROOT.exists() else "FAIL_INTEGRITY",
        "protected_file_count": len(protected_before["files"]),
        "protected_mismatch_count": len(mismatches),
        "protected_mismatches": mismatches,
        "runtime": {
            "work_sha256": work_sha,
            "template_sha256": template_sha,
            "work_matches_template": work_sha == template_sha,
            "output_absent": not OUTPUT.exists(),
            "a4_json_root_absent": not JSON_ROOT.exists(),
        },
        "pad_save": "NOT_RUN",
        "pad_recopy": "NOT_RUN",
        "pad_run_count": 0,
        "manual_generated_robin_edit": False,
        "next_candidate_created": False,
        "github_write": False,
    }
    if integrity["status"] != "PASS_STOPPED_WITHOUT_PAD_OR_RUNTIME_MUTATION":
        raise ValueError(f"Post-stop integrity failure: {integrity}")
    if not pre_comparison_structure_pass:
        raise ValueError("Unexpected A4 generated-Robin mismatch outside C06/C11")
    if (
        compared_saved_indexes != list(range(1, 8))
        or missing_indexes != list(range(8, 13))
        or observed_comparison_texts != expected_observed_comparison_texts
        or [item["line"] for item in inline_action_expressions] != [98, 100, 102]
    ):
        raise ValueError("A4 C11 defect set differs from the observed fixed response")
    if (
        launcher["exact_match"]
        or launcher["powershell_parser_error_count"] != 1
        or launcher["helper_invocation_count"] != 0
        or launcher["helper_sha_check_count"] != 0
        or launcher["invocation_sha_check_count"] != 0
    ):
        raise ValueError("A4 C06 defect set differs from the observed fixed response")
    if launcher["exact_match"] or structure_pass or assessment["wiring_conformance"]["pass"]:
        raise ValueError("Expected A4 generated-Robin stop defect did not reproduce")
    if not delivery_pass or not safety_pass:
        raise ValueError("Delivery capture or static safety evidence is internally inconsistent")

    missing_summary = ", ".join(
        f'{item["source"].replace("fixtures/EX03/", "")} -> {item["saved"]}' for item in missing_positions
    )
    result = f"""# {CYCLE_ID} final result

## Decision

`{final_status}`

The fixed A4 submitted body and same-version bundle were sent exactly once to the normal Microsoft 365 Copilot chat. Copilot produced one Plain Text code preview. The code-copy payload was preserved without editing as `generated.robin` with SHA-256 `{EXPECTED_SHA256['generated']}`.

The generated Robin was rejected before PAD. C06 decodes to SHA-256 `{launcher['decoded_terminal_lf_restored_sha256']}`, not the fixed launcher SHA-256 `{EXPECTED_SHA256['launcher']}`. The decoded payload has {launcher['decoded_line_count']} lines instead of {launcher['expected_line_count']}, contains neither the fixed helper invocation nor the helper/invocation SHA checks, and has {len(parser_errors)} PowerShell parser error(s).

C11 contains {len(comparison_lines)} of 12 required comparisons. Missing fixed positions: {missing_summary}. Lines 98, 100, and 102 also use an uncaptured inline `Variables.ConvertCustomObjectToJson(...)` expression rather than the captured PAD action/output form. These failures independently trigger the fixed stop condition.

## Fixed identity

- Candidate: `{CANDIDATE_ID}`
- Route: `{ROUTE_ID}`
- Instruction SHA-256: `{EXPECTED_SHA256['instruction']}`
- Submitted body SHA-256: `{EXPECTED_SHA256['submitted_body']}`
- Bundle SHA-256: `{EXPECTED_SHA256['bundle']}`
- WIRING SHA-256: `{EXPECTED_SHA256['wiring']}`
- Helper SHA-256: `{EXPECTED_SHA256['helper']}`
- Invocation SHA-256: `{EXPECTED_SHA256['invocation']}`
- Fixed launcher SHA-256: `{EXPECTED_SHA256['launcher']}`
- Generated Robin SHA-256: `{EXPECTED_SHA256['generated']}`
- Copilot response text SHA-256: `{EXPECTED_SHA256['response']}`
- Conversation: `{capture['conversation_url']}`

## Checks and stop boundary

- Copilot send: 1 / 1
- Plain Text code previews: 1
- Browser code-copy payload: unmodified, LF-only, no final newline, 113 lines
- PAD IF/ELSE/END balance: PASS
- Embedded PowerShell parser: {len(parser_errors)} error(s)
- Static forbidden-token and fixed-path safety audit: PASS
- Fixed launcher exactness: FAIL
- Text source JSON mappings/writes: 7 / 7 (fixed launcher gate FAIL; no transfer was run)
- Numeric writes: 5 / 5
- Readback rectangles: 2 / 2
- JSON value/type comparisons: {len(comparison_lines)} / 12, FAIL
- Uncaptured inline expression shapes: {len(inline_action_expressions)}, FAIL
- PAD save/re-copy: NOT_RUN
- PAD Run1 / Run2: NOT_RUN / NOT_RUN
- Resend / manual repair / additional run / next candidate / GitHub write: 0 / 0 / 0 / 0 / 0

## Preserved state

- Protected files checked: {len(protected_before['files'])}
- Protected mismatches: 0
- Work SHA-256: `{work_sha}`
- Work still matches the fixed template: true
- Output absent: true
- A4 JSON handoff directory absent: true
- Formal r12 FAIL remains unchanged.
- Fixed-helper T2 auxiliary PASS is not inherited.
- A3 refusal remains separate and unchanged.
- The legacy 558-difference record remains preserved and is not reclassified.

No PAD/Excel operation was performed after the generated-Robin mismatch was found.
"""
    return live_send, assessment, integrity, result


def main() -> int:
    live_send, assessment, integrity, result = build_assessment()
    write_json_new(OUTPUTS["live_send"], live_send)
    write_json_new(OUTPUTS["assessment"], assessment)
    write_json_new(OUTPUTS["integrity"], integrity)
    write_text_new(OUTPUTS["result"], result)
    print(json.dumps({
        "status": assessment["acceptance"]["final_status"],
        "generated_robin_sha256": assessment["delivery"]["generated_robin_sha256"],
        "decoded_launcher_sha256": assessment["fixed_launcher"]["decoded_terminal_lf_restored_sha256"],
        "comparison_count": assessment["wiring_conformance"]["observed_comparisons"],
        "missing_comparison_count": len(assessment["wiring_conformance"]["missing_positions"]),
        "pad_run_count": assessment["acceptance"]["pad_run_count"],
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
