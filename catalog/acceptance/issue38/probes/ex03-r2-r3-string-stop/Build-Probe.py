#!/usr/bin/env python3
"""Build the bounded EX03 R2/R3 string handoff and stop-gate probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
R11_ROBIN = ROOT / "copilot/versions/20260917-excel-r11/support/EX03-R11-Independent-PAD-Recopy.robin"
R11_SCRIPT = ROOT / "copilot/versions/20260917-excel-r11/support/EX03-R11-Independent-Minimal-FormatSandwich.ps1.txt"
SAFE_SCRIPT = PROBE / "embedded-safe.ps1.txt"
RUNTIME = PROBE / "runtime"
SOURCE = PROBE / "source.xlsx"
TEMPLATE = PROBE / "template.xlsx"
OUTPUT = RUNTIME / "result.xlsx"
WORK = RUNTIME / "work.xlsx"
SUCCESS_OUTPUT = '{"status":"OK","mode":"NORMAL","text_writes":3,"formats_restored":true}'
MODES = {
    "normal": "NORMAL",
    "negative": "INJECT_AFTER_FORMAT_CHANGE",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8", newline="\n")


def write_json(path: Path, value: object) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def robin_literal(value: str) -> str:
    return (
        "$'''"
        + value.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        + "'''"
    )


def script_action(script: str) -> str:
    escaped = script.rstrip("\r\n").replace("\\", "\\\\").replace("'", "\\'")
    return "Scripting.RunPowershellScript.RunScript Script: $'''" + escaped + "''' ScriptOutput=> PowershellOutput"


def build_robin(mode: str, script: str) -> str:
    source_path = robin_literal(str(SOURCE))
    work_path = robin_literal(str(WORK))
    output_path = robin_literal(str(OUTPUT))
    json_paths = [robin_literal(str(RUNTIME / f"source-{index}.json")) for index in range(1, 5)]
    mode_path = robin_literal(str(RUNTIME / "mode.json"))
    success = robin_literal(SUCCESS_OUTPUT)
    normal = robin_literal("NORMAL")
    lines = [
        "SET ProbeState TO $'''NOT_STARTED'''",
        "SET ScriptGatePassed TO False",
        "SET NumericWriteEntered TO False",
        "SET SaveAsEntered TO False",
        f"IF (File.IfFile.Exists File: {output_path}) THEN",
        "    SET ProbeState TO $'''OUTPUT_EXISTS_NO_RUN'''",
        "ELSE",
        f"    Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: {source_path} Visible: True ReadOnly: True UseMachineLocale: False Instance=> SourceBook",
        "    Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: SourceBook Name: $'''Source'''",
        "    Excel.ReadFromExcel.ReadCells Instance: SourceBook StartColumn: $'''A''' StartRow: 2 EndColumn: $'''D''' EndRow: 2 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> SourceData",
        "    Excel.CloseExcel.Close Instance: SourceBook",
        "    SET Source1 TO SourceData[0][0]",
        "    SET Source2 TO SourceData[0][1]",
        "    SET Source3 TO SourceData[0][2]",
        "    SET Source4 TO SourceData[0][3]",
        "    Variables.ConvertCustomObjectToJson CustomObject: { 'probe': Source1 } Json=> Source1Json",
        "    Variables.ConvertCustomObjectToJson CustomObject: { 'probe': Source2 } Json=> Source2Json",
        "    Variables.ConvertCustomObjectToJson CustomObject: { 'probe': Source3 } Json=> Source3Json",
        "    Variables.ConvertCustomObjectToJson CustomObject: { 'probe': Source4 } Json=> Source4Json",
        f"    SET RunMode TO {robin_literal(mode)}",
        "    Variables.ConvertCustomObjectToJson CustomObject: { 'probe': RunMode } Json=> RunModeJson",
    ]
    for index, json_path in enumerate(json_paths, start=1):
        lines.append(
            f"    File.WriteText File: {json_path} TextToWrite: Source{index}Json AppendNewLine: False IfFileExists: File.IfFileExists.Overwrite Encoding: File.FileEncoding.UTF8"
        )
    lines.extend(
        [
            f"    File.WriteText File: {mode_path} TextToWrite: RunModeJson AppendNewLine: False IfFileExists: File.IfFileExists.Overwrite Encoding: File.FileEncoding.UTF8",
            f"    Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: {work_path} Visible: True ReadOnly: False UseMachineLocale: False Instance=> Work",
            "    Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Work Name: $'''Target'''",
            "    " + script_action(script),
            f"    IF PowershellOutput = {success} THEN",
            f"        IF RunMode = {normal} THEN",
            "            SET ScriptGatePassed TO True",
            "            SET NumericWriteEntered TO True",
            "            Excel.WriteToExcel.WriteCell Instance: Work Value: Source4 Column: $'''D''' Row: 2",
            "            SET SaveAsEntered TO True",
            f"            Excel.SaveExcel.SaveAs Instance: Work DocumentFormat: Excel.ExcelFormat.OpenXmlWorkbook DocumentPath: {output_path}",
            "            Excel.CloseExcel.Close Instance: Work",
            f"            Excel.LaunchExcel.LaunchAndOpenUnderExistingProcess Path: {output_path} Visible: True ReadOnly: True UseMachineLocale: False Instance=> Reopened",
            "            Excel.SetActiveWorksheet.ActivateWorksheetByName Instance: Reopened Name: $'''Target'''",
            "            Excel.ReadFromExcel.ReadCells Instance: Reopened StartColumn: $'''A''' StartRow: 2 EndColumn: $'''D''' EndRow: 2 GetCellContentsMode: Excel.GetCellContentsMode.TypedValues FirstLineIsHeader: False RangeValue=> Readback",
            "            Excel.CloseExcel.Close Instance: Reopened",
            "            SET Saved1 TO Readback[0][0]",
            "            SET Saved2 TO Readback[0][1]",
            "            SET Saved3 TO Readback[0][2]",
            "            SET Saved4 TO Readback[0][3]",
            "            Variables.ConvertCustomObjectToJson CustomObject: { 'probe': Saved1 } Json=> Saved1Json",
            "            Variables.ConvertCustomObjectToJson CustomObject: { 'probe': Saved2 } Json=> Saved2Json",
            "            Variables.ConvertCustomObjectToJson CustomObject: { 'probe': Saved3 } Json=> Saved3Json",
            "            Variables.ConvertCustomObjectToJson CustomObject: { 'probe': Saved4 } Json=> Saved4Json",
            "            SET Source1VsSaved TO Source1Json = Saved1Json",
            "            SET Source2VsSaved TO Source2Json = Saved2Json",
            "            SET Source3VsSaved TO Source3Json = Saved3Json",
            "            SET Source4VsSaved TO Source4Json = Saved4Json",
            "            SET ProbeState TO $'''SUCCESS_GATE_PASSED_SAVED_READBACK_READY'''",
            "        ELSE",
            "            Excel.CloseExcel.Close Instance: Work",
            "            SET ProbeState TO $'''MODE_NOT_NORMAL_NO_SAVE'''",
            "        END",
            "    ELSE",
            "        Excel.CloseExcel.Close Instance: Work",
            "        SET ProbeState TO $'''SCRIPT_NOT_SUCCESS_NO_SAVE'''",
            "    END",
            "END",
        ]
    )
    # PAD reserializes action boundaries as CRLF while preserving embedded
    # PowerShell newlines inside the RunScript literal.  Emit that canonical
    # form so a save/re-copy comparison is byte-exact.
    return "\r\n".join(lines) + "\r\n"


def git_object(revision: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"{revision}:{path}"], cwd=ROOT, text=True
    ).strip()


def build_unsafe_r11_example() -> str:
    values = [
        "O'Brien",
        'He said "Go"\nSecond line \'quoted\'',
        "100%",
        "O'Brien",
        'He said "Go"\nSecond line \'quoted\'',
        "100%",
        "O'Brien",
    ]
    expanded = R11_SCRIPT.read_text(encoding="utf-8")
    for index, value in enumerate(values, start=1):
        payload = json.dumps({"probe": value}, ensure_ascii=False, separators=(",", ":"))
        expanded = expanded.replace(f"%TextSource{index}Json%", payload)
    return expanded


def write_postfix_candidates() -> None:
    script = SAFE_SCRIPT.read_text(encoding="utf-8")
    generated: dict[str, Path] = {}
    for label, mode in MODES.items():
        path = PROBE / f"candidate-{label}-postfix.robin"
        write_text(path, build_robin(mode, script))
        generated[label] = path
    write_json(
        PROBE / "postfix-plan.json",
        {
            "schema_version": 1,
            "baseline_commit": "f8765ea42e71e43d4924a6f8101b5950db31868c",
            "reason": "Windows PowerShell 5.1 restores JSON 42.5 as System.Decimal; accept only observed Decimal plus existing Double.",
            "live_run_candidate_sha256": sha256(PROBE / "candidate-normal.robin"),
            "postfix_safe_script_sha256": sha256(SAFE_SCRIPT),
            "postfix_candidate_sha256": {
                label: sha256(path) for label, path in generated.items()
            },
            "live_rerun": "NOT_RUN_STOP_CONDITION",
        },
    )


def main(*, postfix_only: bool = False) -> int:
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != "f8765ea42e71e43d4924a6f8101b5950db31868c":
        raise ValueError("Probe must be built from f8765ea")
    for path in (SOURCE, TEMPLATE, SAFE_SCRIPT, R11_ROBIN, R11_SCRIPT):
        if not path.is_file():
            raise FileNotFoundError(path)
    if postfix_only:
        write_postfix_candidates()
        return 0
    RUNTIME.mkdir(exist_ok=True)
    for name in ("result.xlsx", "source-1.json", "source-2.json", "source-3.json", "source-4.json", "mode.json"):
        if (RUNTIME / name).exists():
            raise FileExistsError(f"Refusing stale runtime file: {RUNTIME / name}")
    shutil.copyfile(TEMPLATE, WORK)

    script = SAFE_SCRIPT.read_text(encoding="utf-8")
    for label, mode in MODES.items():
        write_text(PROBE / f"candidate-{label}.robin", build_robin(mode, script))
    write_text(PROBE / "r11-unsafe-interpolated-obrien.ps1.txt", build_unsafe_r11_example())

    plan = {
        "schema_version": 1,
        "baseline_commit": "f8765ea42e71e43d4924a6f8101b5950db31868c",
        "scope": "Dedicated local synthetic probe only; no r11/candidate/Copilot/EX03 integration changes.",
        "fixed_values": {
            "Source!A2": "O'Brien",
            "Source!B2": 'He said "Go"\nSecond line \'quoted\'',
            "Source!C2": "100%",
            "Source!D2": 42.5,
        },
        "target_before": {
            "Target!A2": ["BEFORE_A", "System.String", "General"],
            "Target!B2": ["BEFORE_B", "System.String", "0.00"],
            "Target!C2": ["BEFORE_C", "System.String", "General"],
            "Target!D2": [7, "System.Double", "0.00"],
        },
        "runs": [
            {"id": "normal", "mode": MODES["normal"], "maximum": 1},
            {"id": "negative", "mode": MODES["negative"], "maximum": 1},
        ],
        "negative_injection": "Target!A2 immediately after NumberFormat='@' and before Value2 assignment",
        "success_output": SUCCESS_OUTPUT,
        "required_stop_gate": "Only exact success output plus NORMAL mode encloses numeric write and SaveAs.",
        "preserved_git_objects": {
            "r11_candidate": git_object("HEAD", "copilot/versions/20260917-excel-r11"),
            "r11_robin": git_object("HEAD", "copilot/versions/20260917-excel-r11/support/EX03-R11-Independent-PAD-Recopy.robin"),
            "r11_script": git_object("HEAD", "copilot/versions/20260917-excel-r11/support/EX03-R11-Independent-Minimal-FormatSandwich.ps1.txt"),
            "r1_finalizer": git_object("HEAD", "tools/Finalize-Issue38Ex03R11FileAux.py"),
            "r1_test": git_object("HEAD", "tests/Test-Issue38Ex03R11FileAuxFinalizer.py"),
        },
        "sha256": {
            "source_xlsx": sha256(SOURCE),
            "template_xlsx": sha256(TEMPLATE),
            "safe_script": sha256(SAFE_SCRIPT),
            "r11_robin": sha256(R11_ROBIN),
            "r11_script": sha256(R11_SCRIPT),
        },
        "out_of_scope": [
            "r11 modification",
            "new candidate version",
            "Copilot submission",
            "EX03 integrated rerun",
            "manifest correction",
            "GitHub write",
            "type generalization beyond these three strings and one number",
        ],
    }
    write_json(PROBE / "plan.json", plan)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--postfix-only", action="store_true")
    args = parser.parse_args()
    raise SystemExit(main(postfix_only=args.postfix_only))
