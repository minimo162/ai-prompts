import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { FileBlob, SpreadsheetFile } = await import(
  pathToFileURL(require.resolve("@oai/artifact-tool")),
);

const probe = path.dirname(new URL(import.meta.url).pathname.slice(1));
const normal = path.join(
  probe,
  "trials",
  "EX03-R2R3-POSTFIX-20260917-T1",
  "normal",
);
const resultPath = path.join(normal, "runtime", "result.xlsx");

async function sha256(filePath) {
  const bytes = await fs.readFile(filePath);
  return crypto.createHash("sha256").update(bytes).digest("hex");
}

const beforeSha256 = await sha256(resultPath);
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(resultPath));
const sheet = workbook.worksheets.getItem("Target");
const range = sheet.getRange("A2:D2");
const inspection = await workbook.inspect({
  kind: "region,formula,computedStyle",
  sheetId: "Target",
  range: "A1:D2",
  maxChars: 12000,
  options: { maxResults: 50 },
});
await fs.writeFile(
  path.join(normal, "result-artifact-inspect.ndjson"),
  `${inspection.ndjson}\n`,
  "utf8",
);
const preview = await workbook.render({
  sheetName: "Target",
  range: "A1:D2",
  scale: 2,
  format: "png",
});
await fs.writeFile(
  path.join(normal, "result-preview.png"),
  new Uint8Array(await preview.arrayBuffer()),
);
const afterSha256 = await sha256(resultPath);
const record = {
  schema_version: 1,
  trial_id: "EX03-R2R3-POSTFIX-20260917-T1",
  result_xlsx_sha256_before: beforeSha256,
  result_xlsx_sha256_after: afterSha256,
  result_xlsx_unchanged: beforeSha256 === afterSha256,
  sheet: "Target",
  range: "A2:D2",
  values: range.values,
  formulas: range.formulas,
  javascript_value_types: range.values[0].map((value) => typeof value),
  inspect_path: "result-artifact-inspect.ndjson",
  preview_path: "result-preview.png",
};
await fs.writeFile(
  path.join(normal, "artifact-inspection.json"),
  `${JSON.stringify(record, null, 2)}\n`,
  "utf8",
);
console.log(JSON.stringify(record));

process.exit(0);
