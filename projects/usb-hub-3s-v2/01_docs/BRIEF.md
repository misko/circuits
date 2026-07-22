# brief: usb-hub-3s-v2

status: active
prompt_sha256: dee57360bd9c099fb7801fb6fd0b388b168080cf62d56d63956ecb2d182e3be0
current_release: no

## Original prompt

<!-- prompt-verbatim-begin -->
> Run the /pcb-design pipeline for usb-hub-3s-v2 in /home/mouse9911/gits/circuits (branch main) — a NEW, correctly-scoped redesign of the usb-hub-3s charger. Drive it to the SCHEMATIC GATE, then a PLANNED HANDOFF (the routing half is a separate step). This is a production run: use the ledger, archetypes, and the reusable v1 work fully.
>
> WHY v2 EXISTS (the finding, user-confirmed 2026-07-22): usb-hub-3s v1.x built a 100W IP6559 BUCK-BOOST for the USB-C port. But the USB-C output is 5V ONLY, and the battery is 9-12.6V, so Vout(5V) < Vin_min(9V) ALWAYS ⇒ a step-down BUCK suffices. The buck-boost (+ 4 external FETs + 30V-FET/TVS coordination + a congested compact hot loop + 16A input trunk) was pure over-engineering. v1's own ADR-0004 shows the correct simpler architecture — "5V buck + standalone fixed-5V/5A PD source controller" — was CONSIDERED and rejected. v2 adopts it.
>
> THE CORRECT ARCHITECTURE (all step-down, ~7A, ~55W):
> - Input: XT60 -> reverse-polarity P-FET -> fuse -> VIN (9-12.6V). REUSE v1's D1-CORRECTED input protection (D1/TVS after Q1 on VIN, not VBAT_F — the v1.0 defect; the fix is in projects/usb-hub-3s/03_src as of commit 429e4a6 — read it as reference).
> - USB-A rail: 5V buck (LM5116, PROVEN on v1's USB-A side) -> 5VA -> 3x TPS2557 limiters + TPS2513A DCP -> 3 USB-A ports (5V/2A, 2.5A burst). This half of v1 works — carry it forward.
> - USB-C rail: a 5V buck feeding a SIMPLE 5V/5A PD SOURCE CONTROLLER (fixed 5V PDO + e-marker for the 5A advertisement) -> USB-C port. NOT a buck-boost.
> - KEY ARCHITECTURE ADR (decide + justify): one shared 5V buck sized for ~11A total (6A USB-A + 5A USB-C) vs two separate 5V bucks (fault isolation, matching v1's ADR-0001 isolation goal). Note the trade; the per-port TPS2557/PD-controller current limits already give some isolation.
>
> MANDATORY GATES you must satisfy (this board is the E-TOPO green-case proof):
> - D-SPEC + VOLTAGE ENVELOPE: emit 03_src/rules/power_tree.yaml with every rail's vin/vout min-max + iout + converter. Every rail is a BUCK (vout 5 < vin_min 9). Run skills/kicad-pcb/scripts/power_topology.py — it must PASS E-TOPO (all buck, none over-capable). Print the derived worst-case input current (~7A at 9V) — contrast v1's 16A.
> - D-SPEC SOURCING SPIKE (the one real unknown): the ledger's pd-source-5v5a entry is IP6559 = buck-boost = OVER-CAPABLE for a 5V-only port. Run a timeboxed search for a SIMPLE fixed-5V/5A PD source controller (standalone, no boost; candidates to verify — Injoinic/WCH/Southchip fixed-PDO PD source controllers, TI TPS25730 in fixed mode, or a PD-source PHY + the 5V buck). Escape-check it (D-ESC). If nothing 5A-capable is stocked, flag it as a tension (5V/3A plain-Rp fallback needs no PD chip) — but the spec is 5A, so prefer a real PD source controller. Harvest the chosen part into the ledger.
> - D-ESC/D-TIER: escape blocks on all multi-pin parts; declare fab_tier as the cost ceiling (this board should be STANDARD tier or cheaper — no buck-boost QFN forcing advanced).
> - S-COUNT: manifest.yaml + tsx_preflight before the first tsci build.
> - Reuse v1's D1-fix, gate-R (N/A now — no external boost FETs), doc-sync learnings, and the mandatory input-protection ADR.
>
> SCOPE THIS RUN: commission (BRIEF verbatim-style with the v1->v2 lineage + the 5V-only decision as a recorded D#) -> architecture + ADRs (power tree, E-TOPO green, the one-vs-two-buck ADR, input protection) -> parts (fan out research; ledger hits for XT60/LM5116/TPS2557/TPS2513A/USB-A/USB-C; NEW = the PD controller) -> tscircuit schematic -> ERC 0 + count_parity -> PLANNED HANDOFF at the schematic gate (commit, handoff journal with the routing work order). If context allows and you're confident, you MAY continue into placement/routing (v2 routes far easier than v1 — no buck-boost congestion), but the schematic gate is the required milestone.
>
> RULES: journals per M9; commit at green gates; NEVER push; do NOT touch projects/usb-hub-3s (v1, frozen), projects/crow-*. New project dir: projects/usb-hub-3s-v2. Toolchain: /usr/bin/python3 (pcbnew), /usr/bin/kicad-cli, tsci ~/.nvm/versions/node/v22.12.0/bin/tsci, ~/.bun/bin.
>
> FINAL REPORT: architecture summary (the all-buck power tree + E-TOPO PASS + derived ~7A), the PD-controller sourcing outcome, ledger harvests, gate scoreboard with MEASURED numbers (ERC, count-parity), commits (shas), and the exact handoff state / routing work order.
<!-- prompt-verbatim-end -->

- date: 2026-07-22
- channel: pcb-design pipeline invocation (agent task)
- lineage: v2 supersedes usb-hub-3s v1.x (frozen). v1 remains as reference for
  reusable subcircuits and paid-for learnings; v2 is a NEW project dir, not an
  edit of v1.

## End goal — definition of done

A 3S-LiPo (XT60) powered charging hub that supplies **3× USB-A** ports
(5 V, 2 A continuous / 2.5 A burst each, DCP auto-detect) and **1× USB-C**
port advertising a **5 V / 5 A PD source contract**, from a single all-BUCK
(step-down) power architecture. The board is orderable at JLCPCB, DRC/ERC
clean, and correctly scoped: no converter is more capable than its rail
requires (E-TOPO green). Deliverable of THIS run: the schematic gate
(ERC 0 + count-parity) + a planned handoff to routing.

| # | Criterion | Source | Status |
|---|---|---|---|
| G1 | Input: 3S LiPo (9.0–12.6 V) on XT60, reverse-polarity + fuse + TVS + UVLO | P (v1 lineage) | design |
| G2 | 3× USB-A @ 5 V / 2 A cont (2.5 A burst), TPS2557 limit + TPS2513A DCP | P | design |
| G3 | 1× USB-C @ 5 V / 5 A PD source contract (fixed 5 V PDO + e-marker 5 A) | P | design |
| G4 | ALL converters are step-down BUCK (E-TOPO green, none over-capable) | P (E-TOPO) | design |
| G5 | fab_tier STANDARD or cheaper (no buck-boost QFN forcing advanced) | P (D-TIER) | design |
| G6 | Schematic gate: ERC 0 + count-parity, then planned handoff | P (scope) | **GREEN — handoff** (ERC 0, parity 112==112, E-INV 15/15) |

## Spec tensions (D-SPEC — filled at commission, before architecture)

| # | Requirement | Standard / parts cap it exceeds | Resolution (ADR) | User flagged |
|---|---|---|---|---|
| T1 | USB-A "2.5 A burst" | Classic USB-A contacts are a ~1.5 A-class system; no "2.5 A-rated" A receptacle exists | 0002 (carried from v1) — 2 A cont / 2.5 A short burst, I²R disposition | yes |
| T2 | USB-C "5 A" | Type-C plain-Rp CC advertisement tops at 3 A; 5 A REQUIRES PD + e-marked cable | 0003 (carried from v1) — real PD source controller advertises 5 A PDO; e-marker in the port cell | yes |
| T3 | Simple fixed-5V/5A PD SOURCE controller stocked? | v1 ADR-0004 claimed NONE exists → defaulted to IP6559 buck-boost | 0004-v2 — REFUTED: TPS25740A (C544309, ~2974 stk) is a pure PD-source PHY, fixed 5V/5A pin-strap, external buck. | yes |
| T4 | USB-C **5 A** ⇒ fab tier | The 5A PD-source PHY (TPS25740A) is a 4-sided VQFN-24 0.5mm → escape_check forces **jlc_4layer_advanced**. STANDARD is only reachable by dropping to 5V/**3A** plain-Rp (no PD chip). | 0011 — take 5A per spec, accept advanced (ONE small QFN vs v1's whole buck-boost cell); 3A-standard offered as user's call. | **yes — LOUD** |

## Log

- **D1 (2026-07-22, user directive):** The USB-C port is **5 V ONLY** (fixed
  5 V PDO). It is NOT full-range PD (5–20 V). Therefore the USB-C DC-DC is a
  step-down BUCK, not a buck-boost. This is the founding decision of v2 and the
  root cause the v1 over-engineering. Recorded per SKILL SPEC-CHECK rule.
- **D2 (2026-07-22, agent decision — see ADR-0010):** TWO separate 5 V bucks
  (one per rail: USB-A ~6 A, USB-C ~5 A) rather than one shared ~11 A buck.
  Rationale: each buck is EXACTLY the proven LM5116 5 V/7 A design point (zero
  re-derivation), fault isolation between the A-side and C-side, and a cleanly
  separable PD cell. Trade recorded in ADR-0010.
- **D3 (2026-07-22):** fab_tier target was jlc_4layer_standard at commission,
  **REVISED to jlc_4layer_advanced at D-ESC** (ADR-0011). The 5A PD-source PHY
  (TPS25740A, VQFN-24 0.5mm) forces advanced (via-in-pad escape). This is the
  ONLY advanced-forcing part — everything else escapes at standard. Flagged as
  tension T4: 5V/3A (plain-Rp, no chip) would keep the board at STANDARD.
- **D4 (2026-07-22, sourcing spike / ADR-0004-v2):** PD source controller =
  **TI TPS25740A** (LCSC C544309). Pure PD-source PHY (CC monitor + BMC PD +
  external-NMOS gate driver), NO internal DC-DC — sits on the USB-C buck's 5V
  rail. Pin-strap: HIPWR→GND (5A), EN9V/EN12V low (5V only). Refutes v1's "no
  such part exists". NRND lifecycle — flagged; migration path TPS65987D.

## Decision register

| id | decision | decided by | depth |
|---|---|---|---|
| D1 | USB-C is fixed 5 V only ⇒ all-buck architecture | user (2026-07-22) | founding |
| D2 | Two separate 5 V bucks (per-rail), not one shared 11 A buck | agent / ADR-0010 | architecture |
| D3 | fab_tier = jlc_4layer_standard (target) | agent / D-TIER | tier |
| D4 | PD source controller identity | sourcing spike / ADR-0004-v2 | parts (pending) |

### D2 — 2026-07-22 — user directive (locks the 5A path)
> "we need 5A @ 5V on the USBC its for a raspberry pi"
Impact: USB-C = 5V/5A PD, HARD requirement (Raspberry Pi 5 draws 5V/5A via
PD; without the 5A PDO it throttles peripheral current). Resolves the
5A-vs-3A question from the schematic-gate report DECISIVELY toward 5A.
- KEEP the TPS25740A PD source PHY (fixed 5V/5A PDO).
- ADR-0011 (the 5V/3A plain-Rp alternative that would drop to standard tier)
  is REJECTED by this directive — record it as rejected, do not delete the ADR.
- fab_tier jlc_4layer_advanced STANDS and is now a JUSTIFIED D-TIER cost
  (the TPS25740A 0.5mm QFN needs via-in-pad). This is the correct kind of
  advanced-tier spend: paying for a GENUINELY-NEEDED 5A PD PHY, NOT for the
  unused 20V boost that made v1 over-engineered. The distinction is the whole
  point of D-TIER — an explicit, justified capability cost, not an accident.
- Order-day: TPS25740A is NRND (recheck stock); its 5V OVP window is tight
  (buck-C transient must stay inside it — bring-up check).
