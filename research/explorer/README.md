# Read-only research viewpoint explorer

Preparation for product issue governance-foundation/ontograph#2781 under epic
#2774; RDR-003, RDR-014, RDR-015, RDR-016 and RDR-017. **Do not merge this PR
before the coordinator's final publication decision:** destination `develop`
automatically publishes GitHub Pages.

This standalone, dependency-free browser surface reads exact copies of the
accepted RD-2 source dossier at
`a4d01ef7503ecba2b809bb7e03e3241f8c3a7123`. It does not reinterpret that dossier
as accepted canonical state. Source model and instance identity remain separate;
selecting a declared type explicitly changes identity instead of equating a type
with its instance. The 31 identity rows are inspected across conceptual,
organisational and OWL/gUFO views; absent same-identity rows remain explicit.

The source DTO copies are byte-identical Git blobs. Their original proposed
claims and review states remain immutable historical producer records. Later
recorded observations appear separately and must bind the same source hashes;
they never globally relabel all displayed identities as executed or accepted.
The source figure/text alternative and full source records are available
without inferring missing conceptual commitments from labels.

## Reader interactions and failure behavior

- Keyboard-accessible tabs support arrows, Home and End; all record selections
  are native buttons. An accessible table exposes every substantive view record.
- Selection uses stable source IDs, survives view/filter changes, and is encoded
  in the URL for browser back/forward and deep links. Unknown IDs stay unresolved.
- No-match filters preserve the selection and expose a clear/reset action.
- The inspector shows source pointers/records, identity domain and lifecycle,
  expected generated IRIs, mappings/reductions, unchanged claim status and gaps.
- A person and a separately identified declared type can be traced explicitly.
- Loading verifies every listed asset's byte count and SHA-256 before display,
  then validates source pointers, unique IDs and DTO references. A missing file,
  digest mismatch or incompatible reference fails closed with no partial view
  and a retry action. Secure-context Web Crypto is required (HTTPS or localhost).
- The browser issues static asset GETs only. It has no live mode, service
  endpoint, write command, storage adapter, admission or semantic authority.

Generic generated SHACL counts total `gufo:mediates` values, while the source
declares independent class-specific minimum-one mediation constraints. That
validation gap remains visible. No canonical dataset/revision, full C0–C7
acceptance, arbitrary inverse, normative appointment authority or expert
endorsement is invented.

## Asset and observation contracts

`data/manifest.json` is an explorer-owned asset index, schema
`ontograph.research.explorer-assets.v1`. Each copied producer file retains its
original repository path, source commit, exact byte count/digest and undeclared
project-data license status. The manifest excludes its own recursive digest;
the external PR/review/package index binds it.

An optional `recordingRef` names a checksum-bound `recording.json` with schema
`ontograph.research.explorer-recording.v1`: sourceCommit, runtimeIdentity
(sourceCommit and binarySha256), inputDigests (model, instances, expectations),
cases (id, sourceOutcome, owlConsistent, shaclConforms, activeRoleIds,
organisationAppointments, evidenceHref), receiptHref and limitations. A recorded
overlay must match source digests and link actual retained evidence. It supplies
neither a canonical revision nor a live connection. Until supplied, fixture
mode is explicit and no actual outcome is shown.

Data and authored SVG license grants remain **UNLICENSED / undeclared**; the
[original case notice](data/case/LICENSE.md) is retained. No third-party artwork,
framework or font distribution is bundled. Scholarly vocabulary references keep
their separate pins/notices; they do not license project-owned fixtures.

## Local checks and preview

The sibling research home belongs to preparation PR
governance-foundation/ontograph-docs#8 at
`3c9ea11b53676aeea78db300e658aad785f71a0b`; it is read-only to this lane. Preview
assembles its `research/index.html` and `styles.css` with this explorer in a
disposable local staging tree. These are separate branches from integrated
`develop`, never stacked delivery branches. The eventual `../` research link
requires coordinated integration of both prepared surfaces.

Serve the assembled static root on localhost. The development-only browser
harness `check.cjs` requires Node, Playwright and its Chromium browser:

```text
EXPLORER_URL=http://127.0.0.1:8769/research/explorer/
node research/explorer/check.cjs
```

Set `PLAYWRIGHT_MODULE` only if Playwright is installed outside normal module
resolution; `EXPLORER_REVIEW_DIR` selects a fresh output directory. The harness
does not install software or publish anything. It exercises desktop/mobile
selection, tab keyboard controls, cross-view absence, source/type tracing,
filter/no-match recovery, browser history, unknown IDs, digest failure/retry
and missing-manifest failure. Screenshots and the author receipt live in
[review/](review/checks.json). These are local author checks, not independent
acceptance or full accessibility certification. Independent review must bind
the exact final pushed source and recorded-observation bytes.

Only `research/explorer/**` is owned here. Research home, downloads, source
runtime, Console and restricted pilot programs remain untouched.
