import logging

from fastapi import APIRouter

from app.services.api_tools_service import ApiToolsError
from app.services.budget_test_service import BudgetTestRequest, calculate_budget_test

router = APIRouter(prefix="/api-tools/orcamentos", tags=["api-tools", "budget-test"])
logger = logging.getLogger(__name__)


@router.post("/teste")
def test_budget(payload: BudgetTestRequest):
    try:
        return calculate_budget_test(payload)
    except ApiToolsError as error:
        raise _to_http_error(error)
    except Exception as error:
        logger.exception("Erro inesperado no teste de orçamentos")
        raise _to_http_error(ApiToolsError(500, "Erro no teste de orçamentos", str(error)))


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