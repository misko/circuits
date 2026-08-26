# contract: board project root

**Purpose** — one fabricable board, standalone and transferable. A clone with
no network and no sibling repos must be enough to understand, regenerate, and
re-order it.

**The organizing axis** — who writes a file, and may it change:

| Folder | Written by | Mutability |
|---|---|---|
| `01_docs/` | humans | hand-edited |
| `03_src/` | humans | hand-edited — THE source of truth |
| `03_tscircuit/` | humans | hand-edited — THE source of truth (TSX authoring; optional, per-board) |
| `02_parts/` | humans (once per part) | append; edit only on datasheet revision |
| `04_kicad/` | generators | regenerated, committed for reviewable diffs |
| `05_firmware/` | humans | hand-edited |
| `06_build/` | tools | disposable, gitignored |
| `07_releases/` | release step | **IMMUTABLE once written** |

## Allowed at root

| Pattern | What |
|---|---|
| `README.md` | what the board is, status, current release, how to build |
| `RESUME.md` | temporary, explicit pause/handoff state; never fabrication evidence |
| `contracts.md` | this file |
| `.gitignore` | must ignore `06_build/`; must NOT ignore `01_docs/decisions/` or `02_parts/` |
| `.gitattributes` | optional repository handling for review-critical binary artifacts such as PDFs and 3D CAD |
| `01_docs/ 03_src/ 03_tscircuit/ 02_parts/ 04_kicad/ 05_firmware/ 06_build/ 07_releases/ 08_reviews/` | see each folder's contract (`03_tscircuit/` only on TSX-authored boards) |

## Forbidden at root

- Loose design docs (`DESIGN.md`, `BOM.md` at root) — they go in `01_docs/`.
- Loose scripts — they go in `03_src/`.
- Any `*_v2`, `*_old`, `*_experiment`, `*_backup` file or folder. **Iterations
  live in git history, never in filenames.** A `board_v2.kicad_pcb` beside
  `board.kicad_pcb` is a defect: nothing says which one is real.
- Generated artifacts (PNG/PDF/netlist) — they go in `06_build/`.

## Fresh-agent verification — zero context required

A brand-new agent verifies the whole project in this order; every step names
its command and expected result:

1. **Read the commission**: `01_docs/BRIEF.md` — verify its own audit block
   (prompt hash, tag resolution, register↔decisions bijection; commands in
   `01_docs/contracts.md`). This tells you WHAT the project must do.
2. **Rebuild + gate**: `bash 03_src/rebuild_all.sh` — must end
   `violations: 0 {}` / `unconnected: 0`. Exercises every generator and
   pipeline script (prerequisites listed in `03_src/contracts.md`).
3. **Placement/pad audit**: printed inside step 2 (`AUDIT: PASS`).
4. **Parts parity**: `python3 03_src/bom_seed.py` after a fab export — fails
   on any BOM line without a `02_parts/` entry or with TBD sourcing.
5. **Checklist**: walk `01_docs/CHECKLIST.md` — every line is a runnable
   command or file inspection by construction.
6. **Releases**: for each `07_releases/<dir>`, verify per
   `07_releases/contracts.md` (sha256 table, git_sha exists, gates evidence).

Each folder's own `contracts.md` carries the folder-local Validate/Repair;
this sequence is the project-level composition of them.

## Iteration vs release — the distinction that matters

- **Revision**: any design state. Recorded as a git tag + one
  `01_docs/CHANGELOG.md` entry. Costs nothing, happens constantly.
- **Release**: a design state that was actually sent to a fab. Gets an
  immutable `07_releases/<ver>-<date>/`. Rare, permanent, checksummed.

Most revisions never become releases. A board can go v4.4 → v4.10 in a day
and ship exactly one of them.

## Validate

- no `*_old|*_v[0-9]|*_backup|*_experiment` paths anywhere in the repo
- `06_build/` is gitignored; `01_docs/decisions/` and `02_parts/` are NOT
- every folder present has a `contracts.md`
- `README.md` names the current release and it exists in `07_releases/`

## Repair

- Loose root docs → move to `01_docs/`, fix links.
- Versioned filenames → keep the newest as the canonical name, delete the
  rest (git history holds them), note it in `01_docs/CHANGELOG.md`.
- Missing `contracts.md` → copy from the template and adapt.
