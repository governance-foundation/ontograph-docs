# OntoGraph Research

This folder is published at
https://governance-foundation.github.io/ontograph-docs/research/ and is authored
directly in this repository. Product documentation elsewhere on the site is
generated from the ontograph repository's `website/` folder, and the
`research/` subtree is reserved from that generator.

## What the page shows (updated 24 November 2026)

`index.html` presents OntoGraph's results on the nine files in the
[gUFO usage examples](https://nemo-ufes.github.io/gufo/examples/): per-example
results, coverage by UFO area, a portable re-check, how the results were
checked, open questions and related work. OntoGraph's own appointment case
follows, labelled as modelling under revision with its known issues listed.

- `gufo-examples-check/` holds the portable check (upstream inputs, OntoGraph
  outputs, pinned gUFO and gufoshapes, `expected.json`, `check.py`), and
  `downloads/gufo-examples-check.zip` is the same bundle as a ZIP. Run
  `python -m pip install -r requirements.txt && python check.py` inside it.
- `explorer/` is the read-only viewpoint explorer for the appointment case. See
  `explorer/README.md`.
- `downloads/` holds the October 2026 technical note, the reproduction archive
  (which needs the non-public OntoGraph runtime) and the recorded receipts.
- `evidence-index.json` lists every published artifact with its byte count and
  SHA-256 hash.

## Status and provenance

- The recorded gUFO examples run is from 9 October 2026 and lives in
  `../evidence/gufo-nine-examples-2026-10-09/`.
- Every review record here is an automated agent review. No human ontologist
  has reviewed this material yet.
- The technical note PDF predates the current page. It still carries a "Review
  candidate" header and can only be regenerated from the ontograph repository.
- Receipts under `downloads/reviews/` are historical and are not rewritten.
  `downloads/reviews/explorer/asset-checks.json` predates the 24 November 2026
  edits to `explorer/`.

## Preview

The pages are static and have no build step. To preview them, serve the
repository root:

```text
python -m http.server 8769
```

Then open http://127.0.0.1:8769/research/.