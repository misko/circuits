# ADR-0004 — The load is a Raspberry Pi 4: the PD-override premise was a Pi 5 feature

status: accepted
date: 2026-07-25
supersedes: the REASONING of ADR-0001 (its conclusion — no PD source controller —
  survives unchanged; its stated justification does not)
relates: ADR-0003 (clamp ordering, re-argued against the Pi 4's documented limits)
decision-log: task#30, user confirmation 2026-07-25

## Context

Every power document on this board rested on one sentence, recorded at commission
as a "user + web-confirmed finding":

> the Raspberry Pi can be told to SKIP PD negotiation and assume a 5 A supply via
> the bootloader EEPROM setting `PSU_MAX_CURRENT=5000` (or
> `usb_max_current_enable=1`)

**That is a Raspberry Pi 5 feature. The user has confirmed the load is a Pi 4,
which has no such setting and no equivalent.** `BRIEF.md` built its end-goal and
its T1/T3 spec tensions on it, ADR-0001 built its whole resolution path on it,
and `power_tree.yaml` carried `iout_max_A: 5` because of it.

The conclusion it was used to justify — **this board needs no PD source
controller** — is still correct. But it is correct for an entirely different
reason, and the difference is not cosmetic:

- A **Pi 5** *is* a PD sink. It negotiates for 5 A and self-limits without a
  negotiated contract. The Pi-5 story was "let us talk it out of negotiating",
  i.e. a deliberate departure from the normal interface.
- A **Pi 4** does not negotiate PD for its power input **at all**. Its USB-C
  input is a plain 5 V sink with CC pull-downs, officially rated **5 V / 3 A
  (15 W)**. There is no profile to request and no override to set. A plain
  regulated 5 V rail is not a workaround for a Pi 4 — **it is the native and only
  interface it has.**

An ADR whose stated reason is false is worse than no ADR, because it looks
decided. This fleet proved that twice in one day: the LMV393 "rail-to-rail" claim
on cooksense, and this. So the digit is not swapped — the argument is replaced.

## Options

- **Swap 5 → 3 and move on.** REJECTED. It leaves `PSU_MAX_CURRENT=5000` in the
  BRIEF, in ADR-0001's decision text, in the release README and in a silk hint,
  all instructing the user to set something that does not exist on their board.
  The number would be right and every sentence around it wrong.
- **Reduce the copper to a 3 A design.** REJECTED. buck-C, the F2 SMD2920-700
  polyfuse (7 A hold), the VBUSC via count and the delivery-corner pour widths
  were all sized for 5 A. Unwinding them is a re-route for negative value.
- **Correct the premise, keep the copper, and SAY that it is over-provisioned.**
  CHOSEN.

## Decision

The USB-C load is a **Raspberry Pi 4 at 5 V / 3 A**. `power_tree.yaml`
`iout_max_A: 5 → 3`. The board **stays provisioned for 5 A** and that is recorded
as deliberate over-provisioning rather than left as an unexplained mismatch. Every
reference to `PSU_MAX_CURRENT` / `usb_max_current_enable` is removed from the live
documents and struck (not deleted) in the BRIEF, which keeps the historical record
of what was believed.

Additionally: add **R42**, a DNP setpoint-trim strap (below).

## Consequences

### The margin improves 16.5x, and the caveat that has followed this board dissolves

Same hardware, same 97 mOhm budget, same 1.2 derating, same 5.227 V worst-case
regulated rail, same 4.63 V undervoltage threshold. Only the load changed, because
we now know what it is:

| | drop at the load | delivered | slack vs 4.63 V |
|---|---|---|---|
| Pi 5 premise @ 5 A | 97 mOhm × 5 A × 1.2 = **582.0 mV** | 4.645 V | **+15.0 mV** |
| Pi 4 actual @ 3 A | 97 mOhm × 3 A × 1.2 = **349.2 mV** | 4.878 V | **+247.8 mV** |

E-MARGIN re-graded: `headroom 597 mV = 199 mOhm total IR budget at 3 A -> PASS`.

"15 mV of paper slack is not a margin you ship on" was a true statement about the
wrong load. It is retired. The bench gates are **not** retired — a computed margin
is still computed — but ORDER_README gates Q2/Q5 are now judged against the 3 A
number, and the pass criterion changes with them.

Note what did *not* change: **the USB-C cable is still ~45 of the 97 mOhm**, the
single largest term in the budget. At 3 A it costs 135 mV instead of 225 mV. A
short, well-made cable remains the highest-leverage thing the user controls.

`load_uv_threshold: 4.63` is left alone — it was always the **Pi 4** undervoltage
figure, previously being applied to a Pi 5 by inference (which happened to be
conservative; a Pi 5 browns out nearer 4.25 V). It is now recorded as what it is.

And one figure is upgraded from inference to specification: the **Pi 4 absolute
maximum input is +6.0 V**, Raspberry Pi 4 datasheet p.8, Absolute Maximum Ratings,
stated in terms to be *"a stress rating only"*. ADR-0003 is re-argued against it.

### R42 — trim the setpoint, not the path

The user asked for an optional way to drop the 5 V rail if the bench says U12 is
too stressed, and their first instinct was **a series resistor in the 5 V line**.
It is recorded here as a rejected option because it is a genuinely attractive trap:

- **Wrong transfer function.** Over-voltage is a **light-load** phenomenon; IR drop
  is a **heavy-load** one. They are anti-correlated. At 0 A a series resistor drops
  0 mV — it does nothing in the exact condition it was added for. At full load it
  removes voltage precisely when the rail is already lowest.
- **It costs real margin.** 20 mOhm at 3 A is 72 mV and 0.18 W (at 5 A, 100 mV and
  0.5 W). That is delivery budget spent to fix a no-load problem.
- **It does nothing about the dangerous case.** Against a fail-high buck,
  20 mOhm × 3 A = 60 mV of a multi-volt excursion.

Trimming the **setpoint** moves the regulation target itself: load-independent,
zero heat, zero delivery-path cost. `Vout = Vref × (1 + Rtop/Rbot)` with
Vref 1.215 V, Rbot = R13 1.21k, Rtop = R12 4.12k → 5.352 V.

**R42 = 160k, 0402, DNP, in PARALLEL with R12.** Rtop becomes 4.12k ‖ 160k =
4.017k → 1.215 × (1 + 4.017/1.21) = **5.249 V**, landing on U12's 5.25 V V_RWM.

Cost if fitted, so whoever fits it knows what they are spending: worst-case
vout_min 5.227 → **5.125 V**; minus 349 mV of IR at 3 A = **4.776 V**, still
**+146 mV** above the 4.63 V threshold. **The trim is only affordable because the
load is a Pi 4.** At the mistaken 5 A it would have consumed the entire margin.

It ships **unpopulated** — bench-decidable insurance, not a fix, the same posture
as the LED brightness resistor. Declared `dnp_by_design` in `assembly.yaml` with
dated evidence, deliberately **uncoded** (no LCSC, so JLC neither sources nor
places it), and its value is pinned by an E-INV `part_value` assert. That last
guard is not decoration: the parallel combination is nonlinear in the strap, so
a 16k slip gives Rtop 3.271k → **4.500 V**, straight through the Pi 4's
undervoltage threshold and into a board that browns out at no load.

### Bench gate (new)

Measure **VBUSC at no load and at 3 A**, and **U12's leakage at the measured
voltage, over temperature**.
**PASS = fit nothing if U12's leakage is acceptable at 5.352 V; fit R42 if it is
not.** Record the measured numbers either way — including the "we fitted nothing"
case, because a gate whose only recorded outcome is the exception teaches nothing.
