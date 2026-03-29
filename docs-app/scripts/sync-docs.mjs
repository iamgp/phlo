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
  "observatory",
]);
const excludedFiles = new Set([
  path.join("operations", "codebase-audit-checklist.md"),
  path.join("operations", "codebase-audit-findings-2026-02-13.md"),
  path.join("reference", "plugin-architecture.md"),
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

function yamlString(value) {
  return `"${value.replaceAll("\\", "\\\\").replaceAll('"', '\\"')}"`;
}

function splitFrontmatter(text) {
  if (!text.startsWith("---\n")) {
    return { frontmatter: "", body: text };
  }

  const end = text.indexOf("\n---\n", 4);
  if (end === -1) {
    return { frontmatter: "", body: text };
  }

  return {
    frontmatter: text.slice(0, end + 5),
    body: text.slice(end + 5),
  };
}

function extractLeadingTitleAndDescription(text) {
  const { frontmatter, body } = splitFrontmatter(text);
  const hasTitle = /(?:^|\n)title:/m.test(frontmatter);
  const hasDescription = /(?:^|\n)description:/m.test(frontmatter);

  let remaining = body.replace(/^\s*/, "");
  let extractedTitle = null;
  let extractedDescription = null;

  const titleMatch = remaining.match(/^#\s+(.+?)\n+/);
  if (titleMatch) {
    extractedTitle = titleMatch[1].trim();
    remaining = remaining.slice(titleMatch[0].length);
  }

  const descriptionMatch = remaining.match(
    /^((?:(?!\n(?:#|```|~~~|>|- |\* |\d+\. |\|)).+\n?)+)(?:\n{2,}|\n*$)/,
  );
  if (descriptionMatch) {
    const candidate = descriptionMatch[1].trim().replace(/\s+/g, " ");
    if (candidate && !candidate.includes(":") && candidate.length <= 220) {
      extractedDescription = candidate;
      remaining = remaining.slice(descriptionMatch[0].length).replace(/^\n+/, "");
    }
  }

  if (!frontmatter && !extractedTitle && !extractedDescription) {
    return text;
  }

  const frontmatterLines = frontmatter
    ? frontmatter
        .slice(4, -5)
        .split("\n")
        .filter((line) => line.length > 0)
    : [];

  if (!hasTitle && extractedTitle) {
    frontmatterLines.unshift(`title: ${yamlString(extractedTitle)}`);
  }

  if (!hasDescription && extractedDescription) {
    const titleIndex = frontmatterLines.findIndex((line) => line.startsWith("title:"));
    const descriptionLine = `description: ${yamlString(extractedDescription)}`;
    if (titleIndex === -1) {
      frontmatterLines.unshift(descriptionLine);
    } else {
      frontmatterLines.splice(titleIndex + 1, 0, descriptionLine);
    }
  }

  const nextFrontmatter =
    frontmatterLines.length > 0 ? `---\n${frontmatterLines.join("\n")}\n---\n\n` : "";
  const nextBody = remaining.replace(/^\n+/, "");

  return `${nextFrontmatter}${nextBody}`;
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
      const normalized = extractLeadingTitleAndDescription(stripEmoji(original));

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

async function removeExcludedFiles(root, relative = "") {
  const entries = await readdir(root, { withFileTypes: true });
  await Promise.all(
    entries.map(async (entry) => {
      const nextRelative = relative ? path.join(relative, entry.name) : entry.name;
      const entryPath = path.join(root, entry.name);

      if (entry.isDirectory()) {
        await removeExcludedFiles(entryPath, nextRelative);
        return;
      }

      if (excludedFiles.has(nextRelative)) {
        await rm(entryPath, { force: true });
      }
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
await removeExcludedFiles(targetRoot);
await normalizeCodeFenceLanguages(targetRoot);
await normalizeDocsContent(targetRoot);
