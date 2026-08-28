# PCB project seed set

These templates are the project-independent source for a newly commissioned
board. Never seed from an existing project: a sibling carries product-specific
facts, exceptions, and historical contract drift.

## Commission through the executable manifest

Use the skill-owned commissioner rather than copying a hand-maintained list:

```bash
python3 skills/pcb-design/scripts/commission_project.py <name> \
  --brief-file /path/to/original-brief.txt \
  --signal-integrity ordinary \
  --assembly jlcpcb \
  --firmware forbidden \
  --target design
```

The script's closed scaffold plan is the executable manifest. It enumerates
every current template, validates the capability profile through the reference
router before writing, refuses symlinks and existing destinations, and removes
a partial new destination if a write fails. `tests/t1_pcb_commission.py` pins
the complete and conditional file census.

## Unconditional seed

The normal commission creates:

- project and stage `contracts.md` files for `01_docs` through `08_reviews`;
- nested contracts for decisions, journal, learnings, sourcing, rules, and
  project-local libraries;
- a navigation-only project `README.md` and `.gitignore`;
- the exact original prompt in `01_docs/BRIEF.md` with its SHA-256;
- `01_docs/capability-profile.json` plus architecture/status/checklist starters;
- a governed `01_docs/reports/` home for Markdown investigations;
- `01_docs/COMMISSIONING-HOLD.md`, a conductor-enforced hold that prevents
  either rebuild conductor from consuming schema examples as adopted design;
- sourcing policy and decision/journal/learning skeletons;
- `03_src/floorplan.yaml`, `route.yaml`, both canonical rebuild drivers, and
  the complete current rule-schema set, including the held
  `rules/connector_assemblies.yaml` connector/mate/tool/cable contract;
- empty governed homes for parts, TSX source, generated KiCad, firmware, build,
  PCB releases, and independent reviews.

The YAML values are explicit examples/placeholders. Their keys document the
schema; they do not become adopted design facts until commission replaces them
and the owning gate accepts them.

Both rebuild conductors compile `rules/connector_assemblies.yaml` before
producer or placement spend. Represented unknown mate/tool/cable/operation or
tolerance evidence exits `INCOMPLETE`; exact typed no-operated-connectors
evidence exits `N-A`. Neither fact-lock result is a realized-board
service-geometry pass; IMP-242 tracks the independent placement consumer.

## Conditional seed

- `--foreign-mating` adds `03_src/rules/mates.yaml`. Omit it when the board
  consumes no third-party geometry; an empty mating declaration is not proof.
- `--enclosure` adds the mechanical source contract, schema-v2 intent template,
  and independent
  `07_enclosure_releases/contracts.md` authority.
- RF still seeds `rules/rf.yaml`; its explicit `enabled` posture must agree
  with the capability profile and project source.
- Firmware remains an empty governed folder unless the profile says
  `requested`. A programmable part never changes that scope by itself.

## After commissioning

1. Read and complete `01_docs/BRIEF.md`; preserve the prompt and append later
   directives.
2. Resolve the capability profile with `skill_reference_router.py`.
3. Close commission fact locks and architecture decisions before authoring
   detailed source.
4. Replace every placeholder and run source/schema gates before expensive
   producers.
5. Treat `COMMISSIONING-HOLD.md` as spanning the separately typed commission,
   architecture, and sourcing admission stages. Remove it only in their
   reviewed admission change, then commit that boundary when the owning
   contracts/schema/source checks pass. Manual deletion is not evidence;
   IMP-235 tracks the missing executable admission compositor.

Heavy producers remain shared under `skills/kicad-pcb/scripts/`. A project
carries design source and configuration, not a copied backend.

## Validation

```bash
python3 tests/t1_pcb_commission.py
python3 scripts/contracts_audit.py --walk --root projects/<name>
```

When a template is added, changed, or made conditional, update the commissioner
and its census test in the same change. Documentation may summarize the seed;
it must not become a second copy manifest.
