stage: architecture/component-selection backtrack
step: "finish exact pin/layout dossiers and module-first exceptions for the replacement power architecture before schematic regeneration"
measure: "MEASURED five replacement MPNs pass the >10-stock two-authorized-supplier pre-selection gate; the LTC3889/CSD18533/TPS259823/LTC4372 path has 75.005 mV static connector margin. A newly found rating mismatch is upstream-owned: live input FET AON6354 is 30 V, not the 60 V asserted by protection_paths.yaml, and cannot remain exposed to the 38.9 V clamp. P-MOD remains red until exact dossiers, bare-IC exception evidence, and live-source retirement of LM5116 are complete. No schematic, layout, or release claim is green."
state: active
next: "complete official pin/equation/layout evidence; use the qualified 60 V CSD18533 in every clamp-exposed FET position; update integration and declarative electrical rules; require P-MOD and early-design gates green before changing placement"
op_pid: none
updated: 2026-08-01T20:39:51-07:00
