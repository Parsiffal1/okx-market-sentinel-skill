#!/usr/bin/env python3
"""Shared helpers for Phase3 source fetchers.

Provides environment loading, raw-cache persistence, and consistent stdout JSON
result helpers used across source scripts.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parents[2]
CONTEXT_DIR = BASE_DIR / "context"
RAW_DIR = CONTEXT_DIR / "raw"
ENV_FILES = [
    BASE_DIR / ".env",
    Path("/root/.config/crypto-agent.env"),
    Path("/root/.config/6551.env"),
    Path("/root/.env"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _resolve_env_value(value: str, env: Dict[str, str], depth: int = 0) -> str:
    value = value.strip().strip('"').strip("'")
    if depth >= 5:
        return value
    if value.startswith("${") and value.endswith("}"):
        ref_key = value[2:-1].strip()
        ref_value = env.get(ref_key) or os.environ.get(ref_key)
        if ref_value is not None:
            return _resolve_env_value(ref_value, env, depth + 1)
    if value.startswith("$") and len(value) > 1 and value[1:].replace("_", "").isalnum():
        ref_key = value[1:].strip()
        ref_value = env.get(ref_key) or os.environ.get(ref_key)
        if ref_value is not None:
            return _resolve_env_value(ref_value, env, depth + 1)
    return value


def load_env_file() -> Dict[str, str]:
    env: Dict[str, str] = {}
    for path in ENV_FILES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip().strip('"').strip("'")
    return {key: _resolve_env_value(value, env) for key, value in env.items()}


def get_env(key: str, default: str = "") -> str:
    return os.environ.get(key) or load_env_file().get(key, default)


def write_raw_cache(filename: str, source: str, status: str, data: Dict[str, Any], error: str | None = None) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any] = {
        "updated_at": utc_now(),
        "source": source,
        "status": status,
        "data": data,
    }
    if error:
        payload["error"] = error
    path = RAW_DIR / filename
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def result_ok(path: Path, source: str, extra: Dict[str, Any] | None = None) -> None:
    payload: Dict[str, Any] = {"ok": True, "source": source, "path": str(path)}
    if extra:
        payload.update(extra)
    print(json.dumps(payload, ensure_ascii=False))


def result_error(source: str, message: str) -> None:
    print(json.dumps({"ok": False, "source": source, "message": message}, ensure_ascii=False))
    raise SystemExit(1)
