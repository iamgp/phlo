import { execFile } from 'node:child_process'
import { mkdir, readdir, readFile, rm, stat, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { promisify } from 'node:util'
import * as Python from 'fumadocs-python'

const execFileAsync = promisify(execFile)

const appRoot = path.resolve(import.meta.dirname, '..')
const repoRoot = path.resolve(appRoot, '..')
const packagePath = path.join(appRoot, 'node_modules', 'fumadocs-python')
const sourceRoot = path.join(appRoot, '.source', 'python-reference')
const outRoot = path.join(appRoot, 'content', 'docs', 'python-reference')
const packagesRoot = path.join(repoRoot, 'packages')
const forceRebuild = process.env.PHLO_FORCE_PYTHON_REFERENCE === '1'

function titleForSegment(segment) {
  return segment
    .split(/[-_]/g)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function moduleTitle(moduleName) {
  return moduleName === 'phlo' ? 'phlo' : moduleName.replaceAll('_', '-')
}

async function readProjectVersion(pyprojectPath) {
  const content = await readFile(pyprojectPath, 'utf8')
  const match = content.match(/^version = "([^"]+)"/m)
  return match?.[1]
}

async function listPackageModules() {
  const packageDirs = await readdir(packagesRoot, { withFileTypes: true })
  const discovered = []

  for (const entry of packageDirs) {
    if (!entry.isDirectory()) continue

    const srcDir = path.join(packagesRoot, entry.name, 'src')
    try {
      const srcEntries = await readdir(srcDir, { withFileTypes: true })
      const moduleEntry = srcEntries.find(
        (child) => child.isDirectory() && !child.name.endsWith('.egg-info'),
      )

      if (!moduleEntry) continue

      discovered.push({
        packageName: entry.name,
        moduleName: moduleEntry.name,
        packageDir: path.join(packagesRoot, entry.name),
        version: await readProjectVersion(
          path.join(packagesRoot, entry.name, 'pyproject.toml'),
        ),
        srcDir,
      })
    } catch {
      continue
    }
  }

  return discovered.sort((a, b) => a.packageName.localeCompare(b.packageName))
}

async function newestMtimeMs(targetPath) {
  const targetStats = await stat(targetPath)
  let newest = targetStats.mtimeMs

  if (!targetStats.isDirectory()) {
    return newest
  }

  const entries = await readdir(targetPath, { withFileTypes: true })
  for (const entry of entries) {
    const entryPath = path.join(targetPath, entry.name)
    const entryNewest = await newestMtimeMs(entryPath)
    if (entryNewest > newest) {
      newest = entryNewest
    }
  }

  return newest
}

async function outputIsFresh(packageModules) {
  try {
    const requiredOutputs = [
      path.join(outRoot, 'index.mdx'),
      path.join(outRoot, 'core', 'index.mdx'),
      path.join(outRoot, 'core', 'phlo', 'index.mdx'),
      path.join(outRoot, 'packages', 'index.mdx'),
    ]
    await Promise.all(requiredOutputs.map((filePath) => stat(filePath)))

    const outputNewest = await newestMtimeMs(outRoot)
    const inputs = [
      path.join(repoRoot, 'pyproject.toml'),
      path.join(repoRoot, 'src', 'phlo'),
      path.join(repoRoot, 'docs', 'python-reference'),
      new URL(import.meta.url),
      ...packageModules.flatMap((entry) => [
        path.join(entry.packageDir, 'pyproject.toml'),
        entry.srcDir,
      ]),
    ]

    for (const input of inputs) {
      const inputPath = input instanceof URL ? input : path.resolve(input)
      const inputNewest = await newestMtimeMs(inputPath)
      if (inputNewest > outputNewest) {
        return false
      }
    }

    return true
  } catch {
    return false
  }
}

async function generateModuleJson(moduleName, pythonPathEntries, version) {
  const moduleSourceDir = path.join(sourceRoot, moduleName)
  const jsonPath = path.join(moduleSourceDir, `${moduleName}.json`)
  await mkdir(moduleSourceDir, { recursive: true })
  const script = `
import json
import sys
import griffe
from fumapy.mksource import CustomEncoder, parse_module
import fumapy.mksource.document_module as document_module
from griffe_typingdoc import TypingDocExtension

module_name = sys.argv[1]
output_path = sys.argv[2]
version = sys.argv[3]
document_module.version = lambda _name: "unknown" if version == "__NONE__" else version
extensions = griffe.load_extensions(TypingDocExtension)
parsed = parse_module(
    griffe.load(module_name, docstring_parser="auto", store_source=True, extensions=extensions)
)
with open(output_path, "w") as f:
    json.dump(parsed, f, cls=CustomEncoder, indent=2, full=True)
`

  await execFileAsync(
    'uv',
    [
      'run',
      '--with',
      packagePath,
      'python',
      '-c',
      script,
      moduleName,
      jsonPath,
      version ?? '__NONE__',
    ],
    {
      cwd: repoRoot,
      env: {
        ...process.env,
        PYTHONPATH: pythonPathEntries.join(path.delimiter),
      },
    },
  )

  return JSON.parse(await readFile(jsonPath, 'utf8'))
}

function filterPrivatePaths(output) {
  return output.filter(
    ({ path: pagePath }) =>
      !pagePath.split('/').some((segment) => segment.startsWith('_')),
  )
}

function rewriteModuleLinks(output, moduleName, publicBase) {
  const absoluteBase = `/docs/${moduleName}`

  return output.map((file) => ({
    ...file,
    content: file.content
      .replaceAll(`"${absoluteBase}/`, `"${publicBase}/`)
      .replaceAll(`"{${absoluteBase}/`, `"{${publicBase}/`)
      .replaceAll(`"${absoluteBase}"`, `"${publicBase}"`),
  }))
}

async function quietWrite(output, targetDir) {
  const originalLog = console.log
  console.log = () => {}
  try {
    await Python.write(output, { outDir: targetDir })
  } finally {
    console.log = originalLog
  }
}

async function writePage(filePath, content) {
  await mkdir(path.dirname(filePath), { recursive: true })
  await writeFile(filePath, content)
}

async function writeMeta(dir, titleOverride) {
  const entries = await readdir(dir, { withFileTypes: true })
  const dirs = entries
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b))
  const pages = entries
    .filter(
      (entry) =>
        entry.isFile() &&
        entry.name.endsWith('.mdx') &&
        entry.name !== 'index.mdx' &&
        entry.name !== 'meta.json',
    )
    .map((entry) => entry.name.replace(/\.mdx$/, ''))
    .sort((a, b) => a.localeCompare(b))
  const title = titleOverride ?? titleForSegment(path.basename(dir))

  await writeFile(
    path.join(dir, 'meta.json'),
    `${JSON.stringify({ title, pages: ['index', ...dirs, ...pages] }, null, 2)}\n`,
  )

  await Promise.all(dirs.map((entry) => writeMeta(path.join(dir, entry))))
}

const packageModules = await listPackageModules()
const pythonPathEntries = [
  path.join(repoRoot, 'src'),
  ...packageModules.map((entry) => entry.srcDir),
]
const coreVersion = await readProjectVersion(
  path.join(repoRoot, 'pyproject.toml'),
)

if (!forceRebuild && (await outputIsFresh(packageModules))) {
  console.log('Python reference is up to date; skipping regeneration.')
  process.exit(0)
}

await rm(outRoot, { recursive: true, force: true })
await rm(sourceRoot, { recursive: true, force: true })
await mkdir(outRoot, { recursive: true })
await mkdir(sourceRoot, { recursive: true })

const coreRaw = await generateModuleJson('phlo', pythonPathEntries, coreVersion)
const coreOutput = rewriteModuleLinks(
  filterPrivatePaths(Python.convert(coreRaw, { baseUrl: '/docs' })),
  'phlo',
  '/docs/python-reference/core/phlo',
)
await quietWrite(coreOutput, path.join(outRoot, 'core', 'phlo'))

const packagePages = []
for (const entry of packageModules) {
  const raw = await generateModuleJson(
    entry.moduleName,
    pythonPathEntries,
    entry.version,
  )
  const converted = rewriteModuleLinks(
    filterPrivatePaths(Python.convert(raw, { baseUrl: '/docs' })),
    entry.moduleName,
    `/docs/python-reference/packages/${entry.packageName}/${entry.moduleName}`,
  )
  await quietWrite(
    converted,
    path.join(outRoot, 'packages', entry.packageName, entry.moduleName),
  )
  packagePages.push(`- [${entry.packageName}](./${entry.packageName})`)
}

await writePage(
  path.join(outRoot, 'index.mdx'),
  `---
title: Python Reference
description: Generated symbol-level reference for the Phlo core runtime and workspace packages.
---

Use this section when you need signatures, docstrings, class members, or module-level reference.

## Sections

- [Core](./core)
- [Packages](./packages)
`,
)

await writePage(
  path.join(outRoot, 'core', 'index.mdx'),
  `---
title: Core
description: Generated reference for the core \`phlo\` package under \`src/phlo/\`.
---

Core runtime reference for CLI, capabilities, hooks, configuration, operations, and plugin infrastructure.

- Start with [phlo](./phlo)
- Pair with [Reference](../../reference/index.md) for canonical commands, contracts, and architecture
`,
)

await writePage(
  path.join(outRoot, 'packages', 'index.mdx'),
  `---
title: Packages
description: Generated reference for workspace package Python modules.
---

Generated symbol-level reference for the installable workspace packages.

${packagePages.join('\n')}
`,
)

for (const entry of packageModules) {
  await writePage(
    path.join(outRoot, 'packages', entry.packageName, 'index.mdx'),
    `---
title: ${entry.packageName}
description: Generated reference for the \`${entry.moduleName}\` Python module.
---

Package module reference for \`${entry.packageName}\`.

- Start with [${moduleTitle(entry.moduleName)}](./${entry.moduleName})
- Pair with [package docs](../../../packages/${entry.packageName}.md) for usage, runtime role, and setup context
`,
  )
}

const outStats = await stat(outRoot)
if (!outStats.isDirectory()) {
  throw new Error(`Expected generated Python reference directory at ${outRoot}`)
}

await writeMeta(outRoot, 'Python Reference')
