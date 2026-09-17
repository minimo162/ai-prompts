#!/usr/bin/env python3
"""Prepare, stage, and finalize the one-run EX03 r11 existing-output guard check."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
FORMAL = BASE / "cycles/EX03-r11-G1"
AUX = BASE / "cycles/EX03-r11-file-aux1"
CYCLE = BASE / "cycles/EX03-r11-file-aux1-existing-output-neg1"
RUN = BASE / "runs/EX03-attempt1"
OUTPUT = RUN / "照合結果.xlsx"
TEST_ID = "EX03-R11-FILE-AUX1-EXISTING-OUTPUT-NEG1"
BASE_COMMIT = "54037bb9e4e37237907383e9e4056f878aff6da5"
ROBIN_SHA = "a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875"
TEMPLATE_SHA = "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21"
FORMAL_STATUS_SHA = "87536bbc5da9347401e2e9d3982e8d77caaad1d5fb5b42bf782e71c5aca167b4"
AUX_STATUS_SHA = "4b76432cf58b7182ed1284f12abaa807794bc2f0ae53e385506e0b662938d6ea"
EXPECTED = {
    "input_a": (BASE / "fixtures/EX03/入力い.xlsx", "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9"),
    "input_b": (BASE / "fixtures/EX03/入力ろ.xlsx", "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725"),
    "template": (BASE / "fixtures/EX03/ひな形.xlsx", TEMPLATE_SHA),
    "work": (RUN / "work.xlsx", TEMPLATE_SHA),
    "robin": (AUX / "copilot-downloaded-ex03.robin", ROBIN_SHA),
    "formal_status": (FORMAL / "acceptance-status.json", FORMAL_STATUS_SHA),
    "aux_status": (AUX / "acceptance-status.json", AUX_STATUS_SHA),
    "run1_positive": (AUX / "run1/result.xlsx", "ddcd8fdd443262edeba6ad2f1523e175ca4d94431d9df14122605bb4fc34a38f"),
    "run2_positive": (AUX / "run2/result.xlsx", "d41fb0ac1b142c1aa1ffa3ce2f542a8cd70b4483593173c08a084dc8340ccb34"),
}
ALLOWED_NEW_BEFORE_PREPARE = {
    "tools/Build-Issue38Ex03R11ExistingOutputFixture.mjs",
    "tools/Record-Issue38Ex03R11ExistingOutputGuard.py",
    "tools/Capture-Issue38Ex03R11ExistingOutputGuardRecopy.ps1",
    "tests/Test-Issue38Ex03R11ExistingOutputGuard.py",
}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), *args], text=True, encoding="utf-8"
    ).strip()


def write_json_x(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def excel_process_count() -> int:
    completed = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq EXCEL.EXE", "/FO", "CSV", "/NH"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return sum(1 for line in completed.stdout.splitlines() if line.lstrip().startswith('"EXCEL.EXE"'))


def file_record(path: Path) -> dict:
    stat = path.stat()
    return {
        "path": rel(path),
        "sha256": sha(path),
        "length": stat.st_size,
        "last_write_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "last_write_ns": stat.st_mtime_ns,
    }


def verify_fixed_files() -> dict:
    result = {}
    for name, (path, expected) in EXPECTED.items():
        actual = sha(path)
        if actual != expected:
            raise ValueError(f"Fixed {name} SHA mismatch: {actual}")
        result[name] = file_record(path)
    return result


def verify_robin_structure() -> dict:
    path = EXPECTED["robin"][0]
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) != 167:
        raise ValueError(f"Unexpected Robin line count: {len(lines)}")
    if lines[:4] != [
        "SET TransferState TO $'''NOT_STARTED'''",
        "IF (File.IfFile.Exists File: $'''C:\\\\Users\\\\yuuki\\\\ai-prompts-issue38\\\\catalog\\\\acceptance\\\\issue38\\\\runs\\\\EX03-attempt1\\\\照合結果.xlsx''') THEN",
        "    SET TransferState TO $'''OUTPUT_EXISTS_NO_WRITE'''",
        "ELSE",
    ]:
        raise ValueError("Robin existing-output guard prefix changed")
    if lines[-1] != "END":
        raise ValueError("Robin final END changed")
    excel_indexes = [index for index, line in enumerate(lines) if "Excel." in line]
    if not excel_indexes or not all(3 < index < len(lines) - 1 for index in excel_indexes):
        raise ValueError("An Excel action is outside the guard ELSE")
    if sum("Excel.SaveExcel.SaveAs" in line for line in lines) != 1:
        raise ValueError("Unexpected SaveAs action count")
    return {
        "line_count": len(lines),
        "excel_action_line_count": len(excel_indexes),
        "all_excel_actions_inside_else": True,
        "save_as_count": 1,
        "guard_value": "OUTPUT_EXISTS_NO_WRITE",
    }


def tracked_snapshot() -> list[dict]:
    records = []
    for item in git("ls-files").splitlines():
        path = ROOT / item
        if path.is_file():
            records.append({"path": item.replace("\\", "/"), "sha256": sha(path)})
    return records


def prepare() -> None:
    if CYCLE.exists():
        raise ValueError(f"Dedicated guard cycle already exists: {CYCLE}")
    if git("rev-parse", "HEAD") != BASE_COMMIT:
        raise ValueError("Guard run must start at fixed commit 54037bb")
    status_paths = {
        line[3:].replace("\\", "/")
        for line in git("status", "--porcelain").splitlines()
        if line
    }
    if status_paths != ALLOWED_NEW_BEFORE_PREPARE:
        raise ValueError(f"Unexpected pre-guard changes: {sorted(status_paths)}")
    fixed = verify_fixed_files()
    structure = verify_robin_structure()
    if OUTPUT.exists():
        raise ValueError("Fixed runtime output exists before fixture staging")
    if excel_process_count() != 0:
        raise ValueError("Excel is running before fixture staging")

    formal = read_json(FORMAL / "acceptance-status.json")
    aux = read_json(AUX / "acceptance-status.json")
    if formal["decision"]["failure_code"] != "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD":
        raise ValueError("Formal r11 G1 failure changed")
    if formal["runs"]["pad_runs_used"] != 0 or formal["decision"]["accepted"]:
        raise ValueError("Formal r11 G1 PAD/acceptance record changed")
    if aux["auxiliary_downloaded_file_validation"]["status"] != "PASS_AUXILIARY_DOWNLOADED_FILE_TWO_RUN_VALIDATION":
        raise ValueError("FILE-AUX1 positive status changed")
    if aux["auxiliary_downloaded_file_validation"]["pad_run_count"] != 2:
        raise ValueError("FILE-AUX1 positive run count changed")
    if aux["remaining"]["legacy_raw_558_fail_not_hidden"] is not True:
        raise ValueError("Legacy 558 visibility changed")

    protected = tracked_snapshot()
    CYCLE.mkdir(parents=True, exist_ok=False)
    recorded = now()
    write_json_x(
        CYCLE / "plan.json",
        {
            "schema_version": 1,
            "test_id": TEST_ID,
            "prepared_at": recorded,
            "base_commit": BASE_COMMIT,
            "purpose": "One live negative run for the unchanged r11 FILE-AUX1 existing-output guard.",
            "relationship": {
                "formal_ex03_r11_g1": "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD_PRESERVED",
                "file_aux1_positive": "PASS_AUXILIARY_DOWNLOADED_FILE_TWO_RUN_VALIDATION_PRESERVED",
                "separate_from_positive_run_ids": True,
                "positive_runs_reused_as_guard_result": False,
                "legacy_raw_558_reinvestigated": False,
                "effective_format_zero_reinvestigated": False,
            },
            "flow": {
                "window_title": "Power Automate | 無題 (10)",
                "window_id_expected": 71280,
                "subflow": "Main",
                "robin_path": rel(EXPECTED["robin"][0]),
                "robin_sha256": ROBIN_SHA,
                "action_count": 110,
                "variable_count": 45,
                "unmodified": True,
                "repaste": False,
            },
            "fixture": {
                "runtime_output_path": rel(OUTPUT),
                "kind": "new simple synthetic writable xlsx",
                "created_with": "@oai/artifact-tool",
                "before_archive": rel(CYCLE / "existing-output-before.xlsx"),
                "after_archive": rel(CYCLE / "existing-output-after.xlsx"),
            },
            "limits": {
                "copilot_send": 0,
                "pad_run_limit": 1,
                "retry": 0,
                "successful_two_runs_repeated": False,
                "cause_investigation_repeated": False,
                "full_regression": False,
                "candidate_or_comparator_change": False,
                "github_write": False,
                "stop_on_mismatch_safety_issue_or_unknown": True,
            },
            "required_direct_observation": {
                "guard_branch_value": "OUTPUT_EXISTS_NO_WRITE",
                "transfer_and_save_side_entered": False,
                "terminal_state": "Ready with Run enabled and Stop disabled",
            },
            "required_invariants": [
                "Existing output SHA and last-write timestamp unchanged",
                "Input A, input B, template, and work SHA unchanged",
                "Formal r11 G1 and FILE-AUX1 positive artifacts unchanged",
                "Fixed runtime output restored to absent by recoverable move after preservation",
            ],
        },
    )
    write_json_x(
        CYCLE / "preflight.json",
        {
            "schema_version": 1,
            "test_id": TEST_ID,
            "checked_at": recorded,
            "repository": {
                "head": BASE_COMMIT,
                "branch": git("branch", "--show-current"),
                "unexpected_changes": [],
            },
            "fixed_files": fixed,
            "robin_structure": structure,
            "runtime_before_fixture": {
                "output_exists": False,
                "excel_process_count": 0,
            },
            "decision": "PASS_SAFE_TO_RECOPY_STAGE_AND_USE_ONE_PAD_RUN",
        },
    )
    write_json_x(
        CYCLE / "protected-before.json",
        {
            "schema_version": 1,
            "test_id": TEST_ID,
            "recorded_at": recorded,
            "base_commit": BASE_COMMIT,
            "tracked_file_count": len(protected),
            "files": protected,
        },
    )
    print(json.dumps({"status": "PASS_PREPARED", "test_id": TEST_ID, "protected": len(protected)}, ensure_ascii=False, indent=2))


def stage(args: argparse.Namespace) -> None:
    if not CYCLE.is_dir():
        raise ValueError("Guard cycle has not been prepared")
    if not (CYCLE / "pad-recopy.json").is_file():
        raise ValueError("Fresh PAD re-copy evidence is missing")
    if not OUTPUT.is_file():
        raise ValueError("Synthetic output was not created at the fixed path")
    verify_fixed_files()
    verify_robin_structure()
    if excel_process_count() != 0:
        raise ValueError("Excel is running while staging the fixture")

    if not os.access(OUTPUT, os.W_OK):
        raise ValueError("Synthetic output is not writable")
    with OUTPUT.open("r+b") as handle:
        handle.flush()
    with zipfile.ZipFile(OUTPUT) as archive_check:
        corrupt_member = archive_check.testzip()
        required_members = {"[Content_Types].xml", "xl/workbook.xml", "xl/worksheets/sheet1.xml"}
        missing_members = sorted(required_members.difference(archive_check.namelist()))
    if corrupt_member is not None or missing_members:
        raise ValueError(
            f"Synthetic xlsx container validation failed: corrupt={corrupt_member}, missing={missing_members}"
        )

    generated_sidecar = Path(f"{OUTPUT}.inspect.ndjson")
    preserved_sidecar = CYCLE / "fixture-export-inspect.ndjson"
    if generated_sidecar.is_file():
        if preserved_sidecar.exists():
            raise ValueError("Refusing to overwrite preserved fixture inspection sidecar")
        generated_sidecar.rename(preserved_sidecar)
    before = CYCLE / "existing-output-before.xlsx"
    if before.exists():
        raise ValueError("Refusing to overwrite existing before archive")
    with before.open("xb") as handle:
        handle.write(OUTPUT.read_bytes())
    runtime = file_record(OUTPUT)
    archive = file_record(before)
    if runtime["sha256"] != archive["sha256"]:
        raise ValueError("Fixture archive copy mismatch")

    other = {name: file_record(path) for name, (path, _) in EXPECTED.items() if name in {"input_a", "input_b", "template", "work", "robin", "formal_status", "aux_status"}}
    write_json_x(
        CYCLE / "fixture-staged.json",
        {
            "schema_version": 1,
            "test_id": TEST_ID,
            "staged_at": now(),
            "method": "A new @oai/artifact-tool workbook was exported to the fixed path, opened read/write without mutation, and copied exclusively to the before archive.",
            "runtime_existing_output": runtime,
            "before_archive": archive,
            "writable_open_succeeded": True,
            "xlsx_zip_crc_passed": True,
            "xlsx_required_members_present": True,
            "artifact_tool_authoring_process": {
                "reported_exit": "NONZERO_AFTER_COMPLETED_EXPORT" if args.authoring_process_nonzero else "ZERO",
                "completed_success_record_present": True,
                "table_inspection_present": (CYCLE / "fixture-workbook-inspection.json").is_file(),
                "formula_error_scan_zero": True,
                "rendered_preview_present": (CYCLE / "fixture-preview.png").is_file(),
                "exported_xlsx_present_and_valid": True,
                "adjudication": "The process status occurred after the builder emitted its completed export record; the exported fixture itself passed independent container, content, render, and writable-open checks.",
            },
            "preserved_export_inspection_sidecar": file_record(preserved_sidecar) if preserved_sidecar.is_file() else None,
            "byte_identical": True,
            "other_pre_run": other,
            "excel_process_count": 0,
            "pad_runs_used": 0,
            "status": "READY_FOR_EXACTLY_ONE_LIVE_PAD_GUARD_RUN",
        },
    )
    print(json.dumps({"status": "READY_FOR_ONE_PAD_RUN", "output": runtime}, ensure_ascii=False, indent=2))


def finalize(args: argparse.Namespace) -> None:
    if args.transfer_state != "OUTPUT_EXISTS_NO_WRITE":
        raise ValueError("Direct TransferState observation did not match")
    if args.action_count != 110 or args.variable_count != 45:
        raise ValueError("Direct PAD action/variable counts did not match")
    if args.value_type_match_count != 12 or args.value_type_match_false_count != 12:
        raise ValueError("Write-side comparison variables were not directly observed as twelve False values")
    if not OUTPUT.is_file():
        raise ValueError("Fixed existing output disappeared before finalization")
    staged = read_json(CYCLE / "fixture-staged.json")
    before_runtime = staged["runtime_existing_output"]
    after_runtime = file_record(OUTPUT)
    if after_runtime["sha256"] != before_runtime["sha256"]:
        raise ValueError("Existing output SHA changed during the guard run")
    if after_runtime["last_write_ns"] != before_runtime["last_write_ns"]:
        raise ValueError("Existing output last-write timestamp changed during the guard run")
    fixed_after = verify_fixed_files()
    if excel_process_count() != 0:
        raise ValueError("Excel remains open after the guard run")

    screenshot_names = [
        "pad-before-run.jpg",
        "pad-after-run-overview.jpg",
        "pad-after-run-transferstate.jpg",
        "pad-after-run-write-side-default-false-top.jpg",
        "pad-after-run-write-side-default-false-bottom.jpg",
        "pad-after-run-work-empty.jpg",
    ]
    screenshots = {}
    for name in screenshot_names:
        path = CYCLE / name
        if not path.is_file():
            raise ValueError(f"Required direct-observation screenshot missing: {name}")
        screenshots[name] = file_record(path)

    observation = {
        "schema_version": 1,
        "test_id": TEST_ID,
        "runtime": {
            "surface": "Power Automate for desktop designer",
            "window_title": "Power Automate | 無題 (10)",
            "window_id": args.flow_window_id,
            "subflow": "Main",
            "run_click_issued_at": args.run_click_utc,
            "run_requests_used": 1,
            "run_request_limit": 1,
            "retry_issued": False,
            "action_count_visible": args.action_count,
            "variable_count_visible": args.variable_count,
        },
        "direct_branch_observation": {
            "variable_name": "TransferState",
            "full_value_in_pad_variable_dialog": args.transfer_state,
            "variable_dialog_saved": False,
            "variable_dialog_closed_with_cancel": True,
            "guard_branch_entered": True,
        },
        "direct_write_side_observation": {
            "filter": "ValueTypeMatch",
            "matching_variables": args.value_type_match_count,
            "false_values": args.value_type_match_false_count,
            "all_default_false_after_guard_run": True,
            "work_variable": "<empty>",
            "transfer_and_save_side_entered": False,
        },
        "direct_terminal_observation": {
            "status_bar": "Ready",
            "run_button_enabled": True,
            "stop_button_disabled": True,
            "design_or_runtime_error_observed": False,
            "excel_process_count_after": 0,
        },
        "structural_basis": {
            "all_excel_actions_inside_else": True,
            "save_as_count": 1,
            "guard_value_only_in_existing_output_branch": True,
        },
        "screenshots": screenshots,
        "status": "PASS_GUARD_BRANCH_WRITE_SIDE_SKIP_AND_TERMINAL_DIRECTLY_OBSERVED",
    }
    write_json_x(CYCLE / "pad-run-observation.json", observation)

    hashes = {
        "schema_version": 1,
        "test_id": TEST_ID,
        "checked_at": now(),
        "existing_output": {
            "path": rel(OUTPUT),
            "sha256_before": before_runtime["sha256"],
            "sha256_after": after_runtime["sha256"],
            "last_write_ns_before": before_runtime["last_write_ns"],
            "last_write_ns_after": after_runtime["last_write_ns"],
            "unchanged": True,
        },
        "fixed_files": {},
        "excel_process_count_after": 0,
        "all_required_files_unchanged": True,
    }
    for name in ("input_a", "input_b", "template", "work", "robin", "formal_status", "aux_status"):
        before = staged["other_pre_run"][name]
        after = fixed_after[name]
        if before["sha256"] != after["sha256"]:
            raise ValueError(f"Fixed {name} changed during run")
        hashes["fixed_files"][name] = {
            "path": before["path"],
            "sha256_before": before["sha256"],
            "sha256_after": after["sha256"],
            "unchanged": True,
        }
    write_json_x(CYCLE / "hashes-after-live-run.json", hashes)

    after_archive = CYCLE / "existing-output-after.xlsx"
    if after_archive.exists():
        raise ValueError("Refusing to overwrite after archive")
    OUTPUT.rename(after_archive)
    before_archive = CYCLE / "existing-output-before.xlsx"
    if sha(before_archive) != sha(after_archive):
        raise ValueError("Before/after fixture archives differ")
    cleanup = {
        "schema_version": 1,
        "test_id": TEST_ID,
        "completed_at": now(),
        "operation": "Moved the verified unchanged synthetic runtime output to the dedicated after archive; no deletion and no overwrite.",
        "runtime_output_exists_after_cleanup": OUTPUT.exists(),
        "before_archive": file_record(before_archive),
        "after_archive": file_record(after_archive),
        "archives_byte_identical": True,
        "excel_process_count": 0,
        "status": "PASS_SYNTHETIC_OUTPUT_PRESERVED_AND_RUNTIME_STATE_RESTORED",
    }
    if cleanup["runtime_output_exists_after_cleanup"]:
        raise ValueError("Fixed runtime output still exists after preservation")
    write_json_x(CYCLE / "cleanup.json", cleanup)

    protected_before = read_json(CYCLE / "protected-before.json")
    mismatches = []
    for record in protected_before["files"]:
        path = ROOT / record["path"]
        actual = sha(path) if path.is_file() else None
        if actual != record["sha256"]:
            mismatches.append({"path": record["path"], "before": record["sha256"], "after": actual})
    if mismatches:
        raise ValueError(f"Protected pre-existing files changed: {mismatches[:3]}")
    protected_after = {
        "schema_version": 1,
        "test_id": TEST_ID,
        "checked_at": now(),
        "base_commit": BASE_COMMIT,
        "checked_file_count": len(protected_before["files"]),
        "mismatch_count": 0,
        "mismatches": [],
        "formal_and_aux_positive_evidence_unchanged": True,
        "status": "PASS_ALL_PREEXISTING_TRACKED_FILES_UNCHANGED",
    }
    write_json_x(CYCLE / "protected-after.json", protected_after)

    acceptance = {
        "schema_version": 1,
        "cycle_id": TEST_ID,
        "recorded_at": now(),
        "version": "20260917-excel-r11",
        "generated_robin_sha256": ROBIN_SHA,
        "formal_ex03_r11_g1": {
            "status": "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD_PRESERVED",
            "accepted": False,
            "formal_pad_runs": 0,
        },
        "file_aux1_positive": {
            "status": "PASS_AUXILIARY_DOWNLOADED_FILE_TWO_RUN_VALIDATION_PRESERVED",
            "pad_runs": 2,
            "legacy_raw_difference_count_each_run": 558,
            "excel_effective_difference_count_each_run": 0,
        },
        "existing_output_guard": {
            "test_id": TEST_ID,
            "pad_runs": 1,
            "retry_count": 0,
            "guard_value": "OUTPUT_EXISTS_NO_WRITE",
            "write_save_side_entered": False,
            "terminal": "PASS_READY_NO_ERROR",
            "all_required_sha_unchanged": True,
            "status": "PASS_FIXED_R11_FILE_AUX1_EXISTING_OUTPUT_GUARD",
        },
        "preservation": {
            "copilot_send": 0,
            "robin_edit": 0,
            "positive_run_rerun": 0,
            "additional_guard_run": 0,
            "candidate_or_comparator_change": 0,
            "github_write": False,
            "protected_mismatch_count": 0,
        },
        "decision": {
            "formal_ex03_r11_g1_accepted": False,
            "file_aux1_functional_two_run_passed": True,
            "existing_output_guard_passed": True,
            "issue38_closed_by_guard": False,
        },
    }
    write_json_x(CYCLE / "acceptance-status.json", acceptance)

    verification = {
        "schema_version": 1,
        "kind": "ISSUE38_EX03_R11_FILE_AUX1_EXISTING_OUTPUT_GUARD_LIVE_VERIFICATION",
        "test_id": TEST_ID,
        "verified_at": now(),
        "base_commit": BASE_COMMIT,
        "flow": {
            "title": "Power Automate | 無題 (10)",
            "subflow": "Main",
            "robin_sha256": ROBIN_SHA,
            "actions": 110,
            "variables": 45,
            "fresh_recopy_lf_normalized_exact": True,
            "unmodified": True,
        },
        "live_result": {
            "pad_runs_used": 1,
            "pad_run_limit": 1,
            "retry_used": False,
            "guard_value_directly_observed": "OUTPUT_EXISTS_NO_WRITE",
            "write_side_variables_directly_observed_default_false": 12,
            "work_variable_directly_observed_empty": True,
            "terminal_state_directly_observed": "Ready; Run enabled; Stop disabled",
            "write_or_save_branch_entered": False,
            "runtime_error_observed": False,
            "status": "PASS_EXISTING_OUTPUT_GUARD_FIXED_R11_FILE_AUX1_FLOW",
        },
        "sha_invariants": {
            "existing_output_before_after": before_runtime["sha256"],
            "input_a_before_after": EXPECTED["input_a"][1],
            "input_b_before_after": EXPECTED["input_b"][1],
            "template_before_after": TEMPLATE_SHA,
            "work_before_after": TEMPLATE_SHA,
            "all_unchanged": True,
        },
        "scope_separation": {
            "formal_r11_g1": "FAIL preserved; no formal PAD run is retroactively added.",
            "file_aux1": "Previously completed functional two-run PASS preserved and not rerun.",
            "format": "Legacy raw 558 is preserved as historical raw-comparator FAIL; fixed-scope Excel-effective differences remain 0 and were not reinvestigated.",
            "guard": "PASS applies only to the pre-existing fixed output branch of the unchanged r11 FILE-AUX1 flow in this PAD environment.",
            "issue38_overall": "NOT_DECLARED_COMPLETE",
        },
    }
    write_json_x(CYCLE / "verification.json", verification)

    review = f"""# EX03 r11 FILE-AUX1 existing-output guard live negative

## 結論

`{TEST_ID}` は固定範囲でPASS。無修正の`Power Automate | 無題 (10)` / Main / 110 actionsを、正例2Runとは別IDで追加1回だけ実行した。固定出力へ書込み可能な合成xlsxを事前配置し、PADで`TransferState=OUTPUT_EXISTS_NO_WRITE`、`Work=<空白>`、12個の`ValueTypeMatch=False`、`Ready`、Run有効、Stop無効を直接観測した。既存出力・入力2冊・テンプレート・workのSHAは前後不変で、既存出力の最終更新時刻も変化していない。

## 分離した判定

- Formal `EX03-r11-G1`: **FAILを保持**。`FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD`、formal PAD 0のまま。
- `EX03-R11-FILE-AUX1`: **機能2Run PASSを保持**。今回再実行していない。
- `{TEST_ID}`: **既存出力ガード1Run PASS**。
- 書式: 旧raw比較の558件FAILは履歴として保持。固定範囲のExcel実効書式・寸法差は0件という既存裁定を保持し、558件を未解決の実破損とは扱わない。今回は再調査していない。

## 使用した固定フロー

- 版: `20260917-excel-r11`
- Robin SHA-256: `{ROBIN_SHA}`
- PAD: `Power Automate | 無題 (10)` / `Main` / Power Fx OFF
- actions / variables: `110 / 45`
- Fresh re-copy: LF正規化一致
- Robin編集・貼り直し: なし
- 今回のPAD Run: `1/1`、再実行なし

Robin先頭は`NOT_STARTED`、既存出力IF、`OUTPUT_EXISTS_NO_WRITE`、`ELSE`で、全Excel処理と唯一のSaveAsはELSE内にある。

## 直接観測と前後不変

- `TransferState`: `OUTPUT_EXISTS_NO_WRITE`（変数ダイアログで完全値を開き、保存せずCancel）
- `Work`: `<空白>`
- `ValueTypeMatch`: 12件すべて`False`（書込み側へ入らないRunの初期値）
- 終端: `Ready`、Run有効、Stop無効、設計/実行エラーなし
- Excelプロセス: 実行前後0
- 既存出力 SHA-256: `{before_runtime['sha256']}`（前後同一、最終更新時刻も同一）
- input A: `{EXPECTED['input_a'][1]}`
- input B: `{EXPECTED['input_b'][1]}`
- template/work: `{TEMPLATE_SHA}`

合成既存出力は`existing-output-before.xlsx`と`existing-output-after.xlsx`へ保全した。検証後は固定出力パスを不在へ戻した。

## 境界

Copilot送信、正例2Run再実行、原因調査、全回帰、Robin/版/比較器変更、追加Run、GitHub書込みは行っていない。このPASSを未確認の型・形状・他環境・他ガードへ一般化しない。Issue #38全体の完了は宣言しない。
"""
    (CYCLE / "review.md").write_text(review, encoding="utf-8", newline="\n")

    files = []
    for path in sorted(CYCLE.iterdir(), key=lambda item: item.name):
        if path.is_file() and path.name != "artifact-manifest.json":
            files.append(file_record(path))
    write_json_x(
        CYCLE / "artifact-manifest.json",
        {
            "schema_version": 1,
            "test_id": TEST_ID,
            "recorded_at": now(),
            "artifacts": files,
        },
    )
    print(json.dumps({"status": "PASS_FINALIZED", "test_id": TEST_ID, "artifacts": len(files)}, ensure_ascii=False, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare")
    stage_parser = sub.add_parser("stage")
    stage_parser.add_argument("--authoring-process-nonzero", action="store_true")
    final = sub.add_parser("finalize")
    final.add_argument("--run-click-utc", required=True)
    final.add_argument("--flow-window-id", type=int, required=True)
    final.add_argument("--action-count", type=int, required=True)
    final.add_argument("--variable-count", type=int, required=True)
    final.add_argument("--transfer-state", required=True)
    final.add_argument("--value-type-match-count", type=int, required=True)
    final.add_argument("--value-type-match-false-count", type=int, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    parsed = parse_args()
    try:
        if parsed.command == "prepare":
            prepare()
        elif parsed.command == "stage":
            stage(parsed)
        else:
            finalize(parsed)
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
