# Research appointments and shared personnel identity

Status: RD-2 source candidate for #2777; runtime outcomes are proposed until RD-4
executes these exact inputs. Bound to RDR-002, RDR-003, RDR-004 and RDR-007.

How can personnel identity and research staffing views describe the same people
without confusing a person with a temporary role, an appointment with a bare
edge, or a recorded membership with valid organisational authority?

The source explicitly declares Person and Organization as Kinds, Researcher as a
Role specializing Person, and Appointment as a Relator. Each appointment is
intended to mediate at least one Person and at least one Organization through
separately identified relations. Both target cardinalities are `1..*`, not
exact-one. A person or organization may have zero or more appointments.
These commitments are authored in the source, never inferred from names.

One person (`person:a`) has two overlapping appointments with `organization:one`.
A second person (`person:b`) shares the display label Research participant but
has no declared research membership. Equal labels prove neither equality nor
inequality. Mass qualities retain their own identities and bearers despite
equal decimal values (`70.0`, `70.00`). Both people participate in the Seminar
event through separately identified qualified facts. Mass and Seminar are
supporting contrasts for quality and event meaning, not staffing criteria.

At 10:30Z the source declares two active memberships. At noon the half-open
interval of the first has ended and only the second remains active. This comes
from separately supplied membership intervals, not an inferred role transition
from an appointment end date. An appointment-link query still lists both
recorded appointments at noon; it is not a temporal staffing query.

If the first appointment loses its organisation link, the intended finite
source grounding fails. The expected existing source validation is CWA-invalid
or OWA-unknown, while OWL consistency may remain true and generic SHACL is
expected to report nonconformance. Declared membership records remain present;
their number cannot establish valid staffing or rights and duties. Each of
these outcomes remains a proposed expectation, not an executed result here.

**Validation gap:** generated generic SHACL requires two total `gufo:mediates`
values. It does not independently enforce one class-correct participant on each
source relation. The source diagram's class-specific minima therefore require
separate source/oracle checks; a generic SHACL pass is insufficient.

## Inspect the source candidate

- [Conceptual diagram](conceptual.svg) and [complete text alternative](diagram.md).
- [Model](../../../fixtures/research-demonstration/organisation/model.json),
  [instances](../../../fixtures/research-demonstration/organisation/instances.json)
  and [frozen expectations](../../../fixtures/research-demonstration/organisation/expectations.json).
- [Dossier](case-dossier.json), [mapping records](mappings.json),
  [claim register](claims.json), [evidence index](evidence-index.json),
  [source register](sources.json), [gap register](gaps.json) and
  [license status](LICENSE.md).
- Fixture view DTOs: [conceptual](viewpoint-conceptual.json),
  [organisational](viewpoint-organisational.json), [OWL/gUFO](viewpoint-owl-gufo.json).

All identity rows currently have null candidateRef and canonicalRef. Source IDs
connect the views; proposed generated IRIs are expectations only. No source
candidate is asserted to be an accepted canonical entity. OWL/gUFO are purpose-
specific outputs, not the expressive ceiling of OntoGraph's canonical model.

The conceptual source retains source-grounded distinctions. The organisational
view foregrounds people, organisations, appointments and explicitly qualified
memberships; quality/event facts remain available rather than being erased.
The projected view is expected to retain mediation, quality bearers and source
IDs, while full modal identity, anti-rigidity and normative commitments remain
unproved. Qualified role and participation facts use composition vocabulary
alongside gUFO; they are not timeless class assertions.

No accepted enrichment is recorded: no Review/Decision/Promotion or authority
record exists for this candidate. Persistence, reasoning, source-assisted
reimport and actual query/diagnostic evidence belong to RD-4. A complete package
reproduction and independent semantic review remain required. No full C0-C7,
second-backend, expert-endorsement or production-publication claim is made.

## Questions for independent semantic review

1. Are the separate minimum-one mediation commitments suitable for this small
   appointment case, without adding an exact-one commitment?
2. What further evidence and commitments would be necessary to interpret these
   appointments as rights, duties or normative truthmakers?
3. Which reductions are acceptable for a staffing view while preserving the
   distinction between declared membership and validated grounding?
