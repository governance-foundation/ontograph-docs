# OntoGraph extension of example 05 (not acceptance)

These two cases extend the events example with a temporal order between the
semi-final and the final. They are an OntoGraph extension, not one of the nine
acceptance cases, and they are not compared with the upstream Turtle.

gUFO has no `before` property, so the extension records order as `ogx:before`
(`https://ontograph.dev/ns/gufo-ext#before`). The shapes in
`../vendor/ontograph-temporal-shapes.ttl` check that the stated dates do not
contradict that order.

- `05-events-ordering-ext` — the semi-final is before the final, and the dates agree.
- `invalid-05-events-ordering-ext` — the same `ogx:before` assertion, with dates that contradict it. gufoshapes still conforms; the extension shape does not.
