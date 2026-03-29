import { cp, mkdir, readdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const thisDir = path.dirname(fileURLToPath(import.meta.url));
const appRoot = path.resolve(thisDir, "..");
const sourceRoot = path.resolve(appRoot, "..", "docs");
const targetRoot = path.resolve(appRoot, "content", "docs");
const excludedDirs = new Set([
  path.join("architecture", "decisions"),
  path.join("architecture", "goals"),
  path.join("architecture", "specs"),
  "handoffs",
  "blog",
]);

async function removeDsStore(root) {
  const entries = await readdir(root, { withFileTypes: true });
  await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(root, entry.name);
      if (entry.isDirectory()) {
        await removeDsStore(entryPath);
        return;
      }
      if (entry.name === ".DS_Store") {
        await rm(entryPath, { force: true });
      }
    }),
  );
}

async function normalizeCodeFenceLanguages(root) {
  const entries = await readdir(root, { withFileTypes: true });
  await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(root, entry.name);
      if (entry.isDirectory()) {
        await normalizeCodeFenceLanguages(entryPath);
        return;
      }
      if (!entry.name.endsWith(".md") && !entry.name.endsWith(".mdx")) {
        return;
      }

      const original = await readFile(entryPath, "utf8");
      const normalized = original
        .replaceAll("```env\n", "```bash\n")
        .replaceAll("```promql\n", "```text\n")
        .replaceAll("```logql\n", "```text\n");

      if (normalized !== original) {
        await writeFile(entryPath, normalized);
      }
    }),
  );
}

function stripEmoji(text) {
  return text.replaceAll(/\p{Extended_Pictographic}\uFE0F?/gu, "");
}

async function normalizeDocsContent(root) {
  const entries = await readdir(root, { withFileTypes: true });
  await Promise.all(
    entries.map(async (entry) => {
      const entryPath = path.join(root, entry.name);
      if (entry.isDirectory()) {
        await normalizeDocsContent(entryPath);
        return;
      }
      if (!entry.name.endsWith(".md") && !entry.name.endsWith(".mdx")) {
        return;
      }

      const original = await readFile(entryPath, "utf8");
      const normalized = stripEmoji(original);

      if (normalized !== original) {
        await writeFile(entryPath, normalized);
      }
    }),
  );
}

async function removeExcludedDirs(root, relative = "") {
  const entries = await readdir(root, { withFileTypes: true });
  await Promise.all(
    entries.map(async (entry) => {
      if (!entry.isDirectory()) {
        return;
      }

      const nextRelative = relative ? path.join(relative, entry.name) : entry.name;
      const entryPath = path.join(root, entry.name);

      if (excludedDirs.has(nextRelative)) {
        await rm(entryPath, { recursive: true, force: true });
        return;
      }

      await removeExcludedDirs(entryPath, nextRelative);
    }),
  );
}

await mkdir(path.dirname(targetRoot), { recursive: true });
await rm(targetRoot, { recursive: true, force: true });
await cp(sourceRoot, targetRoot, { recursive: true });

const targetStats = await stat(targetRoot);
if (!targetStats.isDirectory()) {
  throw new Error(`Expected synced docs directory at ${targetRoot}`);
}

await removeDsStore(targetRoot);
await removeExcludedDirs(targetRoot);
await normalizeCodeFenceLanguages(targetRoot);
await normalizeDocsContent(targetRoot);
