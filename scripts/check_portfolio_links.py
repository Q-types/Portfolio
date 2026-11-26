#!/usr/bin/env python3
"""Check the maintained portfolio overview layer using only the standard library.

Run from any directory: python3 scripts/check_portfolio_links.py
Checks local Markdown/image destinations, case-index coverage and CSV contracts.
Does not request external URLs, run notebooks or audit legacy project internals.
The link parser supports the inline links and HTML images used in this layer;
it is not a general Markdown parser. URL fragments are not validated.
"""

import csv
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
CASES = (
    "ksp-mis", "bank-of-england-nlp", "book-sales-forecasting",
    "student-dropout", "customer-feedback-nlp", "customer-segmentation",
    "qsol-solution-finder", "engineering-workflow", "ship-engine-anomalies",
)
SCHEMAS = {
    "claims.csv": ["claim_id", "project_id", "approved_wording", "source_version",
                   "source_route", "contribution", "evidence_level",
                   "data_access_route", "limitations"],
    "provenance.csv": ["project_id", "component", "source_version", "source_route",
                       "contribution", "evidence_level", "data_access_route",
                       "limitations"],
}


def check_destination(source, destination, errors):
    url = urlsplit(destination.strip("<>"))
    if url.scheme in {"https", "http", "mailto"}:
        return
    if url.scheme or url.netloc or url.path.startswith("/"):
        errors.append(f"{source.relative_to(ROOT)}: unsupported destination {destination}")
        return
    if not url.path:
        return
    target = (source.parent / unquote(url.path)).resolve()
    if not target.is_relative_to(ROOT) or not target.exists():
        errors.append(f"{source.relative_to(ROOT)}: missing/outside destination {destination}")


def check_financial_text_artifacts(errors):
    """Check the declared synthetic result/source bytes without external access."""
    base = ROOT / "examples/financial_text_nlp"
    result_names = {"input.json", "audit.json", "questions.csv", "windows.csv", "bank_quarter.csv"}
    source_names = {"__init__.py", "__main__.py", "measurement.py"}
    try:
        for path in base.rglob("*"):
            if path.is_symlink():
                raise ValueError("symlink in financial-text example")
            if path.name == "__pycache__" or path.suffix == ".pyc":
                raise ValueError("generated cache in financial-text example")
        manifest = json.loads((base / "results/manifest.json").read_bytes())
        if manifest["evidence"] != "synthetic mechanics only":
            raise ValueError("public results must be synthetic")
        if set(manifest["files"]) != result_names or set(manifest["source"]) != source_names:
            raise ValueError("unexpected manifest file set")
        for group, directory in [("files", base / "results"), ("source", base)]:
            for name, expected in manifest[group].items():
                raw = (directory / name).read_bytes()
                if expected != {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}:
                    raise ValueError(f"artifact identity mismatch: {name}")
        raw = (base / "fixtures/synthetic.json").read_bytes()
        if raw != (base / "results/input.json").read_bytes():
            raise ValueError("result input differs from bundled fixture")
        if manifest["input"] != {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}:
            raise ValueError("input identity mismatch")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"Financial-text artifacts: {exc}")


def check_dropout_artifacts(errors):
    """Bind the invented fixture, frozen state, full row contract and result bytes."""
    base = ROOT / "examples/student_dropout"
    result_names = {"input.json", "config.json", "splits.json", "frozen.json", "scores.csv", "predictions.csv"}
    source_names = {"__init__.py", "__main__.py", "contract.py", "metrics.py", "models.py",
                    "protocol.py", "adapters.py", "fixture.py", "test_protocol.py"}
    try:
        for path in base.rglob("*"):
            if path.is_symlink() or path.name == "__pycache__" or path.suffix == ".pyc":
                raise ValueError("symlink/cache in dropout example")
        manifest = json.loads((base / "results/manifest.json").read_bytes())
        if (manifest["evidence"] != "synthetic mechanics only"
                or manifest["scope"] != "public_invented" or manifest["permission_receipt"] is not None):
            raise ValueError("public results must be invented")
        if set(manifest["files"]) != result_names or set(manifest["source"]) != source_names:
            raise ValueError("unexpected manifest file set")
        if {p.name for p in (base / "results").iterdir()} != result_names | {"manifest.json"}:
            raise ValueError("unexpected result file")
        for group, directory in [("files", base / "results"), ("source", base)]:
            for name, expected in manifest[group].items():
                raw = (directory / name).read_bytes()
                if expected != {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}:
                    raise ValueError(f"artifact identity mismatch: {name}")
        for original, retained, field in [("fixtures/cohort.json", "input.json", "input"),
                                           ("protocol.json", "config.json", "config")]:
            raw = (base / original).read_bytes()
            if raw != (base / "results" / retained).read_bytes():
                raise ValueError("result differs from fixture/config")
            if manifest[field] != {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}:
                raise ValueError("fixture/config identity mismatch")
        if manifest["frozen_before_evaluation"] != manifest["files"]["frozen.json"]:
            raise ValueError("frozen-state identity mismatch")
        data = json.loads((base / "fixtures/cohort.json").read_bytes())
        config = json.loads((base / "protocol.json").read_bytes())
        expected = {phase: sorted(r["id"] for r in data["records"] if r["cohort"] in cohorts)
                    for phase, cohorts in config["cohorts"].items()}
        splits = json.loads((base / "results/splits.json").read_bytes())
        if splits != expected or len({key for ids in splits.values() for key in ids}) != len(data["records"]):
            raise ValueError("split identity mismatch")
        combos = {(s, m) for s in ("enrolment", "engagement", "academic_progress")
                  for m in ("prevalence", "logistic")}
        with (base / "results/predictions.csv").open(newline="") as stream:
            predictions = list(csv.DictReader(stream))
        with (base / "results/scores.csv").open(newline="") as stream:
            scores = list(csv.DictReader(stream))
        if len(scores) != 6 or {(r["stage"], r["method"]) for r in scores} != combos:
            raise ValueError("missing stage/method comparison")
        labels = {r["id"]: r["label"] for r in data["records"]}
        if len(predictions) != 6 * len(expected["evaluation"]):
            raise ValueError("prediction count mismatch")
        for stage, method in combos:
            rows = [r for r in predictions if (r["stage"], r["method"]) == (stage, method)]
            if [r["id"] for r in rows] != expected["evaluation"]:
                raise ValueError("evaluation rows missing, duplicate or reordered")
            if any(int(r["label"]) != labels[r["id"]] for r in rows):
                raise ValueError("evaluation label mismatch")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"Dropout artifacts: {exc}")


def main():
    errors = []
    pages = [ROOT / "README.md", ROOT / "docs/project-index.md"]
    pages.extend(ROOT / "projects" / case / "README.md" for case in CASES)
    pages.append(ROOT / "examples/packaging_optimisation/README.md")
    pages.append(ROOT / "examples/book_sales_forecasting/README.md")
    pages.append(ROOT / "examples/financial_text_nlp/README.md")
    pages.append(ROOT / "examples/student_dropout/README.md")
    link_count = 0
    for page in pages:
        if not page.is_file():
            errors.append(f"Missing page: {page.relative_to(ROOT)}")
            continue
        text = page.read_text(encoding="utf-8")
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        destinations = re.findall(r"!?\[[^\]]*\]\(([^\s)]+)\)", text)
        destinations += re.findall(r"<(?:img|a)\b[^>]*?(?:src|href)=[\"']([^\"']+)", text)
        for destination in destinations:
            check_destination(page, destination, errors)
        link_count += len(destinations)

    index = ROOT / "docs/project-index.md"
    index_text = index.read_text(encoding="utf-8") if index.exists() else ""
    for case in CASES:
        if f"../projects/{case}/README.md" not in index_text:
            errors.append(f"Project index missing case: {case}")
    if "../examples/packaging_optimisation/README.md" not in index_text:
        errors.append("Project index missing synthetic packaging example")
    if "../examples/book_sales_forecasting/README.md" not in index_text:
        errors.append("Project index missing synthetic forecasting example")
    if "../examples/financial_text_nlp/README.md" not in index_text:
        errors.append("Project index missing synthetic financial-text example")
    if "../examples/student_dropout/README.md" not in index_text:
        errors.append("Project index missing synthetic dropout example")
    check_financial_text_artifacts(errors)
    check_dropout_artifacts(errors)
    row_counts = {}
    for filename, schema in SCHEMAS.items():
        path = ROOT / "docs" / filename
        if not path.is_file():
            errors.append(f"Missing CSV: {filename}")
            continue
        with path.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != schema:
                errors.append(f"{filename}: schema mismatch")
                continue
            rows = list(reader)
        row_counts[filename] = len(rows)
        seen = set()
        projects = set()
        for number, row in enumerate(rows, 2):
            if None in row or any(not value for value in row.values()):
                errors.append(f"{filename}:{number}: missing or extra fields")
                continue
            key = row.get("claim_id", (row["project_id"], row.get("component")))
            if key in seen:
                errors.append(f"{filename}:{number}: duplicate key {key}")
            seen.add(key)
            projects.add(row["project_id"])
            check_destination(path, row["source_route"], errors)
        for case in (*CASES, "packaging-optimisation"):
            if case not in projects:
                errors.append(f"{filename}: missing case {case}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"PASS: {len(pages)} pages; {link_count} link/image destinations; "
          f"{len(CASES)} indexed cases; CSV rows {row_counts}")
    print("External availability, fragments, scientific validity and publication rights require separate checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
