from __future__ import annotations

import json
import logging
import unicodedata
from decimal import Decimal, ROUND_HALF_EVEN
from dataclasses import dataclass
from time import time
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)

IBGE_BASE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades"
REQUEST_TIMEOUT = 30
_CACHE_TTL_SECONDS = 24 * 60 * 60
_cache: Dict[str, tuple[float, Any]] = {}


class ApiToolsError(Exception):
    def __init__(self, status_code: int, message: str, details: Optional[str] = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(message)


class SolarCalculatorRequest(BaseModel):
    input_type: str = Field(pattern="^(reais|kwh)$")
    account_value: Optional[float] = Field(default=None, ge=0)
    consumption_kwh: Optional[float] = Field(default=None, ge=0)
    value_kwh: float = Field(gt=0)
    generation_percentage: float = Field(gt=0)
    solar_factor: float = Field(gt=0)

    @model_validator(mode="after")
    def _validate_payload(self) -> "SolarCalculatorRequest":
        if self.account_value is None and self.consumption_kwh is None:
            raise ValueError("Informe account_value ou consumption_kwh")
        return self


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.lower().strip()


def _cache_get(key: str) -> Any:
    cached = _cache.get(key)
    if not cached:
        return None
    cached_at, payload = cached
    if time() - cached_at > _CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None
    return payload


def _cache_set(key: str, value: Any) -> None:
    _cache[key] = (time(), value)


def _get_json(url: str, cache_key: Optional[str] = None) -> Any:
    if cache_key is not None:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    if not response.ok:
        raise ApiToolsError(
            response.status_code,
            f"IBGE retornou {response.status_code}",
            response.text,
        )

    data = response.json()
    if cache_key is not None:
        _cache_set(cache_key, data)
    return data


def get_states() -> List[Dict[str, Any]]:
    url = f"{IBGE_BASE_URL}/estados?orderBy=nome"
    states = _get_json(url, cache_key="ibge_states")
    if not isinstance(states, list):
        raise ApiToolsError(500, "Resposta inválida da IBGE", "Esperava lista de estados")

    result = []
    for item in states:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "id": item.get("id"),
                "sigla": item.get("sigla"),
                "nome": item.get("nome"),
                "regiao": item.get("regiao", {}).get("nome") if isinstance(item.get("regiao"), dict) else None,
            }
        )
    return result


def get_cities_by_state(uf: str) -> List[Dict[str, Any]]:
    uf_text = uf.strip().upper()
    if len(uf_text) != 2:
        raise ApiToolsError(400, "UF inválida", "Informe uma sigla de estado com 2 letras")

    cache_key = f"ibge_cities:{uf_text}"
    url = f"{IBGE_BASE_URL}/estados/{uf_text}/municipios?orderBy=nome"
    cities = _get_json(url, cache_key=cache_key)
    if not isinstance(cities, list):
        raise ApiToolsError(500, "Resposta inválida da IBGE", "Esperava lista de municípios")

    result = []
    for item in cities:
        if not isinstance(item, dict):
            continue
        result.append(
            {
                "id": item.get("id"),
                "nome": item.get("nome"),
                "microrregiao": item.get("microrregiao", {}).get("nome") if isinstance(item.get("microrregiao"), dict) else None,
            }
        )
    return result


def lookup_city_ibge_code(uf: str, city_name: str) -> Dict[str, Any]:
    cities = get_cities_by_state(uf)
    needle = _normalize_text(city_name)
    if not needle:
        raise ApiToolsError(400, "Cidade inválida", "Informe o nome da cidade")

    exact_match = None
    starts_with_match = None
    for city in cities:
        city_text = _normalize_text(str(city.get("nome") or ""))
        if city_text == needle:
            exact_match = city
            break
        if starts_with_match is None and city_text.startswith(needle):
            starts_with_match = city

    match = exact_match or starts_with_match
    if not match:
        raise ApiToolsError(404, "Cidade não encontrada", f"Nenhuma cidade encontrada para UF={uf.upper()} e cidade={city_name}")

    return {
        "uf": uf.strip().upper(),
        "cidade": match["nome"],
        "codigoIbge": match["id"],
    }


def calculate_solar_project(payload: SolarCalculatorRequest) -> Dict[str, Any]:
    account_value = payload.account_value
    consumption_source = payload.consumption_kwh

    if payload.input_type == "reais":
        if account_value is None and consumption_source is not None:
            account_value = float(Decimal(str(consumption_source)) * Decimal(str(payload.value_kwh)))
        consumo = Decimal(str(account_value or 0)) / Decimal(str(payload.value_kwh))
    else:
        if consumption_source is None and account_value is not None:
            consumption_source = float(Decimal(str(account_value)) / Decimal(str(payload.value_kwh)))
        consumo = Decimal(str(consumption_source or 0))

    percentual = Decimal(str(payload.generation_percentage)) / Decimal("100")
    fator_solar = Decimal(str(payload.solar_factor))
    geracao = consumo * percentual
    kwp = geracao / fator_solar

    consumo_q = consumo.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    geracao_q = geracao.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    kwp_q = kwp.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

    return {
        "inputType": payload.input_type,
        "consumoKwh": float(consumo_q),
        "geracaoKwh": float(geracao_q),
        "potenciaKwp": float(kwp_q),
        "valorKwh": round(payload.value_kwh, 4),
        "percentualGeracao": round(payload.generation_percentage, 2),
        "fatorSolar": round(payload.solar_factor, 2),
        "accountValue": round(account_value, 2) if account_value is not None else None,
    }
