import logging
import math
from typing import Dict, Any, List

from fastapi import APIRouter

from app.services.api_tools_service import SolarCalculatorRequest, calculate_solar_project, ApiToolsError

router = APIRouter(prefix="/placas", tags=["placas"])
logger = logging.getLogger(__name__)


@router.post("/ver")
def view_panels(payload: SolarCalculatorRequest) -> Dict[str, Any]:
    """Retorna sugestões de placas (quantidade) baseadas na potência necessária.
    Atualmente imita a calculadora solar: calcula a potência (kWp) e gera
    opções de arranjos de painéis com potências típicas.
    """
    try:
        solar = calculate_solar_project(payload)

        potencia_kwp = float(solar.get("potenciaKwp", 0) or 0)

        # opções típicas de módulos em Watts (Wp)
        module_watts = [330, 360, 380, 405, 450]
        panels: List[Dict[str, Any]] = []
        for watt in module_watts:
            # número mínimo de módulos para atingir a potência kwp
            count = math.ceil((potencia_kwp * 1000.0) / watt) if potencia_kwp > 0 else 0
            panels.append(
                {
                    "moduleWp": watt,
                    "count": int(count),
                    "totalWp": int(count * watt),
                    "approxKwp": round((count * watt) / 1000.0, 3),
                }
            )

        return {"solar": solar, "panels": panels}
    except ApiToolsError as error:
        raise _to_http_error(error)
    except Exception as error:
        logger.exception("Erro inesperado ao gerar sugestões de placas")
        raise _to_http_error(ApiToolsError(500, "Erro ao gerar sugestões de placas", str(error)))


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
