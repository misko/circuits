# RESUME STATE

> **Historical snapshot — do not resume from this file.** It is retained only
> as dated evidence. Use Git status/log plus each project's `01_docs/STATUS.md`
> and journal for current work.

_Snapshot: **2026-07-30 ~15:30**. Supersedes the 2026-07-21 snapshot entirely._
_Superseded by commits as they land — `git log` is the primary source; this is only the frame._

---

## 0. READ THIS FIRST — FOUR AGENTS WERE LIVE WHEN THIS WAS WRITTEN

If you are a fresh session, **the biggest risk is clobbering in-flight work.**
Run `git log --oneline -30` and `git status --short` before editing anything —
agents commit as they go, so some of the below may already have landed.

| agent | owns these files EXCLUSIVELY | doing |
|---|---|---|
| **verdict-split** | `skills/kicad-pcb/references/design-policies.md`, `skills/pcb-design/templates/contracts/08_reviews/`, parts of `policy_audit.py` | splitting `verdict:` into two claims (§3A) |
| **rx2-v2 floorplan** | `projects/pluto-rx2-8way-v2/` | floorplan → placement → routing → DRC 0/0/0 |
| **build-staleness** | `skills/pcb-design/templates/03_src/rebuild_all.sh`, `skills/kicad-pcb/scripts/build_provenance.py` (new), `tests/t1_rebuild_templates.py` | freshness assertion (§3B) |
| **suite-repair** | `tests/t1_escape_tier.py`, `t1_layout_precedent.py`, `t1_adr_bounds.py`, `t1_schema_reader.py`, `tests/run_tests.sh`, `adr_bound_provenance.py`, `templates/contracts/02_parts/contracts.md`, parts of `policy_audit.py` | the 7 suite failures (§3C) |

**`policy_audit.py` is SHARED** between verdict-split and suite-repair — a
deliberate, flagged risk. Check it for double-edits.

**Partition agents by EXACT FILE, never by topic.** That is why the table above
is file-level; it was learned by paying for it.

---

## 1. WHAT THIS SESSION IS

A long autonomous run across the board fleet. Two interleaved threads:

1. **Finish boards** — seal `smc0985-cooksense`; commission and build
   `pluto-rx2-8way-v2`; keep `pluto-cal-switch` and `pluto-rx2-8way` moving.
2. **Harden the gates** — the session's recurring discovery is a defect CLASS,
   and most durable value produced is in `skills/`, not in any one board.

### THE INTELLECTUAL THREAD — the recurring defect class

**A gate that is green, internally honest, and structurally incapable of seeing
its subject.** Instances measured this session:

- `R-LEN` regexed on the literal word "length"
- the keypad-isolation DRU's `B.NetName != ''` exempted all unnetted copper
- `P-FACT` reported OK over a **zero denominator**
- `P-SILK-REF` read its own generator's output file
- `A-RENDER` rested on **2 of 203** parts
- 39 `keep_short` budgets named datasheet **pin functions**, not nets
- `tier_preflight` never scanned `route.waves[]`
- **the purest instance, found today:** `tsci build` writes `dist/`, the
  converter reads `build/`. A stale `circuit.json` passed **EVERY** gate on
  `pluto-rx2-8way-v2` — TSX-PRE, S-NETMERGE, E-INV, E-ADR, E-TOPO, E-MARGIN,
  S-COUNT, E-NETREF, M-BOM. **Nothing was wrong with any checker.** They graded
  exactly what they were handed. Caught only by a by-hand netlist read.

**Generalisation worth carrying:** ask of every gate *"what artifact does this
actually read, and could it be the wrong one?"* — separately from *"is the
logic right?"*

---

## 2. BOARD STATUS

| board | stage | gates | blocker / next |
|---|---|---|---|
| **smc0985-cooksense** | `blocked`, v1.7 candidate | DRC **0/0/0 exit 0**; policy_audit **exit 0** PASS=28 WAIVED=6 HUMAN=6 N-A=5; ERC 0 err; E-INV 167/167; E-ADR 11/11; contracts 0; **A-STOCK exit 1** | **EIGHTH decline.** Blocked ONLY by the verdict-field ambiguity — §3A |
| **pluto-rx2-8way-v2** | `placement` | schematic green: S-COUNT 28/28, E-INV 20/20, E-NETREF 78/78 0 ghost, E-TOPO 1/1, ERC 0 err / 248 warn | `floorplan.yaml` UNAUTHORED — the 45° lever (§4) is free right now |
| **pluto-rx2-8way** (v1) | routing, ready | R-DRC **42/17/0** | **NOT superseded** — stands as the bare-chip comparison. 11 U_MCU + 5 USB + 1 corridor. Review battery never run. DO NOT SEAL |
| **pluto-cal-switch** | routing, not promoted | **8/8/0** (from 83/8/0) | chain NOT promoted, `route.final:` still commented out. Residue is STRUCTURAL (all 4 race candidates identical) — do not re-race |
| **crow-mic-pod-v2** | `done` | v1.3 live, orderable | CAL-1 closed at the sibling. 4 open P1s (POE-1, PSR-1, DC-1, MECH-1) |
| **crow-recorder-central-v2** | `done` | v1.7 live, orderable | owes ONE bench measurement (TP11 gate-RC stretch) |

### cooksense — the exact state

**Design-clean and not orderable.** Two different facts; the review schema has
one field for both.

- `C265111` (JST SM08B-GHS-TB): stock **5**, `minPurchaseNum` **21**.
  **MOQ EXCEEDS STOCK → unbuyable at any quantity.** The threshold that
  unblocks "just wait" is **21, not the gate's 10.**
- **DECISION MADE (B30-01):** seal with the GENUINE part specified; document the
  substitution as an ORDER-TIME path. Sealing is not ordering, and picking the
  clone now would bake an unverified mechanical risk into an immutable release
  for zero gain today.
- **CORRECTION — do not repeat my error:** I claimed the substitution changes
  "zero bytes of the fab set." **FALSE — 6 cells across 4 files.** The **COPPER**
  is invariant; BOM and CPL are not. The CPL's `Val` carries the LCSC code
  because `fp.GetValue()` on these footprints *is* `C265111`. An earlier draft
  told a buyer to edit `fab/bom.csv` — **a file JLC never receives** (assembly
  takes `bom_jlc.csv`/`cpl_jlc.csv`) — which would have **ordered the unbuyable
  part**. Fixed; remedy now routes through `cooksense.tsx` + regenerate (M3).
- **The "0.01 mm measured drop-in" was NOT evidence.** Its whole triple is
  verbatim the *genuine* part's own rows; no `jlc_twin` artifact for the clone
  exists anywhere, and `fit=` prints `0.01` for the genuine part too — it cannot
  discriminate. Re-derived by a method that is NOT `jlc_twin` (raw EasyEDA
  `PAD~` + pcbnew): genuine 0.0002 mm, clone 0.0100 signal / **0.0399 tabs**.
- **AND THE TABS DISAGREE:** the board's tab pads are **1.000 × 2.700**, matching
  the **CLONE**; the genuine part's are **1.210 × 2.700** — on the exact axis
  declared unverified. **Unresolved. Flag it.**
- Rebuild moved the netlist md5 and **not the netlist**, proven: 198 nets / 239
  components / 806 nodes both sides, 0 differing node sets, normalised md5
  identical `900941ca…`; board `9f4fd5fa…` unchanged.
- `07_releases/` UNTOUCHED (still v1.0–v1.6). The staged
  `cooksense-v1.7-2026-07-30/` was **REMOVED**, not left implying a seal.

---

## 3. WORK IN FLIGHT

### 3A. THE VERDICT SPLIT — highest value, unblocks cooksense

**Proven by eight failed seal attempts.** The last topology lens wrote that it
**"would accept the seal"** — it judged the M4 waiver sound — but that
**"sealing is not the question this verdict field asks."** The gate reads
`verdict:`, `verdict:` means ORDERABLE, so a reviewer who agrees the board
should seal is **structurally unable to say so.**

**A stock gate measures the WORLD, not the BOARD.** It is red on a fact that
changes hourly and that no source edit can address. Two claims need two fields:

- *"this design is correct"* — **true**, and it is what every gate measures
- *"this design is orderable today"* — **false**, on one line, externally

Spec: `projects/smc0985-cooksense/verification/owed_skill_patches.md`, entries
**P1** and **P10** (10 entries total). Constraints: seal must stay blockable;
non-orderable status must be LOUD, DATED, and reach the BUYER (`ORDER_README`
§5-0); both claims independently gradeable.

### 3B. BUILD-STALENESS — §1's purest instance

Path fix (`build/` → `dist/`) is **necessary and not sufficient.** The real
deliverable: the pipeline must **assert the artifact it grades is the one it
just built**, and must also catch the sibling shape found on the same board —
`rebuild_all.sh` still carrying template knobs (`BOARD=power3s`), i.e. **the
full driver had never run** while stage gates reported green. A blast-radius
count across all project copies was requested.

### 3C. SUITE REPAIR — 7 failures, all attributed. **Ordering matters; #1 masks the rest.**

1. **`t1_layout_precedent.py` ended in a bare `main()`** where siblings use
   `sys.exit(main())`; `harness.main()` returns 1 and the value was discarded.
   AND `run_tests.sh` takes `rc` from exit status but the failure count from a
   **stdout grep** — so fixing the other six would print `1 failed` followed by
   `ALL SUITES PASSED`, **exit 0**: the exact `jlc_twin` shape. It is a
   **REINTRODUCTION** — `0dd56ab0` (07-27) swept the idiom out of nine suites;
   this file was created `bcec2fd6` (07-30) with the bug back. **Nothing guarded
   the idiom** → the deliverable is the GUARD test, not the one-liner.
   *(Believed landed as `2c039a02`.)*
2. **`PREC_OWED_CEILING`: RE-SCOPE, DO NOT RE-BASELINE.** owed **91** vs ceiling
   **89**. It is an ABSOLUTE fleet-wide count, so **commissioning any board with
   ≥1 un-graded in-scope part breaches it on day one**, and no work on existing
   boards can prevent it. As a FRACTION the same event *improves*: 89/89 = 1.000
   → 91/92 = 0.989. `adr_bound_provenance.OWED_CEILING = 37` has the identical
   shape. **It was invisible because the `graded` assertion fails first and
   short-circuits the file — a ceiling that never executes is not a control.**
   Expect this as an 8th failure once #1 and #6 land.
3. **G-ORPHAN ×2** — the only genuine NEW defect. `mechanical:` declared in
   `pluto-rx2-8way-v2/02_parts/RP2040-Zero/part.yaml`, governed by no contract
   row. Floors are MET (251/251, 307/307) — not a ratchet failure. Fix the
   **TEMPLATE** `contracts/02_parts/contracts.md`, never the project file.
4. `CITED_FLOOR` 0 → 1 in `adr_bound_provenance.py:279` — legitimate advance.
5. `t_cited_below_the_floor_fails` hardcodes `--cited-floor 1` → **currently a
   gate that cannot fail.** Fix like its sibling: measure, pass `cited + 1`.
6. `PREC_GRADED_FLOOR` 0 → 1. *(Believed landed as `7b6d0aa1`.)*
7. **P-LAND ×2 — gate right, board right, FIXTURE stale.** The board genuinely
   FIXED 6 of 11 by gaining same-net vias that P-LAND exempts by design.
   **Preserve this contrast:** identical 0.400 mm geometry, but cal-switch's
   clearance floor is 0.150 so `0.400 − 0.125 − 0.100 = 0.175 ≥ 0.150` and
   via-in-pad is **LEGAL**; rx2's floor is 0.200 so `0.175 < 0.200` and **no
   legal via exists.** Same arithmetic, opposite verdict, because the floor
   differs. Recommended fix: pin the 11-pad test to an ARCHIVED pre-stitch board
   (it is a historical incident reproduction); keep the live-board test live.
   See `tests/README.md` "Which real bytes may a fixture read?".

---

## 4. pluto-rx2-8way-v2 — THE NEW BOARD

**Why it exists:** 19 nets leave v1's bare RP2040 QFN-56 and **only 5 are the
board's function** (`SEL_V1..V4` + `LED_STAT`). The other 14 are the chip keeping
itself alive. **28 components vs v1's 64.**

**Module: Waveshare RP2040-Zero**, 18.00 × 23.50 mm, 23 castellated pads @
2.54 mm. Chosen over the Pico because **the Pico's RT6150 defaults to PFM** — a
*variable, load-dependent* switching frequency, the worst spur shape near a
receiver — and forced PWM only locates it to ±20% (f_OSC 0.8/1.0/1.2 MHz). The
RP2040-Zero uses an **RT9013-33 LDO**; a full-text search of its schematic for
`uH`/`nH`/`inductor` returns **zero**.
*Honest caveat recorded by the agent itself:* an RT6150 would have ranked ~4th
behind QSPI anyway. The LDO was chosen **not because the risk was large but
because deleting it costs nothing.**

### THE 45° LEVER — free right now, spend it before routing

**MEASURED on v1: 6 of 9 radials sat off a 45° multiple, each paying 1.0731×.**
KRT routes OCTILINEARLY (`max(dx,dy) + 0.4142·min(dx,dy)`). **Star angles on
multiples of 45° drive the octilinear excess to ZERO by construction.**
`floorplan.yaml` is unauthored, so this is still free — a routing problem solved
as a placement decision. v1 found it by routing for hours.

**Correction to an earlier framing:** the octilinear floor is **NOT** pad
arithmetic. It is a property of the STAR GEOMETRY, unmeasurable until a floorplan
exists. Same for P-LAND (`escape_check.py --board` needs a `.kicad_pcb`).
**Do not estimate either; do not inherit v1's 1.4966 mm.**

### Module facts that constrain the floorplan (all STEP-MEASURED)

- **IT CANNOT SIT FLAT.** 23 components on the **carrier-facing** face — crystal
  **1.000 mm proud**, RP2040 0.850, RT9013 0.700. Joint plane and collision plane
  are the same plane. → `assembly.yaml` is **`not_assembled`/hand-solder, reason
  MECHANICAL** (was wrongly `consigned`; the tree had claimed components were on
  the **top** face, which is *unfalsifiable from a photo of the top*).
- **PAD NUMBERING IS CLOCKWISE FROM TOP-RIGHT** — the mirror of every IC. The
  schematic gate had closed on an INVENTED numbering justified by "Waveshare does
  not number them," which is **false** (schematic P1 "Header 23"; wiki
  "Pin23"/"Pin 21"). Ours was the **EXACT REVERSE: `ours_n = 24 − vendor_n` on
  all 23 pads** — the worst possible collision, since every number is valid in
  both systems and names a different pad. Verified: `pad1→SEL_V1, pad4→SEL_V4,
  pad5→LED_STAT, pad21→3V3_MOD, pad22→GND`.
- **Silk prints GPIO numbers, not pad numbers**, agreeing for **sixteen
  consecutive pads** before diverging at pad 17.
- **No vendor land pattern exists** — the footprint is AUTHORED. Do NOT import
  SnapEDA's; it would launder an estimate into an apparent citation.
- **Two keepouts drawn into the footprint, graded by NOTHING:** HEIGHT
  X 4.0..14.0 × Y 2.5..22.5 (becomes a CUTOUT if reflow is ever wanted); COPPER
  X 2.4..3.6 × Y 4.8..17.0 (ten live underside pads).
- **USB-C edge at/beyond the carrier board edge**; **BOOT+RESET must stay
  accessible** (BOOT/RESET/SWD reach NO castellation — those two buttons are the
  only route into the bootloader, forever, and there is no in-circuit debug
  ever); **GND is ONE castellation** (pad 22) for all 20 GPIO returns.
- **The WS2812 is ungateable**, sits **1.091 mm directly over the RP2040**,
  **runs with the LED commanded black**, and is a **1615-class variant whose MPN
  is OWED**. The only true off switch is VSYS — which composes with the
  self-timed dwell scheme (8192/4096/128).

**Full dossier** (STEP-derived, artifacts sha256'd):
`<scratchpad>/rp2040-zero/DOSSIER-part.yaml` plus vendor artifacts alongside.

### Hold invariant from v1

`In1.Cu` is the **SOLID UNBROKEN RF REFERENCE, EXCLUDED from routing layers**
(this is what makes nine phases comparable). RF on F.Cu only, **no vias inside an
arm**. Fence at λg/20 = **1.37 mm** (settled — §5). Length tolerance is **DRIFT,
not static mismatch**: PE42482A-X's published **13.2°** part-to-part window is
**1.00 mm of copper**, and anything tighter is not physics (v1 carried a
±0.10 mm / 1.3° obligation, withdrawn as unreachable by any router).

---

## 5. THE RF CONSTANTS FINDING (landed `2b8828d4`)

**`eps_eff = 3.350` DID have a provenance, and finding it was the answer.** It
sits in `copper_length_audit.py`'s docstring as
`(er+1)/2 + (er-1)/2 / sqrt(1 + 10h/w)`. **That formula does not exist.** The
constant **10** is Hammerstad-Jensen's; the exponent **−1/2** is
Schneider/Wheeler's. One term from each parent, neither parent's formula. The two
parents agree **with each other to 0.02%** — so 3.350 is not a value between two
disagreeing models, it is **1.5% above two models that agree.** Not a
measurement → outranks nothing under M6. Withdrawn.

**The fleet carried FIVE sets, not three.** The fifth (`pluto-cal-switch`) is the
only one not from a closed form: a 2D field solve on the **as-fabbed**
cross-section, eps_eff **3.383**, whose per-term table prices the **solder mask at
−1.55 Ω** = **+6.3% on eps_eff**. Every closed form is a **bare-trace model, and
no board here fabricates a bare trace.**

> **3.350 was wrong for a bad reason and wrong in the right direction; the
> derivable numbers are right about a cross-section nobody builds.**

v1's fence was **right by luck twice from two unrelated errors** (27.41 =
`50/1.8242`, a wavelength rounded from 49.9654, landing on the correct 27.411 by
coincidence) — *a collision, not a corroboration.*

**Root cause was the TAGGING:** only `[SOURCED]`/`[MEASURED]` existed, so a
COMPUTED number had nowhere to live and 3.350 sat under a heading reading "What
this fleet MEASURED." **`[DERIVED]` added as a third voice.** New **§4A** (not
renumbered — five live board docs cite `4(d)`, `3(b)`, `3(d)`, and renumbering
cited canon is the drift at issue). **Rule: one stackup, one constant set,
identified by `(stackup, w, cross-section, method)` — never by the stackup alone.**

Calibration: the Dk window 4.2–4.6 moves eps_eff 3.187–3.458, **swamping every
disagreement above.** Nothing shipped is unsafe; **the stake is regenerability.**

---

## 6. NEXT STEPS, RANKED

1. **Reconcile the four agents' landings.** `git log`, `git status`, check
   `policy_audit.py` for double-edits. Run `tests/run_tests.sh` and
   `scripts/contracts_audit.py` **UNPIPED**.
2. **Expect an 8th suite failure** (`PREC_OWED_CEILING`, §3C #2) once #1/#6 land.
   **Re-scope it, do not re-baseline it.**
3. **Land the canon rows I deferred for collision reasons.** Two agents were told
   to propose check-IDs in prose rather than edit `design-policies.md`: the
   build-freshness check (§3B) and anything from suite-repair. **A check-ID
   emitted without a canon row in the SAME change is caught by
   `t_skill_contract_sync` in one run.**
4. **Finish cooksense** once the verdict split lands: one rebuild, topology lens
   re-gated on its own resolved finding, MANIFEST, 2-commit seal, and **refresh
   the beacon as part of the seal** (07_releases contract step 4).
5. **rx2-v2 floorplan** with 45° star angles → measure the octilinear floor +
   P-LAND from the real `.kicad_pcb` → route to 0/0/0.
6. **Fleet defect, 5 of 33 sealed archives:** `fp-lib-table` points outside the
   archive, so a standalone DRC returns 14 `lib_footprint_issues`. **Five sealed
   releases cannot be rebuilt from their own bytes.** Needs a gate
   (`owed_skill_patches.md` P9).
7. **Owed skills patches** — `owed_skill_patches.md` has 10 entries; also still
   open from earlier: `refs:` scoping in policy_audit, `P-SILK-REF`
   self-certification, `A-RENDER` MIN_BODY_MM, `pin_audit` blanking 16/54,
   `_resistive_path` GND-transit, `pad_span.py`, `PF-RULES-CLR` returning before
   `PF-ROUTE-CLR`, `jlc_twin` emitting no parseable verdict line.
8. **Consolidation pass** — 34 gates, 73+ check-IDs. `M-BOUND` 37 OWED and `M4`
   22/22 OWED both grade zero.

---

## 7. STANDING CONSTRAINTS (verbatim — do not relax)

- **Subagents on Opus 5 only.** Not `fable-medium`.
- **`04_kicad/` and `07_releases/` are IMMUTABLE.** The only sanctioned write is
  `SUPERSEDED.md`. Never hand-edit `04_kicad/` — fix the generator and rerun (M3).
- **Board agents must NOT edit `skills/`** — report proposed patches.
- **Commits pathspec-scoped:** `git commit -m "..." -- <path>`. **Never**
  `git add -A` or `git commit -a`. Pathspec is necessary and **NOT sufficient** —
  do not leave uncommitted edits in a file an agent owns.
- **Do NOT push unless asked.**
- `/usr/bin/python3` for anything importing `pcbnew`. `bun`/`tsci` from `~/.bun/bin`.
- **Run gates UNPIPED.** `| tail` reports tail's exit code — this burned the
  session twice.
- **Every gate change needs a RED-verified known-bad fixture.** Swap the pre-fix
  code back in, confirm RED, restore, and **say so in the test.**
- **A check-ID emitted must have a canon row in the SAME change**, and the
  governing `contracts.md` TEMPLATE must catch up in the same change.
- **CLASSIFY, NEVER COUNT** — violations **AND** unconnected. Both halves. The
  unconnected half is the one that gets summarised instead.
- **Mark every load-bearing claim MEASURED or INHERITED** when reporting.

### Toolchain (outside any project, all present)

`/usr/bin/python3` (pcbnew) · `/usr/bin/kicad-cli` · `~/.bun/bin` (bun, tsci) ·
KRT `~/gits/KiCadRoutingTools` · venv `~/virtual-envs/spf` ·
`~/.claude/skills/{pcb-design,kicad-pcb,jlcpcb-fab}` are **symlinks →
`~/gits/circuits/skills/*`** (one home, no drift).

---

## 8. MY ERRORS THIS SESSION (so they are not re-inherited)

Recorded because several travelled into agent briefs before being caught.

- **"zero bytes of the fab set"** for the cooksense substitution — **false**,
  6 cells / 4 files. Copper is invariant; BOM and CPL are not. (§2)
- **"the octilinear floor is pad arithmetic"** — it is star geometry, not parts,
  and is unmeasurable until a floorplan exists. (§4)
- **"v1 has 11 unconnected"** — it is **28**.
- **"0.200 mm is a fab floor"** — it is v1's **declared netclass clearance**;
  `min_space` is 0.09 at that tier and v1 already relaxes to 0.14. The module's
  case never needed that argument — it has **19-versus-5**.
- **Relayed a "0.01 mm measured" fit that was not evidence at all.** It was
  marked INHERITED, which is the only reason it got checked — **that tagging
  rule is load-bearing; keep it.**
- Earlier: told agents `STATE (measured, do not re-derive)` about three cooksense
  numbers I had **not** measured (PASS=27, E-INV 180/180, E-ADR 10/10 — truth:
  28, 167/167, 11/11).

---

## 9. WHERE THE CANON LIVES

- `skills/kicad-pcb/references/design-policies.md` — the S/P/R/M check-ID canon
- `skills/kicad-pcb/references/rf-design.md` — RF canon (§4A is new today)
- `docs/decisions/` — ADR-0001 (tscircuit authoring boundary), ADR-0002
  (tscircuit-native pipeline)
- `tests/README.md` — the testing contract, incl. **"Which real bytes may a
  fixture read?"** (pinned commit / sealed release / live-with-a-reason) —
  governs §3C #7
- `skills/pcb-design/SKILL.md` — pipeline orchestration, stage by stage
- `contracts.md` (every folder) — machine-checked by
  `/usr/bin/python3 scripts/contracts_audit.py`
- **`git log` is a primary source** — commit bodies are written as post-mortems.
