import { createHash } from 'node:crypto';

export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

// Byte offsets use a lossless one-byte Latin-1 view, never normalized text.
// This is deliberately limited to the two T10 literal contents.
function intervals(bytes, fields) {
  const view = bytes.toString('latin1');
  return fields.map(field => {
    const prefix = Buffer.from(field.prefix, 'utf8').toString('latin1');
    const start = view.indexOf(prefix);
    if (start < 0 || view.indexOf(prefix, start + 1) >= 0) throw Error('FIELD_MISSING_OR_AMBIGUOUS');
    const a = start + prefix.length;
    const b = view.indexOf("'''", a);
    if (b < a || /[\r\n]/.test(view.slice(a, b))) throw Error('INVALID_LITERAL');
    return { start: a, end: b, line: 1 + (view.slice(0, start).match(/\n/g) || []).length };
  });
}

export function compareT10(source, candidate, contract) {
  if (!Buffer.isBuffer(source) || !Buffer.isBuffer(candidate)) throw Error('BYTES_REQUIRED');
  if (sha256(source) !== contract.source_sha256) throw Error('SOURCE_HASH_MISMATCH');
  if (contract.fields?.length !== 2 || contract.fields[0].line !== 2 || contract.fields[1].line !== 4) throw Error('INVALID_CONTRACT');
  const src = intervals(source, contract.fields);
  for (let i = 0; i < 2; i++) {
    if (src[i].line !== contract.fields[i].line || !source.subarray(src[i].start, src[i].end).equals(Buffer.from(contract.fields[i].before, 'utf8'))) throw Error('SOURCE_FIELD_MISMATCH');
    if (/[\r\n]/.test(contract.fields[i].after) || contract.fields[i].after.includes("'''")) throw Error('INVALID_REPLACEMENT');
  }
  let dst;
  try { dst = intervals(candidate, contract.fields); }
  catch (error) { return { status: 'FAIL', authorized_contents: false, outside_bytes: false, mapping_status: error.message, source_sha256: sha256(source), candidate_sha256: sha256(candidate) }; }
  if (src[0].end > src[1].start || dst[0].end > dst[1].start) return { status: 'FAIL', authorized_contents: false, outside_bytes: false, mapping_status: 'ORDER_CHANGED' };
  const edits = src.map((s, i) => ({ source: s, candidate: dst[i], shift: dst[i].start - s.start,
    requested_value_equal: candidate.subarray(dst[i].start, dst[i].end).equals(Buffer.from(contract.fields[i].after, 'utf8')),
    requested_line_equal: dst[i].line === contract.fields[i].line }));
  const gaps = [];
  let a = 0, b = 0;
  for (let i = 0; i <= 2; i++) {
    const endA = i < 2 ? src[i].start : source.length;
    const endB = i < 2 ? dst[i].start : candidate.length;
    const x = source.subarray(a, endA), y = candidate.subarray(b, endB);
    let first = 0;
    while (first < Math.min(x.length, y.length) && x[first] === y[first]) first++;
    gaps.push({ source_start: a, source_end: endA, candidate_start: b, candidate_end: endB,
      shift: b - a, equal: x.equals(y), first_difference: x.equals(y) ? null : { source_offset: a + first, candidate_offset: b + first } });
    if (i < 2) { a = src[i].end; b = dst[i].end; }
  }
  const authorized = edits.every(e => e.requested_value_equal && e.requested_line_equal);
  const outside = gaps.every(g => g.equal);
  return { status: authorized && outside ? 'PASS' : 'FAIL', authorized_contents: authorized, outside_bytes: outside,
    source_sha256: sha256(source), candidate_sha256: sha256(candidate), source_bytes: source.length, candidate_bytes: candidate.length,
    offset_convention: 'zero-based half-open raw byte intervals; BOM, line endings and EOF remain in gaps', edits, gaps };
}
