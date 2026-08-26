# Commission learnings

## Product names do not define interface scope

- what happened: “USB hub v4” admitted two materially different products; one clarification removed every USB data/PHY/differential-routing obligation and fixed the safety/manufacturing boundary before generation.
- root cause: The commission instructions lock power envelopes but do not require a connector-role matrix distinguishing power, data, control, negotiation and mechanical-only pins.
- avoid next time: Add a D-INTERFACE-SCOPE commission row for every external connector and make “USB” explicitly choose data role, power role, charging advertisement, PD role and standards claim.
- candidate-canon: yes — D-INTERFACE-SCOPE in the commission fact-lock and `requirements.yaml` guidance.

## The canonical seed inventory has drifted

- what happened: The actual template tree contains `rebuild_reuse.sh` and nine unconditional rule schemas, but the SKILL copy list omits `assembly.yaml` and `rf.yaml`; the template README's command list also omits `rebuild_reuse.sh`, `requirements.yaml`, `power_stages.yaml`, `protection_paths.yaml`, `integration.yaml`, `assembly.yaml` and `rf.yaml`. The project contract requires `DETAIL_DESIGN.md` and root `README.md`, but there is no canonical seed for either.
- root cause: The commission inventory is duplicated as prose in the SKILL, template README and contracts, with no executable equality check against the template filesystem and required-file set.
- avoid next time: Generate the copy manifest from one machine-readable list and gate required templates, executable modes and destination paths. Add project-independent `DETAIL_DESIGN.md` and project `README.md` seeds.
- candidate-canon: yes — M-COMMISSION-SEED, a test that compares the declared manifest, template tree and required contract paths.

## Value-bearing example configs are expensive and unsafe commission seeds

- what happened: Seventeen canonical files copied successfully, but several contained another board's cook-loadcell or generic power-example values. Most Stage 0 effort was spent replacing convincing-looking anchors, nets, rails and routes with explicit v4 blockers; the gate commands themselves all completed in about one second or less.
- root cause: One file serves two incompatible purposes: explanatory worked example and new-project seed. Copying it creates a superficially complete foreign design until every value is found and removed.
- avoid next time: Separate worked examples from a zero-value, fail-closed scaffold generated with the new board name. Gate copied config for foreign project tokens and unresolved sample identifiers before the first commit.
- candidate-canon: yes — M-COMMISSION-ZERO-VALUE plus a foreign-token scan in a `commission_project` helper.

## Prompt integrity should not be hand-calculated

- what happened: The correct initial digest was changed after a nested timing harness expanded the `$d` in the documented sed expression and falsely reported another digest. An independent structured comparison caught the harness defect before commit and restored the original value.
- root cause: Prompt quoting/newline normalization and digest calculation are described as a shell pipeline; wrapping that pipeline inside another shell makes its `$` syntax context-sensitive, and the command only prints a digest rather than comparing it with the recorded field.
- avoid next time: A commission helper should write the marker body and digest together, then a dedicated `brief_contract_check.py` should parse and compare the stored field without shell quoting.
- candidate-canon: yes — M-BRIEF-HASH with an equality verdict and a regression for the final-newline rule.

## The no-mating declaration depends on hidden literal wording

- what happened: `import_provenance_check.py` failed “does not currently mate rigidly” but passed “does not mate”; both sentences express the same explicit no-mating decision.
- root cause: Applicability is inferred by a narrow regular expression over prose rather than a structured field or a robust explicit-none marker.
- avoid next time: Put mating applicability in a machine-readable commission field, or accept the contract's `none —` form without requiring one exact phrase.
- candidate-canon: yes — D-MATE-NONE regression covering semantically equivalent explicit-none wording.

## Fail-closed bounded entry worked

- what happened: With architecture intentionally unresolved, `rebuild_all.sh` exited at P-MOD in 0.05 s and never launched schematic generation or routing.
- root cause: No defect in this run; the first-stage gate and bounded-driver ordering did what the pipeline intends.
- avoid next time: Preserve P-MOD and early-design checks ahead of all generators, and keep route blockers/timeouts explicit in the per-board config.
- candidate-canon: no — already canonical behavior; this run is positive regression evidence.
