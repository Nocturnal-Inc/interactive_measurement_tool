#!/usr/bin/env python3
"""Build data/full/measurements.us-adult.{json,js} from the research CSVs.

Reads data/data_from_research_files/*.csv and emits one bundled JSON consumed by
Measurement_Tool_Full.html via window.IMT_DATA. Re-run any time the CSVs change.

    python3 scripts/build_data.py

No external dependencies (stdlib csv/json/math/pathlib only).
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_DIR = ROOT / "data" / "data_from_research_files"
OUT_DIR = ROOT / "data" / "full"

# CSV → (measurement-id-list, unit-conversion-factor-to-cm, plausible-mean-cm-range)
# tragus and mastoid both pull from mastoid_mastoid.csv per user instruction.
# Plausible ranges drop rows whose Mean (after unit conversion) is outside the band —
# these are typically wrong-unit entries inside an otherwise-uniform file
# (e.g. some head_circumference rows have mm values like 584).
# Note: mastoid_mastoid.csv currently mirrors head_circumference.csv (cm-scale) — tragus
# and mastoid distributions are derived from HC until real arc measurements exist. The
# arcs are physically ~half of full head circumference (ear → over face / over back →
# ear), so we apply a 0.5 factor at load time (halves μ and σ together; plausible range
# is correspondingly 20–40 cm). Remove the 0.5 and revert the range once real arc data
# replaces the CSV.
SOURCES = [
    ("head_circumference.csv", ["cranial"],            1.0, (40.0, 80.0)),
    ("ear_height.csv",         ["ear"],                0.1, (3.0, 10.0)),
    ("mastoid_mastoid.csv",    ["tragus", "mastoid"],  0.5, (20.0, 40.0)),
    ("bizygomatic_breadth.csv",["bizygomatic"],        0.1, (8.0, 22.0)),
]

REGION_TYPO_FIXES = {
    "Northern Europse": "Northern Europe",
    "Polysesia": "Polynesia",
}

AGE_BINS = [
    ("18-30", 18, 30),
    ("31-45", 31, 45),
    ("46-60", 46, 60),
    ("60+", 60, 200),
]

MEASUREMENT_META = {
    "cranial":     {"name": "Cranial Circumference",                "unit": "cm", "desc": "Tape at glabella → occipital protuberance",                                            "productDefault": {"min": 54.0, "max": 59.0}},
    "ear":         {"name": "Ear Height",                           "unit": "cm", "desc": "Helix tip → lobule bottom",                                                              "productDefault": {"min": 5.8,  "max": 6.8}},
    "tragus":      {"name": "Tragus-to-Tragus (Front Arc)",         "unit": "cm", "desc": "Surface arc across face, ear to ear",                                                    "productDefault": {"min": 25.5, "max": 30.0}},
    "mastoid":     {"name": "Mastoid-to-Mastoid (Rear Arc)",        "unit": "cm", "desc": "Surface arc over back of skull",                                                         "productDefault": {"min": 26.5, "max": 31.5}},
    "bizygomatic": {"name": "Bizygomatic Breadth",                  "unit": "cm", "desc": "Zygion–zygion straight-line chord (cheekbone to cheekbone)",                             "productDefault": {"min": 13.2, "max": 14.35}, "isNiosh": True},
    "maskarcflex": {"name": "Mask Arc Flex (BZ-derived)",           "unit": "cm", "desc": "Face curvature radius at cheekbone level — smaller = narrower face = more flex demand",  "productDefault": {"min": 8.64, "max": 10.04}, "isMaskFlex": True},
}

MEASUREMENT_ORDER = ["cranial", "ear", "tragus", "mastoid", "bizygomatic", "maskarcflex"]

NOSE_PROMINENCE_CM = 3.0  # used for maskarcflex derivation: R = (BZ² + 4·nose²) / (8·nose)


def normalize_gender(raw: str) -> str:
    s = (raw or "").strip().lower()
    if s in ("male", "m"):
        return "male"
    if s in ("female", "f"):
        return "female"
    return "unspecified"


def parse_int(s: str) -> int | None:
    if not s:
        return None
    s = s.replace(",", "").strip()
    try:
        return int(s)
    except ValueError:
        try:
            return int(float(s))
        except ValueError:
            return None


def parse_float(s: str) -> float | None:
    if not s:
        return None
    try:
        return float(s.replace(",", "").strip())
    except ValueError:
        return None


def normalize_region(raw: str) -> str | None:
    if not raw:
        return None
    r = raw.strip()
    return REGION_TYPO_FIXES.get(r, r)


AGE_RANGE_RE = re.compile(r"^\s*(\d+)\s*[-–to]+\s*(\d+)\s*$")
AGE_PLUS_RE = re.compile(r"^\s*(\d+)\s*\+\s*$")
AGE_LT_RE = re.compile(r"^\s*<\s*(\d+)\s*$")


def parse_age_center(raw: str) -> float | None:
    """Return the midpoint of an age range string, or None if unparseable / pediatric."""
    if not raw:
        return None
    s = raw.strip()
    if not s or s.lower() == "not specified":
        return None
    m = AGE_RANGE_RE.match(s)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        return (lo + hi) / 2
    m = AGE_PLUS_RE.match(s)
    if m:
        return float(m.group(1)) + 5  # rough midpoint for "60+"
    m = AGE_LT_RE.match(s)
    if m:
        return float(m.group(1)) / 2
    try:
        return float(s)
    except ValueError:
        return None


def assign_age_bin(age_center: float | None) -> str | None:
    if age_center is None or age_center < 18:
        return None
    for label, lo, hi in AGE_BINS:
        if lo <= age_center <= hi:
            return label
    return None


def pool(rows: list[dict]) -> dict | None:
    """Pool rows {mean, sd, n} via weighted mean + Cochran's pooled SD."""
    if not rows:
        return None
    total_n = sum(r["n"] for r in rows)
    if total_n <= 1:
        return None
    pooled_mean = sum(r["mean"] * r["n"] for r in rows) / total_n
    if len(rows) == 1:
        # Single study: pooled SD == reported SD (not zero).
        pooled_sd = rows[0]["sd"]
    else:
        num = sum((r["n"] - 1) * r["sd"] ** 2 + r["n"] * (r["mean"] - pooled_mean) ** 2 for r in rows)
        pooled_sd = math.sqrt(max(num / (total_n - 1), 0.0))
    return {
        "mean": round(pooled_mean, 3),
        "sd": round(pooled_sd, 3),
        "n": total_n,
        "studies": len(rows),
    }


def pool_three_ways(rows: list[dict]) -> dict:
    """Pool by gender (male, female) and combined (all three)."""
    out = {}
    for g in ("male", "female"):
        gendered = [r for r in rows if r["gender"] == g]
        p = pool(gendered)
        if p is not None:
            out[g] = p
    combined = pool(rows)
    if combined is not None:
        out["combined"] = combined
    return out


def derive_maskarcflex(bz_pool: dict) -> dict:
    """Map a bizygomatic pool {male/female/combined: {mean, sd, n, studies}} to maskarcflex.

    R(BZ) = (BZ² + 4·nose²) / (8·nose).  Apply via small-perturbation linearization:
    R(μ ± σ) ≈ R(μ) ± (dR/dBZ)·σ  where  dR/dBZ = BZ / (4·nose).
    """
    out = {}
    nose = NOSE_PROMINENCE_CM
    for g, p in bz_pool.items():
        mu = p["mean"]
        sigma = p["sd"]
        r_mu = (mu * mu + 4 * nose * nose) / (8 * nose)
        dR = mu / (4 * nose)
        r_sigma = abs(dR) * sigma
        out[g] = {
            "mean": round(r_mu, 3),
            "sd": round(r_sigma, 3),
            "n": p["n"],
            "studies": p["studies"],
        }
    return out


def load_csv(path: Path, unit_factor: float, plausible_cm: tuple[float, float]) -> list[dict]:
    """Load one CSV. Returns rows with normalized + unit-converted numeric fields.

    Drops rows whose post-conversion Mean is outside `plausible_cm` (likely wrong-unit entries).
    """
    lo, hi = plausible_cm
    rows: list[dict] = []
    dropped_outliers: list[tuple[str, float]] = []
    skipped_missing = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            row = {(k or "").strip(): (v.strip() if isinstance(v, str) else v) for k, v in raw.items()}
            mean = parse_float(row.get("Mean", ""))
            sd = parse_float(row.get("SD", ""))
            n = parse_int(row.get("Sample Size", ""))
            if mean is None or sd is None or n is None or n <= 0 or sd <= 0:
                skipped_missing += 1
                continue
            mean_cm = mean * unit_factor
            sd_cm = sd * unit_factor
            if not (lo <= mean_cm <= hi):
                dropped_outliers.append((row.get("Author + Date", "?"), mean))
                continue
            rows.append({
                "mean": mean_cm,
                "sd": sd_cm,
                "n": n,
                "gender": normalize_gender(row.get("Gender") or row.get("Sex") or ""),
                "region": normalize_region(row.get("Region") or ""),
                "age_bin": assign_age_bin(parse_age_center(row.get("Age") or "")),
                "study": row.get("Author + Date", ""),
            })
    if skipped_missing:
        print(f"    skipped {skipped_missing} rows missing mean/sd/n")
    if dropped_outliers:
        print(f"    dropped {len(dropped_outliers)} out-of-range rows (raw mean outside {lo}–{hi}cm after unit conversion):")
        for study, raw_mean in dropped_outliers[:5]:
            print(f"      {study!r}: raw mean = {raw_mean}")
        if len(dropped_outliers) > 5:
            print(f"      … and {len(dropped_outliers) - 5} more")
    return rows


def compute_xrange(by_region: dict, by_age: dict, all_pool: dict) -> list[float]:
    """xRange = [min(mean − 3·sd) − 0.5, max(mean + 3·sd) + 0.5] over every populated leaf."""
    los, his = [], []
    for tier in (by_region.values(), by_age.values(), [all_pool]):
        for entry in tier:
            for g, p in entry.items():
                los.append(p["mean"] - 3 * p["sd"])
                his.append(p["mean"] + 3 * p["sd"])
    if not los:
        return [0, 1]
    return [round(min(los) - 0.5, 1), round(max(his) + 0.5, 1)]


# A 16-pair palette big enough to cover All + 4 age bins + ~21 regions.
COLOR_PAIRS = [
    ("#38bdf8", "#f472b6"),  # All       — sky/pink (matches old "total")
    ("#c084fc", "#e879f9"),
    ("#34d399", "#6ee7b7"),
    ("#fbbf24", "#fde68a"),
    ("#fb923c", "#fed7aa"),
    ("#94a3b8", "#cbd5e1"),
    ("#818cf8", "#a5b4fc"),
    ("#f87171", "#fca5a5"),
    ("#4ade80", "#86efac"),
    ("#22d3ee", "#67e8f9"),
    ("#a78bfa", "#c4b5fd"),
    ("#f59e0b", "#fcd34d"),
    ("#10b981", "#6ee7b7"),
    ("#ef4444", "#fca5a5"),
    ("#06b6d4", "#67e8f9"),
    ("#84cc16", "#bef264"),
    ("#d946ef", "#f0abfc"),
    ("#0ea5e9", "#7dd3fc"),
    ("#14b8a6", "#5eead4"),
    ("#eab308", "#fde047"),
    ("#a855f7", "#d8b4fe"),
    ("#f43f5e", "#fda4af"),
    ("#3b82f6", "#93c5fd"),
    ("#22c55e", "#86efac"),
    ("#fb7185", "#fda4af"),
    ("#7c3aed", "#c4b5fd"),
]


def assign_colors(keys: list[str]) -> dict:
    out = {}
    for i, k in enumerate(keys):
        m, f = COLOR_PAIRS[i % len(COLOR_PAIRS)]
        out[k] = {"male": m, "female": f, "combined": m}
    return out


def main():
    print(f"Building from {CSV_DIR} → {OUT_DIR}")

    # Load every CSV once.
    by_csv: dict[str, list[dict]] = {}
    for fname, _meas, unit, bounds in SOURCES:
        path = CSV_DIR / fname
        print(f"  {fname}:")
        rows = load_csv(path, unit, bounds)
        by_csv[fname] = rows
        print(f"    kept {len(rows)} rows")

    # Build per-measurement pools.
    measurements_out: list[dict] = []
    region_data: dict[str, dict] = defaultdict(dict)   # region → {meas_id → pool3way}
    age_data: dict[str, dict] = defaultdict(dict)      # ageBin → {meas_id → pool3way}

    # Track which regions and age bins are present (across all measurements).
    all_regions: set[str] = set()
    all_age_bins: set[str] = set()

    # First pass: pool per-region / per-age / all for the four CSV-backed measurements.
    pools_by_meas: dict[str, dict] = {}
    for fname, meas_ids, _unit, _bounds in SOURCES:
        rows = by_csv[fname]
        for mid in meas_ids:
            by_region: dict[str, dict] = {}
            by_age: dict[str, dict] = {}
            # Per region
            region_groups: dict[str, list[dict]] = defaultdict(list)
            for r in rows:
                if r["region"]:
                    region_groups[r["region"]].append(r)
            for region, rs in region_groups.items():
                p = pool_three_ways(rs)
                if p:
                    by_region[region] = p
                    all_regions.add(region)
            # Per age
            age_groups: dict[str, list[dict]] = defaultdict(list)
            for r in rows:
                if r["age_bin"]:
                    age_groups[r["age_bin"]].append(r)
            for ab, rs in age_groups.items():
                p = pool_three_ways(rs)
                if p:
                    by_age[ab] = p
                    all_age_bins.add(ab)
            # All
            all_pool = pool_three_ways(rows)
            pools_by_meas[mid] = {"by_region": by_region, "by_age": by_age, "all": all_pool}

    # Derive maskarcflex from bizygomatic.
    bz = pools_by_meas["bizygomatic"]
    pools_by_meas["maskarcflex"] = {
        "by_region": {region: derive_maskarcflex(p) for region, p in bz["by_region"].items()},
        "by_age":    {ab:     derive_maskarcflex(p) for ab,     p in bz["by_age"].items()},
        "all":       derive_maskarcflex(bz["all"]),
    }

    # Build MEASUREMENTS array.
    for mid in MEASUREMENT_ORDER:
        meta = MEASUREMENT_META[mid]
        pools = pools_by_meas[mid]
        all_pool = pools["all"]
        x_lo, x_hi = compute_xrange(pools["by_region"], pools["by_age"], all_pool)
        entry = {
            "id": mid,
            "name": meta["name"],
            "unit": meta["unit"],
            "desc": meta["desc"],
            "productDefault": meta["productDefault"],
            "xRange": [x_lo, x_hi],
            **{g: all_pool[g] for g in ("male", "female", "combined") if g in all_pool},
        }
        if meta.get("isNiosh"):
            entry["isNiosh"] = True
        if meta.get("isMaskFlex"):
            entry["isMaskFlex"] = True
        measurements_out.append(entry)

    # Build region/age demographics nested by demographic key → {meas_id → pool3way}.
    for region in all_regions:
        for mid in MEASUREMENT_ORDER:
            p = pools_by_meas[mid]["by_region"].get(region)
            if p:
                region_data[region][mid] = p
    for ab in all_age_bins:
        for mid in MEASUREMENT_ORDER:
            p = pools_by_meas[mid]["by_age"].get(ab)
            if p:
                age_data[ab][mid] = p

    regions_sorted = ["All"] + sorted(all_regions)
    age_bins_sorted = [b[0] for b in AGE_BINS if b[0] in all_age_bins]

    # Color palette: deterministic by combined key list.
    color_keys = ["All"] + age_bins_sorted + sorted(all_regions)
    group_colors = assign_colors(color_keys)

    # dimWeights: same defaults as before.
    dim_weights = {"cranial": 1.0, "ear": 2.0, "tragus": 1.0, "mastoid": 1.0, "bizygomatic": 1.0, "maskarcflex": 3.0}

    # bzProfiles / bzCross / mgState / mgControls preserved from prior JSON (mask-geometry section is unchanged).
    # We re-emit them by reading the existing file and copying the keys forward.
    prior_path = OUT_DIR / "measurements.us-adult.json"
    prior = {}
    if prior_path.exists():
        try:
            with prior_path.open() as f:
                prior = json.load(f)
        except json.JSONDecodeError:
            pass

    bz_profiles = prior.get("bzProfiles", [])
    bz_cross = prior.get("bzCross", [])
    mg_state = prior.get("mgState", {})
    mg_controls = prior.get("mgControls", [])

    out = {
        "measurements": measurements_out,
        "regions": regions_sorted,
        "ageBins": age_bins_sorted,
        "demographics": {
            "region": dict(region_data),
            "age": dict(age_data),
        },
        "groupColors": group_colors,
        "dimWeights": dim_weights,
        "bzProfiles": bz_profiles,
        "bzCross": bz_cross,
        "mgState": mg_state,
        "mgControls": mg_controls,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "measurements.us-adult.json"
    with json_path.open("w") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
        f.write("\n")
    js_path = OUT_DIR / "measurements.us-adult.js"
    with js_path.open("w") as f:
        f.write("window.IMT_DATA = ")
        f.write(json.dumps(out, indent=2, ensure_ascii=False))
        f.write(";\n")

    print(f"\nWrote {json_path}")
    print(f"Wrote {js_path}")
    print(f"  regions: {len(regions_sorted)} (incl. All)")
    print(f"  ageBins: {age_bins_sorted}")
    print(f"  measurements: {[m['id'] for m in measurements_out]}")


if __name__ == "__main__":
    main()
