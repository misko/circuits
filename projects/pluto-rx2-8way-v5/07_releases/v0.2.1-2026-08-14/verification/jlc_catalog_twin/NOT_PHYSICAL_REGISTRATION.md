# JLC catalog twin limitation

This directory retains JLC catalog CAD for code, land-pattern, drill and
supplier-preview diagnostics. It is not physical-registration proof for
C429844 / Amphenol 901-143-6RFX.

The converted JLC WRL has a wrong internal XY origin. The catalog overlay's
green expected envelope and pink measured pixels are both derived from that
same mesh, so their agreement can coexist with a 5.731-mm courtyard excursion.
That is the regression mechanism, not evidence that the PCB holes moved.

The blocking physical evidence is in `../sma_native_registration/`. It binds
the native manufacturer STEP by SHA-256 and independently compares the measured
body, F.Fab, F.CrtYd and every drilled attachment centre. J2–J10 pass 9/9 model
instances and 45/45 drilled centres.
