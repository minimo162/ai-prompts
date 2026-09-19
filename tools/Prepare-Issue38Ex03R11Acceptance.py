#!/usr/bin/env python3
"""Prepare and verify the fixed EX03-r11-G1 live-acceptance checkpoint.

Preparation is local only.  It fixes the exact body, same-version bundle,
fixtures, work copy, protected evidence, one-generation/two-run limits, and
fail-closed gates.  It never opens a browser, uploads, sends, or runs PAD.
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
CYCLE = BASE / "cycles/EX03-r11-G1"
RUN = BASE / "runs/EX03-attempt1"
VERSION = ROOT / "copilot/versions/20260917-excel-r11"
LOCAL_PROBE = BASE / "probes/ex03-r11-minimal-powershell"
BASE_COMMIT = "659ae9db649d33226d4bf9220965e263e34ee323"

EXPECTED = {
    "manifest": "295306ea7e2e45da8cf77dec2784e94ea8ea8333da0df6a4000f83e9228b509e",
    "instruction": "bceb1c7e4f47c0cd6a92ad698d08108175002bffcaaaff492a309ca74a122aa1",
    "bundle": "2d95ce344ff66195061fd15010d13b75937888575fa2345fb543ae2115242f69",
    "robin_support": "148267f09f53d74db1059cee823a4a2e159f2bbebfa249d3a25c996796fa765b",
    "script_support": "068e676d70c373a9cf8203d19f6154e38460f609c4fdf774dbef1528f68fc7ae",
    "contract_support": "ffbe75f9803435c55341f2d7db73e85b5ce5ec961f637734da38b6ee332a1ec9",
    "local_acceptance": "eb2b96096dbab2f9bdbc8747cff8d5427ddd60c5e9e9bfc8e80f3987e5c56c16",
    "request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    "input_a": "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    "input_b": "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
    "template": "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21",
}

ROBIN_SUPPORT = VERSION / "support/EX03-R11-Independent-PAD-Recopy.robin"
SCRIPT_SUPPORT = VERSION / "support/EX03-R11-Independent-Minimal-FormatSandwich.ps1.txt"
CONTRACT_SUPPORT = VERSION / "support/EX03-R11-Minimal-Structural-Contract.txt"

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
UNIQUE_GRADER_VALUES = ["春", "夏", "秋", "項目甲", "項目乙", "-4.5", "6.25"]
GRADER_ONLY_VALUES = UNIQUE_GRADER_VALUES + ["100%"]
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
    "Start-Process",
    "Remove-Item",
]
TOKEN_COUNTS = {
    "[string]": 12,
    "[bool]": 2,
    "[void]": 6,
    "[Runtime.InteropServices.Marshal]": 7,
    "[IO.Path]": 2,
    "::GetFullPath(": 2,
    "-ieq": 1,
    "$matches[0]": 1,
    "$beforeNumberFormat": 3,
}
REQUIRED_FRAGMENTS = [
    "if ([IO.Path]::GetFullPath([string]$candidate.FullName) -ieq $targetPath) { $matches += $candidate }",
    "$cell.Value2 = [string]$payload.probe",
    "finally { $cell.NumberFormat = $beforeNumberFormat }",
    "$cell.Value2 -isnot [string]",
    "if ([string]$cell.PrefixCharacter -cne \\'\\')",
]
FORBIDDEN_FRAGMENTS = [
    "[string]::Equals(",
    "[StringComparison]::OrdinalIgnoreCase",
    "[string]::IsNullOrEmpty(",
    ":Equals([IO.Path]",
    "-not :IsNullOrEmpty(",
    "[IO.Path]::GetFulling]",
]


def load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load("issue38_excel_oracle_r11", "tools/Verify-Issue38Excel.py")
source_tool = load(
    "issue38_ex03_r11_source_tool",
    "tools/Prepare-Issue38Ex03R8IndependentSource.py",
)
parser_tool = load(
    "issue38_ex03_r11_parser_tool",
    "tools/Analyze-Issue38Ex03R10Generation.py",
)


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


def package_paths() -> dict[str, Path]:
    return {
        "manifest": VERSION / "manifest.json",
        "instruction": VERSION / "agent-instructions.txt",
        "bundle": VERSION / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
        "robin_support": ROBIN_SUPPORT,
        "script_support": SCRIPT_SUPPORT,
        "contract_support": CONTRACT_SUPPORT,
        "local_acceptance": LOCAL_PROBE / "acceptance.json",
    }


def fixed_paths() -> dict[str, Path]:
    return {
        "request": BASE / "requests/EX03.txt",
        "spec": BASE / "spec.json",
        "expected": BASE / "expected.json",
        "input_a": BASE / "fixtures/EX03/入力い.xlsx",
        "input_b": BASE / "fixtures/EX03/入力ろ.xlsx",
        "template": BASE / "fixtures/EX03/ひな形.xlsx",
    }


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
        ROOT / "copilot/versions/20260917-excel-r9",
        ROOT / "copilot/versions/20260917-excel-r10",
        VERSION,
        BASE / "cycles/EX03-r5-G1",
        BASE / "cycles/EX03-r6-G1",
        BASE / "cycles/EX03-r8-G1",
        BASE / "cycles/EX03-r9-G1",
        BASE / "cycles/EX03-r10-G1",
        BASE / "probes/ex03-r7-robin-source",
        BASE / "probes/ex03-r8-independent-source",
        BASE / "probes/ex03-r9-escape-fidelity",
        BASE / "probes/ex03-r10-structural-fidelity",
        LOCAL_PROBE,
        BASE / "probes/percent-text-write",
    ]
    paths = list(fixed)
    for tree in trees:
        paths.extend(sorted(path for path in tree.rglob("*") if path.is_file()))
    unique = {path.resolve(): path for path in paths}
    return [unique[key] for key in sorted(unique, key=lambda item: str(item).lower())]


def assert_head_and_clean() -> str:
    head = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if head != BASE_COMMIT:
        raise ValueError(f"Expected base commit {BASE_COMMIT}, found {head}")
    status = subprocess.check_output(
        ["git", "-C", str(ROOT), "status", "--porcelain"], text=True
    )
    allowed = {"?? tools/Prepare-Issue38Ex03R11Acceptance.py"}
    actual = {line for line in status.splitlines() if line}
    if actual != allowed:
        raise ValueError(f"Unexpected pre-cycle worktree changes: {sorted(actual)}")
    return head


def validate_fixed_state() -> dict[str, object]:
    oracle.check_frozen()
    package = package_paths()
    fixed = fixed_paths()
    for key, path in {**package, **fixed}.items():
        if sha(path) != EXPECTED[key]:
            raise ValueError(f"Fixed {key} hash mismatch: {sha(path)}")

    manifest = json.loads(package["manifest"].read_bytes())
    local_acceptance = json.loads(package["local_acceptance"].read_bytes())
    if manifest["version"] != "20260917-excel-r11":
        raise ValueError("Unexpected r11 candidate version")
    if manifest["inherits_live_acceptance"]:
        raise ValueError("r11 must not inherit live acceptance")
    if manifest["status"] != (
        "LOCAL_CANDIDATE_EX03_MINIMAL_POWERSHELL_PAD_RECOPIED_"
        "SYNTHETIC_VALIDATED_NOT_COPILOT_OR_INTEGRATED_ACCEPTED"
    ):
        raise ValueError("r11 status no longer marks live acceptance as unproven")
    if manifest["evidence"]["teaching_test_independence"] != (
        "PASS_R11_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_INSTRUCTION_BUNDLE_AND_SUPPORT"
    ):
        raise ValueError("r11 teaching/test independence is not passing")
    if local_acceptance["decision"]["accepted_for_copilot_ex03"]:
        raise ValueError("Local synthetic evidence is being misused as live EX03 acceptance")
    if local_acceptance["scope"]["copilot_send"] != 0:
        raise ValueError("The r11 local probe unexpectedly records a Copilot send")
    if local_acceptance["scope"]["integrated_ex03_run"] != 0:
        raise ValueError("The r11 local probe unexpectedly records an integrated EX03 run")

    for record in manifest["source_files"]:
        if sha(VERSION / record["path"]) != record["sha256"]:
            raise ValueError("r11 source mismatch: " + record["path"])
    for record in manifest["support_files"]:
        if sha(VERSION / record["path"]) != record["sha256"]:
            raise ValueError("r11 support mismatch: " + record["path"])
    for path, expected_hash in manifest["evidence_inputs"].items():
        if sha(ROOT / path) != expected_hash:
            raise ValueError("r11 evidence input changed: " + path)

    instruction_text = package["instruction"].read_text(encoding="utf-8")
    bundle_text = package["bundle"].read_text(encoding="utf-8")
    robin_text = ROBIN_SUPPORT.read_text(encoding="utf-8")
    script_text = SCRIPT_SUPPORT.read_text(encoding="utf-8")
    decoded = source_tool.decode_robin_string(
        source_tool.action_payload(source_tool.extract_action(robin_text))
    )
    if decoded.replace("\r\n", "\n").rstrip("\n") != script_text.replace(
        "\r\n", "\n"
    ).rstrip("\n"):
        raise ValueError("r11 teaching Robin does not decode exactly to support script")
    if parser_tool.parse_powershell(decoded):
        raise ValueError("r11 teaching PowerShell no longer parses cleanly")

    for token, count in TOKEN_COUNTS.items():
        if robin_text.count(token) != count:
            raise ValueError(f"r11 teaching token count changed: {token}")
    for fragment in REQUIRED_FRAGMENTS:
        if robin_text.count(fragment) != 1:
            raise ValueError(f"r11 teaching required fragment changed: {fragment}")
    for fragment in FORBIDDEN_FRAGMENTS:
        if fragment in robin_text:
            raise ValueError(f"r11 teaching contains retired/corrupt fragment: {fragment}")
    forbidden_actions = [
        value
        for value in FORBIDDEN_RUNTIME_ACTIONS
        if value in robin_text or value in script_text
    ]
    if forbidden_actions:
        raise ValueError(f"Unsafe runtime action in r11 source: {forbidden_actions}")
    if robin_text.count("Scripting.RunPowershellScript.RunScript") != 1:
        raise ValueError("r11 teaching RunScript count changed")
    if robin_text.count("Excel.WriteToExcel.WriteCell Instance: Work Value: NumberSource") != 5:
        raise ValueError("r11 teaching numeric-write count changed")
    if robin_text.count("_ValueTypeMatch TO SourceCellJson = SavedCellJson") != 12:
        raise ValueError("r11 teaching JSON comparison count changed")

    fixed_bundle_leaks = [value for value in FIXED_COMPLETION_TERMS if value in bundle_text]
    if fixed_bundle_leaks:
        raise ValueError(f"Fixed EX03 complete-answer terms leaked into bundle: {fixed_bundle_leaks}")
    unique_bundle_leaks = [value for value in UNIQUE_GRADER_VALUES if value in bundle_text]
    if unique_bundle_leaks:
        raise ValueError(f"Unique grader-only values leaked into bundle: {unique_bundle_leaks}")
    for value in FIXED_COMPLETION_TERMS + GRADER_ONLY_VALUES:
        if value in instruction_text or value in robin_text or value in script_text:
            raise ValueError(f"Fixed answer leaked into r11 instruction/source: {value}")

    work = RUN / "work.xlsx"
    output = RUN / "照合結果.xlsx"
    if not work.is_file() or sha(work) != EXPECTED["template"]:
        raise ValueError("EX03 work copy must match the frozen template")
    if output.exists():
        raise ValueError("EX03 output must be absent before the live cycle")
    return {
        "manifest": manifest,
        "package": package,
        "fixed": fixed,
        "work": work,
        "output": output,
        "robin_text": robin_text,
    }


def prepare(destination: Path = CYCLE) -> dict[str, object]:
    destination = Path(destination)
    if destination.exists():
        raise ValueError(f"Cycle already exists; refusing overwrite: {destination}")
    head = assert_head_and_clean()
    state = validate_fixed_state()
    manifest = state["manifest"]
    package = state["package"]
    fixed = state["fixed"]
    work = state["work"]
    output = state["output"]
    robin_text = state["robin_text"]

    body = package["instruction"].read_bytes() + b"\n" + fixed["request"].read_bytes() + b"\n"
    body_text = body.decode("utf-8")
    leaked_values = [value for value in GRADER_ONLY_VALUES if value in body_text]
    if leaked_values:
        raise ValueError(f"Grader-only values leaked into submitted body: {leaked_values}")
    leaked_example = [value for value in INDEPENDENT_EXAMPLE_TERMS if value in body_text]
    if leaked_example:
        raise ValueError(f"Independent example data leaked into submitted body: {leaked_example}")

    protected_list = protected_paths()
    protected = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-G1",
        "base_commit": BASE_COMMIT,
        "files": [
            {"path": repo_path(path), "sha256": sha(path)} for path in protected_list
        ],
    }
    destination.mkdir(parents=True, exist_ok=False)
    submitted = destination / "submitted-body.txt"
    write_bytes(submitted, body)
    canonical_body = CYCLE / "submitted-body.txt"

    plan = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-G1",
        "base_commit": BASE_COMMIT,
        "purpose": "One authorized normal-M365 generation and at-most-two unmodified dedicated-PAD runs for fixed EX03 using frozen r11",
        "candidate": {
            "version": manifest["version"],
            "instruction_path": repo_path(package["instruction"]),
            "instruction_sha256": sha(package["instruction"]),
            "bundle_path": repo_path(package["bundle"]),
            "bundle_sha256": sha(package["bundle"]),
            "manifest_path": repo_path(package["manifest"]),
            "manifest_sha256": sha(package["manifest"]),
            "robin_support_path": repo_path(ROBIN_SUPPORT),
            "robin_support_sha256": sha(ROBIN_SUPPORT),
            "script_support_path": repo_path(SCRIPT_SUPPORT),
            "script_support_sha256": sha(SCRIPT_SUPPORT),
            "contract_support_path": repo_path(CONTRACT_SUPPORT),
            "contract_support_sha256": sha(CONTRACT_SUPPORT),
            "inherits_live_acceptance": False,
        },
        "fixed_inputs": {
            "request": {"path": repo_path(fixed["request"]), "sha256": sha(fixed["request"])},
            "spec": {"path": repo_path(fixed["spec"]), "sha256": sha(fixed["spec"])},
            "grader_only_expected": {
                "path": repo_path(fixed["expected"]),
                "sha256": sha(fixed["expected"]),
                "send_to_copilot": False,
            },
            "input_a": {"path": repo_path(fixed["input_a"]), "sha256": sha(fixed["input_a"])},
            "input_b": {"path": repo_path(fixed["input_b"]), "sha256": sha(fixed["input_b"])},
            "template": {"path": repo_path(fixed["template"]), "sha256": sha(fixed["template"])},
            "work": {
                "path": repo_path(work),
                "sha256": sha(work),
                "must_match_template_before_each_run": True,
            },
            "output": {
                "path": repo_path(output),
                "must_be_absent_before_each_run": True,
            },
        },
        "submission": {
            "body_path": repo_path(canonical_body),
            "body_sha256": sha(submitted),
            "body_contract": "unchanged full r11 instructions followed by unchanged fixed EX03 request",
            "attachment_path": repo_path(package["bundle"]),
            "attachment_sha256": sha(package["bundle"]),
            "normal_m365_new_chat": True,
            "model": "Think Deeper",
            "grader_only_expected_excluded": True,
            "fixed_completed_robin_excluded": True,
            "independent_teaching_robin_in_bundle": True,
        },
        "authorization": {
            "explicit_user_authorization_received": True,
            "r11_normal_m365_send_count": 0,
            "r11_browser_staged": False,
            "computer_use_action_time_confirmation_required_before_send": True,
        },
        "limits": {
            "max_generation_requests": 1,
            "max_pad_runs": 2,
            "no_regeneration_or_manual_robin_repair": True,
            "stop_on_refusal_safety_issue_mismatch_or_unknown_result": True,
            "run2_requires_run1_terminal_comparison_and_artifact_preserved": True,
            "no_successful_probe_or_old_version_result_inheritance": True,
            "no_automatic_successor": True,
        },
        "acceptance": {
            "scope": "fixed EX03 text/number case and r11 package only",
            "required": [
                "one normal-M365 send with exact full body and actual same-version bundle",
                "unmodified generated Robin passes syntax, structure, target-workbook and bounded-side-effect gates",
                "one new dedicated Power Fx OFF flow, save and LF-normalized exact re-copy before Run1",
                "Run1 terminal confirmation, all comparison gates and artifact preservation before Run2",
                "at most two runs with all twelve source/readback JSON type comparisons true",
                "all fixed values, types, positions, outside cells, formulas and effective formats",
                "F6 exact System.String 100%, original format, empty prefix and no formula",
                "all protected input/template SHA values unchanged",
            ],
            "legacy_558_failure_preserved": True,
            "existing_output_guard_live_path_still_required": True,
        },
        "external_actions": {
            "browser_staging": 0,
            "bundle_upload": 0,
            "copilot_send": 0,
            "pad_import": 0,
            "pad_save": 0,
            "pad_recopy": 0,
            "pad_run": 0,
            "github_write": 0,
        },
        "status": "READY_LOCAL_PREFLIGHT_SEND_REQUIRES_COMPUTER_USE_ACTION_TIME_CONFIRMATION",
    }
    preflight = {
        "schema_version": 1,
        "cycle_id": "EX03-R11-G1",
        "base_commit": head,
        "checks": {
            "head_matches_659ae9d": True,
            "worktree_clean_before_cycle_creation": True,
            "fixed_fixture_spec_request_expected_hashes_match": True,
            "r11_instruction_bundle_manifest_support_hashes_match": True,
            "r11_all_evidence_input_hashes_match": True,
            "r11_teaching_test_independence_pass": True,
            "r11_teaching_robin_decodes_exactly_and_parser_zero": True,
            "r11_structural_token_required_forbidden_gate_pass": True,
            "fixed_complete_answer_absent_from_bundle": True,
            "grader_only_values_absent_from_submitted_body": True,
            "independent_example_data_absent_from_submitted_body": True,
            "independent_source_forbidden_runtime_actions_absent": True,
            "local_synthetic_success_not_inherited_as_ex03_acceptance": True,
            "work_exists_and_matches_template": True,
            "output_absent": True,
        },
        "hashes": {
            "submitted_body": sha(submitted),
            "instruction": sha(package["instruction"]),
            "bundle": sha(package["bundle"]),
            "manifest": sha(package["manifest"]),
            "robin_support": sha(ROBIN_SUPPORT),
            "script_support": sha(SCRIPT_SUPPORT),
            "contract_support": sha(CONTRACT_SUPPORT),
            "work_and_template": sha(work),
            "input_a": sha(fixed["input_a"]),
            "input_b": sha(fixed["input_b"]),
        },
        "counts": {
            "protected_files": len(protected_list),
            "submitted_body_utf16_units": len(body_text.encode("utf-16-le")) // 2,
            "submitted_body_utf8_bytes": len(body),
            "submitted_body_lines": len(body_text.splitlines()),
            "teaching_backslash_open_bracket": robin_text.count(r"\["),
            "teaching_backslash_close_bracket": robin_text.count(r"\]"),
            "structural_tokens": TOKEN_COUNTS,
            "required_fragments": len(REQUIRED_FRAGMENTS),
            "forbidden_fragments": len(FORBIDDEN_FRAGMENTS),
        },
        "decision": {
            "local_checkpoint": "PASS",
            "browser_staging": "NOT_STARTED",
            "send": "NOT_SENT_ACTION_TIME_CONFIRMATION_REQUIRED",
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
        "submitted_body_sha256": sha(submitted),
        "submitted_body_utf16_units": preflight["counts"]["submitted_body_utf16_units"],
        "bundle_sha256": sha(package["bundle"]),
        "manifest_sha256": sha(package["manifest"]),
        "protected_file_count": len(protected_list),
        "status": plan["status"],
    }


def verify(cycle: Path = CYCLE) -> dict[str, object]:
    cycle = Path(cycle)
    required = [
        cycle / "plan.json",
        cycle / "preflight.json",
        cycle / "protected-files-before.json",
        cycle / "submitted-body.txt",
    ]
    if not all(path.is_file() for path in required):
        raise ValueError("The r11 live checkpoint is incomplete")
    state = validate_fixed_state()
    plan = json.loads((cycle / "plan.json").read_bytes())
    preflight = json.loads((cycle / "preflight.json").read_bytes())
    protected = json.loads((cycle / "protected-files-before.json").read_bytes())
    if plan["cycle_id"] != "EX03-R11-G1" or preflight["cycle_id"] != "EX03-R11-G1":
        raise ValueError("Unexpected r11 cycle identity")
    if plan["base_commit"] != BASE_COMMIT or preflight["base_commit"] != BASE_COMMIT:
        raise ValueError("Unexpected r11 base commit")
    if plan["candidate"]["version"] != "20260917-excel-r11":
        raise ValueError("Unexpected r11 version")
    if any(plan["external_actions"].values()):
        raise ValueError("The local checkpoint already records an external action")
    if not all(preflight["checks"].values()):
        raise ValueError("An r11 preflight check is not passing")
    expected_body = (
        state["package"]["instruction"].read_bytes()
        + b"\n"
        + state["fixed"]["request"].read_bytes()
        + b"\n"
    )
    body = cycle / "submitted-body.txt"
    if body.read_bytes() != expected_body:
        raise ValueError("Submitted body is not exact r11 instructions plus fixed request")
    if sha(body) != plan["submission"]["body_sha256"]:
        raise ValueError("Submitted body hash differs from plan")
    if sha(state["package"]["bundle"]) != plan["submission"]["attachment_sha256"]:
        raise ValueError("Same-version attachment hash differs from plan")
    if sha(state["work"]) != plan["fixed_inputs"]["work"]["sha256"]:
        raise ValueError("EX03 work copy differs from checkpoint")
    if state["output"].exists():
        raise ValueError("EX03 output exists before Run1")
    mismatches = []
    for record in protected["files"]:
        path = ROOT / record["path"]
        if not path.is_file():
            mismatches.append({"path": record["path"], "status": "MISSING"})
        elif sha(path) != record["sha256"]:
            mismatches.append({"path": record["path"], "status": "HASH_MISMATCH"})
    if mismatches:
        raise ValueError(f"Protected r11 checkpoint drift: {mismatches[:3]}")
    return {
        "schema_version": 1,
        "cycle_id": "EX03-R11-G1",
        "status": "PASS_LOCAL_CHECKPOINT_READY_FOR_BROWSER_STAGING",
        "base_commit": BASE_COMMIT,
        "head": subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip(),
        "submitted_body_sha256": sha(body),
        "bundle_sha256": sha(state["package"]["bundle"]),
        "manifest_sha256": sha(state["package"]["manifest"]),
        "protected_file_count": len(protected["files"]),
        "protected_mismatch_count": 0,
        "work_matches_template": True,
        "output_absent": True,
        "recorded_external_actions": plan["external_actions"],
        "send_authorized_by_user": True,
        "computer_use_action_time_confirmation_still_required": True,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = verify() if args.verify else prepare()
    print(json.dumps(result, ensure_ascii=False, indent=2))
