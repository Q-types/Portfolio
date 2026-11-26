"""Maximal uniform grids, exact costs and immutable synthetic quote snapshots.

Geometry uses integer millimetres; money uses integer SYN minor units (100 = 1).
See README.md for the full candidate family and physical simplifications.
"""

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re

MODEL_VERSION = "synthetic-grid-v1"
CUT_MODEL = "trim-envelope-rows-then-blanks-v1"
TIE_RULE = "total_minor, stock_id ASCII ascending, normal before rotated"
ORIGIN = "Independently authored portfolio code and wholly synthetic inputs; not private MIS or Cambridge results"
LIMITS = "Best among maximal uniform grids only; simplified unstacked cuts; no production validation or commercial benchmark"


def integer(name, value, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def identifier(name, value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", value):
        raise ValueError(f"{name} must be a 1–64 character ASCII identifier")


@dataclass(frozen=True)
class Spec:
    specification_id: str
    width_mm: int
    height_mm: int
    quantity: int
    margin_mm: int = 0
    gap_mm: int = 0
    allow_rotation: bool = True

    def __post_init__(self):
        identifier("specification_id", self.specification_id)
        for name in ("width_mm", "height_mm", "quantity"):
            integer(name, getattr(self, name), 1)
        for name in ("margin_mm", "gap_mm"):
            integer(name, getattr(self, name))
        if type(self.allow_rotation) is not bool:
            raise ValueError("allow_rotation must be a boolean")


@dataclass(frozen=True)
class Stock:
    stock_id: str
    width_mm: int
    height_mm: int
    price_minor: int

    def __post_init__(self):
        identifier("stock_id", self.stock_id)
        for name in ("width_mm", "height_mm", "price_minor"):
            integer(name, getattr(self, name), 1)


@dataclass(frozen=True)
class PriceBook:
    version: str
    stocks: tuple[Stock, ...]
    currency: str = "SYN"

    def __post_init__(self):
        identifier("price version", self.version)
        if self.currency != "SYN":
            raise ValueError("currency must be SYN (synthetic units, 100 minor = 1 major)")
        if type(self.stocks) is not tuple or not self.stocks or not all(type(s) is Stock for s in self.stocks):
            raise ValueError("stocks must be a nonempty tuple of Stock records")
        if len({s.stock_id for s in self.stocks}) != len(self.stocks):
            raise ValueError("stock_id values must be unique within a price version")


@dataclass(frozen=True)
class CutRule:
    version: str
    cost_per_cut_minor: int
    model: str = CUT_MODEL

    def __post_init__(self):
        identifier("cut rule version", self.version)
        integer("cost_per_cut_minor", self.cost_per_cut_minor)
        if self.model != CUT_MODEL:
            raise ValueError(f"unsupported cutting model: {self.model}")


@dataclass(frozen=True)
class Job:
    spec: Spec
    prices: PriceBook
    cutting: CutRule

    def __post_init__(self):
        if type(self.spec) is not Spec or type(self.prices) is not PriceBook or type(self.cutting) is not CutRule:
            raise ValueError("Job requires Spec, PriceBook and CutRule records")

    @classmethod
    def from_dict(cls, data):
        try:
            if set(data) != {"spec", "prices", "cutting"}:
                raise ValueError("job keys must be spec, prices and cutting")
            prices = dict(data["prices"])
            prices["stocks"] = tuple(Stock(**s) for s in prices["stocks"])
            return cls(Spec(**data["spec"]), PriceBook(**prices), CutRule(**data["cutting"]))
        except (TypeError, KeyError, AttributeError) as exc:
            raise ValueError(f"invalid job record: {exc}") from exc


def canonical(value):
    """UTF-8 JSON, sorted keys, no whitespace, ASCII escapes, no NaN; no newline."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def digest(data):
    return sha256(data).hexdigest()


def input_record(job):
    data = asdict(job)
    data["prices"]["stocks"] = sorted(data["prices"]["stocks"], key=lambda s: s["stock_id"])
    return {
        "model_version": MODEL_VERSION,
        "units": {"length": "mm", "money": "SYN minor units; 100 = 1 major"},
        "tie_rule": TIE_RULE,
        "money_rounding": "identity: integer minor units throughout; no fractional prices accepted",
        "job": data,
    }


def input_digest(job):
    return digest(canonical(input_record(job)))


def evaluate(job):
    """Evaluate one maximal grid per stock/orientation; retain infeasible rows."""
    spec = job.spec
    candidates = []
    for stock in sorted(job.prices.stocks, key=lambda s: s.stock_id):
        orientations = [("normal", spec.width_mm, spec.height_mm)]
        if spec.allow_rotation:
            orientations.append(("rotated", spec.height_mm, spec.width_mm))
        for orientation, width, height in orientations:
            usable_w = stock.width_mm - 2 * spec.margin_mm
            usable_h = stock.height_mm - 2 * spec.margin_mm
            row = {
                "stock_id": stock.stock_id, "orientation": orientation,
                "stock_width_mm": stock.width_mm, "stock_height_mm": stock.height_mm,
                "blank_width_mm": width, "blank_height_mm": height,
                "usable_width_mm": usable_w, "usable_height_mm": usable_h,
                "price_per_sheet_minor": stock.price_minor,
            }
            if usable_w < width or usable_h < height:
                row.update(feasible=False, reason="blank does not fit inside margins in this orientation")
                candidates.append(row)
                continue
            cols = (usable_w + spec.gap_mm) // (width + spec.gap_mm)
            rows = (usable_h + spec.gap_mm) // (height + spec.gap_mm)
            span_w = cols * width + (cols - 1) * spec.gap_mm
            span_h = rows * height + (rows - 1) * spec.gap_mm
            count = cols * rows
            sheets = (spec.quantity + count - 1) // count
            # Trim the envelope at left/top if inset, and right/bottom if needed.
            trims = (2 * int(spec.margin_mm > 0)
                     + int(spec.margin_mm + span_w < stock.width_mm)
                     + int(spec.margin_mm + span_h < stock.height_mm))
            gap_cuts = 2 if spec.gap_mm > 0 else 1
            row_cuts = gap_cuts * (rows - 1)
            blank_cuts = rows * gap_cuts * (cols - 1)
            cuts = trims + row_cuts + blank_cuts
            material = sheets * stock.price_minor
            cutting = sheets * cuts * job.cutting.cost_per_cut_minor
            sheet_area = stock.width_mm * stock.height_mm
            blank_area = spec.width_mm * spec.height_mm
            row.update(
                feasible=True, reason="fits", columns=cols, rows=rows,
                span_width_mm=span_w, span_height_mm=span_h,
                blanks_per_sheet=count, sheets_required=sheets,
                unused_blank_capacity=sheets * count - spec.quantity,
                utilisation_numerator=count * blank_area, utilisation_denominator=sheet_area,
                waste_area_per_sheet_mm2=sheet_area - count * blank_area,
                trim_cuts_per_sheet=trims, row_cuts_per_sheet=row_cuts,
                blank_cuts_per_sheet=blank_cuts, cuts_per_sheet=cuts,
                total_cuts=sheets * cuts, material_minor=material,
                cutting_minor=cutting, total_minor=material + cutting,
            )
            candidates.append(row)
    feasible = [c for c in candidates if c["feasible"]]
    if not feasible:
        raise ValueError("infeasible job: no stock/orientation fits inside margins")
    chosen = min(feasible, key=lambda c: (c["total_minor"], c["stock_id"], c["orientation"] != "normal"))
    return {
        "origin": ORIGIN, "limits": LIMITS, "model_version": MODEL_VERSION,
        "input_sha256": input_digest(job), "tie_rule": TIE_RULE,
        "candidates": candidates, "selected": dict(chosen),
    }


@dataclass(frozen=True)
class IssuedSnapshot:
    """Immutable canonical bytes; reading returns a detached record."""
    payload: bytes

    def __post_init__(self):
        if type(self.payload) is not bytes:
            raise ValueError("snapshot payload must be immutable bytes")
        recover(self.payload)


def issue(job, quote_id):
    identifier("quote_id", quote_id)
    record = {"snapshot_version": "synthetic-quote-v1", "quote_id": quote_id,
              "inputs": input_record(job), "result": evaluate(job)}
    return IssuedSnapshot(canonical(record))


def recover(payload):
    """Check canonical form, full input identity and replayed result on load.

    Hashes/replay detect mismatch, not malicious replacement or authenticity.
    Recovery requires this model version; retain its source with issued files.
    """
    try:
        record = json.loads(payload)
        if set(record) != {"snapshot_version", "quote_id", "inputs", "result"}:
            raise ValueError("unexpected snapshot fields")
        if record["snapshot_version"] != "synthetic-quote-v1":
            raise ValueError("unsupported snapshot version")
        identifier("quote_id", record["quote_id"])
        job = Job.from_dict(record["inputs"]["job"])
        if canonical(record["inputs"]) != canonical(input_record(job)):
            raise ValueError("unsupported or altered input contract")
        if canonical(record["result"]) != canonical(evaluate(job)):
            raise ValueError("snapshot result/input mismatch")
        if canonical(record) != payload:
            raise ValueError("snapshot is not canonical JSON bytes")
        return record
    except (TypeError, KeyError, AttributeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid snapshot: {exc}") from exc
