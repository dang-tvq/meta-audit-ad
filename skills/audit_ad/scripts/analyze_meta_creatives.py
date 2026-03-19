import argparse
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# -----------------------------
# Column mapping + parsing
# -----------------------------

CANONICAL = {
    "creative_name": [
        "creative", "creative name", "ad name", "ad", "adname", "asset", "asset name",
        "thumbnail", "thumbnail name", "video", "name", "adset ad name"
    ],
    "spend": ["spend", "amount spent", "cost", "total spend", "spent", "chi tieu", "spending"],
    "impressions": ["impressions", "impr", "views", "lượt hiển thị", "hiển thị"],
    "clicks": [
        "clicks", "click", "link clicks", "link click", "outbound clicks",
        "unique link clicks", "lượt nhấp", "nhấp"
    ],
    "installs": [
        "installs", "install", "app installs", "mobile app installs", "app install",
        "mobile app install", "results", "conversions", "installs (app)", "lượt cài đặt"
    ],
    "cpm": ["cpm", "cost per 1,000 impressions", "cost per mille"],
    "ctr": [
        "ctr", "link ctr", "ctr (link)", "all ctr", "ctr (all)", "click-through rate",
        "link click-through rate"
    ],
    "cti": [
        "cti", "install rate", "click to install", "click-to-install", "cvr", "conversion rate",
        "app install rate", "install conversion rate"
    ],
    "cpi": ["cpi", "cost per install", "cost per app install", "cost per result"],
}

PREF_ORDER_CTR = ["link ctr", "ctr (link)", "ctr", "all ctr", "ctr (all)"]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())


def _parse_number(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    s = str(x).strip()
    if s == "" or s.lower() in {"nan", "none", "null", "-"}:
        return np.nan

    # remove currency symbols and spaces
    s = re.sub(r"[\$\u20ab\u00a3\u20ac]", "", s)  # $, VND sign, etc.
    s = s.replace(" ", "")

    # percent is handled upstream (we keep raw number)
    s = s.replace("%", "")

    # Heuristic for comma/dot
    # - If both present: treat comma as thousands sep -> remove commas
    # - If only comma present: treat comma as decimal sep if looks like decimal (<=2 digits after)
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s and "." not in s:
        parts = s.split(",")
        if len(parts) == 2 and len(parts[1]) in {1, 2}:
            s = ".".join(parts)
        else:
            s = "".join(parts)

    try:
        return float(s)
    except Exception:
        # fallback: extract first float-like token
        m = re.search(r"-?\d+(?:\.\d+)?", s)
        return float(m.group(0)) if m else np.nan


def _coerce_percent_to_fraction(series: pd.Series) -> pd.Series:
    # If values look like 0-100, convert to fraction
    s = series.astype(float)
    # If median > 1.5 => likely percent values
    med = np.nanmedian(s.values)
    if np.isfinite(med) and med > 1.5:
        return s / 100.0
    return s


@dataclass
class MappingResult:
    df: pd.DataFrame
    ctr_source: Optional[str]
    missing_required: List[str]


def canonicalize_columns(df: pd.DataFrame) -> MappingResult:
    original_cols = list(df.columns)
    norm_cols = [_norm(c) for c in original_cols]

    # build reverse index
    col_map: Dict[str, str] = {norm_cols[i]: original_cols[i] for i in range(len(original_cols))}

    chosen: Dict[str, Optional[str]] = {k: None for k in CANONICAL.keys()}

    # Pick CTR with preference (link ctr first)
    ctr_source = None
    for cand in PREF_ORDER_CTR:
        if cand in col_map:
            chosen["ctr"] = col_map[cand]
            ctr_source = cand
            break

    # Map other columns
    for canon, aliases in CANONICAL.items():
        if canon == "ctr":
            continue
        for a in aliases:
            a_norm = _norm(a)
            if a_norm in col_map:
                chosen[canon] = col_map[a_norm]
                break

    # Rename selected columns to canonical
    out = pd.DataFrame()
    for canon, src in chosen.items():
        if src is not None:
            out[canon] = df[src]

    # Ensure creative_name exists
    if "creative_name" not in out.columns:
        # fallback: first string-ish column
        for c in df.columns:
            if df[c].dtype == object:
                out["creative_name"] = df[c]
                break

    # Parse numerics
    for c in ["spend", "impressions", "clicks", "installs", "cpm", "ctr", "cti", "cpi"]:
        if c in out.columns:
            out[c] = out[c].map(_parse_number)

    # Convert ctr/cti to fraction if percent-like
    if "ctr" in out.columns:
        out["ctr"] = _coerce_percent_to_fraction(out["ctr"])
    if "cti" in out.columns:
        out["cti"] = _coerce_percent_to_fraction(out["cti"])

    # Derive missing metrics if possible
    if "cpm" not in out.columns and {"spend", "impressions"}.issubset(out.columns):
        out["cpm"] = (out["spend"] / out["impressions"]) * 1000
    if "ctr" not in out.columns and {"clicks", "impressions"}.issubset(out.columns):
        out["ctr"] = out["clicks"] / out["impressions"]
    if "cti" not in out.columns and {"installs", "clicks"}.issubset(out.columns):
        out["cti"] = out["installs"] / out["clicks"]
    if "cpi" not in out.columns and {"spend", "installs"}.issubset(out.columns):
        out["cpi"] = out["spend"] / out["installs"]

    # Required for analysis
    required_any = ["creative_name", "spend", "impressions", "clicks", "installs"]
    missing_required = [c for c in required_any if c not in out.columns]

    return MappingResult(df=out, ctr_source=ctr_source, missing_required=missing_required)


# -----------------------------
# Decomposition + clustering
# -----------------------------

def cpi_from_components(cpm: float, ctr: float, cti: float) -> float:
    if not np.isfinite(cpm) or not np.isfinite(ctr) or not np.isfinite(cti) or ctr <= 0 or cti <= 0:
        return np.nan
    return cpm / (1000.0 * ctr * cti)


def add_decomposition(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # medians
    med_cpm = np.nanmedian(out["cpm"].values) if "cpm" in out.columns else np.nan
    med_ctr = np.nanmedian(out["ctr"].values) if "ctr" in out.columns else np.nan
    med_cti = np.nanmedian(out["cti"].values) if "cti" in out.columns else np.nan

    base = cpi_from_components(med_cpm, med_ctr, med_cti)
    out["cpi_base_median"] = base

    out["cpi_cf_cpm"] = out.apply(lambda r: cpi_from_components(r.get("cpm", np.nan), med_ctr, med_cti), axis=1)
    out["cpi_cf_ctr"] = out.apply(lambda r: cpi_from_components(med_cpm, r.get("ctr", np.nan), med_cti), axis=1)
    out["cpi_cf_cti"] = out.apply(lambda r: cpi_from_components(med_cpm, med_ctr, r.get("cti", np.nan)), axis=1)

    out["delta_cpm"] = out["cpi_cf_cpm"] - base
    out["delta_ctr"] = out["cpi_cf_ctr"] - base
    out["delta_cti"] = out["cpi_cf_cti"] - base

    # Contribution share for gap direction
    def _shares(row):
        deltas = np.array([row["delta_cpm"], row["delta_ctr"], row["delta_cti"]], dtype=float)
        if not np.all(np.isfinite(deltas)):
            return pd.Series({"share_cpm": np.nan, "share_ctr": np.nan, "share_cti": np.nan})
        gap = row.get("cpi", np.nan) - base
        if not np.isfinite(gap) or gap == 0:
            return pd.Series({"share_cpm": 0.0, "share_ctr": 0.0, "share_cti": 0.0})
        # if gap positive (worse): only positive deltas count; if gap negative (better): only negative deltas count (absolute)
        if gap > 0:
            contrib = np.maximum(deltas, 0)
        else:
            contrib = np.maximum(-deltas, 0)
        s = contrib.sum()
        if s <= 0:
            return pd.Series({"share_cpm": np.nan, "share_ctr": np.nan, "share_cti": np.nan})
        return pd.Series({"share_cpm": contrib[0]/s, "share_ctr": contrib[1]/s, "share_cti": contrib[2]/s})

    shares = out.apply(_shares, axis=1)
    out = pd.concat([out, shares], axis=1)

    return out


def add_clusters(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    med_ctr = np.nanmedian(out["ctr"].values)
    med_cti = np.nanmedian(out["cti"].values)
    med_cpm = np.nanmedian(out["cpm"].values)

    def label(row):
        cpm = row.get("cpm", np.nan)
        ctr = row.get("ctr", np.nan)
        cti = row.get("cti", np.nan)
        if not (np.isfinite(cpm) and np.isfinite(ctr) and np.isfinite(cti)):
            return "Không đủ dữ liệu"
        ctr_high = ctr >= med_ctr
        cti_high = cti >= med_cti
        cpm_high = cpm >= med_cpm

        if ctr_high and (not cti_high):
            return "Hook mạnh – intent yếu"
        if (not ctr_high) and cti_high:
            return "Hook yếu – intent mạnh"
        if cpm_high and ctr_high and cti_high:
            return "Auction đắt nhưng convert tốt"
        if (not cpm_high) and (not ctr_high) and (not cti_high):
            return "Toàn funnel yếu"
        return "Trung tính / hỗn hợp"

    out["cluster"] = out.apply(label, axis=1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to CSV/XLSX")
    ap.add_argument("--sheet", default=None, help="Sheet name for XLSX")
    ap.add_argument("--output", default="cleaned_output.csv", help="Output CSV path")
    args = ap.parse_args()

    if args.input.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(args.input, sheet_name=args.sheet)
    else:
        df = pd.read_csv(args.input)

    mapped = canonicalize_columns(df)
    out = mapped.df

    out = add_decomposition(out) if {"cpm", "ctr", "cti", "cpi"}.issubset(out.columns) else out
    out = add_clusters(out) if {"cpm", "ctr", "cti"}.issubset(out.columns) else out

    out.to_csv(args.output, index=False)

    print("[OK] wrote", args.output)
    if mapped.ctr_source:
        print("[INFO] CTR source picked:", mapped.ctr_source)
    if mapped.missing_required:
        print("[WARN] Missing required columns:", ", ".join(mapped.missing_required))


if __name__ == "__main__":
    main()
