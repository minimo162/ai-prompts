#!/usr/bin/env python3
"""Prepare the separately identified EX03 r11 downloaded-file auxiliary run.

This is intentionally not a continuation or override of EX03-r11-G1.  It
records byte provenance for the downloaded file, freezes the pre-run state,
and creates a new evidence directory.  It never opens or runs PAD.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
SOURCE_CYCLE = BASE / "cycles/EX03-r11-G1"
AUX = BASE / "cycles/EX03-r11-file-aux1"
RUN = BASE / "runs/EX03-attempt1"
DOWNLOAD = Path.home() / "Downloads/ex03.robin"
BASE_COMMIT = "0b681b946ceafa9d938744a857d984fa8fff71e8"
GENERATED_SHA = "a1e07de1f9370640773fcd8d36db1a2effe602f175bb437cb7c65457f6f24875"
TEMPLATE_SHA = "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21"
FLOW_NAME = "RobinIssue38EX03R11FileAux1_20260917A"

FIXED_HASHES = {
    "instruction": (
        ROOT / "copilot/versions/20260917-excel-r11/agent-instructions.txt",
        "bceb1c7e4f47c0cd6a92ad698d08108175002bffcaaaff492a309ca74a122aa1",
    ),
    "bundle": (
        ROOT / "copilot/versions/20260917-excel-r11/knowledge/PAD-Robin-Knowledge-Bundle.txt",
        "2d95ce344ff66195061fd15010d13b75937888575fa2345fb543ae2115242f69",
    ),
    "manifest": (
        ROOT / "copilot/versions/20260917-excel-r11/manifest.json",
        "295306ea7e2e45da8cf77dec2784e94ea8ea8333da0df6a4000f83e9228b509e",
    ),
    "request": (
        BASE / "requests/EX03.txt",
        "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    ),
    "spec": (
        BASE / "spec.json",
        "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    ),
    "expected": (
        BASE / "expected.json",
        "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
    ),
    "input_a": (
        BASE / "fixtures/EX03/入力い.xlsx",
        "c71337956da22ec9e7d23e0c3161dfb0273878d69cf33d61d90e5db0f794d0f9",
    ),
    "input_b": (
        BASE / "fixtures/EX03/入力ろ.xlsx",
        "01598a797432469aa8712bbabdd4e6a875aaf6ea69fc161e1823469e250bd725",
    ),
    "template": (
        BASE / "fixtures/EX03/ひな形.xlsx",
        TEMPLATE_SHA,
    ),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), *args], text=True, encoding="utf-8"
    ).strip()


def main() -> None:
    if AUX.exists():
        raise ValueError(f"Auxiliary cycle already exists: {AUX}")
    if git("rev-parse", "HEAD") != BASE_COMMIT:
        raise ValueError("Auxiliary run must start at the fixed 0b681b9 checkpoint")
    allowed = {
        "?? tools/Prepare-Issue38Ex03R11FileAux.py",
        "?? tools/Capture-Issue38Ex03R11FileAuxPadRecopy.ps1",
    }
    status = {line for line in git("status", "--porcelain").splitlines() if line}
    if status != allowed:
        raise ValueError(f"Unexpected pre-auxiliary worktree changes: {sorted(status)}")

    for name, (path, expected) in FIXED_HASHES.items():
        actual = sha(path)
        if actual != expected:
            raise ValueError(f"Fixed {name} hash mismatch: {actual}")

    generated = SOURCE_CYCLE / "generated.robin"
    audit_path = SOURCE_CYCLE / "generation-safety-audit.json"
    verification_path = SOURCE_CYCLE / "verification.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    audit_sha = audit["inputs"]["generated_robin"]["sha256"]
    source_hashes = {
        "copilot_download": sha(DOWNLOAD),
        "preserved_generated_robin": sha(generated),
        "safety_audit_recorded_target": audit_sha,
    }
    if set(source_hashes.values()) != {GENERATED_SHA}:
        raise ValueError(f"Downloaded/source/audit Robin identity mismatch: {source_hashes}")
    if not audit["fidelity"]["downloaded_payload_static_fidelity_pass"]:
        raise ValueError("Preserved r11 static fidelity is not PASS")
    if not audit["target_workbook_and_side_effect_review"]["payload_static_safety_pass"]:
        raise ValueError("Preserved r11 static safety is not PASS")
    if audit["decision"]["status"] != "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD":
        raise ValueError("The preserved r11-G1 delivery-contract FAIL changed")
    if verification["live_acceptance"]["accepted"]:
        raise ValueError("The preserved r11-G1 record unexpectedly became accepted")
    for field in ("pad_import", "pad_save", "pad_recopy", "run1", "run2"):
        if verification["live_acceptance"][field] != "NOT_RUN":
            raise ValueError(f"Preserved r11-G1 {field} record changed")

    work = RUN / "work.xlsx"
    output = RUN / "照合結果.xlsx"
    if sha(work) != TEMPLATE_SHA:
        raise ValueError("Runtime work.xlsx does not match the frozen template")
    if output.exists():
        raise ValueError("Runtime output already exists before auxiliary Run1")

    tracked = [line for line in git("ls-files").splitlines() if line]
    protected_files = []
    for item in tracked:
        path = ROOT / item
        if path.is_file():
            protected_files.append({"path": item.replace("\\", "/"), "sha256": sha(path)})

    AUX.mkdir(parents=True, exist_ok=False)
    downloaded_copy = AUX / "copilot-downloaded-ex03.robin"
    downloaded_copy.write_bytes(DOWNLOAD.read_bytes())
    now = datetime.now(timezone.utc).astimezone().isoformat()
    write_json(
        AUX / "source-identity.json",
        {
            "schema_version": 1,
            "test_id": "EX03-R11-FILE-AUX1",
            "recorded_at": now,
            "source_cycle": "EX03-R11-G1",
            "source_cycle_formal_result": "FAIL_R11_REQUIRED_CODE_BLOCK_ABSENT_STOP_BEFORE_PAD",
            "download_path": str(DOWNLOAD),
            "preserved_generated_path": relative(generated),
            "safety_audit_path": relative(audit_path),
            "auxiliary_preserved_download_path": relative(downloaded_copy),
            "sha256": source_hashes,
            "all_three_identical": True,
            "download_copy_sha256": sha(downloaded_copy),
            "download_copy_exact": downloaded_copy.read_bytes() == generated.read_bytes(),
            "manual_reconstruction_or_repair": False,
        },
    )
    write_json(
        AUX / "plan.json",
        {
            "schema_version": 1,
            "test_id": "EX03-R11-FILE-AUX1",
            "prepared_at": now,
            "base_commit": BASE_COMMIT,
            "flow_name": FLOW_NAME,
            "source": {
                "version": "20260917-excel-r11",
                "generated_sha256": GENERATED_SHA,
                "static_fidelity": "PASS",
                "static_safety": "PASS",
                "unmodified_required": True,
            },
            "classification": {
                "kind": "SEPARATELY_IDENTIFIED_DOWNLOADED_FILE_AUXILIARY_PAD_VALIDATION",
                "formal_ex03_r11_g1_acceptance": False,
                "formal_ex03_r11_g1_fail_preserved": True,
                "may_not_offset_or_replace_formal_fail": True,
            },
            "limits": {
                "copilot_send": 0,
                "max_pad_runs": 2,
                "manual_robin_edit": 0,
                "candidate_version_change": 0,
                "github_write": 0,
                "run2_requires_run1_terminal_all_comparisons_pass_and_artifact_preserved": True,
                "stop_on_mismatch_safety_issue_or_unknown": True,
            },
            "fixed_runtime": {
                "work_path": relative(work),
                "work_sha256": sha(work),
                "template_sha256": TEMPLATE_SHA,
                "output_path": relative(output),
                "output_absent_before_run1": True,
            },
            "required_checks": [
                "PAD save and LF-normalized exact re-copy before Run1",
                "twelve saved/reopened JSON value-and-type matches",
                "fixed source/target values, types and positions",
                "outside cells, formulas, effective formatting and dimensions",
                "F6 System.String 100%, original format, empty prefix and no formula",
                "original inputs and frozen template SHA unchanged",
            ],
            "known_residuals_preserved": [
                "EX03-r11-G1 delivery-contract FAIL and PAD NOT_RUN",
                "legacy 558 raw comparison differences",
                "existing-output guard live path remains a separate unconfirmed claim",
                "no generalization beyond the fixed EX03 text/number case and this PAD environment",
            ],
        },
    )
    write_json(
        AUX / "preflight.json",
        {
            "schema_version": 1,
            "test_id": "EX03-R11-FILE-AUX1",
            "recorded_at": now,
            "status": "PASS_READY_FOR_DEDICATED_PAD_SAVE_RECOPY_THEN_AT_MOST_TWO_RUNS",
            "checks": {
                "head_is_fixed_checkpoint": True,
                "worktree_had_only_two_new_evidence_tools": True,
                "download_preserved_generated_and_audit_target_sha_identical": True,
                "source_copy_is_byte_exact": True,
                "r11_static_fidelity_pass": True,
                "r11_static_safety_pass": True,
                "r11_g1_formal_fail_and_no_pad_record_preserved": True,
                "fixed_version_request_spec_expected_fixtures_unchanged": True,
                "work_matches_frozen_template": True,
                "output_absent": True,
            },
            "flow_name": FLOW_NAME,
            "protected_tracked_file_count": len(protected_files),
        },
    )
    write_json(
        AUX / "protected-before.json",
        {
            "schema_version": 1,
            "test_id": "EX03-R11-FILE-AUX1",
            "recorded_at": now,
            "base_commit": BASE_COMMIT,
            "files": protected_files,
        },
    )
    print(json.dumps({
        "status": "PASS_READY_FOR_DEDICATED_PAD_SAVE_RECOPY",
        "test_id": "EX03-R11-FILE-AUX1",
        "flow_name": FLOW_NAME,
        "generated_sha256": GENERATED_SHA,
        "protected_tracked_files": len(protected_files),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
