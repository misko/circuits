---
id: 0002
date: 2026-07-30
status: accepted
tags: [assembly, sourcing, protection, topology, spec-tension]
---
# 0002 — the module is CONSIGNED, its own USB-C is the board's only port, and the protection chain goes with the boundary

## Context

Three questions the commission flagged, which turn out to be one question:
**where does the board's boundary run now that the MCU is a module?**

1. **T2 — assembly posture.** SKILL.md's opening rule is that PCBA is the
   deliverable and every footprint is machine-placed unless a recorded decision
   says otherwise. Is a Pico-class module orderable through JLC assembly at all?
2. **T3 — the module's own USB connector.** Wanted, or a liability? v1 has its
   own USB-C. Two USB ports on one board is a decision, not an accident.
3. **A4 — protection.** v1's ADR-0004 draws a PPTC -> TVS -> ferrite -> LDO
   chain around a VBUS entry point that no longer exists on this board.

### Evidence — the live JLC read (MEASURED 2026-07-30, by query, not memory)

Queried `POST /api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`
serially with 1.4 s spacing across 20 keyword forms. The endpoint answered every
call; no fallback was needed. Null results are reported as data:
`RP2040 module`, `RP2040 board`, `RP2040 core board`, `RP2040 development
board`, `castellated RP2040`, `WeAct RP2040`, `YD-RP2040` all returned **0 hits**.

**The structural finding, which is what makes the stock numbers a trap:** JLC
keeps TWO separate catalog entries per module, and only one of them is a line
part.

| code | part | stock | package field | what it is |
|---|---|---|---|---|
| C7203002 | Raspberry Pi Pico | **1499** | **`-`** (none) | LCSC RETAIL board, category "Development Boards & Tools" |
| C5159530 | Raspberry Pi Pico | 0 | `LCC-43` | the placeable entry |
| C19193665 | Raspberry Pi Pico H | 0 | `SMD,51x21mm` | placeable entry |
| C9900255426 | PICO | 0 | `COMM-SMD_L51.0-W21.0-P2.54_PICOW` | consign placeholder |
| **C9900173620** | **RP2040-Zero-NoLogo** | **0** | **`LCC-23(18x23.5)`** | **consign placeholder** |
| C9900177322 | Seeed XIAO RP2040 | 0 | `SMD-14P` | consign placeholder |
| **C2040** | **RP2040 bare chip** | **63091** | **`LQFN-56(7x7)`** | **a real line part** |

Controls run the same day to establish the discriminator: C1525 (100 nF 0402,
46.9 M, package `0402`), C701342 (ESP32-WROOM-32E, 19 416, package
`SMD,25.5x18mm`), C2980306 (ESP32-PICO-MINI-02, 853, `SMD-53P,16.6x13.2mm`).
**A part JLC's line can place always carries a real package string.** Every
in-stock Pico-class board carries `-` and lives under "Development Boards &
Tools" with an `lcscGoodsUrl` pointing at a retail product page.

The clinching detail: **C9900255426's `erpComponentName` is `【邮寄专用】PICO`**
— Chinese for *"mail-in only"*. JLC's own record says that footprint entry
exists to place a Pico **you ship them**.

Stated honestly: `assemblyComponentFlag` is `false` on *every* record including
C2040, so it is not the capability flag it looks like. **The conclusion is
INFERRED from catalog field structure against four controls, not read from an
official assembly-capability API, and no test order was placed.**

### What that means for the closed vocabulary

`reason: not_in_catalog` would be **FALSE**. The part IS in the catalog, with a
real footprint (`LCC-23(18x23.5)`). Writing `not_in_catalog` would put a lie in
the decision record to reach a convenient conclusion — which is the failure mode
a closed vocabulary exists to prevent, and the reason `process_incompatible` had
to be added to it in 2026-07-25 for a different board.

## Options

The skill's escalation ladder is **re-specify -> consign -> not_assembled**, in
that order, and each rung must be refused on evidence before the next is taken.

- **Rung 1 — re-specify to a placeable part.** The only Pico-class module with
  real placeable stock is... none. The only RP2040-bearing part JLC can place
  unattended is **C2040, the bare chip at 63 091 in stock** — which is v1.
  **REFUSED, and refused by the USER, not by me:** the commissioning prompt is
  "with the pico class module" and G8 makes the module the point of the board.
  An agent may not dissolve a user requirement by re-specifying it away. If the
  user later prefers turnkey assembly over the module, that is a directive and
  v1 already exists as the answer.
- **Rung 2 — CONSIGN.** We buy RP2040-Zero modules, ship them with the order,
  JLC places them onto `LCC-23(18x23.5)`. The part stays **ON the CPL** — it is
  ASSEMBLED, and consignment is a SOURCING class, not a population class.
  **CHOSEN.**
- **Rung 3 — `not_assembled` + hand-solder.** REJECTED. A 23-pad 2.54 mm
  castellated module is genuinely easy to hand-solder, so this is tempting and
  it is the wrong answer for a recorded reason: the skill requires the
  hand-solder rung to be a sourcing wall you PROVE you hit, and rung 2 is not
  blocked — JLC will place a consigned module. Taking rung 3 while rung 2 is
  open converts a cost/logistics preference into a fake sourcing constraint.
  **It is, however, the correct fallback if the consignment logistics are
  declined at order time**, and in that case the entry becomes
  `reason: user_supplied` with `on_bom: false` (we supply it and fit it, so JLC
  is asked neither to place nor to source it) plus `FP_EXCLUDE_FROM_POS_FILES`
  on the board. Recorded now so the fallback is a prepared decision rather than
  an order-day improvisation.

### The USB question, decided with it

- **Keep v1's own USB-C AND the module's.** REJECTED. Two ports that both power
  the board is a genuine hazard, not just clutter: plugging both connects two
  5 V sources through the module's 5V pad with nothing arbitrating them. v1's
  USB existed to power and flash a BARE chip. The module already has both.
- **Delete the module's USB.** Not available on RP2040-Zero (it is soldered on),
  and the module that offers it — RP2040-Tiny, USB on a detachable FPC adapter —
  was rejected in ADR-0001 for mechanical fragility.
- **The module's USB-C is the board's ONLY port.** CHOSEN.

## Decision

**1. The RP2040-Zero is CONSIGNED.** `03_src/rules/assembly.yaml` carries a
`consigned:` entry for `U_MCU` with `lcsc: C9900173620`, the dated catalog
evidence above, and an `msl:` line. It stays on the CPL and gets the same
rotation rigor as any placed part — **more**, because a consigned part is the
one you cannot cheaply replace (crow-recorder-central-v2 v1.2 shipped its
consigned TQFP-128 at CPL 270 when the twin measured 90).

**2. The module's own USB-C is the board's ONLY USB port**, for power and for
UF2 firmware loading. v1's entire USB subsystem leaves the design: `J_USB`
(TYPE-C-31-M-12A), `U_ESD` (USBLC6-2SC6) + `C_ESD`, `R_USB1`/`R_USB2` (27.4R
series), `R_CC1`/`R_CC2` (5.1k), `SW_BOOT` + `R_BOOT`, `SW_RUN` + `R_CSPU`.

**3. The protection posture is RE-DERIVED from the new boundary, not inherited.**
This is the mandatory protection ADR for v2 and it reaches a different answer
from v1's for a structural reason: **v1's protection chain defended a power
ENTRY POINT this board no longer has.**

| v1 element | v1's job | v2 disposition |
|---|---|---|
| `F_IN` PPTC 500 mA | limit VBUS fault current at the board's own USB | **REMOVED** — no board USB. The module's USB is behind the module's own input path; defending it is the module vendor's boundary, not ours |
| `D_TVS` SMBJ6.0A on the protected node | clamp VBUS transients | **REMOVED** — same reason. Our board's only power input is a 3V3 pad from an LDO whose output is bounded by construction |
| `FB_IN` ferrite | keep switching/digital noise off the LDO input | **KEPT IN FUNCTION, MOVED IN POSITION** — see below. It is now an RF measure on 3V3, not a protection measure on VBUS |
| `U_LDO` MCP1755S | make 3V3 | **REMOVED** — the module's RT9013-33 makes 3V3 |
| no RF ESD, no DC block on any of the 10 RF ports | deliberate (v1 ADR-0004) | **KEPT, deliberately.** A shunt device on a 50 ohm line is ~0.05-0.1 pF and costs the band the board exists to receive. Unchanged reasoning, re-affirmed rather than inherited |
| reverse-polarity block: absent | USB-C is keyed, no second source | **STILL ABSENT, and now UNREACHABLE**: there is no board-level power connector at all |
| UVLO: absent | nothing stores energy | **STILL ABSENT**, same reason |
| inrush limiter: absent | bypass held under the USB 10 uF cap | **STILL ABSENT** — v2's board-side bypass is smaller than v1's, since the MCU decoupling left with the MCU |

**What v2 ADDS, and it is an RF measure wearing a protection ADR's clothes:** a
**ferrite plus local decoupling between the module's `3V3` pad and the switch's
`VDD`**. The RP2040's core and QSPI current transients ride on the module's 3V3
rail; the PE42482A-X's VDD biases its FET stack, and its datasheet publishes no
PSRR. A series ferrite with a local ceramic at the VDD pin is the standard,
cheap answer and it is the ONE place this board's supply meets its RF part.

**The load is not the question and the numbers say so:** PE42482A-X draws
**120 uA typ / 200 uA max** (v1 dossier, Table 2 PDF p3) against an RT9013 rated
**500 mA**. Rail CLEANLINESS is the question; headroom is not.

## Consequences

- **Committed to a consignment logistics step at order time.** Modules must be
  bought and shipped with the order. This is a real cost and delay that v1 does
  not have, and it is the honest price of the module. It goes in the
  ORDER_README as a first-class step, not a footnote.
- **`msl:` is OWED and I am not filling it with a guess.** The `consigned:`
  schema requires an MSL statement, and it exists because
  crow-recorder-central v1.0 shipped a consigned MSL-3 part with zero MSL text
  in the order paperwork. **Waveshare publishes no MSL rating and no reflow
  profile for RP2040-Zero** — it is a finished consumer assembly, not a
  component sold in a moisture-barrier bag. The entry will state that as an OWED
  fact with the mitigation (bake before shipping, per JEDEC J-STD-033 for an
  unknown-MSL assembly), NOT a number invented to satisfy a schema. **A required
  field filled with a plausible guess is worse than one filled with the truth
  that nobody knows**, because the guess is indistinguishable from a datasheet
  read.
- **The board has no power connector of its own.** Bench-powering it without a
  USB host now means feeding the module's `5V` pad, which is a deliberate
  non-feature. Noted in ORDER_README's first-power ritual, which changes shape:
  there are no power-entry blades to multimeter, so the ritual becomes
  continuity from the module's 3V3 pad to the switch VDD and the absence of a
  3V3-to-GND short before the module is fitted.
- **E-OFF stays N-A and stays STATED**: `source_type: usb_bus_powered_5v`,
  `off_control: unplug`, `quiescent_ua: 0`. Bus-powered, de-energized by
  unplugging, nothing stores energy. Declared in `power_tree.yaml` so the gate
  sees a declaration rather than inferring N-A from silence.
- **E-TOPO becomes a question about a part we do not own.** The 3V3 rail's
  converter is the module's RT9013, which has no `02_parts` dossier because we
  do not buy it. The rail is declared in `power_tree.yaml` as linear with the
  module as its converter; if the gate cannot grade a converter it cannot see,
  that must be reported as UNGRADED rather than passed — resolved at the
  schematic gate, not assumed here.
- **What breaks if reversed:** re-adding a board USB-C brings back the
  dual-source hazard and 9 parts; declining consignment moves the module to
  `user_supplied` + `on_bom: false` and off the CPL, which is a prepared
  fallback above, not a new decision.
- **Re-verify at order time:** the stock read is dated 2026-07-30 and stock
  moves. The consign placeholder C9900173620 is permanently stock 0 BY
  CONSTRUCTION, so what must be re-checked is not JLC's stock but our own — that
  we hold enough modules to ship.
