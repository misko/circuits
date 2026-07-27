# contract: skills/shopping-list/

**Purpose** — the BUYING skill: given a project folder, produce a
per-distributor shopping list for the parts the fab will not source, with the
`M-IMPORT` grade of every number, a stock floor, and a coverage denominator.
It is the only skill here whose primary inputs come from OUTSIDE the repo, so
it is governed by canon **`M-QUOTE`** (design-policies.md, Meta) — the narrow
instance of `M-IMPORT` scoped to distributor facts.

**Mutability** — hand-edited. A tier change (a new distributor, a new
credential path, a new grade) must land in `design-policies.md`'s `M-QUOTE`
row and in `tests/t1_shopping_list.py` in the SAME change.

## Allowed

| Pattern | What |
|---|---|
| `SKILL.md` | the skill manual: the three founding incidents, the tier table, the Mouser protocol, the credential rules, the check IDs |
| `contracts.md` | this file |
| `scripts/` | the checker (own contract) |

## Credentials — the standing rule

- **No key, token or secret is ever written into this folder.** The skill READS
  `$MOUSER_API_KEY` or `<repo root>/.secrets/mouser.env` (gitignored, mode 600)
  and hardcodes neither the key nor an absolute path to it.
- Mouser passes the key in the **query string**, so every URL the tool records
  or reports is a leak site: error paths scrub it, cache files omit it, and
  `t1_shopping_list.t_the_key_is_never_printed` plants a sentinel key and greps
  stdout, the report, the JSON sidecar and every cache file.
- Recorded API fixtures live in `tests/fixtures/shopping_list/` and are grepped
  for credential-shaped content by `t_fixtures_carry_no_credential`.
- Absent credential = say so, degrade to the manual path, grade OWED. Never
  crash; never emit an unsourced list that looks sourced.

## Audit

- `scripts/contracts_audit.py` — structure + C-ISO (no `projects/<board>` path
  may appear here; worked evidence lives in `examples/` or `tests/fixtures/`).
- `skills/kicad-pcb/scripts/gate_contract_audit.py` — `shopping_list.py` prints
  a verdict, so it owes G-INPUT (names the project it graded), G-COVER (`N/M`
  per distributor) and G-RED (`tests/t1_shopping_list.py`).
- `tests/run_tests.sh` — `t1_shopping_list.py`, hermetic via `--replay`; the
  Q-WIDE / Q-SNIPPET / Q-IDENT known-bads are RED-verified against a neutered
  checker and the measurements are recorded in the suite docstring.
