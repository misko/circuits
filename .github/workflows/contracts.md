# contract: .github/workflows/

**Purpose** — CI entry points. Workflow files compose repository-owned scripts
and tests; policy logic stays in those versioned, locally runnable tools.

## Allowed

| Pattern | What |
|---|---|
| `contracts.md` | this file |
| `*.yml` `*.yaml` | GitHub Actions workflows |

## Validate

- Every required check is runnable locally with the command shown in the
  workflow.
- Branch protection requires publication checks; a push-triggered audit alone
  is detection after publication, not prevention.
