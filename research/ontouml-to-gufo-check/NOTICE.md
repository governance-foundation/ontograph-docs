# Notices

`comparison/*.ttl` and `vendor/gufo.ttl` are from gUFO
(https://github.com/nemo-ufes/gufo, commit
`f4122544133544eb4c6c467ba316302ab20b754a`) by João Paulo A. Almeida,
Giancarlo Guizzardi, Tiago P. Sales and Ricardo A. Falbo (NEMO/UFES). They are
licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/) and are
redistributed unchanged. The comparison Turtle files were not inputs to the
projection; they are included so differences can be inspected.

`vendor/gufoshapes.ttl` is `examples/common/gufoshapes.ttl` from the same gUFO
commit. That file is also distributed as gufoshapes (https://github.com/nemo-ufes/gufoshapes)
by João Paulo A. Almeida and Claudenir M. Fonseca (copyright 2026 João Paulo A.
Almeida, Claudenir M. Fonseca, Giancarlo Guizzardi and Tiago Sales), under
CC BY 4.0, and is redistributed unchanged. It is not the later gufoshapes
repository pin used in the October 2026 Turtle round-trip check.

The licence texts, with each project's copyright line, are in
`LICENSE-gufo-CC-BY-4.0.txt` and `LICENSE-gufoshapes-CC-BY-4.0.txt`.

`models/` and `outputs/` are OntoGraph-authored models and OntoGraph projections.
The outputs are not identical to the upstream Turtle. Instance files under
`models/*/instances.json` are OntoGraph-specific, because OntoUML has no
instance level.

`vendor/ontograph-temporal-shapes.ttl` and the files under `extensions/` are
an OntoGraph extension of example 05, not part of the upstream examples and
not part of the acceptance suite.

`check.py`, `expected.json`, `independent-review.json` and the accompanying
README files are provided so readers can verify the published results.
