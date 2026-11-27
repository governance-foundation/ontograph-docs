# OntoUML-to-gUFO check bundle

This bundle is the published evidence for OntoGraph's genuine OntoUML-to-gUFO
projection of the nine [gUFO usage examples](https://nemo-ufes.github.io/gufo/examples/).
It is described on the research page at
https://governance-foundation.github.io/ontograph-docs/research/.

## What was run

OntoGraph read OntoUML JSON models that were authored from the example prose
(not from the upstream Turtle), applied its UFO rules, and wrote gUFO. Instance
data is in a separate OntoGraph-specific file, because OntoUML has no instance
level. The upstream Turtle at gUFO commit `f412254` is a comparison target
only; the outputs are not required to be identical to it, and every difference
is classified in `diffs/`.

The retained run finished at 27 November 2026, 07:05:47 Australia/Sydney.
pySHACL 0.40.2 and Apache Jena 6.2.0 agreed on all nine cases. Pellet (via
owlready2 0.51) found all nine graphs consistent, including the two invalid
ones. Regenerating the outputs needs the OntoGraph runtime, which is not
public. This bundle checks the published outputs, not the pipeline that
produced them.

A separate October 2026 check, in `../gufo-examples-check/`, admits and
regenerates the upstream Turtle itself (808/808 assertions preserved). That is
not this result.

## Re-run the portable checks

```text
python -m pip install -r requirements.txt
python check.py
```

The script checks file hashes, the recorded UFO-rule findings and classified
diff counts, and runs pySHACL on each published output (gUFO plus the output,
no inference, advanced features on). It also checks the two OntoGraph
extensions of example 05, which are not acceptance cases. It does not run
Jena, Pellet, or OntoGraph.

## Layout

- `models/` — OntoUML model.json and instances.json for each of the nine cases
- `outputs/` — OntoGraph gUFO (`*.ttl`) and the same graph with IRIs mapped to the upstream namespace (`*.iri-mapped.ttl`)
- `comparison/` — upstream Turtle, comparison only
- `diffs/` — classified differences versus the upstream Turtle
- `findings/` — OntoGraph UFO-rule findings
- `oracles/` — recorded entailment, query and SHACL oracle results (Pellet is not re-run here)
- `run/` — retained run summary and per-case result records
- `vendor/` — `gufo.ttl` and `gufoshapes.ttl` from gUFO commit `f412254` (`gufoshapes.ttl` is `examples/common/gufoshapes.ttl` at that pin), plus OntoGraph's temporal extension shapes
- `extensions/` — OntoGraph extension of example 05 (`ogx:before`); not acceptance
- `reviewed-differences.v1.json` — each genuine content difference and its reason
- `cases.v1.json` — case catalogue and authoring provenance
- `independent-review.json` — honest provenance: no independent human ontologist review yet
- `expected.json` and `SHA256SUMS` — recorded hashes and expected verdicts
- `check.py` — the portable re-check

## Licence

Upstream Turtle, gUFO and gufoshapes are by the NEMO/UFES authors and are used
under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See `NOTICE.md`.
