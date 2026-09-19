#!/usr/bin/env python3
"""Evaluate the normal gate, then the final normal/negative trial evidence."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
BASELINE = "1f929d6c4e1ba5bc4d963374e3e322c7a52649c1"
TRIAL_ID = "EX03-R2R3-POSTFIX-20260917-T1"
TRIAL = PROBE / "trials" / TRIAL_ID
PLAN = json.loads((TRIAL / "plan.json").read_text(encoding="utf-8"))
TEMPLATE = PROBE / "template.xlsx"
SOURCE = PROBE / "source.xlsx"
NORMAL_OUTPUT = '{"status":"OK","mode":"NORMAL","text_writes":3,"formats_restored":true}'
NEGATIVE_OUTPUT = '{"status":"EXPECTED_ERROR","mode":"INJECT_AFTER_FORMAT_CHANGE","format_restored":true,"value_unchanged":true}'


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def assert_equal(actual: object, expected: object, label: str) -> None:
    if actual != expected:
        raise ValueError(f"{label}: expected {expected!r}, got {actual!r}")


def verify_recopy(phase: Path) -> dict:
    record = load(phase / "pad-recopy.json")
    candidate = phase / "candidate.robin"
    recopy = phase / "pad-recopy-before-run.robin"
    assert_equal(record["result"], "PASS_EXACT_PAD_SAVE_RECOPY_BEFORE_RUN", "recopy result")
    assert_equal(sha256(candidate), sha256(recopy), "candidate/recopy SHA")
    assert_equal(record["candidate_sha256"], sha256(candidate), "recorded candidate SHA")
    assert_equal(record["recopy_sha256"], sha256(recopy), "recorded recopy SHA")
    assert_equal(record["run_invocations_at_capture"], 0, "run count at re-copy")
    return record


def actual_pad_json(runtime: Path, mode: str) -> list[dict[str, object]]:
    expected = [
        '{"probe":"O\'Brien"}',
        '{"probe":"He said \\"Go\\"\\nSecond line \'quoted\'"}',
        '{"probe":"100%"}',
        '{"probe":42.5}',
        json.dumps({"probe": mode}, separators=(",", ":")),
    ]
    names = ["source-1.json", "source-2.json", "source-3.json", "source-4.json", "mode.json"]
    result: list[dict[str, object]] = []
    for name, value in zip(names, expected, strict=True):
        path = runtime / name
        raw = path.read_bytes()
        assert_equal(raw.startswith(b"\xef\xbb\xbf"), True, f"{name} UTF-8 BOM")
        assert_equal(raw.decode("utf-8-sig"), value, f"{name} JSON")
        result.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": sha256(path),
                "encoding": "UTF-8 with BOM",
                "json": value,
            }
        )
    return result


def excel_com_inspect(path: Path) -> dict:
    literal = str(path).replace("'", "''")
    command = r"""
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$ErrorActionPreference='Stop'
$excel=$null;$book=$null;$sheet=$null
try {
  $excel=New-Object -ComObject Excel.Application
  $excel.Visible=$false
  $excel.DisplayAlerts=$false
  $book=$excel.Workbooks.Open('__PATH__',0,$true)
  $sheet=$book.Worksheets.Item('Target')
  $rows=@()
  foreach($address in @('A2','B2','C2','D2')) {
    $cell=$null
    try {
      $cell=$sheet.Range($address)
      $value=$cell.Value2
      $rows += [ordered]@{
        address=$address
        value=$value
        value_type=if($null -eq $value){'null'}else{$value.GetType().FullName}
        number_format=[string]$cell.NumberFormat
        number_format_local=[string]$cell.NumberFormatLocal
        prefix=[string]$cell.PrefixCharacter
        has_formula=[bool]$cell.HasFormula
      }
    }
    finally { if($null -ne $cell){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($cell)} }
  }
  $inspection=[ordered]@{read_only=[bool]$book.ReadOnly;cells=$rows}
  $json=[string]($inspection|ConvertTo-Json -Compress -Depth 5)
  [Console]::Out.Write([Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json)))
}
finally {
  if($null -ne $book){$book.Close($false);[void][Runtime.InteropServices.Marshal]::ReleaseComObject($book)}
  if($null -ne $sheet){[void][Runtime.InteropServices.Marshal]::ReleaseComObject($sheet)}
  if($null -ne $excel){$excel.Quit();[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}
  [GC]::Collect();[GC]::WaitForPendingFinalizers()
}
""".replace("__PATH__", literal)
    before = sha256(path)
    completed = subprocess.run(
        [
            r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    result = json.loads(base64.b64decode(completed.stdout.strip()).decode("utf-8"))
    result["result_xlsx_sha256_before"] = before
    result["result_xlsx_sha256_after"] = sha256(path)
    result["result_xlsx_unchanged"] = result["result_xlsx_sha256_before"] == result["result_xlsx_sha256_after"]
    return result


def verify_normal_observation(observation: dict) -> None:
    assert_equal(observation["trial_id"], TRIAL_ID, "normal trial id")
    assert_equal(observation["phase"], "normal", "normal phase")
    flow = observation["flow"]
    for key in ("paste_invocations", "save_invocations", "recopy_invocations", "run_invocations"):
        assert_equal(flow[key], 1, f"normal {key}")
    assert_equal(flow["power_fx_enabled"], False, "normal Power Fx")
    assert_equal(flow["action_count"], 63, "normal action count")
    run = observation["run"]
    assert_equal(run["terminal"], "READY", "normal terminal")
    assert_equal(run["powershell_output"], NORMAL_OUTPUT, "normal PowerShell output")
    assert_equal(run["probe_state"], "SUCCESS_GATE_PASSED_SAVED_READBACK_READY", "normal state")
    for key in (
        "script_gate_passed",
        "numeric_write_entered",
        "save_as_entered",
        "source1_vs_saved",
        "source2_vs_saved",
        "source3_vs_saved",
        "source4_vs_saved",
    ):
        assert_equal(run[key], True, f"normal {key}")


def verify_negative_observation(observation: dict) -> None:
    assert_equal(observation["trial_id"], TRIAL_ID, "negative trial id")
    assert_equal(observation["phase"], "negative", "negative phase")
    flow = observation["flow"]
    for key in ("paste_invocations", "save_invocations", "recopy_invocations", "run_invocations"):
        assert_equal(flow[key], 1, f"negative {key}")
    assert_equal(flow["power_fx_enabled"], False, "negative Power Fx")
    assert_equal(flow["action_count"], 63, "negative action count")
    run = observation["run"]
    assert_equal(run["terminal"], "READY", "negative terminal")
    assert_equal(run["powershell_output"], NEGATIVE_OUTPUT, "negative PowerShell output")
    assert_equal(run["probe_state"], "SCRIPT_NOT_SUCCESS_NO_SAVE", "negative state")
    for key in ("script_gate_passed", "numeric_write_entered", "save_as_entered"):
        assert_equal(run[key], False, f"negative {key}")


def baseline_files_unchanged() -> dict[str, object]:
    preflight = load(TRIAL / "preflight.json")
    changed: list[str] = []
    for name, expected_blob in preflight["baseline_probe_blobs"].items():
        current = ROOT / name
        actual_blob = subprocess.check_output(
            ["git", "hash-object", f"--path={name}", str(current)], cwd=ROOT, text=True
        ).strip()
        if actual_blob != expected_blob:
            changed.append(name)
    return {"unchanged": not changed, "changed": changed, "checked": len(preflight["baseline_probe_blobs"])}


def evaluate_normal() -> dict:
    phase = TRIAL / "normal"
    runtime = phase / "runtime"
    verify_recopy(phase)
    observation = load(phase / "pad-observation.json")
    verify_normal_observation(observation)
    pad_json = actual_pad_json(runtime, "NORMAL")
    result = runtime / "result.xlsx"
    if not result.is_file():
        raise FileNotFoundError("Normal result.xlsx is absent")
    artifact = load(phase / "artifact-inspection.json")
    assert_equal(artifact["result_xlsx_unchanged"], True, "artifact inspection immutability")
    assert_equal(artifact["values"], [["O'Brien", 'He said "Go"\nSecond line \'quoted\'', "100%", 42.5]], "artifact values")
    assert_equal(artifact["formulas"], [["", "", "", ""]], "artifact formulas")
    assert_equal(artifact["javascript_value_types"], ["string", "string", "string", "number"], "artifact value types")

    com = excel_com_inspect(result)
    template_com = excel_com_inspect(TEMPLATE)
    expected_cells = [
        {"address": "A2", "value": "O'Brien", "value_type": "System.String", "prefix": "", "has_formula": False},
        {"address": "B2", "value": 'He said "Go"\nSecond line \'quoted\'', "value_type": "System.String", "prefix": "", "has_formula": False},
        {"address": "C2", "value": "100%", "value_type": "System.String", "prefix": "", "has_formula": False},
        {"address": "D2", "value": 42.5, "value_type": "System.Double", "prefix": "", "has_formula": False},
    ]
    assert_equal(com["read_only"], True, "COM read-only")
    assert_equal(template_com["read_only"], True, "template COM read-only")
    for actual, template_cell, expected in zip(com["cells"], template_com["cells"], expected_cells, strict=True):
        for key, value in expected.items():
            assert_equal(actual[key], value, f"COM {expected['address']} {key}")
        for key in ("number_format", "number_format_local", "prefix", "has_formula"):
            assert_equal(actual[key], template_cell[key], f"COM {expected['address']} original {key}")
    assert_equal(com["result_xlsx_unchanged"], True, "COM inspection immutability")
    assert_equal(template_com["result_xlsx_unchanged"], True, "template COM inspection immutability")
    com_record = {
        "result": com,
        "template": template_com,
        "all_number_format_prefix_formula_equal": True,
    }
    write_json(phase / "excel-com-inspection.json", com_record)

    preserved = phase / "preserved-result.xlsx"
    if preserved.exists():
        raise FileExistsError("Refusing to overwrite preserved normal result")
    shutil.copyfile(result, preserved)
    assert_equal(sha256(preserved), sha256(result), "preserved normal result SHA")
    old = baseline_files_unchanged()
    assert_equal(old["unchanged"], True, "old evidence unchanged after normal")
    gate = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "phase": "normal",
        "result": "PASS_NORMAL_GATE_NEGATIVE_ONE_RUN_AUTHORIZED",
        "candidate_sha256": sha256(phase / "candidate.robin"),
        "recopy_sha256": sha256(phase / "pad-recopy-before-run.robin"),
        "result_xlsx_sha256": sha256(result),
        "preserved_result_sha256": sha256(preserved),
        "pad_json": pad_json,
        "pad_observation": observation,
        "artifact_inspection": artifact,
        "excel_com_inspection": com_record,
        "old_evidence": old,
    }
    write_json(phase / "normal-gate.json", gate)
    print(json.dumps(gate, ensure_ascii=False, separators=(",", ":")))
    return gate


def evaluate_final() -> dict:
    normal = TRIAL / "normal"
    negative = TRIAL / "negative"
    normal_gate = load(normal / "normal-gate.json")
    assert_equal(normal_gate["result"], "PASS_NORMAL_GATE_NEGATIVE_ONE_RUN_AUTHORIZED", "normal gate")
    assert_equal(sha256(normal / "runtime/result.xlsx"), normal_gate["result_xlsx_sha256"], "normal result preserved")
    assert_equal(sha256(normal / "preserved-result.xlsx"), normal_gate["preserved_result_sha256"], "normal preserved copy")
    verify_recopy(negative)
    observation = load(negative / "pad-observation.json")
    verify_negative_observation(observation)
    pad_json = actual_pad_json(negative / "runtime", "INJECT_AFTER_FORMAT_CHANGE")
    if (negative / "runtime/result.xlsx").exists():
        raise ValueError("Negative completed output exists")
    assert_equal(sha256(negative / "runtime/work.xlsx"), sha256(TEMPLATE), "negative work unchanged")
    old = baseline_files_unchanged()
    assert_equal(old["unchanged"], True, "old evidence unchanged after final")
    final = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "result": "PASS_NORMAL_AND_FORCED_EXCEPTION_ONE_RUN_EACH",
        "baseline_commit": BASELINE,
        "normal": {
            "run_invocations": 1,
            "gate_result": normal_gate["result"],
            "result_xlsx_sha256": normal_gate["result_xlsx_sha256"],
            "preserved_result_sha256": normal_gate["preserved_result_sha256"],
            "pad_observation": normal_gate["pad_observation"],
        },
        "negative": {
            "run_invocations": 1,
            "powershell_output": observation["run"]["powershell_output"],
            "format_restored_directly_observed_by_script": True,
            "value_unchanged_directly_observed_by_script": True,
            "pre_type_check_stop": False,
            "success_gate_passed": False,
            "numeric_write_entered": False,
            "save_as_entered": False,
            "completed_output_exists": False,
            "work_sha256": sha256(negative / "runtime/work.xlsx"),
            "template_sha256": sha256(TEMPLATE),
            "work_unchanged": True,
            "pad_json": pad_json,
            "pad_observation": observation,
        },
        "fixed_sha256": {
            "source_xlsx": sha256(SOURCE),
            "template_xlsx": sha256(TEMPLATE),
            "fixed_script": sha256(PROBE / "embedded-safe.ps1.txt"),
            "fixed_normal_robin": sha256(PROBE / "candidate-normal-postfix.robin"),
            "fixed_negative_robin": sha256(PROBE / "candidate-negative-postfix.robin"),
            "trial_normal_robin": sha256(normal / "candidate.robin"),
            "trial_negative_robin": sha256(negative / "candidate.robin"),
        },
        "old_evidence": old,
        "remaining": [
            "The evidence applies only to the fixed three strings, fixed number 42.5, fixed cells, and this PAD/Excel/Windows PowerShell environment.",
            "No Copilot submission, EX03 integrated rerun, candidate version, full regression, manifest correction, or GitHub write was performed.",
        ],
    }
    write_json(TRIAL / "final-verification.json", final)
    print(json.dumps(final, ensure_ascii=False, separators=(",", ":")))
    return final


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("normal", "final"), required=True)
    args = parser.parse_args()
    if PLAN["trial_id"] != TRIAL_ID:
        raise ValueError("Trial plan ID mismatch")
    if args.phase == "normal":
        evaluate_normal()
    else:
        evaluate_final()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
