#!/usr/bin/env python3
"""Freeze the local-only EX03 r10 single-send acceptance checkpoint.

This preparation is deliberately pre-browser. It fixes the exact r10 body,
same-version bundle, protected-file snapshot, and unchanged stop rules while
recording that the authorized r9 send was consumed and stopped before PAD.
It does not stage a browser, send to Copilot, create/import a PAD flow, or run.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CYCLE = BASE / "cycles/EX03-r10-G1"
RUN = BASE / "runs/EX03-attempt1"
VERSION = ROOT / "copilot/versions/20260917-excel-r10"
R9 = ROOT / "copilot/versions/20260917-excel-r9"
R9_CYCLE = BASE / "cycles/EX03-r9-G1"
AUDIT = BASE / "probes/ex03-r10-structural-fidelity"
BASE_COMMIT = "06aa0a572c58a09357ac1ac27a0a04eeaa4d680d"

EXPECTED = {
    "manifest": "7807e31e8177b05dc89d235496ee1b5978502f7406586dff2621d769981d6cbe",
    "instruction": "9434c976457b2fec14ad24d8ee57a3400e7eb092ba38259e3f8f728139c20681",
    "bundle": "0c53d6ce82fc5e23363332420b59c34470decbb123f804b2e628d26d58928ec6",
    "robin_support": "6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb",
    "script_support": "65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9",
    "fidelity_support": "4b704ade5343b1a28bc0101080d5756107e02210be40445082de3ab30315079d",
    "structural_analysis": "a2b0e39683dfceac45f49ebaa70c71da486954343e5d0be4e2276f971ad0a798",
    "structural_report": "5093f1aeeb4c74687fb4069d0b0325e3f90115442e794ada8d23e9b58c5ee624",
    "dom_confirmation": "a78e4cf2f309b733ae8e9c6d6c268de16206ca8df17d2863d07f512cbcefb34f",
    "r9_acceptance": "d3677a6e026e1a20b5cf109795a848036568182014c0f87bc4e0c119dd373d9b",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "input_a": "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    "input_b": "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
}

ROBIN_SUPPORT = VERSION / "support/EX03-R10-Independent-PAD-Recopy.robin"
SCRIPT_SUPPORT = VERSION / "support/EX03-R10-Independent-FormatSandwich.ps1.txt"
FIDELITY_SUPPORT = VERSION / "support/EX03-R10-Structural-Fidelity-Contract.txt"

FIXED_COMPLETION_TERMS = [
    r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38\\fixtures\\EX03\\入力い.xlsx",
    r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38\\fixtures\\EX03\\入力ろ.xlsx",
    r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38\\runs\\EX03-attempt1\\work.xlsx",
    r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38\\runs\\EX03-attempt1\\照合結果.xlsx",
    "受取明細",
    "追加項目",
    "集計先",
    "追記先",
]
GRADER_ONLY_VALUES = ["春", "夏", "秋", "項目甲", "項目乙", "-4.5", "6.25", "100%"]
INDEPENDENT_EXAMPLE_TERMS = [
    "source-one.xlsx",
    "source-two.xlsx",
    "work-copy.xlsx",
    "example-result.xlsx",
    "教材入力一",
    "教材入力二",
    "教材出力一",
    "教材出力二",
]
FORBIDDEN_RUNTIME_ACTIONS = [
    "File.Delete",
    "Folder.Delete",
    "WebAutomation.",
    "HTTP.",
    "System.RunDOSCommand",
    "System.RunApplication",
]
TOKEN_COUNTS = {
    "[ordered]": 8,
    "[string]": 14,
    "[bool]": 2,
    "[void]": 5,
    "[Runtime.InteropServices.Marshal]": 6,
    "[IO.Path]": 1,
    "[StringComparison]": 1,
    "::GetFullPath(": 1,
    "::OrdinalIgnoreCase": 1,
    "::IsNullOrEmpty(": 1,
    "$matches[0]": 1,
    "$allowedTargets[$sheetName]": 1,
}
REQUIRED_INVARIANT_FRAGMENTS = [
    "[string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)",
    "[string]::IsNullOrEmpty($afterPrefixCharacter)",
]
FORBIDDEN_CORRUPTION_FRAGMENTS = [
    "[IO.Path]::GetFulling]",
    ", :OrdinalIgnoreCase",
    "-not :IsNullOrEmpty(",
]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load("issue38_excel_oracle_r10", "tools/Verify-Issue38Excel.py")


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repo_path(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def write_bytes(path: Path, value: bytes) -> None:
    with path.open("xb") as handle:
        handle.write(value)


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def protected_paths() -> list[Path]:
    fixed = [
        BASE / "expected.json",
        BASE / "spec.json",
        BASE / "freeze.json",
        BASE / "requests/EX03.txt",
        BASE / "fixtures/EX03/入力い.xlsx",
        BASE / "fixtures/EX03/入力ろ.xlsx",
        BASE / "fixtures/EX03/ひな形.xlsx",
        RUN / "work.xlsx",
        RUN / "preparation.json",
    ]
    trees = [
        ROOT / "copilot/versions/20260916-excel-r6",
        ROOT / "copilot/versions/20260916-excel-r7",
        ROOT / "copilot/versions/20260916-excel-r8",
        R9,
        VERSION,
        BASE / "cycles/EX03-r5-G1",
        BASE / "cycles/EX03-r6-G1",
        BASE / "cycles/EX03-r8-G1",
        R9_CYCLE,
        BASE / "probes/ex03-r7-robin-source",
        BASE / "probes/ex03-r8-independent-source",
        BASE / "probes/ex03-r9-escape-fidelity",
        AUDIT,
        BASE / "probes/percent-text-write",
    ]
    paths = list(fixed)
    for tree in trees:
        paths.extend(sorted(path for path in tree.rglob("*") if path.is_file()))
    unique = {path.resolve(): path for path in paths}
    return [unique[key] for key in sorted(unique, key=lambda item: str(item).lower())]


def prepare(destination: Path = CYCLE, verify_head: bool = True) -> dict[str, object]:
    destination = Path(destination)
    if destination.exists():
        raise ValueError(f"Cycle already exists; refusing overwrite: {destination}")
    if verify_head:
        head = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
        if head != BASE_COMMIT:
            raise ValueError(f"Expected base commit {BASE_COMMIT}, found {head}")
    oracle.check_frozen()

    manifest_path = VERSION / "manifest.json"
    instruction_path = VERSION / "agent-instructions.txt"
    bundle_path = VERSION / "knowledge/PAD-Robin-Knowledge-Bundle.txt"
    package = {
        "manifest": manifest_path,
        "instruction": instruction_path,
        "bundle": bundle_path,
        "robin_support": ROBIN_SUPPORT,
        "script_support": SCRIPT_SUPPORT,
        "fidelity_support": FIDELITY_SUPPORT,
        "structural_analysis": AUDIT / "analysis.json",
        "structural_report": AUDIT / "report.md",
        "dom_confirmation": AUDIT / "r9-dom-code-confirmation.json",
        "r9_acceptance": R9_CYCLE / "acceptance-status.json",
    }
    for key, path in package.items():
        if sha(path) != EXPECTED[key]:
            raise ValueError(f"Protected r10/r9 {key} hash mismatch: {sha(path)}")

    manifest = json.loads(manifest_path.read_bytes())
    analysis = json.loads((AUDIT / "analysis.json").read_bytes())
    r9_status = json.loads((R9_CYCLE / "acceptance-status.json").read_bytes())
    if manifest["version"] != "20260917-excel-r10":
        raise ValueError("Unexpected candidate version")
    if manifest["inherits_live_acceptance"]:
        raise ValueError("r10 must not inherit live acceptance")
    if manifest["status"] != (
        "FROZEN_CANDIDATE_EX03_STRUCTURAL_FIDELITY_GATE_NOT_COPILOT_OR_RUNTIME_ACCEPTED"
    ):
        raise ValueError("r10 status no longer marks live acceptance as unproven")
    if manifest["evidence"]["teaching_test_independence"] != (
        "PASS_R10_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_CURRENT_INSTRUCTION_BUNDLE_AND_SUPPORT"
    ):
        raise ValueError("r10 independence evidence is not passing")
    if analysis["decision"] != "PASS_R9_STRUCTURAL_FAILURE_BOUNDARY_READY_FOR_UNSENT_R10":
        raise ValueError("r10 structural analysis is not passing")
    if analysis["scope"]["copilot_send"] != 0 or analysis["scope"]["pad_run"] != 0:
        raise ValueError("r10 analysis unexpectedly records live work")
    if not analysis["response_boundary"]["dom_equals_raw_clipboard"]:
        raise ValueError("r9 response boundary is not confirmed")
    if r9_status["generation"]["normal_m365_send_count"] != 1:
        raise ValueError("The authorized r9 send is not recorded exactly once")
    if r9_status["generation"]["resend_count"] != 0:
        raise ValueError("The r9 cycle unexpectedly records a resend")
    if r9_status["runs"]["pad_runs_used"] != 0:
        raise ValueError("The stopped r9 cycle now records a PAD run")
    if r9_status["decision"]["status"] != (
        "STOPPED_BEFORE_PAD_GENERATED_ROBIN_SAFETY_FAILURE"
    ):
        raise ValueError("The r9 fixed stop decision changed")

    for record in manifest["source_files"]:
        if sha(VERSION / record["path"]) != record["sha256"]:
            raise ValueError("r10 source mismatch: " + record["path"])
    for record in manifest["support_files"]:
        if sha(VERSION / record["path"]) != record["sha256"]:
            raise ValueError("r10 support mismatch: " + record["path"])
    for path, expected_hash in manifest["evidence_inputs"].items():
        if sha(ROOT / path) != expected_hash:
            raise ValueError("r10 evidence input changed: " + path)
    if ROBIN_SUPPORT.read_bytes() != (
        R9 / "support/EX03-R9-Independent-PAD-Recopy.robin"
    ).read_bytes():
        raise ValueError("r10 teaching Robin differs from the r9 source")
    if SCRIPT_SUPPORT.read_bytes() != (
        R9 / "support/EX03-R9-Independent-FormatSandwich.ps1.txt"
    ).read_bytes():
        raise ValueError("r10 embedded script differs from r9")

    request_path = BASE / "requests/EX03.txt"
    spec_path = BASE / "spec.json"
    expected_path = BASE / "expected.json"
    input_a_path = BASE / "fixtures/EX03/入力い.xlsx"
    input_b_path = BASE / "fixtures/EX03/入力ろ.xlsx"
    template_path = BASE / "fixtures/EX03/ひな形.xlsx"
    work_path = RUN / "work.xlsx"
    output_path = RUN / "照合結果.xlsx"
    fixed = {
        "request": request_path,
        "spec": spec_path,
        "expected": expected_path,
        "input_a": input_a_path,
        "input_b": input_b_path,
        "template": template_path,
    }
    for key, path in fixed.items():
        if sha(path) != EXPECTED[key]:
            raise ValueError(f"Fixed {key} hash mismatch: {sha(path)}")
    if not work_path.is_file() or sha(work_path) != EXPECTED["template"]:
        raise ValueError("EX03 work copy must exist and match the frozen template")
    if output_path.exists():
        raise ValueError("EX03 output must be absent before staging a new live cycle")

    body = instruction_path.read_bytes() + b"\n" + request_path.read_bytes() + b"\n"
    body_text = body.decode("utf-8")
    leaked_values = [value for value in GRADER_ONLY_VALUES if value in body_text]
    if leaked_values:
        raise ValueError(f"Grader-only values leaked into submitted body: {leaked_values}")
    leaked_example = [value for value in INDEPENDENT_EXAMPLE_TERMS if value in body_text]
    if leaked_example:
        raise ValueError(f"Independent example data leaked into submitted body: {leaked_example}")

    bundle_text = bundle_path.read_text(encoding="utf-8")
    fixed_bundle_leaks = [value for value in FIXED_COMPLETION_TERMS if value in bundle_text]
    if fixed_bundle_leaks:
        raise ValueError(f"Fixed EX03 complete-answer terms leaked into r10 bundle: {fixed_bundle_leaks}")
    unique_grader_leaks = [value for value in GRADER_ONLY_VALUES[:-1] if value in bundle_text]
    if unique_grader_leaks:
        raise ValueError(f"Unique grader-only values leaked into r10 bundle: {unique_grader_leaks}")
    robin_text = ROBIN_SUPPORT.read_text(encoding="utf-8")
    script_text = SCRIPT_SUPPORT.read_text(encoding="utf-8")
    if robin_text.count(r"\[") or robin_text.count(r"\]"):
        raise ValueError("The authoritative teaching Robin has bracket backslashes")
    for token, count in TOKEN_COUNTS.items():
        if robin_text.count(token) != count:
            raise ValueError(f"Teaching token count changed: {token}")
    for fragment in REQUIRED_INVARIANT_FRAGMENTS:
        if robin_text.count(fragment) != 1:
            raise ValueError(f"Teaching invariant changed: {fragment}")
    for fragment in FORBIDDEN_CORRUPTION_FRAGMENTS:
        if robin_text.count(fragment) != 0:
            raise ValueError(f"Teaching source contains corruption: {fragment}")
    forbidden = [
        action
        for action in FORBIDDEN_RUNTIME_ACTIONS
        if action in robin_text or action in script_text
    ]
    if forbidden:
        raise ValueError(f"Unexpected unsafe runtime action in source: {forbidden}")
    for required in [
        "Do only the listed data-slot substitutions",
        "source-derived exact token counts",
        "Require each invariant fragment exactly once",
        "Require each observed corruption fragment zero times",
        "EX03 text mapping",
        "EX03 text source",
    ]:
        if required not in bundle_text:
            raise ValueError("r10 structural-fidelity contract missing: " + required)

    protected_list = protected_paths()
    protected = {
        "schema_version": 1,
        "cycle_id": "EX03-R10-G1",
        "base_commit": BASE_COMMIT,
        "files": [
            {"path": repo_path(path), "sha256": sha(path)} for path in protected_list
        ],
    }

    destination.mkdir(parents=True, exist_ok=False)
    submitted_path = destination / "submitted-body.txt"
    write_bytes(submitted_path, body)
    canonical_body_path = CYCLE / "submitted-body.txt"
    plan = {
        "schema_version": 1,
        "cycle_id": "EX03-R10-G1",
        "base_commit": BASE_COMMIT,
        "purpose": "Prepare one future normal-M365 generation and at-most-two unmodified PAD runs for fixed EX03 using the r10 structural-fidelity gate",
        "candidate": {
            "version": manifest["version"],
            "instruction_path": repo_path(instruction_path),
            "instruction_sha256": sha(instruction_path),
            "bundle_path": repo_path(bundle_path),
            "bundle_sha256": sha(bundle_path),
            "manifest_path": repo_path(manifest_path),
            "manifest_sha256": sha(manifest_path),
            "robin_support_path": repo_path(ROBIN_SUPPORT),
            "robin_support_sha256": sha(ROBIN_SUPPORT),
            "script_support_path": repo_path(SCRIPT_SUPPORT),
            "script_support_sha256": sha(SCRIPT_SUPPORT),
            "fidelity_support_path": repo_path(FIDELITY_SUPPORT),
            "fidelity_support_sha256": sha(FIDELITY_SUPPORT),
            "inherits_live_acceptance": False,
        },
        "fixed_inputs": {
            "request": {"path": repo_path(request_path), "sha256": sha(request_path)},
            "spec": {"path": repo_path(spec_path), "sha256": sha(spec_path)},
            "grader_only_expected": {
                "path": repo_path(expected_path),
                "sha256": sha(expected_path),
                "send_to_copilot": False,
            },
            "input_a": {"path": repo_path(input_a_path), "sha256": sha(input_a_path)},
            "input_b": {"path": repo_path(input_b_path), "sha256": sha(input_b_path)},
            "template": {"path": repo_path(template_path), "sha256": sha(template_path)},
            "work": {
                "path": repo_path(work_path),
                "sha256": sha(work_path),
                "must_match_template_before_each_run": True,
            },
            "output": {
                "path": repo_path(output_path),
                "must_be_absent_before_each_run": True,
            },
        },
        "submission": {
            "body_path": repo_path(canonical_body_path),
            "body_sha256": sha(submitted_path),
            "body_contract": "unchanged full r10 instructions followed by unchanged fixed EX03 request",
            "attachment_path": repo_path(bundle_path),
            "attachment_sha256": sha(bundle_path),
            "normal_m365_new_chat": True,
            "model": "Think Deeper",
            "grader_only_expected_excluded": True,
            "fixed_completed_robin_excluded": True,
            "independent_teaching_robin_in_bundle": True,
        },
        "authorization": {
            "r9_authorized_send_consumed": True,
            "r9_normal_m365_send_count": 1,
            "r9_resend_count": 0,
            "r9_stop_before_pad_preserved": True,
            "r10_normal_m365_send_count": 0,
            "r10_browser_staged": False,
            "r10_action_time_confirmation_required_before_staging_or_send": True,
        },
        "limits": {
            "max_generation_requests": 1,
            "max_pad_runs": 2,
            "no_regeneration_or_manual_robin_repair": True,
            "stop_on_refusal_safety_issue_mismatch_or_unknown_result": True,
            "run2_requires_run1_terminal_comparison_and_artifact_preserved": True,
        },
        "acceptance": {
            "scope": "fixed EX03 text/number case and r10 package only",
            "required": [
                "one normal-M365 send with exact full body and actual same-version bundle",
                "unmodified generated Robin in a new dedicated Power Fx OFF flow",
                "PAD save and exact re-copy before Run1",
                "Run1 terminal confirmation, full comparison and artifact preservation before Run2",
                "two runs with all twelve source/readback JSON type comparisons",
                "all fixed values, types, positions, outside cells, formulas and effective formats",
                "F6 exact System.String 100%, original format, empty prefix and no formula",
                "all protected input/template SHA values unchanged",
            ],
            "no_old_or_other_case_pass_inheritance": True,
            "no_unconfirmed_type_or_shape_generalization": True,
            "legacy_558_failure_preserved": True,
            "existing_output_guard_live_path_still_required": True,
        },
        "external_actions": {
            "browser_staging": 0,
            "copilot_send": 0,
            "pad_import": 0,
            "pad_run": 0,
            "github_write": 0,
        },
        "status": "READY_FOR_NEW_ACTION_TIME_CONFIRMATION_NOT_STAGED_NOT_SENT",
    }
    preflight = {
        "schema_version": 1,
        "cycle_id": "EX03-R10-G1",
        "base_commit": BASE_COMMIT,
        "checks": {
            "base_commit_matches_frozen_r10": True,
            "fixed_fixture_spec_request_expected_hashes_match": True,
            "r10_instruction_bundle_manifest_support_hashes_match": True,
            "r10_all_evidence_input_hashes_match": True,
            "r10_teaching_test_independence_pass": True,
            "r10_teaching_robin_and_script_byte_identical_to_r9": True,
            "r10_structural_token_and_fragment_gate_in_bundle": True,
            "r9_response_dom_matches_preserved_raw_clipboard": True,
            "fixed_complete_answer_absent_from_r10_bundle": True,
            "grader_only_values_absent_from_submitted_body": True,
            "independent_example_data_absent_from_submitted_body": True,
            "independent_source_forbidden_runtime_actions_absent": True,
            "r9_one_send_consumed_and_no_resend": True,
            "r9_stop_before_pad_preserved": True,
            "work_exists_and_matches_template": True,
            "output_absent": True,
        },
        "hashes": {
            "submitted_body": sha(submitted_path),
            "instruction": sha(instruction_path),
            "bundle": sha(bundle_path),
            "manifest": sha(manifest_path),
            "robin_support": sha(ROBIN_SUPPORT),
            "script_support": sha(SCRIPT_SUPPORT),
            "fidelity_support": sha(FIDELITY_SUPPORT),
            "work_and_template": sha(work_path),
            "input_a": sha(input_a_path),
            "input_b": sha(input_b_path),
        },
        "counts": {
            "protected_files": len(protected_list),
            "submitted_body_utf16_units": len(body_text.encode("utf-16-le")) // 2,
            "submitted_body_utf8_bytes": len(body),
            "submitted_body_lines": len(body_text.splitlines()),
            "teaching_backslash_open_bracket": robin_text.count(r"\["),
            "teaching_backslash_close_bracket": robin_text.count(r"\]"),
            "structural_tokens": TOKEN_COUNTS,
            "required_invariant_fragments": len(REQUIRED_INVARIANT_FRAGMENTS),
            "forbidden_corruption_fragments": len(FORBIDDEN_CORRUPTION_FRAGMENTS),
        },
        "decision": {
            "local_checkpoint": "PASS",
            "browser_staging": "NOT_STARTED_REQUIRES_NEW_ACTION_TIME_CONFIRMATION",
            "send": "NOT_SENT_REQUIRES_NEW_ACTION_TIME_CONFIRMATION",
            "copilot_generation": "NOT_STARTED",
            "pad_run1": "NOT_STARTED",
            "pad_run2": "NOT_STARTED",
        },
    }
    write_json(destination / "plan.json", plan)
    write_json(destination / "protected-files-before.json", protected)
    write_json(destination / "preflight.json", preflight)
    return {
        "cycle": repo_path(CYCLE),
        "version": manifest["version"],
        "submitted_body_sha256": sha(submitted_path),
        "submitted_body_utf16_units": preflight["counts"]["submitted_body_utf16_units"],
        "bundle_sha256": sha(bundle_path),
        "manifest_sha256": sha(manifest_path),
        "protected_file_count": len(protected_list),
        "status": plan["status"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=CYCLE)
    args = parser.parse_args()
    if args.output.resolve() != CYCLE.resolve():
        raise ValueError("CLI preparation is restricted to the canonical sealed cycle path")
    print(json.dumps(prepare(args.output), ensure_ascii=False, indent=2))
