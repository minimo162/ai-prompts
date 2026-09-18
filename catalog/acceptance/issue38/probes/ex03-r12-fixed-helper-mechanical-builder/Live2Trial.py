#!/usr/bin/env python3
"""Record the authorized LIVE2 one-Run trial with json_root preplacement."""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
BASELINE = "dc927db9acce13f8c51cfee81b85622bd22852e2"
TRIAL_ID = "EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE2"
RUN_ID = f"{TRIAL_ID}-RUN1"
TRIAL = PROBE / "trials" / TRIAL_ID
RUN = TRIAL / "run1"
LIVE1 = PROBE / "trials/EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE1"
LIVE1_RECOPY = LIVE1 / "pad-recopy-before-run.robin"
LIVE1_RECOPY_SHA = "570b26c57abeca0e9b8e19368c6542a529b44994bac518f2e70cb69baec52c0f"


def load_module(name: str, path: Path):
    spec = __import__("importlib.util").util.spec_from_file_location(name, path)
    module = __import__("importlib.util").util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


base = load_module("issue38_mechanical_live1_recorder", PROBE / "LiveTrial.py")

RUNTIME = base.RUNTIME
WORK = base.WORK
OUTPUT = base.OUTPUT
JSON_ROOT = base.JSON_ROOT
TEMPLATE = base.TEMPLATE
INPUT_A = base.INPUT_A
INPUT_B = base.INPUT_B
WIRING = base.WIRING
INVOCATION = base.INVOCATION
LAUNCHER = base.LAUNCHER
GENERATED = base.GENERATED
README = PROBE / "README.md"
EXPECTED_SUCCESS = base.EXPECTED_SUCCESS
EXPECTED_STATE = base.EXPECTED_STATE
EXPECTED_WORK_SHA = base.EXPECTED_SHA["template"]
README_MARKER = "### Live PAD preplacement: A4 json_root"


def sha256(path: Path) -> str:
    return base.sha256(path)


def load(path: Path) -> dict:
    return base.load(path)


def write_json(path: Path, value: object) -> None:
    base.write_json(path, value)


def relative(path: Path) -> str:
    return base.relative(path)


def require(condition: bool, message: str) -> None:
    base.require(condition, message)


def fixed_hashes() -> dict[str, str]:
    return base.fixed_hashes()


def excel_running() -> bool:
    return base.excel_running()


def git_blob(path: Path) -> str:
    item = relative(path)
    return subprocess.check_output(
        ["git", "hash-object", f"--path={item}", str(path)],
        cwd=ROOT,
        text=True,
    ).strip()


def live1_protected() -> list[dict[str, str]]:
    result = []
    for path in sorted(item for item in LIVE1.rglob("*") if item.is_file()):
        item = relative(path)
        baseline_blob = subprocess.check_output(
            ["git", "rev-parse", f"{BASELINE}:{item}"], cwd=ROOT, text=True
        ).strip()
        current_blob = git_blob(path)
        require(current_blob == baseline_blob, f"LIVE1 evidence changed: {item}")
        result.append({"path": item, "git_blob": baseline_blob, "sha256": sha256(path)})
    return result


def verify_json_contract(invocation: dict, wiring: dict) -> tuple[Path, list[Path]]:
    invocation_root = Path(invocation["json_root"])
    wiring_root = Path(wiring["runtime"]["a4_json_root_absolute"])
    require(invocation_root == wiring_root, "invocation and WIRING json_root differ")
    require(invocation_root.is_absolute(), "json_root is not absolute")
    expected_root = RUNTIME / "a4-helper-json"
    require(invocation_root == expected_root, "json_root is not the fixed synthetic runtime path")
    require(
        os.path.commonpath((str(invocation_root), str(RUNTIME))) == str(RUNTIME),
        "json_root is outside the synthetic runtime area",
    )
    require(invocation_root.parent.resolve() == RUNTIME.resolve(), "json_root parent changed")

    source_paths = [Path(item["source_json_path"]) for item in wiring["text_mappings"]]
    mode_path = wiring_root / wiring["runtime"]["mode_json_file"]
    all_paths = source_paths + [mode_path]
    require(len(all_paths) == 8 and len(set(all_paths)) == 8, "JSON destination count/uniqueness mismatch")
    require(all(path.parent == wiring_root for path in all_paths), "one or more JSON parents differ from json_root")
    require(
        [path.name for path in source_paths] == [f"source-{index}.json" for index in range(1, 8)],
        "source JSON filename sequence changed",
    )
    require(mode_path.name == "mode.json", "mode JSON filename changed")
    return wiring_root, all_paths


def prepare() -> None:
    require(not TRIAL.exists(), f"refusing to overwrite LIVE2 trial: {TRIAL}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    require(head == BASELINE, f"HEAD is not the authorized baseline: {head}")
    require(subprocess.run(["git", "diff", "--quiet"], cwd=ROOT).returncode == 0, "tracked worktree changes exist")
    require(subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0, "staged changes exist")

    fixed = fixed_hashes()
    require(sha256(LIVE1_RECOPY) == LIVE1_RECOPY_SHA, "LIVE1 saved-flow baseline changed")
    protected_live1 = live1_protected()
    invocation = load(INVOCATION)
    wiring = load(WIRING)
    json_root, json_paths = verify_json_contract(invocation, wiring)
    require(Path(invocation["target_workbook"]) == WORK, "invocation target workbook changed")
    require(Path(wiring["runtime"]["fixed_work_absolute"]) == WORK, "WIRING work path changed")
    require(Path(wiring["runtime"]["fixed_output_absolute"]) == OUTPUT, "WIRING output path changed")
    require(wiring["runtime"]["verifier_preplaces"][-1] == "A4 json_root directory", "WIRING preplacement contract changed")
    require(sha256(WORK) == sha256(TEMPLATE) == EXPECTED_WORK_SHA, "work/template mismatch before preplacement")
    require(not OUTPUT.exists(), "output exists before LIVE2")
    require(not JSON_ROOT.exists(), "json_root already exists before the authorized preplacement")
    require(not excel_running(), "Excel is running before LIVE2 preplacement")

    TRIAL.mkdir(parents=True)
    shutil.copy2(WORK, TRIAL / "work-before.xlsx")
    write_json(
        TRIAL / "plan.json",
        {
            "schema_version": 1,
            "trial_id": TRIAL_ID,
            "baseline_commit": BASELINE,
            "classification": "MECHANICAL_BUILDER_PATH_LIVE2_ONE_NORMAL_RUN_ONLY",
            "source_saved_flow": {
                "trial": "EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE1",
                "recopy_sha256": LIVE1_RECOPY_SHA,
                "repaste_allowed": False,
                "resave_allowed": False,
            },
            "authorization": {
                "create_fixed_json_root": 1,
                "write_probe_create_delete": 1,
                "saved_flow_identity_recopy": 1,
                "normal_pad_runs": 1,
                "additional_runs": 0,
                "run2": 0,
                "copilot_sends": 0,
                "candidate_creation": 0,
                "builder_or_fixed_code_modification": 0,
                "github_writes": 0,
            },
            "successful_generation_checks_repeated": False,
            "full_regression_repeated": False,
        },
    )

    json_root.mkdir()
    require(json_root.is_dir(), "authorized json_root creation failed")
    probe_name = f".live2-write-probe-{uuid.uuid4().hex}.tmp"
    probe_path = json_root / probe_name
    probe_value = uuid.uuid4().hex
    with probe_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(probe_value)
    require(probe_path.read_text(encoding="utf-8") == probe_value, "json_root write probe readback failed")
    probe_sha = sha256(probe_path)
    probe_path.unlink()
    require(not probe_path.exists(), "json_root write probe cleanup failed")
    require(not any(json_root.iterdir()), "json_root is not empty after write probe cleanup")
    require(os.access(json_root, os.W_OK), "json_root is not writable")

    preflight = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "result": "PASS_READY_FOR_SAVED_FLOW_IDENTITY_AND_ONE_NORMAL_RUN",
        "baseline_commit": BASELINE,
        "fixed_sha256": fixed,
        "builder_sha256": sha256(PROBE / "Build.py"),
        "json_contract": {
            "invocation_path": relative(INVOCATION),
            "wiring_path": relative(WIRING),
            "invocation_json_root": str(Path(invocation["json_root"])),
            "wiring_json_root": str(Path(wiring["runtime"]["a4_json_root_absolute"])),
            "roots_exact": True,
            "inside_synthetic_runtime": True,
            "destination_count": 8,
            "destinations": [str(path) for path in json_paths],
            "all_parent_directories_exact_json_root": True,
        },
        "preplacement": {
            "created_directory": str(json_root),
            "created_directory_was_absent": True,
            "existing_file_deleted": False,
            "permission_changed": False,
            "write_probe_name": probe_name,
            "write_probe_sha256": probe_sha,
            "write_probe_readback_exact": True,
            "write_probe_removed": True,
            "directory_empty_after_probe": True,
            "directory_writable": True,
        },
        "pre_run": {
            "work_sha256": sha256(WORK),
            "template_sha256": sha256(TEMPLATE),
            "work_matches_template": True,
            "work_before_path": relative(TRIAL / "work-before.xlsx"),
            "output_absent": True,
            "excel_not_running": True,
        },
        "live1_protected": protected_live1,
        "non_repetition": {
            "Build.py_check": "NOT_REPEATED; fixed committed SHA verified directly",
            "focused_builder_tests": "NOT_REPEATED",
            "full_regression": "NOT_REPEATED",
        },
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(TRIAL / "preflight.json", preflight)
    print(json.dumps({"trial_id": TRIAL_ID, "status": preflight["result"], "json_root": str(json_root), "destinations": 8}, ensure_ascii=False))


def capture_identity(flow_window_id: int, flow_name: str) -> None:
    preflight = load(TRIAL / "preflight.json")
    require(preflight["result"] == "PASS_READY_FOR_SAVED_FLOW_IDENTITY_AND_ONE_NORMAL_RUN", "preflight did not pass")
    require(JSON_ROOT.is_dir() and not any(JSON_ROOT.iterdir()), "json_root is not empty before identity capture")
    require(not OUTPUT.exists(), "output exists before identity capture")
    require(sha256(WORK) == EXPECTED_WORK_SHA, "work changed before identity capture")
    require(not excel_running(), "Excel is running before identity capture")
    recopy_path = TRIAL / "saved-flow-recopy-before-run.robin"
    require(not recopy_path.exists() and not (TRIAL / "saved-flow-identity.json").exists(), "identity evidence exists")
    value = base.clipboard_text()
    recopy_path.write_text(value, encoding="utf-8", newline="")
    require(recopy_path.read_bytes() == LIVE1_RECOPY.read_bytes(), "saved flow differs from LIVE1 exact re-copy")
    require(sha256(recopy_path) == LIVE1_RECOPY_SHA, "saved-flow re-copy SHA mismatch")
    record = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "flow": {"name": flow_name, "window_id": flow_window_id, "subflow": "Main", "power_fx": "OFF"},
        "source_baseline": relative(LIVE1_RECOPY),
        "source_baseline_sha256": LIVE1_RECOPY_SHA,
        "captured_path": relative(recopy_path),
        "captured_sha256": sha256(recopy_path),
        "byte_exact_to_live1_saved_flow": True,
        "repaste_count": 0,
        "resave_count": 0,
        "identity_recopy_count": 1,
        "pad_run_count": 0,
        "result": "PASS_CURRENT_SAVED_FLOW_BYTE_EXACT_TO_LIVE1_BASELINE",
    }
    write_json(TRIAL / "saved-flow-identity.json", record)
    print(json.dumps({"status": record["result"], "sha256": record["captured_sha256"]}, ensure_ascii=False))


def capture_run(args: argparse.Namespace) -> None:
    require(not RUN.exists(), f"refusing to overwrite Run evidence: {RUN}")
    preflight = load(TRIAL / "preflight.json")
    identity = load(TRIAL / "saved-flow-identity.json")
    require(preflight["result"] == "PASS_READY_FOR_SAVED_FLOW_IDENTITY_AND_ONE_NORMAL_RUN", "preflight mismatch")
    require(identity["result"] == "PASS_CURRENT_SAVED_FLOW_BYTE_EXACT_TO_LIVE1_BASELINE", "saved-flow identity mismatch")
    require(args.powershell_output == EXPECTED_SUCCESS, "PowerShell success JSON mismatch")
    require(args.probe_state == EXPECTED_STATE, "ProbeState mismatch")
    require(args.value_type_true_count == 12, "PAD did not expose 12 true comparisons")
    require(sha256(WORK) == EXPECTED_WORK_SHA, "work changed during Run")
    require(OUTPUT.is_file(), "Run output is absent")
    require(JSON_ROOT.is_dir(), "json_root is absent after Run")

    handoff_paths = [JSON_ROOT / f"source-{index}.json" for index in range(1, 8)] + [JSON_ROOT / "mode.json"]
    require(all(path.is_file() for path in handoff_paths), "one or more JSON handoff files are absent")
    require(sorted(path.name for path in JSON_ROOT.iterdir()) == sorted(path.name for path in handoff_paths), "unexpected json_root entry")
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
    require(sha256(RUN / "result.xlsx") == output_sha, "preserved output differs")
    require(sha256(RUN / "work.xlsx") == EXPECTED_WORK_SHA, "preserved work differs")
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
            "method": "PAD Variables pane after the same Run: PowershellOutput was opened and canceled without edits; the ProbeState filter and fixed assignment action showed the success-gate value; Position ValueTypeMatch search showed 12 results, all true.",
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
            "work_sha256": EXPECTED_WORK_SHA,
            "preserved_work_exact": True,
            "handoff_directory": relative(RUN / "handoff"),
            "handoff_sha256": {path.name: sha256(RUN / "handoff" / path.name) for path in handoff_paths},
            "status": "PASS_LIVE2_RUN1_ARTIFACT_AND_HANDOFF_PRESERVED",
        },
    )
    print(json.dumps({"status": "PASS_LIVE2_RUN1_PRESERVED", "output_sha256": output_sha, "handoff_files": 8}, ensure_ascii=False))


def validate_pad_records(run: dict, variables: dict, artifact: dict) -> None:
    for record in (run, variables, artifact):
        require(record["trial_id"] == TRIAL_ID and record["run_id"] == RUN_ID, "Run evidence identity mismatch")
    require(run["run_index"] == 1 and run["run_invocations_total"] == 1, "Run count mismatch")
    require(run["status"] == "PASS_TERMINAL_READY_SUCCESS_JSON_NO_DESIGNER_ERROR", "PAD Run status mismatch")
    require(run["powershell"]["stdout_observed"] == EXPECTED_SUCCESS, "PowerShell observation mismatch")
    require(variables["probe_state"] == {"observed_value": EXPECTED_STATE, "match": True}, "ProbeState observation mismatch")
    require(variables["counts"] == {"true": 12, "false": 0, "total": 12}, "PAD comparison count mismatch")
    names = {f"Position{index}ValueTypeMatch" for index in range(1, 13)}
    require(set(variables["value_type_matches"]) == names, "PAD comparison variable set mismatch")
    require(all(item == {"observed_value": True, "match": True} for item in variables["value_type_matches"].values()), "one or more PAD comparisons are false")
    require(artifact["status"] == "PASS_LIVE2_RUN1_ARTIFACT_AND_HANDOFF_PRESERVED", "artifact status mismatch")


def finalize() -> None:
    for path in (TRIAL / "result.json", TRIAL / "RESULT.md"):
        require(not path.exists(), f"refusing to overwrite final evidence: {path}")
    preflight = load(TRIAL / "preflight.json")
    identity = load(TRIAL / "saved-flow-identity.json")
    pad_run = load(RUN / "pad-run.json")
    pad_variables = load(RUN / "pad-variables.json")
    artifact = load(RUN / "artifact.json")
    typed = load(RUN / "typed-transfer.json")
    legacy = load(RUN / "comparison.json")
    native = load(RUN / "native-styles.json")
    f6 = load(RUN / "f6-native.json")

    require(preflight["result"] == "PASS_READY_FOR_SAVED_FLOW_IDENTITY_AND_ONE_NORMAL_RUN", "preflight mismatch")
    require(identity["result"] == "PASS_CURRENT_SAVED_FLOW_BYTE_EXACT_TO_LIVE1_BASELINE", "identity mismatch")
    require(identity["byte_exact_to_live1_saved_flow"] is True, "saved flow is not LIVE1 exact")
    validate_pad_records(pad_run, pad_variables, artifact)
    result_xlsx = RUN / "result.xlsx"
    result_sha = sha256(result_xlsx)
    require(artifact["output_sha256"] == result_sha, "artifact/result SHA mismatch")

    shared = load_module("issue38_r11_live2_validator", ROOT / "tools/Finalize-Issue38Ex03R11FileAux.py")
    contract = shared.fixed_contract()
    typed_for_shared = copy.deepcopy(typed)
    typed_for_shared["run_label"] = "EX03-R11-FILE-AUX1-RUN1"
    shared.validate_typed_report(typed_for_shared, 1, result_xlsx, result_sha, contract)
    shared.validate_legacy_report(legacy, result_sha, contract)
    shared.validate_native_report(native, result_xlsx, result_sha, contract)
    shared.validate_f6_report(f6, result_xlsx, result_sha, contract)

    require(README_MARKER in README.read_text(encoding="utf-8"), "README preplacement section is absent")
    require(sha256(WORK) == sha256(TEMPLATE) == EXPECTED_WORK_SHA, "work/template changed")
    require(OUTPUT.is_file() and sha256(OUTPUT) == result_sha, "runtime output changed")
    require(sha256(TRIAL / "work-before.xlsx") == EXPECTED_WORK_SHA, "pre-run work copy changed")
    fixed_hashes()
    for item in preflight["live1_protected"]:
        path = ROOT / item["path"]
        require(git_blob(path) == item["git_blob"] and sha256(path) == item["sha256"], f"LIVE1 evidence changed: {item['path']}")

    runtime_output = RUN / "runtime-output-after-run.xlsx"
    shutil.move(str(OUTPUT), str(runtime_output))
    require(not OUTPUT.exists() and sha256(runtime_output) == result_sha, "runtime output preservation failed")
    runtime_handoff = RUN / "runtime-handoff-after-run"
    runtime_handoff.mkdir()
    for name, expected_sha in artifact["handoff_sha256"].items():
        source = JSON_ROOT / name
        destination = runtime_handoff / name
        require(source.is_file(), f"runtime handoff missing: {name}")
        shutil.move(str(source), str(destination))
        require(sha256(destination) == expected_sha, f"runtime handoff preservation mismatch: {name}")
        require(sha256(RUN / "handoff" / name) == expected_sha, f"copied handoff changed: {name}")
    require(JSON_ROOT.is_dir() and not any(JSON_ROOT.iterdir()), "json_root is not preserved empty")
    require(sha256(WORK) == EXPECTED_WORK_SHA, "work changed after preservation")

    result = {
        "schema_version": 1,
        "trial_id": TRIAL_ID,
        "decision": "PASS_MECHANICAL_BUILDER_PATH_LIVE2_NORMAL_RUN1",
        "scope": "This one fixed mechanical-builder-path Run only; not Copilot generation or Issue #38 overall acceptance.",
        "baseline_commit": BASELINE,
        "preplacement": {
            "json_root": str(JSON_ROOT),
            "invocation_wiring_exact": True,
            "inside_synthetic_runtime": True,
            "eight_destination_parents_ready": True,
            "write_probe_readback_and_cleanup": True,
            "existing_file_deleted": False,
            "permission_changed": False,
        },
        "execution_identity": {
            "generated_robin_sha256": base.EXPECTED_SHA["generated"],
            "saved_flow_recopy_sha256": identity["captured_sha256"],
            "byte_exact_to_live1_saved_flow": True,
            "repaste_count": 0,
            "resave_count": 0,
        },
        "pad": {
            "flow_name": pad_run["flow_name"],
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
            "json_root_preserved_empty": JSON_ROOT.is_dir() and not any(JSON_ROOT.iterdir()),
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
            "live1_stop_evidence_unchanged": True,
            "fixed_helper_invocation_launcher_builder_robin_unchanged": True,
            "additional_pad_run_count": 0,
            "run2_count": 0,
            "copilot_send_count": 0,
            "github_write_count": 0,
        },
        "remaining": [
            "The saved Robin has no separate stderr PAD variable; empty stderr is not directly claimed.",
            "This PASS is limited to this fixed mechanical-builder-path LIVE2 Run1.",
            "Copilot generation and Issue #38 overall acceptance are not established by this trial.",
        ],
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(TRIAL / "result.json", result)
    report = f"""# Issue #38 EX03 mechanical-builder LIVE2

## 判定

`{result['decision']}`。LIVE1のSTOP証跡を変更せず、固定invocationとWIRINGが一致する合成検証用`json_root`を事前配置し、保存済み専用フローを再貼付け・再保存せず正常系1Runだけ実行した。

## 事前配置・実行同一性

- json_root: `{JSON_ROOT}`
- invocation/WIRING一致、8保存先の親一致、合成検証用領域内
- 一時書込み・読戻し・削除PASS、既存ファイル削除0、権限変更0
- 保存済みフロー再コピー SHA-256 `{identity['captured_sha256']}`、LIVE1再コピーとbyte一致
- 再貼付け0、再保存0、Run 1

## PAD・成果物

- READY、Designerエラーなし
- `PowershellOutput`: `{EXPECTED_SUCCESS}`
- `ProbeState`: `{EXPECTED_STATE}`
- `Position1ValueTypeMatch`〜`Position12ValueTypeMatch`: 12 true / 0 false
- result SHA-256 `{result_sha}`
- 12対象セル: 値・型・位置 mismatch 0
- 対象外468セル: 値・型・数式 mismatch 0
- Excel実効書式: 480セル、48行、30列、差分0
- F6: `100%` / `System.String` / 元書式 / prefix空 / 数式なし
- 入力2冊・template・work不変
- 旧raw 558差分は診断記録として保持

## 境界

成功済み生成検査・全件回帰、Copilot送信、Run2、候補版作成、追加Run、GitHub書込みは行っていない。本PASSは機械ビルダー経路の今回1Runだけに限定し、Copilot生成経路やIssue #38全体へ転用しない。
"""
    (TRIAL / "RESULT.md").write_text(report, encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="phase", required=True)
    sub.add_parser("prepare")
    identity = sub.add_parser("capture-identity")
    identity.add_argument("--flow-window-id", type=int, required=True)
    identity.add_argument("--flow-name", required=True)
    run = sub.add_parser("capture-run")
    run.add_argument("--flow-window-id", type=int, required=True)
    run.add_argument("--flow-name", required=True)
    run.add_argument("--started-utc", required=True)
    run.add_argument("--terminal-observed-utc", required=True)
    run.add_argument("--variables-observed-utc", required=True)
    run.add_argument("--powershell-output", required=True)
    run.add_argument("--probe-state", required=True)
    run.add_argument("--value-type-true-count", type=int, required=True)
    sub.add_parser("finalize")
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare()
    elif args.phase == "capture-identity":
        capture_identity(args.flow_window_id, args.flow_name)
    elif args.phase == "capture-run":
        capture_run(args)
    else:
        finalize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
