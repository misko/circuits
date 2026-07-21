# contract: tscircuit_modules/

**Purpose** — the shared tscircuit module library: reusable circuit
sub-modules (`src/`) and their demo boards (`demo/`) proving each module
compiles and nets correctly outside any project.

## Allowed

| Pattern | What |
|---|---|
| `README.md` | module index + usage |
| `contracts.md` | this file |
| `.gitignore` | build/cache exclusions |
| `src/**` | one `.tsx` per reusable module |
| `demo/**` | demo board per module family: `.tsx` source, `package.json`, build/dist/kicad/verification outputs committed as evidence |

## Audit

- A module lands with a demo whose verification outputs (netlist/ERC) are
  committed; `demo/verification/` is the evidence, not a claim.
- Modules are project-independent: no imports from `projects/`.
