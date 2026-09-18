#!/usr/bin/env python3
"""Record a fresh normal Run and a gated existing-output Run for the fixed mechanical Robin."""

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
BASELINE = "f38a69d91583a9a75f38cf499a2b5bbfeee2dff5"
CAMPAIGN_ID = "EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE3"
NORMAL_ID = f"{CAMPAIGN_ID}-NORMAL1"
GUARD_ID = f"{CAMPAIGN_ID}-OUTPUT-GUARD1"
NORMAL_RUN_ID = f"{NORMAL_ID}-RUN1"
GUARD_RUN_ID = f"{GUARD_ID}-RUN1"
CAMPAIGN = PROBE / "trials" / CAMPAIGN_ID
NORMAL = CAMPAIGN / "normal"
NORMAL_RUN = NORMAL / "run1"
GUARD = CAMPAIGN / "existing-output-guard"
LIVE2 = PROBE / "trials/EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE2"
LIVE2_RUN = LIVE2 / "run1"
LIVE2_RECOPY = LIVE2 / "saved-flow-recopy-before-run.robin"
LIVE2_RECOPY_SHA = "570b26c57abeca0e9b8e19368c6542a529b44994bac518f2e70cb69baec52c0f"
FLOW_NAME = "無題 (3)"
EXPECTED_GUARD_STATE = "OUTPUT_EXISTS_NO_RUN"
README_MARKER = "### Live PAD preplacement: A4 json_root"
HANDOFF_NAMES = [f"source-{index}.json" for index in range(1, 8)] + ["mode.json"]


def load_module(name: str, path: Path):
    spec = __import__("importlib.util").util.spec_from_file_location(name, path)
    module = __import__("importlib.util").util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


live2 = load_module("issue38_mechanical_live2_recorder_for_live3", PROBE / "Live2Trial.py")
base = live2.base

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


def excel_running() -> bool:
    return base.excel_running()


def git_blob(path: Path) -> str:
    item = relative(path)
    return subprocess.check_output(
        ["git", "hash-object", f"--path={item}", str(path)], cwd=ROOT, text=True
    ).strip()


def protect_tree(path: Path) -> list[dict[str, str]]:
    records = []
    for item_path in sorted(item for item in path.rglob("*") if item.is_file()):
        item = relative(item_path)
        baseline_blob = subprocess.check_output(
            ["git", "rev-parse", f"{BASELINE}:{item}"], cwd=ROOT, text=True
        ).strip()
        current_blob = git_blob(item_path)
        require(current_blob == baseline_blob, f"protected evidence changed: {item}")
        records.append({"path": item, "git_blob": baseline_blob, "sha256": sha256(item_path)})
    require(records, f"protected evidence tree is empty: {path}")
    return records


def fixed_hashes() -> dict[str, str]:
    hashes = base.fixed_hashes()
    require(sha256(PROBE / "Build.py") == "dc6363953d120acf9623e1c28e777b1496c3da9c392704ae4a5c79b3808dea62", "builder changed")
    require(sha256(GENERATED) == base.EXPECTED_SHA["generated"], "generated Robin changed")
    require(sha256(LIVE2_RECOPY) == LIVE2_RECOPY_SHA, "LIVE2 saved-flow baseline changed")
    return hashes


def handoff_paths() -> list[Path]:
    return [JSON_ROOT / name for name in HANDOFF_NAMES]


def file_record(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "path": relative(path),
        "sha256": sha256(path),
        "bytes": stat.st_size,
        "last_write_ns": stat.st_mtime_ns,
    }


def snapshot(paths: list[Path]) -> dict[str, dict[str, object]]:
    return {relative(path): file_record(path) for path in paths}


def require_same_snapshot(before: dict, after: dict, label: str) -> None:
    require(set(before) == set(after), f"{label} path set changed")
    for path in before:
        require(before[path] == after[path], f"{label} changed: {path}")


def require_runtime_inventory(output_allowed: bool) -> list[str]:
    require(RUNTIME.is_dir(), "fixed runtime directory is absent")
    names = sorted(item.name for item in RUNTIME.iterdir())
    allowed = {"work.xlsx", "preparation.json", "a4-helper-json"}
    if output_allowed:
        allowed.add(OUTPUT.name)
    unknown = sorted(set(names) - allowed)
    require(not unknown, f"unknown runtime entries: {unknown}")
    return names


def verify_json_contract() -> list[Path]:
    invocation = load(INVOCATION)
    wiring = load(WIRING)
    json_root, destinations = live2.verify_json_contract(invocation, wiring)
    require(json_root == JSON_ROOT, "json_root changed")
    require(Path(invocation["target_workbook"]) == WORK, "invocation target workbook changed")
    require(Path(wiring["runtime"]["fixed_work_absolute"]) == WORK, "WIRING work path changed")
    require(Path(wiring["runtime"]["fixed_output_absolute"]) == OUTPUT, "WIRING output path changed")
    require(wiring["runtime"]["verifier_preplaces"][-1] == "A4 json_root directory", "README/WIRING preplacement contract changed")
    return destinations


def static_guard_contract() -> dict[str, object]:
    lines = GENERATED.read_text(encoding="utf-8").splitlines()
    require(len(lines) == 195, "Robin line count changed")
    require(lines[0] == "SET ProbeState TO $'''NOT_STARTED'''", "ProbeState initialization changed")
    require(lines[1] == "SET ScriptGatePassed TO False", "ScriptGatePassed reset changed")
    require(lines[2] == "SET NumericWriteEntered TO False", "NumericWriteEntered reset changed")
    require(lines[3] == "SET SaveAsEntered TO False", "SaveAsEntered reset changed")
    require(lines[4].startswith("IF (File.IfFile.Exists File: "), "output guard IF changed")
    require(lines[5].strip() == "SET ProbeState TO $'''OUTPUT_EXISTS_NO_RUN'''", "output guard state changed")
    require(lines[6].strip() == "ELSE", "output guard ELSE changed")
    require(lines[-1] == "END", "outer output guard END changed")
    require(sum("OUTPUT_EXISTS_NO_RUN" in line for line in lines) == 1, "output guard state is not unique")

    sensitive = {
        "json_write": "File.WriteText File:",
        "helper": "Scripting.RunPowershellScript.RunScript",
        "numeric_write": "Excel.WriteToExcel.WriteCell",
        "save_as": "Excel.SaveExcel.SaveAs",
    }
    expected_counts = {"json_write": 8, "helper": 1, "numeric_write": 5, "save_as": 1}
    locations: dict[str, list[int]] = {}
    for name, token in sensitive.items():
        indexes = [index + 1 for index, line in enumerate(lines) if token in line]
        require(len(indexes) == expected_counts[name], f"{name} count changed")
        require(all(index > 7 and index < len(lines) for index in indexes), f"{name} escaped guard ELSE")
        require(all(lines[index - 1].startswith("    ") for index in indexes), f"{name} indentation escaped guard ELSE")
        locations[name] = indexes
    return {
        "robin_path": relative(GENERATED),
        "robin_sha256": sha256(GENERATED),
        "line_count": len(lines),
        "guard_if_line": 5,
        "guard_state_line": 6,
        "else_line": 7,
        "outer_end_line": len(lines),
        "guard_state": EXPECTED_GUARD_STATE,
        "guard_state_unique": True,
        "sensitive_action_lines": locations,
        "all_sensitive_actions_in_mutually_exclusive_else": True,
    }


def prepare() -> None:
    require(not CAMPAIGN.exists(), f"refusing to overwrite campaign: {CAMPAIGN}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    require(head == BASELINE, f"HEAD is not the authorized baseline: {head}")
    require(subprocess.run(["git", "diff", "--quiet"], cwd=ROOT).returncode == 0, "tracked worktree changes exist")
    require(subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0, "staged changes exist")
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).splitlines()
    allowed_untracked = f"?? {relative(Path(__file__))}"
    require(all(line == allowed_untracked for line in status), f"unexpected worktree entries before prepare: {status}")

    fixed = fixed_hashes()
    protected_live2 = protect_tree(LIVE2)
    destinations = verify_json_contract()
    require(README_MARKER in README.read_text(encoding="utf-8"), "README preplacement contract missing")
    require(sha256(WORK) == sha256(TEMPLATE) == EXPECTED_WORK_SHA, "work/template mismatch")
    require(sha256(INPUT_A) == base.EXPECTED_SHA["input_a"], "input A changed")
    require(sha256(INPUT_B) == base.EXPECTED_SHA["input_b"], "input B changed")
    require(JSON_ROOT.is_dir(), "preplaced json_root is absent")
    require(not any(JSON_ROOT.iterdir()), "json_root contains an existing file before normal Run")
    require_runtime_inventory(output_allowed=True)
    require(not excel_running(), "Excel is running before preflight")

    CAMPAIGN.mkdir(parents=True)
    NORMAL.mkdir()
    GUARD.mkdir()
    retired = None
    if OUTPUT.exists():
        live2_sha = load(LIVE2_RUN / "artifact.json")["output_sha256"]
        require(sha256(OUTPUT) == live2_sha, "existing runtime output is not the known LIVE2 artifact")
        retired_path = CAMPAIGN / "preflight-retired-known-live2-output.xlsx"
        shutil.move(str(OUTPUT), str(retired_path))
        retired = file_record(retired_path)
    require(not OUTPUT.exists(), "runtime output still exists before normal Run")

    probe_name = f".live3-write-probe-{uuid.uuid4().hex}.tmp"
    probe_path = JSON_ROOT / probe_name
    probe_value = uuid.uuid4().hex
    with probe_path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(probe_value)
    require(probe_path.read_text(encoding="utf-8") == probe_value, "json_root write probe readback failed")
    probe_sha = sha256(probe_path)
    probe_path.unlink()
    require(not probe_path.exists() and not any(JSON_ROOT.iterdir()), "write probe cleanup failed")
    require(os.access(JSON_ROOT, os.W_OK), "json_root is not writable")

    shutil.copy2(WORK, NORMAL / "work-before.xlsx")
    write_json(
        CAMPAIGN / "plan.json",
        {
            "schema_version": 1,
            "campaign_id": CAMPAIGN_ID,
            "baseline_commit": BASELINE,
            "trials": [NORMAL_ID, GUARD_ID],
            "sequence": ["normal Run1 and full comparison PASS", "existing-output guard Run1"],
            "authorization": {
                "normal_pad_runs": 1,
                "existing_output_guard_pad_runs": 1,
                "guard_only_after_normal_full_pass": True,
                "repaste_count": 0,
                "resave_count": 0,
                "copilot_send_count": 0,
                "candidate_creation_count": 0,
                "full_regression_count": 0,
                "github_write_count": 0,
            },
        },
    )
    write_json(
        NORMAL / "plan.json",
        {
            "schema_version": 1,
            "trial_id": NORMAL_ID,
            "run_id": NORMAL_RUN_ID,
            "classification": "FRESH_FIXED_MECHANICAL_NORMAL_ONE_RUN",
            "pad_run_limit": 1,
            "whole_xlsx_sha_equality_to_live2_required": False,
            "live2_comparison_required": ["value", "type", "position", "effective formatting and dimensions"],
        },
    )
    write_json(
        GUARD / "plan.json",
        {
            "schema_version": 1,
            "trial_id": GUARD_ID,
            "run_id": GUARD_RUN_ID,
            "classification": "FIXED_MECHANICAL_EXISTING_OUTPUT_GUARD_ONE_RUN",
            "pad_run_limit": 1,
            "prerequisite": f"{NORMAL_ID} full PASS",
            "type_comparisons": "NOT_EVALUATED_ON_GUARD_BRANCH",
        },
    )
    write_json(
        CAMPAIGN / "preflight.json",
        {
            "schema_version": 1,
            "campaign_id": CAMPAIGN_ID,
            "result": "PASS_READY_FOR_NORMAL_IDENTITY_AND_ONE_RUN",
            "baseline_commit": BASELINE,
            "fixed_sha256": fixed,
            "builder_sha256": sha256(PROBE / "Build.py"),
            "saved_flow_baseline_sha256": LIVE2_RECOPY_SHA,
            "live2_protected": protected_live2,
            "runtime_inventory": require_runtime_inventory(output_allowed=False),
            "known_output_retired": retired,
            "json_contract": {
                "destinations": [str(path) for path in destinations],
                "count": 8,
                "all_parents_are_json_root": all(path.parent == JSON_ROOT for path in destinations),
            },
            "preplacement": {
                "json_root": str(JSON_ROOT),
                "directory_preexisted": True,
                "write_probe_name": probe_name,
                "write_probe_sha256": probe_sha,
                "write_probe_readback_exact": True,
                "write_probe_removed": True,
                "directory_empty_after_probe": True,
                "directory_writable": True,
                "unknown_file_moved": False,
                "permission_changed": False,
            },
            "pre_run": {
                "work": file_record(WORK),
                "template": file_record(TEMPLATE),
                "input_a": file_record(INPUT_A),
                "input_b": file_record(INPUT_B),
                "output_absent": True,
                "excel_not_running": True,
            },
            "non_repetition": {
                "builder_generation": "NOT_REPEATED",
                "successful_generation_tests": "NOT_REPEATED",
                "full_regression": "NOT_REPEATED",
            },
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    print(json.dumps({"campaign_id": CAMPAIGN_ID, "status": "PASS_READY_FOR_NORMAL_IDENTITY_AND_ONE_RUN"}, ensure_ascii=False))


def capture_identity(stage: str, flow_window_id: int) -> None:
    require(stage in {"normal", "guard"}, "invalid identity stage")
    target = NORMAL if stage == "normal" else GUARD
    require(not (target / "saved-flow-identity.json").exists(), "identity evidence already exists")
    require(sha256(LIVE2_RECOPY) == LIVE2_RECOPY_SHA, "LIVE2 re-copy changed")
    require(not excel_running(), "Excel is running during identity capture")
    if stage == "normal":
        require(load(CAMPAIGN / "preflight.json")["result"] == "PASS_READY_FOR_NORMAL_IDENTITY_AND_ONE_RUN", "campaign preflight mismatch")
        require(not OUTPUT.exists(), "output exists before normal identity capture")
        require(JSON_ROOT.is_dir() and not any(JSON_ROOT.iterdir()), "json_root is not empty before normal identity capture")
    else:
        require(load(NORMAL / "result.json")["decision"] == "PASS_LIVE3_NORMAL1_FULL_FIXED_SCOPE", "normal trial is not full PASS")
        require(OUTPUT.is_file(), "normal output is absent before guard identity capture")
        require(sorted(path.name for path in JSON_ROOT.iterdir()) == sorted(HANDOFF_NAMES), "normal handoff set changed before guard identity capture")

    recopy = target / "saved-flow-recopy-before-run.robin"
    value = base.clipboard_text()
    recopy.write_text(value, encoding="utf-8", newline="")
    require(recopy.read_bytes() == LIVE2_RECOPY.read_bytes(), "saved flow differs from LIVE2 byte baseline")
    record = {
        "schema_version": 1,
        "trial_id": NORMAL_ID if stage == "normal" else GUARD_ID,
        "stage": stage,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "flow": {"name": FLOW_NAME, "window_id": flow_window_id, "subflow": "Main", "power_fx": "OFF"},
        "source_baseline": relative(LIVE2_RECOPY),
        "source_baseline_sha256": LIVE2_RECOPY_SHA,
        "captured_path": relative(recopy),
        "captured_sha256": sha256(recopy),
        "byte_exact_to_live2_saved_flow": True,
        "repaste_count": 0,
        "resave_count": 0,
        "result": "PASS_SAVED_FLOW_BYTE_EXACT_TO_LIVE2_BASELINE",
    }
    write_json(target / "saved-flow-identity.json", record)
    print(json.dumps({"stage": stage, "status": record["result"], "sha256": record["captured_sha256"]}, ensure_ascii=False))


def validate_handoff() -> list[Path]:
    paths = handoff_paths()
    require(all(path.is_file() for path in paths), "one or more handoff JSON files are absent")
    require(sorted(path.name for path in JSON_ROOT.iterdir()) == sorted(HANDOFF_NAMES), "unexpected json_root entry")
    for index, path in enumerate(paths, 1):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        require(set(payload) == {"probe"}, f"unexpected JSON shape: {path.name}")
        if index <= 7:
            require(isinstance(payload["probe"], str), f"text handoff is not string: {path.name}")
        else:
            require(payload["probe"] == "NORMAL", "mode handoff is not NORMAL")
    return paths


def capture_normal(args: argparse.Namespace) -> None:
    require(not NORMAL_RUN.exists(), "normal Run evidence already exists")
    identity = load(NORMAL / "saved-flow-identity.json")
    require(identity["result"] == "PASS_SAVED_FLOW_BYTE_EXACT_TO_LIVE2_BASELINE", "normal saved-flow identity mismatch")
    require(args.powershell_output == EXPECTED_SUCCESS, "PowerShell success JSON mismatch")
    require(args.probe_state == EXPECTED_STATE, "normal ProbeState mismatch")
    require(args.value_type_true_count == 12, "normal PAD did not expose 12 true comparisons")
    require(sha256(WORK) == EXPECTED_WORK_SHA, "work changed during normal Run")
    require(OUTPUT.is_file(), "normal output is absent")
    paths = validate_handoff()

    NORMAL_RUN.mkdir()
    shutil.copy2(WORK, NORMAL_RUN / "work.xlsx")
    shutil.copy2(OUTPUT, NORMAL_RUN / "result.xlsx")
    (NORMAL_RUN / "handoff").mkdir()
    for path in paths:
        shutil.copy2(path, NORMAL_RUN / "handoff" / path.name)
    output_sha = sha256(OUTPUT)
    require(sha256(NORMAL_RUN / "result.xlsx") == output_sha, "normal output preservation mismatch")
    position_names = [f"Position{index}ValueTypeMatch" for index in range(1, 13)]

    write_json(
        NORMAL_RUN / "pad-run.json",
        {
            "schema_version": 1,
            "trial_id": NORMAL_ID,
            "run_id": NORMAL_RUN_ID,
            "flow_name": FLOW_NAME,
            "flow_window_id": args.flow_window_id,
            "run_index_within_trial": 1,
            "campaign_run_index": 1,
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
                "stdout_observed": args.powershell_output,
                "stdout_matches_fixed_success_json": True,
                "stderr_empty_not_claimed": True,
            },
            "status": "PASS_NORMAL_TERMINAL_READY_SUCCESS_JSON",
        },
    )
    write_json(
        NORMAL_RUN / "pad-variables.json",
        {
            "schema_version": 1,
            "trial_id": NORMAL_ID,
            "run_id": NORMAL_RUN_ID,
            "probe_state": {"observed_value": args.probe_state, "match": True},
            "value_type_matches": {name: {"observed_value": True, "match": True} for name in position_names},
            "counts": {"true": 12, "false": 0, "total": 12},
            "type_comparison_evaluation": "EVALUATED_THIS_NORMAL_RUN",
            "status": "PASS_NORMAL_SUCCESS_GATE_AND_12_VALUE_TYPE_MATCH",
        },
    )
    write_json(
        NORMAL_RUN / "artifact.json",
        {
            "schema_version": 1,
            "trial_id": NORMAL_ID,
            "run_id": NORMAL_RUN_ID,
            "runtime_output_path": relative(OUTPUT),
            "preserved_output_path": relative(NORMAL_RUN / "result.xlsx"),
            "output_sha256": output_sha,
            "output_bytes": OUTPUT.stat().st_size,
            "runtime_output_retained_for_guard": True,
            "work_sha256": sha256(WORK),
            "handoff_sha256": {path.name: sha256(path) for path in paths},
            "handoff_stats_before_guard": {path.name: file_record(path) for path in paths},
            "status": "PASS_NORMAL_ARTIFACT_AND_HANDOFF_PRESERVED",
        },
    )
    print(json.dumps({"status": "PASS_NORMAL_RUN_CAPTURED", "output_sha256": output_sha, "handoff_files": 8}, ensure_ascii=False))


def mapping_projection(report: dict) -> list[dict[str, object]]:
    keys = (
        "source_path",
        "source_sheet",
        "source_cell",
        "target_sheet",
        "target_cell",
        "grader_expected",
        "source_actual",
        "target_actual",
        "source_matches_expected",
        "target_matches_expected",
        "source_matches_target",
    )
    return [{key: item[key] for key in keys} for item in report["mappings"]]


def finalize_normal() -> None:
    require(not (NORMAL / "result.json").exists(), "normal result already exists")
    pad_run = load(NORMAL_RUN / "pad-run.json")
    pad_variables = load(NORMAL_RUN / "pad-variables.json")
    artifact = load(NORMAL_RUN / "artifact.json")
    typed = load(NORMAL_RUN / "typed-transfer.json")
    legacy = load(NORMAL_RUN / "comparison.json")
    native = load(NORMAL_RUN / "native-styles.json")
    f6 = load(NORMAL_RUN / "f6-native.json")
    result_xlsx = NORMAL_RUN / "result.xlsx"
    result_sha = sha256(result_xlsx)

    require(pad_run["trial_id"] == NORMAL_ID and pad_run["run_id"] == NORMAL_RUN_ID, "normal PAD identity mismatch")
    require(pad_run["campaign_run_index"] == 1, "normal campaign Run index mismatch")
    require(pad_run["status"] == "PASS_NORMAL_TERMINAL_READY_SUCCESS_JSON", "normal PAD status mismatch")
    require(pad_run["powershell"]["stdout_observed"] == EXPECTED_SUCCESS, "normal PowerShell observation mismatch")
    require(pad_variables["probe_state"] == {"observed_value": EXPECTED_STATE, "match": True}, "normal ProbeState mismatch")
    require(pad_variables["counts"] == {"true": 12, "false": 0, "total": 12}, "normal PAD comparison count mismatch")
    require(artifact["output_sha256"] == result_sha, "normal artifact SHA mismatch")

    shared = load_module("issue38_r11_live3_validator", ROOT / "tools/Finalize-Issue38Ex03R11FileAux.py")
    contract = shared.fixed_contract()
    typed_for_shared = copy.deepcopy(typed)
    typed_for_shared["run_label"] = "EX03-R11-FILE-AUX1-RUN1"
    shared.validate_typed_report(typed_for_shared, 1, result_xlsx, result_sha, contract)
    shared.validate_legacy_report(legacy, result_sha, contract)
    shared.validate_native_report(native, result_xlsx, result_sha, contract)
    shared.validate_f6_report(f6, result_xlsx, result_sha, contract)

    live2_artifact = load(LIVE2_RUN / "artifact.json")
    live2_typed = load(LIVE2_RUN / "typed-transfer.json")
    live2_native = load(LIVE2_RUN / "native-styles.json")
    live2_f6 = load(LIVE2_RUN / "f6-native.json")
    require(live2_artifact["output_sha256"] == sha256(LIVE2_RUN / "result.xlsx"), "LIVE2 artifact binding changed")
    normal_projection = mapping_projection(typed)
    live2_projection = mapping_projection(live2_typed)
    require(len(normal_projection) == 12 and normal_projection == live2_projection, "normal/LIVE2 value-type-position comparison mismatch")
    require(native["bounds"] == live2_native["bounds"], "normal/LIVE2 format bounds differ")
    require(native["snapshot_sha256"]["output"] == live2_native["snapshot_sha256"]["output"], "normal/LIVE2 effective-format snapshot differs")
    require(not native["differences"] and not live2_native["differences"], "normal or LIVE2 effective format differs from template")
    f6_keys = ("value2", "value2_dotnet_type", "number_format_invariant", "number_format_local", "prefix_character", "has_formula")
    require({key: f6["saved_f6"][key] for key in f6_keys} == {key: live2_f6["saved_f6"][key] for key in f6_keys}, "normal/LIVE2 F6 contract differs")

    whole_sha_equal = result_sha == live2_artifact["output_sha256"]
    comparison = {
        "schema_version": 1,
        "kind": "LIVE3_NORMAL1_TO_LIVE2_SEMANTIC_COMPARISON",
        "normal_trial_id": NORMAL_ID,
        "normal_run_id": NORMAL_RUN_ID,
        "normal_artifact_sha256": result_sha,
        "live2_trial_id": "EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE2",
        "live2_run_id": "EX03-R12-FIXED-HELPER-MECHANICAL-P1-LIVE2-RUN1",
        "live2_artifact_sha256": live2_artifact["output_sha256"],
        "value_type_position": {"checked": 12, "mismatches": 0, "status": "MATCH"},
        "effective_format": {
            "checked_cells": native["bounds"]["checked_cells"],
            "checked_rows": native["bounds"]["checked_rows"],
            "checked_columns": native["bounds"]["checked_columns"],
            "normal_snapshot_sha256": native["snapshot_sha256"]["output"],
            "live2_snapshot_sha256": live2_native["snapshot_sha256"]["output"],
            "status": "MATCH",
        },
        "f6_contract": "MATCH",
        "whole_xlsx_sha_equal_observed": whole_sha_equal,
        "whole_xlsx_sha_equality_used_as_gate": False,
        "status": "PASS_LIVE3_NORMAL1_MATCHES_LIVE2_VALUE_TYPE_POSITION_AND_FORMAT",
    }
    write_json(NORMAL_RUN / "live2-semantic-comparison.json", comparison)

    require(OUTPUT.is_file() and sha256(OUTPUT) == result_sha, "runtime normal output changed before guard")
    paths = validate_handoff()
    require(all(sha256(path) == artifact["handoff_sha256"][path.name] for path in paths), "runtime handoff changed before guard")
    require(sha256(WORK) == sha256(TEMPLATE) == EXPECTED_WORK_SHA, "work/template changed after normal Run")
    fixed_hashes()
    protect_tree(LIVE2)

    result = {
        "schema_version": 1,
        "trial_id": NORMAL_ID,
        "run_id": NORMAL_RUN_ID,
        "decision": "PASS_LIVE3_NORMAL1_FULL_FIXED_SCOPE",
        "scope": "Fresh fixed-EX03 mechanical-builder normal Run only.",
        "pad": {
            "run_count": 1,
            "terminal_ready": True,
            "powershell_success_json": EXPECTED_SUCCESS,
            "probe_state": EXPECTED_STATE,
            "value_type_match_true": 12,
            "value_type_match_false": 0,
        },
        "artifact": {"sha256": result_sha, "bytes": result_xlsx.stat().st_size, "runtime_retained_for_guard": True},
        "comparison": {
            "target_cells": {"checked": 12, "mismatches": 0},
            "outside_cells": legacy["checks"]["outside_values_types_formulas"],
            "effective_format": {"status": native["status"], "differences": native["difference_attribute_counts"]},
            "f6": {"status": f6["status"], "saved": f6["saved_f6"]},
            "live2_semantic": comparison,
            "legacy_raw_558": {"status": "FAIL_PRESERVED", "failure_counts": legacy["failure_counts"]},
        },
        "guard_authorized_to_proceed": True,
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(NORMAL / "result.json", result)
    (NORMAL / "RESULT.md").write_text(
        f"""# {NORMAL_ID}\n\n`{result['decision']}`。正常系1RunはREADY、固定helper成功JSON、成功gate、12/12 PAD型照合を確認した。保存後は12対象、対象外468セル、数式、実効書式480セル・48行・30列、原本SHA、F6契約がPASS。LIVE2とは値・型・位置・実効書式で一致し、xlsx全体SHAは受入gateに使っていない。\n\n出力SHA-256: `{result_sha}`。固定出力と8 handoff JSONは、後続の既存出力ガード試行のためそのまま保持した。旧raw 558差分は診断記録として保持した。\n""",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"decision": result["decision"], "guard_authorized_to_proceed": True, "output_sha256": result_sha}, ensure_ascii=False))


def prepare_guard() -> None:
    require(not (GUARD / "preflight.json").exists(), "guard preflight already exists")
    normal = load(NORMAL / "result.json")
    require(normal["decision"] == "PASS_LIVE3_NORMAL1_FULL_FIXED_SCOPE" and normal["guard_authorized_to_proceed"] is True, "normal trial does not authorize guard")
    identity = load(GUARD / "saved-flow-identity.json")
    require(identity["result"] == "PASS_SAVED_FLOW_BYTE_EXACT_TO_LIVE2_BASELINE", "guard saved-flow identity mismatch")
    require(OUTPUT.is_file(), "normal output is absent before guard")
    paths = handoff_paths()
    validate_handoff()
    require(not excel_running(), "Excel is running before guard")
    require_runtime_inventory(output_allowed=True)
    contract = static_guard_contract()
    protected_paths = [OUTPUT, INPUT_A, INPUT_B, TEMPLATE, WORK] + paths
    before = snapshot(protected_paths)
    require(before[relative(OUTPUT)]["sha256"] == normal["artifact"]["sha256"], "runtime output is not the normal artifact")
    shutil.copy2(OUTPUT, GUARD / "existing-output-before.xlsx")
    require(sha256(GUARD / "existing-output-before.xlsx") == before[relative(OUTPUT)]["sha256"], "guard before archive mismatch")
    write_json(
        GUARD / "preflight.json",
        {
            "schema_version": 1,
            "trial_id": GUARD_ID,
            "run_id": GUARD_RUN_ID,
            "result": "PASS_READY_FOR_ONE_EXISTING_OUTPUT_GUARD_RUN",
            "normal_prerequisite": {
                "trial_id": NORMAL_ID,
                "decision": normal["decision"],
                "artifact_sha256": normal["artifact"]["sha256"],
            },
            "saved_flow_identity": identity,
            "static_guard_contract": contract,
            "protected_before": before,
            "output_present_at_fixed_path": True,
            "handoff_count": 8,
            "excel_not_running": True,
            "type_comparison_policy": "NOT_EVALUATED_ON_GUARD_BRANCH; persisted PAD values are not graded",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    print(json.dumps({"trial_id": GUARD_ID, "status": "PASS_READY_FOR_ONE_EXISTING_OUTPUT_GUARD_RUN", "protected_files": len(before)}, ensure_ascii=False))


def parse_false(value: str, name: str) -> bool:
    require(value.lower() in {"true", "false"}, f"invalid boolean for {name}")
    return value.lower() == "true"


def capture_guard(args: argparse.Namespace) -> None:
    require(not (GUARD / "pad-run.json").exists(), "guard Run evidence already exists")
    preflight = load(GUARD / "preflight.json")
    require(preflight["result"] == "PASS_READY_FOR_ONE_EXISTING_OUTPUT_GUARD_RUN", "guard preflight mismatch")
    require(args.probe_state == EXPECTED_GUARD_STATE, "guard ProbeState mismatch")
    script_gate = parse_false(args.script_gate_passed, "ScriptGatePassed")
    numeric_entered = parse_false(args.numeric_write_entered, "NumericWriteEntered")
    save_as_entered = parse_false(args.save_as_entered, "SaveAsEntered")
    require(script_gate is False, "success gate was entered during guard Run")
    require(numeric_entered is False, "numeric write was entered during guard Run")
    require(save_as_entered is False, "SaveAs was entered during guard Run")
    protected_paths = [OUTPUT, INPUT_A, INPUT_B, TEMPLATE, WORK] + handoff_paths()
    after = snapshot(protected_paths)
    require_same_snapshot(preflight["protected_before"], after, "guard-protected files")
    require(not excel_running(), "Excel remains running after guard Run")
    shutil.copy2(OUTPUT, GUARD / "existing-output-after.xlsx")
    require(sha256(GUARD / "existing-output-before.xlsx") == sha256(GUARD / "existing-output-after.xlsx"), "guard output before/after archives differ")

    write_json(
        GUARD / "pad-run.json",
        {
            "schema_version": 1,
            "trial_id": GUARD_ID,
            "run_id": GUARD_RUN_ID,
            "flow_name": FLOW_NAME,
            "flow_window_id": args.flow_window_id,
            "run_index_within_trial": 1,
            "campaign_run_index": 2,
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
            "status": "PASS_GUARD_TERMINAL_READY_NO_DESIGNER_ERROR",
        },
    )
    write_json(
        GUARD / "pad-variables.json",
        {
            "schema_version": 1,
            "trial_id": GUARD_ID,
            "run_id": GUARD_RUN_ID,
            "probe_state": {"observed_value": args.probe_state, "match": True},
            "script_gate_passed": {"observed_value": script_gate, "expected": False, "match": True},
            "numeric_write_entered": {"observed_value": numeric_entered, "expected": False, "match": True},
            "save_as_entered": {"observed_value": save_as_entered, "expected": False, "match": True},
            "powershell_output": "NOT_GRADED; value may persist from the preceding normal Run",
            "value_type_matches": "NOT_EVALUATED_ON_GUARD_BRANCH; persisted values are not mismatches or new PASS evidence",
            "status": "PASS_OUTPUT_GUARD_STATE_AND_NON_ENTRY_FLAGS",
        },
    )
    write_json(
        GUARD / "hashes-after-run.json",
        {
            "schema_version": 1,
            "trial_id": GUARD_ID,
            "run_id": GUARD_RUN_ID,
            "protected_before": preflight["protected_before"],
            "protected_after": after,
            "sha_size_mtime_exact": True,
            "existing_output_before_archive_sha256": sha256(GUARD / "existing-output-before.xlsx"),
            "existing_output_after_archive_sha256": sha256(GUARD / "existing-output-after.xlsx"),
            "status": "PASS_ALL_GUARD_PROTECTED_FILES_UNCHANGED",
        },
    )
    print(json.dumps({"status": "PASS_GUARD_RUN_CAPTURED", "probe_state": args.probe_state, "protected_files": len(after)}, ensure_ascii=False))


def finalize() -> None:
    require(not (CAMPAIGN / "result.json").exists(), "campaign result already exists")
    normal = load(NORMAL / "result.json")
    preflight = load(GUARD / "preflight.json")
    pad_run = load(GUARD / "pad-run.json")
    variables = load(GUARD / "pad-variables.json")
    hashes = load(GUARD / "hashes-after-run.json")
    require(normal["decision"] == "PASS_LIVE3_NORMAL1_FULL_FIXED_SCOPE", "normal result changed")
    require(pad_run["trial_id"] == GUARD_ID and pad_run["run_id"] == GUARD_RUN_ID, "guard PAD identity mismatch")
    require(pad_run["campaign_run_index"] == 2, "guard campaign Run index mismatch")
    require(pad_run["status"] == "PASS_GUARD_TERMINAL_READY_NO_DESIGNER_ERROR", "guard terminal mismatch")
    require(variables["probe_state"] == {"observed_value": EXPECTED_GUARD_STATE, "match": True}, "guard state evidence mismatch")
    require(variables["script_gate_passed"]["observed_value"] is False, "script gate evidence mismatch")
    require(variables["numeric_write_entered"]["observed_value"] is False, "numeric entry evidence mismatch")
    require(variables["save_as_entered"]["observed_value"] is False, "SaveAs entry evidence mismatch")
    require(hashes["sha_size_mtime_exact"] is True, "guard protected hashes were not exact")
    require_same_snapshot(preflight["protected_before"], hashes["protected_after"], "final guard-protected files")
    require(sha256(GUARD / "existing-output-before.xlsx") == sha256(GUARD / "existing-output-after.xlsx"), "guard archives changed")
    require(OUTPUT.is_file(), "fixed output disappeared before final preservation")
    validate_handoff()
    require(not excel_running(), "Excel is running during finalization")
    fixed_hashes()
    protect_tree(LIVE2)

    preserved_output = GUARD / "runtime-output-after-guard.xlsx"
    shutil.move(str(OUTPUT), str(preserved_output))
    require(sha256(preserved_output) == normal["artifact"]["sha256"], "runtime output preservation mismatch")
    preserved_handoff = GUARD / "runtime-handoff-after-guard"
    preserved_handoff.mkdir()
    for path in handoff_paths():
        destination = preserved_handoff / path.name
        shutil.move(str(path), str(destination))
        expected = preflight["protected_before"][relative(path)]["sha256"]
        require(sha256(destination) == expected, f"handoff preservation mismatch: {path.name}")
    require(not OUTPUT.exists(), "runtime output remains after preservation")
    require(JSON_ROOT.is_dir() and not any(JSON_ROOT.iterdir()), "json_root is not empty after preservation")
    require(sha256(WORK) == sha256(TEMPLATE) == EXPECTED_WORK_SHA, "work/template changed during campaign")

    guard_result = {
        "schema_version": 1,
        "trial_id": GUARD_ID,
        "run_id": GUARD_RUN_ID,
        "decision": "PASS_LIVE3_EXISTING_OUTPUT_GUARD1",
        "scope": "Fixed EX03 mechanical-builder existing-output branch only.",
        "guard": {
            "probe_state": EXPECTED_GUARD_STATE,
            "static_else_contains_all_sensitive_actions": preflight["static_guard_contract"]["all_sensitive_actions_in_mutually_exclusive_else"],
            "script_gate_passed": False,
            "numeric_write_entered": False,
            "save_as_entered": False,
            "json_handoff_sha_size_mtime_unchanged": True,
            "existing_output_sha_size_mtime_unchanged": True,
            "inputs_template_work_sha_size_mtime_unchanged": True,
            "normal_termination": True,
        },
        "type_comparisons": "NOT_EVALUATED_ON_GUARD_BRANCH",
        "powershell_output": "NOT_GRADED_AS_FRESH_OUTPUT",
        "runtime_after_preservation": {"output_absent": True, "json_root_empty": True, "excel_not_running": True},
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(GUARD / "result.json", guard_result)
    (GUARD / "RESULT.md").write_text(
        f"""# {GUARD_ID}\n\n`{guard_result['decision']}`。正常系出力を固定出力先に残した1Runで、PADは`{EXPECTED_GUARD_STATE}`へ入りREADYで正常終了した。`ScriptGatePassed=False`、`NumericWriteEntered=False`、`SaveAsEntered=False`を直接確認し、8 handoff JSON、既存出力、入力2冊、template、workのSHA・サイズ・mtimeは前後完全一致した。\n\n型比較はガード分岐で未実行のため`NOT_EVALUATED`であり、前Runから残る変数値を不一致または新たなPASSへ読み替えていない。\n""",
        encoding="utf-8",
        newline="\n",
    )
    campaign_result = {
        "schema_version": 1,
        "campaign_id": CAMPAIGN_ID,
        "decision": "PASS_LIVE3_NORMAL1_THEN_EXISTING_OUTPUT_GUARD1",
        "scope": "Fixed EX03 mechanical-builder path only; not Copilot generation or Issue #38 overall acceptance.",
        "baseline_commit": BASELINE,
        "normal": {
            "trial_id": NORMAL_ID,
            "decision": normal["decision"],
            "artifact_sha256": normal["artifact"]["sha256"],
            "pad_runs": 1,
        },
        "guard": {
            "trial_id": GUARD_ID,
            "decision": guard_result["decision"],
            "pad_runs": 1,
            "type_comparisons": "NOT_EVALUATED",
        },
        "sequence_gate": "GUARD_RAN_ONLY_AFTER_NORMAL_FULL_PASS",
        "preservation": {
            "live2_unchanged": True,
            "fixed_builder_wiring_helper_invocation_launcher_robin_unchanged": True,
            "runtime_output_preserved_then_removed_from_fixed_path": True,
            "runtime_handoff_preserved_then_json_root_emptied": True,
        },
        "not_run": ["Copilot send", "candidate creation", "full regression", "additional PAD Run", "GitHub write"],
        "remaining": [
            "The saved Robin has no separate stderr PAD variable; empty stderr is not directly claimed.",
            "This campaign does not establish Copilot generation or Issue #38 overall acceptance.",
        ],
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(CAMPAIGN / "result.json", campaign_result)
    (CAMPAIGN / "RESULT.md").write_text(
        f"""# {CAMPAIGN_ID}\n\n`{campaign_result['decision']}`。別IDの正常系1Runが固定範囲で完全PASSした後にだけ、別IDの既存出力ガード1Runを実行した。\n\n- 正常系: 12対象、対象外468、数式、実効書式、原本SHA、F6契約、LIVE2との値・型・位置・書式比較PASS\n- 負例: `{EXPECTED_GUARD_STATE}`、成功gate・数値書込み・SaveAs未進入、8 JSON・既存出力・入力・template・work不変、READY正常終了\n- 負例の型比較: 未実行のためNOT_EVALUATED\n- Copilot送信、候補版、全件回帰、追加Run、GitHub書込み: 0\n\n本判定は固定EX03の機械ビルダー経路に限定する。\n""",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(campaign_result, ensure_ascii=False, separators=(",", ":")))


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="phase", required=True)
    sub.add_parser("prepare")
    identity = sub.add_parser("capture-identity")
    identity.add_argument("--stage", choices=("normal", "guard"), required=True)
    identity.add_argument("--flow-window-id", type=int, required=True)
    normal = sub.add_parser("capture-normal")
    normal.add_argument("--flow-window-id", type=int, required=True)
    normal.add_argument("--started-utc", required=True)
    normal.add_argument("--terminal-observed-utc", required=True)
    normal.add_argument("--variables-observed-utc", required=True)
    normal.add_argument("--powershell-output", required=True)
    normal.add_argument("--probe-state", required=True)
    normal.add_argument("--value-type-true-count", type=int, required=True)
    sub.add_parser("finalize-normal")
    sub.add_parser("prepare-guard")
    guard = sub.add_parser("capture-guard")
    guard.add_argument("--flow-window-id", type=int, required=True)
    guard.add_argument("--started-utc", required=True)
    guard.add_argument("--terminal-observed-utc", required=True)
    guard.add_argument("--variables-observed-utc", required=True)
    guard.add_argument("--probe-state", required=True)
    guard.add_argument("--script-gate-passed", required=True)
    guard.add_argument("--numeric-write-entered", required=True)
    guard.add_argument("--save-as-entered", required=True)
    sub.add_parser("finalize")
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare()
    elif args.phase == "capture-identity":
        capture_identity(args.stage, args.flow_window_id)
    elif args.phase == "capture-normal":
        capture_normal(args)
    elif args.phase == "finalize-normal":
        finalize_normal()
    elif args.phase == "prepare-guard":
        prepare_guard()
    elif args.phase == "capture-guard":
        capture_guard(args)
    else:
        finalize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
