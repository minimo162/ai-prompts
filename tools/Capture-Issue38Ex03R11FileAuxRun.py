"""Preserve one observed EX03-r11 downloaded-file auxiliary PAD run.

This recorder is intentionally fixed to the separately identified auxiliary
test.  It does not change or reinterpret the formal EX03-r11-G1 result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1"
RUNTIME = ROOT / "catalog/acceptance/issue38/runs/EX03-attempt1"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
EXPECTED_WORK_SHA = "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21"
TRANSFER_STATE = "SAVED_REOPENED_12_JSON_COMPARISONS_READY"
FLOW_NAME = "無題 (10)"
FLOW_WINDOW_ID = 71280
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


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, choices=(1, 2), required=True)
    parser.add_argument("--started-utc", required=True)
    parser.add_argument("--terminal-observed-utc", required=True)
    parser.add_argument("--variables-observed-utc", required=True)
    args = parser.parse_args()

    run_dir = CYCLE / f"run{args.run}"
    if run_dir.exists():
        raise ValueError(f"Refusing to overwrite run evidence: {run_dir}")
    if not WORK.is_file() or sha256(WORK) != EXPECTED_WORK_SHA:
        raise ValueError("Runtime work.xlsx no longer matches the frozen template")
    if not OUTPUT.is_file():
        raise ValueError("Fixed PAD output is absent")

    run_dir.mkdir(parents=False)
    preserved_work = run_dir / "work.xlsx"
    preserved_result = run_dir / "result.xlsx"
    shutil.copy2(WORK, preserved_work)
    shutil.copy2(OUTPUT, preserved_result)

    output_sha = sha256(OUTPUT)
    if sha256(preserved_work) != EXPECTED_WORK_SHA:
        raise ValueError("Preserved work copy is not byte exact")
    if sha256(preserved_result) != output_sha:
        raise ValueError("Preserved result copy is not byte exact")

    write_json(
        run_dir / "pad-run.json",
        {
            "schema_version": 1,
            "test_id": f"EX03-R11-FILE-AUX1-RUN{args.run}",
            "flow_name": FLOW_NAME,
            "flow_window_id": FLOW_WINDOW_ID,
            "run_index": args.run,
            "run_invocations_total": args.run,
            "started_utc": args.started_utc,
            "terminal_observed_utc": args.terminal_observed_utc,
            "variables_observed_utc": args.variables_observed_utc,
            "terminal_observation": {
                "status_bar": "READY",
                "run_button_enabled": True,
                "stop_button_disabled": True,
                "designer_error_observed": False,
            },
            "status": "PASS_TERMINAL_READY_NO_ERROR_OBSERVED",
        },
    )
    write_json(
        run_dir / "pad-variables.json",
        {
            "schema_version": 1,
            "test_id": f"EX03-R11-FILE-AUX1-RUN{args.run}",
            "flow_name": FLOW_NAME,
            "execution_requested_during_observation": False,
            "method": (
                "PAD Variables pane search after the same run: one ValueTypeMatch "
                "filter showing 12 results across top/bottom scroll positions, plus "
                "TransferState opened in the variable edit dialog and cancelled unchanged"
            ),
            "transfer_state": {
                "observed_value": TRANSFER_STATE,
                "match": True,
            },
            "value_type_matches": {
                name: {"observed_value": True, "match": True}
                for name in VALUE_TYPE_MATCH_VARIABLES
            },
            "counts": {"true": 12, "false": 0, "total": 12},
            "status": "PASS_12_OF_12_PAD_JSON_VALUE_AND_TYPE_MATCH",
        },
    )
    write_json(
        run_dir / "artifact.json",
        {
            "schema_version": 1,
            "runtime_output_path": relative(OUTPUT),
            "preserved_output_path": relative(preserved_result),
            "output_sha256": output_sha,
            "output_bytes": OUTPUT.stat().st_size,
            "preserved_output_exact": True,
            "runtime_work_path": relative(WORK),
            "preserved_work_path": relative(preserved_work),
            "work_sha256": EXPECTED_WORK_SHA,
            "preserved_work_exact": True,
            "status": "PASS_ARTIFACT_PRESERVED",
        },
    )
    print(
        json.dumps(
            {
                "run": args.run,
                "status": "PASS_PAD_TERMINAL_VARIABLES_AND_ARTIFACT_PRESERVED",
                "output_sha256": output_sha,
                "value_type_match_true": 12,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
