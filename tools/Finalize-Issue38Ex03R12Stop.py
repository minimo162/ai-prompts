#!/usr/bin/env python3
"""Finalize the fail-closed EX03-r12-G1 generation result without PAD work."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CYCLE = BASE / "cycles/EX03-r12-G1"
RUN = BASE / "runs/EX03-attempt1"
VERSION = ROOT / "copilot/versions/20260917-excel-r12"
TEMPLATE_SHA = "881afa147fcdb5801aa83629988cc4314f773ef29697ff82401478229aaccd21"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json_new(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text_new(path: Path, value: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def main() -> None:
    outputs = [
        CYCLE / "protected-files-after.json",
        CYCLE / "verification.json",
        CYCLE / "acceptance-status.json",
        CYCLE / "review.md",
    ]
    if any(path.exists() for path in outputs):
        raise FileExistsError("Refusing to overwrite r12 final stop evidence")

    before = json.loads((CYCLE / "protected-files-before.json").read_bytes())
    mismatches: list[dict[str, object]] = []
    after_files: list[dict[str, object]] = []
    for record in before["files"]:
        path = ROOT / record["path"]
        current = sha256(path) if path.is_file() else None
        matches = current == record["sha256"]
        after_files.append({
            "path": record["path"],
            "before_sha256": record["sha256"],
            "after_sha256": current,
            "matches": matches,
        })
        if not matches:
            mismatches.append(after_files[-1])
    if mismatches:
        raise ValueError(f"Protected evidence changed: {mismatches[:5]}")

    audit = json.loads((CYCLE / "generation-safety-audit.json").read_bytes())
    result = json.loads((CYCLE / "generation-result.json").read_bytes())
    expected_decision = (
        "FAIL_GENERATED_ROBIN_MISMATCH_AND_POWERSHELL_PARSE_ERROR_STOP_BEFORE_PAD"
    )
    if audit["decision"] != expected_decision or result["decision"] != expected_decision:
        raise ValueError("Unexpected r12 generation decision")
    if audit["generation"]["send_count"] != 1:
        raise ValueError("r12 must record exactly one Copilot send")
    if not audit["delivery_contract"]["pass"]:
        raise ValueError("The observed r12 failure is payload fidelity, not delivery")
    if audit["adapted_source_comparison"]["exact_match"]:
        raise ValueError("Expected the generated Robin mismatch")
    if audit["powershell_parser"]["generated_error_count"] != 4:
        raise ValueError("Unexpected generated PowerShell parser-error count")
    if audit["structure"]["convert_to_json_compress_count"] != 0:
        raise ValueError("Corrupt output unexpectedly retained ConvertTo-Json -Compress")
    if audit["structure"]["corrupt_press_pipeline_count"] != 1:
        raise ValueError("Expected one corrupt press pipeline")
    if any(audit["stop"][key] for key in [
        "pad_save", "pad_recopy", "pad_run", "manual_repair", "resend",
        "successor_created", "github_write",
    ]):
        raise ValueError("A prohibited post-failure action was recorded")

    work = RUN / "work.xlsx"
    output = RUN / "照合結果.xlsx"
    if sha256(work) != TEMPLATE_SHA:
        raise ValueError("EX03 work copy changed despite stop-before-PAD")
    if output.exists():
        raise ValueError("EX03 output exists despite stop-before-PAD")
    run_files = sorted(path.name for path in RUN.iterdir() if path.is_file())
    if run_files != ["preparation.json", "work.xlsx"]:
        raise ValueError(f"Unexpected EX03 run artifacts: {run_files}")

    now = datetime.now().astimezone().isoformat()
    protected_after = {
        "schema_version": 1,
        "cycle_id": "EX03-r12-G1",
        "checked_at": now,
        "protected_file_count": len(after_files),
        "mismatch_count": 0,
        "files": after_files,
    }
    verification = {
        "schema_version": 1,
        "cycle_id": "EX03-r12-G1",
        "checked_at": now,
        "checks": {
            "normal_m365_send_exactly_once": True,
            "fixed_body_sha_matches": True,
            "same_version_bundle_sha_matches": True,
            "normal_chat_destination_and_think_deeper_observed": True,
            "response_completed_without_refusal": True,
            "single_text_code_block_copy_contract_pass": True,
            "copied_robin_unmodified_and_preserved": True,
            "prepared_source_exact_adaptation_match": False,
            "four_unauthorized_blank_line_deletions_detected": True,
            "convert_to_json_compress_corruption_detected": True,
            "powershell_ast_parser_error_count_is_four": True,
            "stop_before_pad_save_recopy_or_run": True,
            "work_copy_unchanged": True,
            "output_absent": True,
            "protected_prior_evidence_unchanged": True,
            "r11_failure_and_legacy_558_failure_preserved": True,
            "github_write_zero": True,
        },
        "artifacts": {
            name: {"path": rel(CYCLE / name), "sha256": sha256(CYCLE / name)}
            for name in [
                "submitted-body.txt", "live-send.json", "copilot-response.visible.txt",
                "response-dom-inspection.json", "generated.robin",
                "generation-safety-audit.json", "generation-result.json",
            ]
        },
    }
    acceptance = {
        "schema_version": 1,
        "cycle_id": "EX03-r12-G1",
        "version": "20260917-excel-r12",
        "status": expected_decision,
        "accepted": False,
        "candidate_commit": "0f6e47197ecb5f4316e00aa319efa6c4213f696f",
        "instruction_sha256": "11321acdbb96632221b02b7b737d12ba816ea4cf9f35f933a114c7f857539c06",
        "bundle_sha256": "ddee43a1eddc966f62095b63a23b135df184f3cbe0ded635cbf72520e6744b97",
        "submitted_body_sha256": "cf25fb4aa54375d992e00545d336058b67055ab7de934e52ce284dffcd9924cc",
        "generated_robin_sha256": sha256(CYCLE / "generated.robin"),
        "generation": {
            "send_count": 1,
            "send_limit": 1,
            "refusal": False,
            "delivery_contract_pass": True,
            "payload_static_safety_pass": False,
        },
        "pad": {
            "save": "NOT_RUN_STOP_CONDITION",
            "recopy": "NOT_RUN_STOP_CONDITION",
            "run1": "NOT_RUN_STOP_CONDITION",
            "run2": "NOT_RUN_STOP_CONDITION",
            "comparison": "NOT_RUN_STOP_CONDITION",
        },
        "reason": (
            "Unmodified Copilot Robin deleted four non-slot blank lines and changed "
            "ConvertTo-Json -Compress to invalid '| press'; AST parsing returned four errors."
        ),
        "manual_repair": False,
        "resend": False,
        "successor_created": False,
        "github_write": False,
        "remaining": [
            "EX03-r12-G1 is not accepted and cannot proceed to PAD under the fixed stop rule.",
            "No resend, repair, additional run, or successor is authorized by this task.",
            "The existing-output guard live path remains unverified for r12.",
            "Legacy 558 raw differences remain recorded as FAIL; no result here changes them.",
        ],
    }
    review = f"""# EX03-r12-G1 one-send result

## Outcome

`{expected_decision}`. The authorized normal Microsoft 365 Copilot send was used once. The response was not a refusal and exposed one code-preview block whose copied `text/plain` excluded the UI language badge, visual line numbers, and expansion control. The unmodified payload nevertheless failed the fixed fidelity and syntax gates, so no PAD save, re-copy, or Run was attempted.

## Fixed inputs

- candidate: `20260917-excel-r12` at `0f6e47197ecb5f4316e00aa319efa6c4213f696f`
- instruction SHA-256: `11321acdbb96632221b02b7b737d12ba816ea4cf9f35f933a114c7f857539c06`
- bundle SHA-256: `ddee43a1eddc966f62095b63a23b135df184f3cbe0ded635cbf72520e6744b97`
- submitted body SHA-256: `cf25fb4aa54375d992e00545d336058b67055ab7de934e52ce284dffcd9924cc`
- generated Robin SHA-256: `{sha256(CYCLE / 'generated.robin')}`

## New observations

- Send history: no local r12 cycle and no Copilot chat-search result for the full version ID before this cycle.
- Destination/model: normal Microsoft 365 Copilot new chat / Think Deeper.
- Send count: 1 of 1; no retry or regeneration.
- Delivery: one copyable code-preview block; clipboard content starts with a PAD action and ends with `END`.
- Fidelity: expected 276 lines versus generated 272 lines. Four blank lines outside the authorized data-slot substitutions were deleted.
- Blocking corruption: expected `[Console]::Out.Write([string]($result | ConvertTo-Json -Compress))''' ScriptOutput=> PowershellOutput`; generated `[Console]::Out.Write([string]($result | press)''' ScriptOutput=> PowershellOutput`.
- PowerShell AST: prepared script 0 errors; generated embedded script 4 errors (missing closing parenthesis and three cascading missing braces).
- PAD: save 0, re-copy 0, Run1 0, Run2 0, comparison 0.
- Run workspace: `work.xlsx` remains SHA-256 `{sha256(work)}` and `照合結果.xlsx` is absent.
- Protected evidence: {len(after_files)} files checked, mismatch 0.

## Preserved scope

r11's formal delivery-contract failure, its separately identified auxiliary result, the legacy 558 raw-difference failure, fixed request/spec/expected data, and all older evidence remain unchanged. The generated payload was not repaired, and no successor candidate or GitHub write was made.
"""

    write_json_new(outputs[0], protected_after)
    write_json_new(outputs[1], verification)
    write_json_new(outputs[2], acceptance)
    write_text_new(outputs[3], review)
    print(expected_decision)


if __name__ == "__main__":
    main()
