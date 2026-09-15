"""Verify EX02's fixed text/number source-to-target contract without widening it."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils.cell import coordinate_to_tuple, get_column_letter


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'catalog/acceptance/issue38'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = load('issue38_excel_oracle', 'tools/Verify-Issue38Excel.py')
ALLOWED_KINDS = {'text', 'number'}
EXCLUDED_KINDS = ['blank', 'boolean', 'date', 'error', 'formula-result', 'object']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fixed_mappings():
    spec = legacy.case_spec('EX02')
    matrices = json.loads((BASE / 'expected.json').read_text(encoding='utf-8'))['matrices']['EX02']
    if len(matrices) != len(spec['inputs']):
        raise ValueError('Fixed EX02 input and expected-matrix counts differ')
    mappings = []
    for item, expected_matrix in zip(spec['inputs'], matrices):
        source_c1, source_r1, source_c2, source_r2 = legacy.rectangle(item['range'])
        target_r1, target_c1 = coordinate_to_tuple(item['target_start'])
        if len(expected_matrix) != source_r2 - source_r1 + 1:
            raise ValueError('Fixed expected row shape mismatch')
        for row_offset, expected_row in enumerate(expected_matrix):
            if len(expected_row) != source_c2 - source_c1 + 1:
                raise ValueError('Fixed expected column shape mismatch')
            for column_offset, expected_value in enumerate(expected_row):
                source_cell = f'{get_column_letter(source_c1 + column_offset)}{source_r1 + row_offset}'
                target_cell = f'{get_column_letter(target_c1 + column_offset)}{target_r1 + row_offset}'
                expected_typed = legacy.typed(expected_value)
                if expected_typed[0] not in ALLOWED_KINDS:
                    raise ValueError(f'Unverified fixed expected type: {expected_typed[0]}')
                mappings.append({
                    'source_path': item['file'],
                    'source_sheet': item['sheet'],
                    'source_cell': source_cell,
                    'target_sheet': item['target_sheet'],
                    'target_cell': target_cell,
                    'grader_expected': expected_typed,
                })
    if len(mappings) != 12:
        raise ValueError(f'EX02 must have exactly 12 fixed mappings, found {len(mappings)}')
    return mappings


def typed_cell(sheet, address):
    cell = sheet[address]
    if cell.data_type == 'f':
        raise ValueError(f'Formula is outside the verified EX02 target-type scope: {sheet.title}!{address}')
    value = legacy.typed(cell.value)
    if value[0] not in ALLOWED_KINDS:
        raise ValueError(f'Unverified EX02 target type {value[0]}: {sheet.title}!{address}')
    return value


def verify_output(output, run_label):
    output = Path(output)
    if not output.is_file() or output.suffix.lower() != '.xlsx':
        raise ValueError('A saved EX02 xlsx output is required')
    legacy.check_frozen()
    mappings = fixed_mappings()
    original_paths = sorted({m['source_path'] for m in mappings})
    original_hashes_before = {path: sha(BASE / path) for path in original_paths}
    output_sha_before = sha(output)
    sources = {}
    target = load_workbook(output, data_only=False, read_only=True)
    try:
        for path in original_paths:
            sources[path] = load_workbook(BASE / path, data_only=False, read_only=True)
        results = []
        for mapping in mappings:
            source_value = typed_cell(
                sources[mapping['source_path']][mapping['source_sheet']], mapping['source_cell']
            )
            target_value = typed_cell(target[mapping['target_sheet']], mapping['target_cell'])
            expected = mapping['grader_expected']
            results.append({
                **mapping,
                'source_actual': source_value,
                'target_actual': target_value,
                'source_matches_expected': source_value == expected,
                'target_matches_expected': target_value == expected,
                'source_matches_target': source_value == target_value,
            })
    finally:
        target.close()
        for workbook in sources.values():
            workbook.close()
    legacy.check_frozen()
    original_hashes_after = {path: sha(BASE / path) for path in original_paths}
    output_sha_after = sha(output)
    mismatches = [
        result for result in results
        if not (result['source_matches_expected'] and result['target_matches_expected']
                and result['source_matches_target'])
    ]
    immutable = original_hashes_before == original_hashes_after and output_sha_before == output_sha_after
    return {
        'kind': 'EX02_FIXED_TEXT_NUMBER_TYPED_TRANSFER',
        'run_label': run_label,
        'status': 'MATCH_FIXED_EX02_TEXT_NUMBER_SCOPE' if not mismatches and immutable else 'FAIL',
        'scope': {
            'allowed_types': sorted(ALLOWED_KINDS),
            'explicitly_not_generalized_to': EXCLUDED_KINDS,
            'fixed_mapping_count': 12,
            'method': 'read saved xlsx and compare each fixed source/target coordinate with grader-only expected typed value',
            'pad_internal_json_identity': 'SEPARATE_UI_EVIDENCE',
        },
        'output': {
            'path': str(output.resolve()),
            'sha256_before': output_sha_before,
            'sha256_after': output_sha_after,
            'unchanged_by_verifier': output_sha_before == output_sha_after,
        },
        'originals_sha256_before': original_hashes_before,
        'originals_sha256_after': original_hashes_after,
        'originals_unchanged_by_verifier': original_hashes_before == original_hashes_after,
        'mappings': results,
        'mismatches': mismatches,
    }


def workbook_semantics(path):
    workbook = load_workbook(path, data_only=False, read_only=False)
    try:
        sheets = []
        for sheet in workbook.worksheets:
            cells = []
            for row in sheet.iter_rows(max_row=sheet.max_row, max_col=sheet.max_column):
                for cell in row:
                    cells.append({
                        'cell': cell.coordinate,
                        'value': legacy.cell_value(cell),
                        'style': legacy.style(cell),
                        'comment': cell.comment.text if cell.comment else None,
                    })
            row_dimensions = {
                str(key): [value.height, value.hidden]
                for key, value in sheet.row_dimensions.items()
            }
            column_dimensions = {
                str(key): [value.width, value.hidden, value.min, value.max]
                for key, value in sheet.column_dimensions.items()
            }
            sheets.append({
                'name': sheet.title,
                'max_row': sheet.max_row,
                'max_column': sheet.max_column,
                'merged_cells': str(sheet.merged_cells),
                'row_dimensions': row_dimensions,
                'column_dimensions': column_dimensions,
                'cells': cells,
            })
        return sheets
    finally:
        workbook.close()


def compare_runs(run1, run2):
    run1, run2 = Path(run1), Path(run2)
    before = {'run1': sha(run1), 'run2': sha(run2)}
    semantic1, semantic2 = workbook_semantics(run1), workbook_semantics(run2)
    after = {'run1': sha(run1), 'run2': sha(run2)}
    return {
        'kind': 'EX02_TWO_POSITIVE_RUN_SEMANTIC_COMPARISON',
        'status': 'MATCH' if semantic1 == semantic2 and before == after else 'FAIL',
        'run1': {'path': str(run1.resolve()), 'sha256_before': before['run1'], 'sha256_after': after['run1']},
        'run2': {'path': str(run2.resolve()), 'sha256_before': before['run2'], 'sha256_after': after['run2']},
        'binary_sha_equal': before['run1'] == before['run2'],
        'semantic_equal': semantic1 == semantic2,
        'scope': 'all used cells, typed values/formulas, semantic styles, comments, merges, row and column dimensions',
        'checked_cells': sum(len(sheet['cells']) for sheet in semantic1),
        'note': 'Binary archive equality is not required; each run is independently checked against the fixed EX02 oracle.',
    }


def write_new_json(path, value):
    path = Path(path)
    if path.exists():
        raise ValueError(f'Evidence exists; refusing overwrite: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    parser.add_argument('--run-label')
    parser.add_argument('--run1', type=Path)
    parser.add_argument('--run2', type=Path)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    if args.output:
        if args.run1 or args.run2 or not args.run_label:
            parser.error('--output requires --run-label and excludes --run1/--run2')
        result = verify_output(args.output, args.run_label)
    else:
        if not args.run1 or not args.run2 or args.run_label:
            parser.error('--run1 and --run2 are required together')
        result = compare_runs(args.run1, args.run2)
    write_new_json(args.evidence, result)
    print(json.dumps({
        'kind': result['kind'],
        'status': result['status'],
        'mismatch_count': len(result.get('mismatches', [])),
        'checked_cells': result.get('checked_cells'),
    }, ensure_ascii=False))
    raise SystemExit(0 if result['status'] in {'MATCH_FIXED_EX02_TEXT_NUMBER_SCOPE', 'MATCH'} else 1)
