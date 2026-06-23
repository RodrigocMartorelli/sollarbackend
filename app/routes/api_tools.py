import logging
import math
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Query
from pydantic import BaseModel, Field

from app.services.api_tools_service import (
    ApiToolsError,
    SolarCalculatorRequest,
    calculate_solar_project,
    get_cities_by_state,
    get_states,
    lookup_city_ibge_code,
)
from app.services.solaryum_service import montar_kits

router = APIRouter(prefix="/api-tools", tags=["api-tools"])
logger = logging.getLogger(__name__)

DEFAULT_PANEL_POWER_W = 620.0


class KitSelectorCalculationRequest(SolarCalculatorRequest):
    uf: Optional[str] = Field(default=None, min_length=2, max_length=2)
    cidade: Optional[str] = Field(default=None, min_length=1)


class KitSelectorPanelsRequest(BaseModel):
    input_type: str = Field(pattern="^(reais|kwh)$")
    account_value: Optional[float] = Field(default=None, ge=0)
    consumption_kwh: Optional[float] = Field(default=None, ge=0)
    value_kwh: float = Field(gt=0)
    generation_percentage: float = Field(gt=0)
    solar_factor: float = Field(gt=0)
    uf: Optional[str] = Field(default=None, min_length=2, max_length=2)
    cidade: Optional[str] = Field(default=None, min_length=1)
    potenciaPainelW: float = Field(default=DEFAULT_PANEL_POWER_W, gt=0)
    marcaPainel: Optional[str] = None
    marcaInversor: Optional[str] = None
    tensao: Optional[int] = None
    fase: Optional[int] = None
    tipoInv: Optional[int] = None
    ibge: Optional[str] = None
    cifComDescarga: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=200, ge=1, le=200)


class KitSelectorInvertersRequest(BaseModel):
    input_type: str = Field(pattern="^(reais|kwh)$")
    account_value: Optional[float] = Field(default=None, ge=0)
    consumption_kwh: Optional[float] = Field(default=None, ge=0)
    value_kwh: float = Field(gt=0)
    generation_percentage: float = Field(gt=0)
    solar_factor: float = Field(gt=0)
    uf: Optional[str] = Field(default=None, min_length=2, max_length=2)
    cidade: Optional[str] = Field(default=None, min_length=1)
    potenciaPainelW: float = Field(default=DEFAULT_PANEL_POWER_W, gt=0)
    potenciaInversorKw: Optional[float] = Field(default=None, gt=0)
    marcaPainel: Optional[str] = None
    marcaInversor: Optional[str] = None
    tensao: Optional[int] = None
    fase: Optional[int] = None
    tipoInv: Optional[int] = None
    ibge: Optional[str] = None
    cifComDescarga: Optional[bool] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=200, ge=1, le=200)


class KitSelectorSummaryRequest(BaseModel):
    solar: Dict[str, Any]
    panel: Dict[str, Any]
    inverter: Optional[Dict[str, Any]] = None


class IbgeLookupRequest(BaseModel):
    uf: str = Field(min_length=2, max_length=2)
    cidade: str = Field(min_length=1)


@router.get("/ibge/ufs")
def list_ibge_states():
    try:
        return {"items": get_states()}
    except ApiToolsError as error:
        raise _to_http_error(error)
    except Exception as error:
        logger.exception("Erro inesperado ao buscar estados IBGE")
        raise _to_http_error(ApiToolsError(500, "Erro ao buscar estados IBGE", str(error)))


@router.get("/ibge/cidades")
def list_ibge_cities(uf: str = Query(..., min_length=2, max_length=2)):
    try:
        return {"items": get_cities_by_state(uf)}
    except ApiToolsError as error:
        raise _to_http_error(error)
    except Exception as error:
        logger.exception("Erro inesperado ao buscar cidades IBGE")
        raise _to_http_error(ApiToolsError(500, "Erro ao buscar cidades IBGE", str(error)))


@router.post("/ibge/codigo")
def get_ibge_code(payload: IbgeLookupRequest):
    try:
        return lookup_city_ibge_code(payload.uf, payload.cidade)
    except ApiToolsError as error:
        raise _to_http_error(error)
    except Exception as error:
        logger.exception("Erro inesperado ao consultar código IBGE")
        raise _to_http_error(ApiToolsError(500, "Erro ao consultar código IBGE", str(error)))


@router.post("/solar/calculadora")
def calculate_solar(payload: SolarCalculatorRequest):
    try:
        return calculate_solar_project(payload)
    except ApiToolsError as error:
        raise _to_http_error(error)
    except Exception as error:
        logger.exception("Erro inesperado na calculadora solar")
        raise _to_http_error(ApiToolsError(500, "Erro na calculadora solar", str(error)))


@router.post("/montar-kits-seletor/calcular")
def calculate_kit_selector(payload: KitSelectorCalculationRequest):
    try:
        solar = calculate_solar_project(payload)
        location = None
        if payload.uf and payload.cidade:
            location = lookup_city_ibge_code(payload.uf, payload.cidade)
        return {
            "solar": solar,
            "location": location,
            "potenciaKwp": solar["potenciaKwp"],
            "panelPowerW": DEFAULT_PANEL_POWER_W,
        }
    except ApiToolsError as error:
        raise _to_http_error(error)
    except Exception as error:
        logger.exception("Erro inesperado no seletor de kits (cálculo)")
        raise _to_http_error(ApiToolsError(500, "Erro no seletor de kits", str(error)))


@router.post("/montar-kits-seletor/paineis")
def selector_panels(payload: KitSelectorPanelsRequest):
    try:
        solar = calculate_solar_project(
            SolarCalculatorRequest(
                input_type=payload.input_type,
                account_value=payload.account_value,
                consumption_kwh=payload.consumption_kwh,
                value_kwh=payload.value_kwh,
                generation_percentage=payload.generation_percentage,
                solar_factor=payload.solar_factor,
            )
        )
        location = None
        if payload.uf and payload.cidade:
            location = lookup_city_ibge_code(payload.uf, payload.cidade)

        kits = montar_kits(
            potencia_do_kit=float(solar["potenciaKwp"]),
            potencia_do_painel=payload.potenciaPainelW,
            marca_painel=payload.marcaPainel,
            tensao=payload.tensao,
            fase=payload.fase,
            marca_inversor=payload.marcaInversor,
            telhados=None,
            ibge=payload.ibge or (str(location["codigoIbge"]) if location else None),
            cif_com_descarga=payload.cifComDescarga,
        )

        items = _build_panel_options(kits, float(solar["potenciaKwp"]), payload.potenciaPainelW)
        return {
            "solar": solar,
            "location": location,
            "panelPowerW": payload.potenciaPainelW,
            "items": items,
            "total": len(items),
        }
    except ApiToolsError as error:
        raise _to_http_error(error)
    except Exception as error:
        logger.exception("Erro inesperado no seletor de kits (painéis)")
        raise _to_http_error(ApiToolsError(500, "Erro no seletor de painéis", str(error)))


@router.post("/montar-kits-seletor/inversores")
def selector_inverters(payload: KitSelectorInvertersRequest):
    try:
        solar = calculate_solar_project(
            SolarCalculatorRequest(
                input_type=payload.input_type,
                account_value=payload.account_value,
                consumption_kwh=payload.consumption_kwh,
                value_kwh=payload.value_kwh,
                generation_percentage=payload.generation_percentage,
                solar_factor=payload.solar_factor,
            )
        )
        location = None
        if payload.uf and payload.cidade:
            location = lookup_city_ibge_code(payload.uf, payload.cidade)

        kits = montar_kits(
            potencia_do_kit=float(solar["potenciaKwp"]),
            potencia_do_painel=payload.potenciaPainelW,
            marca_painel=payload.marcaPainel,
            tensao=payload.tensao,
            fase=payload.fase,
            marca_inversor=payload.marcaInversor,
            telhados=None,
            ibge=payload.ibge or (str(location["codigoIbge"]) if location else None),
            cif_com_descarga=payload.cifComDescarga,
        )

        items = _build_inverter_options(kits, payload.potenciaInversorKw)
        return {
            "solar": solar,
            "location": location,
            "panelPowerW": payload.potenciaPainelW,
            "selectedInverterPowerKw": payload.potenciaInversorKw,
            "items": items,
            "total": len(items),
        }
    except ApiToolsError as error:
        raise _to_http_error(error)
    except Exception as error:
        logger.exception("Erro inesperado no seletor de kits (inversores)")
        raise _to_http_error(ApiToolsError(500, "Erro no seletor de inversores", str(error)))


@router.post("/montar-kits-seletor/resumo")
def selector_summary(payload: KitSelectorSummaryRequest):
    solar = payload.solar
    panel = payload.panel
    inverter = payload.inverter or {}

    potencia_kwp = float(solar.get("potenciaKwp") or 0)
    panel_power_w = float(panel.get("panelPowerW") or panel.get("potenciaPainelW") or DEFAULT_PANEL_POWER_W)
    quantity = int(math.ceil((potencia_kwp * 1000.0) / panel_power_w)) if potencia_kwp > 0 and panel_power_w > 0 else 0

    return {
        "solar": solar,
        "panel": panel,
        "inverter": inverter,
        "summary": {
            "potenciaKwp": potencia_kwp,
            "panelPowerW": panel_power_w,
            "panelQuantity": quantity,
            "inverterPowerW": inverter.get("potenciaWatts"),
            "estimatedPrice": panel.get("kitPrice") or inverter.get("kitPrice"),
        },
    }


def _to_http_error(error: ApiToolsError):
    from fastapi import HTTPException

    return HTTPException(
        status_code=error.status_code,
        detail={
            "error": error.message,
            "message": error.message,
            "details": error.details,
        },
    )


def _get_nested_composition_item(kit: Dict[str, Any], category_name: str) -> Dict[str, Any]:
    composition = kit.get("composicao")
    if isinstance(composition, list):
        for item in composition:
            if not isinstance(item, dict):
                continue
            category = str(item.get("categoria") or item.get("agrupamento") or "").strip().lower()
            if category == category_name.lower():
                return item
    return {}


def _build_panel_options(kits: List[Dict[str, Any]], potencia_kwp: float, panel_power_w: float) -> List[Dict[str, Any]]:
    items: Dict[tuple[str, str], Dict[str, Any]] = {}
    quantity = int(math.ceil((potencia_kwp * 1000.0) / panel_power_w)) if potencia_kwp > 0 and panel_power_w > 0 else 0

    for kit in kits:
        panel = _get_nested_composition_item(kit, "Painel")
        brand = str(panel.get("marca") or kit.get("marcaPainel") or kit.get("marca") or "-").strip()
        model = str(panel.get("descricao") or kit.get("modelo") or kit.get("descricao") or "-").strip()
        key = (brand.lower(), model.lower())
        if key in items:
            continue

        items[key] = {
            "marca": brand,
            "modelo": model,
            "potenciaPainelW": panel_power_w,
            "quantidade": quantity,
            "totalWp": int(quantity * panel_power_w),
            "approxKwp": round((quantity * panel_power_w) / 1000.0, 3),
            "kitPrice": kit.get("precoVenda"),
            "estrutura": kit.get("estrutura"),
            "fotoUrl": kit.get("fotoUrl"),
            "rawKit": kit,
        }

    return sorted(items.values(), key=lambda item: (item["marca"], item["modelo"]))


def _build_inverter_options(kits: List[Dict[str, Any]], selected_power_kw: Optional[float]) -> List[Dict[str, Any]]:
    target_w = int(round(selected_power_kw * 1000.0)) if selected_power_kw is not None else None
    items: Dict[tuple[str, str, int], Dict[str, Any]] = {}

    for kit in kits:
        inverter = _get_nested_composition_item(kit, "Inversor")
        power_w = int(float(inverter.get("potencia") or kit.get("potenciaInversor") or 0))
        if target_w is not None and power_w < target_w:
            continue

        brand = str(inverter.get("marca") or kit.get("marcaInversor") or kit.get("marca") or "-").strip()
        model = str(inverter.get("descricao") or kit.get("modelo") or kit.get("descricao") or "-").strip()
        key = (brand.lower(), model.lower(), power_w)
        if key in items:
            continue

        items[key] = {
            "marca": brand,
            "modelo": model,
            "potenciaWatts": power_w,
            "quantidadeMppt": inverter.get("mppt") or inverter.get("quantidadeMppt") or inverter.get("nMppt"),
            "quantidadeEntradas": inverter.get("entradas") or inverter.get("quantidadeEntradas") or inverter.get("inputs"),
            "kitPrice": kit.get("precoVenda"),
            "estrutura": kit.get("estrutura"),
            "fotoUrl": inverter.get("fotoUrl") or kit.get("fotoUrl"),
            "atributos": inverter,
            "rawKit": kit,
        }

    result = list(items.values())
    if target_w is not None and result:
        result.sort(key=lambda item: (item["potenciaWatts"] - target_w, item["marca"], item["modelo"]))
    else:
        result.sort(key=lambda item: (item["potenciaWatts"], item["marca"], item["modelo"]))
    return result
