from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class KnowledgeChunk:
    id: str
    text: str


def default_knowledge_base() -> list[KnowledgeChunk]:
    return [
        KnowledgeChunk(
            id="revenue_attribution",
            text="Missing customer or order identifiers can break revenue attribution and duplicate transaction handling.",
        ),
        KnowledgeChunk(
            id="territory_reporting",
            text="Missing region, channel, or account fields can distort territory performance and sales quota rollups.",
        ),
        KnowledgeChunk(
            id="forecasting",
            text="Missing order value or date fields reduce forecast accuracy, weaken trend detection, and bias monthly revenue estimates.",
        ),
        KnowledgeChunk(
            id="operational_risk",
            text="Incomplete records increase manual cleanup, delay dashboards, and can hide underperforming segments from leadership.",
        ),
        KnowledgeChunk(
            id="imputation",
            text="Imputation should be conservative for sales-critical metrics; use it only when business rules define a safe replacement.",
        ),
    ]


def _retrieve(query: str, knowledge_base: list[KnowledgeChunk], top_k: int = 3) -> list[KnowledgeChunk]:
    corpus = [chunk.text for chunk in knowledge_base] + [query]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    ranked = sorted(zip(scores, knowledge_base), key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in ranked[:top_k] if score > 0]


def generate_sales_impact_summary(analysis: dict, business_context: str = "", knowledge_base: list[KnowledgeChunk] | None = None) -> dict:
    knowledge_base = knowledge_base or default_knowledge_base()
    critical = analysis.get("critical_columns", [])
    missing_df = analysis.get("missing_by_column")
    top_fields = []
    if missing_df is not None and not missing_df.empty:
        top_fields = [f"{row.column} ({row.missing_pct}%)" for row in missing_df.head(3).itertuples(index=False)]

    query_parts = [
        "sales impact of missing data",
        "critical columns: " + ", ".join(critical),
        "high missing fields: " + ", ".join(top_fields),
        business_context,
    ]
    query = " ".join(part for part in query_parts if part).strip()
    hits = _retrieve(query, knowledge_base, top_k=3)

    missing_cells = analysis.get("missing_cells", 0)
    at_risk_rows = analysis.get("at_risk_rows", 0)
    rows = max(analysis.get("rows", 0), 1)
    risk_ratio = at_risk_rows / rows

    if missing_cells == 0:
        summary = "No missing data was detected, so current sales reporting risk appears low."
    else:
        lead = f"{missing_cells} missing cells were found across {at_risk_rows} rows, affecting about {risk_ratio:.1%} of records."
        if critical:
            lead += f" Critical sales fields under review: {', '.join(critical)}."
        summary = lead
        if hits:
            summary += " RAG context suggests the biggest business risk is " + "; ".join(chunk.text for chunk in hits[:2])

    evidence = []
    if top_fields:
        evidence.append(f"Top missing fields: {', '.join(top_fields)}")
    if critical:
        evidence.append(f"Critical columns analyzed: {', '.join(critical)}")
    evidence.extend([chunk.text for chunk in hits])

    return {
        "summary": summary,
        "evidence": evidence[:5],
        "retrieved_chunks": hits,
    }
