# ADR-0003 — Status LEDs, and the U12/D5 clamp ordering that cannot be bought

status: accepted
date: 2026-07-25
relates: ADR-0002 (discrete USB-C VBUS protection — this ADR reports on it and
  records the residual it leaves open); ADR-0004 (the load is a Pi 4 — its
  documented +6.0 V absolute maximum is what the clamp order below is argued
  against, and the D5 section was REWRITTEN on 2026-07-25 once that was known)
decision-log: task#30 user decisions D2 (colours), D3 (brightness), D4 (per-port),
  D5 (protection ordering), D7 (bench gate)

## Context

Two unrelated questions arrived together for v1.6 and are recorded together
because the second one turns out to depend on the first for its evidence.

**(1) The board has no indicators at all.** Through v1.5 there is no way to tell,
without a meter, whether the pack is connected, whether either buck is running,
or whether the USB-C protection chain has opened. Every diagnosis starts with
"put a probe on it".

**(2) The USB-C over-voltage clamp may be the wrong device.** ADR-0002 put D5, a
600 W SMB TVS, on VBUSC. U12 (an ST USBLC6-2SC6 data-ESD array in SOT-23-6) also
sits on VBUSC, and its VBUS pin is a rail clamp to GND. If U12 breaks down first,
the small array — not the TVS — is the de facto clamp for the whole port.

## Options

### Indicators

- **One LED on 5VA.** REJECTED: with three current-limited USB-A ports behind
  three TPS2557 switches, a port that has latched off looks identical to a
  working one. The single most likely field fault on this board is invisible.
- **Per-port on VBUSA1/2/3, plus one on the C rail.** CHOSEN (D4). +4 parts,
  +2 nets, and — because the ballast value and the gate FET were selected to
  reuse lines that are already loaded — **+0 feeders**.
- **Pack LED on a switched node.** REJECTED because it does not exist. MEASURED:
  SW1's pads are `pad1 = GND`, `pad2 = ENKILL`, `pad3 = unconnected`; net `VBAT`
  touches only J1 and F1, and `VBAT_F` only F1 and Q1. **SW1 switches ENABLE, not
  power.** There is no node that is hot-when-on and cold-when-off to tap.
- **Pack LED wired directly to ENKILL.** REJECTED: only ~212 uA is available from
  the R8||R17 = 50 k pull-up bus, and an LED across it would clamp the enable bus
  to its own Vf and hold both bucks off.
- **Pack LED ungated on VIN.** REJECTED, and this is the one that would have
  shipped a defect: (12.6 - 2.1)/6980 = **1.504 mA typ** (0.946-1.547 mA over
  VIN 9.0-12.6 V x Vf 1.8-2.4 V). On top of the declared 270 uA OFF-state budget
  that is **6.6x over**, and it flattens a 3S 5000 mAh pack in **~117 days**
  (~94 days to the 20% LiPo floor) with the switch OFF. A customer-visible
  pack-kill introduced by an indicator.
- **Pack LED gated by a low-side N-FET off ENKILL.** CHOSEN. Q8 = BSS138
  (C78284 — the same line as Q7), G = ENKILL, S = GND, D = the D8 cathode.
  OFF-state adder is Q8's I_DSS only, <= 0.5 uA; the gate loads ENKILL by
  <= 100 nA (<= 5 mV of droop on the 50 k bus, nowhere near either LM5116's EN
  threshold). `power_tree.yaml` quiescent 270 -> **271 uA**.
- **C-rail LED on 5VC** vs **on VBUSC.** CHOSEN VBUSC (post Q6, post F2). The
  point of an indicator is to distinguish states: on 5VC it says "the buck is
  running", which the A-port LEDs already imply; on VBUSC a dark C LED with the
  A LEDs lit says **the ADR-0002 protection chain opened**, which nothing else on
  the board can report. Cost to the thin E-MARGIN slack, measured rather than
  assumed: 0.346 mA x 42.4 mOhm = **14.7 uV = 0.0147 mV = 0.098% of 15 mV**.

### Clamp ordering

- **Reselect D5 to break down below U12.** This was the user decision (D5). It
  **cannot be implemented — the part does not exist** — AND, once the target was
  confirmed as a Pi 4 with a documented 6.00 V absolute maximum, it turned out not
  to be the right goal either: D5 cannot protect the Pi at ANY breakdown voltage
  that also clears a 5.479 V operating rail. See below.
- **Lower 5VC so a lower-standoff TVS fits.** REJECTED in the decision itself:
  it spends the 15 mV E-MARGIN slack (`power_tree.yaml`), which is the one number
  on this board that has no room.
- **Substitute a 6.2 V Zener (LGE 1SMB5920B, C713628, Vz 5.89-6.51 V).** The only
  part found whose LOW end undercuts U12's 6.00 V floor. REJECTED: ~1.5 W against
  the 600 W (10/1000us) the D5 role needs. It would be destroyed by the very
  fault it is there for — trading a clamp-order problem for a destroyed clamp.
- **Accept the residual, with numbers and an escalation trigger.** CHOSEN.

## Decision

**Five indicators**: D8 (C2296 amber) on VIN through R37, returned through Q8
gated on ENKILL; D9/D10/D11 (C2297 green) on VBUSA1/2/3 post-TPS2557; D12 (C2297
green) on VBUSC post-Q6/F2. All ballasts 6.98 k (C23215, already on the BOM as
R7/R16), all LEDs 0805 with **pad 1 = cathode**.

**Clamp ordering: the residual is ACCEPTED and documented, because no orderable
part closes it.** D5 keeps its 6.0 V standoff / 6.67-7.37 V breakdown window.

## Consequences

### The clamp-order arithmetic — RE-ARGUED 2026-07-25 against the REAL target

**This section was written while the target was believed to be a Pi 5. The user
then confirmed a Pi 4 (ADR-0004), which gives the rail a DOCUMENTED absolute
maximum instead of an inferred one — and that changes the conclusion from "an
uncomfortable inverted hierarchy we accept" to "a non-issue, for a reason worth
stating plainly."**

Line the whole rail up, in ascending order, every number from a datasheet:

| V | what it is | source |
|---|---|---|
| **5.479 V** | worst-case operating VBUSC (tolerance-inclusive, no load) | `power_tree.yaml` |
| **6.00 V** | **Raspberry Pi 4 ABSOLUTE MAXIMUM input** — "a stress rating only" | Pi 4 datasheet p.8, Absolute Maximum Ratings |
| **6.00 V** | U12 USBLC6-2SC6 guaranteed non-conduction floor (V_BR **min**, no typ, no max published) | ST doc ID 11265 rev 5, Table 2, p.2/14 |
| **6.67 V** | D5 SMBJ6.0A breakdown **minimum** | Littelfuse SMBJ series, rev 06/03/20 |

Read that table once and the real conclusion falls out:

**D5 CANNOT PROTECT THE PI.** By the time the TVS begins to conduct, the rail is
already **670 mV above the Pi's absolute maximum**. That is not a marginal call —
D5 was never the Pi's guardian and could not have been at any breakdown voltage
that also clears a 5.479 V operating rail. D5 protects the **BOARD** against
**transients**, which is what a TVS is for.

So the "inverted hierarchy" that ADR-0003 originally worried about — U12 breaking
down before D5 — **is a non-issue for the Pi**, and the empty TVS window (below)
does not matter. U12 is in fact the only device on this rail that starts
conducting anywhere near the Pi's limit, which makes it the *most* useful thing
there, not a liability.

**STATE IT PLAINLY: NOTHING ON THIS BOARD PROTECTS THE PI FROM A SUSTAINED
OVER-VOLTAGE.** A TVS clamps transients, not a stuck regulator. If buck-C fails
high, the sequence is: U12 conducts (with no rating for sustained conduction — its
only clamping figures, 12 V @ 1 A and 17 V @ 5 A, are 8/20 us ESD pulses), D5
follows above 6.67 V, and F2 trips on the resulting current. The Pi sees an
over-voltage throughout. **This is exactly the fail-high posture the BRIEF already
accepts as best-effort for a supervised prototype** (ADR-0002, BRIEF A3/D3), and
it is now stated with numbers instead of being implied.

**The empty-window finding, retained because it is still true and still saves
someone a day.** A replacement D5 would need Vwm >= 5.479 V **and** Vbr(max)
< 6.00 V simultaneously. That window is empty, and not narrowly: the SMBJ family
has no standard step between Vwm 5.0 V and 6.0 V; 6.0 V's breakdown floor is
already 6.67 V; the tightest SMB-footprint part found at any qualifying standoff
is Vishay/ST **SM6T6V8A** (Vwm 5.80 V, Vbr 6.45-7.14 V @ 10 mA, doc 88385 rev
09-Jan-2024 p.2), whose **minimum** breakdown is still 450 mV above U12's floor
and which returns zero hits on jlcpcb.com for the unidirectional part (only the
bidirectional SM6T6V8CA is stocked, and a bidirectional device has no cathode,
failing this board's pad-1 polarity fact). The generic TVS relation
(Vbr ~ 1.11 x Vwm, +-10%) says why: at Vwm 5.479 V the nominal breakdown is
already 6.08 V, so there is no tolerance budget left to fit a maximum under
6.00 V. **DO NOT RESELECT D5.** It is not a sourcing failure, it is arithmetic.

**ESCALATION, and what KIND of part it is.** If sustained over-voltage protection
is ever actually required — an unattended or production context — the answer is an
**ACTIVE OVP tripping at ~5.6-5.7 V**, i.e. a **disconnect or crowbar**, sitting
between the worst-case 5.479 V operating rail and the 6.00 V Pi limit. **It is not
a different TVS**, and no TVS exists that would do it. That is a v-next hardware
addition, not a BOM substitution.

**A cheaper partial lever exists and ships unpopulated:** R42, the DNP setpoint
trim (ADR-0004), drops the rail 5.352 -> 5.249 V if the bench says U12's leakage
at the nominal setpoint is unacceptable. It reduces U12's steady-state stress; it
does nothing about a fail-high, and must not be mistaken for OVP.

### Bench gate (user decision D7)

`quiescent_ua: 271` rests on a BSS138 I_DSS figure that is a **25 C maximum** and
that nothing has ever measured; MOSFET leakage climbs roughly an order of
magnitude per 40-50 C. ORDER_README therefore carries a new gate: **LEDs fitted,
SW1 OFF, measure pack current with a uA meter and record it together with the
ambient temperature. PASS <= 300 uA.** That measurement, not the datasheet line,
is what qualifies the number.

### The rotation trap this cell introduced

C2296/C2297 are 2-pad polarized parts, the same class that made v1.4
DO-NOT-ORDER (C1/C2 reversed). JLC's own model numbers **pad 1 = ANODE**; KiCad's
`Device:LED` is **pin 1 = K**. A pad-NUMBER fit therefore reports offset **180 at
a 17.7x margin and is WRONG** — a high fit margin is not confidence. Measured with
two numbering-free channels, which agree on **0**: the unlabelled size-matched pad
cloud admits only {0,180} and refutes {90,270} at 12.5x; the polarity marks (our
F.SilkS cathode band at x = -1.685 and F.Fab chamfer corner at (-1.000,-0.600);
JLC's silk diode-glyph apex at x = -0.300 against its base at x = +0.200, and its
silk body chamfered at the WEST end) put both cathodes WEST, so the physical parts
already align. **A 180 row would ship every indicator dark, which on a bench is
indistinguishable from a dry joint.** Both codes go on the JLC order-preview human
gate.
