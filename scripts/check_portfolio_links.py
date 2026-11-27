#!/usr/bin/env python3
"""Check the maintained portfolio overview layer using only the standard library.

Run from any directory: python3 scripts/check_portfolio_links.py
Checks local Markdown/image destinations, case-index coverage and CSV contracts.
Does not request external URLs, run notebooks or audit legacy project internals.
The link parser supports the inline links and HTML images used in this layer;
it is not a general Markdown parser. URL fragments are not validated.
"""

import csv
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


def main():
    errors = []
    pages = [ROOT / "README.md", ROOT / "docs/project-index.md"]
    pages.extend(ROOT / "projects" / case / "README.md" for case in CASES)
    pages.append(ROOT / "examples/packaging_optimisation/README.md")
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
