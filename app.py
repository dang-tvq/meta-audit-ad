from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("META_AD_ANALYZER_DATA_DIR", str(APP_DIR / "data"))).expanduser()
MEDIA_DIR = DATA_DIR / "media"
DB_PATH = DATA_DIR / "creative_assets.db"

METRIC_COLUMNS = ["cpm", "ctr", "cti", "cpi"]
COLUMN_ALIASES_PATH = DATA_DIR / "column_aliases.json"
SKILL_BUNDLE_DIR = APP_DIR / "skills"
AUDIT_SKILL_PATH = os.getenv("AUDIT_AD_SKILL_PATH", "")

DEFAULT_COLUMN_ALIASES = {
    "campaign_name": ["campaign_name", "campaign name", "campaign"],
    "adset_name": ["adset_name", "adset name", "ad set", "adset"],
    "ad_name": ["ad_name", "ad name", "ad", "creative_name", "name"],
    "spend": ["amount spent", "amount_spent", "amount spend", "spend"],
    "impressions": ["impressions", "impr"],
    "clicks": ["clicks", "link_clicks", "all_clicks", "click (all)"],
    "installs": ["installs", "app_installs", "mobile_app_install", "conversions", "results"],
    "cpm": ["cpm (cost per 1,000 impressions)", "cpm"],
    "ctr": ["ctr (all)", "ctr"],
    "cti": ["cti"],
    "cpi": ["cost per result", "cpi", "cost per install"],
}


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    ensure_directories()
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS creative_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creative_name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                media_type TEXT NOT NULL,
                file_path TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_creative_assets_normalized_name
            ON creative_assets(normalized_name)
            """
        )


def load_column_aliases() -> dict[str, list[str]]:
    aliases = {key: value[:] for key, value in DEFAULT_COLUMN_ALIASES.items()}
    if not COLUMN_ALIASES_PATH.exists():
        return aliases

    try:
        with open(COLUMN_ALIASES_PATH, "r", encoding="utf-8") as file:
            raw = json.load(file)
    except (OSError, json.JSONDecodeError):
        return aliases

    if not isinstance(raw, dict):
        return aliases

    for key, values in raw.items():
        if key not in aliases:
            continue
        if isinstance(values, list):
            cleaned = [str(item).strip().casefold() for item in values if str(item).strip()]
            if cleaned:
                aliases[key] = cleaned
    return aliases


def resolve_audit_skill_path() -> Path | None:
    candidates: list[Path] = []

    if AUDIT_SKILL_PATH:
        candidates.append(Path(AUDIT_SKILL_PATH).expanduser())

    candidates.extend(
        [
            SKILL_BUNDLE_DIR / "audit_ad" / "SKILL.md",
            SKILL_BUNDLE_DIR / "audit_ad" / "meta-ads-creative-analyst.md",
            Path("/Users/lap60572/.codex/skills/Audit ad/meta-ads-creative-analyst 2/SKILL.md"),
            Path("/Users/lap60572/.codex/skills/Audit ad/meta-ads-creative-analyst.md"),
        ]
    )

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    return None


def load_audit_skill_text() -> tuple[str, str]:
    path = resolve_audit_skill_path()
    if path is None:
        return "", "No skill file found"
    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return "", str(path)
    return content, str(path)


def normalize_name(value: str) -> str:
    text = str(value or "").strip().casefold()
    text = re.sub(r"\.[^.]+$", "", text)
    text = re.sub(r"[_\-|]+", " ", text)
    text = re.sub(r"[^\w\s]+", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_media_type(file_name: str, mime: str | None) -> str:
    extension = Path(file_name).suffix.lower()
    if mime and mime.startswith("video"):
        return "video"
    if mime and mime.startswith("image"):
        return "image"
    if extension in {".mp4", ".mov", ".m4v", ".avi", ".webm", ".mkv"}:
        return "video"
    return "image"


def save_uploaded_files(uploaded_files: Iterable[st.runtime.uploaded_file_manager.UploadedFile]) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    with get_connection() as conn:
        existing_names = {
            row["normalized_name"]
            for row in conn.execute("SELECT normalized_name FROM creative_assets").fetchall()
        }
        for uploaded in uploaded_files:
            suffix = Path(uploaded.name).suffix.lower() or ".bin"
            media_type = detect_media_type(uploaded.name, uploaded.type)
            creative_name = Path(uploaded.name).stem.strip() or f"creative_{uuid.uuid4().hex[:8]}"
            normalized = normalize_name(creative_name)

            # Skip duplicate creative names (normalized) to keep one canonical asset per name.
            if normalized in existing_names:
                skipped += 1
                continue

            unique_name = f"{uuid.uuid4().hex}{suffix}"
            target_path = MEDIA_DIR / unique_name

            with open(target_path, "wb") as output:
                output.write(uploaded.getbuffer())

            try:
                conn.execute(
                    """
                    INSERT INTO creative_assets (
                        creative_name,
                        normalized_name,
                        media_type,
                        file_path,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        creative_name,
                        normalized,
                        media_type,
                        str(target_path),
                        datetime.utcnow().isoformat(timespec="seconds"),
                    ),
                )
                inserted += 1
                existing_names.add(normalized)
            except sqlite3.IntegrityError:
                skipped += 1
                if target_path.exists():
                    target_path.unlink(missing_ok=True)

    return inserted, skipped


def list_creatives() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT id, creative_name, normalized_name, media_type, file_path, created_at
            FROM creative_assets
            ORDER BY id DESC
            """,
            conn,
        )
    return df


def delete_creatives(ids: list[int]) -> int:
    if not ids:
        return 0

    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT id, file_path FROM creative_assets WHERE id IN ({','.join('?' for _ in ids)})",
            ids,
        ).fetchall()
        for row in rows:
            path = Path(row["file_path"])
            if path.exists():
                path.unlink(missing_ok=True)

        conn.execute(
            f"DELETE FROM creative_assets WHERE id IN ({','.join('?' for _ in ids)})",
            ids,
        )
    return len(rows)


def guess_column(columns: list[str], candidates: list[str]) -> str | None:
    lowered = {col.casefold(): col for col in columns}
    for key in candidates:
        if key in lowered:
            return lowered[key]

    for col in columns:
        name = col.casefold()
        if any(candidate in name for candidate in candidates):
            return col
    return None


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, np.nan)
    return numerator / denominator


def parse_numeric_value(value: object, as_rate: bool = False) -> float:
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    if not text or text.casefold() in {"nan", "none", "null", "n/a", "-"}:
        return np.nan

    has_percent = "%" in text
    text = text.replace(" ", "")
    text = re.sub(r"[^0-9,.\-+]", "", text)
    if not text:
        return np.nan

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "")
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        if re.search(r",\d{3}(,|$)", text):
            text = text.replace(",", "")
        else:
            text = text.replace(",", ".")

    try:
        number = float(text)
    except ValueError:
        return np.nan

    if as_rate:
        if has_percent or number > 1:
            number /= 100.0
        number = max(number, 0.0)

    return number


def to_numeric(series: pd.Series) -> pd.Series:
    return series.map(parse_numeric_value)


def parse_rate_series(series: pd.Series, mode: str = "auto", metric: str = "ctr") -> pd.Series:
    raw = series.astype(str).str.strip()
    raw_has_percent = raw.str.contains("%", regex=False, na=False)
    numeric = raw.map(lambda value: parse_numeric_value(value, as_rate=False))

    if mode == "percent":
        return numeric / 100.0

    if mode == "ratio":
        # Keep ratio values as-is, but values containing '%' still mean percent points.
        rates = np.where(raw_has_percent, numeric / 100.0, numeric)
        return pd.Series(rates, index=series.index, dtype="float64")

    # Auto mode:
    # 1) If literal '%' exists -> treat those as percent.
    rates = np.where(raw_has_percent, numeric / 100.0, numeric)
    rates = pd.Series(rates, index=series.index, dtype="float64")

    # 2) Heuristic for CTR only:
    # some exports store 0.73 to mean 0.73% (instead of 73%).
    finite = rates[np.isfinite(rates)]
    if metric in {"ctr", "cti"} and not finite.empty:
        def should_convert_to_percent_points(values: pd.Series) -> bool:
            if values.empty:
                return False
            vmax = float(values.max())
            q75 = float(values.quantile(0.75))
            q95 = float(values.quantile(0.95))
            # Ratios above 1.0 are impossible for CTR/CTI -> likely percent points.
            if vmax > 1.0 and vmax <= 100.0:
                return True
            # Typical Meta export without '%' often stores 0.73 = 0.73%.
            return q75 > 0.2 and q95 <= 1.0

        if not raw_has_percent.any():
            if should_convert_to_percent_points(finite):
                rates = rates / 100.0
        else:
            non_pct = rates[~raw_has_percent & np.isfinite(rates)]
            if should_convert_to_percent_points(non_pct):
                rates.loc[~raw_has_percent] = rates.loc[~raw_has_percent] / 100.0

    return rates


def first_non_empty(series: pd.Series) -> object:
    for value in series:
        if pd.notna(value) and str(value).strip() != "":
            return value
    return np.nan


def build_metric_table(
    raw_df: pd.DataFrame,
    ad_name_col: str,
    spend_col: str,
    impressions_col: str,
    clicks_col: str | None = None,
    installs_col: str | None = None,
    campaign_name_col: str | None = None,
    adset_name_col: str | None = None,
    cpm_col: str | None = None,
    ctr_col: str | None = None,
    cti_col: str | None = None,
    cpi_col: str | None = None,
    ctr_unit_mode: str = "auto",
    cti_unit_mode: str = "auto",
    extra_table_cols: list[str] | None = None,
) -> pd.DataFrame:
    # Build a fresh metric frame so duplicate source-column mapping never removes required fields.
    df = pd.DataFrame(
        {
            "ad_name": raw_df[ad_name_col],
            "spend": raw_df[spend_col],
            "impressions": raw_df[impressions_col],
            "clicks": raw_df[clicks_col] if clicks_col and clicks_col in raw_df.columns else np.nan,
            "installs": raw_df[installs_col] if installs_col and installs_col in raw_df.columns else np.nan,
        }
    )

    if campaign_name_col and campaign_name_col in raw_df.columns:
        df["campaign_name"] = raw_df[campaign_name_col]
    else:
        df["campaign_name"] = "(Unknown Campaign)"

    if adset_name_col and adset_name_col in raw_df.columns:
        df["adset_name"] = raw_df[adset_name_col]
    else:
        df["adset_name"] = "(Unknown Adset)"

    if cpm_col and cpm_col in raw_df.columns:
        df["_cpm_override"] = to_numeric(raw_df[cpm_col])
    if ctr_col and ctr_col in raw_df.columns:
        df["_ctr_override"] = parse_rate_series(raw_df[ctr_col], mode=ctr_unit_mode, metric="ctr")
    if cti_col and cti_col in raw_df.columns:
        df["_cti_override"] = parse_rate_series(raw_df[cti_col], mode=cti_unit_mode, metric="cti")
    if cpi_col and cpi_col in raw_df.columns:
        df["_cpi_override"] = to_numeric(raw_df[cpi_col])

    selected_extra_cols = [col for col in (extra_table_cols or []) if col in raw_df.columns]
    used_source_cols = {
        ad_name_col,
        spend_col,
        impressions_col,
        clicks_col,
        installs_col,
        campaign_name_col,
        adset_name_col,
        cpm_col,
        ctr_col,
        cti_col,
        cpi_col,
    }
    selected_extra_cols = [col for col in selected_extra_cols if col not in used_source_cols]
    for col in selected_extra_cols:
        df[col] = raw_df[col]

    df["ad_name"] = df["ad_name"].astype(str).str.strip()
    df["campaign_name"] = df["campaign_name"].astype(str).str.strip()
    df["adset_name"] = df["adset_name"].astype(str).str.strip()
    df.loc[df["campaign_name"] == "", "campaign_name"] = "(Unknown Campaign)"
    df.loc[df["adset_name"] == "", "adset_name"] = "(Unknown Adset)"
    df = df[df["ad_name"] != ""].copy()

    for col in ["spend", "impressions", "clicks", "installs"]:
        df[col] = to_numeric(df[col])

    if "_ctr_override" in df.columns:
        estimated_clicks = df["_ctr_override"] * df["impressions"]
        df["clicks"] = np.where((df["clicks"] > 0) & np.isfinite(df["clicks"]), df["clicks"], estimated_clicks)

    if "_cti_override" in df.columns:
        estimated_installs = df["_cti_override"] * df["clicks"]
        df["installs"] = np.where((df["installs"] > 0) & np.isfinite(df["installs"]), df["installs"], estimated_installs)

    if "_cpi_override" in df.columns:
        estimated_installs_from_cpi = safe_divide(df["spend"], df["_cpi_override"])
        df["installs"] = np.where(
            (df["installs"] > 0) & np.isfinite(df["installs"]),
            df["installs"],
            estimated_installs_from_cpi,
        )

    for col in ["spend", "impressions", "clicks", "installs"]:
        df[col] = df[col].fillna(0.0)

    df["normalized_name"] = df["ad_name"].map(normalize_name)
    group_keys = ["campaign_name", "adset_name", "ad_name", "normalized_name"]

    agg_spec: dict[str, object] = {
        "spend": "sum",
        "impressions": "sum",
        "clicks": "sum",
        "installs": "sum",
    }
    for col in ["_cpm_override", "_ctr_override", "_cti_override", "_cpi_override"]:
        if col in df.columns:
            agg_spec[col] = "mean"
    for col in selected_extra_cols:
        agg_spec[col] = first_non_empty

    df = df.groupby(group_keys, as_index=False).agg(agg_spec)

    df["ctr"] = safe_divide(df["clicks"], df["impressions"])
    df["cpm"] = safe_divide(df["spend"] * 1000.0, df["impressions"])
    df["cti"] = safe_divide(df["installs"], df["clicks"])
    df["cpi"] = safe_divide(df["spend"], df["installs"])

    if "_cpm_override" in df.columns:
        df["cpm"] = np.where(np.isfinite(df["cpm"]) & (df["cpm"] > 0), df["cpm"], df["_cpm_override"])
    if "_ctr_override" in df.columns:
        df["ctr"] = np.where(np.isfinite(df["ctr"]) & (df["ctr"] > 0), df["ctr"], df["_ctr_override"])
    if "_cti_override" in df.columns:
        df["cti"] = np.where(np.isfinite(df["cti"]) & (df["cti"] > 0), df["cti"], df["_cti_override"])
    if "_cpi_override" in df.columns:
        df["cpi"] = np.where(np.isfinite(df["cpi"]) & (df["cpi"] > 0), df["cpi"], df["_cpi_override"])

    return df


def latest_creatives_by_name() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            WITH latest AS (
                SELECT normalized_name, MAX(id) AS max_id
                FROM creative_assets
                GROUP BY normalized_name
            )
            SELECT c.id, c.creative_name, c.normalized_name, c.media_type, c.file_path
            FROM creative_assets c
            INNER JOIN latest l ON c.id = l.max_id
            """,
            conn,
        )
    return df


def calculate_benchmark(df: pd.DataFrame) -> dict[str, float]:
    benchmark: dict[str, float] = {}
    for metric in METRIC_COLUMNS:
        values = df[metric].replace([np.inf, -np.inf], np.nan).dropna()
        values = values[values > 0]
        benchmark[metric] = float(values.median()) if not values.empty else np.nan
    return benchmark


def classify_driver(row: pd.Series, benchmark: dict[str, float]) -> str:
    if any(np.isnan(benchmark[m]) for m in METRIC_COLUMNS):
        return "insufficient benchmark data"
    if not np.isfinite(row["cpi"]) or row["cpi"] <= 0:
        return "insufficient row data"

    effects = {
        "low CPM": np.log(benchmark["cpm"] / row["cpm"]) if row["cpm"] > 0 else np.nan,
        "high CTR": np.log(row["ctr"] / benchmark["ctr"]) if row["ctr"] > 0 else np.nan,
        "high CTI": np.log(row["cti"] / benchmark["cti"]) if row["cti"] > 0 else np.nan,
    }
    valid_effects = {k: v for k, v in effects.items() if np.isfinite(v)}
    if not valid_effects:
        return "insufficient row data"

    if row["cpi"] < benchmark["cpi"]:
        top_driver = max(valid_effects, key=valid_effects.get)
        return f"WIN by {top_driver}"

    top_driver = min(valid_effects, key=valid_effects.get)
    if top_driver == "low CPM":
        return "LOSS due to high CPM"
    if top_driver == "high CTR":
        return "LOSS due to low CTR"
    return "LOSS due to low CTI"


def load_csv(file_obj) -> pd.DataFrame:
    try:
        return pd.read_csv(file_obj, sep=None, engine="python")
    except UnicodeDecodeError:
        file_obj.seek(0)
        return pd.read_csv(file_obj, sep=None, engine="python", encoding="latin-1")


def format_percent(value: float) -> str:
    if pd.isna(value) or not np.isfinite(value):
        return "-"
    return f"{value * 100:.2f}%"


def format_number(value: float, digits: int = 2) -> str:
    if pd.isna(value) or not np.isfinite(value):
        return "-"
    return f"{value:,.{digits}f}"


def short_label(value: str, max_len: int = 36) -> str:
    text = str(value or "").strip()
    if len(text) <= max_len:
        return text
    return f"{text[: max_len - 3]}..."


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.strip().lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _lerp_color(low_hex: str, high_hex: str, t: float) -> tuple[int, int, int]:
    low = _hex_to_rgb(low_hex)
    high = _hex_to_rgb(high_hex)
    t = min(1.0, max(0.0, float(t)))
    return (
        int(round(low[0] + (high[0] - low[0]) * t)),
        int(round(low[1] + (high[1] - low[1]) * t)),
        int(round(low[2] + (high[2] - low[2]) * t)),
    )


def make_gradient_styles(series: pd.Series, low_hex: str = "#DCEBFF", high_hex: str = "#1F4AA8") -> list[str]:
    numeric = pd.to_numeric(series, errors="coerce")
    finite = numeric[np.isfinite(numeric)]
    if finite.empty:
        return [""] * len(series)

    low = float(finite.min())
    high = float(finite.max())
    styles: list[str] = []
    for value in numeric:
        if not np.isfinite(value):
            styles.append("")
            continue

        t = 0.0 if high == low else (float(value) - low) / (high - low)
        r, g, b = _lerp_color(low_hex, high_hex, t)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        text_color = "#0F172A" if luminance > 0.62 else "#F8FAFC"
        styles.append(f"background-color: rgb({r},{g},{b}); color: {text_color};")
    return styles


def build_skill_thresholds(
    df: pd.DataFrame,
    use_manual: bool,
    cpi_good_input: float,
    cpi_bad_input: float,
    min_spend_for_decision: float,
) -> dict[str, float]:
    valid = df.copy()
    valid = valid[np.isfinite(valid["cpi"]) & (valid["cpi"] > 0)]
    if valid.empty:
        return {
            "cpi_good": np.nan,
            "cpi_bad": np.nan,
            "cpm_high": np.nan,
            "ctr_low": np.nan,
            "cti_low": np.nan,
            "min_spend": min_spend_for_decision,
        }

    cpi_good = cpi_good_input if use_manual and cpi_good_input > 0 else float(valid["cpi"].quantile(0.25))
    cpi_bad = cpi_bad_input if use_manual and cpi_bad_input > 0 else float(valid["cpi"].quantile(0.75))
    cpm_high = float(valid["cpm"].replace([np.inf, -np.inf], np.nan).dropna().quantile(0.75))
    ctr_low = float(valid["ctr"].replace([np.inf, -np.inf], np.nan).dropna().quantile(0.25))
    cti_low = float(valid["cti"].replace([np.inf, -np.inf], np.nan).dropna().quantile(0.25))

    return {
        "cpi_good": cpi_good,
        "cpi_bad": cpi_bad,
        "cpm_high": cpm_high,
        "ctr_low": ctr_low,
        "cti_low": cti_low,
        "min_spend": min_spend_for_decision,
    }


def evaluate_with_audit_skill(row: pd.Series, thresholds: dict[str, float]) -> tuple[str, str]:
    if row["spend"] < thresholds["min_spend"]:
        return "⏳ CHỜ THÊM DATA", "⏳ CHỜ THÊM DATA"

    cpi = row.get("cpi", np.nan)
    if not np.isfinite(cpi) or cpi <= 0:
        return "⏳ CHỜ THÊM DATA", "⏳ CHỜ THÊM DATA"

    if cpi <= thresholds["cpi_good"]:
        return "✅ WORK", "🚀 SCALE"

    if cpi > thresholds["cpi_bad"]:
        ctr = row.get("ctr", np.nan)
        cpm = row.get("cpm", np.nan)
        if np.isfinite(ctr) and np.isfinite(cpm) and ctr < thresholds["ctr_low"] and cpm > thresholds["cpm_high"]:
            return "❌ KHÔNG WORK", "❌ TẮT"
        return "❌ KHÔNG WORK", "❌ TẮT"

    return "⚠️ TRUNG BÌNH", "⚠️ THEO DÕI"


def build_ai_conclusion(df: pd.DataFrame, benchmark: dict[str, float]) -> str:
    if df.empty:
        return "Chưa có dữ liệu hợp lệ để kết luận."

    valid_df = df[np.isfinite(df["cpi"]) & (df["cpi"] > 0)].copy()
    if valid_df.empty or not np.isfinite(benchmark.get("cpi", np.nan)):
        return "Không đủ dữ liệu CPI để kết luận."

    winners = valid_df[valid_df["audit_status"] == "✅ WORK"].copy() if "audit_status" in valid_df.columns else valid_df[valid_df["cpi"] < benchmark["cpi"]].copy()
    losers = valid_df[valid_df["audit_status"] == "❌ KHÔNG WORK"].copy() if "audit_status" in valid_df.columns else valid_df[valid_df["cpi"] >= benchmark["cpi"]].copy()
    top_winner = winners.sort_values(["cpi", "installs"], ascending=[True, False]).head(1)
    top_loser = losers.sort_values(["cpi", "installs"], ascending=[False, False]).head(1)
    driver_counts = winners["win_driver"].value_counts()
    top_driver = driver_counts.index[0] if not driver_counts.empty else "N/A"

    scale_df = valid_df[valid_df.get("audit_action", "") == "🚀 SCALE"] if "audit_action" in valid_df.columns else winners
    off_df = valid_df[valid_df.get("audit_action", "") == "❌ TẮT"] if "audit_action" in valid_df.columns else losers
    wait_df = df[df.get("audit_action", "") == "⏳ CHỜ THÊM DATA"] if "audit_action" in df.columns else pd.DataFrame()

    lines: list[str] = [
        f"- CPI benchmark hiện tại: **${benchmark['cpi']:.4f}**.",
        f"- Creative đang work: **{len(winners)}/{len(valid_df)}** ads có CPI thấp hơn benchmark.",
        f"- Driver thắng nổi bật nhất: **{top_driver}**.",
    ]

    if not top_winner.empty:
        row = top_winner.iloc[0]
        lines.append(
            f"- Top winner: **{row['ad_name']}** (CPI ${row['cpi']:.4f}, CTR {row['ctr']*100:.2f}%, CTI {row['cti']*100:.2f}%)."
        )

    if not top_loser.empty:
        row = top_loser.iloc[0]
        lines.append(
            f"- Cần tối ưu gấp: **{row['ad_name']}** (CPI ${row['cpi']:.4f}) - {row['win_driver']}."
        )

    if not scale_df.empty:
        names = ", ".join(short_label(name, 28) for name in scale_df["ad_name"].head(5).tolist())
        lines.append(f"- Danh sách SCALE: {names}.")
    if not off_df.empty:
        names = ", ".join(short_label(name, 28) for name in off_df["ad_name"].head(5).tolist())
        lines.append(f"- Danh sách TẮT: {names}.")
    if not wait_df.empty:
        names = ", ".join(short_label(name, 28) for name in wait_df["ad_name"].head(5).tolist())
        lines.append(f"- Chờ thêm data: {names}.")

    lines.append(
        "- Khuyến nghị: scale nhóm winner theo driver tốt nhất; với loser, ưu tiên tối ưu hook/CTA nếu CTR thấp, hoặc landing/store flow nếu CTI thấp."
    )
    return "\n".join(lines)


def show_creative_preview(row: pd.Series) -> None:
    path = row.get("file_path")
    if not isinstance(path, (str, os.PathLike)) or not str(path).strip() or not os.path.exists(path):
        st.caption("No creative found")
        return

    if row.get("media_type") == "video":
        st.video(path)
    else:
        st.image(path, width="stretch")


def render_creative_library() -> None:
    st.subheader("Creative Library")
    uploaded_files = st.file_uploader(
        "Upload creative images/videos",
        type=["png", "jpg", "jpeg", "webp", "gif", "mp4", "mov", "m4v", "avi", "webm", "mkv"],
        accept_multiple_files=True,
        help="File name (without extension) will be used as creative name for matching.",
    )

    if st.button("Save uploads", type="primary", disabled=not uploaded_files):
        inserted, skipped = save_uploaded_files(uploaded_files)
        st.success(f"Saved {inserted} files. Skipped {skipped} duplicates.")

    creative_df = list_creatives()
    if creative_df.empty:
        st.info("No creative in library yet.")
        return

    st.dataframe(
        creative_df,
        width="stretch",
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "file_path": st.column_config.TextColumn("File Path", width="large"),
        },
    )

    delete_all = st.checkbox("ALL", value=False, help="Delete all creative records in the library.")
    selected_ids = st.multiselect(
        "Delete selected creative IDs",
        creative_df["id"].tolist(),
        disabled=delete_all,
    )
    ids_to_delete = creative_df["id"].tolist() if delete_all else selected_ids

    if st.button("Delete selected", disabled=not ids_to_delete):
        deleted = delete_creatives(ids_to_delete)
        st.warning(f"Deleted {deleted} records.")
        st.rerun()


def render_analysis() -> None:
    st.subheader("CSV Analysis")

    csv_file = st.file_uploader("Upload CSV metrics file", type=["csv"], key="analysis_csv")
    if not csv_file:
        st.info("Upload CSV to start analysis.")
        return

    raw_df = load_csv(csv_file)
    if raw_df.empty:
        st.error("CSV is empty.")
        return

    columns = raw_df.columns.tolist()
    aliases = load_column_aliases()
    guesses = {
        "campaign_name": guess_column(columns, aliases["campaign_name"]),
        "adset_name": guess_column(columns, aliases["adset_name"]),
        "ad_name": guess_column(columns, aliases["ad_name"]),
        "spend": guess_column(columns, aliases["spend"]),
        "impressions": guess_column(columns, aliases["impressions"]),
        "clicks": guess_column(columns, aliases["clicks"]),
        "installs": guess_column(columns, aliases["installs"]),
        "cpm": guess_column(columns, aliases["cpm"]),
        "ctr": guess_column(columns, aliases["ctr"]),
        "cti": guess_column(columns, aliases["cti"]),
        "cpi": guess_column(columns, aliases["cpi"]),
    }

    campaign_name_col = guesses["campaign_name"]
    adset_name_col = guesses["adset_name"]
    ad_name_col = guesses["ad_name"]
    spend_col = guesses["spend"]
    impressions_col = guesses["impressions"]
    clicks_col = guesses["clicks"]
    installs_col = guesses["installs"]
    cpm_col = guesses["cpm"]
    ctr_col = guesses["ctr"]
    cti_col = guesses["cti"]
    cpi_col = guesses["cpi"]
    # Meta export commonly stores CTR/CTI as percent points (e.g. 0.73 means 0.73%).
    ctr_unit_mode = "percent"
    cti_unit_mode = "percent"

    st.caption("Column mapping đang chạy auto. Mở mục Advanced mapping chỉ khi cần chỉnh tay.")
    with st.expander("Advanced mapping (optional)", expanded=False):
        optional_columns = ["(none)"] + columns
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            campaign_name_ui = st.selectbox(
                "Campaign Name (optional)",
                optional_columns,
                index=optional_columns.index(campaign_name_col) if campaign_name_col else 0,
            )
        with c2:
            adset_name_ui = st.selectbox(
                "Adset Name (optional)",
                optional_columns,
                index=optional_columns.index(adset_name_col) if adset_name_col else 0,
            )
        with c3:
            ad_name_col = st.selectbox(
                "Ad Name",
                columns,
                index=columns.index(ad_name_col) if ad_name_col else 0,
            )
        with c4:
            spend_col = st.selectbox(
                "Spend",
                columns,
                index=columns.index(spend_col) if spend_col else 0,
            )

        c5, c6, c7 = st.columns(3)
        with c5:
            impressions_col = st.selectbox(
                "Impressions",
                columns,
                index=columns.index(impressions_col) if impressions_col else 0,
            )
        with c6:
            clicks_ui = st.selectbox(
                "Clicks (optional)",
                optional_columns,
                index=optional_columns.index(clicks_col) if clicks_col else 0,
            )
        with c7:
            installs_ui = st.selectbox(
                "Installs (optional)",
                optional_columns,
                index=optional_columns.index(installs_col) if installs_col else 0,
            )

        c8, c9, c10, c11 = st.columns(4)
        with c8:
            cpm_ui = st.selectbox(
                "CPM (optional, from CSV)",
                optional_columns,
                index=optional_columns.index(cpm_col) if cpm_col else 0,
            )
        with c9:
            ctr_ui = st.selectbox(
                "CTR (optional, from CSV)",
                optional_columns,
                index=optional_columns.index(ctr_col) if ctr_col else 0,
            )
        with c10:
            cti_ui = st.selectbox(
                "CTI (optional, from CSV)",
                optional_columns,
                index=optional_columns.index(cti_col) if cti_col else 0,
            )
        with c11:
            cpi_ui = st.selectbox(
                "CPI (optional, from CSV)",
                optional_columns,
                index=optional_columns.index(cpi_col) if cpi_col else 0,
            )

        rate_mode_labels = [
            "Auto",
            "Percent (0.73 = 0.73%)",
            "Ratio (0.0073 = 0.73%)",
        ]
        mode_label_to_value = {
            "Auto": "auto",
            "Percent (0.73 = 0.73%)": "percent",
            "Ratio (0.0073 = 0.73%)": "ratio",
        }
        r1, r2 = st.columns(2)
        with r1:
            ctr_mode_label = st.selectbox("CTR unit mode", rate_mode_labels, index=1)
        with r2:
            cti_mode_label = st.selectbox("CTI unit mode", rate_mode_labels, index=1)

        campaign_name_col = None if campaign_name_ui == "(none)" else campaign_name_ui
        adset_name_col = None if adset_name_ui == "(none)" else adset_name_ui
        clicks_col = None if clicks_ui == "(none)" else clicks_ui
        installs_col = None if installs_ui == "(none)" else installs_ui
        cpm_col = None if cpm_ui == "(none)" else cpm_ui
        ctr_col = None if ctr_ui == "(none)" else ctr_ui
        cti_col = None if cti_ui == "(none)" else cti_ui
        cpi_col = None if cpi_ui == "(none)" else cpi_ui
        ctr_unit_mode = mode_label_to_value[ctr_mode_label]
        cti_unit_mode = mode_label_to_value[cti_mode_label]

    used_mapping_cols = {
        ad_name_col,
        spend_col,
        impressions_col,
        clicks_col,
        installs_col,
        campaign_name_col,
        adset_name_col,
        cpm_col,
        ctr_col,
        cti_col,
        cpi_col,
    }
    additional_options = [col for col in columns if col not in used_mapping_cols]
    extra_table_cols = st.multiselect(
        "Additional columns to display in table",
        options=additional_options,
        default=[],
        help="Các cột core đã có mặc định. Dùng mục này để bật thêm cột bạn muốn xem.",
    )

    missing_required = [name for name, value in {"Ad Name": ad_name_col, "Spend": spend_col, "Impressions": impressions_col}.items() if not value]
    if missing_required:
        st.error(f"Missing required mapping: {', '.join(missing_required)}")
        return

    base_mapping = [ad_name_col, spend_col, impressions_col]
    if len(set(base_mapping)) < len(base_mapping):
        st.warning(
            "Bạn đang map trùng giữa các cột bắt buộc. Tool vẫn chạy, nhưng kết quả có thể sai. "
            "Nên chọn mỗi chỉ số từ một cột riêng."
        )

    metrics_df = build_metric_table(
        raw_df=raw_df,
        ad_name_col=ad_name_col,
        spend_col=spend_col,
        impressions_col=impressions_col,
        clicks_col=clicks_col,
        installs_col=installs_col,
        campaign_name_col=campaign_name_col,
        adset_name_col=adset_name_col,
        cpm_col=cpm_col,
        ctr_col=ctr_col,
        cti_col=cti_col,
        cpi_col=cpi_col,
        ctr_unit_mode=ctr_unit_mode,
        cti_unit_mode=cti_unit_mode,
        extra_table_cols=extra_table_cols,
    )

    if metrics_df.empty:
        st.error("No valid ad rows after mapping.")
        return

    st.markdown("#### Filters")
    min_installs = st.number_input("Minimum installs", min_value=0, value=0, step=1)
    only_with_creative = st.checkbox("Only rows matched with creative", value=False)
    preview_limit = st.slider("Preview rows", min_value=1, max_value=50, value=10)

    st.markdown("#### Audit Skill Settings")
    skill_text, skill_path = load_audit_skill_text()
    if skill_text:
        st.caption(f"Đang áp dụng rubric từ skill: `{skill_path}`")
    else:
        st.warning(f"Không đọc được skill file tại `{skill_path}`. Tool sẽ dùng logic fallback.")

    s1, s2, s3 = st.columns(3)
    with s1:
        use_manual_benchmark = st.checkbox("Manual CPI benchmark", value=False)
    with s2:
        cpi_good_input = st.number_input("CPI tốt (<=)", min_value=0.0, value=0.0, step=0.01, format="%.4f")
    with s3:
        cpi_bad_input = st.number_input("CPI kém (>)", min_value=0.0, value=0.0, step=0.01, format="%.4f")
    min_spend_for_decision = st.number_input(
        "Min spend để kết luận (Audit ad)",
        min_value=0.0,
        value=20.0,
        step=1.0,
        format="%.2f",
    )

    filtered_df = metrics_df[metrics_df["installs"] >= min_installs].copy()

    creative_df = latest_creatives_by_name()
    merged_df = filtered_df.merge(creative_df, how="left", on="normalized_name")

    if only_with_creative:
        merged_df = merged_df[merged_df["file_path"].notna()].copy()

    if merged_df.empty:
        st.warning("No rows after filters.")
        return

    benchmark = calculate_benchmark(merged_df)
    merged_df["win_driver"] = merged_df.apply(classify_driver, axis=1, benchmark=benchmark)
    thresholds = build_skill_thresholds(
        merged_df,
        use_manual=use_manual_benchmark,
        cpi_good_input=cpi_good_input,
        cpi_bad_input=cpi_bad_input,
        min_spend_for_decision=min_spend_for_decision,
    )
    skill_eval = merged_df.apply(lambda row: evaluate_with_audit_skill(row, thresholds), axis=1, result_type="expand")
    skill_eval.columns = ["audit_status", "audit_action"]
    merged_df = pd.concat([merged_df, skill_eval], axis=1)
    merged_df["is_win"] = merged_df["cpi"] < benchmark["cpi"] if np.isfinite(benchmark["cpi"]) else False
    merged_df["win_score"] = benchmark["cpi"] / merged_df["cpi"] if np.isfinite(benchmark["cpi"]) else np.nan
    merged_df = merged_df.sort_values(["cpi", "installs"], ascending=[True, False], na_position="last")

    creative_tested_count = int(merged_df["ad_name"].nunique())
    total_test_spend = float(merged_df["spend"].sum())
    b1, b2, b3, b4, b5, b6 = st.columns(6)
    b1.metric("Creatives Tested", f"{creative_tested_count:,}")
    b2.metric("Total Test Spend", f"${format_number(total_test_spend, 2)}")
    b3.metric("Benchmark CPI", format_number(benchmark["cpi"], 2))
    b4.metric("Benchmark CPM", format_number(benchmark["cpm"], 2))
    b5.metric("Benchmark CTR", format_percent(benchmark["ctr"]))
    b6.metric("Benchmark CTI", format_percent(benchmark["cti"]))
    st.caption(
        f"Audit thresholds -> CPI tốt <= ${format_number(thresholds['cpi_good'],2)}, "
        f"CPI kém > ${format_number(thresholds['cpi_bad'],2)}, "
        f"min spend ${format_number(thresholds['min_spend'],2)}"
    )

    table_columns = [
        "campaign_name",
        "adset_name",
        "ad_name",
        "audit_status",
        "audit_action",
        "spend",
        "installs",
        "cpi",
        "cpm",
        "ctr",
        "cti",
    ]
    table_columns.extend([col for col in extra_table_cols if col in merged_df.columns and col not in table_columns])
    table_df = merged_df[table_columns].copy()
    table_df = table_df.rename(columns={"spend": "cost"})
    table_df["ctr"] = table_df["ctr"] * 100
    table_df["cti"] = table_df["cti"] * 100

    st.markdown("#### Metrics Table")
    st.caption("Các cột tên dài đã set độ rộng lớn hơn. Bạn có thể kéo cạnh cột để resize thủ công.")
    styled_table_df = (
        table_df.style.format(
            {
                "cost": "${:,.2f}",
                "cpm": "${:,.2f}",
                "cpi": "${:,.2f}",
                "ctr": "{:.2f}%",
                "cti": "{:.2f}%",
            },
            na_rep="-",
        )
        .apply(make_gradient_styles, subset=["cpi"])
        .apply(make_gradient_styles, subset=["ctr"])
        .apply(make_gradient_styles, subset=["cti"])
    )
    st.dataframe(
        styled_table_df,
        width="stretch",
        height=460,
        column_config={
            "campaign_name": st.column_config.TextColumn("Campaign Name", width="medium"),
            "adset_name": st.column_config.TextColumn("Adset Name", width="medium"),
            "ad_name": st.column_config.TextColumn("Ad Name", width="medium"),
            "audit_status": st.column_config.TextColumn("Đánh giá tổng", width="medium"),
            "audit_action": st.column_config.TextColumn("Khuyến nghị", width="medium"),
            "cost": st.column_config.NumberColumn("Cost", format="$%.2f"),
            "installs": st.column_config.NumberColumn("Install", format="%d"),
            "cpm": st.column_config.NumberColumn("CPM", format="$%.2f"),
            "cpi": st.column_config.NumberColumn("CPI", format="$%.2f"),
            "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
            "cti": st.column_config.NumberColumn("CTI", format="%.2f%%"),
        },
    )

    with st.expander("Debug CTR/CTI calculations", expanded=False):
        debug_df = merged_df[
            [
                "campaign_name",
                "adset_name",
                "ad_name",
                "impressions",
                "clicks",
                "installs",
                "ctr",
                "cti",
            ]
        ].copy()
        debug_df["ctr_pct"] = debug_df["ctr"] * 100
        debug_df["cti_pct"] = debug_df["cti"] * 100
        st.dataframe(
            debug_df[
                [
                    "campaign_name",
                    "adset_name",
                    "ad_name",
                    "impressions",
                    "clicks",
                    "installs",
                    "ctr_pct",
                    "cti_pct",
                ]
            ],
            width="stretch",
            height=260,
            column_config={
                "ctr_pct": st.column_config.NumberColumn("CTR (%)", format="%.2f"),
                "cti_pct": st.column_config.NumberColumn("CTI (%)", format="%.2f"),
            },
        )
        st.caption("CTR = clicks / impressions * 100; CTI = installs / clicks * 100")

    unmatched = merged_df[merged_df["file_path"].isna()]["ad_name"].drop_duplicates().tolist()
    if unmatched:
        st.warning(f"{len(unmatched)} ads do not have matched creative in library.")
        with st.expander("View unmatched ad names"):
            st.write(unmatched)

    st.markdown("#### AI Conclusion")
    st.markdown(build_ai_conclusion(merged_df, benchmark))

    st.markdown("#### Creative Preview")
    preview_mode = st.radio(
        "Preview mode",
        options=["Top winners by CPI", "Top spend rows"],
        horizontal=True,
    )
    cards_per_row = st.slider("Cards per row", min_value=2, max_value=6, value=4)
    if preview_mode == "Top winners by CPI":
        preview_df = merged_df.sort_values("cpi", ascending=True).head(preview_limit)
    else:
        preview_df = merged_df.sort_values("spend", ascending=False).head(preview_limit)

    preview_df = preview_df.reset_index(drop=True)
    for start_idx in range(0, len(preview_df), cards_per_row):
        row_cols = st.columns(cards_per_row)
        chunk = preview_df.iloc[start_idx : start_idx + cards_per_row]
        for col_idx, (_, row) in enumerate(chunk.iterrows()):
            with row_cols[col_idx]:
                with st.container(border=True):
                    show_creative_preview(row)
                    st.caption(short_label(row["ad_name"], max_len=48))
                    st.caption(
                        f"CPI ${format_number(row['cpi'], 2)} | CPM ${format_number(row['cpm'], 2)}"
                    )
                    st.caption(f"CTR {format_percent(row['ctr'])} | CTI {format_percent(row['cti'])}")
                    st.caption(f"{row['audit_status']} | {row['audit_action']} | {row['win_driver']}")


def main() -> None:
    st.set_page_config(page_title="Meta Ad Analyzer", layout="wide")
    init_db()

    st.title("Meta Ad Creative Analyzer (MVP)")
    st.write(
        "Upload creative assets once, then upload CSV metrics to detect winning ads and why they win "
        "based on CPI/CPM/CTR/CTI."
    )

    tab_library, tab_analysis = st.tabs(["1. Creative Library", "2. Analyze CSV"])
    with tab_library:
        render_creative_library()
    with tab_analysis:
        render_analysis()


if __name__ == "__main__":
    main()
