#!/usr/bin/env python3
"""Record the A3-G1 fail-closed stop that occurred before any Copilot send."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalog/acceptance/issue38"
CYCLE = BASE / "cycles/EX03-r12-fixed-helper-A3-G1"
RUNTIME = BASE / "probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T1/runtime"
WORK = RUNTIME / "work.xlsx"
OUTPUT = RUNTIME / "照合結果.xlsx"
TEMPLATE = BASE / "fixtures/EX03/ひな形.xlsx"

CYCLE_ID = "EX03-R12-FIXED-HELPER-COPILOT-A3-G1"
STOP_STATUS = "STOPPED_BEFORE_SEND_COMPUTER_USE_URL_UNVERIFIED"
COMPUTER_USE_ERROR = (
    "Computer Use has been stopped for this turn because it could not determine "
    "the current browser URL on Windows with enough confidence to enforce policy."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, value: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(value)


def main() -> int:
    if not CYCLE.is_dir():
        raise FileNotFoundError(f"Prepared A3-G1 cycle is absent: {CYCLE}")
    for name in ("history-check.json", "live-send.json", "generation-assessment.json", "post-stop-integrity.json", "RESULT.md"):
        if (CYCLE / name).exists():
            raise FileExistsError(f"A3-G1 stop record already exists: {name}")

    protected_before = json.loads((CYCLE / "protected-before.json").read_text(encoding="utf-8"))
    mismatches: list[dict[str, str]] = []
    checked: list[dict[str, object]] = []
    for record in protected_before["files"]:
        path = ROOT / record["path"]
        if not path.is_file():
            mismatches.append({"path": record["path"], "reason": "MISSING"})
            continue
        current_sha = sha256(path)
        current_bytes = path.stat().st_size
        same = current_sha == record["sha256"] and current_bytes == record["bytes"]
        checked.append({"path": record["path"], "sha256": current_sha, "bytes": current_bytes, "matches_before": same})
        if not same:
            mismatches.append({"path": record["path"], "reason": "SHA_OR_SIZE_CHANGED"})

    handoffs = [RUNTIME / f"source-{index}.json" for index in range(1, 8)] + [RUNTIME / "mode.json"]
    runtime = {
        "work_sha256": sha256(WORK),
        "template_sha256": sha256(TEMPLATE),
        "work_matches_template": sha256(WORK) == sha256(TEMPLATE),
        "output_absent": not OUTPUT.exists(),
        "handoff_absent": all(not path.exists() for path in handoffs),
        "handoff_present": [str(path) for path in handoffs if path.exists()],
    }
    if mismatches or not runtime["work_matches_template"] or not runtime["output_absent"] or not runtime["handoff_absent"]:
        raise ValueError(f"Protected state changed before finalizing stop: mismatches={mismatches}, runtime={runtime}")

    now = datetime.now(timezone.utc).astimezone().isoformat()
    write_json(CYCLE / "history-check.json", {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "recorded_at": now,
        "local_previous_cycle_or_send_record_found_before_prepare": False,
        "ui_history_checked": False,
        "ui_history_result": "NOT_CONFIRMED_COMPUTER_USE_STOPPED_BEFORE_URL_VERIFICATION",
        "send_allowed_after_history_gate": False,
    })
    write_json(CYCLE / "live-send.json", {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "recorded_at": now,
        "status": STOP_STATUS,
        "target": "NORMAL_MICROSOFT_365_COPILOT_CHAT",
        "observed_window": {
            "app": "Chrome",
            "title": "チャット | Microsoft Copilot - Google Chrome",
            "candidate_window_count": 1,
            "current_url_verified": False,
        },
        "computer_use_error": COMPUTER_USE_ERROR,
        "body_entered": False,
        "bundle_attached": False,
        "send_button_clicked": False,
        "send_count": 0,
        "send_limit_total": 1,
        "send_limit_consumed": False,
        "response_observed": False,
    })
    write_json(CYCLE / "generation-assessment.json", {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "recorded_at": now,
        "final_status": STOP_STATUS,
        "generation": "NOT_RUN",
        "copilot_response": "NOT_AVAILABLE_NO_SEND",
        "text_code_block_count": 0,
        "generated_robin": False,
        "generated_robin_sha256": None,
        "safety_audit": "NOT_RUN_NO_GENERATED_ROBIN",
        "pad_save": "NOT_RUN",
        "pad_recopy": "NOT_RUN",
        "pad_run1": "NOT_RUN",
        "pad_run2": "NOT_RUN",
        "pad_run_count": 0,
        "stop_reason": COMPUTER_USE_ERROR,
        "resend_performed": False,
        "manual_generated_robin_edit": False,
        "next_candidate_created": False,
        "github_write": False,
    })
    write_json(CYCLE / "post-stop-integrity.json", {
        "schema_version": 1,
        "cycle_id": CYCLE_ID,
        "recorded_at": now,
        "status": "PASS_NO_TRANSMISSION_OR_RUNTIME_MUTATION",
        "protected_file_count": len(checked),
        "protected_mismatch_count": len(mismatches),
        "protected_mismatches": mismatches,
        "files": checked,
        "runtime": runtime,
    })
    write_text(CYCLE / "RESULT.md", f"""# {CYCLE_ID} result

## Decision

`{STOP_STATUS}`

The fixed A3 candidate passed the local preflight. One Chrome window titled `チャット | Microsoft Copilot - Google Chrome` was returned, but Computer Use could not determine its current URL with enough confidence and stopped the UI turn. The normal Microsoft 365 Copilot destination and send history therefore could not be confirmed. No body text was entered, no bundle was attached, and Send was not clicked.

## Counts

- Copilot send: 0 / 1
- Copilot response: NOT_AVAILABLE_NO_SEND
- generated Robin: none
- PAD save/re-copy: NOT_RUN
- PAD Run1: NOT_RUN
- PAD Run2: NOT_RUN
- GitHub write: 0

## Integrity

- Protected files checked: {len(checked)}
- Protected mismatches: 0
- Work matches the fixed template: true
- Output absent: true
- Eight JSON handoff files absent: true

No resend, manual edit, additional run, next candidate, or fixed-condition change was performed.
""")
    print(json.dumps({
        "status": STOP_STATUS,
        "send_count": 0,
        "pad_run_count": 0,
        "protected_file_count": len(checked),
        "protected_mismatch_count": len(mismatches),
        "work_sha256": runtime["work_sha256"],
        "output_absent": runtime["output_absent"],
        "handoff_absent": runtime["handoff_absent"],
    }, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
