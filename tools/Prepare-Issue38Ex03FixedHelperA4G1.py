#!/usr/bin/env python3
"""Prepare the one-send, at-most-two-run EX03 fixed-helper A4-G1 cycle."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CANDIDATE = ROOT / "copilot/versions/20260918-excel-r12-fixed-helper-a4"
CYCLE = BASE / "cycles/EX03-R12-FIXED-HELPER-A4-G1"
PROBE = BASE / "probes/ex03-r12-fixed-helper"
A4_PROBE = BASE / "probes/ex03-r12-fixed-helper-a4"
RUNTIME = BASE / "runs/EX03-attempt1"

HELPER = PROBE / "EX03-R12-Fixed-StringTransfer.ps1"
INVOCATION = A4_PROBE / "invocation.json"
LAUNCHER = A4_PROBE / "launcher.ps1"
REQUEST = BASE / "requests/EX03.txt"
SPEC = BASE / "spec.json"
EXPECTED = BASE / "expected.json"
TEMPLATE = BASE / "fixtures/EX03/ひな形.xlsx"
INPUT1 = BASE / "fixtures/EX03/入力い.xlsx"
INPUT2 = BASE / "fixtures/EX03/入力ろ.xlsx"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
JSON_ROOT = RUNTIME / "a4-helper-json"

INSTRUCTION = CANDIDATE / "agent-instructions.txt"
SEND_CONDITIONS = CANDIDATE / "send-conditions.txt"
SUBMITTED_BODY = CANDIDATE / "submitted-body.txt"
BUNDLE = CANDIDATE / "knowledge/PAD-Robin-Fixed-Helper-A4-Bundle.txt"
WIRING = CANDIDATE / "wiring-spec.json"
MANIFEST = CANDIDATE / "manifest.json"
RULES = CANDIDATE / "assembly-rules.json"
DELTA = CANDIDATE / "instruction-delta.json"
COVERAGE = CANDIDATE / "COVERAGE.md"
PLACEMENT = CANDIDATE / "PLACEMENT.md"
NON_LIVE = CANDIDATE / "non-live-verification.json"

CYCLE_ID = "EX03-R12-FIXED-HELPER-A4-G1"
ROUTE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A4"
CANDIDATE_ID = "20260918-excel-r12-fixed-helper-a4"
BASE_COMMIT = "4a1e890fa95bc55cbe981578a2694548bb310c94"
CANDIDATE_PAYLOAD_SHA256 = "43b3a49ac2352470213d438c532a4207612a48fb2264fa3a85df58bb706747a3"
EXPECTED_SUCCESS = '{"status":"OK","mode":"NORMAL","text_writes":7,"formats_restored":true}'

EXPECTED_SHA256 = {
    "instruction": "93cfd7aa5d0f1c380e1a5c50f764794a7bab2e676f1d064c9fe9b349788f3829",
    "send_conditions": "2ea75126d8d63fe5c6a5a61c9a3aa0ca3d9bbad17f5e8745c3016a6b37a6f9a3",
    "submitted_body": "8924f824256a161f035f686b221ea58bf2033a66e0ef359c8968506c338f9647",
    "bundle": "62695ca3c007ab291732657ddaeca66723a57115d151efc7b1730ef5341c514c",
    "wiring": "c62ec6951bdd36e895acfc937d7a1f390e75e8d984b26a9531cc2c88d970f58c",
    "manifest": "525c5450e1e17e68d50dbaf25556e77e6e8393cf2ad2cd15792b54859ae7242f",
    "rules": "57305c13d9bff292d7c7c2bc3e3152bcd75b85fd1bd800679df1671f79c7bc6e",
    "delta": "9d20461575931d61fab6eeeb8ccfb94cbf9fee6794001bb8930e40dde3127fb2",
    "coverage": "de209de09132048e5b7e9aa775c38099077a977c3f1ed11e561ee7343b1a45a5",
    "placement": "17c9ebe4373a0bfce215f0033d517353da979bfb475a5759471685f93d68f98a",
    "non_live": "9dfb6ebe8b47ee781d64d135a751495c84c87a6ff21a97b2d54f437088e645f2",
    "helper": "08d1a307dfc72d375018a6f70a4abdc33d6efe42009bb100e67712098c02d135",
    "invocation": "5c5a2008f55296a48f63fa65178aab971e4212455bb2af58e33149bdcaec40d8",
    "launcher": "a286179f8fb7f8febc87f1915cf10965ee0a50769251ecb17573c00926c174d5",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
    "input1": "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    "input2": "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
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


def source_key(item: dict) -> tuple[str, str, str]:
    return item["input_workbook"], item["input_sheet"], item["input_cell"]


def target_key(item: dict, text: bool) -> tuple[str, str]:
    if text:
        return item["helper_target_sheet"], item["helper_target_cell"]
    return item["target_sheet"], item["target_cell"]


def validate_wiring(wiring: dict) -> dict:
    text = wiring["text_mappings"]
    numeric = wiring["numeric_mappings"]
    readbacks = wiring["readbacks"]
    comparisons = wiring["comparison_contract"]["positions"]
    if len(text) != 7 or len(numeric) != 5 or len(readbacks) != 2 or len(comparisons) != 12:
        raise ValueError("A4 WIRING SPEC count mismatch")
    if [item["helper_source_index"] for item in text] != list(range(1, 8)):
        raise ValueError("A4 helper source indexes are not exactly 1..7")
    if [item["source_json_file"] for item in text] != [f"source-{index}.json" for index in range(1, 8)]:
        raise ValueError("A4 source JSON names are not exactly source-1..7")
    text_sources = {source_key(item) for item in text}
    numeric_sources = {source_key(item) for item in numeric}
    text_targets = {target_key(item, True) for item in text}
    numeric_targets = {target_key(item, False) for item in numeric}
    if len(text_sources) != 7 or len(numeric_sources) != 5:
        raise ValueError("A4 source mapping duplicate")
    if len(text_targets) != 7 or len(numeric_targets) != 5:
        raise ValueError("A4 target mapping duplicate")
    if text_sources & numeric_sources or text_targets & numeric_targets:
        raise ValueError("A4 text/numeric mapping overlap")
    expected_sources = {
        ("fixtures/EX03/入力い.xlsx", "受取明細", cell)
        for cell in ("D4", "E4", "D5", "E5", "D6", "E6")
    } | {
        ("fixtures/EX03/入力ろ.xlsx", "追加項目", cell)
        for cell in ("B2", "C2", "D2", "B3", "C3", "D3")
    }
    expected_targets = {
        ("集計先", cell) for cell in ("F7", "G7", "F8", "G8", "F9", "G9")
    } | {
        ("追記先", cell) for cell in ("D5", "E5", "F5", "D6", "E6", "F6")
    }
    if text_sources | numeric_sources != expected_sources:
        raise ValueError("A4 input rectangles are not covered one-to-one")
    if text_targets | numeric_targets != expected_targets:
        raise ValueError("A4 target rectangles are not covered one-to-one")
    if [(item["sheet"], item["range"], item["variable"]) for item in readbacks] != [
        ("集計先", "F7:G9", "Readback1"),
        ("追記先", "D5:F6", "Readback2"),
    ]:
        raise ValueError("A4 readback rectangles changed")
    if [item["order"] for item in comparisons] != list(range(1, 13)):
        raise ValueError("A4 comparison order changed")
    comparison_sources = {
        (item["source_workbook"], item["source_sheet"], item["source_cell"])
        for item in comparisons
    }
    comparison_targets = {(item["saved_sheet"], item["saved_cell"]) for item in comparisons}
    if comparison_sources != expected_sources or comparison_targets != expected_targets:
        raise ValueError("A4 comparison coverage changed")
    if not all(item["source_and_saved_positions_immutable"] for item in comparisons):
        raise ValueError("A4 comparison position is mutable")
    if wiring["generation_contract"]["cell_or_grader_values_included"]:
        raise ValueError("A4 WIRING SPEC includes grader values")
    return {
        "text_count": 7,
        "numeric_count": 5,
        "readback_count": 2,
        "comparison_count": 12,
        "source_coverage": 12,
        "target_coverage": 12,
        "text_numeric_source_overlap": 0,
        "text_numeric_target_overlap": 0,
    }


def main() -> int:
    if CYCLE.exists():
        raise FileExistsError(f"A4-G1 cycle already exists: {CYCLE}")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if head != BASE_COMMIT:
        raise ValueError(f"A4-G1 must start at {BASE_COMMIT}, observed {head}")
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    expected_new = "?? tools/Prepare-Issue38Ex03FixedHelperA4G1.py\n"
    if status.replace("\\", "/") != expected_new:
        raise ValueError(f"Unexpected preflight worktree changes: {status!r}")

    paths = {
        "instruction": INSTRUCTION,
        "send_conditions": SEND_CONDITIONS,
        "submitted_body": SUBMITTED_BODY,
        "bundle": BUNDLE,
        "wiring": WIRING,
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
        "input1": INPUT1,
        "input2": INPUT2,
        "work": WORK,
    }
    actual_sha = {name: sha256(path) for name, path in paths.items()}
    if actual_sha != EXPECTED_SHA256:
        raise ValueError(f"A4 fixed SHA mismatch: {actual_sha}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest["candidate_id"] != CANDIDATE_ID or manifest["route_id"] != ROUTE_ID:
        raise ValueError("A4 manifest identity mismatch")
    if manifest["candidate_payload_sha256"] != CANDIDATE_PAYLOAD_SHA256:
        raise ValueError("A4 candidate payload SHA mismatch")
    if manifest["teaching_independence"]["status"] != "PASS":
        raise ValueError("A4 teaching independence is not PASS")

    wiring = json.loads(WIRING.read_text(encoding="utf-8"))
    wiring_validation = validate_wiring(wiring)
    bundle_text = BUNDLE.read_text(encoding="utf-8")
    begin = "A4_WIRING_SPEC_JSON_BEGIN\n"
    end = "\nA4_WIRING_SPEC_JSON_END"
    if bundle_text.count(begin) != 1 or bundle_text.count(end) != 1:
        raise ValueError("A4 bundle WIRING SPEC markers changed")
    embedded = bundle_text.split(begin, 1)[1].split(end, 1)[0]
    if json.loads(embedded) != wiring:
        raise ValueError("A4 bundle WIRING SPEC differs from wiring-spec.json")

    invocation = json.loads(INVOCATION.read_text(encoding="utf-8"))
    if Path(invocation["target_workbook"]).resolve() != WORK.resolve():
        raise ValueError("A4 invocation target_workbook mismatch")
    if Path(invocation["json_root"]).resolve() != JSON_ROOT.resolve():
        raise ValueError("A4 invocation json_root mismatch")
    expected_text_writes = [
        {
            "source_index": item["helper_source_index"],
            "source_label": item["source_reference"],
            "sheet": item["helper_target_sheet"],
            "cell": item["helper_target_cell"],
        }
        for item in wiring["text_mappings"]
    ]
    if invocation["text_writes"] != expected_text_writes:
        raise ValueError("A4 invocation text routing differs from WIRING SPEC")
    launcher_text = LAUNCHER.read_text(encoding="utf-8")
    for fixed in (str(HELPER.resolve()), str(INVOCATION.resolve()), actual_sha["helper"], actual_sha["invocation"], EXPECTED_SUCCESS):
        if fixed not in launcher_text:
            raise ValueError(f"A4 launcher missing fixed identity: {fixed}")

    if not WORK.is_file() or actual_sha["work"] != actual_sha["template"]:
        raise ValueError("A4 fixed work is absent or differs from the template")
    if OUTPUT.exists():
        raise ValueError("A4 output already exists before send")
    if JSON_ROOT.exists():
        raise ValueError("A4 JSON root unexpectedly exists before send")

    request = REQUEST.read_text(encoding="utf-8").rstrip("\r\n")
    conditions = SEND_CONDITIONS.read_text(encoding="utf-8").rstrip("\r\n")
    instruction = INSTRUCTION.read_text(encoding="utf-8").rstrip("\r\n")
    body = SUBMITTED_BODY.read_text(encoding="utf-8")
    if body != request + "\n\n" + conditions + "\n\n" + instruction + "\n":
        raise ValueError("A4 submitted body is not the fixed request + conditions + instruction")
    for required in (CANDIDATE_ID, ROUTE_ID, BUNDLE.name):
        if required not in body or required not in bundle_text:
            raise ValueError(f"A4 body/bundle identity missing: {required}")
    if wiring["spec_id"] not in bundle_text:
        raise ValueError("A4 WIRING SPEC identity missing from bundle")
    wiring_text = WIRING.read_text(encoding="utf-8")
    for grader_value in ("春", "夏", "秋", "項目甲", "項目乙", "日本語", "100%"):
        if grader_value in wiring_text or grader_value in bundle_text:
            raise ValueError(f"EX03 grader text leaked into A4 WIRING/bundle: {grader_value}")
    # "日本語" is also an ordinary word in the generic instruction sentence
    # "利用者の日本語の依頼"; it is not used there as a cell/grader value.
    for distinctive_grader_value in ("春", "夏", "秋", "項目甲", "項目乙", "100%"):
        if distinctive_grader_value in body:
            raise ValueError(f"EX03 distinctive grader text leaked into A4 body: {distinctive_grader_value}")

    history = subprocess.run(
        ["git", "grep", "-F", CYCLE_ID, BASE_COMMIT, "--"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if history.returncode != 1:
        raise ValueError(f"A4-G1 local history is not unused: {history.stdout}")

    criteria = {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "fixed_before_send": True,
        "response": {
            "markdown_text_code_block_count": 1,
            "generated_robin_unmodified": True,
            "code_first_and_last_nonempty_lines_are_pad_instructions": True,
            "no_explanation_heading_line_number_fence_or_pseudocode_inside": True,
            "refusal_no_code_or_multiple_code_blocks": "STOP",
        },
        "wiring_spec": {
            "sha256": actual_sha["wiring"],
            "validation": wiring_validation,
            "all_source_and_saved_positions_immutable": True,
            "per_position_variable_names_may_be_generated": True,
            "unknown_action_argument_enum_or_control_fabrication_allowed": False,
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
        "fixed_paths_and_parameters": {
            "input1": str(INPUT1.resolve()),
            "input1_sheet": "受取明細",
            "input1_range": "D4:E6",
            "input2": str(INPUT2.resolve()),
            "input2_sheet": "追加項目",
            "input2_range": "B2:D3",
            "work": str(WORK.resolve()),
            "output": str(OUTPUT.resolve()),
            "json_root": str(JSON_ROOT.resolve()),
            "readbacks": ["集計先!F7:G9=>Readback1", "追記先!D5:F6=>Readback2"],
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
        },
        "safety": {
            "helper_invocation_or_launcher_creation_or_modification": False,
            "network": False,
            "delete": False,
            "overwrite_existing_output": False,
            "invoke_expression": False,
            "permission_security_excel_setting_change": False,
            "manual_generated_robin_edit": False,
            "unknown_syntax_wiring_mismatch_or_recopy_difference": "STOP",
        },
        "run_gate": {
            "max_runs": 2,
            "run1_requires_terminal_success_all_comparisons_and_artifact_preserved_before_run2": True,
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
        INSTRUCTION, SEND_CONDITIONS, SUBMITTED_BODY, BUNDLE, WIRING, MANIFEST, RULES,
        DELTA, COVERAGE, PLACEMENT, NON_LIVE,
        PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2/pad-recopy-before-run.robin",
        PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T2/result.json",
        BASE / "cycles/EX03-r12-G1/acceptance-status.json",
        BASE / "cycles/EX03-r12-fixed-helper-A3-G1/copilot-response.txt",
        BASE / "cycles/EX03-r12-fixed-helper-A3-G1/generation-assessment-final.json",
    ]
    protected = [
        {"path": relative(path), "sha256": sha256(path), "bytes": path.stat().st_size}
        for path in protected_paths
    ]

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
            "submitted_body_path": relative(SUBMITTED_BODY),
            "submitted_body_sha256": actual_sha["submitted_body"],
            "attachment_path": relative(BUNDLE),
            "attachment_sha256": actual_sha["bundle"],
            "wiring_spec_path": relative(WIRING),
            "wiring_spec_sha256": actual_sha["wiring"],
        },
        "runtime": {
            "root": str(RUNTIME.resolve()),
            "work": str(WORK.resolve()),
            "output": str(OUTPUT.resolve()),
            "json_root": str(JSON_ROOT.resolve()),
            "helper": str(HELPER.resolve()),
            "invocation": str(INVOCATION.resolve()),
            "launcher": str(LAUNCHER.resolve()),
            "helper_sha256": actual_sha["helper"],
            "invocation_sha256": actual_sha["invocation"],
            "launcher_sha256": actual_sha["launcher"],
        },
        "limits": {
            "copilot_generations_max": 1,
            "pad_runs_max": 2,
            "run2_requires_run1_terminal_all_comparisons_pass_and_artifact_preserved": True,
            "manual_generated_robin_edit": 0,
            "additional_run": 0,
            "next_candidate": 0,
            "github_write": 0,
            "stop_on_refusal_mismatch_safety_issue_or_unknown": True,
        },
        "classification": {
            "formal_r12_request_text_modified": False,
            "a4_wiring_spec_is_generation_basis": True,
            "formal_r12_work_and_output_paths_aligned": True,
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
            "head_is_4a1e890": True,
            "candidate_manifest_identity": True,
            "candidate_and_all_fixed_sha": True,
            "prepared_submitted_body_exact": True,
            "instruction_body_bundle_aligned": True,
            "wiring_spec_machine_and_bundle_exact": True,
            "wiring_7_5_2_12_coverage_disjointness": True,
            "helper_invocation_launcher_fixed_and_runtime_aligned": True,
            "grader_text_absent_from_wiring_and_bundle": True,
            "distinctive_grader_text_absent_from_body": True,
            "comparison_criteria_fixed_before_send": True,
            "work_matches_template": True,
            "output_absent": True,
            "a4_json_root_absent_before_send": True,
            "local_cycle_history_absent": True,
            "ui_send_history_checked": False,
            "normal_m365_chat_confirmed": False,
        },
        "next_gate": "RECORD_CONFIRMED_A4_G1_NOT_PREVIOUSLY_SENT_IN_NORMAL_M365_CHAT",
    })
    write_json(CYCLE / "protected-before.json", {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "recorded_at": now,
        "base_commit": BASE_COMMIT,
        "files": protected,
        "runtime": {
            "work_sha256": actual_sha["work"],
            "output_absent": True,
            "a4_json_root_absent": True,
        },
    })
    print(json.dumps({
        "status": "PASS_LOCAL_READY_PENDING_UI_HISTORY_RECORD",
        "cycle_id": CYCLE_ID,
        "submitted_body_sha256": actual_sha["submitted_body"],
        "submitted_body_characters": len(body),
        "bundle_sha256": actual_sha["bundle"],
        "wiring_sha256": actual_sha["wiring"],
        "criteria_sha256": sha256(CYCLE / "generation-acceptance-criteria.json"),
        "runtime": str(RUNTIME.resolve()),
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
