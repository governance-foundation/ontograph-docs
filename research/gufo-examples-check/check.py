#!/usr/bin/env python3
"""Re-check OntoGraph's results on the gUFO usage examples with RDFLib and pySHACL.

For each of the nine example files this script checks that:
  1. every file matches the SHA-256 recorded in expected.json;
  2. OntoGraph's output graph is isomorphic to the upstream input
     (every source assertion preserved, nothing added or lost);
  3. pySHACL with the pinned gufoshapes, run the way the gUFO examples'
     own test suite runs it (gufo.ttl + the example, inference "none",
     advanced=True), gives the expected verdict and exactly the expected
     violations for OntoGraph's output, and the same verdict for the
     upstream input. Violation messages are compared after removing the
     angle brackets the recorded (Apache Jena) run put around IRIs.

It does not run an OWL 2 DL reasoner (that needs Java and Pellet) and does
not run OntoGraph itself. Usage:  python check.py  [--json results.json]
Exit code 0 means every expectation was reproduced.
"""
import argparse, hashlib, json, sys
from collections import Counter
from pathlib import Path

try:
    import rdflib
    import pyshacl
    from rdflib.compare import isomorphic
    from rdflib.namespace import RDF, SH
except ImportError:
    sys.exit("Missing dependencies. Run:  python -m pip install -r requirements.txt")

HERE = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(*paths):
    graph = rdflib.Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def violations(data_graph, shapes):
    conforms, report, _ = pyshacl.validate(
        data_graph, shacl_graph=shapes, inference="none", advanced=True)
    found = []
    for result in report.subjects(RDF.type, SH.ValidationResult):
        value = lambda p: report.value(result, p)
        text = lambda p: None if value(p) is None else str(value(p))
        found.append({"focusNode": text(SH.focusNode), "resultPath": text(SH.resultPath),
                      "value": text(SH.value), "message": text(SH.resultMessage)})
    return conforms, found


def key(v):
    # Jena writes IRIs in messages as <iri>; pySHACL writes them bare.
    message = (v["message"] or "").replace("<", "").replace(">", "")
    return (v["focusNode"], v["resultPath"], v["value"], message)


def short(text):
    return text.replace("https://purl.org/nemo/gufo-examples/", "ex:").replace("<", "").replace(">", "")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", help="also write machine-readable results to this file")
    args = parser.parse_args()
    expected = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))

    problems = []
    for pin in ("gufo", "gufoshapes"):
        if sha256(HERE / expected[pin]["file"]) != expected[pin]["sha256"]:
            problems.append(f"{expected[pin]['file']}: SHA-256 differs from the pinned {pin} commit")
    gufo = load(HERE / expected["gufo"]["file"])
    shapes = load(HERE / expected["gufoshapes"]["file"])

    rows, results = [], []
    for case in expected["cases"]:
        name = case["id"]
        inp, out = HERE / case["input"], HERE / case["output"]
        for path, digest in ((inp, case["inputSha256"]), (out, case["outputSha256"])):
            if sha256(path) != digest:
                problems.append(f"{path.relative_to(HERE)}: SHA-256 differs from expected.json")
        source, generated = load(inp), load(out)
        preserved = isomorphic(source, generated)
        if not preserved or len(source) != case["sourceAssertions"]:
            problems.append(f"{name}: output is not isomorphic to the upstream input")
        out_conforms, out_violations = violations(gufo + generated, shapes)
        in_conforms, in_violations = violations(gufo + source, shapes)
        exact = Counter(map(key, out_violations)) == Counter(map(key, case["expectedViolations"]))
        if out_conforms != case["expectedConforms"] or not exact:
            problems.append(f"{name}: SHACL result differs from the recorded OntoGraph result")
        if in_conforms != out_conforms or len(in_violations) != len(out_violations):
            problems.append(f"{name}: upstream input and OntoGraph output disagree")
        verdict = "conforms" if out_conforms else f"{len(out_violations)} violation(s)"
        rows.append((name, "valid" if case["expectedValid"] else "invalid", f"{len(generated)}/{len(source)}",
                     verdict, "yes" if (exact and out_conforms == case["expectedConforms"]) else "NO"))
        results.append({"id": name, "triplesSource": len(source), "triplesOutput": len(generated),
                        "isomorphic": preserved, "conforms": out_conforms,
                        "violations": out_violations, "upstreamInputConforms": in_conforms,
                        "upstreamInputViolations": len(in_violations), "matchesExpected": exact})

    header = ("Example", "Expected", "Assertions out/in", "gufoshapes (pySHACL)", "Matches record")
    widths = [max(len(str(r[i])) for r in rows + [header]) for i in range(len(header))]
    line = lambda r: "  ".join(str(c).ljust(w) for c, w in zip(r, widths))
    print(line(header)); print(line(["-" * w for w in widths]))
    for r in rows:
        print(line(r))
    for r in results:
        for v in sorted(r["violations"], key=key):
            print(f"  {r['id']}: {short(v['message'])}")
    total_in = sum(r["triplesSource"] for r in results)
    preserved = sum(r["triplesOutput"] for r in results if r["isomorphic"])
    valid = [r for r, c in zip(results, expected["cases"]) if c["expectedValid"]]
    invalid = [r for r, c in zip(results, expected["cases"]) if not c["expectedValid"]]
    print()
    print(f"Assertions preserved: {preserved}/{total_in}")
    print(f"Valid examples conforming: {sum(r['conforms'] for r in valid)}/{len(valid)}")
    print("Invalid examples flagged: " + ", ".join(f"{r['id']} = {len(r['violations'])} violations" for r in invalid))
    print(f"rdflib {rdflib.__version__}, pySHACL {pyshacl.__version__}")
    if args.json:
        Path(args.json).write_text(json.dumps({"results": results, "problems": problems}, indent=2) + "\n", encoding="utf-8")
    if problems:
        print("\nNOT REPRODUCED:"); [print("  - " + p) for p in problems]
        return 1
    print("\nAll expectations reproduced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
