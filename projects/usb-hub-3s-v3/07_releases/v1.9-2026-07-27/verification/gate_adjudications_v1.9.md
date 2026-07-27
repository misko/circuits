# v1.9 GATE ADJUDICATIONS — two NEW gates, first run on this board

Both gates below run for the FIRST TIME on usb-hub-3s-v3 in v1.9. Both report
findings. Neither finding is a board defect, and this file says exactly why,
with the measurement, so a reader can disagree with the judgement instead of
having to rediscover the geometry. Both are also REPORTED UPSTREAM as gate
gaps rather than fixed here — the gates are shared and two other agents were
working in `skills/` on 2026-07-27.

---

## 1. A-RENDER — `twin_overlay.py`, top side: 29 refs flagged, 0 board defects

`twin_overlay.py` measures each part BODY in pixels out of the modeled render
and compares it against the body position the BOARD implies (mesh bbox x JLC's
own model transform x placement). Its verdict on `twin_top.png` is:

    COVERAGE: 53 measured / 121 refs with an expected body
              (68 unresolvable, 0 resolvable-but-unmeasured, 1 no-model)
    OVERLAY FAIL: 29 unfaithful ref(s)

**Coverage first, as the skill requires.** 53 of 121 measured; `0
resolvable-but-unmeasured` is the number that matters — no ref that COULD have
been measured was skipped. The 68 unresolvable are the dense 0402/0603 field,
which pixel extraction cannot segment; that is partial by construction.

The bottom side was run too and the gate **REFUSED** it:

    OVERLAY REFUSED: no footprint has a courtyard on the B.CrtYd layer, but 129
    have one on the other side.

That refusal is CORRECT and is itself evidence: all 119 CPL placements are on
the top (`placement histogram: top=119`). This board has no populated bottom
side, so "both sides that carry parts" is one side.

The 29 flagged refs fall into three classes. Each was adjudicated by LOOKING at
the per-ref crop `06_build/twin_v19/overlay_<ref>.png`, not by arguing from the
table. Green = expected body, magenta = measured body, red = courtyard.

### Class A — 18 bulk MLCCs: the MEASUREMENT is wrong, the render is right
`C9 C10 C11 C12 C14 C15 C16 C17 C24 C25 C26 C27 C29 C30 C31 C32 C49 C50`
(1210 and 0805 bulk ceramics, centre delta 1.50-1.67 mm, outward 0.00-0.15 mm)

Looked at `overlay_C10.png`: the GREEN expected box sits exactly on the cap body
in the render. The MAGENTA measured box is a narrow strip on the body's left
edge. The numbers say the same thing — expected `58.300..61.500` = 3.200 mm
wide, measured `57.834..58.643` = **0.809 mm** wide, `body px = 46` at
7.4174 px/mm = 0.820 mm. The extractor latched onto the high-contrast silver
terminal band instead of the gold body, which is close in colour to the copper
pour underneath it. The centre delta of ~1.6 mm is exactly half of the 2.39 mm
of body the sliver misses, and the right-edge delta is reported as -2.85 mm for
every one of them — a constant, not a scatter.

Nothing on the board moved: these caps' CPL rows are byte-identical to v1.8's.
**Disposition: gate segmentation limitation on a light body over a filled pour.
No board exposure. REPORTED upstream.**

### Class B — 6 PowerPAK SO-8 FETs: MOUNT-FALLBACK, no pad correspondence
`Q1 Q2 Q3 Q4 Q5 Q6` (centre delta 1.65-1.98 mm, outward 0.24-0.56 mm)

`twin_report.csv` reports each of these as `fit: NONE (best 2.85-2.87mm) ->
JLC's own transform`. The cause is documented in
`02_parts/AON6354/part.yaml`: the KiCad `PowerPAK_SO-8_Single` land names ALL
FOUR drain pads `5` (single merged drain paddle), while JLC's model numbers them
separately — so a pad-NUMBER fit has nothing to correspond and jlc_twin falls
back to mounting the body at JLC's own footprint transform.

Looked at `overlay_Q2.png`: the MAGENTA measured box sits exactly on the grey
FET body as rendered; the GREEN expected box is offset ~1.5 mm. So the
measurement is good and the EXPECTED value is computed on an assumption that
does not hold for a fallback-mounted body. jlc_twin's own text for this class:

    MOUNT-FALLBACK: no pad correspondence exists, so this body is at JLC's OWN
    transform and the leads CANNOT be expected to sit on our pads — the render
    answers "what does JLC's CAD look like on our board", not "do the leads
    land". Settle the land pattern against the datasheet; the picture cannot.

Gerbers and the CPL derive from PADS, never from the model, so there is no board
exposure. **This is a genuine render-fidelity limit for six refs and it was
handed to the fresh-context render reviewer as an explicit instruction: judge
Q1..Q6 placement from the courtyard and pads, not from the body position.**
That is what A-RENDER is for — it converted "the render might be lying" into a
named list of six refs where it is, before a human looked at it.

### Class C — 5 connectors: real, intended courtyard overhang
`J1 J2 J3 J4 J5` (J2/J3/J4 centre delta 0.713-0.715 mm, outward 1.447 mm)

Looked at `overlay_J2.png`: green and magenta essentially coincide. The flag is
the OUTWARD excursion past the red courtyard, which is the edge-mounted USB-A
receptacle body legitimately overhanging the board edge. Per SKILL.md this class
— body outside its courtyard with expected and measured AGREEING — is
"reported, never gated, because gating it buys a permanent waiver and canon M4
says an inherited waiver is a defect vector."

J1 (XT60, centre delta 6.792 mm) is Class A's segmentation problem on a large
dark connector against the dark off-board area: expected 18.100 mm wide,
measured 7.415 mm.

### A-RENDER disposition
**29 flagged, 0 board defects, 6 refs (Q1..Q6) with a real render-fidelity
caveat that was passed to the render review as a constraint.** No ref shows a
body in a place the board does not put it.

---

## 2. P-FACT — `part_facts_check.py`: 1 violated fact, and the fact is TRUE

    P-FACT: 8/29 part.yaml declare an `asserts:` block; 8 assertions graded
    P-FACT: KT-0805Y/D8: pad 1 is on net 'LEDPKK' (positive) but part.yaml
            asserts pad 1 is negative
    P-FACT FAIL: 1 violated part fact(s)

The assertion in `02_parts/KT-0805Y/part.yaml` is that D8 pad 1 (the LED
CATHODE, KiCad `Device:LED` pin 1 = K) sits on a negative net. Traced out of the
SHIPPED netlist `source/usb_hub_3s_v2.net`, node by node:

    VIN --- R37.1
            R37.2 --- LEDPK --- D8.2  (pinfunction A_2, the ANODE)
                                D8.1  (pinfunction K_1, the CATHODE)
                                  |
                                LEDPKK --- Q8.3 (pinfunction D_3, the DRAIN)
                                           Q8.2 (SOURCE) --- GND
                                           Q8.1 (GATE)   --- ENKILL

D8's cathode is on the drain of a low-side N-FET whose source is GND. That IS
the negative side of the indicator; the LED is the right way round.

The gate cannot see it because its polarity classifier is a CLOSED net-NAME
list, by design:

    NEG_NET = ^(GND\b|AGND|DGND|PGND|VSS|GNDA|0V|VEE|.*_N$|.*-$)
    #: Deliberately a closed, readable list rather than a heuristic.

`LEDPKK` is a SWITCHED low-side node, not a rail called GND, so it does not
match and is classified positive. The four green rail LEDs D9-D12 (KT-0805G)
pass, because their cathodes go straight to GND — same assertion, same part
family, and the only difference is that D8's return is gated by Q8.

**Disposition: the assertion is correct, the circuit is correct, and the gate's
closed name list has no way to express "switched low side". REPORTED upstream
as a P-FACT schema gap (an assert-level `negative_via:` or an explicit expected
net would close it). No change made to the assert — weakening it to make the
gate quiet would be exactly the inherited-waiver failure canon M4 names.**

P-FACT is not wired into `policy_audit.py`; it does not affect the M-REL
zero-FAIL requirement. It is shipped here, failing, WITH this adjudication,
rather than omitted — a gate whose output is hidden because it is inconvenient
is worse than a gate that never ran.

---

## 3. The two v1.9 RENDER-REVIEW P1s — both adjudicated, both real, neither a board defect

Raised by the zero-context render review of this staging directory
(`08_reviews/2026-07-27_v1.9_render-review.md`, verdict **PASS**, findings 1
and 2), and settled here before the seal because after the seal the only remedy
is a supersede.

### 3.1 `assembly_coverage.txt` shipped a **FAIL** the MANIFEST reported as clean

**The finding is correct.** The archived `assembly_coverage.txt` ended
`A-POP: FAIL (1 finding(s))` on `MANIFEST-UNDECLARED: the release MANIFEST
carries no not_assembled: line`, while `MANIFEST.txt` plainly carries
`not_assembled:  F1, R42, SW1`. The reviewer root-caused it by **mtime**, which
is the right instrument: `assembly_coverage.txt` 11:43:54, `MANIFEST.txt`
12:04:45 — **A-POP read the MANIFEST 21 minutes before the MANIFEST was
written**, so on a first build this check could never pass.

**RE-RUN 2026-07-27 against the staged MANIFEST, unchanged command otherwise:**

    board=129 footprints, cpl=119 placements, unpopulated=10
      (declared=3, consigned=0, exempt_prefixes=['H','TP','FID','MH'])
    placement histogram: top=119
    A-POS datum: 119 rows graded, worst 0.00050 mm (Q6), tol 0.05 mm
    A-POP: PASS (every unpopulated part is declared with evidence)

**The archived file is the RE-RUN, and it is regenerated AFTER the MANIFEST
stamp** — which is where the seal procedure already puts `policy_audit` and
`release_freshness_check` for exactly this reason (a gate that grades the
manifest must run after the manifest exists). No board change; the FAIL was an
ordering artifact and nothing else. The MANIFEST's GATES block now states the
A-POP result *and* names this ordering dependency, so the next person does not
rediscover it.

### 3.2 `missing_models.txt` says 122/122 while R12 has **no JLC model at all**

**The finding is correct in its consequence, and the file is not wrong — it is
answering a different question than the one a reviewer asks of it.** Both halves
matter:

* **What the gate measures:** `jlc_twin.py`'s NO-BODY pass walks each CPL
  designator on the *mounted* board and asks **"does this ref render a 3D body?"**
  `bodies mounted: 122/122` is TRUE by that definition — R12 renders the body
  from its own KiCad footprint.
* **What it does NOT measure:** whether **JLC** has a model. Measured
  independently here by set-differencing `twin_report.csv`: **46 LCSC codes, 45
  carry a `MODEL-REG*` row, exactly one does not — `C2984354` (R12)**, whose only
  row is `FETCH-FAILED: Failed to fetch data from EasyEDA API for part
  C2984354`. That is consistent with ORDER_README gate **P5**, which already
  records the 404 as genuine absence from EasyEDA's library rather than a flake
  (re-probed 2026-07-27, 8 attempts).
* **Why it matters:** a reviewer who sees R12 bodiless in JLC's own preview and
  consults the file the contract designates would be told every part has a body,
  and could conclude R12 is missing from the board. It is not — it is on the BOM
  and the CPL; JLC simply has no CAD for it.

**NOT HAND-EDITED.** The header says `GENERATED … do not edit`, and v1.5 of this
board shipped a HAND-AUTHORED copy claiming zero gaps while seven placements
rendered nothing — a counter nobody could falsify. The correction therefore
lands where it can be trusted: **the MANIFEST `twin:` line now carries the
caveat and the R12 name**, and the gap is on the upstream table below.
Also noted, and disclosed by the file itself: the denominator is **122 checked
refs**, not the 119 CPL placements, because `--cpl` was not passed to that run.

---

## Gate gaps reported upstream from this release

| gate | gap | consequence here |
|---|---|---|
| `twin_overlay.py` (A-RENDER) | pixel segmentation loses a light body over a filled copper pour; 1210 MLCCs measure as a ~0.8 mm terminal sliver of a 3.2 mm body | 18 false FAILs |
| `twin_overlay.py` (A-RENDER) | a MOUNT-FALLBACK body (no pad correspondence) is graded against an expected position computed for a FITTED body | 6 false FAILs (Q1..Q6) |
| `part_facts_check.py` (P-FACT) | `pad1_net_polarity` resolves polarity from a closed net-NAME list, so a switched low-side node reads as positive | 1 false FAIL (D8) |
| `rules_audit.py` (A-AMP) | has `pour_fed:` for a plane-carried class but no way to declare a LOW-DUTY PULSED one | the GATE class had to write its RMS into `current:` with the derivation in a comment |
| `rules_audit.py` (A-ORDER) | the read-only-checker whitelist keys on FILENAME, so it cannot see that `route_and_stitch_generic.py verify-fill` writes nothing | `rebuild_*.sh` reordered instead (harmless: `generate_rules_generic.py` never opens the `.kicad_pcb`) |
| `count_parity.py` (S-COUNT) | prints `extra[:8]` — the message TRUNCATES at eight refdes | the 2026-07-27 audit read "8 refs missing"; the real gap was 12 (D8-D12, Q8, R37-R42) |
| `jlc_twin.py` (NO-BODY) | `missing_models.txt` conflates **"a body renders"** with **"JLC has a model"**. A ref whose EasyEDA fetch FAILED still mounts its KiCad footprint's own body and is counted as mounted, so the designated file reports `(none)` while a `FETCH-FAILED` row sits in `twin_report.csv`. A second counter — models RESOLVED FROM JLC — would close it | §3.2: 122/122 mounted, but 1 of 46 LCSC codes (C2984354 / R12) has no JLC model. Adjudicated, not hidden |
| `assembly_coverage.py` (A-POP) | `MANIFEST-UNDECLARED` grades a file the SEAL writes later, so on a first build the check cannot pass and its FAIL is an ordering artifact. It has no way to say "manifest not yet stamped" | §3.1: shipped FAIL, re-run PASS. Fixed here by running it after the stamp, as the seal procedure already does for `policy_audit` |
| `power_topology.py` (E-OFF) | `grade_off_control()` checks only that `quiescent_ua` is **DECLARED**; it never reconciles the number against the netlist, so a budget can omit a whole term and still pass | the 271 uA figure omitted 443 uA of always-on UVLO divider across three sealed releases (v1.6-v1.8) and would have made bench gate Q6 **condemn a good board**. Corrected in v1.9 — ORDER_README "Q6 in plain words" |
