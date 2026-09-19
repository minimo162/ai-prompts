"""Classify the preserved EX02 legacy format failures without rewriting them."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from openpyxl import load_workbook
from openpyxl.utils.cell import column_index_from_string


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'catalog/acceptance/issue38'
CYCLE = BASE / 'cycles/EX02-r5-G2'

PATHS = {
    'template': BASE / 'fixtures/EX02/template.xlsx',
    'noop': BASE / 'cycles/EX02-r4/native-noop/result.xlsx',
    'run1': CYCLE / 'run1/result.xlsx',
    'run2': CYCLE / 'run2/result.xlsx',
    'legacy_noop': BASE / 'cycles/EX02-r4/native-noop/comparison.json',
    'legacy_run1': CYCLE / 'run1/comparison.json',
    'legacy_run2': CYCLE / 'run2/comparison.json',
    'native_noop': CYCLE / 'format-reconciliation/noop-effective.json',
    'native_run1': CYCLE / 'format-reconciliation/run1-effective.json',
    'native_run2': CYCLE / 'format-reconciliation/run2-effective.json',
    'negative': CYCLE / 'format-reconciliation/negative-format-dimensions.xlsx',
    'legacy_negative': CYCLE / 'format-reconciliation/negative-legacy.json',
    'native_negative': CYCLE / 'format-reconciliation/negative-effective.json',
    'old_acceptance': CYCLE / 'acceptance-status.json',
}

FAILURE_PATTERNS = [
    ('cell_style', re.compile(r'^(?P<sheet>.+)!(?P<location>[A-Z]+[1-9][0-9]*): style changed$')),
    ('row_dimension', re.compile(r'^(?P<sheet>.+): row dimension (?P<location>[1-9][0-9]*)$')),
    ('column_dimension', re.compile(r'^(?P<sheet>.+): column dimension (?P<location>[A-Z]+)$')),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def canonical_sha(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def json_read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def parse_failure(text):
    for category, pattern in FAILURE_PATTERNS:
        match = pattern.fullmatch(text)
        if match:
            return category, match.group('sheet'), match.group('location')
    return None


def color(value):
    if value is None:
        return None
    return {key: item for key, item in value.__dict__.items() if not key.startswith('_')}


def side(value):
    if value is None:
        return None
    return {'style': value.style, 'color': color(value.color)}


def cell_style(cell):
    font = cell.font
    fill = cell.fill
    border = cell.border
    alignment = cell.alignment
    protection = cell.protection
    return {
        'font': {
            'name': font.name, 'size': font.sz, 'bold': font.b, 'italic': font.i,
            'underline': font.u, 'strike': font.strike, 'color': color(font.color),
            'vertical_align': font.vertAlign, 'charset': font.charset, 'family': font.family,
            'scheme': font.scheme, 'outline': font.outline, 'shadow': font.shadow,
            'condense': font.condense, 'extend': font.extend,
        },
        'fill': {
            'type': fill.fill_type, 'pattern_type': fill.patternType,
            'foreground': color(fill.fgColor), 'background': color(fill.bgColor),
        },
        'border': {
            'left': side(border.left), 'right': side(border.right),
            'top': side(border.top), 'bottom': side(border.bottom),
            'diagonal': side(border.diagonal), 'vertical': side(border.vertical),
            'horizontal': side(border.horizontal), 'start': side(border.start),
            'end': side(border.end), 'outline': border.outline,
            'diagonal_up': border.diagonalUp, 'diagonal_down': border.diagonalDown,
        },
        'alignment': {
            key: value for key, value in alignment.__dict__.items() if not key.startswith('_')
        },
        'number_format': cell.number_format,
        'protection': {
            key: value for key, value in protection.__dict__.items() if not key.startswith('_')
        },
    }


def row_dimension(sheet, row_number):
    dimension = sheet.row_dimensions.get(row_number)
    if dimension is None:
        return {
            'height': None, 'hidden': False, 'outline_level': 0, 'collapsed': False,
            'thick_top': False, 'thick_bottom': False, 'style_id': 0,
        }
    return {
        'height': dimension.height,
        'hidden': bool(dimension.hidden),
        'outline_level': dimension.outlineLevel,
        'collapsed': bool(dimension.collapsed),
        'thick_top': bool(dimension.thickTop),
        'thick_bottom': bool(dimension.thickBot),
        'style_id': dimension.style_id,
    }


def column_dimension(sheet, column_letter):
    column_number = column_index_from_string(column_letter)
    covering = []
    for dimension in sheet.column_dimensions.values():
        minimum = dimension.min or column_index_from_string(dimension.index)
        maximum = dimension.max or minimum
        if minimum <= column_number <= maximum:
            covering.append((minimum, maximum, dimension))
    if len(covering) != 1:
        raise ValueError(
            f'Expected one serialized column record covering {sheet.title}!{column_letter}, '
            f'found {len(covering)}'
        )
    minimum, maximum, dimension = covering[0]
    return {
        'min': minimum, 'max': maximum, 'width': dimension.width,
        'hidden': bool(dimension.hidden), 'outline_level': dimension.outlineLevel,
        'collapsed': bool(dimension.collapsed), 'best_fit': bool(dimension.bestFit),
        'custom_width': bool(dimension.customWidth), 'style_id': dimension.style_id,
    }


def deep_differences(before, after, prefix=''):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before) | set(after)):
            path = f'{prefix}.{key}' if prefix else key
            result.extend(deep_differences(before.get(key), after.get(key), path))
        return result
    if before != after:
        return [{'attribute': prefix, 'before': before, 'after': after}]
    return []


def raw_value(workbooks, name, category, sheet_name, location):
    sheet = workbooks[name][sheet_name]
    if category == 'cell_style':
        return cell_style(sheet[location])
    if category == 'row_dimension':
        return row_dimension(sheet, int(location))
    if category == 'column_dimension':
        return column_dimension(sheet, location)
    raise ValueError(category)


def effective_value(native, side_name, category, sheet_name, location):
    snapshot = native[f'{side_name}_snapshot'][sheet_name]
    if category == 'cell_style':
        return snapshot['cells'][location]
    if category == 'row_dimension':
        return snapshot['rows'][str(location)]
    if category == 'column_dimension':
        return snapshot['columns'][str(column_index_from_string(location))]
    raise ValueError(category)


def cause(category):
    return {
        'cell_style': 'FONT_METADATA_AND_EMPTY_BORDER_ELEMENT_NORMALIZATION',
        'row_dimension': 'ROW_HEIGHT_UNIT_SERIALIZATION_NORMALIZATION',
        'column_dimension': 'EQUIVALENT_COLUMN_RECORD_COALESCING',
    }[category]


def classify(evidence_path):
    for name, path in PATHS.items():
        if not path.is_file():
            raise ValueError(f'Missing fixed input: {name}: {path}')
    hashes_before = {name: sha(path) for name, path in PATHS.items()}
    legacy = {name: json_read(PATHS[f'legacy_{name}']) for name in ('noop', 'run1', 'run2')}
    native = {name: json_read(PATHS[f'native_{name}']) for name in ('noop', 'run1', 'run2')}
    old_acceptance = json_read(PATHS['old_acceptance'])
    negative_legacy = json_read(PATHS['legacy_negative'])
    negative_native = json_read(PATHS['native_negative'])

    if old_acceptance['legacy_558']['count'] != 558 or old_acceptance['overall']['accepted']:
        raise ValueError('The preserved old FAIL no longer has its recorded state')
    positive_snapshot_hashes = set()
    for name in ('noop', 'run1', 'run2'):
        if native[name]['status'] != 'MATCH_EFFECTIVE_FORMAT' or native[name]['differences']:
            raise ValueError(f'Positive effective-format comparison is not a match: {name}')
        if native[name]['snapshot_sha256']['reference'] != native[name]['snapshot_sha256']['output']:
            raise ValueError(f'Positive effective snapshot hashes differ: {name}')
        positive_snapshot_hashes.add(native[name]['snapshot_sha256']['reference'])
    if len(positive_snapshot_hashes) != 1:
        raise ValueError('No-op, Run1 and Run2 do not share one Excel-effective snapshot')
    positive_snapshot_sha256 = next(iter(positive_snapshot_hashes))

    format_failures = {}
    for name, record in legacy.items():
        parsed = [parse_failure(item) for item in record['legacy']['failures']]
        format_failures[name] = {
            (category, sheet, location): text
            for text, parsed_item in zip(record['legacy']['failures'], parsed)
            if parsed_item is not None
            for category, sheet, location in [parsed_item]
        }
    canonical_keys = set(format_failures['run1'])
    if len(canonical_keys) != 558:
        raise ValueError(f'Run1 must preserve exactly 558 legacy format failures, found {len(canonical_keys)}')
    if canonical_keys != set(format_failures['run2']) or canonical_keys != set(format_failures['noop']):
        raise ValueError('The no-op, Run1 and Run2 legacy format failure locations differ')

    workbooks = {
        name: load_workbook(PATHS[name], data_only=False, read_only=False)
        for name in ('template', 'noop', 'run1', 'run2')
    }
    entries = []
    raw_attribute_counts = Counter()
    classification_counts = Counter()
    try:
        for category, sheet_name, location in sorted(canonical_keys):
            template_value = raw_value(workbooks, 'template', category, sheet_name, location)
            raw_changes = {}
            for comparison in ('noop', 'run1', 'run2'):
                value = raw_value(workbooks, comparison, category, sheet_name, location)
                raw_changes[comparison] = deep_differences(template_value, value)
            same_raw_change = canonical(raw_changes['noop']) == canonical(raw_changes['run1']) == canonical(raw_changes['run2'])
            effective_before = effective_value(native['run1'], 'reference', category, sheet_name, location)
            effective_after = effective_value(native['run1'], 'output', category, sheet_name, location)
            effective_changes = deep_differences(effective_before, effective_after)
            if same_raw_change and raw_changes['run1'] and not effective_changes:
                classification = 'SERIALIZATION_OR_COMPARISON_METHOD_ONLY'
            elif effective_changes:
                classification = 'ACTUAL_EFFECTIVE_FORMAT_CHANGE'
            else:
                classification = 'UNRESOLVED'
            classification_counts[classification] += 1
            for change in raw_changes['run1']:
                raw_attribute_counts[f'{category}:{change["attribute"]}'] += 1
            entries.append({
                'legacy_failure': format_failures['run1'][(category, sheet_name, location)],
                'category': category,
                'sheet': sheet_name,
                'location': location,
                'raw_cause': cause(category),
                'raw_template_to_run1': raw_changes['run1'],
                'raw_change_reproduced_by_noop_and_run2': same_raw_change,
                'effective_before_sha256': canonical_sha(effective_before),
                'effective_after_sha256': canonical_sha(effective_after),
                'effective_changed_attributes': effective_changes,
                'classification': classification,
            })
    finally:
        for workbook in workbooks.values():
            workbook.close()

    category_counts = Counter(entry['category'] for entry in entries)
    representatives = {}
    preferred = {
        'cell_style': ('Target A', 'C4'),
        'row_dimension': ('Target A', '1'),
        'column_dimension': ('Target A', 'A'),
    }
    for category, (sheet_name, location) in preferred.items():
        entry = next(item for item in entries
                     if item['category'] == category and item['sheet'] == sheet_name
                     and item['location'] == location)
        before = effective_value(native['run1'], 'reference', category, sheet_name, location)
        after = effective_value(native['run1'], 'output', category, sheet_name, location)
        representatives[category] = {
            **entry,
            'effective_before': before,
            'effective_after': after,
        }

    expected_negative = {
        ('cell_style', 'Target A', 'C4', 'fill'),
        ('row_dimension', 'Target A', '2', 'height'),
        ('column_dimension', 'Target A', '2', 'width'),
    }
    actual_negative = {
        (item['category'], item['sheet'], str(item['location']), item['attribute'])
        for item in negative_native['differences']
    }
    negative_pass = (
        negative_native['status'] == 'DIFFERENCES_FOUND'
        and actual_negative == expected_negative
        and negative_legacy['checks']['target_values_types_positions']['mismatches'] == []
        and negative_legacy['checks']['outside_values_types_formulas']['mismatches'] == []
    )
    all_classified = classification_counts == Counter({'SERIALIZATION_OR_COMPARISON_METHOD_ONLY': 558})
    result = {
        'schema_version': 1,
        'kind': 'EX02_LEGACY_558_FORMAT_RECONCILIATION',
        'scope': {
            'baseline': 'frozen EX02 template',
            'comparisons': ['Excel no-edit SaveAs control', 'G2 Run1', 'G2 Run2'],
            'contract_area': 'all three sheets A1:J16; 480 cells, 48 rows, 30 columns',
            'method': 'preserved raw openpyxl/OOXML deltas correlated per location with read-only Excel-effective attributes',
        },
        'source_sha256': {
            name: hashes_before[name] for name in
            ('template', 'noop', 'run1', 'run2', 'legacy_noop', 'legacy_run1',
             'legacy_run2', 'native_noop', 'native_run1', 'native_run2')
        },
        'positive_effective_snapshot_sha256': positive_snapshot_sha256,
        'old_fail_preserved': {
            'path': str(PATHS['old_acceptance'].relative_to(ROOT)),
            'sha256': hashes_before['old_acceptance'],
            'accepted': old_acceptance['overall']['accepted'],
            'status': old_acceptance['overall']['status'],
            'legacy_count': old_acceptance['legacy_558']['count'],
        },
        'legacy_failure_counts': dict(category_counts),
        'raw_attribute_change_counts': dict(sorted(raw_attribute_counts.items())),
        'classification_counts': dict(classification_counts),
        'representative_before_after': representatives,
        'entries': entries,
        'negative_detection': {
            'status': 'PASS_EXACT_THREE_EFFECTIVE_CHANGES' if negative_pass else 'FAIL',
            'output_path': str(PATHS['negative'].relative_to(ROOT)),
            'output_sha256': hashes_before['negative'],
            'effective_differences': negative_native['differences'],
            'legacy_failure_counts': negative_legacy['failure_counts'],
            'target_value_type_position_mismatches': negative_legacy['checks']['target_values_types_positions']['mismatches'],
            'outside_value_type_formula_mismatches': negative_legacy['checks']['outside_values_types_formulas']['mismatches'],
            'visual_review': 'PASS_RED_FILL_ROW_HEIGHT_AND_COLUMN_WIDTH_VISIBLE',
        },
        'decision': {
            'status': 'PASS_558_CLASSIFIED_AS_NON_EFFECTIVE_NORMALIZATION' if all_classified and negative_pass else 'UNRESOLVED',
            'actual_effective_changes_in_positive_outputs': classification_counts['ACTUAL_EFFECTIVE_FORMAT_CHANGE'],
            'unresolved_legacy_failures': classification_counts['UNRESOLVED'],
            'legacy_comparator_problem': (
                'It compares openpyxl object serialization and sparse dimension records. '
                'Excel SaveAs adds font metadata and empty border elements, converts row-height units, '
                'and coalesces equivalent column records even when Excel-effective formatting is unchanged.'
            ),
            'acceptance_impact': (
                'The legacy 558 formatting/dimension blocker is resolved for the fixed EX02 files and '
                'Excel environment. The old FAIL remains immutable; this record is the separate adjudication.'
            ),
            'functional_g2_status_preserved': old_acceptance['overall']['functional_generated_pad_path'],
            'existing_output_guard_live_check': 'NOT_RUN_REMAINS_OPEN',
            'candidate_version_changed': False,
            'copilot_regenerated': False,
            'pad_additional_run': False,
            'github_write': False,
        },
    }
    hashes_after = {name: sha(path) for name, path in PATHS.items()}
    if hashes_before != hashes_after:
        raise ValueError('Read-only reconciliation changed an input or prior evidence file')
    evidence_path = Path(evidence_path)
    if evidence_path.exists():
        raise ValueError(f'Evidence exists; refusing overwrite: {evidence_path}')
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    with evidence_path.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    outcome = classify(args.evidence)
    print(json.dumps({
        'status': outcome['decision']['status'],
        'legacy_failure_counts': outcome['legacy_failure_counts'],
        'classification_counts': outcome['classification_counts'],
        'negative_detection': outcome['negative_detection']['status'],
    }, ensure_ascii=False))
    raise SystemExit(0 if outcome['decision']['status'].startswith('PASS_') else 1)
