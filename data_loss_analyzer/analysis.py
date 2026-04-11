from __future__ import annotations

from typing import Iterable

import pandas as pd


_RISK_ORDER = {"high": 0, "medium": 1, "low": 2}


def _risk_level(missing_pct: float, column: str, critical_columns: set[str]) -> str:
    if column in critical_columns and missing_pct >= 0.2:
        return "high"
    if missing_pct >= 0.5:
        return "high"
    if missing_pct >= 0.1:
        return "medium"
    return "low"


def analyze_missing_data(df: pd.DataFrame, critical_columns: Iterable[str] | None = None) -> dict:
    critical_columns = set(critical_columns or [])
    rows = len(df)
    columns = len(df.columns)

    missing_counts = df.isna().sum().sort_values(ascending=False)
    missing_pct = (missing_counts / max(rows, 1)).fillna(0.0)
    missing_df = pd.DataFrame(
        {
            "column": missing_counts.index,
            "missing_count": missing_counts.values,
            "missing_pct": (missing_pct.values * 100).round(1),
        }
    )
    missing_df = missing_df[missing_df["missing_count"] > 0].reset_index(drop=True)

    fields = []
    for _, row in missing_df.iterrows():
        pct = row["missing_pct"] / 100.0
        fields.append(
            {
                "column": row["column"],
                "missing_count": int(row["missing_count"]),
                "missing_pct": round(float(row["missing_pct"]), 1),
                "risk_level": _risk_level(pct, row["column"], critical_columns),
            }
        )
    high_risk_fields = pd.DataFrame(fields)
    if not high_risk_fields.empty:
        high_risk_fields["risk_rank"] = high_risk_fields["risk_level"].map(_RISK_ORDER).fillna(99)
        high_risk_fields = high_risk_fields.sort_values(
            by=["risk_rank", "missing_pct"], ascending=[True, False]
        ).drop(columns=["risk_rank"]).reset_index(drop=True)

    row_missing_mask = df.isna().any(axis=1)
    at_risk_rows = int(row_missing_mask.sum())
    missing_cells = int(df.isna().sum().sum())

    recommendations = []
    if missing_cells == 0:
        recommendations.append("No missing data found. Keep current validation checks in place.")
    else:
        if not high_risk_fields.empty:
            top = high_risk_fields.iloc[0]
            recommendations.append(
                f"Prioritize fixing `{top['column']}` because it has {top['missing_pct']}% missing values."
            )
        if critical_columns:
            impacted = [c for c in critical_columns if c in df.columns and df[c].isna().any()]
            if impacted:
                recommendations.append(
                    "Critical sales fields have gaps, so revenue reporting and attribution may be biased."
                )
        recommendations.append("Backfill or impute missing rows before revenue forecasting or territory rollups.")
        recommendations.append("Add ingestion-time validation to block incomplete sales records.")

    return {
        "rows": rows,
        "columns": columns,
        "missing_cells": missing_cells,
        "at_risk_rows": at_risk_rows,
        "missing_by_column": missing_df,
        "high_risk_fields": high_risk_fields,
        "recommendations": recommendations,
        "critical_columns": sorted(critical_columns),
    }
