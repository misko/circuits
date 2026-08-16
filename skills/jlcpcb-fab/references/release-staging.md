# JLC fabrication and release-staging procedure

Use this procedure on the exact pre-seal archive. It grades the payload as
JLCPCB and assembly operators will receive it.

## Contents

1. Stage atomically
2. Fabrication payload census
3. Assembly battery
4. Mechanical and process evidence
5. Handoff to the seal owner

Via-process release coverage is the `A-VIA` obligation.

## 1. Stage atomically

Export into a fresh sibling staging directory. Do not reuse a mutable fab
folder containing prior KiCad-version output. Validate every required output,
reopen the durable CSV/zip/JSON bytes, write a bundle manifest last, and promote
only the accepted complete directory.

Stale files from a previous export must not enter the Gerber zip. A failed
rotation, BOM, stock, or model gate leaves no apparently current upload pair.

## 2. Fabrication payload census

Run the payload census on staged bytes and require:

- exact expected copper layer count;
- front/back mask, paste, and silk as applicable;
- edge cuts;
- PTH and NPTH drills;
- upload zip containing fabrication files only;
- BOM and CPL outside the zip;
- expected CSV headers and nonzero denominators;
- no unexpected stale extension duplicates.

Run standalone replot/open checks against copied release source. Exact Gerber,
drill, and archive identities are release evidence; a PDF or board screenshot
does not substitute for them.

## 3. Assembly battery

Run against the staged archive:

- BOM source identity;
- BOM legibility;
- stock verdict and sidecar;
- assembly/population coverage;
- part-owned facts;
- rotation authority and human worklist;
- digital twin and same-camera registration;
- model/body coverage;
- release freshness/required-artifact checks.

Every gate reports graded/total coverage. Zero denominator fails unless the
contract explicitly proves non-applicability.

Keep design and order conclusions distinct. A correct design may remain
`BLOCKED-SOURCING`, `FIRST-ARTICLE-ONLY`, or `DO-NOT-ORDER` because JLC stackup,
stock, uploader mappings, or operator previews are unresolved.

## 4. Mechanical and process evidence

Capture or explicitly hold:

- selected JLC layer stackup and controlled-impedance construction;
- local impedance calculation using the same fabricated dimensions;
- signal layer/reference plane and copper treatment;
- via drill/diameter/aspect-ratio checks;
- selective via-fill/cap process where relevant;
- board thickness, finish, copper weight, solder-mask, and impedance options;
- THT/consigned/manual assembly scope;
- BOM match and rotation previews;
- first-article test plan.

Public JLC capability tables are useful for feasibility but do not prove which
stackup/order options the uploader will apply. Preserve the final selected
values/previews. A release can be design-sound while order-blocked on those
facts.

## 5. Handoff to the seal owner

Return a typed result containing the staged bundle identity, gate scoreboard,
design/order verdict inputs, unresolved operator items, and exact paths.
`pcb-design` owns review admission, the immutable seal, status-beacon refresh,
and publication. This procedure must not duplicate or abbreviate the normative
two-commit seal in the `07_releases` project contract.
