import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { SpreadsheetFile } = await import(
  pathToFileURL(require.resolve("@oai/artifact-tool")),
);

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname.slice(1)));
for (const run of ["run1", "run2"]) {
  const workbookPath = path.join(root, run, "result.xlsx");
  const bytes = await fs.readFile(workbookPath);
  const arrayBuffer = bytes.buffer.slice(
    bytes.byteOffset,
    bytes.byteOffset + bytes.byteLength,
  );
  const workbook = await SpreadsheetFile.importXlsx(arrayBuffer);
  const inspection = await workbook.inspect({
    kind: "table",
    range: "Target!A1:B2",
    include: "values,formulas",
    tableMaxRows: 2,
    tableMaxCols: 2,
    maxChars: 4000,
  });
  await fs.writeFile(
    path.join(root, run, "result.inspect.ndjson"),
    `${inspection.ndjson}\n`,
    "utf8",
  );
  const preview = await workbook.render({
    sheetName: "Target",
    range: "A1:B2",
    scale: 2,
    format: "png",
  });
  await fs.writeFile(
    path.join(root, run, "result-preview.png"),
    new Uint8Array(await preview.arrayBuffer()),
  );
  console.log(`${run}: ${inspection.ndjson}`);
}

// artifact-tool may set a non-zero process exit code after successfully
// completing workbook rendering. Reaching this line means both outputs and
// inspections were written without an exception.
process.exitCode = 0;
