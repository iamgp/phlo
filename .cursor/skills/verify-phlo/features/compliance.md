# Compliance evidence

A user exports a signed evidence pack and verifies a pack ZIP. Group `phlo compliance`.

## Sub-features

- `export-evidence` — required `--output/-o` and `--created-by`; optional `--domain --description --audit-records --signatures --manifest`.
- `verify-evidence` — `verify-evidence ZIP_PATH`; nonzero on integrity failure.

## How to get to it (user POV)

- `phlo compliance --help`
- `phlo compliance export-evidence -o /tmp/pack.zip --created-by user@example.com`
- `phlo compliance verify-evidence /tmp/pack.zip`

## Driving it with CLI

Preconditions:

- Isolated `/tmp` output paths. Export needs a working evidence key/capability; missing key surfaces `EvidenceKeyError` / nonzero exit.
- Verify is CLI-only given a ZIP.

- Help: `uv run --locked phlo compliance --help` → `export-evidence`, `verify-evidence`.
- Verify a junk file: `uv run --locked phlo compliance verify-evidence /tmp/not-a-pack.zip` → nonzero; capture stderr. Do not invent a passing pack.

## Gotchas

- Not `phlo governance` and not `phlo audit`.
- Do not commit evidence ZIPs with secrets.
