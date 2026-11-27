# OntoGraph Research

This folder is published at
https://governance-foundation.github.io/ontograph-docs/research/ and is authored
directly in this repository. Product documentation elsewhere on the site is
generated from the ontograph repository's `website/` folder, and the
`research/` subtree is reserved from that generator.

## What the page shows (updated 27 November 2026)

`index.html` leads with the product frame: OntoGraph productises OntoUML into
one engine you load models (cartridges) into, feed data, and query. The
direction is a utility that drives grounded context for AI and can act as a
second brain; that assistant layer is marked as direction, not a shipped
capability. What the engine already does is load OntoUML (from authored JSON
or from Tonto via `ontograph-dsl-tonto`), apply UFO rules, project gUFO, merge
instance data, store the result, and answer checks and queries. The nine
[gUFO usage examples](https://nemo-ufes.github.io/gufo/examples/) are the
acceptance suite for that semantic core.

The page then takes three things in order: how each of the nine examples
played out, what we found (including Tonto 0.9.4 as a cross-check and the
three questions pending NEMO review), and how we executed it (architecture, a
walkthrough of example 01 from Tonto into a query on the projected graph, and
the dual-verdict format on example 05). The recorded evidence stays beneath:
UFO-rule findings, gufoshapes in pySHACL and Apache Jena 6.2.0, Pellet
consistency, classified differences from the upstream Turtle (a comparison
target only), the portable re-check, the OntoGraph-only temporal extension of
example 05, and open questions. The October 2026 Turtle admit-and-regenerate
result (808/808 assertions preserved) is kept on the page and clearly labelled
as a separate Turtle round-trip, not the headline. OntoGraph's own appointment
case follows, labelled as modelling under revision with its known issues
listed.

- `ontouml-to-gufo-check/` holds the projection evidence (models, instance
  files, outputs, diffs, findings, oracles, the retained run record, pinned
  gUFO and gufoshapes, `expected.json`, `check.py`), and
  `downloads/ontouml-to-gufo-check.zip` is the same bundle as a ZIP. Run
  `python -m pip install -r requirements.txt && python check.py` inside it.
  `independent-review.json` states honestly that there is no independent
  human ontologist review yet.
- `gufo-examples-check/` holds the earlier Turtle round-trip check (upstream
  inputs, regenerated outputs, pinned gUFO and gufoshapes, `expected.json`,
  `check.py`), and `downloads/gufo-examples-check.zip` is that bundle as a ZIP.
- `explorer/` is the read-only viewpoint explorer for the appointment case. See
  `explorer/README.md`.
- `downloads/` also holds the October 2026 technical note, the reproduction
  archive (which needs the non-public OntoGraph runtime) and the recorded
  receipts for that earlier work.
- `evidence-index.json` lists every published artifact with its byte count and
  SHA-256 hash.

## Status and provenance

- The recorded OntoUML-to-gUFO projection run finished at 27 November 2026,
  07:05:47 Australia/Sydney, and is published in `ontouml-to-gufo-check/`.
- The recorded Turtle round-trip run is from 9 October 2026 and lives in
  `../evidence/gufo-nine-examples-2026-10-09/`.
- Every review record here is either an automated agent review or a
  self-review. No human ontologist has reviewed this material yet. The
  October `downloads/organisation-independent-review.json` does not cover the
  OntoUML projection.
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
