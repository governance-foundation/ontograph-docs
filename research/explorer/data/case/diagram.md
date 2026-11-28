# Conceptual diagram text alternative

The diagram describes explicitly declared types, not live instances or accepted
canonical objects. Person and Organization are Kinds. Researcher is a Role
specializing Person; the triangle points from Researcher to Person. Appointment
is a Relator. Its person mediation leads to Person with target multiplicity
1..*; its organisation mediation leads to Organization with target multiplicity
1..*. Each reverse end has multiplicity 0..*. These independent minima do not
mean exactly one participant, and are not the same as generic SHACL minCount 2.

Mass is a Quality characterized by exactly one Person; a Person may bear zero
or more such qualities. Person participation in Seminar (an Event) has 0..*
at both model ends. Instances provide separate qualification intervals.

The source instance view contains person:a and person:b (same display label),
organization:one, appointment:one, appointment:two, quality:mass-a,
quality:mass-b, event:seminar, membership:one, membership:two,
participation:one and participation:two. Both appointments mediate person:a
and organization:one. Each membership names its own appointment and interval.
The qualities respectively inhere in person:a and person:b; participation
facts separately connect those people to event:seminar. No equality or
inequality is inferred from different IDs, equal labels or equal values.

Legend: boxes are source-declared classifiers; lines are source relations;
the hollow triangle marks specialization. Multiplicities describe source
commitments; runtime validation coverage must be inspected separately.
