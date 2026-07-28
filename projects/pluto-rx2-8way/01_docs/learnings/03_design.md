# Learnings — 03 design docs / ADRs / rules (pluto-rx2-8way)

Raw harvest evidence, written at stage completion (canon M9). Not canon.

## The commission scaffold silently skipped the SUB-FOLDER contracts

- what happened: `contracts_audit.py --projects` reported **3 C-ALLOW failures**
  on this board — `03_src/rules/{nets,electrical_invariants,power_tree}.yaml`
  "not permitted by `projects/pluto-rx2-8way/03_src/contracts.md`". Every other
  board in the fleet passes, because every other board has
  `03_src/rules/contracts.md` and this one did not. It had been failing since
  the commission commit, unnoticed for a day.
- root cause: TWO mechanisms compounding. (1) The commission step copies "each
  folder's `contracts.md`" for the **nine stage folders + ROOT**, and the skill's
  template set also ships `03_src/rules/`, `03_src/lib/`, `01_docs/decisions/`,
  `01_docs/journal/`, `01_docs/learnings/`, `01_docs/sourcing/` — six sub-folder
  contracts that the stage-folder loop does not enumerate. (2) The **plain**
  `contracts_audit.py` invocation, which is the one CLAUDE.md names and the one
  the test suite runs, **does not grade `projects/` at all** — so the failure was
  invisible unless somebody thought to add `--projects`, and a green "243 files,
  0 violations" reads as coverage.
- avoid next time: the commission step should copy the template contract set by
  WALKING `templates/contracts/**`, not by iterating a hardcoded stage list —
  the same M-WIDTH shape as every other "fix the instance, leave the class open"
  finding. A cheaper backstop: have the scaffold assert that every directory it
  creates resolves to a contract.
- candidate-canon: **yes** — suggest **C-SEED**: a newly commissioned project's
  contract set must be a superset of `templates/contracts/**` by PATH, checked
  once at commission. Note the related gap in the auditor's own coverage line:
  a run that grades zero project files should say so (canon M-COVER).

## A deep tap has a SECOND cost, and it is not on the path you are optimising

- what happened: T2 chose the pickoff depth by minimising RX1's insertion loss
  and published −19.8 dB / 0.43 dB / 26.3 dB. At stage 3, computing the
  REFERENCE dwell's signal-to-interference ratio gave **+1.2 dB at 4–6 GHz** on
  guaranteed specs — the reference channel is nearly buried by leakage from the
  seven live antennas, and nobody had computed it because the tap loss had been
  treated as a cost to RX1 only.
- root cause: an attenuator in a MULTIPLEXED chain attenuates the wanted signal
  but NOT the interference that arrives through the multiplexer's own isolation.
  The cost function had one term where it needed two. It was invisible because
  the number that looks alarming (−20 dB) sits on the path everyone was
  watching, and the number that matters (tap − Σ isolation) is on neither
  datasheet row by itself.
- avoid next time: whenever a signal is attenuated BEFORE a switch/mux/combiner,
  compute its level relative to the aggregate LEAKAGE at that node, not only
  relative to the source. State it as a ratio, per band, from the guaranteed
  column.
- candidate-canon: **yes** — an RF-selection design rule: *any deliberate
  attenuation upstream of a multiplexer must publish the resulting SIR against
  the mux's aggregate isolation, per band, from the min/max columns.*

## An isolation column grades the LEAKER, not the LISTENER

- what happened: the instinct "put the reference on the best-isolation port"
  (RF4/RF5, 38 dB min) is WRONG and measurably so: the interference on any dwell
  is the power sum over the SEVEN DESELECTED ports, so choosing the reference
  port chooses which term is REMOVED from that sum. Putting it on the
  WORST-isolation port (RF1/RF8, 29 dB) removes the largest term:
  **−23.4 dB vs −22.5 dB**, and it also has the best insertion loss.
- root cause: the adjacent-property error (canon M-IMPORT's co-resident
  corollary) inside a datasheet table — the row is indexed by port, and it is
  natural to read it as a property OF that port's channel rather than of that
  port's leakage into the common one.
- avoid next time: when reading an N-throw switch's isolation table, write down
  explicitly which port each row describes before assigning functions to ports.
- candidate-canon: no — too specific to multi-throw RF switches to be a check
  ID, but it belongs in the part.yaml `gotchas:` for this family and in the
  proven-parts harvest.

## The reference layout's OUTLINE was a property of its CONNECTOR, not of the circuit

- what happened: pSemi's routed reference board (Figure 21) is OCTAGONAL, and
  copying that shape would have forced a bespoke `03_src/generate_board.py` —
  the shared generic backend supports a rectangle with a corner radius and edge
  notches and **has no polygon outline at all**.
- root cause: the octagon exists because the EVK uses EDGE-LAUNCH jacks, which
  must sit on an edge; nine of them force nine sides. This board uses VERTICAL
  THT flange jacks that mount on the board FACE. The load-bearing decision was
  the RADIAL EQUAL-LENGTH STAR; the polygon was its connector's shadow.
- avoid next time: when adapting a reference layout, separate the decisions the
  CIRCUIT forces from the ones the reference's own COMPONENT CHOICES force. The
  canon already says "study, then re-derive" — this is a concrete test for it:
  ask what would change if one component were swapped.
- candidate-canon: **yes** — add to the D-ADJ / layout-precedent guidance:
  *before adopting a reference layout's OUTLINE, check whether it is implied by
  a connector/package choice this board does not share.*

## Protection that lives in a firmware register is not protection

- what happened: the switch's digital absolute maximum is 3.6 V on a 3.3 V rail.
  An unterminated CMOS edge into the 67 Ω control trace reaches **4.81 V** at
  the far end with the MCU pad at its strongest drive. The obvious mitigation —
  "configure the pad to 2 mA" — makes a DEVICE ABSOLUTE MAXIMUM depend on a
  register value that an SDK default or a port could change.
- root cause: treating a firmware setting as a design constraint. Nothing on the
  board objects when it changes, and the failure is cumulative and silent.
- avoid next time: size the series termination against the STRONGEST drive
  setting, not the intended one — here `R_S ≥ Z_line − Z_drv,min` = 42 Ω ⇒ 47 Ω,
  which holds the bound across the whole estimated pad-impedance range. The
  firmware recommendation then becomes good practice rather than load-bearing.
- candidate-canon: **yes** — a review-lens question: *does any absolute-maximum
  bound on this board depend on a firmware-selected value? If so, can copper
  hold it instead?*

## `keep_short` on a net that does not exist is graded by nothing

- what happened: `02_parts/PE42482A-X/part.yaml` budgets `SW_LS ≤ 2 mm`. The
  design decision (ADR-0005) puts LS directly on GND via a via at the pad, which
  is electrically right — and means `SW_LS` is not a net. `policy_audit`'s P-ADJ
  does `pts = netpads.get(net) or []` and `if len(pts) < 2: continue`, so the
  budget is SILENTLY SKIPPED.
- root cause: a checker treating "nothing to grade" as "nothing wrong" — the
  exact class canon M-COVER names, and the exact thing P-FACT already handles
  correctly by reporting an assertion that reaches no ref as UNREACHED.
- avoid next time: discharge the budget geometrically and put it on the
  CHECKLIST as a measured line (done). The gate fix is proposed upstream.
- candidate-canon: **yes** — P-ADJ should report a `keep_short` net that resolves
  to fewer than 2 pads as **UNREACHED** with the net named, never skip it.

## A retail stock number and an assembly stock number are different facts

- what happened: LCSC's retail product page reports **stock 0** for C25091 on
  the same day the JLCPCB assembly parts library reports **995,162** and library
  type `base`. C25091 is the resistor the whole user-confirmed pickoff depends
  on. A casual retail check reads as a blocker that is not one.
- root cause: measuring the state of a CATALOG RECORD instead of the state of
  the PART — canon M-QUOTE's own incident shape, one layer over (the two
  incidents in the canon are a search page and a catalog entry; this is a
  different WAREHOUSE).
- avoid next time: for a PCBA line, the assembly-library figure is the one that
  decides; the retail figure decides only for a hand-supplied part. Quote which
  pool a number came from, always.
- candidate-canon: **yes** — extend M-QUOTE's member list with *"an LCSC RETAIL
  stock figure where the property is JLCPCB ASSEMBLY-library availability"*, and
  have `jlc_stock_check.py`'s SCOPE note (which already says the assembly
  uploader allocates from a different pool) name the reverse direction too.

## Writing a marker string into the document that the marker delimits

- what happened: documenting how to reproduce the BRIEF's prompt hash meant
  writing the extraction command — which contains the two verbatim marker
  strings. That gave the file THREE occurrences of each marker, so
  `sed -n '/begin/,/end/p'` re-opened the range and swallowed the rest of the
  document. The check then reported a hash over ~13 KB of unrelated prose.
- root cause: a delimiter that is not escaped and not unique once the document
  starts talking about itself.
- avoid next time: describe such an extraction in WORDS, or use a unique
  sentinel. And note the shell trap found alongside it: `$(...)` strips ALL
  trailing newlines, not one, so a command-substitution version and a
  `head -c -1` version agree only by luck.
- candidate-canon: no — a documentation hygiene note, though the underlying
  fact (the recorded prompt sha is over the block with the final newline
  STRIPPED, while the 01_docs contract's runnable line KEEPS it) is worth
  fixing in the contract so every board's hash check stops disagreeing with its
  own recorded value.
