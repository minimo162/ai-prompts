#!/usr/bin/env python3
"""Preserve the single authorized saved-flow T2 PAD run before comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
T1 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
T2 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2"
RUNTIME = T1 / "runtime"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
RUN = T2 / "run1"
EXPECTED_WORK_SHA = "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21"
EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'
VALUE_TYPE_MATCH_VARIABLES = [
    "追記先_D5_ValueTypeMatch",
    "追記先_D6_ValueTypeMatch",
    "追記先_E5_ValueTypeMatch",
    "追記先_E6_ValueTypeMatch",
    "追記先_F5_ValueTypeMatch",
    "追記先_F6_ValueTypeMatch",
    "集計先_F7_ValueTypeMatch",
    "集計先_F8_ValueTypeMatch",
    "集計先_F9_ValueTypeMatch",
    "集計先_G7_ValueTypeMatch",
    "集計先_G8_ValueTypeMatch",
    "集計先_G9_ValueTypeMatch",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--started-utc", required=True)
    parser.add_argument("--terminal-observed-utc", required=True)
    parser.add_argument("--variables-observed-utc", required=True)
    parser.add_argument("--powershell-output", required=True)
    parser.add_argument("--transfer-state", required=True)
    parser.add_argument("--value-type-true-count", required=True, type=int)
    args = parser.parse_args()

    if RUN.exists():
        raise FileExistsError(f"Refusing to overwrite T2 Run evidence: {RUN}")
    preflight = load(T2 / "preflight.json")
    if preflight["result"] != "PASS_READY_FOR_ONE_SAVED_FLOW_NORMAL_PAD_RUN":
        raise ValueError("T2 preflight did not authorize the single Run")
    if args.powershell_output != EXPECTED_SUCCESS:
        raise ValueError("Observed PowerShell output is not the fixed success JSON")
    if args.transfer_state != "SAVED_REOPENED_12_JSON_COMPARISONS_READY":
        raise ValueError("Observed TransferState is not the fixed terminal state")
    if args.value_type_true_count != 12:
        raise ValueError("PAD did not expose 12 true value/type results")
    if not WORK.is_file() or sha256(WORK) != EXPECTED_WORK_SHA:
        raise ValueError("Runtime work no longer matches the frozen template")
    if not OUTPUT.is_file():
        raise FileNotFoundError("Authorized T2 PAD output is absent")

    handoff_paths = [RUNTIME / f"source-{index}.json" for index in range(1, 8)]
    handoff_paths.append(RUNTIME / "mode.json")
    missing = [str(path) for path in handoff_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"T2 JSON handoff missing: {missing}")
    for index, path in enumerate(handoff_paths, start=1):
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if set(payload) != {"probe"}:
            raise ValueError(f"Unexpected JSON handoff shape: {path}")
        if index <= 7 and not isinstance(payload["probe"], str):
            raise ValueError(f"Text handoff is not a string: {path}")
        if index == 8 and payload["probe"] != "NORMAL":
            raise ValueError("T2 mode handoff is not NORMAL")

    RUN.mkdir(parents=False)
    preserved_work = RUN / "work.xlsx"
    preserved_result = RUN / "result.xlsx"
    handoff_dir = RUN / "handoff"
    handoff_dir.mkdir()
    shutil.copy2(WORK, preserved_work)
    shutil.copy2(OUTPUT, preserved_result)
    for path in handoff_paths:
        shutil.copy2(path, handoff_dir / path.name)

    output_sha = sha256(OUTPUT)
    if sha256(preserved_work) != EXPECTED_WORK_SHA:
        raise ValueError("Preserved work is not the frozen template")
    if sha256(preserved_result) != output_sha:
        raise ValueError("Preserved result is not byte exact")
    handoff_hashes = {
        path.name: sha256(handoff_dir / path.name) for path in handoff_paths
    }
    if any(sha256(path) != handoff_hashes[path.name] for path in handoff_paths):
        raise ValueError("Preserved JSON handoff is not byte exact")

    write_json(
        RUN / "pad-run.json",
        {
            "schema_version": 1,
            "trial_id": "EX03-R12-FIXED-HELPER-P1-T2",
            "run_id": "EX03-R12-FIXED-HELPER-P1-T2-RUN1",
            "flow_name": "無題 (14)",
            "flow_window_id": 1382846,
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
                "stderr_observation": "NO_DESIGNER_ERROR_OBSERVED; NO_SEPARATE_STDERR_VARIABLE",
                "stderr_empty_not_claimed": True,
            },
            "status": "PASS_TERMINAL_READY_SUCCESS_JSON_NO_DESIGNER_ERROR",
        },
    )
    write_json(
        RUN / "pad-variables.json",
        {
            "schema_version": 1,
            "trial_id": "EX03-R12-FIXED-HELPER-P1-T2",
            "run_id": "EX03-R12-FIXED-HELPER-P1-T2-RUN1",
            "flow_name": "無題 (14)",
            "execution_requested_during_observation": False,
            "method": (
                "PAD Variables pane after the same Run: PowershellOutput and "
                "TransferState values opened read-only/cancelled; ValueTypeMatch "
                "search showed all 12 results true"
            ),
            "powershell_output": {
                "observed_value": args.powershell_output,
                "match": True,
            },
            "transfer_state": {
                "observed_value": args.transfer_state,
                "match": True,
            },
            "value_type_matches": {
                name: {"observed_value": True, "match": True}
                for name in VALUE_TYPE_MATCH_VARIABLES
            },
            "counts": {"true": 12, "false": 0, "total": 12},
            "status": "PASS_SUCCESS_JSON_TRANSFER_STATE_AND_12_VALUE_TYPE_MATCH",
        },
    )
    write_json(
        RUN / "artifact.json",
        {
            "schema_version": 1,
            "trial_id": "EX03-R12-FIXED-HELPER-P1-T2",
            "run_id": "EX03-R12-FIXED-HELPER-P1-T2-RUN1",
            "runtime_output_path": relative(OUTPUT),
            "preserved_output_path": relative(preserved_result),
            "output_sha256": output_sha,
            "output_bytes": OUTPUT.stat().st_size,
            "preserved_output_exact": True,
            "runtime_work_path": relative(WORK),
            "preserved_work_path": relative(preserved_work),
            "work_sha256": EXPECTED_WORK_SHA,
            "preserved_work_exact": True,
            "handoff_directory": relative(handoff_dir),
            "handoff_sha256": handoff_hashes,
            "status": "PASS_T2_RUN1_ARTIFACT_AND_HANDOFF_PRESERVED",
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS_T2_RUN1_PRESERVED",
                "output_sha256": output_sha,
                "work_sha256": sha256(WORK),
                "handoff_files": len(handoff_paths),
                "pad_value_type_true": 12,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
