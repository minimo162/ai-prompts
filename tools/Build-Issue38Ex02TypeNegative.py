"""Create the fixed EX02 one-cell number-to-text negative from a positive PAD output."""
import argparse
import hashlib
import importlib.util
import json
import posixpath
import re
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
TARGET_SHEET = 'Target A'
TARGET_CELL = 'D4'
BEFORE_TYPED = ['number', 12.5]
AFTER_TYPED = ['text', '12.5']
WORKBOOK_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
DOC_REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = load('issue38_excel_oracle_for_negative', 'tools/Verify-Issue38Excel.py')
typed_transfer = load('issue38_typed_transfer_for_negative', 'tools/Verify-Issue38Ex02TypedTransfer.py')


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    return sha_bytes(Path(path).read_bytes())


def worksheet_member(entries):
    workbook = ET.fromstring(entries['xl/workbook.xml'])
    rels = ET.fromstring(entries['xl/_rels/workbook.xml.rels'])
    sheet = next((item for item in workbook.findall(f'.//{{{WORKBOOK_NS}}}sheet')
                  if item.attrib.get('name') == TARGET_SHEET), None)
    if sheet is None:
        raise ValueError(f'Missing fixed target sheet: {TARGET_SHEET}')
    relationship_id = sheet.attrib.get(f'{{{DOC_REL_NS}}}id')
    relationship = next((item for item in rels.findall(f'{{{REL_NS}}}Relationship')
                         if item.attrib.get('Id') == relationship_id), None)
    if relationship is None:
        raise ValueError('Missing fixed target worksheet relationship')
    target = relationship.attrib.get('Target', '')
    member = posixpath.normpath(posixpath.join('xl', target.lstrip('/')))
    if not member.startswith('xl/worksheets/') or '..' in member.split('/') or member not in entries:
        raise ValueError(f'Unsafe or missing worksheet member: {member}')
    return member


def mutate_fixed_cell(sheet_xml):
    pattern = re.compile(rb'<c(?=[^>]*\br="D4")[^>]*><v>12\.5</v></c>')
    matches = list(pattern.finditer(sheet_xml))
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one fixed numeric D4 cell, found {len(matches)}')
    match = matches[0]
    original = match.group(0)
    open_end = original.index(b'>')
    open_tag = original[:open_end + 1]
    if re.search(rb'\bt=', open_tag):
        raise ValueError('Fixed source D4 unexpectedly has an explicit type attribute')
    replacement = open_tag[:-1] + b' t="inlineStr"><is><t>12.5</t></is></c>'
    changed = sheet_xml[:match.start()] + replacement + sheet_xml[match.end():]
    if changed.count(replacement) != 1:
        raise ValueError('Fixed replacement was not unique')
    return changed, original.decode('utf-8'), replacement.decode('utf-8')


def typed_at(path, sheet, cell):
    workbook = load_workbook(path, data_only=False, read_only=True)
    try:
        item = workbook[sheet][cell]
        if item.data_type == 'f':
            return ['formula', item.value]
        return oracle.typed(item.value)
    finally:
        workbook.close()


def build(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists():
        raise ValueError(f'Negative output exists; refusing overwrite: {destination}')
    if typed_at(source, TARGET_SHEET, TARGET_CELL) != BEFORE_TYPED:
        raise ValueError('Positive source does not contain the fixed numeric 12.5 at Target A!D4')
    source_sha_before = sha(source)
    with ZipFile(source, 'r') as archive:
        infos = archive.infolist()
        entries = {info.filename: archive.read(info.filename) for info in infos}
        archive_comment = archive.comment
    member = worksheet_member(entries)
    changed_xml, original_fragment, replacement_fragment = mutate_fixed_cell(entries[member])
    if entries[member] == changed_xml:
        raise AssertionError('Fixed XML mutation did not change the worksheet payload')
    output_entries = dict(entries)
    output_entries[member] = changed_xml
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, 'x') as archive:
        archive.comment = archive_comment
        for info in infos:
            archive.writestr(info, output_entries[info.filename])
    source_sha_after = sha(source)
    if source_sha_before != source_sha_after:
        raise ValueError('Positive source changed while creating the negative')
    before_names = set(entries)
    with ZipFile(destination, 'r') as archive:
        after_names = set(archive.namelist())
        negative_entries = {name: archive.read(name) for name in archive.namelist()}
    if before_names != after_names:
        raise ValueError('Negative package members changed')
    member_differences = [name for name in sorted(entries) if entries[name] != negative_entries[name]]
    if member_differences != [member]:
        raise ValueError(f'Unexpected package payload differences: {member_differences}')
    after_typed = typed_at(destination, TARGET_SHEET, TARGET_CELL)
    if after_typed != AFTER_TYPED:
        raise ValueError(f'Negative target type mismatch: {after_typed}')
    semantic_before = typed_transfer.workbook_semantics(source)
    semantic_after = typed_transfer.workbook_semantics(destination)
    if len(semantic_before) != len(semantic_after):
        raise ValueError('Negative changed the workbook sheet count')
    deltas = []
    for before_sheet, after_sheet in zip(semantic_before, semantic_after):
        if before_sheet['name'] != after_sheet['name']:
            deltas.append({'kind': 'sheet-name', 'before': before_sheet['name'], 'after': after_sheet['name']})
            continue
        before_cells = {cell['cell']: cell for cell in before_sheet['cells']}
        after_cells = {cell['cell']: cell for cell in after_sheet['cells']}
        for address in sorted(set(before_cells) | set(after_cells)):
            before_cell, after_cell = before_cells.get(address), after_cells.get(address)
            if before_cell != after_cell:
                deltas.append({
                    'kind': 'cell',
                    'sheet': before_sheet['name'],
                    'cell': address,
                    'before': before_cell,
                    'after': after_cell,
                })
        for key in ['max_row', 'max_column', 'merged_cells', 'row_dimensions', 'column_dimensions']:
            if before_sheet[key] != after_sheet[key]:
                deltas.append({
                    'kind': key,
                    'sheet': before_sheet['name'],
                    'before': before_sheet[key],
                    'after': after_sheet[key],
                })
    if len(deltas) != 1 or deltas[0].get('sheet') != TARGET_SHEET or deltas[0].get('cell') != TARGET_CELL:
        raise ValueError(f'Negative semantic delta was not exactly {TARGET_SHEET}!{TARGET_CELL}: {deltas}')
    cell_delta = deltas[0]
    if cell_delta['before']['value'] != BEFORE_TYPED or cell_delta['after']['value'] != AFTER_TYPED:
        raise ValueError('Negative semantic value/type delta differs from fixed contract')
    if cell_delta['before']['style'] != cell_delta['after']['style']:
        raise ValueError('Negative changed the target cell style')
    if cell_delta['before']['comment'] != cell_delta['after']['comment']:
        raise ValueError('Negative changed the target cell comment')
    return {
        'kind': 'EX02_FIXED_ONE_CELL_TYPE_NEGATIVE',
        'status': 'CREATED_AND_ONE_LOGICAL_TYPE_MISMATCH_PROVEN',
        'scope': {
            'verified_before_type': 'number',
            'verified_after_type': 'text',
            'explicitly_not_generalized_to': typed_transfer.EXCLUDED_KINDS,
        },
        'positive_source': {
            'path': str(source.resolve()),
            'sha256_before': source_sha_before,
            'sha256_after': source_sha_after,
            'unchanged': source_sha_before == source_sha_after,
        },
        'negative_output': {
            'path': str(destination.resolve()),
            'sha256': sha(destination),
        },
        'fixed_change': {
            'sheet': TARGET_SHEET,
            'cell': TARGET_CELL,
            'before': BEFORE_TYPED,
            'after': AFTER_TYPED,
            'same_display_text': str(BEFORE_TYPED[1]) == AFTER_TYPED[1],
            'style_unchanged': cell_delta['before']['style'] == cell_delta['after']['style'],
            'comment_unchanged': cell_delta['before']['comment'] == cell_delta['after']['comment'],
        },
        'package_payload': {
            'member_count': len(entries),
            'changed_members': member_differences,
            'unchanged_member_count': len(entries) - len(member_differences),
            'source_member_sha256': sha_bytes(entries[member]),
            'negative_member_sha256': sha_bytes(negative_entries[member]),
            'original_cell_xml': original_fragment,
            'negative_cell_xml': replacement_fragment,
        },
        'semantic_delta_count': len(deltas),
        'semantic_deltas': deltas,
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
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    args = parser.parse_args()
    if args.evidence.exists() or args.output.exists():
        raise SystemExit('Output or evidence exists; refusing overwrite')
    result = build(args.source, args.output)
    write_new_json(args.evidence, result)
    print(json.dumps({
        'status': result['status'],
        'cell': f'{TARGET_SHEET}!{TARGET_CELL}',
        'before': BEFORE_TYPED,
        'after': AFTER_TYPED,
        'changed_members': result['package_payload']['changed_members'],
    }, ensure_ascii=False))
