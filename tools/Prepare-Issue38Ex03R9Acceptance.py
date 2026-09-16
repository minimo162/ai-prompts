#!/usr/bin/env python3
"""Freeze the local-only EX03 r9 single-send acceptance checkpoint.

This preparation is deliberately pre-browser.  It fixes the exact r9 body,
same-version bundle, protected-file snapshot, and stop rules, while recording
that the one authorized r8 send was already consumed.  It does not stage a
browser, send to Copilot, create/import a PAD flow, or execute PAD.
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
CYCLE = BASE / "cycles/EX03-r9-G1"
RUN = BASE / "runs/EX03-attempt1"
VERSION = ROOT / "copilot/versions/20260917-excel-r9"
R8 = ROOT / "copilot/versions/20260916-excel-r8"
R8_CYCLE = BASE / "cycles/EX03-r8-G1"
AUDIT = BASE / "probes/ex03-r9-escape-fidelity"
BASE_COMMIT = "969a64e41638cc1e0ffca64ef7b6ed1668b80027"

EXPECTED = {
    "manifest": "1b64005c85aee3215160c9381d956a64531863b5d838d9091009fded5007f540",
    "instruction": "a699dd910a4b0529fc71c9b8045b845bf49b8a407df9da88027a0ca0ab0f51fa",
    "bundle": "b402a6c78fb39cb68dd4111590122b9f9be3364609358fd58a9ad3880d29b993",
    "robin_support": "6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb",
    "script_support": "65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9",
    "fidelity_support": "321ee7f2ac09c7a4410fcc2680f4b87fb8a6e1fed6d1074f0c6a7b23cefd912c",
    "escape_analysis": "37009a713dd38f68bb142e80c465620fbd29152e445fc1fc72b0b744e7b3f13a",
    "escape_report": "b99d4fa156b780d04ce0af707bd6040545cfc7c0bddca44a9552323bd7f39247",
    "r8_acceptance": "2f9a7dea1319496ff955bd19cf116fde67f90822021e20eca1c1016a6076a53d",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "input_a": "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    "input_b": "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
}

ROBIN_SUPPORT = VERSION / "support/EX03-R9-Independent-PAD-Recopy.robin"
SCRIPT_SUPPORT = VERSION / "support/EX03-R9-Independent-FormatSandwich.ps1.txt"
FIDELITY_SUPPORT = VERSION / "support/EX03-R9-Escape-Fidelity-Contract.txt"

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


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load("issue38_excel_oracle_r9", "tools/Verify-Issue38Excel.py")


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
        R8,
        VERSION,
        BASE / "cycles/EX03-r5-G1",
        BASE / "cycles/EX03-r6-G1",
        R8_CYCLE,
        BASE / "probes/ex03-r7-robin-source",
        BASE / "probes/ex03-r8-independent-source",
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
        "escape_analysis": AUDIT / "analysis.json",
        "escape_report": AUDIT / "report.md",
        "r8_acceptance": R8_CYCLE / "acceptance-status.json",
    }
    for key, path in package.items():
        if sha(path) != EXPECTED[key]:
            raise ValueError(f"Protected r9/r8 {key} hash mismatch: {sha(path)}")

    manifest = json.loads(manifest_path.read_bytes())
    analysis = json.loads((AUDIT / "analysis.json").read_bytes())
    r8_status = json.loads((R8_CYCLE / "acceptance-status.json").read_bytes())
    if manifest["version"] != "20260917-excel-r9":
        raise ValueError("Unexpected candidate version")
    if manifest["inherits_live_acceptance"]:
        raise ValueError("r9 must not inherit live acceptance")
    if manifest["status"] != (
        "FROZEN_CANDIDATE_EX03_ESCAPE_FIDELITY_GATE_NOT_COPILOT_OR_RUNTIME_ACCEPTED"
    ):
        raise ValueError("r9 status no longer marks live acceptance as unproven")
    if manifest["evidence"]["teaching_test_independence"] != (
        "PASS_R9_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_CURRENT_INSTRUCTION_BUNDLE_AND_SUPPORT"
    ):
        raise ValueError("r9 independence evidence is not passing")
    if analysis["decision"] != "PASS_ROOT_CAUSE_BOUNDARY_READY_FOR_UNSENT_SUCCESSOR":
        raise ValueError("r9 escape analysis is not passing")
    if analysis["scope"]["copilot_send"] != 0 or analysis["scope"]["pad_run"] != 0:
        raise ValueError("r9 analysis unexpectedly records live work")
    if r8_status["generation"]["normal_m365_send_count"] != 1:
        raise ValueError("The authorized r8 send is not recorded exactly once")
    if r8_status["generation"]["resend_count"] != 0:
        raise ValueError("The r8 cycle unexpectedly records a resend")
    if r8_status["runs"]["pad_runs_used"] != 0:
        raise ValueError("The stopped r8 cycle now records a PAD run")
    if r8_status["decision"]["status"] != "STOPPED_BEFORE_RUN1_PAD_RECOPY_MISMATCH":
        raise ValueError("The r8 fixed stop decision changed")

    for record in manifest["source_files"]:
        if sha(VERSION / record["path"]) != record["sha256"]:
            raise ValueError("r9 source mismatch: " + record["path"])
    for record in manifest["support_files"]:
        if sha(VERSION / record["path"]) != record["sha256"]:
            raise ValueError("r9 support mismatch: " + record["path"])
    for path, expected_hash in manifest["evidence_inputs"].items():
        if sha(ROOT / path) != expected_hash:
            raise ValueError("r9 evidence input changed: " + path)
    if ROBIN_SUPPORT.read_bytes() != (
        R8 / "support/EX03-R8-Independent-PAD-Recopy.robin"
    ).read_bytes():
        raise ValueError("r9 teaching Robin differs from the PAD-recopied r8 source")
    if SCRIPT_SUPPORT.read_bytes() != (
        R8 / "support/EX03-R8-Independent-FormatSandwich.ps1.txt"
    ).read_bytes():
        raise ValueError("r9 embedded script differs from r8")

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
        raise ValueError(f"Fixed EX03 complete-answer terms leaked into r9 bundle: {fixed_bundle_leaks}")
    unique_grader_leaks = [value for value in GRADER_ONLY_VALUES[:-1] if value in bundle_text]
    if unique_grader_leaks:
        raise ValueError(f"Unique grader-only values leaked into r9 bundle: {unique_grader_leaks}")
    robin_text = ROBIN_SUPPORT.read_text(encoding="utf-8")
    script_text = SCRIPT_SUPPORT.read_text(encoding="utf-8")
    if robin_text.count(r"\[") or robin_text.count(r"\]"):
        raise ValueError("The authoritative teaching Robin has forbidden bracket backslashes")
    forbidden = [
        action
        for action in FORBIDDEN_RUNTIME_ACTIONS
        if action in robin_text or action in script_text
    ]
    if forbidden:
        raise ValueError(f"Unexpected unsafe runtime action in independent source: {forbidden}")
    for required in [
        "Never prefix them with a backslash",
        "Both counts must be zero",
        "No teaching-only label may remain",
    ]:
        if required not in bundle_text:
            raise ValueError("r9 fidelity contract missing from bundle: " + required)

    protected_list = protected_paths()
    protected = {
        "schema_version": 1,
        "cycle_id": "EX03-R9-G1",
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
        "cycle_id": "EX03-R9-G1",
        "base_commit": BASE_COMMIT,
        "purpose": "Prepare one future normal-M365 generation and at-most-two unmodified PAD runs for fixed EX03 using the r9 fidelity gate",
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
            "body_contract": "unchanged full r9 instructions followed by unchanged fixed EX03 request",
            "attachment_path": repo_path(bundle_path),
            "attachment_sha256": sha(bundle_path),
            "normal_m365_new_chat": True,
            "model": "Think Deeper",
            "grader_only_expected_excluded": True,
            "fixed_completed_robin_excluded": True,
            "independent_teaching_robin_in_bundle": True,
        },
        "authorization": {
            "r8_authorized_send_consumed": True,
            "r8_normal_m365_send_count": 1,
            "r8_resend_count": 0,
            "r9_normal_m365_send_count": 0,
            "r9_browser_staged": False,
            "r9_action_time_confirmation_required_before_staging_or_send": True,
        },
        "limits": {
            "max_generation_requests": 1,
            "max_pad_runs": 2,
            "no_regeneration_or_manual_robin_repair": True,
            "stop_on_refusal_safety_issue_mismatch_or_unknown_result": True,
            "run2_requires_run1_terminal_comparison_and_artifact_preserved": True,
        },
        "acceptance": {
            "scope": "fixed EX03 text/number case and r9 package only",
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
        "cycle_id": "EX03-R9-G1",
        "base_commit": BASE_COMMIT,
        "checks": {
            "base_commit_matches_frozen_r9": True,
            "fixed_fixture_spec_request_expected_hashes_match": True,
            "r9_instruction_bundle_manifest_support_hashes_match": True,
            "r9_all_evidence_input_hashes_match": True,
            "r9_teaching_test_independence_pass": True,
            "r9_teaching_robin_and_script_byte_identical_to_r8": True,
            "r9_teaching_robin_bracket_backslashes_zero": True,
            "r9_fidelity_contract_in_bundle": True,
            "fixed_complete_answer_absent_from_r9_bundle": True,
            "grader_only_values_absent_from_submitted_body": True,
            "independent_example_data_absent_from_submitted_body": True,
            "independent_source_forbidden_runtime_actions_absent": True,
            "r8_one_send_consumed_and_no_resend": True,
            "r8_stop_before_run1_preserved": True,
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
