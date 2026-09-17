"""Fail-closed Run1 gate and recoverable setup for the second auxiliary run."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1"
RUN1 = CYCLE / "run1"
RUNTIME = ROOT / "catalog/acceptance/issue38/runs/EX03-attempt1"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
EXPECTED_WORK_SHA = "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21"
EXPECTED_LEGACY_COUNTS = {"styles": 480, "row_dimensions": 48, "column_dimensions": 30}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(name: str) -> dict:
    with (RUN1 / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    verification_path = RUN1 / "verification.json"
    advance_path = RUN1 / "advance-to-run2.json"
    moved_output = RUN1 / "runtime-output-before-run2.xlsx"
    for path in (verification_path, advance_path, moved_output):
        if path.exists():
            raise ValueError(f"Refusing to overwrite gate evidence: {path}")

    pad_run = read_json("pad-run.json")
    pad_variables = read_json("pad-variables.json")
    artifact = read_json("artifact.json")
    typed = read_json("typed-transfer.json")
    legacy = read_json("comparison.json")
    native = read_json("native-styles.json")
    f6 = read_json("f6-native.json")

    legacy_counts = legacy.get("failure_counts", {})
    legacy_total = sum(legacy_counts.values())
    native_counts = native.get("difference_attribute_counts", {})
    native_location_counts = native.get("difference_location_counts", {})
    checks = {
        "pad_terminal_ready": pad_run.get("status") == "PASS_TERMINAL_READY_NO_ERROR_OBSERVED",
        "pad_12_json_value_and_type_matches": (
            pad_variables.get("status") == "PASS_12_OF_12_PAD_JSON_VALUE_AND_TYPE_MATCH"
            and pad_variables.get("counts") == {"true": 12, "false": 0, "total": 12}
        ),
        "artifact_preserved": artifact.get("status") == "PASS_ARTIFACT_PRESERVED",
        "fixed_typed_transfer": typed.get("status") == "MATCH_FIXED_EX03_TEXT_NUMBER_SCOPE",
        "typed_mismatches_zero": not typed.get("mismatches"),
        "originals_unchanged": typed.get("originals_unchanged_by_verifier") is True,
        "legacy_raw_fail_preserved": legacy.get("status") == "FAIL",
        "legacy_558_exact": legacy_counts == EXPECTED_LEGACY_COUNTS and legacy_total == 558,
        "legacy_target_mismatches_zero": not legacy["checks"]["target_values_types_positions"]["mismatches"],
        "legacy_outside_mismatches_zero": not legacy["checks"]["outside_values_types_formulas"]["mismatches"],
        "excel_effective_format_matches": native.get("status") == "MATCH_EFFECTIVE_FORMAT",
        "excel_effective_attribute_differences_zero": all(value == 0 for value in native_counts.values()),
        "excel_effective_location_differences_zero": all(value == 0 for value in native_location_counts.values()),
        "f6_native_contract": f6.get("status") == "PASS_F6_SYSTEM_STRING_100_PERCENT_ORIGINAL_FORMAT_EMPTY_PREFIX_NO_FORMULA",
        "work_still_frozen_template": WORK.is_file() and sha256(WORK) == EXPECTED_WORK_SHA,
        "runtime_output_exists": OUTPUT.is_file(),
        "runtime_output_matches_preserved": (
            OUTPUT.is_file()
            and sha256(OUTPUT) == artifact.get("output_sha256")
            and sha256(OUTPUT) == sha256(RUN1 / "result.xlsx")
        ),
    }
    if not all(checks.values()):
        raise ValueError(f"Run1 gate failed: {[name for name, passed in checks.items() if not passed]}")

    verification = {
        "schema_version": 1,
        "test_id": "EX03-R11-FILE-AUX1-RUN1",
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "fixed_scope": {
            "target_cells": 12,
            "target_mismatches": 0,
            "outside_cells": 468,
            "outside_value_type_formula_mismatches": 0,
            "pad_json_value_and_type_true": 12,
            "pad_json_value_and_type_false": 0,
        },
        "legacy_raw_diagnostic": {
            "status": "FAIL_PRESERVED_NOT_USED_AS_EFFECTIVE_FORMAT_GATE",
            "failure_counts": legacy_counts,
            "total": legacy_total,
            "classification": (
                "The existing raw openpyxl comparison reports serialization/comparison "
                "differences; the read-only Excel-effective comparison reports zero "
                "format, row, column, or sheet-structure differences."
            ),
        },
        "run2_gate": "PASS_AUTHORIZED_BY_FIXED_RULES",
        "formal_ex03_r11_g1_result": "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD_PRESERVED",
        "acceptance_boundary": (
            "Auxiliary downloaded-file PAD evidence only; it does not replace or offset "
            "the formal EX03-r11-G1 delivery-contract failure and is not generalized "
            "beyond the fixed EX03 text/number mapping."
        ),
    }
    write_json(verification_path, verification)

    output_sha = sha256(OUTPUT)
    shutil.move(str(OUTPUT), str(moved_output))
    if OUTPUT.exists() or sha256(moved_output) != output_sha:
        raise ValueError("Run1 runtime output move was not exact")
    if sha256(WORK) != EXPECTED_WORK_SHA:
        raise ValueError("Runtime work changed during Run2 setup")

    write_json(
        advance_path,
        {
            "schema_version": 1,
            "advanced_at": datetime.now(timezone.utc).isoformat(),
            "run1_runtime_output_preserved_as": moved_output.relative_to(ROOT).as_posix(),
            "run1_runtime_output_sha256": output_sha,
            "runtime_output_absent_before_run2": True,
            "runtime_work_sha256": sha256(WORK),
            "runtime_work_matches_frozen_template": True,
            "status": "PASS_READY_FOR_RUN2",
        },
    )
    print(
        json.dumps(
            {
                "status": "PASS_READY_FOR_RUN2",
                "legacy_raw_differences_preserved": legacy_total,
                "effective_format_differences": sum(native_counts.values()),
                "runtime_output_absent": not OUTPUT.exists(),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
