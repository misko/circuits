# Independent enclosure release stream

Enclosure publication is independent of PCB fabrication and firmware
publication.  A new enclosure release binds an existing immutable PCB release;
it never edits, reseals, or supersedes the bytes in `07_releases/`.

Use this stream for new releases:

```text
projects/<project>/
├── 07_releases/<pcb-version-date>/              immutable PCB parent
└── 07_enclosure_releases/
    ├── contracts.md
    └── <enclosure-semver>-<date>/                immutable enclosure release
```

Copy `assets/enclosure-release.contracts.md` to the project's
`07_enclosure_releases/contracts.md` when establishing a new stream.  Existing
hand-authored enclosure releases remain read-only.  The v2 publisher does not
rewrite them merely to adopt the new contract. Publication refuses a missing
or linked `contracts.md`; it never silently creates a contractless stream.

## Contents

1. [Prepared workspace](#prepared-workspace)
2. [Status composition](#status-composition)
3. [Publish transaction](#publish-transaction)
4. [Reopen verification](#reopen-verification)
5. [Manifest contract](#manifest-contract)

## Prepared workspace

Publish from a disposable, stable snapshot, not directly from mutable CAD
outputs while another process is generating them.  The prepared directory may
contain only these roots:

| Path | Content |
|---|---|
| `README.md` | actual readiness, open work, print and assembly notes |
| `source/**` | release-local enclosure configuration and input contracts |
| `cad/**` | exact authored CAD authority |
| `meshes/**` | printable STL payload; at least one STL is required |
| `renders/**` | declared visual-review evidence, never fit proof |
| `verification/**` | governing receipts and exact collision evidence |
| `tooling/**` | exact scripts required to resolve and regrade the release |
| `package/**` | optional self-contained transfer package |

`MANIFEST.json` and `authorities/**` are publisher-owned.  The prepared
workspace must not contain them.  Every directory and file must be ordinary:
symlinks, hard links, special files, empty extra directories, path traversal,
Unicode-normalization aliases, and case-fold aliases are rejected.

The configuration named by `--replay-config` must be below `source/` and must
already be rewritten for release-root (`.`) resolution.  Its parent manifest,
PCB, and STEP bindings use `authorities/pcb-release/...`; other bound inputs
use their released `cad/`, `source/`, or `verification/` paths.  The publisher
recursively checks every `{path, sha256, size}` mapping in this config against
an exact release payload and specifically requires all three parent-authority
bindings.  A copied config that still names live `07_releases/`, `06_build/`,
or `03_src/` paths therefore cannot publish.

Every `--replay-tool role=path` must name a unique ordinary file below
`tooling/`.  The manifest records `replay.root: "."` plus these exact config
and tool identities, so resolution is from the released tree rather than a
live project or skill checkout.

## Status composition

Declare at least one scope with `--scope name=STATUS`.  Typical component
scopes are `shell`, `board_retention`, and `antenna_accessory`.  The overall
status must equal the least-ready scope:

```text
INCOMPLETE < CAD_READY < PRINT_VERIFIED < THERMALLY_VERIFIED
```

Conservative aggregation means `shell=CAD_READY` plus
`antenna_accessory=INCOMPLETE` evaluates to overall `INCOMPLETE`. During the
current rollout, however, that mixed component claim is evidence only and is
not accepted by the publisher. An immutable candidate must declare every
required schema-v2 scope `INCOMPLETE`, use `--immutable-candidate`, and keep
`order_ready=false`.

The deployed publisher is intentionally capped at that boundary. It rejects
`CAD_READY`, `PRINT_VERIFIED`, `THERMALLY_VERIFIED`, and `--order-ready`, even
when caller-supplied scope strings appear consistent. Ready publication stays
disabled until the publisher accepts one governing schema-v2 scope receipt,
reopens all of its exact evidence, independently regrades the bound v1 CAD and
project-specific motion/physical checks, and recomputes the aggregate. This is
a fail-closed rollout boundary, not a claim that ready publication is
impossible in the future.

Scopes describe independently governed installed deliverables.  Do not add an
optional physical-validation scope merely to lower a legitimate `CAD_READY`
claim.  Instead, let the evaluator assign the component's achieved readiness
from its required automated and physical evidence.

## Publish transaction

Example for an enclosure derived from a fixed PCB release:

```bash
/usr/bin/python3 skills/pcb-enclosure/scripts/stage_enclosure_release.py \
  /tmp/project-enclosure-prepared \
  --project-root projects/<project> \
  --artifact-id project-enclosure \
  --version v0.4.1 \
  --date 2026-08-25 \
  --pcb-release v0.2.1-2026-08-14 \
  --pcb-manifest MANIFEST.txt \
  --pcb source/board.kicad_pcb \
  --step 3d/board.step \
  --status INCOMPLETE \
  --status-reason "Shell CAD passes; actual antenna fit remains unevidenced." \
  --scope shell=INCOMPLETE \
  --scope board_retention=INCOMPLETE \
  --scope antenna_accessory=INCOMPLETE \
  --scope thermal=INCOMPLETE \
  --replay-config source/enclosure-v2.yaml \
  --replay-tool compose=tooling/enclosure_v2.py \
  --replay-tool verify=tooling/verify_enclosure.py \
  --replay-tool collision=tooling/build_collision.py \
  --predecessor v0.4.0-2026-08-25 \
  --immutable-candidate
```

The publisher performs this closed transaction:

1. Validate metadata, the all-INCOMPLETE rollout boundary, the workspace
   census, and replay resolution before opening a staging directory.
2. Resolve exactly one `07_releases/<id>` parent and require its manifest to
   bind the selected PCB and STEP hashes.
3. Copy the exact parent manifest, PCB, and STEP beneath
   `authorities/pcb-release/` without writing anywhere in `07_releases/`.
4. Optionally copy and hash-bind the exact predecessor `MANIFEST.json` beneath
   `authorities/enclosure-predecessor/`.
5. Copy every prepared regular file; reopen the complete release-local
   schema-v2 config; derive its exact required-scope census; then generate a
   sorted full-file census and bind the replay config and tools.
6. Write schema-v2 `MANIFEST.json` and reopen the complete staging tree with
   the same verifier used after publication.
7. Recheck the prepared workspace, live parent, and optional predecessor
   identities; recheck case/Unicode destination aliases while holding the
   release-stream lock; then publish with one directory-relative atomic,
   no-replace rename.

The advisory lock serializes this publisher with other cooperating publishers.
The final alias census and `renameat2(RENAME_NOREPLACE)` still protect the exact
destination; a noncooperating same-UID process can create a different
case-folded sibling on a case-sensitive filesystem, so repository permissions
remain part of the publication boundary.

This transaction proves the integrity and replay layout of an INCOMPLETE
candidate. It does not promote caller-authored scope rows into ready evidence.

An existing destination always fails; it is never merged or overwritten.
Any failure before publication removes only the uniquely named staging
directory.  Correct a published release by incrementing the enclosure SemVer.

## Reopen verification

The ordinary release check is self-contained:

```bash
/usr/bin/python3 skills/pcb-enclosure/scripts/verify_enclosure_release.py \
  projects/<project>/07_enclosure_releases/<version-date>
```

It verifies every payload byte, the exact authority copies, parent-manifest
PCB/STEP declarations, conservative status composition, immutable-candidate
rules, predecessor copy, and release-local replay resolution.  It rejects any
missing, extra, linked, aliased, or unmanifested object.

Replay resolution proves that every file binding names exact release-local
bytes and that the declared tools are in the payload; the release verifier
does not execute those tools. Include each script's import/dependency closure
under `tooling/`, then run the release-local toolchain separately before
claiming that executable replay has succeeded.

Add `--project-root projects/<project>` to also compare the release against the
current external PCB parent and optional enclosure predecessor.  This external
comparison is an integrity audit, not a replay dependency: an extracted
release still reopens from its local authorities and tooling.

## Manifest contract

`MANIFEST.json` has `kind: pcb-enclosure-release-v2` and carries:

- independent `artifact_id`, enclosure `version`, `date`, and `release_id`;
- lifecycle, overall status, status reason, scoped statuses, and publication
  flags;
- exact source and release-local identities for the PCB manifest, PCB, and
  STEP;
- an optional exact predecessor manifest identity and local copy;
- exact release-root (`.`) replay config and role-to-tool identities;
- a sorted record for every ordinary payload file except `MANIFEST.json`.

The manifest deliberately does not claim firmware compatibility.  Compose PCB,
firmware, and enclosure identities only in a separate product-lock artifact.
