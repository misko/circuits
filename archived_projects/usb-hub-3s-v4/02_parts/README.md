# Stage 1 evidence exceptions

Every selected complex or polarity-sensitive part has an immutable fact dossier.
Vendor PDFs are pinned beside the dossier. Where the manufacturer's primary
endpoint rejected automation, the exact manufacturer-authored document was
retrieved through the selected LCSC code's catalog mirror and its bytes were
hashed locally. This applies to Littelfuse SMBJ15A (`C83846`) and Phoenix Contact
1715022 (`C3817933`); their dossiers retain the primary manufacturer URL and
record the mirror provenance instead of disguising an access failure as a
missing authority.

Stock counts and price are intentionally not copied into dossiers because they
change. The dated live catalog response and the final 16/16 candidate report are in
`../06_build/cache/`; the JLC order uploader remains the final assembly-allocation
authority.
