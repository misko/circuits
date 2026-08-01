# Independent RF schematic review protocol

Run this phase after the RF schematic/netlist is stable and **before placement**.
It answers whether the circuit can meet the RF contract; it does not judge
trace geometry or fabrication output.

## Independence and input

Use a fresh-context reviewer who did not author the circuit. Give only:

- `03_src/rules/rf.yaml`;
- BRIEF/ARCHITECTURE/DETAIL_DESIGN and relevant ADRs;
- exact schematic/netlist artifact named by `rf.reviews.schematic.artifact`;
- cited part dossiers/datasheets and reference designs.

Do not give prior review conclusions, journals, STATUS, or dispositions. The
reviewer derives the expected topology before comparing it with the artifact.

## Required examination

For every RF port and performance claim, independently verify:

1. complete source-to-load topology, DC bias path, terminations, switch states,
   unused-port behavior, and power-off behavior;
2. absolute maximum, linearity/compression, isolation, insertion-loss, noise,
   and ESD/protection budgets over the declared band and corners;
3. package pin numbers/functions against the primary datasheet figure;
4. whether every vendor-mandated matching/bias/decoupling element is present,
   correctly valued, and connected on the intended side of series elements;
5. each `performance_claim` has a numeric acceptance and reproducible evidence;
6. the declared risk tier follows electrical length/performance sensitivity,
   not merely the fundamental clock or nominal carrier frequency.

## Output contract

Archive the review verbatim in `08_reviews/` at the path declared in
`rf.yaml`. Header:

    review_kind: RF_SCHEMATIC
    subject: <project + artifact>
    reviewer: <identity/model>
    independence: independent-from-design-author
    source_commit: <full 40-character SHA>
    artifact_sha256: <SHA256 of exact schematic/netlist artifact>
    design_verdict: SOUND | DEFECTIVE

Then include exactly one line for every declared schematic requirement ID:

    requirement: RF-SCH-... PASS | FAIL

`rf_contract_check.py --require-review schematic` derives the denominator from
`rf.yaml`, rejects zero/partial/duplicate coverage, and verifies the artifact
hash. Any FAIL or `DEFECTIVE` returns the design to schematic work.
