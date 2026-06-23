from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.services.utility_companies_db import get_company_by_ibge, init_db

DATA_FILE = Path(__file__).resolve().parent / "data" / "utility_companies.json"


@lru_cache(maxsize=1)
def _load_mapping() -> dict[str, str]:
    if not DATA_FILE.exists():
        return {}
    with DATA_FILE.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        return {}
    return {
        str(key).strip(): str(value).strip()
        for key, value in raw.items()
        if str(key).strip() and str(value).strip()
    }


def detect_utility_company(*, ibge_code: int | str, uf: Optional[str] = None, city: Optional[str] = None) -> str:
    # ensure DB exists
    try:
        init_db()
    except Exception:
        pass

    code = str(ibge_code).strip()
    if not code:
        return ""

    # 0) try DB lookup first
    try:
        db_val = get_company_by_ibge(int(code))
        if db_val:
            return db_val
    except Exception:
        # fallthrough to JSON/fallback
        pass

    mapping = _load_mapping()
    # 1) exact IBGE code (string keys)
    if code in mapping:
        return mapping[code]

    # 2) UF-level fallback (mapping key like "UF:XX")
    if uf:
        key = f"UF:{str(uf).strip().upper()}"
        if key in mapping:
            return mapping[key]

    # 3) try city name exact match (case-insensitive)
    if city:
        cname = str(city).strip().lower()
        for k, v in mapping.items():
            if k.strip().lower() == cname:
                return v

    return ""