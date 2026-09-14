import { readFile, writeFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { sha256 } from './Compare-T10Bytes.mjs';

// Save a directly acquired JS string, not a reconstructed Robin answer.
export async function saveCapture(capture, output) {
  const input = Buffer.from(capture.utf16le_base64, 'base64');
  if (input.toString('base64') !== capture.utf16le_base64 || input.length % 2) throw Error('INVALID_UTF16_BYTES');
  const value = input.toString('utf16le');
  const encoded = Buffer.from(value, 'utf8');
  if (value.length !== capture.utf16_code_units || sha256(encoded) !== capture.utf8_sha256 ||
      encoded.toString('utf8') !== value) throw Error('CAPTURE_ENCODING_MISMATCH');
  await writeFile(output, encoded, { flag: 'wx' });
  const saved = await readFile(output);
  if (!saved.equals(encoded)) throw Error('SAVE_MISMATCH');
  return { bytes: saved.length, sha256: sha256(saved), utf16_code_units: value.length,
    code_points: [...value].length, encoding: 'UTF-8, no added BOM or newline; U+FEFF retained if present',
    utf16_source_sha256: sha256(input), saved_equal_encoded_capture: true,
    source_file_raw_bytes_directly_observed: false };
}
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const record = JSON.parse(await readFile(process.argv[2], 'utf8'));
  console.log(JSON.stringify(await saveCapture(record, process.argv[3]), null, 2));
}
