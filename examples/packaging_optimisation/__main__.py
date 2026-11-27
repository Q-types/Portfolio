"""Run the fixed synthetic walkthrough; all output bytes are deterministic."""

import argparse
import csv
import io
import json
from pathlib import Path

from .model import (Job, LIMITS, MODEL_VERSION, ORIGIN, canonical, digest,
                    evaluate, input_record, issue, recover)

PACKAGE = Path(__file__).resolve().parent


def demo_files():
    jobs = [Job.from_dict(json.loads((PACKAGE / "fixtures" / name).read_text(encoding="utf-8")))
            for name in ("initial.json", "repriced.json")]
    issued = issue(jobs[0], "SYN-quote-01")
    preserved = issued.payload
    estimates = [evaluate(job) for job in jobs]
    assert issued.payload == preserved
    assert recover(preserved)["result"] == estimates[0]
    old, new = (estimate["selected"] for estimate in estimates)
    feasible = [c for c in estimates[0]["candidates"] if c["feasible"]]
    cheapest = min(feasible, key=lambda c: (c["price_per_sheet_minor"], c["total_minor"], c["stock_id"], c["orientation"]))
    summary = {
        "origin": ORIGIN, "limits": LIMITS,
        "initial_selected_stock": old["stock_id"], "initial_total_minor": old["total_minor"],
        "lowest_feasible_sheet_price_stock": cheapest["stock_id"],
        "lowest_sheet_price_best_layout_total_minor": cheapest["total_minor"],
        "combined_objective_difference_minor": cheapest["total_minor"] - old["total_minor"],
        "repriced_selected_stock": new["stock_id"], "repriced_total_minor": new["total_minor"],
        "reprice_change": "SYN-large sheet price 155 to 175 minor units; price version v1 to v2; all other inputs unchanged",
        "issued_payload_preserved": issued.payload == preserved,
        "issued_payload_sha256": digest(preserved),
        "initial_input_sha256": estimates[0]["input_sha256"],
        "repriced_input_sha256": estimates[1]["input_sha256"],
    }
    files = {"issued.json": preserved, "summary.json": canonical(summary) + b"\n"}
    for label, job, estimate in zip(("initial", "repriced"), jobs, estimates):
        files[f"{label}_inputs.json"] = canonical(input_record(job))
        files[f"{label}_estimate.json"] = canonical(estimate) + b"\n"
        fields = list(dict.fromkeys(key for row in estimate["candidates"] for key in row))
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(estimate["candidates"])
        files[f"{label}_candidates.csv"] = stream.getvalue().encode("utf-8")
    sources = {p.relative_to(PACKAGE).as_posix(): digest(p.read_bytes())
               for p in sorted(PACKAGE.glob("*.py"))}
    fixtures = {p.relative_to(PACKAGE).as_posix(): digest(p.read_bytes())
                for p in sorted((PACKAGE / "fixtures").glob("*.json"))}
    manifest = {
        "model_version": MODEL_VERSION, "origin": ORIGIN, "limits": LIMITS,
        "units": {"geometry": "integer mm", "area": "integer mm^2", "money": "integer SYN minor; 100 = 1 major"},
        "python_contract": "Python 3.10+ standard library; builder ran 3.14.0",
        "source_files_sha256": sources, "source_bundle_sha256": digest(canonical(sources)),
        "source_identity_rule": "SHA-256 of canonical path-to-hash map for package root *.py, including tests; no final Git commit asserted",
        "fixture_files_sha256": fixtures,
        "output_files_sha256": {name: digest(value) for name, value in sorted(files.items())},
        "hash_scope": "manifest excludes itself; input digest excludes result and is canonical input bytes without newline",
        "measured": "Candidate counts, geometry, sheet and cut counts, exact costs, input digests and issued byte preservation from this demo",
        "not_measured": "Runtime speedups, commercial impact, manufacturing accuracy, private MIS behaviour or Cambridge outcomes",
        "acceptance": "Builder execution only; independent review required",
    }
    files["manifest.json"] = json.dumps(manifest, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    return files, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PACKAGE / "results",
                        help="output directory; existing unequal files are refused")
    args = parser.parse_args()
    files, summary = demo_files()
    args.output.mkdir(parents=True, exist_ok=True)
    # Preflight every file before writing any; issued files cannot be silently repriced.
    for name, payload in files.items():
        path = args.output / name
        if path.exists() and path.read_bytes() != payload:
            parser.error(f"refusing to overwrite differing artifact: {path}; use a fresh --output directory")
    for name, payload in files.items():
        path = args.output / name
        if not path.exists():
            with path.open("xb") as stream:
                stream.write(payload)
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Wrote or verified {len(files)} deterministic artifacts.")


if __name__ == "__main__":
    main()
