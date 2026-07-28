> **CORRECTION, 2026-07-26 — the island POPULATION in this file was measured
> on a refill-in-memory, not on the fill that ships.** Every `136` below has
> been changed to **121**, which is what the stored fill in
> `source/cooksense.kicad_pcb` actually contains: GND/F.Cu **106**, GND/B.Cu
> **13**, GND/In1.Cu **1**, 3V3/In2.Cu **1**. `verification/mrepro.md`
> independently reported 106/13/1/1 and was right; this file and the summary
> tables that copied it were wrong. **The CONCLUSION is unchanged and was
> re-run against the shipped fill: 121 islands, 121 bonded, 0 stranded.**
> A conservative population is not automatically a correct one.

# Stranded-island check — cooksense v1.3, 2026-07-26

Board: `04_kicad/cooksense.kicad_pcb`, loaded IN PLACE (the sibling
`cooksense.kicad_pro` carries the netclasses; a copied board fills with DEFAULT
clearances and every number becomes a phantom), zones filled in memory.

**Question DRC cannot answer.** A filled zone island with no same-net copper
landing in it is floating copper, but it is not "unconnected" in the netlist
sense, so `--severity-all` passes over it. The board's 0/0/0 is unaffected either
way — which is exactly why the check is worth running separately.

## Result: 121 islands, 121 bonded, **0 stranded**

The coordinator's independent run reported **7 stranded, 3.0719 mm2**. I
reproduce those figures EXACTLY with the method as described, and they are an
artifact of the containment test rather than a property of the board.

| method | bonded | stranded | area |
|---|---|---|---|
| (a) same-net item POSITION `Contains()` inside the island | 129 | **7** | 3.0719 mm2 |
| (b) same-net copper SHAPE `Collide()` with the island | **121** | **0** | 0.0000 mm2 |

Method (a) asks whether a pad/via/track *centre* falls inside the island. Method
(b) asks whether its *copper* touches the island. These seven islands are the
pour fragments that wrap around a pad's thermal relief, so the bonding pad's
centre is outside the fragment while its copper overlaps the fragment's edge.
Same failure mode as the nearest-point overlap test that once called the
J_ESTOPLOOP/J_DOOR short "+0.250 mm clear" (canon P11): **a position is not a
shape.**

## Every one of the seven, with the copper that bonds it

| layer | area mm2 | bbox | bonded by |
|---|---|---|---|
| F.Cu | 0.8613 | x[121.75,122.76] y[89.00,90.61] | pad `R_CTRREQPD.2` + a via |
| F.Cu | 0.7541 | x[153.45,155.05] y[90.73,91.25] | pad `D_LCCLK.2` + a via |
| F.Cu | 0.5319 | x[24.85,25.43] y[90.40,91.55] | pad `C_COMP2.2` + a via |
| F.Cu | 0.2494 | x[152.75,153.25] y[97.40,97.97] | pad `J_LOADCELL.3` |
| B.Cu | 0.2483 | x[99.21,99.94] y[96.77,97.41] | pad `J_PI.6` |
| In1.Cu | 0.2483 | x[99.21,99.94] y[96.77,97.41] | pad `J_PI.6` |
| F.Cu | 0.1786 | x[142.39,142.98] y[94.28,94.87] | pad `J_PI.39` |

## The identical-area pair, resolved

The coordinator flagged the B.Cu and In1.Cu fragments as suspicious for being
byte-identical in area (0.2483 mm2 each) and asked whether they sit near a
mounting hole or the isolation moat, because copper fragments in the barrier
region are a different conversation.

**They are neither.** Both are the pour fragment around **`J_PI` pad 6 (GND, a
1.00 mm-drill THT pad at (99.08, 97.54))** — the Pi header's GND pin. A THT pad
exists on every copper layer, so the fragment it produces projects identically
onto B.Cu and In1.Cu. That is precisely the "one geometric feature projecting
onto two layers" hypothesis, and the feature is a plated through-hole pad. The
location is the middle of the J_PI header field: **~92 mm from H4 (193,52), and
nowhere near the ISO moat** (`iso_moat_block` x[192.20,200.10] y[86.65,102.10]).
The fragments are bonded to the very GND pin they surround.

## Third, independent agreement: KiCad's own island removal

| zones | net | island_removal_mode | min_island_area |
|---|---|---|---|
| 1 | 3V3 | **0 = ALWAYS remove unconnected islands** | 1.0e13 |
| 3 | GND | **0 = ALWAYS remove unconnected islands** | 1.0e13 |

Island removal is not merely on, it is set to ALWAYS, and all seven fragments
survived a filler explicitly instructed to delete unconnected islands. That is
KiCad's own verdict that they are connected, reached by a third method that
shares nothing with either test above (canon M1).

To the coordinator's question — *"if island removal is already on and these
survived, that is a more interesting finding than if it is simply off"* — it is
on, they survived, and the interesting part is that the filler was right.

## Disposition

**No action, and no v1.4 island-removal change either.** The proposed v1.4 fix
(tune the zone island-removal property) would be a fix for a defect that is not
present: these are not orphaned slivers, they are bonded pour fragments around
THT and SMD pads, and the setting that would remove them is already at its most
aggressive value and correctly leaves them alone. Changing `min_island_area`
would delete *connected* copper.

Recorded so that "we checked and found 0 stranded islands, having first
reproduced a 7-island result and identified the method that produced it" is on
file. For comparison the coordinator measured usb-hub-3s-v3 v1.6 at 105/105/0.

**Discrimination, so this is not an unfalsifiable pass:** the coordinator proved
their checker can fail by stripping all 178 usb-hub GND vias, which produced one
stranded island of 11407 mm2. The overlap variant used here inherits that
property — it differs only in testing shapes rather than positions, and it is
strictly harder to satisfy in the direction that matters (an island with NO
same-net copper anywhere near it fails both tests identically).

---

# Appendix — the sibling-context trap, now confirmed TWICE

Recorded here because it bit two different gates in one session and it will bite
any agent that measures a KiCad artifact by copying it somewhere convenient.

**A KiCad CLI or pcbnew check silently grades against a DEGRADED context when
the file's project siblings are absent.** The file bytes are identical; the
answer is not.

| measurement | run beside its siblings | run on a bare copy | what the sibling was |
|---|---|---|---|
| GND/3V3 zone fill area | 8434.792 mm2 | 8380.892 mm2 (~54 mm2 low) | `cooksense.kicad_pro` — netclass clearances |
| ERC warning count | **1311** (0 errors) | 1533 (0 errors) | `fp-lib-table` — 222 spurious `footprint_link_issues` |

The ERC case is the sharper one because the extra 222 are a *plausible-looking*
class: "footprint link issues" reads like a real finding, and the run that
produced them was on byte-identical source. The only way to tell was to diff the
violation TYPES between the two runs:

```
1311 run: endpoint_off_grid 921, lib_symbol_issues 389, isolated_pin_label 1
1533 run: endpoint_off_grid 921, lib_symbol_issues 389, isolated_pin_label 1,
          footprint_link_issues 222
```

It also produced a real MANIFEST/EVIDENCE MISMATCH that the release-freshness
gate caught: MANIFEST said 1533, `policy_audit.md` said 1311, and `erc.json` said
1533 — three numbers for one fact, because two of them came from a bare-directory
run. The shipped `verification/erc.json` is now the in-place run (1311) and the
MANIFEST agrees with it.

**Rule:** measure artifacts IN PLACE. If you must copy, copy the whole sibling
set (`.kicad_pro`, `.kicad_prl`, `fp-lib-table`, `.kicad_dru`) under matching
basenames, and state which context you measured in.

### Numbers in this appendix are the 2026-07-26 measurement, not the shipped counts

The 1311 / 1533 pair above was measured on the schematic as it stood when the
trap was found. The schematic changed afterwards (P1-1 moved `R_TEMPOK` to
3V3_ANALOG), so **this archive's ERC is 1303 warnings / 0 errors**. The trap is
the point, not the specific integers: same bytes, different sibling context,
different answer.

**The same defect was found a second time, in this archive, and is now fixed.**
`source/fp-lib-table` pointed the project `cooksense` library at
`${KIPRJMOD}/../03_src/lib/cooksense.pretty` — a path OUTSIDE the archive —
while the footprints ship at `source/cooksense.pretty/`. 14 placements use that
library (12 Standex reeds, J_TC, J_ISOLOOP), so a recipient extracting only this
archive could not reproduce the stated ERC or DRC numbers. Repointed to
`${KIPRJMOD}/cooksense.pretty` and PROVEN standalone: `source/` extracted to a
bare temp directory with nothing of the project around it re-runs at

    DRC 0 violations / 0 unconnected / 0 schematic parity
    ERC 0 errors / 1303 warnings
    ERC classes: endpoint_off_grid 913, lib_symbol_issues 389, isolated_pin_label 1
                 (zero footprint_link_issues)
