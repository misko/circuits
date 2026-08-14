# Stage 5 verification journal

## 2026-08-11 12:50 PDT — start

- did: entered the independent exact-routed-artifact review stage at commit `cc8368ffbb7b93cf8f4b567534e8537df792d638`.
- result: review subject board SHA-256 is `5480b2b2c0ed98f03d006b6fbd006bcfacd67215e15703f1d8d7926be5c8be65`; routing checkpoint remains KiCad DRC 0/0/0.
- next: generate conclusion-free pin dossiers and fresh routed renders, then run isolated pin, render, topology/protection and layout/thermal/power-integrity lenses.

## 2026-08-11 — schematic-readability backtrack

- did: submitted the exact delivered schematic PDF to a fresh-context
  readability review after electrical/PCB work was already advanced.
- result: rejected. The one-page native layout used approximately 2.1--2.5 pt
  text, weak functional grouping, no visible block headings or major active MPN
  identities, unexplained NCs, and large unused page area. Connectivity, ERC,
  parity and source section metadata were green; none measured whether a human
  could read the delivered artifact.
- time: native section experiments took about 6 seconds each and TSX rebuilds
  about 9--14 seconds, but the expensive part was the late process position:
  presentation work had to be reopened after placement/routing. Rendering six
  independently fitted pages from an already-built Circuit JSON takes under a
  second and does not need another TSX evaluation.
- changed process: added the early first-picture review, an exact multi-sheet
  Circuit-JSON PDF renderer, a mandatory hash-bound freeze readability review,
  and a content-hash checkpoint/resume boundary. The initial full run now stops
  for human review; `--resume-after-schematic-review` verifies the exact bytes
  and continues without rerunning nondeterministic TSX.
- general lesson: readability is an artifact property, not a source-code
  property. Review the real PDF at normal zoom as soon as the functional
  skeleton exists, then repeat on the exact freeze artifact. A human checkpoint
  also needs an identity-preserving resume path or the pipeline invalidates its
  own approval when it restarts.
- next: generate the canonical six-page PDF and electrical artifacts, inspect
  every page, then obtain fresh topology and readability verdicts on the exact
  hashes before resuming PCB generation.
