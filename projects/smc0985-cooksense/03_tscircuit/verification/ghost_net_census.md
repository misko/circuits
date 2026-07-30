# Ghost net-name census — cooksense, v1.8 (2026-07-29)

Every net name referenced by a rule file or a `02_parts` dossier, checked against
the net names that actually exist in `06_build/netlists/cooksense.net`. Produced
by reading the netlist, not by reading the design.

**This is the class behind two shipped defects.** The silk printed `GND_ISO ONLY`
for a net that does not exist (fixed 9ca93b1), and the eFuse's `keep_short`
budget was addressed to `5V_SELV`, also not a net — which is why nobody noticed
that **`5V_IN`/`5V_FUSED`/`5V_RPP` carried zero capacitors for five releases.**
An unenforceable budget is not a weak check; it is a check that cannot fail.

## The denominator

| quantity | v1.7 | v1.8 |
|---|---|---|
| real nets in the netlist (excl. `unconnected-*`) | 173 | **171** |
| net-name references from rule files + dossiers | 236 | **236** |
| DISTINCT names referenced | 132 | **124** |
| **ghost names (referenced, do not exist)** | **26 distinct / 25 rows** | **14 distinct / 22 rows** |

Two notes on reconciling this with the v1.7 battery's "10 of 123 (8%)":

- The v1.7 figure did **not** count `chain:` entries. Neither does this one: a
  `series_chain` alternates net and REFDES (`[5V_IN, F1, 5V_FUSED, Q_REV, …]`),
  so `F1`/`Q_REV`/`R_KEY`/`R_OVT`/`R_OVB`/`R_STOPRAIL`/`Q_COIL`/`K_PRESS` are
  **not** ghosts — they are part references, and an earlier pass of this census
  wrongly reported all eight. Recorded because a census that over-reports is as
  useless as one that under-reports.
- Of the 14 remaining, **5 belong to parts that are not on this board at all**
  (see class C). Excluding those and the one `pins.*.tie` row gives **11**, which
  is the same population the battery counted; the residual difference is whether
  a name appearing on N dossiers counts once or N times.

## The 14, with a disposition each

### Class A — RAIL-PIN budgets: NOT renamed, and that is the reasoned answer (9 names, 13 rows)

`VCC` ×7, `VDD` ×2, `VREF`, `N3V3`, `3V3_DIGITAL`, `+5V`

These are per-INSTANCE local budgets — "0.1 µF bypass hard against **this**
package's VCC pin" — written as a PIN name. The node the datasheet sentence is
about is *this package's VCC pin*, and **the schema cannot name it**: a
`keep_short` row names a net, a dossier is per part TYPE, and the net these
resolve to is the whole-board rail (`3V3`, 76 pads, ~150 mm span). Renaming them
to `3V3` would not be "naming the node the sentence is about" — it would convert
13 honest *never evaluated* rows into 13 instant violations of a budget nobody
ever intended to apply to a 150 mm rail.

The electrical intent is verified **by a different instrument** (canon M1):
`audit_board.py`'s I-PROX gate measures every IC decoupler 2–5 mm from its own
package pin, pad-to-pad, and passes. That is the fact these rows were written to
assert and the one a whole-rail span metric structurally cannot see.

**OWED SKILL PATCH** (reported, not applied — a sibling is live in `skills/`):
P-ADJ needs a per-instance budget form, e.g.
`{pin: 14, to_part: C_SCHM, within_mm: 5}`. Already recorded in
`policy_waivers.yaml` under `P-ADJ-UNREACHED`; repeated here because it is the
same one field that blocks 13 of 14 rows in this census.

### Class B — a unique real node existed: RENAMED in v1.8 (4 names, 4 rows — now closed)

| was | now | dossier | graded result |
|---|---|---|---|
| `5V_SELV` | `5V_RPP` | TPS259573DSGR | VIOLATION (15.581 mm vs 3), waived with the local measurement |
| `EN_OVLO_N` | `EF_OVLO` | TPS259573DSGR | VIOLATION (8.473 mm vs 5), same |
| `ILM` | `EF_ILM` | TPS259573DSGR | VIOLATION (6.982 mm vs 5), same |
| `dVdt` | `EF_DVDT` | TPS259573DSGR | **PASS** (4.524 mm vs 5) |

Renamed because the part has exactly ONE instance and each pin exactly ONE net,
so the real name is unambiguous. **Renamed to the node, not to a passing score**:
three of the four now VIOLATE, which is strictly better evidence than four rows
that could never be evaluated. `5V_SELV` is the row that hid a missing part.

### Class B, still open — same shape, NOT done in this revision (4 names, 4 rows)

`T_PLUS` → `TC_POS` (13.640 mm vs 5), `T_MINUS` → `TC_NEG` (8.967 mm vs 5),
`BIAS` → `TC_NEG`, `OPTO_LED` → `OPTO_LED_A` (5.722 mm vs 6, would PASS).

Deliberately left: renaming them without re-placing `U_TC`/`U_OPTO` trades 3
unreached rows for 3 violations on a placement **this revision did not author**,
and the two nets already grade PASS against `PCC-SMP-K`'s own 20 mm budget, so
the local relationship is not unmeasured. They are named here so the next
placement pass inherits a list and not a search.

### Class B, INEXPRESSIBLE — multi-instance (1 name, 2 rows)

`HS_GATE` on `2N7002` and `AO3401A`. Both part types appear at FIVE instances
carrying five different nets (`HS_GATE_COIL`, `SWG_A`, `SWG_B`, `SWG_RHA`,
`SWG_RHE`). A per-part-type dossier cannot name a per-instance net; no rename is
truthful. Measured spans, so the reader can see what a rename would have scored:
`HS_GATE_COIL` 10.169, `SWG_A` 4.128, `SWG_B` 6.445, `SWG_RHA` 6.445,
`SWG_RHE` 7.429 (budget 6). Blocked on the same OWED patch as class A.

### Class C — the part is not on this board (3 names, 3 rows)

`LED_DRIVE` (AQY212GS), `RCEXT` (SN74LVC1G123DCTR), and 3 of the 7 `VCC` rows
(SN74HC138DR, SN74HC139DR, SN74LVC1G123DCTR — all superseded parts).
Unresolvable by construction; the dossiers are kept because they are the
provenance for *why* those parts were rejected.

### One outlier — a PIN-name tie, not a keep_short (1 name, 1 row)

`AMS1117-3.3` `pins.4.tie: VOUT`. Pin 4 is the SOT-223 tab and the tie names the
datasheet's own pin name. It is a ghost only if `tie:` is read as a net; nothing
reads it that way today. Left as-is and recorded so a future gate that DOES read
`tie:` as a net starts from a known list.

## Net-count delta this revision

`DOOR_RAW_IN`, `ESTOP_RAW_IN` added (ADR-0024's split); `DOOR_RAW`/`ESTOP_RAW`
survive as logic-side nets. 173 → 171 in the census figure is the
`unconnected-*` filter plus `J_DOOR.4` leaving `DOOR_RAW` for `GND`.

## Reproduce

The census is 30 lines of Python over `06_build/netlists/cooksense.net` +
`02_parts/*/part.yaml` + `03_src/cooksense/rules/*.yaml`; it walks `net:`,
`nets:`, `rail:`, `from:`, `to:`, `parent:`, `child:`, `on_net:` and
`pins.*.tie`, and deliberately does NOT walk `chain:` (see the denominator note).
**This should be a GATE, not an artifact** — a sibling agent is building the
general one. This file exists so the two counts can be reconciled on the same
board rather than argued about.


## RECONCILED against the fleet gate (E-NETREF, `701f099`) — 2026-07-29

The sibling's `net_reference_audit.py` landed while this was being written, so the
two counts are reconciled here on the same board instead of being argued about.
Run after this revision's fixes:

    E-NETREF: FAIL — 281/302 references resolved, 21 ghost (5 with a named
              near-miss), 0 unreached          [exit 1]

**They agree, and the difference is informative.**

- **All 21 of E-NETREF's ghosts are `K7` = `02_parts/*/part.yaml
  layout.keep_short[].net`** — the same population as classes A/B-open/B-multi/C
  above, and the same 13 distinct names once `VOUT` is set aside.
- **The four eFuse rows this revision re-pointed are GONE from its output.**
  `5V_SELV`, `EN_OVLO_N`, `ILM` and `dVdt` do not appear. That is the Blocker-2
  fix confirmed by an INDEPENDENT instrument written by another author (canon M1:
  the checker and the checked must not share a method). Before the fix its count
  would have been 25.
- Its denominator is larger (302 vs 236) because it scans twelve kinds — netclass
  members, floorplan zones/pad_net asserts/captions, `power_tree` rail names — where
  this census walked eight keys.

### THE ONE ROW E-NETREF DOES NOT SEE, and it is the field the `GND_ISO` ghost lived in

This census counts **22 rows** to E-NETREF's 21. The extra is
`02_parts/AMS1117-3.3/part.yaml` `pins.4.tie: VOUT`, and **`pins.<n>.tie` is not
among E-NETREF's K1–K12.**

It is not a harmless field. Six dossiers use it and **five name the real net
`GND`** — and those ties drive real copper: the eFuse `pins.9.tie: GND` is an
entire rebuild stage (`5a/8 tie U_EFUSE EP unnamed sub-pads -> GND`), and the
connector `MP: {tie: GND}` tabs are exactly what `parity_padmap.txt` adjudicates —
**the file where the `GND_ISO` ghost that reached the shipped F.Silkscreen was
found.** So this is the field class that already cost this project once.

The sixth (`VOUT`) is a PIN name, not a net, which is why the kind needs the
net-name-vs-pin-name discrimination rather than a blanket rule — and is why it is
worth a kind of its own.

**REPORTED UPSTREAM, not patched here** (a sibling is live in `skills/`):
add a kind for `02_parts/*/part.yaml pins.<n>.tie`, tolerant of pin names in the
way K6 is advisory about rail names.
