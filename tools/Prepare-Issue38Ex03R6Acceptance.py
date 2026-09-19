"""Freeze the single normal-Copilot / at-most-two-PAD-run EX03 r6 cycle."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'catalog/acceptance/issue38'
CYCLE = BASE / 'cycles/EX03-r6-G1'
RUN = BASE / 'runs/EX03-attempt1'
VERSION = ROOT / 'copilot/versions/20260916-excel-r6'
BASE_COMMIT = '1701d8dd3ca88c2c60de443205e54a764e578fc9'
OLD_CYCLE = BASE / 'cycles/EX03-r5-G1'
PROBE = BASE / 'probes/percent-text-write'


def load_oracle():
    spec = importlib.util.spec_from_file_location(
        'issue38_excel_oracle', ROOT / 'tools/Verify-Issue38Excel.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load_oracle()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def repo_path(path):
    return Path(path).resolve().relative_to(ROOT.resolve()).as_posix()


def write_bytes(path, value):
    with Path(path).open('xb') as handle:
        handle.write(value)


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def protected_paths():
    fixed = [
        BASE / 'expected.json',
        BASE / 'spec.json',
        BASE / 'freeze.json',
        BASE / 'requests/EX03.txt',
        BASE / 'fixtures/EX03/入力い.xlsx',
        BASE / 'fixtures/EX03/入力ろ.xlsx',
        BASE / 'fixtures/EX03/ひな形.xlsx',
    ]
    trees = [
        ROOT / 'copilot/versions/20260915-excel-r5',
        OLD_CYCLE,
        PROBE,
        VERSION,
    ]
    paths = list(fixed)
    for tree in trees:
        paths.extend(sorted(path for path in tree.rglob('*') if path.is_file()))
    unique = {path.resolve(): path for path in paths}
    return [unique[key] for key in sorted(unique, key=lambda item: str(item).lower())]


def prepare():
    if CYCLE.exists():
        raise ValueError(f'Cycle already exists; refusing overwrite: {CYCLE}')
    head = subprocess.check_output(
        ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True
    ).strip()
    if head != BASE_COMMIT:
        raise ValueError(f'Expected base commit {BASE_COMMIT}, found {head}')
    oracle.check_frozen()

    manifest_path = VERSION / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['version'] != '20260916-excel-r6':
        raise ValueError('Unexpected candidate version')
    instruction_path = VERSION / manifest['instruction_path']
    bundle_path = VERSION / manifest['bundle_path']
    support_record = manifest['support_files'][0]
    support_path = VERSION / support_record['path']
    if sha(instruction_path) != manifest['instruction_sha256']:
        raise ValueError('r6 instruction hash mismatch')
    if sha(bundle_path) != manifest['bundle_sha256']:
        raise ValueError('r6 bundle hash mismatch')
    if sha(support_path) != support_record['sha256']:
        raise ValueError('r6 embedded-script hash mismatch')
    for record in manifest['source_files']:
        if sha(VERSION / record['path']) != record['sha256']:
            raise ValueError('r6 source hash mismatch: ' + record['path'])
    for path, expected in manifest['evidence_inputs'].items():
        if sha(ROOT / path) != expected:
            raise ValueError('r6 evidence input changed: ' + path)

    request_path = BASE / 'requests/EX03.txt'
    expected_path = BASE / 'expected.json'
    spec_path = BASE / 'spec.json'
    template_path = BASE / 'fixtures/EX03/ひな形.xlsx'
    input_a_path = BASE / 'fixtures/EX03/入力い.xlsx'
    input_b_path = BASE / 'fixtures/EX03/入力ろ.xlsx'
    work_path = RUN / 'work.xlsx'
    output_path = RUN / '照合結果.xlsx'
    preparation_path = RUN / 'preparation.json'
    old_archived_output = OLD_CYCLE / 'run1/result.xlsx'

    if not work_path.is_file() or sha(work_path) != sha(template_path):
        raise ValueError('EX03 work copy must exist and match the frozen template')
    if not preparation_path.is_file():
        raise ValueError('Existing EX03 preparation evidence is required')
    prior_runtime = None
    if output_path.exists():
        if not old_archived_output.is_file() or sha(output_path) != sha(old_archived_output):
            raise ValueError('Existing runtime output is not the archived r5 Run1 artifact')
        prior_runtime = {
            'path': repo_path(output_path),
            'sha256': sha(output_path),
            'archived_as': repo_path(old_archived_output),
            'archived_sha256': sha(old_archived_output),
            'safe_to_remove_for_new_fixed_run': True,
        }

    body = instruction_path.read_bytes() + b'\n' + request_path.read_bytes() + b'\n'
    body_text = body.decode('utf-8')
    forbidden_expected_values = ['春', '夏', '秋', '項目甲', '項目乙', '-4.5', '6.25']
    leaked = [value for value in forbidden_expected_values if value in body_text]
    if leaked:
        raise ValueError(f'Grader-only expected values leaked into submission: {leaked}')

    protected = {
        'schema_version': 1,
        'cycle_id': 'EX03-R6-G1',
        'base_commit': head,
        'files': [
            {'path': repo_path(path), 'sha256': sha(path)}
            for path in protected_paths()
        ],
    }

    if prior_runtime:
        output_path.unlink()
    if output_path.exists():
        raise ValueError('EX03 output collision after bounded prior-runtime cleanup')

    CYCLE.mkdir(parents=True, exist_ok=False)
    submitted_path = CYCLE / 'submitted-body.txt'
    write_bytes(submitted_path, body)
    plan = {
        'schema_version': 1,
        'cycle_id': 'EX03-R6-G1',
        'base_commit': head,
        'purpose': 'Same-version live acceptance of the fixed EX03 percent-text successor',
        'candidate': {
            'version': manifest['version'],
            'instruction_path': repo_path(instruction_path),
            'instruction_sha256': sha(instruction_path),
            'bundle_path': repo_path(bundle_path),
            'bundle_sha256': sha(bundle_path),
            'manifest_path': repo_path(manifest_path),
            'manifest_sha256': sha(manifest_path),
            'support_path': repo_path(support_path),
            'support_sha256': sha(support_path),
            'inherits_live_acceptance': False,
        },
        'fixed_inputs': {
            'request': {'path': repo_path(request_path), 'sha256': sha(request_path)},
            'spec': {'path': repo_path(spec_path), 'sha256': sha(spec_path)},
            'grader_only_expected': {
                'path': repo_path(expected_path),
                'sha256': sha(expected_path),
                'send_to_copilot': False,
            },
            'input_a': {'path': repo_path(input_a_path), 'sha256': sha(input_a_path)},
            'input_b': {'path': repo_path(input_b_path), 'sha256': sha(input_b_path)},
            'template': {'path': repo_path(template_path), 'sha256': sha(template_path)},
            'work': {
                'path': repo_path(work_path),
                'sha256': sha(work_path),
                'must_match_template_before_each_run': True,
            },
            'output': {
                'path': repo_path(output_path),
                'must_be_absent_before_each_run': True,
            },
        },
        'integration': {
            'text_sources': 7,
            'numeric_sources': 5,
            'text_write': 'one embedded PowerShell action before SaveAs; each fixed text target written once',
            'numeric_write': 'five ordinary numeric WriteCell actions',
            'workbook_guard': 'exact absolute FullName and exactly one matching active workbook',
            'cell_guard': 'seven fixed EX03 text target pairs only; formula targets refused',
            'format_restore': 'per-cell inner finally restores captured NumberFormat before validation',
            'post_fix': False,
            'external_runtime_file': False,
        },
        'submission': {
            'body_path': repo_path(submitted_path),
            'body_sha256': sha(submitted_path),
            'body_contract': 'unchanged full r6 instructions followed by unchanged EX03 request',
            'attachment_path': repo_path(bundle_path),
            'attachment_sha256': sha(bundle_path),
            'normal_m365_new_chat': True,
            'model': 'Think Deeper',
            'grader_only_expected_excluded': True,
            'completed_robin_excluded': True,
        },
        'limits': {
            'max_generation_requests': 1,
            'max_pad_runs': 2,
            'no_regeneration_or_manual_robin_repair': True,
            'stop_on_refusal_safety_issue_mismatch_or_unknown_result': True,
            'run2_requires_run1_terminal_and_artifact_preserved': True,
        },
        'pad': {
            'new_dedicated_flow': True,
            'power_fx': 'OFF',
            'unmodified_code_copy_only': True,
            'save_and_recopy_before_run1': True,
            'preserve_run1_before_run2': True,
            'restore_work_from_frozen_template_before_run2': True,
            'output_absent_before_run2': True,
        },
        'acceptance': {
            'scope': 'fixed EX03 text/number case and r6 package only',
            'required': [
                'one normal-M365 send with exact full body and actual same-version bundle',
                'unmodified generated Robin, dedicated-flow paste/save/recopy',
                'Run1 terminal confirmation before Run2',
                'two PAD runs with 12 source/readback JSON type checks',
                'all 12 fixed expected values, types, and positions after save/reopen',
                'F6 text 100%, original effective format, empty prefix, and no formula',
                'all outside cells, formulas, effective formats and dimensions unchanged',
                'all input/template original SHA values unchanged',
            ],
            'no_old_pass_inheritance': True,
            'no_other_case_or_unconfirmed_type_generalization': True,
        },
        'github_write': False,
        'status': 'READY_AFTER_NON_LIVE_CHECKS',
    }
    preflight = {
        'schema_version': 1,
        'cycle_id': 'EX03-R6-G1',
        'base_commit': head,
        'checks': {
            'frozen_fixture_spec_request_expected_hashes_match': True,
            'r6_instruction_bundle_manifest_support_hashes_match': True,
            'r6_all_evidence_input_hashes_match': True,
            'r5_and_old_cycle_included_in_protection_manifest': True,
            'work_exists_and_matches_template': True,
            'output_absent': True,
            'grader_only_expected_values_except_authorized_percent_probe_absent_from_body': True,
            'completed_robin_absent_from_submission': True,
        },
        'prior_runtime_cleanup': prior_runtime or {
            'path': repo_path(output_path),
            'existed': False,
            'archived_r5_artifact_preserved': old_archived_output.is_file(),
        },
        'hashes': {
            'submitted_body': sha(submitted_path),
            'instruction': sha(instruction_path),
            'bundle': sha(bundle_path),
            'manifest': sha(manifest_path),
            'support': sha(support_path),
            'work_and_template': sha(work_path),
            'input_a': sha(input_a_path),
            'input_b': sha(input_b_path),
        },
        'decision': {
            'safe_to_run_non_live_checks': True,
            'copilot_generation': 'NOT_STARTED',
            'pad_run1': 'NOT_STARTED',
            'pad_run2': 'NOT_STARTED',
        },
    }
    write_json(CYCLE / 'plan.json', plan)
    write_json(CYCLE / 'protected-files-before.json', protected)
    write_json(CYCLE / 'preflight.json', preflight)
    return {
        'cycle': repo_path(CYCLE),
        'version': manifest['version'],
        'submitted_body_sha256': sha(submitted_path),
        'bundle_sha256': sha(bundle_path),
        'manifest_sha256': sha(manifest_path),
        'support_sha256': sha(support_path),
        'protected_file_count': len(protected['files']),
        'status': 'READY_AFTER_NON_LIVE_CHECKS',
    }


if __name__ == '__main__':
    print(json.dumps(prepare(), ensure_ascii=False, indent=2))
