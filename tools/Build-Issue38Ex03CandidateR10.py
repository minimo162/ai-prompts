#!/usr/bin/env python3
"""Build the unsent EX03 r10 successor with a structural-fidelity gate.

r10 keeps the fixed request and expectations unchanged and reuses the exact
independent r9 teaching Robin and embedded script.  It adds only a
generation-time contract for source-derived token counts and invariant
PowerShell fragments.  It does not send to Copilot, paste into PAD, or run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "copilot/versions/20260917-excel-r9"
VERSION = "20260917-excel-r10"
BASE_COMMIT = "e8fc12c2a916df7a708536b652017d12c81f2714"
AUDIT = ROOT / "catalog/acceptance/issue38/probes/ex03-r10-structural-fidelity"
R9_CYCLE = ROOT / "catalog/acceptance/issue38/cycles/EX03-r9-G1"
R9_MARKER = "Issue #38 EX03 / 20260917-excel-r9 候補の現在の範囲"
R9_INSTRUCTION_MARKER = "【Excel値転記・20260917-excel-r9候補】"
SCRIPT_SUPPORT = Path("support/EX03-R10-Independent-FormatSandwich.ps1.txt")
ROBIN_SUPPORT = Path("support/EX03-R10-Independent-PAD-Recopy.robin")
FIDELITY_SUPPORT = Path("support/EX03-R10-Structural-Fidelity-Contract.txt")

INPUTS = {
    "r9_manifest": BASE / "manifest.json",
    "r9_instruction": BASE / "agent-instructions.txt",
    "r9_bundle": BASE / "knowledge/PAD-Robin-Knowledge-Bundle.txt",
    "r9_script": BASE / "support/EX03-R9-Independent-FormatSandwich.ps1.txt",
    "r9_robin": BASE / "support/EX03-R9-Independent-PAD-Recopy.robin",
    "structural_analysis": AUDIT / "analysis.json",
    "structural_report": AUDIT / "report.md",
    "dom_confirmation": AUDIT / "r9-dom-code-confirmation.json",
    "r9_generated": R9_CYCLE / "generated.robin",
    "r9_raw_capture": R9_CYCLE / "generated-robin.clipboard.utf8.b64",
    "r9_generation": R9_CYCLE / "generation-result.json",
    "r9_safety": R9_CYCLE / "generation-safety-audit.json",
    "r9_acceptance": R9_CYCLE / "acceptance-status.json",
    "fixed_request": ROOT / "catalog/acceptance/issue38/requests/EX03.txt",
    "fixed_spec": ROOT / "catalog/acceptance/issue38/spec.json",
    "grader_expected": ROOT / "catalog/acceptance/issue38/expected.json",
}

EXPECTED = {
    "r9_manifest": "1b64005c85aee3215160c9381d956a64531863b5d838d9091009fded5007f540",
    "r9_instruction": "a699dd910a4b0529fc71c9b8045b845bf49b8a407df9da88027a0ca0ab0f51fa",
    "r9_bundle": "b402a6c78fb39cb68dd4111590122b9f9be3364609358fd58a9ad3880d29b993",
    "r9_script": "65b86b0e5be4ec2da30e57a6bd858e395d1103da2d05ab2e7607362772d1dfd9",
    "r9_robin": "6d9c23eabfacbcd65b1a18eabf5681805494e41171f94a9b01a28b24452815bb",
    "structural_analysis": "a2b0e39683dfceac45f49ebaa70c71da486954343e5d0be4e2276f971ad0a798",
    "structural_report": "5093f1aeeb4c74687fb4069d0b0325e3f90115442e794ada8d23e9b58c5ee624",
    "dom_confirmation": "a78e4cf2f309b733ae8e9c6d6c268de16206ca8df17d2863d07f512cbcefb34f",
    "r9_generated": "7a02ea0d073adde698578b8fa578f5701c728114ee55fbf20aa0ecdaaa32cb14",
    "r9_raw_capture": "42a03537c81e2300834a240932fde5a1de4bde23cf0bdcdf4bb611fbf773d894",
    "r9_generation": "2051065a60419e7c6f2c7ec0ef36302f3364489f114874f277f48b299f03914e",
    "r9_safety": "375e225bcd494e9204a31a633b719dd6915e4d4d4ad01be89ee44cf05c1fa8c1",
    "r9_acceptance": "d3677a6e026e1a20b5cf109795a848036568182014c0f87bc4e0c119dd373d9b",
    "fixed_request": "b530557d87ebaf7ceac01c62c7cb00f7169b3577554ef24bae646391e9a7c370",
    "fixed_spec": "a6d6dec7ec8d76d3780ecfa5b76a9d6da5944fbdc069ff3a742379276dde4380",
    "grader_expected": "49c5e1c24624e0d5550e324118f67af722830f7762327135946e8214cdf89a4d",
}

FIXED_ROOT = r"C:\\Users\\yuuki\\ai-prompts-issue38\\catalog\\acceptance\\issue38"
FIXED_COMPLETION_TERMS = [
    FIXED_ROOT + r"\\fixtures\\EX03\\入力い.xlsx",
    FIXED_ROOT + r"\\fixtures\\EX03\\入力ろ.xlsx",
    FIXED_ROOT + r"\\runs\\EX03-attempt1\\work.xlsx",
    FIXED_ROOT + r"\\runs\\EX03-attempt1\\照合結果.xlsx",
    "受取明細",
    "追加項目",
    "集計先",
    "追記先",
]
UNIQUE_GRADER_STRINGS = ["春", "夏", "秋", "項目甲", "項目乙"]
EXPECTED_TEXT = "100%"

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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def normalized(value: str) -> str:
    return value.replace("\r\n", "\n").rstrip("\n")


def example_mapping() -> str:
    return """r10独立教材例のデータ対応（固定する命令構造と、変更するdata slotを分離）:
- source-one.xlsx / 教材入力一 H3:I5 -> 教材出力一 J4:K6。各行の第1列はtext、第2列はnumber。
- source-two.xlsx / 教材入力二 C7:E8 -> 教材出力二 B10:D11。各行はtext, number, text。
- work-copy.xlsxだけを編集し、未存在のexample-result.xlsxへSaveAsする。
- 文字列7位置は同一RunのDataTableをJSON primitiveで確認して内包scriptから各1回、数値5位置は通常WriteCellから各1回だけ書く。保存・クローズ・ReadOnly再開後に12位置を個別JSON比較する。
- 固定するもの: 命令名、引数名、mode、DataTable添字、型の役割、依存順、分岐、1 RunScript、5 numeric writes、12 JSON comparisons、RunScript内のraw角括弧。
- 依頼から変更するもの: 同じ確認範囲内のpath、存在するsheet名、3x2と2x3のrectangle、対応する開始位置、work copy、未存在output、data slotに由来するerror label。
- text/number以外、異なるshape、空白、真偽値、日付、error、formula result、任意object、別PC/PAD版へ一般化しない。
"""


FIDELITY_CONTRACT = """EX03 r10 generation structural-fidelity contract
This contract applies to the one raw Robin text code block derived from the independent PAD-recopied source.
1. Do only the listed data-slot substitutions. Do not paraphrase, shorten, repair, optimize, or rewrite any other character of the source.
2. A text code block is raw Robin text. Do not apply Markdown escaping. The exact substring counts for backslash-open-bracket and backslash-close-bracket must both be zero.
3. After substitution, require these source-derived exact token counts: `[ordered]` 8; `[string]` 14; `[bool]` 2; `[void]` 5; `[Runtime.InteropServices.Marshal]` 6; `[IO.Path]` 1; `[StringComparison]` 1; `::GetFullPath(` 1; `::OrdinalIgnoreCase` 1; `::IsNullOrEmpty(` 1; `$matches[0]` 1; `$allowedTargets[$sheetName]` 1.
4. Require each invariant fragment exactly once: `[string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)`; `[string]::IsNullOrEmpty($afterPrefixCharacter)`.
5. Require each observed corruption fragment zero times: `[IO.Path]::GetFulling]`; `, :OrdinalIgnoreCase`; `-not :IsNullOrEmpty(`.
6. Replace every independent-example data slot consistently, including paths, sheet names, ranges, target cells, allowed-target entries, and teaching-only error labels. The adapted error labels must be exactly `EX03 text mapping` and `EX03 text source`; no teaching-only label may remain.
7. If any count, fragment, data-slot, or label check fails, emit no Robin and report the failed check. Do not repair after output. A refusal or no-code result is not a runtime PASS.
8. This narrow gate addresses only the r9 structural corruption already confirmed in the rendered Copilot response. It does not prove execution, types outside text/number, other shapes, another PAD version, or another PC.
"""


R10_SCOPE = """Issue #38 EX03 / 20260917-excel-r10 候補の現在の範囲
この節だけがr9後継の追加範囲である。r9以前の版、固定依頼・期待値、旧証跡、成功済みprobe、558差分FAILを変更せず、旧版の生成・Run結果をr10へ継承しない。
1. r9 G1は通常M365 Copilotへ1回だけ送信し、再送0回で197行のRobinを生成した。固定停止条件によりPAD import、再コピー、Run1/Run2は0回である。
2. r9の生成候補は期待適応と50行目・90行目だけが異なった。保存したclipboard payloadとCopilot応答の全197行DOMをCRLF連結したSHA-256は同一であり、2件の破損はcopy/PADより前の表示済み応答に存在した。非公開のmodel/service内部原因は不明のまま確定しない。
3. r9のbackslash-open-bracket / backslash-close-bracket各0件ゲートはPASSしたが、必要な型・member tokenと2つのPowerShell不変断片を検証しなかったため、構造破損を止められなかった。
4. r10はr9の独立教材Robinと内包scriptをbyte同一で再利用し、新規PAD採取を行わない。教材と固定試験の独立性を保持し、完全Robinを固定試験から教材へ混入させない。
5. 依頼本文から列挙したdata slotと教材専用error labelだけを一貫置換し、それ以外の文字を言い換え、短縮、修復、最適化、再構成しない。error labelは正確に `EX03 text mapping` と `EX03 text source` にする。
6. 角括弧backslash各0件に加え、source由来の12 tokenを指定件数、2不変断片を各1件、r9で観測した3破損断片を各0件と確認する。どれか不一致ならRobinを出さず、失敗項目を説明する。
7. r10は未送信候補であり、通常M365生成、PAD貼付け・再コピー、Run1/Run2、成果物照合、既存output guard実機経路は未実施である。旧FAILと未確認範囲を維持する。
"""


R10_INSTRUCTIONS = """【Excel値転記・20260917-excel-r10候補】
標準入力は同版の指示全文＋bundle実添付です。r9 G1の生成安全FAIL、固定依頼・期待値、旧版、成功済みprobe、558差分FAILを保持し、r9の生成や旧Run結果をr10の受入へ継承しません。00/04/06末尾の「EX03 / 20260917-excel-r10」だけを後継追加範囲として参照します。
r10はr9の別path・別sheet・別range・別target・別outputの独立教材Robinと内包scriptをbyte同一で再利用します。この原文は専用PAD 2.71.115.26224、日本語UI、Power Fx OFFで110 action・45 variableとして保存・再コピー済みですが、教材例の実行証拠ではありません。
r9 G1の197行生成候補は期待適応と50・90行目だけが異なり、Copilot応答DOMと保存clipboardの全体SHAも一致しました。したがってcopy/PAD由来ではありませんが、非公開のmodel/service内部原因は不明です。r10では依頼本文から列挙したdata slotと教材専用error labelだけを置換し、それ以外の1文字も言い換え、短縮、修復、最適化、再構成しません。
回答確定前に候補内のbackslash-open-bracketとbackslash-close-bracketが各0件であること、および次の完全一致token件数を確認します: `[ordered]` 8、`[string]` 14、`[bool]` 2、`[void]` 5、`[Runtime.InteropServices.Marshal]` 6、`[IO.Path]` 1、`[StringComparison]` 1、`::GetFullPath(` 1、`::OrdinalIgnoreCase` 1、`::IsNullOrEmpty(` 1、`$matches[0]` 1、`$allowedTargets[$sheetName]` 1。
次の不変断片を各1件必要とします: `[string]::Equals([IO.Path]::GetFullPath([string]$candidate.FullName), $targetPath, [StringComparison]::OrdinalIgnoreCase)`、`[string]::IsNullOrEmpty($afterPrefixCharacter)`。次の破損断片は各0件とします: `[IO.Path]::GetFulling]`、`, :OrdinalIgnoreCase`、`-not :IsNullOrEmpty(`。教材専用error labelは残さず、適応後のlabelを正確に `EX03 text mapping` と `EX03 text source` にします。どれか不一致ならRobinを出さず、失敗項目を説明します。生成後の手修正や再表示で合格にしません。
固定するのは命令名、引数名、mode、DataTable添字、text/numberの役割、依存順、分岐・block構造、1 RunScript、5 numeric write、12 JSON compare、RunScript内のraw角括弧です。依頼から置換するのは同じ確認範囲内のpath、存在するsheet名、3x2と2x3のrectangle、対応するtarget start、work copy、未存在outputと、それらdata slotに由来するerror labelです。教材専用path・sheet・target・error labelを候補へ残しません。
固定試験の具体的なpath、sheet、target cell、grader値、完成Robinを教材から補いません。依頼本文のdataだけで独立例のdata slotを置換します。text/number以外、異なるshape、空白、真偽値、日付、error、formula result、任意object、別PC/PAD版へ一般化しません。
入力と原本はReadOnlyで開き、検証者が準備したwork copyだけを編集します。既存output時はwrite経路へ入らず、文字列7位置は同じRunのDataTableからJSON化して内包scriptで各1回、数値5位置は通常WriteCellで各1回だけ書きます。固定値や1 cellだけの事後修正を入れません。
内包scriptの絶対FullName 1冊、許可target、source文字列、非formula、元NumberFormat、一時@、Value2、finally復元、直後の値・System.String・元format・prefix空・formulaなしの検査を保持します。失敗時はSaveAs・完了状態へ進まず、外部ps1、network、delete、overwrite、権限・security・Excel設定変更を要求しません。
SaveAs後はcloseしてReadOnly再開し、2矩形をTypedValuesで再取得して12位置を個別JSON比較します。原本・対象外全cell・formula・effective formatは独立検査を維持し、書式・寸法558差分FAILを隠しません。
回答は利用者依頼の全工程を一つのtextコードブロックへ入れます。r10は独立教材と出力前structural-fidelity gateの候補であり、通常M365 Copilot生成、無修正EX03 PAD貼付け・再コピー・Run1/Run2、成果物照合、既存output guard実機経路は未実施です。完成・実行済み・受入済みと表示しません。
"""


def audit_section(analysis: dict) -> str:
    comparison = analysis["r9_comparison"]
    boundary = analysis["response_boundary"]
    token_summary = "; ".join(
        f"{token} expected {data['expected_count']} / generated {data['generated_count']}"
        for token, data in comparison["token_inventory"].items()
    )
    return f"""r10 structural-fidelity機械照合
- source audit: {relative(INPUTS['structural_analysis'])} / SHA-256 {sha256(INPUTS['structural_analysis'])}
- rendered-DOM record: {relative(INPUTS['dom_confirmation'])} / SHA-256 {sha256(INPUTS['dom_confirmation'])}
- r9 independent PAD source: {relative(INPUTS['r9_robin'])} / SHA-256 {sha256(INPUTS['r9_robin'])}
- r9 G1 generated Robin: {relative(INPUTS['r9_generated'])} / SHA-256 {sha256(INPUTS['r9_generated'])}
- exact expected adaptation vs generated differing lines: {comparison['expected_vs_generated_differing_line_count']} ({', '.join(str(item['line']) for item in comparison['differing_lines'])})
- rendered response DOM equals preserved raw clipboard: {str(boundary['dom_equals_raw_clipboard']).lower()} / SHA-256 {boundary['dom_sha256']}
- token inventory: {token_summary}
- required invariant fragments are absent in r9 generated output; each remains once in the teaching source. Three observed corruption fragments occur once each in r9 generated output and zero times in the teaching source.
- hidden model/service cause remains unknown. Confirmed boundary is the rendered Copilot response before copy or PAD.
- r10 changes only the instruction/bundle structural-fidelity contract; the independent teaching Robin and embedded script remain byte-identical. Copilot send 0、PAD import/run 0、GitHub write 0。

{FIDELITY_CONTRACT.rstrip()}
"""


def build(destination: Path) -> None:
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Candidate exists; sealed versions must not be overwritten")

    actual = {name: sha256(path) for name, path in INPUTS.items()}
    if actual != EXPECTED:
        raise ValueError(f"Protected r9/audit/fixed input hash mismatch: {actual}")

    manifest = json.loads(INPUTS["r9_manifest"].read_bytes())
    analysis = json.loads(INPUTS["structural_analysis"].read_bytes())
    acceptance = json.loads(INPUTS["r9_acceptance"].read_bytes())
    safety = json.loads(INPUTS["r9_safety"].read_bytes())
    if manifest["version"] != "20260917-excel-r9":
        raise ValueError("Unexpected base candidate")
    if analysis["decision"] != "PASS_R9_STRUCTURAL_FAILURE_BOUNDARY_READY_FOR_UNSENT_R10":
        raise ValueError("Structural analysis is not passing")
    if acceptance["decision"]["status"] != "STOPPED_BEFORE_PAD_GENERATED_ROBIN_SAFETY_FAILURE":
        raise ValueError("r9 G1 stop evidence changed")
    if acceptance["runs"]["pad_runs_used"] != 0:
        raise ValueError("r9 G1 now records an execution")
    if safety["decision"]["status"] != "FAIL_GENERATED_ROBIN_SYNTAX_CORRUPTION_STOP_BEFORE_PAD":
        raise ValueError("r9 safety evidence changed")
    for record in manifest["source_files"]:
        if sha256(BASE / record["path"]) != record["sha256"]:
            raise ValueError(f"r9 source mismatch: {record['path']}")
    if manifest["instruction_sha256"] != actual["r9_instruction"]:
        raise ValueError("r9 instruction manifest mismatch")
    if manifest["bundle_sha256"] != actual["r9_bundle"]:
        raise ValueError("r9 bundle manifest mismatch")

    base_instruction = text(INPUTS["r9_instruction"])
    base_bundle = text(INPUTS["r9_bundle"])
    teaching_robin = text(INPUTS["r9_robin"])
    generated = text(INPUTS["r9_generated"])
    if any(term in base_instruction + base_bundle + teaching_robin for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS):
        raise ValueError("Fixed EX03 answer leaked into the independent r9 package")
    if EXPECTED_TEXT in base_instruction or EXPECTED_TEXT in teaching_robin:
        raise ValueError("Fixed EX03 expected percent text leaked into r9 instruction/source")
    if teaching_robin.count(r"\[") or teaching_robin.count(r"\]"):
        raise ValueError("Authoritative teaching Robin contains forbidden bracket backslashes")
    for token, expected_count in TOKEN_COUNTS.items():
        if teaching_robin.count(token) != expected_count:
            raise ValueError(f"Teaching source token count changed: {token}")
    for fragment in REQUIRED_INVARIANT_FRAGMENTS:
        if teaching_robin.count(fragment) != 1:
            raise ValueError(f"Teaching source invariant changed: {fragment}")
    for fragment in FORBIDDEN_CORRUPTION_FRAGMENTS:
        if teaching_robin.count(fragment) != 0:
            raise ValueError(f"Teaching source contains corruption fragment: {fragment}")
    comparison = analysis["r9_comparison"]
    if comparison["expected_vs_generated_differing_line_count"] != 2:
        raise ValueError("Observed r9 difference count changed")
    if [item["line"] for item in comparison["differing_lines"]] != [50, 90]:
        raise ValueError("Observed r9 differing lines changed")
    if not analysis["response_boundary"]["dom_equals_raw_clipboard"]:
        raise ValueError("Rendered response no longer matches raw clipboard evidence")
    if (generated.count(r"\["), generated.count(r"\]")) != (0, 0):
        raise ValueError("Observed r9 bracket-backslash counts changed")

    (destination / "knowledge").mkdir(parents=True)
    (destination / "support").mkdir(parents=True)
    shutil.copyfile(INPUTS["r9_script"], destination / SCRIPT_SUPPORT)
    shutil.copyfile(INPUTS["r9_robin"], destination / ROBIN_SUPPORT)
    (destination / FIDELITY_SUPPORT).write_text(
        FIDELITY_CONTRACT, encoding="utf-8", newline="\n"
    )

    audit = audit_section(analysis)
    mapping = example_mapping()
    for record in manifest["source_files"]:
        source = BASE / record["path"]
        name = Path(record["path"]).name
        content = text(source)
        if name.startswith(("PAD-Robin-00-", "PAD-Robin-04-", "PAD-Robin-06-")):
            if R9_MARKER not in content:
                raise ValueError(f"r9 replacement marker missing: {name}")
            content = content.split(R9_MARKER, 1)[0].rstrip("\r\n") + "\n\n"
            content += R10_SCOPE + mapping
            if name.startswith("PAD-Robin-04-"):
                content += "\n" + audit
            if name.startswith("PAD-Robin-06-"):
                content += "\nEX03 r10 PAD保存・再コピー独立教材原文（r9とbyte同一。別条件例・未実行・未受入）\n"
                content += f"source: {ROBIN_SUPPORT.as_posix()} / SHA-256 {sha256(INPUTS['r9_robin'])}\n"
                content += "この見出しより後のRobinだけを逐語使用する。依頼から列挙したdata slotと教材専用error label以外の文字を変更しない。角括弧、token件数、不変断片、禁止断片をstructural-fidelity contractどおり検査する。\n"
                content += teaching_robin.rstrip("\r\n") + "\n"
        (destination / record["path"]).write_bytes(content.encode("utf-8"))

    if R9_INSTRUCTION_MARKER not in base_instruction:
        raise ValueError("r9 instruction replacement marker missing")
    instructions = base_instruction.split(R9_INSTRUCTION_MARKER, 1)[0] + R10_INSTRUCTIONS
    (destination / "agent-instructions.txt").write_text(
        instructions, encoding="utf-8", newline="\n"
    )
    instruction_utf16 = len(instructions.encode("utf-16-le")) // 2
    if instruction_utf16 > 8000:
        raise ValueError(f"Instruction exceeds limit: {instruction_utf16}")
    if any(term in instructions for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS + [EXPECTED_TEXT]):
        raise ValueError("Fixed EX03 answer leaked into r10 instruction")

    subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(ROOT / "tools/Build-KnowledgeBundle.ps1"),
            "-Root",
            str(destination),
            "-KnowledgeDirectory",
            "knowledge",
            "-OutputPath",
            "knowledge/PAD-Robin-Knowledge-Bundle.txt",
        ],
        check=True,
    )

    bundle_path = destination / manifest["bundle_path"]
    current_bundle = text(bundle_path)
    if any(term in current_bundle for term in FIXED_COMPLETION_TERMS + UNIQUE_GRADER_STRINGS):
        raise ValueError("Fixed EX03 complete answer or grader data leaked into r10 bundle")
    if normalized(teaching_robin) not in normalized(current_bundle):
        raise ValueError("Independent PAD teaching source is missing from r10 bundle")
    for required in [
        "Do only the listed data-slot substitutions",
        "source-derived exact token counts",
        "Require each invariant fragment exactly once",
        "Require each observed corruption fragment zero times",
        "EX03 text mapping",
        "EX03 text source",
    ]:
        if required not in current_bundle:
            raise ValueError(f"Structural-fidelity contract missing from r10 bundle: {required}")

    evidence_inputs = dict(manifest.get("evidence_inputs", {}))
    for path in INPUTS.values():
        evidence_inputs[relative(path)] = sha256(path)

    support_files = []
    for support_path, runtime in [
        (SCRIPT_SUPPORT, "embedded_in_robin_not_loaded_from_disk"),
        (ROBIN_SUPPORT, "authoritative_independent_teaching_source_reused_not_executed"),
        (FIDELITY_SUPPORT, "generation_time_structural_fidelity_contract_not_runtime_code"),
    ]:
        path = destination / support_path
        support_files.append(
            {
                "path": support_path.as_posix(),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
                "runtime": runtime,
            }
        )

    manifest.update(
        version=VERSION,
        status="FROZEN_CANDIDATE_EX03_STRUCTURAL_FIDELITY_GATE_NOT_COPILOT_OR_RUNTIME_ACCEPTED",
        inherits_live_acceptance=False,
        base_candidate="20260917-excel-r9",
        base_commit=BASE_COMMIT,
        instruction_sha256=sha256(destination / "agent-instructions.txt"),
        instruction_utf16=instruction_utf16,
        bundle_sha256=sha256(bundle_path),
        evidence_inputs=evidence_inputs,
        builder="tools/Build-Issue38Ex03CandidateR10.py",
        support_files=support_files,
    )
    for record in manifest["source_files"]:
        path = destination / record["path"]
        record.update(sha256=sha256(path), bytes=path.stat().st_size)
    manifest["evidence"].update(
        copilot="R9_G1_ONE_SEND_GENERATED_STRUCTURALLY_CORRUPT_R10_NOT_SENT",
        pad="R9_G1_STOP_BEFORE_PAD_IMPORT_RUN0_R10_NO_PAD_ACTION",
        teaching_test_independence="PASS_R10_FIXED_EX03_COMPLETE_ANSWER_ABSENT_FROM_CURRENT_INSTRUCTION_BUNDLE_AND_SUPPORT",
        structural_failure_boundary="CONFIRMED_RENDERED_NORMAL_M365_RESPONSE_DOM_MATCHES_RAW_CLIPBOARD_BEFORE_COPY_OR_PAD",
        structural_failure_hidden_model_or_service_cause="UNKNOWN_NOT_CLAIMED",
        r9_response_dom_sha256=analysis["response_boundary"]["dom_sha256"],
        r9_response_dom_equals_raw_clipboard=True,
        generated_backslash_open_bracket_count=0,
        generated_backslash_close_bracket_count=0,
        teaching_backslash_open_bracket_count=0,
        teaching_backslash_close_bracket_count=0,
        expected_vs_generated_differing_lines=2,
        expected_vs_generated_differing_line_numbers=[50, 90],
        structural_token_expected_counts=TOKEN_COUNTS,
        structural_token_generated_counts={
            token: data["generated_count"]
            for token, data in comparison["token_inventory"].items()
        },
        required_invariant_fragment_count=len(REQUIRED_INVARIANT_FRAGMENTS),
        forbidden_corruption_fragment_count=len(FORBIDDEN_CORRUPTION_FRAGMENTS),
        manual_repair_applied=False,
        source_chain="R9_PAD_SOURCE_TO_R9_G1_RENDERED_RESPONSE_AND_CLIPBOARD_AUDITED_R10_STRUCTURAL_FIDELITY_GATE_ADDED",
        source_pad_recopy_sha256=sha256(INPUTS["r9_robin"]),
        source_reused_exact_bytes=True,
        source_new_pad_capture_required=False,
        source_new_pad_capture_reason="UNCHANGED_AUTHORITATIVE_R8_SOURCE_ALREADY_PASTE_SAVE_RECOPY_VERIFIED",
        fixed_request_spec_expected_hashes_preserved=True,
        fixed_completion_terms_absent_from_independent_source=True,
        unique_grader_strings_absent_from_independent_source=True,
        existing_output_guard="STATIC_ONLY_NOT_LIVE_TESTED",
        legacy_558_failure_preserved=True,
        candidate_adaptation="UNSENT_STRUCTURAL_FIDELITY_GATE_WITH_UNCHANGED_INDEPENDENT_PAD_SOURCE",
        candidate_script_sha256=sha256(INPUTS["r9_script"]),
        candidate_robin_sha256=sha256(INPUTS["r9_robin"]),
        structural_fidelity_contract_sha256=sha256(destination / FIDELITY_SUPPORT),
    )
    (destination / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "instruction_utf16": instruction_utf16,
                "instruction_sha256": manifest["instruction_sha256"],
                "bundle_sha256": manifest["bundle_sha256"],
                "manifest_sha256": sha256(destination / "manifest.json"),
                "teaching_robin_sha256": manifest["evidence"]["source_pad_recopy_sha256"],
                "structural_fidelity_contract_sha256": manifest["evidence"]["structural_fidelity_contract_sha256"],
                "independence": manifest["evidence"]["teaching_test_independence"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "copilot/versions" / VERSION
    )
    build(parser.parse_args().output)
