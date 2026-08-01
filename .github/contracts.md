# contract: .github/

**Purpose** — repository-host automation that enforces the same local gates at
the collaboration boundary.

## Allowed

| Pattern | What |
|---|---|
| `contracts.md` | this file |
| `workflows/` | GitHub Actions workflows (own contract) |

## Validate

- Workflow YAML parses.
- Publication workflows call the repository-owned gate; they do not duplicate
  its selection or verdict logic in YAML.
