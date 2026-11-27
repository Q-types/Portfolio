"""Hand calculations and an independent tiny placement/edge oracle; offline."""

from dataclasses import FrozenInstanceError, replace
from itertools import product
import json
from pathlib import Path
import unittest

from .model import (CutRule, Job, PriceBook, Spec, Stock, canonical, digest,
                    evaluate, input_digest, issue, recover)


def job(width=2, height=2, sheet_w=4, sheet_h=4, quantity=4, gap=0, margin=0,
        rotate=False, price=100, cut=10):
    return Job(Spec("SYN-spec", width, height, quantity, margin, gap, rotate),
               PriceBook("SYN-price", (Stock("SYN-stock", sheet_w, sheet_h, price),)),
               CutRule("SYN-rule", cut))


def tiny_oracle(j):
    """Grow coordinate lists by placement, then count distinct physical cut edges.

    Verifies maximal uniform grids only, with tiny dimensions. Does not call
    production geometry/count/selection helpers or use floor/ceiling formulas.
    """
    candidates = []
    s = j.spec
    for stock in j.prices.stocks:
        orientations = [("normal", s.width_mm, s.height_mm)]
        if s.allow_rotation:
            orientations.append(("rotated", s.height_mm, s.width_mm))
        for orientation, w, h in orientations:
            xs, ys = [], []
            x = s.margin_mm
            while x + w <= stock.width_mm - s.margin_mm:
                xs.append(x)
                x += w + s.gap_mm
            y = s.margin_mm
            while y + h <= stock.height_mm - s.margin_mm:
                ys.append(y)
                y += h + s.gap_mm
            if not xs or not ys:
                continue
            blanks = [(x, y, x + w, y + h) for x in xs for y in ys]
            xmin, xmax = min(b[0] for b in blanks), max(b[2] for b in blanks)
            ymin, ymax = min(b[1] for b in blanks), max(b[3] for b in blanks)
            # Exterior edges that coincide with stock edges need no operation.
            trim_edges = {("x", x) for x in (xmin, xmax) if x not in (0, stock.width_mm)}
            trim_edges |= {("y", y) for y in (ymin, ymax) if y not in (0, stock.height_mm)}
            horizontal = {v for b in blanks for v in (b[1], b[3]) if ymin < v < ymax}
            vertical = {(b[1], v) for b in blanks for v in (b[0], b[2]) if xmin < v < xmax}
            cuts = len(trim_edges) + len(horizontal) + len(vertical)
            sheets, produced = 0, 0
            while produced < s.quantity:
                sheets += 1
                produced += len(blanks)
            total = sum(stock.price_minor + cuts * j.cutting.cost_per_cut_minor for _ in range(sheets))
            candidates.append((total, stock.stock_id, orientation != "normal", len(blanks), sheets, cuts))
    return min(candidates) if candidates else None


class ModelTests(unittest.TestCase):
    def test_hand_calculated_trim_gap_and_money(self):
        j = job(40, 30, 100, 80, 12, 5, 5)
        c = evaluate(j)["selected"]
        expected = {"columns": 2, "rows": 2, "blanks_per_sheet": 4,
                    "span_width_mm": 85, "span_height_mm": 65, "sheets_required": 3,
                    "trim_cuts_per_sheet": 4, "row_cuts_per_sheet": 2,
                    "blank_cuts_per_sheet": 4, "cuts_per_sheet": 10,
                    "material_minor": 300, "cutting_minor": 300, "total_minor": 600,
                    "utilisation_numerator": 4800, "utilisation_denominator": 8000,
                    "waste_area_per_sheet_mm2": 3200}
        for key, value in expected.items():
            self.assertEqual(c[key], value, key)

    def test_exact_fit_has_no_boundary_gap_or_trim(self):
        c = evaluate(job(2, 2, 5, 5, gap=1))["selected"]
        self.assertEqual((c["blanks_per_sheet"], c["trim_cuts_per_sheet"], c["cuts_per_sheet"]), (4, 0, 6))
        smaller = evaluate(job(2, 2, 4, 5, gap=1))["selected"]
        self.assertEqual(smaller["blanks_per_sheet"], 2)
        self.assertEqual(evaluate(job())["selected"]["cuts_per_sheet"], 3)

    def test_margins_exact_fit_and_one_mm_short(self):
        c = evaluate(job(2, 2, 7, 7, gap=1, margin=1))["selected"]
        self.assertEqual((c["blanks_per_sheet"], c["trim_cuts_per_sheet"]), (4, 4))
        self.assertEqual(evaluate(job(2, 2, 6, 7, gap=1, margin=1))["selected"]["blanks_per_sheet"], 2)

    def test_rotation_and_rejected_candidate(self):
        j = job(3, 2, 2, 3, quantity=1, rotate=True)
        result = evaluate(j)
        self.assertEqual(result["selected"]["orientation"], "rotated")
        self.assertFalse(result["candidates"][0]["feasible"])
        self.assertIn("does not fit", result["candidates"][0]["reason"])
        with self.assertRaisesRegex(ValueError, "infeasible job"):
            evaluate(replace(j, spec=replace(j.spec, allow_rotation=False)))

    def test_quantity_rounding_and_full_last_sheet(self):
        c = evaluate(job(quantity=5))["selected"]
        self.assertEqual((c["sheets_required"], c["unused_blank_capacity"], c["total_cuts"], c["total_minor"]), (2, 3, 6, 260))

    def test_exact_money_including_large_integer(self):
        self.assertEqual(evaluate(job(price=1, cut=1))["selected"]["total_minor"], 4)
        huge = 10**25 + 1
        self.assertEqual(evaluate(job(price=huge, cut=1))["selected"]["total_minor"], huge + 3)
        with self.assertRaises(ValueError):
            job(price=0.1)

    def test_invalid_inputs(self):
        for changes in ({"width": 0}, {"height": -1}, {"quantity": 0},
                        {"quantity": True}, {"margin": -1}, {"gap": 0.5},
                        {"price": 0}, {"cut": -1}, {"rotate": 1}, {"sheet_w": 0}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                job(**changes)
        with self.assertRaisesRegex(ValueError, "infeasible"):
            evaluate(job(margin=3))
        with self.assertRaises(ValueError):
            PriceBook("v", ())
        with self.assertRaises(ValueError):
            PriceBook("v", (Stock("s", 2, 2, 1),) * 2)
        with self.assertRaises(ValueError):
            CutRule("v", 1, "unknown")
        with self.assertRaises(ValueError):
            Job.from_dict({"spec": {}})

    def test_tie_rule_and_stock_order_invariance(self):
        j = job(rotate=True)
        a, z = Stock("A", 4, 4, 100), Stock("Z", 4, 4, 100)
        j = replace(j, prices=PriceBook("v", (z, a)))
        reverse = replace(j, prices=PriceBook("v", (a, z)))
        self.assertEqual(evaluate(j), evaluate(reverse))
        c = evaluate(j)["selected"]
        self.assertEqual((c["stock_id"], c["orientation"]), ("A", "normal"))

    def test_canonical_digest_and_all_input_changes(self):
        self.assertEqual(canonical({"z": 2, "a": 1}), b'{"a":1,"z":2}')
        self.assertEqual(digest(b"abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        j = job()
        changes = [replace(j, spec=replace(j.spec, **{key: value})) for key, value in
                   {"specification_id": "other", "width_mm": 1, "height_mm": 1,
                    "quantity": 1, "margin_mm": 1, "gap_mm": 1, "allow_rotation": True}.items()]
        changes += [replace(j, cutting=replace(j.cutting, version="v2")),
                    replace(j, cutting=replace(j.cutting, cost_per_cut_minor=11)),
                    replace(j, prices=replace(j.prices, version="v2"))]
        changes += [replace(j, prices=replace(j.prices, stocks=(replace(j.prices.stocks[0], **{k: v}),)))
                    for k, v in {"stock_id": "other", "width_mm": 5, "height_mm": 5, "price_minor": 101}.items()]
        for changed in changes:
            self.assertNotEqual(input_digest(j), input_digest(changed))

    def test_issued_preservation_recovery_and_tamper_detection(self):
        j = job()
        snapshot = issue(j, "SYN-quote")
        before = snapshot.payload
        new = replace(j, prices=PriceBook("v2", (Stock("SYN-stock", 4, 4, 200),)))
        self.assertEqual(evaluate(new)["selected"]["total_minor"], 230)
        self.assertEqual(snapshot.payload, before)
        restored = recover(before)
        self.assertEqual(restored["result"]["selected"]["total_minor"], 130)
        with self.assertRaises(FrozenInstanceError):
            snapshot.payload = b"changed"
        restored["result"]["selected"]["total_minor"] = 0
        self.assertEqual(recover(before)["result"]["selected"]["total_minor"], 130)
        with self.assertRaisesRegex(ValueError, "mismatch"):
            recover(canonical(restored))
        restored = recover(before)
        restored["inputs"]["job"]["prices"]["version"] = "v2"
        with self.assertRaisesRegex(ValueError, "mismatch"):
            recover(canonical(restored))

    def test_fixture_selection_and_reprice(self):
        root = Path(__file__).parent / "fixtures"
        initial, repriced = [Job.from_dict(json.loads((root / name).read_text()))
                             for name in ("initial.json", "repriced.json")]
        first, second = evaluate(initial), evaluate(repriced)
        self.assertEqual((first["selected"]["stock_id"], first["selected"]["total_minor"]), ("SYN-large", 590))
        self.assertEqual((second["selected"]["stock_id"], second["selected"]["total_minor"]), ("SYN-small", 600))
        small = [c for c in first["candidates"] if c["stock_id"] == "SYN-small" and c["feasible"]]
        self.assertEqual(min(c["total_minor"] for c in small), 600)
        self.assertEqual(sum(not c["feasible"] for c in first["candidates"]), 2)

    def test_artifact_hashes_and_repeated_generation(self):
        from .__main__ import demo_files
        files, summary = demo_files()
        self.assertEqual(files, demo_files()[0])
        manifest = json.loads(files["manifest.json"])
        for name, expected in manifest["output_files_sha256"].items():
            self.assertEqual(digest(files[name]), expected)
        self.assertEqual(digest(files["initial_inputs.json"]), summary["initial_input_sha256"])
        self.assertEqual(digest(files["repriced_inputs.json"]), summary["repriced_input_sha256"])
        self.assertEqual(recover(files["issued.json"])["result"], json.loads(files["initial_estimate.json"]))
        self.assertEqual(summary["combined_objective_difference_minor"], 10)

    def test_independent_tiny_oracle(self):
        # 1,152 jobs, two stocks each. Exhaust every combination in this domain.
        for w, h, sw, sh, gap, margin, quantity in product(
                (1, 2, 3), (1, 2), (2, 3, 4, 5), (2, 3, 4, 5), (0, 1), (0, 1), (1, 3, 7)):
            j = job(w, h, sw, sh, quantity, gap, margin, True, 3, 1)
            j = replace(j, prices=PriceBook("v", (Stock("A", sw, sh, 3), Stock("B", sh + 1, sw, 4))))
            expected = tiny_oracle(j)
            with self.subTest(w=w, h=h, sw=sw, sh=sh, gap=gap, margin=margin, quantity=quantity):
                if expected is None:
                    with self.assertRaises(ValueError):
                        evaluate(j)
                else:
                    c = evaluate(j)["selected"]
                    self.assertEqual((c["total_minor"], c["stock_id"], c["orientation"] != "normal",
                                      c["blanks_per_sheet"], c["sheets_required"], c["cuts_per_sheet"]), expected)


if __name__ == "__main__":
    unittest.main()
