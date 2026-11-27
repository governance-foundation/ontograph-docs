#!/usr/bin/env python3
"""Re-check the published OntoUML-to-gUFO projection outputs with RDFLib and pySHACL.

This script does not run OntoGraph, Apache Jena, or Pellet. It checks that:

  1. every published file named in expected.json still has the recorded SHA-256;
  2. the recorded UFO-rule finding counts and rule ids are still in findings/*.json,
     and that published diff summaries still have zero unclassified differences;
  3. pySHACL with the pinned gufoshapes, run the way the gUFO examples' own
     test suite runs it (gufo.ttl + the OntoGraph output, inference "none",
     advanced=True), gives the expected verdict and exactly the expected
     violations for each of the nine acceptance outputs;
  4. for the two OntoGraph extensions of example 05 (not acceptance cases),
     gufoshapes still conforms and the OntoGraph temporal shapes give the
     expected verdict.

Violation messages are compared after removing the angle brackets that Apache
Jena sometimes puts around IRIs.

Usage:  python check.py  [--json results.json]
Exit code 0 means every expectation was reproduced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

try:
    import rdflib
    import pyshacl
    from rdflib.namespace import RDF, SH
except ImportError:
    sys.exit("Missing dependencies. Run:  python -m pip install -r requirements.txt")

HERE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(*paths: Path) -> rdflib.Graph:
    graph = rdflib.Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def violations(data_graph, shapes):
    conforms, report, _ = pyshacl.validate(
        data_graph, shacl_graph=shapes, inference="none", advanced=True)
    found = []
    for result in report.subjects(RDF.type, SH.ValidationResult):
        def value(p):
            return report.value(result, p)

        def text(p):
            return None if value(p) is None else str(value(p))

        found.append({
            "focusNode": text(SH.focusNode),
            "resultPath": text(SH.resultPath),
            "value": text(SH.value),
            "message": text(SH.resultMessage),
            "sourceShape": text(SH.sourceShape),
        })
    return conforms, found


def blank(value):
    if value in (None, "None", "none", ""):
        return None
    return value


def key(v):
    message = (v.get("message") or "").replace("<", "").replace(">", "")
    return (blank(v.get("focusNode")), blank(v.get("resultPath")), blank(v.get("value")), message)


def short(text: str) -> str:
    return (
        (text or "")
        .replace("https://ontograph.dev/examples/gufo-examples/", "ex:")
        .replace("https://purl.org/nemo/gufo-examples/", "ex:")
        .replace("<", "")
        .replace(">", "")
    )


def check_hash(problems, path: Path, digest: str, label: str) -> None:
    if not path.is_file():
        problems.append(f"{label}: missing file {path.relative_to(HERE)}")
        return
    if sha256(path) != digest:
        problems.append(f"{label}: SHA-256 differs from expected.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", help="also write machine-readable results to this file")
    args = parser.parse_args()
    expected = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
    problems = []

    for pin in ("gufo", "gufoshapes"):
        check_hash(problems, HERE / expected[pin]["file"], expected[pin]["sha256"], expected[pin]["file"])
    ext_shapes_info = expected["extensions"]["extensionShapes"]
    check_hash(problems, HERE / ext_shapes_info["file"], ext_shapes_info["sha256"], ext_shapes_info["file"])

    gufo = load(HERE / expected["gufo"]["file"])
    shapes = load(HERE / expected["gufoshapes"]["file"])
    ext_shapes = load(HERE / ext_shapes_info["file"])

    rows, results = [], []
    for case in expected["cases"]:
        name = case["id"]
        for rel, digest in (
            (case["model"], case["modelSha256"]),
            (case["instances"], case["instancesSha256"]),
            (case["output"], case["outputSha256"]),
            (case["iriMappedOutput"], case["iriMappedOutputSha256"]),
            (case["comparison"], case["comparisonSha256"]),
        ):
            check_hash(problems, HERE / rel, digest, f"{name}:{rel}")

        findings_path = HERE / case["findings"]
        if not findings_path.is_file():
            problems.append(f"{name}: missing findings file")
            finding_ids = []
        else:
            finding_doc = json.loads(findings_path.read_text(encoding="utf-8"))
            finding_ids = [f["ruleId"] for f in finding_doc.get("findings") or []]
            if len(finding_ids) != case["expectedUfoFindingCount"] or finding_ids != case["expectedUfoFindingRuleIds"]:
                problems.append(f"{name}: UFO-rule findings differ from expected.json")

        diff_path = HERE / case["diff"]
        if diff_path.is_file():
            diff = json.loads(diff_path.read_text(encoding="utf-8"))
            # Accept either a wrapper or the summary shape used in expected.json.
            summary = diff.get("summary") or diff
            unclassified = summary.get("unclassified")
            if unclassified is None and isinstance(diff.get("unclassified"), int):
                unclassified = diff["unclassified"]
            if unclassified != case["diffSummary"]["unclassified"]:
                problems.append(f"{name}: published diff unclassified count differs from the recorded run")
            for field in ("matched", "extra", "missing", "ontographTriples", "upstreamTriples"):
                if field in summary and summary[field] != case["diffSummary"][field]:
                    problems.append(f"{name}: published diff {field} differs from the recorded run")
        else:
            problems.append(f"{name}: missing diff file")

        generated = load(HERE / case["output"])
        out_conforms, out_violations = violations(gufo + generated, shapes)
        exact = Counter(map(key, out_violations)) == Counter(map(key, case["expectedViolations"]))
        if out_conforms != case["expectedConforms"] or not exact:
            problems.append(f"{name}: gufoshapes result differs from the recorded OntoGraph result")

        verdict = "conforms" if out_conforms else f"{len(out_violations)} violation(s)"
        findings_ok = finding_ids == case["expectedUfoFindingRuleIds"]
        rows.append((
            name,
            "valid" if case["expectedValid"] else "invalid",
            str(case["expectedUfoFindingCount"]),
            verdict,
            "yes" if exact and out_conforms == case["expectedConforms"] and findings_ok else "NO",
        ))
        results.append({
            "id": name,
            "triplesOutput": len(generated),
            "ufoFindings": finding_ids,
            "conforms": out_conforms,
            "violations": out_violations,
            "matchesExpected": exact and findings_ok,
        })

    header = ("Example", "Expected", "UFO findings", "gufoshapes (pySHACL)", "Matches record")
    widths = [max(len(str(r[i])) for r in rows + [header]) for i in range(len(header))]

    def line(r):
        return "  ".join(str(c).ljust(w) for c, w in zip(r, widths))

    print("Acceptance suite (OntoUML models -> OntoGraph UFO rules -> gUFO)")
    print("Upstream Turtle is comparison only; outputs are not required to be isomorphic to it.")
    print(line(header))
    print(line(["-" * w for w in widths]))
    for r in rows:
        print(line(r))
    for r in results:
        for v in sorted(r["violations"], key=key):
            print(f"  {r['id']}: {short(v['message'])}")

    valid = [r for r, c in zip(results, expected["cases"]) if c["expectedValid"]]
    invalid = [r for r, c in zip(results, expected["cases"]) if not c["expectedValid"]]
    print()
    print(f"Valid examples with no UFO-rule findings and conforming gufoshapes: "
          f"{sum(r['conforms'] and not r['ufoFindings'] for r in valid)}/{len(valid)}")
    print("Invalid examples flagged: " + ", ".join(
        f"{r['id']} = {len(r['ufoFindings'])} rule finding(s), {len(r['violations'])} gufoshapes violation(s)"
        for r in invalid
    ))

    # Extensions: not acceptance.
    print()
    print("OntoGraph extension of example 05 (not acceptance): ogx:before")
    ext_rows, ext_results = [], []
    for case in expected["extensions"]["cases"]:
        name = case["id"]
        for rel, digest in (
            (case["model"], case["modelSha256"]),
            (case["instances"], case["instancesSha256"]),
            (case["output"], case["outputSha256"]),
        ):
            check_hash(problems, HERE / rel, digest, f"{name}:{rel}")
        generated = load(HERE / case["output"])
        gf_conforms, gf_violations = violations(gufo + generated, shapes)
        ext_conforms, ext_violations = violations(gufo + generated, ext_shapes)
        exact = Counter(map(key, ext_violations)) == Counter(map(key, case["expectedExtensionViolations"]))
        if gf_conforms != case["expectedGufoshapesConforms"]:
            problems.append(f"{name}: gufoshapes result differs from the recorded extension run")
        if ext_conforms != case["expectedExtensionShaclConforms"] or not exact:
            problems.append(f"{name}: extension-shape result differs from the recorded extension run")
        ext_rows.append((
            name,
            "valid" if case["expectedValid"] else "invalid",
            "conforms" if gf_conforms else f"{len(gf_violations)} violation(s)",
            "conforms" if ext_conforms else f"{len(ext_violations)} violation(s)",
            "yes" if exact and gf_conforms == case["expectedGufoshapesConforms"]
            and ext_conforms == case["expectedExtensionShaclConforms"] else "NO",
        ))
        ext_results.append({
            "id": name,
            "gufoshapesConforms": gf_conforms,
            "gufoshapesViolations": gf_violations,
            "extensionConforms": ext_conforms,
            "extensionViolations": ext_violations,
            "matchesExpected": exact,
        })
        for v in sorted(ext_violations, key=key):
            print(f"  {name}: {short(v['message'])}")

    ext_header = ("Extension", "Expected", "gufoshapes", "ogx:before shapes", "Matches record")
    ext_widths = [max(len(str(r[i])) for r in ext_rows + [ext_header]) for i in range(len(ext_header))]

    def ext_line(r):
        return "  ".join(str(c).ljust(w) for c, w in zip(r, ext_widths))

    print(ext_line(ext_header))
    print(ext_line(["-" * w for w in ext_widths]))
    for r in ext_rows:
        print(ext_line(r))

    print()
    print(f"rdflib {rdflib.__version__}, pySHACL {pyshacl.__version__}")
    if args.json:
        Path(args.json).write_text(
            json.dumps({"results": results, "extensions": ext_results, "problems": problems}, indent=2) + "\n",
            encoding="utf-8",
        )
    if problems:
        print("\nNOT REPRODUCED:")
        for p in problems:
            print("  - " + p)
        return 1
    print("\nAll expectations reproduced.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
