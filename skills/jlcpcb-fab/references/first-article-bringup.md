# Staged first-article bring-up

Fabrication readiness is not first-power readiness. Before energizing a new
assembly, create `03_src/rules/first_article.yaml` from the power tree,
assembly rules, and footprints. It owns the population stage, exposed pads,
rail probe points, expected unpowered resistance, supply/current limit,
expected voltage/no-load current, and abort ranges.

```text
power tree + footprints + assembly rules -> first_article.yaml
physical inspection + meter readings ----> first_article.json
                                             |
                                             v
                                  AUTHORIZED | HOLD
```

Example:

```yaml
stages:
  - name: regulator-only
    installed: [F1, U2, U11]
    exposed_pads: [U2]
rails:
  - name: 5VA
    resistance: {probe: C17, min_ohm: 1000, max_ohm: 2500}
    voltage: {probe: C17, min_v: 5.0, max_v: 5.3}
    no_load_current: {probe: bench_supply, min_a: 0, max_a: 0.03}
    supply: {probe: bench_supply, min_v: 9.5, max_v: 12.2,
             max_current_limit_a: 0.05}
```

Record readings with explicit units and probe names in
`01_docs/journal/first_article.json`, then run:

```bash
python3 skills/jlcpcb-fab/scripts/first_article_check.py PROJECT \
  --json PROJECT/06_build/first_article_verdict.json
```

Missing evidence or an abnormal value is HOLD. Do not continue powering a
failed board to gather more evidence. Firmware is not generated or required by
this gate unless the project explicitly requests a separate firmware task.
