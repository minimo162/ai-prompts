"""Finalize the separately identified EX03-r11 downloaded-file PAD evidence."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1"
FORMAL = ROOT / "catalog/acceptance/issue38/cycles/EX03-r11-G1"
RUNTIME = ROOT / "catalog/acceptance/issue38/runs/EX03-attempt1"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
EXPECTED_WORK_SHA = "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21"
EXPECTED_GENERATED_SHA = "a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875"
EXPECTED_LEGACY_COUNTS = {"styles": 480, "row_dimensions": 48, "column_dimensions": 30}
FORMAL_FAILURE = "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def validate_run(run_number: int) -> dict:
    run = CYCLE / f"run{run_number}"
    pad_run = load(run / "pad-run.json")
    pad_variables = load(run / "pad-variables.json")
    artifact = load(run / "artifact.json")
    typed = load(run / "typed-transfer.json")
    legacy = load(run / "comparison.json")
    native = load(run / "native-styles.json")
    f6 = load(run / "f6-native.json")
    legacy_counts = legacy.get("failure_counts", {})
    native_counts = native.get("difference_attribute_counts", {})
    native_locations = native.get("difference_location_counts", {})
    result = run / "result.xlsx"
    work = run / "work.xlsx"
    checks = {
        "pad_terminal_ready": pad_run.get("status") == "PASS_TERMINAL_READY_NO_ERROR_OBSERVED",
        "pad_run_index": pad_run.get("run_index") == run_number,
        "pad_json_12_true": (
            pad_variables.get("status") == "PASS_12_OF_12_PAD_JSON_VALUE_AND_TYPE_MATCH"
            and pad_variables.get("counts") == {"true": 12, "false": 0, "total": 12}
        ),
        "artifact_preserved": artifact.get("status") == "PASS_ARTIFACT_PRESERVED",
        "result_sha": result.is_file() and sha256(result) == artifact.get("output_sha256"),
        "work_frozen": work.is_file() and sha256(work) == EXPECTED_WORK_SHA,
        "typed_transfer": typed.get("status") == "MATCH_FIXED_EX03_TEXT_NUMBER_SCOPE",
        "typed_mismatches_zero": not typed.get("mismatches"),
        "originals_unchanged": typed.get("originals_unchanged_by_verifier") is True,
        "legacy_fail_preserved": legacy.get("status") == "FAIL",
        "legacy_558": legacy_counts == EXPECTED_LEGACY_COUNTS and sum(legacy_counts.values()) == 558,
        "legacy_target_mismatches_zero": not legacy["checks"]["target_values_types_positions"]["mismatches"],
        "legacy_outside_mismatches_zero": not legacy["checks"]["outside_values_types_formulas"]["mismatches"],
        "effective_format_match": native.get("status") == "MATCH_EFFECTIVE_FORMAT",
        "effective_attribute_differences_zero": all(value == 0 for value in native_counts.values()),
        "effective_location_differences_zero": all(value == 0 for value in native_locations.values()),
        "f6_contract": f6.get("status") == "PASS_F6_SYSTEM_STRING_100_PERCENT_ORIGINAL_FORMAT_EMPTY_PREFIX_NO_FORMULA",
    }
    if not all(checks.values()):
        raise ValueError(
            f"Run{run_number} verification failed: "
            f"{[name for name, passed in checks.items() if not passed]}"
        )
    return {
        "checks": checks,
        "pad_run": pad_run,
        "pad_variables": pad_variables,
        "artifact": artifact,
        "typed": typed,
        "legacy": legacy,
        "native": native,
        "f6": f6,
    }


def main() -> int:
    final_paths = [
        CYCLE / "run2/verification.json",
        CYCLE / "run2/runtime-output-after-run2.xlsx",
        CYCLE / "protected-after.json",
        CYCLE / "acceptance-status.json",
        CYCLE / "verification.json",
        CYCLE / "review.md",
        CYCLE / "artifact-manifest.json",
    ]
    existing = [str(path) for path in final_paths if path.exists()]
    if existing:
        raise ValueError(f"Refusing to overwrite final evidence: {existing}")

    source = load(CYCLE / "source-identity.json")
    recopy = load(CYCLE / "pad-recopy.json")
    run1 = validate_run(1)
    run2 = validate_run(2)
    two_run = load(CYCLE / "two-run-semantic.json")
    formal = load(FORMAL / "acceptance-status.json")
    formal_plan = load(FORMAL / "plan.json")

    if not (
        source.get("all_three_identical") is True
        and source["sha256"]["copilot_download"] == EXPECTED_GENERATED_SHA
        and source["sha256"]["preserved_generated_robin"] == EXPECTED_GENERATED_SHA
        and source["sha256"]["safety_audit_recorded_target"] == EXPECTED_GENERATED_SHA
    ):
        raise ValueError("Downloaded, preserved, and safety-audit Robin identity failed")
    if not (
        recopy.get("result") == "PASS_UNMODIFIED_PAD_SAVE_RECOPY_BEFORE_RUN1"
        and recopy["comparison"]["lf_normalized_exact"] is True
        and recopy["observation"]["actions_after_paste"] == 110
        and recopy["observation"]["variables_after_paste"] == 45
    ):
        raise ValueError("PAD save/re-copy gate failed")
    if not (
        formal["generation"]["failure_code"] == FORMAL_FAILURE
        and formal["generation"]["delivery_contract"] == "FAIL"
        and formal["pad_import"]["dedicated_flow_opened"] is False
        and formal["runs"]["pad_runs_used"] == 0
        and formal["decision"]["accepted"] is False
    ):
        raise ValueError("Formal EX03-r11-G1 failure boundary changed")
    if not (
        two_run.get("status") == "MATCH"
        and two_run.get("semantic_equal") is True
        and two_run.get("checked_cells") == 480
    ):
        raise ValueError("Two-run semantic comparison failed")
    if not WORK.is_file() or sha256(WORK) != EXPECTED_WORK_SHA:
        raise ValueError("Runtime work.xlsx is not the frozen template")
    if not OUTPUT.is_file() or sha256(OUTPUT) != run2["artifact"]["output_sha256"]:
        raise ValueError("Runtime output does not match preserved Run2")

    run2_verification = {
        "schema_version": 1,
        "test_id": "EX03-R11-FILE-AUX1-RUN2",
        "decided_at": datetime.now(timezone.utc).isoformat(),
        "checks": run2["checks"],
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
            "failure_counts": run2["legacy"]["failure_counts"],
            "total": sum(run2["legacy"]["failure_counts"].values()),
        },
        "two_run_semantic_comparison": {
            "status": two_run["status"],
            "checked_cells": two_run["checked_cells"],
            "binary_sha_equal": two_run["binary_sha_equal"],
            "semantic_equal": two_run["semantic_equal"],
        },
        "status": "PASS_AUXILIARY_RUN2_AND_TWO_RUN_SEMANTIC_MATCH",
        "formal_ex03_r11_g1_result": f"{FORMAL_FAILURE}_PRESERVED",
    }
    write_json(CYCLE / "run2/verification.json", run2_verification)

    runtime_output_sha = sha256(OUTPUT)
    moved_output = CYCLE / "run2/runtime-output-after-run2.xlsx"
    shutil.move(str(OUTPUT), str(moved_output))
    if OUTPUT.exists() or sha256(moved_output) != runtime_output_sha:
        raise ValueError("Final Run2 runtime output move was not exact")
    if sha256(WORK) != EXPECTED_WORK_SHA:
        raise ValueError("Runtime work changed during final output preservation")

    protected_before_path = CYCLE / "protected-before.json"
    protected_before = load(protected_before_path)
    mismatches = []
    for item in protected_before["files"]:
        path = ROOT / item["path"]
        actual = sha256(path) if path.is_file() else None
        if actual != item["sha256"]:
            mismatches.append(
                {"path": item["path"], "before_sha256": item["sha256"], "after_sha256": actual}
            )
    protected_after = {
        "schema_version": 1,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "base_commit": protected_before["base_commit"],
        "protected_before_sha256": sha256(protected_before_path),
        "checked_file_count": len(protected_before["files"]),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "runtime_work_sha256": sha256(WORK),
        "runtime_work_matches_frozen_template": sha256(WORK) == EXPECTED_WORK_SHA,
        "runtime_output_absent_after_preservation": not OUTPUT.exists(),
        "status": "PASS_ALL_PROTECTED_FILES_UNCHANGED" if not mismatches else "FAIL",
    }
    if mismatches:
        raise ValueError(f"Protected files changed: {mismatches[:5]}")
    write_json(CYCLE / "protected-after.json", protected_after)

    f6_saved = run2["f6"]["saved_f6"]
    candidate = formal_plan["candidate"]
    submission = formal_plan["submission"]
    acceptance = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-FILE-AUX1",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "candidate": {
            "version": candidate["version"],
            "instruction_sha256": candidate["instruction_sha256"],
            "bundle_sha256": candidate["bundle_sha256"],
            "manifest_sha256": candidate["manifest_sha256"],
            "submitted_body_sha256": submission["body_sha256"],
            "generated_robin_sha256": EXPECTED_GENERATED_SHA,
        },
        "formal_ex03_r11_g1": {
            "normal_m365_send_count": formal["generation"]["normal_m365_send_count"],
            "generation_completed": formal["generation"]["completed"],
            "refusal": formal["generation"]["refusal"],
            "generated_file_static_safety": formal["generation"]["generated_file_static_safety"],
            "response_code_blocks": {
                "required": formal["generation"]["required_text_code_block_count"],
                "actual": formal["generation"]["actual_text_code_block_count"],
            },
            "delivery_contract": formal["generation"]["delivery_contract"],
            "failure_code": formal["generation"]["failure_code"],
            "formal_pad_runs": formal["runs"]["pad_runs_used"],
            "accepted": False,
            "status": "FORMAL_FAIL_PRESERVED",
        },
        "auxiliary_downloaded_file_validation": {
            "classification": "SEPARATELY_IDENTIFIED_AUXILIARY_NOT_FORMAL_ACCEPTANCE",
            "source_identity": "PASS_DOWNLOAD_PRESERVED_AUDIT_SHA_IDENTICAL",
            "pad_flow": {"name": recopy["flow_name"], "window_id": recopy["flow_window_id"]},
            "save_recopy": recopy["result"],
            "pad_run_count": 2,
            "run1": {
                "terminal": run1["pad_run"]["status"],
                "pad_json_type_matches": run1["pad_variables"]["counts"],
                "artifact_sha256": run1["artifact"]["output_sha256"],
                "typed_transfer": run1["typed"]["status"],
                "effective_format": run1["native"]["status"],
                "legacy_raw_difference_count": sum(run1["legacy"]["failure_counts"].values()),
                "f6": run1["f6"]["status"],
            },
            "run2": {
                "terminal": run2["pad_run"]["status"],
                "pad_json_type_matches": run2["pad_variables"]["counts"],
                "artifact_sha256": run2["artifact"]["output_sha256"],
                "typed_transfer": run2["typed"]["status"],
                "effective_format": run2["native"]["status"],
                "legacy_raw_difference_count": sum(run2["legacy"]["failure_counts"].values()),
                "f6": run2["f6"]["status"],
            },
            "two_run_semantic": {
                "status": two_run["status"],
                "checked_cells": two_run["checked_cells"],
                "binary_sha_equal": two_run["binary_sha_equal"],
                "semantic_equal": two_run["semantic_equal"],
            },
            "fixed_cell_checks": {
                "targets": 12,
                "target_mismatches_each_run": 0,
                "outside_cells": 468,
                "outside_mismatches_each_run": 0,
            },
            "f6_saved": f6_saved,
            "status": "PASS_AUXILIARY_DOWNLOADED_FILE_TWO_RUN_VALIDATION",
        },
        "preservation": protected_after,
        "remaining": {
            "formal_r11_delivery_contract_fail": True,
            "legacy_raw_558_fail_not_hidden": True,
            "existing_output_guard_live_path": "REMAINS_UNCONFIRMED",
            "unconfirmed_type_or_shape_generalization": False,
            "github_write": False,
        },
        "decision": {
            "formal_ex03_r11_g1_accepted": False,
            "auxiliary_validation_passed": True,
            "issue38_closed_by_this_auxiliary": False,
            "reason": (
                "The downloaded file independently passed the dedicated two-run PAD path, "
                "but the fixed formal r11 response delivery contract had already failed; "
                "auxiliary success cannot replace that failure."
            ),
        },
    }
    write_json(CYCLE / "acceptance-status.json", acceptance)

    verification = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-FILE-AUX1",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "gates": {
            "source_sha_identity": True,
            "unmodified_pad_save_recopy": True,
            "run1_terminal_and_all_fixed_gates": True,
            "run1_artifact_preserved_before_run2": True,
            "run2_terminal_and_all_fixed_gates": True,
            "two_run_semantic_match": True,
            "protected_files_unchanged": True,
            "runtime_output_absent_after_preservation": True,
        },
        "diagnostics": {
            "legacy_raw_status": "FAIL",
            "legacy_raw_difference_count_each_run": 558,
            "excel_effective_difference_count_each_run": 0,
        },
        "formal_boundary": {
            "ex03_r11_g1_failure_code": FORMAL_FAILURE,
            "formal_acceptance": False,
            "auxiliary_acceptance": True,
        },
        "status": "PASS_AUXILIARY_ONLY_FORMAL_FAIL_PRESERVED",
    }
    write_json(CYCLE / "verification.json", verification)

    review = f"""# EX03-r11 downloaded-file auxiliary PAD validation

## Decision

- Formal `EX03-r11-G1`: **NOT ACCEPTED**. Its one normal-M365 response delivered zero of the one required text code blocks, so `{FORMAL_FAILURE}` remains unchanged and its formal PAD count remains 0.
- Separately identified downloaded-file auxiliary path: **PASS** for the fixed EX03 text/number case only. This does not offset the formal delivery-contract failure and does not close Issue #38.

## Fixed identity

- Version: `{candidate['version']}`
- Instruction SHA-256: `{candidate['instruction_sha256']}`
- Bundle SHA-256: `{candidate['bundle_sha256']}`
- Manifest SHA-256: `{candidate['manifest_sha256']}`
- Submitted body SHA-256: `{submission['body_sha256']}`
- Copilot downloaded / preserved / safety-audit target Robin SHA-256: `{EXPECTED_GENERATED_SHA}` (all identical)
- PAD flow: `{recopy['flow_name']}` (window `{recopy['flow_window_id']}`, Power Fx OFF), 110 actions and 45 flow variables
- Save/re-copy: LF-normalized exact match; no generated Robin repair

## Two PAD runs

| Gate | Run1 | Run2 |
| --- | --- | --- |
| Terminal READY, no designer error | PASS | PASS |
| PAD JSON value-and-type flags | 12 True / 0 False | 12 True / 0 False |
| Fixed target values/types/positions | 12/12, mismatch 0 | 12/12, mismatch 0 |
| Outside values/types/formulas | 468 checked, mismatch 0 | 468 checked, mismatch 0 |
| Excel-effective format/dimensions | 480 cells + 48 rows + 30 columns, difference 0 | same, difference 0 |
| Legacy raw comparator | FAIL 558 preserved (480 styles, 48 rows, 30 columns) | same |
| Artifact SHA-256 | `{run1['artifact']['output_sha256']}` | `{run2['artifact']['output_sha256']}` |

The two XLSX archives have different binary SHA values, which is expected for separately saved ZIP packages, while the full 480-cell semantic comparison is `MATCH`.

## F6 fixed text edge case

Both runs independently read saved/reopened `追記先!F6` as:

- value: `100%`
- .NET type: `System.String`
- number format: `G/標準` (unchanged from the template)
- prefix character: empty
- formula: none

## Preservation and remaining work

- All {protected_after['checked_file_count']} pre-existing tracked files match the pre-run SHA snapshot.
- Runtime `work.xlsx` remains `{EXPECTED_WORK_SHA}` and the fixed output path is absent after recoverable evidence preservation.
- Existing-output guard live behavior remains unconfirmed.
- The old raw 558-result is retained and is not relabeled as PASS; the separate Excel-effective comparison records zero actual format/dimension changes.
- No type or shape beyond the fixed EX03 text/number mapping is generalized.
- No GitHub write was performed.
"""
    with (CYCLE / "review.md").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(review)

    manifest_entries = []
    manifest_path = CYCLE / "artifact-manifest.json"
    for path in sorted(CYCLE.rglob("*")):
        if path.is_file() and path != manifest_path:
            manifest_entries.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
            )
    write_json(
        manifest_path,
        {
            "schema_version": 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "cycle_id": "EX03-R11-FILE-AUX1",
            "file_count": len(manifest_entries),
            "files": manifest_entries,
        },
    )

    print(
        json.dumps(
            {
                "status": verification["status"],
                "formal_failure": FORMAL_FAILURE,
                "auxiliary_runs": 2,
                "run1_sha256": run1["artifact"]["output_sha256"],
                "run2_sha256": run2["artifact"]["output_sha256"],
                "semantic_equal": two_run["semantic_equal"],
                "legacy_raw_differences_each_run": 558,
                "effective_differences_each_run": 0,
                "protected_mismatches": len(mismatches),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
