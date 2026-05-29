from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

import streamlit as st
from pymongo import MongoClient
from pymongo.collection import Collection


def _safe_secrets() -> dict:
    try:
        return st.secrets.to_dict()
    except Exception:
        return {}


def _secret_or_env(secret_name: str, env_name: str, default: str = "") -> str:
    value = ""
    secrets = _safe_secrets()
    if secret_name in secrets:
        value = secrets.get(secret_name, "")
    if not value:
        value = secrets.get("mongodb", {}).get(secret_name.lower(), "")
    if not value:
        import os

        value = os.getenv(env_name, default)
    return value.strip() if isinstance(value, str) else value


def mongo_config_status() -> tuple[bool, str]:
    uri = _secret_or_env("MONGODB_URI", "MONGODB_URI")
    if not uri:
        return False, "Missing MongoDB config. Add MONGODB_URI in Streamlit secrets or environment variables."
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return True, "MongoDB storage is configured."
    except Exception as exc:  # pragma: no cover - network/client errors
        return False, f"MongoDB connection failed: {exc}"


@lru_cache(maxsize=1)
def _mongo_collection() -> Collection:
    uri = _secret_or_env("MONGODB_URI", "MONGODB_URI")
    database_name = _secret_or_env("MONGODB_DATABASE", "MONGODB_DATABASE", "data_loss_analyzer")
    collection_name = _secret_or_env("MONGODB_COLLECTION", "MONGODB_COLLECTION", "analysis_history")

    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client[database_name][collection_name]


def save_uploaded_csv_pair(*, user_email: str, csv_file_name: str) -> tuple[bool, str]:
    try:
        document = {
            "key": user_email,
            "value": csv_file_name,
            "user_email": user_email,
            "csv_file_name": csv_file_name,
            "created_at": datetime.now(timezone.utc),
        }
        _mongo_collection().insert_one(document)
        return True, "CSV upload saved to MongoDB."
    except Exception as exc:  # pragma: no cover - network/client errors
        return False, f"Could not save CSV upload: {exc}"


def recent_user_history(user_email: str, limit: int = 5) -> list[dict]:
    try:
        cursor = (
            _mongo_collection()
            .find({"key": user_email}, {"value": 1, "csv_file_name": 1, "created_at": 1})
            .sort("created_at", -1)
            .limit(limit)
        )
        return list(cursor)
    except Exception:
        return []

