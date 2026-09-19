#!/usr/bin/env python3
"""Record the single authorized live PAD trial for the mechanical Robin.

The recorder never edits the builder, fixed inputs, runtime work workbook, or
generated Robin.  Each phase is exclusive-create/fail-closed so a stopped trial
cannot be silently reused as a successful one.
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
TRIAL_ID = "EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE1"
RUN_ID = f"{TRIAL_ID}-RUN1"
BASELINE = "fd2cc2c345c0e0de8778d7eb05ef18daf233dc55"
FLOW_NAME = "Issue38 EX03 Mechanical P1 Live1"
TRIAL = PROBE / "trials" / TRIAL_ID
RUN = TRIAL / "run1"
BUILDER = PROBE / "Build.py"
GENERATED = PROBE / "generated/EX03-R12-FIXED-HELPER-MECHANICAL-P1.robin"
VERIFICATION = PROBE / "verification.json"

BASE = ROOT / "catalog/acceptance/issue38"
RUNTIME = BASE / "runs/EX03-attempt1"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
JSON_ROOT = RUNTIME / "a4-helper-json"
TEMPLATE = BASE / "fixtures/EX03/ひな形.xlsx"
INPUT_A = BASE / "fixtures/EX03/入力い.xlsx"
INPUT_B = BASE / "fixtures/EX03/入力ろ.xlsx"

A4 = ROOT / "copilot/versions/20260918-excel-r12-fixed-helper-a4"
WIRING = A4 / "wiring-spec.json"
BUNDLE = A4 / "knowledge/PAD-Robin-Fixed-Helper-A4-Bundle.txt"
ASSEMBLY = A4 / "assembly-rules.json"
A4_MANIFEST = A4 / "manifest.json"
HELPER = BASE / "probes/ex03-r12-fixed-helper/EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = BASE / "probes/ex03-r12-fixed-helper-a4/invocation.json"
LAUNCHER = BASE / "probes/ex03-r12-fixed-helper-a4/launcher.ps1"
FIXED_REQUEST = BASE / "requests/EX03.txt"
FIXED_SPEC = BASE / "spec.json"
FIXED_EXPECTED = BASE / "expected.json"

EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'
EXPECTED_STATE = "SUCCESS_GATE_PASSED_SAVED_READBACK_READY"
EXPECTED_SHA = {
    "generated": "3d9c1671a5debc6f0247cef8c5e0d414dc07246a7cb7ce0ac6245fb860967e47",
    "verification": "3578d75f4c7fa7f3c6b5b997b82094299d339c30780faf1453f017a2dee241e0",
    "wiring": "c62ec6951bdd36e895acfc937d7a1f390e75e8d984b26a9531cc2c88d970f58c",
    "bundle": "62695ca3c007ab291732657ddaeca66723a57115d151efc7b1730ef5341c514c",
    "assembly": "57305c13d9bff292d7c7c2bc3e3152bcd75b85fd1bd800679df1671f79c7bc6e",
    "a4_manifest": "525c5450e1e17e68d50dbaf25556e77e6e8393cf2ad2cd15792b54859ae7242f",
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "5c5a2008f55296a48f63fa65178aab971e4212455bb2af58e33149bdcaec40d8",
    "launcher": "a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "fixed_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
    "input_a": "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    "input_b": "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fixed_paths() -> dict[str, Path]:
    return {
        "generated": GENERATED,
        "verification": VERIFICATION,
        "wiring": WIRING,
        "bundle": BUNDLE,
        "assembly": ASSEMBLY,
        "a4_manifest": A4_MANIFEST,
        "helper": HELPER,
        "invocation": INVOCATION,
        "launcher": LAUNCHER,
        "fixed_request": FIXED_REQUEST,
        "fixed_spec": FIXED_SPEC,
        "fixed_expected": FIXED_EXPECTED,
        "template": TEMPLATE,
        "input_a": INPUT_A,
        "input_b": INPUT_B,
    }


def fixed_hashes() -> dict[str, str]:
    result = {name: sha256(path) for name, path in fixed_paths().items()}
    require(result == EXPECTED_SHA, f"fixed SHA mismatch: {result}")
    return result


def excel_running() -> bool:
    tasklist = subprocess.check_output(
        ["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE"],
        text=True,
        encoding="mbcs",
        errors="replace",
    )
    return "EXCEL.EXE" in tasklist.upper()


def prepare() -> None:
    require(not TRIAL.exists(), f"refusing to overwrite trial: {TRIAL}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    require(head == BASELINE, f"HEAD is not the authorized baseline: {head}")

    check = subprocess.run(
        ["python", str(BUILDER), "--check"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    check_record = json.loads(check.stdout)
    require(check_record["operation"] == "CHECK_BYTE_IDENTICAL", "builder check operation mismatch")
    require(check_record["generated_sha256"] == EXPECTED_SHA["generated"], "builder check SHA mismatch")
    require(check_record["json_writes"] == 8, "builder check JSON count mismatch")
    require(check_record["numeric_writes"] == 5, "builder check numeric count mismatch")
    require(check_record["readbacks"] == 2, "builder check readback count mismatch")
    require(check_record["comparisons"] == 12, "builder check comparison count mismatch")

    hashes = fixed_hashes()
    require(sha256(WORK) == EXPECTED_SHA["template"], "runtime work differs from template")
    require(not OUTPUT.exists(), "runtime output exists before Run")
    require(not JSON_ROOT.exists(), "runtime JSON root exists before Run")
    require(not excel_running(), "Excel is running before Run")

    TRIAL.mkdir(parents=True)
    shutil.copy2(WORK, TRIAL / "work-before.xlsx")
    require(sha256(TRIAL / "work-before.xlsx") == EXPECTED_SHA["template"], "work-before copy mismatch")

    protected = []
    for name, path in {**fixed_paths(), "builder": BUILDER}.items():
        item = {"name": name, "path": relative(path), "sha256": sha256(path)}
        try:
            item["git_blob"] = subprocess.check_output(
                ["git", "hash-object", f"--path={item['path']}", str(path)],
                cwd=ROOT,
                text=True,
            ).strip()
        except subprocess.CalledProcessError:
            item["git_blob"] = None
        protected.append(item)

    write_json(
        TRIAL / "plan.json",
        {
            "schema_version": 1,
            "trial_id": TRIAL_ID,
            "baseline_commit": BASELINE,
            "flow_name": FLOW_NAME,
            "classification": "MECHANICAL_BUILDER_PATH_LIMITED_LIVE_PAD_TRIAL_ONLY",
            "authorization": {
                "pad_paste_save_recopy": 1,
                "normal_pad_runs": 1,
                "run2": 0,
                "negative_runs": 0,
                "copilot_sends": 0,
                "candidate_creation": 0,
                "builder_modification": 0,
                "github_writes": 0,
            },
            "stop_conditions": [
                "Build.py --check or fixed SHA mismatch",
                "unknown PAD re-copy content difference, missing command, or syntax damage",
                "PAD error, comparison mismatch, safety issue, or unknown result",
            ],
            "scope_boundary": "Not Copilot generation acceptance and not Issue #38 overall acceptance.",
        },
    )
    write_json(
        TRIAL / "preflight.json",
        {
            "schema_version": 1,
            "trial_id": TRIAL_ID,
            "result": "PASS_READY_FOR_ONE_MECHANICAL_ROBIN_NORMAL_PAD_RUN",
            "baseline_commit": BASELINE,
            "build_check": check_record,
            "fixed_sha256": hashes,
            "runtime": {
                "work_path": relative(WORK),
                "work_sha256": sha256(WORK),
                "work_matches_template": True,
                "output_path": relative(OUTPUT),
                "output_absent": True,
                "json_root": relative(JSON_ROOT),
                "json_root_absent": True,
                "excel_not_running": True,
            },
            "protected_files": protected,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    print(json.dumps({"trial_id": TRIAL_ID, "status": "PASS_PREFLIGHT", "build_check": check_record}, ensure_ascii=False))


def clipboard_text() -> str:
    command = (
        "Add-Type -AssemblyName System.Windows.Forms;"
        "$value=[Windows.Forms.Clipboard]::GetText();"
        "[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($value))"
    )
    encoded = subprocess.check_output(
        ["powershell", "-NoProfile", "-Command", command],
        text=True,
        encoding="ascii",
    ).strip()
    require(bool(encoded), "clipboard is empty")
    return base64.b64decode(encoded).decode("utf-8")


def capture_recopy(flow_window_id: int, flow_name: str) -> None:
    preflight = load(TRIAL / "preflight.json")
    require(preflight["result"] == "PASS_READY_FOR_ONE_MECHANICAL_ROBIN_NORMAL_PAD_RUN", "preflight did not pass")
    recopy_path = TRIAL / "pad-recopy-before-run.robin"
    record_path = TRIAL / "pad-recopy.json"
    require(not record_path.exists(), "refusing to overwrite re-copy evidence")

    candidate = GENERATED.read_text(encoding="utf-8", newline="")
    resumed_existing_capture = recopy_path.exists()
    if resumed_existing_capture:
        recopy = recopy_path.read_text(encoding="utf-8", newline="")
    else:
        recopy = clipboard_text()
        recopy_path.write_text(recopy, encoding="utf-8", newline="")
    candidate_normalized = candidate.replace("\r\n", "\n").rstrip("\r\n") + "\n"
    recopy_normalized = recopy.replace("\r\n", "\n").rstrip("\r\n") + "\n"
    normalized_exact = recopy_normalized == candidate_normalized

    builder = load_module("issue38_mechanical_live_builder", BUILDER)
    decoded = builder.embedded_script(recopy_normalized)
    restored = decoded.encode("utf-8") + b"\n"
    decoded_launcher_sha = hashlib.sha256(restored).hexdigest()
    decoded_launcher_exact = restored == LAUNCHER.read_bytes()
    require(normalized_exact, "unknown PAD re-copy content difference")
    require(decoded_launcher_exact, "PAD re-copy decoded launcher mismatch")
    audit = builder.audit_robin(recopy_normalized.encode("utf-8"), load(WIRING), LAUNCHER.read_bytes())

    record = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "flow": {"name": flow_name, "window_id": flow_window_id, "subflow": "Main", "power_fx": "OFF"},
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "path": relative(GENERATED),
            "sha256": sha256(GENERATED),
            "characters": len(candidate),
            "utf8_bytes": len(candidate.encode("utf-8")),
        },
        "recopy": {
            "path": relative(recopy_path),
            "sha256": sha256(recopy_path),
            "characters": len(recopy),
            "utf8_bytes": len(recopy.encode("utf-8")),
            "crlf_count": recopy.count("\r\n"),
            "lf_only_count": recopy.count("\n") - recopy.count("\r\n"),
            "terminal_newline": recopy.endswith(("\r", "\n")),
        },
        "classification": {
            "normalized_line_endings_and_terminal_newline_exact": normalized_exact,
            "unknown_content_difference_count": 0,
            "missing_command_count": 0,
            "syntax_damage_count": 0,
            "decoded_launcher_sha256": decoded_launcher_sha,
            "decoded_launcher_exact": decoded_launcher_exact,
            "audit": audit,
        },
        "observation": {"paste_count": 1, "save_count": 1, "recopy_count": 1, "pad_run_count": 0},
        "recorder": {
            "resumed_existing_capture_after_loader_error": resumed_existing_capture,
            "additional_pad_copy_count": 0,
        },
        "result": "PASS_PAD_RECOPY_ONLY_KNOWN_SERIALIZATION_DIFFERENCES_RUN_ALLOWED",
    }
    write_json(record_path, record)
    print(json.dumps({"status": record["result"], "recopy_sha256": sha256(recopy_path), "audit": audit}, ensure_ascii=False))


def capture_run(args: argparse.Namespace) -> None:
    require(not RUN.exists(), f"refusing to overwrite Run evidence: {RUN}")
    identity = load(TRIAL / "pad-recopy.json")
    require(identity["result"] == "PASS_PAD_RECOPY_ONLY_KNOWN_SERIALIZATION_DIFFERENCES_RUN_ALLOWED", "re-copy gate did not pass")
    require(args.powershell_output == EXPECTED_SUCCESS, "PowerShell success JSON mismatch")
    require(args.probe_state == EXPECTED_STATE, "ProbeState mismatch")
    require(args.value_type_true_count == 12, "12 true PAD value/type results were not observed")
    require(sha256(WORK) == EXPECTED_SHA["template"], "runtime work changed")
    require(OUTPUT.is_file(), "runtime output is absent")
    require(JSON_ROOT.is_dir(), "runtime JSON handoff root is absent")

    handoff_paths = [JSON_ROOT / f"source-{index}.json" for index in range(1, 8)] + [JSON_ROOT / "mode.json"]
    require(all(path.is_file() for path in handoff_paths), "one or more JSON handoff files are absent")
    require(sorted(path.name for path in JSON_ROOT.iterdir()) == sorted(path.name for path in handoff_paths), "unexpected JSON handoff file")
    for index, path in enumerate(handoff_paths, 1):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        require(set(payload) == {"probe"}, f"unexpected JSON shape: {path.name}")
        if index <= 7:
            require(isinstance(payload["probe"], str), f"text handoff is not string: {path.name}")
        else:
            require(payload["probe"] == "NORMAL", "mode handoff is not NORMAL")

    RUN.mkdir(parents=True)
    shutil.copy2(WORK, RUN / "work.xlsx")
    shutil.copy2(OUTPUT, RUN / "result.xlsx")
    (RUN / "handoff").mkdir()
    for path in handoff_paths:
        shutil.copy2(path, RUN / "handoff" / path.name)
    output_sha = sha256(OUTPUT)
    require(sha256(RUN / "result.xlsx") == output_sha, "preserved output is not byte exact")
    require(sha256(RUN / "work.xlsx") == EXPECTED_SHA["template"], "preserved work mismatch")

    position_names = [f"Position{index}ValueTypeMatch" for index in range(1, 13)]
    write_json(
        RUN / "pad-run.json",
        {
            "schema_version": 1,
            "trial_id": TRIAL_ID,
            "run_id": RUN_ID,
            "flow_name": args.flow_name,
            "flow_window_id": args.flow_window_id,
            "run_index": 1,
            "run_invocations_total": 1,
            "started_utc": args.started_utc,
            "terminal_observed_utc": args.terminal_observed_utc,
            "variables_observed_utc": args.variables_observed_utc,
            "terminal_observation": {
                "status_bar": "READY",
                "run_button_enabled": True,
                "stop_button_disabled": True,
                "designer_error_observed": False,
                "normal_termination_observed": True,
            },
            "powershell": {
                "stdout_variable": "PowershellOutput",
                "stdout_observed": args.powershell_output,
                "stdout_matches_fixed_success_json": True,
                "separate_stderr_variable_in_saved_robin": False,
                "stderr_empty_not_claimed": True,
            },
            "status": "PASS_TERMINAL_READY_SUCCESS_JSON_NO_DESIGNER_ERROR",
        },
    )
    write_json(
        RUN / "pad-variables.json",
        {
            "schema_version": 1,
            "trial_id": TRIAL_ID,
            "run_id": RUN_ID,
            "flow_name": args.flow_name,
            "execution_requested_during_observation": False,
            "method": "PAD Variables pane after the same Run: PowershellOutput and ProbeState opened without edits; Position ValueTypeMatch filter showed all 12 true.",
            "powershell_output": {"observed_value": args.powershell_output, "match": True},
            "probe_state": {"observed_value": args.probe_state, "match": True},
            "value_type_matches": {name: {"observed_value": True, "match": True} for name in position_names},
            "counts": {"true": 12, "false": 0, "total": 12},
            "status": "PASS_SUCCESS_JSON_PROBE_STATE_AND_12_VALUE_TYPE_MATCH",
        },
    )
    write_json(
        RUN / "artifact.json",
        {
            "schema_version": 1,
            "trial_id": TRIAL_ID,
            "run_id": RUN_ID,
            "runtime_output_path": relative(OUTPUT),
            "preserved_output_path": relative(RUN / "result.xlsx"),
            "output_sha256": output_sha,
            "output_bytes": OUTPUT.stat().st_size,
            "preserved_output_exact": True,
            "runtime_work_path": relative(WORK),
            "preserved_work_path": relative(RUN / "work.xlsx"),
            "work_sha256": EXPECTED_SHA["template"],
            "preserved_work_exact": True,
            "handoff_directory": relative(RUN / "handoff"),
            "handoff_sha256": {path.name: sha256(RUN / "handoff" / path.name) for path in handoff_paths},
            "status": "PASS_MECHANICAL_LIVE1_RUN1_ARTIFACT_AND_HANDOFF_PRESERVED",
        },
    )
    print(json.dumps({"status": "PASS_RUN1_PRESERVED", "output_sha256": output_sha, "handoff_files": 8}, ensure_ascii=False))


def record_stop(args: argparse.Namespace) -> None:
    require(not RUN.exists(), f"refusing to overwrite Run evidence: {RUN}")
    for path in (TRIAL / "result.json", TRIAL / "RESULT.md"):
        require(not path.exists(), f"refusing to overwrite stop evidence: {path}")
    preflight = load(TRIAL / "preflight.json")
    recopy = load(TRIAL / "pad-recopy.json")
    require(preflight["result"] == "PASS_READY_FOR_ONE_MECHANICAL_ROBIN_NORMAL_PAD_RUN", "preflight did not pass")
    require(recopy["result"] == "PASS_PAD_RECOPY_ONLY_KNOWN_SERIALIZATION_DIFFERENCES_RUN_ALLOWED", "re-copy gate did not pass")
    require(sha256(WORK) == sha256(TEMPLATE) == EXPECTED_SHA["template"], "work/template changed after failed Run")
    require(not OUTPUT.exists(), "output exists after the stopped Run")
    require(not JSON_ROOT.exists(), "JSON root exists after the stopped Run")
    require(not excel_running(), "Excel remains running after the stopped Run")
    fixed_hashes()

    error_path = JSON_ROOT / "source-1.json"
    visible_error = (
        "無効なディレクトリ (パス '"
        + str(error_path)
        + "' の一部が見つかりませんでした..."
    )
    RUN.mkdir(parents=True)
    write_json(
        RUN / "pad-run.json",
        {
            "schema_version": 1,
            "trial_id": TRIAL_ID,
            "run_id": RUN_ID,
            "flow_name": args.flow_name,
            "flow_window_id": args.flow_window_id,
            "run_index": 1,
            "run_invocations_total": 1,
            "started_utc": args.started_utc,
            "terminal_observed_utc": args.terminal_observed_utc,
            "terminal_observation": {
                "status_bar": "ステータス: 見つかったランタイム エラー",
                "run_button_enabled": True,
                "stop_button_disabled": True,
                "designer_error_count": 1,
                "normal_termination_observed": False,
            },
            "error": {
                "type": "runtime_error",
                "visible_text_as_displayed_with_ui_truncation": visible_error,
                "subflow": "Main",
                "line": 32,
                "action": "File.WriteText source-1.json",
                "path": str(error_path),
                "path_parent_absent_after_stop": not JSON_ROOT.exists(),
            },
            "status": "STOP_PAD_RUNTIME_ERROR_LINE32_INVALID_DIRECTORY",
        },
    )
    write_json(
        RUN / "artifact-absence.json",
        {
            "schema_version": 1,
            "trial_id": TRIAL_ID,
            "run_id": RUN_ID,
            "runtime_output_path": relative(OUTPUT),
            "output_absent": True,
            "json_root": relative(JSON_ROOT),
            "json_root_absent": True,
            "excel_process_count": 0,
            "work_sha256": sha256(WORK),
            "work_matches_template": True,
            "input_sha256": {"入力い.xlsx": sha256(INPUT_A), "入力ろ.xlsx": sha256(INPUT_B)},
            "input_template_work_unchanged": True,
            "helper_success_json": "NOT_OBSERVED_RUN_STOPPED_BEFORE_HELPER",
            "target_comparison": "NOT_RUN_NO_OUTPUT",
            "outside_cell_comparison": "NOT_RUN_NO_OUTPUT",
            "effective_format_comparison": "NOT_RUN_NO_OUTPUT",
            "f6_comparison": "NOT_RUN_NO_OUTPUT",
            "status": "PASS_ABSENCE_AND_ORIGINAL_PRESERVATION_AFTER_STOP",
        },
    )
    result = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "decision": "STOP_MECHANICAL_BUILDER_PATH_RUN1_RUNTIME_DIRECTORY_MISSING",
        "scope": "Mechanical-builder path only; not Copilot generation acceptance and not Issue #38 overall acceptance.",
        "baseline_commit": BASELINE,
        "build_check": preflight["build_check"],
        "execution_identity": {
            "generated_robin_sha256": EXPECTED_SHA["generated"],
            "pad_recopy_sha256": recopy["recopy"]["sha256"],
            "normalized_exact": True,
            "unknown_difference_count": 0,
            "decoded_launcher_sha256": EXPECTED_SHA["launcher"],
            "decoded_launcher_exact": True,
        },
        "pad": {
            "flow_name": args.flow_name,
            "paste_count": 1,
            "save_count": 1,
            "recopy_count": 1,
            "run_count": 1,
            "terminal": "RUNTIME_ERROR",
            "error_count": 1,
            "error_line": 32,
            "error_path": str(error_path),
            "helper_success_json": "NOT_OBSERVED",
            "value_type_match": "NOT_RUN",
        },
        "artifact": {
            "output_absent": True,
            "json_root_absent": True,
            "excel_process_count": 0,
            "work_sha256": sha256(WORK),
            "work_matches_template": True,
        },
        "comparison": {
            "target_12": "NOT_RUN_NO_OUTPUT",
            "outside_468": "NOT_RUN_NO_OUTPUT",
            "formulas": "NOT_RUN_NO_OUTPUT",
            "effective_format_rows_columns": "NOT_RUN_NO_OUTPUT",
            "f6": "NOT_RUN_NO_OUTPUT",
            "original_inputs_unchanged": True,
            "template_unchanged": True,
            "work_unchanged": True,
        },
        "preservation": {
            "fixed_files_unchanged": True,
            "additional_pad_run_count": 0,
            "run2_count": 0,
            "negative_run_count": 0,
            "copilot_send_count": 0,
            "github_write_count": 0,
        },
        "remaining": [
            "The fixed Robin does not reach helper execution because the a4-helper-json parent directory is absent at File.WriteText line 32.",
            "No saved output exists, so the 12 target, 468 outside, formula, effective-format, and F6 comparisons are not run.",
            "No retry, hand edit, builder edit, or additional PAD Run is authorized or performed.",
            "This stopped result is not generalized to the Copilot route or Issue #38 overall.",
        ],
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(TRIAL / "result.json", result)
    report = f"""# Issue #38 EX03 mechanical-builder LIVE1

## 判定

`{result['decision']}`。固定Robin `{EXPECTED_SHA['generated']}` は専用PADへの無修正貼付け・保存・再コピーを通過したが、正常系Run1はMain 32行目で停止した。再Runは行っていない。

## 実行前・再コピー

- Build.py --check: PASS / CHECK_BYTE_IDENTICAL
- PAD再コピー SHA-256: `{recopy['recopy']['sha256']}`
- 改行・末尾改行の正規化後は固定Robinと全文一致
- 未知差分0、命令欠落0、構文破損0
- 8 JSON保存、5数値書込み、2矩形readback、12比較、guard、成功gate、SaveAs、失敗分岐の再監査PASS
- 復号launcher SHA-256: `{EXPECTED_SHA['launcher']}`

## Run1停止

- PAD Run: 通算1回
- PAD表示: `{visible_error}`
- 場所: Main 32行目、最初の `source-1.json` File.WriteText
- `a4-helper-json` 親ディレクトリは停止後も不在
- helper成功JSON、保存出力、12比較はいずれも未到達
- `照合結果.xlsx` なし、JSON handoffなし、Excelプロセス0
- 入力2冊・template・workのSHAは不変

## 比較・境界

出力がないため、12対象セル、対象外468セル、数式、実効書式・行高・列幅、F6の比較はNOT_RUN。Run2、負例、Copilot送信、A5、ビルダー修正、全件回帰、追加Run、GitHub書込みは行っていない。本結果は機械ビルダー経路の停止証跡であり、Copilot生成経路やIssue #38全体の判定へ転用しない。
"""
    (TRIAL / "RESULT.md").write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


def validate_pad_records(run: dict, variables: dict, artifact: dict) -> None:
    for record in (run, variables, artifact):
        require(record["trial_id"] == TRIAL_ID and record["run_id"] == RUN_ID, "Run evidence identity mismatch")
    require(run["run_index"] == 1 and run["run_invocations_total"] == 1, "Run count mismatch")
    require(run["status"] == "PASS_TERMINAL_READY_SUCCESS_JSON_NO_DESIGNER_ERROR", "PAD Run did not pass")
    require(run["powershell"]["stdout_observed"] == EXPECTED_SUCCESS, "saved PowerShell observation mismatch")
    require(variables["probe_state"] == {"observed_value": EXPECTED_STATE, "match": True}, "saved ProbeState mismatch")
    require(variables["counts"] == {"true": 12, "false": 0, "total": 12}, "saved PAD comparison count mismatch")
    expected_names = {f"Position{index}ValueTypeMatch" for index in range(1, 13)}
    require(set(variables["value_type_matches"]) == expected_names, "saved PAD comparison variable set mismatch")
    require(all(item == {"observed_value": True, "match": True} for item in variables["value_type_matches"].values()), "one or more PAD comparisons are not true")
    require(artifact["status"] == "PASS_MECHANICAL_LIVE1_RUN1_ARTIFACT_AND_HANDOFF_PRESERVED", "artifact preservation did not pass")


def finalize() -> None:
    for path in (TRIAL / "result.json", TRIAL / "RESULT.md"):
        require(not path.exists(), f"refusing to overwrite final evidence: {path}")
    preflight = load(TRIAL / "preflight.json")
    recopy = load(TRIAL / "pad-recopy.json")
    pad_run = load(RUN / "pad-run.json")
    pad_variables = load(RUN / "pad-variables.json")
    artifact = load(RUN / "artifact.json")
    typed = load(RUN / "typed-transfer.json")
    legacy = load(RUN / "comparison.json")
    native = load(RUN / "native-styles.json")
    f6 = load(RUN / "f6-native.json")

    require(preflight["result"] == "PASS_READY_FOR_ONE_MECHANICAL_ROBIN_NORMAL_PAD_RUN", "preflight mismatch")
    require(recopy["result"] == "PASS_PAD_RECOPY_ONLY_KNOWN_SERIALIZATION_DIFFERENCES_RUN_ALLOWED", "re-copy mismatch")
    require(recopy["classification"]["unknown_content_difference_count"] == 0, "unknown re-copy difference")
    require(recopy["classification"]["decoded_launcher_exact"] is True, "decoded launcher not exact")
    validate_pad_records(pad_run, pad_variables, artifact)

    result_xlsx = RUN / "result.xlsx"
    result_sha = sha256(result_xlsx)
    require(artifact["output_sha256"] == result_sha, "artifact/result SHA mismatch")
    require(sha256(RUN / "work.xlsx") == EXPECTED_SHA["template"], "preserved work changed")

    shared = load_module("issue38_r11_shared_validator", ROOT / "tools/Finalize-Issue38Ex03R11FileAux.py")
    contract = shared.fixed_contract()
    typed_for_shared = copy.deepcopy(typed)
    typed_for_shared["run_label"] = "EX03-R11-FILE-AUX1-RUN1"
    shared.validate_typed_report(typed_for_shared, 1, result_xlsx, result_sha, contract)
    shared.validate_legacy_report(legacy, result_sha, contract)
    shared.validate_native_report(native, result_xlsx, result_sha, contract)
    shared.validate_f6_report(f6, result_xlsx, result_sha, contract)

    require(sha256(WORK) == sha256(TEMPLATE) == EXPECTED_SHA["template"], "runtime work/template changed")
    require(OUTPUT.is_file() and sha256(OUTPUT) == result_sha, "runtime output differs from preserved output")
    require(sha256(TRIAL / "work-before.xlsx") == EXPECTED_SHA["template"], "pre-run work copy changed")
    fixed_hashes()

    for item in preflight["protected_files"]:
        require(sha256(ROOT / item["path"]) == item["sha256"], f"protected file changed: {item['path']}")

    runtime_output = RUN / "runtime-output-after-run.xlsx"
    shutil.move(str(OUTPUT), str(runtime_output))
    require(sha256(runtime_output) == result_sha and not OUTPUT.exists(), "runtime output preservation failed")
    runtime_handoff = RUN / "runtime-handoff-after-run"
    runtime_handoff.mkdir()
    for name, expected_sha in artifact["handoff_sha256"].items():
        source = JSON_ROOT / name
        destination = runtime_handoff / name
        require(source.is_file(), f"runtime handoff missing: {name}")
        shutil.move(str(source), str(destination))
        require(sha256(destination) == expected_sha, f"runtime handoff preservation mismatch: {name}")
        require(sha256(RUN / "handoff" / name) == expected_sha, f"copied handoff changed: {name}")
    require(not any(JSON_ROOT.iterdir()), "unexpected runtime JSON remains")
    JSON_ROOT.rmdir()
    require(not JSON_ROOT.exists(), "runtime JSON root was not restored absent")
    require(sha256(WORK) == EXPECTED_SHA["template"], "runtime work changed after preservation")

    result = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "decision": "PASS_MECHANICAL_BUILDER_PATH_LIMITED_LIVE_PAD_RUN1",
        "scope": "Mechanical-builder path only; not Copilot generation acceptance and not Issue #38 overall acceptance.",
        "baseline_commit": BASELINE,
        "build_check": preflight["build_check"],
        "execution_identity": {
            "generated_robin_sha256": EXPECTED_SHA["generated"],
            "pad_recopy_sha256": recopy["recopy"]["sha256"],
            "normalized_exact": True,
            "unknown_difference_count": 0,
            "decoded_launcher_sha256": EXPECTED_SHA["launcher"],
            "decoded_launcher_exact": True,
        },
        "pad": {
            "flow_name": pad_run["flow_name"],
            "paste_count": 1,
            "save_count": 1,
            "recopy_count": 1,
            "run_count": 1,
            "terminal": pad_run["terminal_observation"],
            "powershell_stdout": EXPECTED_SUCCESS,
            "stderr_empty_directly_proven": False,
            "probe_state": EXPECTED_STATE,
            "value_type_match_true": 12,
            "value_type_match_false": 0,
        },
        "artifact": {
            "result_path": relative(result_xlsx),
            "result_sha256": result_sha,
            "result_bytes": result_xlsx.stat().st_size,
            "runtime_output_preserved_path": relative(runtime_output),
            "runtime_output_absent_after_preservation": not OUTPUT.exists(),
            "runtime_json_root_absent_after_preservation": not JSON_ROOT.exists(),
            "work_sha256": sha256(WORK),
            "work_matches_template": sha256(WORK) == sha256(TEMPLATE),
        },
        "comparison": {
            "target_cells": {"checked": 12, "mismatches": 0, "status": typed["status"]},
            "outside_cells": legacy["checks"]["outside_values_types_formulas"],
            "formulas": {"mismatches": 0, "status": "PASS"},
            "effective_format": {
                "checked_cells": native["bounds"]["checked_cells"],
                "checked_rows": native["bounds"]["checked_rows"],
                "checked_columns": native["bounds"]["checked_columns"],
                "difference_attribute_counts": native["difference_attribute_counts"],
                "status": native["status"],
            },
            "f6": {
                "value": f6["saved_f6"]["value2"],
                "dotnet_type": f6["saved_f6"]["value2_dotnet_type"],
                "number_format": f6["saved_f6"]["number_format_invariant"],
                "prefix": f6["saved_f6"]["prefix_character"],
                "has_formula": f6["saved_f6"]["has_formula"],
                "status": f6["status"],
            },
            "legacy_raw_diagnostic": {
                "status": "FAIL_PRESERVED_NOT_USED_AS_EFFECTIVE_FORMAT_GATE",
                "failure_counts": legacy["failure_counts"],
                "total": sum(legacy["failure_counts"].values()),
            },
            "original_inputs_unchanged": True,
            "template_unchanged": True,
            "work_unchanged": True,
        },
        "preservation": {
            "fixed_files_unchanged": True,
            "copilot_send_count": 0,
            "run2_count": 0,
            "negative_run_count": 0,
            "github_write_count": 0,
        },
        "remaining": [
            "No separate stderr PAD variable exists, so empty stderr is not directly claimed.",
            "This result does not validate Copilot generation of the Robin.",
            "This result is not generalized beyond the fixed EX03 text/number case or to Issue #38 overall acceptance.",
        ],
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(TRIAL / "result.json", result)
    report = f"""# Issue #38 EX03 mechanical-builder LIVE1

## 判定

`{result['decision']}`。固定Robin `{EXPECTED_SHA['generated']}` を専用PADへ無修正で1回貼付け、保存・再コピーの既知シリアライズ差だけを確認してから、正常系1Runだけを実施した。

## 実行・照合

- Build.py --check: PASS / CHECK_BYTE_IDENTICAL
- PAD再コピー: 未知差分0、欠落0、構文破損0、復号launcher `{EXPECTED_SHA['launcher']}`
- PAD: READY、Designerエラーなし、固定helper成功JSON一致、ProbeState `{EXPECTED_STATE}`、12/12 ValueTypeMatch true
- result SHA-256: `{result_sha}`
- 対象12セル: 値・型・位置 mismatch 0
- 対象外468セル: 値・型・数式 mismatch 0
- Excel実効書式: 480セル、48行、30列、差分0
- F6: `100%` / `System.String` / 元書式 / prefix空 / 数式なし
- 原本入力・template・workは不変
- 旧raw 558差分は診断記録として保持し、実効書式PASSへの読み替えや隠蔽をしていない

## 境界

Run2、負例、Copilot送信、A5、ビルダー修正、全件回帰、GitHub書込みは行っていない。別stderr変数がないためstderr空は直接主張しない。本結果は機械ビルダー経路の固定EX03限定で、Copilot生成経路やIssue #38全体のPASSには転用しない。
"""
    (TRIAL / "RESULT.md").write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="phase", required=True)
    sub.add_parser("prepare")
    recopy = sub.add_parser("capture-recopy")
    recopy.add_argument("--flow-window-id", type=int, required=True)
    recopy.add_argument("--flow-name", required=True)
    run = sub.add_parser("capture-run")
    run.add_argument("--flow-window-id", type=int, required=True)
    run.add_argument("--flow-name", required=True)
    run.add_argument("--started-utc", required=True)
    run.add_argument("--terminal-observed-utc", required=True)
    run.add_argument("--variables-observed-utc", required=True)
    run.add_argument("--powershell-output", required=True)
    run.add_argument("--probe-state", required=True)
    run.add_argument("--value-type-true-count", type=int, required=True)
    stop = sub.add_parser("record-stop")
    stop.add_argument("--flow-window-id", type=int, required=True)
    stop.add_argument("--flow-name", required=True)
    stop.add_argument("--started-utc", required=True)
    stop.add_argument("--terminal-observed-utc", required=True)
    sub.add_parser("finalize")
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare()
    elif args.phase == "capture-recopy":
        capture_recopy(args.flow_window_id, args.flow_name)
    elif args.phase == "capture-run":
        capture_run(args)
    elif args.phase == "record-stop":
        record_stop(args)
    else:
        finalize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
