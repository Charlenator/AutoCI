"""S1: Translation Agent — Classifies NL queries as SQL or RAG route."""

from enum import Enum
from dataclasses import dataclass

class QueryIntent(Enum):
    SQL = "sql"
    RAG = "rag"  # semantic/doc lookup

@dataclass
class TranslationResult:
    intent: QueryIntent
    original_query: str
    agent_routed_to: str  # "s2_rag" or "s3_sql"
    extracted_entities: dict = None

class TranslationAgent:
    """Classifies intents into SQL (metric) vs RAG (semantic) — deterministic rules."""

    METRIC_KEYWORDS = [
        "time to fill", "ttf", "conversion rate", "dropoff", "offer acceptance",
        "source yield", "average", "median", "count", "how many", "percentage",
        "trend", "pipeline", "stage", "interview", "score", "lag", "cost",
    ]

    def __init__(self):
        pass

    def classify(self, query: str) -> TranslationResult:
        """Classify query by keyword matching."""
        q = query.lower()
        intent = QueryIntent.RAG
        for kw in self.METRIC_KEYWORDS:
            if kw in q:
                intent = QueryIntent.SQL
                break
        agent = "s3_sql" if intent == QueryIntent.SQL else "s2_rag"
        return TranslationResult(
            intent=intent,
            original_query=query,
            agent_routed_to=agent,
        )
