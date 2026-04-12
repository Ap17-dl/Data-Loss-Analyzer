from __future__ import annotations

from functools import lru_cache
from typing import Any

import streamlit as st
from supabase import Client, create_client


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
        supabase_cfg = secrets.get("supabase", {})
        value = supabase_cfg.get(secret_name.replace("SUPABASE_", "").lower(), "")

    if not value:
        supabase_cfg = secrets.get("supabase", {})
        value = supabase_cfg.get(secret_name.lower(), "")

    if not value:
        import os

        value = os.getenv(env_name, default)

    return value


def _supabase_key() -> str:
    key = _secret_or_env("SUPABASE_ANON_KEY", "SUPABASE_ANON_KEY")
    if key:
        return key
    return _secret_or_env("SUPABASE_KEY", "SUPABASE_KEY")


def auth_config_status() -> tuple[bool, str]:
    url = _secret_or_env("SUPABASE_URL", "SUPABASE_URL")
    key = _supabase_key()
    if not url or not key:
        return (
            False,
            "Missing Supabase config. Add SUPABASE_URL and SUPABASE_ANON_KEY (or SUPABASE_KEY) in Streamlit secrets or environment variables.",
        )
    return True, "Supabase authentication is configured."


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    url = _secret_or_env("SUPABASE_URL", "SUPABASE_URL")
    key = _supabase_key()
    return create_client(url, key)


def sign_up_user(email: str, password: str) -> tuple[bool, str]:
    try:
        response = get_supabase_client().auth.sign_up({"email": email, "password": password})
        if response.user is None:
            return False, "Signup failed. Check your details and try again."
        return True, "Account created. Check your email for verification if confirmation is enabled."
    except Exception as exc:  # pragma: no cover - network/client errors
        return False, f"Signup failed: {exc}"


def sign_in_user(email: str, password: str) -> tuple[bool, str, dict[str, Any] | None]:
    try:
        response = get_supabase_client().auth.sign_in_with_password({"email": email, "password": password})
        if response.user is None or response.session is None:
            return False, "Invalid email/password or account not verified.", None
        user = {
            "id": response.user.id,
            "email": response.user.email,
            "access_token": response.session.access_token,
        }
        return True, "Signed in successfully.", user
    except Exception as exc:  # pragma: no cover - network/client errors
        return False, f"Sign-in failed: {exc}", None


def get_user_from_token(access_token: str) -> dict[str, Any] | None:
    if not access_token:
        return None
    try:
        response = get_supabase_client().auth.get_user(access_token)
        if response.user is None:
            return None
        return {"id": response.user.id, "email": response.user.email, "access_token": access_token}
    except Exception:
        return None


def sign_out_user() -> tuple[bool, str]:
    try:
        get_supabase_client().auth.sign_out()
        return True, "Signed out."
    except Exception as exc:  # pragma: no cover - network/client errors
        return False, f"Sign-out warning: {exc}"
