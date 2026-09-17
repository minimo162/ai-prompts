#!/usr/bin/env python3
"""Build the fixed Issue #38 EX01-EX05 review archive.

The evidence payload is read from the pinned b73e0b5 Git tree so a later
working-tree change cannot silently replace a reviewed artifact.  Only the two
review documents authored for this snapshot are read from the working tree.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path, PurePosixPath
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CHECKPOINT = "b73e0b5a1a2c3f854ced3046b2a2648ddd0b8184"
REVIEW_ID = "ISSUE38-EX01-EX05-REVIEW-B73E0B5"
REVIEW_DIR = ROOT / "catalog/acceptance/issue38/review/20260917-b73e0b5"
ARCHIVE_NAME = "issue38-review-b73e0b5.zip"
ARCHIVE_PATH = REVIEW_DIR / ARCHIVE_NAME
ARCHIVE_META_PATH = REVIEW_DIR / "archive.json"
ARCHIVE_SHA_PATH = REVIEW_DIR / f"{ARCHIVE_NAME}.sha256"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

EXPECTED_R11_FILES = {
    "agent-instructions.txt",
    "manifest.json",
    "knowledge/PAD-Robin-00-Index.txt",
    "knowledge/PAD-Robin-01-Basics.txt",
    "knowledge/PAD-Robin-02-Control.txt",
    "knowledge/PAD-Robin-03-Files.txt",
    "knowledge/PAD-Robin-04-Office-PDF.txt",
    "knowledge/PAD-Robin-05-UI-Web.txt",
    "knowledge/PAD-Robin-06-Examples.txt",
    "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "support/EX03-R11-Independent-Minimal-FormatSandwich.ps1.txt",
    "support/EX03-R11-Independent-PAD-Recopy.robin",
    "support/EX03-R11-Minimal-Structural-Contract.txt",
}

EVIDENCE_PATHS = [
    # Fixed contract and requests.
    "catalog/acceptance/issue38/plan.md",
    "catalog/acceptance/issue38/spec.json",
    "catalog/acceptance/issue38/expected.json",
    "catalog/acceptance/issue38/freeze.json",
    "catalog/acceptance/issue38/requests/EX01.txt",
    "catalog/acceptance/issue38/requests/EX02.txt",
    "catalog/acceptance/issue38/requests/EX03.txt",
    "catalog/acceptance/issue38/requests/EX04.json",
    "catalog/acceptance/issue38/requests/EX05.json",
    # EX01 formal evidence.
    "catalog/acceptance/issue38/copilot/EX01/plan.json",
    "catalog/acceptance/issue38/copilot/EX01/roundtrip.json",
    "catalog/acceptance/issue38/copilot/EX01/two-run-comparison.json",
    "catalog/acceptance/issue38/copilot/EX01/run1-comparison.json",
    "catalog/acceptance/issue38/copilot/EX01/run1.json",
    "catalog/acceptance/issue38/copilot/EX01/run2.json",
    "catalog/acceptance/issue38/copilot/EX01/generated.robin",
    # EX02 formal, typed negative, and format reconciliation.
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/acceptance-status.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/verification.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/generation-result.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/generated.robin",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/pad-import-and-recopy.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/two-run-comparison.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/run1/run.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/run1/typed-transfer.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/run1/comparison.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/run2/run.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/run2/typed-transfer.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/run2/comparison.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/negative/build-evidence.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/negative/typed-transfer.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/negative/comparison.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/format-reconciliation/review.md",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/format-reconciliation/verification.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/format-reconciliation/classification.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/format-reconciliation/negative-build.json",
    "catalog/acceptance/issue38/cycles/EX02-r5-G2/format-reconciliation/negative-effective.json",
    "catalog/acceptance/issue38/cycles/EX04-r5-G2-existing-output-neg1/review.md",
    "catalog/acceptance/issue38/cycles/EX04-r5-G2-existing-output-neg1/verification.json",
    # EX03 r11 formal result.
    "catalog/acceptance/issue38/cycles/EX03-r11-G1/acceptance-status.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-G1/verification.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-G1/generation-result.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-G1/generation-safety-audit.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-G1/live-send.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-G1/submitted-body.txt",
    "catalog/acceptance/issue38/cycles/EX03-r11-G1/copilot-response.visible.txt",
    "catalog/acceptance/issue38/cycles/EX03-r11-G1/review.md",
    # EX03 downloaded-file auxiliary two-run evidence.
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/acceptance-status.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/verification.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/source-identity.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/pad-recopy.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/two-run-semantic.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/review.md",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run1/artifact.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run1/pad-run.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run1/pad-variables.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run1/typed-transfer.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run1/comparison.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run1/f6-native.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run1/native-styles.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run1/verification.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run2/artifact.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run2/pad-run.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run2/pad-variables.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run2/typed-transfer.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run2/comparison.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run2/f6-native.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run2/native-styles.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run2/verification.json",
    # EX03 r11 unchanged-flow existing-output guard.
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1/acceptance-status.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1/verification.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1/pad-run-observation.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1/hashes-after-live-run.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1/pad-recopy.json",
    "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1/review.md",
    # EX04 formal generation-stop records.
    "catalog/acceptance/issue38/copilot/EX04-missing-sheet/plan.json",
    "catalog/acceptance/issue38/copilot/EX04-missing-sheet/result.json",
    "catalog/acceptance/issue38/copilot/EX04-missing-sheet/response-full.txt",
    "catalog/acceptance/issue38/copilot/EX04-invalid-range/plan.json",
    "catalog/acceptance/issue38/copilot/EX04-invalid-range/result.json",
    "catalog/acceptance/issue38/copilot/EX04-invalid-range/response-full.txt",
    "catalog/acceptance/issue38/copilot/EX04-same-output/plan.json",
    "catalog/acceptance/issue38/copilot/EX04-same-output/result.json",
    "catalog/acceptance/issue38/copilot/EX04-same-output/response-full.txt",
    "catalog/acceptance/issue38/copilot/EX04-existing-output/plan.json",
    "catalog/acceptance/issue38/copilot/EX04-existing-output/result.json",
    "catalog/acceptance/issue38/copilot/EX04-existing-output/response-full.txt",
    # EX05 scope records.
    "catalog/acceptance/issue38/copilot/EX05-values-only/plan.json",
    "catalog/acceptance/issue38/copilot/EX05-values-only/result.json",
    "catalog/acceptance/issue38/copilot/EX05-values-only/response-full.txt",
    "catalog/acceptance/issue38/copilot/EX05-full-copy/plan.json",
    "catalog/acceptance/issue38/copilot/EX05-full-copy/result.json",
    "catalog/acceptance/issue38/copilot/EX05-full-copy/response-full.txt",
]

CURRENT_CODE_PATHS = [
    "tools/Compare-Issue38NativeStyles.ps1",
    "tools/Classify-Issue38Ex02FormatDifferences.py",
    "tools/Verify-Issue38Excel.py",
    "tools/Verify-Issue38Ex02TypedTransfer.py",
    "tools/Analyze-Issue38Ex03R11Generation.py",
    "tools/Finalize-Issue38Ex03R11FileAux.py",
    "tools/Record-Issue38Ex03R11ExistingOutputGuard.py",
    "tests/Test-Issue38Ex02.py",
    "tests/Test-Issue38Ex03.py",
    "tests/Test-Issue38Ex03R11ExistingOutputGuard.py",
]

WORKBOOKS = {
    "workbooks/EX02/fixtures/input-a.xlsx": "catalog/acceptance/issue38/fixtures/EX02/input-a.xlsx",
    "workbooks/EX02/fixtures/input-b.xlsx": "catalog/acceptance/issue38/fixtures/EX02/input-b.xlsx",
    "workbooks/EX02/fixtures/template.xlsx": "catalog/acceptance/issue38/fixtures/EX02/template.xlsx",
    "workbooks/EX02/outputs/run1-result.xlsx": "catalog/acceptance/issue38/cycles/EX02-r5-G2/run1/result.xlsx",
    "workbooks/EX02/outputs/run2-result.xlsx": "catalog/acceptance/issue38/cycles/EX02-r5-G2/run2/result.xlsx",
    "workbooks/EX02/negatives/one-cell-type-changed.xlsx": "catalog/acceptance/issue38/cycles/EX02-r5-G2/negative/result-one-type-changed.xlsx",
    "workbooks/EX02/negatives/format-dimensions-changed.xlsx": "catalog/acceptance/issue38/cycles/EX02-r5-G2/format-reconciliation/negative-format-dimensions.xlsx",
    "workbooks/EX03/fixtures/入力い.xlsx": "catalog/acceptance/issue38/fixtures/EX03/入力い.xlsx",
    "workbooks/EX03/fixtures/入力ろ.xlsx": "catalog/acceptance/issue38/fixtures/EX03/入力ろ.xlsx",
    "workbooks/EX03/fixtures/ひな形.xlsx": "catalog/acceptance/issue38/fixtures/EX03/ひな形.xlsx",
    "workbooks/EX03/outputs/run1-result.xlsx": "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run1/result.xlsx",
    "workbooks/EX03/outputs/run2-result.xlsx": "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/run2/result.xlsx",
    "workbooks/EX03/guard/existing-output-before.xlsx": "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1/existing-output-before.xlsx",
    "workbooks/EX03/guard/existing-output-after.xlsx": "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1-existing-output-neg1/existing-output-after.xlsx",
}

DIFFS = [
    {
        "archive": "diffs/01-ex02-effective-format-comparator-and-tests.diff",
        "from": "7131d60",
        "to": "a6662d8",
        "paths": [
            "tools/Compare-Issue38NativeStyles.ps1",
            "tools/Classify-Issue38Ex02FormatDifferences.py",
            "tests/Test-Issue38Ex02.py",
        ],
    },
    {
        "archive": "diffs/02-ex03-r11-candidate-builder-and-tests.diff",
        "from": "ac90b09",
        "to": "659ae9d",
        "paths": [
            "tools/Build-Issue38Ex03CandidateR11.py",
            "tests/Test-Issue38Ex03.py",
            "copilot/versions/20260917-excel-r11/support",
        ],
    },
    {
        "archive": "diffs/03-ex03-r11-formal-analysis-and-file-aux-finalization.diff",
        "from": "659ae9d",
        "to": "54037bb",
        "paths": [
            "tools/Analyze-Issue38Ex03R11Generation.py",
            "tools/Finalize-Issue38Ex03R11Stop.py",
            "tools/Finalize-Issue38Ex03R11FileAux.py",
        ],
    },
    {
        "archive": "diffs/04-ex03-r11-existing-output-guard-tools-and-test.diff",
        "from": "54037bb",
        "to": "b73e0b5",
        "paths": [
            "tools/Record-Issue38Ex03R11ExistingOutputGuard.py",
            "tools/Build-Issue38Ex03R11ExistingOutputFixture.mjs",
            "tests/Test-Issue38Ex03R11ExistingOutputGuard.py",
        ],
    },
]


def run_git(*args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout


def git_blob(path: str) -> bytes:
    return run_git("show", f"{SOURCE_CHECKPOINT}:{path}")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def normalized_text_file_bytes(path: Path) -> bytes:
    """Read a UTF-8 source with checkout-specific line endings normalized."""
    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def safe_archive_name(value: str) -> str:
    normalized = PurePosixPath(value).as_posix()
    if normalized.startswith("/") or ".." in PurePosixPath(normalized).parts:
        raise ValueError(f"unsafe archive path: {value}")
    return normalized


def add_content(
    content: dict[str, bytes],
    records: list[dict[str, object]],
    archive_path: str,
    data: bytes,
    *,
    kind: str,
    source: str,
) -> None:
    archive_path = safe_archive_name(archive_path)
    if archive_path in content:
        raise ValueError(f"duplicate archive path: {archive_path}")
    content[archive_path] = data
    records.append(
        {
            "archive_path": archive_path,
            "kind": kind,
            "source": source,
            "bytes": len(data),
            "sha256": sha256(data),
        }
    )


def add_checkpoint_paths(
    content: dict[str, bytes],
    records: list[dict[str, object]],
    paths: Iterable[str],
    *,
    archive_prefix: str,
    kind: str,
) -> None:
    for path in paths:
        add_content(
            content,
            records,
            f"{archive_prefix}/{path}",
            git_blob(path),
            kind=kind,
            source=f"git:{SOURCE_CHECKPOINT}:{path}",
        )


def build() -> None:
    run_git("cat-file", "-e", f"{SOURCE_CHECKPOINT}^{{commit}}")
    head = run_git("rev-parse", "HEAD").decode("ascii").strip()
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", SOURCE_CHECKPOINT, head],
        cwd=ROOT,
        check=False,
    )
    if ancestry.returncode != 0:
        raise RuntimeError(f"HEAD {head} is not a descendant of {SOURCE_CHECKPOINT}")

    content: dict[str, bytes] = {}
    records: list[dict[str, object]] = []

    for archive_path, local_name in [
        ("00-REVIEW-SUMMARY.md", "README.md"),
        ("01-CASE-MATRIX.json", "case-matrix.json"),
    ]:
        source_path = REVIEW_DIR / local_name
        add_content(
            content,
            records,
            archive_path,
            normalized_text_file_bytes(source_path),
            kind="review_document",
            source=str(source_path.relative_to(ROOT)).replace("\\", "/"),
        )

    for repo_path in [
        "tools/Build-Issue38ReviewBundle.py",
        "tests/Test-Issue38ReviewBundle.py",
    ]:
        source_path = ROOT / repo_path
        add_content(
            content,
            records,
            f"review-tools/{repo_path}",
            normalized_text_file_bytes(source_path),
            kind="review_archive_tooling",
            source=repo_path,
        )

    diff_ranges = {
        "schema_version": 1,
        "source_checkpoint": SOURCE_CHECKPOINT,
        "diffs": DIFFS,
        "note": "Each diff is path-limited. Binary evidence is supplied separately as workbooks, not embedded in a Git binary patch.",
    }
    add_content(
        content,
        records,
        "02-DIFF-RANGES.json",
        json_bytes(diff_ranges),
        kind="review_index",
        source="generated from pinned diff configuration",
    )

    r11_prefix = "copilot/versions/20260917-excel-r11"
    r11_paths = [
        line
        for line in run_git(
            "ls-tree", "-r", "--name-only", SOURCE_CHECKPOINT, "--", r11_prefix
        )
        .decode("utf-8")
        .splitlines()
        if line
    ]
    relative_r11_paths = {path.removeprefix(f"{r11_prefix}/") for path in r11_paths}
    if relative_r11_paths != EXPECTED_R11_FILES:
        missing = sorted(EXPECTED_R11_FILES - relative_r11_paths)
        extra = sorted(relative_r11_paths - EXPECTED_R11_FILES)
        raise RuntimeError(f"unexpected r11 candidate set; missing={missing}, extra={extra}")
    for path in sorted(r11_paths):
        relative_path = path.removeprefix(f"{r11_prefix}/")
        add_content(
            content,
            records,
            f"candidate/20260917-excel-r11/{relative_path}",
            git_blob(path),
            kind="r11_candidate",
            source=f"git:{SOURCE_CHECKPOINT}:{path}",
        )

    generated_sources = {
        "generated/EX03-r11-formal-generated.robin": "catalog/acceptance/issue38/cycles/EX03-r11-G1/generated.robin",
        "generated/EX03-r11-file-aux1-downloaded.robin": "catalog/acceptance/issue38/cycles/EX03-r11-file-aux1/copilot-downloaded-ex03.robin",
    }
    for archive_path, source_path in generated_sources.items():
        add_content(
            content,
            records,
            archive_path,
            git_blob(source_path),
            kind="unmodified_generated_robin",
            source=f"git:{SOURCE_CHECKPOINT}:{source_path}",
        )

    for diff in DIFFS:
        data = run_git(
            "diff",
            "--no-ext-diff",
            "--unified=3",
            f"{diff['from']}..{diff['to']}",
            "--",
            *diff["paths"],
        )
        if not data:
            raise RuntimeError(f"empty required diff: {diff['archive']}")
        add_content(
            content,
            records,
            str(diff["archive"]),
            data,
            kind="git_diff",
            source=f"git diff {diff['from']}..{diff['to']} -- {' '.join(diff['paths'])}",
        )

    r10_r11_diff_path = (
        "catalog/acceptance/issue38/probes/ex03-r11-minimal-powershell/"
        "r10-to-r11-script.diff"
    )
    add_content(
        content,
        records,
        "diffs/00-r10-to-r11-embedded-script.diff",
        git_blob(r10_r11_diff_path),
        kind="embedded_script_diff",
        source=f"git:{SOURCE_CHECKPOINT}:{r10_r11_diff_path}",
    )

    add_checkpoint_paths(
        content,
        records,
        EVIDENCE_PATHS,
        archive_prefix="evidence",
        kind="decision_or_comparison_evidence",
    )
    add_checkpoint_paths(
        content,
        records,
        CURRENT_CODE_PATHS,
        archive_prefix="code/current",
        kind="current_review_code",
    )

    for archive_path, source_path in WORKBOOKS.items():
        add_content(
            content,
            records,
            archive_path,
            git_blob(source_path),
            kind="synthetic_comparison_workbook",
            source=f"git:{SOURCE_CHECKPOINT}:{source_path}",
        )

    records.sort(key=lambda item: str(item["archive_path"]))
    manifest = {
        "schema_version": 1,
        "review_id": REVIEW_ID,
        "source_checkpoint": SOURCE_CHECKPOINT,
        "acceptance_conditions_changed": False,
        "copilot_sends_added": 0,
        "pad_runs_added": 0,
        "candidate_versions_changed": 0,
        "github_writes": 0,
        "issue38_complete": False,
        "entry_count_excluding_manifest": len(records),
        "entries": records,
    }
    manifest_data = json_bytes(manifest)

    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = ARCHIVE_PATH.with_suffix(".zip.tmp")
    with zipfile.ZipFile(
        temporary_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        all_entries = dict(content)
        all_entries["MANIFEST.json"] = manifest_data
        for name in sorted(all_entries):
            info = zipfile.ZipInfo(filename=name, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, all_entries[name])
    os.replace(temporary_path, ARCHIVE_PATH)

    archive_data = ARCHIVE_PATH.read_bytes()
    archive_sha = sha256(archive_data)
    archive_meta = {
        "schema_version": 1,
        "review_id": REVIEW_ID,
        "source_checkpoint": SOURCE_CHECKPOINT,
        "archive": ARCHIVE_NAME,
        "archive_sha256": archive_sha,
        "archive_bytes": len(archive_data),
        "zip_entry_count_including_manifest": len(content) + 1,
        "content_manifest_sha256": sha256(manifest_data),
        "issue38_complete": False,
    }
    ARCHIVE_META_PATH.write_bytes(json_bytes(archive_meta))
    ARCHIVE_SHA_PATH.write_text(f"{archive_sha}  {ARCHIVE_NAME}\n", encoding="ascii")

    print(
        json.dumps(
            {
                "status": "PASS_REVIEW_ARCHIVE_BUILT",
                "archive": str(ARCHIVE_PATH.relative_to(ROOT)),
                "sha256": archive_sha,
                "entries": len(content) + 1,
                "bytes": len(archive_data),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    build()
