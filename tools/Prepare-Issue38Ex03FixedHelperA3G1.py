#!/usr/bin/env python3
"""Prepare the one-send, at-most-two-run EX03 fixed-helper A3-G1 cycle."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CANDIDATE = ROOT / "copilot/versions/20260918-excel-r12-fixed-helper-a3"
CYCLE = BASE / "cycles/EX03-r12-fixed-helper-A3-G1"
PROBE = BASE / "probes/ex03-r12-fixed-helper"
T1 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
T2 = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2"
RUNTIME = T1 / "runtime"

HELPER = PROBE / "EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = T1 / "invocation.json"
LAUNCHER = T1 / "launcher.ps1"
REQUEST = BASE / "requests/EX03.txt"
SPEC = BASE / "spec.json"
EXPECTED = BASE / "expected.json"
TEMPLATE = BASE / "fixtures/EX03/ひな形.xlsx"
INPUT1 = BASE / "fixtures/EX03/入力い.xlsx"
INPUT2 = BASE / "fixtures/EX03/入力ろ.xlsx"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"

INSTRUCTION = CANDIDATE / "agent-instructions.txt"
SEND_CONDITIONS = CANDIDATE / "send-conditions.txt"
SUBMITTED_BODY = CANDIDATE / "submitted-body.txt"
BUNDLE = CANDIDATE / "knowledge/PAD-Robin-Fixed-Helper-A3-Bundle.txt"
MANIFEST = CANDIDATE / "manifest.json"
RULES = CANDIDATE / "assembly-rules.json"
DELTA = CANDIDATE / "instruction-delta.json"
COVERAGE = CANDIDATE / "COVERAGE.md"
PLACEMENT = CANDIDATE / "PLACEMENT.md"
NON_LIVE = CANDIDATE / "non-live-verification.json"

CYCLE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A3-G1"
ROUTE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A3"
CANDIDATE_ID = "20260918-excel-r12-fixed-helper-a3"
BASE_COMMIT = "d28c68966f9b7e7209aad397c793f16a4f6bc08f"
EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'

EXPECTED_SHA256 = {
    "instruction": "87d4fad6445be8371bfcad9d35d2ce8c384758714c7d48e0232a1ce60ab89d98",
    "send_conditions": "ab93331cce8902e8e0bf4c9182a1b783012a08a6b83b7812da1b5ef77014fed6",
    "submitted_body": "eae9de79a8c0ec4796ee90b3dd9e41b35c72490c483d7f15723891b0441142c3",
    "bundle": "50c60d9533b9afb4d698416d6f9bf0b30040dee69206cf1734dea565f740b0c4",
    "manifest": "fc8d62994e21361deea300e697167ad410c4567ed181820dd86d64a99d8f8fe4",
    "rules": "c43bcce32095c3a4ba3c565d3902c26f11dee66be3cb0354ff4610c37689ed0d",
    "delta": "be46ee0dac1a65cbdb72cad37ccd1327af1d48f87ab6dcbfd0655695b30a472e",
    "coverage": "8080dc541d261deeb48eb4902d20c9cb0e55c144bd235d1531524f16b6879b4b",
    "placement": "981030804fbaab8179047b62584ae21091300f50784be03c0bc65f49c38f7c08",
    "non_live": "2e507cccbc30830a5699993a5261db803a55a96c13149a818c8a8ebad4ae8ccb",
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "92ea864a7e43cec61b4215592a3bae9b8b31109af4e18d3ff0a79dcb15fc5ad6",
    "launcher": "1e9750385455999460e9b1dce754e2a649d4837ae1939cd444376fc360a25ee1",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
    "work": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> int:
    if CYCLE.exists():
        raise FileExistsError(f"A3-G1 cycle already exists: {CYCLE}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != BASE_COMMIT:
        raise ValueError(f"A3-G1 must start at {BASE_COMMIT}, observed {head}")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True):
        expected_new = "?? tools/Prepare-Issue38Ex03FixedHelperA3G1.py\n"
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
        if status.replace("\\", "/") != expected_new:
            raise ValueError(f"Unexpected preflight worktree changes: {status!r}")

    paths = {
        "instruction": INSTRUCTION,
        "send_conditions": SEND_CONDITIONS,
        "submitted_body": SUBMITTED_BODY,
        "bundle": BUNDLE,
        "manifest": MANIFEST,
        "rules": RULES,
        "delta": DELTA,
        "coverage": COVERAGE,
        "placement": PLACEMENT,
        "non_live": NON_LIVE,
        "helper": HELPER,
        "invocation": INVOCATION,
        "launcher": LAUNCHER,
        "request": REQUEST,
        "spec": SPEC,
        "expected": EXPECTED,
        "template": TEMPLATE,
        "work": WORK,
    }
    actual_sha = {name: sha256(path) for name, path in paths.items()}
    if actual_sha != EXPECTED_SHA256:
        raise ValueError(f"A3 fixed SHA mismatch: {actual_sha}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["candidate_id"] != CANDIDATE_ID or manifest["route_id"] != ROUTE_ID:
        raise ValueError("A3 manifest identity mismatch")
    if manifest["candidate_payload_sha256"] != "ae889f6ab810224c841769607aaa79af5ebb38dcb29422b4c8fc23495ae867b5":
        raise ValueError("A3 candidate payload SHA mismatch")
    if manifest["teaching_independence"]["status"] != "PASS":
        raise ValueError("A3 teaching/test independence is not PASS")

    invocation = json.loads(INVOCATION.read_text(encoding="utf-8"))
    if Path(invocation["target_workbook"]).resolve() != WORK.resolve():
        raise ValueError("Fixed invocation target_workbook mismatch")
    if Path(invocation["json_root"]).resolve() != RUNTIME.resolve():
        raise ValueError("Fixed invocation json_root mismatch")
    if len(invocation["text_writes"]) != 7:
        raise ValueError("Fixed invocation text routing count changed")

    handoff_paths = [RUNTIME / f"source-{index}.json" for index in range(1, 8)] + [RUNTIME / "mode.json"]
    if OUTPUT.exists():
        raise ValueError("A3 output already exists before send")
    if any(path.exists() for path in handoff_paths):
        raise ValueError("A3 JSON handoff residue exists before send")

    request = REQUEST.read_text(encoding="utf-8").rstrip("\r\n")
    conditions = SEND_CONDITIONS.read_text(encoding="utf-8").rstrip("\r\n")
    instruction = INSTRUCTION.read_text(encoding="utf-8").rstrip("\r\n")
    body = SUBMITTED_BODY.read_text(encoding="utf-8")
    expected_body = request + "\n\n" + conditions + "\n\n" + instruction + "\n"
    if body != expected_body:
        raise ValueError("Prepared A3 submitted body is not the exact fixed request + conditions + instruction")
    for required in (CANDIDATE_ID, ROUTE_ID, BUNDLE.name, *[rule["id"] for rule in json.loads(RULES.read_text(encoding="utf-8"))["rules"]]):
        if required not in body or required not in BUNDLE.read_text(encoding="utf-8"):
            raise ValueError(f"A3 body/bundle alignment missing: {required}")
    for grader_value in ("春", "夏", "秋", "項目甲", "項目乙", "100%"):
        if grader_value in body:
            raise ValueError(f"Grader value leaked into submitted body: {grader_value}")

    criteria = {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "fixed_before_send": True,
        "response": {
            "markdown_text_code_block_count": 1,
            "generated_robin_unmodified": True,
            "code_first_and_last_nonempty_lines_are_pad_instructions": True,
            "no_explanation_heading_line_number_fence_or_pseudocode_inside": True,
            "refusal_or_no_code": "STOP",
        },
        "syntax_and_structure": {
            "balanced_if_else_end": True,
            "actions_must_use_bundle_observed_command_argument_enum_shapes": True,
            "existing_output_guard_before_read_json_work_and_helper": True,
            "read_only_input_open_count": 2,
            "typed_input_range_read_count": 2,
            "source_json_write_count": 7,
            "mode_json_write_count": 1,
            "fixed_runscript_count": 1,
            "exact_success_and_normal_double_gate": True,
            "numeric_write_count": 5,
            "save_as_count": 1,
            "read_only_output_reopen_count": 1,
            "typed_readback_rectangle_count": 2,
            "json_value_type_comparison_count": 12,
            "failure_close_no_save": True,
        },
        "assembly_rules": {
            "AR04_EXPLICIT_JSON_HANDOFF": "definitions_then_json_then_mode_then_source_files_then_mode_file_explicit_copies",
            "AR09_EXPLICIT_NUMERIC_WRITES": "definitions_before_explicit_writes_inside_normal_success_branch",
            "AR10_MULTIPLE_RECTANGLE_READBACK": "one_save_close_reopen_then_explicit_activation_read_pairs_then_one_close",
            "AR11_MULTIPLE_JSON_COMPARISONS": "saved_definitions_then_json_then_matching_comparisons_then_one_success_state",
            "new_pad_loop_commands": 0,
            "required_control_close_order": ["NORMAL_MODE", "EXACT_SUCCESS", "OUTPUT_GUARD"],
        },
        "fixed_paths_and_parameters": {
            "input1": str(INPUT1.resolve()),
            "input1_sheet": "受取明細",
            "input1_range": "D4:E6",
            "input2": str(INPUT2.resolve()),
            "input2_sheet": "追加項目",
            "input2_range": "B2:D3",
            "work": str(WORK.resolve()),
            "output": str(OUTPUT.resolve()),
            "target1_sheet": "集計先",
            "target1_start": "F7",
            "target2_sheet": "追記先",
            "target2_start": "D5",
            "json_root": str(RUNTIME.resolve()),
        },
        "fixed_launcher": {
            "helper_path": str(HELPER.resolve()),
            "helper_sha256": actual_sha["helper"],
            "invocation_path": str(INVOCATION.resolve()),
            "invocation_sha256": actual_sha["invocation"],
            "launcher_path": str(LAUNCHER.resolve()),
            "launcher_sha256": actual_sha["launcher"],
            "decoded_launcher_terminal_lf_restored_sha256": actual_sha["launcher"],
            "expected_stdout": EXPECTED_SUCCESS,
            "no_launcher_changes": True,
        },
        "safety": {
            "helper_or_invocation_creation_or_modification": False,
            "network": False,
            "delete": False,
            "overwrite_existing_output": False,
            "invoke_expression": False,
            "permission_security_excel_setting_change": False,
            "manual_generated_robin_edit": False,
            "unknown_syntax_or_recopy_difference": "STOP",
        },
        "run_gate": {
            "max_runs": 2,
            "run1_requires_all_comparisons_and_preservation_before_run2": True,
            "each_run_target_value_type_position_count": 12,
            "each_run_outside_value_type_formula_count": 468,
            "each_run_effective_format_cells": 480,
            "each_run_effective_format_rows": 48,
            "each_run_effective_format_columns": 30,
            "f6": {"value": "100%", "dotnet_type": "System.String", "number_format": "G/標準", "prefix": "", "has_formula": False},
            "original_input_and_template_sha_unchanged": True,
        },
    }

    protected_paths = [
        HELPER, INVOCATION, LAUNCHER, REQUEST, SPEC, EXPECTED, TEMPLATE, INPUT1, INPUT2,
        INSTRUCTION, SEND_CONDITIONS, SUBMITTED_BODY, BUNDLE, MANIFEST, RULES, DELTA,
        COVERAGE, PLACEMENT, NON_LIVE, T2 / "pad-recopy-before-run.robin", T2 / "result.json",
        BASE / "cycles/EX03-r12-G1/acceptance-status.json",
        BASE / "cycles/EX03-r12-fixed-helper-A1-G1/copilot-response.txt",
        BASE / "cycles/EX03-r12-fixed-helper-A1-G1/generation-assessment.json",
        BASE / "cycles/EX03-r12-fixed-helper-A2-G1/copilot-response.txt",
        BASE / "cycles/EX03-r12-fixed-helper-A2-G1/generation-assessment.json",
    ]
    protected = [{"path": relative(path), "sha256": sha256(path), "bytes": path.stat().st_size} for path in protected_paths]

    now = datetime.now(timezone.utc).astimezone().isoformat()
    CYCLE.mkdir(parents=True, exist_ok=False)
    write_text(CYCLE / "send-conditions.txt", conditions + "\n")
    write_text(CYCLE / "submitted-body.txt", body)
    write_json(CYCLE / "generation-acceptance-criteria.json", criteria)
    write_json(CYCLE / "plan.json", {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "route_id": ROUTE_ID,
        "candidate_id": CANDIDATE_ID,
        "prepared_at": now,
        "base_commit": BASE_COMMIT,
        "target": "NORMAL_MICROSOFT_365_COPILOT_CHAT",
        "send": {"limit_total": 1, "local_recorded_before": 0, "ui_history_absence_required_before_send": True, "resend": 0},
        "input": {
            "fixed_request_path": relative(REQUEST),
            "fixed_request_sha256": actual_sha["request"],
            "send_conditions_path": relative(SEND_CONDITIONS),
            "send_conditions_sha256": actual_sha["send_conditions"],
            "instruction_path": relative(INSTRUCTION),
            "instruction_sha256": actual_sha["instruction"],
            "submitted_body_path": relative(SUBMITTED_BODY),
            "submitted_body_sha256": actual_sha["submitted_body"],
            "attachment_path": relative(BUNDLE),
            "attachment_sha256": actual_sha["bundle"],
        },
        "runtime": {
            "root": str(RUNTIME.resolve()), "work": str(WORK.resolve()), "output": str(OUTPUT.resolve()),
            "helper": str(HELPER.resolve()), "invocation": str(INVOCATION.resolve()),
            "helper_sha256": actual_sha["helper"], "invocation_sha256": actual_sha["invocation"], "launcher_sha256": actual_sha["launcher"],
        },
        "limits": {
            "copilot_generations_max": 1, "pad_runs_max": 2,
            "run2_requires_run1_terminal_all_comparisons_pass_and_artifact_preserved": True,
            "manual_generated_robin_edit": 0, "additional_run": 0, "next_candidate": 0,
            "full_regression": 0, "github_write": 0,
            "stop_on_refusal_mismatch_safety_issue_or_unknown": True,
        },
        "classification": {
            "formal_r12_request_text_modified": False,
            "a3_assembly_rules_are_generation_basis": True,
            "formal_r12_path_compliance_claimed": False,
            "fixed_input_sheet_range_target_expected_preserved": True,
            "t2_auxiliary_pass_inherited": False,
        },
    })
    write_json(CYCLE / "preflight.json", {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "recorded_at": now,
        "status": "PASS_LOCAL_READY_PENDING_UI_HISTORY_RECORD",
        "checks": {
            "head_is_d28c689": True,
            "candidate_manifest_identity": True,
            "candidate_and_all_fixed_sha": True,
            "prepared_submitted_body_exact": True,
            "instruction_body_bundle_aligned": True,
            "helper_invocation_launcher_fixed": True,
            "grader_values_absent_from_body": True,
            "comparison_criteria_fixed_before_send": True,
            "work_matches_template": True,
            "output_absent": True,
            "json_handoff_residue_absent": True,
            "local_cycle_history_absent": True,
            "ui_send_history_checked": False,
            "normal_m365_chat_confirmed": False,
        },
        "next_gate": "RECORD_CONFIRMED_A3_G1_NOT_PREVIOUSLY_SENT_IN_NORMAL_M365_CHAT",
    })
    write_json(CYCLE / "protected-before.json", {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "recorded_at": now,
        "base_commit": BASE_COMMIT,
        "files": protected,
        "runtime": {"work_sha256": actual_sha["work"], "output_absent": True, "handoff_absent": [relative(path) for path in handoff_paths]},
    })
    print(json.dumps({
        "status": "PASS_LOCAL_READY_PENDING_UI_HISTORY_RECORD",
        "cycle_id": CYCLE_ID,
        "submitted_body_sha256": actual_sha["submitted_body"],
        "submitted_body_characters": len(body),
        "bundle_sha256": actual_sha["bundle"],
        "criteria_sha256": sha256(CYCLE / "generation-acceptance-criteria.json"),
        "runtime": str(RUNTIME.resolve()),
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
