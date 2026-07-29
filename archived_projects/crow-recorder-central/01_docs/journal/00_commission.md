# journal — 00_commission

## 2026-07-21 21:17 — start
- did: commissioned alongside crow-mic-pod (skeleton from SKILL templates, BRIEF with condensed-prompt UNVERIFIED marking, ADR-0000 scope split); D-SPEC sourcing spike run at commission for all spec-critical central parts
- result: TENSIONS (live JLC stock 2026-07-21, cached at 06_build/cache/dspec_stock_spike_2026-07-21.txt): XU316-1024-TQ128-I24 stock=0 (T1, consign/global-sourcing plan), FA-238 24MHz stock=0 (T2, Digi-Key fallback), TCR2LF18 stock=0 (T3, alternate search due); T4 fab-tier pre-declared 6L+small-via (archive ADR-0008/0009 proved 4L does not close the XU316 escape). All other criticals stocked: PCM1865 1674, USB4105 3958, NC7NZ34 1508, AP61102 455, XC6227 268, SHT40 13.8k, W25Q16 102k, TPD4EUSB30 6k
- next: pod releases first (ADR-0000); then adopt archived crow-array-central under an ADR-0005-style provenance rule, re-verify everything, resolve T1-T3 at parts stage with fresh alternates search

## note — successor resume pointers (written by the commissioning session)
- Archive precedent: archived_projects/crow-array-central (sealed v1.0-2026-07-18, 6L, DRC 0/0/0 w/ 2 waived Zone-Zone slivers, ADR-0010). Its promoted route artifact is the FULL final board (03_src/route/final.kicad_pcb, 3.7MB) copied to 04_kicad by rebuild_all.sh — verify it reproduces (the POD archive's promoted chain was STALE; check for the same defect FIRST: run its chain into 06_build/proof and diff DRC).
- Adoption path proven on the pod: skeleton from SKILL templates (done), ADR-0005-style provenance ADR, import 01_docs design docs + 02_parts + 03_src with rename crow_array_central->crow_recorder_central, re-run every gate.
- Parts stage MUST resolve commission tensions T1-T3 (XU316/FA-238/TCR2LF18 all JLC stock=0 on 2026-07-21) with a fresh alternates/consign decision ADR + D-TIER ADR for 6L+small-via (T4). RJ45 map interop authority = pod 01_docs/decisions/0004 (contact-for-contact).
- P-ESC will fail on archive-era part.yamls without escape blocks — compute with skills/kicad-pcb/scripts/escape_check.py (see pod part.yamls for the pattern); XU316 TQFP-128 0.4mm needs the D-ESC/via-in-pad block from archive ADR-0009.
