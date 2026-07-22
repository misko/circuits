# learnings — routing

- issue: archived crow-array-pod's committed route artifact (03_src/route/r3.kicad_pcb, sha f9684a7…) does not reproduce its sealed v1.1 board — it is the pre-J1-rot-90-fix route; the post-fix re-route lived only in gitignored 06_build/route/ and evaporated. Rebuild from the archive's own sources yields DRC 41/12.
  root cause: promotion (canon 3g) happened once at the first route and was not repeated after the v1.1 fix re-route; no gate compares the promoted chain against the sealed board.
  avoid next time: at release, verify the promoted chain REPRODUCES the sealed board (rebuild_all from a clean 06_build must hit 0/0/0 before seal — a "reproducibility gate"). candidate-canon: yes (suggested M3-REPRO: release gate = fresh-rebuild DRC equals sealed DRC).
