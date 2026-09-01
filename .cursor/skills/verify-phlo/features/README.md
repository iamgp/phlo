# Feature map

Index of user-facing Phlo CLI features this skill can drive. Observatory UI is out of scope. `phlo-api` is secondary (reached after generated services start).

| File | Feature | Docker? |
| --- | --- | --- |
| [cli-identity.md](cli-identity.md) | `phlo --help` / `--version` | No |
| [project-init.md](project-init.md) | `phlo init` project layout | No |
| [plugin-check.md](plugin-check.md) | `phlo plugin list` / `plugin check` | `--containers` only |
| [doctor.md](doctor.md) | `phlo doctor` diagnostics | Probes Docker; CLI still runs |
| [services-generate.md](services-generate.md) | `phlo services init` / `start` / `status` | Generate: no. Start/status: yes |

Default proof: **project-init** (`scripts/prove-project-init.sh`).
