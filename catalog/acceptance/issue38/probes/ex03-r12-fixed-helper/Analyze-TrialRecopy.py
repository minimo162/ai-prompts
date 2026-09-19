#!/usr/bin/env python3
"""Classify the saved PAD re-copy mismatch without another paste, copy, or Run."""

from __future__ import annotations

import difflib
import hashlib
import importlib.util
import json
from pathlib import Path


PROBE = Path(__file__).resolve().parent
ROOT = PROBE.parents[4]
TRIAL = PROBE / "trials/EX03-R12-FIXED-HELPER-P1-T1"
CANDIDATE = TRIAL / "candidate.robin"
RECOPY = TRIAL / "pad-recopy-mismatch.robin"
MISMATCH = TRIAL / "pad-recopy-mismatch.json"
ANALYSIS = TRIAL / "pad-recopy-diff-analysis.json"
BUILDER_PATH = ROOT / "tools/Build-Issue38Ex03CandidateR12.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load("issue38_fixed_helper_recopy_builder", BUILDER_PATH)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def normalized(value: str, trim_final: bool = False) -> str:
    result = value.replace("\r\n", "\n")
    return result.rstrip("\r\n") if trim_final else result


def main() -> int:
    if ANALYSIS.exists():
        raise FileExistsError(f"Refusing to overwrite analysis: {ANALYSIS}")
    mismatch = json.loads(MISMATCH.read_text(encoding="utf-8"))
    if mismatch["decision"] != "STOP_PAD_RECOPY_NOT_BYTE_EXACT_NO_RUN":
        raise ValueError("Mismatch record no longer carries the required stop decision")

    candidate = exact_text(CANDIDATE)
    recopy = exact_text(RECOPY)
    before = normalized(candidate, trim_final=True).split("\n")
    after = normalized(recopy, trim_final=True).split("\n")
    hunks: list[dict[str, object]] = []
    for tag, a1, a2, b1, b2 in difflib.SequenceMatcher(None, before, after).get_opcodes():
        if tag != "equal":
            hunks.append({
                "operation": tag,
                "candidate_lines": [a1 + 1, a2],
                "recopy_lines": [b1 + 1, b2],
                "candidate": before[a1:a2],
                "recopy": after[b1:b2],
            })

    candidate_script = builder.embedded_script(candidate)
    recopy_script = builder.embedded_script(recopy)
    expected_candidate_line = (
        "$expectedSuccess = \\'{\"status\":\"OK\",\"mode\":\"NORMAL\"," 
        "\"text_writes\":7,\"formats_restored\":true}\\'"
    )
    expected_recopy_line = expected_candidate_line.replace('"', '\\"')
    if hunks != [{
        "operation": "replace",
        "candidate_lines": [48, 48],
        "recopy_lines": [48, 48],
        "candidate": [expected_candidate_line],
        "recopy": [expected_recopy_line],
    }]:
        raise ValueError(f"Unexpected saved re-copy content drift: {hunks!r}")
    if candidate_script != recopy_script:
        raise ValueError("PAD re-copy changes the decoded launcher script")

    result = {
        "schema_version": 1,
        "trial_id": "EX03-R12-FIXED-HELPER-P1-T1",
        "decision": "STOP_REQUIRED_EXACT_RECOPY_CONTRACT_FAILED",
        "supersedes": {
            "path": "catalog/acceptance/issue38/probes/ex03-r12-fixed-helper/trials/EX03-R12-FIXED-HELPER-P1-T1/pad-recopy-diff-analysis-superseded-newline-read.json",
            "reason": "The first analysis used universal-newline text reads for the line-ending summary. Its content hunk and stop decision remain valid; this record uses exact newline reads.",
        },
        "candidate_sha256": sha256(CANDIDATE),
        "recopy_sha256": sha256(RECOPY),
        "content_diff_hunks_ignoring_line_endings_and_final_newline": hunks,
        "content_diff_hunk_count": len(hunks),
        "classification": {
            "robin_double_quote_canonicalization": (
                "PAD added Robin backslash escaping to the eight JSON double quotes "
                "in the launcher expectedSuccess assignment"
            ),
            "decoded_embedded_launcher_exact": True,
            "line_ending_serialization": {
                "candidate_crlf": candidate.count("\r\n"),
                "candidate_lf_only": candidate.count("\n") - candidate.count("\r\n"),
                "candidate_final_newline": candidate.endswith(("\r", "\n")),
                "recopy_crlf": recopy.count("\r\n"),
                "recopy_lf_only": recopy.count("\n") - recopy.count("\r\n"),
                "recopy_final_newline": recopy.endswith(("\r", "\n")),
            },
            "semantic_equivalence_does_not_satisfy_byte_exact_gate": True,
        },
        "execution": {
            "pad_run_count": 0,
            "launcher_invocation_count": 0,
            "helper_invocation_count": 0,
            "excel_execution_count": 0,
            "artifact_comparison": "NOT_RUN_BECAUSE_PRE_RUN_RECOPY_GATE_FAILED",
        },
        "no_retry": {
            "second_recopy": 0,
            "repaste": 0,
            "candidate_rebuild": 0,
            "additional_pad_run": 0,
        },
    }
    with ANALYSIS.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
