# OntoGraph on the gUFO usage examples: portable check

This bundle lets you re-check OntoGraph's recorded results on the nine files in
the [gUFO usage examples](https://nemo-ufes.github.io/gufo/examples/) (seven
example ontologies plus the two deliberately invalid variants for examples 1
and 7) without installing OntoGraph.

## Run it

Python 3.9 or later:

```sh
python -m pip install -r requirements.txt
python check.py
```

The script exits with status 0 and prints `All expectations reproduced.` when
every expectation in `expected.json` holds. `python check.py --json results.json`
also writes the per-example results.

## What it checks

For each example the script:

1. checks the SHA-256 of every file against `expected.json`;
2. checks that OntoGraph's output (`outputs/*.ontograph.ttl`) is isomorphic to
   the upstream input (`inputs/*.ttl`), so every source assertion came back
   with nothing added or lost (808 assertions in total);
3. runs pySHACL with the pinned gufoshapes the same way the gUFO examples' own
   test suite does (`gufo.ttl` plus the example, `inference="none"`,
   `advanced=True`). It checks that OntoGraph's output gives the expected verdict
   and exactly the expected violations, and that the upstream input gives the
   same verdict.

Expected result: the seven valid examples conform, `01-endurant-types-invalid`
has 2 violations and `07-higher-order-types-invalid` has 5.

## What it does not check

- **OWL 2 DL reasoning.** The recorded OntoGraph run checked OWL consistency
  with Pellet, and all nine files were consistent, including the two invalid
  ones. Reproducing that step needs Java and a DL reasoner, for example
  the examples' own test harness in the gUFO repository (owlready2 + Pellet).
- **OntoGraph itself.** The outputs here were produced by the OntoGraph runtime
  (source commit `1c3e2f7d4f1957cf6061b7f03386e3adaf9758e5`, binary SHA-256
  `688c5fc66d6b61963877fe5bd29324938f3cb03216eec58e0994137e0ee34a9d`) on
  9 October 2026. That runtime is not publicly distributed yet, so this bundle
  checks the published outputs and doesn't regenerate them.
- **An OntoUML-to-gUFO transformation.** The inputs are gUFO Turtle files. This
  tests that OntoGraph admits and regenerates them without semantic loss. It
  doesn't test how OntoGraph would project an OntoUML model into gUFO.

## Contents

| Path | What it is |
| --- | --- |
| `inputs/` | The nine upstream example files, unchanged, from gUFO commit `f4122544133544eb4c6c467ba316302ab20b754a` |
| `outputs/` | OntoGraph's regenerated graph for each example (N-Triples, which is valid Turtle) |
| `vendor/gufo.ttl` | gUFO at the same commit |
| `vendor/gufoshapes.ttl` | gufoshapes at commit `b95e14b034c93c42323e8beb8c08f697b026e553` |
| `expected.json` | Hashes and expected results, taken from the recorded run's per-example oracles |
| `check.py` | The check script |
| `SHA256SUMS` | Checksums for every file in the bundle |
| `NOTICE.md`, `LICENSE-*.txt` | Attribution and CC BY 4.0 licence texts |

The recorded run used Apache Jena for SHACL, and this script uses pySHACL. The
two tools produce the same violations. The only difference is that Jena writes
IRIs inside messages as `<iri>`, so messages are compared with the angle
brackets removed.
