from __future__ import annotations

from typing import Any, Dict, Literal

from pydantic import BaseModel, Field

from app.services.api_tools_service import (
    SolarCalculatorRequest,
    calculate_solar_project,
    lookup_city_ibge_code,
)
from app.services.utility_company_service import detect_utility_company

DEFAULT_VALUE_KWH = 0.96
DEFAULT_GENERATION_PERCENTAGE = 110.0
DEFAULT_SOLAR_FACTOR = 140.14


class BudgetTestRequest(BaseModel):
    input_type: Literal["reais", "kwh"]
    value: float = Field(gt=0)
    uf: str = Field(min_length=2, max_length=2)
    cidade: str = Field(min_length=1)
    utility_company: str | None = Field(default=None)


def _build_solar_request(payload: BudgetTestRequest) -> SolarCalculatorRequest:
    common_kwargs = {
        "input_type": payload.input_type,
        "value_kwh": DEFAULT_VALUE_KWH,
        "generation_percentage": DEFAULT_GENERATION_PERCENTAGE,
        "solar_factor": DEFAULT_SOLAR_FACTOR,
    }

    if payload.input_type == "reais":
        return SolarCalculatorRequest(
            **common_kwargs,
            account_value=payload.value,
        )

    return SolarCalculatorRequest(
        **common_kwargs,
        consumption_kwh=payload.value,
    )


def calculate_budget_test(payload: BudgetTestRequest) -> Dict[str, Any]:
    ibge_data = lookup_city_ibge_code(payload.uf, payload.cidade)
    solar_request = _build_solar_request(payload)
    solar_result = calculate_solar_project(solar_request)
    detected_company = (payload.utility_company or "").strip() or detect_utility_company(
        ibge_code=ibge_data["codigoIbge"],
        uf=ibge_data.get("uf"),
        city=ibge_data.get("cidade"),
    )

    return {
        "codigoIbge": ibge_data["codigoIbge"],
        "concessionaria": detected_company,
        "consumoKwh": solar_result["consumoKwh"],
        "geracaoKwh": solar_result["geracaoKwh"],
        "potenciaKwp": solar_result["potenciaKwp"],
    }