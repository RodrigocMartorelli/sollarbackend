from fastapi import APIRouter
from typing import List

from app.services.utility_companies_db import get_all_companies
from app.services.utility_company_service import detect_utility_company

from fastapi import Query

router = APIRouter()


@router.get("/api-tools/utility-companies", response_model=List[str])
def list_utility_companies():
    """Return a list of known utility companies (concessionárias)."""
    companies = get_all_companies()
    return companies



@router.get("/api-tools/utility-company", response_model=str)
def detect_utility_company_route(
    ibge: int | None = Query(None), uf: str | None = Query(None), cidade: str | None = Query(None)
):
    """Detect utility company by IBGE code, UF or city name.

    Priority: IBGE -> UF fallback -> city name
    """
    try:
        result = detect_utility_company(ibge_code=ibge or '', uf=uf, city=cidade)
        return result or ''
    except Exception:
        return ''
