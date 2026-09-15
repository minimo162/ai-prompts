"""Add dimensions to the unchanged legacy oracle; never convert its FAIL to PASS."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path

module = importlib.util.spec_from_file_location('legacy', Path(__file__).with_name('Verify-Issue38Excel.py'))
legacy = importlib.util.module_from_spec(module)
module.loader.exec_module(legacy)


def dimension(failure):
    for marker, name in [('value/type/position', 'values_types_positions'),
                         ('style changed', 'styles'), ('row dimension', 'row_dimensions'),
                         ('column dimension', 'column_dimensions'), ('comment changed', 'comments'),
                         ('merged cells changed', 'merges')]:
        if marker in failure:
            return name
    return 'structure'


def compare(output):
    output = Path(output)
    before = legacy.sha(output)
    old = legacy.compare('EX02', output)
    spec = legacy.case_spec('EX02')
    expected = legacy.targets(spec)
    template = legacy.load_workbook(legacy.BASE / spec['template'], data_only=False)
    actual = legacy.load_workbook(output, data_only=False)
    cells = []
    style_attributes = Counter()
    dimensions = []
    try:
        for ts in template:
            if ts.title not in actual.sheetnames:
                continue
            os = actual[ts.title]
            if max(ts.max_row, os.max_row) * max(ts.max_column, os.max_column) > 100000:
                continue  # The unchanged legacy oracle records Unexpected sheet size.
            for row in os.iter_rows(max_row=max(ts.max_row, os.max_row), max_col=max(ts.max_column, os.max_column)):
                for cell in row:
                    before_cell = ts[cell.coordinate]
                    target = (ts.title, cell.coordinate) in expected
                    wanted = expected.get((ts.title, cell.coordinate), legacy.cell_value(before_cell))
                    found = legacy.cell_value(cell)
                    cells.append({'sheet': ts.title, 'cell': cell.coordinate, 'target': target,
                                  'expected': wanted, 'actual': found, 'match': found == wanted})
                    for name in ['font', 'fill', 'border', 'alignment', 'number_format', 'protection']:
                        if str(getattr(cell, name)) != str(getattr(before_cell, name)):
                            style_attributes[name] += 1
            for r in sorted(set(ts.row_dimensions) | set(os.row_dimensions)):
                a, b = ts.row_dimensions[r], os.row_dimensions[r]
                if (a.height, a.hidden) != (b.height, b.hidden):
                    dimensions.append({'sheet': ts.title, 'row': r,
                                       'before': [a.height, a.hidden], 'after': [b.height, b.hidden]})
            for c in sorted(set(ts.column_dimensions) | set(os.column_dimensions)):
                a, b = ts.column_dimensions[c], os.column_dimensions[c]
                if (a.width, a.hidden, a.min, a.max) != (b.width, b.hidden, b.min, b.max):
                    dimensions.append({'sheet': ts.title, 'column': c,
                                       'before': [a.width, a.hidden, a.min, a.max],
                                       'after': [b.width, b.hidden, b.min, b.max]})
    finally:
        template.close()
        actual.close()
    # Reading may not change any original, fixed expectation or output.
    legacy.check_frozen()
    after = legacy.sha(output)
    if before != after:
        raise ValueError('Output changed during read-only comparison')
    counts = dict(Counter(dimension(f) for f in old['failures']))
    groups = {}
    for name, subset in [('target_values_types_positions', [c for c in cells if c['target']]),
                         ('outside_values_types_formulas', [c for c in cells if not c['target']])]:
        failures = [c for c in subset if not c['match']]
        groups[name] = {'checked': len(subset), 'mismatches': failures,
                        'status': 'MATCH_SAVED_XLSX_ONLY' if not failures and subset else 'FAIL'}
    return {'status': old['status'], 'kind': 'EX02_INDEPENDENT_DIAGNOSTIC',
            'legacy': old, 'failure_counts': counts, 'checks': groups,
            'style_attribute_difference_counts': dict(style_attributes),
            'dimension_differences': dimensions, 'cells': cells,
            'output_sha_before': before, 'output_sha_after': after,
            'originals_sha256': {p: legacy.sha(legacy.BASE / p) for p in
                                 [i['file'] for i in spec['inputs']] + [spec['template']]},
            'native_styles': 'NOT_RUN_BY_THIS_COMPARATOR',
            'flow_internal_type_check': 'NOT_PROVEN',
            'copilot_generation': 'NOT_ASSERTED', 'pad_execution': 'NOT_ASSERTED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    if args.evidence.exists():
        raise SystemExit('Evidence exists; refusing overwrite')
    result = compare(args.output)
    with args.evidence.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: result[k] for k in ['status', 'failure_counts', 'checks', 'style_attribute_difference_counts']}, ensure_ascii=False))
    raise SystemExit(1 if result['status'] == 'FAIL' else 0)
