# circuits

Agent skills for taking a PCB from generator scripts to a fab-ready, ordered
board — written for [Claude Code](https://claude.com/claude-code), usable as
plain documentation by anyone.

These are not tutorials. Every claim in them was paid for by a real failure on
a real board (a 136-part, 4-layer rover power board, 2026-07): bugs that
shipped silently past DRC, routers that produced fuses instead of traces,
assembly previews that lied. The skills exist so the next board doesn't
rediscover them.

## The two skills

| Skill | Covers |
|---|---|
| [`kicad-pcb`](skills/kicad-pcb/) | Schematic generation, placement, routing, verification. 11 golden rules, 7 reference docs, 4 project-agnostic scripts. |
| [`jlcpcb-fab`](skills/jlcpcb-fab/) | Fab outputs and ordering: gerber/BOM/CPL export, live JLCPCB stock checks, part-spec confirmation, CPL rotation correction. |

## The model: KiCad as a library, not a GUI

Nothing here opens eeschema or pcbnew to draw. The design is **code**:

- The schematic is *generated* — a Python script emits `.kicad_sch`
  s-expressions from a component/net table.
- The board is *generated* — a script drives the `pcbnew` Python API to load
  footprints and place them from a floorplan.
- Routing is **not** KiCad's job (it has no autorouter) — it is
  [KiCadRoutingTools](https://github.com/drandyhaas/KiCadRoutingTools),
  invoked with the exact command lines recorded in
  [`references/routing-pipeline.md`](skills/kicad-pcb/references/routing-pipeline.md).
- KiCad's remaining roles: the `pcbnew` API (geometry, exact collision, zone
  fill) and `kicad-cli` (headless DRC/ERC, netlist export, plotting).

Because the design is code, it is diffable, reviewable, and regenerable. The
corollary — and the source of most of the failures below — is that a generator
bug becomes a physical defect silently.

## What this catches that nothing else does

Every one of these passed DRC, passed connectivity, and was electrically
self-consistent. All were found by a human question or a cross-check, not a
tool:

- A part in the schematic that never reached the board (one silent `print` in
  a generator). Fix: missing footprint is a hard error, plus
  `kicad-cli pcb drc --schematic-parity` in the gate list.
- Three polarized parts wired backwards — including the battery connector,
  which would have made every board dead on arrival. KiCad footprints put the
  **cathode on pad 1**; generic `1`/`2` symbols let the author guess wrong.
- Two 6 A buck switch nodes routed at 0.15 mm — fuses, not traces. No tool
  checks ampacity by default. Fix: current-tiered netclasses with
  `.kicad_dru` minimum-width rules, defined **before** routing.
- Mounting holes underneath connector shells (no screw access).
- BOM parts matched by value string that were the wrong voltage, the wrong
  package, or an entirely different component (a motor driver proposed as an
  ideal-diode controller; a thermistor coded as a plain resistor).

## Install

These follow the standard skill layout — `SKILL.md` frontmatter for
discovery, `references/` and `scripts/` read only when needed — so they work
in any agent that supports it. Only the install path differs:

```bash
git clone https://github.com/misko/circuits

# Claude Code   (project-scoped: .claude/skills)
mkdir -p ~/.claude/skills && cp -r circuits/skills/* ~/.claude/skills/

# Codex         (repo-scoped: .agents/skills)
mkdir -p ~/.agents/skills && cp -r circuits/skills/* ~/.agents/skills/
```

Either agent picks a skill up implicitly when a task matches its
`description`, or on explicit request.

The scripts need the KiCad-bundled interpreter (a `python3` where
`import pcbnew` works); each takes `--help`-documented arguments and none
hardcodes a board. Routing additionally needs a KiCadRoutingTools clone.

Verified on KiCad 7.0.x and re-validated on 10.0.4; version deltas are noted
in the skills.

## Scope

These cover **generate → route → verify → order**. Turning an English
requirement into an architecture and a part selection is *not* covered — that
remains expert work, documented per project.
